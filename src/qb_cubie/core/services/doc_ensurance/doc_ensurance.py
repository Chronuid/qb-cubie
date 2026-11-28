"""Tries to verify structural conventions and runtime outputs of documentation code examples."""

from __future__ import annotations

import contextlib
import dataclasses
import io
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from ...arenas.tempfs import TempFS
from ...linter import CstLinter, LinterDiagnostic
from ...protocols import Arena, DiagnosticProtocol, FileCheckProtocol, Reporter, WorldState
from ...reporter import PytestReporter
from ...service_core.guards import validate_positive_float
from ...service_core.rules import RuleRegistry, WorkspaceCheckRuleProtocol, execute_file_checks
from ...service_core.workspace import FileSource, find_project_root, normalize_excludes
from ._markdown_scanner import _MarkdownScanner
from .adapters import resolve_sources
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
from .doc_rules import DocRuleSet
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

_DEFAULT_REPORTER: Final[PytestReporter] = PytestReporter()
_RuleEntry = DocRuleProtocol | WorkspaceCheckRuleProtocol | FileCheckProtocol


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
        pattern: DocPatternProtocol | Sequence[Any] | None = None,
        scope: DocScopeProtocol | None = None,
        arena: Arena | None = None,
        reporter: Reporter[DocReport] | None = _DEFAULT_REPORTER,
        pre_state: WorldState | None = None,
        excludes: Sequence[str] | None = None,
        rules: Sequence[Any] | None = None,
        *,
        timeout: float | None = 10.0,
    ) -> None:
        """Initializes the documentation verification service with default project conventions."""
        self.timeout = validate_positive_float(timeout, "timeout", allow_none=True)
        self.target: str | Path = target if target is not None else find_project_root()
        self.pattern, self._extra_patterns = self._normalize_patterns(pattern)
        self.scope = scope or TaggedScope()
        self.arena = self._configure_arena(arena, self.timeout)
        self.reporter = reporter
        self.pre_state = pre_state or WorldState()
        self.excludes = set(normalize_excludes(excludes))
        self.rules: list[_RuleEntry] = self._build_rules(self.pattern, rules)
        self._reset_state()

    def register_rule(self, *rules: Any) -> DocEnsurance:
        """Registers or overrides one or more check rules without muting orthogonal linters."""
        registry = RuleRegistry(self.rules, coerce=self._coerce_rule, merge=self._merge_doc_rule)
        registry.register(*self._unpack_rule_sets(rules))
        if any(r.rule_id == "DOC-NO-OUTPUT" for r in registry.rules):
            registry.remove("DOC-OUT-MISSING")
        self.rules = list(registry.rules)
        return self

    @classmethod
    def _build_rules(
        cls, pattern: DocPatternProtocol, custom: Sequence[Any] | None
    ) -> list[_RuleEntry]:
        """Merges default rules, pattern block rules, and user-provided rules without silent muting."""
        explicit_empty = custom is not None and len(custom) == 0
        defaults = (OutputMatchRule(severity="error"),) if explicit_empty else DEFAULT_DOC_RULES
        registry = RuleRegistry(defaults, coerce=cls._coerce_rule, merge=cls._merge_doc_rule)
        registry.register(*cls._extract_pattern_rules(pattern), *cls._unpack_rule_sets(custom or ()))
        if any(r.rule_id == "DOC-NO-OUTPUT" for r in registry.rules):
            registry.remove("DOC-OUT-MISSING")
        return list(registry.rules)

    @classmethod
    def _unpack_rule_sets(cls, items: Sequence[Any]) -> list[Any]:
        """Expand DocRuleSet containers into their underlying rule entries."""
        unpacked: list[Any] = []
        for item in items:
            if isinstance(item, DocRuleSet):
                unpacked.extend(item.rules)
            elif isinstance(item, (list, tuple)):
                unpacked.extend(cls._unpack_rule_sets(item))
            else:
                unpacked.append(item)
        return unpacked

    @staticmethod
    def _normalize_patterns(raw: Any) -> tuple[DocPatternProtocol, tuple[DocPatternProtocol, ...]]:
        """Validates pattern inputs and returns the primary scanner plus all patterns."""
        if raw is None:
            return CUBIE_DOC_STYLE, ()
        items = list(raw) if isinstance(raw, (list, tuple)) else [raw]
        if not all(isinstance(p, DocPatternProtocol) for p in items):
            raise TypeError("STATE-GUARD: Invalid pattern item passed to DocEnsurance.")
        primary = next((p for p in items if hasattr(p, "anchor")), items[0] if items else CUBIE_DOC_STYLE)
        return primary, tuple(items)

    @classmethod
    def _merge_doc_rule(cls, existing: _RuleEntry, incoming: _RuleEntry) -> _RuleEntry | None:
        """Merge compatible CstLinter rules, coexist differing linters, or override regular rules."""
        if isinstance(existing, DocLinterRule) and isinstance(incoming, DocLinterRule):
            return cls._merge_linter_rules(existing, incoming)
        return incoming

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
        self._diagnostics: list[DiagnosticProtocol] = []
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
    def _coerce_rule(item: Any) -> _RuleEntry:
        """Normalizes rule classes, Linter instances, WorkspaceCheckRuleProtocol, FileCheckProtocol, and DocRuleProtocol."""
        instance = item() if isinstance(item, type) else item
        if isinstance(instance, (DocRuleProtocol, WorkspaceCheckRuleProtocol, FileCheckProtocol)):
            return instance
        if hasattr(instance, "check") and hasattr(instance, "name"):
            return DocLinterRule(linter=instance)
        raise TypeError(
            f"STATE-GUARD: Rule must implement DocRuleProtocol or Linter; received {type(instance).__name__}."
        )

    @staticmethod
    def _configure_arena(arena: Arena | None, timeout: float | None) -> Arena:
        """Builds a default TempFS with the TTL timeout or applies it to an unconfigured arena."""
        if arena is None:
            return TempFS(timeout=timeout)
        if timeout is not None and getattr(arena, "timeout", None) is None:
            setattr(arena, "timeout", timeout)  # noqa: B010
        return arena

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
        self._sources = resolve_sources(self.target, self.excludes)
        all_examples = self._scan_all_sources()
        self._sessions = self.scope.group(all_examples)

    def _scan_all_sources(self) -> list[ExtractedExample]:
        """Scans all loaded Markdown sources, checking file-level rules and code examples."""
        self._run_file_rules()
        all_examples: list[ExtractedExample] = []
        for file_path, content in self._sources:
            examples, diags = self.pattern.scan(_MarkdownScanner(content).parse(), file_path)
            self._diagnostics.extend(diags)
            all_examples.extend(self._partition_executable(examples, diags))
        return all_examples

    def _run_file_rules(self) -> None:
        """Executes registered WorkspaceCheckRuleProtocol and FileCheckProtocol rules across file sources."""
        file_rules: list[WorkspaceCheckRuleProtocol | FileCheckProtocol] = [
            r for r in self.rules if isinstance(r, (WorkspaceCheckRuleProtocol, FileCheckProtocol))
        ]
        if not file_rules or not self._sources or self._sources[0][0] == "IN_MEMORY":
            return
        file_sources = [FileSource(path=fp, rel_path=Path(fp).name, content=txt) for fp, txt in self._sources]
        options = {"target": self.target, "excludes": tuple(self.excludes), "patterns": self._extra_patterns}
        diags = execute_file_checks(file_rules, file_sources, target=self.target, excludes=self.excludes, options=options)
        self._diagnostics.extend(diags)

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
    def _has_errors(diags: Sequence[DiagnosticProtocol]) -> bool:
        """Checks whether any recorded diagnostic has error severity."""
        return any(d.severity == "error" for d in diags)

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------
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
        step_rules = [r for r in self.rules if isinstance(r, DocRuleProtocol)]
        rules = step_rules if include_linters else [r for r in step_rules if not isinstance(r, DocLinterRule)]
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