"""Evaluate declared CI gates without dropping absent or unresolved observations."""

from pathlib import Path

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.planning.gates import population, validate_gates
from cubie_benchmarks.reporting import _pilot_stats as stats
from cubie_benchmarks.reporting.archives import read_archive


def evaluate_gates(archive_path: str | Path) -> dict:
    """Recompute gates from a verified archive without changing archived bytes."""
    root = Path(archive_path).resolve()
    try:
        result = read_archive(root)
        manifest = v.read_data(root / "manifest.json")
        return assess(manifest["plan"], result["runs"])
    except (KeyError, TypeError, IndexError, OSError) as error:
        raise ValueError(f"archive: missing or malformed gate evidence: {error}") from error


def assess(plan, runs):
    """Compute the same gate view for initial saving and later archive inspection."""
    definitions = validate_gates(plan.get("gates", []), plan["runs"])
    gates = [_evaluate(gate, population(gate, runs)) for gate in definitions]
    status = "not_configured" if not gates else "passed" if all(gate["passed"] for gate in gates) else "failed"
    return {"schema_version": 1, "execution_complete": all(run["status"] == "completed" for run in runs),
            "gate_status": status, "gates": gates}


def _evaluate(gate, runs):
    """Require all selected observations before applying an inclusive threshold."""
    values = [_observation(run, gate["metric"]) for run in runs]
    known = [value for value in values if value is not None]
    value = _aggregate(known, gate["metric"]) if len(known) == len(runs) else None
    passed = value is not None and (value >= gate["threshold"] if gate["operator"] == "gte" else value <= gate["threshold"])
    reason = "Threshold reached" if passed else "Missing required observations" if value is None else "Threshold not reached"
    return {**gate, "value": value, "passed": passed, "required_count": len(runs), "observed_count": len(known),
            "reason": reason, "evidence": sorted({path for run in runs for path in run["evidence"]})}


def _aggregate(values, metric):
    """Sum complete cost observations and average complete ratio observations."""
    result = sum(values) if metric == "cost" else sum(values) / len(values)
    return v.number(result, "gates.value")


def _observation(run, metric):
    """Read only completed, evaluated and well-typed mandatory measurements."""
    v.choice(run["status"], v.STATUSES, "status")
    v.choice(run["evaluation_status"], {"complete", "not_evaluated", "pending_adjudication"}, "evaluation_status")
    if not stats.evaluated(run):
        return None
    if metric in {"quality_pass_rate", "process_pass_rate"}:
        return _boolean(run.get("quality_passed" if metric == "quality_pass_rate" else "process_passed"))
    if metric == "cost":
        value = run["usage"].get("cost")
        return None if value is None else v.number(value, "gates.cost")
    return stats.metric_value(run, metric)


def _boolean(value):
    """Preserve missing judgments and reject numeric impostors of boolean results."""
    v.require(value is None or type(value) is bool, "gates.observation", "expected boolean or null")
    return None if value is None else float(value)


def render(evaluation):
    """Explain execution completeness, gate thresholds and evidence in Markdown."""
    lines = ["## Gates", "", f"execution_complete: {evaluation['execution_complete']}; gate_status: {evaluation['gate_status']}", ""]
    for gate in evaluation["gates"]:
        lines.extend([f"### {gate['id']}", "", f"{gate['metric']}: {gate['value']} {gate['operator']} {gate['threshold']}",
                      f"{gate['reason']} ({gate['observed_count']}/{gate['required_count']} observations)",
                      *[f"- [Evidence]({path})" for path in gate["evidence"]], ""])
    return lines
