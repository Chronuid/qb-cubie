"""Bounded Windows arena execution using Win32 Job Objects and reader threads."""

import ctypes
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, BinaryIO

_JOB_EXTENDED_LIMIT_INFO = 9
_JOB_KILL_ON_CLOSE = 0x2000
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_KERNEL32_SPECS: tuple[tuple[str, list[Any], Any], ...] = (
    ("CreateJobObjectW", [ctypes.c_void_p, ctypes.c_wchar_p], ctypes.c_void_p),
    ("SetInformationJobObject", [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32], ctypes.c_int),
    ("AssignProcessToJobObject", [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
    ("TerminateJobObject", [ctypes.c_void_p, ctypes.c_uint32], ctypes.c_int),
    ("CloseHandle", [ctypes.c_void_p], ctypes.c_int),
)


class _BasicLimitInfo(ctypes.Structure):
    """Win32 JOBOBJECT_BASIC_LIMIT_INFORMATION layout for 32/64-bit Windows."""

    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _IoCounters(ctypes.Structure):
    """Win32 IO_COUNTERS layout embedded inside extended job limits."""

    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class _ExtendedLimitInfo(ctypes.Structure):
    """Win32 JOBOBJECT_EXTENDED_LIMIT_INFORMATION (144 bytes on 64-bit)."""

    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInfo),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _StreamBudget:
    """Thread-safe shared byte budget and active stream tracker."""

    def __init__(self, active: int) -> None:
        """Initialize locks, wakeup event, and per-stream byte accumulators."""
        self.lock = threading.Lock()
        self.wakeup = threading.Event()
        self.output = [bytearray(), bytearray()]
        self.total = 0
        self.exceeded = False
        self.active = active

    def next_chunk_size(self, limit: int | None) -> int:
        """Return bounded next chunk size or zero once budget is exceeded."""
        with self.lock:
            if self.exceeded:
                return 0
            return 65536 if limit is None else max(0, min(65536, limit - self.total + 1))

    def record(self, index: int, chunk: bytes, limit: int | None) -> bool:
        """Account for read bytes and signal immediately when limit is exceeded."""
        with self.lock:
            if self.exceeded:
                return False
            self.total += len(chunk)
            if limit is not None and self.total > limit:
                self.exceeded = True
                self.wakeup.set()
                return False
            self.output[index].extend(chunk)
            return True

    def finish_stream(self) -> None:
        """Mark one reader thread finished and wake the monitor loop."""
        with self.lock:
            self.active -= 1
        self.wakeup.set()

    def snapshot(self) -> tuple[bool, int]:
        """Return current (exceeded, active_readers) tuple atomically."""
        with self.lock:
            return self.exceeded, self.active


def _kernel32() -> Any:
    """Return configured ctypes windll.kernel32 interface on Windows, or None."""
    windll = getattr(ctypes, "windll", None)
    if windll is None:
        return None
    return _configure_kernel32(windll.kernel32)


def _configure_kernel32(lib: Any) -> Any:
    """Bind explicit ctypes signatures for Win32 Job Object functions."""
    for name, argtypes, restype in _KERNEL32_SPECS:
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = argtypes, restype
    return lib


def _attach_job(process: subprocess.Popen[bytes]) -> int | None:
    """Attach process to a kill-on-close Win32 Job Object when supported."""
    lib = _kernel32()
    proc_handle = getattr(process, "_handle", None)
    if lib is None or proc_handle is None:
        return None
    job = lib.CreateJobObjectW(None, None)
    if not job:
        return None
    return _configure_job_handle(lib, job, int(proc_handle))


def _configure_job_handle(lib: Any, job: Any, proc_handle: int) -> int | None:
    """Apply kill-on-close flag and assign process handle to job."""
    info = _ExtendedLimitInfo()
    info.BasicLimitInformation.LimitFlags = _JOB_KILL_ON_CLOSE
    configured = lib.SetInformationJobObject(job, _JOB_EXTENDED_LIMIT_INFO, ctypes.byref(info), ctypes.sizeof(info))
    if configured and lib.AssignProcessToJobObject(job, proc_handle):
        return int(job)
    lib.CloseHandle(job)
    return None


def _close_job(job: int | None) -> None:
    """Close an open Win32 Job Object handle if present."""
    lib = _kernel32() if job is not None else None
    if lib is not None and job is not None:
        lib.CloseHandle(job)


def _terminate_win32(process: subprocess.Popen[bytes], job: int | None) -> None:
    """Terminate the Win32 job tree or fall back to taskkill and Popen.kill."""
    lib = _kernel32() if job is not None else None
    if lib is not None and job is not None and lib.TerminateJobObject(job, 1):
        process.wait(timeout=1)
        return
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)
    if process.poll() is None:
        process.kill()
    process.wait(timeout=1)


def _cleanup_win32(process: subprocess.Popen[bytes], job: int | None, error: BaseException) -> None:
    """Terminate timed-out or failed child trees and attach any cleanup note."""
    try:
        _terminate_win32(process, job)
    except (OSError, subprocess.SubprocessError) as cleanup_error:
        error.add_note(f"Arena process cleanup also failed: {cleanup_error}")


def _read_once(stream: BinaryIO, size: int) -> bytes:
    """Read one unbuffered chunk while tolerating closed pipe shutdown races."""
    try:
        return stream.read(size)
    except (OSError, ValueError):
        return b""


def _read_stream(stream: BinaryIO, index: int, budget: _StreamBudget, limit: int | None) -> None:
    """Drain one raw pipe into the shared byte budget until EOF or limit breach."""
    try:
        while (size := budget.next_chunk_size(limit)) > 0:
            chunk = _read_once(stream, size)
            if not chunk or not budget.record(index, chunk, limit):
                break
    finally:
        budget.finish_stream()


def _start_readers(
    process: subprocess.Popen[bytes], limit: int | None,
) -> tuple[list[threading.Thread], _StreamBudget]:
    """Launch daemon pipe reader threads for active stdout and stderr streams."""
    streams = [(idx, s) for idx, s in enumerate((process.stdout, process.stderr)) if s is not None]
    budget = _StreamBudget(len(streams))
    threads = [
        threading.Thread(target=_read_stream, args=(stream, idx, budget, limit), daemon=True)
        for idx, stream in streams
    ]
    for thread in threads:
        thread.start()
    return threads, budget


def _wait_win32(
    process: subprocess.Popen[bytes], budget: _StreamBudget,
    deadline: float | None, timeout: float | None, limit: int | None,
) -> list[bytearray]:
    """Wait until process exit and stream EOF while enforcing timeout and output budget."""
    while True:
        budget.wakeup.clear()
        exceeded, active = budget.snapshot()
        if exceeded:
            raise RuntimeError(f"Arena output limit exceeded ({limit} bytes)")
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            raise TimeoutError(f"Arena target timed out after {timeout} seconds")
        if process.poll() is not None and active <= 0:
            return budget.output
        budget.wakeup.wait(0.02 if remaining is None else min(0.02, remaining))


def _finalize_win32(
    process: subprocess.Popen[bytes], threads: list[threading.Thread], job: int | None,
) -> None:
    """Close pipe descriptors, join daemon reader threads, and close job handles."""
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            stream.close()
    for thread in threads:
        thread.join(timeout=0.5)
    _close_job(job)


def run_win32_process(
    args: list[str], *, cwd: Path, env: dict | None,
    timeout: float | None, max_output_bytes: int | None, capture: bool,
) -> subprocess.CompletedProcess[bytes]:
    """Execute one child process with bounded Win32 output readers and job-tree termination."""
    deadline = None if timeout is None else time.monotonic() + timeout
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", _CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0
    process = subprocess.Popen(
        args, cwd=cwd, env=env, bufsize=0, creationflags=flags,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    job = _attach_job(process)
    threads, budget = _start_readers(process, max_output_bytes)
    output = _monitor_win32(process, budget, threads, job, deadline, timeout, max_output_bytes)
    return _completed_win32(args, process, output, capture)


def _monitor_win32(
    process: subprocess.Popen[bytes], budget: _StreamBudget, threads: list[threading.Thread],
    job: int | None, deadline: float | None, timeout: float | None, limit: int | None,
) -> list[bytearray]:
    """Run wait loop, clean up process tree on abort, and release resources."""
    try:
        return _wait_win32(process, budget, deadline, timeout, limit)
    except BaseException as error:
        _cleanup_win32(process, job, error)
        raise
    finally:
        _finalize_win32(process, threads, job)


def _completed_win32(
    args: list[str], process: subprocess.Popen[bytes], output: list[bytearray], capture: bool,
) -> subprocess.CompletedProcess[bytes]:
    """Construct CompletedProcess from finalized returncode and raw byte buffers."""
    if process.returncode is None:
        raise RuntimeError("STATE-GUARD: Arena process has not completed.")
    return subprocess.CompletedProcess(
        args, process.returncode,
        stdout=bytes(output[0]) if capture else None,
        stderr=bytes(output[1]) if capture else None,
    )
