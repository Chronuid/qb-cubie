"""Modular documentation rules, structural block matchers, patterns, and scope definitions."""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable, Sequence
from typing import Final

from ...linter import Linter, LinterDiagnostic
from .protocols import (
    DocBlockProtocol,
    DocDiagnostic,
    ExampleSession,
    ExtractedExample,
    MdBlock,
    validate_severity,
)

_TAG_RE = re.compile(r"\b(?P<key>session|raises)=(?P<val>[^\s,]+)")


# ========== 1. PLUGGABLE CHECK RULES (EXPLANATION, CODE, OUTPUT) ======================================================
@dataclasses.dataclass(frozen=True)
class ExplanationRule:
    """Validates extracted explanation text against a custom predicate."""

    rule_id: str
    message: str
    check_fn: Callable[[str], bool]
    severity: str = "error"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Runs the explanation predicate when an explanation is present."""
        if example.explanation is None or self.check_fn(example.explanation):
            return []
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                self.message, example.session_id, self.severity,
            )
        ]


@dataclasses.dataclass(frozen=True)
class CodeRule:
    """Validates extracted example source code against a custom predicate."""

    rule_id: str
    message: str
    check_fn: Callable[[str], bool]
    severity: str = "error"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Evaluates the code snippet and emits a diagnostic if the predicate fails."""
        if self.check_fn(example.code):
            return []
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                self.message, example.session_id, self.severity,
            )
        ]


@dataclasses.dataclass(frozen=True)
class DocLinterRule:
    """Adapts any qb-cubie Linter to validate documentation code snippets."""

    linter: Linter
    severity: str | None = None

    def __post_init__(self) -> None:
        if self.severity is not None:
            validate_severity(self.severity)

    @property
    def rule_id(self) -> str:
        """Returns the wrapped linter's display name as the rule identifier."""
        return f"DOC-LINT:{self.linter.name}"

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Runs the underlying linter on the in-memory snippet and maps line offsets."""
        raw_diags = self.linter.check(example.code)
        return [self._map_diagnostic(example, d) for d in raw_diags]

    def _map_diagnostic(self, example: ExtractedExample, diag: LinterDiagnostic) -> DocDiagnostic:
        """Converts a LinterDiagnostic into a file-relative DocDiagnostic."""
        is_warn = diag.severity.lower() in ("warning", "note", "convention", "refactor", "info")
        sev = self.severity or ("warning" if is_warn else "error")
        line = example.line + max(1, diag.line)
        return DocDiagnostic(
            example.file_path, diag.rule_id, line, diag.message, example.session_id, sev
        )


@dataclasses.dataclass(frozen=True)
class OutputRule:
    """Validates expected and actual runtime output using a custom predicate."""

    rule_id: str
    message: str
    check_fn: Callable[[str | None, str | None], bool]
    severity: str = "error"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Evaluates expected and actual outputs after snippet execution."""
        if actual_output is None or self.check_fn(example.expected_output, actual_output):
            return []
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                self.message, example.session_id, self.severity,
            )
        ]


@dataclasses.dataclass(frozen=True)
class MissingOutputRule:
    """Flags empty or missing expected outputs inside documentation result blocks."""

    severity: str = "warning"
    rule_id: str = "DOC-OUT-MISSING"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Emits a diagnostic when a completed step has an empty result block."""
        if actual_output is None or example.expected_output is None or example.expected_output.strip():
            return []
        msg = "Missing expected output in result block."
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                msg, example.session_id, self.severity,
            )
        ]


@dataclasses.dataclass(frozen=True)
class OutputMatchRule:
    """Compares non-empty expected outputs against actual runtime stdout."""

    severity: str = "error"
    rule_id: str = "DOC-OUT"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        """Emits a diagnostic if the observed runtime output diverges from expectation."""
        if actual_output is None or not example.expected_output or not example.expected_output.strip():
            return []
        if actual_output == example.expected_output:
            return []
        msg = f"Output mismatch: expected {example.expected_output!r}, got {actual_output!r}."
        return [
            DocDiagnostic(
                example.file_path, self.rule_id, example.line,
                msg, example.session_id, self.severity,
            )
        ]


DEFAULT_DOC_RULES: Final[tuple[ExplanationRule | CodeRule | DocLinterRule | OutputRule | MissingOutputRule | OutputMatchRule, ...]] = (
    MissingOutputRule(severity="warning"),
    OutputMatchRule(severity="error"),
)


# ========== 2. ATOMIC BLOCK PROTOCOLS (LEVEL 1) =======================================================================
@dataclasses.dataclass(frozen=True)
class Explanation:
    """Matches a narrative Markdown paragraph with a required minimum character count."""

    min_chars: int = 20
    role: str = "explanation"
    severity: str = "error"
    rules: Sequence[ExplanationRule | CodeRule | DocLinterRule | OutputRule | MissingOutputRule | OutputMatchRule] = ()

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def matches(self, block: MdBlock) -> bool:
        """Checks whether the block is a paragraph meeting the minimum length."""
        return block.kind == "paragraph" and len(block.content.strip()) >= self.min_chars

    def extract(self, block: MdBlock) -> str:
        """Returns the stripped paragraph text."""
        return block.content.strip()


@dataclasses.dataclass(frozen=True)
class CodeSnippet:
    """Matches a fenced code block for a target language and extracts fence metadata."""

    lang: str = "python"
    role: str = "target"
    severity: str = "error"
    rules: Sequence[ExplanationRule | CodeRule | DocLinterRule | OutputRule | MissingOutputRule | OutputMatchRule] = ()

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def matches(self, block: MdBlock) -> bool:
        """Checks whether the block is a code fence for the configured language."""
        tokens = re.split(r"[\s,]+", block.meta.strip())
        return block.kind == "code" and bool(tokens) and tokens[0] == self.lang

    def extract(self, block: MdBlock) -> str:
        """Returns the raw source code of the snippet."""
        return block.content

    @staticmethod
    def parse_tags(meta: str) -> dict[str, str]:
        """Extracts key-value execution tags such as session and raises from fence metadata."""
        return {m.group("key"): m.group("val") for m in _TAG_RE.finditer(meta)}


@dataclasses.dataclass(frozen=True)
class CollapsibleResult:
    """Matches a collapsible HTML <details> block and strips optional inner code fences."""

    summary: str | None = None
    role: str = "result"
    severity: str = "error"
    rules: Sequence[ExplanationRule | CodeRule | DocLinterRule | OutputRule | MissingOutputRule | OutputMatchRule] = ()

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def matches(self, block: MdBlock) -> bool:
        """Checks whether the block is a details container with an optional summary match."""
        if block.kind != "details":
            return False
        return self.summary is None or self.summary in block.meta

    def extract(self, block: MdBlock) -> str:
        """Extracts the expected output text and unwraps a single inner code fence."""
        raw = block.content.strip("\r\n")
        lines = raw.splitlines()
        if len(lines) >= 2 and self._is_wrapped_fence(lines):
            return "\n".join(lines[1:-1]).strip("\r\n")
        return raw.strip() if len(lines) <= 1 else raw

    @staticmethod
    def _is_wrapped_fence(lines: list[str]) -> bool:
        """Checks whether lines start and end with a single matching fence without inner closes."""
        first, last = lines[0].strip(), lines[-1].strip()
        if not first.startswith(("```", "~~~")):
            return False
        fence = first[: len(first) - len(first.lstrip(first[0]))]
        return last == fence and not any(line.strip() == fence for line in lines[1:-1])


# ========== 3. PATTERN & SCOPE PROTOCOLS (LEVEL 2) ====================================================================
@dataclasses.dataclass(frozen=True)
class ExamplePattern:
    """Validates pre- and post-blocks around every anchor block in a Markdown stream."""

    anchor: DocBlockProtocol = CodeSnippet(lang="python")
    pre: Sequence[DocBlockProtocol] = ()
    post: Sequence[DocBlockProtocol] = ()
    name: str = "example-pattern"

    def scan(
        self, blocks: Sequence[MdBlock], file_path: str
    ) -> tuple[list[ExtractedExample], list[DocDiagnostic]]:
        """Scans a sequence of Markdown blocks and returns valid examples and diagnostics."""
        examples: list[ExtractedExample] = []
        diagnostics: list[DocDiagnostic] = []
        for idx, block in enumerate(blocks):
            if self.anchor.matches(block):
                self._inspect_anchor(blocks, idx, file_path, examples, diagnostics)
        return examples, diagnostics

    def _inspect_anchor(
        self,
        blocks: Sequence[MdBlock],
        idx: int,
        file_path: str,
        examples: list[ExtractedExample],
        diagnostics: list[DocDiagnostic],
    ) -> None:
        """Checks pre/post conditions around an anchor and records extracted examples."""
        anchor_block = blocks[idx]
        _, explanation = self._check_pre(blocks, idx, file_path, anchor_block.line, diagnostics)
        _, expected_out = self._check_post(blocks, idx, file_path, anchor_block.line, diagnostics)
        examples.append(self._build_example(anchor_block, file_path, explanation, expected_out))

    def _check_pre(
        self, blocks: Sequence[MdBlock], idx: int, file_path: str, line: int, diags: list[DocDiagnostic]
    ) -> tuple[bool, str | None]:
        """Validates all preceding block rules relative to the anchor index."""
        ok, explanation = True, None
        for offset, rule in enumerate(reversed(self.pre), start=1):
            target_idx = idx - offset
            if target_idx < 0 or not rule.matches(blocks[target_idx]):
                msg = f"Missing or invalid pre-block '{rule.role}'."
                diags.append(DocDiagnostic(file_path, "DOC-PRE", line, msg, severity=rule.severity))
                ok = ok and rule.severity != "error"
                explanation = self._fallback_explanation(rule, blocks, target_idx, explanation)
            elif rule.role == "explanation" or explanation is None:
                explanation = rule.extract(blocks[target_idx])
        return ok, explanation

    @staticmethod
    def _fallback_explanation(
        rule: DocBlockProtocol, blocks: Sequence[MdBlock], target_idx: int, current: str | None
    ) -> str | None:
        """Extracts paragraph text even when an Explanation block fails min_chars."""
        if current is None and target_idx >= 0 and rule.role == "explanation" and blocks[target_idx].kind == "paragraph":
            return rule.extract(blocks[target_idx])
        return current

    def _check_post(
        self, blocks: Sequence[MdBlock], idx: int, file_path: str, line: int, diags: list[DocDiagnostic]
    ) -> tuple[bool, str | None]:
        """Validates all succeeding block rules relative to the anchor index."""
        expected_out: str | None = None
        for offset, rule in enumerate(self.post, start=1):
            target_idx = idx + offset
            if target_idx >= len(blocks) or not rule.matches(blocks[target_idx]):
                msg = f"Missing or invalid post-block '{rule.role}'."
                diags.append(DocDiagnostic(file_path, "DOC-POST", line, msg, severity=rule.severity))
                return rule.severity != "error", None
            expected_out = rule.extract(blocks[target_idx])
        return True, expected_out

    def _build_example(
        self, block: MdBlock, file_path: str, explanation: str | None, expected_out: str | None
    ) -> ExtractedExample:
        """Constructs an ExtractedExample instance from a verified anchor block."""
        tags = CodeSnippet.parse_tags(block.meta)
        return ExtractedExample(
            file_path=file_path,
            line=block.line,
            code=self.anchor.extract(block),
            expected_output=expected_out,
            explanation=explanation,
            session_id=tags.get("session"),
            expected_raises=tags.get("raises"),
        )


CUBIE_DOC_STYLE: Final[ExamplePattern] = ExamplePattern(
    name="cubie-doc-style",
    pre=(Explanation(min_chars=20),),
    anchor=CodeSnippet(lang="python"),
    post=(CollapsibleResult(),),
)


class TaggedScope:
    """Groups examples with identical `session=<id>` tags per file while keeping untagged blocks isolated."""

    def group(self, examples: Sequence[ExtractedExample]) -> list[ExampleSession]:
        """Clusters examples by file path and session tag while preserving declaration order."""
        buckets: dict[str, list[ExtractedExample]] = {}
        for idx, ex in enumerate(examples):
            suffix = f"session:{ex.session_id}" if ex.session_id else f"isolated:{idx}"
            key = f"{ex.file_path}::{suffix}"
            buckets.setdefault(key, []).append(ex)
        return [ExampleSession(session_id=k, steps=tuple(v)) for k, v in buckets.items()]
