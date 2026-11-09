"""EBT cases for GUTACHTEN.md, section 8, priority 1.4.

Only Mypy's success/diagnostic exit codes (0/1) may yield diagnostics.
Unexpected exits must propagate as tool errors, even with empty or parseable
output. These desired contracts deliberately have no xfail markers.
"""

import re
import subprocess
import sys

import pytest

from qb_cubie import EBT, AstLinter, LinterDiagnostic, MyPy, WorldState

SOURCE = "answer: int = 42"
DIAGNOSTIC = '<string>:1:7: error: Incompatible types in assignment [assignment]\n'


@pytest.fixture
def simulated_process(monkeypatch):
    """Replace only process execution; keep command building and parsing real."""
    calls = []

    def configure(returncode, stdout="", stderr=""):
        def run(cmd, *, text, capture_output):
            assert text is True
            assert capture_output is True
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

        monkeypatch.setattr("qb_cubie.linters.mypy.subprocess.run", run)
        return calls

    return configure


@pytest.mark.parametrize("stderr", ["", "nonfatal notice\n"], ids=["silent", "notice"])
def test_successful_empty_analysis_is_an_empty_diagnostic_list(simulated_process, stderr):
    calls = simulated_process(0, stderr=stderr)
    result = EBT(
        target=AstLinter(MyPy(executable="mypy-test-double")).check,
        pre=WorldState(args=(SOURCE,)),
        post=WorldState(returns=[]),
    ).run()

    assert result.evaluation is True
    assert len(result.traces) == 1
    assert result.traces[0].outcome.returns == []
    assert calls == [[
        "mypy-test-double", "--show-error-codes", "--no-error-summary", "-c", SOURCE,
    ]]


def test_diagnostic_exit_code_preserves_structured_findings(simulated_process):
    simulated_process(1, stdout=DIAGNOSTIC)
    expected = LinterDiagnostic(
        file_path="<string>", linter_name="Mypy", rule_id="assignment",
        line=1, column=7, message="Incompatible types in assignment", severity="error",
    )
    result = EBT(
        target=AstLinter(MyPy(executable="mypy-test-double")).check,
        pre=WorldState(args=(SOURCE,)),
        post=WorldState(returns=[expected]),
    ).run()

    assert result.evaluation is True
    assert result.traces[0].outcome.returns == [expected]


@pytest.mark.parametrize("returncode", [-9, -15, 2, 3, 127],
                         ids=["killed", "terminated", "usage-error", "unexpected", "missing-command"])
@pytest.mark.parametrize("stdout, stderr", [
    ("", ""),
    ("", "fatal tool error\n"),
    ("analysis aborted\n", ""),
    (DIAGNOSTIC, "fatal tool error\n"),
], ids=["silent", "stderr-only", "stdout-only", "partial-diagnostic"])
def test_unexpected_exit_is_a_tool_error_not_an_analysis_result(
    simulated_process, returncode, stdout, stderr,
):
    calls = simulated_process(returncode, stdout, stderr)
    reported = []

    class RecordingReporter:
        def report(self, trace):
            reported.append(trace)

    case = EBT(
        target=AstLinter(MyPy(executable="mypy-test-double")).check,
        pre=WorldState(args=(SOURCE,)),
        post=WorldState(returns=[]),
        reporter=RecordingReporter(),
    )
    with pytest.raises(RuntimeError) as error:
        case.run()

    assert len(calls) == 1
    assert reported == []
    assert case.run_trace is None
    message = str(error.value)
    assert "Mypy" in message
    # A code of 2 must not accidentally match the source literal 42.
    assert re.search(rf"(?<![\w-]){returncode}(?!\w)", message)
    for argument in calls[0]:
        assert argument in message
    for output in (stdout, stderr):
        if output.strip():
            assert output.strip() in message


def test_negative_ebt_expectation_does_not_turn_a_tool_crash_into_success(simulated_process):
    simulated_process(-9)
    with pytest.raises(RuntimeError):
        EBT(
            target=AstLinter(MyPy(executable="mypy-test-double")).check,
            pre=WorldState(args=(SOURCE,)),
            post=WorldState(returns=[]),
            expect=False,
            reporter=None,
        ).run()


@pytest.mark.parametrize("returncode", [0, 2], ids=["success", "silent-failure"])
def test_real_silent_process_exit_is_classified_without_mypy_installation(returncode):
    """Exercise the real subprocess boundary with a local Python stand-in."""
    case = EBT(
        target=AstLinter(MyPy(executable=[
            sys.executable, "-c", f"raise SystemExit({returncode})",
        ])).check,
        pre=WorldState(args=(SOURCE,)),
        post=WorldState(returns=[]),
    )
    if returncode == 0:
        result = case.run()
        assert result.evaluation is True
        assert result.traces[0].outcome.returns == []
    else:
        with pytest.raises(RuntimeError):
            case.run()
