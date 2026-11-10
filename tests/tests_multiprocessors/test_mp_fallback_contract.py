"""Desired EBT contracts for GUTACHTEN.md, section 8, priority 3.3.

No xfail: failures expose violations of the fallback contract. Deterministic
mappers distinguish lifecycle faults from task faults; real pools additionally
exercise exception transport and persistent side effects across processes.
See docs/dev/DEV-GUIDE_2-4_Multiprocessors.md for the retry semantics.
"""

import errno
import os
import pickle
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import pytest

from qb_cubie import EBT, WorldState
from qb_cubie.multiprocessors import LokyProcessor, PickleProcessor


class ContractMapper:
    def __init__(self, processor):
        self.processor = processor
        self.exited = False
        self.exit_error = None

    def __enter__(self):
        self.processor.events.append("enter")
        self.processor.fail_if("enter")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        self.exit_error = exc_val
        self.processor.events.append("exit")
        self.processor.fail_if("exit")

    def map(self, fn, *iterables):
        self.processor.events.append("map")
        self.processor.fail_if("map")
        return self.results(fn, iterables)

    def results(self, fn, iterables):
        for index, args in enumerate(zip(*iterables)):
            # A failure here belongs to the backend, outside the task callable.
            if index == self.processor.fail_at:
                raise self.processor.error
            self.processor.task_indices.append(index)
            yield fn(*args)


class ContractProcessor:
    def __init__(self, priority, *, phase=None, error=None, fail_at=None):
        self.priority = priority
        self.phase = phase
        self.error = error
        self.fail_at = fail_at
        self.requests = []
        self.events = []
        self.task_indices = []
        self.mapper = ContractMapper(self)

    def check_condition(self, pre_states, post_states):
        return True

    def create_handler(self, n_tasks, *, max_workers=None):
        self.requests.append((n_tasks, max_workers))
        self.fail_if("create")
        return self.mapper

    def fail_if(self, phase):
        if self.phase == phase:
            raise self.error


def make_case(target, processors, values=(0, 1, 2), *, reporter=None):
    case = EBT(
        target=target,
        pre=[WorldState(args=(value,)) for value in values],
        post=WorldState(returns=int),
        multiprocessing=True,
        max_workers=1,
        reporter=reporter,
    )
    case.MULTIPROCESSORS = processors
    return case


def assert_no_fallback(case, preferred, fallback, recwarn):
    assert preferred.priority == 100
    assert fallback.priority == 10
    assert fallback.requests == []
    assert len(recwarn) == 0
    assert case.run_trace is None


@pytest.mark.parametrize("error_type", [
    ValueError, RuntimeError, TypeError, OSError, pickle.PicklingError,
    BrokenProcessPool,
])
def test_task_exception_is_propagated_without_replay(error_type, recwarn):
    """Origin matters even when the task raises an infrastructure-like type."""
    error = error_type("deliberate task failure")
    calls = []

    def target(value):
        calls.append(value)
        if value == 1:
            raise error
        return value

    preferred = ContractProcessor(100)
    fallback = ContractProcessor(10)
    case = make_case(target, [preferred, fallback])

    with pytest.raises(error_type, match="deliberate task failure") as caught:
        case.run()

    assert caught.value is error
    assert calls == [0, 1]
    assert_no_fallback(case, preferred, fallback, recwarn)
    assert preferred.mapper.exited
    assert preferred.mapper.exit_error is error


@pytest.mark.parametrize("phase", ["create", "enter", "map"])
@pytest.mark.parametrize("error_type", [ValueError, TypeError, RuntimeError])
def test_backend_programming_error_is_not_a_retry_signal(phase, error_type, recwarn):
    error = error_type("invalid backend configuration")
    preferred = ContractProcessor(100, phase=phase, error=error)
    fallback = ContractProcessor(10)
    calls = []
    case = make_case(lambda value: calls.append(value) or value,
                     [preferred, fallback])

    with pytest.raises(error_type, match="invalid backend configuration") as caught:
        case.run()

    assert caught.value is error
    assert calls == []
    assert_no_fallback(case, preferred, fallback, recwarn)


@pytest.mark.parametrize("phase,error", [
    ("create", OSError(errno.EMFILE, "pool resource unavailable")),
    ("enter", OSError(errno.EMFILE, "pool resource unavailable")),
    ("map", pickle.PicklingError("task serialization unavailable")),
], ids=["pool-creation", "pool-entry", "input-serialization"])
def test_infrastructure_failure_before_dispatch_allows_fallback(phase, error, recwarn):
    preferred = ContractProcessor(100, phase=phase, error=error)
    fallback = ContractProcessor(10)
    calls = []
    case = make_case(lambda value: calls.append(value) or value,
                     [preferred, fallback])

    result = case.run()

    assert result.evaluation is True
    assert calls == [0, 1, 2]
    assert preferred.task_indices == []
    assert preferred.requests == fallback.requests == [(3, 1)]
    assert preferred.priority == 0
    assert fallback.priority == 10
    assert fallback.mapper.exited
    assert len(recwarn) == 1
    assert str(error) in str(recwarn[0].message)


@pytest.mark.parametrize("fail_at", [0, 1], ids=["before-first-result", "partial-result"])
def test_broken_pool_replays_batch_and_warns_about_duplicate_effects(fail_at, recwarn):
    """Discarding partial results does not undo already executed side effects."""
    preferred = ContractProcessor(
        100, fail_at=fail_at, error=BrokenProcessPool("worker disappeared"),
    )
    fallback = ContractProcessor(10)
    calls = []
    case = make_case(lambda value: calls.append(value) or value,
                     [preferred, fallback])

    result = case.run()

    assert result.evaluation is True
    assert calls == list(range(fail_at)) + [0, 1, 2]
    assert [trace.outcome.returns for trace in result.traces] == [0, 1, 2]
    assert len({trace.step_id for trace in result.traces}) == 3
    assert preferred.requests == fallback.requests == [(3, 1)]
    assert preferred.priority == 0
    assert preferred.mapper.exited and fallback.mapper.exited
    assert len(recwarn) == 1
    message = str(recwarn[0].message).lower()
    assert "worker disappeared" in message
    # Semantic wording only: avoid freezing the complete diagnostic string.
    assert "all" in message and "task" in message
    assert "repeat" in message or "replay" in message or "rerun" in message
    assert "side effect" in message and ("duplicate" in message or "repeat" in message)


def test_cleanup_error_after_completed_tasks_does_not_replay_batch(recwarn):
    error = OSError(errno.EIO, "pool cleanup failed")
    preferred = ContractProcessor(100, phase="exit", error=error)
    fallback = ContractProcessor(10)
    calls = []
    case = make_case(lambda value: calls.append(value) or value,
                     [preferred, fallback])

    with pytest.raises(OSError, match="pool cleanup failed") as caught:
        case.run()

    assert caught.value is error
    assert calls == [0, 1, 2]
    assert preferred.mapper.exited
    assert_no_fallback(case, preferred, fallback, recwarn)


def test_unclassified_oserror_during_mapping_does_not_trigger_fallback(recwarn):
    error = OSError(errno.EIO, "unknown mapping failure")
    preferred = ContractProcessor(100, phase="map", error=error)
    fallback = ContractProcessor(10)
    case = make_case(lambda value: value, [preferred, fallback])

    with pytest.raises(OSError, match="unknown mapping failure") as caught:
        case.run()

    assert caught.value is error
    assert preferred.mapper.exited
    assert_no_fallback(case, preferred, fallback, recwarn)


def test_eligibility_hook_error_is_not_reported_as_registry_exhaustion(recwarn, monkeypatch):
    error = RuntimeError("invalid eligibility hook")
    preferred = ContractProcessor(100)
    fallback = ContractProcessor(10)

    def fail_check(pre, post):
        raise error

    monkeypatch.setattr(preferred, "check_condition", fail_check)
    case = make_case(lambda value: value, [preferred, fallback])
    with pytest.raises(RuntimeError, match="invalid eligibility hook") as caught:
        case.run()

    assert caught.value is error
    assert preferred.requests == []
    assert_no_fallback(case, preferred, fallback, recwarn)


@pytest.mark.parametrize("origin", ["task", "backend"])
def test_cleanup_failure_preserves_primary_error_and_prevents_replay(origin, recwarn):
    primary = BrokenProcessPool("primary failure")
    preferred = ContractProcessor(
        100, phase="exit", error=OSError(errno.EIO, "cleanup failure"),
    )
    if origin == "backend":
        preferred.fail_at = 0
        # Keep a separate error for the iterator and for __exit__.
        def fail_map(fn, *iterables):
            raise primary
        preferred.mapper.map = fail_map
    fallback = ContractProcessor(10)

    def target(value):
        raise primary

    case = make_case(target, [preferred, fallback])
    with pytest.raises(BrokenProcessPool, match="primary failure") as caught:
        case.run()

    assert caught.value is primary
    assert any("cleanup failure" in note for note in primary.__notes__)
    assert preferred.mapper.exited
    assert_no_fallback(case, preferred, fallback, recwarn)


def test_result_mismatch_is_reported_without_backend_fallback(recwarn):
    preferred = ContractProcessor(100)
    fallback = ContractProcessor(10)
    case = make_case(lambda value: "wrong", [preferred, fallback])

    result = case.run()

    assert result.evaluation is False
    assert len(result.traces) == 3
    assert preferred.priority == 100
    assert fallback.requests == []
    assert preferred.mapper.exited
    assert len(recwarn) == 0


def test_exhausted_infrastructure_fallback_keeps_actual_failure_as_cause(recwarn):
    first_error = OSError(errno.EMFILE, "pool resource unavailable")
    last_error = BrokenProcessPool("last worker disappeared")
    preferred = ContractProcessor(100, phase="create", error=first_error)
    fallback = ContractProcessor(10, fail_at=0, error=last_error)
    case = make_case(lambda value: value, [preferred, fallback])

    with pytest.raises(RuntimeError, match="All Processors failed") as caught:
        case.run()

    assert caught.value.__cause__ is last_error
    assert preferred.requests == fallback.requests == [(3, 1)]
    assert preferred.priority == fallback.priority == 0
    assert fallback.mapper.exited
    assert case.run_trace is None
    assert len(recwarn) == 2


def fail_once_after_persistent_effect(log_path, error_name):
    """Importable target: a retry succeeds and would hide the original error."""
    path = Path(log_path)
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    with path.open("a", encoding="utf-8") as log:
        log.write("effect\n")
    if not previous:
        error_type = {
            "ValueError": ValueError,
            "OSError": OSError,
            "PicklingError": pickle.PicklingError,
            "BrokenProcessPool": BrokenProcessPool,
        }[error_name]
        raise error_type("persistent task failure")
    return 1


@pytest.mark.parametrize("processor_type", [PickleProcessor, LokyProcessor],
                         ids=["pickle", "loky"])
@pytest.mark.parametrize("error_type", [
    ValueError, OSError, pickle.PicklingError, BrokenProcessPool,
])
def test_real_worker_error_cannot_be_hidden_by_successful_retry(
    processor_type, error_type, tmp_path, recwarn, monkeypatch,
):
    preferred = processor_type()
    preferred.priority = 100
    # Force the selected real backend: these picklable states would otherwise
    # make Loky's normal eligibility check skip it entirely.
    monkeypatch.setattr(preferred, "check_condition", lambda pre, post: True)
    fallback = ContractProcessor(10)
    log = tmp_path / "effects.txt"
    case = EBT(
        target=fail_once_after_persistent_effect,
        pre=WorldState(args=(str(log), error_type.__name__)),
        post=WorldState(returns=1),
        multiprocessing=True,
        max_workers=1,
        reporter=None,
    )
    case.MULTIPROCESSORS = [preferred, fallback]

    with pytest.raises(error_type, match="persistent task failure"):
        case.run()

    assert log.read_text(encoding="utf-8") == "effect\n"
    assert_no_fallback(case, preferred, fallback, recwarn)


def terminate_worker_once(log_path):
    path = Path(log_path)
    previous = path.exists()
    with path.open("a", encoding="utf-8") as log:
        log.write("effect\n")
    if not previous:
        os._exit(7)
    return 1


class UntransportableError(Exception):
    def __init__(self, message, *, detail):
        super().__init__(message)
        self.detail = detail


class UnserializableError(UntransportableError):
    def __reduce__(self):
        raise TypeError("exception cannot be serialized")


def raise_untransportable_error(log_path, error_type):
    with Path(log_path).open("a", encoding="utf-8") as log:
        log.write("effect\n")
    raise error_type("custom task failure", detail="required constructor argument")


@pytest.mark.parametrize("processor_type", [PickleProcessor, LokyProcessor], ids=["pickle", "loky"])
@pytest.mark.parametrize("error_type", [UntransportableError, UnserializableError])
def test_untransportable_task_error_does_not_turn_into_pool_fallback(
    processor_type, error_type, tmp_path, monkeypatch, recwarn,
):
    preferred = processor_type()
    preferred.priority = 100
    monkeypatch.setattr(preferred, "check_condition", lambda pre, post: True)
    fallback = ContractProcessor(10)
    log = tmp_path / "custom-error.txt"
    case = EBT(
        target=raise_untransportable_error,
        pre=WorldState(args=(str(log), error_type)),
        multiprocessing=True,
        max_workers=1,
        reporter=None,
    )
    case.MULTIPROCESSORS = [preferred, fallback]

    with pytest.raises(RuntimeError, match=f"Task raised {error_type.__name__}: custom task failure"):
        case.run()

    assert log.read_text(encoding="utf-8") == "effect\n"
    assert_no_fallback(case, preferred, fallback, recwarn)


@pytest.mark.parametrize("processor_type", [PickleProcessor, LokyProcessor],
                         ids=["pickle", "loky"])
def test_actual_worker_loss_allows_documented_replay(processor_type, tmp_path, monkeypatch, recwarn):
    preferred = processor_type()
    preferred.priority = 100
    monkeypatch.setattr(preferred, "check_condition", lambda pre, post: True)
    fallback = ContractProcessor(10)
    log = tmp_path / "worker-loss.txt"
    case = EBT(
        target=terminate_worker_once,
        pre=WorldState(args=(str(log),)),
        post=WorldState(returns=1),
        multiprocessing=True,
        max_workers=1,
        reporter=None,
    )
    case.MULTIPROCESSORS = [preferred, fallback]

    result = case.run()

    assert result.evaluation is True
    assert len(result.traces) == 1
    assert log.read_text(encoding="utf-8") == "effect\neffect\n"
    assert preferred.priority == 0
    assert fallback.requests == [(1, 1)]
    assert fallback.mapper.exited
    fallback_warnings = [warning for warning in recwarn if "Attempting fallback" in str(warning.message)]
    assert len(fallback_warnings) == 1
    assert "all tasks will be replayed" in str(fallback_warnings[0].message)
    assert "duplicate side effects" in str(fallback_warnings[0].message)
