"""A real JSONL subprocess must provide verifiable submissions and phases."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from .conftest import ROOT, configure_agent, read_json, traffic, write_suite


def run_external(public_api, root, mode="reference", selection='benchmarks = ["review_agent"]'):
    configure_agent(root, mode)
    return accepted(public_api("run_suite"), write_suite(root, selection), expected=lambda r: bool(r["runs"]))


def test_own_process_reviews_both_variants_without_a_second_agent(external, public_api):
    result = run_external(public_api, external)
    assert len(result["runs"]) == 2
    for run in result["runs"]:
        assert run["status"] == "completed" and run["evaluation_status"] == "complete"
        assert run["quality_passed"] is True and run["agent_kind"] == "process"
        assert run["agent_version"] == "fixture-1"
        assert run["agent_id"] == "own-agent" and run["condition"] == "cubie"
        assert run["usage"] == {"input_tokens": None, "output_tokens": None, "cost": None}
        assert run["model_id"] is None
    assert {r["criterion_results"]["free_threshold"] for r in result["runs"]} == {"pass", "fail"}
    assert len({e["session"] for e in traffic(external) if e["request"]["type"] == "request"}) == 2


def test_process_approval_is_scored_by_independent_evaluator(external, public_api):
    result = run_external(public_api, external, "approve_all")
    runs = {r["scenario_id"]: r for r in result["runs"]}
    assert runs["shop/review-correct"]["quality_passed"] is True
    assert runs["shop/review-boundary"]["quality_passed"] is False
    assert all(r["status"] == "completed" for r in result["runs"])


def test_process_receives_visible_material_and_runner_archives_the_exchange(external, public_api, monkeypatch):
    monkeypatch.setenv("CUBIE_PHASE3_SECRET", "credential-sentinel")
    result = run_external(public_api, external)
    entries = [e for e in traffic(external) if e["request"]["type"] == "request"]
    assert len(entries) == 2 and all(not e["credential_present"] for e in entries)
    for entry in entries:
        assert {"task.md", "shipping.py"} <= set(entry["files"])
        assert not any("evaluator" in name or "reference.json" in name or name.endswith(".py.txt") for name in entry["files"])
    root = Path(result["output"])
    manifest = read_json(root / "manifest.json")
    archived = [root / p for p in manifest["artifact_hashes"]]
    assert any(p.suffix == ".jsonl" and any(json.loads(line).get("type") == "request"
               for line in p.read_text(encoding="utf-8").splitlines()) for p in archived)
    assert any("phase3 fixture diagnostic" in p.read_text(encoding="utf-8") for p in archived if p.suffix == ".log")
    assert all("credential-sentinel" not in p.read_text(encoding="utf-8") for p in archived
               if p.suffix in {".json", ".jsonl", ".log", ".toml", ".md"})


@pytest.mark.parametrize("mode,status", [
    ("invalid_json", "invalid_output"), ("foreign_run", "invalid_output"),
    ("foreign_scenario", "invalid_output"), ("foreign_phase", "invalid_output"),
    ("missing_artifact", "invalid_output"), ("tampered_artifact", "invalid_output"),
    ("traversal", "invalid_output"), ("absolute_artifact", "invalid_output"),
    ("no_evidence", "invalid_output"), ("mutate_source", "invalid_output"),
    ("mutate_task", "invalid_output"), ("crash", "infrastructure_error"), ("eof", "invalid_output"),
])
def test_bad_process_submissions_never_become_quality_success(external, public_api, mode, status):
    result = run_external(public_api, external, mode)
    for run in result["runs"]:
        assert run["status"] == status and run["reason"]
        assert run["evaluation_status"] == "not_evaluated" and run["criterion_results"] == {}
        assert run["quality_passed"] is False
        assert all(m["value"] is None for m in run["metrics"])


def test_developer_process_keeps_one_session_across_observed_phases(external, public_api):
    result = run_external(public_api, external, selection='ids = ["shop/fee-initial"]')
    run, = result["runs"]
    assert run["status"] == "completed" and run["quality_passed"] is True and run["process_passed"] is True
    assert [p["phase"] for p in run["phases"]] == ["test_design", "red", "green", "refactor"]
    assert [p["test_outcome"] for p in run["phases"]][1:] == ["assertion_failure", "passed", "passed"]
    assert len({p["test_tree_sha256"] for p in run["phases"]}) == 1
    entries = [e for e in traffic(external) if e["request"]["type"] == "request"]
    assert [e["request"]["phase"] for e in entries] == ["test_design", "red", "green", "refactor"]
    assert len({e["session"] for e in entries}) == 1


@pytest.mark.parametrize("mode", ["early_implementation", "modify_tests", "red_import_error"])
def test_process_claims_do_not_replace_the_runner_phase_observations(external, public_api, mode):
    run, = run_external(public_api, external, mode, 'ids = ["shop/fee-initial"]')["runs"]
    assert run["process_passed"] is False and run["process_reason"]


def test_wrong_external_implementation_fails_independent_acceptance(external, public_api):
    run, = run_external(public_api, external, "wrong_solution", 'ids = ["shop/fee-initial"]')["runs"]
    assert run["status"] == "completed" and run["evaluation_status"] == "complete"
    assert run["criterion_results"]["fee"] == "fail" and run["quality_passed"] is False


@pytest.mark.parametrize("mode,match", [("wrong_version", "schema_version|version"),
                                       ("missing_capabilities", "capabilit")])
def test_actual_handshake_is_checked_before_any_task_is_sent(external, public_api, mode, match):
    configure_agent(external, mode)
    rejected(public_api("run_suite"), external / "sets/team.toml", match=match)
    entries = traffic(external)
    assert entries and all(e["request"]["type"] == "capabilities" for e in entries)
    assert not (external / "results").exists()


def test_review_only_agent_cannot_be_planned_for_development(external, public_api):
    configure_agent(external, capabilities=["review_output", "wall_time", "cancel", "tool_calls"])
    rejected(public_api("run_suite"), external / "sets/team.toml", match="phased_submission|workspace_changes")
    assert not traffic(external)


def test_timeout_stops_a_blocking_process_with_an_outer_deadline(external, public_api):
    public_api("run_suite")
    configure_agent(external, "hang")
    suite = write_suite(external, 'ids = ["shop/review-correct"]', seconds=0.25)
    code = ('import json,sys; sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2]); '
            'from cubie_benchmarks import run_suite; print(json.dumps(run_suite(sys.argv[3])))')
    process = accepted(lambda: subprocess.run(
        [sys.executable, "-I", "-c", code, str(ROOT / "src"), str(ROOT / "experiments/benchmarks"), str(suite)],
        cwd=external.parent, capture_output=True, text=True, timeout=12, check=False), expected=lambda p: p.returncode == 0)
    run, = json.loads(process.stdout)["runs"]
    assert run["status"] == "agent_timeout" and run["quality_passed"] is False
    assert run["evaluation_status"] == "not_evaluated"
    if os.name == "posix":
        requests = [e for e in traffic(external) if e["request"]["type"] == "request"]
        assert len(requests) == 1
        with pytest.raises(ProcessLookupError):
            os.kill(requests[0]["pid"], 0)
