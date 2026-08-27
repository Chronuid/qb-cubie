import os, subprocess, sys, tempfile, shutil, uuid
from pathlib import Path
from typing import Any, Optional, Protocol
from pyvenv_codec import MSGspecCodec


# ========== PROTOCOLS & DATACLASSES ===================================================================================

class IPCCodec(Protocol):
    file_suffix: str
    requirements: list[str]
    def dump(self, obj: Any, path: str) -> None:
        """Writes the object to the specified path."""
        ...
    def load(self, path: str) -> Any:
        """Reads the object from the path."""
        ...
    def get_runner_snippet(self, in_path: str, out_path: str) -> str:
        """Generates the Python code for the arena, matching the codec."""
        ...


# ========== ARENA =====================================================================================================

class PyVenv:
    """
    Executes targets as a lightweight arena runner within ephemeral, virtual Python environments.
    """  # DISCLAIMER: Does not provide an OS-level security sandbox against potential jailbreaks.
    def __init__(
            self,
            env_path: str,
            codec: Optional[IPCCodec] = None,
            custom_id: str | None = None,
            fs: Optional[dict] = None
    ):
        self.codec = codec or MSGspecCodec()
        self.custom_id = custom_id or f"{self.__class__.__name__.lower()}"
        self.arena_id = f"cubie_arena_{custom_id}_{uuid.uuid4().hex[:8]}"
        self.env_path = Path(env_path)
        self.fs = fs or {}
        self.workspace_path: Optional[Path] = None
        self.virtual_path: Optional[Path] = None

        self._python_exe: Optional[Path] = None
        self._env_vars: Optional[dict] = None
        self._in_path: Optional[str] = None
        self._out_path: Optional[str] = None
        self._process: Optional[subprocess.CompletedProcess] = None

    # ----- Services ---------------------------------------------------------------------------------------------------

    # ↓--- Full Lifecycle ---↓

    def run(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Encapsulates the entire lifecycle of the arena for standalone invocations."""
        __tracebackhide__ = True
        self.setup()
        try: return self.execute(target, args, kwargs)
        finally: self.teardown()

    # ↓--- each phase ---↓

    def setup(self) -> None:
        """Creates an ephemeral clone of the virtual environment."""
        __tracebackhide__ = True
        if not self.env_path.exists(): raise RuntimeError(f"STATE-GUARD: Base arena not found: {self.env_path}")
        self._ensure_codec_requirements(self.env_path)
        workspace_dir = tempfile.mkdtemp(prefix=f"{self.arena_id}_")
        self.workspace_path = Path(workspace_dir)
        if self.workspace_path is None: raise RuntimeError("STATE-GUARD: 'workspace_path' could not be created.")
        self.virtual_path = self.workspace_path / ".venv"
        if self.virtual_path is None: raise RuntimeError("STATE-GUARD: 'virtual_path' is missing for hydration.")
        shutil.copytree(self.env_path, self.virtual_path, symlinks=True)
        self._hydrate()

    def execute(
            self,
            target: Any,
            args: tuple,
            kwargs: dict
    ) -> Any:
        __tracebackhide__ = True
        self._get_python_exe()
        self._prepare_env()
        return self._run_in_subprocess(target, args, kwargs)

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
        if self.workspace_path is None: raise RuntimeError("STATE-GUARD: 'workspace_path' is missing for hydration.")
        for target_rel_path, host_source_path in self.fs.items():
            source = Path(host_source_path)
            target = self.workspace_path / target_rel_path
            if not source.exists(): raise FileNotFoundError(f"Host path for fs mapping not found:  {source}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir(): shutil.copytree(source, target, symlinks=True, dirs_exist_ok=True)
            else: shutil.copy2(source, target)

    def _ensure_codec_requirements(self, base_env_path: Path) -> None:
        """Checks and injects the codec's side packages into the base arena."""
        requirements = getattr(self.codec, "requirements", [])
        if not requirements: return
        bin_dir = base_env_path / "bin" if (base_env_path / "bin").exists() else base_env_path / "Scripts"
        python_exe = bin_dir / "python"
        import subprocess
        try:
            subprocess.run(
                args= ["uv", "pip", "install", *requirements, "--python", str(python_exe)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Could not install codec requirements {requirements}: {e.stderr.decode()}")

    def _get_python_exe(self) -> None:
        __tracebackhide__ = True
        if self.virtual_path is None: raise RuntimeError("STATE-GUARD: 'virtual_path' was not initialized.")
        if (self.virtual_path / "bin").exists():  bin_dir = self.virtual_path / "bin"
        else: bin_dir = self.virtual_path / "Scripts"
        exe = bin_dir / "python"
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
        """Overrides PATH and VIRTUAL_ENV to enforce the sandbox at the OS level."""
        __tracebackhide__ = True
        if self._env_vars is None or self.virtual_path is None:
            raise RuntimeError("STATE-GUARD: '_env_vars' or 'virtual_path' was not initialized.")
        self._env_vars["VIRTUAL_ENV"] = str(self.virtual_path.absolute())
        bin_dir = self.virtual_path / "bin" if (self.virtual_path / "bin").exists() else self.virtual_path / "Scripts"
        self._env_vars["PATH"] = f"{bin_dir.absolute()}{os.pathsep}{self._env_vars.get('PATH', '')}"

    # ↓--- _run_in_subprocess() ---↓

    def _setup_ipc_files(self) -> None:
        """Creates temporary files for data exchange and releases their file descriptors."""
        __tracebackhide__ = True
        if self.workspace_path is None: raise RuntimeError("STATE-GUARD: 'workspace_path' was not initialized.")
        self._in_path = str(self.workspace_path / f"ipc_in{self.codec.file_suffix}")
        self._out_path = str(self.workspace_path / f"ipc_out{self.codec.file_suffix}")

    def _serialize_inputs(self, target: Any, args: tuple, kwargs: dict) -> None:
        """Serializes the target and its parameters into the input file."""
        __tracebackhide__ = True
        if self._in_path is None: raise RuntimeError("STATE-GUARD: '_in_path' was not initialized.")
        self.codec.dump((target, args, kwargs), self._in_path)

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
        self._process = subprocess.run(
            cmd_args,
            env=self._env_vars,
            cwd=self.workspace_path,
            capture_output=True,
            text=True
        )
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