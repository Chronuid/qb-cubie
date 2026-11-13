"""Compute descriptive pilot statistics while preserving unavailable observations."""

import statistics
from datetime import datetime

from cubie_benchmarks.contracts import _validation as v

FAMILIES = {"correctness", "file_workflow", "state_lifecycle", "error_handling", "test_quality", "maintainability"}
EPISODES = {"initial_development", "maintenance", "diagnosis"}


def stats(values):
    """Report defined observations and the sample standard deviation."""
    known = [v.number(value, "observation") for value in values if value is not None]
    return {"defined_count": len(known), "mean": statistics.mean(known) if known else None,
            "stddev": statistics.stdev(known) if len(known) > 1 else None}


def usage(runs):
    """Separate unknown usage from known totals and observed elapsed time."""
    return {"cost": _usage([run["usage"]["cost"] for run in runs], total=True),
            "input_tokens": _usage([run["usage"]["input_tokens"] for run in runs], total=True),
            "output_tokens": _usage([run["usage"]["output_tokens"] for run in runs], total=True),
            "wall_time_seconds": _usage([_elapsed(run) for run in runs])}


def _usage(values, total=False):
    """Avoid asserting complete costs when any constituent is unknown."""
    summary = stats(values)
    count = summary.pop("defined_count")
    result = {"known_count": count, "unknown_count": len(values) - count, **summary}
    if total:
        subtotal = sum(value for value in values if value is not None)
        result.update(known_total=subtotal, total=subtotal if count == len(values) else None)
    return result


def _elapsed(run):
    """Measure started attempts only and reject inconsistent timestamps."""
    if run["status"] == "not_started":
        return None
    try:
        start, finish = (datetime.fromisoformat(run[key]) for key in ("started_at", "finished_at"))
        return v.number((finish - start).total_seconds(), "wall_time_seconds")
    except (ValueError, TypeError) as error:
        raise ValueError(f"archive timestamps: {error}") from error


def evaluated(run):
    """Distinguish completed judgments from pending or interrupted attempts."""
    return run["status"] == "completed" and run["evaluation_status"] == "complete"


def counts(runs):
    """Count attempts without crediting unresolved or unstarted work."""
    complete = [run for run in runs if evaluated(run)]
    return {"planned": len(runs), "started": sum(run["status"] != "not_started" for run in runs),
            "completed": sum(run["status"] == "completed" for run in runs), "evaluated": len(complete),
            "pending": sum(run["evaluation_status"] == "pending_adjudication" for run in runs),
            "not_started": sum(run["status"] == "not_started" for run in runs),
            "quality_passed": sum(run["quality_passed"] is True for run in complete),
            "process_passed": sum(run.get("process_passed") is True for run in complete if run["benchmark"] == "developer_agent")}


def family(run):
    """Keep subjective tasks separate and support packages without family tags."""
    families = set(run["types"]) & FAMILIES
    if "maintainability" in families:
        return "maintainability"
    return next(iter(families)) if len(families) == 1 else "unclassified"


def family_stats(runs):
    """Summarize each family without substituting values for missing metrics."""
    return {name: {"assessment": "manual" if name == "maintainability" else "executable",
                   **{metric: stats([metric_value(run, metric) for run in runs if family(run) == name])
                      for metric in ("precision", "recall")}}
            for name in sorted({family(run) for run in runs})}


def metric_value(run, name):
    """Read only fully evaluated, compatible per-scenario ratio metrics."""
    if not evaluated(run):
        return None
    values = [metric for metric in run["metrics"] if metric["name"] == name]
    v.require(len(values) <= 1, "metrics", f"duplicate metric: {name}")
    if not values:
        return None
    metric, = values
    v.require((metric["unit"], metric["direction"], metric["aggregation"]) == ("ratio", "higher", "per_scenario"),
              "metrics", f"incompatible definition: {name}")
    v.require(metric["value"] is None or 0 <= v.number(metric["value"], name) <= 1, name, "expected ratio")
    return metric["value"]


def macro(families):
    """Weight each defined objective family once regardless of its size."""
    return {metric: stats([group[metric]["mean"] for group in families.values()
                           if group["assessment"] == "executable"])["mean"] for metric in ("precision", "recall")}
