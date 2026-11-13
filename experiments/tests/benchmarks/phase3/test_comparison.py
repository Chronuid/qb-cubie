"""Compare archived observations only when tasks and execution conditions match."""

import json
from pathlib import Path

import pytest

from ..contracts import accepted, edit_json, rejected
from .conftest import CAPABILITIES, cli, read_json, write_suite


@pytest.fixture
def record_run(external, public_api):
    def record(behavior="reference", selection='benchmarks = ["review_agent"]', seconds=10, identifier="baseline"):
        agent = external / "agents/current.toml"
        agent.write_text('schema_version = 1\ncommand = ["builtin:fake"]\n'
                         f'id = {json.dumps(identifier)}\ncapabilities = {json.dumps(CAPABILITIES)}\n'
                         f'\n[fake]\nbehavior = {json.dumps(behavior)}\n', encoding="utf-8")
        suite = write_suite(external, selection, seconds=seconds)
        return accepted(public_api("run_suite"), suite, expected=lambda r: len(r["runs"]) > 0)
    return record


def compare(public_api, before, after):
    return accepted(public_api("compare_runs"), Path(before["output"]), Path(after["output"]),
                    expected=lambda r: r["schema_version"] == 1)


def test_saved_runs_compare_once_per_scenario_across_agent_versions(public_api, record_run):
    before = record_run()
    after = record_run(identifier="candidate")
    result = compare(public_api, before, after)
    assert result["scope"] == "full" and len(result["pairs"]) == 2
    assert {p["scenario_id"] for p in result["pairs"]} == {"shop/review-correct", "shop/review-boundary"}
    for pair in result["pairs"]:
        assert pair["before"]["agent_id"] == "baseline" and pair["after"]["agent_id"] == "candidate"
        assert pair["condition"] == "cubie" and pair["repetition"] == 1
        assert pair["before"]["quality_passed"] is pair["after"]["quality_passed"] is True
        assert all(value in (None, 0) for value in pair["metric_deltas"].values())


def test_comparison_shows_regression_and_keeps_undefined_metrics(public_api, record_run):
    result = compare(public_api, record_run(), record_run("approve_all"))
    pairs = {p["scenario_id"]: p for p in result["pairs"]}
    faulty = pairs["shop/review-boundary"]
    assert faulty["before"]["quality_passed"] is True and faulty["after"]["quality_passed"] is False
    assert faulty["metric_deltas"]["recall"] == -1
    assert faulty["metric_deltas"]["precision"] is None
    assert pairs["shop/review-correct"]["metric_deltas"]["recall"] is None


def test_changed_selection_produces_a_labelled_partial_comparison(public_api, record_run):
    before = record_run()
    after = record_run(selection='ids = ["shop/review-boundary"]')
    result = compare(public_api, before, after)
    assert result["scope"] == "partial" and result["warnings"]
    assert [p["scenario_id"] for p in result["pairs"]] == ["shop/review-boundary"]


def test_comparison_never_pairs_different_conditions(external, public_api, record_run):
    before = record_run()
    suite = external / "sets/team.toml"
    suite.write_text(suite.read_text(encoding="utf-8").replace('profile = "agent-evaluation"',
                                                             'profile = "cubie-vs-pytest"'), encoding="utf-8")
    after = accepted(public_api("run_suite"), suite, expected=lambda r: len(r["runs"]) == 4)
    result = compare(public_api, before, after)
    assert result["scope"] == "partial" and result["warnings"]
    assert len(result["pairs"]) == 2 and all(p["condition"] == "cubie" for p in result["pairs"])


def test_identical_suite_name_cannot_hide_changed_budgets(public_api, record_run):
    result = compare(public_api, record_run(), record_run(seconds=11))
    assert result["scope"] == "incompatible" and result["pairs"] == []
    assert any("budget" in warning.lower() for warning in result["warnings"])


@pytest.mark.parametrize("change", ["version", "source", "reference"])
def test_same_ids_cannot_hide_changed_package_material(external, public_api, record_run, change):
    before = record_run()
    if change == "version":
        edit_json(external / "package.json", lambda p: p.update(version="2.0.0"))
    elif change == "source":
        with (external / "scenarios/review-correct/visible/shipping.py").open("a", encoding="utf-8") as stream:
            stream.write("\n# changed source context\n")
    else:
        edit_json(external / "scenarios/review-correct/evaluator/reference.json",
                  lambda p: p.update(provenance_note="Revised reference metadata"))
    result = compare(public_api, before, record_run())
    assert result["scope"] == "incompatible" and result["pairs"] == [] and result["warnings"]


def test_incomplete_attempts_remain_visible_without_numeric_improvement(public_api, record_run):
    result = compare(public_api, record_run(), record_run("timeout"))
    assert result["scope"] == "full" and len(result["pairs"]) == 2
    for pair in result["pairs"]:
        assert pair["after"]["status"] == "agent_timeout"
        assert pair["after"]["evaluation_status"] == "not_evaluated"
        assert pair["after"]["quality_passed"] is False
        assert all(value is None for value in pair["metric_deltas"].values())


def test_renaming_suite_does_not_change_the_resolved_experiment(external, public_api, record_run):
    before = record_run()
    suite = external / "sets/team.toml"
    suite.write_text(suite.read_text(encoding="utf-8").replace('name = "team-smoke"', 'name = "renamed"'), encoding="utf-8")
    after = accepted(public_api("run_suite"), suite, expected=lambda r: len(r["runs"]) == 2)
    assert compare(public_api, before, after)["scope"] == "full"


def test_comparison_reads_only_archives_and_leaves_them_unchanged(external, public_api, record_run):
    before, after = record_run(), record_run()
    paths = [Path(value["output"]) / name for value in (before, after)
             for name in ("results.json", "manifest.json", "report.md")]
    original = {p: p.read_bytes() for p in paths}
    (external / "sets/team.toml").unlink()
    (external / "agents/current.toml").unlink()
    assert compare(public_api, before, after)["scope"] == "full"
    assert all(p.read_bytes() == data for p, data in original.items())


def test_comparison_rejects_results_not_bound_to_their_manifest(public_api, record_run):
    comparator = public_api("compare_runs")
    before, after = record_run(), record_run()
    edit_json(Path(after["output"]) / "results.json", lambda r: r.update(run_id="unrelated-run"))
    rejected(comparator, Path(before["output"]), Path(after["output"]), match="run_id|manifest|hash")


def test_cli_comparison_equals_public_api_and_explains_partial_scope(external, public_api, record_run):
    before = record_run()
    after = record_run(selection='ids = ["shop/review-boundary"]')
    expected = compare(public_api, before, after)
    output = accepted(lambda: cli("compare", before["output"], after["output"], "--format", "json", cwd=external.parent),
                      expected=lambda p: p.returncode == 0)
    assert json.loads(output.stdout) == expected
    output = accepted(lambda: cli("compare", before["output"], after["output"], cwd=external.parent),
                      expected=lambda p: p.returncode == 0)
    assert "partial" in output.stdout.lower() and "shop/review-boundary" in output.stdout


def test_comparison_archive_contains_evaluator_identity(record_run):
    result = record_run()
    plan = read_json(Path(result["output"]) / "manifest.json")["plan"]
    assert all(r["evaluator"]["kind"] == "builtin.review_reference_v1" for r in plan["runs"])
