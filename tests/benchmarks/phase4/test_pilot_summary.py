"""Evaluate repeats, costs and unresolved judgments without inventing model measurements."""

import hashlib
import json
import math
import shutil
import statistics
from datetime import datetime

import pytest

from ..contracts import accepted, edit_json, rejected
from ..phase2.conftest import configure_fake
from ..phase3.conftest import cli
from .conftest import read_json, replace_observation


def summarize(public_api, *archives):
    return accepted(public_api("summarize_pilot"), list(archives), expected=lambda value: (
        value["schema_version"] == 1 and bool(value["groups"])))


def review_group(summary):
    group, = summary["groups"]
    assert group["benchmark"] == "review_agent" and group["condition"] == "cubie"
    assert group["agent_id"] == "own-agent"
    return group


def test_pilot_fixture_contains_real_bound_archives_and_deliberate_missed_findings(pilot_archive, public_api):
    accepted(public_api("compare_runs"), pilot_archive, pilot_archive, expected=lambda value: (
        value["scope"] == "full" and len(value["pairs"]) == 10))
    runs = read_json(pilot_archive / "results.json")["runs"]
    assert sum(run["quality_passed"] for run in runs) == 4
    assert len({run["workspace"] for run in runs}) == 10
    assert len({run["group_id"] for run in runs}) == 2
    assert all(run["agent_kind"] == "process" and run["model_id"] is None for run in runs)
    assert sorted(run["usage"]["cost"] for run in runs if run["usage"]["cost"] is not None) == [1] * 6 + [3] * 2
    recall = [metric["value"] for run in runs for metric in run["metrics"] if metric["name"] == "recall"]
    assert recall.count(0.0) == 6 and recall.count(1.0) == 2 and recall.count(None) == 2


def test_repeats_do_not_increase_the_number_of_independent_projects(pilot_archive, public_api):
    summary = summarize(public_api, pilot_archive)
    group = review_group(summary)
    assert group["counts"] == {"planned": 10, "started": 10, "completed": 10, "evaluated": 10,
                               "pending": 0, "not_started": 0, "quality_passed": 4, "process_passed": 0}
    assert group["independent_groups"] == 2 and group["scenario_count"] == 5
    assert group["repetitions"] == [1, 2]
    assert group["quality_pass_rate"] == pytest.approx(0.4)
    assert summary["measurement_kind"] == "infrastructure_only"
    assert summary["warnings"]  # A process transport alone is not a real model measurement.


def test_review_recall_is_macro_averaged_over_families_with_unequal_sizes(pilot_archive, public_api):
    group = review_group(summarize(public_api, pilot_archive))
    assert group["families"]["correctness"]["recall"] == {"defined_count": 6, "mean": 0.0, "stddev": 0.0}
    assert group["families"]["error_handling"]["recall"] == {"defined_count": 2, "mean": 1.0, "stddev": 0.0}
    assert group["macro_metrics"]["recall"] == pytest.approx(0.5)
    # Pooling the eight defined observations would incorrectly produce 0.25.
    assert group["families"]["correctness"]["precision"] == {
        "defined_count": 0, "mean": None, "stddev": None}
    assert group["macro_metrics"]["precision"] == 1.0


def test_unknown_costs_are_counted_and_never_reported_as_zero(pilot_archive, public_api):
    costs = review_group(summarize(public_api, pilot_archive))["usage"]["cost"]
    assert costs["known_count"] == 8 and costs["unknown_count"] == 2
    assert costs["known_total"] == 12 and costs["total"] is None
    assert costs["mean"] == 1.5 and costs["stddev"] == pytest.approx(math.sqrt(6 / 7))


def test_elapsed_time_and_sample_dispersion_come_from_archived_attempts(pilot_archive, public_api):
    runs = read_json(pilot_archive / "results.json")["runs"]
    seconds = [(datetime.fromisoformat(run["finished_at"]) - datetime.fromisoformat(run["started_at"])).total_seconds()
               for run in runs]
    observed = review_group(summarize(public_api, pilot_archive))["usage"]["wall_time_seconds"]
    assert observed["known_count"] == 10 and observed["unknown_count"] == 0
    assert observed["mean"] == pytest.approx(statistics.mean(seconds))
    assert observed["stddev"] == pytest.approx(statistics.stdev(seconds))


@pytest.mark.parametrize("status", ["agent_timeout", "budget_exceeded", "invalid_output", "infrastructure_error"])
def test_each_started_failure_stays_in_the_success_denominator(pilot_archive, public_api, status):
    runs = read_json(pilot_archive / "results.json")["runs"]
    index = next(i for i, run in enumerate(runs) if run["quality_passed"])
    replace_observation(pilot_archive, index, status=status, evaluation_status="not_evaluated",
                        quality_passed=False, metrics=[], criterion_results={}, reason="Simulated pilot interruption")
    group = review_group(summarize(public_api, pilot_archive))
    assert group["counts"]["started"] == 10 and group["counts"]["evaluated"] == 9
    assert group["counts"]["quality_passed"] == 3 and group["quality_pass_rate"] == pytest.approx(0.3)
    assert group["statuses"][status] == 1


def test_unstarted_trials_are_visible_separately_from_started_failures(pilot_archive, public_api):
    index = next(i for i, run in enumerate(read_json(pilot_archive / "results.json")["runs"]) if run["quality_passed"])
    replace_observation(pilot_archive, index, status="not_started", evaluation_status="not_evaluated",
                        quality_passed=False, metrics=[], criterion_results={}, reason="Simulated global limit")
    group = review_group(summarize(public_api, pilot_archive))
    assert group["counts"]["planned"] == 10 and group["counts"]["started"] == 9
    assert group["counts"]["not_started"] == 1 and group["quality_pass_rate"] == pytest.approx(3 / 9)


def test_pending_adjudication_has_evidence_and_no_numeric_quality_credit(pilot_archive, public_api):
    runs = read_json(pilot_archive / "results.json")["runs"]
    index, run = next((index, run) for index, run in enumerate(runs) if run["quality_passed"])
    replace_observation(pilot_archive, index, evaluation_status="pending_adjudication", quality_passed=None,
                        metrics=[], criterion_results={}, reason="Simulated new plausible finding")
    summary = summarize(public_api, pilot_archive)
    group = review_group(summary)
    assert group["counts"]["pending"] == 1 and group["counts"]["evaluated"] == 9
    assert group["counts"]["quality_passed"] == 3 and group["quality_pass_rate"] == pytest.approx(0.3)
    pending, = summary["pending_adjudications"]
    assert pending["run_id"] == run["run_id"] and pending["scenario_id"] == run["scenario_id"]
    assert pending["evidence"] == run["evidence"] and pending["archive"] == str(pilot_archive.resolve())


def test_single_observation_has_no_invented_sample_dispersion(pilot_archive, public_api):
    runs = read_json(pilot_archive / "results.json")["runs"]
    indices = [i for i, run in enumerate(runs) if "error_handling" in run["types"]]
    replace_observation(pilot_archive, indices[1], evaluation_status="pending_adjudication", quality_passed=None,
                        metrics=[], criterion_results={}, reason="Simulated dispute")
    recall = review_group(summarize(public_api, pilot_archive))["families"]["error_handling"]["recall"]
    assert recall == {"defined_count": 1, "mean": 1.0, "stddev": None}


def test_summary_is_read_only_and_uses_the_relocated_archive(pilot_archive, public_api):
    before = {p.relative_to(pilot_archive): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in pilot_archive.rglob("*") if p.is_file()}
    result = summarize(public_api, pilot_archive)
    assert before == {p.relative_to(pilot_archive): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in pilot_archive.rglob("*") if p.is_file()}
    # Copied archive paths deliberately differ from all archived workspace paths.
    assert review_group(result)["counts"]["planned"] == 10


@pytest.mark.parametrize("damage", ["result-bytes", "missing-evidence", "plan-bytes"])
def test_pilot_rejects_unverifiable_archive_material(pilot_archive, public_api, damage):
    if damage == "result-bytes":
        with (pilot_archive / "results.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
    elif damage == "plan-bytes":
        (pilot_archive / "inputs/plan.json").write_text("{}\n", encoding="utf-8")
    else:
        run = read_json(pilot_archive / "results.json")["runs"][0]
        (pilot_archive / run["evidence"][0]).unlink()
    rejected(public_api("summarize_pilot"), [pilot_archive], match="hash|archive|manifest|evidence|exist")


def test_same_trial_cannot_be_counted_twice_by_copying_an_archive(pilot_archive, tmp_path, public_api):
    duplicate = tmp_path / "second copy"
    shutil.copytree(pilot_archive, duplicate)
    rejected(public_api("summarize_pilot"), [pilot_archive, duplicate], match="duplicate|run_id|trial")


def test_pilot_cli_and_public_api_produce_the_same_summary(pilot_archive, public_api):
    expected = summarize(public_api, pilot_archive)
    output = accepted(lambda: cli("summarize-pilot", pilot_archive, "--format", "json", cwd=pilot_archive.parent),
                      expected=lambda process: process.returncode == 0)
    assert json.loads(output.stdout) == expected


def test_subjective_family_is_visible_but_excluded_from_objective_macro_metrics(tmp_path, public_api):
    suite = tmp_path / "manual" / "sets/smoke.toml"
    accepted(public_api("init_smoke_suite"), suite, expected=lambda value: value["suite"] == str(suite.resolve()))
    configure_fake(suite, "reference", "review_agent")
    case = suite.parent.parent / "scenarios/smoke/scenarios/review-paid-faulty/scenario.json"
    # Deliberate classification fixture: a numeric matcher score is insufficient for a manual family.
    edit_json(case, lambda value: value.update(types=["maintainability"]))
    suite.write_text(suite.read_text(encoding="utf-8").replace('benchmarks = ["review_agent"]',
                      'ids = ["smoke/review-paid-faulty"]'), encoding="utf-8")
    run = accepted(public_api("run_suite"), suite, expected=lambda value: len(value["runs"]) == 1)
    summary = summarize(public_api, run["output"])
    group, = summary["groups"]
    assert group["families"]["maintainability"]["assessment"] == "manual"
    assert group["macro_metrics"]["recall"] is None and group["macro_metrics"]["precision"] is None
