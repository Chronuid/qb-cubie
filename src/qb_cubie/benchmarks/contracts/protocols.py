"""Validate version-one agent and evaluator messages without running adapters."""

from pathlib import PurePosixPath, PureWindowsPath

from qb_cubie.benchmarks.contracts import _validation as v


def validate_agent_request(payload: dict) -> dict:
    """Return a detached valid agent request with its original JSON values."""
    data = _envelope(payload)
    benchmark = v.choice(data.get("benchmark"), v.PHASES, "benchmark")
    v.choice(data.get("phase"), v.PHASES[benchmark], "phase")
    v.text(data.get("task"), "task")
    _workspace(data.get("workspace"), "workspace")
    _criteria(data)
    v.choice(data.get("output_format"), {"review_v1" if benchmark == "review_agent" else "project_v1"}, "output_format")
    limits = v.budgets(data.get("budgets"))
    v.require(bool(limits), "budgets", "at least one limit is required")
    return data


def validate_agent_event(payload: dict, request: dict) -> dict:
    """Validate an agent event bound to one request and process phase."""
    request = validate_agent_request(request)
    data = _bound(payload, request)
    v.require(data.get("phase") == request["phase"], "phase", "event belongs to another phase")
    status = v.choice(data.get("status"), v.STATUSES, "status")
    v.locations(data.get("artifacts"), "artifacts", nonempty=status == "completed")
    _usage(data.get("usage"))
    if status != "completed":
        v.text(data.get("reason"), "reason")
    return data


def validate_evaluator_request(payload: dict) -> dict:
    """Validate independent evaluator inputs and their artifact hash manifest."""
    data = _envelope(payload)
    for field in ("evaluator_id", "evaluator_version"):
        v.text(data.get(field), field)
    _separate(data)
    _criteria(data)
    _hashes(data.get("artifact_hashes"))
    return data


def validate_evaluation(payload: dict, request: dict) -> dict:
    """Validate criterion judgments separately from execution and adjudication status."""
    request = validate_evaluator_request(request)
    data = _bound(payload, request)
    status = v.choice(data.get("status"), v.STATUSES, "status")
    state = v.choice(data.get("evaluation_status"), {"complete", "not_evaluated", "pending_adjudication"}, "evaluation_status")
    _completion(data, status, state)
    v.decisions(data.get("criterion_results"), request["criteria"], complete=state == "complete")
    v.locations(data.get("evidence"), "evidence", nonempty=status == "completed")
    _metrics(data.get("metrics"), state)
    return data


def _envelope(payload):
    """Validate the common versioned message envelope."""
    data = v.version(v.snapshot(payload))
    v.text(data.get("run_id"), "run_id")
    v.identifier(data.get("scenario_id"), "scenario_id", qualified=True)
    return data


def _bound(payload, request):
    """Bind an event or evaluation to its originating request."""
    data = _envelope(payload)
    for field in ("run_id", "scenario_id"):
        v.require(data[field] == request[field], field, "result belongs to another request")
    return data


def _criteria(data):
    """Validate the nonempty list of requested criteria."""
    v.strings(data.get("criteria"), "criteria", nonempty=True)


def _workspace(value, field):
    """Validate an absolute workspace path without traversal."""
    v.text(value, field)
    path = PureWindowsPath(value) if PureWindowsPath(value).drive else PurePosixPath(value)
    v.require(path.is_absolute() and ".." not in path.parts, field, "expected an absolute path without parent traversal")
    return path


def _usage(value):
    """Validate measured or explicitly unknown resource usage."""
    v.mapping(value, "usage")
    for key in ("input_tokens", "output_tokens", "cost"):
        v.require(key in value, "usage", f"missing {key}; use null for unknown values")
        if value[key] is not None:
            v.number(value[key], f"usage.{key}", integer=key != "cost")


def _hashes(value):
    """Validate submitted artifact paths and SHA-256 digests."""
    v.mapping(value, "artifact_hashes")
    v.require(bool(value), "artifact_hashes", "expected submitted artifacts")
    for path, digest in value.items():
        v.relative(path, "artifact_hashes")
        v.require(type(digest) is str and len(digest) == 64
                  and all(char in "0123456789abcdef" for char in digest),
                  "artifact_hashes", "expected a lowercase SHA-256 digest")


def _completion(data, status, state):
    """Validate consistency between execution and evaluation status."""
    if status == "completed":
        v.require(state != "not_evaluated", "evaluation_status", "completed evaluation needs a judgment or adjudication")
    else:
        v.require(state == "not_evaluated", "evaluation_status", "interruption is not a complete evaluation")
        v.text(data.get("reason"), "reason")


def _metrics(values, state):
    """Validate distinct metrics and their evaluation completeness."""
    v.require(type(values) is list, "metrics", "expected a list")
    names = set()
    for metric in values:
        _metric(v.mapping(metric, "metrics"), state)
        v.require(metric["name"] not in names, "metrics", "duplicate metric name")
        names.add(metric["name"])


def _metric(metric, state):
    """Validate metric metadata and values against evaluation completeness."""
    for field in ("name", "unit", "aggregation"):
        v.text(metric.get(field), f"metrics.{field}")
    v.choice(metric.get("direction"), {"higher", "lower", "neutral"}, "metrics.direction")
    v.require("value" in metric, "metrics.value", "missing value; use null for unknown values")
    value = metric["value"]
    if value is not None:
        v.require(type(value) in (int, float), "metrics.value", "expected a number or null")
    v.require(state == "complete" or value is None, "metrics.value", "incomplete evaluation cannot claim numeric quality")


def _separate(data):
    """Require nonoverlapping submitted and reference workspaces."""
    submitted = _workspace(data.get("submitted_workspace"), "submitted_workspace")
    reference = _workspace(data.get("reference_workspace"), "reference_workspace")
    v.require(not (submitted.is_relative_to(reference) or reference.is_relative_to(submitted)),
              "reference_workspace", "workspaces must be separate without overlap")
