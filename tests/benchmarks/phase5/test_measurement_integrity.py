"""Cover runtime provenance, permission modes, helper resources and archived freeze identity."""

import os
import shutil
import sys
import tomllib
from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from ..phase4.conftest import read_json, replace_observation, write_json
from .conftest import append_gate
from .test_frozen_measurements import freeze


def test_bundle_can_live_in_a_project_beside_its_declared_scenarios(process_suite, tmp_path, public_api):
    bundle = process_suite.parent.parent / "frozen/team"
    freeze(public_api, process_suite, bundle)
    result = accepted(public_api("run_frozen_suite"), bundle, tmp_path / "results", expected=lambda value: value["runs"])
    assert len(result["runs"]) == 4 and all(run["status"] == "completed" for run in result["runs"])


def test_frozen_python_adapter_uses_the_provisioned_runtime_instead_of_a_host_path(process_suite, tmp_path, public_api):
    bundle = tmp_path / "frozen"
    freeze(public_api, process_suite, bundle)
    agent = tomllib.loads((bundle / "inputs/agents/own-agent.toml").read_text(encoding="utf-8"))
    assert agent["command"][0] == Path(sys.executable).name
    assert not Path(agent["command"][0]).is_absolute()
    result = accepted(public_api("run_frozen_suite"), bundle, tmp_path / "results", expected=lambda value: value["runs"])
    assert all(run["status"] == "completed" for run in result["runs"])


def test_declared_adapter_resources_survive_freezing_and_removal_of_originals(process_suite, tmp_path, public_api):
    root = process_suite.parent.parent
    resource = root / "agents/resources/session.json"
    resource.parent.mkdir()
    write_json(resource, {"session": "fixed-resource-session"})
    agent = root / "agents/current.toml"
    agent.write_text(agent.read_text(encoding="utf-8") + '\nadapter_files = ["resources"]\n', encoding="utf-8")
    source = root / "agents/jsonl_agent.py"
    text = source.read_text(encoding="utf-8").replace('SESSION = uuid.uuid4().hex',
        'SESSION = json.loads((Path(__file__).parent / "resources/session.json").read_text())["session"]')
    source.write_text(text, encoding="utf-8")
    bundle = tmp_path / "frozen"
    freeze(public_api, process_suite, bundle)
    shutil.rmtree(root)
    accepted(public_api("run_frozen_suite"), bundle, tmp_path / "results", expected=lambda result: (
        len(result["runs"]) == 4 and all(run["status"] == "completed" for run in result["runs"])))


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission mode distinction")
def test_changed_frozen_permissions_are_rejected_before_execution(process_suite, tmp_path, public_api):
    bundle = tmp_path / "frozen"
    freeze(public_api, process_suite, bundle)
    script = next(bundle.rglob("jsonl_agent.py"))
    script.chmod(script.stat().st_mode ^ 0o100)
    rejected(public_api("run_frozen_suite"), bundle, tmp_path / "results", match="mode|permission")
    assert not (tmp_path / "results").exists()


@pytest.mark.parametrize("field,value", [("python_version", "3.1.0"), ("wheel_sha256", "0" * 64),
                                        ("source_sha256", "0" * 64), ("python_version", None), ("source_sha256", None)])
def test_frozen_runtime_mismatches_are_configuration_errors(process_suite, tmp_path, public_api, field, value):
    bundle = tmp_path / "frozen"
    freeze(public_api, process_suite, bundle)
    manifest = read_json(bundle / "measurement.json")
    manifest["runtime"][field] = value
    write_json(bundle / "measurement.json", manifest)
    rejected(public_api("run_frozen_suite"), bundle, tmp_path / "results", match="runtime|different")
    assert not (tmp_path / "results").exists()


def test_archived_measurement_identity_is_recomputed_by_gate_inspection(process_suite, tmp_path, public_api):
    bundle = tmp_path / "frozen"
    freeze(public_api, process_suite, bundle)
    result = accepted(public_api("run_frozen_suite"), bundle, tmp_path / "results", expected=lambda value: value["runs"])
    root = Path(result["output"])
    manifest = read_json(root / "manifest.json")
    manifest["measurement_sha256"] = "0" * 64
    write_json(root / "manifest.json", manifest)
    rejected(public_api("evaluate_gates"), root, match="measurement|hash|identity")


def test_partly_known_costs_cannot_satisfy_an_upper_limit(measurement_suite, public_api):
    append_gate(measurement_suite, metric="cost", operator="lte", threshold=10.0)
    result = accepted(public_api("run_suite"), measurement_suite, expected=lambda value: len(value["runs"]) == 2)
    replace_observation(Path(result["output"]), 0, usage={"input_tokens": None, "output_tokens": None, "cost": 1.0})
    evaluation = accepted(public_api("evaluate_gates"), result["output"], expected=lambda value: value["gate_status"] == "failed")
    gate, = evaluation["gates"]
    assert gate["value"] is None and gate["observed_count"] == 1 and gate["required_count"] == 2
