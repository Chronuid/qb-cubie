"""Resolve and archive trusted fake-run inputs before starting an episode."""

import importlib.util
import shutil
from pathlib import Path

from qb_cubie.benchmarks.adapters.fake import validate_fake
from qb_cubie.benchmarks.adapters.process import configuration, probe
from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.contracts.packages import load_package
from qb_cubie.benchmarks.planning._planning import _identity
from qb_cubie.benchmarks.reporting._files import copy_tree, inventory, write_json


def prepare(path, plan):
    """Validate executable suite inputs before creating run artifacts."""
    suite = v.read_data(path, toml=True)
    agents = _agents(path.parent, suite)
    packages = [(path.parent / entry["path"]).resolve() for entry in suite["sources"]]
    scenarios = _scenarios(packages)
    _layout(plan, scenarios)
    for run in plan["runs"]:
        _executable(run, agents[run["agent_id"]], scenarios[run["scenario_id"]])
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
    inputs = {"suite": ["inputs/suite.toml"], "plan": ["inputs/plan.json"],
              "agent": agent_paths, "packages": package_paths}
    return inputs, _scenarios([destination / "packages" / p["namespace"] for p in plan["packages"]])


def _agents(root, suite):
    """Load and validate supported fake-agent configurations."""
    result = {}
    for name in suite["agents"]:
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
            probe(entry["config"], entry["cwd"], required)


def _scenarios(packages):
    """Resolve scenario manifests and private references from local packages."""
    result = {}
    for root in packages:
        for scenario in load_package(root)["scenarios"]:
            base = (root / scenario["manifest"]).parent
            result[scenario["qualified_id"]] = {"scenario": scenario, "base": base,
                "reference": v.read_data(base / scenario["evaluator"]["reference"])}
    return result


def _executable(run, agent, material):
    """Validate runtime capabilities and private project test materials."""
    v.require(set(run["budgets"]) <= {"wall_time_seconds", "tool_calls"}, "budgets", "runner enforces wall time and its own tool invocations only")
    if run["benchmark"] == "developer_agent":
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
    shutil.copy2(source / "package.json", target / "package.json")


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
    v.require(len(names) == len(set(names)) and Path("task.md") not in names,
              "visible", "export names collide with each other or reserved task.md")
