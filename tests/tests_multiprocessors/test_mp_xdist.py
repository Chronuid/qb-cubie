"""Exercise real pytest-xdist workers containing real EBT process pools.

The tests launch their own two-worker pytest session, so normal serial pytest
runs cover both concurrency layers too. Four filesystem rendezvous files prove
that both xdist workers and both EBT pools overlap, without shared CWD assumptions.
"""

import json
import multiprocessing
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import pytest

from src.qb_cubie import EBT, TempFS, WorldState, multiprocessors

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHILD_TEST = """
import os
from pathlib import Path

from tests.tests_multiprocessors.test_mp_xdist import _run_nested_ebt


def test_ebt_pool_inside_xdist_worker(worker_id, monkeypatch):
    assert worker_id != "master"
    _run_nested_ebt(
        os.environ["CUBIE_XDIST_BACKEND"],
        worker_id,
        Path(os.environ["CUBIE_XDIST_SHARED"]),
        monkeypatch,
    )
"""


def _parallel_target(label, shared_root):
    """Keep all four targets active until both process pools have arrived."""
    workspace = Path.cwd()
    Path("output.txt").write_text(label, encoding="utf-8")
    shared = Path(shared_root)
    (shared / f"{label}.ready").touch()
    deadline = time.monotonic() + 30
    while len(list(shared.glob("*.ready"))) < 4:
        if time.monotonic() >= deadline:
            raise TimeoutError("Expected two xdist workers with two EBT processes each")
        time.sleep(0.01)
    return {
        "pid": os.getpid(),
        "xdist_worker": os.environ["PYTEST_XDIST_WORKER"],
        "workspace": str(workspace),
        "label": label,
        "read": Path("input.txt").read_text(encoding="utf-8"),
        "written": Path("output.txt").read_text(encoding="utf-8"),
        "cwd_stable": Path.cwd() == workspace,
    }


def _isolated_result(actual):
    return (
        actual["read"] == actual["label"]
        and actual["written"] == actual["label"]
        and actual["label"].startswith(actual["xdist_worker"] + "-")
        and actual["cwd_stable"]
    )


def _run_nested_ebt(backend_name, worker_id, shared, monkeypatch):
    """Called inside each xdist worker, never in the outer pytest process."""
    original = Path.cwd()
    monkeypatch.setattr(multiprocessors.os, "cpu_count", lambda: 2)
    monkeypatch.setattr(
        multiprocessors,
        "ProcessPoolExecutor",
        partial(ProcessPoolExecutor, mp_context=multiprocessing.get_context("spawn")),
    )
    processor = {
        "pickle": multiprocessors.PickleProcessor,
        "loky": multiprocessors.LokyProcessor,
    }[backend_name]()
    sources = {}
    for suffix in ("A", "B"):
        label = f"{worker_id}-{suffix}"
        source = shared / f"{label}.txt"
        source.write_text(label, encoding="utf-8")
        sources[label] = source

    predicate = _isolated_result
    if backend_name == "loky":
        predicate = lambda actual: _isolated_result(actual)
    engine = EBT(
        arena=TempFS(custom_id=worker_id),
        target=_parallel_target,
        pre=[
            WorldState(args=(label, str(shared)), fs={"input.txt": str(source)})
            for label, source in sources.items()
        ],
        post=WorldState(returns=predicate),
        multiprocessing=True,
    )
    # Isolate the chosen backend so fallback cannot hide a nested-pool failure.
    engine.MULTIPROCESSORS = [processor]
    assert processor.check_condition(engine.pre, engine.post)

    trace = engine.run()

    assert trace.evaluation is True
    assert len(trace.traces) == 2
    results = [step.outcome.returns for step in trace.traces]
    assert len({result["pid"] for result in results}) == 2
    assert all(result["pid"] != os.getpid() for result in results)
    assert all(result["xdist_worker"] == worker_id for result in results)
    assert all(not Path(result["workspace"]).exists() for result in results)
    assert all(source.read_text(encoding="utf-8") == label for label, source in sources.items())
    assert Path.cwd() == original
    assert not (original / "input.txt").exists()
    assert not (original / "output.txt").exists()
    (shared / f"report-{worker_id}.json").write_text(
        json.dumps({"worker_id": worker_id, "pid": os.getpid(), "results": results}),
        encoding="utf-8",
    )


@pytest.mark.parametrize("backend_name", ["pickle", "loky"])
def test_xdist_workers_with_ebt_multiprocessing(backend_name, tmp_path):
    pytest.importorskip("xdist", reason="Install the dev extra for the xdist integration tests")
    if backend_name == "loky" and not multiprocessors.LOKY_AVAILABLE:
        pytest.skip("Loky is not installed")
    original = Path.cwd()
    shared = tmp_path / "shared"
    shared.mkdir()
    child_test = tmp_path / "test_nested_ebt.py"
    child_test.write_text(CHILD_TEST, encoding="utf-8")
    env = os.environ.copy()
    # A parent run may itself use xdist; start an independent nested session.
    for key in list(env):
        if key.startswith("PYTEST_XDIST_") or key in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}:
            env.pop(key)
    env.update({
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join([
            str(PROJECT_ROOT), str(PROJECT_ROOT / "src"), env.get("PYTHONPATH", ""),
        ]),
        "CUBIE_XDIST_BACKEND": backend_name,
        "CUBIE_XDIST_SHARED": str(shared),
    })

    process = subprocess.run(
        [
            sys.executable, "-B", "-m", "pytest", "-q",
            "-p", "xdist.plugin", "-p", "no:cacheprovider",
            "-n", "2", "--dist=each", "--max-worker-restart=0",
            "--confcutdir", str(tmp_path), "--rootdir", str(tmp_path),
            str(child_test),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )

    assert process.returncode == 0, process.stdout + process.stderr
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in shared.glob("report-*.json")]
    assert {report["worker_id"] for report in reports} == {"gw0", "gw1"}
    xdist_pids = {report["pid"] for report in reports}
    assert len(xdist_pids) == 2
    results = [result for report in reports for result in report["results"]]
    ebt_pids = {result["pid"] for result in results}
    assert len(ebt_pids) == 4
    assert ebt_pids.isdisjoint(xdist_pids | {os.getpid()})
    assert len({result["workspace"] for result in results}) == 4
    assert all(not Path(result["workspace"]).exists() for result in results)
    assert len(list(shared.glob("*.ready"))) == 4
    assert Path.cwd() == original
