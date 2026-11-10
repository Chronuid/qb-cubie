"""A separate namespace and domain use the public loaders and evaluators."""

import runpy
import shutil

import pytest

from ..contracts import accepted, edit_json, rejected
from .conftest import read_json, traffic, write_suite


def test_external_example_loads_without_core_registration(external, public_api):
    package = accepted(public_api("load_package"), external, expected=lambda p: (
        p["namespace"] == "shop" and len(p["scenarios"]) == 3))
    assert package["scenarios"][0]["types"] == package["scenarios"][0]["tags"] == []
    assert all(s["evaluator"]["kind"].startswith("builtin.") for s in package["scenarios"])
    assert not traffic(external)


@pytest.mark.parametrize("subtotal,expected", [(0, False), (4999, False), (5000, True), (5001, True)])
def test_review_reference_has_an_independent_boundary_counterexample(external, subtotal, expected):
    directory = external / "scenarios"
    correct = runpy.run_path(str(directory / "review-correct/visible/shipping.py"))["is_free"]
    faulty = runpy.run_path(str(directory / "review-boundary/visible/shipping.py"))["is_free"]
    accepted(correct, subtotal, expected=expected)
    assert faulty(subtotal) == (False if subtotal == 5000 else expected)
    reference = read_json(directory / "review-boundary/evaluator/reference.json")
    assert reference["findings"][0]["counterexample"] == {"subtotal": 5000, "expected": True, "actual": False}
    assert reference["validation_status"] == "author_checked" and reference["human_reviews"] == []


@pytest.mark.parametrize("subtotal,expected", [(0, 499), (4999, 499), (5000, 0), (9000, 0)])
def test_developer_reference_and_mutant_are_distinguishable(external, subtotal, expected):
    base = external / "scenarios/fee-initial/evaluator"
    accepted(runpy.run_path(str(base / "solution.py.txt"))["fee"], subtotal, expected=expected)
    mutant = runpy.run_path(str(base / "wrong.py.txt"))["fee"]
    assert mutant(subtotal) == (499 if subtotal == 5000 else expected)


@pytest.mark.parametrize("selection,ids", [
    ('benchmarks = ["review_agent"]', ["review-boundary", "review-correct"]),
    ('types_any = ["shop/shipping", "correctness"]\ntags_all = ["shipping", "boundary"]',
     ["fee-initial", "review-boundary"]),
    ('types_all = ["correctness", "shop/shipping"]\nbenchmarks = ["review_agent"]', ["review-boundary"]),
    ('tags_any = ["boundary"]\ntypes_none = ["initial_development"]\nexclude_ids = ["shop/fee-initial"]',
     ["review-boundary"]),
    ('types_none = ["shop/shipping"]', ["review-correct"]),
])
def test_external_type_tag_filters_have_the_existing_set_semantics(external, public_api, selection, ids):
    suite = write_suite(external, selection)
    accepted(public_api("plan_suite"), suite, expected=lambda plan: (
        sorted(r["scenario_id"] for r in plan["runs"]) == ["shop/" + name for name in ids]
        and all(r["agent_id"] == "own-agent" and r["condition"] == "cubie" for r in plan["runs"])))
    assert not traffic(external)


def test_existing_and_external_packages_share_one_plan(external, package, public_api):
    suite = write_suite(external, sources=["..", str(package)], selection='benchmarks = ["review_agent"]')
    accepted(public_api("plan_suite"), suite, expected=lambda plan: (
        {r["scenario_id"] for r in plan["runs"]} == {
            "shop/review-correct", "shop/review-boundary", "phase1/review-paid-correct", "phase1/review-paid-faulty"}))
    assert not traffic(external)


def test_external_package_and_suite_can_move_to_another_working_directory(external, public_api, tmp_path, monkeypatch):
    destination = tmp_path / "moved team"
    shutil.copytree(external, destination)
    shutil.rmtree(external)
    monkeypatch.chdir(tmp_path)
    accepted(public_api("plan_suite"), destination / "sets/team.toml", expected=lambda plan: (
        len(plan["runs"]) == 3 and plan["output"] == str(destination / "results")))
    assert not traffic(destination)


@pytest.mark.parametrize("selection,match", [
    ('ids = ["shop/missing"]', "shop/missing"),
    ('types_any = ["unknown/type"]', "unknown/type"),
    ('tags_any = ["unknown-tag"]', "unknown-tag"),
    ('tags_all = []', "tags_all"),
])
def test_invalid_selection_prevents_process_launch(external, public_api, selection, match):
    rejected(public_api("run_suite"), write_suite(external, selection), match=match)
    assert not traffic(external) and not (external / "results").exists()


def test_structural_validation_never_executes_scenario_code(external, public_api):
    marker = external / "EXECUTED"
    code = f'from pathlib import Path\nPath({str(marker)!r}).write_text("unexpected")\nraise RuntimeError("executed")\n'
    (external / "scenarios/fee-initial/evaluator/solution.py.txt").write_text(code, encoding="utf-8")
    accepted(public_api("load_package"), external, expected=lambda p: p["namespace"] == "shop")
    accepted(public_api("plan_suite"), external / "sets/team.toml", expected=lambda p: len(p["runs"]) == 3)
    assert not marker.exists() and not traffic(external)


def test_declared_episode_dependency_cannot_be_removed_by_selection(external, public_api):
    path = external / "scenarios/fee-initial/scenario.json"
    edit_json(path, lambda s: s.update(requires=["shop/review-correct"]))
    rejected(public_api("run_suite"), write_suite(external, 'ids = ["shop/fee-initial"]'), match="requires|prerequisite")
    assert not traffic(external)
