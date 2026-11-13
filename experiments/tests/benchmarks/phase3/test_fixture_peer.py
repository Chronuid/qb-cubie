"""Check reference material and the JSONL peer independently of new product APIs."""

import hashlib
import json
import shutil
import subprocess
import sys

import pytest

from ..contracts import accepted
from .conftest import CAPABILITIES, read_json


@pytest.mark.parametrize("name,decision", [("review-correct", "pass"), ("review-boundary", "fail")])
def test_fixture_peer_produces_a_valid_source_bound_review(external, public_api, tmp_path, name, decision):
    workspace = tmp_path / "visible-only"
    workspace.mkdir()
    scenario = external / "scenarios" / name
    shutil.copyfile(scenario / "visible/shipping.py", workspace / "shipping.py")
    shutil.copyfile(scenario / "task.md", workspace / "task.md")
    request = {"schema_version": 1, "type": "request", "run_id": "fixture-run", "scenario_id": "shop/" + name,
               "benchmark": "review_agent", "phase": "review", "task": (workspace / "task.md").read_text(encoding="utf-8"),
               "workspace": str(workspace), "criteria": ["free_threshold"],
               "output_format": "review_v1", "budgets": {"wall_time_seconds": 10}}
    accepted(public_api("validate_agent_request"), request, expected=request)
    messages = [{"schema_version": 1, "type": "capabilities"}, request]
    process = accepted(lambda: subprocess.run(
        [sys.executable, "-I", "jsonl_agent.py"], cwd=external / "agents",
        input="".join(json.dumps(m) + "\n" for m in messages), capture_output=True, text=True,
        timeout=5, check=False), expected=lambda p: p.returncode == 0)
    handshake, event = map(json.loads, process.stdout.splitlines())
    assert set(handshake["capabilities"]) == set(CAPABILITIES)
    accepted(public_api("validate_agent_event"), event, request, expected=event)
    assert read_json(workspace / "review.json")["criterion_results"] == {"free_threshold": decision}
    assert event["artifact_hashes"]["review.json"] == hashlib.sha256((workspace / "review.json").read_bytes()).hexdigest()


@pytest.mark.parametrize("material,exitcode,failed", [
    ("evaluator/solution.py.txt", 0, None),
    ("evaluator/wrong.py.txt", 1, "test_fee[5000-0]"),
    ("visible/shipping.py.txt", 1, "test_fee"),
])
def test_external_acceptance_independently_distinguishes_solution_mutant_and_stub(external, tmp_path, material, exitcode, failed):
    workspace = tmp_path / "independent evaluator"
    workspace.mkdir()
    scenario = external / "scenarios/fee-initial"
    shutil.copyfile(scenario / material, workspace / "shipping.py")
    shutil.copyfile(scenario / "evaluator/acceptance.py.txt", workspace / "test_acceptance.py")
    config = workspace / "pytest.ini"
    config.write_text("[pytest]\npythonpath = .\n", encoding="utf-8")
    process = accepted(lambda: subprocess.run(
        [sys.executable, "-I", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "--confcutdir=" + str(workspace), "-c", str(config), str(workspace / "test_acceptance.py")],
        cwd=workspace, capture_output=True, text=True, timeout=10, check=False), expected=lambda p: p.returncode == exitcode)
    if failed:
        assert failed in process.stdout and "AssertionError" in process.stdout
