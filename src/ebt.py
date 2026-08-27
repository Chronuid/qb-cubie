from typing import Union, List, runtime_checkable
from dataclasses import dataclass
from pyvenv import *
import filecmp, inspect


# ========== PROTOCOLS & DATACLASSES ===================================================================================

@runtime_checkable
class Arena(Protocol):
    """
    Contract for isolated execution environments.
    """
    @property
    def fs(self) -> dict:
        """Overwritten by EBT with the normalized pre.fs state before setup."""
        # EBT injects a dictionary here before setup() is called, in the format:
        # {'target_path_in_arena': 'host_source_path_as_string'} ...

    @fs.setter
    def fs(self, value: dict) -> None: ...

    @property
    def workspace_path(self) -> Optional[Path]:
        """Set in `setup()` and read by EBT to diff the post-state."""
        # Must return the absolute path to the isolated working directory after setup().
        # EBT strictly requires this path for byte-level diffing during the _report() phase. ...

    def setup(self) -> None:
        """Creates the temporary workspace and hydrates the declared files from `self.fs`."""
        # Must create an isolated directory and place it in `self.workspace_path`.
        # Must project the host files defined in `self.fs` into the workspace.
        # Guarantees the integrity of the host process's workspace. ...

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Executes the target within an isolated workspace and returns the result."""
        # The target must be invoked within the context of `workspace_path` (via CWD change or subprocess).
        # System and runtime errors from the target should be propagated transparently.
        # The target's result must be returned to EBT unmodified. ...

    def teardown(self) -> None:
        """Destroys the workspace and cleans up all temporary environment states."""
        # Must completely delete the folder defined in `self.workspace_path`.
        # Must restore all temporarily modified global host states. ...


@dataclass
class WorldState:
    """
    Declares execution environments, file system states, and functional parameters of a test world.
    """
    arena: Any = None
    args: Any = None
    kwargs: Any = None
    returns: Any = None
    fs: Any = None


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
            expect: bool = True or False
    ):
        if inspect.isclass(arena):
            raise TypeError(f"STATE-GUARD: 'arena' must be an instance. "
            f"Use '{arena.__name__}()' instead of '{arena.__name__}'.")
        self.target = target
        self.arena = arena
        self.pre = pre or WorldState()
        self.post = post or WorldState()
        self.expect = expect

        self._active_pre: WorldState = WorldState()
        self._active_post: WorldState = WorldState()
        self._actual_returns: Any = None

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
        self._set_element()

    def _validate(self) -> None:
        """Executes the target with the defined input parameters of the pre-state."""
        __tracebackhide__ = True
        args = self._normalize_args(self._active_pre.args)
        kwargs = self._active_pre.kwargs if self._active_pre.kwargs is not None else {}
        self._execute_target(args, kwargs)

    def _report(self) -> None:
        """Compares the actual result with the expected post-state."""
        __tracebackhide__ = True
        if self._active_post.returns: self._assert_func()
        if self._active_post.fs: self._assert_fs()

    # ----- Utilities --------------------------------------------------------------------------------------------------

    # ↓--- _arrange() ---↓

    def _set_element(self):
        """Normalizes the pre- and post-declarations into a single element."""
        if isinstance(self.pre, list) or isinstance(self.post, list):
            raise NotImplementedError("Quantifiers (lists) are not implemented until Phase 5.")
        self._active_pre = self.pre if isinstance(self.pre, WorldState) else WorldState()
        self._active_post = self.post if isinstance(self.post, WorldState) else WorldState()
        self._active_pre.fs = self._normalize_fs(self._active_pre.fs)
        self._active_post.fs = self._normalize_fs(self._active_post.fs)
        if self.arena is not None:
            self.arena.fs = self._active_pre.fs
            self.arena.setup()

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

    def _execute_target(self, args: tuple, kwargs: dict) -> None:
        """Encapsulates the actual function call within the correct context (arena or in-memory)."""
        __tracebackhide__ = True
        if self.arena: self._actual_returns = self.arena.execute(self.target, args, kwargs)
        else: self._actual_returns = self.target(*args, **kwargs)

    # ↓--- _report() ---↓

    def _assert_func(self):
        if self.expect: assert self._actual_returns == self._active_post.returns
        else: assert self._actual_returns != self._active_post.returns

    def _assert_fs(self) -> None:
        """Performs a byte-by-byte diff between the post-arena workspace and post-declarations."""
        __tracebackhide__ = True
        if self.arena is None or not hasattr(self.arena, "workspace_path") or self.arena.workspace_path is None:
            raise RuntimeError("STATE-GUARD: Arena or 'workspace_path' is missing for FS assertion.")
        for target_rel_path, host_source_path in self._active_post.fs.items():
            arena_path = Path(self.arena.workspace_path) / target_rel_path
            host_path = Path(host_source_path)
            assert arena_path.exists(), f"FS-Assert failed: File/folder missing in the arena: {target_rel_path}"
            assert host_path.exists(), f"FS-Assert failed: Host comparison file missing: {host_source_path}"
            is_match = self._compare_paths(arena_path, host_path)
            if self.expect: assert is_match, f"FS-Assert failed: File contents differ for {target_rel_path}"
            else: assert not is_match, f"FS-Assert failed (negative test): Unexpected Match at {target_rel_path}"

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