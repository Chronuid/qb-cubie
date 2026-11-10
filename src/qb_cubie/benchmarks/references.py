"""Validate independent reference metadata and its declared material."""

from . import _validation as v


def validate_reference(root, scenario, reference):
    """Validate reference coverage without executing reference programs."""
    v.decisions(reference.get("criterion_results"), scenario["criteria"])
    v.choice(reference.get("validation_status"), {"author_checked", "independently_checked"}, "validation_status")
    reviews = reference.get("human_reviews")
    v.require(type(reviews) is list, "human_reviews", "expected a list")
    if reference["validation_status"] == "independently_checked":
        v.require(len(reviews) >= 2, "human_reviews", "two independent reviews are required")
    if scenario["benchmark"] == "review_agent":
        _review(root, scenario, reference)
    else:
        _project(root, scenario, reference)


def _review(root, scenario, reference):
    findings = reference.get("findings")
    v.require(type(findings) is list, "findings", "expected a list")
    failed = {key for key, value in reference["criterion_results"].items() if value == "fail"}
    covered = set()
    for finding in findings:
        v.mapping(finding, "findings")
        v.choice(finding.get("criterion_id"), failed, "criterion_id")
        _finding(root, scenario, finding)
        covered.add(finding["criterion_id"])
    v.require(covered == failed, "findings", f"missing failure references: {sorted(failed - covered)}")


def _finding(root, scenario, finding):
    visible = (root / scenario["visible"]).resolve()
    v.contained(visible, finding.get("path"), "findings.path")
    for field in ("symbol", "mechanism", "impact"):
        v.text(finding.get(field), f"findings.{field}")
    v.strings(finding.get("allowed_alternatives", []), "allowed_alternatives")
    if "counterexample" in finding:
        example = v.mapping(finding["counterexample"], "counterexample")
        v.require("expected" in example and "actual" in example, "counterexample", "expected and actual required")
        v.require(example["expected"] != example["actual"], "counterexample", "must distinguish the defect")


def _project(root, scenario, reference):
    _private(root, scenario, reference.get("solution"), "solution")
    mutants = v.mapping(reference.get("mutants"), "mutants")
    criteria = v.mapping(reference.get("mutant_criteria"), "mutant_criteria")
    v.require(bool(mutants) and mutants.keys() == criteria.keys(), "mutant_criteria", "each mutant needs criterion coverage")
    for name, material in mutants.items():
        _private(root, scenario, material, f"mutants.{name}")
        keys = v.strings(criteria[name], f"mutant_criteria.{name}", nonempty=True)
        v.require(set(keys) <= set(scenario["criteria"]), "mutant_criteria", f"unknown criteria in {name}")


def _private(root, scenario, material, field):
    path = v.contained(root, material, field)
    visible = (root / scenario["visible"]).resolve()
    v.require(not path.is_relative_to(visible), field, "reference material must stay outside visible tree")
