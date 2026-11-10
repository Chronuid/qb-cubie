"""Create a relocatable offline benchmark suite from installed resources."""

from importlib.resources import as_file, files
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.reporting._files import copy_tree

SUITE = '''schema_version = 1
name = "smoke"
profile = "agent-evaluation"
repetitions = 1
agents = ["../agents/fake.toml"]
output = "../results"

[[sources]]
path = "../scenarios/smoke"

[budgets]
wall_time_seconds = 20
tool_calls = 10

[limits]
max_runs = 3
max_total_wall_time_seconds = 60
'''
AGENT = '''schema_version = 1
id = "fake"
command = ["builtin:fake"]
capabilities = ["review_output", "workspace_changes", "phased_submission", "cancel", "wall_time", "tool_calls"]

[fake]
behavior = "reference"
'''


def init_smoke_suite(path: str | Path) -> dict:
    """Create a standalone smoke suite with a deterministic fake agent."""
    suite = Path(path).resolve()
    agent = suite.parent.parent / "agents" / "fake.toml"
    package = suite.parent.parent / "scenarios" / "smoke"
    for destination in (suite, agent, package):
        v.require(not destination.exists(), "destination", f"already exists; refusing overwrite: {destination}")
    with as_file(files("qb_cubie.benchmarks").joinpath("data/smoke")) as source:
        copy_tree(source, package)
    _review_sources(package)
    _write(agent, AGENT)
    _write(suite, SUITE)
    return {"suite": str(suite), "agent": str(agent), "package": str(package)}


def _write(path, text):
    """Create a template file without overwriting existing content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def _review_sources(package):
    """Restore executable filenames in exported review templates."""
    for path in package.glob("scenarios/review-*/visible/*.py.txt"):
        path.rename(path.with_suffix(""))
