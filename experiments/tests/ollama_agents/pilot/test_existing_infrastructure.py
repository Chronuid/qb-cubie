"""Independently verify the real infrastructure used behind the still missing pilot gate."""

import sys
import tomllib
from pathlib import Path

import pytest

from cubie_benchmarks import freeze_suite, run_frozen_suite, summarize_pilot

from ...benchmarks.contracts import accepted
from .support import inventory, read_json, suite_at


@pytest.mark.parametrize("profile,groups", [("agent-evaluation", 1), ("cubie-vs-pytest", 2)])
def test_real_five_repeat_execution_has_fresh_workspaces_and_no_private_references(tmp_path, profile, groups):
    suite = suite_at(tmp_path / "inputs", repetitions=5, profile=profile)
    bundle = tmp_path / "generic frozen suite"
    accepted(freeze_suite, suite, bundle, expected=lambda value: bool(value["measurement_sha256"]))
    before = inventory(bundle)
    result = accepted(run_frozen_suite, bundle, tmp_path / "results",
                      expected=lambda value: len(value["runs"]) == 10 * groups)
    summary = accepted(summarize_pilot, [result["output"]], expected=lambda value: (
        value["measurement_kind"] == "infrastructure_only" and len(value["groups"]) == groups))
    for group in summary["groups"]:
        assert group["counts"]["started"] == 10 and group["repetitions"] == [1, 2, 3, 4, 5]
        assert group["independent_groups"] == 1 and group["usage"]["cost"]["total"] is None
    assert len({run["workspace"] for run in result["runs"]}) == 10 * groups
    for run in result["runs"]:
        export = Path(result["output"]) / run["export_manifest"]
        assert not list((export.parent / "source").rglob("reference.json"))
    assert inventory(bundle) == before
    # This generic primitive deliberately accepts author references without calibration.
    assert "pilot" not in read_json(bundle / "measurement.json")


@pytest.mark.parametrize("old,new", [
    ('revision = "synthetic-digest"', 'revision = "other-digest"'),
    ('prompt_sha256 = "' + "a" * 64 + '"', 'prompt_sha256 = "' + "b" * 64 + '"'),
    ("temperature = 0", "temperature = 1"), ("seed = 42", "seed = 43"),
    ("num_ctx = 16384", "num_ctx = 8192"), ("num_predict = 2048", "num_predict = 4096"),
    ("think = false", "think = true"), ("max_model_calls = 6", "max_model_calls = 7"),
])
def test_model_prompt_and_internal_limits_change_the_frozen_identity_without_inference(tmp_path, old, new):
    suite = suite_at(tmp_path / "inputs", repetitions=5)
    agent = suite.parent.parent / "agents/fake.toml"
    adapter = agent.parent / "adapter.py"
    adapter.write_text("raise AssertionError('Freezing must never start an agent or model')\n", encoding="utf-8")
    agent.write_text('schema_version = 1\nid = "offline"\ntransport = "jsonl-v1"\ncwd = "."\n'
                     f'command = ["{sys.executable}", "-I", "adapter.py"]\n'
                     'capabilities = ["review_output", "cancel", "wall_time", "tool_calls"]\n'
                     '[model]\nmodel_id = "synthetic/no-provider"\nrevision = "synthetic-digest"\n'
                     'provider = "offline-test"\nprovider_version = "test-1"\nadapter_version = "test-1"\n'
                     'prompt_sha256 = "' + "a" * 64 + '"\n'
                     '[model.parameters]\ntemperature = 0\nseed = 42\nnum_ctx = 16384\nnum_predict = 2048\n'
                     'think = false\nmax_model_calls = 6\nmax_tool_calls = 12\n', encoding="utf-8")
    first = accepted(freeze_suite, suite, tmp_path / "first", expected=lambda value: value["measurement_sha256"])
    saved = tmp_path / "first/inputs/agents/offline.toml"
    assert tomllib.loads(saved.read_text(encoding="utf-8"))["model"] == tomllib.loads(agent.read_text(encoding="utf-8"))["model"]
    original = agent.read_text(encoding="utf-8")
    assert old in original
    agent.write_text(original.replace(old, new), encoding="utf-8")
    second = accepted(freeze_suite, suite, tmp_path / "second", expected=lambda value: value["measurement_sha256"])
    assert first["measurement_sha256"] != second["measurement_sha256"]
