"""Simulate separately supplied held-out material without publishing a measurement dataset."""

import json
import shutil
from pathlib import Path

import pytest

from ..contracts import accepted, edit_json, rejected
from ..phase3.conftest import traffic
from ..phase4.conftest import read_json, write_json


@pytest.fixture
def held_out_suite(process_suite):
    root = process_suite.parent.parent
    package = read_json(root / "package.json")
    package.update(namespace="private-fixture", version="2.1.0", dataset="dataset.json",
                   provenance="Synthetic held-out metadata fixture; no real unseen tasks or measurement.")
    write_json(root / "package.json", package)
    cases = {}
    for name in package["scenarios"]:
        path = root / name
        edit_json(path, lambda case: case.update(split="held_out"))
        case = read_json(path)
        cases[case["id"]] = {"origin": "Synthetic offline acceptance material, not a real private dataset",
                             "license": "MIT", "design_id": case["group_id"], "domain": "synthetic-shipping",
                             "potentially_known": False, "assessment": "executable"}
    write_json(root / "dataset.json", {"schema_version": 1, "publication_status": "held_out", "cases": cases})
    private = root / "scenarios/review-boundary/evaluator/private-sentinel.txt"
    private.write_text("PHASE5_PRIVATE_EVALUATOR_SENTINEL\n", encoding="utf-8")
    text = process_suite.read_text(encoding="utf-8").replace('benchmarks = ["review_agent"]',
                                                          'benchmarks = ["review_agent"]\nsplits = ["held_out"]')
    process_suite.write_text(text, encoding="utf-8")
    return process_suite


def test_existing_split_contract_accepts_external_scenarios_without_a_public_catalog(process_suite, public_api):
    root = process_suite.parent.parent
    for name in read_json(root / "package.json")["scenarios"]:
        edit_json(root / name, lambda case: case.update(split="held_out"))
    accepted(public_api("load_package"), root,
             expected=lambda value: all(case["split"] == "held_out" for case in value["scenarios"]))
    assert traffic(root) == []


def test_external_held_out_catalog_has_its_own_version_and_preserves_unknownness(held_out_suite, public_api):
    root = held_out_suite.parent.parent
    package = accepted(public_api("load_package"), root, expected=lambda value: (
        value["namespace"] == "private-fixture" and value["version"] == "2.1.0"))
    assert all(case["split"] == "held_out" for case in package["scenarios"])
    plan = accepted(public_api("plan_suite"), held_out_suite, expected=lambda value: len(value["runs"]) == 4)
    assert all(run["package"]["namespace"] == "private-fixture" and run["split"] == "held_out" for run in plan["runs"])
    assert traffic(root) == []


def test_evaluator_material_stays_out_of_held_out_agent_exports_and_requests(held_out_suite, public_api):
    result = accepted(public_api("run_suite"), held_out_suite, expected=lambda value: len(value["runs"]) == 4)
    root = Path(result["output"])
    assert all(run["quality_passed"] and run["split"] == "held_out" for run in result["runs"])
    for run in result["runs"]:
        export = read_json(root / run["export_manifest"])
        assert not any("evaluator" in Path(name).parts for name in export["files"])
        workspace = Path(run["workspace"])
        assert not list(workspace.rglob("reference.json")) and not list(workspace.rglob("private-sentinel.txt"))
        assert all(b"PHASE5_PRIVATE_EVALUATOR_SENTINEL" not in path.read_bytes()
                   for path in workspace.rglob("*") if path.is_file())
    requests = json.dumps([item["request"] for item in traffic(held_out_suite.parent.parent)])
    assert "PHASE5_PRIVATE_EVALUATOR_SENTINEL" not in requests and '"reference"' not in requests
    assert any(path.name == "private-sentinel.txt" for path in (root / "inputs").rglob("*"))
    summary = accepted(public_api("summarize_pilot"), [root], expected=lambda value: value["groups"])
    assert summary["measurement_kind"] == "infrastructure_only" and summary["warnings"]


def test_public_base_cases_cannot_be_relabelled_as_unseen_measurement_tasks(tmp_path, public_api):
    package = tmp_path / "public base"
    accepted(public_api("init_base_package"), package, expected=lambda value: package.is_dir())
    for name in read_json(package / "package.json")["scenarios"]:
        edit_json(package / name, lambda case: case.update(split="held_out"))
    rejected(public_api("load_package"), package, match="public|known|development|dataset")


def test_held_out_catalog_cannot_silently_contain_development_cases(held_out_suite, public_api):
    root = held_out_suite.parent.parent
    for name in read_json(root / "package.json")["scenarios"]:
        edit_json(root / name, lambda case: case.update(split="development"))
    rejected(public_api("load_package"), root, match="held_out|split|dataset|publication")


def test_held_out_catalog_is_part_of_the_frozen_measurement_identity(held_out_suite, tmp_path, public_api):
    freezer = public_api("freeze_suite")
    first = accepted(freezer, held_out_suite, tmp_path / "first", expected=lambda value: value["measurement_sha256"])
    catalog = held_out_suite.parent.parent / "dataset.json"
    edit_json(catalog, lambda data: data["cases"]["review-boundary"].update(origin="Revised synthetic provenance"))
    second = accepted(freezer, held_out_suite, tmp_path / "second", expected=lambda value: value["measurement_sha256"])
    assert first["measurement_sha256"] != second["measurement_sha256"]


def test_a_held_out_run_uses_an_external_package_without_core_changes(held_out_suite, tmp_path, public_api):
    root = held_out_suite.parent.parent
    moved = tmp_path / "separately provisioned evaluator package"
    shutil.move(root, moved)
    suite = moved / held_out_suite.relative_to(root)
    result = accepted(public_api("run_suite"), suite, expected=lambda value: len(value["runs"]) == 4)
    manifest = read_json(Path(result["output"]) / "manifest.json")
    assert any(name.endswith("dataset.json") for name in manifest["inputs"]["packages"])
    assert all(run["task_version"] == "2.1.0" for run in result["runs"])
