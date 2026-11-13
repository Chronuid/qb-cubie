"""Assert actual reviewer artifacts, protocol contracts and independently read evidence."""

import json

from cubie_benchmarks.contracts.protocols import validate_agent_event

from ...benchmarks.contracts import accepted
from ..conftest import tree_bytes
from ..test_evidence_replays import verified_manifest
from .support import hashes, request, written_report


def completed(adapter, root, payload):
    before = tree_bytes(root)
    incoming = request(root)
    event = accepted(lambda: adapter.review(incoming), expected=lambda value: value["status"] == "completed")
    accepted(validate_agent_event, event, incoming, expected=event)
    assert event["type"] == "event" and event["artifacts"] == ["review.json"]
    assert event["artifact_hashes"] == {"review.json": hashes(root)["review.json"]}
    assert written_report(root) == payload
    assert tree_bytes(root) == {**before, "review.json": (root / "review.json").read_bytes()}
    return event


def interrupted(adapter, root, status):
    incoming = request(root)
    event = accepted(lambda: adapter.review(incoming), expected=lambda value: value["status"] == status)
    accepted(validate_agent_event, event, incoming, expected=event)
    assert event["type"] == "event" and event["reason"].strip()
    assert event["artifacts"] == [] and event["artifact_hashes"] == {}
    assert not (root / "review.json").exists()
    return event


def records(writer, tmp_path):
    summary = writer.finalize()
    manifest, archive = verified_manifest(summary, tmp_path / "archives")
    return [json.loads((archive / name).read_bytes()) for name in manifest["steps"]]
