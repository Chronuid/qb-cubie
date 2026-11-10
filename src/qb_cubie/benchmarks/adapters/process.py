"""Validate and connect version-one external benchmark agents."""

import time
from pathlib import Path

from qb_cubie.benchmarks.adapters._transport import JsonlProcess
from qb_cubie.benchmarks.adapters.provenance import handshake_model, validate_model
from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.execution._process import ExecutionError


def configuration(path):
    """Load a process configuration and resolve cwd from its original file."""
    path = Path(path).resolve()
    agent = v.read_data(path, toml=True)
    validate_config(agent)
    cwd = (path.parent / agent.get("cwd", ".")).resolve()
    v.require(cwd.is_dir(), "agent.cwd", f"missing directory: {cwd}")
    return agent, cwd


def validate_config(agent):
    """Check data-only process options without starting a program."""
    v.version(agent)
    v.identifier(agent.get("id"), "agent.id")
    v.require("transport" in agent, "agent.command", "external commands require transport = jsonl-v1")
    v.choice(agent.get("transport"), {"jsonl-v1"}, "agent.transport")
    v.command(agent.get("command"))
    v.strings(agent.get("capabilities"), "agent.capabilities")
    v.text(agent.get("cwd", "."), "agent.cwd")
    if "model" in agent:
        validate_model(agent["model"])


def handshake(peer, agent, required=()):
    """Confirm identity, protocol version and actually available abilities."""
    answer = peer.exchange({"schema_version": 1, "type": "capabilities"})
    v.require(answer.get("type") == "capabilities", "type", "expected capabilities response")
    v.require(answer.get("agent_id") == agent["id"], "agent_id", "unexpected process identity")
    v.text(answer.get("agent_version"), "agent_version")
    actual = v.strings(answer.get("capabilities"), "capabilities")
    missing = (set(required) | set(agent["capabilities"])) - set(actual)
    v.require(not missing, "capabilities", f"process is missing {sorted(missing)}")
    return {"schema_version": 1, "valid": True, **{key: answer[key]
            for key in ("agent_id", "agent_version", "capabilities")}, **handshake_model(agent, answer)}


def probe(agent, cwd, required=()):
    """Check the live peer with a bounded handshake and no scenario request."""
    try:
        with JsonlProcess(agent["command"], cwd, time.monotonic() + 5) as peer:
            result = handshake(peer, agent, required)
            peer.finish()
            return result
    except (ExecutionError, OSError) as error:
        raise ValueError(f"agent handshake: {error}") from error


def validate_agent(path: str | Path) -> dict:
    """Validate the configured external process without running a scenario."""
    agent, cwd = configuration(path)
    return probe(agent, cwd)
