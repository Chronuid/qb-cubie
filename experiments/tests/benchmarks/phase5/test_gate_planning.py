"""Reject ambiguous quality gates before starting an agent or producing results."""

import pytest

from ..contracts import accepted, rejected
from ..phase3.conftest import traffic
from .conftest import append_gate


def test_resolved_plan_preserves_gate_thresholds_and_type_scope(measurement_suite, public_api):
    gate = append_gate(measurement_suite, select={"types_any": ["team/payment"]})
    plan = accepted(public_api("plan_suite"), measurement_suite,
                    expected=lambda value: value.get("gates") == [gate])
    assert len(plan["runs"]) == 2  # Multiple matching types must not multiply observations.
    assert not (measurement_suite.parent.parent / "results").exists()


@pytest.mark.parametrize("changes", [
    {"metric": "unknown_score"}, {"operator": "gt"}, {"threshold": -0.01},
    {"threshold": 1.01}, {"threshold": True}, {"threshold": "1.0"},
    {"id": ""}, {"select": {"types_any": []}}, {"select": {"types_any": ["missing"]}},
    {"select": {"benchmarks": ["developer_agent"]}}, {"select": {"typo": ["correctness"]}},
], ids=["unknown-metric", "unknown-operator", "negative-ratio", "ratio-over-one", "boolean-threshold",
        "string-threshold", "empty-id", "empty-filter", "unknown-type", "empty-population", "unknown-filter"])
def test_invalid_gates_fail_during_planning(measurement_suite, public_api, changes):
    append_gate(measurement_suite, **changes)
    rejected(public_api("plan_suite"), measurement_suite, match="gate|threshold|metric|select")
    assert not (measurement_suite.parent.parent / "results").exists()


@pytest.mark.parametrize("literal", ["nan", "inf", "-inf"])
def test_nonfinite_thresholds_are_configuration_errors(measurement_suite, public_api, literal):
    append_gate(measurement_suite)
    text = measurement_suite.read_text(encoding="utf-8").replace("threshold = 1.0", f"threshold = {literal}")
    measurement_suite.write_text(text, encoding="utf-8")
    rejected(public_api("plan_suite"), measurement_suite, match="gate|threshold|finite")


def test_gate_ids_are_unique(measurement_suite, public_api):
    append_gate(measurement_suite)
    append_gate(measurement_suite, threshold=0.5)
    rejected(public_api("plan_suite"), measurement_suite, match="gate|duplicate")


def test_invalid_gate_is_rejected_before_even_a_process_capability_probe(process_suite, public_api):
    append_gate(process_suite, id="invalid", metric="typo")
    rejected(public_api("run_suite"), process_suite, match="gate|metric")
    assert traffic(process_suite.parent.parent) == []
    assert not (process_suite.parent.parent / "results").exists()
