"""Freeze all local inputs before measurement and execute the reviewed snapshot."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from ..phase3.conftest import cli, traffic
from ..phase4.conftest import read_json, write_json


def inventory(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def freeze(public_api, suite, destination):
    return accepted(public_api("freeze_suite"), suite, destination, expected=lambda value: (
        value["schema_version"] == 1 and value["path"] == str(destination.resolve())
        and len(value["measurement_sha256"]) == 64))


def test_freezing_archives_configurations_material_and_adapter_without_starting_it(process_suite, tmp_path, public_api):
    bundle = tmp_path / "frozen measurement"
    result = freeze(public_api, process_suite, bundle)
    manifest = read_json(bundle / "measurement.json")
    assert result["measurement_sha256"] == hashlib.sha256((bundle / "measurement.json").read_bytes()).hexdigest()
    assert manifest["schema_version"] == 1 and manifest["plan"]["seed"] == 41
    assert len(manifest["plan"]["runs"]) == 4 and manifest["plan"]["gates"][0]["threshold"] == 1.0
    assert manifest["runtime"]["python_version"]
    assert {"wheel_sha256", "dependency_lock_sha256"} <= manifest["runtime"].keys()
    files = manifest["files"]
    for name, checksum in files.items():
        assert not Path(name).is_absolute() and ".." not in Path(name).parts
        assert hashlib.sha256((bundle / name).read_bytes()).hexdigest() == checksum
    assert any(name.endswith("jsonl_agent.py") for name in files)
    assert any(name.endswith("evaluator/reference.json") for name in files)
    assert any(name.endswith("task.md") for name in files)
    assert traffic(process_suite.parent.parent) == []
    assert not list(bundle.rglob("results.json"))


def test_same_inputs_have_the_same_measurement_identity_at_different_destinations(process_suite, tmp_path, public_api):
    first = freeze(public_api, process_suite, tmp_path / "first")
    second = freeze(public_api, process_suite, tmp_path / "second")
    assert first["measurement_sha256"] == second["measurement_sha256"]


@pytest.mark.parametrize("component", ["gate", "budget", "seed", "source", "reference", "adapter", "agent"])
def test_material_changes_require_a_new_measurement_identity(process_suite, tmp_path, public_api, component):
    first = freeze(public_api, process_suite, tmp_path / "first")
    root = process_suite.parent.parent
    files = {"source": root / "scenarios/review-boundary/visible/shipping.py",
             "reference": root / "scenarios/review-boundary/evaluator/reference.json",
             "adapter": root / "agents/jsonl_agent.py"}
    if component in files:
        with files[component].open("a", encoding="utf-8") as stream:
            stream.write("\n" if component == "reference" else "\n# changed measurement material\n")
    elif component == "agent":
        agent = root / "agents/current.toml"
        agent.write_text(agent.read_text(encoding="utf-8").replace('"reference"', '"approve_all"'), encoding="utf-8")
    else:
        old, new = {"gate": ("threshold = 1.0", "threshold = 0.9"),
                    "budget": ("wall_time_seconds = 10", "wall_time_seconds = 9"),
                    "seed": ("seed = 41", "seed = 42")}[component]
        text = process_suite.read_text(encoding="utf-8")
        assert old in text
        process_suite.write_text(text.replace(old, new), encoding="utf-8")
    second = freeze(public_api, process_suite, tmp_path / "second")
    assert first["measurement_sha256"] != second["measurement_sha256"]


def test_frozen_run_works_after_removing_original_inputs_and_relocating_bundle(process_suite, tmp_path, public_api):
    bundle = tmp_path / "frozen"
    frozen = freeze(public_api, process_suite, bundle)
    moved = tmp_path / "moved frozen inputs"
    shutil.move(bundle, moved)
    shutil.rmtree(process_suite.parent.parent)
    before = inventory(moved)
    output = tmp_path / "new results"
    result = accepted(public_api("run_frozen_suite"), moved, output, expected=lambda value: len(value["runs"]) == 4)
    assert all(run["status"] == "completed" and run["quality_passed"] for run in result["runs"])
    assert all(Path(run["workspace"]).is_relative_to(output) for run in result["runs"])
    manifest = read_json(Path(result["output"]) / "manifest.json")
    assert manifest["measurement_sha256"] == frozen["measurement_sha256"]
    archived_measurement, = manifest["inputs"]["measurement"]
    assert archived_measurement in manifest["artifact_hashes"]
    assert (Path(result["output"]) / archived_measurement).read_bytes() == (moved / "measurement.json").read_bytes()
    original_plan = read_json(moved / "measurement.json")["plan"]
    assert manifest["plan"]["runs"] == original_plan["runs"]
    assert manifest["plan"]["gates"] == original_plan["gates"]
    assert inventory(moved) == before  # Adapter scratch files belong to the new run.
    accepted(public_api("compare_runs"), result["output"], result["output"],
             expected=lambda value: value["scope"] == "full" and len(value["pairs"]) == 4)


@pytest.mark.parametrize("damage", ["changed-file", "missing-file", "extra-file", "escaping-path"])
def test_damaged_frozen_inputs_fail_before_any_agent_start(process_suite, tmp_path, public_api, damage):
    bundle = tmp_path / "frozen"
    freeze(public_api, process_suite, bundle)
    manifest = read_json(bundle / "measurement.json")
    name = next(name for name in manifest["files"] if name.endswith("jsonl_agent.py"))
    if damage == "missing-file":
        (bundle / name).unlink()
    elif damage == "changed-file":
        with (bundle / name).open("a", encoding="utf-8") as stream:
            stream.write("\n# changed after freeze\n")
    elif damage == "extra-file":
        (bundle / name).with_name("unfrozen_helper.py").write_text("VALUE = 42\n", encoding="utf-8")
    else:
        manifest["files"]["../outside.py"] = "0" * 64
        write_json(bundle / "measurement.json", manifest)
    output = tmp_path / "must not start"
    rejected(public_api("run_frozen_suite"), bundle, output, match="hash|frozen|measurement|exist|path|escap")
    assert not output.exists() and traffic(process_suite.parent.parent) == []


def test_freezing_refuses_to_overwrite_an_existing_measurement(process_suite, tmp_path, public_api):
    destination = tmp_path / "reviewed bundle"
    freeze(public_api, process_suite, destination)
    before = inventory(destination)
    rejected(public_api("freeze_suite"), process_suite, destination, match="exist|overwrite|destination")
    assert inventory(destination) == before


def test_frozen_execution_cannot_write_results_into_its_own_input_bundle(process_suite, tmp_path, public_api):
    bundle = tmp_path / "frozen"
    freeze(public_api, process_suite, bundle)
    before = inventory(bundle)
    rejected(public_api("run_frozen_suite"), bundle, bundle / "results", match="output|frozen|measurement|inside")
    assert inventory(bundle) == before


def test_cli_freeze_and_frozen_execution_share_the_public_contract(process_suite, tmp_path, public_api):
    bundle = tmp_path / "frozen"
    process = accepted(lambda: cli("freeze", "--suite", process_suite, "--destination", bundle,
                                  "--format", "json", cwd=tmp_path),
                       expected=lambda value: value.returncode == 0)
    assert process.stdout and (bundle / "measurement.json").is_file()
    process = accepted(lambda: cli("run-frozen", bundle, "--output", tmp_path / "results", "--format", "json", cwd=tmp_path),
                       expected=lambda value: value.returncode == 0)
    result = json.loads(process.stdout)
    gate_result = accepted(public_api("evaluate_gates"), result["output"],
                           expected=lambda value: value["gate_status"] == "passed")
    assert result["gate_evaluation"] == gate_result
