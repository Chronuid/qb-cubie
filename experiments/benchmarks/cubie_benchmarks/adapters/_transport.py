"""Exchange bounded JSONL messages with a persistent external process."""

import json
import os
import queue
import subprocess
import threading
import time

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.execution._process import ExecutionError, _environment, _kill

MAX_LINE = 1024 * 1024


class JsonlProcess:
    """Own one process session, its output readers and optional raw archives."""

    def __init__(self, command, cwd, deadline, directory=None):
        """Start a process without a shell or inherited credentials."""
        self.deadline, self.directory = deadline, directory
        self.messages: queue.Queue = queue.Queue(maxsize=64)
        self.stopped = threading.Event()
        self.process = subprocess.Popen(command, cwd=cwd, env=_environment(), stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        start_new_session=os.name != "nt")
        self.readers = [threading.Thread(target=target, daemon=True) for target in (self._stdout, self._stderr)]
        for reader in self.readers:
            reader.start()

    def __enter__(self):
        """Expose the active process session."""
        return self

    def __exit__(self, *_):
        """Always kill and reap the session and close its pipes."""
        self.close()

    def close(self):
        """Reap the process group even when a protocol exchange fails."""
        if self.stopped.is_set():
            return
        self.stopped.set()
        _kill(self.process)
        self.process.wait()
        for reader in self.readers:
            reader.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream is not None:
                stream.close()

    def finish(self):
        """Check a peer's final exit while allowing persistent sessions to stop."""
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            code = self.process.wait(timeout=min(0.2, self._remaining()))
        except subprocess.TimeoutExpired:
            return
        if code != 0:
            raise ExecutionError("infrastructure_error", f"Agent exited with code {code}")

    def exchange(self, payload):
        """Send one request and receive one versioned JSON object."""
        line = json.dumps(payload, allow_nan=False).encode("utf-8") + b"\n"
        if len(line) > MAX_LINE:
            raise ExecutionError("invalid_output", "Request exceeds JSONL line limit")
        self._send(line)
        response = self._receive()
        try:
            return v.version(v.snapshot(json.loads(response, object_pairs_hook=v.unique_keys)))
        except (ValueError, UnicodeError, RecursionError) as error:
            raise ExecutionError("invalid_output", f"Invalid JSONL response: {error}") from error

    def _send(self, line):
        """Send a bounded request with a deadline for blocked stdin."""
        self._remaining()
        sender = threading.Thread(target=self._write, args=(line,), daemon=True)
        sender.start()
        sender.join(timeout=self._remaining())
        if sender.is_alive():
            raise ExecutionError("agent_timeout", "Agent did not consume its request")
        self._archive("requests.jsonl", line)

    def _write(self, line):
        """Write a request while tolerating a peer that has already exited."""
        try:
            if self.process.stdin is not None:
                self.process.stdin.write(line)
                self.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            pass

    def _remaining(self):
        """Return the remaining session time or reject an expired deadline."""
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ExecutionError("agent_timeout", "Agent exceeded wall_time_seconds")
        return remaining

    def _receive(self):
        """Receive one line, distinguishing timeout, EOF and process crash."""
        try:
            line = self.messages.get(timeout=self._remaining())
        except queue.Empty as error:
            raise ExecutionError("agent_timeout", "Agent exceeded wall_time_seconds") from error
        if not line:
            self._eof()
        if len(line) > MAX_LINE or not line.endswith(b"\n"):
            raise ExecutionError("invalid_output", "Incomplete or oversized JSONL line")
        return line

    def _eof(self):
        """Classify a peer that closed stdout before submitting an event."""
        try:
            code = self.process.wait(timeout=min(0.1, self._remaining()))
        except subprocess.TimeoutExpired:
            code = None
        status = "infrastructure_error" if code not in (None, 0) else "invalid_output"
        raise ExecutionError(status, f"Agent closed stdout without an event (exit {code})")

    def _stdout(self):
        """Read bounded protocol lines without allowing an unbounded queue."""
        while not self.stopped.is_set() and self.process.stdout is not None:
            line = self.process.stdout.readline(MAX_LINE + 1)
            self._archive("responses.jsonl", line)
            if not self._enqueue(line) or not line or len(line) > MAX_LINE:
                break

    def _enqueue(self, line):
        """Apply backpressure to unsolicited stdout traffic."""
        while not self.stopped.is_set():
            try:
                self.messages.put(line, timeout=0.1)
                return True
            except queue.Full:
                continue
        return False

    def _stderr(self):
        """Drain diagnostics concurrently, retaining a bounded raw log."""
        remaining = 4 * MAX_LINE
        while not self.stopped.is_set() and self.process.stderr is not None:
            chunk = os.read(self.process.stderr.fileno(), 8192)
            if not chunk:
                break
            if remaining > 0:
                self._archive("stderr.log", chunk[:remaining])
                remaining -= len(chunk)

    def _archive(self, name, data):
        """Append raw transport bytes to the episode archive when requested."""
        if self.directory is not None and data:
            self.directory.mkdir(parents=True, exist_ok=True)
            with (self.directory / name).open("ab") as stream:
                stream.write(data)
