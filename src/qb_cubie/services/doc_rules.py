"""Standard didactic verification rules for documentation code examples."""

from __future__ import annotations

import dataclasses
from typing import Final

from .protocols import (
    DocDiagnostic,
    DocRuleProtocol,
    ExtractedExample,
    validate_severity,
)


def _validate_positive_int(value: int, name: str) -> int:
    """Validates that a configured rule threshold is a positive integer."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"STATE-GUARD: {name} must be a positive integer; received {value!r}.")
    return value


@dataclasses.dataclass(frozen=True)
class NoOutput:
    """Explains why a result block is empty and how to craft a verifiable example output."""

    severity: str = "warning"
    rule_id: str = "DOC-NO-OUTPUT"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Emits a context-aware diagnostic when a completed example has an empty result block."""
        expected = example.expected_output
        if actual_output is None or expected is None or expected.strip():
            return []
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                self._build_message(actual_output), example.session_id, self.severity,
            )
        ]

    @staticmethod
    def _build_message(actual_output: str) -> str:
        """Explains why the output is missing and how to design a verifiable example."""
        if actual_output.strip():
            return (
                f"Result block is empty, but the snippet produced stdout ({actual_output!r}). "
                "Document the expected output in the result block to guard it against regressions."
            )
        return (
            "Result block is empty because the snippet produced no stdout. "
            "Print a key return value or state property (e.g., 'print(result)'), "
            "or connect pure setup code to an active step via 'session=<id>'."
        )


@dataclasses.dataclass(frozen=True)
class HighComplexity:
    """Flags overly long code examples and suggests didactic simplifications."""

    max_lines: int = 30
    severity: str = "error"
    rule_id: str = "DOC-HIGH-COMPLEXITY"

    def __post_init__(self) -> None:
        validate_severity(self.severity)
        _validate_positive_int(self.max_lines, "max_lines")

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Emits a diagnostic when the code snippet exceeds max_lines."""
        _ = actual_output
        count = len(example.code.splitlines())
        if count <= self.max_lines:
            return []
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                self._build_message(count), example.session_id, self.severity,
            )
        ]

    def _build_message(self, count: int) -> str:
        """Explains why overly long snippets hurt readability and how to simplify them."""
        return (
            f"Code example has {count} lines (limit: {self.max_lines}). "
            "Overly long snippets in documentation can confuse readers and obscure the core "
            "concept; split sequential steps via 'session=<id>' with intermediate explanations "
            "or move setup boilerplate into 'pre_state=WorldState(fs=...)'."
        )


@dataclasses.dataclass(frozen=True)
class LargeOutput:
    """Flags overly long console outputs that reduce readability and make checks brittle."""

    max_lines: int = 25
    severity: str = "warning"
    rule_id: str = "DOC-LARGE-OUTPUT"

    def __post_init__(self) -> None:
        validate_severity(self.severity)
        _validate_positive_int(self.max_lines, "max_lines")

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Emits a diagnostic when the observed or expected output exceeds max_lines."""
        sample = actual_output if actual_output is not None else (example.expected_output or "")
        count = len(sample.splitlines())
        if count <= self.max_lines:
            return []
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                self._build_message(count), example.session_id, self.severity,
            )
        ]

    def _build_message(self, count: int) -> str:
        """Explains why large console dumps make documentation brittle and harder to scan."""
        return (
            f"Output spans {count} lines (limit: {self.max_lines}). "
            "Large console dumps reduce readability and make documentation checks brittle; "
            "print a concise summary or key attributes instead."
        )


@dataclasses.dataclass(frozen=True)
class RawTraceback:
    """Flags raw Python tracebacks in result blocks and recommends raises=<Exception>."""

    severity: str = "warning"
    rule_id: str = "DOC-RAW-TRACEBACK"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Emits a diagnostic when an expected output contains a raw traceback header."""
        _ = actual_output
        marker = "Traceback (most recent call last):"
        if not example.expected_output or marker not in example.expected_output:
            return []
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                self._build_message(), example.session_id, self.severity,
            )
        ]

    @staticmethod
    def _build_message() -> str:
        """Explains why raw tracebacks are brittle and recommends raises=<Exception>."""
        return (
            "Result block contains a raw Python traceback. "
            "Raw stack traces depend on local file paths and line numbers; "
            "use the 'raises=<Exception>' fence tag to verify expected exceptions cleanly."
        )


NoOutputRule = NoOutput
HighComplexityRule = HighComplexity
LargeOutputRule = LargeOutput
RawTracebackRule = RawTraceback

CUBIE_DOC_RULES: Final[tuple[DocRuleProtocol, ...]] = (
    NoOutput(severity="warning"),
    HighComplexity(max_lines=30, severity="error"),
    LargeOutput(max_lines=25, severity="warning"),
    RawTraceback(severity="warning"),
)
