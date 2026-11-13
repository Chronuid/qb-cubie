"""Require the complete public dataset, independently checkable references and episodes."""

import hashlib
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from ..contracts import accepted, rejected

FAMILIES = {"correctness", "file_workflow", "state_lifecycle", "error_handling", "test_quality", "maintainability"}
PROJECTS = {"billing-export", "configuration-package", "document-index", "pure-calculation"}
EPISODES = {"initial_development", "maintenance", "diagnosis"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def export_base(public_api, destination):
    exported = accepted(public_api("init_base_package"), destination, expected=lambda value: (
        value["package"] == str(destination.resolve()) and (destination / "package.json").is_file()))
    package = accepted(public_api("load_package"), Path(exported["package"]),
                       expected=lambda value: value["namespace"] == "base-v1")
    return package


def references(root, package, benchmark):
    return [(case, read_json((root / case["manifest"]).parent / case["evaluator"]["reference"]))
            for case in package["scenarios"] if case["benchmark"] == benchmark]


def test_base_export_contains_exactly_24_reviews_and_12_project_episodes(tmp_path, public_api):
    package = export_base(public_api, tmp_path / "base")
    assert Counter(case["benchmark"] for case in package["scenarios"]) == {
        "review_agent": 24, "developer_agent": 12}
    assert len({case["qualified_id"] for case in package["scenarios"]}) == 36


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_each_review_family_has_two_conforming_and_two_faulty_cases(tmp_path, public_api, family):
    root = tmp_path / "base"
    package = export_base(public_api, root)
    reviews = references(root, package, "review_agent")
    assert all(len(set(case["types"]) & FAMILIES) == 1 for case, _ in reviews)
    selected = [(case, ref) for case, ref in reviews if family in case["types"]]
    assert len(selected) == 4
    assert Counter(any(value == "fail" for value in ref["criterion_results"].values())
                   for _, ref in selected) == {False: 2, True: 2}
    # The named context is a reviewable requirement, not just a second unused file.
    cross_file = [(case, ref) for case, ref in selected if ref.get("required_context")]
    assert any(len(set(ref["required_context"])) >= 2 and ref["findings"] for _, ref in cross_file)
    for case, ref in cross_file:
        visible = (root / case["manifest"]).parent / case["visible"]
        assert all((visible / path).is_file() for path in ref["required_context"])
        assert ref["context_reason"].strip()


@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_each_independent_project_has_three_separately_reportable_episodes(tmp_path, public_api, project):
    root = tmp_path / "base"
    package = export_base(public_api, root)
    cases = references(root, package, "developer_agent")
    assert {case["group_id"] for case, _ in cases} == PROJECTS
    selected = [(case, ref) for case, ref in cases if case["group_id"] == project]
    assert len(selected) == 3
    assert Counter(next(iter(set(case["types"]) & EPISODES)) for case, _ in selected) == dict.fromkeys(EPISODES, 1)
    for case, reference in selected:
        assert reference["acceptance_tests"] and reference["agent_tests"] and reference["pytest_agent_tests"]
        assert reference["mutants"] and reference["mutant_criteria"]
        assert all(value == "pass" for value in reference["criterion_results"].values())
        assert ("file_workflow" in case["types"]) is (project != "pure-calculation")
        # Primary maintenance and diagnosis start from checked material, independently of initial success.
        assert case["requires"] == []


def test_public_base_is_development_material_with_honest_provenance(tmp_path, public_api):
    root = tmp_path / "base"
    package = export_base(public_api, root)
    catalog = read_json(root / "dataset.json")
    assert catalog["schema_version"] == 1 and catalog["publication_status"] == "public"
    assert set(catalog["cases"]) == {case["id"] for case in package["scenarios"]}
    for case in package["scenarios"]:
        record = catalog["cases"][case["id"]]
        assert case["split"] == "development"
        assert all(record[key].strip() for key in ("origin", "license", "design_id", "domain"))
        assert record["potentially_known"] is True
        assert record["assessment"] == ("manual" if "maintainability" in case["types"] else "executable")
    grouped = defaultdict(set)
    for case in package["scenarios"]:
        grouped[case["group_id"]].add(catalog["cases"][case["id"]]["design_id"])
    assert all(len(designs) == 1 for designs in grouped.values())
    project_designs = [next(iter(grouped[project])) for project in PROJECTS]
    assert len(set(project_designs)) == 4


def test_base_export_is_relocatable_and_never_overwrites_authored_data(tmp_path, public_api):
    root = tmp_path / "original"
    export_base(public_api, root)
    previous = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    rejected(public_api("init_base_package"), root, match="exist|overwrite")
    assert previous == {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    moved = tmp_path / "other directory with spaces" / "base"
    moved.parent.mkdir()
    shutil.move(root, moved)
    accepted(public_api("load_package"), moved, expected=lambda value: len(value["scenarios"]) == 36)


def test_reference_validation_executes_objective_cases_and_labels_manual_cases(tmp_path, public_api):
    root = tmp_path / "base"
    package = export_base(public_api, root)
    result = accepted(lambda: public_api("validate_package")(root, check_references=True), expected=lambda value: (
        value["valid"] is True and value["references_checked"] is True))
    checked = {case["scenario_id"]: case for case in result["scenarios"]}
    assert set(checked) == {case["qualified_id"] for case in package["scenarios"]}
    for case in package["scenarios"]:
        outcome = checked[case["qualified_id"]]
        if "maintainability" in case["types"]:
            assert outcome["reference_check"] == "manual_required" and outcome["reference_passed"] is None
        else:
            assert outcome["reference_check"] == "executed" and outcome["reference_passed"] is True
        if case["benchmark"] == "developer_agent":
            assert outcome["mutants"] and all(mutant["detected"] for mutant in outcome["mutants"])
    # Program execution cannot promote an author reference into human approval.
    for benchmark in ("review_agent", "developer_agent"):
        for _, reference in references(root, package, benchmark):
            assert reference["validation_status"] == "author_checked" and reference["human_reviews"] == []


@pytest.mark.parametrize("damage", ["reference", "surviving-mutant", "acceptance-import"])
def test_base_reference_validation_detects_broken_material(tmp_path, public_api, damage):
    root = tmp_path / "base"
    package = export_base(public_api, root)
    case, reference = next((case, ref) for case, ref in references(root, package, "developer_agent")
                           if case["group_id"] == "billing-export" and "initial_development" in case["types"])
    base = (root / case["manifest"]).parent
    if damage == "reference":
        (base / reference["solution"]).write_text("raise RuntimeError('broken reference')\n", encoding="utf-8")
    elif damage == "surviving-mutant":
        (base / next(iter(reference["mutants"].values()))).write_bytes((base / reference["solution"]).read_bytes())
    else:
        (base / reference["acceptance_tests"]).write_text("import missing_base_acceptance_dependency\n", encoding="utf-8")
    rejected(lambda: public_api("validate_package")(root, check_references=True),
             match="reference|mutant|execute|billing")


def test_dataset_export_does_not_relabel_the_old_review_examples_as_new_cases(tmp_path, public_api):
    root = tmp_path / "base"
    package = export_base(public_api, root)
    old = Path(__file__).parents[1] / "fixtures/phase1/scenarios"
    historical = {hashlib.sha256(p.read_bytes()).hexdigest()
                  for name in ("review-paid-correct", "review-paid-faulty")
                  for p in (old / name / "visible").glob("*.py")}
    for case, _ in references(root, package, "review_agent"):
        visible = (root / case["manifest"]).parent / case["visible"]
        assert all(hashlib.sha256(p.read_bytes()).hexdigest() not in historical
                   for p in visible.rglob("*") if p.is_file())
