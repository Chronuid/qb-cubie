"""EBT specifications for the terminal-based RBT reviewer.

Contract: ``HeadlessReviewer(answer: bool | None = None)`` implements
``review(target, check) -> ReviewData``. A boolean bypasses all terminal input;
None asks for y/n (case-insensitive, surrounding whitespace ignored), then an
optional report. Invalid decisions are retried. Input errors propagate instead
of silently deciding a review. RBT uses this reviewer by default.

"""

import pytest

from src.qb_cubie import rbt
from src.qb_cubie.ebt import EBT
from src.qb_cubie.protocols import ReviewData, WorldState


@pytest.fixture(autouse=True)
def forbid_gui_and_unexpected_input(monkeypatch):
    """A regression must neither open a window nor wait for real stdin."""
    def unexpected_gui(*args, **kwargs):
        pytest.fail("Headless reviews must not start a Tkinter GUI")

    def unexpected_input(*args, **kwargs):
        pytest.fail("An automated review must not read terminal input")

    monkeypatch.setattr(rbt, "_load_tk", unexpected_gui)
    monkeypatch.setattr(rbt.HumanReviewer, "_run_gui", unexpected_gui)
    monkeypatch.setattr("builtins.input", unexpected_input)


@pytest.fixture
def terminal(monkeypatch):
    """Install finite scripted input; unexpected extra prompts fail immediately."""
    def install(*answers):
        remaining = iter(answers)
        prompts = []

        def read(prompt=""):
            prompts.append(prompt)
            print(prompt, end="")
            try:
                return next(remaining)
            except StopIteration:
                pytest.fail("HeadlessReviewer requested more input than specified")

        monkeypatch.setattr("builtins.input", read)
        return prompts

    return install


@pytest.mark.parametrize("answer", [True, False], ids=["pass", "fail"])
@pytest.mark.parametrize("target", ["Example target", None], ids=["target", "no-target"])
def test_predefined_answer_returns_review_data_without_input(answer, target):
    def review():
        reviewer = rbt.HeadlessReviewer(answer=answer)
        return reviewer.review(target=target, check="Check the result")

    EBT(target=review, post=WorldState(returns=ReviewData(passed=answer))).run()


@pytest.mark.parametrize(
    "decision, passed",
    [("y", True), ("n", False), ("Y", True), ("N", False),
     ("  y\t", True), ("\tn  ", False)],
    ids=["yes", "no", "uppercase-yes", "uppercase-no", "padded-yes", "padded-no"],
)
def test_terminal_decision_is_normalized(decision, passed, terminal):
    prompts = terminal(decision, "")

    def review():
        result = rbt.HeadlessReviewer().review(target="Example", check="Check")
        return result, len(prompts)

    EBT(
        target=review,
        post=WorldState(returns=(ReviewData(passed=passed), 2)),
    ).run()


@pytest.mark.parametrize("passed, decision", [(True, "y"), (False, "n")])
@pytest.mark.parametrize(
    "text, report",
    [("  Prüfung abgeschlossen ✓  ", {"text": "Prüfung abgeschlossen ✓"}),
     (" \t ", {})],
    ids=["trimmed-report", "blank-report"],
)
def test_optional_report_is_normalized(passed, decision, text, report, terminal):
    terminal(decision, text)

    def review():
        return rbt.HeadlessReviewer().review(target="Example", check="Check")

    EBT(
        target=review,
        post=WorldState(returns=ReviewData(passed=passed, report=report)),
    ).run()


@pytest.mark.parametrize("decision, passed", [("y", True), ("n", False)])
def test_invalid_decisions_are_retried(decision, passed, terminal):
    prompts = terminal("", "maybe", "1", decision, "Final report")

    def review():
        result = rbt.HeadlessReviewer().review(target=None, check="Check")
        return result, len(prompts)

    EBT(
        target=review,
        post=WorldState(returns=(
            ReviewData(passed=passed, report={"text": "Final report"}), 5,
        )),
    ).run()


@pytest.mark.parametrize("target", ["Unique review target", None])
def test_terminal_displays_check_and_available_target(target, terminal, capsys):
    terminal("y", "")

    def review():
        rbt.HeadlessReviewer().review(target=target, check="Unique review instruction")
        output = capsys.readouterr().out
        return "Unique review instruction" in output, target is None or target in output

    EBT(target=review, post=WorldState(returns=(True, True))).run()


def test_explicit_none_answer_enables_terminal_mode(terminal):
    terminal("n", "Needs correction")

    def review():
        return rbt.HeadlessReviewer(answer=None).review(target=None, check="Check")

    EBT(
        target=review,
        post=WorldState(returns=ReviewData(False, {"text": "Needs correction"})),
    ).run()


@pytest.mark.parametrize("answer", [True, False], ids=["pass", "fail"])
def test_predefined_answer_is_reusable_with_independent_results(answer):
    def review_twice():
        reviewer = rbt.HeadlessReviewer(answer=answer)
        first = reviewer.review(target="First", check="First check")
        first.report["text"] = "Caller mutation"
        second = reviewer.review(target=None, check="Second check")
        return first is not second, second

    EBT(
        target=review_twice,
        post=WorldState(returns=(True, ReviewData(passed=answer))),
    ).run()


def test_terminal_reviews_do_not_reuse_previous_decision_or_report(terminal):
    prompts = terminal("y", "First report", "n", "")

    def review_twice():
        reviewer = rbt.HeadlessReviewer()
        first = reviewer.review(target="First", check="First check")
        second = reviewer.review(target=None, check="Second check")
        return first, second, len(prompts)

    EBT(
        target=review_twice,
        post=WorldState(returns=(
            ReviewData(True, {"text": "First report"}), ReviewData(False), 4,
        )),
    ).run()


@pytest.mark.parametrize("error_type", [EOFError, OSError, KeyboardInterrupt])
@pytest.mark.parametrize("phase", ["decision", "report"])
def test_input_errors_propagate_without_a_review(error_type, phase, monkeypatch):
    error = error_type("Terminal input unavailable")
    calls = []

    def read(prompt=""):
        calls.append(prompt)
        if phase == "report" and len(calls) == 1:
            return "y"
        raise error

    monkeypatch.setattr("builtins.input", read)

    def review():
        reviewer = rbt.HeadlessReviewer()
        with pytest.raises(error_type) as caught:
            reviewer.review(target=None, check="Check")
        return caught.value is error, len(calls)

    EBT(
        target=review,
        post=WorldState(returns=(True, 1 if phase == "decision" else 2)),
    ).run()


def test_rbt_uses_headless_reviewer_by_default(terminal):
    terminal("y", "")

    def run():
        test = rbt.RBT(check="Default reviewer check", target="Example", reporter=None)
        is_headless = isinstance(test.reviewer, rbt.HeadlessReviewer)
        test.run()
        return is_headless, test._result

    EBT(target=run, post=WorldState(returns=(True, ReviewData(True)))).run()


@pytest.mark.parametrize("answer", [True, False], ids=["pass", "fail"])
def test_injected_headless_reviewer_forwards_result_to_reporter(answer):
    def run():
        results = []

        class RecordingReporter:
            def report(self, result):
                results.append(result)

        reviewer = rbt.HeadlessReviewer(answer=answer)
        test = rbt.RBT(check="Check", reviewer=reviewer, reporter=RecordingReporter())
        test.run()
        return test.reviewer is reviewer, results, results[0] is test._result

    EBT(
        target=run,
        post=WorldState(returns=(True, [ReviewData(passed=answer)], True)),
    ).run()
