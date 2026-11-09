import dataclasses, filecmp, uuid, time, re, types, functools
from pathlib import Path
from typing import Union, Set, get_origin, get_args, Optional
from .multiprocessors import *
from .protocols import Arena, WorldState, EvaluationTrace, RunTrace, Reporter, Multiprocessor
from .reporter import PytestReporter

# ========== EXAMPLE-BASED-TESTING =====================================================================================

@dataclasses.dataclass(frozen=True)
class EBTContext:
    target: Any
    arena: Optional[Arena]
    post_states: List[WorldState]
    run_id: str
    fs_ignores: Set[str]
    arena_ignores: Set[str]
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
            expect: bool = True,
            custom_id: Optional[str] = None,
            reporter: Reporter | None = PytestReporter(),
            multiprocessing: bool = False,
            multiprocessors: Optional[List['Multiprocessor']] = None,
            tags = None
        ):
        self.tags = tags
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
        self.MULTIPROCESSING = multiprocessing or False
        self.MULTIPROCESSORS: List['Multiprocessor'] = [PickleProcessor(), LokyProcessor()]
        if multiprocessors: self.MULTIPROCESSORS.extend(multiprocessors)

    # ---------- SERVICES ----------------------------------------------------------------------------------------------

    def run(self) -> RunTrace | None:
        """Executes the test pipeline, consisting of preparation, execution, and evaluation."""
        __tracebackhide__ = True
        self._t_run_start = time.perf_counter()
        self._arrange()
        self._validate()
        self._run_duration = time.perf_counter() - self._t_run_start
        self._report()
        return self.run_trace

    # ---------- SUB-SERVICES ------------------------------------------------------------------------------------------

    def _arrange(self) -> None:
        """Validates and normalizes the states passed to the pipeline."""
        __tracebackhide__ = True
        for state in self.pre + self.post: state.fs = self._normalize_fs(state.fs)

    def _validate(self) -> None:
        """Executes the pre-states (∀) and evaluates the outcome against all post-states (∃)."""
        __tracebackhide__ = True
        if not self.MULTIPROCESSING: self._validate_singleprocess()
        else: self._validate_multiprocess()

    def _report(self) -> None:
        """Evaluates the run and delegates the Result to the reporter if present."""
        __tracebackhide__ = True
        self._evaluate_run()
        if not self.run_trace: raise TypeError("STATE-GUARD: No run_trace found.")
        if self.reporter: self.reporter.report(self.run_trace)

    # ---------- PROCESSING-STRATEGIES ---------------------------------------------------------------------------------

    def _build_context(self) -> EBTContext:
        """Safely encapsulates the volatile OOP state into an FP record."""
        return EBTContext(
            target=self.target,
            arena=self.arena,
            post_states=self.post,
            run_id=self._run_id,
            fs_ignores=self.FS_IGNORES,
            arena_ignores=self.ARENA_IGNORES
        )

    def _validate_singleprocess(self) -> None:
        """Sequential processing, reusing the unified task logic."""
        __tracebackhide__ = True
        ctx = self._build_context()
        for pre_idx, pre_state in enumerate(self.pre):
            outcome, traces = self._process_single_task(pre_idx, pre_state, ctx)
            self._outcome.append(outcome)
            self._traces.extend(traces)

    def _validate_multiprocess(self) -> None:
        """Parallel execution via the decoupled DI facade (MultiprocessManager)."""
        __tracebackhide__ = True
        ctx = self._build_context()
        task_func = functools.partial(self._process_single_task, ctx=ctx)
        manager = MultiprocessManager(
            pre_states=self.pre,
            post_states=self.post,
            task_func=task_func,
            processors=self.MULTIPROCESSORS
        )
        raw_results = manager.execute()
        if isinstance(raw_results, Exception): raise raw_results
        if raw_results is None: raise RuntimeError("STATE-GUARD: MultiprocessManager.execute() returned None (FAIL).")
        results = list(raw_results)
        for outcome, traces in results:
            self._outcome.append(outcome)
            self._traces.extend(traces)

    @staticmethod
    def _process_single_task(
            pre_idx: int,
            pre_state: WorldState,
            ctx: EBTContext
    ) -> tuple[WorldState, List[EvaluationTrace]]:
        """Parallel-ready processing reusing the stateless step functions."""
        __tracebackhide__ = True
        t_step_start = time.perf_counter()
        active_arena = pre_state.arena if hasattr(pre_state.arena, "setup") else ctx.arena
        traces = []
        try:
            outcome = EBT._execute_step(pre_state, ctx.target, active_arena)
            for post_state in ctx.post_states:
                trace = EBT._evaluate_step(
                    pre_idx=pre_idx, t_step_start=t_step_start,ctx=ctx,
                    pre_state=pre_state, post_state=post_state, outcome=outcome
                )
                traces.append(trace)
        finally:
            if active_arena: active_arena.teardown()
        return outcome, traces

    # ---------- HELPER ------------------------------------------------------------------------------------------------

    def _evaluate_run(self) -> None:
        """Evaluates overall quantifier logic, applies the expect modifier and constructs RunTrace."""
        __tracebackhide__ = True
        steps = self._group_traces_by_step()
        step_successes = {sid: self._evaluate_step_logic(traces) for sid, traces in steps.items()}
        self._run_evaluation = all(step_successes.values()) if self.expect else not all(step_successes.values())
        self.run_trace = RunTrace(
            run_id=self._run_id, arena=self.arena,
            target=getattr(self.target, '__name__', str(self.target)),
            expect=self.expect, traces=self._traces, evaluation=self._run_evaluation,
            duration=self._run_duration
        )

    @staticmethod
    def _execute_step(pre_state: WorldState, target: Any, active_arena: Optional[Arena]) -> WorldState:
        """Executes the target for a single step and returns the normalized outcome state."""
        __tracebackhide__ = True
        args = EBT._normalize_args(pre_state.args)
        kwargs = pre_state.kwargs if pre_state.kwargs is not None else {}
        if not isinstance(kwargs, dict):
            raise TypeError(f"STATE-GUARD: Expected a dict for 'kwargs', but received {type(kwargs).__name__}.")
        if active_arena:
            active_arena.setup(pre_state)
            active_arena.execute(target, args, kwargs)
            return active_arena.get_state()
        return WorldState(returns=target(*args, **kwargs))

    @staticmethod
    def _evaluate_step(
            pre_idx: int, t_step_start: float,
            pre_state: WorldState, post_state: WorldState,
            outcome: WorldState, ctx: EBTContext
    ) -> EvaluationTrace:
        """Evaluates the outcome against the expected post-state and returns the trace."""
        __tracebackhide__ = True
        diffs = EBT._calculate_diffs(post_state, outcome, ctx)
        return EvaluationTrace(
            step_id=f"{ctx.run_id}_{pre_idx}",
            target=getattr(ctx.target, '__name__', str(ctx.target)),
            pre=pre_state, post=post_state, outcome=outcome,
            evaluation=not bool(diffs), diffs=diffs or None,
            duration=time.perf_counter() - t_step_start
        )

    @staticmethod
    def _calculate_diffs(post: WorldState, outcome: WorldState, ctx: EBTContext) -> dict:
        """Isolates the formal-logical diff calculation and delegates to the type guard."""
        __tracebackhide__ = True
        diffs = {}
        if post.returns is not None: EBT._append_diff(diffs, "returns", EBT._evaluate_func(post, outcome))
        if post.arena:
            EBT._append_diff(
                diffs,
                "arena",
                EBT._evaluate_arena(post.arena, outcome.arena, ctx.arena_ignores)
            )
        if post.fs:
            if not isinstance(post.fs, dict): raise TypeError("STATE-GUARD: post_state.fs must be a dict.")
            EBT._append_diff(diffs, "fs", EBT._evaluate_fs(post.fs, outcome.fs, ctx.fs_ignores))
        return diffs

    @staticmethod
    def _append_diff(diffs: dict, key: str, val: Any) -> None:
        """Validates the data type and appends identified diffs to the target dictionary."""
        __tracebackhide__ = True
        if val is not None:
            if not isinstance(val, dict): raise TypeError(f"STATE-GUARD: {key} evaluation must return a dict.")
            diffs[key] = val

    @staticmethod
    def _evaluate_arena(expected_arena: Any, outcome_arena: Optional[str], arena_ignores: Set[str]) -> Optional[dict]:
        """Performs a targeted evaluation against the expected arena topology and returns diffs."""
        __tracebackhide__ = True
        if not isinstance(expected_arena, str) and not hasattr(expected_arena, "env_path"):
            return None if outcome_arena is None else {"error": "Unexpected arena present in outcome."}
        if not outcome_arena: return {"error": "Outcome arena is completely missing."}
        host_path = Path(expected_arena) if isinstance(expected_arena, str) else Path(str(expected_arena.env_path))
        arena_path = Path(outcome_arena)
        if not arena_path.exists() or not host_path.exists():
            return {"error": f"Missing paths. Arena: {arena_path.exists()}, Host: {host_path.exists()}"}
        return EBT._generate_diff(
            EBT._collect_topology(host_path, arena_ignores, is_arena=True),
            EBT._collect_topology(arena_path, arena_ignores, is_arena=True)
        )

    @staticmethod
    def _evaluate_fs(expected_fs: dict, outcome_fs: Optional[str], fs_ignores: Set[str]) -> Optional[dict]:
        """Performs a deep diff evaluation against the expected filesystem topology or callables."""
        __tracebackhide__ = True
        if not outcome_fs: return {"error": "Outcome FS is missing."}
        diffs = {}
        for target_rel_path, expected_val in expected_fs.items():
            arena_path = Path(outcome_fs) / target_rel_path
            if callable(expected_val):
                try:
                    if not expected_val(arena_path): diffs[target_rel_path] = {"error": "Callable eval failed."}
                except Exception as e: diffs[target_rel_path] = {"error": f"Callable raised Exception: {e}"}
                continue
            host_path = Path(expected_val)
            if path_diff := EBT._compare_paths(arena_path, host_path, fs_ignores): diffs[target_rel_path] = path_diff
        return diffs or None

    @staticmethod
    def _compare_paths(arena_path: Path, host_path: Path, fs_ignores: Set[str]) -> Optional[dict]:
        """Compares individual files or delegates recursive deep scans to the diff generator."""
        __tracebackhide__ = True
        if not arena_path.exists() or not host_path.exists():
            return {"error": f"Path not found. Arena: {arena_path.exists()}, Host: {host_path.exists()}"}
        if host_path.is_dir() and arena_path.is_dir():
            return EBT._generate_diff(
                EBT._collect_topology(host_path, fs_ignores),
                EBT._collect_topology(arena_path, fs_ignores)
            )
        if host_path.is_file() and arena_path.is_file():
            if not filecmp.cmp(arena_path, host_path, shallow=False): return {"modified": [str(host_path.name)]}
            return None
        return {"error": "Topology mismatch (file vs dir)."}

    @staticmethod
    def _evaluate_func(post_state: WorldState, outcome: WorldState) -> Optional[dict]:
        """Evaluates functional return values dynamically."""
        __tracebackhide__ = True
        if EBT._compare(post_state.returns, outcome.returns): return None
        return {"expected": str(post_state.returns), "actual": outcome.returns}

    @staticmethod
    def _compare(exp: Any, act: Any) -> bool:
        """Routes values to the appropriate comparison strategy."""
        if exp is Any: return True
        if EBT._is_union(exp): return EBT._cmp_union(exp, act)
        if isinstance(exp, type): return isinstance(act, exp)
        if isinstance(exp, re.Pattern): return EBT._cmp_regex(exp, act)
        if callable(exp): return EBT._cmp_call(exp, act)
        if isinstance(exp, (dict, list, tuple)): return EBT._cmp_nest(exp, act)
        return exp == act

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------

    # ↓ ========== _arrange() ========== ↓

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

    @staticmethod
    def _is_union(exp: Any) -> bool:
        """Checks if the expected value is a union type."""
        origin = get_origin(exp)
        return origin is Union or type(exp) is getattr(types, "UnionType", type(None))

    @staticmethod
    def _cmp_union(exp: Any, act: Any) -> bool:
        """Evaluates union types against the actual value."""
        return any(EBT._compare(arg, act) for arg in get_args(exp))

    @staticmethod
    def _cmp_regex(exp: re.Pattern, act: Any) -> bool:
        """Evaluates a regular expression against the actual value."""
        return False if act is None else bool(exp.match(str(act)))

    @staticmethod
    def _cmp_call(exp: Callable, act: Any) -> bool:
        """Safely evaluates a callable predicate without triggering broad exception warnings."""
        try: return bool(exp(act))
        except (TypeError, ValueError, AttributeError, KeyError, IndexError): return False

    @staticmethod
    def _cmp_nest(exp: Any, act: Any) -> bool:
        """Recursively evaluates nested data structures."""
        if isinstance(exp, dict) and isinstance(act, dict):
            if exp.keys() != act.keys(): return False
            return all(EBT._compare(exp[k], act[k]) for k in exp)
        if isinstance(exp, (list, tuple)) and isinstance(act, (list, tuple)):
            if len(exp) != len(act): return False
            return all(EBT._compare(e, a) for e, a in zip(exp, act))
        return False

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