"""Run isolation contracts from GUTACHTEN.md, section 8, priority 1.2.

These regression cases deliberately assert the desired behavior without xfail.
Independent pytest assertions prevent EBT's own quantifier logic from masking
stale results. Historical snapshots must survive later runs and mutations of
caller-owned data; this does not prescribe a particular frozen trace API.
"""

from copy import deepcopy
from multiprocessing import Manager

import pytest

from cubie import EBT, WorldState


def echo(value):
    return value


@pytest.fixture(params=[False, True], ids=["singleprocess", "multiprocess"])
def execution_mode(request, monkeypatch):
    # Exercise the real process path while bounding its worker count.
    monkeypatch.setattr("cubie.multiprocessors.os.cpu_count", lambda: 2)
    return request.param


@pytest.mark.parametrize("values, expected", [
    ((1, 2), (True, False)),
    ((2, 1), (False, True)),
])
def test_each_run_evaluates_only_its_own_positive_matches(execution_mode, values, expected):
    case = EBT(target=echo, post=WorldState(returns=1), reporter=None,
               multiprocessing=execution_mode)
    for value, matches in zip(values, expected):
        case.pre = [WorldState(args=(value,))]
        result = case.run()
        assert result.evaluation is matches


def test_previous_negative_match_does_not_poison_next_run(execution_mode):
    case = EBT(target=echo, pre=WorldState(args=(0,)),
               post=WorldState(returns=0, expect=False), reporter=None,
               multiprocessing=execution_mode)
    assert case.run().evaluation is False
    case.pre = [WorldState(args=(1,))]
    assert case.run().evaluation is True


def test_global_expect_false_uses_only_current_run(execution_mode):
    case = EBT(target=echo, pre=WorldState(args=(1,)),
               post=WorldState(returns=1), expect=False, reporter=None,
               multiprocessing=execution_mode)
    assert case.run().evaluation is False
    case.pre = [WorldState(args=(2,))]
    assert case.run().evaluation is True


def test_repeated_run_has_exactly_current_matrix_and_outcomes(execution_mode):
    case = EBT(target=echo,
               pre=[WorldState(args=(1,)), WorldState(args=(2,))],
               post=[WorldState(returns=1), WorldState(returns=2)],
               reporter=None, multiprocessing=execution_mode)
    case.run()
    result = case.run()
    assert len(result.traces) == 4
    assert len(case._outcome) == 2
    assert [state.returns for state in case._outcome] == [1, 2]


def test_each_run_and_its_steps_have_distinct_ids(execution_mode):
    case = EBT(target=echo, pre=WorldState(args=(1,)), reporter=None,
               custom_id="repeat", multiprocessing=execution_mode)
    first = case.run()
    first_ids = {trace.step_id for trace in first.traces}
    second = case.run()
    assert second.run_id != first.run_id
    assert first_ids.isdisjoint(trace.step_id for trace in second.traces)
    assert all(trace.step_id == f"{second.run_id}_0" for trace in second.traces)


def test_later_run_does_not_change_previous_run(execution_mode):
    case = EBT(target=echo, pre=WorldState(args=(1,)), reporter=None,
               multiprocessing=execution_mode)
    first = case.run()
    snapshot = deepcopy(first)
    second = case.run()
    assert first == snapshot
    assert first is not second
    assert first.traces is not second.traces
    assert case.run_trace is second


def test_default_reporter_rejects_failure_after_success():
    values = iter([1, 2])
    case = EBT(target=lambda: next(values), post=WorldState(returns=1))
    case.run()
    with pytest.raises(AssertionError):
        case.run()


def test_retry_after_reporter_assertion_has_no_stale_traces():
    values = iter([2, 1])
    case = EBT(target=lambda: next(values), post=WorldState(returns=1))
    with pytest.raises(AssertionError):
        case.run()
    failed = case.run_trace
    snapshot = deepcopy(failed)
    result = case.run()
    assert result.evaluation is True
    assert len(result.traces) == 1
    assert failed == snapshot


def test_retry_after_partial_execution_discards_incomplete_run():
    def fail_on_second(value):
        if value == 2:
            raise ValueError("target failed")
        return value

    case = EBT(target=fail_on_second,
               pre=[WorldState(args=(1,)), WorldState(args=(2,))], reporter=None)
    with pytest.raises(ValueError, match="target failed"):
        case.run()
    case.pre = [WorldState(args=(3,))]
    result = case.run()
    assert len(result.traces) == 1
    assert result.traces[0].outcome.returns == 3
    assert len(case._outcome) == 1


def test_aborted_run_does_not_expose_previous_success_as_current_result():
    def fail():
        raise ValueError("target failed")

    case = EBT(target=lambda: 1, reporter=None)
    first = case.run()
    snapshot = deepcopy(first)
    case.target = fail
    with pytest.raises(ValueError, match="target failed"):
        case.run()
    assert case.run_trace is None
    assert case._run_evaluation is None
    assert case._run_duration is None
    assert first == snapshot


@pytest.mark.parametrize("field", ["pre", "post", "outcome", "diffs"])
def test_history_is_detached_from_nested_caller_owned_data(field):
    actual = {"items": [1]}
    expected = {"items": [2]}
    pre = WorldState(args=(actual,), kwargs={"unused": {"items": [3]}})
    post = WorldState(returns=expected)
    case = EBT(target=lambda value, **kwargs: value, pre=pre, post=post, reporter=None)
    result = case.run()
    snapshot = deepcopy(result)

    if field == "pre":
        pre.kwargs["unused"]["items"].append(4)
    elif field == "post":
        expected["items"].append(4)
        post.expect = False
    else:
        # The returned object also occurs in diffs['returns']['actual'].
        actual["items"].append(4)

    trace = result.traces[0]
    assert getattr(trace, field) == getattr(snapshot.traces[0], field)
    assert result == snapshot


def test_mutating_configuration_for_next_run_preserves_previous_states():
    pre = WorldState(args=(1,))
    post = WorldState(returns=1)
    case = EBT(target=echo, pre=pre, post=post, reporter=None)
    first = case.run()
    snapshot = deepcopy(first)
    pre.args = (2,)
    post.returns = 2
    second = case.run()
    assert second.evaluation is True
    assert first == snapshot


def test_pre_snapshot_records_arguments_before_target_mutation():
    def mutate(value):
        value["items"].append(2)
        return value

    value = {"items": [1]}
    result = EBT(target=mutate, pre=WorldState(args=(value,)), reporter=None).run()
    assert result.traces[0].pre.args == ({"items": [1]},)
    assert result.traces[0].outcome.returns == {"items": [1, 2]}


def test_later_step_cannot_change_already_recorded_outcome():
    shared = []

    def append(value):
        shared.append(value)
        return shared

    result = EBT(target=append,
                 pre=[WorldState(args=(1,)), WorldState(args=(2,))],
                 reporter=None).run()
    assert [trace.outcome.returns for trace in result.traces] == [[1], [1, 2]]


def test_copy_failure_is_reported_instead_of_publishing_shared_history():
    class Uncopyable:
        def __deepcopy__(self, memo):
            raise TypeError("cannot snapshot")

    case = EBT(target=Uncopyable, reporter=None)
    with pytest.raises(TypeError, match="cannot snapshot"):
        case.run()
    assert case.run_trace is None


def test_manager_resources_execute_normally_and_history_survives_shutdown():
    def signal(event):
        event.set()
        return event.is_set()

    with Manager() as manager:
        event = manager.Event()
        result = EBT(target=signal, pre=WorldState(args=(event,)),
                     post=WorldState(returns=True), reporter=None).run()
        assert event.is_set()
        assert result.evaluation is True

    reference = result.traces[0].pre.args[0]
    assert reference.resource_type == "Event"
    assert isinstance(reference.resource_id, str)
    assert result == deepcopy(result)


def test_predicates_see_original_return_value_before_history_is_copied():
    value = {"items": [1]}
    result = EBT(target=lambda: value,
                 post=WorldState(returns=lambda actual: actual is value),
                 reporter=None).run()
    assert result.evaluation is True
    assert result.traces[0].outcome.returns == value
    assert result.traces[0].outcome.returns is not value
