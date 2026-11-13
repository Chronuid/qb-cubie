"""Exercise frozen measurements, gate exit codes and pytest opt-in from an installed wheel."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from qb_cubie import EBT, WorldState
from cubie_benchmarks import (
    evaluate_gates,
    freeze_suite,
    init_example,
    init_smoke_suite,
    run_frozen_suite,
)


def contract(target, *args, expected):
    trace = EBT(target=target, pre=WorldState(args=args), post=WorldState(returns=expected), reporter=None).run()
    assert trace.evaluation is True and trace.traces[0].evaluation is True
    return trace.traces[0].outcome.returns


def suite_at(root, behavior="reference"):
    suite = root / "sets/team.toml"
    init_smoke_suite(suite)
    text = suite.read_text(encoding="utf-8") + '\n[select]\nbenchmarks = ["review_agent"]\n'
    text += '\n[[gates]]\nid = "quality"\nmetric = "quality_pass_rate"\noperator = "gte"\nthreshold = 1.0\n'
    suite.write_text(text, encoding="utf-8")
    agent = root / "agents/fake.toml"
    agent.write_text(agent.read_text(encoding="utf-8").replace('behavior = "reference"', f'behavior = "{behavior}"'), encoding="utf-8")
    return suite


def test_installed_frozen_measurement_survives_relocation_and_archives_original_identity(tmp_path):
    suite = suite_at(tmp_path / "original")
    bundle = tmp_path / "frozen"
    frozen = contract(freeze_suite, suite, bundle, expected=lambda value: value["measurement_sha256"])
    recorded = json.loads((bundle / "measurement.json").read_text(encoding="utf-8"))
    assert recorded["runtime"]["wheel_sha256"] == os.environ["QB_CUBIE_TEST_WHEEL_SHA256"]
    moved = tmp_path / "relocated frozen bundle"
    shutil.move(bundle, moved)
    shutil.rmtree(suite.parent.parent)
    result = contract(run_frozen_suite, moved, tmp_path / "results", expected=lambda value: value["gate_evaluation"]["gate_status"] == "passed")
    root = Path(result["output"])
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    saved, = manifest["inputs"]["measurement"]
    assert hashlib.sha256((root / saved).read_bytes()).hexdigest() == frozen["measurement_sha256"]
    contract(evaluate_gates, root, expected=lambda value: value == result["gate_evaluation"])


def test_installed_cli_returns_a_distinct_quality_failure_exitcode(tmp_path):
    suite = suite_at(tmp_path / "inputs", "approve_all")
    command = Path(sys.executable).parent / ("cubie-bench.exe" if os.name == "nt" else "cubie-bench")
    process = contract(lambda: subprocess.run([str(command), "run", "--suite", str(suite), "--format", "json"],
        cwd=tmp_path, capture_output=True, text=True, timeout=60, check=False), expected=lambda value: value.returncode == 4)
    result = json.loads(process.stdout)
    assert result["gate_evaluation"]["execution_complete"] is True
    assert result["gate_evaluation"]["gate_status"] == "failed"
    assert (Path(result["output"]) / "report.md").is_file()


def test_installed_process_adapter_runs_from_bundled_sources_after_deleting_the_example(tmp_path):
    example = tmp_path / "example"
    initialized = init_example(example)
    suite = Path(initialized["suite"])
    suite.write_text(suite.read_text(encoding="utf-8") + '\n[select]\nbenchmarks = ["review_agent"]\n', encoding="utf-8")
    bundle = tmp_path / "frozen"
    contract(freeze_suite, suite, bundle, expected=lambda value: value["measurement_sha256"])
    shutil.rmtree(example)
    result = contract(run_frozen_suite, bundle, tmp_path / "results", expected=lambda value: len(value["runs"]) == 2)
    assert all(run["status"] == "completed" and run["quality_passed"] for run in result["runs"])
    assert all(run["agent_kind"] == "process" and run["model_id"] is None for run in result["runs"])


def test_installed_pytest_plugin_skips_episodes_without_explicit_enablement(tmp_path):
    probe = tmp_path / "test_episode.py"
    probe.write_text('import pytest\nfrom pathlib import Path\n@pytest.mark.agent_benchmark\n'
                     'def test_episode():\n    Path("must-not-start").touch()\n', encoding="utf-8")
    process = contract(lambda: subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-p",
        "cubie_benchmarks.pytest_plugin", str(probe)], cwd=tmp_path, capture_output=True,
        text=True, timeout=30, check=False), expected=lambda value: value.returncode == 0)
    assert "1 skipped" in process.stdout and not (tmp_path / "must-not-start").exists()
