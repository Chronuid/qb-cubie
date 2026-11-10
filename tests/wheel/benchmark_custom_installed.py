"""Phase 10.3 tutorial workflow from an installed wheel and an external example."""

import importlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from qb_cubie import EBT, WorldState


def contract(target, *args, expected):
    trace = EBT(target=target, pre=WorldState(args=args),
                post=WorldState(returns=expected), reporter=None).run()
    assert trace.evaluation is True and trace.traces[0].evaluation is True
    return trace.traces[0].outcome.returns


def cli(*args, cwd):
    command = Path(sys.executable).parent / ("cubie-bench.exe" if os.name == "nt" else "cubie-bench")
    return subprocess.run([str(command), *map(str, args)], cwd=cwd, capture_output=True,
                          text=True, timeout=30, check=False)


@pytest.fixture
def own_example(tmp_path):
    source = Path(__file__).parent / "phase3-example"
    assert source.is_dir(), "Wheel harness must export the public phase-10.3 example"
    root = tmp_path / "my independent project"
    shutil.copytree(source, root)
    script = root / "agents/jsonl_agent.py.txt"
    script.rename(script.with_suffix(""))
    return root


def configure(path):
    template = tomllib.loads(path.read_text(encoding="utf-8"))
    data = {"schema_version": template["schema_version"], "id": "own-agent", "transport": "jsonl-v1", "cwd": ".",
            "command": [sys.executable, "-I", "jsonl_agent.py"],
            "capabilities": ["review_output", "workspace_changes", "phased_submission", "cancel", "wall_time", "tool_calls"]}
    path.write_text("\n".join(f"{key} = {json.dumps(value)}" for key, value in data.items()) + "\n", encoding="utf-8")


def test_installed_wheel_exposes_custom_workflow_commands(own_example):
    module = importlib.import_module("qb_cubie.benchmarks")
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    contract(lambda: cli("--help", cwd=own_example), expected=lambda p: p.returncode == 0 and all(
        name in p.stdout for name in ["init-agent", "validate-agent", "init-scenario", "validate", "list", "compare"]))


def test_installed_example_and_guide_need_no_repository_fixture(tmp_path):
    destination = tmp_path / "standalone shipping"
    contract(lambda: cli("init-example", destination, cwd=tmp_path), expected=lambda p: p.returncode == 0)
    guide = contract(lambda: cli("guide", cwd=tmp_path), expected=lambda p: p.returncode == 0)
    assert "init-example" in guide.stdout and "validate-agent" in guide.stdout
    run_cli(destination / "sets/team.toml", tmp_path)


def test_tutorial_connects_one_agent_and_one_external_package_without_checkout(own_example):
    agent = own_example / "agents/current.toml"
    contract(lambda: cli("init-agent", agent, "--format", "json", cwd=own_example), expected=lambda p: p.returncode == 0)
    configure(agent)
    for arguments in [("validate-agent", agent), ("validate", own_example, "--check-references"),
                      ("list", "--package", own_example)]:
        contract(lambda arguments=arguments: cli(*arguments, "--format", "json", cwd=own_example.parent), expected=lambda p: p.returncode == 0)
    suite = own_example / "sets/team.toml"
    contract(lambda: cli("init-suite", suite, "--preset", "smoke", "--agent", agent, "--package", own_example,
                         "--format", "json", cwd=own_example.parent), expected=lambda p: p.returncode == 0)
    plan = contract(lambda: cli("plan", "--suite", suite, "--format", "json", cwd=own_example.parent),
                    expected=lambda p: p.returncode == 0)
    assert len(json.loads(plan.stdout)["runs"]) == 3
    results = [run_cli(suite, own_example.parent) for _ in range(2)]
    compared = contract(lambda: cli("compare", results[0]["output"], results[1]["output"], "--format", "json",
                                    cwd=own_example.parent), expected=lambda p: p.returncode == 0)
    assert json.loads(compared.stdout)["scope"] == "full"


def run_cli(suite, cwd):
    process = contract(lambda: cli("run", "--suite", suite, "--format", "json", cwd=cwd),
                       expected=lambda p: p.returncode == 0)
    result = json.loads(process.stdout)
    assert len(result["runs"]) == 3
    assert all(r["status"] == "completed" and r["quality_passed"] for r in result["runs"])
    assert all(r["agent_id"] == "own-agent" and r["condition"] == "cubie" for r in result["runs"])
    assert {r["benchmark"] for r in result["runs"]} == {"review_agent", "developer_agent"}
    return result


@pytest.mark.parametrize("benchmark", ["review_agent", "developer_agent"])
def test_installed_scenario_templates_are_valid_external_packages(own_example, benchmark):
    destination = own_example.parent / ("new-" + benchmark)
    contract(lambda: cli("init-scenario", "--benchmark", benchmark, destination, "--format", "json", cwd=own_example),
             expected=lambda p: p.returncode == 0)
    contract(lambda: cli("validate", destination, "--check-references", "--format", "json", cwd=own_example),
             expected=lambda p: p.returncode == 0)
