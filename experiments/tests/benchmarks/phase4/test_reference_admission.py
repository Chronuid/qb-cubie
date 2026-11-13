"""Human admission requires distinct approvals and traceable evidence, not list length."""

import copy

import pytest

from ..contracts import accepted, edit_json, rejected, scenario


def reviews(package, receipts):
    base = scenario(package).parent
    directory = base / "evaluator/reviews"
    directory.mkdir(exist_ok=True)
    for receipt in receipts:
        if isinstance(receipt, dict) and receipt.get("evidence", "").startswith("evaluator/reviews/"):
            path = base / receipt["evidence"]
            path.write_text("Synthetic approval receipt for schema testing; no human validation occurred.\n",
                            encoding="utf-8")
    edit_json(base / "evaluator/reference.json", lambda reference: reference.update(
        validation_status="independently_checked", human_reviews=receipts))


APPROVALS = [
    {"reviewer_id": "reviewer-a", "decision": "approve", "evidence": "evaluator/reviews/a.md"},
    {"reviewer_id": "reviewer-b", "decision": "approve", "evidence": "evaluator/reviews/b.md"},
]


def test_two_distinct_documented_approvals_are_structurally_admissible(package, public_api):
    reviews(package, copy.deepcopy(APPROVALS))
    accepted(public_api("load_package"), package, expected=lambda value: len(value["scenarios"]) == 5)


@pytest.mark.parametrize("fault", ["same-reviewer", "strings", "dispute", "missing-evidence", "escaped-evidence", "empty-reviewer"])
def test_independent_admission_rejects_invalid_or_unresolved_human_reviews(package, public_api, fault):
    receipts = copy.deepcopy(APPROVALS)
    if fault == "same-reviewer":
        receipts[1]["reviewer_id"] = receipts[0]["reviewer_id"]
    elif fault == "strings":
        receipts = ["approved", "approved"]
    elif fault == "dispute":
        receipts[1]["decision"] = "dispute"
    elif fault == "missing-evidence":
        receipts[1]["evidence"] = "evaluator/does-not-exist.md"
    elif fault == "escaped-evidence":
        (package.parent / "outside.md").write_text("outside receipt\n", encoding="utf-8")
        receipts[1]["evidence"] = "../../../outside.md"
    else:
        receipts[1]["reviewer_id"] = ""
    reviews(package, receipts)
    rejected(public_api("load_package"), package, match="human_reviews|reviewer|approval|evidence|decision")


def test_author_checked_references_remain_usable_without_claiming_human_admission(package, public_api):
    result = accepted(public_api("validate_package"), package, expected=lambda value: value["valid"] is True)
    assert all(case["validation_status"] == "author_checked" for case in result["scenarios"])
    assert all(case["reference_passed"] is None for case in result["scenarios"])
