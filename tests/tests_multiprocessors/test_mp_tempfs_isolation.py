"""CWD and relative-path isolation through EBT's real process backends.

Unlike threads, workers have separate CWDs. These contracts should therefore
pass, including when a worker is reused after TempFS changes its directory.
"""

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from pathlib import Path

import pytest

from src.qb_cubie import EBT, TempFS, WorldState, multiprocessors


@pytest.fixture(params=["pickle", "loky"])
def backend(request, monkeypatch):
    if request.param == "loky" and not multiprocessors.LOKY_AVAILABLE:
        pytest.skip("Loky is not installed")
    # Bound the real pools and keep both concurrent tasks in separate chunks.
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 2)
    # Spawn avoids forking a host that has a CWD observer thread running.
    monkeypatch.setattr(
        multiprocessors,
        "ProcessPoolExecutor",
        partial(ProcessPoolExecutor, mp_context=multiprocessing.get_context("spawn")),
    )
    processor_type = {
        "pickle": multiprocessors.PickleProcessor,
        "loky": multiprocessors.LokyProcessor,
    }[request.param]
    return request.param, processor_type()


def _make_engine(backend, target, pre, post, arena=None):
    name, processor = backend
    if name == "loky":
        # Exercise the actual lambda/closure routing condition for Loky.
        predicate = post.returns
        post.returns = lambda actual: predicate(actual)
    engine = EBT(
        target=target,
        arena=arena,
        pre=pre,
        post=post,
        multiprocessing=True,
    )
    # A fallback must not make a failed backend look successful.
    engine.MULTIPROCESSORS = [processor]
    assert processor.check_condition(engine.pre, engine.post)
    return engine


def _overlapping_file_operations(label, barrier, ready, release):
    workspace = Path.cwd()
    Path("output.txt").write_text(label, encoding="utf-8")
    # Both workers must be inside their TempFS targets before either reads.
    barrier.wait(timeout=20)
    ready.set()
    if not release.wait(timeout=20):
        raise TimeoutError("Host did not observe overlapping TempFS workers")
    return {
        "pid": os.getpid(),
        "workspace": str(workspace),
        "label": label,
        "read": Path("marker.txt").read_text(encoding="utf-8"),
        "written": Path("output.txt").read_text(encoding="utf-8"),
        "cwd_stable": Path.cwd() == workspace,
    }


def _isolated_file_result(actual):
    return (
        actual["read"] == actual["label"]
        and actual["written"] == actual["label"]
        and actual["cwd_stable"]
    )


def _observe_host_cwd(ready, release):
    try:
        if not ready.wait(timeout=20):
            raise TimeoutError("TempFS workers did not overlap")
        return Path.cwd()
    finally:
        release.set()


def test_overlapping_processes_isolate_relative_io_and_host_cwd(backend, tmp_path):
    original = Path.cwd()
    parent_pid = os.getpid()
    sources = {}
    for label in ("A", "B"):
        source = tmp_path / f"{label}.txt"
        source.write_text(label, encoding="utf-8")
        sources[label] = source

    # Spawn keeps manager startup independent of inherited interpreter state.
    with multiprocessing.get_context("spawn").Manager() as manager:
        barrier = manager.Barrier(2)
        ready, release = manager.Event(), manager.Event()
        engine = _make_engine(
            backend,
            target=_overlapping_file_operations,
            arena=TempFS(),
            pre=[
                WorldState(
                    args=(label, barrier, ready, release),
                    fs={"marker.txt": str(source)},
                )
                for label, source in sources.items()
            ],
            post=WorldState(returns=_isolated_file_result),
        )
        # Only observation uses a thread; EBT targets run in real processes.
        with ThreadPoolExecutor(max_workers=1) as observer:
            host_cwd = observer.submit(_observe_host_cwd, ready, release)
            try:
                trace = engine.run()
            finally:
                ready.set()
                release.set()
            assert host_cwd.result(timeout=5) == original

    assert trace.evaluation is True
    assert len(trace.traces) == 2
    results = [step.outcome.returns for step in trace.traces]
    assert len({result["pid"] for result in results}) == 2
    assert all(result["pid"] != parent_pid for result in results)
    workspaces = [Path(result["workspace"]) for result in results]
    assert len(set(workspaces)) == 2
    assert all(not workspace.exists() for workspace in workspaces)
    assert all(source.read_text(encoding="utf-8") == label for label, source in sources.items())
    assert not (original / "output.txt").exists()
    assert Path.cwd() == original


def _worker_cwd_probe(action, error_name=None):
    """Catch target errors inside the worker so a second task can inspect it."""
    original = Path.cwd()
    result = {
        "pid": os.getpid(),
        "cwd": str(original),
        "restored": True,
        "removed": True,
        "error_propagated": True,
    }
    if action == "observe":
        return result

    class RecordingTempFS(TempFS):
        def setup(self, state):
            super().setup(state)
            self.created_workspace = self.workspace_path

    arena = RecordingTempFS()
    errors = {cls.__name__: cls for cls in (RuntimeError, KeyboardInterrupt, SystemExit)}
    expected_error = errors[error_name]("target interrupted") if error_name else None
    caught_error = None

    def change_directory():
        workspace = Path.cwd()
        (workspace / "nested").mkdir()
        os.chdir("nested")
        if expected_error is not None:
            raise expected_error
        return True

    try:
        EBT(arena=arena, target=change_directory, post=WorldState(returns=True)).run()
    except (RuntimeError, KeyboardInterrupt, SystemExit) as error:
        caught_error = error

    result.update(
        restored=Path.cwd() == original,
        removed=(
            not arena.created_workspace.exists()
            and arena.workspace_path is None
        ),
        error_propagated=(
            caught_error is None if expected_error is None else
            type(caught_error) is type(expected_error) and caught_error.args == expected_error.args
        ),
    )
    return result


def _clean_worker_result(actual):
    return actual["restored"] and actual["removed"] and actual["error_propagated"]


@pytest.mark.parametrize("error_name", [None, "RuntimeError", "KeyboardInterrupt", "SystemExit"],
                         ids=["success", "exception", "keyboard-interrupt", "system-exit"])
def test_reused_worker_restores_cwd_after_tempfs(backend, error_name, monkeypatch):
    original = Path.cwd()
    # One worker forces the observation task to reuse the mutated process.
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 1)
    engine = _make_engine(
        backend,
        target=_worker_cwd_probe,
        pre=[
            WorldState(args=("execute", error_name)),
            WorldState(args=("observe",)),
        ],
        post=WorldState(returns=_clean_worker_result),
    )

    trace = engine.run()

    assert trace.evaluation is True
    assert len(trace.traces) == 2
    first, second = [step.outcome.returns for step in trace.traces]
    assert first["pid"] == second["pid"] != os.getpid()
    assert first["cwd"] == second["cwd"] == str(original)
    assert Path.cwd() == original
