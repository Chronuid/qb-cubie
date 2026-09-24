import os, tempfile, shutil, uuid, warnings
from pathlib import Path
from typing import Any, Optional
from ..protocols import WorldState


class TempFS:
    """
    Executes targets directly within the host process and encapsulates file system operations in an ephemeral workspace.
    """
    def __init__(
            self,
            custom_id: str | None = None
    ):
        self.custom_id = custom_id or f"{self.__class__.__name__.lower()}"
        self.arena_id = f"cubie_arena_{self.custom_id}_{uuid.uuid4().hex[:8]}"
        self.workspace_path: Optional[Path] = None
        self._original_cwd: Optional[Path] = None
        self._config_state: Optional[WorldState] = None
        self._actual_returns: Any = None

    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(
            self,
            target: Any,
            args: tuple,
            kwargs: dict,
            state: Optional[WorldState] = None
    ) -> Any:
        """Encapsulates the entire lifecycle of the arena for standalone invocations."""
        __tracebackhide__ = True
        self.setup(state or WorldState())
        try: return self.execute(target, args, kwargs)
        finally: self.teardown()

    def setup(self, state: WorldState) -> None:
        """Creates the temporary workspace and projects the declared host files into it."""
        __tracebackhide__ = True
        self._config_state = state
        if state.arena: warnings.warn(
            "TempFS is not intended for venv or side-package isolation; use PyVenv instead.")
        workspace_dir = tempfile.mkdtemp(prefix=f"{self.arena_id}_")
        self.workspace_path = Path(workspace_dir)
        if self.workspace_path is None: raise RuntimeError("STATE-GUARD: 'workspace_path' could not be created.")
        self._hydrate()

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Executes the target directly but precisely encapsulates the execution within the isolated workspace."""
        __tracebackhide__ = True
        self._switch_cwd_to_workspace()
        try:
            self._actual_returns = target(*args, **kwargs)
            return self._actual_returns
        finally: self._restore_original_cwd()

    def get_state(self) -> WorldState:
        """Packages and returns the mutated environment reality as a complete WorldState."""
        __tracebackhide__ = True
        if self._config_state is None: raise RuntimeError("STATE-GUARD: Missing config state.")
        processing_fs = str(self.workspace_path.absolute()) if self.workspace_path else None
        return WorldState(
            args=self._config_state.args,
            kwargs=self._config_state.kwargs,
            arena=None,
            fs=processing_fs,
            returns=self._actual_returns,
            expect=self._config_state.expect
        )

    def teardown(self) -> None:
        """Completely destroys the ephemeral workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None: raise RuntimeError(
            "STATE-GUARD: Teardown was started, but 'workspace_path' is missing.")
        if self.workspace_path.exists(): shutil.rmtree(self.workspace_path)
        self.workspace_path = None

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _hydrate(self) -> None:
        """Projects the declared files and folders from the host into the Arena workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None or self._config_state is None: raise RuntimeError(
            "STATE-GUARD: 'workspace_path' or '_config_state' is missing.")
        if not self._config_state.fs: return
        for target_rel_path, host_source_path in self._config_state.fs.items():
            source = Path(host_source_path)
            target = self.workspace_path / target_rel_path
            if not source.exists(): raise FileNotFoundError(f"Host path for FS mapping not found: {source}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir(): shutil.copytree(source, target, symlinks=True, dirs_exist_ok=True)
            else: shutil.copy2(source, target)

    def _switch_cwd_to_workspace(self) -> None:
        """Saves the host's current working directory and switches to the temporary workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None: raise RuntimeError("STATE-GUARD: 'workspace_path' is missing for CWD change.")
        self._original_cwd = Path.cwd()
        os.chdir(self.workspace_path)

    def _restore_original_cwd(self) -> None:
        """Switches back to the secured host working directory."""
        __tracebackhide__ = True
        if self._original_cwd is not None:
            os.chdir(self._original_cwd)
            self._original_cwd = None