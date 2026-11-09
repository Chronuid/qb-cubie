import typing
from typing import Any, Optional, Protocol, runtime_checkable, Dict, List, Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

# ========== REVIEWER-PROTOCOL | REVIEW-BASED-TESTING ==================================================================

@dataclass
class ReviewData:
    """
    Encapsulates the standardized result of an RBT test.
    """
    passed: bool
    report: Dict[str, Any] = field(default_factory=dict)

class Reviewer(Protocol):
    """
    Defines the contract for all injectable test instances.
    """
    def review(
            self,
            target: Optional[str],
            check: str
    ) -> ReviewData: ...


# ========== WORLDSTATE-DATACLASS | EXAMPLE-BASED-TESTING ==============================================================

@dataclass
class WorldState:
    """
    Declares execution environments, file system states, and functional parameters of a test world.
    """
    args: Optional[Any] = None
    kwargs: Optional[Any]  = None
    arena: Optional[Any]  = None
    fs: Optional[Any]  = None
    returns: Optional[Any]  = None
    expect: Optional[bool]  = True


# ========== ARENA-PROTOCOL | EXAMPLE-BASED-TESTING ====================================================================

@runtime_checkable
class Arena(Protocol):
    """
    Contract for isolated execution environments.
    """
    @property
    def workspace_path(self) -> Optional[Path]:
        """Returns the absolute path to the isolated working directory after setup."""
        ...
    def setup(self, state: WorldState) -> None:
        """Creates the temporary workspace and hydrates it based on the provided WorldState."""
        ...
    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Executes the target within the isolated workspace and returns the raw functional result."""
        ...
    def get_state(self) -> WorldState:
        """Packages and returns the mutated environment reality as a complete WorldState."""
        ...
    def teardown(self) -> None:
        """Destroys the workspace and cleans up all temporary environment states."""
        ...

# ========== TRACING-DATACLASSES | EXAMPLE-BASED-TESTING ===============================================================

@dataclass
class EvaluationTrace:
    """
    Encapsulates the complete trajectory and evaluation of a single execution step.
    """
    step_id: str
    target: str
    pre: WorldState
    post: WorldState
    outcome: WorldState
    evaluation: bool
    duration: Optional[float] = None
    diffs: Optional[dict] = None

@dataclass
class RunTrace:
    """
    Encapsulates the complete trajetories of all steps and the evaluation of the entire run.
    """
    run_id: str
    target: str
    expect: bool
    arena: Optional[Arena] = None
    traces: Optional[List[EvaluationTrace]] = None
    evaluation: Optional[bool] = None
    duration: Optional[float] = None


# ========== IPC-CODEC-PROTOCOL | PYVENV-ARENA =========================================================================

class IPCC(Protocol):
    """
    Defines the contract for Inter-Process Communication Codecs.
    """
    file_suffix: str
    requirements: list[str]
    def dump(self, obj: Any, path: str) -> None:
        """Serializes and writes the object to the specified path."""
        ...
    def load(self, path: str) -> Any:
        """Reads and deserializes the object from the specified path."""
        ...
    def get_runner_snippet(self, in_path: str, out_path: str) -> str:
        """Generates the matching Python execution snippet for the arena."""
        ...


# ========== REPORTER-PROTOCOL ========================================================================================

class Reporter[ResultT](Protocol):
    """
    Defines the contract for reporters consuming a test result.
    """
    def report(self, trace: ResultT, /) -> None:
        """Processes and outputs the final test result."""
        ...


# ========== MULTIRPOCESSOR-PROTOCOLS ==================================================================================


class Mapper(typing.ContextManager['Mapper'], Protocol):
    """
    The execution interface of the multiprocessor protocol, which also manages its own lifecycle.
    """
    def map(self, fn: Callable, *iterables: Iterable) -> Iterable[Any]: ...


class Multiprocessor(Protocol):
    """
    The DI protocol for the multiprocessor registration.
    """
    priority: int

    def check_condition(self, pre_states: list, post_states: list) -> bool:
        """The hook-case under review. Evaluates whether this processor is responsible."""
        ...

    def create_handler(self, n_tasks: int) -> Mapper:
        """Returns the mapper instance as interface- and execution-layer (which is itself a context manager)."""
        ...

# ========== VM-ARENA-PROTOCOLS ========================================================================================

@dataclass
class DeviceResources:
    ram_mb: Optional[int] = None
    cpu_cores: Optional[float] = None
    # Extensible in the future to include I/O limits, GPU allocations, etc.
