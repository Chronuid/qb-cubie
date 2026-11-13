"""Phase 10.1: versioned agent and evaluator messages preserve status meaning."""

from copy import deepcopy

import pytest

from .contracts import accepted, rejected

REQUEST = {
    "schema_version": 1, "run_id": "run-1", "scenario_id": "phase1/review-paid-faulty",
    "benchmark": "review_agent", "phase": "review", "task": "Review the paid balance.",
    "workspace": "/workspace/run-1", "criteria": ["paid_only", "exact_cents"],
    "output_format": "review_v1", "budgets": {"wall_time_seconds": 60, "tool_calls": 5},
}
EVENT = {
    "schema_version": 1, "run_id": "run-1", "scenario_id": "phase1/review-paid-faulty",
    "status": "completed", "phase": "review", "artifacts": ["review.json"],
    "usage": {"input_tokens": None, "output_tokens": None, "cost": None},
}
EVALUATOR_REQUEST = {
    "schema_version": 1, "run_id": "run-1", "scenario_id": "phase1/review-paid-faulty",
    "evaluator_id": "builtin.review_reference_v1", "evaluator_version": "1.0.0",
    "submitted_workspace": "/evaluation/run-1/submitted", "reference_workspace": "/evaluation/run-1/reference",
    "criteria": ["paid_only", "exact_cents"], "artifact_hashes": {"review.json": "a" * 64},
}
EVALUATION = {
    "schema_version": 1, "run_id": "run-1", "scenario_id": "phase1/review-paid-faulty",
    "status": "completed", "evaluation_status": "complete",
    "criterion_results": {"paid_only": "fail", "exact_cents": "pass"},
    "metrics": [], "evidence": ["observations/counterexample.json"],
}


def message_arguments(name, payload):
    if name in {"validate_agent_request", "validate_evaluator_request"}:
        return (payload,)
    return payload, EVALUATOR_REQUEST if name == "validate_evaluation" else REQUEST


@pytest.mark.parametrize("name,payload", [("validate_agent_request", REQUEST),
                                          ("validate_agent_event", EVENT),
                                          ("validate_evaluator_request", EVALUATOR_REQUEST),
                                          ("validate_evaluation", EVALUATION)])
def test_version_one_messages_roundtrip_without_invented_values(public_api, name, payload):
    arguments = message_arguments(name, payload)
    accepted(public_api(name), *deepcopy(arguments), expected=payload)


@pytest.mark.parametrize("name,payload", [("validate_agent_request", REQUEST),
                                          ("validate_agent_event", EVENT),
                                          ("validate_evaluator_request", EVALUATOR_REQUEST),
                                          ("validate_evaluation", EVALUATION)])
def test_unknown_protocol_version_is_rejected(public_api, name, payload):
    payload = {**deepcopy(payload), "schema_version": 99}
    args = message_arguments(name, payload)
    rejected(public_api(name), *args, match="schema_version")


@pytest.mark.parametrize("field", ["run_id", "scenario_id", "workspace", "phase", "budgets", "criteria"])
def test_agent_request_requires_context_and_limits(public_api, field):
    payload = deepcopy(REQUEST)
    del payload[field]
    rejected(public_api("validate_agent_request"), payload, match=field)


@pytest.mark.parametrize("name,payload", [("validate_agent_event", EVENT), ("validate_evaluation", EVALUATION)])
@pytest.mark.parametrize("field,value", [("run_id", "foreign-run"), ("scenario_id", "phase1/foreign")])
def test_foreign_results_cannot_bind_to_request(public_api, name, payload, field, value):
    payload = {**deepcopy(payload), field: value}
    rejected(public_api(name), *message_arguments(name, payload), match=field)


@pytest.mark.parametrize("status", ["agent_timeout", "budget_exceeded", "invalid_output",
                                    "infrastructure_error", "not_started"])
def test_execution_failure_is_preserved_and_is_not_a_criterion_decision(public_api, status):
    payload = {**deepcopy(EVALUATION), "status": status, "criterion_results": {},
               "evaluation_status": "not_evaluated", "evidence": [], "reason": "test interruption"}
    accepted(public_api("validate_evaluation"), payload, EVALUATOR_REQUEST, expected=payload)


@pytest.mark.parametrize("decision", ["pass", "fail", "abstain"])
def test_criterion_decisions_are_preserved_including_abstention(public_api, decision):
    payload = deepcopy(EVALUATION)
    payload["criterion_results"]["paid_only"] = decision
    accepted(public_api("validate_evaluation"), payload, EVALUATOR_REQUEST, expected=payload)


def test_pending_adjudication_preserves_unknown_metric(public_api):
    payload = {**deepcopy(EVALUATION), "evaluation_status": "pending_adjudication",
               "metrics": [{"name": "recall", "value": None, "unit": "ratio",
                            "direction": "higher", "aggregation": "macro"}]}
    accepted(public_api("validate_evaluation"), payload, EVALUATOR_REQUEST, expected=payload)


@pytest.mark.parametrize("change,match", [
    ({"status": "pass"}, "status"),
    ({"criterion_results": {"paid_only": "pass"}}, "exact_cents"),
    ({"criterion_results": {"paid_only": "pass", "exact_cents": "pass", "invented": "pass"}}, "invented"),
    ({"criterion_results": {"paid_only": True, "exact_cents": "pass"}}, "paid_only"),
    ({"evidence": []}, "evidence"),
    ({"evidence": ["../other-run/result.json"]}, "evidence"),
])
def test_invalid_or_incomplete_evaluation_is_rejected(public_api, change, match):
    rejected(public_api("validate_evaluation"), {**deepcopy(EVALUATION), **change}, EVALUATOR_REQUEST, match=match)


@pytest.mark.parametrize("artifacts", [[], ["../foreign.json"], ["/other-run/result.json"]])
def test_completed_submission_requires_workspace_relative_artifact_paths(public_api, artifacts):
    rejected(public_api("validate_agent_event"), {**deepcopy(EVENT), "artifacts": artifacts},
             REQUEST, match="artifacts")


@pytest.mark.parametrize("benchmark,phase,valid", [
    ("developer_agent", "test_design", True), ("developer_agent", "red", True),
    ("developer_agent", "green", True), ("developer_agent", "refactor", True),
    ("developer_agent", "review", False), ("review_agent", "green", False),
])
def test_benchmark_determines_allowed_phases_not_types(public_api, benchmark, phase, valid):
    payload = {**deepcopy(REQUEST), "benchmark": benchmark, "phase": phase,
               "output_format": "project_v1" if benchmark == "developer_agent" else "review_v1"}
    if valid:
        accepted(public_api("validate_agent_request"), payload, expected=payload)
    else:
        rejected(public_api("validate_agent_request"), payload, match="phase")


@pytest.mark.parametrize("field", ["submitted_workspace", "reference_workspace", "evaluator_id",
                                    "evaluator_version", "artifact_hashes"])
def test_evaluator_request_requires_independent_inputs(public_api, field):
    payload = deepcopy(EVALUATOR_REQUEST)
    del payload[field]
    rejected(public_api("validate_evaluator_request"), payload, match=field)


def test_evaluator_request_rejects_invalid_artifact_hash(public_api):
    payload = {**deepcopy(EVALUATOR_REQUEST), "artifact_hashes": {"review.json": "not-sha256"}}
    rejected(public_api("validate_evaluator_request"), payload, match="artifact_hashes")
