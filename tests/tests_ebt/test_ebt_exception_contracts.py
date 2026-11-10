"""Priority 3.5 desired exception API; see CONTRACT_CASES_3_5.md.

Imports of the proposed model stay inside tests so absent APIs fail individual
cases without breaking collection of existing tests. No xfail or fallback shim.
"""

from pathlib import Path

import pytest

from qb_cubie import EBT, UNSPECIFIED, TempFS, WorldState
from qb_cubie.reporter import PytestReporter


def expectation(exception_type=ValueError, match=None):
    from qb_cubie.protocols import ExceptionExpectation

    return ExceptionExpectation(exception_type=exception_type, match=match)


def operation(mode):
    if mode == "value-error":
        raise ValueError("invalid order: 17")
    if mode == "wrong-message":
        raise ValueError("unknown customer")
    if mode == "wrong-type":
        raise TypeError("invalid order: 17")
    if mode == "subclass":
        raise UnicodeError("invalid order: 17")
    if mode == "returned-exception":
        return ValueError("invalid order: 17")
    return None


@pytest.fixture(params=[False, True], ids=["direct", "tempfs"])
def arena(request):
    return TempFS() if request.param else None


@pytest.mark.parametrize("mode, matches", [
    ("value-error", True), ("subclass", True),
    ("wrong-type", False), ("wrong-message", False),
    ("returned-exception", False), ("none", False),
])
def test_exception_type_and_message_form_one_contract(arena, mode, matches):
    result = EBT(
        target=operation, arena=arena, pre=WorldState(args=(mode,)),
        post=WorldState(raises=expectation(match=r"^invalid order: \d+$")),
        reporter=None,
    ).run()
    assert result.evaluation is matches
    assert len(result.traces) == 1
    trace = result.traces[0]
    assert trace.evaluation is matches
    assert ("raises" in (trace.diffs or {})) is (not matches)
    if mode in {"none", "returned-exception"}:
        assert trace.outcome.exception is None
        assert trace.outcome.returns is not UNSPECIFIED
    else:
        assert isinstance(trace.outcome.exception, Exception)
        assert trace.outcome.returns is UNSPECIFIED
    if arena:
        assert arena.workspace_path is None


@pytest.mark.parametrize("mode, expected", [("none", [True, False]), ("value-error", [False, True])])
def test_return_and_exception_are_distinct_post_alternatives(arena, mode, expected):
    result = EBT(
        target=operation, arena=arena, pre=WorldState(args=(mode,)),
        post=[WorldState(returns=None), WorldState(raises=expectation())], reporter=None,
    ).run()
    assert result.evaluation is True
    assert [trace.evaluation for trace in result.traces] == expected


@pytest.mark.parametrize("mode, matches", [("value-error", True), ("wrong-message", False)])
def test_forbidden_exception_uses_raw_match_then_negates(arena, mode, matches):
    result = EBT(
        target=operation, arena=arena, pre=WorldState(args=(mode,)),
        post=WorldState(raises=expectation(match="^invalid order:"), expect=False),
        reporter=None,
    ).run()
    assert result.traces[0].evaluation is matches
    assert result.evaluation is (not matches)


@pytest.mark.parametrize("global_expect", [True, False])
def test_undeclared_target_exception_still_propagates(arena, global_expect):
    case = EBT(target=operation, arena=arena, pre=WorldState(args=("value-error",)),
               post=WorldState(), expect=global_expect, reporter=None)
    with pytest.raises(ValueError) as error:
        case.run()
    # TempFS adds traceback notes; pytest's regex matching includes those notes.
    assert str(error.value) == "invalid order: 17"
    assert case.run_trace is None
    if arena:
        assert arena.workspace_path is None


@pytest.mark.parametrize("correct_fs", [True, False])
def test_exception_and_filesystem_expectations_must_both_match(tmp_path, correct_fs):
    def write_then_raise():
        Path("error.txt").write_text("invalid order", encoding="utf-8")
        raise ValueError("invalid order: 17")

    reference = tmp_path / "expected.txt"
    reference.write_text("invalid order" if correct_fs else "different", encoding="utf-8")
    arena = TempFS()
    result = EBT(target=write_then_raise, arena=arena,
                 post=WorldState(raises=expectation(ValueError), fs={"error.txt": str(reference)}),
                 reporter=None).run()
    assert result.evaluation is correct_fs
    trace = result.traces[0]
    assert "raises" not in (trace.diffs or {})
    assert ("fs" in (trace.diffs or {})) is (not correct_fs)
    assert type(trace.outcome.exception) is ValueError
    assert arena.workspace_path is None


@pytest.mark.parametrize("multiprocessing", [False, True], ids=["sequential", "process-pool"])
def test_exception_matching_is_evaluated_per_input(multiprocessing):
    result = EBT(
        target=operation,
        pre=[WorldState(args=("value-error",)), WorldState(args=("wrong-message",))],
        post=WorldState(raises=expectation(match="^invalid order:")),
        multiprocessing=multiprocessing, max_workers=2, reporter=None,
    ).run()
    assert result.evaluation is False
    assert [trace.evaluation for trace in result.traces] == [True, False]
    assert len({trace.step_id for trace in result.traces}) == 2


def test_exception_mismatch_is_an_ebt_failure_with_expected_and_observed_evidence(arena):
    case = EBT(target=operation, arena=arena, pre=WorldState(args=("wrong-type",)),
               post=WorldState(raises=expectation(match="^invalid order:")), reporter=None)
    result = case.run()
    assert result.evaluation is False
    with pytest.raises(AssertionError, match="EBT-Assert failed") as error:
        PytestReporter().report(result)
    for detail in ("ValueError", "TypeError", "invalid order:"):
        assert detail in str(error.value)


@pytest.mark.parametrize("invalid", ["return-and-raise", "instance", "non-exception", "base-exception", "regex"])
def test_invalid_exception_contract_is_rejected_before_target_execution(invalid):
    calls = []
    with pytest.raises((TypeError, ValueError)):
        if invalid == "return-and-raise":
            post = WorldState(returns=None, raises=expectation())
        elif invalid == "regex":
            post = WorldState(raises=expectation(match="["))
        else:
            wrong_type = {"instance": ValueError(), "non-exception": int,
                          "base-exception": BaseException}[invalid]
            post = WorldState(raises=expectation(wrong_type))
        EBT(target=lambda: calls.append("executed"), post=post, reporter=None).run()
    assert calls == []


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_process_control_exceptions_are_never_an_expected_exception_match(arena, error_type):
    def interrupt():
        raise error_type("stop")

    case = EBT(target=interrupt, arena=arena,
               post=WorldState(raises=expectation(Exception)), reporter=None)
    with pytest.raises(error_type, match="stop"):
        case.run()
    assert case.run_trace is None
    if arena:
        assert arena.workspace_path is None


@pytest.mark.parametrize("stage", ["setup", "execute", "get_state", "teardown"])
def test_arena_infrastructure_errors_cannot_satisfy_exception_contract(stage):
    class BrokenArena:
        def setup(self, state):
            if stage == "setup":
                raise OSError("arena infrastructure")

        def execute(self, target, args, kwargs):
            if stage == "execute":
                raise OSError("arena infrastructure")
            return target(*args, **kwargs)

        def get_state(self):
            if stage == "get_state":
                raise OSError("arena infrastructure")
            return WorldState(returns=None)

        def teardown(self):
            if stage == "teardown":
                raise OSError("arena infrastructure")

    case = EBT(target=lambda: None, arena=BrokenArena(),
               post=WorldState(raises=expectation(OSError)), reporter=None)
    with pytest.raises(OSError, match="arena infrastructure"):
        case.run()
    assert case.run_trace is None
