"""Paired tasks retain independent agent configs, isolation and portable identities."""

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from qb_cubie.benchmarks import (
    compare_runs,
    freeze_suite,
    init_smoke_suite,
    init_suite,
    plan_suite,
    run_suite,
)
from qb_cubie.benchmarks.execution._inputs import prepare
from qb_cubie.benchmarks.measurement._bundle import verify
from qb_cubie.benchmarks.swebench.agent import WITHOUT_CUBIE, AgentContainer


@pytest.fixture
def paired(tmp_path):
    initial = init_smoke_suite(tmp_path / "sets/smoke.toml")
    cubie = Path(initial["agent"])
    baseline = cubie.with_name("pytest.toml")
    baseline.write_text(cubie.read_text().replace('id = "fake"', 'id = "pytest-specialist"'))
    suite = tmp_path / "sets/paired.toml"
    init_suite(suite, cubie, initial["package"], pytest_agent=baseline)
    return suite


def test_pair_runs_identical_tasks_with_separate_agents_and_frozen_configs(paired, tmp_path):
    plan = plan_suite(paired)
    assert len(plan["runs"]) == 2
    cubie, baseline = plan["runs"]
    assert (cubie["agent_id"], baseline["agent_id"]) == ("fake", "pytest-specialist")
    assert (cubie["condition"], baseline["condition"]) == ("cubie", "pytest")
    for field in ("scenario_id", "budgets", "package", "evaluator", "agent_pair_id", "repetition"):
        assert cubie[field] == baseline[field]
    bundle = tmp_path / "frozen"
    freeze_suite(paired, bundle)
    moved = tmp_path / "moved"
    shutil.move(bundle, moved)
    assert plan_suite(moved / "inputs/suite.toml")["runs"] == verify(moved)["plan"]["runs"]
    assert len(list((moved / "inputs/agents").glob("*.toml"))) == 2


def test_explicit_condition_comparison_pairs_specialists_without_rerunning(paired, capsys):
    result = run_suite(paired)
    archive = result["output"]
    comparison = compare_runs(archive, archive, before_condition="cubie", after_condition="pytest")
    assert comparison["scope"] == "full" and len(comparison["pairs"]) == 1
    left, right = comparison["pairs"][0]["before"], comparison["pairs"][0]["after"]
    assert left["quality_passed"] and right["quality_passed"]
    assert left["process_passed"] and right["process_passed"]
    assert left["task_sha256"] == right["task_sha256"]
    assert left["source_tree_sha256"] == right["source_tree_sha256"]
    assert left["context_sha256"] == right["context_sha256"]
    assert comparison["pairs"][0]["effort_deltas"]["tool_calls"] == 0
    assert comparison["pairs"][0]["effort_deltas"]["cost"] is None
    ordinary = compare_runs(archive, archive, before_agent="fake", after_agent="pytest-specialist")
    assert ordinary["scope"] == "incompatible"
    with pytest.raises(ValueError, match="condition"):
        compare_runs(archive, archive, before_condition="cubie")
    from qb_cubie.benchmarks.cli import main
    assert main(["compare", archive, archive, "--before-condition", "cubie", "--after-condition", "pytest",
                 "--before-agent", "fake", "--after-agent", "pytest-specialist"]) == 0
    output = capsys.readouterr().out
    assert "cubie → pytest" in output and "effort_deltas" in output and "process_passed=True" in output


def test_cli_creates_mirrored_suite_from_existing_agents(paired):
    from qb_cubie.benchmarks.cli import main
    root = paired.parent.parent
    target = paired.with_name("from-cli.toml")
    assert main(["init-suite", str(target), "--preset", "smoke", "--agent", str(root / "agents/fake.toml"),
                 "--pytest-agent", str(root / "agents/pytest.toml"),
                 "--package", str(root / "scenarios/smoke")]) == 0
    assert len(plan_suite(target)["runs"]) == 2


@pytest.mark.parametrize("mutation,match", [
    ('agents = ["../agents/fake.toml"]\n', "combine"),
    (None, "requires cubie-vs-pytest"),
])
def test_invalid_pair_configuration_fails_before_start(paired, mutation, match):
    text = paired.read_text()
    if mutation is None:
        text = text.replace('profile = "cubie-vs-pytest"', 'profile = "agent-evaluation"')
    else:
        text = mutation + text
    paired.write_text(text)
    with pytest.raises(ValueError, match=match):
        plan_suite(paired)


def test_real_baseline_requires_container_before_any_agent_probe(paired):
    path = paired.parent.parent / "agents/pytest.toml"
    agent = tomllib.loads(path.read_text())
    path.write_text('schema_version = 1\ntransport = "jsonl-v1"\nid = "pytest-specialist"\n'
                    'command = ["must-never-start"]\ncapabilities = ' + json.dumps(agent["capabilities"]) + '\n')
    with pytest.raises(ValueError, match="container_image"):
        prepare(paired, plan_suite(paired))


def test_container_mounts_only_visible_workspace_and_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr("qb_cubie.benchmarks.swebench.agent.docker", lambda *_: "docker")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    agent = {"container_image": "sha256:" + "a" * 64, "command": ["python", "/adapter/process.py"]}
    session = AgentContainer(agent, "baseline", workspace, tmp_path / "evidence", without_cubie=True, network=False)
    command = session.command
    mounts = [command[index + 1] for index, word in enumerate(command) if word == "--mount"]
    assert mounts == [f"type=bind,source={workspace},target={workspace}",
                      f"type=bind,source={tmp_path / 'evidence'},target=/agent-evidence"]
    assert command[command.index("--network") + 1] == "none"
    assert command[command.index("--entrypoint") + 1] == "python"
    assert WITHOUT_CUBIE in command
    assert not {"--privileged", "--pid=host", "--network=host", "-v"} & set(command)


def test_baseline_startup_rejects_an_image_with_cubie():
    completed = subprocess.run([sys.executable, "-I", "-c", WITHOUT_CUBIE, sys.executable, "-c", "print('launched')"],
                               capture_output=True, text=True, check=False)
    assert completed.returncode != 0 and "contains Cubie" in completed.stderr
    assert "launched" not in completed.stdout


def test_example_developer_tools_work_when_every_cubie_import_is_blocked(tmp_path):
    adapter = Path(__file__).resolve().parents[2] / "experiments/ollama-agents"
    workspace = tmp_path / "project"
    (workspace / "tests").mkdir(parents=True)
    (workspace / "tests/test_regular.py").write_text("def test_regular():\n    assert 2 + 2 == 4\n")
    code = '''import importlib.abc, pathlib, sys
class NoCubie(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.startswith('qb_cubie'):
            raise AssertionError('Cubie dependency in baseline adapter')
sys.meta_path.insert(0, NoCubie())
sys.path.insert(0, sys.argv[1])
from ollama_agents.developer.adapter import DeveloperAdapter
from ollama_agents.developer.tools import observe
assert observe(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), 10)['test_outcome'] == 'passed'
'''
    result = subprocess.run([sys.executable, "-I", "-c", code, str(adapter), str(workspace), str(tmp_path)],
                            capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 0, result.stderr
