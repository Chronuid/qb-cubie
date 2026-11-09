"""EBT specifications for RBT reporting and reporter injection.

Injected reporters consume the ReviewData returned by the reviewer.
"""

import pytest

from src.qb_cubie.ebt import EBT
from src.qb_cubie.protocols import ReviewData, WorldState
from src.qb_cubie.rbt import RBT


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
