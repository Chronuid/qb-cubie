from typing import List, Dict
from ebt import RunTrace, EvaluationTrace

# ========== PYTEST REPORTER ===========================================================================================

class PytestReporter:
    """
    Consumes a RunTrace and delegates failures to Pytest via standard assertions.
    """
    def report(self, trace: RunTrace) -> None:
        """Evaluates the final run status and raises an assertion with formatted trace details on failure."""
        __tracebackhide__ = True
        if trace.evaluation is False:
            report_msg = self._generate_report(trace)
            assert False, report_msg

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------

    def _generate_report(self, run_trace: RunTrace) -> str:
        """Determines which step caused the failure and initiates the string formatting."""
        __tracebackhide__ = True
        if not run_trace.traces: return f"EBT-Assert failed: Run '{run_trace.run_id}' completed without traces."
        steps = self._group_traces_by_step(run_trace.traces)
        if run_trace.expect: target_id = next(
            (sid for sid, tr in steps.items() if not self._evaluate_step_logic(tr)),
            next(iter(steps))
        )
        else: target_id = next(iter(steps))
        return self._build_report_message(target_id, steps[target_id], run_trace.expect)

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

    def _build_report_message(self, step_id: str, traces: List[EvaluationTrace], expect: bool) -> str:
        """Constructs a detailed error string, exposing all evaluated quantifier states."""
        __tracebackhide__ = True
        prefix = "EBT-Assert failed" if expect else "EBT-Negative-Assert failed"
        lines = [f"{prefix} for step '{step_id}':", f"Target: {traces[0].target}"]
        for idx, t in enumerate(traces): lines.extend(self._format_trace_details(idx, t))
        return "\n".join(lines)

    @staticmethod
    def _format_trace_details(idx: int, t: EvaluationTrace) -> List[str]:
        """Formats the detailed property comparisons leveraging the pre-calculated diffs."""
        __tracebackhide__ = True
        lines = [f"  [Q-State {idx}] Validation: {'Matched' if t.evaluation else 'Mismatch'}"]
        diffs = t.diffs or {}
        if t.post.returns is not None:
            match = "Mismatch" if "returns" in diffs else "Match"
            lines.append(f"    - Returns: Expected {t.post.returns} | Actual {t.outcome.returns} ({match})")
        if t.post.fs:
            match = "Mismatch" if "fs" in diffs else "Match"
            lines.append(f"    - FS: Expected {t.post.fs} | Actual {t.outcome.fs} ({match})")
        if t.post.arena:
            match = "Mismatch" if "arena" in diffs else "Match"
            expected = getattr(t.post.arena, "env_path", t.post.arena)
            lines.append(f"    - Arena: Expected {expected} | Actual {t.outcome.arena} ({match})")
        return lines