"""Bind optional model declarations to both configuration and live handshakes."""

from qb_cubie.benchmarks.contracts import _validation as v

FIELDS = {"model_id", "revision", "provider", "provider_version", "adapter_version", "parameters", "prompt_sha256"}


def validate_model(value):
    """Validate a complete declared model identity without assuming provider access."""
    v.mapping(value, "model")
    v.require(set(value) == FIELDS, "model", f"expected fields: {sorted(FIELDS)}")
    for field in FIELDS - {"parameters", "prompt_sha256"}:
        v.text(value[field], "model." + field)
    v.mapping(value["parameters"], "model.parameters")
    checksum = value["prompt_sha256"]
    v.require(type(checksum) is str and len(checksum) == 64 and all(char in "0123456789abcdef" for char in checksum),
              "model.prompt_sha256", "expected lowercase SHA-256")
    return v.snapshot(value)


def handshake_model(agent, answer):
    """Accept a declaration only when the live adapter matches its frozen config."""
    if "model" not in agent:
        return {}
    expected = validate_model(agent["model"])
    actual = validate_model(answer.get("model"))
    v.require(actual == expected, "model", "live model declaration differs from agent configuration")
    return {"model_id": actual["model_id"], "model_provenance": {**actual, "source": "matched_agent_handshake"}}
