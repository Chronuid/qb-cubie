"""GUTACHTEN 9.1 / B3: an incomplete analysis is never a clean EBT gate.

Controlled CompletedProcess results cover status/output combinations, while a
real child verifies silent exit and signal handling independently of Pylint.
"""

import json
import os
import subprocess
import sys

import pytest

from qb_cubie import EBT, LinterDiagnostic, Pylint, WorldState

SOURCE = "answer = 42"
FINDING = {
    "path": "example.py", "message-id": "E0602", "line": 1, "column": 9,
    "message": "Undefined variable 'missing'", "type": "error", "obj": "",
}


@pytest.fixture
def process_result(monkeypatch):
    def configure(returncode, stdout="", stderr=""):
        calls = []

        def run(cmd, *, input=None, text, capture_output):
            assert text is True and capture_output is True
            assert input == SOURCE
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

        monkeypatch.setattr("qb_cubie.linters.pylint.subprocess.run", run)
        return calls

    return configure


def gate(executable, reporter=None, expect=True):
    return EBT(target=Pylint(executable=executable).check,
               pre=WorldState(args=(SOURCE,)), post=WorldState(returns=[]),
               reporter=reporter, expect=expect)


@pytest.mark.parametrize("returncode", [-9, -15, 32, 64, 127],
                         ids=["killed", "terminated", "usage-error", "unknown-bit", "missing-command"])
@pytest.mark.parametrize("stdout, stderr", [
    ("", ""), ("", "fatal tool error"), ("[]", ""),
    (json.dumps([FINDING]), "partial analysis"),
], ids=["silent", "stderr-only", "empty-json", "partial-findings"])
def test_invalid_process_status_cannot_publish_an_analysis(process_result, returncode, stdout, stderr):
    calls = process_result(returncode, stdout, stderr)
    reports = []

    class Reporter:
        def report(self, trace):
            reports.append(trace)

    case = gate("pylint-test-double", reporter=Reporter())
    with pytest.raises(RuntimeError):
        case.run()
    assert len(calls) == 1
    assert reports == []
    assert case.run_trace is None


def test_valid_empty_json_analysis_can_pass(process_result):
    process_result(0, "[]", "nonfatal notice")
    result = gate("pylint-test-double").run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == []


@pytest.mark.parametrize("returncode, kinds", [
    (1, [("fatal", "F0001")]), (2, [("error", "E0602")]),
    (4, [("warning", "W0611")]), (8, [("refactor", "R0903")]),
    (16, [("convention", "C0114")]),
    (6, [("error", "E0602"), ("warning", "W0611")]),
    (18, [("error", "E0602"), ("convention", "C0114")]),
], ids=["fatal", "error", "warning", "refactor", "convention", "error-warning", "error-convention"])
def test_valid_diagnostic_bitmasks_preserve_findings(process_result, returncode, kinds):
    findings = [{**FINDING, "type": severity, "message-id": code} for severity, code in kinds]
    process_result(returncode, json.dumps(findings))
    expected = [LinterDiagnostic(
        file_path="example.py", linter_name="Pylint", rule_id=code,
        line=1, column=9, message=FINDING["message"], severity=severity, node_name="",
    ) for severity, code in kinds]
    result = EBT(target=Pylint(executable="pylint-test-double").check,
                 pre=WorldState(args=(SOURCE,)), post=WorldState(returns=expected)).run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == expected


@pytest.mark.parametrize("returncode, stdout", [(0, ""), (2, ""), (2, "[]")],
                         ids=["missing-success-payload", "missing-findings", "empty-error-payload"])
def test_missing_analysis_evidence_is_a_tool_error(process_result, returncode, stdout):
    process_result(returncode, stdout)
    case = gate("pylint-test-double")
    with pytest.raises(RuntimeError):
        case.run()
    assert case.run_trace is None


def test_negating_the_contract_cannot_accept_a_tool_crash(process_result):
    process_result(-9)
    with pytest.raises(RuntimeError):
        gate("pylint-test-double", expect=False).run()


@pytest.mark.parametrize("stdout", ["{}", "null", "true", "[{}]", "[1]", "[broken"])
def test_malformed_or_wrongly_shaped_json_is_a_tool_error(process_result, stdout):
    process_result(0, stdout)
    case = gate("pylint-test-double")
    with pytest.raises(RuntimeError, match="Pylint.*Invalid JSON analysis") as error:
        case.run()
    assert stdout in str(error.value)
    assert case.run_trace is None


@pytest.mark.parametrize("action, expected_code", [
    ("raise SystemExit(32)", 32),
    pytest.param("import os, signal; os.kill(os.getpid(), signal.SIGKILL)", -9,
                 marks=pytest.mark.skipif(os.name != "posix", reason="POSIX signal termination")),
], ids=["silent-usage-exit", "sigkill"])
def test_real_child_abort_never_becomes_diagnostic_freedom(action, expected_code):
    command = [sys.executable, "-c", action]
    observed = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    assert observed.returncode == expected_code
    assert observed.stdout == observed.stderr == ""
    case = gate(command)
    with pytest.raises(RuntimeError):
        case.run()
    assert case.run_trace is None
