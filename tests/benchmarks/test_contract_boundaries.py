"""Exercise planning and validation boundaries beyond the initial acceptance set."""

from copy import deepcopy

import pytest

from qb_cubie.benchmarks import (
    load_package,
    plan_suite,
    validate_agent_event,
    validate_agent_request,
    validate_evaluation,
    validate_evaluator_request,
)

from .contracts import accepted, edit_json, rejected, scenario
from .test_protocol_contracts import EVALUATION, EVALUATOR_REQUEST, EVENT, REQUEST
from .test_suite_semantics import suite


@pytest.mark.parametrize("target,payload", [(validate_agent_request, REQUEST),
                                           (validate_evaluator_request, EVALUATOR_REQUEST)])
@pytest.mark.parametrize("value", [None, [], {"schema_version": True}, {"schema_version": 1.0}])
def test_malformed_envelopes_are_value_errors(target, payload, value):
    rejected(target, value, match="payload|schema_version")


def test_validation_returns_a_detached_json_snapshot():
    original = deepcopy(REQUEST)
    actual = validate_agent_request(original)
    original["criteria"].append("changed")
    original["budgets"]["tool_calls"] = 1000
    assert actual == REQUEST


@pytest.mark.parametrize("budget", [{"wall_time_seconds": True}, {"tool_calls": 1.5},
                                   {"wall_time_seconds": float("nan")}, {"cost": -1}, {"typo": 10}])
def test_invalid_hard_limits_are_rejected(budget):
    rejected(validate_agent_request, {**deepcopy(REQUEST), "budgets": budget}, match="budgets|payload")


@pytest.mark.parametrize("value", ["../other.json", "C:/other.json", "C:other.json", "\\\\host\\other.json"])
def test_artifact_paths_are_confined_on_both_path_platforms(value):
    rejected(validate_agent_event, {**deepcopy(EVENT), "artifacts": [value]}, REQUEST, match="artifacts")


@pytest.mark.parametrize("status", ["agent_timeout", "infrastructure_error", "not_started"])
def test_interruption_cannot_claim_complete_evaluation(status):
    rejected(validate_evaluation, {**deepcopy(EVALUATION), "status": status},
             EVALUATOR_REQUEST, match="evaluation_status")


def test_pending_adjudication_cannot_invent_numeric_quality():
    payload = {**deepcopy(EVALUATION), "evaluation_status": "pending_adjudication", "metrics": [
        {"name": "recall", "value": 1.0, "unit": "ratio", "direction": "higher", "aggregation": "macro"}]}
    rejected(validate_evaluation, payload, EVALUATOR_REQUEST, match="metrics.value")


def test_negative_metrics_are_valid_when_their_domain_allows_them():
    payload = {**deepcopy(EVALUATION), "metrics": [
        {"name": "time_delta", "value": -2, "unit": "seconds", "direction": "lower", "aggregation": "mean"}]}
    accepted(validate_evaluation, payload, EVALUATOR_REQUEST, expected=payload)


def test_reference_cannot_be_exported_as_visible_material(package):
    edit_json(scenario(package), lambda data: data.update(visible="evaluator"))
    rejected(load_package, package, match="reference")


def test_project_solution_cannot_be_placed_in_visible_material(package):
    base = scenario(package, "index-initial").parent
    edit_json(base / "evaluator/reference.json", lambda data: data.update(solution="visible/indexer.py.txt"))
    rejected(load_package, package, match="solution")


def test_visible_symlink_cannot_disclose_evaluator_material(package):
    base = scenario(package).parent
    (base / "visible/leaked-reference.json").symlink_to(base / "evaluator/reference.json")
    rejected(load_package, package, match="visible")


def test_unknown_required_criterion_in_reference_is_rejected(package):
    edit_json(scenario(package).parent / "evaluator/reference.json",
              lambda data: data["criterion_results"].update(unknown="pass"))
    rejected(load_package, package, match="unknown")


def test_prerequisite_cycle_is_a_configuration_error(package):
    edit_json(scenario(package, "index-initial"),
              lambda data: data.update(requires=["phase1/index-diagnosis"]))
    rejected(plan_suite, suite(package), match="cyclic.*prerequisites")


def test_enormous_plan_is_rejected_without_materializing_trials(package):
    path = suite(package)
    path.write_text(path.read_text(encoding="utf-8").replace("repetitions = 1", "repetitions = 1000000000000000"), encoding="utf-8")
    rejected(plan_suite, path, match="max_runs")


def test_unmeasurable_hard_budget_is_rejected(package):
    path = package / "agents/fake.toml"
    path.write_text(path.read_text(encoding="utf-8").replace(', "tool_calls"', ''), encoding="utf-8")
    rejected(plan_suite, suite(package), match="capabilities.*tool_calls")


def test_scenario_budget_override_cannot_escape_global_limit(package):
    edit_json(scenario(package), lambda data: data.update(budgets={"wall_time_seconds": 61}))
    rejected(plan_suite, suite(package), match="max_total_wall_time_seconds")


def test_scenario_budget_override_is_visible_in_plan(package):
    edit_json(scenario(package), lambda data: data.update(budgets={"wall_time_seconds": 10}))
    accepted(plan_suite, suite(package), expected=lambda plan: (
        plan["total_wall_time_seconds"] == 250 and next(
            run for run in plan["runs"] if run["scenario_id"] == "phase1/review-paid-correct"
        )["budgets"]["wall_time_seconds"] == 10))


def test_duplicate_identical_package_does_not_duplicate_trials(package):
    accepted(plan_suite, suite(package, extra='\n[[sources]]\npath = ".."\n'),
             expected=lambda plan: len(plan["runs"]) == 5 and len(plan["packages"]) == 1)


def test_source_mutation_changes_package_identity(package):
    path = suite(package)
    before = plan_suite(path)["packages"][0]["sha256"]
    (scenario(package).parent / "visible/policy.py").write_text("def eligible(row):\n    return True\n", encoding="utf-8")
    after = plan_suite(path)["packages"][0]["sha256"]
    assert before != after


def test_malformed_manifest_and_duplicate_json_keys_are_configuration_errors(package):
    (package / "package.json").write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    rejected(load_package, package, match="duplicate JSON key")


@pytest.mark.parametrize("kind", ["builtin.pytest_project_v1", "builtin.missing_v1"])
def test_review_cannot_select_incompatible_or_unknown_evaluator(package, kind):
    edit_json(scenario(package), lambda data: data["evaluator"].update(kind=kind))
    rejected(load_package, package, match="evaluator.kind")


@pytest.mark.parametrize("submitted,reference", [
    ("/evaluation/submitted", "/evaluation/./submitted"),
    ("/evaluation/submitted", "/evaluation/submitted/private"),
    ("C:/Evaluation/Submitted", "c:/evaluation/submitted"),
    ("C:/Evaluation/Submitted", "C:/Evaluation/Submitted/private"),
])
def test_evaluator_workspaces_cannot_alias_or_contain_each_other(submitted, reference):
    payload = {**deepcopy(EVALUATOR_REQUEST), "submitted_workspace": submitted, "reference_workspace": reference}
    rejected(validate_evaluator_request, payload, match="reference_workspace")
