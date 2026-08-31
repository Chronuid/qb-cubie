import filecmp, inspect, uuid
from typing import Union, List, Set, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from protocols import Arena, WorldState

# ==========  DATACLASSES ==============================================================================================

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
        self._run_id = f"cubie_run_{self.custom_id}_{uuid.uuid4().hex[:8]}"
        self.expect = expect
        self.target = target
        self.arena = arena
        self.FS_IGNORES: Set[str] = {""}
        self.ARENA_IGNORES: Set[str] = {
            "bin", "Scripts", "pyvenv.cfg", "CACHEDIR.TAG",
            ".gitignore", ".lock", "__pycache__",
            "_virtualenv.pth", "_virtualenv.py"
        }
        self.pre: List[WorldState] = self._ensure_list(pre)
        self.post: List[WorldState] = self._ensure_list(post)
        self._outcome: List[WorldState] = []
        self._traces: List[EvaluationTrace] = []

    # ---------- SERVICES ----------------------------------------------------------------------------------------------

    def run(self) -> None:
        """Executes the test pipeline, consisting of preparation, execution, and evaluation."""
        __tracebackhide__ = True
        try:
            self._arrange()
            self._validate()
            self._report()
        finally:
            if self.arena: self.arena.teardown()

    # ---------- PIPES -------------------------------------------------------------------------------------------------

    def _arrange(self) -> None:
        """Validates and normalizes the states passed to the pipeline."""
        __tracebackhide__ = True
        self._check_runnability()
        self._normalize_declarations()

    def _validate(self) -> None:
        """Executes the pre-states (∀) and evaluates the outcome against all post-states (∃)."""
        __tracebackhide__ = True
        for pre_idx, pre_state in enumerate(self.pre):
            outcome = self._execute_step(pre_state)
            self._outcome.append(outcome)
            step_id = f"{self._run_id}_{pre_idx}"
            for post_idx, _ in enumerate(self.post):
                self._traces.append(self._evaluate_step(pre_idx, post_idx, step_id))

    def _report(self) -> None:
        """Preapares the report and asserts the results."""
        __tracebackhide__ = True
        self._assert_traces()

    # ---------- Sub-Pipes ---------------------------------------------------------------------------------------------

    def _execute_step(self, pre_state: WorldState) -> WorldState:
        """Executes the target for a single step and returns the normalized outcome state."""
        __tracebackhide__ = True
        active_arena = pre_state.arena if hasattr(pre_state.arena, "setup") else self.arena
        if active_arena: active_arena.setup(pre_state)
        args = self._normalize_args(pre_state.args)
        kwargs = pre_state.kwargs if pre_state.kwargs is not None else {}
        if active_arena:
            active_arena.execute(self.target, args, kwargs)
            return active_arena.get_state()
        actual_returns = self.target(*args, **kwargs)
        return WorldState(returns=actual_returns)

    def _evaluate_step(self, pre_idx: int, post_idx: int, step_id: str) -> EvaluationTrace:
        """Evaluates the outcome against the expected post-state using index topology."""
        __tracebackhide__ = True
        pre_state, post_state, outcome = self.pre[pre_idx], self.post[post_idx], self._outcome[pre_idx]
        raw_match = True
        if post_state.returns is not None and not self._evaluate_func(post_state, outcome): raw_match = False
        if post_state.fs and not self._evaluate_fs(post_state.fs, outcome.fs): raw_match = False
        if post_state.arena and not self._evaluate_arena(post_state.arena, outcome.arena): raw_match = False
        target_name = getattr(self.target, '__name__', str(self.target))
        return EvaluationTrace(
            step_id=step_id, target=target_name, pre=pre_state, post=post_state, outcome=outcome, evaluation=raw_match
        )

    @staticmethod
    def _evaluate_func(post_state: WorldState, outcome: WorldState) -> bool:
        """Evaluates the functional return values between expected and actual states."""
        __tracebackhide__ = True
        return outcome.returns == post_state.returns

    def _evaluate_arena(self, expected_arena: Any, outcome_arena: Optional[str]) -> bool:
        """Performs a targeted evaluation against the expected arena topology."""
        __tracebackhide__ = True
        if not outcome_arena: return False
        if isinstance(expected_arena, str): host_path = Path(expected_arena)
        elif hasattr(expected_arena, "env_path"): host_path = Path(str(expected_arena.env_path))
        else: raise TypeError(f"STATE-GUARD: Invalid expected_arena type: {type(expected_arena)}")
        arena_path = Path(outcome_arena)
        if not arena_path.exists() or not host_path.exists(): return False
        return self._compare_venv_contents(arena_path, host_path)

    def _evaluate_fs(self, expected_fs: dict, outcome_fs: Optional[str]) -> bool:
        """Performs a byte-by-byte diff evaluation against the expected filesystem topology."""
        __tracebackhide__ = True
        if not outcome_fs: return False
        for target_rel_path, host_source_path in expected_fs.items():
            arena_path = Path(outcome_fs) / target_rel_path
            host_path = Path(host_source_path)
            if not arena_path.exists() or not host_path.exists(): return False
            if not self._compare_paths(arena_path, host_path): return False
        return True

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------

    # ↓ ========== _arrange() ========== ↓

    def _check_runnability(self) -> None:
        """Validates all declarations for logical runnability prior to execution (Fail-Fast)."""
        __tracebackhide__ = True
        if not callable(self.target): raise TypeError("STATE-GUARD: Target must be a callable function or method.")
        for idx, post_state in enumerate(self.post):
            has_assertion = (post_state.returns is not None) or bool(post_state.fs) or bool(post_state.arena)
            if not has_assertion: raise RuntimeError(
                f"STATE-GUARD: Non-runnable WorldState in post-declaration (Index {idx}).")

    @staticmethod
    def _ensure_list(raw_value: Union[WorldState, List[WorldState], None]) -> List[WorldState]:
        """Ensures that inputs are uniformly converted into a list of WorldStates."""
        __tracebackhide__ = True
        if raw_value is None: return [WorldState()]
        if isinstance(raw_value, list): return raw_value
        return [raw_value]

    def _normalize_declarations(self) -> None:
        """Normalizes the file system topologies for all defined pre- and post-states."""
        __tracebackhide__ = True
        for state in self.pre + self.post: state.fs = self._normalize_fs(state.fs)

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

    @staticmethod
    def _normalize_args(args_raw: Any) -> tuple:
        """Normalizes the arguments into a tuple and prevents accidental string unpacking."""
        __tracebackhide__ = True
        if args_raw is None: return ()
        if isinstance(args_raw, (list, tuple)): return tuple(args_raw)
        return (args_raw,)

    # ↓ ========== _validate() ========== ↓

    # ↓--- _evaluate_arena() ---↓

    def _compare_venv_contents(self, arena_path: Path, host_path: Path) -> bool:
        """Compares venv contents bidirectionally, filtering volatile metadata."""
        __tracebackhide__ = True
        import filecmp
        host_files = self._get_filtered_venv_files(host_path)
        arena_files = self._get_filtered_venv_files(arena_path)
        if set(host_files.keys()) != set(arena_files.keys()): return False
        for rel_path in host_files.keys():
            if not filecmp.cmp(arena_files[rel_path], host_files[rel_path], shallow=False): return False
        return True

    def _get_filtered_venv_files(self, base_dir: Path) -> dict[Path, Path]:
        """Collects all functional source files of a venv, ignoring caches and volatile metadata."""
        __tracebackhide__ = True
        files = {}
        for item in base_dir.rglob('*'):
            if not item.is_file(): continue
            parts = item.parts
            if any(p in self.ARENA_IGNORES or p.endswith(".dist-info") for p in parts): continue
            if item.suffix == ".pyc": continue
            files[item.relative_to(base_dir)] = item
        return files

    # ↓--- _evaluate_fs() ---↓

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

    # ↓ ========== _report() ========== ↓

    @staticmethod
    def _evaluate_step_logic(traces: List[EvaluationTrace]) -> bool:
        """Evaluates the boolean success of a single step based on positive and negative states."""
        __tracebackhide__ = True
        positives = [t for t in traces if t.post.expect]
        negatives = [t for t in traces if not t.post.expect]
        violates_neg = any(t.evaluation for t in negatives)
        satisfies_pos = any(t.evaluation for t in positives) if positives else True
        return satisfies_pos and not violates_neg

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

    def _build_report_message(self, step_id: str, traces: List[EvaluationTrace]) -> str:
        """Constructs a detailed error string, exposing all evaluated quantifier states."""
        __tracebackhide__ = True
        prefix = "EBT-Assert failed" if self.expect else "EBT-Negative-Assert failed"
        lines = [f"{prefix} for step '{step_id}':", f"Target: {traces[0].target}"]
        for idx, t in enumerate(traces): lines.extend(self._format_trace_details(idx, t))
        return "\n".join(lines)

    def _format_trace_details(self, idx: int, t: EvaluationTrace) -> List[str]:
        """Formats the detailed property comparisons for a single EvaluationTrace."""
        __tracebackhide__ = True
        lines = [f"  [Q-State {idx}] Validation: {'Matched' if t.evaluation else 'Mismatch'}"]
        if t.post.returns is not None:
            match = "Match" if self._evaluate_func(t.post, t.outcome) else "Mismatch"
            lines.append(f"    - Returns: Expected {t.post.returns} | Actual {t.outcome.returns} ({match})")
        if t.post.fs:
            match = "Match" if self._evaluate_fs(t.post.fs, t.outcome.fs) else "Mismatch"
            lines.append(f"    - FS: Expected {t.post.fs} | Actual {t.outcome.fs} ({match})")
        if t.post.arena:
            match = "Match" if self._evaluate_arena(t.post.arena, t.outcome.arena) else "Mismatch"
            expected = getattr(t.post.arena, "env_path", t.post.arena)
            lines.append(f"    - Arena: Expected {expected} | Actual {t.outcome.arena} ({match})")
        return lines