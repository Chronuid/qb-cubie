import dataclasses
from typing import List, Dict
from .ebt import RunTrace, EvaluationTrace


# ========== PYTEST REPORTER ===========================================================================================

@dataclasses.dataclass(frozen=True)
class ReportContext:
    verbosity: int
    max_diff_items: int
class PytestReporter:
    """
    Consumes a RunTrace and delegates failures to Pytest via standard assertions.
    """
    def __init__(self, verbosity: int = 1, max_diff_items: int = 5):
        self.verbosity = verbosity
        self.max_diff_items = max_diff_items

    # ---------- SERVICES ----------------------------------------------------------------------------------------------

    def report(self, trace: RunTrace) -> None:
        """Evaluates the final run status and raises an assertion with formatted trace details on failure."""
        __tracebackhide__ = True
        if trace.evaluation is False:
            ctx = ReportContext(verbosity=self.verbosity, max_diff_items=self.max_diff_items)
            report_msg = self._generate_report(trace, ctx)
            assert False, report_msg

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------

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
        if t.post.returns is not None:
            match = "Mismatch" if "returns" in diffs else "Match"
            lines.append(f"    - Returns: Expected {t.post.returns} | Actual {t.outcome.returns} ({match})")
        if t.post.fs: lines.extend(PytestReporter._build_diff_section("FS", "fs", diffs, ctx))
        if t.post.arena: lines.extend(PytestReporter._build_diff_section("Arena", "arena", diffs, ctx))
        return lines

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
        if isinstance(section_diff, dict) and "error" in section_diff:
            return lines + [f"      Error: {section_diff['error']}"]
        if ctx.verbosity >= 1 and isinstance(section_diff, dict):
            lines.extend(PytestReporter._format_aggregate(section_diff))
            lines.extend(PytestReporter._format_items(section_diff, ctx))
        return lines

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