"""Tries to verify structural conventions and runtime outputs of documentation code examples."""

from __future__ import annotations

import contextlib
import dataclasses
import io
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from ..arenas.tempfs import TempFS
from ..linter import DEFAULT_EXCLUDES, CstLinter, Linter, LinterDiagnostic
from ..protocols import Arena, Reporter, WorldState
from ..reporter import PytestReporter
from ._markdown_scanner import _MarkdownScanner
from .doc_patterns import (
    CUBIE_DOC_STYLE,
    DEFAULT_DOC_RULES,
    CodeRule,
    CodeSnippet,
    CollapsibleResult,
    DocLinterRule,
    ExamplePattern,
    Explanation,
    ExplanationRule,
    MissingOutputRule,
    OutputMatchRule,
    OutputRule,
    TaggedScope,
)
from .protocols import (
    DocDiagnostic,
    DocPatternProtocol,
    DocReport,
    DocRuleProtocol,
    DocScopeProtocol,
    ExampleSession,
    ExtractedExample,
    SessionTrace,
)

__all__ = [
    "CUBIE_DOC_STYLE",
    "DEFAULT_DOC_RULES",
    "CodeRule",
    "CodeSnippet",
    "CollapsibleResult",
    "DocEnsurance",
    "DocLinterRule",
    "ExamplePattern",
    "Explanation",
    "ExplanationRule",
    "MissingOutputRule",
    "OutputMatchRule",
    "OutputRule",
    "TaggedScope",
]

_MD_PREFIXES = ("#", "`", "~", "<", ">", "-", "*", "+", "!", "[", "|")
_DEFAULT_REPORTER: Final[PytestReporter] = PytestReporter()


# ========== 1. ARENA SESSION WORKER (IPC-SAFE PRIMITIVES) =============================================================
def _execute_session_payload(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Top-level worker executed inside the Arena; shares globals and CWD across steps."""
    shared_globals: dict[str, Any] = {"__name__": "__main__"}
    return [_execute_single_step(step, shared_globals) for step in steps]


def _execute_single_step(step: dict[str, Any], env: dict[str, Any]) -> dict[str, Any]:
    """Executes one snippet, captures stdout, and intercepts expected exceptions."""
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            exec(compile(step["code"], "<doc>", "exec"), env)  # noqa: S102
    except BaseException as error:  # noqa: BLE001
        return _classify_step_exception(error, step.get("expected_raises"))
    return _finalize_normal_step(buffer.getvalue().strip("\r\n"), step.get("expected_raises"))


def _classify_step_exception(error: BaseException, expected_raises: str | None) -> dict[str, Any]:
    """Determines whether a caught exception satisfies a declared `raises=` tag."""
    mro_names = {
        name for cls in type(error).__mro__ for name in (cls.__name__, f"{cls.__module__}.{cls.__name__}")
    }
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
        """Registers or overrides one or more check rules without muting orthogonal linters."""
        registry = self._index_existing_rules(self.rules)
        for raw in rules:
            self._register_into(registry, self._coerce_rule(raw))
        if any(r.rule_id == "DOC-NO-OUTPUT" for r in registry.values()):
            registry.pop("DOC-OUT-MISSING", None)
        self.rules = list(registry.values())
        return self

    @classmethod
    def _build_rules(
        cls, pattern: DocPatternProtocol, custom: Sequence[DocRuleProtocol | Linter | type] | None
    ) -> list[DocRuleProtocol]:
        """Merges default rules, pattern block rules, and user-provided rules without silent muting."""
        explicit_empty = custom is not None and len(custom) == 0
        defaults = (OutputMatchRule(severity="error"),) if explicit_empty else DEFAULT_DOC_RULES
        registry: dict[str, DocRuleProtocol] = {r.rule_id: r for r in defaults}
        for raw in (*cls._extract_pattern_rules(pattern), *(custom or ())):
            cls._register_into(registry, cls._coerce_rule(raw))
        if any(r.rule_id == "DOC-NO-OUTPUT" for r in registry.values()):
            registry.pop("DOC-OUT-MISSING", None)
        return list(registry.values())

    @classmethod
    def _index_existing_rules(cls, rules: Sequence[DocRuleProtocol]) -> dict[str, DocRuleProtocol]:
        """Indexes existing rules into a mutable registry while preserving duplicate linter slots."""
        registry: dict[str, DocRuleProtocol] = {}
        for rule in rules:
            key = cls._unique_rule_key(registry, rule.rule_id) if rule.rule_id in registry else rule.rule_id
            registry[key] = rule
        return registry

    @classmethod
    def _register_into(cls, registry: dict[str, DocRuleProtocol], rule: DocRuleProtocol) -> None:
        """Registers a rule by rule_id while merging or preserving multiple linter instances."""
        existing = registry.get(rule.rule_id)
        if existing is not None and isinstance(rule, DocLinterRule) and isinstance(existing, DocLinterRule):
            merged = cls._merge_linter_rules(existing, rule)
            key = rule.rule_id if merged is not None else cls._unique_rule_key(registry, rule.rule_id)
            registry[key] = merged if merged is not None else rule
            return
        registry[rule.rule_id] = rule

    @staticmethod
    def _unique_rule_key(registry: dict[str, DocRuleProtocol], rule_id: str) -> str:
        """Finds a collision-free slot key when multiple linters share the same rule_id."""
        idx = len(registry)
        while f"{rule_id}#{idx}" in registry:
            idx += 1
        return f"{rule_id}#{idx}"

    @staticmethod
    def _merge_linter_rules(existing: DocLinterRule, incoming: DocLinterRule) -> DocLinterRule | None:
        """Merges two CstLinter rules with matching severity into a single combined linter."""
        if (
            isinstance(existing.linter, CstLinter)
            and isinstance(incoming.linter, CstLinter)
            and existing.severity == incoming.severity
        ):
            excludes = sorted(existing.linter._excludes | incoming.linter._excludes)
            merged = CstLinter(rules=[*existing.linter.rules, *incoming.linter.rules], excludes=excludes)
            return DocLinterRule(linter=merged, severity=existing.severity)
        return None

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
        """Scans all loaded Markdown sources, checking rules on unexecuted broken steps too."""
        all_examples: list[ExtractedExample] = []
        for file_path, content in self._sources:
            examples, diags = self.pattern.scan(_MarkdownScanner(content).parse(), file_path)
            self._diagnostics.extend(diags)
            all_examples.extend(self._partition_executable(examples, diags))
        return all_examples

    def _partition_executable(
        self, examples: list[ExtractedExample], diags: list[DocDiagnostic]
    ) -> list[ExtractedExample]:
        """Runs static rules on structurally broken untagged steps while skipping arena execution."""
        broken = {d.line for d in diags if d.severity == "error"}
        executable: list[ExtractedExample] = []
        for ex in examples:
            if ex.session_id is None and ex.line in broken:
                self._diagnostics.extend(self._run_step_rules(ex, None, None))
            else:
                executable.append(ex)
        return executable

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
        if "\n" in stripped or stripped.startswith(_MD_PREFIXES) or "](" in stripped or "://" in stripped:
            return False
        if Path(stripped).exists() or stripped.lower().endswith((".md", ".markdown")):
            return True
        if " " not in stripped:
            return any(ch in stripped for ch in ("/", "\\", ".", "_", "-"))
        first = stripped.split()[0]
        return ("/" in first or "\\" in first) and not stripped.endswith((".", "!", "?"))

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
            stripped = excl.strip("/")
            if not stripped:
                continue
            norm = stripped.removeprefix(f"{root_name}/")
            if rel_posix == norm or rel_posix.startswith(f"{norm}/") or ("/" not in stripped and norm in rel_path.parts):
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
        include_linters = len(session.steps) <= 1
        for step, outcome in zip(session.steps, outcomes):
            outputs.append(outcome["output"])
            diags.extend(self._check_step_outcome(step, outcome, session.session_id, include_linters))
        if not include_linters:
            diags.extend(self._run_session_linters(session))
        passed = not self._has_errors(diags) and not self._has_structural_errors(session)
        return SessionTrace(session.session_id, tuple(outputs), passed), diags

    def _has_structural_errors(self, session: ExampleSession) -> bool:
        """Checks whether any step in the session already failed DOC-PRE or DOC-POST."""
        step_keys = {(s.file_path, s.line) for s in session.steps}
        return any(d.severity == "error" and (d.file_path, d.line) in step_keys for d in self._diagnostics)

    def _check_step_outcome(
        self, step: ExtractedExample, outcome: dict[str, Any], session_id: str, include_linters: bool = True
    ) -> list[DocDiagnostic]:
        """Evaluates runtime execution errors and dispatches all registered DocRuleProtocols."""
        step_diags: list[DocDiagnostic] = []
        if outcome["status"] in ("DOC-EXEC", "DOC-RAISE"):
            step_diags.append(
                DocDiagnostic(step.file_path, outcome["status"], step.line, outcome["error"], session_id)
            )
        actual_out = outcome["output"] if outcome["status"] == "OK" else None
        step_diags.extend(self._run_step_rules(step, actual_out, session_id, include_linters=include_linters))
        return step_diags

    def _run_step_rules(
        self, step: ExtractedExample, actual_out: str | None, session_id: str | None, *, include_linters: bool = True
    ) -> list[DocDiagnostic]:
        """Runs registered rules for a step and attaches the canonical session_id."""
        rules = self.rules if include_linters else [r for r in self.rules if not isinstance(r, DocLinterRule)]
        return [dataclasses.replace(d, session_id=session_id) for r in rules for d in r.check(step, actual_out)]

    def _run_session_linters(self, session: ExampleSession) -> list[DocDiagnostic]:
        """Runs DocLinterRules across combined session steps so cross-step definitions stay visible."""
        linters = [r for r in self.rules if isinstance(r, DocLinterRule)]
        valid = [s for s in session.steps if s.expected_raises != "SyntaxError"]
        broken = [s for s in session.steps if s.expected_raises == "SyntaxError"]
        diags = [dataclasses.replace(d, session_id=session.session_id) for r in linters for s in broken for d in r.check(s)]
        if len(valid) == 1:
            diags.extend(dataclasses.replace(d, session_id=session.session_id) for r in linters for d in r.check(valid[0]))
        elif len(valid) > 1:
            diags.extend(self._lint_joined_steps(linters, valid, session.session_id))
        return diags

    @classmethod
    def _lint_joined_steps(
        cls, linters: Sequence[DocLinterRule], steps: Sequence[ExtractedExample], session_id: str
    ) -> list[DocDiagnostic]:
        """Runs linters on concatenated session code and maps diagnostics back to each step."""
        ranges = cls._step_line_ranges(steps)
        joined = "\n".join(s.code for s in steps)
        return [cls._map_session_diag(r, d, ranges, session_id) for r in linters for d in r.linter.check(joined)]

    @staticmethod
    def _step_line_ranges(steps: Sequence[ExtractedExample]) -> list[tuple[int, int, ExtractedExample]]:
        """Computes 1-based inclusive line spans for each step in concatenated session code."""
        offset, ranges = 0, []
        for step in steps:
            span = step.code.count("\n") + 1
            ranges.append((offset + 1, offset + span, step))
            offset += span
        return ranges

    @staticmethod
    def _map_session_diag(
        rule: DocLinterRule, diag: LinterDiagnostic, ranges: list[tuple[int, int, ExtractedExample]], session_id: str
    ) -> DocDiagnostic:
        """Maps a diagnostic from concatenated session code back to its owning Markdown step."""
        start, _, owner = next(((s, e, ex) for s, e, ex in ranges if s <= diag.line <= e), ranges[-1])
        local = dataclasses.replace(diag, line=max(1, diag.line - start + 1))
        return dataclasses.replace(rule._map_diagnostic(owner, local), session_id=session_id)