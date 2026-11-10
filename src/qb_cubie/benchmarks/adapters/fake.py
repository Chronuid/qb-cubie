"""Provision deterministic submissions independently of their evaluation."""

import shutil
import sys

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.execution._process import ExecutionError, invoke
from qb_cubie.benchmarks.reporting._files import digest, write_json

BEHAVIORS = {"reference", "mutant", "wrong_solution", "approve_all", "reject_all", "abstain",
             "duplicate_findings", "missing_red", "red_import_error", "green_failure", "modify_tests",
             "missing_artifact", "foreign_run", "tampered_artifact", "mutate_context", "missing_evidence",
             "timeout", "hang", "crash"}
USAGE = {"input_tokens": None, "output_tokens": None, "cost": None}


def validate_fake(agent):
    """Validate supported fake behavior and adapter configuration."""
    v.require(agent.get("command") == ["builtin:fake"], "agent.command", "phase 2 executes builtin:fake only")
    options = v.mapping(agent.get("fake", {}), "fake")
    v.choice(options.get("behavior", "reference"), BEHAVIORS, "fake.behavior")
    v.require(set(options) <= {"behavior", "mutant"}, "fake", "unknown fake option")


def interrupt(context):
    """Produce the configured adapter interruption or blocking behavior."""
    behavior = context["behavior"]
    if behavior == "hang":
        invoke(context, [sys.executable, "-I", "-c", "import time; time.sleep(3600)"],
               context["workspace"], context["directory"] / "hang.json")
    if behavior == "timeout":
        raise ExecutionError("agent_timeout", "Fake adapter reported a timeout")
    if behavior == "crash":
        raise ExecutionError("infrastructure_error", "Fake adapter crashed")


def review(context):
    """Provision deterministic review decisions and configured finding variants."""
    reference, behavior = context["reference"], context["behavior"]
    decisions = dict(reference["criterion_results"])
    findings = v.snapshot(reference["findings"])
    if behavior in {"approve_all", "reject_all", "abstain"}:
        decision = {"approve_all": "pass", "reject_all": "fail", "abstain": "abstain"}[behavior]
        decisions = dict.fromkeys(decisions, decision)
        findings = []
    if behavior == "duplicate_findings":
        findings *= 3
    payload = {"schema_version": 1, "criterion_results": decisions, "findings": findings,
               "sources": [] if behavior == "missing_evidence" else list(context["source_files"])}
    return _submission(context, payload)


def _submission(context, payload):
    """Write a review artifact and apply configured integrity faults."""
    path = context["workspace"] / "review.json"
    write_json(path, payload)
    hashes = {"review.json": digest(path)}
    if context["behavior"] == "missing_artifact":
        path.unlink()
    if context["behavior"] == "tampered_artifact":
        write_json(path, {**payload, "changed": True})
    if context["behavior"] == "mutate_context":
        (context["workspace"] / "task.md").write_text("Changed context", encoding="utf-8")
    return {"artifacts": ["review.json"], "artifact_hashes": hashes,
            "criterion_results": payload["criterion_results"],
            "run_id": "foreign-run" if context["behavior"] == "foreign_run" else context["run"]["run_id"]}


def tests(context):
    """Provision agent tests for the selected comparison condition."""
    reference = context["reference"]
    destination = context["workspace"] / "tests" / "test_project.py"
    destination.parent.mkdir()
    field = "agent_tests" if context["run"]["condition"] == "cubie" else "pytest_agent_tests"
    shutil.copy2(context["base"] / reference[field], destination)


def implement(context):
    """Submit the configured reference solution or project mutant."""
    reference = context["reference"]
    source = reference["solution"]
    if context["behavior"] in {"mutant", "wrong_solution"}:
        source = reference["mutants"][context["agent"].get("fake", {}).get("mutant", "wrong-return")]
    shutil.copy2(context["base"] / source, context["workspace"] / reference["submission_module"])


def alter_red(context):
    """Prepare the configured red-phase fault and preserve the original module."""
    path = context["workspace"] / context["reference"]["submission_module"]
    original = path.read_bytes()
    if context["behavior"] == "red_import_error":
        path.write_text("import missing_cubie_smoke_dependency\n", encoding="utf-8")
    return path, original


def alter_green(context):
    """Apply configured test changes and implementation behavior."""
    if context["behavior"] == "modify_tests":
        path = context["workspace"] / "tests" / "test_project.py"
        path.write_text("def test_index():\n    assert True\n", encoding="utf-8")
    if context["behavior"] != "green_failure":
        implement(context)
