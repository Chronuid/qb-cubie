"""Bounded POSIX arena execution; unlimited calls retain subprocess.run semantics."""

import math
import os
import selectors
import signal
import subprocess
import time
from pathlib import Path
from typing import BinaryIO, cast


def validate_limits(timeout: float | None, max_output_bytes: int | None) -> None:
    _validate_timeout(timeout)
    _validate_output(max_output_bytes)
    if os.name != "posix" and (timeout is not None or max_output_bytes is not None):
        raise NotImplementedError("Arena execution limits currently require POSIX process groups")


def run_process(
    args: list[str], *, cwd: Path, env: dict | None = None,
    timeout: float | None = None, max_output_bytes: int | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    """Drain both streams concurrently, with bounded reads and one shared budget."""
    validate_limits(timeout, max_output_bytes)
    if timeout is None and max_output_bytes is None:
        return subprocess.run(args, cwd=cwd, env=env, capture_output=capture_output, check=False)
    capture = capture_output or max_output_bytes is not None
    with selectors.DefaultSelector() as selector:
        process, deadline = _start_process(args, cwd, env, capture, timeout)
        output = _monitor_process(process, selector, deadline, timeout, max_output_bytes, capture)
    return _completed_process(args, process, output, capture)


def _validate_timeout(timeout: float | None) -> None:
    if timeout is None:
        return
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise TypeError("timeout must be a positive finite number or None")
    try:
        finite = math.isfinite(timeout)
    except OverflowError:
        finite = False
    if not finite or timeout <= 0:
        raise ValueError("timeout must be a positive finite number or None")


def _validate_output(limit: int | None) -> None:
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("max_output_bytes must be a nonnegative integer or None")
    if limit < 0:
        raise ValueError("max_output_bytes must be a nonnegative integer or None")


def _start_process(
    args: list[str], cwd: Path, env: dict | None, capture: bool, timeout: float | None,
) -> tuple[subprocess.Popen[bytes], float | None]:
    deadline = None if timeout is None else time.monotonic() + timeout
    process = subprocess.Popen(
        args, cwd=cwd, env=env, start_new_session=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return process, deadline


def _monitor_process(
    process: subprocess.Popen[bytes], selector: selectors.BaseSelector,
    deadline: float | None, timeout: float | None, limit: int | None, capture: bool,
) -> list[bytearray]:
    try:
        if capture:
            _register_streams(process, selector)
        return _drain_streams(process, selector, deadline, timeout, limit)
    except BaseException as error:
        _cleanup_process(process, error)
        raise
    finally:
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()


def _register_streams(process: subprocess.Popen, selector: selectors.BaseSelector) -> None:
    for index, stream in enumerate((process.stdout, process.stderr)):
        if stream is not None:
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, index)


def _drain_streams(
    process: subprocess.Popen[bytes], selector: selectors.BaseSelector,
    deadline: float | None, timeout: float | None, limit: int | None,
) -> list[bytearray]:
    output = [bytearray(), bytearray()]
    total = 0
    while True:
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            raise TimeoutError(f"Arena target timed out after {timeout} seconds")
        # Poll even after EOF: a target may close both streams and keep running.
        events = selector.select(0.05 if remaining is None else min(0.05, remaining))
        total = _read_events(selector, events, output, total, limit)
        if process.poll() is not None and not selector.get_map():
            return output


def _read_events(
    selector: selectors.BaseSelector, events: list[tuple[selectors.SelectorKey, int]],
    output: list[bytearray], total: int, limit: int | None,
) -> int:
    for key, _ in events:
        size = 65536 if limit is None else min(65536, limit - total + 1)
        chunk = _read_chunk(selector, key, size)
        total += len(chunk)
        if limit is not None and total > limit:
            raise RuntimeError(f"Arena output limit exceeded ({limit} bytes)")
        output[key.data].extend(chunk)
    return total


def _read_chunk(selector: selectors.BaseSelector, key: selectors.SelectorKey, size: int) -> bytes:
    try:
        chunk = os.read(key.fd, size)
    except BlockingIOError:
        return b""
    if not chunk:
        selector.unregister(key.fileobj)
        # Only streams registered by _register_streams reach this reader.
        cast(BinaryIO, key.fileobj).close()
    return chunk


def _cleanup_process(process: subprocess.Popen, error: BaseException) -> None:
    try:
        _stop_process_group(process)
    except (OSError, subprocess.TimeoutExpired) as cleanup_error:
        error.add_note(f"Arena process cleanup also failed: {cleanup_error}")


def _stop_process_group(process: subprocess.Popen) -> None:
    """Escalate even if the leader has already exited but descendants survive."""
    if _signal_group(process.pid, signal.SIGTERM):
        _wait_group(process)
        _signal_group(process.pid, signal.SIGKILL)
    process.wait(timeout=1)


def _signal_group(pid: int, sig: int) -> bool:
    try:
        os.killpg(pid, sig)
        return True
    except ProcessLookupError:
        return False


def _wait_group(process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 0.2
    while time.monotonic() < deadline:
        # Reap the leader while allowing cooperative descendants to exit.
        process.poll()
        if not _signal_group(process.pid, 0):
            return
        time.sleep(0.01)


def _completed_process(
    args: list[str], process: subprocess.Popen[bytes], output: list[bytearray], capture: bool,
) -> subprocess.CompletedProcess[bytes]:
    if process.returncode is None:
        raise RuntimeError("STATE-GUARD: Arena process has not completed.")
    return subprocess.CompletedProcess(
        args, process.returncode,
        stdout=bytes(output[0]) if capture else None,
        stderr=bytes(output[1]) if capture else None,
    )
