from __future__ import annotations

import dataclasses
import json
import math
import os
from pathlib import Path
import re
import tempfile
import types
from typing import TYPE_CHECKING, Dict, List

from .protocols import EvaluationTrace, ReviewData, RunTrace, UNSPECIFIED
from ._execution import exception_details, qualified_name

if TYPE_CHECKING:
    from .services.protocols import ServiceReportProtocol

# ========== PYTEST REPORTER ===========================================================================================


@dataclasses.dataclass(frozen=True)
class ReportContext:
    verbosity: int
    max_diff_items: int


class PytestReporter:
    """Consumes EBT or RBT results and delegates failures via standard assertions."""

    def __init__(self, verbosity: int = 1, max_diff_items: int = 5):
        self.verbosity = verbosity
        self.max_diff_items = max_diff_items

    # ---------- SERVICES ----------------------------------------------------------------------------------------------

    def report(self, trace: RunTrace | ReviewData | ServiceReportProtocol) -> None:
        """Evaluates the final run status and raises an assertion with formatted trace details on failure."""
        __tracebackhide__ = True
        if isinstance(trace, ReviewData):
            assert trace.passed, self._generate_review_report(trace)
            return
        if not isinstance(trace, RunTrace):
            assert trace.passed, self._generate_service_report(trace)
            return
        if trace.evaluation is False:
            ctx = ReportContext(verbosity=self.verbosity, max_diff_items=self.max_diff_items)
            report_msg = self._generate_report(trace, ctx)
            assert False, report_msg

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------

    @staticmethod
    def _generate_review_report(result: ReviewData) -> str:
        """Formats review diagnostics for a failed run."""
        lines = ["\n--- Report ---"]
        lines.extend(f"- {key}: {value}" for key, value in result.report.items())
        return "\n".join(lines)

    @staticmethod
    def _generate_service_report(result: ServiceReportProtocol) -> str:
        """Formats diagnostics for a failed service run (e.g. DocEnsurance)."""
        lines = [f"\n--- Service Report ({result.target}) ---"]
        lines.extend(
            f"- [{d.rule_id}] {d.file_path}:{d.line}: {d.message}"
            for d in result.diagnostics
        )
        return "\n".join(lines)

    def _generate_report(self, run_trace: RunTrace, ctx: ReportContext) -> str:
        """Determines which step caused the failure and initiates the string formatting."""
        __tracebackhide__ = True
        if not run_trace.traces:
            return f"EBT-Assert failed: Run '{run_trace.run_id}' completed without traces."
        steps = self._group_traces_by_step(run_trace.traces)
        if run_trace.expect:
            target_id = next((sid for sid, tr in steps.items() if not self._evaluate_step_logic(tr)), next(iter(steps)))
        else:
            target_id = next(iter(steps))
        return self._build_report_message(target_id, steps[target_id], run_trace.expect, ctx)

    @staticmethod
    def _group_traces_by_step(traces: List[EvaluationTrace]) -> Dict[str, List[EvaluationTrace]]:
        """Groups all recorded traces by their execution step ID."""
        __tracebackhide__ = True
        steps: Dict[str, List[EvaluationTrace]] = {}
        for t in traces:
            steps.setdefault(t.step_id, []).append(t)
        return steps

    @staticmethod
    def _evaluate_step_logic(traces: List[EvaluationTrace]) -> bool:
        """Evaluates the boolean success of a single step based on positive and negative states."""
        __tracebackhide__ = True
        positives = [t for t in traces if t.post.expect]
        negatives = [t for t in traces if not t.post.expect]
        violates_neg = any(t.evaluation for t in negatives)
        satisfies_pos = any(t.evaluation for t in positives) if positives else True
        return satisfies_pos and not violates_neg

    def _build_report_message(
        self, step_id: str, traces: List[EvaluationTrace], expect: bool, ctx: ReportContext
    ) -> str:
        """Constructs a detailed error string, exposing all evaluated quantifier states."""
        __tracebackhide__ = True
        prefix = "EBT-Assert failed" if expect else "EBT-Negative-Assert failed"
        lines = [f"{prefix} for step '{step_id}':", f"Target: {traces[0].target}"]
        for idx, t in enumerate(traces):
            lines.extend(self._format_trace_details(idx, t, ctx))
        return "\n".join(lines)

    @staticmethod
    def _format_trace_details(idx: int, t: EvaluationTrace, ctx: ReportContext) -> List[str]:
        """Format the result and property comparisons for one evaluated state."""
        __tracebackhide__ = True
        lines = [f"  [Q-State {idx}] Validation: {'Matched' if t.evaluation else 'Mismatch'}"]
        diffs = t.diffs or {}
        if t.post.returns is not UNSPECIFIED:
            lines.extend(PytestReporter._return_section(t, ctx, diffs))
        if t.post.raises is not None or t.outcome.exception is not None:
            lines.extend(PytestReporter._exception_section(t, diffs))
        if t.post.fs:
            lines.extend(PytestReporter._build_diff_section("FS", "fs", diffs, ctx))
        if t.post.arena:
            lines.extend(PytestReporter._build_diff_section("Arena", "arena", diffs, ctx))
        return lines

    @staticmethod
    def _return_section(trace: EvaluationTrace, ctx: ReportContext, diffs: dict) -> list[str]:
        match = "Mismatch" if "returns" in diffs else "Match"
        returns = PytestReporter._format_returns(trace.post.returns, trace.outcome.returns, ctx)
        return [f"    - Returns: {returns} ({match})"]

    @staticmethod
    def _exception_section(trace: EvaluationTrace, diffs: dict) -> list[str]:
        expected = trace.post.raises
        expected_text = (
            f"{qualified_name(expected.exception_type)} | Message pattern {expected.match!r}"
            if expected is not None else "normal return"
        )
        actual = exception_details(trace.outcome.exception)
        actual_text = f"{actual['type']}: {actual['message']}" if actual else "normal return"
        match = "Mismatch" if "raises" in diffs else "Match"
        return [f"    - Raises: Expected {expected_text} | Actual {actual_text} ({match})"]

    @staticmethod
    def _format_returns(expected, actual, ctx: ReportContext) -> str:
        """Formats expected and actual returns, truncating large lists based on max_diff_items."""
        __tracebackhide__ = True

        def format_val(val):
            if isinstance(val, (list, tuple)) and len(val) > ctx.max_diff_items:
                head = list(val[: ctx.max_diff_items])
                return f"{head} ... [and {len(val) - ctx.max_diff_items} more items]"
            return str(val)

        return f"Expected {format_val(expected)} | Actual {format_val(actual)}"

    # ---------- DIFF FORMATTING ---------------------------------------------------------------------------------------

    @staticmethod
    def _build_diff_section(label: str, diff_key: str, diffs: dict, ctx: ReportContext) -> List[str]:
        """Render a filesystem or arena comparison at the requested verbosity."""
        __tracebackhide__ = True
        if diff_key not in diffs:
            return [f"    - {label}: Match"]
        return [f"    - {label}: Mismatch"] + PytestReporter._section_details(diff_key, diffs[diff_key], ctx)

    @staticmethod
    def _section_details(key: str, section, ctx: ReportContext) -> list[str]:
        if isinstance(section, dict) and isinstance(section.get("error"), str):
            return [f"      Error: {section['error']}"]
        lines: list[str] = []
        if key == "fs" and isinstance(section, dict):
            section, errors = PytestReporter._summarize_fs_diffs(section)
            lines.extend(errors)
            if not any(section.values()):
                return lines
        if ctx.verbosity >= 1 and isinstance(section, dict):
            lines.extend(PytestReporter._format_aggregate(section))
            lines.extend(PytestReporter._format_items(section, ctx))
        return lines

    @staticmethod
    def _summarize_fs_diffs(scoped_diffs: dict) -> tuple[dict[str, list[str]], list[str]]:
        """Aggregate scoped records without accessing expired workspace/reference paths."""
        changes: dict[str, set[str]] = {category: set() for category in ("missing", "unexpected", "modified")}
        errors = []
        for scope, diff in sorted(scoped_diffs.items(), key=lambda item: str(item[0])):
            if "error" in diff:
                errors.append(f"      Error: {os.path.normpath(str(scope))}: {diff['error']}")
            for category, paths in changes.items():
                paths.update(os.path.normpath(os.path.join(str(scope), str(name))) for name in diff.get(category, []))
        return {category: sorted(paths) for category, paths in changes.items()}, errors

    @staticmethod
    def _format_aggregate(section_diff: dict) -> List[str]:
        """Formats the high-level counts for missing, unexpected, and modified files."""
        __tracebackhide__ = True
        missing = len(section_diff.get("missing", []))
        unexpected = len(section_diff.get("unexpected", []))
        modified = len(section_diff.get("modified", []))
        return [f"      Details: -{missing} Missing | +{unexpected} Unexpected | ~{modified} Modified"]

    @staticmethod
    def _format_items(section_diff: dict, ctx: ReportContext) -> List[str]:
        """Formats the concrete file paths up to the configured limits."""
        __tracebackhide__ = True
        changes = PytestReporter._collect_changes(section_diff)
        lines = [f"        {c}" for c in changes[: ctx.max_diff_items]]
        if len(changes) > ctx.max_diff_items:
            lines.append(f"        ... and {len(changes) - ctx.max_diff_items} more.")
        return lines

    @staticmethod
    def _collect_changes(section_diff: dict) -> List[str]:
        """Extracts and prefixes all file changes into a flat list."""
        __tracebackhide__ = True
        changes = [f"- {item}" for item in section_diff.get("missing", [])]
        changes.extend([f"+ {item}" for item in section_diff.get("unexpected", [])])
        changes.extend([f"~ {item}" for item in section_diff.get("modified", [])])
        return changes


# ========== JSON REPORTER =============================================================================================


class JsonReporter:
    """Persist one completed EBT run as versioned UTF-8 JSON, without asserting."""

    # Paths and evidence are recorded from the trace; no workspace/reference files
    # are reopened. Patterns and opaque objects are descriptions, never executable
    # serialized payloads. Use distinct paths to retain multiple runs.

    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)

    def report(self, trace: RunTrace, /) -> None:
        if not isinstance(trace, RunTrace):
            raise TypeError("JsonReporter requires a RunTrace.")
        payload = json.dumps(self._document(trace), ensure_ascii=True, allow_nan=False, indent=2) + "\n"
        self._write(payload)

    def _document(self, trace: RunTrace) -> dict:
        return {
            "schema_version": 1, "run_id": trace.run_id, "target": trace.target,
            "expect": trace.expect, "evaluation": trace.evaluation, "duration": trace.duration,
            "arena": self._value(trace.arena),
            "traces": [self._trace(item) for item in trace.traces or []],
        }

    def _write(self, payload: str) -> None:
        # Replace the destination only after serialization and a complete write.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, prefix=f".{self.path.name}.", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @classmethod
    def _trace(cls, trace: EvaluationTrace) -> dict:
        return {
            "step_id": trace.step_id,
            "target": trace.target,
            "evaluation": trace.evaluation,
            "duration": trace.duration,
            "pre": cls._state(trace.pre),
            "post": cls._state(trace.post, patterns=True),
            "outcome": cls._state(trace.outcome),
            "diffs": cls._data(trace.diffs),
        }

    @classmethod
    def _state(cls, state, *, patterns: bool = False) -> dict:
        return {
            "args": cls._value(state.args), "kwargs": cls._value(state.kwargs),
            "arena": cls._value(state.arena), "fs": cls._value(state.fs, patterns=patterns),
            "returns": cls._value(state.returns, patterns=patterns), "expect": state.expect,
            "raises": cls._raises(state), "exception": exception_details(state.exception),
        }

    @staticmethod
    def _raises(state) -> dict | None:
        if state.raises is None:
            return None
        return {"type": qualified_name(state.raises.exception_type), "match": state.raises.match}

    @staticmethod
    def _description(value) -> str:
        try:
            return repr(value)[:2000]
        except Exception:  # noqa: BLE001 -- diagnostics must tolerate a broken user __repr__
            return "<description unavailable>"

    @classmethod
    def _value(cls, value, active=None, *, patterns: bool = False) -> dict:
        simple = cls._simple_value(value, patterns)
        if simple is not None:
            return simple
        active = set() if active is None else active
        if id(value) in active:
            return {"kind": "cycle", "type": qualified_name(type(value))}
        active.add(id(value))
        try:
            return cls._structured_value(value, active, patterns)
        finally:
            active.remove(id(value))

    @classmethod
    def _simple_value(cls, value, patterns: bool) -> dict | None:
        if value is UNSPECIFIED:
            return {"kind": "unspecified"}
        type_name = qualified_name(type(value))
        if patterns and (isinstance(value, (type, re.Pattern, types.UnionType)) or callable(value)):
            return {"kind": "pattern", "type": type_name, "description": cls._description(value)}
        node = {"kind": "value", "type": type_name}
        if cls._literal(value):
            return {**node, "value": value}
        if isinstance(value, Path):
            return {**node, "value": str(value)}
        return None

    @staticmethod
    def _literal(value) -> bool:
        return value is None or type(value) in (bool, int, str) or (type(value) is float and math.isfinite(value))

    @classmethod
    def _structured_value(cls, value, active, patterns: bool) -> dict:
        node = {"kind": "value", "type": qualified_name(type(value))}
        if isinstance(value, dict):
            return {**node, "value": cls._mapping_value(value, active, patterns)}
        if isinstance(value, (list, tuple, set, frozenset)):
            return {**node, "value": cls._sequence_value(value, active, patterns)}
        if isinstance(value, Exception):
            return {**node, "value": exception_details(value)}
        return {"kind": "description", "type": node["type"], "description": cls._description(value)}

    @classmethod
    def _mapping_value(cls, value: dict, active, patterns: bool):
        if all(type(key) is str for key in value):
            return {key: cls._value(item, active, patterns=patterns) for key, item in value.items()}
        return [
            [cls._value(key, active), cls._value(item, active, patterns=patterns)]
            for key, item in value.items()
        ]

    @classmethod
    def _sequence_value(cls, value, active, patterns: bool) -> list:
        content = [cls._value(item, active, patterns=patterns) for item in value]
        if isinstance(value, (set, frozenset)):
            content.sort(key=lambda item: json.dumps(item, sort_keys=True))
        return content

    @classmethod
    def _data(cls, value, active=None):
        """Keep diff paths readable and describe non-JSON leaf values."""
        if cls._literal(value):
            return value
        active = set() if active is None else active
        if id(value) in active:
            return {"kind": "cycle", "type": qualified_name(type(value))}
        active.add(id(value))
        try:
            return cls._data_content(value, active)
        finally:
            active.remove(id(value))

    @classmethod
    def _data_content(cls, value, active):
        if isinstance(value, dict) and all(type(key) is str for key in value):
            return {key: cls._data(item, active) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._data(item, active) for item in value]
        return cls._value(value)
