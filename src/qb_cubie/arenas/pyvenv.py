import locale
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, List, Optional

from ..protocols import IPCC, WorldState
from ._hydration import hydrate_workspace
from ._process import run_process, validate_limits
from ._requirements import _environment_python, _requirements_satisfied
from .codecs import MSGspecCodec

# ========== PYVENV-ARENA ==============================================================================================

CURRENT_DIR = Path(__file__).parent
class PyVenv:
    """
    Executes targets in a child process using an ephemeral virtual Python environment.

    Hydration destinations are confined to the workspace. Targets retain host
    OS rights; sources, base environments, targets and IPC results must be trusted.

    Optional POSIX limits: timeout in seconds and a shared stdout/stderr budget
    in bytes. Neither limit includes environment provisioning or cloning.
    """
    def __init__(
            self,
            env_path: str = str(CURRENT_DIR / "arena_envs" / "empty_test_env"),
            codec: Optional[IPCC] = None,
            decontams: Optional[List] = None,
            custom_id: str | None = None,
            *,
            timeout: float | None = None,
            max_output_bytes: int | None = None,
    ):
        validate_limits(timeout, max_output_bytes)
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self.codec = codec or MSGspecCodec()
        self.custom_id = custom_id or f"{self.__class__.__name__.lower()}"
        self.arena_id = f"cubie_arena_{self.custom_id}_{uuid.uuid4().hex[:8]}"
        self.env_path = Path(env_path)
        self.workspace_path: Optional[Path] = None
        self.virtual_path: Optional[Path] = None
        self._config_state: Optional[WorldState] = None
        self._actual_returns: Any = None
        self._python_exe: Optional[Path] = None
        self._env_vars: Optional[dict] = None
        self._in_path: Optional[str] = None
        self._out_path: Optional[str] = None
        self._process: Optional[subprocess.CompletedProcess] = None
        self._decontams = ["pytest", "_pytest", "loky"]
        if decontams: self._decontams.extend(decontams)

    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(self, target: Any, args: tuple, kwargs: dict, state: Optional[WorldState] = None) -> Any:
        """Encapsulates the entire lifecycle of the arena for standalone invocations."""
        __tracebackhide__ = True
        try:
            self.setup(state or WorldState())
            return self.execute(target, args, kwargs)
        finally:
            if self.workspace_path is not None:
                self.teardown()

    def setup(self, state: WorldState) -> None:
        """Creates an ephemeral clone of the virtual environment based on the configured state."""
        __tracebackhide__ = True
        self._config_state = state
        base_env = Path(state.arena) if isinstance(state.arena, str) else self.env_path
        if not base_env.exists():
            raise RuntimeError(
                f"STATE-GUARD: Base arena not found: {base_env}. "
                "Provision it explicitly with ArenaBuilder(path).build() before running PyVenv."
            )
        self._ensure_codec_requirements(base_env)
        self.workspace_path = Path(tempfile.mkdtemp(prefix=f"{self.arena_id}_"))
        if self.workspace_path is None: raise RuntimeError("STATE-GUARD: Missing virtual environment.")
        self.virtual_path = self.workspace_path / ".venv"
        shutil.copytree(base_env, str(self.virtual_path), symlinks=True)
        self._hydrate()

    def execute(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Executes the target in the subprocess and caches the functional returns."""
        __tracebackhide__ = True
        self._get_python_exe()
        self._prepare_env()
        self._actual_returns = None
        self._process = None
        self._actual_returns = self._run_in_subprocess(target, args, kwargs)
        return self._actual_returns

    def get_state(self) -> WorldState:
        """Packages and returns the mutated environment reality as a complete WorldState."""
        __tracebackhide__ = True
        if self._config_state is None: raise RuntimeError("STATE-GUARD: Missing config state.")
        processing_fs = str(self.workspace_path.absolute()) if self.workspace_path else None
        return WorldState(
            args=self._config_state.args,
            kwargs=self._config_state.kwargs,
            arena=str(self.virtual_path.absolute()) if self.virtual_path else None,
            fs=processing_fs,
            returns=self._actual_returns,
            expect=self._config_state.expect
        )

    def teardown(self) -> None:
        """Completely destroys the ephemeral clone and restores the original state."""
        __tracebackhide__ = True
        if self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: Teardown was started, but 'workspace_path' is missing.")
        if self.workspace_path.exists(): shutil.rmtree(self.workspace_path)
        self.workspace_path = None
        self.virtual_path = None

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _hydrate(self) -> None:
        """Projects the declared files and folders from the host into the Arena workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None or self._config_state is None:
            raise RuntimeError("STATE-GUARD: 'workspace_path' or '_config_state' is missing.")
        if not self._config_state.fs: return
        hydrate_workspace(self.workspace_path, self._config_state.fs)

    def _ensure_codec_requirements(self, base_env_path: Path) -> None:
        """Validates codec dependencies without installing or modifying the base."""
        requirements = getattr(self.codec, "requirements", [])
        if not requirements: return
        python_exe = _environment_python(base_env_path)
        if _requirements_satisfied(python_exe, requirements): return
        raise RuntimeError(
            f"Arena codec requirements are not satisfied in {base_env_path}: {requirements}. "
            "Provision the base explicitly with "
            "ArenaBuilder(path).build(codec=codec) before running PyVenv. "
            "PyVenv.setup() does not install packages."
        )

    def _get_python_exe(self) -> None:
        __tracebackhide__ = True
        if self.virtual_path is None: raise RuntimeError("STATE-GUARD: 'virtual_path' was not initialized.")
        exe = _environment_python(self.virtual_path)
        if not exe.exists(): raise RuntimeError(f"Python Arena missing: {exe}")
        self._python_exe = exe

    def _prepare_env(self) -> None:
        """Simulates 'source activate' for the subprocess and injects the code."""
        __tracebackhide__ = True
        self._env_vars = os.environ.copy()
        self._inject_project_code()
        self._activate_arena_env()

    def _run_in_subprocess(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Wraps the callable, executes it in the arena, and unwraps the result."""
        __tracebackhide__ = True
        if self._python_exe is None or self._env_vars is None:
            raise RuntimeError("STATE-GUARD: Python executable or environment is missing.")
        self._setup_ipc_files()
        try:
            self._serialize_inputs(target, args, kwargs)
            self._invoke_script()
            return self._deserialize_outputs()
        finally: self._teardown_ipc_files()

    def _invoke_script(self) -> None:
        """Generates the runner script and launches the subprocess in the arena."""
        __tracebackhide__ = True
        script = self._generate_runner_script()
        self._execute_runner_script(script)

    # ----- Utilities --------------------------------------------------------------------------------------------------

    # ↓--- _prepare_env() ---↓

    def _inject_project_code(self) -> None:
        """Isolates PYTHONPATH from host packages and blocks PYTHONHOME."""
        __tracebackhide__ = True
        if self._env_vars is None: raise RuntimeError("STATE-GUARD: '_env_vars' was not initialized.")
        safe_paths = [p for p in sys.path if "site-packages" not in p and "dist-packages" not in p]
        self._env_vars["PYTHONPATH"] = os.pathsep.join(safe_paths)
        self._env_vars.pop("PYTHONHOME", None)

    def _activate_arena_env(self) -> None:
        """Selects the copied environment via PATH and VIRTUAL_ENV without restricting OS rights."""
        __tracebackhide__ = True
        if self._env_vars is None or self.virtual_path is None:
            raise RuntimeError("STATE-GUARD: '_env_vars' or 'virtual_path' was not initialized.")
        self._env_vars["VIRTUAL_ENV"] = str(self.virtual_path.absolute())
        bin_dir = self.virtual_path / "bin" if (self.virtual_path / "bin").exists() else self.virtual_path / "Scripts"
        self._env_vars["PATH"] = f"{bin_dir.absolute()}{os.pathsep}{self._env_vars.get('PATH', '')}"

    # ↓--- _run_in_subprocess() ---↓

    def _setup_ipc_files(self) -> None:
        """Creates temporary files for data exchange and injects the phantom middleware."""
        __tracebackhide__ = True
        if self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: 'workspace_path' was not initialized.")
        self._in_path = str(self.workspace_path / f"ipc_in{self.codec.file_suffix}")
        self._out_path = str(self.workspace_path / f"ipc_out{self.codec.file_suffix}")
        phantom_src = CURRENT_DIR / "phantom_hook.py"
        if not phantom_src.exists():
            raise FileNotFoundError(f"STATE-GUARD: Phantom-Middleware missing at {phantom_src}")
        shutil.copy2(phantom_src, self.workspace_path / "_cubie_phantom.py")

    def _serialize_inputs(self, target: Any, args: tuple, kwargs: dict) -> None:
        """Serializes the target and its parameters into the input file."""
        __tracebackhide__ = True
        if self._in_path is None: raise RuntimeError("STATE-GUARD: '_in_path' was not initialized.")
        self.codec.dump((target, args, kwargs, self._decontams), self._in_path)

    def _deserialize_outputs(self) -> Any:
        """Reads the output of the subprocess and throws the appropriate exception in case of errors."""
        __tracebackhide__ = True
        if self._out_path is None: raise RuntimeError("STATE-GUARD: '_out_path' was not initialized.")
        status, result = self.codec.load(self._out_path)
        if status == "ERROR": raise RuntimeError(f"Arena Error: {result}")
        return result

    def _teardown_ipc_files(self) -> None:
        """Cleans up temporary files after execution completes and resets the state."""
        __tracebackhide__ = True
        if self._in_path and os.path.exists(self._in_path): os.remove(self._in_path)
        if self._out_path and os.path.exists(self._out_path): os.remove(self._out_path)
        self._in_path = None
        self._out_path = None

    # ↓--- _invoke_script() ---↓

    def _generate_runner_script(self) -> str:
        """Generates the Python source code for the isolated execution wrapper."""
        __tracebackhide__ = True
        if self._in_path is None or self._out_path is None:
            raise RuntimeError("STATE-GUARD: In/out paths for script generation are missing.")
        return self.codec.get_runner_snippet(self._in_path, self._out_path)

    def _execute_runner_script(self, script: str) -> None:
        """Starts the subprocess with the generated script and catches system errors."""
        __tracebackhide__ = True
        if self._python_exe is None or self._env_vars is None or self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: Python executable, environment, or workspace is missing.")
        cmd_args = [str(self._python_exe), "-c", script]
        self._process = run_process(
            cmd_args,
            env=self._env_vars,
            cwd=self.workspace_path,
            capture_output=True,
            timeout=self.timeout, max_output_bytes=self.max_output_bytes,
        )
        encoding = locale.getpreferredencoding(False)
        for channel in ("stdout", "stderr"):
            payload = getattr(self._process, channel)
            text = payload.decode(encoding, errors="replace").replace("\r\n", "\n").replace("\r", "\n")
            setattr(self._process, channel, text)
        self._raise_arena_error()

    def _raise_arena_error(self):
        """Reports arena runtime errors."""
        __tracebackhide__ = True
        if self._process is None: raise RuntimeError("STATE-GUARD: '_process' was not initialized.")
        if self._process.returncode != 0:
            raise RuntimeError(
                f"Arena System-Error (Exit Code {self._process.returncode}):\n"
                f"STDOUT: {self._process.stdout}\n"
                f"STDERR: {self._process.stderr}"
            )


# ========== ARENA-BUILDER =============================================================================================

class ArenaBuilder:
    """
    Programmatically provisions base environments and constructs PyVenv arenas via a fluent interface.
    """
    def __init__(self, env_path: str):
        self.env_path = Path(env_path)
        self._packages: list[str] = []

    # ----- Services ---------------------------------------------------------------------------------------------------

    def with_packages(self, packages: list[str]) -> 'ArenaBuilder':
        """Registers a list of packages to be installed in the arena."""
        __tracebackhide__ = True
        self._packages.extend(packages)
        return self

    def build(self, codec: Optional[IPCC] = None) -> PyVenv:
        """Explicitly provisions packages and codec dependencies, then returns the arena."""
        __tracebackhide__ = True
        arena = PyVenv(env_path=str(self.env_path), codec=codec)
        self._ensure_venv_exists()
        packages = list(dict.fromkeys([*self._packages, *getattr(arena.codec, "requirements", [])]))
        if packages: self._install_packages(packages)
        return arena

    # ----- Utilities --------------------------------------------------------------------------------------------------

    def _ensure_venv_exists(self) -> None:
        """Creates a new uv virtual environment if the target path does not already exist."""
        __tracebackhide__ = True
        if self.env_path.exists(): return
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["uv", "venv", str(self.env_path), "--python", sys.executable],
                check=True, capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ArenaBuilder failed to create venv:\n{e.stderr.decode()}")

    def _install_packages(self, packages: list[str]) -> None:
        """Installs the requested packages and codec dependencies in the base."""
        __tracebackhide__ = True
        python_exe = _environment_python(self.env_path)
        if _requirements_satisfied(python_exe, packages): return
        try:
            subprocess.run(
                ["uv", "pip", "install", *packages, "--python", str(python_exe)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ArenaBuilder failed to install packages {packages}:\n{e.stderr.decode()}")
