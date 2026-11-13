"""Full-context inclusion, immutable originals and private-source boundaries."""

import json

import pytest

from ..conftest import tree_bytes
from .checks import completed, interrupted, records
from .support import SOURCES, hashes, report, response, setup_session, submit


def test_every_original_is_in_the_actual_model_request_with_current_hash(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    before = tree_bytes(root)
    adapter, transport, writer = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    completed(adapter, root, report())
    body = json.loads(transport.requests[0][0].data)
    context = json.dumps(body["messages"], ensure_ascii=False)
    messages = "\n".join(message["content"] for message in body["messages"])
    for name in SOURCES:
        assert name in context and hashes(root)[name] in context
        text = before[name].decode("utf-8")
        representations = [text, json.dumps(text, ensure_ascii=False)[1:-1], json.dumps(text)[1:-1]]
        assert any(value in messages for value in representations)
    steps = records(writer, tmp_path)
    assert any(step["request"]["messages"] == body["messages"] for step in steps)


@pytest.mark.parametrize("sources", [[], ["escaping.py", "renderer.py", "tests/test_renderer.py"],
                                    ["escaping.py", "task.md"], SOURCES + ["review.json"],
                                    SOURCES + ["task.md"], SOURCES + ["../reference.json"]],
                         ids=["none", "task-missing", "partial", "output-is-not-source", "duplicate", "private"])
def test_sources_must_equal_the_complete_exported_inventory(api, reviewer_api, review_workspace, tmp_path, sources):
    root = review_workspace()
    payload = report()
    payload["sources"] = sources
    adapter, _, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(payload))] * 2)
    interrupted(adapter, root, "invalid_output")


@pytest.mark.parametrize("name,operation", [("escaping.py", "replace"), ("task.md", "replace"),
                                          ("renderer.py", "delete"), ("extra.py", "add")])
def test_changed_removed_or_added_original_context_blocks_publication(api, reviewer_api, review_workspace, tmp_path, name, operation):
    root = review_workspace()
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    original = transport.__class__.__call__

    def change_during_inference(self, outgoing, *, timeout):
        path = root / name
        path.unlink() if operation == "delete" else path.write_bytes(b"externally changed\n")
        return original(self, outgoing, timeout=timeout)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(transport.__class__, "__call__", change_during_inference)
        interrupted(adapter, root, "invalid_output")


def test_invalid_utf8_source_is_rejected_before_inference(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    (root / "renderer.py").write_bytes(b"\xff\xfe invalid UTF-8")
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    interrupted(adapter, root, "invalid_output")
    assert not transport.requests


def test_private_sibling_is_never_part_of_initial_context(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    (root.parent / "reference.json").write_text("PRIVATE_REFERENCE_SENTINEL", encoding="utf-8")
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    completed(adapter, root, report())
    assert all(b"PRIVATE_REFERENCE_SENTINEL" not in outgoing.data for outgoing, _ in transport.requests)


def test_symlink_in_exported_sources_fails_before_inference(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    private = root.parent / "private.py"
    private.write_text("PRIVATE_SYMLINK_SENTINEL", encoding="utf-8")
    (root / "escaping.py").unlink()
    (root / "escaping.py").symlink_to(private)
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    interrupted(adapter, root, "invalid_output")
    assert not transport.requests and private.read_text() == "PRIVATE_SYMLINK_SENTINEL"


def test_small_context_overflow_is_explicit_without_truncation_or_model_call(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    (root / "task.md").write_text("visible requirement " * 10000, encoding="utf-8")
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    interrupted(adapter, root, "budget_exceeded")
    assert not transport.requests
