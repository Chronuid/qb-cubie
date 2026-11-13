"""Archive complete replay steps outside the workspace and verify all hashes independently."""

import hashlib
import json
from pathlib import Path

import pytest

from ..benchmarks.contracts import accepted
from .conftest import (
    ACTION,
    MESSAGES,
    WRITE_SCHEMA,
    ReplayTransport,
    client,
    tree_bytes,
)
from .contracts import failed


def step(**changes):
    return {"phase": "green", "request": {"messages": MESSAGES, "format": WRITE_SCHEMA},
            "raw_response": '{"message":{"content":"invalid JSON"}}', "action": None,
            "tool_result": None, "artifact_hashes": {}, "duration_seconds": 0.25,
            "usage": {"input_tokens": 13, "output_tokens": 7, "cost": None},
            "status": "invalid_output", **changes}


def verified_manifest(summary, archive_root):
    manifest_path = Path(summary["manifest_path"])
    assert manifest_path.is_relative_to(archive_root)
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == summary["manifest_sha256"]
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["schema_version"] == 1 and manifest["archive_id"] == summary["archive_id"]
    assert manifest["artifact_hashes"], "An empty archive cannot substantiate a model step"
    for name, digest in manifest["artifact_hashes"].items():
        path = manifest_path.parent / name
        assert not Path(name).is_absolute() and ".." not in Path(name).parts
        assert path.is_file() and not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    actual = {p.relative_to(manifest_path.parent).as_posix() for p in manifest_path.parent.rglob("*")
              if p.is_file() and p != manifest_path}
    assert actual == set(manifest["artifact_hashes"])
    return manifest, manifest_path.parent


def test_invalid_raw_response_and_validation_failure_are_retained_without_stdout(api, workspace, tmp_path, capsys):
    archive_root = tmp_path / "adapter archives"
    before = tree_bytes(workspace)
    writer = api("EvidenceWriter")(archive_root=archive_root, workspace=workspace)
    record = step()
    writer.record_step(**record)
    summary = accepted(writer.finalize, expected=lambda value: bool(value.get("manifest_sha256")))
    manifest, root = verified_manifest(summary, archive_root)
    assert len(manifest["steps"]) == 1
    assert json.loads((root / manifest["steps"][0]).read_bytes()) == record
    assert tree_bytes(workspace) == before
    output = capsys.readouterr()
    assert output.out == ""
    assert summary["archive_id"] in output.err and summary["manifest_sha256"] in output.err
    assert len(output.err.encode()) < 4 * 1024 * 1024


def test_large_raw_response_stays_in_archive_and_diagnostics_remain_small(api, workspace, tmp_path, capsys):
    archive_root = tmp_path / "archives"
    writer = api("EvidenceWriter")(archive_root=archive_root, workspace=workspace)
    record = step(raw_response="raw-model-evidence-" * 250000)
    writer.record_step(**record)
    summary = accepted(writer.finalize, expected=lambda value: bool(value.get("manifest_sha256")))
    manifest, root = verified_manifest(summary, archive_root)
    assert json.loads((root / manifest["steps"][0]).read_bytes()) == record
    output = capsys.readouterr()
    assert output.out == "" and len(output.err.encode()) < 65536
    assert record["raw_response"] not in output.err


@pytest.mark.parametrize("suffix", [".", "evidence"], ids=["workspace-itself", "workspace-child"])
def test_evidence_archive_cannot_be_placed_inside_visible_workspace(api, workspace, suffix):
    before = tree_bytes(workspace)
    failed(lambda: api("EvidenceWriter")(archive_root=workspace / suffix, workspace=workspace),
           status="invalid_output", match="archive|workspace|outside")
    assert tree_bytes(workspace) == before
    assert not (workspace / "evidence").exists()


def test_symlink_archive_parent_cannot_route_evidence_back_into_workspace(api, workspace, tmp_path):
    link = tmp_path / "archive-link"
    link.symlink_to(workspace, target_is_directory=True)
    failed(lambda: api("EvidenceWriter")(archive_root=link / "evidence", workspace=workspace),
           status="invalid_output", match="archive|workspace|outside|symlink")
    assert not (workspace / "evidence").exists()


def test_fresh_writers_keep_separate_archives_instead_of_overwriting_evidence(api, workspace, tmp_path):
    archive_root = tmp_path / "archives"
    writer_type = api("EvidenceWriter")
    summaries = []
    for raw in ("first-session-sentinel", "second-session-sentinel"):
        writer = writer_type(archive_root=archive_root, workspace=workspace)
        writer.record_step(**step(raw_response=raw))
        summaries.append(accepted(writer.finalize, expected=lambda value: bool(value.get("archive_id"))))
    assert summaries[0]["archive_id"] != summaries[1]["archive_id"]
    for summary, raw in zip(summaries, ("first-session-sentinel", "second-session-sentinel"), strict=True):
        manifest, root = verified_manifest(summary, archive_root)
        assert len(manifest["steps"]) == 1
        assert json.loads((root / manifest["steps"][0]).read_bytes())["raw_response"] == raw


def test_offline_replay_connects_client_budget_workspace_and_evidence(api, response, workspace, tmp_path):
    transport = ReplayTransport(response)
    adapter = client(api, transport)
    budget = api("BudgetLedger")(wall_time_seconds=30, max_model_calls=2, max_tool_calls=3,
                               reserve_seconds=5, clock=lambda: 100.0)
    policy = api("WorkspacePolicy")(root=workspace, readable=["src/fee.py"], writable=["src/fee.py"])
    writer = api("EvidenceWriter")(archive_root=tmp_path / "archives", workspace=workspace)

    def replay():
        timeout = budget.claim_model()
        result = adapter.chat(messages=MESSAGES, schema=WRITE_SCHEMA, timeout=timeout)
        budget.record_usage(input_tokens=result["usage"]["input_tokens"], output_tokens=result["usage"]["output_tokens"])
        budget.claim_tool()
        hashes = policy.write_files(result["action"]["files"])
        writer.record_step(**step(raw_response=result["raw"], action=result["action"], status="completed",
                                  tool_result={"written": sorted(hashes)}, artifact_hashes=hashes, usage=budget.usage()))
        return {"hashes": hashes, "usage": budget.usage(), "evidence": writer.finalize()}

    digest = hashlib.sha256(ACTION["files"]["src/fee.py"].encode()).hexdigest()
    result = accepted(replay, expected=lambda value: value["hashes"] == {"src/fee.py": digest}
                      and value["usage"] == {"input_tokens": 13, "output_tokens": 7, "cost": None})
    assert hashlib.sha256((workspace / "src/fee.py").read_bytes()).hexdigest() == digest
    assert len(transport.requests) == 1 and transport.requests[0][1] == 25.0
    manifest, root = verified_manifest(result["evidence"], tmp_path / "archives")
    record = json.loads((root / manifest["steps"][0]).read_bytes())
    assert record["raw_response"] == response and record["action"] == ACTION
    assert record["artifact_hashes"] == result["hashes"]
