"""Expose CI decisions consistently in JSON, linked reports and command exit codes."""

from pathlib import Path

import pytest

from ..contracts import accepted
from ..phase2.conftest import configure_fake
from ..phase3.conftest import cli
from ..phase4.conftest import read_json
from .conftest import append_gate


@pytest.mark.parametrize("behavior,threshold,exitcode", [
    ("reference", 1.0, 0), ("approve_all", 1.0, 4), ("approve_all", None, 0), ("crash", 1.0, 3),
], ids=["gate-passed", "quality-gate-failed", "reporting-without-gate", "execution-error-precedes-gate"])
def test_cli_distinguishes_execution_errors_from_quality_failures(measurement_suite, behavior, threshold, exitcode):
    configure_fake(measurement_suite, behavior)
    if threshold is not None:
        append_gate(measurement_suite, threshold=threshold)
    process = accepted(lambda: cli("run", "--suite", measurement_suite, "--format", "json", cwd=measurement_suite.parent),
                       expected=lambda value: value.returncode == exitcode)
    assert '"runs"' in process.stdout


def test_invalid_gate_is_a_configuration_error_before_creating_artifacts(measurement_suite):
    append_gate(measurement_suite, metric="typo")
    process = accepted(lambda: cli("run", "--suite", measurement_suite, cwd=measurement_suite.parent),
                       expected=lambda value: value.returncode == 2)
    assert "gate" in process.stderr.lower() or "metric" in process.stderr.lower()
    assert not (measurement_suite.parent.parent / "results").exists()


def test_text_cli_explains_failed_gates_without_requiring_a_json_reader(measurement_suite):
    configure_fake(measurement_suite, "approve_all")
    append_gate(measurement_suite, id="payment-quality")
    process = accepted(lambda: cli("run", "--suite", measurement_suite, cwd=measurement_suite.parent),
                       expected=lambda value: value.returncode == 4)
    assert all(text in process.stdout for text in ("payment-quality", "quality_pass_rate", "0.5", "1.0", "failed"))


def test_saved_json_markdown_and_api_explain_the_same_failed_gate(measurement_suite, public_api):
    configure_fake(measurement_suite, "approve_all")
    append_gate(measurement_suite, id="payment-quality")
    result = accepted(public_api("run_suite"), measurement_suite,
                      expected=lambda value: value.get("gate_evaluation", {}).get("gate_status") == "failed")
    root = Path(result["output"])
    assert read_json(root / "results.json") == result
    evaluation = accepted(public_api("evaluate_gates"), root,
                          expected=lambda value: value == result["gate_evaluation"])
    gate, = evaluation["gates"]
    report = (root / "report.md").read_text(encoding="utf-8")
    assert all(text in report for text in ("payment-quality", "quality_pass_rate", "0.5", "1.0", "failed"))
    assert gate["reason"] and gate["reason"] in report
    assert gate["evidence"] and all(path in report and (root / path).is_file() for path in gate["evidence"])


def test_installed_guide_documents_team_ci_and_product_measurement_boundaries(tmp_path):
    process = accepted(lambda: cli("guide", cwd=tmp_path), expected=lambda value: value.returncode == 0)
    guide = process.stdout.lower()
    assert all(command in guide for command in ("freeze", "run-frozen", "[[gates]]"))
    assert all(text in guide for text in ("held_out", "exitcode", "4", "produkt", "qualit", "pilot"))
