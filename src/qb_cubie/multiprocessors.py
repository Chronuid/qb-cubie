import os
import pickle
import warnings
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from enum import Enum, auto
from functools import partial
from typing import Any, Callable, Iterable, List, Never, TypedDict

import cloudpickle  # type: ignore[import-untyped]

from .protocols import Mapper, Multiprocessor

try:
    from loky import get_reusable_executor  # type: ignore[import-untyped]

    LOKY_AVAILABLE = True
except ImportError:
    LOKY_AVAILABLE = False


class _TaskFailure(Exception):
    """Transport a task exception separately from executor/serialization errors."""

    # Transport the original exception as bytes so a failing exception reducer or
    # constructor cannot break the pool and accidentally initiate task replay.
    # Executors retain the remote traceback as this wrapper's cause.

    def __reduce__(self):
        error = self.args[0]
        try:
            payload = cloudpickle.dumps(error)
        except Exception:  # noqa: BLE001 -- arbitrary exception reducers must not cause infrastructure replay
            payload = None
        try:
            message = str(error)
        except Exception:  # noqa: BLE001 -- a broken __str__ must not hide task origin
            message = "<exception message unavailable>"
        return _restore_task_failure, (payload, type(error).__qualname__, message)


def _restore_task_failure(payload, error_type, message):
    try:
        if payload is None:
            raise TypeError("exception serialization failed")
        error = cloudpickle.loads(payload)
        if not isinstance(error, Exception):
            raise TypeError("exception reconstruction did not return an Exception")
    except Exception:  # noqa: BLE001 -- a broken constructor must not turn a task error into pool loss
        error = RuntimeError(f"Task raised {error_type}: {message}. The original exception could not be transported.")
    return _TaskFailure(error)


def _call_task(task_func, *args):
    try:
        return task_func(*args)
    except Exception as error:
        raise _TaskFailure(error) from error


class _BackendFailure(Exception):
    def __init__(self, error, phase):
        super().__init__(error)
        self.error = error
        self.phase = phase


class _NoEligibleProcessor(RuntimeError):
    """Resolver exhaustion, distinct from errors raised by eligibility hooks."""


def _validate_max_workers(max_workers: int | None) -> None:
    if max_workers is None:
        return
    if isinstance(max_workers, bool) or not isinstance(max_workers, int):
        raise TypeError("max_workers must be a positive integer or None")
    if max_workers < 1:
        raise ValueError("max_workers must be a positive integer or None")


def _worker_count(n_tasks: int, max_workers: int | None) -> int:
    _validate_max_workers(max_workers)
    if n_tasks < 1:
        raise ValueError("n_tasks must be positive before creating a process pool")
    workers = min(os.cpu_count() or 1, n_tasks)
    return min(workers, max_workers) if max_workers is not None else workers


########################################################################################################################
####### =======================  MULTIPROCESSOR (PROTOCOL) - IMPLEMENTATIONS  ================================== #######
########## -------------------------------------------------------------------------------------------------- ##########


# ========== PICKLE PROCESSOR ======================================================================================== #


class PickleMapper:
    """The pickle-specific mapper - acts up with lambdas and locals but is otherwise pretty fast."""

    def __init__(self, n_tasks: int, *, max_workers: int | None = None):
        self.n_worker = _worker_count(n_tasks, max_workers)
        self.chunksize = max(1, n_tasks // (self.n_worker * 4))
        self.executor = ProcessPoolExecutor(max_workers=self.n_worker)

    def __enter__(self) -> "PickleMapper":
        self.executor.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.executor.__exit__(exc_type, exc_val, exc_tb)

    def map(self, fn: Callable, *iterables: Iterable) -> Iterable[Any]:
        return self.executor.map(fn, *iterables, chunksize=self.chunksize)


# ------------------ Multiprocessor(Protocol) ------------------------------------------------------------------------ #


class PickleProcessor:
    priority = 1

    @staticmethod
    def check_condition(pre_states: list, post_states: list) -> bool:
        return not StateInspector.has_unpicklable_callables(pre_states, post_states)

    @staticmethod
    def create_handler(n_tasks: int, *, max_workers: int | None = None) -> Mapper:
        return PickleMapper(n_tasks, max_workers=max_workers)


# ========== LOKY PROCESSOR ========================================================================================== #


class LokyMapper:
    """The Loky-specific mapper - uses cloudpickle serialization for dynamic predicates (lambdas and locals)."""

    def __init__(self, n_tasks: int, *, max_workers: int | None = None):
        self.n_worker = _worker_count(n_tasks, max_workers)
        self.chunksize = max(1, n_tasks // (self.n_worker * 4))
        self.executor = get_reusable_executor(max_workers=self.n_worker, context="loky", timeout=10)

    def __enter__(self) -> "LokyMapper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.executor.shutdown(wait=True)

    def map(self, fn: Callable, *iterables: Iterable) -> Iterable[Any]:
        return self.executor.map(fn, *iterables, chunksize=self.chunksize)


# ------------------ Multiprocessor(Protocol) ------------------------------------------------------------------------ #


class LokyProcessor:
    priority = 1

    @staticmethod
    def check_condition(pre_states: list, post_states: list) -> bool:
        needs_loky = StateInspector.has_unpicklable_callables(pre_states, post_states)
        if needs_loky and not LOKY_AVAILABLE:
            warnings.warn(
                "Loky is not installed, but lambdas/closures were found in the test states. "
                "Native multiprocessing might fail. "
            )
            return False
        return needs_loky and LOKY_AVAILABLE

    @staticmethod
    def create_handler(n_tasks: int, *, max_workers: int | None = None) -> LokyMapper:
        if not LOKY_AVAILABLE:
            raise RuntimeError("LokyProcessor was called without the Loky module installed.")
        return LokyMapper(n_tasks, max_workers=max_workers)


# ========== STATE INSPECTOR ========================================================================================= #


class StateInspector:
    @staticmethod
    def has_unpicklable_callables(*containers) -> bool:
        try:
            pickle.dumps(containers)
            return False
        except (AttributeError, TypeError, pickle.PicklingError):
            return True


########################################################################################################################


########################################################################################################################
####### =======================  M U L T I P R O C E S S  ====================================================== #######
########## -------------------------------------------------------------------------------------------------- ##########


class S(Enum):
    INITIAL = auto()
    RESOLVE = auto()
    SETUP = auto()
    EXECUTE = auto()


class F(Enum):
    SUCCESS = auto()
    FAIL = auto()


class _ManagerContext(TypedDict):
    processor: Multiprocessor | None
    runner: "MultiprocessRunner | None"
    result: Iterable[Any] | None
    error: Exception | None


class MultiprocessManager:
    """Receives data of the EBT class, controls the resolver and runner, and provides the execution."""

    def __init__(
        self,
        pre_states: list,
        post_states: list,
        task_func: Callable,
        processors: List["Multiprocessor"],
        *,
        max_workers: int | None = None,
    ):
        _validate_max_workers(max_workers)
        self._pre_states = pre_states
        self._post_states = post_states
        self._task_func = task_func
        self._processors = processors
        self._max_workers = max_workers
        self._configure_states()
        self.ctx: _ManagerContext | None = None


    # ------------------------------------------------------------------------------------------------------------------

    def execute(self) -> None | Iterable[Any]:
        self.ctx = {"processor": None, "runner": None, "result": None, "error": None}
        state: S | F = S.INITIAL
        while isinstance(state, S):
            state = self.dispatcher[state]()
        ctx = self._context()
        if state is F.FAIL:
            raise RuntimeError("STATE-GUARD: All Processors failed") from ctx["error"]
        return ctx["result"]

    # ------------------------------------------------------------------------------------------------------------------

    def _configure_states(self) -> None:
        self.dispatcher: dict[S, Callable[[], S | F]] = {  #'δ'
            S.INITIAL: self._state_initial,
            S.RESOLVE: self._state_resolve,
            S.SETUP: self._state_setup,
            S.EXECUTE: self._state_execute,
        }

    def _state_initial(self) -> S:
        ctx = self._context()
        ctx.update({"processor": None, "runner": None, "result": None})
        return S.RESOLVE

    def _state_resolve(self) -> S | F:
        ctx = self._context()
        try:
            ctx["processor"] = self._resolve_handler()
            return S.SETUP
        except _NoEligibleProcessor as e:
            # Keep the last actual infrastructure failure when fallback exhausts.
            if ctx["error"] is None:
                ctx["error"] = e
            return F.FAIL

    def _state_setup(self) -> S:
        ctx = self._context()
        processor = ctx["processor"]
        if processor is None:
            raise RuntimeError("STATE-GUARD: No processor selected for SETUP state.")
        ctx["runner"] = self._setup_runner(processor)
        return S.EXECUTE

    def _state_execute(self) -> S | F:
        ctx = self._context()
        try:
            runner = ctx["runner"]
            if runner is None:
                ctx["error"] = RuntimeError("STATE-GUARD: Runner was None in EXECUTE state")
                return F.FAIL
            ctx["result"] = runner.execute()
            return F.SUCCESS
        except _BackendFailure as failure:
            return self._fallback(failure)

    def _fallback(self, failure: _BackendFailure) -> S:
        ctx = self._context()
        ctx["error"] = failure.error
        self._degrade_and_warn(ctx["processor"], failure.phase, failure.error)
        return S.INITIAL

    def _context(self) -> _ManagerContext:
        if self.ctx is None:
            raise RuntimeError("STATE-GUARD: Multiprocess context was not initialized.")
        return self.ctx

    # ----- Helper -----

    def _resolve_handler(self) -> Multiprocessor:
        return MultiprocessResolver.resolve(self._pre_states, self._post_states, self._processors)

    def _setup_runner(self, processor: Multiprocessor) -> "MultiprocessRunner":
        return MultiprocessRunner(
            handler=processor, pre_states=self._pre_states, task_func=self._task_func, max_workers=self._max_workers
        )

    def _degrade_and_warn(self, processor, phase: str, error: Exception):
        for p in self._processors:
            if p is processor:
                p.priority = 0
                break
        warnings.warn(
            f"STATE-GUARD: [{phase}] Multiprocessor '{processor.__class__.__name__}' has crashed. "
            "Priority set to 0. Attempting fallback: all tasks will be replayed if another "
            "eligible backend is available. Tasks may already have run; duplicate side effects "
            f"are possible and are not rolled back.\nError: {error}",
            category=UserWarning,
            stacklevel=2,
        )


# ========== RESOLVER ================================================================================================ #


class MultiprocessResolver:
    """Manages the Chain of Responsibility and determines the responsible multiprocessor."""

    @classmethod
    def resolve(cls, pre_states: list, post_states: list, processors: List[Multiprocessor]) -> Multiprocessor:
        sorted_processors = sorted(processors, key=lambda p: getattr(p, "priority", 0), reverse=True)
        for processor in sorted_processors:
            if getattr(processor, "priority", 0) > 0 and processor.check_condition(pre_states, post_states):
                return processor
        raise _NoEligibleProcessor(
            "STATE-GUARD: MultiprocessResolver could not find a valid processor throughout 'resolve'. "
            "-> Are all processors really working as they should and are all priorities set correctly?"
        )

    @classmethod
    def _find_eligible_processor(
        cls, processors: List[Multiprocessor], pre_states: list, post_states: list
    ) -> Multiprocessor:
        """Iterates through the pipeline and triggers the evaluation of the hooks."""
        for processor in processors:
            if cls._is_processor_active(processor) and processor.check_condition(pre_states, post_states):
                return processor
        raise _NoEligibleProcessor(
            "STATE-GUARD: MultiprocessResolver could not find a valid processor throughout '_find_eligable_processor'. "
            "-> Are all processors really working as they should and are all priorities set correctly?"
        )

    @staticmethod
    def _is_processor_active(processor: Multiprocessor) -> bool:
        """Checks whether the processor is actually activated by a priority > 0."""
        return getattr(processor, "priority", 0) > 0


# ========== RUNNER ================================================================================================== #


class MultiprocessRunner:
    """Manage mapper execution, error classification, and cleanup."""

    def __init__(
        self, handler: Multiprocessor, pre_states: list, task_func: Callable, *, max_workers: int | None = None
    ):
        _validate_max_workers(max_workers)
        self._handler = handler
        self._pre_states = pre_states
        self._task_func = task_func
        self._max_workers = max_workers
        self._n_tasks = len(pre_states)
        self._indices = list(range(self._n_tasks))

    def execute(self) -> Iterable:
        """Execute all tasks within the mapper lifecycle."""
        context, mapper = self._open()
        return self._run(context, mapper)

    def _open(self) -> tuple[Mapper, Mapper]:
        """Create and enter the configured mapper context."""
        # Preserve legacy custom factories when no explicit limit was requested.
        options = {} if self._max_workers is None else {"max_workers": self._max_workers}
        try:
            context = self._handler.create_handler(n_tasks=self._n_tasks, **options)
            return context, context.__enter__()
        except (OSError, BrokenProcessPool) as error:
            raise _BackendFailure(error, "STATE-GUARD: Setup failed") from error

    def _run(self, context: Mapper, mapper: Mapper) -> Iterable:
        """Collect results and close the mapper on success or failure."""
        try:
            results = self._collect(mapper)
        except BaseException as error:  # noqa: BLE001 -- all mapping failures must pass through cleanup
            failure = error
        else:
            context.__exit__(None, None, None)
            return results
        # Handle failures outside except to avoid task-wrapper context cycles.
        self._abort(context, failure)

    def _collect(self, mapper: Mapper) -> list:
        """Consume all task results from the active mapper."""
        return list(
            mapper.map(
                partial(_call_task, self._task_func),
                self._indices,
                self._pre_states,
            )
        )

    def _abort(self, context: Mapper, failure: BaseException) -> Never:
        """Close the failed mapper and propagate the classified error."""
        original = self._unwrap(failure)
        self._cleanup(context, original)
        if not isinstance(failure, _TaskFailure) and isinstance(failure, (BrokenProcessPool, pickle.PicklingError)):
            raise _BackendFailure(failure, "STATE-GUARD: Execution failed") from failure
        raise original

    @staticmethod
    def _unwrap(failure: BaseException) -> BaseException:
        """Recover the original task exception and its remote cause."""
        if not isinstance(failure, _TaskFailure):
            return failure
        original = failure.args[0]
        if failure.__cause__ is not None and failure.__cause__ is not original:
            original.__cause__ = failure.__cause__
        return original.with_traceback(original.__traceback__ or failure.__traceback__)

    @staticmethod
    def _cleanup(context: Mapper, error: BaseException) -> None:
        """Close the mapper while preserving the primary exception."""
        try:
            context.__exit__(type(error), error, error.__traceback__)
        except BaseException as cleanup_error:  # noqa: BLE001 -- preserve the primary error even during cancellation
            error.add_note(f"Multiprocessor cleanup also failed: {cleanup_error!r}")
            raise error


########################################################################################################################
