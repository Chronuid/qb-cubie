"""GUTACHTEN 9.1 / B1: decide against the contract recorded before execution.

These are desired contracts, deliberately without xfail. pytest independently
checks the verdict, raw match and evidence; EBT must not validate itself alone.
"""

import json

import pytest

from qb_cubie import EBT, ExceptionExpectation, JsonReporter, PytestReporter, WorldState


@pytest.mark.parametrize("reporting", ["silent", "pytest", "json"])
@pytest.mark.parametrize("forbidden", [False, True], ids=["required", "forbidden"])
def test_replacing_return_contract_cannot_rewrite_the_verdict(tmp_path, reporting, forbidden):
    post = WorldState(returns=7, expect=not forbidden)
    path = tmp_path / "trace.json"
    reporters = {"silent": None, "pytest": PytestReporter(), "json": JsonReporter(path)}

    def mutate():
        post.returns = 42
        return 42

    case = EBT(target=mutate, post=post, reporter=reporters[reporting])
    if reporting == "pytest" and not forbidden:
        with pytest.raises(AssertionError, match="EBT-Assert failed"):
            case.run()
    else:
        case.run()
    result = case.run_trace
    assert result is not None
    trace = result.traces[0]
    assert post.returns == 42, "The target must actually have performed the mutation"
    assert trace.post.returns == 7
    assert trace.outcome.returns == 42
    assert trace.evaluation is False
    assert trace.diffs["returns"] == {"expected": "7", "actual": 42}
    assert result.evaluation is forbidden
    if reporting == "json":
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["evaluation"] is forbidden
        assert document["traces"][0]["evaluation"] is False
        assert document["traces"][0]["post"]["returns"]["value"] == 7


def test_nested_expectation_shared_with_input_cannot_follow_target_mutation():
    shared = {"items": [7]}

    def mutate(value):
        value["items"][0] = 42
        return value

    result = EBT(target=mutate, pre=WorldState(args=(shared,)),
                 post=WorldState(returns=shared), reporter=None).run()
    trace = result.traces[0]
    assert shared == {"items": [42]}
    assert trace.pre.args == ({"items": [7]},)
    assert trace.post.returns == {"items": [7]}
    assert trace.outcome.returns == {"items": [42]}
    assert result.evaluation is False
    assert trace.evaluation is False
    assert trace.diffs["returns"] == {
        "expected": "{'items': [7]}", "actual": {"items": [42]},
    }


def test_target_cannot_remove_an_unsatisfied_post_from_the_matrix():
    posts = [WorldState(returns=7)]

    def mutate():
        posts.clear()
        return 42

    result = EBT(target=mutate, post=posts, reporter=None).run()
    assert posts == []
    assert len(result.traces) == 1
    assert result.traces[0].post.returns == 7
    assert result.traces[0].outcome.returns == 42
    assert result.traces[0].evaluation is False
    assert result.evaluation is False


def test_target_cannot_replace_expected_exception_before_comparison():
    post = WorldState(raises=ExceptionExpectation(ValueError, match="^required$"))

    def mutate():
        post.raises = ExceptionExpectation(TypeError, match="^actual$")
        raise TypeError("actual")

    result = EBT(target=mutate, post=post, reporter=None).run()
    trace = result.traces[0]
    assert trace.post.raises == ExceptionExpectation(ValueError, match="^required$")
    assert isinstance(trace.outcome.exception, TypeError)
    assert trace.evaluation is False
    assert "raises" in trace.diffs
    assert result.evaluation is False


def test_snapshotting_contract_preserves_identity_predicates_on_actual_values():
    value = object()
    result = EBT(target=lambda: value,
                 post=WorldState(returns=lambda actual: actual is value)).run()
    assert result.evaluation is True
    assert result.traces[0].evaluation is True
    assert result.traces[0].diffs is None


def test_uncopyable_contract_fails_before_target_and_reporter_are_called():
    class Uncopyable:
        def __deepcopy__(self, memo):
            raise TypeError("contract cannot be snapshotted")

    calls = []

    class Reporter:
        def report(self, trace):
            calls.append("report")

    case = EBT(target=lambda: calls.append("target"),
               post=WorldState(returns=Uncopyable()), reporter=Reporter())
    with pytest.raises(TypeError, match="contract cannot be snapshotted"):
        case.run()
    assert calls == []
    assert case.run_trace is None


def test_all_inputs_use_the_contract_fixed_at_run_start():
    post = WorldState(returns=7)

    def mutate(value):
        post.returns = 42
        return value

    result = EBT(target=mutate, pre=[WorldState(args=(7,)), WorldState(args=(42,))],
                 post=post, reporter=None).run()
    assert post.returns == 42
    assert [trace.post.returns for trace in result.traces] == [7, 7]
    assert [trace.evaluation for trace in result.traces] == [True, False]
    assert result.evaluation is False
