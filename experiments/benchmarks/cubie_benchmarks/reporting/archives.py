"""Verify archived evidence and bind observations to their resolved trial plan."""

from pathlib import Path

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.reporting._files import digest, tree_hash


def read_archive(path):
    """Check archived bytes and bind all trial records to the saved plan."""
    root = Path(path).resolve()
    result = v.read_data(root / "results.json")
    manifest = v.read_data(root / "manifest.json")
    v.require(result.get("run_id") == manifest.get("run_id"), "run_id", "result does not match manifest")
    hashes = _hashes(root, manifest)
    _plan(root, manifest, result)
    _inputs(root, manifest, hashes)
    _measurement(root, manifest)
    _evidence(root, hashes, result)
    return result


def _measurement(root, manifest):
    """Bind frozen measurement contents and trial semantics to the result manifest."""
    from cubie_benchmarks.measurement._bundle import portable, verify
    checksum = manifest.get("measurement_sha256")
    paths = manifest["inputs"].get("measurement")
    v.require((checksum is None) == (paths is None), "measurement", "incomplete measurement provenance")
    if paths is None:
        return
    v.require(len(paths) == 1, "measurement", "expected one frozen manifest")
    path = v.contained(root, paths[0], "measurement")
    v.require(digest(path) == checksum, "measurement.hash", "frozen manifest differs from measurement identity")
    frozen = verify(path.parent)
    v.require(portable(manifest["plan"]) == frozen["plan"], "measurement.plan", "execution differs from frozen plan")


def _hashes(root, manifest):
    """Verify all declared content digests before consuming archived inputs."""
    hashes = v.mapping(manifest.get("artifact_hashes"), "manifest.artifact_hashes")
    v.require("results.json" in hashes, "manifest", "results.json is not hashed")
    for name, checksum in hashes.items():
        v.require(digest(v.contained(root, name, "manifest.artifact_hashes")) == checksum,
                  "manifest.hash", f"archived bytes changed: {name}")
    return hashes


def _evidence(root, hashes, result):
    """Require each cited artifact to be present and covered by archive hashes."""
    for run in result["runs"]:
        paths = v.strings(run.get("evidence"), "evidence", nonempty=True)
        for name in paths:
            v.require(name in hashes, "evidence", f"unhashed artifact: {name}")
            v.contained(root, name, "evidence")
        _sources(root, hashes, run)


def _inputs(root, manifest, hashes):
    """Bind archived configurations and declared package inputs to their hashes."""
    for paths in v.mapping(manifest["inputs"], "manifest.inputs").values():
        for name in v.strings(paths, "manifest.inputs", nonempty=True):
            v.require(name in hashes, "manifest.inputs", f"unhashed input: {name}")
    name, = manifest["inputs"]["suite"]
    v.require(digest(v.contained(root, name, "manifest.suite")) == manifest.get("suite_sha256"),
              "manifest.suite", "suite hash mismatch")


def _sources(root, hashes, run):
    """Recompute source and task identities from archived content, including modes."""
    name = run["export_manifest"]
    v.require(name in hashes, "export_manifest", "export is not hashed")
    export = v.contained(root, name, "export_manifest")
    source = export.parent / "source"
    checksum = tree_hash(source)
    v.require(source.is_dir() and checksum == run["source_tree_sha256"] == run["context_sha256"],
              "archive.sources", "source or context hash differs from archived source tree")
    v.require(digest(source / "task.md") == run["task_sha256"], "archive.task", "task hash differs from archived bytes")


def _plan(root, manifest, result):
    """Verify the stored plan and each result's resolved trial identity."""
    name, = manifest["inputs"]["plan"]
    path = v.contained(root, name, "manifest.plan")
    v.require(digest(path) == manifest.get("resolved_plan_sha256"), "manifest.plan", "plan hash mismatch")
    plan = v.read_data(path)
    v.require(plan == manifest.get("plan"), "manifest.plan", "stored plan differs")
    runs = result.get("runs")
    v.require(type(runs) is list and len(runs) == len(plan["runs"]), "runs", "trial count differs from plan")
    for run, planned in zip(runs, plan["runs"], strict=True):
        v.mapping(run, "runs")
        v.require(all(run.get(key) == value for key, value in planned.items()), "runs", "trial differs from plan")


