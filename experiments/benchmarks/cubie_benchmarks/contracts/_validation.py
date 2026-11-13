"""Shared validation primitives for data-only benchmark contracts."""

import json
import math
import re
import tomllib
from pathlib import Path, PurePosixPath, PureWindowsPath

DECISIONS = {"pass", "fail", "abstain"}
STATUSES = {"completed", "agent_timeout", "budget_exceeded", "invalid_output",
            "infrastructure_error", "not_started"}
PHASES = {"review_agent": {"review"}, "developer_agent": {"test_design", "red", "green", "refactor"}}
BUDGETS = {"wall_time_seconds", "tool_calls", "input_tokens", "output_tokens", "cost"}


def require(condition, field, detail="invalid or missing value"):
    """Reject a value that violates the named contract."""
    if not condition:
        raise ValueError(f"{field}: {detail}")


def mapping(value, field):
    """Validate a JSON object with string keys."""
    require(type(value) is dict, field, "expected an object")
    require(all(type(key) is str for key in value), field, "keys must be strings")
    return value


def text(value, field):
    """Validate nonempty textual content."""
    require(type(value) is str and bool(value.strip()), field, "expected nonempty text")
    return value


def choice(value, options, field):
    """Validate a value against the allowed alternatives."""
    require(type(value) is str and value in options, field, f"expected one of {sorted(options)}")
    return value


def strings(value, field, *, nonempty=False):
    """Validate a list of distinct nonempty strings."""
    require(type(value) is list and (bool(value) or not nonempty), field, "expected a list")
    for item in value:
        text(item, field)
    require(len(value) == len(set(value)), field, "duplicate values")
    return value


def command(value):
    """Validate a nonempty argument list while preserving repeated arguments."""
    require(type(value) is list and bool(value), "agent.command", "expected a nonempty argument list")
    for argument in value:
        text(argument, "agent.command")
        require("\x00" not in argument, "agent.command", "NUL in command")
    return value


def number(value, field, *, positive=False, integer=False):
    """Validate a finite numeric value within the requested bounds."""
    require(type(value) in (int, float), field, "expected a finite number")
    require(type(value) is int or math.isfinite(value), field, "expected a finite number")
    require(not integer or type(value) is int, field, "expected an integer")
    require(value > 0 if positive else value >= 0, field, "value outside allowed range")
    return value


def version(payload):
    """Validate the supported schema version."""
    mapping(payload, "payload")
    require(type(payload.get("schema_version")) is int and payload["schema_version"] == 1,
            "schema_version", "only version 1 is supported")
    return payload


def identifier(value, field, *, qualified=False):
    """Validate a local or qualified benchmark identifier."""
    text(value, field)
    pattern = r"[A-Za-z0-9][A-Za-z0-9_.-]*"
    require(re.fullmatch(pattern + ("/" + pattern if qualified else ""), value) is not None,
            field, "invalid identifier")
    return value


def relative(value, field):
    """Validate a workspace-relative POSIX path."""
    text(value, field)
    parts = value.split("/")
    require(not PurePosixPath(value).is_absolute() and not PureWindowsPath(value).drive,
            field, "expected a relative POSIX path")
    require("\\" not in value and all(part not in {"", ".", ".."} for part in parts),
            field, "path must stay inside its workspace")
    return value


def contained(root, value, field, *, directory=False):
    """Resolve existing material within its declared root."""
    relative(value, field)
    path = (root / value).resolve()
    require(path.is_relative_to(root.resolve()), field, "path escapes its root")
    require(path.is_dir() if directory else path.is_file(), field, f"missing material: {value}")
    return path


def locations(values, field, *, nonempty=False):
    """Validate workspace-relative artifact locations."""
    for path in strings(values, field, nonempty=nonempty):
        relative(path, field)


def budgets(value, field="budgets"):
    """Validate the supported resource limits."""
    mapping(value, field)
    require(not (set(value) - BUDGETS), field, f"unknown limits: {sorted(set(value) - BUDGETS)}")
    for key, amount in value.items():
        number(amount, f"{field}.{key}", positive=True, integer=key in {"tool_calls", "input_tokens", "output_tokens"})
    return value


def decisions(value, criteria, *, complete=True):
    """Validate criterion coverage and decision values."""
    mapping(value, "criterion_results")
    extra, missing = set(value) - set(criteria), set(criteria) - set(value)
    require(not extra, "criterion_results", f"unknown criteria: {sorted(extra)}")
    require(not complete or not missing, "criterion_results", f"missing criteria: {sorted(missing)}")
    for key, decision in value.items():
        choice(decision, DECISIONS, key)


def snapshot(payload):
    """Return an independent finite JSON snapshot."""
    try:
        json_value(payload)
        return json.loads(json.dumps(payload, allow_nan=False))
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError(f"payload: expected finite JSON data: {error}") from error


def json_value(value):
    """Validate recursively representable JSON data."""
    require(type(value) in (dict, list, str, int, float, bool, type(None)), "payload", "not JSON data")
    if type(value) is dict:
        for item in mapping(value, "payload").values():
            json_value(item)
    elif type(value) is list:
        for item in value:
            json_value(item)


def read_data(path, *, toml=False):
    """Read a versioned JSON or TOML document."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
        payload = tomllib.loads(raw) if toml else json.loads(raw, object_pairs_hook=unique_keys)
        return version(snapshot(payload))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error


def unique_keys(pairs):
    """Reject duplicate keys while decoding JSON objects."""
    result = {}
    for key, value in pairs:
        require(key not in result, key, "duplicate JSON key")
        result[key] = value
    return result
