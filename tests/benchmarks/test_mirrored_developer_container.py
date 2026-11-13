"""Opt-in real Docker boundary check, using a local Python/pytest base image."""

import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from cubie_benchmarks import compare_runs, init_suite, run_suite
from cubie_benchmarks.measurement._toml import write_toml

BASE = os.environ.get("CUBIE_TEST_BASELINE_IMAGE")
pytestmark = pytest.mark.skipif(not BASE, reason="set CUBIE_TEST_BASELINE_IMAGE to a local Python/pytest image digest")


def test_real_baseline_cannot_read_cubie_or_private_material(tmp_path):
    fixtures = Path(__file__).parent / "fixtures/phase3"
    package = tmp_path / "package"
    shutil.copytree(fixtures, package)
    source = (package / "agents/jsonl_agent.py.txt").read_text()
    peer = package / "agents/jsonl_agent.py"
    peer.write_text(source)
    # The regular agent has its own tests; neither arm reads the private oracle.
    baseline = source[:source.index("TESTS = ")] + 'TESTS = "from shipping import fee\\ndef test_fee():\\n    assert fee(5000) == 0\\n"\n' + source[source.index("SOLUTION = "):]
    start, end = baseline.index("def record(request):"), baseline.index("\n\ndef handshake")
    checkout = Path(__file__).resolve().parents[2]
    baseline = baseline[:start] + (
        "def record(request):\n"
        "    import importlib.util\n"
        "    assert importlib.util.find_spec('qb_cubie') is None\n"
        f"    assert not Path({str(checkout)!r}).exists()\n"
        f"    assert not Path({str(package / 'scenarios/fee-initial/evaluator')!r}).exists()\n"
    ) + baseline[end:]
    build = tmp_path / "image"
    build.mkdir()
    (build / "agent.py").write_text(baseline)
    tag = "cubie-baseline-test-" + uuid.uuid4().hex
    base_id = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", BASE], text=True).strip()
    subprocess.run(["docker", "tag", base_id, tag + "-base"], check=True, capture_output=True)
    (build / "Dockerfile").write_text(f"FROM {tag}-base\nCOPY agent.py /agent.py\n")
    try:
        built = subprocess.run(["docker", "build", "--network", "none", "-q", "-t", tag, str(build)], check=False, capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        digest = subprocess.check_output(["docker", "image", "inspect", "--format", "{{.Id}}", tag], text=True).strip()
        capabilities = ["workspace_changes", "phased_submission", "cancel", "wall_time", "tool_calls"]
        for identifier, command in (("cubie", [sys.executable, "-I", str(peer), "reference", "cubie"]),
                                    ("pytest", ["python", "-I", "/agent.py", "reference", "pytest"])):
            config = {"schema_version": 1, "id": identifier, "transport": "jsonl-v1", "command": command, "capabilities": capabilities}
            if identifier == "pytest":
                config["container_image"] = digest
            write_toml(tmp_path / (identifier + ".toml"), config)
        suite = tmp_path / "suite.toml"
        init_suite(suite, tmp_path / "cubie.toml", package, pytest_agent=tmp_path / "pytest.toml")
        result = run_suite(suite)
        assert len(result["runs"]) == 2
        assert all(run["status"] == "completed" and run["quality_passed"] and run["process_passed"] for run in result["runs"]), result["runs"]
        comparison = compare_runs(result["output"], result["output"], before_condition="cubie", after_condition="pytest")
        assert comparison["scope"] == "full" and len(comparison["pairs"]) == 1
    finally:
        subprocess.run(["docker", "image", "rm", tag, tag + "-base"], check=False, capture_output=True)
