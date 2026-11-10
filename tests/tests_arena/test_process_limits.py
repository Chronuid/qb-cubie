"""Independent checks for validation, stream handling and bounded buffering."""

import os
import sys
import time
import tracemalloc
from types import SimpleNamespace

import pytest

from qb_cubie import PyVenv, TempFS
from qb_cubie.arenas import _process


@pytest.mark.parametrize("arena", [TempFS, PyVenv])
@pytest.mark.parametrize("parameter, value, error", [
    ("timeout", 0, ValueError),
    ("timeout", -1, ValueError),
    ("timeout", float("inf"), ValueError),
    ("timeout", float("nan"), ValueError),
    ("timeout", 10 ** 1000, ValueError),
    ("timeout", True, TypeError),
    ("timeout", "1", TypeError),
    ("max_output_bytes", -1, ValueError),
    ("max_output_bytes", 1.5, TypeError),
    ("max_output_bytes", True, TypeError),
    ("max_output_bytes", "1024", TypeError),
])
def test_invalid_limits_are_rejected_before_setup(arena, parameter, value, error):
    with pytest.raises(error, match=parameter):
        arena(**{parameter: value})


def test_unsupported_platform_rejects_limits_explicitly(monkeypatch):
    monkeypatch.setattr(_process, "os", SimpleNamespace(name="nt"))
    _process.validate_limits(None, None)
    for limits in ((1, None), (None, 0)):
        with pytest.raises(NotImplementedError, match="POSIX"):
            _process.validate_limits(*limits)


@pytest.mark.skipif(os.name != "posix", reason="Limits require POSIX process groups")
def test_output_buffer_memory_is_bounded(tmp_path):
    # The child offers 16 MiB on each stream. Retaining it before checking the
    # 1 KiB budget would exceed the independent allocation threshold by far.
    script = "import os; os.write(1, b'x' * (16 * 1024 * 1024)); os.write(2, b'y' * (16 * 1024 * 1024))"
    tracemalloc.start()
    try:
        with pytest.raises(RuntimeError, match="output limit"):
            _process.run_process(
                [sys.executable, "-c", script], cwd=tmp_path,
                timeout=5, max_output_bytes=1024, capture_output=True,
            )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 1024 * 1024, f"Output monitoring allocated {peak} bytes for a 1024-byte budget"


@pytest.mark.skipif(os.name != "posix", reason="Limits require POSIX process groups")
def test_timeout_still_applies_after_both_streams_close(tmp_path):
    script = "import os, time; os.close(1); os.close(2); time.sleep(2)"
    with pytest.raises(TimeoutError, match="timed out"):
        _process.run_process(
            [sys.executable, "-c", script], cwd=tmp_path,
            timeout=0.1, max_output_bytes=0,
        )


@pytest.mark.skipif(os.name != "posix", reason="Limits require POSIX process groups")
def test_binary_output_is_counted_without_decoding(tmp_path):
    process = _process.run_process(
        [sys.executable, "-c", "import os; os.write(1, b'\\xff'); os.write(2, b'\\xfe')"],
        cwd=tmp_path, timeout=5, max_output_bytes=2,
    )
    assert process.returncode == 0
    assert process.stdout == b"\xff" and process.stderr == b"\xfe"


@pytest.mark.skipif(os.name != "posix", reason="Limits require POSIX process groups")
def test_timeout_includes_process_startup(tmp_path, monkeypatch):
    original = _process.subprocess.Popen

    def delayed_start(*args, **kwargs):
        process = original(*args, **kwargs)
        time.sleep(0.1)
        return process

    monkeypatch.setattr(_process.subprocess, "Popen", delayed_start)
    with pytest.raises(TimeoutError, match="timed out"):
        _process.run_process(
            [sys.executable, "-c", "pass"], cwd=tmp_path,
            timeout=0.05, capture_output=True,
        )
