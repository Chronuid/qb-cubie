import locale
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, List, Optional

from .._execution import CapturedResult, RemoteException
from ..protocols import IPCC, WorldState
from ._hydration import hydrate_workspace
from ._process import run_process, validate_limits
from ._requirements import _environment_python, _requirements_satisfied
from ._relocation import relocate_scripts
from .codecs import MSGspecCodec

# ========== PYVENV-ARENA ==============================================================================================

CURRENT_DIR = Path(__file__).parent
DEFAULT_ARENA_ENV_VAR = "QB_CUBIE_DEFAULT_ARENA"


def default_arena_path() -> Path:
    """Return the default external base arena path for the active Python version."""
    override = os.environ.get(DEFAULT_ARENA_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser()
    tag = f"py{sys.version_info.major}.{sys.version_info.minor}-empty"
    return _cache_root() / "qb-cubie" / "arenas" / tag


def _cache_root() -> Path:
    """Resolve the platform-appropriate user cache root directory."""
    xdg_cache = os.environ.get("XDG_CACHE_HOME", "").strip()
    if xdg_cache:
        return Path(xdg_cache).expanduser()
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
        if local_app_data:
            return Path(local_app_data)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches"
    return Path.home() / ".cache"


def _remove_readonly(func: Any, path: str, exc: BaseException) -> None:
    """Clear read-only bits during tree deletion so Windows and POSIX clones clean up."""
    if not isinstance(exc, PermissionError):
        raise exc
    os.chmod(path, stat.S_IMODE(os.lstat(path).st_mode) | stat.S_IWUSR)
    parent = os.path.dirname(path)
    if func in (os.unlink, os.rmdir) and parent:
        os.chmod(parent, stat.S_IMODE(os.lstat(parent).st_mode) | stat.S_IWUSR | stat.S_IXUSR)
    func(path)


class _ArenaState:
    def __init__(self) -> None:
        self._root_path: Optional[Path] = None
        self.workspace_path: Optional[Path] = None
        self.virtual_path: Optional[Path] = None
        self._config_state: Optional[WorldState] = None
        self._actual_returns: Any = None
        self._python_exe: Optional[Path] = None
        self._env_vars: Optional[dict[str, str]] = None
        self._in_path: Optional[str] = None
        self._out_path: Optional[str] = None
        self._process: Optional[subprocess.CompletedProcess] = None


class PyVenv(_ArenaState):
    """Executes targets in a child process using an ephemeral virtual Python environment."""

    # Hydration destinations are confined to the workspace. Targets retain host
    # OS rights; sources, base environments, targets and IPC results must be trusted.
    #
    # Optional POSIX and Windows limits: timeout in seconds and a shared stdout/stderr
    # budget in bytes. Neither limit includes environment provisioning or cloning.

    def __init__(
        self,
        env_path: str | os.PathLike[str] | None = None,
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
        self.env_path = Path(env_path) if env_path is not None else default_arena_path()
        super().__init__()
        self._decontams = list(decontams or [])


    # ----- Services ---------------------------------------------------------------------------------------------------

    def run(self, target: Any, args: tuple, kwargs: dict, state: Optional[WorldState] = None) -> Any:
        """Encapsulates the entire lifecycle of the arena for standalone invocations."""
        __tracebackhide__ = True
        try:
            self.setup(state or WorldState())
            return self.execute(target, args, kwargs)
        finally:
            if self._root_path is not None or self.workspace_path is not None:
                self.teardown()

    def setup(self, state: WorldState) -> None:
        """Create an ephemeral environment clone and hydrate its workspace."""
        __tracebackhide__ = True
        self._config_state = state
        base_env = self._base_environment(state)
        self._ensure_codec_requirements(base_env)
        virtual_path = self._prepare_directories()
        shutil.copytree(base_env, str(virtual_path), symlinks=True)
        relocate_scripts(base_env, virtual_path)
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
        if self._config_state is None:
            raise RuntimeError("STATE-GUARD: Missing config state.")
        processing_fs = str(self.workspace_path.absolute()) if self.workspace_path else None
        return WorldState(
            args=self._config_state.args,
            kwargs=self._config_state.kwargs,
            arena=str(self.virtual_path.absolute()) if self.virtual_path else None,
            fs=processing_fs,
            returns=self._actual_returns,
            expect=self._config_state.expect,
        )

    def teardown(self) -> None:
        """Completely destroys the ephemeral clone and restores the original state."""
        __tracebackhide__ = True
        if self._root_path is None:
            raise RuntimeError("STATE-GUARD: Teardown was started, but 'workspace_path' is missing.")
        if self._root_path.exists():
            shutil.rmtree(self._root_path, onexc=_remove_readonly)
        self._root_path = None
        self.workspace_path = None
        self.virtual_path = None

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _prepare_directories(self) -> Path:
        """Create separate workspace and venv directories beneath an arena root."""
        root = Path(tempfile.mkdtemp(prefix=f"{self.arena_id}_")).resolve()
        workspace = root / "workspace"
        workspace.mkdir()
        virtual_path = root / ".venv"
        self._root_path = root
        self.workspace_path = workspace
        self.virtual_path = virtual_path
        return virtual_path

    def _base_environment(self, state: WorldState) -> Path:
        base_env = Path(state.arena) if isinstance(state.arena, str) else self.env_path
        if not base_env.exists():
            raise RuntimeError(
                f"STATE-GUARD: Base arena not found: {base_env}. "
                "Provision it explicitly with ArenaBuilder(path).build() before running PyVenv."
            )
        if _environment_python(base_env).exists() and not (base_env / "pyvenv.cfg").is_file():
            raise RuntimeError(
                f"STATE-GUARD: Invalid virtual environment (missing pyvenv.cfg): {base_env}. "
                "Remove any incomplete directory and provision it with ArenaBuilder(path).build()."
            )
        return base_env

    def _hydrate(self) -> None:
        """Projects the declared files and folders from the host into the Arena workspace."""
        __tracebackhide__ = True
        if self.workspace_path is None or self._config_state is None:
            raise RuntimeError("STATE-GUARD: 'workspace_path' or '_config_state' is missing.")
        if not self._config_state.fs:
            return
        hydrate_workspace(self.workspace_path, self._config_state.fs)

    def _ensure_codec_requirements(self, base_env_path: Path) -> None:
        """Validates codec dependencies without installing or modifying the base."""
        requirements = getattr(self.codec, "requirements", [])
        if not requirements:
            return
        python_exe = _environment_python(base_env_path)
        if _requirements_satisfied(python_exe, requirements):
            return
        raise RuntimeError(
            f"Arena codec requirements are not satisfied in {base_env_path}: {requirements}. "
            "Provision the base explicitly with "
            "ArenaBuilder(path).build(codec=codec) before running PyVenv. "
            "PyVenv.setup() does not install packages."
        )

    def _get_python_exe(self) -> None:
        __tracebackhide__ = True
        if self.virtual_path is None:
            raise RuntimeError("STATE-GUARD: 'virtual_path' was not initialized.")
        exe = _environment_python(self.virtual_path)
        if not exe.exists():
            raise RuntimeError(f"Python Arena missing: {exe}")
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
        if self._python_exe is None or self._env_vars is None or self._root_path is None:
            raise RuntimeError("STATE-GUARD: Python executable, environment, or root is missing.")
        with tempfile.TemporaryDirectory(prefix="ipc_", dir=self._root_path) as ipc_dir:
            self._setup_ipc_files(Path(ipc_dir))
            try:
                self._serialize_inputs(target, args, kwargs)
                self._invoke_script()
                return self._deserialize_outputs()
            finally:
                self._teardown_ipc_files()

    def _invoke_script(self) -> None:
        """Generates the runner script and launches the subprocess in the arena."""
        __tracebackhide__ = True
        script = self._generate_runner_script()
        self._execute_runner_script(script)

    # ----- Utilities --------------------------------------------------------------------------------------------------

    # ↓--- _prepare_env() ---↓

    @staticmethod
    def _safe_host_paths() -> list[str]:
        """Collect normalized host import paths while excluding site packages and CWD aliases."""
        paths: list[str] = []
        for entry in sys.path:
            if not entry or entry == ".":
                continue
            lowered = entry.lower()
            if "site-packages" in lowered or "dist-packages" in lowered:
                continue
            paths.append(str(Path(entry).absolute()))
        return paths

    def _inject_project_code(self) -> None:
        """Isolates PYTHONPATH from host packages and blocks PYTHONHOME."""
        __tracebackhide__ = True
        if self._env_vars is None:
            raise RuntimeError("STATE-GUARD: '_env_vars' was not initialized.")
        safe_paths = self._safe_host_paths()
        if safe_paths:
            self._env_vars["PYTHONPATH"] = os.pathsep.join(safe_paths)
        else:
            self._env_vars.pop("PYTHONPATH", None)
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

    def _setup_ipc_files(self, ipc_dir: Path) -> None:
        """Creates temporary files for data exchange and injects the phantom middleware."""
        __tracebackhide__ = True
        if self._env_vars is None:
            raise RuntimeError("STATE-GUARD: '_env_vars' was not initialized.")
        self._in_path = str(ipc_dir / f"ipc_in{self.codec.file_suffix}")
        self._out_path = str(ipc_dir / f"ipc_out{self.codec.file_suffix}")
        phantom_src = CURRENT_DIR / "phantom_hook.py"
        if not phantom_src.exists():
            raise FileNotFoundError(f"STATE-GUARD: Phantom-Middleware missing at {phantom_src}")
        shutil.copyfile(phantom_src, ipc_dir / "_cubie_phantom.py")
        self._prepend_ipc_pythonpath(ipc_dir)

    def _prepend_ipc_pythonpath(self, ipc_dir: Path) -> None:
        """Prepend the temporary IPC directory to PYTHONPATH for child bootstrap."""
        if self._env_vars is None:
            raise RuntimeError("STATE-GUARD: '_env_vars' was not initialized.")
        existing = self._env_vars.get("PYTHONPATH", "")
        ipc_entry = str(ipc_dir.absolute())
        self._env_vars["PYTHONPATH"] = f"{ipc_entry}{os.pathsep}{existing}" if existing else ipc_entry

    def _serialize_inputs(self, target: Any, args: tuple, kwargs: dict) -> None:
        """Serializes the target and its parameters into the input file."""
        __tracebackhide__ = True
        if self._in_path is None:
            raise RuntimeError("STATE-GUARD: '_in_path' was not initialized.")
        self.codec.dump((target, args, kwargs, self._decontams), self._in_path)

    def _deserialize_outputs(self) -> Any:
        """Read the child result and preserve the distinction between target and arena errors."""
        __tracebackhide__ = True
        if self._out_path is None:
            raise RuntimeError("STATE-GUARD: '_out_path' was not initialized.")
        status, result = self.codec.load(self._out_path)
        if status == "ERROR":
            raise RuntimeError(f"Arena Error: {result}")
        if status == "CAPTURED_SUCCESS":
            return CapturedResult(value=result)
        if status == "TARGET_EXCEPTION":
            return self._captured_exception(result)
        return self._successful_result(status, result)

    @staticmethod
    def _captured_exception(result: Any) -> CapturedResult:
        if isinstance(result, dict):
            result = RemoteException(result["type"], result["message"], result["mro"])
        if not isinstance(result, Exception):
            raise TypeError("Invalid captured target exception from arena.")
        return CapturedResult(exception=result)

    @staticmethod
    def _successful_result(status: str, result: Any) -> Any:
        if status != "SUCCESS":
            raise RuntimeError(f"Unknown arena result status: {status!r}")
        return result

    def _teardown_ipc_files(self) -> None:
        """Resets active IPC file path references after execution completes."""
        __tracebackhide__ = True
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
        """Launch the runner and report child process failures."""
        __tracebackhide__ = True
        if self._python_exe is None or self._env_vars is None or self.workspace_path is None:
            raise RuntimeError("STATE-GUARD: Python executable, environment, or workspace is missing.")
        self._process = run_process(
            [str(self._python_exe), "-P", "-c", script], env=self._env_vars,
            cwd=self.workspace_path, capture_output=True,
            timeout=self.timeout, max_output_bytes=self.max_output_bytes,
        )
        self._decode_output()
        self._raise_arena_error()

    def _decode_output(self) -> None:
        if self._process is None:
            raise RuntimeError("STATE-GUARD: '_process' was not initialized.")
        encoding = locale.getpreferredencoding(False)
        for channel in ("stdout", "stderr"):
            payload = getattr(self._process, channel)
            text = payload.decode(encoding, errors="replace").replace("\r\n", "\n").replace("\r", "\n")
            setattr(self._process, channel, text)

    def _raise_arena_error(self):
        """Reports arena runtime errors."""
        __tracebackhide__ = True
        if self._process is None:
            raise RuntimeError("STATE-GUARD: '_process' was not initialized.")
        if self._process.returncode != 0:
            raise RuntimeError(
                f"Arena System-Error (Exit Code {self._process.returncode}):\n"
                f"STDOUT: {self._process.stdout}\n"
                f"STDERR: {self._process.stderr}"
            )


# ========== ARENA-BUILDER =============================================================================================


class ArenaBuilder:
    """Programmatically provisions base environments and constructs PyVenv arenas via a fluent interface."""

    def __init__(self, env_path: str | os.PathLike[str] | None = None):
        self.env_path = Path(env_path) if env_path is not None else default_arena_path()
        self._packages: list[str] = []

    # ----- Services ---------------------------------------------------------------------------------------------------

    def with_packages(self, packages: list[str]) -> "ArenaBuilder":
        """Registers a list of packages to be installed in the arena."""
        __tracebackhide__ = True
        self._packages.extend(packages)
        return self

    def build(self, codec: Optional[IPCC] = None) -> PyVenv:
        """Explicitly provisions packages and codec dependencies, then returns the arena."""
        __tracebackhide__ = True
        arena = PyVenv(env_path=str(self.env_path), codec=codec)
        self._ensure_venv_exists()
        requirements: list[str] = getattr(arena.codec, "requirements", [])
        packages = list(dict.fromkeys(self._packages + requirements))
        if packages:
            self._install_packages(packages)
        return arena

    # ----- Utilities --------------------------------------------------------------------------------------------------

    def _ensure_venv_exists(self) -> None:
        """Creates a new uv virtual environment if the target path does not already exist."""
        __tracebackhide__ = True
        if self.env_path.exists():
            return
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["uv", "venv", str(self.env_path), "--python", sys.executable],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ArenaBuilder failed to create venv:\n{e.stderr.decode(errors='replace')}")

    def _install_packages(self, packages: list[str]) -> None:
        """Installs the requested packages and codec dependencies in the base."""
        __tracebackhide__ = True
        python_exe = _environment_python(self.env_path)
        if _requirements_satisfied(python_exe, packages):
            return
        try:
            subprocess.run(
                ["uv", "pip", "install", *packages, "--python", str(python_exe)], check=True, capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"ArenaBuilder failed to install packages {packages}:\n{e.stderr.decode(errors='replace')}"
            )
