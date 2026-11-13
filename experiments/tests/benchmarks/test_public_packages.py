"""Phase 10.1: public package format, references and separation of taxonomy."""

import json

import pytest

from .contracts import accepted, edit_json, rejected, scenario

IDS = ["index-diagnosis", "index-initial", "index-maintenance",
       "review-paid-correct", "review-paid-faulty"]


def test_package_loads_with_complete_qualified_ids(package, public_api):
    accepted(public_api("load_package"), package, expected=lambda result: (
        result["schema_version"] == 1 and result["namespace"] == "phase1"
        and result["version"] == "1.0.0"
        and sorted(s["qualified_id"] for s in result["scenarios"]) == [f"phase1/{id_}" for id_ in IDS]
    ))


@pytest.mark.parametrize("types", [None, [], ["myteam/payment_rules"], ["correctness", "file_workflow"]])
def test_types_are_optional_open_and_do_not_select_evaluator(package, public_api, types):
    if types is not None:
        edit_json(scenario(package), lambda data: data.update(types=types))
    accepted(public_api("load_package"), package, expected=lambda result: any(
        s["qualified_id"] == "phase1/review-paid-correct"
        and s["types"] == (types or []) and s["tags"] == []
        and s["benchmark"] == "review_agent"
        and s["evaluator"]["kind"] == "builtin.review_reference_v1"
        for s in result["scenarios"]
    ))


@pytest.mark.parametrize("field", ["namespace", "version", "license", "provenance", "scenarios"])
def test_package_requires_identity_and_provenance(package, public_api, field):
    edit_json(package / "package.json", lambda data: data.pop(field))
    rejected(public_api("load_package"), package, match=field)


@pytest.mark.parametrize("field,value", [
    ("schema_version", 99), ("benchmark", "other"), ("criteria", []),
    ("types", "correctness"), ("tags", [1]), ("split", "unknown"),
])
def test_invalid_scenario_fields_are_configuration_errors(package, public_api, field, value):
    edit_json(scenario(package), lambda data: data.update({field: value}))
    rejected(public_api("load_package"), package, match=field)


@pytest.mark.parametrize("field", ["benchmark", "criteria", "evaluator", "task", "visible", "group_id", "split"])
def test_scenario_requires_explicit_workflow_and_references(package, public_api, field):
    edit_json(scenario(package), lambda data: data.pop(field))
    rejected(public_api("load_package"), package, match=field)


@pytest.mark.parametrize("field,value", [("task", "missing.md"), ("visible", "missing"),
                                         ("task", "../../../../outside.md")])
def test_missing_or_escaping_material_is_rejected(package, public_api, field, value):
    edit_json(scenario(package), lambda data: data.update({field: value}))
    rejected(public_api("load_package"), package, match=field)


def test_duplicate_scenario_id_is_rejected(package, public_api):
    edit_json(scenario(package, "review-paid-faulty"), lambda data: data.update(id="review-paid-correct"))
    rejected(public_api("load_package"), package, match="duplicate.*review-paid-correct")


def test_episode_group_cannot_cross_splits(package, public_api):
    edit_json(scenario(package, "index-diagnosis"), lambda data: data.update(split="held_out"))
    rejected(public_api("load_package"), package, match="split.*document-index|document-index.*split")


def test_missing_evaluator_reference_is_rejected(package, public_api):
    path = scenario(package).parent / "evaluator" / "reference.json"
    path.unlink()
    rejected(public_api("load_package"), package, match="reference")


def test_reference_must_cover_exactly_visible_criteria(package, public_api):
    path = scenario(package).parent / "evaluator" / "reference.json"
    edit_json(path, lambda data: data["criterion_results"].pop("exact_cents"))
    rejected(public_api("load_package"), package, match="exact_cents")


def test_loading_does_not_execute_visible_or_evaluator_code(package, public_api):
    marker = package / "executed"
    for directory in ["visible", "evaluator"]:
        path = scenario(package).parent / directory / "__init__.py"
        path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\nraise RuntimeError('executed')\n", encoding="utf-8")
    accepted(public_api("load_package"), package, expected=lambda result: len(result["scenarios"]) == 5)
    assert not marker.exists()


def test_developer_episode_has_explicit_predecessor(package):
    expected = {"initial": [], "maintenance": ["phase1/index-initial"],
                "diagnosis": ["phase1/index-maintenance"]}
    for episode, requires in expected.items():
        payload = json.loads(scenario(package, "index-" + episode).read_text(encoding="utf-8"))
        assert payload["requires"] == requires
        assert payload["group_id"] == "document-index"
