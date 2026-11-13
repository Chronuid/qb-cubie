"""Freeze trusted local benchmark inputs and execute only their reviewed snapshot."""

import shutil
import tempfile
from pathlib import Path

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.execution import _inputs
from cubie_benchmarks.measurement import _bundle
from cubie_benchmarks.measurement._adapters import archive_adapters
from cubie_benchmarks.measurement._toml import write_toml
from cubie_benchmarks.planning.planner import plan_suite
from cubie_benchmarks.reporting._files import digest, write_json
from cubie_benchmarks.runner import execute_prepared


def freeze_suite(suite_path: str | Path, destination: str | Path) -> dict:
    """Publish a new portable input bundle without executing a capability probe or agent."""
    suite, destination = Path(suite_path).resolve(), Path(destination).resolve()
    v.require(not destination.exists(), "destination", "already exists; refusing overwrite")
    plan = plan_suite(suite)
    prepared = _inputs.prepare(suite, plan, probe_agents=False)
    _destination(destination, prepared)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".measurement-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "bundle"
        staging.mkdir()
        _freeze(staging, suite, prepared, plan)
        staging.rename(destination)
    return {"schema_version": 1, "path": str(destination), "measurement_sha256": digest(destination / "measurement.json")}


def _destination(destination, prepared):
    """Keep bundles outside declared scenario materials and adapter working directories."""
    roots = [material["base"] for material in _inputs._scenarios(prepared["packages"]).values()]
    roots.extend(entry["cwd"] for entry in prepared["agents"].values() if "container_image" not in entry["config"])
    v.require(not any(destination.is_relative_to(root) for root in roots), "destination", "must stay outside input material")


def _freeze(root, suite, prepared, plan):
    """Archive original inputs, normalize runtime paths and record a stable identity."""
    _inputs.archive(prepared, plan, root)
    shutil.copy2(suite, root / "inputs/original-suite.toml")
    archive_adapters(prepared, root)
    _suite(root, suite, prepared, plan)
    v.require(_bundle.portable(plan_suite(root / "inputs/suite.toml")) == _bundle.portable(plan),
              "measurement.plan", "inputs changed during freeze")
    write_json(root / "inputs/plan.json", _bundle.portable(plan))
    manifest = {"schema_version": 1, "suite": "inputs/suite.toml", "plan": _bundle.portable(plan),
                "runtime": _bundle.runtime(), "files": _bundle.files(root), "modes": _bundle.modes(root)}
    write_json(root / "measurement.json", manifest)


def _suite(root, suite, prepared, plan):
    """Resolve package and agent references relative to the bundled suite."""
    data = v.read_data(suite, toml=True)
    data["sources"] = [{"path": "packages/" + package["namespace"]} for package in plan["packages"]]
    repair_namespaces = {run["package"]["namespace"] for run in plan["runs"] if run.get("process_profile") == "issue_resolution"}
    for source in data["sources"]:
        namespace = source["path"].split("/")[-1]
        if namespace in repair_namespaces:
            source["reference_report"] = "references/" + namespace + "/report.json"
    _agents(data, suite, prepared)
    data["output"] = "../results"
    write_toml(root / "inputs/suite.toml", data)


def _agents(data, suite, prepared):
    """Resolve each configured agent to its bundled configuration file."""
    if "agent_pairs" in data:
        from cubie_benchmarks.planning.pairs import agent_paths
        names = {name: "agents/" + v.read_data(suite.parent / name, toml=True)["id"] + ".toml"
                 for name in agent_paths(data)}
        data["agent_pairs"] = [{**pair, **{arm: names[pair[arm]] for arm in ("cubie", "pytest")}}
                               for pair in data["agent_pairs"]]
    else:
        data["agents"] = ["agents/" + identifier + ".toml" for identifier in prepared["agents"]]


def run_frozen_suite(bundle_path: str | Path, output_path: str | Path) -> dict:
    """Execute a verified frozen bundle from disposable copies and archive its full contents."""
    bundle, output = Path(bundle_path).resolve(), Path(output_path).resolve()
    manifest = _bundle.verify(bundle)
    v.require(not output.is_relative_to(bundle), "output", "must stay outside frozen measurement")
    _bundle.check_runtime(manifest["runtime"])
    with tempfile.TemporaryDirectory(prefix="cubie-measurement-") as temporary:
        snapshot = Path(temporary) / "snapshot"
        _snapshot(bundle, snapshot, manifest)
        return _execute(snapshot, Path(temporary) / "runtime", output, manifest)


def _snapshot(bundle, snapshot, manifest):
    """Reject concurrent bundle changes while producing a verified immutable working copy."""
    shutil.copytree(bundle, snapshot)
    v.require(_bundle.verify(snapshot) == manifest, "measurement", "changed during copy")
    v.require(digest(snapshot / "measurement.json") == digest(bundle / "measurement.json"), "measurement", "changed during copy")


def _execute(snapshot, working, output, manifest):
    """Replan the copied inputs and require the exact frozen trial semantics before probing."""
    shutil.copytree(snapshot, working)
    suite = v.contained(working, manifest["suite"], "measurement.suite")
    plan = plan_suite(suite)
    v.require(_bundle.portable(plan) == manifest["plan"], "measurement.plan", "resolved plan differs from frozen plan")
    plan["output"] = str(output)
    prepared = _inputs.prepare(suite, plan)
    return execute_prepared(plan, prepared, (snapshot, digest(snapshot / "measurement.json")))
