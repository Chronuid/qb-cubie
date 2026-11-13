"""Persisted evidence must support the result independently of adapter claims."""

import hashlib
import json
from pathlib import Path

from .conftest import initialize_smoke


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_saved_plan_is_exactly_the_plan_used_by_public_api(smoke_suite, public_api, execute):
    initialize_smoke(public_api, smoke_suite)
    plan = public_api("plan_suite")(smoke_suite)
    result = execute()
    manifest = read_json(Path(result["output"]) / "manifest.json")
    assert manifest["plan"] == plan
    assert len(result["runs"]) == len(plan["runs"])
    for run, planned in zip(result["runs"], plan["runs"], strict=True):
        for key in ["scenario_id", "agent_id", "condition", "repetition", "budgets"]:
            assert run[key] == planned[key]


def test_json_and_markdown_preserve_failures_with_links_to_real_evidence(execute):
    result = execute("mutant", "developer_agent", "wrong-return")
    root = Path(result["output"])
    assert read_json(root / "results.json") == result
    report = (root / "report.md").read_text(encoding="utf-8")
    for run in result["runs"]:
        assert run["scenario_id"] in report and "returns_none" in report
        for relative in run["evidence"]:
            path = (root / relative).resolve()
            assert path.is_relative_to(root.resolve()) and path.is_file()
            assert relative in report


def test_artifact_hashes_match_archived_bytes_and_cover_evidence(execute):
    result = execute()
    root = Path(result["output"])
    manifest = read_json(root / "manifest.json")
    hashes = manifest["artifact_hashes"]
    assert hashes
    for name, digest in hashes.items():
        path = (root / name).resolve()
        assert path.is_relative_to(root.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    assert {name for r in result["runs"] for name in r["evidence"]} <= hashes.keys()


def test_manifest_identifies_configuration_and_archives_its_inputs(execute, smoke_suite):
    result = execute()
    root = Path(result["output"])
    manifest = read_json(root / "manifest.json")
    assert manifest["schema_version"] == 1 and manifest["run_id"] == result["run_id"]
    for field in ["suite_sha256", "resolved_plan_sha256"]:
        digest = manifest[field]
        assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
    assert manifest["python_version"]
    assert "wheel_sha256" in manifest  # null is honest when running from source.
    assert manifest["suite_sha256"] == hashlib.sha256(smoke_suite.read_bytes()).hexdigest()
    plan_files = manifest["inputs"]["plan"]
    assert len(plan_files) == 1
    assert manifest["resolved_plan_sha256"] == hashlib.sha256((root / plan_files[0]).read_bytes()).hexdigest()
    for key in ["suite", "plan", "agent", "packages"]:
        paths = manifest["inputs"][key]
        assert paths
        assert all(path in manifest["artifact_hashes"] for path in paths)
    for run in result["runs"]:
        for field in ["source_tree_sha256", "submitted_tree_sha256", "task_sha256", "context_sha256"]:
            assert len(run[field]) == 64
            assert all(c in "0123456789abcdef" for c in run[field])


def test_offline_fake_does_not_invent_model_usage(execute):
    for run in execute()["runs"]:
        assert run["usage"] == {"input_tokens": None, "output_tokens": None, "cost": None}
        assert run["agent_kind"] == "fake"
        assert run["model_id"] is None


def test_agent_export_contains_tasks_and_sources_but_no_evaluator_material(execute):
    result = execute()
    root = Path(result["output"])
    for run in result["runs"]:
        workspace = Path(run["workspace"])
        exported = read_json(root / run["export_manifest"])
        assert exported["task"] and exported["criteria"] and exported["files"]
        assert (workspace / "task.md").is_file()
        assert all((workspace / name).is_file() for name in exported["files"])
        assert not any("evaluator" in Path(name).parts for name in exported["files"])
        assert not list(workspace.rglob("reference.json"))
        assert not list(workspace.rglob("*.py.txt")), "Project sources must be usable .py files"
        if run["benchmark"] == "developer_agent":
            assert list(workspace.rglob("indexer.py"))
