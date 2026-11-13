"""Establish actual repeat counts, condition pairing and error observations."""

from collections import defaultdict

import pytest

from cubie_benchmarks import plan_suite, summarize_pilot

from ...benchmarks.contracts import accepted
from .support import calibrate, read_json, suite_at


@pytest.mark.parametrize("repetitions", [2, 5], ids=["calibration", "pilot"])
@pytest.mark.parametrize("profile,conditions", [
    ("agent-evaluation", {"cubie"}), ("cubie-vs-pytest", {"cubie", "pytest"}),
])
@pytest.mark.parametrize("benchmark,scenarios", [("review_agent", 2), ("developer_agent", 1)])
def test_each_selected_task_and_condition_has_exactly_the_required_repeats(
        tmp_path, repetitions, profile, conditions, benchmark, scenarios):
    suite = suite_at(tmp_path / "inputs", repetitions=repetitions, profile=profile, benchmark=benchmark)
    plan = accepted(plan_suite, suite, expected=lambda value: len(value["runs"]) == (
        scenarios * repetitions * len(conditions)))
    cells = defaultdict(list)
    for run in plan["runs"]:
        cells[run["scenario_id"], run["agent_id"], run["condition"]].append(run["repetition"])
    assert {key[2] for key in cells} == conditions
    assert all(sorted(values) == list(range(1, repetitions + 1)) for values in cells.values())
    assert not (suite.parent.parent / "results").exists()


@pytest.mark.parametrize("behavior,status", [("timeout", "agent_timeout"), ("crash", "infrastructure_error"),
                                           ("tampered_artifact", "invalid_output")])
def test_actual_interrupted_calibration_keeps_every_started_trial(tmp_path, behavior, status):
    suite = suite_at(tmp_path / "inputs", behavior=behavior)
    archive = calibrate(suite)
    runs = read_json(archive / "results.json")["runs"]
    assert len(runs) == 4 and {run["status"] for run in runs} == {status}
    group, = accepted(summarize_pilot, [archive], expected=lambda value: (
        value["measurement_kind"] == "infrastructure_only"))["groups"]
    assert group["counts"]["started"] == 4 and group["counts"]["quality_passed"] == 0
    assert group["quality_pass_rate"] == 0.0 and group["statuses"] == {status: 4}
