"""Stage 2 CI-matrix contracts for Win32 .exe launcher relocation, POSIX diff paths, and Windows hygiene."""

import ctypes
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path, PureWindowsPath

import pytest

from qb_cubie import EBT, PickleCodec, PyVenv, WorldState
from qb_cubie.arenas import _hydration, _relocation, _requirements, pyvenv
from qb_cubie.arenas.pyvenv import ArenaBuilder
from qb_cubie.reporter import PytestReporter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COWSAY_BASE = PROJECT_ROOT / "tests" / ".arenas" / "cowsay_env"


def _build_distlib_exe(shebang_target: str, script_text: str = "print('ok')\n") -> bytes:
    """Create a synthetic PE + #!shebang + ZIP distlib-style console wrapper."""
    quoted = f'"{shebang_target}"' if " " in shebang_target else shebang_target
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as archive:
        archive.writestr("__main__.py", script_text)
    return b"MZ" + (b"\x00" * 64) + f"#!{quoted}\r\n".encode("utf-8") + zip_buf.getvalue()


def _extract_distlib_shebang(data: bytes) -> bytes:
    """Return the embedded #!... line preceding the ZIP payload."""
    pk = data.index(b"PK\x03\x04")
    start = data.rindex(b"#!", 0, pk)
    return data[start:pk]


def _make_fake_resource_kernel32(
    resources: dict[str, bytes],
    calls: list[tuple],
    updated: dict[str, bytes],
):
    """Build a ctypes-compatible fake kernel32 module for Win32 PE resource APIs."""
    buffers = {name: ctypes.create_string_buffer(raw, len(raw)) for name, raw in resources.items()}
    state = {"loaded": False, "update_open": False}

    class FakeResourceKernel32:
        def LoadLibraryExW(self, path, file_handle, flags):
            assert file_handle is None and flags == 0x2
            state["loaded"] = True
            calls.append(("LoadLibraryExW", path, flags))
            return 42

        def FindResourceW(self, module, name, type_id):
            assert module == 42 and type_id == 10
            if name not in buffers:
                return 0
            return 100 + list(buffers).index(name)

        def SizeofResource(self, module, resource):
            assert module == 42 and resource >= 100
            name = list(buffers)[resource - 100]
            return len(resources[name])

        def LoadResource(self, module, resource):
            assert module == 42 and resource >= 100
            return 200 + (resource - 100)

        def LockResource(self, mem):
            name = list(buffers)[mem - 200]
            return ctypes.addressof(buffers[name])

        def FreeLibrary(self, module):
            assert module == 42
            state["loaded"] = False
            calls.append(("FreeLibrary", module))
            return 1

        def BeginUpdateResourceW(self, path, delete_existing):
            assert not state["loaded"], "Module handle must be freed before BeginUpdateResourceW"
            assert delete_existing == 0
            state["update_open"] = True
            calls.append(("BeginUpdateResourceW", path, delete_existing))
            return 99

        def UpdateResourceW(self, handle, type_id, name, lang, data, size):
            assert handle == 99 and state["update_open"]
            assert type_id == 10 and name == "UV_PYTHON_PATH" and lang == 0
            raw = data[:size] if isinstance(data, (bytes, bytearray)) else ctypes.string_at(data, size)
            updated[name] = raw
            calls.append(("UpdateResourceW", handle, name, size))
            return 1

        def EndUpdateResourceW(self, handle, discard):
            assert handle == 99 and discard == 0
            state["update_open"] = False
            calls.append(("EndUpdateResourceW", handle, discard))
            return 1

    return FakeResourceKernel32()


# ========== E2-A: DISTLIB / PIP ZIP WRAPPER RELOCATION ================================================================


@pytest.mark.parametrize(
    ("base_name", "clone_name", "use_backslash"),
    [
        ("base", "clone", False),
        ("base with spaces", "clone with spaces", False),
        ("base with spaces", "clone with spaces", True),
    ],
    ids=["plain-posix", "spaces-posix", "spaces-backslash"],
)
def test_distlib_exe_launcher_relocates_base_shebang_and_preserves_zip(
    tmp_path, base_name, clone_name, use_backslash,
):
    base = tmp_path / base_name
    clone = tmp_path / clone_name
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)
    shebang_target = f"{base}\\Scripts\\python.exe" if use_backslash else str(base / "Scripts" / "python.exe")
    launcher = clone / "Scripts" / "cowsay.exe"
    launcher.write_bytes(_build_distlib_exe(shebang_target, "print('cowsay-relocated')\n"))

    _relocation.relocate_scripts(base, clone)

    relocated_bytes = launcher.read_bytes()
    assert relocated_bytes.startswith(b"MZ")
    shebang_line = _extract_distlib_shebang(relocated_bytes)
    assert shebang_line.startswith(b"#!") and shebang_line.endswith(b"\r\n")
    inner = shebang_line[2:-2].decode("utf-8")
    if " " in str(clone):
        assert inner.startswith('"') and inner.endswith('"')
    unquoted = inner.strip('"').replace("\\", "/")
    assert unquoted == f"{clone.as_posix()}/Scripts/python.exe"
    assert str(base).encode("utf-8") not in relocated_bytes[: relocated_bytes.index(b"PK\x03\x04")]
    with zipfile.ZipFile(io.BytesIO(relocated_bytes)) as archive:
        assert archive.read("__main__.py") == b"print('cowsay-relocated')\n"


def test_distlib_exe_rejects_external_non_python_or_corrupt_exe(tmp_path):
    base = tmp_path / "base"
    clone = tmp_path / "clone"
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)

    probes = {
        "native.exe": b"MZ\x00\x00not-a-zip",
        "cmd_wrapper.exe": _build_distlib_exe(r"C:\Windows\System32\cmd.exe"),
        "external.exe": _build_distlib_exe(r"C:\OtherEnv\Scripts\python.exe"),
    }
    for name, payload in probes.items():
        script = clone / "Scripts" / name
        script.write_bytes(payload)
        with pytest.raises(RuntimeError, match="Unsupported console entry point"):
            _relocation.relocate_scripts(base, clone)
        script.unlink()


# ========== E2-A: UV 0.11.3 PE RESOURCE TRAMPOLINE RELOCATION =========================================================


def test_uv_resource_trampoline_relocates_absolute_python_path(tmp_path, monkeypatch):
    from qb_cubie.arenas import _relocation_win32

    base = tmp_path / "uv base"
    clone = tmp_path / "uv clone"
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)
    launcher = clone / "Scripts" / "cowsay.exe"
    launcher.write_bytes(b"MZ" + b"\x00" * 64)

    calls: list[tuple] = []
    updated: dict[str, bytes] = {}
    fake_lib = _make_fake_resource_kernel32(
        {
            "UV_TRAMPOLINE_KIND": b"\x01",
            "UV_PYTHON_PATH": f"{base}\\Scripts\\python.exe".encode("utf-8"),
        },
        calls,
        updated,
    )
    monkeypatch.setattr(_relocation_win32, "_resource_kernel32", lambda: fake_lib)

    _relocation.relocate_scripts(base, clone)
    assert ("FreeLibrary", 42) in calls
    assert ("BeginUpdateResourceW", str(launcher), 0) in calls
    assert calls.index(("FreeLibrary", 42)) < calls.index(("BeginUpdateResourceW", str(launcher), 0))
    assert "UV_PYTHON_PATH" in updated
    relocated_target = Path(updated["UV_PYTHON_PATH"].decode("utf-8").replace("\\", "/"))
    assert relocated_target.as_posix() == f"{clone.as_posix()}/Scripts/python.exe"


@pytest.mark.parametrize(
    ("kind", "py_path", "should_accept"),
    [
        (b"\x01", b"python.exe", True),
        (b"\x01", b"pythonw3.13.exe", True),
        (b"\x01", b"..\\..\\outside\\python.exe", False),
        (b"\x01", b"cmd.exe", False),
        (b"\x02", b"python.exe", False),
    ],
    ids=["safe-relative", "safe-relative-variant", "escape-relative", "non-python", "wrong-kind"],
)
def test_uv_resource_trampoline_accepts_safe_relative_and_rejects_unsafe(
    tmp_path, monkeypatch, kind, py_path, should_accept,
):
    from qb_cubie.arenas import _relocation_win32

    base = tmp_path / "base"
    clone = tmp_path / "clone"
    (base / "Scripts").mkdir(parents=True)
    (clone / "Scripts").mkdir(parents=True)
    launcher = clone / "Scripts" / "tool.exe"
    launcher.write_bytes(b"MZ" + b"\x00" * 64)

    calls: list[tuple] = []
    updated: dict[str, bytes] = {}
    fake_lib = _make_fake_resource_kernel32(
        {"UV_TRAMPOLINE_KIND": kind, "UV_PYTHON_PATH": py_path},
        calls,
        updated,
    )
    monkeypatch.setattr(_relocation_win32, "_resource_kernel32", lambda: fake_lib)

    if should_accept:
        _relocation.relocate_scripts(base, clone)
        assert not any(call[0] == "BeginUpdateResourceW" for call in calls)
        assert updated == {}
    else:
        with pytest.raises(RuntimeError, match="Unsupported console entry point"):
            _relocation.relocate_scripts(base, clone)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows uv launcher execution")
def test_windows_native_cowsay_launcher_runs_from_clone():
    def invoke_cowsay() -> dict[str, str]:
        import shutil
        import subprocess
        import sys
        from pathlib import Path

        exe = shutil.which("cowsay")
        assert exe is not None
        res = subprocess.run([exe, "-t", "cubie"], capture_output=True, text=True, encoding="utf-8", check=True)
        return {"exe": exe, "stdout": res.stdout, "prefix": sys.prefix}

    trace = EBT(
        arena=PyVenv(str(COWSAY_BASE), codec=PickleCodec()),
        target=invoke_cowsay,
        pre=WorldState(),
        post=WorldState(
            returns=lambda obs: (
                Path(obs["exe"]).resolve().is_relative_to(Path(obs["prefix"]).resolve())
                and "cubie" in obs["stdout"]
            )
        ),
        reporter=None,
    ).run()
    assert trace.evaluation is True


# ========== E3-A: CROSS-PLATFORM POSIX DIFF NORMALIZATION =============================================================


def test_ebt_generate_diff_normalizes_windows_path_keys(tmp_path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_a.write_text("one", encoding="utf-8")
    file_b.write_text("two", encoding="utf-8")

    exp_missing = {PureWindowsPath("a\\b"): file_a, PureWindowsPath("nested\\report.bin"): file_a}
    act_unexp = {PureWindowsPath("extra\\item.txt"): file_a, PureWindowsPath("nested\\report.bin"): file_b}
    diff = EBT._generate_diff(exp_missing, act_unexp)
    assert diff == {
        "missing": ["a/b"],
        "unexpected": ["extra/item.txt"],
        "modified": ["nested/report.bin"],
    }


def test_reporter_summarize_fs_diffs_normalizes_backslashes():
    changes, errors = PytestReporter._summarize_fs_diffs(
        {
            "out\\2026": {"modified": ["sub\\report.csv"], "missing": ["gone\\file.txt"]},
            "bad\\dir": {"error": "missing"},
        }
    )
    assert changes == {
        "missing": ["out/2026/gone/file.txt"],
        "modified": ["out/2026/sub/report.csv"],
        "unexpected": [],
    }
    assert errors == ["      Error: bad/dir: missing"]


# ========== W9 & W10: HYDRATION BACKSLASHES, PROVISION CLEANUP & UTF-8 SUBPROCESS HYGIENE =============================


def test_hydration_normalize_fs_trims_trailing_backslashes():
    mapping = _hydration.normalize_fs([r"folder\\"], "fs")
    assert mapping == {"folder": r"folder\\"}


def test_requirements_inspect_uses_utf8_with_replace(tmp_path, monkeypatch):
    seen_kwargs: list[dict] = []

    def fake_run(cmd, **kwargs):
        seen_kwargs.append(kwargs)
        return subprocess.CompletedProcess(cmd, 0, stdout='{"environment": {}, "distributions": [], "is_venv": true}', stderr="")

    monkeypatch.setattr(_requirements.subprocess, "run", fake_run)
    snap = _requirements._inspect_environment(tmp_path / "Scripts" / "python.exe")
    assert snap["is_venv"] is True
    assert seen_kwargs[0]["encoding"] == "utf-8"
    assert seen_kwargs[0]["errors"] == "replace"


def test_provision_script_cleans_readonly_incomplete_venv(tmp_path):
    script_path = PROJECT_ROOT / "scripts" / "provision_test_arenas.py"
    spec = importlib.util.spec_from_file_location("cubie_provision_under_test", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    incomplete = tmp_path / "incomplete"
    locked = incomplete / "locked"
    locked.mkdir(parents=True)
    ro_file = locked / "ro.txt"
    ro_file.write_text("locked", encoding="utf-8")
    ro_file.chmod(0o444)
    locked.chmod(0o555)
    try:
        module._remove_incomplete_venv(incomplete)
        assert not incomplete.exists()
    finally:
        if locked.exists():
            locked.chmod(0o755)
        if ro_file.exists():
            ro_file.chmod(0o644)


def test_arena_builder_decodes_non_utf8_stderr_without_crash(tmp_path, monkeypatch):
    def fail_uv(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr=b"\xffbad-utf8\xfe")

    monkeypatch.setattr(pyvenv.subprocess, "run", fail_uv)
    with pytest.raises(RuntimeError, match="ArenaBuilder failed to create venv"):
        ArenaBuilder(tmp_path / "new_env").build()
