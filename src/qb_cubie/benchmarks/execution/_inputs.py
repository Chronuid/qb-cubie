"""Resolve and archive trusted fake-run inputs before starting an episode."""

import importlib.util
import shutil
from pathlib import Path

from qb_cubie.benchmarks.adapters.fake import validate_fake
from qb_cubie.benchmarks.adapters.process import configuration, probe
from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.contracts.packages import load_package
from qb_cubie.benchmarks.planning._planning import _identity
from qb_cubie.benchmarks.planning.pairs import agent_paths
from qb_cubie.benchmarks.reporting._files import copy_tree, inventory, write_json


def prepare(path, plan, *, probe_agents=True):
    """Validate executable suite inputs before creating run artifacts."""
    suite = v.read_data(path, toml=True)
    agents = _agents(path.parent, suite)
    packages = [(path.parent / entry["path"]).resolve() for entry in suite["sources"]]
    scenarios = _scenarios(packages)
    _layout(plan, scenarios)
    for run in plan["runs"]:
        _executable(run, agents[run["agent_id"]], scenarios[run["scenario_id"]], check_runtime=probe_agents)
    if probe_agents:
        _probe(agents, plan)
    return {"suite": path, "agents": agents, "packages": list(dict.fromkeys(packages))}


def archive(prepared, plan, root):
    """Freeze suite inputs and resolve scenarios from the archived packages."""
    destination = root / "inputs"
    destination.mkdir()
    shutil.copy2(prepared["suite"], destination / "suite.toml")
    write_json(destination / "plan.json", plan)
    agent_paths = _archive_agents(prepared["agents"], destination)
    package_paths = _archive_packages(prepared["packages"], destination, plan)
    reports = _archive_reports(prepared, plan, destination, root)
    inputs = {"suite": ["inputs/suite.toml"], "plan": ["inputs/plan.json"],
              "agent": agent_paths, "packages": package_paths}
    if reports:
        inputs["reference_reports"] = sorted(set(reports))
    return inputs, _scenarios([destination / "packages" / p["namespace"] for p in plan["packages"]])


def _agents(root, suite):
    """Load and validate supported fake-agent configurations."""
    result = {}
    for name in agent_paths(suite):
        path = (root / name).resolve()
        agent = v.read_data(path, toml=True)
        cwd = path.parent
        if agent.get("command") == ["builtin:fake"]:
            validate_fake(agent)
        else:
            agent, cwd = configuration(path)
        result[agent["id"]] = {"path": path, "config": agent, "cwd": cwd}
    return result


def _probe(agents, plan):
    """Check selected process capabilities after all data-only preconditions."""
    for identifier in dict.fromkeys(run["agent_id"] for run in plan["runs"]):
        entry = agents[identifier]
        if entry["config"]["command"] != ["builtin:fake"]:
            required = {cap for run in plan["runs"] if run["agent_id"] == identifier for cap in run["required_capabilities"]}
            baseline = any(run["agent_id"] == identifier and run["condition"] == "pytest"
                           and run["benchmark"] == "developer_agent" for run in plan["runs"])
            probe(entry["config"], entry["cwd"], required, without_cubie=baseline)


def _scenarios(packages):
    """Resolve scenario manifests and private references from local packages."""
    result = {}
    for root in packages:
        for scenario in load_package(root)["scenarios"]:
            base = (root / scenario["manifest"]).parent
            result[scenario["qualified_id"]] = {"scenario": scenario, "base": base,
                "reference": v.read_data(base / scenario["evaluator"]["reference"])}
    return result


def _executable(run, agent, material, *, check_runtime=True):
    """Validate runtime capabilities and private project test materials."""
    v.require(set(run["budgets"]) <= {"wall_time_seconds", "tool_calls"}, "budgets", "runner enforces wall time and its own tool invocations only")
    if (run["benchmark"] == "developer_agent" and run["condition"] == "pytest"
            and agent["config"]["command"] != ["builtin:fake"]):
        from qb_cubie.benchmarks.swebench.agent import image
        image(agent["config"])
    if run.get("process_profile") == "issue_resolution":
        _repair_runtime(run, agent, material, check_runtime)
        return
    if run["benchmark"] == "developer_agent":
        _project_runtime(run, agent, material)


def _archive_agents(agents, destination):
    """Freeze agent configurations and reject concurrent changes."""
    directory = destination / "agents"
    directory.mkdir()
    for identifier, entry in agents.items():
        shutil.copy2(entry["path"], directory / f"{identifier}.toml")
        v.require(v.read_data(directory / f"{identifier}.toml", toml=True) == entry["config"],
                  "agent", "configuration changed while archiving")
    return [f"inputs/agents/{identifier}.toml" for identifier in agents]


def _archive_packages(packages, destination, plan):
    """Freeze scenario packages and verify their planned identities."""
    expected = {p["namespace"]: p for p in plan["packages"]}
    for source in packages:
        package = load_package(source)
        target = destination / "packages" / package["namespace"]
        if not target.exists():
            _copy_package(source, target, package)
        v.require(_identity(target, package) == expected[package["namespace"]], "package", "inputs changed after planning")
    return ["inputs/packages/" + name for name in inventory(destination / "packages")]


def _copy_package(source, target, package):
    """Copy scenario material without duplicating overlapping directories."""
    paths = {Path(s["manifest"]).parent for s in package["scenarios"]}
    copied: list[Path] = []
    for name in sorted(paths, key=lambda path: len(path.parts)):
        if any(name.is_relative_to(parent) for parent in copied):
            continue
        directory = source / name
        v.require(not any(p.is_symlink() for p in directory.rglob("*")), "package", "execution requires regular files")
        copy_tree(directory, target / name)
        copied.append(name)
    _copy_manifests(source, target, package)


def _copy_catalog(source, target, package):
    """Archive an optional declared provenance catalog alongside its package."""
    if "dataset" in package:
        destination = target / package["dataset"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(v.contained(source, package["dataset"], "dataset"), destination)


def _layout(plan, scenarios):
    """Reject result directories inside scenario material and unsupported symlinks."""
    output = Path(plan["output"])
    for material in scenarios.values():
        base = material["base"].resolve()
        v.require(not output.is_relative_to(base), "output", "results must stay outside scenario material")
        v.require(not any(p.is_symlink() for p in base.rglob("*")), "package", "execution requires regular files")
        _exports(material)


def _exports(material):
    """Reject collisions among exported filenames and reserved task material."""
    visible = material["base"] / material["scenario"]["visible"]
    paths = [p.relative_to(visible) for p in visible.rglob("*") if p.is_file()]
    names = [p.with_suffix("") if p.name.endswith(".py.txt") else p for p in paths]
    if material["scenario"].get("process_profile") == "issue_resolution":
        names = paths
    v.require(len(names) == len(set(names)) and Path("task.md") not in names,
              "visible", "export names collide with each other or reserved task.md")


def _archive_reports(prepared, plan, destination, root):
    """Archive reference reports and verify their planned admission hashes."""
    suite = v.read_data(prepared["suite"], toml=True)
    reports = []
    for source in suite["sources"]:
        if "reference_report" in source:
            reports.append(_archive_report(prepared, plan, destination, root, source))
    return reports


def _archive_report(prepared, plan, destination, root, source):
    """Copy one reference report and check its archived package binding."""
    from qb_cubie.benchmarks.swebench.admission import check_report, copy_report
    package = load_package(prepared["suite"].parent / source["path"])
    target = destination / "references" / package["namespace"] / "report.json"
    copy_report(prepared["suite"].parent / source["reference_report"], target)
    archived_package = destination / "packages" / package["namespace"]
    checksum = check_report(target, archived_package, load_package(archived_package))
    expected = {run["reference_report_sha256"] for run in plan["runs"]
                if run["package"]["namespace"] == package["namespace"] and "reference_report_sha256" in run}
    v.require(not expected or expected == {checksum}, "reference_report", "evidence changed after planning")
    return target.relative_to(root).as_posix()


def _repair_runtime(run, agent, material, check_runtime):
    """Validate repair adapter identity and the admitted evaluation image."""
    from qb_cubie.benchmarks.swebench.agent import image
    from qb_cubie.benchmarks.swebench.runtime import ContainerExecutor
    v.require(agent["config"]["command"] != ["builtin:fake"], "agent", "repair tasks require a project_patch adapter")
    image(agent["config"])
    if check_runtime:
        from qb_cubie.benchmarks.swebench.validation import request_for
        executor = ContainerExecutor(material["reference"]["harness_revision"])
        request = request_for(material["base"], material["reference"], "gold", Path("/tmp/cubie-preflight-unused"))
        environment = executor.prepare_request(request)["execution_environment"]
        v.require(environment["image_digest"] == run["reference_image_digest"], "reference_report", "evaluation image differs from reference validation")


def _project_runtime(run, agent, material):
    """Validate builtin project tests and fake-agent mutant selection."""
    v.require(importlib.util.find_spec("pytest") is not None, "benchmarks", "install qb-cubie[benchmarks]")
    reference, base = material["reference"], material["base"]
    tests = "agent_tests" if run["condition"] == "cubie" else "pytest_agent_tests"
    fake = agent["config"]["command"] == ["builtin:fake"]
    for field in ("acceptance_tests", tests) if fake else ("acceptance_tests",):
        v.contained(base, reference.get(field), field)
    v.relative(reference.get("submission_module"), "submission_module")
    if fake:
        mutant = agent["config"].get("fake", {}).get("mutant", "wrong-return")
        v.require(mutant in reference["mutants"], "fake.mutant", f"unknown mutant: {mutant}")


def _copy_manifests(source, target, package):
    """Copy package, catalog and optional import manifests together."""
    shutil.copy2(source / "package.json", target / "package.json")
    _copy_catalog(source, target, package)
    if "swebench_import" in package:
        shutil.copy2(source / package["swebench_import"], target / package["swebench_import"])
