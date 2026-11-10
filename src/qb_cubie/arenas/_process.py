"""Bounded POSIX arena execution; unlimited calls retain subprocess.run semantics."""

import math
import os
import selectors
import signal
import subprocess
import time
from pathlib import Path


def validate_limits(timeout: float | None, max_output_bytes: int | None) -> None:
    if timeout is not None:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be a positive finite number or None")
        try:
            finite = math.isfinite(timeout)
        except OverflowError:
            finite = False
        if not finite or timeout <= 0:
            raise ValueError("timeout must be a positive finite number or None")
    if max_output_bytes is not None:
        if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int):
            raise TypeError("max_output_bytes must be a nonnegative integer or None")
        if max_output_bytes < 0:
            raise ValueError("max_output_bytes must be a nonnegative integer or None")
    if os.name != "posix" and (timeout is not None or max_output_bytes is not None):
        raise NotImplementedError("Arena execution limits currently require POSIX process groups")


def _stop_process_group(process: subprocess.Popen) -> None:
    """Escalate even if the leader has already exited but descendants survive."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    else:
        deadline = time.monotonic() + 0.2
        while time.monotonic() < deadline:
            # Reap the leader while allowing cooperative descendants to exit.
            process.poll()
            try:
                os.killpg(process.pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.01)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=1)


def run_process(
    args: list[str], *, cwd: Path, env: dict | None = None,
    timeout: float | None = None, max_output_bytes: int | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    """Drain both streams concurrently, with bounded reads and one shared budget.

    Returned output is bytes. With an output limit, at most that many bytes are
    retained across both streams, plus one fixed-size read. EOF alone does not
    imply completion: the runner may close its streams and continue running.
    Conversely descendants may keep streams open after the runner exits.
    """
    validate_limits(timeout, max_output_bytes)
    if timeout is None and max_output_bytes is None:
        return subprocess.run(args, cwd=cwd, env=env, capture_output=capture_output, check=False)

    deadline = None if timeout is None else time.monotonic() + timeout
    capture = capture_output or max_output_bytes is not None
    output = [bytearray(), bytearray()]
    total = 0
    with selectors.DefaultSelector() as selector:
        process = subprocess.Popen(
            args, cwd=cwd, env=env, start_new_session=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
        )
        try:
            if capture:
                for index, stream in enumerate((process.stdout, process.stderr)):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ, index)
            while True:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    raise TimeoutError(f"Arena target timed out after {timeout} seconds")
                # Poll even without readable streams, including targets which
                # close both descriptors and then hang indefinitely.
                events = selector.select(0.05 if remaining is None else min(0.05, remaining))
                for key, _ in events:
                    size = 65536 if max_output_bytes is None else min(65536, max_output_bytes - total + 1)
                    try:
                        chunk = os.read(key.fd, size)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue
                    total += len(chunk)
                    if max_output_bytes is not None and total > max_output_bytes:
                        raise RuntimeError(f"Arena output limit exceeded ({max_output_bytes} bytes)")
                    output[key.data].extend(chunk)
                if process.poll() is not None and not selector.get_map():
                    break
        except BaseException as error:
            try:
                _stop_process_group(process)
            except (OSError, subprocess.TimeoutExpired) as cleanup_error:
                error.add_note(f"Arena process cleanup also failed: {cleanup_error}")
            raise
        finally:
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
    return subprocess.CompletedProcess(
        args, process.returncode,
        stdout=bytes(output[0]) if capture else None,
        stderr=bytes(output[1]) if capture else None,
    )
