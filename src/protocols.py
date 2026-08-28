from typing import Any, Optional, Protocol, runtime_checkable, Dict
from dataclasses import dataclass, field
from pathlib import Path

# ========== REVIEWER-PROTOCOL | REVIEW-BASED-TESTING ==================================================================

@dataclass
class ReviewData:
    """Encapsulates the standardized result of an RBT test."""
    passed: bool
    report: Dict[str, Any] = field(default_factory=dict)

class Reviewer(Protocol):
    """Defines the contract for all injectable test instances."""
    def review(
            self,
            target: Optional[str],
            check: str
    ) -> ReviewData: ...

# ========== ARENA-PROTOCOL | EXAMPLE-BASED-TESTING ====================================================================

@runtime_checkable
class Arena(Protocol):
    """
    Contract for isolated execution environments.
    """
    @property
    def fs(self) -> dict:
        """Overwritten by EBT with the normalized pre.fs state before setup."""
        # EBT injects a dictionary here before setup() is called, in the format:
        # {'target_path_in_arena': 'host_source_path_as_string'} ...

    @fs.setter
    def fs(self, value: dict) -> None: ...

    @property
    def workspace_path(self) -> Optional[Path]:
        """Set in `setup()` and read by EBT to diff the post-state."""
        # Must return the absolute path to the isolated working directory after setup().
        # EBT strictly requires this path for byte-level diffing during the _report() phase. ...

    def setup(self) -> None:
        """Creates the temporary workspace and hydrates the declared files from `self.fs`."""
        # Must create an isolated directory and place it in `self.workspace_path`.
        # Must project the host files defined in `self.fs` into the workspace.
        # Guarantees the integrity of the host process's workspace. ...

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Executes the target within an isolated workspace and returns the result."""
        # The target must be invoked within the context of `workspace_path` (via CWD change or subprocess).
        # System and runtime errors from the target should be propagated transparently.
        # The target's result must be returned to EBT unmodified. ...

    def teardown(self) -> None:
        """Destroys the workspace and cleans up all temporary environment states."""
        # Must completely delete the folder defined in `self.workspace_path`.
        # Must restore all temporarily modified global host states. ...

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