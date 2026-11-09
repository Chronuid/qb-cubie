"""TempFS lifecycle contracts and regressions for process-wide CWD.

Thread probes coordinate their child targets through files. Separate processes
(including xdist workers) do not share CWD. A fatal target exit must leave the
host CWD intact and still allow workspace cleanup.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from cubie import EBT, TempFS, WorldState


@pytest.fixture(autouse=True)
def restore_host_cwd():
    """Keep even failing regression probes from changing subsequent tests' CWD."""
    original = Path.cwd()
    try:
        yield original
    finally:
        os.chdir(original)


def test_ebt_hydrates_mutates_and_removes_workspace(tmp_path, restore_host_cwd):
    source = tmp_path / "source.txt"
    source.write_text("host content", encoding="utf-8")
    arena = TempFS()

    def mutate(filename, *, content):
        assert Path.cwd() == arena.workspace_path
        assert Path(filename).read_text(encoding="utf-8") == "host content"
        Path(filename).write_text(content, encoding="utf-8")
        return content

    trace = EBT(
        arena=arena,
        target=mutate,
        pre=WorldState(
            args=("nested/input.txt",),
            kwargs={"content": "workspace content"},
            fs={"nested/input.txt": str(source)},
        ),
        post=WorldState(
            returns="workspace content",
            fs={"nested/input.txt": lambda path: path.read_text(encoding="utf-8") == "workspace content"},
        ),
    ).run()

    assert Path.cwd() == restore_host_cwd
    assert source.read_text(encoding="utf-8") == "host content"
    assert not Path(trace.traces[0].outcome.fs).exists()
    assert arena.workspace_path is None


def test_ebt_sequential_states_receive_fresh_workspaces(restore_host_cwd):
    arena = TempFS()

    def write_once(value):
        assert not Path("output.txt").exists()
        Path("output.txt").write_text(value, encoding="utf-8")
        return True

    trace = EBT(
        arena=arena,
        target=write_once,
        pre=[WorldState(args=("first",)), WorldState(args=("second",))],
        post=WorldState(returns=True),
    ).run()

    workspaces = [Path(step.outcome.fs) for step in trace.traces]
    assert len(set(workspaces)) == 2
    assert all(not workspace.exists() for workspace in workspaces)
    assert Path.cwd() == restore_host_cwd


@pytest.mark.parametrize("entrypoint", ["ebt", "run"])
@pytest.mark.parametrize("error_type", [RuntimeError, KeyboardInterrupt, SystemExit])
def test_target_exception_restores_cwd_and_cleans_workspace(
    entrypoint, error_type, restore_host_cwd,
):
    arena = TempFS()
    error = error_type("target interrupted")

    def interrupt():
        assert Path.cwd() == arena.workspace_path
        error.add_note(f"workspace: {Path.cwd()}")
        # Restoration must also work if the target changes directory itself.
        Path("nested").mkdir()
        os.chdir("nested")
        raise error

    with pytest.raises(error_type) as caught:
        if entrypoint == "ebt":
            EBT(arena=arena, target=interrupt).run()
        else:
            arena.run(interrupt, (), {})

    assert caught.value.args == error.args
    assert any("TempFS child traceback" in note for note in caught.value.__notes__)
    assert Path.cwd() == restore_host_cwd
    workspace = next(note.removeprefix("workspace: ") for note in caught.value.__notes__
                     if note.startswith("workspace: "))
    assert not Path(workspace).exists()
    assert arena.workspace_path is None


def test_nested_ebt_restores_outer_then_host_cwd(restore_host_cwd):
    outer = TempFS()
    inner = TempFS()

    def inner_target():
        return Path.cwd() == inner.workspace_path

    def outer_target():
        workspace = Path.cwd()
        trace = EBT(arena=inner, target=inner_target, post=WorldState(returns=True)).run()
        return {"restored": Path.cwd() == workspace, "inner_workspace": trace.traces[0].outcome.fs}

    trace = EBT(arena=outer, target=outer_target,
                post=WorldState(returns=lambda result: result["restored"])).run()

    workspaces = [Path(trace.traces[0].outcome.fs), Path(trace.traces[0].outcome.returns["inner_workspace"])]
    assert len(set(workspaces)) == 2
    assert all(not workspace.exists() for workspace in workspaces)
    assert Path.cwd() == restore_host_cwd


def _wait(path):
    deadline = time.monotonic() + 10
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("TempFS thread probe did not reach the expected phase")
        time.sleep(0.01)


def _probe_overlapping_execution(coordination):
    """Force A-enter, B-enter, A-exit, B-exit and observe reads/writes/restore.

    Workspaces survive both execute calls so a deleted directory cannot mask
    the CWD restoration bug. The harness restores CWD before removing either.
    """
    original = Path.cwd()
    arenas = [TempFS(custom_id="thread_a"), TempFS(custom_id="thread_b")]
    a_entered = coordination / "a_entered"
    b_entered = coordination / "b_entered"
    a_finished = coordination / "a_finished"
    try:
        for arena, label in zip(arenas, ("A", "B")):
            arena.setup(WorldState())
            (arena.workspace_path / "marker.txt").write_text(label, encoding="utf-8")

        def target_a():
            a_entered.touch()
            _wait(b_entered)
            observed = Path("marker.txt").read_text(encoding="utf-8")
            Path("written_by_a.txt").write_text("A", encoding="utf-8")
            return observed

        def execute_a():
            try:
                return arenas[0].execute(target_a, (), {})
            finally:
                a_finished.touch()

        def target_b():
            b_entered.touch()
            _wait(a_finished)

        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(execute_a)
            _wait(a_entered)
            host_cwd_during_execution = Path.cwd()
            future_b = pool.submit(arenas[1].execute, target_b, (), {})
            observed = future_a.result(timeout=10)
            future_b.result(timeout=10)

        return {
            "relative_reads_stay_in_a": observed == "A",
            "relative_writes_stay_in_a": (
                (arenas[0].workspace_path / "written_by_a.txt").exists()
                and not (arenas[1].workspace_path / "written_by_a.txt").exists()
            ),
            "host_cwd_restored": Path.cwd() == original,
            "host_cwd_stable": host_cwd_during_execution == original,
        }
    finally:
        os.chdir(original)
        for arena in arenas:
            if arena.workspace_path is not None:
                arena.teardown()


@pytest.mark.parametrize("contract", [
    "relative_reads_stay_in_a",
    "relative_writes_stay_in_a",
    "host_cwd_restored",
    "host_cwd_stable",
])
def test_overlapping_threads_preserve_workspace_isolation(contract, tmp_path):
    # The probe itself must run without an arena: its two execute calls are the
    # operations under test, and an outer CWD switch would hide host corruption.
    EBT(
        target=_probe_overlapping_execution,
        pre=WorldState(args=(tmp_path,)),
        post=WorldState(returns=lambda observations: observations[contract]),
    ).run()


class RecordingTempFS(TempFS):
    """Remember the parent-created workspace even after teardown clears it."""

    def setup(self, state):
        super().setup(state)
        self.created_workspace = self.workspace_path


@pytest.mark.parametrize("exit_code", [0, 17])
def test_abrupt_target_exit_preserves_host_and_cleans_workspace(exit_code, restore_host_cwd):
    arena = RecordingTempFS()

    def exit_without_result():
        os.chdir("..")
        os._exit(exit_code)

    with pytest.raises(RuntimeError, match=f"TempFS target process exited with code {exit_code}"):
        EBT(arena=arena, target=exit_without_result).run()

    assert Path.cwd() == restore_host_cwd
    assert not arena.created_workspace.exists()
    assert arena.workspace_path is None


def test_targets_and_results_are_copies_across_process_boundary():
    original = []

    def mutate_copy(value):
        value.append("child")
        return os.getpid(), value

    child_pid, result = TempFS().run(mutate_copy, (original,), {})

    assert child_pid != os.getpid()
    assert original == []
    assert result == ["child"]
    assert result is not original


@pytest.mark.parametrize("mode", ["return", "exception"])
def test_unserializable_result_reports_error_and_cleans_workspace(
    mode, restore_host_cwd, tmp_path, monkeypatch,
):
    import tempfile
    from threading import Lock

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    arena = RecordingTempFS()

    def unpicklable_result():
        if mode == "exception":
            error = RuntimeError("unserializable exception")
            error.lock = Lock()
            raise error
        return Lock()

    with pytest.raises(RuntimeError, match="TempFS could not serialize the target result"):
        arena.run(unpicklable_result, (), {})

    assert Path.cwd() == restore_host_cwd
    assert not arena.created_workspace.exists()
    assert arena.workspace_path is None
    assert list(tmp_path.iterdir()) == []


def test_unserializable_input_cleans_workspace(restore_host_cwd, tmp_path, monkeypatch):
    import tempfile
    from threading import Lock

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    arena = RecordingTempFS()
    with pytest.raises(TypeError, match="cannot pickle"):
        arena.run(lambda value: value, (Lock(),), {})

    assert Path.cwd() == restore_host_cwd
    assert not arena.created_workspace.exists()
    assert arena.workspace_path is None
    assert list(tmp_path.iterdir()) == []


def test_process_start_failure_cleans_workspace_and_ipc(tmp_path, monkeypatch, restore_host_cwd):
    import tempfile

    from cubie.arenas import tempfs

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))

    def fail_to_start(*args, **kwargs):
        raise OSError("process could not start")

    monkeypatch.setattr(tempfs.subprocess, "run", fail_to_start)
    arena = RecordingTempFS()
    with pytest.raises(OSError, match="process could not start"):
        arena.run(lambda: True, (), {})

    assert arena.workspace_path is None
    assert list(tmp_path.iterdir()) == []
    assert Path.cwd() == restore_host_cwd


def test_workspace_contains_no_ipc_files_and_cannot_shadow_transport(tmp_path):
    source = tmp_path / "cloudpickle.py"
    source.write_text("raise RuntimeError('transport shadowed')", encoding="utf-8")
    EBT(
        arena=TempFS(),
        target=lambda: sorted(path.name for path in Path.cwd().iterdir()),
        pre=WorldState(fs={"cloudpickle.py": str(source)}),
        post=WorldState(returns=["cloudpickle.py"]),
    ).run()


def test_failed_hydration_cleans_standalone_workspace(tmp_path, restore_host_cwd):
    arena = TempFS()
    with pytest.raises(FileNotFoundError, match="Host path for FS mapping not found"):
        arena.run(lambda: True, (), {}, WorldState(fs={"input.txt": str(tmp_path / "missing")}))

    assert arena.workspace_path is None
    assert Path.cwd() == restore_host_cwd


def test_relative_hydration_uses_host_cwd_while_other_target_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("source.txt").write_text("host content", encoding="utf-8")
    entered, release = tmp_path / "entered", tmp_path / "release"

    def hold_workspace():
        entered.touch()
        _wait(release)

    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(TempFS().run, hold_workspace, (), {})
        try:
            _wait(entered)
            EBT(
                arena=TempFS(),
                target=lambda: Path("input.txt").read_text(encoding="utf-8"),
                pre=WorldState(fs={"input.txt": "source.txt"}),
                post=WorldState(returns="host content"),
            ).run()
            assert Path.cwd() == tmp_path
        finally:
            release.touch()
        running.result(timeout=10)
