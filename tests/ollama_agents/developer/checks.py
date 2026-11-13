"""EBT phase observations, protocol validation and byte-bound artifact checks."""

from cubie_benchmarks.contracts.protocols import validate_agent_event

from ...benchmarks.contracts import accepted
from .support import hashes, request


def phase(adapter, root, name, status="completed"):
    incoming = request(root, name)
    event = accepted(lambda: adapter.develop(incoming), expected=lambda value: value["status"] == status)
    accepted(validate_agent_event, event, incoming, expected=event)
    assert event["type"] == "event"
    if status == "completed":
        actual = hashes(root)
        assert set(event["artifact_hashes"]) == set(event["artifacts"])
        assert event["artifact_hashes"] == {path: actual[path] for path in event["artifacts"]}
    else:
        assert event["reason"].strip()
        assert event["artifacts"] == [] and event["artifact_hashes"] == {}
    return event
