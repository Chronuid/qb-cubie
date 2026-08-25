import os, pickle, subprocess, sys, tempfile, textwrap, shutil
from pathlib import Path
from typing import Any, Optional


# ========== ARENA =====================================================================================================

class PyVenv:
    """
    Führt Targets als leichtgewichtiger Arena-Runner in flüchtigen, virtuellen Python-Umgebungen aus.
    """
    # DISCLAIMER: Bietet als funktionaler MVP keine OS-Level Security-Sandbox gegen mutwillige Jailbreaks.
    def __init__(self, env_path: str):
        self._env_path = Path(env_path)
        self._original_path: Optional[Path] = None
        self._python_exe: Optional[Path] = None
        self._env_vars: Optional[dict] = None
        self._in_path: Optional[str] = None
        self._out_path: Optional[str] = None
        self._process: Optional[subprocess.CompletedProcess] = None


    # ----- Services ---------------------------------------------------------------------------------------------------

    # ↓--- Full Lifecycle ---↓

    def run(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Kapselt den gesamten Lebenszyklus der Arena für eigenständige Aufrufe."""
        __tracebackhide__ = True
        self.setup()
        try: return self.execute(target, args, kwargs)
        finally: self.teardown()


    # ↓--- each phase ---↓

    def setup(self) -> None:
        """Erstellt einen flüchtigen Klon der virtuellen Umgebung."""
        __tracebackhide__ = True
        if not self._env_path.exists():
            raise RuntimeError(f"STATE-GUARD: Basis-Arena nicht gefunden: {self._env_path}")
        self._original_path = self._env_path
        if self._original_path is None:
            raise RuntimeError("STATE-GUARD: Backup des Original-Pfads ist fehlgeschlagen.")
        clone_dir = tempfile.mkdtemp(prefix="cubie_arena_")
        self._env_path = Path(clone_dir)
        shutil.rmtree(self._env_path)
        shutil.copytree(self._original_path, self._env_path, symlinks=True)

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
        """Zerstört den flüchtigen Klon restlos und stellt den Ursprungszustand her."""
        __tracebackhide__ = True
        if self._original_path is None:
            raise RuntimeError("STATE-GUARD: Teardown aufgerufen, aber '_original_path' fehlt.")
        if self._env_path.exists(): shutil.rmtree(self._env_path)
        self._env_path = self._original_path
        self._original_path = None

    # ----- Pipes ------------------------------------------------------------------------------------------------------

    def _get_python_exe(self) -> None:
        __tracebackhide__ = True
        if (self._env_path / "bin").exists():
            bin_dir=self._env_path / "bin"
        else: bin_dir=self._env_path / "Scripts"
        exe = bin_dir / "python"
        if not exe.exists():
            raise RuntimeError(f"Arena Python fehlt: {exe}")
        self._python_exe = exe

    def _prepare_env(self) -> None:
        """Simuliert 'source activate' für den Subprozess und reicht den Projekt-Code durch."""
        __tracebackhide__ = True
        self._env_vars = os.environ.copy()
        self._inject_project_code()
        self._activate_arena_env()

    def _run_in_subprocess(self, target: Any, args: tuple, kwargs: dict) -> Any:
        """Verpackt das Callable, führt es in der Arena aus und entpackt das Ergebnis."""
        __tracebackhide__ = True
        if self._python_exe is None or self._env_vars is None:
            raise RuntimeError("STATE-GUARD: Python-Executable oder Environment fehlen.")
        self._setup_ipc_files()
        try:
            self._serialize_inputs(target, args, kwargs)
            self._invoke_script()
            return self._deserialize_outputs()
        finally: self._teardown_ipc_files()

    def _invoke_script(self) -> None:
        """Generiert das Runner-Skript und feuert den Subprozess in der Arena ab."""
        __tracebackhide__ = True
        script = self._generate_runner_script()
        self._execute_runner_script(script)


    # ----- Utilities --------------------------------------------------------------------------------------------------

    # ↓--- _prepare_env() ---↓

    def _inject_project_code(self) -> None:
        """Isoliert den PYTHONPATH von Host-Paketen und blockiert PYTHONHOME."""
        __tracebackhide__ = True
        if self._env_vars is None:
            raise RuntimeError("STATE-GUARD: '_env_vars' wurde nicht initialisiert.")
        safe_paths = [p for p in sys.path if "site-packages" not in p and "dist-packages" not in p]
        self._env_vars["PYTHONPATH"] = os.pathsep.join(safe_paths)
        self._env_vars.pop("PYTHONHOME", None)

    def _activate_arena_env(self) -> None:
        """Überschreibt PATH und VIRTUAL_ENV, um die Sandbox auf OS-Ebene zu erzwingen."""
        __tracebackhide__ = True
        if self._env_vars is None:
            raise RuntimeError("STATE-GUARD: '_env_vars' wurde nicht initialisiert.")
        self._env_vars["VIRTUAL_ENV"] = str(self._env_path.absolute())
        bin_dir = self._env_path / "bin" if (self._env_path / "bin").exists() else self._env_path / "Scripts"
        self._env_vars["PATH"] = f"{bin_dir.absolute()}{os.pathsep}{self._env_vars.get('PATH', '')}"

    # ↓--- _run_in_subprocess() ---↓

    def _setup_ipc_files(self) -> None:
        """Erstellt temporäre Dateien für den Datenaustausch und gibt deren File-Deskriptoren frei."""
        __tracebackhide__ = True
        fd_in, self._in_path = tempfile.mkstemp(suffix=".pkl")
        fd_out, self._out_path = tempfile.mkstemp(suffix=".pkl")
        os.close(fd_in)
        os.close(fd_out)

    def _serialize_inputs(self, target: Any, args: tuple, kwargs: dict) -> None:
        """Serialisiert das Target und dessen Parameter in die Eingabedatei."""
        __tracebackhide__ = True
        if self._in_path is None:
            raise RuntimeError("STATE-GUARD: '_in_path' wurde nicht initialisiert.")
        with open(self._in_path, "wb") as f: pickle.dump((target, args, kwargs), f)

    def _deserialize_outputs(self) -> Any:
        """Liest das Ergebnis des Subprozesses aus und wirft bei Fehlern die entsprechende Exception."""
        __tracebackhide__ = True
        if self._out_path is None:
            raise RuntimeError("STATE-GUARD: '_out_path' wurde nicht initialisiert.")
        with open(self._out_path, "rb") as f: status, result = pickle.load(f)
        if status == "ERROR": raise result
        return result

    def _teardown_ipc_files(self) -> None:
        """Bereinigt die temporären Dateien nach Abschluss der Ausführung und setzt den Zustand zurück."""
        __tracebackhide__ = True
        if self._in_path and os.path.exists(self._in_path):
            os.remove(self._in_path)
        if self._out_path and os.path.exists(self._out_path):
            os.remove(self._out_path)
        self._in_path = None
        self._out_path = None

    # ↓--- _invoke_script() ---↓

    def _generate_runner_script(self) -> str:
        """Generiert den Python-Quellcode für den isolierten Ausführungs-Wrapper."""
        __tracebackhide__ = True
        if self._in_path is None or self._out_path is None:
            raise RuntimeError("STATE-GUARD: In/Out Pfade für die Skript-Generierung fehlen.")
        wrapped_text = textwrap.dedent(
            f"""
            import pickle
            try:
                with open({repr(self._in_path)}, 'rb') as f: t, a, k = pickle.load(f)
                res = t(*a, **k)
                with open({repr(self._out_path)}, 'wb') as f: pickle.dump(("SUCCESS", res), f)
            except Exception as e:
                with open({repr(self._out_path)}, 'wb') as f: pickle.dump(("ERROR", e), f)
            """
        )
        return wrapped_text

    def _execute_runner_script(self, script: str) -> None:
        """Startet den Subprozess mit dem generierten Skript und fängt Systemfehler ab."""
        __tracebackhide__ = True
        if self._python_exe is None or self._env_vars is None:
            raise RuntimeError("STATE-GUARD: Python-Executable oder Environment fehlen.")
        cmd_args = [str(self._python_exe), "-c", script]
        self._process = subprocess.run(
            cmd_args,
            env=self._env_vars,
            capture_output=True,
            text=True
        )
        self._raise_arena_error()

    def _raise_arena_error(self):
        """Gibt Laufzeit-Fehler der Arena bekannt."""
        __tracebackhide__ = True
        if self._process is None:
            raise RuntimeError("STATE-GUARD: '_process' wurde nicht initialisiert.")
        if self._process.returncode != 0:
            raise RuntimeError(
                f"Arena System-Fehler (Exit Code {self._process.returncode}):\n"
                f"STDOUT: {self._process.stdout}\n"
                f"STDERR: {self._process.stderr}"
            )