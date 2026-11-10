"""Compare intact archived trials with identical resolved execution contracts."""

import json
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.reporting._files import digest

IDENTITY = ("scenario_id", "condition", "repetition", "benchmark", "package", "budgets",
            "evaluator_id", "evaluator_version", "source_tree_sha256", "task_sha256", "context_sha256")


def compare_runs(before: str | Path, after: str | Path, *, before_agent=None, after_agent=None) -> dict:
    """Compare compatible trials without restarting agents or modifying archives."""
    try:
        return _compare(_index(_archive(before), before_agent), _index(_archive(after), after_agent))
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


def _archive(path):
    """Check archived bytes and bind all trial records to the saved plan."""
    root = Path(path).resolve()
    result = v.read_data(root / "results.json")
    manifest = v.read_data(root / "manifest.json")
    v.require(result.get("run_id") == manifest.get("run_id"), "run_id", "result does not match manifest")
    hashes = v.mapping(manifest.get("artifact_hashes"), "manifest.artifact_hashes")
    v.require("results.json" in hashes, "manifest", "results.json is not hashed")
    for name, checksum in hashes.items():
        v.require(digest(v.contained(root, name, "manifest.artifact_hashes")) == checksum,
                  "manifest.hash", f"archived bytes changed: {name}")
    _plan(root, manifest, result)
    return result


def _plan(root, manifest, result):
    """Verify the stored plan and each result's resolved trial identity."""
    name, = manifest["inputs"]["plan"]
    path = v.contained(root, name, "manifest.plan")
    v.require(digest(path) == manifest.get("resolved_plan_sha256"), "manifest.plan", "plan hash mismatch")
    plan = v.read_data(path)
    v.require(plan == manifest.get("plan"), "manifest.plan", "stored plan differs")
    runs = result.get("runs")
    v.require(type(runs) is list and len(runs) == len(plan["runs"]), "runs", "trial count differs from plan")
    for run, planned in zip(runs, plan["runs"], strict=True):
        v.mapping(run, "runs")
        v.require(all(run.get(key) == value for key, value in planned.items()), "runs", "trial differs from plan")


def _index(result, agent):
    """Require an explicit selection when an archive contains several agents."""
    agents = {run["agent_id"] for run in result["runs"]}
    v.require(agent in agents if agent is not None else len(agents) == 1,
              "agent", f"select one agent from {sorted(agents)}")
    chosen = agent if agent is not None else next(iter(agents))
    index = {}
    for run in result["runs"]:
        if run["agent_id"] == chosen:
            key = json.dumps([run[field] for field in IDENTITY], sort_keys=True, allow_nan=False)
            v.require(key not in index, "runs", "duplicate trial identity")
            index[key] = run
    return index


def _pair(before, after):
    """Describe one comparison without conflating failure and unknown quality."""
    return {**{key: before[key] for key in ("scenario_id", "condition", "repetition")},
            "before": before, "after": after, "metric_deltas": _deltas(before, after)}


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
