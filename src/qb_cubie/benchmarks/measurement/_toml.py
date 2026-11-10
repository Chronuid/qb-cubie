"""Serialize JSON-compatible TOML inputs while preserving their data semantics."""

import json

from qb_cubie.benchmarks.contracts import _validation as v


def write_toml(path, data):
    """Write top-level assignments with recursively encoded inline tables."""
    path.write_text("\n".join(f"{json.dumps(key)} = {_literal(value)}" for key, value in data.items()) + "\n", encoding="utf-8")


def _literal(value):
    """Encode TOML scalar, array or inline table values without shell interpolation."""
    if type(value) is dict:
        return "{ " + ", ".join(f"{json.dumps(key)} = {_literal(item)}" for key, item in value.items()) + " }"
    if type(value) is list:
        return "[" + ", ".join(_literal(item) for item in value) + "]"
    v.require(type(value) in {str, int, float, bool}, "frozen.toml", "unsupported TOML value")
    return json.dumps(value, ensure_ascii=False, allow_nan=False)
