"""**Tries to** specify Cycle 1 STATE-GUARD validators and attribute parsers in core.service_core.guards."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

from qb_cubie import EBT, ExceptionExpectation, WorldState

pytestmark = pytest.mark.services


def _guards_module() -> Any:
    """Lazily imports qb_cubie.core.service_core.guards so Phase-Red collection stays clean."""
    return importlib.import_module("qb_cubie.core.service_core.guards")


def _call_validate_choice(value: Any, valid: Any, field: str = "mode") -> str:
    """Invokes service_core.guards.validate_choice."""
    return _guards_module().validate_choice(value, valid, field)


def _call_validate_non_empty_str(value: Any, field: str = "id") -> str:
    """Invokes service_core.guards.validate_non_empty_str."""
    return _guards_module().validate_non_empty_str(value, field)


def _call_validate_positive_int(value: Any, field: str = "limit") -> int:
    """Invokes service_core.guards.validate_positive_int."""
    return _guards_module().validate_positive_int(value, field)


def _call_validate_positive_float(value: Any, field: str = "timeout", allow_none: bool = False) -> float | None:
    """Invokes service_core.guards.validate_positive_float."""
    return _guards_module().validate_positive_float(value, field, allow_none=allow_none)


def _call_validate_str_sequence(
    value: Any, field: str = "excludes", allow_none: bool = True
) -> tuple[str, ...]:
    """Invokes service_core.guards.validate_str_sequence."""
    return _guards_module().validate_str_sequence(value, field, allow_none=allow_none)


def _call_parse_bool_attr(raw: Any, field: str = "routable", default: Any = True) -> bool:
    """Invokes service_core.guards.parse_bool_attr."""
    return _guards_module().parse_bool_attr(raw, field, default=default)


def _call_parse_int_attr(raw: Any, field: str = "order", allow_none: bool = True) -> int | None:
    """Invokes service_core.guards.parse_int_attr."""
    return _guards_module().parse_int_attr(raw, field, allow_none=allow_none)


# ======================================================================================================================
# 1. validate_choice (Ersetzt validate_severity / validate_zone / validate_wrap_tag / validate_catalog_mode)
# ======================================================================================================================


@pytest.mark.parametrize("value", ["error", "warning"])
def test_ebt_validate_choice_accepts_member_of_valid_set(value: str) -> None:
    """Valid string members are returned unchanged."""
    EBT(
        target=_call_validate_choice,
        pre=WorldState(args=(value, ("error", "warning"), "severity")),
        post=WorldState(returns=value),
        custom_id=f"service_core_guards_choice_valid_{value}",
    ).run()


def test_ebt_validate_choice_rejects_unknown_and_non_string_values() -> None:
    """Unknown choices, non-strings, and empty valid sets raise ValueError STATE-GUARD."""
    EBT(
        target=_call_validate_choice,
        pre=[
            WorldState(args=("fatal", ("error", "warning"), "severity")),
            WorldState(args=("", ("error", "warning"), "severity")),
            WorldState(args=(None, ("error", "warning"), "severity")),
            WorldState(args=(123, ("error", "warning"), "severity")),
            WorldState(args=(True, ("error", "warning"), "severity")),
            WorldState(args=("error", (), "severity")),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:.*severity")),
        custom_id="service_core_guards_choice_invalid",
    ).run()


# ======================================================================================================================
# 2. validate_non_empty_str
# ======================================================================================================================


@pytest.mark.parametrize("value", ["CUBIE_DOC_FRAME_1", "  kept-padding  ", "a"])
def test_ebt_validate_non_empty_str_accepts_non_blank_strings(value: str) -> None:
    """Non-empty strings with visible characters are returned unmodified."""
    EBT(
        target=_call_validate_non_empty_str,
        pre=WorldState(args=(value, "frame_id")),
        post=WorldState(returns=value),
        custom_id="service_core_guards_non_empty_str_valid",
    ).run()


def test_ebt_validate_non_empty_str_rejects_blank_and_non_strings() -> None:
    """Blank strings raise ValueError STATE-GUARD; non-strings raise TypeError STATE-GUARD."""
    EBT(
        target=_call_validate_non_empty_str,
        pre=[
            WorldState(args=("", "frame_id")),
            WorldState(args=("   \t\n", "frame_id")),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:.*frame_id")),
        custom_id="service_core_guards_non_empty_str_blank",
    ).run()
    EBT(
        target=_call_validate_non_empty_str,
        pre=[
            WorldState(args=(None, "frame_id")),
            WorldState(args=(42, "frame_id")),
            WorldState(args=(["a"], "frame_id")),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*frame_id")),
        custom_id="service_core_guards_non_empty_str_type",
    ).run()


# ======================================================================================================================
# 3. validate_positive_int & validate_positive_float (inkl. bool-ist-int-Falle)
# ======================================================================================================================


@pytest.mark.parametrize("value", [1, 12, 500])
def test_ebt_validate_positive_int_accepts_positive_integers(value: int) -> None:
    """Strictly positive integers are returned as exact ints."""
    EBT(
        target=_call_validate_positive_int,
        pre=WorldState(args=(value, "max_lines")),
        post=WorldState(returns=value),
        custom_id=f"service_core_guards_pos_int_valid_{value}",
    ).run()


def test_ebt_validate_positive_int_rejects_non_positive_and_bool_trap() -> None:
    """Zero and negatives raise ValueError; bool, float, str, and None raise TypeError."""
    EBT(
        target=_call_validate_positive_int,
        pre=[
            WorldState(args=(0, "max_lines")),
            WorldState(args=(-1, "max_lines")),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:.*max_lines")),
        custom_id="service_core_guards_pos_int_value",
    ).run()
    EBT(
        target=_call_validate_positive_int,
        pre=[
            WorldState(args=(True, "max_lines")),
            WorldState(args=(False, "max_lines")),
            WorldState(args=(1.0, "max_lines")),
            WorldState(args=("5", "max_lines")),
            WorldState(args=(None, "max_lines")),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*max_lines")),
        custom_id="service_core_guards_pos_int_type_and_bool_trap",
    ).run()


@pytest.mark.parametrize("raw, allow_none, expected", [(1, False, 1.0), (2.5, False, 2.5), (None, True, None)])
def test_ebt_validate_positive_float_valid_cases(
    raw: int | float | None, allow_none: bool, expected: float | None
) -> None:
    """Positive numbers normalize to float; None is accepted only when allow_none=True."""
    EBT(
        target=_call_validate_positive_float,
        pre=WorldState(args=(raw, "timeout", allow_none)),
        post=WorldState(returns=expected),
        custom_id=f"service_core_guards_pos_float_valid_{raw}_{allow_none}",
    ).run()


def test_ebt_validate_positive_float_rejects_invalid_values_and_types() -> None:
    """Non-positive or non-finite numbers raise ValueError; bool, str, and disallowed None raise TypeError."""
    EBT(
        target=_call_validate_positive_float,
        pre=[
            WorldState(args=(0, "timeout", False)),
            WorldState(args=(-0.1, "timeout", False)),
            WorldState(args=(float("inf"), "timeout", False)),
            WorldState(args=(float("-inf"), "timeout", False)),
            WorldState(args=(float("nan"), "timeout", False)),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:.*timeout")),
        custom_id="service_core_guards_pos_float_value",
    ).run()
    EBT(
        target=_call_validate_positive_float,
        pre=[
            WorldState(args=(None, "timeout", False)),
            WorldState(args=(True, "timeout", True)),
            WorldState(args=(False, "timeout", True)),
            WorldState(args=("10.0", "timeout", True)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*timeout")),
        custom_id="service_core_guards_pos_float_type",
    ).run()


# ======================================================================================================================
# 4. validate_str_sequence (Schutz gegen nackte Strings & Bytes)
# ======================================================================================================================


@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, ()),
        ((), ()),
        (["docs/drafts", "tests"], ("docs/drafts", "tests")),
        (("a", "b"), ("a", "b")),
    ],
)
def test_ebt_validate_str_sequence_normalizes_valid_inputs(raw: Any, expected: tuple[str, ...]) -> None:
    """Valid sequences of strings (and optional None) normalize to a tuple[str, ...]."""
    EBT(
        target=_call_validate_str_sequence,
        pre=WorldState(args=(raw, "excludes", True)),
        post=WorldState(returns=expected),
        custom_id="service_core_guards_str_seq_valid",
    ).run()


def test_ebt_validate_str_sequence_rejects_bare_strings_and_bad_elements() -> None:
    """Bare str, bytes, non-sequences, non-str elements, and disallowed None raise TypeError STATE-GUARD."""
    EBT(
        target=_call_validate_str_sequence,
        pre=[
            WorldState(args=("tests", "excludes", True)),
            WorldState(args=(b"tests", "excludes", True)),
            WorldState(args=(123, "excludes", True)),
            WorldState(args=({"tests": True}, "excludes", True)),
            WorldState(args=(["valid", 99], "excludes", True)),
            WorldState(args=(None, "excludes", False)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*excludes")),
        custom_id="service_core_guards_str_seq_invalid",
    ).run()


# ======================================================================================================================
# 5. parse_bool_attr & parse_int_attr (Eliminiert Duplikat D5)
# ======================================================================================================================


@pytest.mark.parametrize(
    "raw, default, expected",
    [
        ("true", False, True),
        (" TRUE ", False, True),
        ("1", False, True),
        ("yes", False, True),
        ("false", True, False),
        (" False ", True, False),
        ("0", True, False),
        ("no", True, False),
        (None, True, True),
        ("   ", False, False),
    ],
)
def test_ebt_parse_bool_attr_valid_values(raw: str | None, default: bool, expected: bool) -> None:
    """Standard truthy/falsy string tokens parse deterministically; None/blank falls back to default."""
    EBT(
        target=_call_parse_bool_attr,
        pre=WorldState(args=(raw, "routable", default)),
        post=WorldState(returns=expected),
        custom_id=f"service_core_guards_bool_attr_{raw}_{default}",
    ).run()


def test_ebt_parse_bool_attr_rejects_invalid_tokens_and_types() -> None:
    """Unknown tokens raise ValueError; non-str raw inputs and non-bool defaults raise TypeError."""
    EBT(
        target=_call_parse_bool_attr,
        pre=[
            WorldState(args=("maybe", "routable", True)),
            WorldState(args=("2", "routable", True)),
            WorldState(args=("y", "routable", True)),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:.*routable")),
        custom_id="service_core_guards_bool_attr_value_guard",
    ).run()
    EBT(
        target=_call_parse_bool_attr,
        pre=[
            WorldState(args=(True, "routable", False)),
            WorldState(args=(1, "routable", False)),
            WorldState(args=(None, "routable", 1)),
            WorldState(args=(None, "routable", "true")),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_guards_bool_attr_type_guard",
    ).run()


@pytest.mark.parametrize(
    "raw, allow_none, expected",
    [
        ("0", True, 0),
        ("10", False, 10),
        (" -7 ", True, -7),
        (None, True, None),
        ("   ", True, None),
    ],
)
def test_ebt_parse_int_attr_valid_values(raw: str | None, allow_none: bool, expected: int | None) -> None:
    """Valid integer strings parse to int; None/blank returns None when allow_none=True."""
    EBT(
        target=_call_parse_int_attr,
        pre=WorldState(args=(raw, "order", allow_none)),
        post=WorldState(returns=expected),
        custom_id=f"service_core_guards_int_attr_{raw}_{allow_none}",
    ).run()


def test_ebt_parse_int_attr_rejects_invalid_strings_and_types() -> None:
    """Non-integer strings and disallowed blanks raise ValueError; non-str raw raises TypeError."""
    EBT(
        target=_call_parse_int_attr,
        pre=[
            WorldState(args=("abc", "order", True)),
            WorldState(args=("1.5", "order", True)),
            WorldState(args=(None, "order", False)),
            WorldState(args=("  ", "order", False)),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:.*order")),
        custom_id="service_core_guards_int_attr_value_guard",
    ).run()
    EBT(
        target=_call_parse_int_attr,
        pre=[
            WorldState(args=(10, "order", True)),
            WorldState(args=(True, "order", True)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:.*order")),
        custom_id="service_core_guards_int_attr_type_guard",
    ).run()
