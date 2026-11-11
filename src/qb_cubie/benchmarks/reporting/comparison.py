"""Compare intact archived trials with identical resolved execution contracts."""

import json
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.reporting._pilot_stats import _elapsed
from qb_cubie.benchmarks.reporting.archives import read_archive

IDENTITY = ("scenario_id", "condition", "repetition", "benchmark", "package", "budgets",
            "evaluator_id", "evaluator_version", "source_tree_sha256", "task_sha256", "context_sha256")


def compare_runs(before: str | Path, after: str | Path, *, before_agent=None, after_agent=None,
                 before_condition=None, after_condition=None) -> dict:
    """Compare compatible trials without restarting agents or modifying archives."""
    try:
        cross = before_condition is not None or after_condition is not None
        if cross:
            for condition in (before_condition, after_condition):
                v.choice(condition, {"cubie", "pytest"}, "condition")
        result = _compare(_index(read_archive(before), before_agent, before_condition, cross),
                          _index(read_archive(after), after_agent, after_condition, cross))
        if cross:
            result["conditions"] = {"before": before_condition, "after": after_condition}
            result["warnings"].append("Different specialized agents and images may contribute to the observed difference; this comparison measures the configured workflows.")
        return result
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError(f"archive: malformed run manifest or results: {error}") from error


def _compare(left, right):
    """Pair already validated observations and describe comparison coverage."""
    common = sorted(left.keys() & right.keys())
    scope = "full" if left.keys() == right.keys() else "partial" if common else "incompatible"
    warnings = [] if scope == "full" else [
        "Selection or execution conditions differ: only common trials with identical package, evaluator, sources and budgets are compared."]
    return {"schema_version": 1, "scope": scope, "warnings": warnings,
            "pairs": [_pair(left[key], right[key]) for key in common]}


def _index(result, agent, condition=None, cross=False):
    """Require an explicit selection when an archive contains several agents."""
    selected = [run for run in result["runs"] if condition is None or run["condition"] == condition]
    agents = {run["agent_id"] for run in selected}
    v.require(agent in agents if agent is not None else len(agents) == 1,
              "agent", f"select one agent from {sorted(agents)}")
    chosen = agent if agent is not None else next(iter(agents))
    index = {}
    for run in selected:
        if run["agent_id"] == chosen:
            fields = [field for field in IDENTITY if not (cross and field == "condition")]
            extra = [run.get(name) for name in ("agent_pair_id", "process_profile", "reference_image_digest")]
            key = json.dumps([run[field] for field in fields] + extra, sort_keys=True, allow_nan=False)
            v.require(key not in index, "runs", "duplicate trial identity")
            index[key] = run
    return index


def _pair(before, after):
    """Describe one comparison without conflating failure and unknown quality."""
    return {**{key: before[key] for key in ("scenario_id", "condition", "repetition")},
            "before": before, "after": after, "metric_deltas": _deltas(before, after),
            "effort_deltas": {**{key: _difference(before["usage"].get(key), after["usage"].get(key))
                                 for key in ("input_tokens", "output_tokens", "cost")},
                              "tool_calls": _difference(before.get("tool_calls"), after.get("tool_calls")),
                              "wall_time_seconds": _difference(_elapsed(before), _elapsed(after))}}


def _difference(before, after):
    """Preserve unknown effort rather than replacing unmeasured values with zero."""
    return None if before is None or after is None else after - before


def _deltas(before, after):
    """Subtract comparable metric values only when both evaluations are complete."""
    left = {metric["name"]: metric for metric in before["metrics"]}
    right = {metric["name"]: metric for metric in after["metrics"]}
    complete = all(run["evaluation_status"] == "complete" and run["status"] == "completed" for run in (before, after))
    return {name: _delta(left.get(name), right.get(name)) if complete else None for name in sorted(left.keys() | right.keys())}


def _delta(before, after):
    """Preserve undefined values and incompatible metric definitions."""
    if before is None or after is None or before["value"] is None or after["value"] is None:
        return None
    if any(before[key] != after[key] for key in ("unit", "direction", "aggregation")):
        return None
    return after["value"] - before["value"]
