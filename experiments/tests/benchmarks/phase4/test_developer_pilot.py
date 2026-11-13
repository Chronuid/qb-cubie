"""Keep developer quality, observed process, conditions and agents distinguishable."""

from ..contracts import accepted
from .conftest import read_json
from .test_pilot_summary import summarize


def test_developer_fixture_really_observes_both_process_outcomes(developer_recording, public_api):
    # Multi-agent archives require explicit selection even for their self-check.
    accepted(lambda: public_api("compare_runs")(developer_recording, developer_recording,
                                                before_agent="fake", after_agent="fake"),
             expected=lambda value: value["scope"] == "full" and len(value["pairs"]) == 4)
    runs = read_json(developer_recording / "results.json")["runs"]
    assert all(run["quality_passed"] for run in runs)
    assert all(run["process_passed"] is (run["agent_id"] == "candidate") for run in runs)


def test_pilot_groups_keep_agent_and_condition_separate(developer_recording, public_api):
    summary = summarize(public_api, developer_recording)
    assert len(summary["groups"]) == 4
    identities = {(group["agent_id"], group["condition"]) for group in summary["groups"]}
    assert identities == {(agent, condition) for agent in ("fake", "candidate") for condition in ("cubie", "pytest")}
    for group in summary["groups"]:
        assert group["benchmark"] == "developer_agent"
        assert group["counts"]["planned"] == group["counts"]["quality_passed"] == 2
        assert group["counts"]["process_passed"] == (2 if group["agent_id"] == "candidate" else 0)
        assert group["independent_groups"] == 1 and group["scenario_count"] == 1
        assert set(group["episodes"]) == {"initial_development"}
        assert group["episodes"]["initial_development"]["counts"]["planned"] == 2
    assert "overall_score" not in summary


def test_pilot_does_not_turn_completely_unknown_usage_into_free_execution(developer_recording, public_api):
    summary = summarize(public_api, developer_recording)
    assert summary["measurement_kind"] == "infrastructure_only"
    for group in summary["groups"]:
        cost = group["usage"]["cost"]
        assert cost == {"known_count": 0, "unknown_count": 2, "known_total": 0,
                        "total": None, "mean": None, "stddev": None}
