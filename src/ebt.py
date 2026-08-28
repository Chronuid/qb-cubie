import filecmp, inspect, uuid
from typing import Union, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from protocols import Arena

# ==========  DATACLASSES ==============================================================================================

@dataclass
class WorldState:
    """Declares execution environments, file system states, and functional parameters of a test world."""
    arena: Any = None
    args: Any = None
    kwargs: Any = None
    returns: Any = None
    fs: Any = None
    expect: bool = True or False

@dataclass
class EvaluationTrace:
    """Encapsulates the complete trajectory and evaluation of a single execution step."""
    step_id: str
    target: str
    pre: WorldState
    post: WorldState
    outcome: WorldState
    evaluation: bool

# ========== EXAMPLE-BASED-TESTING =====================================================================================

class EBT:
    """
    Orchestrates example-based-testing runs according to the formal Hoare triple `{P}S{Q}`.
    """
    def __init__(
            self,
            target: Any,
            arena: Optional[Arena] = None,
            pre: Union[WorldState, List[WorldState], None] = None,
            post: Union[WorldState, List[WorldState], None] = None,
            expect: bool = True or False,
            custom_id: Optional[str] = None
    ):
        if inspect.isclass(arena): raise TypeError(f"STATE-GUARD: 'arena' must be an instance.")
        self.custom_id = custom_id or self.__class__.__name__.lower()
        self.run_id = f"cubie_run_{self.custom_id}_{uuid.uuid4().hex[:8]}"
        self.target = target
        self.arena = arena
        self.expect = expect
        self.pre = pre or WorldState()
        self.post = post or WorldState()
        self._traces: List[EvaluationTrace] = []

    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(self) -> None:
        """Executes the test pipeline, consisting of preparation, execution, and evaluation."""
        __tracebackhide__ = True
        try:
            self._arrange()
            self._validate()
            self._report()
        finally:
            if self.arena: self.arena.teardown()

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _arrange(self) -> None:
        """Validates and normalizes the states passed to the pipeline."""
        __tracebackhide__ = True
        self._check_runnability()
        self._normalize_declarations()

    def _validate(self) -> None:
        """Executes the pre-states (∀) and evaluates the outcome against all post-states (∃)."""
        __tracebackhide__ = True
        pre_states = self.pre if isinstance(self.pre, list) else [self.pre]
        post_states = self.post if isinstance(self.post, list) else [self.post]
        for idx, pre in enumerate(pre_states):
            step_id = f"{self.run_id}_{idx}"
            outcome = self._execute_step(pre)
            for post in post_states: self._traces.append(self._evaluate_step(pre, post, outcome, step_id))

    def _report(self) -> None:
        """Preapares the report and asserts the results."""
        __tracebackhide__ = True
        self._assert_traces()

    # ----- Utilities --------------------------------------------------------------------------------------------------

    # ↓--- _arrange() ---↓

    def _check_runnability(self) -> None:
        """Validates all declarations for logical runnability prior to execution (Fail-Fast)."""
        __tracebackhide__ = True
        if not callable(self.target): raise TypeError("STATE-GUARD: Target must be a callable function or method.")
        post_states = self.post if isinstance(self.post, list) else [self.post]
        for idx, post_state in enumerate(post_states):
            has_assertion = (post_state.returns is not None) or bool(post_state.fs) or bool(post_state.arena)
            if not has_assertion:
                raise RuntimeError(f"STATE-GUARD: Non-runnable WorldState in post-declaration (Index {idx}).")

    def _normalize_declarations(self) -> None:
        """Normalizes the file system topologies for all defined pre- and post-states."""
        __tracebackhide__ = True
        pre_states = self.pre if isinstance(self.pre, list) else [self.pre]
        post_states = self.post if isinstance(self.post, list) else [self.post]
        for state in pre_states + post_states: state.fs = self._normalize_fs(state.fs)

    @staticmethod
    def _normalize_fs(fs_raw: Any) -> dict:
        """Normalizes set conventions into explicit target-to-host dictionaries."""
        __tracebackhide__ = True
        if not fs_raw: return {}
        if isinstance(fs_raw, dict): return fs_raw
        if isinstance(fs_raw, (set, list, tuple)):
            normalized = {}
            for path_str in fs_raw:
                p = Path(str(path_str).rstrip("/"))
                normalized[p.name] = str(path_str)
            return normalized
        raise ValueError(f"Invalid type for fs: {type(fs_raw)}")

    # ↓--- _validate() ---↓

    @staticmethod
    def _normalize_args(args_raw: Any) -> tuple:
        """Normalizes the arguments into a tuple and prevents accidental string unpacking."""
        __tracebackhide__ = True
        if args_raw is None: return ()
        if isinstance(args_raw, (list, tuple)): return tuple(args_raw)
        return (args_raw,)

    def _execute_step(self, pre_state: WorldState) -> WorldState:
        """Executes the target for a single step and returns the outcome state."""
        __tracebackhide__ = True
        if self.arena:
            self.arena.fs = pre_state.fs
            self.arena.setup()
        args = self._normalize_args(pre_state.args)
        kwargs = pre_state.kwargs if pre_state.kwargs is not None else {}
        if self.arena: actual_returns = self.arena.execute(self.target, args, kwargs)
        else: actual_returns = self.target(*args, **kwargs)
        return WorldState(returns=actual_returns)

    def _evaluate_step(
            self,
            pre_state: WorldState,
            post_state: WorldState,
            outcome: WorldState,
            step_id: str
    ) -> EvaluationTrace:
        """Evaluates the outcome against the expected post-state (raw match)."""
        __tracebackhide__ = True
        raw_match = True
        if post_state.returns is not None and not self._evaluate_func(post_state, outcome): raw_match = False
        if post_state.fs and not self._evaluate_fs(post_state.fs): raw_match = False
        target_name = getattr(self.target, '__name__', str(self.target))
        return EvaluationTrace(
            step_id=step_id,
            target=target_name,
            pre=pre_state,
            post=post_state,
            outcome=outcome,
            evaluation=raw_match
        )

    @staticmethod
    def _evaluate_func(post_state: WorldState, outcome: WorldState) -> bool:
        """Evaluates the functional return values between expected and actual states."""
        __tracebackhide__ = True
        return outcome.returns == post_state.returns

    def _evaluate_fs(self, expected_fs: dict) -> bool:
        """Performs a byte-by-byte diff evaluation against the expected filesystem topology."""
        __tracebackhide__ = True
        if self.arena is None or getattr(self.arena, "workspace_path", None) is None: return False
        for target_rel_path, host_source_path in expected_fs.items():
            arena_path = Path(str(self.arena.workspace_path)) / target_rel_path
            host_path = Path(host_source_path)
            if not arena_path.exists() or not host_path.exists(): return False
            if not self._compare_paths(arena_path, host_path): return False
        return True

    @staticmethod
    def _compare_paths(arena_path: Path, host_path: Path) -> bool:
        """Compares individual files using byte-level diffing and folders via a recursive deep scan."""
        __tracebackhide__ = True
        if host_path.is_dir():
            if not arena_path.is_dir(): return False
            for host_item in host_path.rglob('*'):
                if not host_item.is_file(): continue
                rel_path = host_item.relative_to(host_path)
                arena_item = arena_path / rel_path
                if not arena_item.exists() or not arena_item.is_file(): return False
                if not filecmp.cmp(arena_item, host_item, shallow=False): return False
            return True
        else:
            if not arena_path.is_file(): return False
            return filecmp.cmp(arena_path, host_path, shallow=False)

    # ↓--- _report() ---↓

    def _assert_traces(self) -> None:
        """Evaluates overall quantifier logic and applies the global expect modifier."""
        __tracebackhide__ = True
        steps = self._group_traces_by_step()
        step_successes = {sid: self._evaluate_step_logic(traces) for sid, traces in steps.items()}
        run_success = all(step_successes.values())
        if self.expect and not run_success:
            failed_id = next(sid for sid, succ in step_successes.items() if not succ)
            assert False, self._build_report_message(failed_id, steps[failed_id])
        elif not self.expect and run_success:
            first_id = next(iter(steps))
            assert False, self._build_report_message(first_id, steps[first_id])

    def _group_traces_by_step(self) -> dict[str, List[EvaluationTrace]]:
        """Groups all recorded traces by their execution step ID."""
        __tracebackhide__ = True
        steps: dict[str, List[EvaluationTrace]] = {}
        for t in self._traces: steps.setdefault(t.step_id, []).append(t)
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

    def _build_report_message(self, step_id: str, traces: List[EvaluationTrace]) -> str:
        """Constructs a detailed error string, exposing all evaluated quantifier states."""
        __tracebackhide__ = True
        prefix = "EBT-Assert failed" if self.expect else "EBT-Negative-Assert failed"
        base = traces[0]
        lines = [f"{prefix} for step '{step_id}':",f"Target: {base.target} | Actual Returns: {base.outcome.returns}"]
        for idx, t in enumerate(traces):
            match_status = "Matched" if t.evaluation else "Mismatch"
            lines.append(f"  [Q-State {idx}] Expected Returns: {t.post.returns} | Validation: {match_status}")
        return "\n".join(lines)