"""Run real planner, fake adapter and independent evaluators through EBT."""

import json
import socket
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

import qb_cubie

from ..contracts import accepted, rejected
from .conftest import configure_fake, initialize_smoke


def all_completed(result):
    return all(run["status"] == "completed" and run["evaluation_status"] == "complete"
               for run in result["runs"])


def test_reference_smoke_covers_both_benchmarks_with_one_agent(execute):
    result = execute()
    assert all_completed(result)
    assert {r["benchmark"] for r in result["runs"]} == {"review_agent", "developer_agent"}
    assert len({r["agent_id"] for r in result["runs"]}) == 1
    assert all(r["condition"] == "cubie" and r["repetition"] == 1 for r in result["runs"])
    assert all(r["quality_passed"] is True for r in result["runs"])


def test_fake_smoke_needs_no_network_or_provider_credentials(execute, monkeypatch):
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "AZURE_OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    def no_connection(*args, **kwargs):
        raise AssertionError("The deterministic fake smoke must remain offline")

    original_connect = socket.socket.connect

    def offline_connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            no_connection()
        return original_connect(sock, address)

    monkeypatch.setattr(socket.socket, "connect", offline_connect)
    monkeypatch.setattr(socket, "create_connection", no_connection)
    assert all_completed(execute())


@pytest.mark.parametrize("mutant,criterion", [
    ("wrong-return", "returns_none"), ("missing-copy", "copies"),
    ("corrupt-copy", "copies"), ("extra-file", "exact_tree"),
    ("reverse-sort", "sorted_index"),
])
def test_independent_project_acceptance_rejects_faulty_solution(execute, mutant, criterion):
    result = execute("mutant", "developer_agent", mutant)
    assert all_completed(result), "A wrong solution is an evaluated outcome, not a runner error"
    for run in result["runs"]:
        assert run["quality_passed"] is False
        assert run["criterion_results"][criterion] == "fail"
        assert run["evidence"]


@pytest.mark.parametrize("behavior", ["approve_all", "reject_all", "abstain"])
def test_constant_review_decisions_cannot_pass_the_reference_pair(execute, behavior):
    result = execute(behavior, "review_agent")
    assert all_completed(result)
    assert any(r["quality_passed"] is False for r in result["runs"])
    assert all(r["evidence"] for r in result["runs"])
    if behavior == "abstain":
        assert all(r["quality_passed"] is False for r in result["runs"])


def test_repeated_finding_does_not_inflate_recall(execute):
    result = execute("duplicate_findings", "review_agent")
    metrics = [m for r in result["runs"] for m in r["metrics"] if m["name"] == "recall"]
    assert any(m["value"] == 1 for m in metrics)
    assert all(m["value"] is None or 0 <= m["value"] <= 1 for m in metrics)


def test_developer_success_has_observed_red_green_and_frozen_tests(execute):
    result = execute(benchmark="developer_agent")
    for run in result["runs"]:
        assert run["process_passed"] is True
        phases = run["phases"]
        assert [p["phase"] for p in phases] == ["test_design", "red", "green", "refactor"]
        assert phases[1]["test_outcome"] == "assertion_failure"
        assert phases[2]["test_outcome"] == phases[3]["test_outcome"] == "passed"
        assert len({p["test_tree_sha256"] for p in phases}) == 1
        assert all(p["evidence"] for p in phases)


@pytest.mark.parametrize("behavior,outcome", [
    ("missing_red", None), ("red_import_error", "import_error"),
    ("green_failure", "assertion_failure"), ("modify_tests", None),
])
def test_green_claim_without_valid_phase_evidence_fails_process(execute, behavior, outcome):
    result = execute(behavior, "developer_agent")
    for run in result["runs"]:
        assert run["process_passed"] is False
        assert run["process_reason"]
        if outcome:
            phase = "red" if behavior == "red_import_error" else "green"
            assert next(p for p in run["phases"] if p["phase"] == phase)["test_outcome"] == outcome


@pytest.mark.parametrize("behavior,status", [
    ("missing_artifact", "invalid_output"), ("foreign_run", "invalid_output"),
    ("tampered_artifact", "invalid_output"), ("mutate_context", "invalid_output"),
    ("missing_evidence", "invalid_output"),
    ("timeout", "agent_timeout"), ("crash", "infrastructure_error"),
])
def test_unusable_submissions_preserve_execution_failure(execute, behavior, status):
    result = execute(behavior, "review_agent")
    for run in result["runs"]:
        assert run["status"] == status
        assert run["evaluation_status"] == "not_evaluated"
        assert run["quality_passed"] is False
        assert run["criterion_results"] == {}
        assert run["reason"]
        assert all(m["value"] is None for m in run["metrics"])


def test_timeout_is_enforced_by_runner_not_only_reported_by_fake(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    configure_fake(smoke_suite, "hang", "review_agent")
    import cubie_benchmarks

    source = str(Path(qb_cubie.__file__).resolve().parent.parent)
    benchmarks_source = str(Path(cubie_benchmarks.__file__).resolve().parent.parent)
    code = ("import json,sys; sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2]); "
            "from cubie_benchmarks import run_suite; print(json.dumps(run_suite(sys.argv[3])))")
    process = accepted(lambda: subprocess.run(
        [sys.executable, "-I", "-c", code, source, benchmarks_source, str(smoke_suite)],
        capture_output=True, text=True, timeout=15, check=False), expected=lambda p: p.returncode == 0)
    result = json.loads(process.stdout)
    assert all(r["status"] == "agent_timeout" for r in result["runs"])
    assert all(r["quality_passed"] is False for r in result["runs"])


def test_repeated_calls_keep_previous_run_and_use_fresh_workspaces(execute):
    first = execute()
    before = (Path(first["output"]) / "results.json").read_bytes()
    second = execute()
    assert first["run_id"] != second["run_id"] and first["output"] != second["output"]
    assert (Path(first["output"]) / "results.json").read_bytes() == before
    workspaces = [r["workspace"] for result in [first, second] for r in result["runs"]]
    assert len(workspaces) == len(set(workspaces))


def test_config_error_happens_before_creating_results(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    text = smoke_suite.read_text(encoding="utf-8")
    smoke_suite.write_text(text + '\n[select]\nids = ["unknown/scenario"]\n', encoding="utf-8")
    rejected(public_api("run_suite"), smoke_suite, match="unknown/scenario")
    # No run is allowed to begin after failed planning; check the declared output.
    declared = tomllib.loads(smoke_suite.read_text(encoding="utf-8"))["output"]
    assert not (smoke_suite.parent / declared).exists()


def test_init_template_does_not_overwrite_existing_files(smoke_suite, public_api):
    initialize_smoke(public_api, smoke_suite)
    previous = smoke_suite.read_bytes()
    rejected(public_api("init_smoke_suite"), smoke_suite, match="exist|overwrite")
    assert smoke_suite.read_bytes() == previous


def test_template_is_accepted_by_existing_public_planner(smoke_suite, public_api, monkeypatch, tmp_path):
    initialize_smoke(public_api, smoke_suite)
    monkeypatch.chdir(tmp_path)
    accepted(public_api("plan_suite"), smoke_suite, expected=lambda plan: (
        {r["benchmark"] for r in plan["runs"]} == {"review_agent", "developer_agent"}
        and all(r["repetition"] == 1 and r["condition"] == "cubie" for r in plan["runs"])))
