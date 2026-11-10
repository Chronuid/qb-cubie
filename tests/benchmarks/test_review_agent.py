"""Run explicitly enabled review episodes from the user's configured benchmark suite."""

import pytest


@pytest.mark.agent_benchmark
@pytest.mark.review_agent
def test_review_agent_episodes(agent_benchmark_result):
    runs = [run for run in agent_benchmark_result["runs"] if run["benchmark"] == "review_agent"]
    if not runs:
        pytest.skip("The selected suite contains no review episodes")
    assert all(run["status"] == "completed" for run in runs)
    assert agent_benchmark_result["gate_evaluation"]["gate_status"] != "failed"
