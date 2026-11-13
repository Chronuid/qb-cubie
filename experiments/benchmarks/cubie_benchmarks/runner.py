"""Run the installed deterministic smoke pipeline against archived inputs."""

import shutil
import time
import uuid
from pathlib import Path

from cubie_benchmarks.execution import _inputs
from cubie_benchmarks.execution._episode import execute
from cubie_benchmarks.planning.planner import plan_suite
from cubie_benchmarks.reporting.results import save


def run_suite(path: str | Path) -> dict:
    """Execute a planned suite with the built-in offline fake adapter."""
    path = Path(path).resolve()
    plan = plan_suite(path)
    prepared = _inputs.prepare(path, plan)
    return execute_prepared(plan, prepared)


def execute_prepared(plan, prepared, measurement=None):
    """Execute validated inputs and optionally archive their frozen measurement bundle."""
    root = Path(plan["output"]) / uuid.uuid4().hex
    root.mkdir(parents=True)
    inputs, scenarios = _inputs.archive(prepared, plan, root)
    metadata = _measurement(root, inputs, measurement)
    return save(root, plan, inputs, _observations(root, plan, prepared, scenarios), metadata)


def _observations(root, plan, prepared, scenarios):
    """Observe all planned attempts while retaining exhausted global-limit entries."""
    deadline = time.monotonic() + plan["max_total_wall_time_seconds"]
    return [execute(root, run, scenarios[run["scenario_id"]],
                    _agent(prepared["agents"][run["agent_id"]]), index, deadline)
            for index, run in enumerate(plan["runs"], 1)]


def _measurement(root, inputs, measurement):
    """Keep frozen manifest contents and local adapter sources alongside run evidence."""
    if measurement is None:
        return {}
    source, checksum = measurement
    shutil.copytree(source, root / "measurement")
    inputs["measurement"] = ["measurement/measurement.json"]
    return {"measurement_sha256": checksum}


def _agent(entry):
    """Preserve the original agent working directory after archiving."""
    return {**entry["config"], "_cwd": str(entry.get("cwd", entry["path"].parent))}
