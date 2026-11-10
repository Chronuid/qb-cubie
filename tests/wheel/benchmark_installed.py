"""Phase 10.2: run ONLY in the wheel test venv, outside the Cubie checkout.

scripts/check_wheel.py explicitly invokes this file with the benchmarks extra.
No repository conftest, source path, model or network is needed by these cases.
"""

import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from qb_cubie import EBT, WorldState


def contract(target, *args, expected):
    trace = EBT(target=target, pre=WorldState(args=args),
                post=WorldState(returns=expected), reporter=None).run()
    assert trace.evaluation is True
    assert trace.traces[0].evaluation is True
    return trace.traces[0].outcome.returns


def cli(*args, cwd):
    command = Path(sys.executable).parent / ("cubie-bench.exe" if os.name == "nt" else "cubie-bench")
    assert command.is_file(), "Phase 10.2: installed cubie-bench entry point is missing"
    return subprocess.run([str(command), *map(str, args)], cwd=cwd, capture_output=True,
                          text=True, timeout=30, check=False)


@pytest.fixture
def installed_suite(tmp_path):
    work = tmp_path / "own project with spaces"
    work.mkdir()
    return work / "sets" / "smoke.toml"


def initialize_cli(suite):
    contract(lambda: cli("init-suite", suite, "--preset", "smoke", "--fake", cwd=suite.parent.parent),
             expected=lambda p: p.returncode == 0)
    assert suite.is_file()


def test_distribution_exposes_benchmark_extra_and_cli():
    distribution = importlib.metadata.distribution("qb-cubie")
    assert "benchmarks" in distribution.metadata.get_all("Provides-Extra", [])
    entries = [ep for ep in distribution.entry_points if ep.group == "console_scripts"
               and ep.name == "cubie-bench"]
    assert len(entries) == 1 and callable(entries[0].load())
    module = __import__("qb_cubie.benchmarks", fromlist=["benchmarks"])
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    assert sys.prefix != sys.base_prefix


def test_help_gives_offline_smoke_commands(tmp_path):
    contract(lambda: cli("--help", cwd=tmp_path), expected=lambda p: (
        p.returncode == 0 and all(word in p.stdout for word in ["init-suite", "plan", "run"])))


def test_installed_cli_and_python_api_produce_identical_plan(installed_suite, tmp_path):
    initialize_cli(installed_suite)
    from qb_cubie.benchmarks import plan_suite

    result = contract(lambda: cli("plan", "--suite", installed_suite, "--format", "json", cwd=tmp_path),
                      expected=lambda p: p.returncode == 0)
    assert json.loads(result.stdout) == plan_suite(installed_suite)


def test_packaged_templates_are_relocatable(installed_suite, tmp_path):
    initialize_cli(installed_suite)
    from qb_cubie.benchmarks import plan_suite

    destination = tmp_path / "relocated"
    shutil.copytree(installed_suite.parent.parent, destination)
    shutil.rmtree(installed_suite.parent.parent)
    suite = destination / "sets" / "smoke.toml"
    contract(plan_suite, suite, expected=lambda plan: (
        bool(plan["runs"]) and Path(plan["output"]).is_relative_to(destination)))


def test_installed_smoke_runs_both_benchmarks_and_persists_evidence(installed_suite, tmp_path):
    initialize_cli(installed_suite)
    from qb_cubie.benchmarks import plan_suite

    plan = plan_suite(installed_suite)
    contract(lambda: cli("run", "--suite", installed_suite, cwd=tmp_path),
             expected=lambda p: p.returncode == 0)
    results = list(Path(plan["output"]).glob("*/results.json"))
    assert len(results) == 1
    root = results[0].parent
    result = json.loads(results[0].read_text(encoding="utf-8"))
    assert {r["benchmark"] for r in result["runs"]} == {"review_agent", "developer_agent"}
    assert all(r["status"] == "completed" and r["quality_passed"] for r in result["runs"])
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["plan"] == plan and (root / "report.md").is_file()
    assert manifest["wheel_sha256"] == os.environ["QB_CUBIE_TEST_WHEEL_SHA256"]
    for name, digest in manifest["artifact_hashes"].items():
        path = (root / name).resolve()
        assert path.is_relative_to(root.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("kind,code", [("configuration", 2), ("quality", 0), ("timeout", 3)])
def test_cli_exitcodes_distinguish_outcomes(installed_suite, tmp_path, kind, code):
    initialize_cli(installed_suite)
    import tomllib

    if kind == "configuration":
        with installed_suite.open("a", encoding="utf-8") as stream:
            stream.write('\n[select]\nids = ["missing/scenario"]\n')
    else:
        suite = tomllib.loads(installed_suite.read_text(encoding="utf-8"))
        agent = installed_suite.parent / suite["agents"][0]
        text = agent.read_text(encoding="utf-8").split("\n[fake]")[0]
        behavior = "wrong_solution" if kind == "quality" else "timeout"
        agent.write_text(text + f'\n[fake]\nbehavior = "{behavior}"\n', encoding="utf-8")
    contract(lambda: cli("run", "--suite", installed_suite, cwd=tmp_path),
             expected=lambda p: p.returncode == code)
    if kind == "quality":
        # Without explicit gates a completed measurement has exit code zero.
        output = installed_suite.parent / suite["output"]
        reports = list(output.glob("*/results.json"))
        assert len(reports) == 1
        runs = json.loads(reports[0].read_text(encoding="utf-8"))["runs"]
        assert any(r["quality_passed"] is False for r in runs)
