import multiprocessing
import pickle
import shutil
import sys
import tempfile
import uuid
import warnings
from pathlib import Path
from typing import Any

import cloudpickle

from ..protocols import WorldState
from ._hydration import hydrate_workspace
from ._process import run_process, validate_limits


class TempFS:
    """
    Executes targets in a fresh host-interpreter process with an ephemeral workspace.

    The caller's CWD is never changed. Targets, arguments and results must be
    cloudpickle-serializable; target mutations of host Python objects are not
    shared back. Use a separate arena instance for each active lifecycle.

    Hydration destinations are confined to the workspace. This does not restrict
    target OS rights: inputs, targets and Cloudpickle results must be trusted.

    Optional POSIX limits: timeout in seconds and a combined stdout/stderr
    budget in bytes. Output-limited runs replay output after exit.
    """
    def __init__(
            self,
            custom_id: str | None = None,
            *,
            timeout: float | None = None,
            max_output_bytes: int | None = None,
    ):
        validate_limits(timeout, max_output_bytes)
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self.custom_id = custom_id or f"{self.__class__.__name__.lower()}"
        self.arena_id = f"cubie_arena_{self.custom_id}_{uuid.uuid4().hex[:8]}"
        self.workspace_path: Path | None = None
        self._config_state: WorldState | None = None
        self._actual_returns: Any = None

    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(
            self,
            target: Any,
            args: tuple,
            kwargs: dict,
            state: WorldState | None = None
    ) -> Any:
        """Encapsulates the entire lifecycle of the arena for standalone invocations."""
        __tracebackhide__ = True
        try:
            self.setup(state or WorldState())
            return self.execute(target, args, kwargs)
        finally:
            if self.workspace_path is not None:
                self.teardown()

    def setup(self, state: WorldState) -> None:
        """Creates the temporary workspace and projects the declared host files into it."""
        __tracebackhide__ = True
        self._config_state = state
        self._actual_returns = None
        if state.arena: warnings.warn(
            "TempFS is not intended for venv or side-package isolation; use PyVenv instead.")
        workspace_dir = tempfile.mkdtemp(prefix=f"{self.arena_id}_")
        self.workspace_path = Path(workspace_dir)
        if self.workspace_path is None: raise RuntimeError("STATE-GUARD: 'workspace_path' could not be created.")
        self._hydrate()

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Runs the target in a child whose CWD is the workspace, preserving host CWD."""
        __tracebackhide__ = True
        if self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: 'workspace_path' is missing for target execution.")
        self._actual_returns = None
        # IPC files live outside the workspace so FS postconditions see only
        # hydrated files and target output, including while evaluation runs.
        with tempfile.TemporaryDirectory(prefix=f"{self.arena_id}_ipc_") as ipc_dir:
            input_path = Path(ipc_dir) / "input.pkl"
            output_path = Path(ipc_dir) / "output.pkl"
            import_paths = [str(Path(entry).absolute()) for entry in sys.path]
            with input_path.open("wb") as stream:
                # Manager proxies passed as arguments authenticate using the
                # calling process's key, including inside EBT process workers.
                pickle.dump((import_paths, bytes(multiprocessing.current_process().authkey)), stream)
                cloudpickle.dump((target, args, kwargs), stream)
            runner = Path(__file__).with_name("_tempfs_runner.py").resolve()
            process = run_process(
                [sys.executable, str(runner), str(input_path), str(output_path)],
                cwd=self.workspace_path,
                timeout=self.timeout, max_output_bytes=self.max_output_bytes,
            )
            if self.max_output_bytes is not None:
                for stream, payload in ((sys.stdout, process.stdout), (sys.stderr, process.stderr)):
                    if hasattr(stream, "buffer"):
                        stream.buffer.write(payload)
                        stream.buffer.flush()
                    else:
                        stream.write(payload.decode(errors="replace"))
                        stream.flush()
            if process.returncode != 0 or not output_path.is_file():
                raise RuntimeError(
                    f"TempFS target process exited with code {process.returncode} "
                    "without a complete result."
                )
            with output_path.open("rb") as stream:
                succeeded, result, remote_traceback = cloudpickle.load(stream)
            if not succeeded:
                result.add_note(f"TempFS child traceback:\n{remote_traceback}")
                raise result
            self._actual_returns = result
            return result

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
        hydrate_workspace(self.workspace_path, self._config_state.fs)
