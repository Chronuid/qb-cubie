"""Evaluation and UI acceptance contracts extending the 180702 pilot series.

Real backend, execution, pytest, telemetry, report aggregation and monitor JS;
synthetic workspaces and deterministic swegemma/container/model boundaries.
"""

import asyncio
import difflib
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from test_pilot_technical_ebt import LocalSandbox, contract
from testguided_study import backend, execution
from testguided_study.artifacts import read, write
from testguided_study.design import default_design
from testguided_study.iteration import identity
from testguided_study.report import arm
from testguided_study.telemetry import Observer

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def evaluation_attempt(tmp_path, monkeypatch):
    """Replace orchestration ports while keeping evaluation classification real."""
    managers, pristine_exits = [], []
    source = "VALUE = 1\n"
    task = SimpleNamespace(repo="synthetic/pilot", FAIL_TO_PASS=["test_value.py::test_value"],
                           PASS_TO_PASS=[], test_files=["test_value.py"])

    class Manager(LocalSandbox):
        def __init__(self):
            root = tmp_path / f"sandbox-{len(managers)}"
            root.mkdir()
            super().__init__(root, False)
            self.env["PYTHONDONTWRITEBYTECODE"] = "1"
            (self.tree / "module.py").write_text(source)
            (self.tree / "conftest.py").write_text("from module import VALUE\n")
            (self.tree / "test_value.py").write_text("from module import VALUE\ndef test_value(): assert VALUE == 1\n")
            self.cleaned = False
            managers.append(self)

        def start(self):
            return self

        def cleanup_all(self):
            self.cleaned = True

        def exec(self, sandbox, cmd, *, timeout):
            if cmd == "SIMULATED_VERIFIER_TIMEOUT":
                return SimpleNamespace(exit_code=124, stdout="", stderr="verifier timed out", timed_out=True)
            if cmd == "SIMULATED_CONTAINER_DISCONNECT":
                raise ConnectionError("Synthetic evaluator connection lost")
            return super().exec(sandbox, cmd, timeout=timeout)

    monkeypatch.setattr(backend, "manager", lambda *_: Manager())
    monkeypatch.setattr(backend, "task_for", lambda *_: task)
    monkeypatch.setattr(backend, "prepare", lambda *_: None)
    monkeypatch.setattr(backend, "harness_config", lambda *_: SimpleNamespace())
    # swegemma is optional on the host. Its entry point is the replaced port;
    # backend.evaluate itself and the verifier's pytest subprocess remain real.
    for name in ("swegemma", "swegemma.harness", "swegemma.harness.verification"):
        module = ModuleType(name)
        module.__path__ = []
        monkeypatch.setitem(sys.modules, name, module)
    verifier = sys.modules["swegemma.harness.verification"]
    verifier.strip_protected_files_from_patch = lambda patch, **_: patch

    def run(scenario):
        replacement = {
            "syntax": "VALUE = (\n",
            "indentation": "if True:\n    VALUE = 1\n  VALUE = 2\n",
            "missing_import": "import missing_evaluator_dependency\nVALUE = 1\n",
            "assertion": "VALUE = 2\n",
        }.get(scenario, source)
        submitted = "".join(difflib.unified_diff(source.splitlines(True), replacement.splitlines(True),
                                                 fromfile="a/module.py", tofile="b/module.py"))

        async def verify_task(mgr, config, evaluated_task, snapshot, *, agent_patch, start_time):
            def pytest_command(extra=""):
                report = f"/tmp/_swegemma_junit_{uuid.uuid4().hex}.xml"
                return ("cd /workspace && PYTHONPATH=/workspace PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "
                        "python3 -s -m pytest test_value.py " + extra + " --junitxml=" + report + " -q")

            baseline = mgr.exec(mgr, pytest_command(), timeout=20)
            pristine_exits.append(baseline.exit_code)
            if agent_patch:
                applied = await asyncio.to_thread(subprocess.run, ["git", "apply", "-"],
                                                  cwd=mgr.tree, input=agent_patch,
                                                  capture_output=True, text=True, timeout=5, check=False)
                assert applied.returncode == 0, applied.stderr
            if scenario == "timeout":
                result = mgr.exec(mgr, "SIMULATED_VERIFIER_TIMEOUT", timeout=1)
            elif scenario == "container_error":
                result = mgr.exec(mgr, "SIMULATED_CONTAINER_DISCONNECT", timeout=1)
            else:
                result = mgr.exec(mgr, pytest_command("--invalid-pilot-option" if scenario == "bad_option" else ""), timeout=20)
            return SimpleNamespace(resolved=result.exit_code == 0, test_exit_code=result.exit_code,
                                   test_output=result.stdout + result.stderr, error=None, duration_seconds=0.1)

        verifier.verify_task = verify_task
        root = tmp_path / "study"
        root.mkdir()
        row = {"run_id": "0004", "pair_id": "0002", "task_id": "example", "mode": "cubie", "seed": 42}
        write(root / "schedule.json", [row])
        write(root / "tasks.json", [{"id": "example", "snapshot": "unused-snapshot.tar.gz"}])
        guides = {"cubie": "Synthetic framework guide"}
        write(root / "guides.json", guides)
        design = default_design("cubie", guides)
        write(root / "designs/cubie.json", {"design": design, "identity": identity(design)})
        config = {"study_id": "evaluation-contract", "budgets": {"command_seconds": 20, "verification_seconds": 20,
                                                                  "wall_seconds": 900}}
        images = {mode: {"image_id": mode} for mode in ("cubie", "evaluator")}
        monkeypatch.setattr(execution, "ready", lambda _: (config, {"images": images}))
        monkeypatch.setattr(execution, "develop", lambda *args, **kwargs: {"status": "stalled", "patch": submitted})
        observer = Observer(root)
        execution.run(root, observer)
        result = read(root / "runs/0004/result.json")
        return result, observer.state, arm([result]), managers, pristine_exits, root

    return run


@pytest.mark.parametrize("scenario,exit_code,resolved", [
    ("syntax", 4, False), ("indentation", 4, False), ("missing_import", 4, False),
    ("assertion", 1, False), ("pass", 0, True),
])
def test_a12_agent_caused_import_failure_counts_as_unsolved_through_report(evaluation_attempt, scenario, exit_code, resolved):
    def observe():
        result, state, summary, managers, pristine, root = evaluation_attempt(scenario)
        evaluation = result.get("evaluation", {})
        archived = read(root / "runs/0004/evaluation/result.json")
        return (pristine, evaluation.get("test_exit_code"), evaluation.get("available"), result["resolved"],
                state["completed_runs"], state["failed_runs"], state["unavailable_runs"],
                summary["available"], summary["unavailable"], summary["resolved"],
                archived == evaluation, all(m.cleaned for m in managers))

    contract(observe, ([0], exit_code, True, resolved, 1, int(not resolved), 0, 1, 0, int(resolved), True, True))


@pytest.mark.parametrize("scenario", ["bad_option", "timeout", "container_error"])
def test_a13_verifier_failures_remain_unavailable_and_are_cleaned_up(evaluation_attempt, scenario):
    def observe():
        result, state, summary, managers, pristine, _ = evaluation_attempt(scenario)
        evaluation = result.get("evaluation", {})
        evidence = (evaluation.get("test_exit_code") == 4 if scenario == "bad_option" else
                    evaluation.get("observation") == "timeout" if scenario == "timeout" else
                    "Synthetic evaluator connection lost" in result.get("error", ""))
        return (pristine, result["resolved"], state["completed_runs"], state["failed_runs"],
                state["unavailable_runs"], summary["available"], summary["unavailable"],
                evidence, all(m.cleaned for m in managers))

    contract(observe, ([0], None, 1, 0, 1, 0, 1, True, True))


def monitor_states(states):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required to execute the actual monitor JavaScript")
    result = subprocess.run([
        node, str(Path(__file__).parent / "fixtures/pilot_outcomes.cjs"),
        str(ROOT / "experiments/testguided-study/testguided_study/monitor.html"),
    ], input=json.dumps(states), check=True, capture_output=True, text=True, timeout=10)
    return json.loads(result.stdout)


def monitor_state(status, resolved, *, completed=True):
    return {"state": "model_wait" if completed else "evaluating", "phase": "running", "total_runs": 2,
            "completed_runs": int(completed), "unavailable_runs": int(completed and resolved is None),
            "failed_runs": int(resolved is False), "resolved_runs": int(resolved is True),
            "active": {"run_id": "0005" if completed else "0004", "operation": "model" if completed else "evaluation"},
            "runs": [{"run_id": "0004", "task_id": "example", "mode": "cubie", "status": status,
                      "resolved": resolved, **({"total_seconds": 601.17} if completed else {})}],
            "events": [], "agent": {}}


@pytest.mark.parametrize("status", [
    "stalled", "submitted", "context_budget", "invalid_output", "wall_budget",
    "model_budget", "tool_budget", "infrastructure_error", "unavailable",
])
def test_a14_finished_attempt_with_missing_evaluation_is_never_still_open(status):
    def observe():
        view = monitor_states([monitor_state(status, None)])[0]
        return view["result"], view["elapsed"], view["unavailable"]

    contract(observe, ("Nicht verfügbar", "10:01", "1"))


@pytest.mark.parametrize("status,resolved,completed,label", [
    ("pending", None, False, "—"), ("running", None, False, "Noch offen"),
    ("stalled", False, True, "Nicht gelöst"), ("submitted", True, True, "Gelöst"),
])
def test_a15_pending_running_and_known_results_remain_distinguishable(status, resolved, completed, label):
    contract(lambda: monitor_states([monitor_state(status, resolved, completed=completed)])[0]["result"], label)


def test_a16_monitor_updates_from_evaluation_to_unavailable_to_definite_failure():
    def observe():
        views = monitor_states([
            monitor_state("running", None, completed=False),
            monitor_state("stalled", None),
            monitor_state("stalled", False),
        ])
        return ([view["result"] for view in views], [view["unavailable"] for view in views],
                [view["failed"] for view in views])

    contract(observe, (["Noch offen", "Nicht verfügbar", "Nicht gelöst"], ["0", "1", "0"], ["0", "0", "1"]))
