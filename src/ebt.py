import filecmp, uuid, time
from typing import Union, List, Set, Any, Optional
from pathlib import Path
from protocols import Arena, WorldState, EvaluationTrace, RunTrace, Reporter
from reporter import PytestReporter

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
            custom_id: Optional[str] = None,
            reporter: Reporter = PytestReporter()
    ):
        self.target = target
        self.arena = arena
        self.pre: List[WorldState] = self._ensure_list(pre)
        self._outcome: List[WorldState] = []
        self.post: List[WorldState] = self._ensure_list(post)
        self.expect = expect
        self.FS_IGNORES: Set[str] = {""}
        self.ARENA_IGNORES: Set[str] = {
            "bin", "Scripts", "pyvenv.cfg", "CACHEDIR.TAG", ".gitignore",
            ".lock", "__pycache__", "_virtualenv.pth", "_virtualenv.py"
        }
        self.reporter = reporter
        self.custom_id = custom_id or self.__class__.__name__.lower()
        self._run_id = f"cubie_run_{self.custom_id}_{uuid.uuid4().hex[:8]}"
        self._t_run_start = None
        self._run_duration: Optional[float] = None
        self._run_evaluation: Optional[bool] = None
        self._traces: List[EvaluationTrace] = []
        self.run_trace: Optional[RunTrace] = None

        self._current_pre: Optional[int] = None
        self._current_post: Optional[int] = None
        self._t_step_start: Optional[float] = None

    # ---------- SERVICES ----------------------------------------------------------------------------------------------

    def run(self) -> RunTrace | None:
        """Executes the test pipeline, consisting of preparation, execution, and evaluation."""
        __tracebackhide__ = True
        try:
            self._t_run_start = time.perf_counter()
            self._arrange()
            self._validate()
            self._run_duration = time.perf_counter() - self._t_run_start
            self._report()
        finally:
            if self.arena: self.arena.teardown()
        return self.run_trace

    # ---------- PIPES -------------------------------------------------------------------------------------------------

    def _arrange(self) -> None:
        """Validates and normalizes the states passed to the pipeline."""
        __tracebackhide__ = True
        self._check_runnability()
        for state in self.pre + self.post: state.fs = self._normalize_fs(state.fs)

    def _validate(self) -> None:
        """Executes the pre-states (∀) and evaluates the outcome against all post-states (∃)."""
        __tracebackhide__ = True
        for idx, _ in enumerate(self.pre):
            self._current_pre = idx
            self._t_step_start = time.perf_counter()
            self._execute_step()
            for p_idx, _ in enumerate(self.post):
                self._current_post = p_idx
                self._evaluate_step()

    def _report(self) -> None:
        """Evaluates the run and delegates the Result to the reporter if present."""
        __tracebackhide__ = True
        self._evaluate_run()
        if not self.run_trace: raise TypeError("STATE-GUARD: No run_trace found.")
        if self.reporter: self.reporter.report(self.run_trace)

    # ---------- Sub-Pipes ---------------------------------------------------------------------------------------------

    def _execute_step(self) -> None:
        """Executes the target for a single step and saves the normalized outcome state."""
        __tracebackhide__ = True
        if self._current_pre is None: raise RuntimeError("STATE-GUARD: Missing pre_idx.")
        pre_state = self.pre[self._current_pre]
        args = self._normalize_args(pre_state.args)
        kwargs = pre_state.kwargs if pre_state.kwargs is not None else {}
        active_arena = pre_state.arena if hasattr(pre_state.arena, "setup") else self.arena
        if active_arena:
            active_arena.setup(pre_state); active_arena.execute(self.target, args, kwargs)
            self._outcome.append(active_arena.get_state())
        else: self._outcome.append(WorldState(returns=self.target(*args, **kwargs)))

    def _evaluate_run(self) -> None:
        """Evaluates overall quantifier logic, applies the expect modifier and constructs RunTrace."""
        __tracebackhide__ = True
        steps = self._group_traces_by_step()
        step_successes = {sid: self._evaluate_step_logic(traces) for sid, traces in steps.items()}
        self._run_evaluation = all(step_successes.values()) if self.expect else not all(step_successes.values())
        self.run_trace = RunTrace(
            run_id=self._run_id,
            target=getattr(self.target, '__name__', str(self.target)),
            expect=self.expect,
            arena=self.arena,
            traces=self._traces,
            evaluation=self._run_evaluation,
            duration=self._run_duration
        )

    def _evaluate_step(self) -> None:
        """Evaluates the outcome against the expected post-state and appends the trace."""
        __tracebackhide__ = True
        if self._current_pre is None or self._current_post is None: raise RuntimeError("STATE-GUARD: Missing idx.")
        pre_x, post_x = self.pre[self._current_pre], self.post[self._current_post]
        outcome, diffs = self._outcome[self._current_pre], {}
        if post_x.returns is not None and (r := self._evaluate_func(post_x, outcome)): diffs["returns"] = r
        if post_x.fs and (f := self._evaluate_fs(post_x.fs, outcome.fs)): diffs["fs"] = f
        if post_x.arena and (a := self._evaluate_arena(post_x.arena, outcome.arena)): diffs["arena"] = a
        trace = EvaluationTrace(
            step_id=f"{self._run_id}_{self._current_pre}",
            target=getattr(self.target, '__name__', str(self.target)),
            pre=pre_x, post=post_x, outcome=outcome,
            evaluation=not bool(diffs), diffs=diffs or None,
            duration=time.perf_counter() - self._t_step_start
        )
        self._traces.append(trace)

    @staticmethod
    def _evaluate_func(post_state: WorldState, outcome: WorldState) -> Optional[dict]:
        """Evaluates functional return values and returns a diff dict on mismatch."""
        __tracebackhide__ = True
        if outcome.returns == post_state.returns: return None
        return {"expected": post_state.returns, "actual": outcome.returns}

    def _evaluate_arena(self, expected_arena: Any, outcome_arena: Optional[str]) -> Optional[dict]:
        """Performs a targeted evaluation against the expected arena topology and returns diffs."""
        __tracebackhide__ = True
        if not isinstance(expected_arena, str) and not hasattr(expected_arena, "env_path"):
            return None if outcome_arena is None else {"error": "Unexpected arena present in outcome."}
        if not outcome_arena: return {"error": "Outcome arena is completely missing."}
        host_path = Path(expected_arena) if isinstance(expected_arena, str) else Path(str(expected_arena.env_path))
        arena_path = Path(outcome_arena)
        if not arena_path.exists() or not host_path.exists(): return {
            "error": f"Missing paths. Arena: {arena_path.exists()}, Host: {host_path.exists()}"}
        return self._generate_diff(
            self._collect_topology(host_path, self.ARENA_IGNORES, is_arena=True),
            self._collect_topology(arena_path, self.ARENA_IGNORES, is_arena=True)
        )

    def _evaluate_fs(self, expected_fs: dict, outcome_fs: Optional[str]) -> Optional[dict]:
        """Performs a deep diff evaluation against the expected filesystem topology."""
        __tracebackhide__ = True
        if not outcome_fs: return {"error": "Outcome FS is missing."}
        diffs = {}
        for target_rel_path, host_source_path in expected_fs.items():
            arena_path, host_path = Path(outcome_fs) / target_rel_path, Path(host_source_path)
            if path_diff := self._compare_paths(arena_path, host_path): diffs[target_rel_path] = path_diff
        return diffs or None

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------

    # ↓ ========== _arrange() ========== ↓

    def _check_runnability(self) -> None:
        """Validates all declarations for logical runnability prior to execution (Fail-Fast)."""
        __tracebackhide__ = True
        if not callable(self.target): raise TypeError("STATE-GUARD: Target must be a callable function or method.")
        for idx, post_state in enumerate(self.post):
            has_assertion = (post_state.returns is not None) or bool(post_state.fs) or bool(post_state.arena)
            if not has_assertion: raise RuntimeError(f"STATE-GUARD: Non-runnable WorldState in post (Index {idx}).")

    @staticmethod
    def _ensure_list(raw_value: Union[WorldState, List[WorldState], None]) -> List[WorldState]:
        """Ensures that inputs are uniformly converted into a list of WorldStates."""
        __tracebackhide__ = True
        if raw_value is None: return [WorldState()]
        if isinstance(raw_value, list): return raw_value
        return [raw_value]

    @staticmethod
    def _normalize_fs(fs_raw: Any) -> dict:
        """Normalizes set conventions into explicit target-to-host dictionaries."""
        __tracebackhide__ = True
        if not fs_raw: return {}
        if isinstance(fs_raw, dict): return fs_raw
        if isinstance(fs_raw, (set, list, tuple)):
            normalized = {}
            for path_str in fs_raw: p = Path(str(path_str).rstrip("/")); normalized[p.name] = str(path_str)
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

    @staticmethod
    def _generate_diff(expected: dict[Path, Path], actual: dict[Path, Path]) -> Optional[dict]:
        """Generates a structured diff dictionary mapping missing, unexpected, and modified files."""
        __tracebackhide__ = True
        exp_keys, act_keys = set(expected.keys()), set(actual.keys())
        diff = {
            "missing": [str(p) for p in exp_keys - act_keys],
            "unexpected": [str(p) for p in act_keys - exp_keys],
            "modified": [str(p) for p in exp_keys & act_keys if not filecmp.cmp(actual[p], expected[p], shallow=False)]
        }
        return {k: v for k, v in diff.items() if v} or None

    @staticmethod
    def _collect_topology(base_dir: Path, ignores: Set[str], is_arena: bool = False) -> dict[Path, Path]:
        """Collects all relevant files of a directory, respecting ignore configurations."""
        __tracebackhide__ = True
        files = {}
        for item in base_dir.rglob('*'):
            if not item.is_file(): continue
            rel_path = item.relative_to(base_dir)
            if any(p in ignores for p in rel_path.parts): continue
            if is_arena and (item.suffix == ".pyc" or any(p.endswith(".dist-info") for p in rel_path.parts)): continue
            files[rel_path] = item
        return files

    # ↓--- _evaluate_fs() ---↓

    def _compare_paths(self, arena_path: Path, host_path: Path) -> Optional[dict]:
        """Compares individual files or delegates recursive deep scans to the diff generator."""
        __tracebackhide__ = True
        if not arena_path.exists() or not host_path.exists(): return {
            "error": f"Path not found. Arena: {arena_path.exists()}, Host: {host_path.exists()}"}
        if host_path.is_dir() and arena_path.is_dir(): return self._generate_diff(
            self._collect_topology(host_path, self.FS_IGNORES), self._collect_topology(arena_path, self.FS_IGNORES))
        if host_path.is_file() and arena_path.is_file():
            if not filecmp.cmp(arena_path, host_path, shallow=False): return {"modified": [str(host_path.name)]}
            return None
        return {"error": "Topology mismatch (file vs dir)."}

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

    def _group_traces_by_step(self) -> dict[str, List[EvaluationTrace]]:
        """Groups all recorded traces by their execution step ID."""
        __tracebackhide__ = True
        steps: dict[str, List[EvaluationTrace]] = {}
        for t in self._traces: steps.setdefault(t.step_id, []).append(t)
        return steps