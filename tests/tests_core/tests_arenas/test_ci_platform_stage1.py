"""Stage 1 CI-matrix contracts for macOS symlink roots, POSIX limits, Win32 limits, and wheel tooling."""

import ctypes
import importlib.util
import ntpath
import os
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from types import SimpleNamespace

import pytest

from qb_cubie import EBT, PickleCodec, PyVenv, TempFS, WorldState
from qb_cubie.core.arenas import _process, _relocation
from qb_cubie.core.services import DocFrame

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EMPTY_BASE = PROJECT_ROOT / "tests" / ".arenas" / "empty_venv"


def _symlink_alias(tmp_path: Path) -> tuple[Path, Path]:
    """Create a real directory and a symlink alias to emulate macOS /var -> /private/var."""
    real_dir = tmp_path / "real_root"
    real_dir.mkdir()
    alias_dir = tmp_path / "alias_root"
    try:
        alias_dir.symlink_to(real_dir, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Symlink creation unavailable on this host: {exc}")
    return real_dir.resolve(), alias_dir


def _load_script_module(rel_path: str, module_name: str):
    """Load a standalone Python script outside src/ for isolated unit checks."""
    script_path = PROJECT_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pyvenv_probe_env() -> dict[str, str]:
    """Return child CWD, prefix, and VIRTUAL_ENV paths from inside PyVenv."""
    return {
        "cwd": str(Path.cwd()),
        "cwd_resolved": str(Path.cwd().resolve()),
        "prefix": str(Path(sys.prefix).resolve()),
        "virtual_env": os.environ["VIRTUAL_ENV"],
    }


def _fake_win32_process(pid: int = 4321, handle: int = 100):
    """Construct a lightweight fake Popen object recording kill/wait invocations."""
    events: list[tuple] = []

    class FakeProcess:
        def __init__(self) -> None:
            self.pid = pid
            self._handle = handle
            self.returncode = None

        def poll(self):
            return self.returncode

        def kill(self) -> None:
            events.append(("kill", self.pid))
            self.returncode = 1

        def wait(self, timeout=None) -> int:
            events.append(("wait", timeout))
            self.returncode = 1
            return 1

    return FakeProcess(), events


# ========== M1: SYMLINK-RESOLVED ROOTS & READ-ONLY CLEANUP ============================================================


def test_tempfs_resolves_symlinked_mkdtemp_workspace(tmp_path, monkeypatch):
    real_dir, alias_dir = _symlink_alias(tmp_path)
    original_mkdtemp = tempfile.mkdtemp

    def make_alias_tempdir(suffix=None, prefix=None, dir=None):
        if dir is None and (prefix or "").startswith("cubie_arena_"):
            created = Path(original_mkdtemp(prefix=prefix, dir=real_dir))
            return str(alias_dir / created.name)
        return original_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)

    monkeypatch.setattr("qb_cubie.core.arenas.tempfs.tempfile.mkdtemp", make_alias_tempdir)
    arena = TempFS()

    def check_cwd() -> dict[str, str]:
        return {"cwd": str(Path.cwd()), "resolved": str(Path.cwd().resolve())}

    trace = EBT(
        arena=arena,
        target=check_cwd,
        pre=WorldState(),
        post=WorldState(returns=lambda obs: obs["cwd"] == obs["resolved"]),
        reporter=None,
    ).run()
    assert trace.evaluation is True
    reported_fs = trace.traces[0].outcome.fs
    assert reported_fs == trace.traces[0].outcome.returns["cwd"]
    assert Path(reported_fs).is_relative_to(real_dir)


def test_pyvenv_resolves_symlinked_mkdtemp_root(tmp_path, monkeypatch):
    real_dir, alias_dir = _symlink_alias(tmp_path)
    original_mkdtemp = tempfile.mkdtemp

    def make_alias_tempdir(suffix=None, prefix=None, dir=None):
        if dir is None and (prefix or "").startswith("cubie_arena_"):
            created = Path(original_mkdtemp(prefix=prefix, dir=real_dir))
            return str(alias_dir / created.name)
        return original_mkdtemp(suffix=suffix, prefix=prefix, dir=dir)

    monkeypatch.setattr("qb_cubie.core.arenas.pyvenv.tempfile.mkdtemp", make_alias_tempdir)
    arena = PyVenv(str(EMPTY_BASE), codec=PickleCodec())

    trace = EBT(
        arena=arena,
        target=_pyvenv_probe_env,
        pre=WorldState(),
        post=WorldState(
            returns=lambda obs: (
                obs["cwd"] == obs["cwd_resolved"]
                and Path(obs["virtual_env"]) == Path(obs["virtual_env"]).resolve()
                and Path(obs["prefix"]) == Path(obs["virtual_env"]).resolve()
            )
        ),
        reporter=None,
    ).run()
    assert trace.evaluation is True
    assert trace.traces[0].outcome.fs == trace.traces[0].outcome.returns["cwd"]
    assert trace.traces[0].outcome.arena == trace.traces[0].outcome.returns["virtual_env"]
    assert Path(trace.traces[0].outcome.fs).is_relative_to(real_dir)


def test_relocate_link_handles_symlinked_base_prefix(tmp_path):
    real_dir, alias_dir = _symlink_alias(tmp_path)
    real_base = real_dir / "base_env"
    alias_base = alias_dir / "base_env"
    (real_base / "bin").mkdir(parents=True)
    body = real_base / "alias-body.py"
    body.write_text(f"#!{real_base}/bin/python\nprint('ok')\n", encoding="utf-8")
    body.chmod(0o755)

    clone = tmp_path / "clone"
    (clone / "bin").mkdir(parents=True)
    clone_body = clone / "alias-body.py"
    clone_body.write_bytes(body.read_bytes())
    clone_body.chmod(0o755)
    script_link = clone / "bin" / "tool"
    script_link.symlink_to(body)

    _relocation.relocate_scripts(alias_base, clone)
    assert Path(os.readlink(script_link)).resolve() == clone_body.resolve()

    outside = tmp_path / "outside.py"
    outside.write_text("#!/bin/sh\necho bad\n", encoding="utf-8")
    outside_link = clone / "bin" / "escape"
    outside_link.symlink_to(outside)
    with pytest.raises(RuntimeError, match="Unsupported console entry point"):
        _relocation.relocate_scripts(alias_base, clone)


def test_tempfs_teardown_cleans_readonly_subtree(tmp_path, monkeypatch):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr("qb_cubie.core.arenas.tempfs.tempfile.tempdir", str(scratch))
    arena = TempFS()
    arena.setup(WorldState())
    workspace = arena.workspace_path
    assert workspace is not None
    locked_dir = workspace / "locked"
    locked_dir.mkdir()
    locked_file = locked_dir / "readonly.txt"
    locked_file.write_text("immutable", encoding="utf-8")
    locked_file.chmod(0o444)
    locked_dir.chmod(0o555)
    try:
        arena.teardown()
        assert not workspace.exists()
        assert arena.workspace_path is None
    finally:
        if locked_dir.exists():
            locked_dir.chmod(0o755)
        if locked_file.exists():
            locked_file.chmod(0o644)


# ========== M2: PORTABLE POSIX PROCESS-GROUP TIMEOUT WITHOUT /proc ====================================================


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group probe")
def test_ebt_posix_timeout_stops_spawned_child_without_proc(tmp_path):
    heartbeat = tmp_path / "heartbeat.txt"

    def spawn_long_lived_child(marker_path: str) -> str:
        child_code = (
            "import time; from pathlib import Path; "
            f"p = Path({marker_path!r}); "
            "i = 0\n"
            "with p.open('a', encoding='utf-8') as stream:\n"
            "    while True:\n"
            "        i += 1\n"
            "        stream.write(f'{i}\\n')\n"
            "        stream.flush()\n"
            "        time.sleep(0.02)\n"
        )
        subprocess.Popen([sys.executable, "-c", child_code])
        time.sleep(5.0)
        return "unreachable"

    arena = TempFS(timeout=0.4)
    case = EBT(
        arena=arena,
        target=spawn_long_lived_child,
        pre=WorldState(args=(str(heartbeat),)),
        post=WorldState(returns="unreachable"),
        reporter=None,
    )
    with pytest.raises(TimeoutError, match="timed out"):
        case.run()
    assert arena.workspace_path is None
    assert heartbeat.is_file()
    time.sleep(0.15)
    first_lines = heartbeat.read_text(encoding="utf-8").splitlines()
    assert len(first_lines) >= 1
    time.sleep(0.15)
    second_lines = heartbeat.read_text(encoding="utf-8").splitlines()
    assert first_lines == second_lines


# ========== W1 (E1-A): WIN32 BOUNDED EXECUTION BACKEND & DISPATCHER ===================================================


def test_win32_backend_enforces_budget_timeout_and_binary_output(tmp_path, monkeypatch):
    from qb_cubie.core.arenas import _process_win32

    if ctypes.sizeof(ctypes.c_void_p) == 8:
        assert ctypes.sizeof(_process_win32._ExtendedLimitInfo) == 144

    flood_script = "import os; os.write(1, b'x' * (16 * 1024 * 1024)); os.write(2, b'y' * (16 * 1024 * 1024))"
    tracemalloc.start()
    try:
        with pytest.raises(RuntimeError, match="output limit"):
            _process_win32.run_win32_process(
                [sys.executable, "-c", flood_script],
                cwd=tmp_path, env=None, timeout=5.0, max_output_bytes=1024, capture=True,
            )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 1024 * 1024

    binary = _process_win32.run_win32_process(
        [sys.executable, "-c", "import os; os.write(1, b'\\xff'); os.write(2, b'\\xfe')"],
        cwd=tmp_path, env=None, timeout=5.0, max_output_bytes=2, capture=True,
    )
    assert binary.returncode == 0
    assert binary.stdout == b"\xff" and binary.stderr == b"\xfe"

    with pytest.raises(TimeoutError, match="timed out"):
        _process_win32.run_win32_process(
            [sys.executable, "-c", "import os, time; os.close(1); os.close(2); time.sleep(2)"],
            cwd=tmp_path, env=None, timeout=0.1, max_output_bytes=0, capture=True,
        )

    original_popen = _process_win32.subprocess.Popen

    def delayed_popen(*args, **kwargs):
        proc = original_popen(*args, **kwargs)
        time.sleep(0.1)
        return proc

    monkeypatch.setattr(_process_win32.subprocess, "Popen", delayed_popen)
    with pytest.raises(TimeoutError, match="timed out"):
        _process_win32.run_win32_process(
            [sys.executable, "-c", "pass"],
            cwd=tmp_path, env=None, timeout=0.05, max_output_bytes=None, capture=True,
        )


def test_win32_job_object_lifecycle_and_taskkill_fallback(monkeypatch):
    from qb_cubie.core.arenas import _process_win32

    calls: list[tuple] = []

    class FakeKernel32:
        def __init__(self, assign_result: int) -> None:
            self.assign_result = assign_result

        def CreateJobObjectW(self, attrs, name):
            calls.append(("CreateJobObjectW", attrs, name))
            return 777

        def SetInformationJobObject(self, job, info_class, info_ptr, length):
            info = ctypes.cast(info_ptr, ctypes.POINTER(_process_win32._ExtendedLimitInfo)).contents
            calls.append(("SetInformationJobObject", job, info_class, info.BasicLimitInformation.LimitFlags, length))
            return 1

        def AssignProcessToJobObject(self, job, proc_handle):
            calls.append(("AssignProcessToJobObject", job, proc_handle))
            return self.assign_result

        def TerminateJobObject(self, job, exit_code):
            calls.append(("TerminateJobObject", job, exit_code))
            return 1

        def CloseHandle(self, handle):
            calls.append(("CloseHandle", handle))
            return 1

    fake_lib = FakeKernel32(assign_result=1)
    monkeypatch.setattr(_process_win32, "_kernel32", lambda: fake_lib)
    proc, proc_events = _fake_win32_process()
    job = _process_win32._attach_job(proc)
    assert job == 777
    assert ("SetInformationJobObject", 777, 9, 0x2000, ctypes.sizeof(_process_win32._ExtendedLimitInfo)) in calls
    assert ("AssignProcessToJobObject", 777, 100) in calls

    _process_win32._terminate_win32(proc, job)
    assert ("TerminateJobObject", 777, 1) in calls
    assert ("wait", 1) in proc_events

    calls.clear()
    fake_fail_lib = FakeKernel32(assign_result=0)
    monkeypatch.setattr(_process_win32, "_kernel32", lambda: fake_fail_lib)
    taskkill_cmds: list[list[str]] = []
    monkeypatch.setattr(
        _process_win32.subprocess,
        "run",
        lambda cmd, **kwargs: taskkill_cmds.append(list(cmd)) or subprocess.CompletedProcess(cmd, 0),
    )
    proc2, proc2_events = _fake_win32_process(pid=9876)
    assert _process_win32._attach_job(proc2) is None
    assert ("CloseHandle", 777) in calls
    _process_win32._terminate_win32(proc2, None)
    assert taskkill_cmds == [["taskkill", "/F", "/T", "/PID", "9876"]]
    assert ("kill", 9876) in proc2_events
    assert ("wait", 1) in proc2_events


def test_run_process_dispatches_to_win32_when_os_is_nt(tmp_path, monkeypatch):
    dispatched: list[tuple] = []

    def spy_win32(args, *, cwd, env, timeout, max_output_bytes, capture):
        dispatched.append((args, cwd, env, timeout, max_output_bytes, capture))
        return subprocess.CompletedProcess(args, 0, b"", b"")

    monkeypatch.setattr(_process, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(_process, "run_win32_process", spy_win32)
    result = _process.run_process([sys.executable, "-c", "pass"], cwd=tmp_path, timeout=1.0)
    assert result.returncode == 0
    assert len(dispatched) == 1
    assert dispatched[0][3] == 1.0


# ========== W2–W4: WHEEL PATH ISOLATION, BENCHMARKS & OLLAMA AGENTS =====================================================


def test_check_wheel_windows_env_isolates_path_without_host_leak():
    module = _load_script_module("scripts/check_wheel.py", "cubie_check_wheel_under_test")
    base_env = {
        "PATH": r"C:\HostLinters;C:\GlobalPython\Scripts",
        "SystemRoot": r"C:\Windows",
        "WINDIR": r"C:\Windows",
        "COMSPEC": r"C:\Windows\System32\cmd.exe",
        "PATHEXT": ".COM;.EXE",
        "TEMP": r"C:\Temp",
        "TMP": r"C:\Temp",
        "PYTHONPATH": r"C:\Leak",
        "PYTEST_ADDOPTS": "-q",
        "QB_CUBIE_DEFAULT_ARENA": r"C:\Leak",
    }
    env = module.build_wheel_environment(
        base_env,
        python=Path(r"C:\TestVenv\Scripts\python.exe"),
        virtualenv=Path(r"C:\TestVenv"),
        os_name="nt",
        base_prefix=r"C:\BasePython",
    )
    path_entries = env["PATH"].split(";")
    assert r"C:\HostLinters" not in env["PATH"]
    assert r"C:\GlobalPython\Scripts" not in env["PATH"]
    for expected in (
        str(Path(r"C:\TestVenv\Scripts")),
        r"C:\BasePython",
        r"C:\Windows\System32",
        r"C:\Windows",
        r"C:\Windows\System32\Wbem",
    ):
        assert expected in path_entries
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    for var in ("WINDIR", "SystemRoot", "COMSPEC", "PATHEXT", "TEMP", "TMP"):
        assert env[var] == base_env[var]
    assert "PYTHONPATH" not in env and "PYTEST_ADDOPTS" not in env and "QB_CUBIE_DEFAULT_ARENA" not in env


def test_benchmarks_process_windows_env_and_utf8(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(PROJECT_ROOT / "experiments" / "benchmarks"))
    import cubie_benchmarks.execution._process as bench_proc

    fake_env = {
        "SYSTEMROOT": r"C:\Windows",
        "WINDIR": r"C:\Windows",
        "COMSPEC": r"C:\Windows\System32\cmd.exe",
        "PATHEXT": ".COM;.EXE",
        "TEMP": r"C:\Temp",
        "TMP": r"C:\Temp",
        "OPENAI_API_KEY": "secret",
    }
    monkeypatch.setattr(
        bench_proc,
        "os",
        SimpleNamespace(name="nt", environ=fake_env, path=ntpath, pathsep=";"),
    )
    env = bench_proc._environment()
    assert r"C:\Windows\System32" in env["PATH"].split(";")
    assert env["COMSPEC"] == r"C:\Windows\System32\cmd.exe"
    assert env["PATHEXT"] == ".COM;.EXE"
    assert env["PYTHONUTF8"] == "1"
    assert "OPENAI_API_KEY" not in env

    seen_kwargs: list[dict] = []

    class FakePopen:
        def __init__(self, command, **kwargs) -> None:
            seen_kwargs.append(kwargs)
            self.returncode = 0

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def communicate(self, timeout=None):
            return ("ok", "")

    monkeypatch.setattr(bench_proc.subprocess, "Popen", FakePopen)
    observed = bench_proc._execute([sys.executable, "-c", "pass"], tmp_path, 5)
    assert observed["returncode"] == 0
    assert seen_kwargs[0]["encoding"] == "utf-8"
    assert seen_kwargs[0]["errors"] == "replace"


def test_ollama_reviewer_tools_uses_windows_kill_on_nt(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(PROJECT_ROOT / "experiments" / "ollama-agents"))
    from ollama_agents.errors import AdapterError
    import ollama_agents.reviewer.tools as reviewer_tools

    def forbid_killpg(*_args):
        raise AssertionError("os.killpg must not be called on Windows")

    monkeypatch.setattr(
        reviewer_tools,
        "os",
        SimpleNamespace(name="nt", environ=dict(os.environ), killpg=forbid_killpg),
    )
    popen_kwargs: list[dict] = []
    run_calls: list[list[str]] = []

    class FakeTimeoutPopen:
        def __init__(self, command, **kwargs) -> None:
            popen_kwargs.append(kwargs)
            self.pid = 5432
            self.calls = 0

        def poll(self):
            return None if self.calls < 2 else 1

        def kill(self):
            self.calls += 1

        def wait(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired(["pytest"], timeout)
            return 1

    monkeypatch.setattr(reviewer_tools.subprocess, "Popen", FakeTimeoutPopen)
    monkeypatch.setattr(
        reviewer_tools.subprocess,
        "run",
        lambda cmd, **kwargs: run_calls.append(list(cmd)) or subprocess.CompletedProcess(cmd, 0),
    )
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        with pytest.raises(AdapterError) as caught:
            reviewer_tools._process(["pytest"], tmp_path, {}, 0.5, out, err)
    assert caught.value.status == "agent_timeout"
    assert popen_kwargs[0].get("start_new_session") is False
    assert run_calls == [["taskkill", "/F", "/T", "/PID", "5432"]]


# ========== W6: PYTHON LAUNCHER VARIANTS, BACKSLASH GUARD & DOCFRAME LF HYGIENE =========================================


@pytest.mark.parametrize(
    "exe_name",
    ["pythonw3.13.exe", "python3.13t.exe", "python_d.exe", "pythonw_d.exe", "python3.14t.exe", "𝜋thon3.14.exe"],
)
def test_relocation_allows_windows_python_interpreter_variants(tmp_path, exe_name):
    base = tmp_path / "base"
    clone = tmp_path / "clone"
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)
    (clone / "Scripts" / exe_name).write_bytes(b"PE-stub")
    _relocation.relocate_scripts(base, clone)


def test_relocation_rejects_backslash_base_reference_in_windows_script(tmp_path):
    base = tmp_path / "base"
    clone = tmp_path / "clone"
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)
    batch = clone / "Scripts" / "run.bat"
    batch.write_bytes(f"@echo off\r\n{base}\\Scripts\\python.exe -m demo\r\n".encode("utf-8"))
    with pytest.raises(RuntimeError, match="Unsupported console entry point"):
        _relocation.relocate_scripts(base, clone)


def test_docframe_update_writes_explicit_lf_newlines(tmp_path, monkeypatch):
    root = tmp_path / "doc_project"
    (root / "docs" / ".assets").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (root / "docs" / ".assets" / "cubie-logo-written.png").write_bytes(b"png")
    (root / "docs" / ".assets" / "cubie-small.png").write_bytes(b"png")
    (root / "README.md").write_text(
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Demo\n<!-- /qb:frame -->\n\n'
        'Body\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
        encoding="utf-8",
    )

    newlines: list[object] = []
    original_write_text = Path.write_text

    def spy_write_text(self, data, encoding=None, errors=None, newline=None):
        newlines.append(newline)
        return original_write_text(self, data, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(Path, "write_text", spy_write_text)
    report = DocFrame.update(root)
    assert report.updated_files == ("README.md",)
    assert newlines == ["\n"]
