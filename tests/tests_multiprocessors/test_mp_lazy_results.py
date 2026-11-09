"""EBT regressions for consuming mapper results within the managed lifecycle."""

import warnings

import pytest

from src.cubie.ebt import EBT
from src.cubie.protocols import WorldState


class LazyResultMapper:
    """Deterministic lazy mapper; errors occur on iteration, never in map()."""

    def __init__(self, fail_at=None):
        self.fail_at = fail_at
        self.active = False
        self.events = []
        self.exit_error = None

    def __enter__(self):
        self.active = True
        self.events.append("enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit_error = exc_val
        self.events.append("exit")
        self.active = False

    def map(self, fn, *iterables):
        self.events.append("map")
        return self._results(fn, iterables)

    def _results(self, fn, iterables):
        for index, args in enumerate(zip(*iterables)):
            if index == self.fail_at:
                raise RuntimeError("deferred mapper failure")
            result = fn(*args)
            self.events.append(("yield", index, self.active))
            yield result
        self.events.append(("exhausted", self.active))


class LazyResultProcessor:
    def __init__(self, priority=100, fail_at=None):
        self.priority = priority
        self.mapper = LazyResultMapper(fail_at)
        self.task_counts = []

    def check_condition(self, pre_states, post_states):
        return True

    def create_handler(self, n_tasks):
        self.task_counts.append(n_tasks)
        return self.mapper


def normalize(text):
    return text.strip().lower()


def make_engine(processors, values):
    engine = EBT(
        target=normalize,
        pre=[WorldState(args=(value,)) for value in values],
        post=WorldState(returns=str),
        multiprocessing=True,
        reporter=None,
    )
    # Replace the registry so installed backends cannot hide a regression.
    engine.MULTIPROCESSORS = processors
    return engine


def assert_complete_trace(run_trace, values):
    assert run_trace.evaluation is True
    assert [trace.pre.args for trace in run_trace.traces] == [
        (value,) for value in values
    ]
    assert [trace.outcome.returns for trace in run_trace.traces] == [
        normalize(value) for value in values
    ]
    assert all(trace.evaluation for trace in run_trace.traces)
    assert len({trace.step_id for trace in run_trace.traces}) == len(values)


@pytest.mark.parametrize("values", [[], [" A "], [" A ", " B ", " C "]],
                         ids=["empty", "single", "multiple"])
def test_ebt_consumes_lazy_results_before_mapper_exit(values):
    """Every result and iterator exhaustion belong to the mapper context."""
    processor = LazyResultProcessor()
    engine = make_engine([processor], values)

    run_trace = engine.run()

    assert_complete_trace(run_trace, values)
    assert processor.task_counts == [len(values)]
    assert processor.mapper.events == [
        "enter",
        "map",
        *[("yield", index, True) for index in range(len(values))],
        ("exhausted", True),
        "exit",
    ]
    assert processor.mapper.active is False
    assert processor.mapper.exit_error is None
    assert processor.priority == 100


@pytest.mark.parametrize("fail_at", [0, 1], ids=["first-result", "after-partial-result"])
def test_ebt_retries_with_fallback_after_lazy_result_failure(fail_at, recwarn):
    """Deferred errors trigger fallback; partial results do not leak or duplicate."""
    failed = LazyResultProcessor(priority=100, fail_at=fail_at)
    fallback = LazyResultProcessor(priority=10)
    values = [" A ", " B ", " C "]
    engine = make_engine([fallback, failed], values)

    run_trace = engine.run()

    assert_complete_trace(run_trace, values)
    assert failed.priority == 0
    assert fallback.priority == 10
    assert failed.task_counts == fallback.task_counts == [len(values)]
    assert isinstance(failed.mapper.exit_error, RuntimeError)
    assert str(failed.mapper.exit_error) == "deferred mapper failure"
    assert failed.mapper.active is fallback.mapper.active is False
    assert len(recwarn) == 1
    assert recwarn[0].category is UserWarning
    assert "STATE-GUARD: Execution failed" in str(recwarn[0].message)
    assert "deferred mapper failure" in str(recwarn[0].message)


@pytest.mark.parametrize("fail_at", [0, 1], ids=["first-result", "after-partial-result"])
def test_ebt_reports_state_guard_when_lazy_processors_are_exhausted(fail_at, recwarn):
    """An exhausted registry produces the manager's failure, not a raw iterator error."""
    # Both instances emit the same message from the same manager source line.
    warnings.simplefilter("always", UserWarning)
    processors = [
        LazyResultProcessor(priority=100, fail_at=fail_at),
        LazyResultProcessor(priority=10, fail_at=fail_at),
    ]
    engine = make_engine(processors, [" A ", " B "])

    with pytest.raises(RuntimeError, match="STATE-GUARD: All Processors failed"):
        engine.run()

    assert all(processor.priority == 0 for processor in processors)
    assert all(processor.task_counts == [2] for processor in processors)
    assert all(processor.mapper.active is False for processor in processors)
    assert all(isinstance(processor.mapper.exit_error, RuntimeError)
               for processor in processors)
    assert len(recwarn) == 2
    assert all(warning.category is UserWarning for warning in recwarn)
    assert all("deferred mapper failure" in str(warning.message) for warning in recwarn)
    assert engine.run_trace is None
