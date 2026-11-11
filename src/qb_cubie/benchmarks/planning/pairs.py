"""Resolve explicit Cubie/Pytest agent pairs without starting adapter code."""

from qb_cubie.benchmarks.contracts import _validation as v


def agent_paths(suite):
    """Return all declared agent files, preserving their first occurrence."""
    if "agent_pairs" not in suite:
        return v.strings(suite.get("agents"), "agents", nonempty=True)
    v.require("agents" not in suite, "agent_pairs", "cannot combine with agents")
    v.require(suite["profile"] == "cubie-vs-pytest", "agent_pairs", "requires cubie-vs-pytest")
    pairs = suite["agent_pairs"]
    v.require(type(pairs) is list and bool(pairs), "agent_pairs", "expected nonempty list")
    return _paths(pairs)


def _paths(pairs):
    """Validate pair identities and collect distinct agent paths in order."""
    paths: list[str] = []
    ids: set[str] = set()
    for pair in pairs:
        v.mapping(pair, "agent_pairs")
        v.require(set(pair) == {"id", "cubie", "pytest"}, "agent_pairs", "expected id, cubie and pytest")
        identifier = v.identifier(pair["id"], "agent_pairs.id")
        v.require(identifier not in ids, "agent_pairs.id", "duplicate pair")
        ids.add(identifier)
        paths.extend(v.text(pair[condition], "agent_pairs." + condition) for condition in ("cubie", "pytest"))
    return list(dict.fromkeys(paths))


def groups(suite, configured_agents):
    """Keep legacy cross products or bind one separately editable agent per arm."""
    if "agent_pairs" not in suite:
        conditions = ("cubie", "pytest") if suite["profile"] == "cubie-vs-pytest" else ("cubie",)
        return [(None, dict.fromkeys(conditions, agent)) for agent in configured_agents]
    by_path = dict(zip(agent_paths(suite), configured_agents, strict=True))
    return [(pair["id"], {condition: by_path[pair[condition]] for condition in ("cubie", "pytest")})
            for pair in suite["agent_pairs"]]
