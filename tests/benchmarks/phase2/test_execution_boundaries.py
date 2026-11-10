"""Exercise runtime boundaries beyond the original phase-two acceptance cases."""

import json
import re
import subprocess
import tomllib
from pathlib import Path

from ..contracts import accepted, edit_json, rejected
from .conftest import configure_fake, initialize_smoke


def output_path(suite):
    return suite.parent / tomllib.loads(suite.read_text(encoding="utf-8"))["output"]


def test_exhausted_tool_budget_is_reported(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    text = smoke_suite.read_text(encoding="utf-8")
    smoke_suite.write_text(re.sub(r"(?m)^tool_calls = .*", "tool_calls = 1", text), encoding="utf-8")
    configure_fake(smoke_suite, "reference", "developer_agent")
    accepted(public_api("run_suite"), smoke_suite, expected=lambda result: all(
        r["status"] == "budget_exceeded" and r["quality_passed"] is False for r in result["runs"]))


def test_unsupported_adapter_is_rejected_before_results(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    config = tomllib.loads(smoke_suite.read_text(encoding="utf-8"))
    agent = smoke_suite.parent / config["agents"][0]
    agent.write_text(agent.read_text(encoding="utf-8").replace("builtin:fake", "external-command"), encoding="utf-8")
    rejected(public_api("run_suite"), smoke_suite, match="agent.command")
    assert not output_path(smoke_suite).exists()


def test_archived_phase_snapshots_reproduce_actual_test_outcomes(execute, tmp_path):
    result = execute(benchmark="developer_agent")
    root = Path(result["output"])
    for run in result["runs"]:
        for phase in run["phases"][1:]:
            observation = json.loads((root / phase["evidence"][0]).read_text(encoding="utf-8"))
            command = ["--junitxml=" + str(tmp_path / "replay.xml") if arg.startswith("--junitxml=") else arg
                       for arg in observation["command"]]
            snapshot = root / phase["snapshot"]
            replay = subprocess.run(command, cwd=snapshot, capture_output=True, text=True,
                                    timeout=15, check=False, env={"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
            assert replay.returncode == observation["returncode"] == (1 if phase["phase"] == "red" else 0)


def test_rbt_results_are_recorded_without_private_field_access(execute):
    result = execute(benchmark="review_agent")
    decisions = []
    for run in result["runs"]:
        record = Path(run["workspace"]).parent / "rbt.json"
        data = json.loads(record.read_text(encoding="utf-8"))
        decisions.append(data["passed"])
        assert data["report"]["run_id"] == run["run_id"]
        assert run["quality_passed"] is True
    assert sorted(decisions) == [False, True]


def test_paired_profile_executes_ebt_and_pytest_tests(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    text = smoke_suite.read_text(encoding="utf-8").replace('profile = "agent-evaluation"', 'profile = "cubie-vs-pytest"')
    smoke_suite.write_text(text, encoding="utf-8")
    configure_fake(smoke_suite, "reference", "developer_agent")
    result = accepted(public_api("run_suite"), smoke_suite, expected=lambda value: all(
        r["quality_passed"] and r["process_passed"] for r in value["runs"]))
    assert {run["condition"] for run in result["runs"]} == {"cubie", "pytest"}
    for run in result["runs"]:
        test = (Path(run["workspace"]) / "tests/test_project.py").read_text(encoding="utf-8")
        assert ("EBT(" in test) is (run["condition"] == "cubie")


def test_results_cannot_be_written_inside_scenario_material(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    text = smoke_suite.read_text(encoding="utf-8").replace('output = "../results"',
        'output = "../scenarios/smoke/scenarios/index-initial/visible/results"')
    smoke_suite.write_text(text, encoding="utf-8")
    rejected(public_api("run_suite"), smoke_suite, match="output")
    assert not output_path(smoke_suite).exists()


def test_missing_independent_criterion_is_infrastructure_failure(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    configure_fake(smoke_suite, "reference", "developer_agent")
    acceptance = smoke_suite.parent.parent / "scenarios/smoke/scenarios/index-initial/evaluator/acceptance.py.txt"
    text = acceptance.read_text(encoding="utf-8").replace("def test_copies(", "def test_omitted(")
    acceptance.write_text(text, encoding="utf-8")
    accepted(public_api("run_suite"), smoke_suite, expected=lambda result: all(
        r["status"] == "infrastructure_error" and not r["quality_passed"] for r in result["runs"]))


def test_global_time_limit_marks_remaining_attempts_not_started(smoke_suite, public_api, monkeypatch):
    from qb_cubie.benchmarks import runner

    initialize_smoke(public_api, smoke_suite)
    ticks = iter([0])
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(ticks, 1000))
    result = accepted(public_api("run_suite"), smoke_suite, expected=lambda value: all(
        r["status"] == "not_started" and not r["quality_passed"] for r in value["runs"]))
    assert len(result["runs"]) == 3
    assert all(r["tool_calls"] == 0 for r in result["runs"])


def test_acceptance_material_cannot_be_exported_to_agent(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    base = smoke_suite.parent.parent / "scenarios/smoke/scenarios/index-initial"
    (base / "visible/private.py.txt").write_text("def test_leak():\n    assert True\n", encoding="utf-8")
    edit_json(base / "evaluator/reference.json", lambda data: data.update(acceptance_tests="visible/private.py.txt"))
    rejected(public_api("run_suite"), smoke_suite, match="acceptance_tests")
    assert not output_path(smoke_suite).exists()
