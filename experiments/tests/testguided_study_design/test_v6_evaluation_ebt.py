# ruff: noqa: F811
"""Preserve the existing independent evaluator contract for incomplete teams.

The team result is a deterministic boundary response. Preparation, freeze,
execution.run, evaluator invocation, result archival and reporting are real.
This does not claim that v6 is wired into execution.run yet.
"""

from pathlib import Path

import pytest
from test_run_management_ebt import managed_study  # noqa: F401
from testguided_study import execution
from testguided_study.artifacts import read
from v6_support import contract


@pytest.mark.parametrize("reason", ["wall_budget", "invalid_output"])
@pytest.mark.parametrize("correct_patch", [False, True], ids=["unsolved", "solved"])
def test_a18_private_evaluation_runs_despite_incomplete_internal_result(managed_study, monkeypatch, reason, correct_patch):
    env = managed_study
    evaluated = []
    original_evaluate = execution.backend.evaluate

    def develop(manager, sandbox, task, row, config, guides, directory, **kwargs):
        patch = task.patch if correct_patch else ""
        (directory / "full.patch").write_text(patch)
        return {"status": "incomplete", "reason": reason, "completion": {"status": "incomplete"}, "patch": patch}

    def evaluate(root, item, config, image, directory, patch, **kwargs):
        if directory.parent.parent.name == "runs":
            evaluated.append(patch)
        return original_evaluate(root, item, config, image, directory, patch, **kwargs)

    monkeypatch.setattr(execution, "develop", develop)
    monkeypatch.setattr(execution.backend, "evaluate", evaluate)

    def observe():
        archive = Path(env.start(mode="smoke")["archive"]) / "frozen"
        rows = read(archive / "schedule.json")
        results = [read(archive / "runs" / row["run_id"] / "result.json") for row in rows]
        return (len(rows), len(evaluated),
                all(result["agent"]["completion"]["status"] == "incomplete" for result in results),
                [result["resolved"] for result in results],
                all((archive / "runs" / row["run_id"] / "full.patch").read_text() == patch
                    for row, patch in zip(rows, evaluated, strict=True)),
                all(manager.cleaned for manager in env.managers))
    contract(observe, (2, 2, True, [correct_patch, correct_patch], True, True))
