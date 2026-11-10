import dataclasses
import json
import math
import os
from pathlib import Path
import re
import tempfile
import types
from typing import Dict, List

from .protocols import EvaluationTrace, ReviewData, RunTrace, UNSPECIFIED
from ._execution import exception_details, qualified_name

# ========== PYTEST REPORTER ===========================================================================================

@dataclasses.dataclass(frozen=True)
class ReportContext:
    verbosity: int
    max_diff_items: int
class PytestReporter:
    """
    Consumes EBT or RBT results and delegates failures via standard assertions.
    """
    def __init__(self, verbosity: int = 1, max_diff_items: int = 5):
        self.verbosity = verbosity
        self.max_diff_items = max_diff_items

    # ---------- SERVICES ----------------------------------------------------------------------------------------------

    def report(self, trace: RunTrace | ReviewData) -> None:
        """Evaluates the final run status and raises an assertion with formatted trace details on failure."""
        __tracebackhide__ = True
        if isinstance(trace, ReviewData):
            assert trace.passed, self._generate_review_report(trace)
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

    def _generate_report(
            self,
            run_trace: RunTrace,
            ctx: ReportContext
    ) -> str:
        """Determines which step caused the failure and initiates the string formatting."""
        __tracebackhide__ = True
        if not run_trace.traces: return f"EBT-Assert failed: Run '{run_trace.run_id}' completed without traces."
        steps = self._group_traces_by_step(run_trace.traces)
        if run_trace.expect:
            target_id = next(
                (sid for sid, tr in steps.items() if not self._evaluate_step_logic(tr)),
                next(iter(steps))
            )
        else: target_id = next(iter(steps))
        return self._build_report_message(target_id, steps[target_id], run_trace.expect, ctx)

    @staticmethod
    def _group_traces_by_step(traces: List[EvaluationTrace]) -> Dict[str, List[EvaluationTrace]]:
        """Groups all recorded traces by their execution step ID."""
        __tracebackhide__ = True
        steps: Dict[str, List[EvaluationTrace]] = {}
        for t in traces: steps.setdefault(t.step_id, []).append(t)
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
            self,
            step_id: str,
            traces: List[EvaluationTrace],
            expect: bool,
            ctx: ReportContext
    ) -> str:
        """Constructs a detailed error string, exposing all evaluated quantifier states."""
        __tracebackhide__ = True
        prefix = "EBT-Assert failed" if expect else "EBT-Negative-Assert failed"
        lines = [f"{prefix} for step '{step_id}':", f"Target: {traces[0].target}"]
        for idx, t in enumerate(traces): lines.extend(self._format_trace_details(idx, t, ctx))
        return "\n".join(lines)

    @staticmethod
    def _format_trace_details(
            idx: int,
            t: EvaluationTrace,
            ctx: ReportContext
    ) -> List[str]:
        """Formats the detailed property comparisons leveraging the pre-calculated diffs."""
        __tracebackhide__ = True
        lines = [f"  [Q-State {idx}] Validation: {'Matched' if t.evaluation else 'Mismatch'}"]
        diffs = t.diffs or {}
        if t.post.returns is not UNSPECIFIED:
            match = "Mismatch" if "returns" in diffs else "Match"
            returns_str = PytestReporter._format_returns(t.post.returns, t.outcome.returns, ctx)
            lines.append(f"    - Returns: {returns_str} ({match})")
        if t.post.raises is not None or t.outcome.exception is not None:
            expected = t.post.raises
            expected_text = (
                f"{qualified_name(expected.exception_type)} | Message pattern {expected.match!r}"
                if expected is not None else "normal return"
            )
            actual = exception_details(t.outcome.exception)
            actual_text = f"{actual['type']}: {actual['message']}" if actual else "normal return"
            match = "Mismatch" if "raises" in diffs else "Match"
            lines.append(f"    - Raises: Expected {expected_text} | Actual {actual_text} ({match})")
        if t.post.fs: lines.extend(PytestReporter._build_diff_section("FS", "fs", diffs, ctx))
        if t.post.arena: lines.extend(PytestReporter._build_diff_section("Arena", "arena", diffs, ctx))
        return lines

    @staticmethod
    def _format_returns(expected, actual, ctx: ReportContext) -> str:
        """Formats expected and actual returns, truncating large lists based on max_diff_items."""
        __tracebackhide__ = True

        def format_val(val):
            if isinstance(val, (list, tuple)) and len(val) > ctx.max_diff_items:
                head = list(val[:ctx.max_diff_items])
                return f"{head} ... [and {len(val) - ctx.max_diff_items} more items]"
            return str(val)

        return f"Expected {format_val(expected)} | Actual {format_val(actual)}"

    # ---------- DIFF FORMATTING ---------------------------------------------------------------------------------------

    @staticmethod
    def _build_diff_section(
            label: str,
            diff_key: str,
            diffs: dict,
            ctx: ReportContext
    ) -> List[str]:
        """Routes the diff section rendering based on matches and verbosity."""
        __tracebackhide__ = True
        if diff_key not in diffs: return [f"    - {label}: Match"]
        lines = [f"    - {label}: Mismatch"]
        section_diff = diffs[diff_key]
        if isinstance(section_diff, dict) and isinstance(section_diff.get("error"), str):
            return lines + [f"      Error: {section_diff['error']}"]
        if diff_key == "fs" and isinstance(section_diff, dict):
            section_diff, errors = PytestReporter._summarize_fs_diffs(section_diff)
            lines.extend(errors)
            # A failed comparison does not establish zero file differences.
            if not any(section_diff.values()):
                return lines
        if ctx.verbosity >= 1 and isinstance(section_diff, dict):
            lines.extend(PytestReporter._format_aggregate(section_diff))
            lines.extend(PytestReporter._format_items(section_diff, ctx))
        return lines

    @staticmethod
    def _summarize_fs_diffs(scoped_diffs: dict) -> tuple[dict[str, list[str]], list[str]]:
        """Aggregate scoped records without accessing expired workspace/reference paths."""
        changes = {category: set() for category in ("missing", "unexpected", "modified")}
        errors = []
        for scope, diff in sorted(scoped_diffs.items(), key=lambda item: str(item[0])):
            if "error" in diff:
                errors.append(f"      Error: {os.path.normpath(str(scope))}: {diff['error']}")
            for category, paths in changes.items():
                paths.update(os.path.normpath(os.path.join(str(scope), str(name)))
                             for name in diff.get(category, []))
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
        lines = [f"        {c}" for c in changes[:ctx.max_diff_items]]
        if len(changes) > ctx.max_diff_items: lines.append(f"        ... and {len(changes) - ctx.max_diff_items} more.")
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
    """Persist one completed EBT run as versioned UTF-8 JSON, without asserting.

    Paths and evidence are recorded from the trace; no workspace/reference files
    are reopened. Patterns and opaque objects are descriptions, never executable
    serialized payloads. Use distinct paths to retain multiple runs.
    """

    def __init__(self, path: str | os.PathLike):
        self.path = Path(path)

    def report(self, trace: RunTrace, /) -> None:
        if not isinstance(trace, RunTrace):
            raise TypeError("JsonReporter requires a RunTrace.")
        document = {
            "schema_version": 1, "run_id": trace.run_id, "target": trace.target,
            "expect": trace.expect, "evaluation": trace.evaluation, "duration": trace.duration,
            "arena": self._value(trace.arena),
            "traces": [self._trace(item) for item in trace.traces or []],
        }
        payload = json.dumps(document, ensure_ascii=True, allow_nan=False, indent=2) + "\n"
        # Serialize before touching the destination and replace only a complete
        # file. A failed write must not truncate an earlier report.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix=f".{self.path.name}.", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(payload)
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @classmethod
    def _trace(cls, trace: EvaluationTrace) -> dict:
        return {
            "step_id": trace.step_id, "target": trace.target,
            "evaluation": trace.evaluation, "duration": trace.duration,
            "pre": cls._state(trace.pre), "post": cls._state(trace.post, patterns=True),
            "outcome": cls._state(trace.outcome),
            "diffs": cls._data(trace.diffs),
        }

    @classmethod
    def _state(cls, state, *, patterns: bool = False) -> dict:
        return {
            "args": cls._value(state.args), "kwargs": cls._value(state.kwargs),
            "arena": cls._value(state.arena), "fs": cls._value(state.fs, patterns=patterns),
            "returns": cls._value(state.returns, patterns=patterns), "expect": state.expect,
            "raises": ({"type": qualified_name(state.raises.exception_type), "match": state.raises.match}
                       if state.raises is not None else None),
            "exception": exception_details(state.exception),
        }

    @staticmethod
    def _description(value) -> str:
        try:
            return repr(value)[:2000]
        except Exception:  # noqa: BLE001 -- diagnostics must tolerate a broken user __repr__
            return "<description unavailable>"

    @classmethod
    def _value(cls, value, active=None, *, patterns: bool = False) -> dict:
        if value is UNSPECIFIED:
            return {"kind": "unspecified"}
        type_name = qualified_name(type(value))
        if patterns and (isinstance(value, (type, re.Pattern, types.UnionType)) or callable(value)):
            return {"kind": "pattern", "type": type_name, "description": cls._description(value)}
        node = {"kind": "value", "type": type_name}
        if value is None or type(value) in (bool, int, str):
            return {**node, "value": value}
        if type(value) is float and math.isfinite(value):
            return {**node, "value": value}
        if isinstance(value, Path):
            return {**node, "value": str(value)}
        active = set() if active is None else active
        if id(value) in active:
            return {"kind": "cycle", "type": type_name}
        active.add(id(value))
        try:
            if isinstance(value, dict):
                if all(type(key) is str for key in value):
                    content = {key: cls._value(item, active, patterns=patterns) for key, item in value.items()}
                else:
                    content = [[cls._value(key, active), cls._value(item, active, patterns=patterns)]
                               for key, item in value.items()]
                return {**node, "value": content}
            if isinstance(value, (list, tuple, set, frozenset)):
                content = [cls._value(item, active, patterns=patterns) for item in value]
                if isinstance(value, (set, frozenset)):
                    content.sort(key=lambda item: json.dumps(item, sort_keys=True))
                return {**node, "value": content}
            if isinstance(value, Exception):
                return {**node, "value": exception_details(value)}
            return {"kind": "description", "type": type_name, "description": cls._description(value)}
        finally:
            active.remove(id(value))

    @classmethod
    def _data(cls, value, active=None):
        """Keep diff paths/categories directly readable; tag non-JSON leaf values."""
        if value is None or type(value) in (bool, int, str):
            return value
        if type(value) is float and math.isfinite(value):
            return value
        active = set() if active is None else active
        if id(value) in active:
            return {"kind": "cycle", "type": qualified_name(type(value))}
        active.add(id(value))
        try:
            if isinstance(value, dict) and all(type(key) is str for key in value):
                return {key: cls._data(item, active) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [cls._data(item, active) for item in value]
            return cls._value(value)
        finally:
            active.remove(id(value))
