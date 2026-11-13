"""Create editable agent, scenario and suite templates from public resources."""

import json
import os
import sys
from importlib.resources import as_file, files
from pathlib import Path

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.contracts.packages import load_package
from cubie_benchmarks.reporting._files import copy_tree, write_json
from cubie_benchmarks.scaffolding.templates import (
    AGENT,
    SUITE,
    _review_sources,
    _write,
)


def init_agent(path: str | Path) -> dict:
    """Create an editable JSONL agent configuration without starting it."""
    path = Path(path).resolve()
    command = json.dumps([sys.executable, "-I", "agent.py"])
    text = AGENT.split("\n[fake]")[0].replace('id = "fake"', 'id = "own-agent"')
    text = text.replace('["builtin:fake"]', command)
    _available(path)
    _write(path, text + '\ntransport = "jsonl-v1"\ncwd = "."\n')
    return {"agent": str(path)}


def init_example(path: str | Path) -> dict:
    """Export the standalone shipping package and its offline JSONL peer."""
    path = Path(path).resolve()
    _available(path)
    with as_file(files("cubie_benchmarks").joinpath("data/shipping")) as source:
        copy_tree(source, path)
    _review_sources(path)
    script = path / "agents/jsonl_agent.py.txt"
    script.rename(script.with_suffix(""))
    agent = path / "agents/current.toml"
    init_agent(agent)
    agent.write_text(agent.read_text(encoding="utf-8").replace('"agent.py"', '"jsonl_agent.py"'), encoding="utf-8")
    return init_suite(path / "sets/team.toml", agent, path)


def init_scenario(path: str | Path, benchmark: str) -> dict:
    """Create a standalone package with one complete example scenario."""
    v.choice(benchmark, v.PHASES, "benchmark")
    path = Path(path).resolve()
    _available(path)
    name = "review-paid-correct" if benchmark == "review_agent" else "index-initial"
    with as_file(files("cubie_benchmarks").joinpath("data/smoke")) as source:
        copy_tree(source / "scenarios" / name, path / "scenarios" / name)
    _review_sources(path)
    write_json(path / "package.json", _package(name))
    return {"package": str(path)}


def _package(name):
    """Describe a new author-maintained development package."""
    return {"schema_version": 1, "namespace": "custom", "version": "1.0.0", "license": "MIT",
            "provenance": "Editable public example; references are author_checked, not agent measurements.",
            "scenarios": [f"scenarios/{name}/scenario.json"]}


def _available(path):
    """Refuse template creation over any existing file, directory or link."""
    v.require(not path.exists() and not path.is_symlink(), "destination", f"already exists; refusing overwrite: {path}")


def init_suite(path: str | Path, agent: str | Path, package: str | Path, *, pytest_agent: str | Path | None = None) -> dict:
    """Create a relocatable suite for one explicit agent and package."""
    path, agent, package = Path(path).resolve(), Path(agent).resolve(), Path(package).resolve()
    _available(path)
    v.read_data(agent, toml=True)
    scenarios = load_package(package)["scenarios"]
    text = SUITE.replace('["../agents/fake.toml"]', json.dumps([_relative(agent, path.parent)]))
    text = text.replace('"../scenarios/smoke"', json.dumps(_relative(package, path.parent)))
    text, count, extra = _comparison(text, path, agent, pytest_agent, scenarios)
    text = text.replace("max_runs = 3", f"max_runs = {count}")
    text = text.replace("max_total_wall_time_seconds = 60", f"max_total_wall_time_seconds = {count * 20}")
    _write(path, text)
    return {"suite": str(path), "agent": str(agent), "package": str(package), **extra}


def _relative(path, parent):
    """Render relocatable TOML paths using portable separators."""
    return Path(os.path.relpath(path, parent)).as_posix()


def _comparison(text, path, agent, pytest_agent, scenarios):
    """Select ordinary suite limits or validate an explicit comparison arm."""
    if pytest_agent is None:
        return text, len(scenarios), {}
    pytest_agent = Path(pytest_agent).resolve()
    v.read_data(pytest_agent, toml=True)
    count = 2 * sum(case["benchmark"] == "developer_agent" for case in scenarios)
    v.require(count > 0, "package", "comparison requires developer_agent tasks")
    return _paired_suite(text, path, agent, pytest_agent), count, {"pytest_agent": str(pytest_agent)}


def _paired_suite(text, path, agent, pytest_agent):
    """Render a developer comparison suite with separate agent configurations."""
    text = text.replace('profile = "agent-evaluation"', 'profile = "cubie-vs-pytest"')
    text = text.replace('agents = ' + json.dumps([_relative(agent, path.parent)]), '')
    text += ('\n[select]\nbenchmarks = ["developer_agent"]\n\n[[agent_pairs]]\nid = "developer"\n'
             + 'cubie = ' + json.dumps(_relative(agent, path.parent)) + '\n'
             + 'pytest = ' + json.dumps(_relative(pytest_agent, path.parent)) + '\n')
    return text
