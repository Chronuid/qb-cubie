"""Build deterministic benchmark plans without starting scenario or adapter code."""

from pathlib import Path

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.planning._planning import agents, expand, limits, sources
from cubie_benchmarks.planning.gates import validate_gates
from cubie_benchmarks.planning.pairs import agent_paths
from cubie_benchmarks.planning.selection import select_scenarios


def plan_suite(path: str | Path) -> dict:
    """Resolve a version-one suite into a detached, JSON-compatible run plan."""
    path = Path(path).resolve()
    suite = v.read_data(path, toml=True)
    _suite(suite)
    chosen, packages = _selected(path, suite)
    configured_agents = agents(path.parent, agent_paths(suite))
    runs = expand(chosen, configured_agents, suite)
    bounds = limits(suite.get("limits", {}), len(runs), sum(r["budgets"]["wall_time_seconds"] for r in runs))
    return v.snapshot({"schema_version": 1, "name": suite["name"], "profile": suite["profile"],
            "output": str((path.parent / suite["output"]).resolve()), "runs": runs,
            "packages": packages, "seed": suite.get("seed"),
            "gates": validate_gates(suite.get("gates", []), runs), **bounds})


def _repairs(scenarios):
    """Reject overlap and missing reference admission before any agent is started."""
    seen = set()
    for scenario in scenarios:
        if scenario.get("process_profile") != "issue_resolution":
            continue
        source = scenario["source"]
        key = tuple(source[field] for field in ("repo", "instance_id", "base_commit"))
        v.require(key not in seen, "selection", "duplicate overlapping SWE-bench instance")
        seen.add(key)
        v.require(bool(scenario.get("reference_report_sha256")), "reference_report", "repair measurement requires a successful bound reference report")


def _suite(suite):
    """Validate suite identity, profile and repetition settings."""
    v.text(suite.get("name"), "name")
    v.text(suite.get("output"), "output")
    v.choice(suite.get("profile"), {"agent-evaluation", "cubie-vs-pytest"}, "profile")
    v.number(suite.get("repetitions"), "repetitions", positive=True, integer=True)
    v.budgets(suite.get("budgets", {}))
    if "seed" in suite:
        v.require(type(suite["seed"]) is int, "seed", "expected an integer")


def _selected(path, suite):
    """Select scenarios and reject invalid repair admissions."""
    scenarios, packages = sources(path.parent, suite.get("sources"))
    chosen = select_scenarios(scenarios, suite.get("select", {}))
    _repairs(chosen)
    return (chosen, packages)
