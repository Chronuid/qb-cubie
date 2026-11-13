"""Exercise pytest opt-in in child processes whose marked test only writes a sentinel."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from ..contracts import accepted

ROOT = Path(__file__).resolve().parents[3]
PROBE = '''from pathlib import Path
import pytest

@pytest.mark.agent_benchmark
@pytest.mark.review_agent
def test_agent_episode():
    Path(__file__).with_name("episode-started").write_text("started", encoding="utf-8")
'''


def run_probe(root, *args, plugin=True):
    probe = root / "test_opt_in_probe.py"
    probe.write_text(PROBE, encoding="utf-8")
    code = ('import sys; sys.path.insert(0, sys.argv.pop(1)); sys.path.insert(0, sys.argv.pop(1)); '
            'import pytest; raise SystemExit(pytest.main(sys.argv[1:]))')
    plugins = ["-p", "cubie_benchmarks.pytest_plugin"] if plugin else []
    return subprocess.run([sys.executable, "-I", "-c", code, str(ROOT / "src"), str(ROOT / "experiments/benchmarks"),
                           *plugins, "-q", "-o", "addopts=", str(probe), *map(str, args)], cwd=root,
                          env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": ""},
                          capture_output=True, text=True, timeout=30, check=False)


def test_sentinel_probe_runs_under_plain_pytest_without_a_model(tmp_path):
    accepted(lambda: run_probe(tmp_path, plugin=False), expected=lambda process: process.returncode == 0)
    assert (tmp_path / "episode-started").read_text(encoding="utf-8") == "started"


@pytest.mark.parametrize("arguments", [(), ("-m", "agent_benchmark")], ids=["standard-run", "marker-only"])
def test_marked_episodes_are_skipped_without_explicit_enablement(tmp_path, arguments):
    process = accepted(lambda: run_probe(tmp_path, *arguments), expected=lambda value: value.returncode == 0)
    assert "1 skipped" in process.stdout and not (tmp_path / "episode-started").exists()


def test_collection_needs_neither_agent_configuration_nor_adapter_start(tmp_path):
    process = accepted(lambda: run_probe(tmp_path, "--collect-only"), expected=lambda value: value.returncode == 0)
    assert "test_agent_episode" in process.stdout and not (tmp_path / "episode-started").exists()


@pytest.mark.parametrize("arguments", [("--run-agent-benchmarks",),
                                       ("--run-agent-benchmarks", "--suite", "missing.toml")],
                         ids=["missing-configuration", "nonexistent-suite"])
def test_explicit_enablement_with_missing_configuration_is_a_usage_error(tmp_path, arguments):
    process = accepted(lambda: run_probe(tmp_path, *arguments), expected=lambda value: value.returncode == 4)
    assert "suite" in (process.stdout + process.stderr).lower()
    assert not (tmp_path / "episode-started").exists()


def test_explicit_enablement_accepts_a_valid_offline_suite(tmp_path, measurement_suite):
    process = accepted(lambda: run_probe(tmp_path, "--run-agent-benchmarks", "--suite", measurement_suite),
                       expected=lambda value: value.returncode == 0)
    assert "1 passed" in process.stdout and (tmp_path / "episode-started").is_file()


def test_enablement_with_unavailable_adapter_fails_before_the_episode_body(tmp_path, process_suite):
    agent = process_suite.parent.parent / "agents/current.toml"
    text = agent.read_text(encoding="utf-8").replace(sys.executable, str(tmp_path / "missing-agent-executable"))
    agent.write_text(text, encoding="utf-8")
    process = accepted(lambda: run_probe(tmp_path, "--run-agent-benchmarks", "--suite", process_suite),
                       expected=lambda value: value.returncode == 4)
    assert "agent" in (process.stdout + process.stderr).lower()
    assert not (tmp_path / "episode-started").exists()


def test_plugin_registers_all_three_public_benchmark_markers(tmp_path):
    process = accepted(lambda: run_probe(tmp_path, "--markers"), expected=lambda value: value.returncode == 0)
    assert all(f"@pytest.mark.{marker}" in process.stdout
               for marker in ("agent_benchmark", "review_agent", "developer_agent"))


def test_shared_result_fixture_cannot_start_an_unmarked_episode_without_enablement(tmp_path, monkeypatch):
    source = PROBE.replace("@pytest.mark.agent_benchmark\n", "").replace("@pytest.mark.review_agent\n", "")
    source = source.replace("def test_agent_episode():", "def test_agent_episode(agent_benchmark_result):")
    monkeypatch.setattr(sys.modules[__name__], "PROBE", source)
    process = accepted(lambda: run_probe(tmp_path), expected=lambda value: value.returncode == 0)
    assert "1 skipped" in process.stdout and not (tmp_path / "episode-started").exists()
