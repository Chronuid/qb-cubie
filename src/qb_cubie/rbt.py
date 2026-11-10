import tkinter as tk
from typing import Any, Optional

from .protocols import Reporter, ReviewData, Reviewer
from .reporter import PytestReporter

_DEFAULT_REPORTER = PytestReporter()


# ========== REVIEW-BASED-TESTING ======================================================================================


class RBT:
    """Orchestrates the review-based test process."""

    def __init__(
        self,
        check: str,
        target: Optional[Any] = None,
        reviewer: Optional[Reviewer] = None,
        tags: Optional[list[str]] = None,
        reporter: Reporter[ReviewData] | None = _DEFAULT_REPORTER,
    ):
        self.check = check
        self.target = target
        self.reviewer = reviewer if reviewer is not None else HeadlessReviewer()
        self.reporter = reporter
        self.tags = tags or []
        self._target_string: Optional[str] = None
        self._result: Optional[ReviewData] = None

    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(self) -> None:
        """Executes the test pipeline."""
        __tracebackhide__ = True
        self._arrange()
        self._review()
        self._report()

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _arrange(self) -> None:
        """Prepares the input data for the auditor."""
        self._target_string = self._evaluate(self.target)

    def _review(self) -> None:
        """Delegates the check to the injected instance."""
        self._result = self.reviewer.review(target=self._target_string, check=self.check)

    def _report(self) -> None:
        """Delegates the review result to the reporter, if present."""
        __tracebackhide__ = True
        if self._result is None:
            raise RuntimeError("RBT Pipeline Error: The review phase yielded no result.")
        if self.reporter is not None:
            self.reporter.report(self._result)

    # ----- Utilities --------------------------------------------------------------------------------------------------

    @staticmethod
    def _evaluate(obj: Any) -> Optional[str]:
        """Converts the passed target object into a string."""
        if obj is None or isinstance(obj, str):
            return obj
        return getattr(obj, "__name__", str(obj))


# ========== HUMAN-IN-THE-LOOP =========================================================================================


class HeadlessReviewer:
    """Reviews through the terminal or returns a predefined boolean decision."""

    # Pass ``answer=True`` or ``answer=False`` for unattended runs. With no answer,
    # each review asks for y/n and an optional report. Interactive pytest runs need
    # stdin capture disabled (``pytest -s``). Input errors propagate to the caller.

    def __init__(self, answer: bool | None = None) -> None:
        self.answer = answer

    def review(self, target: str | None, check: str) -> ReviewData:
        """Return a fresh result from a configured answer or terminal input."""
        if self.answer is not None:
            return ReviewData(passed=self.answer)
        if target is not None:
            print(f"Target: {target}")
        print(f"Check: {check}")
        decision = self._decision()
        text = input("Report (optional, Enter to skip): ").strip()
        return ReviewData(passed=decision, report={"text": text} if text else {})

    @staticmethod
    def _decision() -> bool:
        while True:
            decision = input("Pass? [y/n]: ").strip().lower()
            if decision in ("y", "n"):
                return decision == "y"
            print("Please enter y or n.")


class HumanReviewer:
    """Provides the interactive Tkinter-based test."""

    def __init__(self) -> None:
        self._target: Optional[str] = None
        self._check: str = ""
        self._passed: bool = False
        self._report_text: str = ""
        self._root: Optional[tk.Tk] = None
        self._text_widget: Optional[tk.Text] = None

    # ----- Services ---------------------------------------------------------------------------------------------------

    def review(self, target: Optional[str], check: str) -> ReviewData:
        """Carries out the manual review process."""
        self._target = target
        self._check = check
        self._passed = False
        self._report_text = ""
        self._root = None
        self._text_widget = None
        self._run_gui()
        report_payload = {"text": self._report_text} if self._report_text else {}
        return ReviewData(passed=self._passed, report=report_payload)

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _run_gui(self) -> None:
        """Initializes and starts the blocking GUI window."""
        self._root = tk.Tk()
        self._root.title("RBT - Manual Check")
        self._root.attributes("-topmost", True)
        self._build_widgets()
        self._root.wait_window()

    def _build_widgets(self) -> None:
        """Constructs the visual UI elements for the window."""
        if self._root is None:
            raise RuntimeError("GUI Error: Root window is not initialized.")
        if self._target:
            tk.Label(self._root, text=f"Target: {self._target}", font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(self._root, text=f"Check: {self._check}", font=("Arial", 12)).pack(pady=5)
        self._text_widget = tk.Text(self._root, height=8, width=60)
        if self._text_widget:
            self._text_widget.pack(pady=10, padx=20)
        self._build_buttons()

    def _build_buttons(self) -> None:
        """Creates the confirmation buttons for the binary decision."""
        frame = tk.Frame(self._root)
        frame.pack(pady=10)
        tk.Button(frame, text="Pass", bg="green", fg="white", command=self._on_pass).pack(side=tk.LEFT, padx=20)
        tk.Button(frame, text="Fail", bg="red", fg="white", command=self._on_fail).pack(side=tk.RIGHT, padx=20)

    # ----- Utilities --------------------------------------------------------------------------------------------------

    def _on_pass(self) -> None:
        """Saves the positive result and closes the window."""
        self._passed = True
        self._finalize()

    def _on_fail(self) -> None:
        """Saves the negative result and closes the window."""
        self._passed = False
        self._finalize()

    def _finalize(self) -> None:
        """Reads the optional report and terminates the UI loop."""
        if self._root is None or self._text_widget is None:
            raise RuntimeError("GUI Error: UI components missing during finalization.")
        self._report_text = self._text_widget.get("1.0", "end-1c").strip()
        self._root.destroy()
