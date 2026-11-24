"""EBT specifications for RBT reporting, reporter injection, and python -O resilience.

Injected reporters consume the ReviewData returned by the reviewer.
"""

from pathlib import Path
import subprocess
import sys

import pytest

from qb_cubie.core.ebt import EBT
from qb_cubie.core.protocols import ReviewData, WorldState
from qb_cubie.core.rbt import RBT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = str(PROJECT_ROOT / "src")



class StubReviewer:
    """Returns a fixed review without starting an interactive UI."""

    def __init__(self, result: ReviewData):
        self.result = result
        self.calls = []

    def review(self, target, check) -> ReviewData:
        self.calls.append((target, check))
        return self.result


class RecordingReporter:
    """Records results without asserting on failed reviews."""

    def __init__(self):
        self.results = []

    def report(self, result: ReviewData) -> None:
        self.results.append(result)


def run_with_default_reporter(passed: bool):
    result = ReviewData(passed=passed, report={"text": "Prüfung abgeschlossen"})
    reviewer = StubReviewer(result)
    rbt = RBT(check="Check the target", target="Example", reviewer=reviewer)
    if passed:
        rbt.run()
        reported = True
    else:
        with pytest.raises(AssertionError) as error:
            rbt.run()
        reported = "Prüfung abgeschlossen" in str(error.value)
    return reported, rbt._result is result, reviewer.calls


@pytest.mark.parametrize("passed", [True, False], ids=["pass", "fail"])
def test_default_reporter_preserves_pytest_behavior(passed):
    EBT(
        target=run_with_default_reporter,
        pre=WorldState(args=(passed,)),
        post=WorldState(returns=(True, True, [("Example", "Check the target")])),
    ).run()


def run_with_custom_reporter(passed: bool):
    result = ReviewData(passed=passed, report={"text": "Keep this report", "score": 7})
    reviewer = StubReviewer(result)
    reporter = RecordingReporter()
    rbt = RBT(
        check="Check the target", target="Example", reviewer=reviewer,
        reporter=reporter,
    )
    rbt.run()
    return (
        rbt.reporter is reporter,
        len(reporter.results),
        reporter.results[0] is result,
        reporter.results[0].passed,
        reporter.results[0].report,
        reviewer.calls,
    )


@pytest.mark.parametrize("passed", [True, False], ids=["pass", "fail"])
def test_custom_reporter_receives_original_result_once(passed):
    """A failed review also reaches the reporter without an internal assertion."""
    EBT(
        target=run_with_custom_reporter,
        pre=WorldState(args=(passed,)),
        post=WorldState(returns=(
            True, 1, True, passed, {"text": "Keep this report", "score": 7},
            [("Example", "Check the target")],
        )),
    ).run()


def run_without_reporter(passed: bool):
    result = ReviewData(passed=passed, report={"text": "Silent review"})
    reviewer = StubReviewer(result)
    rbt = RBT(
        check="Check the target", target="Example", reviewer=reviewer,
        reporter=None,
    )
    rbt.run()
    return rbt.reporter is None, rbt._result is result, reviewer.calls


@pytest.mark.parametrize("passed", [True, False], ids=["pass", "fail"])
def test_none_reporter_runs_review_silently(passed, capsys):
    EBT(
        target=run_without_reporter,
        pre=WorldState(args=(passed,)),
        post=WorldState(returns=(True, True, [("Example", "Check the target")])),
    ).run()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def run_with_reporter_error():
    failure = RuntimeError("Reporter failed")
    received = []

    class FailingReporter:
        def report(self, result: ReviewData) -> None:
            received.append(result)
            raise failure

    result = ReviewData(passed=True)
    rbt = RBT(check="Check", reviewer=StubReviewer(result), reporter=FailingReporter())
    with pytest.raises(RuntimeError) as error:
        rbt.run()
    return error.value is failure, len(received), received[0] is result


def test_reporter_exceptions_propagate():
    EBT(
        target=run_with_reporter_error,
        post=WorldState(returns=(True, 1, True)),
    ).run()


def report_without_review():
    rbt = RBT(check="Check", reviewer=StubReviewer(ReviewData(passed=True)))
    with pytest.raises(RuntimeError, match="review phase yielded no result"):
        rbt._report()
    return True


def test_reporting_requires_a_review_result():
    EBT(target=report_without_review, post=WorldState(returns=True)).run()


def run_with_missing_review_result():
    reporter = RecordingReporter()
    rbt = RBT(check="Check", reviewer=StubReviewer(None), reporter=reporter)
    with pytest.raises(RuntimeError, match="review phase yielded no result"):
        rbt.run()
    return len(reporter.results)


def test_missing_review_result_is_not_sent_to_reporter():
    EBT(target=run_with_missing_review_result, post=WorldState(returns=0)).run()


_OPTIMIZED_SNIPPETS: dict[str, tuple[str, str]] = {
    "ebt_fail": (
        "from qb_cubie import EBT, WorldState\n"
        "EBT(target=lambda: 1, post=WorldState(returns=2)).run()\n",
        "EBT-Assert failed",
    ),
    "ebt_negative_fail": (
        "from qb_cubie import EBT, WorldState\n"
        "EBT(target=lambda: 2, post=WorldState(returns=2), expect=False).run()\n",
        "EBT-Negative-Assert failed",
    ),
    "ebt_pass": (
        "from qb_cubie import EBT, WorldState\n"
        "EBT(target=lambda: 2, post=WorldState(returns=2)).run()\n",
        "",
    ),
    "rbt_fail": (
        "from qb_cubie.core.rbt import RBT, HeadlessReviewer\n"
        "RBT(check='Quality check', target='SampleTarget', reviewer=HeadlessReviewer(answer=False)).run()\n",
        "--- Report ---",
    ),
    "rbt_pass": (
        "from qb_cubie.core.rbt import RBT, HeadlessReviewer\n"
        "RBT(check='Quality check', target='SampleTarget', reviewer=HeadlessReviewer(answer=True)).run()\n",
        "",
    ),
    "service_fail": (
        "from dataclasses import dataclass\n"
        "from qb_cubie import PytestReporter\n"
        "from qb_cubie.core.protocols import Diagnostic\n"
        "@dataclass(frozen=True)\n"
        "class _StubServiceReport:\n"
        "    target: str\n"
        "    passed: bool\n"
        "    diagnostics: tuple[Diagnostic, ...]\n"
        "PytestReporter().report(_StubServiceReport(\n"
        "    target='docs/sample.md',\n"
        "    passed=False,\n"
        "    diagnostics=(Diagnostic('docs/sample.md', 'DOC-OUT', 7, 'Mismatch', 'error'),),\n"
        "))\n",
        "[DOC-OUT] docs/sample.md:7: Mismatch",
    ),
    "service_warning_pass": (
        "from dataclasses import dataclass\n"
        "import warnings\n"
        "from qb_cubie import PytestReporter\n"
        "from qb_cubie.core.protocols import Diagnostic\n"
        "@dataclass(frozen=True)\n"
        "class _StubServiceReport:\n"
        "    target: str\n"
        "    passed: bool\n"
        "    diagnostics: tuple[Diagnostic, ...]\n"
        "with warnings.catch_warnings(record=True) as caught:\n"
        "    warnings.simplefilter('always')\n"
        "    PytestReporter().report(_StubServiceReport(\n"
        "        target='docs/sample.md',\n"
        "        passed=True,\n"
        "        diagnostics=(Diagnostic('docs/sample.md', 'DOC-WARN', 3, 'Advisory', 'warning'),),\n"
        "    ))\n"
        "if len(caught) != 1:\n"
        "    raise RuntimeError(f'Expected 1 warning, got {len(caught)}')\n",
        "",
    ),
}


def run_reporter_under_python_optimize(kind: str, opt_flag: str = "-O") -> dict[str, object]:
    """Execute a PytestReporter contract in a child process with python -O or -OO."""
    snippet, marker = _OPTIMIZED_SNIPPETS[kind]
    script = (
        f"import sys\nsys.path.insert(0, {SRC_PATH!r})\n"
        "if __debug__:\n    raise RuntimeError('Optimization mode not active')\n"
        + snippet
    )
    proc = subprocess.run(
        [sys.executable, opt_flag, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    return {
        "failed": proc.returncode != 0,
        "has_assertion_error": "AssertionError" in proc.stderr,
        "has_expected_marker": (marker in proc.stderr) if marker else (proc.returncode == 0),
    }


@pytest.mark.parametrize(
    "kind, opt_flag, expected",
    [
        ("ebt_fail", "-O", {"failed": True, "has_assertion_error": True, "has_expected_marker": True}),
        ("ebt_negative_fail", "-O", {"failed": True, "has_assertion_error": True, "has_expected_marker": True}),
        ("ebt_fail", "-OO", {"failed": True, "has_assertion_error": True, "has_expected_marker": True}),
        ("rbt_fail", "-O", {"failed": True, "has_assertion_error": True, "has_expected_marker": True}),
        ("service_fail", "-O", {"failed": True, "has_assertion_error": True, "has_expected_marker": True}),
        ("ebt_pass", "-O", {"failed": False, "has_assertion_error": False, "has_expected_marker": True}),
        ("rbt_pass", "-O", {"failed": False, "has_assertion_error": False, "has_expected_marker": True}),
        ("service_warning_pass", "-O", {"failed": False, "has_assertion_error": False, "has_expected_marker": True}),
    ],
    ids=[
        "ebt-fail-O",
        "ebt-negative-fail-O",
        "ebt-fail-OO",
        "rbt-fail-O",
        "service-fail-O",
        "ebt-pass-O",
        "rbt-pass-O",
        "service-warning-pass-O",
    ],
)
def test_pytest_reporter_enforces_assertions_under_python_optimize(
    kind: str,
    opt_flag: str,
    expected: dict[str, object],
) -> None:
    """BUG-002: PytestReporter must deterministically raise AssertionError even under python -O/-OO."""
    EBT(
        target=run_reporter_under_python_optimize,
        pre=WorldState(args=(kind, opt_flag)),
        post=WorldState(returns=expected),
    ).run()
