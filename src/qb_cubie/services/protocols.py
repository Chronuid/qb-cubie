"""Protocols and immutable data records for the qb_cubie.services package."""

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable


# ========== DOC-ENSURANCE DATA RECORDS ================================================================================
@dataclass(frozen=True)
class MdBlock:
    """Represents a single structural block parsed from a Markdown document."""
    kind: str
    content: str
    line: int
    meta: str = ""


@dataclass(frozen=True)
class ExtractedExample:
    """Encapsulates a structurally validated code example and its expectations."""
    file_path: str
    line: int
    code: str
    expected_output: str | None = None
    explanation: str | None = None
    session_id: str | None = None
    expected_raises: str | None = None


@dataclass(frozen=True)
class ExampleSession:
    """Groups one or more examples that share a single arena and namespace lifecycle."""
    session_id: str
    steps: tuple[ExtractedExample, ...]


@dataclass(frozen=True)
class DocDiagnostic:
    """Describes a structural or runtime violation in a documentation file."""
    file_path: str
    rule_id: str
    line: int
    message: str
    session_id: str | None = None


@dataclass(frozen=True)
class SessionTrace:
    """Records the observed outputs and evaluation status of one executed session."""
    session_id: str
    actual_outputs: tuple[str, ...]
    passed: bool


@dataclass(frozen=True)
class DocReport:
    """Aggregates all session traces and diagnostics of a DocEnsurance run."""
    target: str
    passed: bool
    sessions: tuple[SessionTrace, ...] = ()
    diagnostics: tuple[DocDiagnostic, ...] = ()


# ========== DOC-ENSURANCE PROTOCOLS ===================================================================================
@runtime_checkable
class ServiceReportProtocol(Protocol):
    """Uniform report contract for services delegating diagnostics to PytestReporter."""

    @property
    def target(self) -> str: ...
    @property
    def passed(self) -> bool: ...
    @property
    def diagnostics(self) -> Sequence[DocDiagnostic]: ...


class DocBlockProtocol(Protocol):
    """Contract for atomic Markdown block matchers and extractors."""

    @property
    def role(self) -> str: ...

    def matches(self, block: MdBlock) -> bool: ...
    def extract(self, block: MdBlock) -> str: ...


class DocPatternProtocol(Protocol):
    """Contract for structural documentation patterns composed of block protocols."""

    @property
    def name(self) -> str: ...

    def scan(
        self, blocks: Sequence[MdBlock], file_path: str
    ) -> tuple[list[ExtractedExample], list[DocDiagnostic]]: ...


class DocScopeProtocol(Protocol):
    """Contract for grouping extracted examples into shared or isolated arena sessions."""
    def group(self, examples: Sequence[ExtractedExample]) -> list[ExampleSession]: ...