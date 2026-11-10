"""Keep complete execution, measured quality and unavailable evidence distinct."""

import hashlib
from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from ..phase2.conftest import configure_fake
from ..phase4.conftest import read_json, replace_observation
from .conftest import append_gate


def evaluate(public_api, archive):
    return accepted(public_api("evaluate_gates"), archive, expected=lambda value: value["schema_version"] == 1)


def test_real_archive_is_a_valid_control_before_gate_evaluation(gate_archive, public_api):
    accepted(public_api("compare_runs"), gate_archive, gate_archive,
             expected=lambda value: value["scope"] == "full" and len(value["pairs"]) == 2)


def test_gate_passes_at_the_exact_threshold_and_links_evidence(gate_archive, public_api):
    result = evaluate(public_api, gate_archive)
    assert result["execution_complete"] is True and result["gate_status"] == "passed"
    gate, = result["gates"]
    assert gate["id"] == "acceptance" and gate["value"] == 1.0 and gate["passed"] is True
    assert gate["required_count"] == gate["observed_count"] == 2
    assert gate["evidence"] and all((gate_archive / path).is_file() for path in gate["evidence"])


def test_completed_run_with_wrong_reviews_fails_only_the_quality_gate(measurement_suite, public_api):
    configure_fake(measurement_suite, "approve_all")
    append_gate(measurement_suite)
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    result = evaluate(public_api, run["output"])
    assert result["execution_complete"] is True and result["gate_status"] == "failed"
    gate, = result["gates"]
    assert gate["value"] == 0.5 and gate["passed"] is False


def test_completed_run_without_thresholds_is_reporting_only(measurement_suite, public_api):
    configure_fake(measurement_suite, "approve_all")
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    result = evaluate(public_api, run["output"])
    assert result["execution_complete"] is True and result["gate_status"] == "not_configured"
    assert result["gates"] == [] and any(not item["quality_passed"] for item in run["runs"])


@pytest.mark.parametrize("status", ["agent_timeout", "budget_exceeded", "invalid_output", "infrastructure_error", "not_started"])
def test_missing_attempts_never_shrink_a_gate_to_the_successful_subset(gate_archive, public_api, status):
    replace_observation(gate_archive, 0, status=status, evaluation_status="not_evaluated",
                        quality_passed=False, metrics=[], criterion_results={}, reason="Simulated missing observation")
    result = evaluate(public_api, gate_archive)
    gate, = result["gates"]
    assert result["execution_complete"] is False and result["gate_status"] == "failed"
    assert gate["required_count"] == 2 and gate["observed_count"] == 1
    assert gate["passed"] is False and gate["reason"]


def test_pending_adjudication_cannot_satisfy_even_a_zero_threshold(measurement_suite, public_api):
    append_gate(measurement_suite, threshold=0.0)
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    root = Path(run["output"])
    replace_observation(root, 0, evaluation_status="pending_adjudication", quality_passed=None,
                        metrics=[], criterion_results={}, reason="Simulated unresolved finding")
    result = evaluate(public_api, root)
    assert result["execution_complete"] is True and result["gate_status"] == "failed"
    gate, = result["gates"]
    assert gate["observed_count"] == 1 and gate["passed"] is False


def test_unavailable_cost_does_not_pass_an_upper_cost_limit(measurement_suite, public_api):
    append_gate(measurement_suite, metric="cost", operator="lte", threshold=10.0)
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    gate, = evaluate(public_api, run["output"])["gates"]
    assert gate["value"] is None and gate["observed_count"] == 0
    assert gate["required_count"] == 2 and gate["passed"] is False and gate["reason"]


@pytest.mark.parametrize("threshold,passed", [(4.0, True), (3.0, False)])
def test_known_costs_use_the_total_and_an_inclusive_upper_limit(measurement_suite, public_api, threshold, passed):
    append_gate(measurement_suite, metric="cost", operator="lte", threshold=threshold)
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    root = Path(run["output"])
    for index, cost in enumerate((1.0, 3.0)):
        replace_observation(root, index, usage={"input_tokens": None, "output_tokens": None, "cost": cost})
    gate, = evaluate(public_api, root)["gates"]
    assert gate["value"] == 4.0 and gate["passed"] is passed
    assert gate["required_count"] == gate["observed_count"] == 2


@pytest.mark.parametrize("behavior,value,passed", [("reference", 1.0, True), ("approve_all", 0.0, False)])
def test_recall_gate_checks_the_selected_faulty_case(measurement_suite, public_api, behavior, value, passed):
    configure_fake(measurement_suite, behavior)
    append_gate(measurement_suite, metric="recall", select={"ids": ["smoke/review-paid-faulty"]})
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda result: len(result["runs"]) == 2)
    gate, = evaluate(public_api, run["output"])["gates"]
    assert gate["value"] == value and gate["passed"] is passed
    assert gate["observed_count"] == gate["required_count"] == 1


@pytest.mark.parametrize("metric", ["precision", "recall"])
def test_undefined_review_metrics_never_satisfy_even_a_zero_gate(measurement_suite, public_api, metric):
    append_gate(measurement_suite, metric=metric, threshold=0.0, select={"ids": ["smoke/review-paid-correct"]})
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    gate, = evaluate(public_api, run["output"])["gates"]
    assert gate["value"] is None and gate["observed_count"] == 0
    assert gate["required_count"] == 1 and gate["passed"] is False and gate["reason"]


def test_type_scope_uses_only_its_planned_population(measurement_suite, public_api):
    append_gate(measurement_suite, select={"types_any": ["team/payment", "correctness"]})
    append_gate(measurement_suite, id="faulty-only", select={"ids": ["smoke/review-paid-faulty"]})
    configure_fake(measurement_suite, "approve_all")
    run = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    broad, narrow = evaluate(public_api, run["output"])["gates"]
    assert broad["required_count"] == 2 and broad["value"] == 0.5
    assert narrow["required_count"] == 1 and narrow["value"] == 0.0
    assert broad["passed"] is narrow["passed"] is False


def test_process_gate_detects_correct_code_without_observed_red_phase(tmp_path, public_api):
    suite = tmp_path / "developer/sets/measurement.toml"
    accepted(public_api("init_smoke_suite"), suite, expected=lambda value: suite.is_file())
    configure_fake(suite, "missing_red", "developer_agent")
    append_gate(suite, metric="process_pass_rate", select={"benchmarks": ["developer_agent"]})
    run = accepted(public_api("run_suite"), suite, expected=lambda value: len(value["runs"]) == 1)
    assert run["runs"][0]["quality_passed"] is True and run["runs"][0]["process_passed"] is False
    gate, = evaluate(public_api, run["output"])["gates"]
    assert gate["value"] == 0.0 and gate["passed"] is False


def test_gate_evaluation_is_read_only_after_relocation(gate_archive, public_api):
    before = {p.relative_to(gate_archive): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in gate_archive.rglob("*") if p.is_file()}
    evaluate(public_api, gate_archive)
    assert before == {p.relative_to(gate_archive): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in gate_archive.rglob("*") if p.is_file()}


@pytest.mark.parametrize("damage", ["results", "evidence"])
def test_gates_reject_tampered_or_missing_evidence(gate_archive, public_api, damage):
    if damage == "results":
        with (gate_archive / "results.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
    else:
        first = read_json(gate_archive / "results.json")["runs"][0]
        (gate_archive / first["evidence"][0]).unlink()
    rejected(public_api("evaluate_gates"), gate_archive, match="hash|archive|evidence|exist")
