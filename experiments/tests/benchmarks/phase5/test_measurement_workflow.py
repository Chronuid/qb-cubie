"""Check the reviewable CI entry point without starting GitHub jobs or model calls."""

import os
import re
import subprocess
import sys
import tarfile
import textwrap
from pathlib import Path

from ..contracts import accepted

WORKFLOW = Path(__file__).resolve().parents[4] / ".github/workflows/benchmarks.yml"


def workflow_text():
    return WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.is_file() else ""


def test_measurement_workflow_is_explicit_and_separate_from_pull_requests():
    text = accepted(workflow_text, expected=lambda value: bool(value.strip()))
    assert "workflow_dispatch:" in text
    assert not re.search(r"(?m)^\s*(pull_request(?:_target)?|push):", text)
    assert "run-frozen" in text and "--output" in text


def test_measurement_job_is_bounded_and_uses_locked_dependencies():
    text = accepted(workflow_text, expected=lambda value: bool(value.strip()))
    assert re.search(r"timeout-minutes:\s*[1-9][0-9]*", text)
    assert "--locked" in text or "--require-hashes" in text
    assert "contents: read" in text


def test_measurement_job_keeps_reports_even_when_execution_or_gates_fail():
    text = accepted(workflow_text, expected=lambda value: bool(value.strip()))
    assert "actions/upload-artifact@" in text and "always()" in text
    assert "continue-on-error: true" not in text


def test_workflow_python_steps_restore_a_real_bundle_and_check_its_identity(measurement_suite, tmp_path, public_api):
    bundle = tmp_path / "bundle"
    frozen = accepted(public_api("freeze_suite"), measurement_suite, bundle, expected=lambda value: value["measurement_sha256"])
    provisioned = tmp_path / "provisioned"
    provisioned.mkdir()
    with tarfile.open(provisioned / "measurement.tar", "w") as archive:
        archive.add(bundle, arcname=".")
    snippets = re.findall(r"(?m)^\s*python - <<'PY'\n(.*?)^\s*PY\s*$", workflow_text(), re.DOTALL)
    assert len(snippets) == 3
    environment = {**os.environ, "MEASUREMENT_SHA256": frozen["measurement_sha256"], "GITHUB_OUTPUT": str(tmp_path / "outputs")}
    for source in snippets:
        accepted(lambda source=source: subprocess.run([sys.executable, "-I", "-c", textwrap.dedent(source)],
            cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=30, check=False),
            expected=lambda process: process.returncode == 0)
    assert "python_version=" in (tmp_path / "outputs").read_text(encoding="utf-8")
    accepted(public_api("run_frozen_suite"), tmp_path / "frozen", tmp_path / "results", expected=lambda value: (
        value["gate_evaluation"]["execution_complete"] is True and len(value["runs"]) == 2))

