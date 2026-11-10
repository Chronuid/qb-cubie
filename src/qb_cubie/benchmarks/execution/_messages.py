"""Bind fake-adapter exchanges to the public version-one message contracts."""

from qb_cubie.benchmarks.adapters import fake
from qb_cubie.benchmarks.contracts.protocols import (
    validate_agent_event,
    validate_agent_request,
)
from qb_cubie.benchmarks.reporting._files import write_json


def exchange(context, phase, artifacts, run_id=None):
    """Archive a validated request and its bound fake-adapter event."""
    request = _request(context, phase)
    event = {"schema_version": 1, "run_id": run_id or request["run_id"],
             "scenario_id": request["scenario_id"], "phase": phase, "status": "completed",
             "artifacts": artifacts, "usage": dict(fake.USAGE)}
    directory = context["directory"] / "messages"
    write_json(directory / f"{phase}-request.json", request)
    write_json(directory / f"{phase}-event.json", event)
    validate_agent_event(event, request)


def _request(context, phase):
    """Build a phase request bound to the current task and workspace."""
    run = context["run"]
    return validate_agent_request({"schema_version": 1, "run_id": run["run_id"],
        "scenario_id": run["scenario_id"], "benchmark": run["benchmark"], "phase": phase,
        "task": context["task"], "workspace": str(context["workspace"]),
        "criteria": context["scenario"]["criteria"], "budgets": run["budgets"],
        "output_format": "review_v1" if run["benchmark"] == "review_agent" else "project_v1"})
