import dataclasses
import uuid
import time
import re
import types
import functools
from copy import deepcopy
from multiprocessing.managers import BaseProxy
from pathlib import Path
from typing import Any, Callable, List, Union, Set, get_origin, get_args, Optional
from .multiprocessors import PickleProcessor, LokyProcessor, MultiprocessManager
from .multiprocessors import _validate_max_workers
from .protocols import Arena, WorldState, EvaluationTrace, RunTrace, Reporter, Multiprocessor, UNSPECIFIED, ExceptionExpectation
from .reporter import PytestReporter
from ._execution import CaptureTarget, CapturedResult, RemoteException, exception_details, qualified_name
from ._files import same_contents

# ========== EXAMPLE-BASED-TESTING =====================================================================================


@dataclasses.dataclass(frozen=True)
class _ProcessResourceReference:
    """Historical identity of a process resource, without a live connection."""

    resource_type: str
    resource_id: str


def _snapshot(value: Any) -> Any:
    """Deep-copy data without dereferencing process manager resources."""
    return _Snapshot().copy(value)


class _Snapshot:
    def __init__(self):
        self.memo: dict[int, Any] = {}
        self.visited: set[int] = set()

    def copy(self, value: Any) -> Any:
        self._collect(value)
        return deepcopy(value, self.memo)

    def _collect(self, item: Any) -> None:
        if id(item) in self.visited:
            return
        self.visited.add(id(item))
        if isinstance(item, BaseProxy):
            token = getattr(item, "_token")
            self.memo[id(item)] = _ProcessResourceReference(token.typeid, token.id)
        else:
            for child in self._children(item):
                self._collect(child)

    @staticmethod
    def _children(item: Any):
        if isinstance(item, dict):
            for key, value in item.items():
                yield key
                yield value
        elif isinstance(item, (list, tuple, set, frozenset)):
            yield from item
        elif dataclasses.is_dataclass(item) and not isinstance(item, type):
            yield from (getattr(item, field.name) for field in dataclasses.fields(item))
        elif not isinstance(item, (type, types.FunctionType, types.MethodType)) and hasattr(item, "__dict__"):
            yield vars(item)


@dataclasses.dataclass(frozen=True)
class EBTContext:
    target: Any
    arena: Optional[Arena]
    post_states: List[WorldState]
    run_id: str
    fs_ignores: Set[str]
    arena_ignores: Set[str]


class EBT:
    """Runs concrete examples against result patterns; the Hoare triple is a structural analogy, not a proof."""

    # With multiprocessing enabled, max_workers optionally caps each built-in
    # pool in addition to CPU and input counts. None adds no user limit; a
    # positive integer is required otherwise. The cap applies per EBT instance.

    def __init__(
        self, target: Any, arena: Optional[Arena] = None,
        pre: Union[WorldState, List[WorldState], None] = None,
        post: Union[WorldState, List[WorldState], None] = None,
        expect: bool = True, custom_id: Optional[str] = None,
        reporter: Reporter[RunTrace] | None = PytestReporter(),
        multiprocessing: bool = False,
        multiprocessors: Optional[List[Multiprocessor]] = None,
        tags=None, *, max_workers: int | None = None,
    ):
        _validate_max_workers(max_workers)
        self.max_workers = max_workers
        self.tags = tags
        self._configure_states(target, arena, pre, post, expect)
        self._configure_reporting(reporter, custom_id)
        self._configure_processors(multiprocessing, multiprocessors)
        self._outcome: List[WorldState] = []
        self._t_run_start: float | None = None
        self._run_duration: float | None = None
        self._run_evaluation: bool | None = None
        self._traces: List[EvaluationTrace] = []
        self.run_trace: RunTrace | None = None


    # ---------- SERVICES ----------------------------------------------------------------------------------------------

    def run(self) -> RunTrace | None:
        """Execute a fresh run and return a detached historical snapshot."""
        __tracebackhide__ = True
        started = self._start_run()
        self._arrange()
        self._validate()
        self._run_duration = time.perf_counter() - started
        self._report()
        return self.run_trace


    # ---------- SUB-SERVICES ------------------------------------------------------------------------------------------

    def _configure_states(
        self, target: Any, arena: Arena | None,
        pre: WorldState | list[WorldState] | None,
        post: WorldState | list[WorldState] | None, expect: bool,
    ) -> None:
        self.target = target
        self.arena = arena
        self.pre: List[WorldState] = self._ensure_list(pre, "pre")
        self.post: List[WorldState] = self._ensure_list(post, "post")
        self.expect = expect
        self.FS_IGNORES: Set[str] = {""}
        self.ARENA_IGNORES: Set[str] = {
            "bin", "Scripts", "pyvenv.cfg", "CACHEDIR.TAG", ".gitignore", ".lock",
            "__pycache__", "_virtualenv.pth", "_virtualenv.py",
        }

    def _configure_reporting(self, reporter: Reporter[RunTrace] | None, custom_id: str | None) -> None:
        self.reporter = reporter
        self.custom_id = custom_id or self.__class__.__name__.lower()
        self._run_id = f"cubie_run_{self.custom_id}_{uuid.uuid4().hex[:8]}"

    def _configure_processors(self, multiprocessing: bool, processors: list[Multiprocessor] | None) -> None:
        self.MULTIPROCESSING = multiprocessing or False
        self.MULTIPROCESSORS: List[Multiprocessor] = [PickleProcessor(), LokyProcessor()]
        if processors:
            self.MULTIPROCESSORS.extend(processors)

    def _initialize_results(self) -> None:
        self._outcome = []
        self._t_run_start = None
        self._run_duration = None
        self._run_evaluation = None
        self._traces = []
        self.run_trace = None

    def _start_run(self) -> float:
        self._run_id = f"cubie_run_{self.custom_id}_{uuid.uuid4().hex}"
        self._initialize_results()
        started = time.perf_counter()
        self._t_run_start = started
        return started

    def _arrange(self) -> None:
        """Validate all declared states before normalizing their filesystems."""
        __tracebackhide__ = True
        _validate_max_workers(self.max_workers)
        self.pre = self._ensure_list(self.pre, "pre")
        self.post = self._ensure_list(self.post, "post")
        for state in (*self.pre, *self.post):
            state.validate_exception_contract()
        normalized = self._normalized_states()
        for state, fs in normalized:
            state.fs = fs

    def _normalized_states(self) -> list[tuple[WorldState, dict]]:
        return [
            (state, self._normalize_fs(state.fs, f"{field}[{index}].fs"))
            for field, states in (("pre", self.pre), ("post", self.post))
            for index, state in enumerate(states)
        ]

    def _validate(self) -> None:
        """Executes the pre-states (∀) and evaluates the outcome against all post-states (∃)."""
        __tracebackhide__ = True
        if not self.MULTIPROCESSING:
            self._validate_singleprocess()
        else:
            self._validate_multiprocess()

    def _report(self) -> None:
        """Evaluates the run and delegates the Result to the reporter if present."""
        __tracebackhide__ = True
        self._evaluate_run()
        if not self.run_trace:
            raise TypeError("STATE-GUARD: No run_trace found.")
        if self.reporter:
            self.reporter.report(self.run_trace)

    # ---------- PROCESSING-STRATEGIES ---------------------------------------------------------------------------------

    def _build_context(self) -> EBTContext:
        """Safely encapsulates the volatile OOP state into an FP record."""
        return EBTContext(
            target=self.target,
            arena=self.arena,
            post_states=_snapshot(self.post),
            run_id=self._run_id,
            fs_ignores=set(self.FS_IGNORES),
            arena_ignores=set(self.ARENA_IGNORES),
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
        """Execute tasks through the multiprocessor facade."""
        __tracebackhide__ = True
        for outcome, traces in self._multiprocess_results():
            self._outcome.append(outcome)
            self._traces.extend(traces)

    def _multiprocess_results(self) -> list[tuple[WorldState, list[EvaluationTrace]]]:
        task_func = functools.partial(self._process_single_task, ctx=self._build_context())
        manager = MultiprocessManager(
            pre_states=self.pre, post_states=self.post, task_func=task_func,
            processors=self.MULTIPROCESSORS, max_workers=self.max_workers,
        )
        raw_results = manager.execute()
        if isinstance(raw_results, Exception):
            raise raw_results
        if raw_results is None:
            raise RuntimeError("STATE-GUARD: MultiprocessManager.execute() returned None (FAIL).")
        return list(raw_results)

    @staticmethod
    def _process_single_task(pre_idx: int, pre_state: WorldState, ctx: EBTContext) -> tuple[WorldState, List[EvaluationTrace]]:
        """Observe and evaluate one task while preserving its arena lifecycle."""
        __tracebackhide__ = True
        started = time.perf_counter()
        arena = pre_state.arena if hasattr(pre_state.arena, "setup") else ctx.arena
        try:
            outcome, traces = EBT._observe_task(pre_idx, pre_state, ctx, arena, started)
        except BaseException as error:
            EBT._cleanup_arena(arena, error)
            raise
        if arena:
            arena.teardown()
        return outcome, traces

    @staticmethod
    def _observe_task(
        pre_idx: int, pre_state: WorldState, ctx: EBTContext, arena: Arena | None, started: float,
    ) -> tuple[WorldState, list[EvaluationTrace]]:
        # Snapshot declarations before target code can mutate them.
        recorded_pre, recorded_posts = _snapshot((pre_state, ctx.post_states))
        outcome = EBT._execute_step(
            pre_state, ctx.target, arena,
            capture_exceptions=any(post.raises is not None for post in recorded_posts),
        )
        traces = EBT._task_traces(pre_idx, recorded_pre, recorded_posts, outcome, ctx, started)
        return _snapshot((outcome, traces))

    @staticmethod
    def _task_traces(
        pre_idx: int, recorded_pre: WorldState, recorded_posts: list[WorldState],
        outcome: WorldState, ctx: EBTContext, started: float,
    ) -> list[EvaluationTrace]:
        traces = []
        for post in recorded_posts:
            trace = EBT._evaluate_step(
                pre_idx=pre_idx, t_step_start=started, ctx=ctx,
                pre_state=recorded_pre, post_state=post, outcome=outcome,
            )
            traces.append(trace)
        return traces

    @staticmethod
    def _cleanup_arena(arena: Arena | None, error: BaseException) -> None:
        if arena:
            try:
                arena.teardown()
            except Exception as cleanup_error:
                error.add_note(f"Arena teardown also failed: {cleanup_error}")

    # ---------- HELPER ------------------------------------------------------------------------------------------------

    def _evaluate_run(self) -> None:
        """Evaluate the quantifiers and record the completed run."""
        __tracebackhide__ = True
        steps = self._group_traces_by_step()
        successes = [self._evaluate_step_logic(traces) for traces in steps.values()]
        success = all(successes)
        self._run_evaluation = success if self.expect else not success
        self.run_trace = RunTrace(
            run_id=self._run_id, arena=_snapshot(self.arena),
            target=getattr(self.target, "__name__", str(self.target)),
            expect=self.expect, traces=_snapshot(self._traces),
            evaluation=self._run_evaluation, duration=self._run_duration,
        )

    @staticmethod
    def _execute_step(pre_state: WorldState, target: Any, active_arena: Optional[Arena], *, capture_exceptions: bool = False) -> WorldState:
        """Execute one target call and normalize its observed outcome."""
        __tracebackhide__ = True
        args = EBT._normalize_args(pre_state.args)
        kwargs = EBT._normalize_kwargs(pre_state.kwargs)
        execution_target = CaptureTarget(target) if capture_exceptions else target
        result, outcome = EBT._invoke_target(pre_state, execution_target, args, kwargs, active_arena)
        if capture_exceptions:
            EBT._apply_captured(outcome, result)
        return outcome

    @staticmethod
    def _normalize_kwargs(kwargs: Any) -> dict:
        if kwargs is None:
            return {}
        if not isinstance(kwargs, dict):
            raise TypeError(f"STATE-GUARD: Expected a dict for 'kwargs', but received {type(kwargs).__name__}.")
        return kwargs

    @staticmethod
    def _invoke_target(
        pre_state: WorldState, target: Any, args: tuple, kwargs: dict, arena: Arena | None,
    ) -> tuple[Any, WorldState]:
        if arena:
            arena.setup(pre_state)
            result = arena.execute(target, args, kwargs)
            return result, arena.get_state()
        result = target(*args, **kwargs)
        return result, WorldState(returns=result)

    @staticmethod
    def _apply_captured(outcome: WorldState, captured: Any) -> None:
        if not isinstance(captured, CapturedResult):
            raise TypeError("Arena did not preserve the captured target result.")
        outcome.returns = UNSPECIFIED if captured.exception is not None else captured.value
        outcome.exception = captured.exception

    @staticmethod
    def _evaluate_step(
        pre_idx: int,
        t_step_start: float,
        pre_state: WorldState,
        post_state: WorldState,
        outcome: WorldState,
        ctx: EBTContext,
    ) -> EvaluationTrace:
        """Evaluates the outcome against the expected post-state and returns the trace."""
        __tracebackhide__ = True
        diffs = EBT._calculate_diffs(post_state, outcome, ctx)
        return EvaluationTrace(
            step_id=f"{ctx.run_id}_{pre_idx}",
            target=getattr(ctx.target, "__name__", str(ctx.target)),
            pre=pre_state,
            post=post_state,
            outcome=outcome,
            evaluation=not bool(diffs),
            diffs=diffs or None,
            duration=time.perf_counter() - t_step_start,
        )

    @staticmethod
    def _calculate_diffs(post: WorldState, outcome: WorldState, ctx: EBTContext) -> dict:
        """Aggregate exception, return, arena and filesystem differences."""
        __tracebackhide__ = True
        diffs: dict[str, Any] = {}
        EBT._append_diff(diffs, "raises", EBT._exception_diff(post, outcome))
        if post.returns is not UNSPECIFIED:
            EBT._append_diff(diffs, "returns", EBT._return_diff(post, outcome))
        if post.arena:
            EBT._append_diff(diffs, "arena", EBT._evaluate_arena(post.arena, outcome.arena, ctx.arena_ignores))
        if post.fs:
            EBT._append_diff(diffs, "fs", EBT._filesystem_diff(post, outcome, ctx))
        return diffs

    @staticmethod
    def _exception_diff(post: WorldState, outcome: WorldState) -> dict | None:
        if post.raises is not None:
            return EBT._expected_exception_diff(post.raises, outcome.exception)
        if outcome.exception is not None:
            return {"expected": None, "actual": exception_details(outcome.exception)}
        return None

    @staticmethod
    def _expected_exception_diff(expected: ExceptionExpectation, error: Exception | None) -> dict | None:
        matches = (
            qualified_name(expected.exception_type) in error.type_mro
            if isinstance(error, RemoteException) else isinstance(error, expected.exception_type)
        )
        if matches and (expected.match is None or re.search(expected.match, str(error)) is not None):
            return None
        return {
            "expected": {"type": qualified_name(expected.exception_type), "match": expected.match},
            "actual": exception_details(error),
        }

    @staticmethod
    def _return_diff(post: WorldState, outcome: WorldState) -> dict | None:
        if outcome.exception is not None:
            return {"expected": str(post.returns), "error": "Target raised instead of returning."}
        return EBT._evaluate_func(post, outcome)

    @staticmethod
    def _filesystem_diff(post: WorldState, outcome: WorldState, ctx: EBTContext) -> dict | None:
        if not isinstance(post.fs, dict):
            raise TypeError("STATE-GUARD: post_state.fs must be a dict.")
        return EBT._evaluate_fs(post.fs, outcome.fs, ctx.fs_ignores)

    @staticmethod
    def _append_diff(diffs: dict, key: str, val: Any) -> None:
        """Validates the data type and appends identified diffs to the target dictionary."""
        __tracebackhide__ = True
        if val is not None:
            if not isinstance(val, dict):
                raise TypeError(f"STATE-GUARD: {key} evaluation must return a dict.")
            diffs[key] = val

    @staticmethod
    def _evaluate_arena(expected_arena: Any, outcome_arena: Optional[str], arena_ignores: Set[str]) -> Optional[dict]:
        """Compare the expected and observed arena topology."""
        __tracebackhide__ = True
        if not isinstance(expected_arena, str) and not hasattr(expected_arena, "env_path"):
            return None if outcome_arena is None else {"error": "Unexpected arena present in outcome."}
        if not outcome_arena:
            return {"error": "Outcome arena is completely missing."}
        host = Path(expected_arena) if isinstance(expected_arena, str) else Path(str(expected_arena.env_path))
        actual = Path(outcome_arena)
        if not actual.exists() or not host.exists():
            return {"error": f"Missing paths. Arena: {actual.exists()}, Host: {host.exists()}"}
        return EBT._arena_diff(host, actual, arena_ignores)

    @staticmethod
    def _arena_diff(host: Path, actual: Path, ignores: set[str]) -> dict | None:
        return EBT._generate_diff(
            EBT._collect_topology(host, ignores, is_arena=True),
            EBT._collect_topology(actual, ignores, is_arena=True),
        )

    @staticmethod
    def _evaluate_fs(expected_fs: dict, outcome_fs: Optional[str], fs_ignores: Set[str]) -> Optional[dict]:
        """Compare each declared filesystem scope or callable predicate."""
        __tracebackhide__ = True
        if not outcome_fs:
            return {"error": "Outcome FS is missing."}
        diffs = {}
        for relative, expected in expected_fs.items():
            actual = Path(outcome_fs) / relative
            diff = EBT._filesystem_entry(actual, expected, fs_ignores)
            if diff:
                diffs[relative] = diff
        return diffs or None

    @staticmethod
    def _filesystem_entry(actual: Path, expected: Any, ignores: set[str]) -> dict | None:
        if not callable(expected):
            return EBT._compare_paths(actual, Path(expected), ignores)
        try:
            return None if expected(actual) else {"error": "Callable eval failed."}
        except Exception as error:
            return {"error": f"Callable raised Exception: {error}"}

    @staticmethod
    def _compare_paths(arena_path: Path, host_path: Path, fs_ignores: Set[str]) -> Optional[dict]:
        """Compares individual files or delegates recursive deep scans to the diff generator."""
        __tracebackhide__ = True
        if not arena_path.exists() or not host_path.exists():
            return {"error": f"Path not found. Arena: {arena_path.exists()}, Host: {host_path.exists()}"}
        if host_path.is_dir() and arena_path.is_dir():
            return EBT._generate_diff(
                EBT._collect_topology(host_path, fs_ignores), EBT._collect_topology(arena_path, fs_ignores)
            )
        if host_path.is_file() and arena_path.is_file():
            # Diff entries are relative to the compared object. A single file
            # denotes itself, independently of its host reference's basename.
            if not same_contents(arena_path, host_path):
                return {"modified": ["."]}
            return None
        return {"error": "Topology mismatch (file vs dir)."}

    @staticmethod
    def _evaluate_func(post_state: WorldState, outcome: WorldState) -> Optional[dict]:
        """Evaluates functional return values dynamically."""
        __tracebackhide__ = True
        if EBT._compare(post_state.returns, outcome.returns):
            return None
        return {"expected": str(post_state.returns), "actual": outcome.returns}

    @staticmethod
    def _compare(exp: Any, act: Any) -> bool:
        """Route patterns to their matching strategy."""
        if exp is Any:
            return True
        if EBT._is_union(exp):
            return EBT._cmp_union(exp, act)
        if isinstance(exp, type):
            return isinstance(act, exp)
        if isinstance(exp, re.Pattern):
            return EBT._cmp_regex(exp, act)
        return EBT._compare_value(exp, act)

    @staticmethod
    def _compare_value(exp: Any, act: Any) -> bool:
        if callable(exp):
            return EBT._cmp_call(exp, act)
        if isinstance(exp, (dict, list, tuple)):
            return EBT._cmp_nest(exp, act)
        return exp == act

    # ---------- UTILITIES ---------------------------------------------------------------------------------------------

    # ↓ ========== _arrange() ========== ↓

    @staticmethod
    def _ensure_list(raw_value: WorldState | list[WorldState] | None, field: str = "state") -> list[WorldState]:
        """Normalize and validate a nonempty list of WorldStates."""
        __tracebackhide__ = True
        if raw_value is None:
            return [WorldState()]
        if isinstance(raw_value, WorldState):
            return [raw_value]
        EBT._validate_states(raw_value, field)
        return raw_value

    @staticmethod
    def _validate_states(states: Any, field: str) -> None:
        if not isinstance(states, list):
            raise TypeError(
                f"STATE-GUARD: {field} must be a WorldState, a list of WorldStates or None; "
                f"received {type(states).__name__}."
            )
        if not states:
            raise ValueError(f"STATE-GUARD: {field} must not be an empty list.")
        for index, state in enumerate(states):
            if not isinstance(state, WorldState):
                raise TypeError(f"STATE-GUARD: {field}[{index}] must be a WorldState; received {type(state).__name__}.")

    @staticmethod
    def _normalize_fs(fs_raw: Any, field: str = "fs") -> dict:
        """Normalize filesystem shorthand while rejecting ambiguous basenames."""
        __tracebackhide__ = True
        if not fs_raw:
            return {}
        if isinstance(fs_raw, dict):
            return fs_raw
        if isinstance(fs_raw, (set, list, tuple)):
            return EBT._filesystem_mapping(fs_raw, field)
        raise ValueError(f"Invalid type for {field}: {type(fs_raw)}")

    @staticmethod
    def _filesystem_mapping(paths, field: str) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for value in paths:
            path = Path(str(value).rstrip("/"))
            if path.name in normalized and Path(normalized[path.name]) != path:
                raise ValueError(
                    f"STATE-GUARD: {field}: ambiguous destination {path.name!r} for sources "
                    f"{normalized[path.name]!r} and {str(value)!r}; use an explicit destination-to-source mapping."
                )
            normalized.setdefault(path.name, str(value))
        return normalized

    @staticmethod
    def _normalize_args(args_raw: Any) -> tuple:
        """Normalizes the arguments into a tuple and prevents accidental string unpacking."""
        __tracebackhide__ = True
        if args_raw is None:
            return ()
        if isinstance(args_raw, (list, tuple)):
            return tuple(args_raw)
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
        try:
            return bool(exp(act))
        except (TypeError, ValueError, AttributeError, KeyError, IndexError):
            return False

    @staticmethod
    def _cmp_nest(exp: Any, act: Any) -> bool:
        """Recursively evaluates nested data structures."""
        if isinstance(exp, dict) and isinstance(act, dict):
            if exp.keys() != act.keys():
                return False
            return all(EBT._compare(exp[k], act[k]) for k in exp)
        if isinstance(exp, (list, tuple)) and isinstance(act, (list, tuple)):
            if len(exp) != len(act):
                return False
            return all(EBT._compare(e, a) for e, a in zip(exp, act))
        return False

    @staticmethod
    def _generate_diff(expected: dict[Path, Path], actual: dict[Path, Path]) -> Optional[dict]:
        """Describe missing, unexpected and modified paths."""
        __tracebackhide__ = True
        exp_keys, act_keys = set(expected), set(actual)
        diff = {
            "missing": [str(path) for path in sorted(exp_keys - act_keys)],
            "unexpected": [str(path) for path in sorted(act_keys - exp_keys)],
            "modified": EBT._modified_paths(expected, actual),
        }
        return {key: value for key, value in diff.items() if value} or None

    @staticmethod
    def _modified_paths(expected: dict[Path, Path], actual: dict[Path, Path]) -> list[str]:
        modified = []
        for path in sorted(expected.keys() & actual.keys()):
            exp, act = expected[path], actual[path]
            if exp.is_dir() != act.is_dir() or (exp.is_file() and not same_contents(act, exp)):
                modified.append(str(path))
        return modified

    @staticmethod
    def _collect_topology(base_dir: Path, ignores: Set[str], is_arena: bool = False) -> dict[Path, Path]:
        """Collect regular files and directories, including empty ones, within scope."""
        __tracebackhide__ = True
        files = {}
        for item in base_dir.rglob("*"):
            if not (item.is_file() or item.is_dir()):
                continue
            rel_path = item.relative_to(base_dir)
            if any(p in ignores for p in rel_path.parts):
                continue
            if is_arena and (item.suffix == ".pyc" or any(p.endswith(".dist-info") for p in rel_path.parts)):
                continue
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
        for t in self._traces:
            steps.setdefault(t.step_id, []).append(t)
        return steps
