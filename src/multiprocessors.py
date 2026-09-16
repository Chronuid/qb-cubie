import os
import pickle
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Iterable, List, Any
from protocols import Mapper, Multiprocessor
from loky import get_reusable_executor


########################################################################################################################
####### =======================  MULTIPROCESSOR (PROTOCOL) - IMPLEMENTATIONS  ================================== #######
########## -------------------------------------------------------------------------------------------------- ##########


# ========== PICKLE PROCESSOR ======================================================================================== #

class PickleMapper:
    """
    The pickle-specific mapper that acts up with lambdas and locals but is otherwise pretty fast.
    """
    def __init__(self, n_tasks: int):
        self.n_worker = os.cpu_count() or 1
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
    def create_handler(n_tasks: int) -> Mapper:
        return PickleMapper(n_tasks)


# ========== LOKY PROCESSOR ========================================================================================== #

class LokyMapper:
    """
    The Loky-specific mapper, which uses cloudpickle serialization for dynamic predicates (lambdas and locals).
    """
    def __init__(self, n_tasks: int):
        self.n_worker = os.cpu_count() or 1
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
        return StateInspector.has_unpicklable_callables(pre_states, post_states)

    @staticmethod
    def create_handler(n_tasks: int) -> LokyMapper:
        return LokyMapper(n_tasks)


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


# ========== MANAGER ================================================================================================= #

class MultiprocessManager:
    """
    The facade: Receives all data of the EBT class, controls the resolver and runner, and provides the execution.
    """
    def __init__(
            self,
            pre_states: list,
            post_states: list,
            task_func: Callable,
            processors: List[Multiprocessor]
    ):
        self._pre_states = pre_states
        self._post_states = post_states
        self._task_func = task_func
        self._processors = processors
        self.processor = self._resolve_handler()
        self.runner = self._setup_runner()

    def execute(self) -> Iterable: return self.runner.execute()


    def _resolve_handler(self):
        return MultiprocessResolver.resolve(
            self._pre_states,
            self._post_states,
            self._processors
        )

    def _setup_runner(self):
        return MultiprocessRunner(
            handler=self.processor,
            pre_states=self._pre_states,
            task_func=self._task_func
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
            "STATE-GUARD: MultiprocessResolver could not find a valid processor throughout the 'resolve'. "
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
            "STATE-GUARD: MultiprocessResolver could not find a valid processor during '_find_eligable_processor'. "
            "-> Are all processors really working as they should and are all priorities set correctly?"
        )

    @staticmethod
    def _is_processor_active(processor: Multiprocessor) -> bool:
        """Checks whether the processor is actually activated by a priority > 0."""
        return getattr(processor, "priority", 0) > 0


# ========== RUNNER ================================================================================================== #

class MultiprocessRunner:
    """
    Encapsulates the physical execution. Leaves heuristics to the respective handler.
    """
    def __init__(
            self,
            handler: Multiprocessor,
            pre_states: list,
            task_func: Callable
    ):
        self._handler = handler
        self._pre_states = pre_states
        self._task_func = task_func
        self._n_tasks = len(pre_states)
        self._indices = list(range(self._n_tasks))

    def execute(self) -> Iterable:
        with self._handler.create_handler(n_tasks=self._n_tasks) as mapper:
            return mapper.map(
                self._task_func,
                self._indices,
                self._pre_states
            )


########################################################################################################################