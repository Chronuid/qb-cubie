"""Build deterministic benchmark plans without starting scenario or adapter code."""

from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.planning._planning import agents, expand, limits, sources
from qb_cubie.benchmarks.planning.gates import validate_gates
from qb_cubie.benchmarks.planning.selection import select_scenarios


def plan_suite(path: str | Path) -> dict:
    """Resolve a version-one suite into a detached, JSON-compatible run plan."""
    path = Path(path).resolve()
    suite = v.read_data(path, toml=True)
    _suite(suite)
    scenarios, packages = sources(path.parent, suite.get("sources"))
    chosen = select_scenarios(scenarios, suite.get("select", {}))
    configured_agents = agents(path.parent, suite.get("agents"))
    runs = expand(chosen, configured_agents, suite)
    bounds = limits(suite.get("limits", {}), len(runs), sum(r["budgets"]["wall_time_seconds"] for r in runs))
    return v.snapshot({"schema_version": 1, "name": suite["name"], "profile": suite["profile"],
            "output": str((path.parent / suite["output"]).resolve()), "runs": runs,
            "packages": packages, "seed": suite.get("seed"),
            "gates": validate_gates(suite.get("gates", []), runs), **bounds})


def _suite(suite):
    """Validate suite identity, profile and repetition settings."""
    v.text(suite.get("name"), "name")
    v.text(suite.get("output"), "output")
    v.choice(suite.get("profile"), {"agent-evaluation", "cubie-vs-pytest"}, "profile")
    v.number(suite.get("repetitions"), "repetitions", positive=True, integer=True)
    v.budgets(suite.get("budgets", {}))
    if "seed" in suite:
        v.require(type(suite["seed"]) is int, "seed", "expected an integer")
