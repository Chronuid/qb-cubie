"""Return contracts from GUTACHTEN.md, section 8, priority 1.1.

An omitted return expectation is unrestricted; explicit None is an exact value.
Use independent assertions so EBT cannot conceal an incorrect positive result.
"""

import copy
import pickle

import cloudpickle
import pytest

from qb_cubie import EBT, UNSPECIFIED, WorldState
from qb_cubie.arenas.tempfs import TempFS


def echo(value):
    return value


def test_omitted_return_expectation_is_distinct_from_explicit_none():
    assert WorldState().returns is UNSPECIFIED
    assert WorldState(returns=None).returns is None


@pytest.mark.parametrize("clone", [
    copy.copy, copy.deepcopy,
    lambda value: pickle.loads(pickle.dumps(value)),
    lambda value: cloudpickle.loads(cloudpickle.dumps(value)),
], ids=["copy", "deepcopy", "pickle", "cloudpickle"])
def test_sentinel_identity_survives_world_state_copy_and_serialization(clone):
    assert clone(WorldState()).returns is UNSPECIFIED
    assert clone(WorldState(returns=None)).returns is None


def test_explicit_sentinel_leaves_return_value_unrestricted():
    result = EBT(
        target=echo,
        pre=WorldState(args=(42,)),
        post=WorldState(returns=UNSPECIFIED),
        reporter=None,
    ).run()

    assert result.evaluation is True
    assert not result.traces[0].diffs


@pytest.mark.parametrize("actual", [None, 42, 0, False, "", [], {}])
def test_explicit_none_matches_only_none(actual):
    result = EBT(
        target=echo,
        pre=WorldState(args=(actual,)),
        post=WorldState(returns=None),
        reporter=None,
    ).run()

    assert len(result.traces) == 1
    trace = result.traces[0]
    assert type(trace.outcome.returns) is type(actual)
    assert trace.outcome.returns == actual
    assert trace.evaluation is (actual is None)
    assert result.evaluation is (actual is None)
    if actual is None:
        assert not trace.diffs
    else:
        assert "returns" in trace.diffs
        assert trace.diffs["returns"]["actual"] == actual


@pytest.mark.parametrize("actual", [None, 42, 0, False, "", [], {}])
def test_omitted_return_expectation_accepts_any_actual_value(actual):
    result = EBT(
        target=echo,
        pre=WorldState(args=(actual,)),
        post=WorldState(),
        reporter=None,
    ).run()

    assert len(result.traces) == 1
    assert type(result.traces[0].outcome.returns) is type(actual)
    assert result.traces[0].outcome.returns == actual
    assert result.traces[0].evaluation is True
    assert not result.traces[0].diffs
    assert result.evaluation is True


@pytest.mark.parametrize("actual", [None, 42, 0, False])
def test_negative_none_contract_forbids_only_none(actual):
    result = EBT(
        target=echo,
        pre=WorldState(args=(actual,)),
        post=WorldState(returns=None, expect=False),
        reporter=None,
    ).run()

    assert len(result.traces) == 1
    # A matching negative post-state makes the overall contract fail.
    assert result.traces[0].evaluation is (actual is None)
    assert result.evaluation is (actual is not None)


@pytest.mark.parametrize("actual, matches", [(None, True), (42, True), (99, False)])
def test_none_in_alternative_post_states_is_not_a_wildcard(actual, matches):
    result = EBT(
        target=echo,
        pre=WorldState(args=(actual,)),
        post=[WorldState(returns=None), WorldState(returns=42)],
        reporter=None,
    ).run()

    assert len(result.traces) == 2
    assert [trace.evaluation for trace in result.traces] == [
        actual is None, actual == 42,
    ]
    assert result.evaluation is matches


def test_default_reporter_rejects_non_none_when_none_is_expected():
    with pytest.raises(AssertionError, match="Expected None \\| Actual 42"):
        EBT(
            target=echo,
            pre=WorldState(args=(42,)),
            post=WorldState(returns=None),
        ).run()


@pytest.mark.parametrize("expected, actual", [(42, None), (0, 1), (False, True), ("", "x"), ([], [1])])
def test_reporter_includes_none_and_falsy_return_values(expected, actual):
    with pytest.raises(AssertionError) as error:
        EBT(
            target=echo,
            pre=WorldState(args=(actual,)),
            post=WorldState(returns=expected),
        ).run()

    assert f"Expected {expected} | Actual {actual}" in str(error.value)


def write_file_and_return_value(value):
    from pathlib import Path

    Path("output.txt").write_text("created", encoding="utf-8")
    return value


@pytest.mark.parametrize("actual", [None, 42])
@pytest.mark.parametrize("specify_none", [False, True], ids=["omitted", "explicit-none"])
def test_filesystem_contract_preserves_return_expectation(tmp_path, actual, specify_none):
    expected_file = tmp_path / "expected.txt"
    expected_file.write_text("created", encoding="utf-8")
    post = WorldState(fs={"output.txt": str(expected_file)})
    if specify_none:
        post.returns = None

    result = EBT(
        arena=TempFS(),
        target=write_file_and_return_value,
        pre=WorldState(args=(actual,)),
        post=post,
        reporter=None,
    ).run()

    assert len(result.traces) == 1
    trace = result.traces[0]
    assert trace.outcome.returns == actual
    assert "fs" not in (trace.diffs or {})
    matches = not specify_none or actual is None
    assert trace.evaluation is matches
    assert result.evaluation is matches
