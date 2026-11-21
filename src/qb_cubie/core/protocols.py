import re
import typing
from collections.abc import Sequence
from typing import Any, Final, Optional, Protocol, runtime_checkable, Dict, List, Callable, Iterable, Literal
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

# ========== REVIEWER-PROTOCOL | REVIEW-BASED-TESTING ==================================================================


@dataclass
class ReviewData:
    """Encapsulates the standardized result of an RBT test."""

    passed: bool
    report: Dict[str, Any] = field(default_factory=dict)


class Reviewer(Protocol):
    """Defines the contract for all injectable test instances."""

    def review(self, target: Optional[str], check: str) -> ReviewData: ...


# ========== WORLDSTATE-DATACLASS | EXAMPLE-BASED-TESTING ==============================================================


class _UnspecifiedReturn(Enum):
    """Keep the sentinel's identity stable through copying and process serialization."""

    VALUE = "UNSPECIFIED"

    def __repr__(self) -> str:
        return "UNSPECIFIED"


UNSPECIFIED = _UnspecifiedReturn.VALUE


@dataclass(frozen=True)
class ExceptionExpectation:
    """Match an ordinary target exception by subclass and optional message regex."""

    exception_type: type[Exception]
    match: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.exception_type, type) or not issubclass(self.exception_type, Exception):
            raise TypeError("exception_type must be a subclass of Exception.")
        if self.match is not None:
            if not isinstance(self.match, str):
                raise TypeError("ExceptionExpectation.match must be a string or None.")
            try:
                re.compile(self.match)
            except re.error as error:
                raise ValueError(f"Invalid exception message regex: {error}") from error


@dataclass
class WorldState:
    """Declares execution environments, file system states, and functional parameters of a test world."""

    # Omit returns (or use UNSPECIFIED) to leave the return value unrestricted.
    # Explicit returns=None requires the target to return None.
    # raises declares an alternative exceptional completion; it cannot be combined
    # with returns in the same state. exception records an observed target error.

    args: Optional[Any] = None
    kwargs: Optional[Any] = None
    arena: Optional[Any] = None
    fs: Optional[Any] = None
    returns: Any = UNSPECIFIED
    expect: bool = True
    raises: ExceptionExpectation | None = None
    exception: Exception | None = None

    def __post_init__(self) -> None:
        self.validate_expect()
        self.validate_exception_contract()

    def validate_expect(self) -> None:
        """Validate that WorldState.expect is strictly a bool."""
        validate_bool_expect(self.expect, "WorldState.expect")

    def validate_exception_contract(self) -> None:
        """Also called before each run, since WorldState is mutable."""
        if self.raises is not None:
            if not isinstance(self.raises, ExceptionExpectation):
                raise TypeError("WorldState.raises must be an ExceptionExpectation or None.")
            if self.returns is not UNSPECIFIED:
                raise ValueError("A WorldState cannot specify both returns and raises.")
        if self.exception is not None:
            if not isinstance(self.exception, Exception):
                raise TypeError("WorldState.exception must be an Exception or None.")
            if self.returns is not UNSPECIFIED:
                raise ValueError("An exceptional outcome cannot also contain a return value.")


# ========== ARENA-PROTOCOL | EXAMPLE-BASED-TESTING ====================================================================


@runtime_checkable
class Arena(Protocol):
    """Contract for temporary execution environments; no OS security boundary is implied."""

    @property
    def workspace_path(self) -> Optional[Path]:
        """Returns the absolute path to the arena working directory after setup."""
        ...

    def setup(self, state: WorldState) -> None:
        """Creates the temporary workspace and hydrates it based on the provided WorldState."""
        ...

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Executes the target within the arena workspace and returns the raw functional result."""
        ...

    def get_state(self) -> WorldState:
        """Packages and returns the mutated environment reality as a complete WorldState."""
        ...

    def teardown(self) -> None:
        """Destroys the workspace and cleans up all temporary environment states."""
        ...


# ========== TRACING-DATACLASSES | EXAMPLE-BASED-TESTING ===============================================================

Quantor = Literal["all", "exists"]
StateInput = WorldState | List[WorldState] | Dict[str, Any] | None


def validate_bool_expect(value: Any, field: str) -> bool:
    """Validate that an expect flag is strictly a bool, rejecting int, None, and other types."""
    if type(value) is not bool:
        raise TypeError(
            f"STATE-GUARD: {field} must be a bool (True or False); received {type(value).__name__}."
        )
    return value


def evaluate_step_logic(traces: List["EvaluationTrace"], post_quantor: Quantor = "exists") -> bool:
    """Evaluate one step's traces purely under the declared post_quantor."""
    results: list[bool] = []
    for trace in traces:
        expected = validate_bool_expect(trace.post.expect, "post.expect")
        if post_quantor == "exists" and not expected:
            raise ValueError(
                "STATE-GUARD: WorldState(expect=False) is forbidden under post_quantor='exists'; "
                "use post={'quantor': 'all', 'states': [...]}."
            )
        results.append(trace.evaluation if expected else not trace.evaluation)
    return all(results) if post_quantor == "all" else any(results)


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
    pre_quantor: Quantor = "all"
    post_quantor: Quantor = "exists"


# ========== IPC-CODEC-PROTOCOL | PYVENV-ARENA =========================================================================


class IPCC(Protocol):
    """Defines the contract for Inter-Process Communication Codecs."""

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
    """Defines the contract for reporters consuming a test result."""

    def report(self, trace: ResultT, /) -> None:
        """Processes and outputs the final test result."""
        ...


# ========== MULTIRPOCESSOR-PROTOCOLS ==================================================================================


class Mapper(typing.ContextManager["Mapper"], Protocol):
    """The execution interface of the multiprocessor protocol, which also manages its own lifecycle."""

    # Call the supplied function and preserve its exceptions across transport.
    # Do not suppress task errors or replace them with backend failures. EBT
    # ignores exception suppression from __exit__ to avoid successful empty runs.

    def map(self, fn: Callable, *iterables: Iterable) -> Iterable[Any]: ...


class Multiprocessor(Protocol):
    """The DI protocol for the multiprocessor registration."""

    priority: int

    def check_condition(self, pre_states: list, post_states: list) -> bool:
        """The hook-case under review. Evaluates whether this processor is responsible."""
        ...

    def create_handler(self, n_tasks: int, *, max_workers: int | None = None) -> Mapper:
        """Return a context-managed mapper respecting an optional worker limit."""

        # Legacy factories taking only n_tasks are called without max_workers
        # when EBT has no explicit limit. An explicit limit requires support.
        ...


# ========== VM-ARENA-PROTOCOLS ========================================================================================


@dataclass
class DeviceResources:
    ram_mb: Optional[int] = None
    cpu_cores: Optional[float] = None
    # Extensible in the future to include I/O limits, GPU allocations, etc.


# ========== SERVICE-DIAGNOSTIC-PROTOCOLS ==============================================================================

VALID_SEVERITIES: Final[tuple[str, ...]] = ("error", "warning")


def validate_severity(severity: str) -> str:
    """Validates that a configured diagnostic severity is supported."""
    if not isinstance(severity, str) or severity not in VALID_SEVERITIES:
        raise ValueError(
            f"STATE-GUARD: severity must be one of {VALID_SEVERITIES}; received {severity!r}."
        )
    return severity


@dataclass(frozen=True)
class Diagnostic:
    """Describes a domain-neutral structural, rule-based, or runtime diagnostic."""

    file_path: str
    rule_id: str
    line: int
    message: str
    severity: str = "error"

    def __post_init__(self) -> None:
        validate_severity(self.severity)


@runtime_checkable
class DiagnosticProtocol(Protocol):
    """Structural contract for any diagnostic emitted by a qb-cubie service."""

    @property
    def file_path(self) -> str: ...
    @property
    def rule_id(self) -> str: ...
    @property
    def line(self) -> int: ...
    @property
    def message(self) -> str: ...
    @property
    def severity(self) -> str: ...


@runtime_checkable
class ServiceReportProtocol(Protocol):
    """Uniform report contract for services delegating diagnostics to PytestReporter."""

    @property
    def target(self) -> str: ...
    @property
    def passed(self) -> bool: ...
    @property
    def diagnostics(self) -> Sequence[DiagnosticProtocol]: ...


@runtime_checkable
class FileCheckProtocol(Protocol):
    """Domain-neutral contract for rules checking whole files within a target workspace."""

    @property
    def rule_id(self) -> str: ...
    @property
    def severity(self) -> str | None: ...
    @property
    def context_key(self) -> str: ...
    def prepare_context(
        self,
        target: str | Path,
        excludes: Sequence[str],
        patterns: Sequence[Any],
    ) -> Any: ...
    def check_file(
        self,
        file_path: str,
        content: str,
        context: Any,
    ) -> Sequence[DiagnosticProtocol]: ...
