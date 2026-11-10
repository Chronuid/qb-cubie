"""Run the installed deterministic smoke pipeline against archived inputs."""

import time
import uuid
from pathlib import Path

from qb_cubie.benchmarks.execution import _inputs
from qb_cubie.benchmarks.execution._episode import execute
from qb_cubie.benchmarks.planning.planner import plan_suite
from qb_cubie.benchmarks.reporting.results import save


def run_suite(path: str | Path) -> dict:
    """Execute a planned suite with the built-in offline fake adapter."""
    path = Path(path).resolve()
    plan = plan_suite(path)
    prepared = _inputs.prepare(path, plan)
    root = Path(plan["output"]) / uuid.uuid4().hex
    root.mkdir(parents=True)
    inputs, scenarios = _inputs.archive(prepared, plan, root)
    deadline = time.monotonic() + plan["max_total_wall_time_seconds"]
    runs = [execute(root, run, scenarios[run["scenario_id"]],
                    _agent(prepared["agents"][run["agent_id"]]), index, deadline)
            for index, run in enumerate(plan["runs"], 1)]
    return save(root, plan, inputs, runs)


def _agent(entry):
    """Preserve the original agent working directory after archiving."""
    return {**entry["config"], "_cwd": str(entry.get("cwd", entry["path"].parent))}
