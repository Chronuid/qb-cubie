"""Executable regression contracts for BUG-001 (PyVenv workspace isolation)."""

import os
import sys
import tempfile
import venv
from pathlib import Path

import pytest

from qb_cubie import CloudpickleCodec, EBT, MSGspecCodec, PickleCodec, PyVenv, WorldState
from qb_cubie.arenas._requirements import _environment_python

EMPTY_BASE = "tests/.arenas/empty_venv"
CODECS = [PickleCodec, MSGspecCodec, CloudpickleCodec]
CODEC_IDS = ["pickle", "msgspec", "cloudpickle"]


def _write_workspace_file(name: str, content: str) -> str:
    """Create a workspace file inside the active arena without importing workspace modules."""
    Path(name).write_text(content, encoding="utf-8")
    return "ok"


def _inspect_runtime() -> dict[str, object]:
    """Capture child CWD, sys.path, PYTHONPATH, and _cubie_phantom module cache state."""
    return {
        "cwd": str(Path.cwd()),
        "sys_path": list(sys.path),
        "pythonpath": os.environ.get("PYTHONPATH", ""),
        "has_phantom_mod": "_cubie_phantom" in sys.modules,
    }


def _raise_zero_division() -> int:
    """Raise an ordinary ZeroDivisionError inside the arena target."""
    return 1 // 0


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_pre_fs_ipc_in_is_not_overwritten(tmp_path: Path, codec_cls) -> None:
    """K1: pre.fs files named ipc_in<suffix> must reach target and post.fs unaltered."""
    codec = codec_cls()
    filename = f"ipc_in{codec.file_suffix}"
    source = tmp_path / "source.bin"
    source.write_bytes(b"abc")
    expected_ref = tmp_path / "ref"
    expected_ref.mkdir()
    (expected_ref / filename).write_bytes(b"abc")

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec),
        target="os.path:getsize",
        pre=WorldState(args=(filename,), fs={filename: str(source)}),
        post=WorldState(returns=3, fs={filename: str(source), ".": str(expected_ref)}),
    ).run()


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_pre_fs_ipc_out_is_preserved_after_execute(tmp_path: Path, codec_cls) -> None:
    """K2: pre.fs files named ipc_out<suffix> must survive execute() and teardown of IPC files."""
    codec = codec_cls()
    filename = f"ipc_out{codec.file_suffix}"
    source = tmp_path / "source.bin"
    source.write_bytes(b"hello")
    expected_ref = tmp_path / "ref"
    expected_ref.mkdir()
    (expected_ref / filename).write_bytes(b"hello")

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec),
        target="os.path:getsize",
        pre=WorldState(args=(filename,), fs={filename: str(source)}),
        post=WorldState(returns=5, fs={filename: str(source), ".": str(expected_ref)}),
    ).run()


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_pre_fs_cubie_phantom_is_preserved_and_importable_with_decontams(tmp_path: Path, codec_cls) -> None:
    """K3+K6: User _cubie_phantom.py in pre.fs stays intact and importable even with decontams active."""
    user_phantom = tmp_path / "_cubie_phantom.py"
    user_phantom.write_text('USER_MARKER = "workspace-phantom"\n', encoding="utf-8")
    probe_file = tmp_path / "probe_mod.py"
    probe_file.write_text(
        "import blocked_dep\n"
        "import _cubie_phantom\n\n"
        "def run():\n"
        "    return _cubie_phantom.USER_MARKER\n",
        encoding="utf-8",
    )

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls(), decontams=["blocked_dep"]),
        target="probe_mod:run",
        pre=WorldState(fs={"_cubie_phantom.py": str(user_phantom), "probe_mod.py": str(probe_file)}),
        post=WorldState(
            returns="workspace-phantom",
            fs={"_cubie_phantom.py": str(user_phantom), "probe_mod.py": str(probe_file)},
        ),
    ).run()


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_decontams_still_enforces_phantom_error_with_user_phantom_file(tmp_path: Path, codec_cls) -> None:
    """K3-Counterprobe: A user _cubie_phantom.py in workspace cannot disable decontams enforcement."""
    user_phantom = tmp_path / "_cubie_phantom.py"
    user_phantom.write_text('USER_MARKER = "workspace-phantom"\n', encoding="utf-8")
    boom_file = tmp_path / "boom_mod.py"
    boom_file.write_text(
        "import blocked_dep\n\n"
        "def run():\n"
        "    return blocked_dep.call()\n",
        encoding="utf-8",
    )

    case = EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls(), decontams=["blocked_dep"]),
        target="boom_mod:run",
        pre=WorldState(fs={"_cubie_phantom.py": str(user_phantom), "boom_mod.py": str(boom_file)}),
        post=WorldState(returns="never"),
        reporter=None,
    )
    with pytest.raises(RuntimeError, match=r"PhantomObject.*blocked_dep\.call"):
        case.run()
    assert case.run_trace is None


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_full_workspace_comparison_matches_empty_reference(tmp_path: Path, codec_cls) -> None:
    """K4: Full-workspace comparison against an empty reference directory succeeds."""
    empty_ref = tmp_path / "empty_ref"
    empty_ref.mkdir()

    trace = EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target="builtins:int",
        pre=WorldState(args=("7",)),
        post=WorldState(returns=7, fs={".": str(empty_ref)}),
    ).run()
    assert trace.evaluation is True
    assert trace.traces[0].diffs is None


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_full_workspace_comparison_detects_unexpected_target_file(tmp_path: Path, codec_cls) -> None:
    """K4-Control: Full-workspace comparison matches exact output and rejects missing expected state."""
    expected_ref = tmp_path / "expected_ref"
    expected_ref.mkdir()
    (expected_ref / "created.txt").write_text("data", encoding="utf-8")
    empty_ref = tmp_path / "empty_ref"
    empty_ref.mkdir()

    pos_trace = EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target=_write_workspace_file,
        pre=WorldState(args=("created.txt", "data")),
        post=WorldState(returns="ok", fs={".": str(expected_ref)}),
    ).run()
    assert pos_trace.evaluation is True

    neg_trace = EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target=_write_workspace_file,
        pre=WorldState(args=("created.txt", "data")),
        post=WorldState(returns="ok", fs={".": str(empty_ref)}),
        expect=False,
    ).run()
    assert neg_trace.evaluation is True


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_workspace_directory_listing_contains_only_hydrated_files(tmp_path: Path, codec_cls) -> None:
    """K4-CWD: os.listdir('.') sees exclusively hydrated workspace entries without arena artifacts."""
    alpha = tmp_path / "alpha.txt"
    alpha.write_text("a", encoding="utf-8")
    sub_dir = tmp_path / "sub_src"
    sub_dir.mkdir()
    (sub_dir / "beta.txt").write_text("b", encoding="utf-8")

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target="os:listdir",
        pre=WorldState(args=(".",), fs={"alpha.txt": str(alpha), "sub": str(sub_dir)}),
        post=WorldState(returns=lambda entries: sorted(entries) == ["alpha.txt", "sub"]),
    ).run()


@pytest.mark.parametrize("mode", ["file", "dir"])
@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_pre_fs_dotvenv_file_and_directory_stay_isolated_from_arena_venv(
    tmp_path: Path, codec_cls, mode: str,
) -> None:
    """K5: pre.fs '.venv' files and trees stay inside workspace without touching virtual_path."""
    host_file = tmp_path / "payload.txt"
    host_file.write_text("user-venv-content", encoding="utf-8")
    dest = ".venv" if mode == "file" else ".venv/user.txt"

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target="os.path:isfile",
        pre=WorldState(args=(dest,), fs={dest: str(host_file)}),
        post=WorldState(returns=True, fs={dest: str(host_file)}, arena=PyVenv(EMPTY_BASE)),
    ).run()


@pytest.mark.parametrize(
    "shadow_name",
    ["pickle.py", "msgspec.py", "cloudpickle.py", "importlib.py", "_cubie_phantom.py"],
)
@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_workspace_modules_cannot_shadow_codec_transport(tmp_path: Path, codec_cls, shadow_name: str) -> None:
    """K6: Workspace files matching transport/stdlib names never shadow the PyVenv runner."""
    shadow_file = tmp_path / shadow_name
    shadow_file.write_text('raise RuntimeError("TRANSPORT_SHADOWED")\n', encoding="utf-8")

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target="builtins:int",
        pre=WorldState(args=("42",), fs={shadow_name: str(shadow_file)}),
        post=WorldState(returns=42, fs={shadow_name: str(shadow_file)}),
    ).run()


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_empty_sys_path_entry_cannot_reintroduce_workspace_shadowing(
    tmp_path: Path, monkeypatch, codec_cls,
) -> None:
    """K6+PYTHONPATH: Filtering '' and '.' from host sys.path blocks implicit CWD precedence."""
    shadow_map = {
        PickleCodec: "pickle.py",
        MSGspecCodec: "msgspec.py",
        CloudpickleCodec: "cloudpickle.py",
    }
    shadow_name = shadow_map[codec_cls]
    codec_shadow = tmp_path / shadow_name
    codec_shadow.write_text('raise RuntimeError("SHADOWED_VIA_PYTHONPATH")\n', encoding="utf-8")
    phantom_shadow = tmp_path / "_cubie_phantom.py"
    phantom_shadow.write_text('raise RuntimeError("PHANTOM_SHADOWED")\n', encoding="utf-8")
    monkeypatch.setattr(sys, "path", ["", ".", *sys.path])

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target="builtins:int",
        pre=WorldState(
            args=("9",),
            fs={shadow_name: str(codec_shadow), "_cubie_phantom.py": str(phantom_shadow)},
        ),
        post=WorldState(
            returns=9,
            fs={shadow_name: str(codec_shadow), "_cubie_phantom.py": str(phantom_shadow)},
        ),
    ).run()


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_ipc_dir_is_removed_from_child_sys_path_and_pythonpath(codec_cls) -> None:
    """Bootstrap detaches _cubie_phantom and IPC directory from child sys.path and PYTHONPATH."""
    def check_runtime(data: dict) -> bool:
        cwd = Path(data["cwd"]).resolve()
        sys_path = data["sys_path"]
        pythonpath_entries = [p for p in data["pythonpath"].split(os.pathsep) if p]
        no_empty_entries = all(bool(entry) and entry != "." for entry in sys_path)
        no_ipc_in_sys_path = all(
            entry and not (Path(entry) / "_cubie_phantom.py").exists() for entry in sys_path
        )
        no_ipc_in_pythonpath = all(
            not (Path(entry) / "_cubie_phantom.py").exists() for entry in pythonpath_entries
        )
        return (
            data["has_phantom_mod"] is False
            and bool(sys_path)
            and Path(sys_path[0]).resolve() == cwd
            and no_empty_entries
            and no_ipc_in_sys_path
            and no_ipc_in_pythonpath
        )

    EBT(
        arena=PyVenv(EMPTY_BASE, codec=codec_cls()),
        target=_inspect_runtime,
        post=WorldState(returns=check_runtime),
    ).run()


@pytest.mark.parametrize("codec_cls", CODECS, ids=CODEC_IDS)
def test_repeated_execute_calls_leave_workspace_and_root_clean(tmp_path: Path, monkeypatch, codec_cls) -> None:
    """Lifecycle: Repeated execute() calls clean up per-run ipc_* dirs and leave zero leaks on teardown."""
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))
    src = tmp_path / "keep.txt"
    src.write_text("keep", encoding="utf-8")

    arena = PyVenv(EMPTY_BASE, codec=codec_cls())
    arena.setup(WorldState(fs={"keep.txt": str(src)}))
    try:
        first = arena.execute("os:listdir", (".",), {})
        assert sorted(first) == ["keep.txt"]
        assert sorted(p.name for p in arena._root_path.iterdir()) == [".venv", "workspace"]

        second = arena.execute("os:listdir", (".",), {})
        assert sorted(second) == ["keep.txt"]
        assert sorted(p.name for p in arena._root_path.iterdir()) == [".venv", "workspace"]

        arena.teardown()
        assert arena.workspace_path is None
        assert arena.virtual_path is None
        assert list(scratch.iterdir()) == []
    finally:
        if arena.workspace_path is not None:
            arena.teardown()


@pytest.mark.parametrize("failure_kind", ["hydration-escape", "target-exception", "relocation-error"])
def test_failed_setup_and_target_error_leave_zero_tempdir_leaks(
    tmp_path: Path, monkeypatch, failure_kind: str,
) -> None:
    """Lifecycle: Failures during hydration, relocation, or execution leave zero directories in tempdir."""
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))

    if failure_kind == "hydration-escape":
        src = tmp_path / "payload.txt"
        src.write_text("escape", encoding="utf-8")
        arena = PyVenv(EMPTY_BASE, codec=PickleCodec())
        case = EBT(
            arena=arena,
            target="builtins:int",
            pre=WorldState(args=("1",), fs={"../.venv/escape.txt": str(src)}),
            reporter=None,
        )
        with pytest.raises(ValueError, match="\\.\\./\\.venv/escape\\.txt"):
            case.run()
    elif failure_kind == "target-exception":
        arena = PyVenv(EMPTY_BASE, codec=PickleCodec())
        case = EBT(arena=arena, target=_raise_zero_division, reporter=None)
        with pytest.raises(RuntimeError, match="ZeroDivisionError"):
            case.run()
    else:
        base = tmp_path / "bad_base"
        venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(base)
        launcher = _environment_python(base).parent / "native.exe"
        launcher.write_bytes(b"dummy")
        if os.name == "posix":
            launcher.chmod(0o755)
        arena = PyVenv(str(base), codec=PickleCodec())
        case = EBT(arena=arena, target="builtins:int", pre=WorldState(args=("1",)), reporter=None)
        with pytest.raises(RuntimeError, match="Unsupported console entry point"):
            case.run()

    assert arena.workspace_path is None
    assert arena.virtual_path is None
    assert list(scratch.iterdir()) == []
