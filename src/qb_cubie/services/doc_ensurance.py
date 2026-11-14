"""Tries to verify structural conventions and runtime outputs of documentation code examples."""

from __future__ import annotations

import contextlib
import dataclasses
import io
import math
import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Final

from ..arenas.tempfs import TempFS
from ..linter import DEFAULT_EXCLUDES, Linter, LinterDiagnostic
from ..protocols import Arena, Reporter, WorldState
from ..reporter import PytestReporter
from ._markdown_scanner import _MarkdownScanner
from .protocols import (
    DocBlockProtocol,
    DocDiagnostic,
    DocPatternProtocol,
    DocReport,
    DocRuleProtocol,
    DocScopeProtocol,
    ExampleSession,
    ExtractedExample,
    MdBlock,
    SessionTrace,
    validate_severity,
)

_TAG_RE = re.compile(r"\b(?P<key>session|raises)=(?P<val>[^\s]+)")
_MD_PREFIXES = ("#", "`", "~", "<", ">", "-", "*", "+", "!", "[", "|")
_DEFAULT_REPORTER: Final[PytestReporter] = PytestReporter()


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
        is_warn = diag.severity in ("warning", "note", "convention", "refactor")
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


DEFAULT_DOC_RULES: Final[tuple[DocRuleProtocol, ...]] = (
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
    rules: Sequence[DocRuleProtocol] = ()

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
    rules: Sequence[DocRuleProtocol] = ()

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def matches(self, block: MdBlock) -> bool:
        """Checks whether the block is a code fence for the configured language."""
        tokens = block.meta.strip().split()
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
    rules: Sequence[DocRuleProtocol] = ()

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def matches(self, block: MdBlock) -> bool:
        """Checks whether the block is a details container with an optional summary match."""
        if block.kind != "details":
            return False
        return self.summary is None or self.summary in block.meta

    def extract(self, block: MdBlock) -> str:
        """Extracts the expected output text and unwraps a single inner code fence."""
        raw = block.content.strip()
        lines = raw.splitlines()
        if len(lines) >= 2 and self._is_wrapped_fence(lines):
            return "\n".join(lines[1:-1]).strip()
        return raw

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
        """Checks pre/post conditions around an anchor and records valid or session-bound steps."""
        anchor_block = blocks[idx]
        pre_ok, explanation = self._check_pre(blocks, idx, file_path, anchor_block.line, diagnostics)
        post_ok, expected_out = self._check_post(blocks, idx, file_path, anchor_block.line, diagnostics)
        has_session = "session" in CodeSnippet.parse_tags(anchor_block.meta)
        if (pre_ok and post_ok) or has_session:
            examples.append(self._build_example(anchor_block, file_path, explanation, expected_out))

    def _check_pre(
        self, blocks: Sequence[MdBlock], idx: int, file_path: str, line: int, diags: list[DocDiagnostic]
    ) -> tuple[bool, str | None]:
        """Validates all preceding block rules relative to the anchor index."""
        explanation: str | None = None
        for offset, rule in enumerate(reversed(self.pre), start=1):
            target_idx = idx - offset
            if target_idx < 0 or not rule.matches(blocks[target_idx]):
                msg = f"Missing or invalid pre-block '{rule.role}'."
                diags.append(DocDiagnostic(file_path, "DOC-PRE", line, msg, severity=rule.severity))
                return rule.severity != "error", None
            if rule.role == "explanation" or explanation is None:
                explanation = rule.extract(blocks[target_idx])
        return True, explanation

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


class IsolatedScope:
    """Assigns every extracted example to its own isolated arena session."""

    def group(self, examples: Sequence[ExtractedExample]) -> list[ExampleSession]:
        """Wraps each example into a dedicated single-step ExampleSession."""
        return [
            ExampleSession(session_id=f"{ex.file_path}::isolated:{idx}", steps=(ex,))
            for idx, ex in enumerate(examples)
        ]


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


# ========== 4. ARENA SESSION WORKER (IPC-SAFE PRIMITIVES) =============================================================
def _execute_session_payload(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Top-level worker executed inside the Arena; shares globals and CWD across steps."""
    shared_globals: dict[str, Any] = {"__name__": "__main__"}
    return [_execute_single_step(step, shared_globals) for step in steps]


def _execute_single_step(step: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    """Executes one snippet, captures stdout, and intercepts expected exceptions."""
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(compile(step["code"], f"<doc_line_{step['line']}>", "exec"), env)  # noqa: S102
    except (Exception, SystemExit) as error:  # noqa: BLE001
        return _classify_step_exception(error, step.get("expected_raises"))
    return _finalize_normal_step(buffer.getvalue().strip(), step.get("expected_raises"))


def _classify_step_exception(error: BaseException, expected_raises: str | None) -> dict[str, Any]:
    """Determines whether a caught exception satisfies a declared `raises=` tag."""
    mro_names = {cls.__name__ for cls in type(error).__mro__}
    formatted = f"{type(error).__name__}: {error}".strip()
    if expected_raises is not None:
        if expected_raises in mro_names:
            return {"status": "OK", "output": formatted}
        msg = f"Expected exception '{expected_raises}', but '{type(error).__name__}' was raised."
        return {"status": "DOC-RAISE", "output": formatted, "error": msg}
    return {"status": "DOC-EXEC", "output": "", "error": f"Unhandled {formatted}"}


def _finalize_normal_step(output: str, expected_raises: str | None) -> dict[str, Any]:
    """Checks whether an exception was expected when the snippet completed normally."""
    if expected_raises is not None:
        msg = f"Expected exception '{expected_raises}', but snippet completed normally."
        return {"status": "DOC-RAISE", "output": output, "error": msg}
    return {"status": "OK", "output": output}


# ========== 5. DOC-ENSURANCE SERVICE (LEVEL 3) ========================================================================
class DocEnsurance:
    """Verifies structural conventions, custom rules, and runtime outputs of documentation examples."""

    def __init__(
        self,
        target: str | Path | None = None,
        pattern: DocPatternProtocol | None = None,
        scope: DocScopeProtocol | None = None,
        arena: Arena | None = None,
        reporter: Reporter[DocReport] | None = _DEFAULT_REPORTER,
        pre_state: WorldState | None = None,
        excludes: Sequence[str] | None = None,
        rules: Sequence[DocRuleProtocol | Linter | type] | None = None,
        *,
        timeout: float | None = 10.0,
    ) -> None:
        """Initializes the documentation verification service with default project conventions."""
        self.timeout = self._validate_timeout(timeout)
        self.target: str | Path = target if target is not None else self._default_project_dir()
        self.pattern = pattern or CUBIE_DOC_STYLE
        self.scope = scope or TaggedScope()
        self.arena = self._configure_arena(arena, self.timeout)
        self.reporter = reporter
        self.pre_state = pre_state or WorldState()
        self.excludes = set(DEFAULT_EXCLUDES) | set(excludes or ())
        self.rules: list[DocRuleProtocol] = self._build_rules(self.pattern, rules)
        self._reset_state()

    def register_rule(self, *rules: DocRuleProtocol | Linter | type) -> DocEnsurance:
        """Registers or overrides one or more check rules by rule_id."""
        registry = {r.rule_id: r for r in self.rules}
        for raw in rules:
            rule = self._coerce_rule(raw)
            registry[rule.rule_id] = rule
        self.rules = list(registry.values())
        return self

    @classmethod
    def _build_rules(
        cls, pattern: DocPatternProtocol, custom: Sequence[DocRuleProtocol | Linter | type] | None
    ) -> list[DocRuleProtocol]:
        """Merges default rules, pattern block rules, and user-provided rules by rule_id."""
        defaults = DEFAULT_DOC_RULES if custom is None else (OutputMatchRule(severity="error"),)
        registry: dict[str, DocRuleProtocol] = {r.rule_id: r for r in defaults}
        for raw in (*cls._extract_pattern_rules(pattern), *(custom or ())):
            rule = cls._coerce_rule(raw)
            registry[rule.rule_id] = rule
        return list(registry.values())

    def _reset_state(self) -> None:
        """Resets internal pipeline buffers before a verification run."""
        self._sources: list[tuple[str, str]] = []
        self._sessions: list[ExampleSession] = []
        self._diagnostics: list[DocDiagnostic] = []
        self._traces: list[SessionTrace] = []
        self.report_result: DocReport | None = None

    @staticmethod
    def _extract_pattern_rules(pattern: DocPatternProtocol) -> list[Any]:
        """Extracts rules attached directly to pre, anchor, or post blocks of a pattern."""
        blocks = [
            *getattr(pattern, "pre", ()),
            getattr(pattern, "anchor", None),
            *getattr(pattern, "post", ()),
        ]
        return [r for b in blocks if b is not None for r in getattr(b, "rules", ())]

    @staticmethod
    def _coerce_rule(item: Any) -> DocRuleProtocol:
        """Normalizes rule classes, Linter instances, and DocRuleProtocol objects."""
        instance = item() if isinstance(item, type) else item
        if isinstance(instance, DocRuleProtocol):
            return instance
        if hasattr(instance, "check") and hasattr(instance, "name"):
            return DocLinterRule(linter=instance)
        raise TypeError(
            f"STATE-GUARD: Rule must implement DocRuleProtocol or Linter; received {type(instance).__name__}."
        )

    @staticmethod
    def _validate_timeout(timeout: float | None) -> float | None:
        """Validates that the configured TTL timeout is a positive finite number or None."""
        if timeout is None:
            return None
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("STATE-GUARD: timeout must be a positive finite number or None.")
        if timeout <= 0 or math.isnan(timeout) or math.isinf(timeout):
            raise ValueError("STATE-GUARD: timeout must be a positive finite number or None.")
        return float(timeout)

    @staticmethod
    def _configure_arena(arena: Arena | None, timeout: float | None) -> Arena:
        """Builds a default TempFS with the TTL timeout or applies it to an unconfigured arena."""
        if arena is None:
            return TempFS(timeout=timeout)
        if timeout is not None and getattr(arena, "timeout", None) is None:
            setattr(arena, "timeout", timeout)  # noqa: B010
        return arena

    @staticmethod
    def _default_project_dir() -> Path:
        """Resolves the project root directory relative to CWD or pyproject.toml."""
        cwd = Path.cwd().resolve()
        for directory in (cwd, *cwd.parents):
            if (directory / "pyproject.toml").exists():
                return directory
        return cwd

    # ---------- SERVICES ----------------------------------------------------------------------------------------------
    def run(self) -> DocReport:
        """Executes the documentation verification pipeline and returns the report."""
        __tracebackhide__ = True
        self._arrange()
        self._validate()
        self._report()
        if self.report_result is None:
            raise RuntimeError("STATE-GUARD: DocEnsurance run yielded no report_result.")
        return self.report_result

    # ---------- PIPES -------------------------------------------------------------------------------------------------
    def _arrange(self) -> None:
        """Validates inputs, parses Markdown blocks, and groups valid examples into sessions."""
        __tracebackhide__ = True
        self._reset_state()
        self._sources = self._resolve_sources(self.target, self.excludes)
        all_examples = self._scan_all_sources()
        self._sessions = self.scope.group(all_examples)

    def _scan_all_sources(self) -> list[ExtractedExample]:
        """Scans all loaded Markdown sources and filters broken isolated steps."""
        all_examples: list[ExtractedExample] = []
        for file_path, content in self._sources:
            examples, diags = self.pattern.scan(_MarkdownScanner(content).parse(), file_path)
            self._diagnostics.extend(diags)
            all_examples.extend(self._filter_examples(examples, diags))
        return all_examples

    def _filter_examples(
        self, examples: list[ExtractedExample], diags: list[DocDiagnostic]
    ) -> list[ExtractedExample]:
        """Drops examples with hard error diagnostics when running in IsolatedScope."""
        if not isinstance(self.scope, IsolatedScope):
            return examples
        broken_lines = {d.line for d in diags if d.severity == "error"}
        return [ex for ex in examples if ex.line not in broken_lines]

    def _validate(self) -> None:
        """Executes each grouped session inside the configured Arena and checks outputs."""
        __tracebackhide__ = True
        for session in self._sessions:
            trace, diags = self._execute_session(session)
            self._traces.append(trace)
            self._diagnostics.extend(diags)

    def _report(self) -> None:
        """Builds the final DocReport and delegates it to the configured reporter."""
        __tracebackhide__ = True
        is_memory = bool(self._sources) and self._sources[0][0] == "IN_MEMORY"
        label = "IN_MEMORY" if is_memory else str(self.target)
        report = DocReport(
            target=label,
            passed=not self._has_errors(self._diagnostics),
            sessions=tuple(self._traces),
            diagnostics=tuple(self._diagnostics),
        )
        self.report_result = report
        if self.reporter is not None:
            self.reporter.report(report)

    @staticmethod
    def _has_errors(diags: Sequence[DocDiagnostic]) -> bool:
        """Checks whether any recorded diagnostic has error severity."""
        return any(d.severity == "error" for d in diags)

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------
    @classmethod
    def _resolve_sources(cls, target: Any, excludes: set[str]) -> list[tuple[str, str]]:
        """Validates the target and loads Markdown content from file, directory, or memory."""
        if isinstance(target, Path):
            return cls._load_path_sources(target, excludes)
        if isinstance(target, str):
            if not target.strip():
                raise ValueError("STATE-GUARD: Markdown target string must not be empty.")
            if cls._looks_like_path(target):
                return cls._load_path_sources(Path(target.strip()), excludes)
            return [("IN_MEMORY", target)]
        raise TypeError(
            f"STATE-GUARD: target must be a Markdown str or Path; received {type(target).__name__}."
        )

    @staticmethod
    def _looks_like_path(target: str) -> bool:
        """Distinguishes single-line filesystem path strings from in-memory Markdown."""
        stripped = target.strip()
        if "\n" in stripped or stripped.startswith(_MD_PREFIXES):
            return False
        if "](" in stripped or "://" in stripped:
            return False
        if Path(stripped).exists():
            return True
        first_token = stripped.split()[0]
        return " " not in stripped or "/" in first_token or "\\" in first_token

    @classmethod
    def _crawl_directory(cls, root: Path, excludes: set[str]) -> list[Path]:
        """Recursively collects sorted Markdown files while respecting relative exclusions."""
        resolved = root.resolve()
        return [
            path for path in sorted(resolved.rglob("*.md"))
            if path.is_file() and not cls._is_excluded(path.relative_to(resolved), resolved.name, excludes)
        ]

    @staticmethod
    def _is_excluded(rel_path: Path, root_name: str, excludes: set[str]) -> bool:
        """Checks whether a path relative to root matches any segment or subpath exclusion."""
        rel_posix = rel_path.as_posix()
        for excl in excludes:
            norm = excl.strip("/").removeprefix(f"{root_name}/")
            if norm in rel_path.parts or rel_posix == norm or rel_posix.startswith(f"{norm}/"):
                return True
        return False

    @classmethod
    def _load_path_sources(cls, target: Path, excludes: set[str]) -> list[tuple[str, str]]:
        """Loads either a single Markdown file or crawls a directory recursively."""
        if not target.exists():
            raise FileNotFoundError(f"STATE-GUARD: Documentation path not found: {target}")
        if target.is_file():
            return [(str(target), target.read_text(encoding="utf-8"))]
        files = cls._crawl_directory(target, excludes)
        if not files:
            raise ValueError(f"STATE-GUARD: No Markdown files found in directory: {target}")
        return [(str(path), path.read_text(encoding="utf-8")) for path in files]

    def _execute_session(self, session: ExampleSession) -> tuple[SessionTrace, list[DocDiagnostic]]:
        """Runs a single session in the arena and evaluates all step outcomes and rules."""
        payload = [
            {"code": s.code, "line": s.line, "expected_raises": s.expected_raises}
            for s in session.steps
        ]
        raw_outcomes = self._invoke_arena(payload)
        return self._evaluate_outcomes(session, raw_outcomes)

    def _invoke_arena(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Dispatches the session payload to the Arena lifecycle."""
        self.arena.setup(self.pre_state)
        try:
            return self.arena.execute(_execute_session_payload, (payload,), {})
        finally:
            self.arena.teardown()

    def _evaluate_outcomes(
        self, session: ExampleSession, outcomes: list[dict[str, Any]]
    ) -> tuple[SessionTrace, list[DocDiagnostic]]:
        """Compares step outcomes against expected outputs and registered rules."""
        diags: list[DocDiagnostic] = []
        outputs: list[str] = []
        for step, outcome in zip(session.steps, outcomes):
            outputs.append(outcome["output"])
            diags.extend(self._check_step_outcome(step, outcome, session.session_id))
        passed = not self._has_errors(diags)
        return SessionTrace(session.session_id, tuple(outputs), passed), diags

    def _check_step_outcome(
        self, step: ExtractedExample, outcome: dict[str, Any], session_id: str
    ) -> list[DocDiagnostic]:
        """Evaluates runtime execution errors and dispatches all registered DocRuleProtocols."""
        step_diags: list[DocDiagnostic] = []
        if outcome["status"] in ("DOC-EXEC", "DOC-RAISE"):
            step_diags.append(
                DocDiagnostic(step.file_path, outcome["status"], step.line, outcome["error"], session_id)
            )
        actual_out = outcome["output"] if outcome["status"] == "OK" else None
        step_diags.extend(self._run_step_rules(step, actual_out, session_id))
        return step_diags

    def _run_step_rules(
        self, step: ExtractedExample, actual_out: str | None, session_id: str
    ) -> list[DocDiagnostic]:
        """Runs all registered rules for a step and attaches the canonical session_id."""
        return [
            dataclasses.replace(d, session_id=session_id)
            for rule in self.rules
            for d in rule.check(step, actual_out)
        ]