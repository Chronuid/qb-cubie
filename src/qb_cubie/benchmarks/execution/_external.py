"""Run external agent sessions while the runner owns all observations."""

import shutil
from contextlib import nullcontext

from qb_cubie.benchmarks.adapters._transport import JsonlProcess
from qb_cubie.benchmarks.adapters.process import handshake
from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.contracts.protocols import validate_agent_event
from qb_cubie.benchmarks.execution import evaluators
from qb_cubie.benchmarks.execution._messages import _request
from qb_cubie.benchmarks.execution._process import ExecutionError
from qb_cubie.benchmarks.execution._project import _design, _entry, _process
from qb_cubie.benchmarks.execution._pytest import observe
from qb_cubie.benchmarks.reporting._files import (
    copy_tree,
    digest,
    inventory,
    tree_hash,
    write_json,
)


def perform(context):
    """Own a fresh process session for one review or development episode."""
    agent = context["agent"]
    directory = context["directory"] / "transport"
    repair = context["run"].get("process_profile") == "issue_resolution"
    session = _session(context, agent, repair)
    with session as command, JsonlProcess(command, agent["_cwd"], context["deadline"], directory) as peer:
        context["peer"] = peer
        identity = handshake(peer, agent, context["run"]["required_capabilities"])
        context["agent_version"] = identity["agent_version"]
        context["model_provenance"] = identity.get("model_provenance")
        result = _repair(context) if repair else _review(context) if context["run"]["benchmark"] == "review_agent" else _develop(context)
        return {**result, "agent_version": identity["agent_version"], "usage": context["usage"]}


def _repair(context):
    """Accept one complete patch without assigning TDD process credit."""
    event = exchange(context, "repair")
    _stop(context)
    context["repair_container"].stop()
    _artifacts(context, event)
    v.require(event["artifacts"] == ["submission.patch"], "artifacts", "repair requires submission.patch")
    from qb_cubie.benchmarks.swebench.evaluation import evaluate_patch, protect_tests
    patch = context["workspace"] / "submission.patch"
    protect_tests(patch.read_text(encoding="utf-8"), (context["base"] / context["reference"]["test_patch"]).read_text(encoding="utf-8"))
    try:
        return evaluate_patch(context, patch)
    except (ValueError, OSError) as error:
        raise ExecutionError("infrastructure_error", f"SWE-bench evaluator: {error}") from error


def exchange(context, phase):
    """Request an agent phase and validate every submitted artifact."""
    request = {**_request(context, phase), "type": "request"}
    event = context["peer"].exchange(request)
    v.require(event.get("type") == "event", "type", "expected event")
    validate_agent_event(event, request)
    context["usage"] = _usage(context.get("usage"), event["usage"])
    if event["status"] != "completed":
        raise ExecutionError(event["status"], event["reason"])
    _artifacts(context, event)
    return event


def _artifacts(context, event):
    """Check path confinement and bytes before using any phase artifact."""
    hashes = v.mapping(event.get("artifact_hashes"), "artifact_hashes")
    v.require(set(hashes) == set(event["artifacts"]), "artifact_hashes", "must cover exactly submitted artifacts")
    _regular(context["workspace"])
    for name in event["artifacts"]:
        path = v.contained(context["workspace"], name, "artifacts")
        v.require(digest(path) == hashes[name], "artifact_hashes", f"hash mismatch: {name}")


def _regular(workspace):
    """Reject symlinks and nonregular files before copying an agent tree."""
    v.require(not workspace.is_symlink(), "workspace", "symlink workspace")
    for path in workspace.rglob("*"):
        v.require(not path.is_symlink() and (path.is_file() or path.is_dir()),
                  "workspace", "agent output requires regular files and directories")


def _usage(previous, current):
    """Sum only complete phase usage, retaining unknown measurements."""
    if previous is None:
        return dict(current)
    return {name: None if previous[name] is None or current[name] is None else previous[name] + current[name]
            for name in ("input_tokens", "output_tokens", "cost")}


def _review(context):
    """Evaluate a source-bound review through the requested integration."""
    submission = exchange(context, "review")
    _stop(context)
    for name, checksum in context["source_files"].items():
        v.require(digest(v.contained(context["workspace"], name, "sources")) == checksum,
                  "sources", "review context changed")
    result = evaluators.review(context, submission)
    _review_record(context)
    return result


def _stop(context):
    """Stop the submitting process tree before independent evaluation."""
    context["peer"].finish()
    context["peer"].close()


def _review_record(context):
    """Record the external review through RBT for the Cubie condition."""
    if context["run"]["condition"] == "cubie":
        from qb_cubie.benchmarks.execution._review import submit
        submit(context, v.read_data(context["workspace"] / "review.json"))


def _develop(context):
    """Observe controlled phases and evaluate the final project independently."""
    exchange(context, "test_design")
    v.contained(context["workspace"], "tests", "tests", directory=True)
    original = _unchanged(context)
    design = _design(context)
    context["frozen_tests"] = context["directory"] / "test_design/snapshot/tests"
    phases = [design, *[_phase(context, phase) for phase in ("red", "green", "refactor")]]
    _stop(context)
    valid, reason = _process(phases)
    if not original or any(p.get("tests_changed") or p.get("production_changed") for p in phases):
        valid, reason = False, "Production changed before red or frozen tests changed"
    result = evaluators.project(context)
    return {**result, "phases": phases, "process_passed": valid, "process_reason": reason}


def _unchanged(context):
    """Check that test design preserves every original task and source file."""
    current = inventory(context["workspace"])
    return all(current.get(name) == checksum for name, checksum in context["source_files"].items())


def _phase(context, phase):
    """Observe a submitted phase using the frozen design tests."""
    exchange(context, phase)
    directory = context["directory"] / phase
    snapshot = copy_tree(context["workspace"], directory / "snapshot")
    changed = tree_hash(snapshot / "tests") != tree_hash(context["frozen_tests"])
    shutil.rmtree(snapshot / "tests", ignore_errors=True)
    copy_tree(context["frozen_tests"], snapshot / "tests")
    record = directory / "observation.json"
    observed = observe(context, snapshot, snapshot / "tests", record)
    write_json(record, observed)
    return {**_entry(context, phase, observed["test_outcome"], snapshot, [record, record.with_suffix(".xml")]),
            "tests_changed": changed, "production_changed": phase == "red" and not _unchanged(context)}


def _session(context, agent, repair):
    """Select an isolated repair session or a local process session."""
    if not repair:
        return nullcontext(agent["command"])
    from qb_cubie.benchmarks.swebench.agent import AgentContainer
    session = AgentContainer(agent, context["run"]["run_id"], context["workspace"], context["directory"] / "agent-evidence")
    context["repair_container"] = session
    return session
