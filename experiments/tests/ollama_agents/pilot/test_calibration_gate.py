"""Require complete calibration evidence before freezing a pilot, regardless of success."""

import json
import shutil

import pytest

from cubie_benchmarks import run_suite

from ...benchmarks.contracts import accepted, edit_json, rejected
from ...benchmarks.phase4.conftest import replace_observation
from .support import (
    admit_references,
    calibrate,
    freeze,
    inventory,
    pilot_inputs,
    read_json,
    set_repetitions,
    suite_at,
)


@pytest.mark.parametrize("repetitions", [1, 3, 5])
def test_calibration_requires_two_repetitions_per_selected_cell(pilot_api, tmp_path, repetitions):
    gate = pilot_api()
    suite, archive = pilot_inputs(tmp_path / "inputs", repetitions=repetitions)
    target = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=target),
             match="calibration|repetition|two|2")
    assert not target.exists()


@pytest.mark.parametrize("repetitions", [1, 2, 4, 6])
def test_measurement_requires_five_repetitions(pilot_api, prepared, tmp_path, repetitions):
    gate = pilot_api()
    suite, archive = prepared
    set_repetitions(suite, repetitions)
    target = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=target),
             match="pilot|measurement|repetition|five|5")
    assert not target.exists()


def test_pilot_cannot_be_frozen_without_calibration(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, _ = prepared
    target = tmp_path / "premature pilot"
    rejected(lambda: gate(calibration_archives=[], suite_path=suite, destination=target), match="calibration|empty")
    assert not target.exists()


@pytest.mark.parametrize("behavior,status", [("timeout", "agent_timeout"), ("crash", "infrastructure_error"),
                                           ("tampered_artifact", "invalid_output"), ("approve_all", "completed")])
def test_unsuccessful_calibration_is_retained_and_does_not_trigger_best_of_n(
        pilot_api, tmp_path, behavior, status):
    gate = pilot_api()
    suite, archive = pilot_inputs(tmp_path / "inputs", behavior=behavior)
    before = inventory(archive)
    bundle = tmp_path / "frozen"
    freeze(gate, suite, [archive], bundle)
    receipt, = read_json(bundle / "measurement.json")["pilot"]["calibration_archives"]
    saved = bundle / receipt["path"]
    runs = read_json(saved / "results.json")["runs"]
    assert len(runs) == 4 and {run["status"] for run in runs} == {status}
    assert any(run["quality_passed"] is not True for run in runs)
    assert inventory(archive) == before


@pytest.mark.parametrize("fault", ["duplicate-path", "copied-archive", "missing-trial", "changed-evidence", "not-started"])
def test_incomplete_or_duplicate_calibration_is_rejected_before_freeze(pilot_api, prepared, tmp_path, fault):
    gate = pilot_api()
    suite, archive = prepared
    archives = [archive]
    if fault == "duplicate-path":
        archives.append(archive)
    elif fault == "copied-archive":
        copied = tmp_path / "copied calibration"
        shutil.copytree(archive, copied)
        archives.append(copied)
    elif fault == "missing-trial":
        payload = read_json(archive / "results.json")
        payload["runs"].pop()
        (archive / "results.json").write_text(json.dumps(payload), encoding="utf-8")
    elif fault == "changed-evidence":
        manifest = read_json(archive / "manifest.json")
        name = next(name for name in manifest["artifact_hashes"] if name.endswith("task.md"))
        (archive / name).write_text("Changed archived calibration evidence.\n", encoding="utf-8")
    else:
        replace_observation(archive, 0, status="not_started", evaluation_status="not_evaluated",
                            quality_passed=False, metrics=[], criterion_results={}, reason="Not attempted")
    target = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=archives, suite_path=suite, destination=target),
             match="calibration|duplicate|trial|hash|started|archive|plan")
    assert not target.exists()


def test_extra_started_calibration_round_must_not_be_silently_dropped(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, first = prepared
    set_repetitions(suite, 2)
    # A separately started round is a distinct archive, not a copy of the first.
    second = accepted(run_suite, suite, expected=lambda value: len(value["runs"]) == 4)["output"]
    set_repetitions(suite, 5)
    target = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=[first, second], suite_path=suite, destination=target),
             match="calibration|repetition|duplicate|two|2")
    assert not target.exists()


def test_changing_selected_conditions_after_calibration_requires_new_calibration(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    suite.write_text(suite.read_text(encoding="utf-8").replace('profile = "agent-evaluation"',
                                                             'profile = "cubie-vs-pytest"'), encoding="utf-8")
    target = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=target),
             match="condition|calibration|cell|selection")
    assert not target.exists()


def test_tuning_budget_after_calibration_is_allowed_until_freeze(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    suite.write_text(suite.read_text(encoding="utf-8").replace("wall_time_seconds = 20", "wall_time_seconds = 15"),
                     encoding="utf-8")
    freeze(gate, suite, [archive], tmp_path / "frozen")


def test_selected_scenarios_must_all_have_been_calibrated(pilot_api, tmp_path):
    gate = pilot_api()
    suite = suite_at(tmp_path / "inputs", benchmark="developer_agent")
    archive = calibrate(suite)
    set_repetitions(suite, 5)
    admit_references(suite)
    suite.write_text(suite.read_text(encoding="utf-8").replace('benchmarks = ["developer_agent"]',
                                                             'benchmarks = ["review_agent"]'), encoding="utf-8")
    target = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=target),
             match="calibration|scenario|selection|cell")
    assert not target.exists()


@pytest.mark.parametrize("component", ["source", "task", "package-version"])
def test_changed_task_material_requires_new_calibration(pilot_api, prepared, tmp_path, component):
    gate = pilot_api()
    suite, archive = prepared
    package = suite.parent.parent / "scenarios/smoke"
    if component == "package-version":
        edit_json(package / "package.json", lambda value: value.update(version="2.0.0"))
    else:
        case = package / "scenarios/review-paid-correct"
        target = case / ("visible/policy.py" if component == "source" else "task.md")
        target.write_text(target.read_text(encoding="utf-8") + "\n# Changed task material\n", encoding="utf-8")
    destination = tmp_path / "frozen"
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=destination),
             match="calibration|source|task|version|identity|material")
    assert not destination.exists()
