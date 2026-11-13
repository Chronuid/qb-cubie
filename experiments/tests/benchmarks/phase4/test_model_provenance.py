"""Test model declarations with an offline peer, without claiming provider execution."""

import json
import shutil
from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from ..phase3.conftest import FIXTURES, configure_agent, write_suite

MODEL = {"model_id": "synthetic/no-provider", "revision": "fixture-revision", "provider": "offline-test",
         "provider_version": "fixture-1", "adapter_version": "test-1", "parameters": {"temperature": 0.0},
         "prompt_sha256": "a" * 64}


@pytest.fixture
def declared_agent(tmp_path):
    root = tmp_path / "declared peer"
    shutil.copytree(FIXTURES, root)
    peer = root / "agents/jsonl_agent.py.txt"
    source = peer.read_text(encoding="utf-8").replace('emit(handshake())', f'emit({{**handshake(), "model": {MODEL!r}}})')
    peer.with_suffix("").write_text(source, encoding="utf-8")
    peer.unlink()
    agent = configure_agent(root)
    with agent.open("a", encoding="utf-8") as stream:
        stream.write('\n[model]\n' + ''.join(f'{key} = {json.dumps(value)}\n' for key, value in MODEL.items() if key != "parameters"))
        stream.write('\n[model.parameters]\ntemperature = 0.0\n')
    return root, agent


def test_live_model_declaration_is_bound_and_archived_but_remains_adapter_declared(declared_agent, public_api):
    root, agent = declared_agent
    checked = accepted(public_api("validate_agent"), agent, expected=lambda value: value["model_id"] == MODEL["model_id"])
    assert checked["model_provenance"] == {**MODEL, "source": "matched_agent_handshake"}
    result = accepted(public_api("run_suite"), write_suite(root, 'ids = ["shop/review-boundary"]'),
                      expected=lambda value: len(value["runs"]) == 1 and value["runs"][0]["quality_passed"] is True)
    run, = result["runs"]
    assert run["model_id"] == MODEL["model_id"] and run["model_provenance"] == checked["model_provenance"]
    archived = Path(result["output"])
    assert any('"model"' in path.read_text(encoding="utf-8") for path in archived.glob("episodes/*/transport/responses.jsonl"))
    summary = accepted(public_api("summarize_pilot"), [archived],
                       expected=lambda value: value["measurement_kind"] == "agent_evaluation")
    assert any("adapter-declared" in warning for warning in summary["warnings"])


def test_changed_model_configuration_cannot_reuse_a_different_live_declaration(declared_agent, public_api):
    _, agent = declared_agent
    agent.write_text(agent.read_text(encoding="utf-8").replace('fixture-revision', 'other-revision'), encoding="utf-8")
    rejected(public_api("validate_agent"), agent, match="model|declaration")


def test_incomplete_model_declaration_fails_before_any_peer_request(declared_agent, public_api):
    root, agent = declared_agent
    agent.write_text(agent.read_text(encoding="utf-8").replace('provider_version = "fixture-1"\n', ''), encoding="utf-8")
    rejected(public_api("validate_agent"), agent, match="model|fields")
    assert not (root / "agents/traffic.jsonl").exists()
