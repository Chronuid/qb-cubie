import subprocess, json
from typing import Union, Optional, List
from ..linter import LinterDiagnostic, _ensure_installed
from pathlib import Path

# ------- PYLINT -------------------------------------------------------------------------------------------------------

class Pylint:
    """
    Implements the Linter protocol to execute Pylint and parse its output.
    """
    def __init__(
            self,
            executable: Optional[Union[str, List[str]]] = None,
            excludes: Optional[List[str]] = None,
            disable: Optional[List[str]] = None
    ) -> None:
        self._executable = executable
        self._excludes = set(excludes) if excludes else set()
        self._disable = disable if disable else []

    @property
    def name(self) -> str:
        """Provides the display name of the integrated linter."""
        return "Pylint"

    def register_excludes(self, excludes: List[str]) -> None:
        """Merges new directory patterns into the internal exclusion registry."""
        self._excludes.update(excludes)

    def check(self, target: Union[str, Path]) -> List[LinterDiagnostic]:
        """Executes the analysis on the given target and returns structured diagnostics."""
        cmd = self._build_command(target)
        process = self._execute_subprocess(cmd, target)
        self._guard_process_success(process, cmd)
        return self._parse_json(process.stdout)

    def _build_command(self, target: Union[str, Path]) -> List[str]:
        """Constructs the CLI command with robust regex exclusion paths and rule disables."""
        exe_cmd = self._resolve_executable()
        cmd = exe_cmd + ["-f", "json"]
        if self._disable: cmd.append(f"--disable={','.join(self._disable)}")
        if self._excludes and isinstance(target, Path):
            patterns = [f".*{excl}.*" for excl in self._excludes]
            cmd.append(f"--ignore-paths={','.join(patterns)}")
        return cmd

    def _parse_json(self, stdout: str) -> List[LinterDiagnostic]:
        """Parses the Pylint JSON output into uniform diagnostic objects with path and scope mapping."""
        diagnostics = []
        if not stdout.strip(): return diagnostics
        for error in json.loads(stdout):
            diagnostics.append(LinterDiagnostic(
                file_path=error.get("path", "UNKNOWN"),
                linter_name=self.name,
                rule_id=error.get("message-id", "UNKNOWN"),
                line=error.get("line", 0),
                column=error.get("column", 0),
                message=error.get("message", ""),
                severity=error.get("type", "error"),
                node_name=error.get("obj", "")
            ))
        return diagnostics

    def _resolve_executable(self) -> List[str]:
        """Resolves the Pylint executable command."""
        if isinstance(self._executable, list): return self._executable
        if isinstance(self._executable, str): return [self._executable]
        return _ensure_installed("pylint", "QB_CUBIE_PYLINT_PATH")

    @staticmethod
    def _execute_subprocess(cmd: List[str], target: Union[str, Path]) -> subprocess.CompletedProcess:
        """Executes the Pylint process either against a file path or via stdin."""
        if isinstance(target, str):
            cmd.extend(["--from-stdin", "mock_module"])
            return subprocess.run(cmd, input=target, text=True, capture_output=True)
        cmd.append(str(target))
        return subprocess.run(cmd, text=True, capture_output=True)

    @staticmethod
    def _guard_process_success(process: subprocess.CompletedProcess, cmd: List[str]) -> None:
        """Guards against silent failures or hard crashes of the linter."""
        if process.returncode != 0 and not process.stdout.strip() and process.stderr.strip():
            raise RuntimeError(
                f"Linter 'Pylint' crashed or is missing.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Stderr: {process.stderr.strip()}"
            )