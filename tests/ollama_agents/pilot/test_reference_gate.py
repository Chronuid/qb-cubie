"""Keep author references usable for calibration and require independent pilot admission."""

import pytest

from qb_cubie.benchmarks import load_package

from ...benchmarks.contracts import accepted, edit_json, rejected
from .support import freeze, inventory, reference_paths


@pytest.mark.parametrize("fault", ["author-only", "same-reviewer", "dispute", "missing-evidence", "visible-evidence"])
def test_official_pilot_requires_two_distinct_private_documented_approvals(pilot_api, prepared, tmp_path, fault):
    gate = pilot_api()
    suite, archive = prepared
    reference = next(path for path in reference_paths(suite) if "review-" in str(path))

    def damage(value):
        if fault == "author-only":
            value.update(validation_status="author_checked", human_reviews=[])
        elif fault == "same-reviewer":
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
