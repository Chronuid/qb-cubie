"""Manage fresh fake episodes and classify observed execution failures."""

import shutil
import time

from qb_cubie.benchmarks.adapters import fake
from qb_cubie.benchmarks.execution import _external, evaluators
from qb_cubie.benchmarks.execution._messages import exchange
from qb_cubie.benchmarks.execution._process import ExecutionError
from qb_cubie.benchmarks.execution._project import develop
from qb_cubie.benchmarks.execution._review import submit
from qb_cubie.benchmarks.reporting._files import (
    copy_tree,
    digest,
    inventory,
    now,
    tree_hash,
    write_json,
)


def execute(root, planned, material, agent, index, deadline):
    """Run a fresh episode and preserve its classified outcome."""
    context = _context(root, planned, material, agent, index, deadline)
    result = _initial(context)
    if time.monotonic() >= deadline:
        result.update(_failure("not_started", "Global wall time exhausted before episode start"))
    else:
        result.update(_attempt(context))
    return _finish(context, result)


def _attempt(context):
    """Classify adapter, protocol and infrastructure failures during an episode."""
    try:
        fake.interrupt(context)
        result = _perform(context)
        if time.monotonic() >= context["deadline"]:
            raise ExecutionError("agent_timeout", "Episode wall time exhausted during evaluation")
        return result
    except ExecutionError as error:
        return _failure(error.status, str(error))
    except ValueError as error:
        return _failure("invalid_output", str(error))
    except OSError as error:
        return _failure("infrastructure_error", str(error))


def _context(root, planned, material, agent, index, deadline):
    """Create an isolated episode context with a bounded execution deadline."""
    directory = root / "episodes" / f"{index:04d}"
    directory.mkdir(parents=True)
    workspace = directory / "workspace"
    workspace.mkdir()
    _export(material, workspace)
    source = copy_tree(workspace, directory / "source")
    run = {**planned, "run_id": f"{root.name}-{index:04d}"}
    return {**material, "run": run, "agent": agent, "root": root, "directory": directory,
            "workspace": workspace, "task": (workspace / "task.md").read_text(encoding="utf-8"), "started_at": now(),
            "behavior": agent.get("fake", {}).get("behavior", "reference"), "source_files": inventory(source),
            "deadline": min(deadline, time.monotonic() + planned["budgets"]["wall_time_seconds"]), "tool_calls": 0}


def _export(material, workspace):
    """Export visible materials with executable Python filenames."""
    source = material["base"] / material["scenario"]["visible"]
    for path in source.rglob("*"):
        if path.is_file() and not {"__pycache__", ".pytest_cache"} & set(path.relative_to(source).parts):
            relative = path.relative_to(source)
            repair = material["scenario"].get("process_profile") == "issue_resolution"
            target = workspace / (relative.with_suffix("") if not repair and relative.name.endswith(".py.txt") else relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    shutil.copy2(material["base"] / material["scenario"]["task"], workspace / "task.md")


def _initial(context):
    """Record initial source identities and an unevaluated result."""
    workspace = context["workspace"]
    export = write_json(context["directory"] / "export.json", {"task": context["task"],
        "criteria": context["scenario"]["criteria"], "files": list(context["source_files"])})
    extra = {"process_passed": None} if context["run"].get("process_profile") == "issue_resolution" else {}
    return {**context["run"], **extra, **_failure("not_started", "Episode has not started"),
            "started_at": context["started_at"], "task_version": context["run"]["package"]["version"],
            "evaluator_id": context["scenario"]["evaluator"]["kind"], "evaluator_version": "1.0.0",
            "agent_kind": "fake", "model_id": None, "usage": dict(fake.USAGE),
            "workspace": str(workspace), "export_manifest": export.relative_to(context["root"]).as_posix(),
            "source_tree_sha256": tree_hash(context["directory"] / "source"),
            "task_sha256": digest(workspace / "task.md"), "context_sha256": tree_hash(workspace)}


def _perform(context):
    """Execute the appropriate review or developer workflow."""
    if context["agent"]["command"] != ["builtin:fake"]:
        return _external.perform(context)
    if context["run"]["benchmark"] == "review_agent":
        submission = submit(context)
        exchange(context, "review", submission["artifacts"], submission["run_id"])
        return evaluators.review(context, submission)
    process = develop(context)
    result = evaluators.project(context)
    return {**result, **process}


def _failure(status, reason):
    """Represent an execution failure without fabricated criterion judgments."""
    return {"status": status, "evaluation_status": "not_evaluated", "criterion_results": {},
            "metrics": [], "evidence": [], "quality_passed": False, "reason": reason}


def _finish(context, result):
    """Preserve final submission identity and episode evidence."""
    result["agent_kind"] = "fake" if context["agent"]["command"] == ["builtin:fake"] else "process"
    if result["agent_kind"] == "process":
        result.update(agent_version=context.get("agent_version"), usage=context.get("usage", dict(fake.USAGE)))
        result.update(model_provenance=context.get("model_provenance"),
                      model_id=(context.get("model_provenance") or {}).get("model_id"))
    result["finished_at"] = now()
    result["submitted_tree_sha256"] = tree_hash(context["workspace"])
    result["tool_calls"] = context["tool_calls"]
    result["reason"] = None if result["status"] == "completed" else result["reason"]
    record = write_json(context["directory"] / "result.json", result)
    result["evidence"] = [*result["evidence"], record.relative_to(context["root"]).as_posix()]
    return result
