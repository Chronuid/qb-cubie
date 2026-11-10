"""Run explicitly enabled developer episodes from the user's configured benchmark suite."""

import pytest


@pytest.mark.agent_benchmark
@pytest.mark.developer_agent
def test_developer_agent_episodes(agent_benchmark_result):
    runs = [run for run in agent_benchmark_result["runs"] if run["benchmark"] == "developer_agent"]
    if not runs:
        pytest.skip("The selected suite contains no developer episodes")
    assert all(run["status"] == "completed" for run in runs)
    assert agent_benchmark_result["gate_evaluation"]["gate_status"] != "failed"
