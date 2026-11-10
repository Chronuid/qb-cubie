"""Run a public-API scenario in a fresh interpreter with Tk deliberately absent."""

import importlib.abc
import re
import sys


class MissingTk(importlib.abc.MetaPathFinder):
    def __init__(self, missing):
        self.missing = missing
        self.attempts = []

    def find_spec(self, fullname, path=None, target=None):
        if fullname == self.missing or fullname.startswith(self.missing + "."):
            self.attempts.append(fullname)
            raise ModuleNotFoundError(f"No module named '{fullname}'", name=fullname)
        return None


def exercise(feature, missing):
    guard = MissingTk(missing)
    sys.meta_path.insert(0, guard)
    assert not any(name in sys.modules for name in ("tkinter", "_tkinter"))
    if feature == "guard":
        try:
            __import__(missing)
        except ModuleNotFoundError as error:
            assert error.name == missing
        else:
            raise AssertionError("The missing-Tk guard did not block the import")
        assert guard.attempts
        return

    from qb_cubie import EBT, TempFS, WorldState
    from qb_cubie.protocols import ReviewData
    from qb_cubie.rbt import HeadlessReviewer, HumanReviewer, RBT

    if feature == "imports":
        assert callable(EBT) and callable(HumanReviewer)
    elif feature == "ebt":
        result = EBT(target=sum, pre=WorldState(args=([1, 2],)),
                     post=WorldState(returns=3)).run()
        assert result.evaluation is True
    elif feature == "tempfs":
        arena = TempFS()
        result = EBT(target=sum, arena=arena, pre=WorldState(args=([1, 2],)),
                     post=WorldState(returns=3)).run()
        assert result.evaluation is True and arena.workspace_path is None
    elif feature == "headless":
        for decision in (True, False):
            review = RBT("Check", "Target", HeadlessReviewer(answer=decision), reporter=None)
            review.run()
            assert review._result == ReviewData(decision)
    elif feature == "gui-unavailable":
        reviewer = HumanReviewer()
        try:
            reviewer.review("Target", "Check")
        except RuntimeError as error:
            message = str(error)
            assert re.search(r"tkinter|\bTk\b", message, re.IGNORECASE), message
            assert re.search(r"install|python3?-tk|verfügbar", message, re.IGNORECASE), message
            assert guard.attempts, "Only actual Tk dependency failures belong to this contract"
        else:
            raise AssertionError("A GUI review without Tk must report its missing dependency")
        return
    else:
        raise AssertionError(f"Unknown Tk scenario: {feature}")
    assert not guard.attempts, "Core functionality attempted to load Tk"
    assert "tkinter" not in sys.modules and "_tkinter" not in sys.modules


if __name__ == "__main__":
    # Repository tests explicitly select src; wheel tests supply no source path.
    if len(sys.argv) == 4:
        sys.path.insert(0, sys.argv[3])
    exercise(sys.argv[1], sys.argv[2])
