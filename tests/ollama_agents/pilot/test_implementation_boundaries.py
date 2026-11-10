"""Check explicit exploratory use, private evaluator identity and portable admission paths."""

import json

import pytest

from qb_cubie.benchmarks import run_frozen_suite

from ...benchmarks.contracts import accepted, edit_json, rejected
from ...benchmarks.phase4.conftest import replace_observation
from .support import freeze, read_json, reference_paths


def test_exploratory_freeze_retains_author_references_without_fabricating_admission(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    for path in reference_paths(suite):
        reference = read_json(path)
        for review in reference["human_reviews"]:
            (path.parent.parent / review["evidence"]).unlink()
        edit_json(path, lambda value: value.update(validation_status="author_checked", human_reviews=[]))
    bundle = tmp_path / "exploratory"
    accepted(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=bundle,
                          exploratory=True), expected=lambda value: value["measurement_sha256"])
    receipt = read_json(bundle / "measurement.json")["pilot"]
    assert receipt["study_kind"] == "exploratory" and receipt["reference_admission"] == "author_checked"
    result = accepted(run_frozen_suite, bundle, tmp_path / "results", expected=lambda value: len(value["runs"]) == 10)
    assert all(run["status"] == "completed" for run in result["runs"])


def test_exploratory_flag_must_be_explicit_boolean(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=tmp_path / "bundle",
                          exploratory="false"), match="exploratory|boolean")


def test_private_evaluator_change_requires_recalibration(pilot_api, tmp_path):
    from .support import pilot_inputs
    gate = pilot_api()
    suite, archive = pilot_inputs(tmp_path / "inputs", benchmark="developer_agent")
    reference = next(path for path in reference_paths(suite) if "review-" not in str(path))
    tests = reference.parent.parent / read_json(reference)["acceptance_tests"]
    tests.write_text(tests.read_text(encoding="utf-8") + "\n# changed private acceptance\n", encoding="utf-8")
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=tmp_path / "bundle"),
             match="calibration|evaluator|material")


def test_changed_reference_decision_requires_recalibration(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    path = next(path for path in reference_paths(suite) if "review-paid-faulty" in str(path))
    edit_json(path, lambda value: value.update(criterion_results=dict.fromkeys(value["criterion_results"], "pass"), findings=[]))
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=tmp_path / "bundle"),
             match="calibration|reference|material")


@pytest.mark.parametrize("changes", [
    {"finished_at": "2099-01-01T00:00:00+00:00"},
    {"started_at": "2099-01-01T00:00:00+00:00"},
    {"finished_at": "2026-01-01T00:00:00"},
])
def test_calibration_clock_cannot_be_future_reversed_or_naive(pilot_api, prepared, tmp_path, changes):
    gate = pilot_api()
    suite, archive = prepared
    replace_observation(archive, 0, **changes)
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=tmp_path / "bundle"),
             match="calibration|time|finish")


def test_gate_cli_uses_installed_contract_and_keeps_stdout_json(pilot_api, prepared, tmp_path, monkeypatch, capsys):
    pilot_api()
    from ollama_agents.pilot.__main__ import main
    suite, archive = prepared
    bundle = tmp_path / "from cli"
    assert main(["--suite", str(suite), "--calibration", str(archive), "--destination", str(bundle)]) == 0
    assert json.loads(capsys.readouterr().out)["path"] == str(bundle)
    assert main(["--suite", str(suite), "--calibration", str(archive), "--destination", str(bundle)]) == 2
    output = capsys.readouterr()
    assert output.out == "" and "exist" in output.err


def test_live_study_requires_opt_in_before_provider_access(pilot_api, tmp_path):
    pilot_api()
    from ollama_agents.pilot.live import measure_smoke
    target = tmp_path / "must not infer"
    rejected(lambda: measure_smoke(target), match="exploratory")
    assert not target.exists()


def test_official_receipt_is_explicit(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    bundle = tmp_path / "bundle"
    freeze(gate, suite, [archive], bundle)
    assert read_json(bundle / "measurement.json")["pilot"]["study_kind"] == "official"


def test_unknown_calibration_status_cannot_count_as_a_started_trial(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    replace_observation(archive, 0, status="unclassified")
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=tmp_path / "bundle"),
             match="calibration.status")


def test_changed_source_permissions_require_recalibration(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    source = suite.parent.parent / "scenarios/smoke/scenarios/review-paid-correct/visible/policy.py"
    source.chmod(source.stat().st_mode ^ 0o100)
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=tmp_path / "bundle"),
             match="calibration|source|material")
