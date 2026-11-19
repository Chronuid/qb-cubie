"""Return reporting contracts from GUTACHTEN.md, section 8, priority 1.4.

Check both the independent run result and the reporter's assertion text so a
false positive in EBT cannot conceal a missing return comparison.
"""

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.reporter import PytestReporter


def echo(value):
    return value


@pytest.mark.parametrize("expected, actual", [
    (None, 42), (42, None),
    (0, 1), (1, 0),
    (False, True), (True, False),
    ("", "text"), ("text", ""),
    ([], [1]), ([1], []),
    ({}, {"key": 1}), ({"key": 1}, {}),
    ((), (1,)), ((1,), ()),
    (set(), {1}), ({1}, set()),
], ids=[
    "expected-none", "actual-none", "expected-zero", "actual-zero",
    "expected-false", "actual-false", "expected-empty-string", "actual-empty-string",
    "expected-empty-list", "actual-empty-list", "expected-empty-dict", "actual-empty-dict",
    "expected-empty-tuple", "actual-empty-tuple", "expected-empty-set", "actual-empty-set",
])
@pytest.mark.parametrize("verbosity", [0, 1])
def test_return_mismatch_reports_both_values_even_when_one_is_falsy(expected, actual, verbosity):
    result = EBT(
        target=echo,
        pre=WorldState(args=(actual,)),
        post=WorldState(returns=expected),
        reporter=None,
    ).run()

    assert result.evaluation is False
    assert len(result.traces) == 1
    trace = result.traces[0]
    assert trace.evaluation is False
    assert trace.diffs["returns"]["actual"] == actual

    with pytest.raises(AssertionError) as error:
        PytestReporter(verbosity=verbosity).report(result)

    lines = str(error.value).splitlines()
    assert "  [Q-State 0] Validation: Mismatch" in lines
    assert f"    - Returns: Expected {expected} | Actual {actual} (Mismatch)" in lines


def test_all_alternative_falsy_return_expectations_are_reported():
    expected_values = [None, 0, False, "", [], {}, (), set()]
    case = EBT(
        target=echo,
        pre=WorldState(args=("unexpected-value",)),
        post=[WorldState(returns=value) for value in expected_values],
    )
    with pytest.raises(AssertionError) as error:
        case.run()

    assert case.run_trace.evaluation is False
    assert len(case.run_trace.traces) == len(expected_values)
    assert all(trace.evaluation is False for trace in case.run_trace.traces)
    lines = str(error.value).splitlines()
    for index, expected in enumerate(expected_values):
        state_line = lines.index(f"  [Q-State {index}] Validation: Mismatch")
        assert lines[state_line + 1] == (
            f"    - Returns: Expected {expected} | Actual unexpected-value (Mismatch)"
        )


@pytest.mark.parametrize("value", [None, 0, False, "", [], {}, (), set()])
def test_allowed_falsy_return_passes_with_negative_filter(value):
    result = EBT(
        target=echo,
        pre=WorldState(args=(value,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns=value), WorldState(returns="forbidden", expect=False)],
        },
        reporter=None,
    ).run()

    assert result.evaluation is True
    assert [trace.evaluation for trace in result.traces] == [True, False]


@pytest.mark.parametrize("value", [None, 0, False, "", [], {}, (), set()])
def test_forbidden_falsy_return_reports_the_matching_value(value):
    case = EBT(
        target=echo,
        pre=WorldState(args=(value,)),
        post={
            "quantor": "all",
            "states": [WorldState(returns="allowed"), WorldState(returns=value, expect=False)],
        },
    )
    with pytest.raises(AssertionError) as error:
        case.run()

    assert case.run_trace.evaluation is False
    assert [trace.evaluation for trace in case.run_trace.traces] == [False, True]
    lines = str(error.value).splitlines()
    state_line = lines.index("  [Q-State 1] Validation: Matched")
    assert lines[state_line + 1] == f"    - Returns: Expected {value} | Actual {value} (Match)"


def test_omitted_return_expectation_accepts_non_matching_negative_filter():
    """An unrestricted positive state passes when the negative return filter does not match."""
    result = EBT(
        target=lambda: "ok",
        post={
            "quantor": "all",
            "states": [WorldState(), WorldState(returns="forbidden", expect=False)],
        },
        reporter=None,
    ).run()

    assert result.evaluation is True
    assert [trace.evaluation for trace in result.traces] == [True, False]


def test_omitted_return_expectation_does_not_invent_a_return_comparison():
    """A forbidden unrestricted state fails without specifying returns."""
    case = EBT(
        target=lambda: None,
        post={"quantor": "all", "states": [WorldState(), WorldState(expect=False)]},
    )
    with pytest.raises(AssertionError) as error:
        case.run()

    assert case.run_trace.evaluation is False
    assert "Returns:" not in str(error.value)
    assert "UNSPECIFIED" not in str(error.value)
