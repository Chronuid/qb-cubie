import os, pickle, warnings
from enum import Enum, auto
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Iterable, List, Any
from .protocols import Mapper, Multiprocessor
try:
    from loky import get_reusable_executor
    LOKY_AVAILABLE = True
except ImportError:  LOKY_AVAILABLE = False


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
    """
    The pickle-specific mapper - acts up with lambdas and locals but is otherwise pretty fast.
    """
    def __init__(self, n_tasks: int, *, max_workers: int | None = None):
        self.n_worker = _worker_count(n_tasks, max_workers)
        self.chunksize = max(1, n_tasks // (self.n_worker * 4))
        self.executor = ProcessPoolExecutor(max_workers=self.n_worker)
    def __enter__(self) -> 'PickleMapper':
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
    """
    The Loky-specific mapper - uses cloudpickle serialization for dynamic predicates (lambdas and locals).
    """
    def __init__(self, n_tasks: int, *, max_workers: int | None = None):
        self.n_worker = _worker_count(n_tasks, max_workers)
        self.chunksize = max(1, n_tasks // (self.n_worker * 4))
        self.executor = get_reusable_executor(
            max_workers=self.n_worker,
            context="loky",
            timeout=10
        )
    def __enter__(self) -> 'LokyMapper':
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
        if not LOKY_AVAILABLE: raise RuntimeError("LokyProcessor was called without the Loky module installed.")
        return LokyMapper(n_tasks, max_workers=max_workers)


# ========== STATE INSPECTOR ========================================================================================= #

class StateInspector:
    @staticmethod
    def has_unpicklable_callables(*containers) -> bool:
        try:
            pickle.dumps(containers)
            return False
        except (AttributeError, TypeError, pickle.PicklingError): return True


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
class MultiprocessManager:
    """
    Receives data of the EBT class, controls the resolver and runner, and provides the execution.
    """
    def __init__(
            self,
            pre_states: list,
            post_states: list,
            task_func: Callable,
            processors: List['Multiprocessor'],
            *,
            max_workers: int | None = None
    ):
        _validate_max_workers(max_workers)
        self._pre_states = pre_states
        self._post_states = post_states
        self._task_func = task_func
        self._processors = processors
        self._max_workers = max_workers
        self.dispatcher = {  #'δ'
            S.INITIAL: self._state_initial,
            S.RESOLVE: self._state_resolve,
            S.SETUP: self._state_setup,
            S.EXECUTE: self._state_execute
        }
        self.ctx = None

    # ------------------------------------------------------------------------------------------------------------------

    def execute(self) -> None | RuntimeError | Iterable[Any]:
        self.ctx = {"processor": None, "runner": None, "result": None, "error": None}
        dispatcher = self.dispatcher
        state = S.INITIAL
        while state not in (F.SUCCESS, F.FAIL): state = dispatcher[state]()
        if state == F.SUCCESS: return self.ctx["result"]
        if state == F.FAIL: raise RuntimeError("STATE-GUARD: All Processors failed") from self.ctx["error"]

    # ------------------------------------------------------------------------------------------------------------------

    def _state_initial(self) -> S:
        self.ctx.update({"processor": None, "runner": None, "result": None})
        return S.RESOLVE

    def _state_resolve(self) -> S | F:
        try:
            self.ctx["processor"] = self._resolve_handler()
            return S.SETUP
        except RuntimeError as e:
            self.ctx["error"] = e
            return F.FAIL

    def _state_setup(self) -> S:
        try:
            self.ctx["runner"] = self._setup_runner(self.ctx["processor"])
            return S.EXECUTE
        except Exception as e:
            self._degrade_and_warn(self.ctx["processor"], "STATE-GUARD: Setup failed", e)
            return S.INITIAL

    def _state_execute(self) -> S | F:
        try:
            runner = self.ctx["runner"]
            if runner:
                self.ctx["result"] = runner.execute()
                return F.SUCCESS
            self.ctx["error"] = RuntimeError("STATE-GUARD: Runner was None in EXECUTE state")
            return F.FAIL
        except Exception as e:
            self._degrade_and_warn(self.ctx["processor"], "STATE-GUARD: Execution failed", e)
            return S.INITIAL

    # ----- Helper -----

    def _resolve_handler(self):
        return MultiprocessResolver.resolve(
            self._pre_states,
            self._post_states,
            self._processors
        )

    def _setup_runner(self, processor):
        return MultiprocessRunner(
            handler=processor,
            pre_states=self._pre_states,
            task_func=self._task_func,
            max_workers=self._max_workers
        )

    def _degrade_and_warn(self, processor, phase: str, error: Exception):
        for p in self._processors:
            if p is processor:
                p.priority = 0
                break
        warnings.warn(
            f"STATE-GUARD: [{phase}] Multiprocessor '{processor.__class__.__name__}' has crashed. "
            f"Priority set to 0. Attempting fallback... \nError: {error}",
            category=UserWarning, stacklevel=2
        )


# ========== RESOLVER ================================================================================================ #

class MultiprocessResolver:
    """
    Manages the Chain of Responsibility and determines the responsible multiprocessor.
    """
    @classmethod
    def resolve(
            cls,
            pre_states: list,
            post_states: list,
            processors: List[Multiprocessor]
    ) -> Multiprocessor:
        sorted_processors = sorted(processors, key=lambda p: getattr(p, "priority", 0), reverse=True)
        for processor in sorted_processors:
            if getattr(processor, "priority", 0) > 0 and processor.check_condition(pre_states, post_states):
                return processor
        raise RuntimeError(
            "STATE-GUARD: MultiprocessResolver could not find a valid processor throughout 'resolve'. "
            "-> Are all processors really working as they should and are all priorities set correctly?"
        )

    @classmethod
    def _find_eligible_processor(
            cls,
            processors: List[Multiprocessor],
            pre_states: list,
            post_states: list
    ) -> Multiprocessor:
        """Iterates through the pipeline and triggers the evaluation of the hooks."""
        for processor in processors:
            if cls._is_processor_active(processor) and processor.check_condition(pre_states, post_states):
                return processor
        raise RuntimeError(
            "STATE-GUARD: MultiprocessResolver could not find a valid processor throughout '_find_eligable_processor'. "
            "-> Are all processors really working as they should and are all priorities set correctly?"
        )

    @staticmethod
    def _is_processor_active(processor: Multiprocessor) -> bool:
        """Checks whether the processor is actually activated by a priority > 0."""
        return getattr(processor, "priority", 0) > 0


# ========== RUNNER ================================================================================================== #

class MultiprocessRunner:
    """
    Encapsulates the physical execution. Leaves optimization heuristics to the respective processors.
    """
    def __init__(
            self,
            handler: Multiprocessor,
            pre_states: list,
            task_func: Callable,
            *,
            max_workers: int | None = None
    ):
        _validate_max_workers(max_workers)
        self._handler = handler
        self._pre_states = pre_states
        self._task_func = task_func
        self._max_workers = max_workers
        self._n_tasks = len(pre_states)
        self._indices = list(range(self._n_tasks))
    def execute(self) -> Iterable:
        # Preserve legacy custom factories when no explicit limit was requested.
        # With a limit, require backend support rather than silently ignoring it.
        options = {} if self._max_workers is None else {"max_workers": self._max_workers}
        with self._handler.create_handler(n_tasks=self._n_tasks, **options) as mapper:
            # Consume results here so deferred errors reach the manager's fallback.
            return list(mapper.map(
                self._task_func,
                self._indices,
                self._pre_states
            ))

########################################################################################################################
