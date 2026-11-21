"""Priority 3.5: returns describe values, never an implicit exception contract."""

import pytest

from qb_cubie import EBT, UNSPECIFIED, TempFS, WorldState


def echo(value):
    return value


@pytest.fixture(params=[False, True], ids=["direct", "tempfs"])
def arena(request):
    return TempFS() if request.param else None


@pytest.mark.parametrize("actual, matches", [
    ({"result": None}, True),
    ({"result": 42}, False),
    ({}, False),
])
def test_nested_none_requires_a_present_key_with_none(arena, actual, matches):
    result = EBT(target=echo, arena=arena, pre=WorldState(args=(actual,)),
                 post=WorldState(returns={"result": None}), reporter=None).run()
    assert result.evaluation is matches
    assert result.traces[0].evaluation is matches
    assert bool((result.traces[0].diffs or {}).get("returns")) is (not matches)


@pytest.mark.parametrize("actual, matches", [(None, False), (UNSPECIFIED, True)])
def test_nested_unspecified_is_a_value_not_a_wildcard(arena, actual, matches):
    result = EBT(target=echo, arena=arena, pre=WorldState(args=([actual],)),
                 post=WorldState(returns=[UNSPECIFIED]), reporter=None).run()
    assert result.evaluation is matches
    assert result.traces[0].evaluation is matches
    assert result.traces[0].outcome.returns[0] is actual


def test_returned_exception_is_an_ordinary_return_value(arena):
    result = EBT(target=echo, arena=arena, pre=WorldState(args=(ValueError("invalid"),)),
                 post=WorldState(returns=ValueError), reporter=None).run()
    assert result.evaluation is True
    observed = result.traces[0].outcome.returns
    assert type(observed) is ValueError
    assert str(observed) == "invalid"


@pytest.mark.parametrize("value, pattern", [(False, int), (0, False), ([1], (1,))])
def test_existing_python_value_and_pattern_semantics_remain_explicit(arena, value, pattern):
    """No silent switch to strict bool/int equality or list/tuple identity."""
    result = EBT(target=echo, arena=arena, pre=WorldState(args=(value,)),
                 post=WorldState(returns=pattern), reporter=None).run()
    assert result.evaluation is True
    assert type(result.traces[0].outcome.returns) is type(value)
