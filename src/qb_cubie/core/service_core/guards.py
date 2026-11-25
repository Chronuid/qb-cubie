"""Domain-neutral STATE-GUARD validators and attribute parsers for qb-cubie services."""

from __future__ import annotations

from collections.abc import Sequence
import math
from typing import Any

_TRUE_TOKENS = frozenset({"true", "1", "yes"})
_FALSE_TOKENS = frozenset({"false", "0", "no"})


def validate_choice(value: Any, valid: Sequence[str], field: str) -> str:
    """Validate that value is a string member of a non-empty valid choice sequence."""
    choices = tuple(valid) if isinstance(valid, Sequence) and not isinstance(valid, (str, bytes)) else ()
    if not choices or not isinstance(value, str) or value not in choices:
        raise ValueError(f"STATE-GUARD: {field} must be one of {choices}; received {value!r}.")
    return value


def validate_non_empty_str(value: Any, field: str) -> str:
    """Validate that value is a string containing at least one non-whitespace character."""
    if not isinstance(value, str):
        raise TypeError(f"STATE-GUARD: {field} must be a non-empty string; received {type(value).__name__}.")
    if not value.strip():
        raise ValueError(f"STATE-GUARD: {field} must not be empty or blank.")
    return value


def validate_positive_int(value: Any, field: str) -> int:
    """Validate that value is a strictly positive int while rejecting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"STATE-GUARD: {field} must be a positive int; received {type(value).__name__}.")
    if value <= 0:
        raise ValueError(f"STATE-GUARD: {field} must be > 0; received {value!r}.")
    return value


def validate_positive_float(value: Any, field: str, *, allow_none: bool = False) -> float | None:
    """Validate that value is a strictly positive finite float (or None when allowed)."""
    if value is None:
        if allow_none:
            return None
        raise TypeError(f"STATE-GUARD: {field} must be a positive finite number; received None.")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"STATE-GUARD: {field} must be a positive finite number; received {type(value).__name__}.")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"STATE-GUARD: {field} must be a positive finite number; received {value!r}.")
    return number


def validate_str_sequence(value: Any, field: str, *, allow_none: bool = True) -> tuple[str, ...]:
    """Validate a sequence of strings while rejecting bare str, bytes, and mappings."""
    if value is None:
        if allow_none:
            return ()
        raise TypeError(f"STATE-GUARD: {field} must be a sequence of strings; received None.")
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"STATE-GUARD: {field} must be a sequence of strings; received {type(value).__name__}.")
    if not all(isinstance(item, str) for item in value):
        raise TypeError(f"STATE-GUARD: All entries in {field} must be strings.")
    return tuple(value)


def parse_bool_attr(raw: Any, field: str, *, default: bool = True) -> bool:
    """Parse a boolean string attribute token with strict type and value guards."""
    if type(default) is not bool:
        raise TypeError(f"STATE-GUARD: default for {field} must be a bool; received {type(default).__name__}.")
    if raw is None:
        return default
    if not isinstance(raw, str):
        raise TypeError(f"STATE-GUARD: {field} must be a str or None; received {type(raw).__name__}.")
    token = raw.strip().lower()
    if not token:
        return default
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    raise ValueError(f"STATE-GUARD: {field} must be a boolean token; received {raw!r}.")


def parse_int_attr(raw: Any, field: str, *, allow_none: bool = True) -> int | None:
    """Parse an integer string attribute with strict type and optional-blank guards."""
    if raw is None:
        _ensure_optional_int(field, raw, allow_none)
        return None
    if not isinstance(raw, str):
        raise TypeError(f"STATE-GUARD: {field} must be a str or None; received {type(raw).__name__}.")
    stripped = raw.strip()
    if not stripped:
        _ensure_optional_int(field, raw, allow_none)
        return None
    try:
        return int(stripped)
    except ValueError as exc:
        raise ValueError(f"STATE-GUARD: {field} must be an integer; received {raw!r}.") from exc


def _ensure_optional_int(field: str, raw: Any, allow_none: bool) -> None:
    """Raise ValueError when a required integer attribute is missing or blank."""
    if not allow_none:
        raise ValueError(f"STATE-GUARD: {field} must be an integer string; received {raw!r}.")
