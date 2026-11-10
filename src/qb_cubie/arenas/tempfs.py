import multiprocessing
import pickle
import subprocess
import shutil
import sys
import tempfile
import uuid
import warnings
from pathlib import Path
from typing import Any

import cloudpickle  # type: ignore[import-untyped]

from ..protocols import WorldState
from ._hydration import hydrate_workspace
from ._process import run_process, validate_limits


class TempFS:
    """Executes targets in a fresh host-interpreter process with an ephemeral workspace."""

    # The caller's CWD is never changed. Targets, arguments and results must be
    # cloudpickle-serializable; target mutations of host Python objects are not
    # shared back. Use a separate arena instance for each active lifecycle.
    #
    # Hydration destinations are confined to the workspace. This does not restrict
    # target OS rights: inputs, targets and Cloudpickle results must be trusted.
    #
    # Optional POSIX limits: timeout in seconds and a combined stdout/stderr
    # budget in bytes. Output-limited runs replay output after exit.

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

    def run(self, target: Any, args: tuple, kwargs: dict, state: WorldState | None = None) -> Any:
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
        if state.arena:
            warnings.warn("TempFS is not intended for venv or side-package isolation; use PyVenv instead.")
        workspace_dir = tempfile.mkdtemp(prefix=f"{self.arena_id}_")
        self.workspace_path = Path(workspace_dir)
        self._hydrate()

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Run the target in a child whose CWD is the workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: 'workspace_path' is missing for target execution.")
        self._actual_returns = None
        # Keep IPC artifacts outside the workspace inspected by FS postconditions.
        with tempfile.TemporaryDirectory(prefix=f"{self.arena_id}_ipc_") as ipc_dir:
            input_path, output_path = Path(ipc_dir) / "input.pkl", Path(ipc_dir) / "output.pkl"
            self._serialize(target, args, kwargs, input_path)
            process = self._invoke(input_path, output_path)
            self._replay_output(process)
            self._actual_returns = self._read_result(process, output_path)
            return self._actual_returns

    def get_state(self) -> WorldState:
        """Packages and returns the mutated environment reality as a complete WorldState."""
        __tracebackhide__ = True
        if self._config_state is None:
            raise RuntimeError("STATE-GUARD: Missing config state.")
        processing_fs = str(self.workspace_path.absolute()) if self.workspace_path else None
        return WorldState(
            args=self._config_state.args,
            kwargs=self._config_state.kwargs,
            arena=None,
            fs=processing_fs,
            returns=self._actual_returns,
            expect=self._config_state.expect,
        )

    def teardown(self) -> None:
        """Completely destroys the ephemeral workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: Teardown was started, but 'workspace_path' is missing.")
        if self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)
        self.workspace_path = None

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    @staticmethod
    def _serialize(target: Any, args: tuple, kwargs: dict, path: Path) -> None:
        import_paths = [str(Path(entry).absolute()) for entry in sys.path]
        with path.open("wb") as stream:
            # Manager proxies authenticate with the caller's key, including in EBT workers.
            pickle.dump((import_paths, bytes(multiprocessing.current_process().authkey)), stream)
            cloudpickle.dump((target, args, kwargs), stream)

    def _invoke(self, input_path: Path, output_path: Path) -> subprocess.CompletedProcess:
        if self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: 'workspace_path' is missing for target execution.")
        runner = Path(__file__).with_name("_tempfs_runner.py").resolve()
        return run_process(
            [sys.executable, str(runner), str(input_path), str(output_path)],
            cwd=self.workspace_path, timeout=self.timeout, max_output_bytes=self.max_output_bytes,
        )

    def _replay_output(self, process: subprocess.CompletedProcess) -> None:
        if self.max_output_bytes is None:
            return
        for stream, payload in ((sys.stdout, process.stdout), (sys.stderr, process.stderr)):
            if hasattr(stream, "buffer"):
                stream.buffer.write(payload)
                stream.buffer.flush()
            else:
                stream.write(payload.decode(errors="replace"))
                stream.flush()

    @staticmethod
    def _read_result(process: subprocess.CompletedProcess, path: Path) -> Any:
        if process.returncode != 0 or not path.is_file():
            raise RuntimeError(
                f"TempFS target process exited with code {process.returncode} without a complete result."
            )
        with path.open("rb") as stream:
            succeeded, result, remote_traceback = cloudpickle.load(stream)
        if not succeeded:
            result.add_note(f"TempFS child traceback:\n{remote_traceback}")
            raise result
        return result

    def _hydrate(self) -> None:
        """Projects the declared files and folders from the host into the Arena workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None or self._config_state is None:
            raise RuntimeError("STATE-GUARD: 'workspace_path' or '_config_state' is missing.")
        if not self._config_state.fs:
            return
        hydrate_workspace(self.workspace_path, self._config_state.fs)
