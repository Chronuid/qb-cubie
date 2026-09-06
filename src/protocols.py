from typing import Any, Optional, Protocol, runtime_checkable, Dict, List
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
    args: Any = None
    kwargs: Any = None
    arena: Any = None
    fs: Any = None
    returns: Any = None
    expect: bool = True or False


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
    """Encapsulates the complete trajectory and evaluation of a single execution step."""
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
    """Encapsulates the complete trajetories of all steps and the evaluation of the entire run."""
    run_id: str
    target: str
    expect: bool
    arena: Optional[Arena] = None
    traces: Optional[List[EvaluationTrace]] = None
    evaluation: Optional[bool] = None
    duration: Optional[float] = None


# ========== IPC-CODEC-PROTOCOL | PYVENV-ARENA =========================================================================

class IPCC(Protocol):
    file_suffix: str
    requirements: list[str]

    def dump(self, obj: Any, path: str) -> None:
        """Writes the object to the specified path."""
        ...
    def load(self, path: str) -> Any:
        """Reads the object from the path."""
        ...
    def get_runner_snippet(self, in_path: str, out_path: str) -> str:
        """Generates the Python code for the arena, matching the codec."""
        ...

# ========== REPORTER-PROTOCOL | EXAMPLE-BASED-TESTING =================================================================

class Reporter(Protocol):
    """
    Protocol for EBT result reporters.
    """
    def report(self, trace: RunTrace) -> None: ...