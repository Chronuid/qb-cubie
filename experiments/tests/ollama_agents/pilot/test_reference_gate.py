"""Keep human admission optional while validating any claimed independent approvals."""

import pytest

from cubie_benchmarks import load_package

from ...benchmarks.contracts import accepted, edit_json, rejected
from .support import freeze, inventory, reference_paths


@pytest.mark.parametrize("fault", ["same-reviewer", "dispute", "missing-evidence", "visible-evidence"])
def test_claimed_independent_admission_requires_valid_documented_approvals(pilot_api, prepared, tmp_path, fault):
    gate = pilot_api()
    suite, archive = prepared
    reference = next(path for path in reference_paths(suite) if "review-" in str(path))

    def damage(value):
        if fault == "same-reviewer":
            value["human_reviews"][1]["reviewer_id"] = value["human_reviews"][0]["reviewer_id"]
        elif fault == "dispute":
            value["human_reviews"][1]["decision"] = "dispute"
        else:
            value["human_reviews"][1]["evidence"] = (
                "evaluator/missing.md" if fault == "missing-evidence" else "visible/policy.py")

    edit_json(reference, damage)
    target = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=target),
             match="independent|validation_status|human_reviews|reviewer|evidence|decision|approval")
    assert not target.exists()


def test_gate_checks_selected_cases_instead_of_unselected_package_material(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    # The unselected Developer reference remains a valid local author reference.
    reference = next(path for path in reference_paths(suite) if "review-" not in str(path))
    edit_json(reference, lambda value: value.update(validation_status="author_checked", human_reviews=[]))
    freeze(gate, suite, [archive], tmp_path / "frozen")


def test_test_receipts_satisfy_structure_without_claiming_actual_human_validation(prepared):
    suite, _ = prepared
    package = suite.parent.parent / "scenarios/smoke"
    accepted(load_package, package, expected=lambda value: len(value["scenarios"]) == 3)
    for receipt in package.rglob("reviews/*.md"):
        assert "SYNTHETIC TEST RECEIPT" in receipt.read_text(encoding="utf-8")


def test_freeze_preserves_calibration_author_status_and_archives_new_admission(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    before = inventory(archive)
    bundle = tmp_path / "frozen"
    freeze(gate, suite, [archive], bundle)
    assert inventory(archive) == before
    references = list((bundle / "inputs/packages").rglob("evaluator/reference.json"))
    assert references and all('"independently_checked"' in path.read_text(encoding="utf-8") for path in references)
    assert any(b'"author_checked"' in content for name, content in before.items()
               if name.endswith("evaluator/reference.json"))


@pytest.mark.parametrize("all_author", [False, True])
def test_official_pilot_accepts_author_references_without_claiming_independent_admission(
        pilot_api, prepared, tmp_path, all_author):
    from .support import read_json

    gate = pilot_api()
    suite, archive = prepared
    selected = [path for path in reference_paths(suite) if "review-" in str(path)]
    for path in selected if all_author else selected[:1]:
        value = read_json(path)
        for review in value["human_reviews"]:
            (path.parent.parent / review["evidence"]).unlink()
        edit_json(path, lambda value: value.update(validation_status="author_checked", human_reviews=[]))
    bundle = tmp_path / "official"
    freeze(gate, suite, [archive], bundle)
    receipt = read_json(bundle / "measurement.json")["pilot"]
    assert receipt["study_kind"] == "official"
    assert receipt["reference_admission"] == "author_checked"
    references = list((bundle / "inputs/packages").rglob("evaluator/reference.json"))
    assert any(read_json(path)["validation_status"] == "author_checked" for path in references)
