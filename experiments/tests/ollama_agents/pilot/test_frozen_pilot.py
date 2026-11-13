"""Exercise the planned pilot gate with genuine frozen execution and archive verification."""

import shutil
import tomllib
from datetime import datetime
from pathlib import Path

import pytest

from cubie_benchmarks import run_frozen_suite, summarize_pilot
from cubie_benchmarks.measurement._toml import write_toml
from cubie_benchmarks.reporting.archives import read_archive

from ...benchmarks.contracts import accepted, rejected
from .support import digest, freeze, inventory, pilot_inputs, read_json


def test_freeze_binds_calibration_and_admissions_before_measurement_starts(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    bundle = tmp_path / "frozen"
    before = inventory(suite.parent.parent)
    freeze(gate, suite, [archive], bundle)
    manifest = read_json(bundle / "measurement.json")
    pilot = manifest["pilot"]
    assert pilot["calibration_repetitions"] == 2 and pilot["measurement_repetitions"] == 5
    assert pilot["reference_admission"] == "independently_checked"
    assert len(manifest["plan"]["runs"]) == 10
    receipt, = pilot["calibration_archives"]
    path = Path(receipt["path"])
    assert not path.is_absolute() and ".." not in path.parts
    assert receipt["manifest_sha256"] == digest(archive / "manifest.json")
    saved = bundle / path
    assert inventory(saved) == inventory(archive)
    accepted(read_archive, saved, expected=lambda value: len(value["runs"]) == 4)
    assert manifest["files"][(path / "manifest.json").as_posix()] == receipt["manifest_sha256"]
    frozen_at = datetime.fromisoformat(pilot["frozen_at"])
    assert frozen_at.tzinfo is not None
    assert all(datetime.fromisoformat(run["finished_at"]) <= frozen_at
               for run in read_json(archive / "results.json")["runs"])
    assert inventory(suite.parent.parent) == before  # Freezing starts no further episode.


@pytest.mark.parametrize("profile,conditions", [
    ("agent-evaluation", {"cubie"}), ("cubie-vs-pytest", {"cubie", "pytest"}),
])
def test_relocated_pilot_uses_frozen_inputs_and_excludes_calibration_from_statistics(
        pilot_api, tmp_path, profile, conditions):
    gate = pilot_api()
    suite, archive = pilot_inputs(tmp_path / "inputs", profile=profile)
    bundle = tmp_path / "frozen"
    identity = freeze(gate, suite, [archive], bundle)
    moved = tmp_path / "relocated bundle"
    shutil.move(bundle, moved)
    shutil.rmtree(suite.parent.parent)
    before = inventory(moved)
    result = accepted(run_frozen_suite, moved, tmp_path / "pilot results",
                      expected=lambda value: len(value["runs"]) == 10 * len(conditions))
    accepted(read_archive, result["output"], expected=lambda value: value["runs"] == result["runs"])
    summary = accepted(summarize_pilot, [result["output"]], expected=lambda value: (
        value["measurement_kind"] == "infrastructure_only"))
    assert {group["condition"] for group in summary["groups"]} == conditions
    for group in summary["groups"]:
        assert group["counts"]["started"] == 10 and group["repetitions"] == [1, 2, 3, 4, 5]
        assert group["scenario_count"] == 2 and group["independent_groups"] == 1
        assert group["usage"]["cost"]["total"] is None
    archived = read_json(Path(result["output"]) / "manifest.json")
    assert archived["measurement_sha256"] == identity["measurement_sha256"]
    receipt, = archived["inputs"]["measurement"]
    frozen_at = datetime.fromisoformat(read_json(moved / "measurement.json")["pilot"]["frozen_at"])
    assert all(datetime.fromisoformat(run["started_at"]) >= frozen_at for run in result["runs"])
    assert read_json(Path(result["output"]) / receipt)["pilot"] == read_json(moved / "measurement.json")["pilot"]
    assert len({run["workspace"] for run in result["runs"]}) == len(result["runs"])
    for run in result["runs"]:
        source = Path(result["output"]) / run["export_manifest"]
        assert not list((source.parent / "source").rglob("reference.json"))
        assert not list((source.parent / "source").rglob("reviews/*.md"))
    assert inventory(moved) == before


@pytest.mark.parametrize("damage", ["budget", "seed", "source", "reference", "admission", "agent", "calibration"])
def test_frozen_changes_are_rejected_before_any_measurement(pilot_api, prepared, tmp_path, damage):
    gate = pilot_api()
    suite, archive = prepared
    bundle = tmp_path / "frozen"
    freeze(gate, suite, [archive], bundle)
    manifest = read_json(bundle / "measurement.json")
    suffixes = {"budget": "inputs/suite.toml", "seed": "inputs/suite.toml", "source": "visible/policy.py",
                "reference": "evaluator/reference.json", "admission": "reviews/human-a.md",
                "agent": "inputs/agents/fake.toml"}
    if damage == "calibration":
        receipt, = manifest["pilot"]["calibration_archives"]
        target = bundle / receipt["path"] / "results.json"
    else:
        target = bundle / next(name for name in manifest["files"]
                               if name.endswith(suffixes[damage]) and "calibration" not in name)
    original = target.read_text(encoding="utf-8")
    if damage in {"budget", "seed"}:
        data = tomllib.loads(original)
        if damage == "budget":
            assert data["budgets"]["wall_time_seconds"] == 20
            data["budgets"]["wall_time_seconds"] = 19
        else:
            assert data["seed"] == 42
            data["seed"] = 43
        write_toml(target, data)
    else:
        target.write_text(original + "\nChanged after freeze.\n", encoding="utf-8")
    output = tmp_path / "must not start"
    rejected(run_frozen_suite, bundle, output, match="hash|frozen|measurement")
    assert not output.exists()


def test_refreezing_cannot_overwrite_a_published_pilot(pilot_api, prepared, tmp_path):
    gate = pilot_api()
    suite, archive = prepared
    bundle = tmp_path / "frozen"
    freeze(gate, suite, [archive], bundle)
    before = inventory(bundle)
    rejected(lambda: gate(calibration_archives=[archive], suite_path=suite, destination=bundle),
             match="exist|overwrite|destination")
    assert inventory(bundle) == before


def test_every_failed_measurement_remains_in_the_pilot_denominator(pilot_api, tmp_path):
    gate = pilot_api()
    suite, archive = pilot_inputs(tmp_path / "inputs", behavior="timeout")
    bundle = tmp_path / "frozen"
    freeze(gate, suite, [archive], bundle)
    result = accepted(run_frozen_suite, bundle, tmp_path / "results",
                      expected=lambda value: len(value["runs"]) == 10)
    group, = accepted(summarize_pilot, [result["output"]], expected=lambda value: bool(value["groups"]))["groups"]
    assert group["counts"]["started"] == 10 and group["counts"]["completed"] == 0
    assert group["statuses"] == {"agent_timeout": 10} and group["quality_pass_rate"] == 0.0
