"""GUTACHTEN 9.1 / B4: Windows paths and unrecognized error output.

Only process execution is replaced: public MyPy.check, parsing, EBT matching
and reporting remain real. Controlled Windows output also runs on Linux;
these cases do not claim to replace a native Windows acceptance run.
"""

import subprocess

import pytest

from qb_cubie import EBT, LinterDiagnostic, MyPy, WorldState

MESSAGE = "Incompatible types in assignment"


@pytest.fixture
def process_result(monkeypatch):
    def configure(returncode, stdout="", stderr=""):
        calls = []

        def run(cmd, *, text, capture_output):
            assert text is True and capture_output is True
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

        monkeypatch.setattr("qb_cubie.linters.mypy.subprocess.run", run)
        return calls

    return configure


@pytest.mark.parametrize("path", [
    r"C:\work\example.py", "C:/work/example.py", r"D:\work tree\example.py",
    r"\\server\share\example.py", "/work/example.py", "relative/example.py",
], ids=["drive-backslash", "drive-slash", "drive-spaces", "unc", "posix", "relative"])
@pytest.mark.parametrize("column", [None, 7], ids=["line-only", "line-and-column"])
def test_file_diagnostics_keep_paths_locations_and_codes(tmp_path, process_result, path, column):
    source = tmp_path / "example.py"
    source.write_text('answer: int = "wrong"\n', encoding="utf-8")
    location = "12:" if column is None else f"12:{column}:"
    calls = process_result(1, f"{path}:{location} error: {MESSAGE} [assignment]\r\n")
    expected = LinterDiagnostic(
        file_path=path, linter_name="Mypy", rule_id="assignment", line=12,
        column=column or 0, message=MESSAGE, severity="error",
    )
    result = EBT(target=MyPy(executable="mypy-test-double").check,
                 pre=WorldState(args=(source,)), post=WorldState(returns=[expected])).run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == [expected]
    assert calls == [["mypy-test-double", "--show-error-codes", "--no-error-summary", str(source)]]


@pytest.mark.parametrize("stdout, stderr", [
    ("", ""), ("", "type analysis failed"),
    ("unrecognized diagnostic format\n", ""),
    ("Found 1 error in 1 file\n", ""),
    ("example.py:1: note: analysis stopped\n", ""),
], ids=["silent", "stderr-only", "unknown-format", "summary-only", "note-only"])
def test_error_exit_without_an_error_diagnostic_cannot_be_a_clean_gate(process_result, stdout, stderr):
    calls = process_result(1, stdout, stderr)
    reports = []

    class Reporter:
        def report(self, trace):
            reports.append(trace)

    case = EBT(target=MyPy(executable="mypy-test-double").check,
               pre=WorldState(args=("answer: int = 42",)),
               post=WorldState(returns=[]), reporter=Reporter())
    with pytest.raises(RuntimeError):
        case.run()
    assert len(calls) == 1
    assert reports == []
    assert case.run_trace is None


def test_mixed_posix_and_windows_diagnostics_are_not_partially_discarded(process_result):
    paths = ["/work/first.py", r"C:\work\second.py"]
    process_result(1, "".join(f"{path}:1: error: {MESSAGE} [assignment]\n" for path in paths))
    case = EBT(target=MyPy(executable="mypy-test-double").check,
               pre=WorldState(args=("answer: int = 42",)),
               post=WorldState(returns=[]), reporter=None)
    result = case.run()
    assert result.evaluation is False
    assert [item.file_path for item in result.traces[0].outcome.returns] == paths


def test_successful_empty_analysis_remains_a_clean_gate(process_result):
    process_result(0)
    result = EBT(target=MyPy(executable="mypy-test-double").check,
                 pre=WorldState(args=("answer: int = 42",)),
                 post=WorldState(returns=[])).run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == []


@pytest.mark.parametrize("returncode", [0, 1])
@pytest.mark.parametrize("known", [False, True], ids=["only-unknown", "partially-recognized"])
def test_unrecognized_output_is_never_silently_discarded(process_result, returncode, known):
    output = "new or broken diagnostic format\n"
    if known:
        output += f"example.py:1: error: {MESSAGE} [assignment]\n"
    process_result(returncode, output)
    case = EBT(target=MyPy(executable="mypy-test-double").check,
               pre=WorldState(args=("answer: int = 42",)),
               post=WorldState(returns=[]), reporter=None)
    with pytest.raises(RuntimeError, match="Mypy.*Unrecognized analysis output") as error:
        case.run()
    assert output in str(error.value)
    assert case.run_trace is None
