"""GUTACHTEN 9.1 / B5: each GUI review needs an explicit new decision.

Selected contract: closing without a decision returns ReviewData(False, {}).
Tk windows/widgets are replaced, but review, GUI lifecycle and the pass/fail
callbacks remain real. No display server or manual interaction is required.
"""

from collections import deque
from types import SimpleNamespace

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.protocols import ReviewData
from qb_cubie.rbt import RBT, HumanReviewer


@pytest.fixture
def gui_sessions(monkeypatch):
    def configure(reviewer, *sessions):
        pending = deque(sessions)
        windows = []

        def create_window():
            assert pending, "Unexpected extra review window"
            decision, text = pending.popleft()
            window = SimpleNamespace(
                title=lambda *args: None, attributes=lambda *args: None, destroyed=False,
            )

            def destroy():
                window.destroyed = True

            def wait_window():
                if decision == "pass":
                    reviewer._on_pass()
                elif decision == "fail":
                    reviewer._on_fail()
                else:
                    assert decision == "close"
                    destroy()  # Tk's default window-manager close action.

            window.destroy = destroy
            window.wait_window = wait_window
            window.text = text
            windows.append(window)
            return window

        def build_widgets(self):
            self._text_widget = SimpleNamespace(get=lambda *args: self._root.text)

        monkeypatch.setattr("qb_cubie.rbt.tk.Tk", create_window)
        monkeypatch.setattr(HumanReviewer, "_build_widgets", build_widgets)
        return windows, pending

    return configure


@pytest.mark.parametrize("first_decision, passed", [("pass", True), ("fail", False)])
def test_closing_a_reused_reviewer_discards_previous_decision_and_report(
    gui_sessions, first_decision, passed,
):
    reviewer = HumanReviewer()
    windows, pending = gui_sessions(reviewer, (first_decision, "First report"), ("close", "Unsubmitted"))

    def review_twice():
        return (
            reviewer.review("First target", "First check"),
            reviewer.review("Second target", "Second check"),
        )

    result = EBT(target=review_twice, post=WorldState(returns=(
        ReviewData(passed, {"text": "First report"}), ReviewData(False),
    )), reporter=None).run()
    first, second = result.traces[0].outcome.returns
    assert first == ReviewData(passed, {"text": "First report"})
    assert second.passed is False
    assert second.report == {}
    assert result.evaluation is True
    assert len(windows) == 2 and all(window.destroyed for window in windows)
    assert not pending


@pytest.mark.parametrize("decision, passed", [("pass", True), ("fail", False)])
def test_new_explicit_decision_replaces_previous_review(gui_sessions, decision, passed):
    reviewer = HumanReviewer()
    gui_sessions(reviewer, ("pass", "Old approval"), (decision, ""))

    def review_twice():
        first = reviewer.review("First", "Check first")
        second = reviewer.review("Second", "Check second")
        return first, second, first is not second

    result = EBT(target=review_twice, post=WorldState(returns=(
        ReviewData(True, {"text": "Old approval"}), ReviewData(passed), True,
    ))).run()
    assert result.evaluation is True


def test_first_window_close_is_rejection_and_drops_unsubmitted_report(gui_sessions):
    reviewer = HumanReviewer()
    gui_sessions(reviewer, ("close", "Unsubmitted approval"))
    result = EBT(target=reviewer.review,
                 pre=WorldState(args=("Target", "Check")),
                 post=WorldState(returns=ReviewData(False))).run()
    assert result.traces[0].outcome.returns == ReviewData(False)


def test_explicit_approval_after_close_can_succeed(gui_sessions):
    reviewer = HumanReviewer()
    gui_sessions(reviewer, ("close", ""), ("pass", "New approval"))

    def review_twice():
        return reviewer.review("First", "Check"), reviewer.review("Second", "Check")

    result = EBT(target=review_twice, post=WorldState(returns=(
        ReviewData(False), ReviewData(True, {"text": "New approval"}),
    ))).run()
    assert result.evaluation is True


@pytest.mark.parametrize("reporting", ["pytest", "silent"])
def test_rbt_gate_cannot_inherit_approval_from_an_earlier_window(gui_sessions, reporting):
    reviewer = HumanReviewer()
    gui_sessions(reviewer, ("pass", "Approved version one"), ("close", ""))
    case = RBT(target="Version one", check="Approve", reviewer=reviewer)
    if reporting == "silent":
        case.reporter = None
    case.run()
    first = case._result
    assert first == ReviewData(True, {"text": "Approved version one"})
    case.target = "Version two"
    if reporting == "pytest":
        with pytest.raises(AssertionError):
            case.run()
    else:
        case.run()
    assert case._result == ReviewData(False)
    assert first == ReviewData(True, {"text": "Approved version one"})
