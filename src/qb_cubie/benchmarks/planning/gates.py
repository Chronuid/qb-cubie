"""Validate gates and select their planned observation populations."""

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.planning.selection import select_runs

METRICS = {"quality_pass_rate", "process_pass_rate", "precision", "recall", "cost"}


def validate_gates(values, runs):
    """Validate every gate before execution or capability probes."""
    v.require(type(values) is list, "gates", "expected a list")
    identifiers = set()
    for gate in values:
        _gate(gate)
        v.require(gate["id"] not in identifiers, "gates.id", "duplicate gate ID")
        identifiers.add(gate["id"])
        population(gate, runs)
    return values


def _gate(gate):
    """Reject unknown fields, metrics, operators and invalid thresholds."""
    v.mapping(gate, "gates")
    v.require(set(gate) <= {"id", "metric", "operator", "threshold", "select"}, "gates", "unknown gate field")
    v.text(gate.get("id"), "gates.id")
    v.choice(gate.get("metric"), METRICS, "gates.metric")
    v.choice(gate.get("operator"), {"gte", "lte"}, "gates.operator")
    threshold = v.number(gate.get("threshold"), "gates.threshold")
    v.require(gate["metric"] == "cost" or threshold <= 1, "gates.threshold", "ratio exceeds one")


def population(gate, runs):
    """Select planned attempts once each without imposing episode prerequisites."""
    try:
        selected = select_runs(runs, gate.get("select", {}))
        if gate["metric"] == "process_pass_rate":
            selected = [run for run in selected if run["benchmark"] == "developer_agent" and run.get("process_profile") != "issue_resolution"]
        if gate["metric"] == "quality_pass_rate":
            profiles = {run.get("process_profile", "builtin") for run in selected}
            v.require(len(profiles) <= 1, "gates.select", "repair quality requires a separate population")
        v.require(bool(selected), "gates.select", "empty gate population")
        return selected
    except ValueError as error:
        raise ValueError(f"gates.select: {error}") from error
