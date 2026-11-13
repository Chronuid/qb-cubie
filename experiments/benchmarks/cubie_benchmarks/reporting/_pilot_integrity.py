"""Reject pilot pools that would silently mix incompatible experimental contracts."""

import json

from cubie_benchmarks.adapters.provenance import validate_model
from cubie_benchmarks.contracts import _validation as v

TASK_IDENTITY = ("package", "evaluator_id", "evaluator_version", "source_tree_sha256", "task_sha256",
                 "context_sha256", "budgets", "split", "types", "group_id")


def compatible(entries):
    """Allow repeated attempts while requiring stable task and agent identities."""
    tasks: dict[tuple[str, str], str] = {}
    agents: dict[str, str] = {}
    for root, run in entries:
        key = (run["scenario_id"], run["condition"])
        identity = {name: run[name] for name in TASK_IDENTITY}
        _same(tasks, key, identity, "scenario")
        agent = v.read_data(root / "inputs" / "agents" / (run["agent_id"] + ".toml"), toml=True)
        _model(run, agent)
        _same(agents, run["agent_id"], {"configuration": agent, "version": run.get("agent_version")}, "agent")


def _model(run, agent):
    """Check that reported model provenance still matches the archived declaration."""
    model = run.get("model_provenance")
    if not model:
        v.require(run.get("model_id") is None, "model", "model_id without provenance")
        return
    v.require(run["agent_kind"] == "process", "model", "fake attempts are not model observations")
    v.require(model.get("source") == "matched_agent_handshake", "model", "unbound model provenance")
    declaration = validate_model({key: value for key, value in model.items() if key != "source"})
    v.require(declaration == agent.get("model") and run["model_id"] == declaration["model_id"],
              "model", "provenance differs from archived agent configuration")


def _same(identities, key, value, label):
    """Require an explicit new identity when an experimental input changes."""
    signature = json.dumps(value, sort_keys=True, allow_nan=False)
    v.require(key not in identities or identities[key] == signature, "archive", f"incompatible {label} identity: {key}")
    identities[key] = signature
