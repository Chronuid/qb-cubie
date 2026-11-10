"""Run fake review requests through RBT with an explicit recording reporter."""

import json

from qb_cubie.benchmarks.adapters import fake
from qb_cubie.benchmarks.reporting._files import write_json
from qb_cubie.protocols import ReviewData
from qb_cubie.rbt import RBT


def submit(context):
    """Submit a fake review through the selected RBT or direct integration."""
    if context["run"]["condition"] == "pytest":
        return fake.review(context)
    recorder = _Recorder()
    RBT(target=str(context["workspace"]), check=json.dumps(context["scenario"]["criteria"]),
        reviewer=_Reviewer(context), reporter=recorder).run()
    if recorder.result is None:
        raise RuntimeError("RBT reporter received no result")
    write_json(context["directory"] / "rbt.json", {"passed": recorder.result.passed, "report": recorder.result.report})
    return recorder.result.report


class _Reviewer:
    def __init__(self, context):
        """Bind the fake reviewer to its episode context."""
        self._context = context

    def review(self, target, check):
        """Return the source-bound fake review decision for RBT."""
        if target != str(self._context["workspace"]) or json.loads(check) != self._context["scenario"]["criteria"]:
            raise ValueError("RBT target/check does not match the current context")
        submission = fake.review(self._context)
        return ReviewData(passed=all(value == "pass" for value in submission["criterion_results"].values()),
                          report=submission)


class _Recorder:
    def __init__(self):
        """Initialize an empty RBT result recorder."""
        self.result: ReviewData | None = None

    def report(self, trace):
        """Record the review result supplied by RBT."""
        self.result = trace
