"""Exercise the real HTTP wrapper, failure evidence and additional recovery boundaries offline."""

import base64
import http.client
import io
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from ..benchmarks.contracts import accepted
from .conftest import (
    ACTION,
    MESSAGES,
    WRITE_SCHEMA,
    ReplayTransport,
    chat,
    client,
    tree_bytes,
)
from .contracts import failed
from .test_evidence_replays import step, verified_manifest
from .test_workspace_policy import policy


def test_default_http_transport_uses_the_request_deadline_without_starting_a_model(api, response, monkeypatch):
    calls = []

    def open_response(request, *, timeout):
        calls.append((request, timeout))
        return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(urllib.request, "urlopen", open_response)
    adapter = api("OllamaClient")(endpoint="http://localhost:11434", model="gemma4:12b", options={})
    accepted(lambda: chat(adapter), expected={
        "action": ACTION, "usage": {"input_tokens": 13, "output_tokens": 7, "cost": None}, "raw": response,
    })
    assert len(calls) == 1 and calls[0][1] == 4.5
    assert calls[0][0].full_url == "http://localhost:11434/api/chat"


@pytest.mark.parametrize("error,status", [
    (urllib.error.URLError(TimeoutError("read timed out")), "agent_timeout"),
    (urllib.error.HTTPError("http://localhost:11434/api/chat", 503, "unavailable", {}, None), "infrastructure_error"),
    (http.client.IncompleteRead(b"partial-response"), "infrastructure_error"),
], ids=["wrapped-timeout", "http-unavailable", "incomplete-response"])
def test_standard_library_transport_failures_are_classified(api, monkeypatch, error, status):
    calls = []

    def open_response(request, *, timeout):
        calls.append(request)
        raise error

    monkeypatch.setattr(urllib.request, "urlopen", open_response)
    adapter = api("OllamaClient")(endpoint="http://localhost:11434", model="gemma4:12b", options={})
    failed(lambda: chat(adapter), status=status, match="provider|timeout|response")
    assert len(calls) == 1


def test_invalid_model_output_keeps_raw_response_and_usage_for_the_same_attempt(api, response):
    response["done_reason"] = "length"
    adapter = client(api, ReplayTransport(response))

    def observe():
        try:
            chat(adapter)
        except ValueError as error:
            return {"status": error.status, "raw": error.raw, "usage": error.usage}
        return None

    accepted(observe, expected={"status": "invalid_output", "raw": response,
                               "usage": {"input_tokens": 13, "output_tokens": 7, "cost": None}})


@pytest.mark.parametrize("body", [b"invalid-utf8-\xff", b'{"content":"\\ud800"}'],
                         ids=["invalid-wire-utf8", "unpaired-unicode-surrogate"])
def test_malformed_wire_bytes_can_be_archived_without_loss(api, workspace, tmp_path, body):
    adapter = client(api, ReplayTransport(body))
    writer = api("EvidenceWriter")(archive_root=tmp_path / "archives", workspace=workspace)

    def record_failure():
        try:
            chat(adapter)
        except ValueError as error:
            writer.record_step(**step(raw_response=error.raw, usage=error.usage, status=error.status))
            return writer.finalize()
        return None

    summary = accepted(record_failure, expected=lambda value: bool(value.get("archive_id")))
    manifest, root = verified_manifest(summary, tmp_path / "archives")
    record = json.loads((root / manifest["steps"][0]).read_bytes())
    assert record["raw_response"]["encoding"] == "base64"
    assert base64.b64decode(record["raw_response"]["data"]) == body
    assert record["usage"] == {"input_tokens": None, "output_tokens": None, "cost": None}


def test_unsupported_schema_cannot_silently_relax_validation(api, response):
    transport = ReplayTransport(response)
    adapter = client(api, transport)
    schema = {**WRITE_SCHEMA, "$ref": "some-unimplemented-schema.json"}
    failed(lambda: adapter.chat(messages=MESSAGES, schema=schema, timeout=4.5),
           status="infrastructure_error", match="schema|unsupported")
    assert transport.requests == []


def test_second_commit_failure_removes_an_already_published_new_file(api, workspace, monkeypatch):
    access = policy(api, workspace, writable=["fresh/module.py", "src/fee.py"])
    before = tree_bytes(workspace)
    original = os.replace

    def fail_existing(source, destination, *args, **kwargs):
        if Path(destination) == workspace / "src/fee.py":
            assert (workspace / "fresh/module.py").read_bytes() == b"# new\n"
            raise OSError("simulated second commit failure")
        return original(source, destination, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fail_existing)
    failed(lambda: access.write_files({"fresh/module.py": "# new\n", "src/fee.py": "# changed\n"}),
           status="infrastructure_error", match="commit|write")
    assert tree_bytes(workspace) == before and not (workspace / "fresh").exists()


def test_nonencodable_second_file_is_rejected_before_any_change(api, workspace):
    access = policy(api, workspace)
    before = tree_bytes(workspace)
    failed(lambda: access.write_files({"src/fee.py": "# changed\n", "src/new.py": "\ud800"}),
           status="invalid_output", match="encoding|utf")
    assert tree_bytes(workspace) == before


def test_archive_tampering_prevents_successful_finalization(api, workspace, tmp_path):
    archive_root = tmp_path / "archives"
    writer = api("EvidenceWriter")(archive_root=archive_root, workspace=workspace)
    writer.record_step(**step())
    recorded, = archive_root.glob("*/step-*.json")
    recorded.write_text('{"tampered":true}', encoding="utf-8")
    failed(writer.finalize, status="infrastructure_error", match="hash|evidence")
    assert not list(archive_root.glob("*/manifest.json"))


def test_finalized_archive_is_immutable_and_repeated_finalization_is_verifiable(api, workspace, tmp_path):
    writer = api("EvidenceWriter")(archive_root=tmp_path / "archives", workspace=workspace)
    writer.record_step(**step())
    summary = accepted(writer.finalize, expected=lambda value: bool(value.get("manifest_sha256")))
    accepted(writer.finalize, expected=summary)
    before = tree_bytes(tmp_path / "archives")
    failed(lambda: writer.record_step(**step()), status="infrastructure_error", match="finalized")
    assert tree_bytes(tmp_path / "archives") == before
