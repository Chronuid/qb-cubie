"""Protocols and immutable data records for the qb_cubie.services.doc_ensurance package."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final, Protocol, runtime_checkable

VALID_SEVERITIES: Final[tuple[str, ...]] = ("error", "warning")


def validate_severity(severity: str) -> str:
    """Validates that a configured diagnostic severity is supported."""
    if not isinstance(severity, str) or severity not in VALID_SEVERITIES:
        raise ValueError(
            f"STATE-GUARD: severity must be one of {VALID_SEVERITIES}; received {severity!r}."
        )
    return severity


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
    """Describes a structural, rule-based, or runtime violation in a documentation file."""

    file_path: str
    rule_id: str
    line: int
    message: str
    session_id: str | None = None
    severity: str = "error"

    def __post_init__(self) -> None:
        validate_severity(self.severity)


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
    sessions: tuple[SessionTrace, ...] = field(default_factory=tuple)
    diagnostics: tuple[DocDiagnostic, ...] = field(default_factory=tuple)


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


@runtime_checkable
class DocRuleProtocol(Protocol):
    """Contract for pluggable documentation rules checking explanation, code, or output."""

    @property
    def rule_id(self) -> str: ...
    @property
    def severity(self) -> str | None: ...
    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> Sequence[DocDiagnostic]: ...


class DocBlockProtocol(Protocol):
    """Contract for atomic Markdown block matchers and extractors."""

    @property
    def role(self) -> str: ...
    @property
    def severity(self) -> str: ...
    @property
    def rules(self) -> Sequence[DocRuleProtocol]: ...
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