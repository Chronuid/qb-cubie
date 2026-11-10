import re
import subprocess
from pathlib import Path
from typing import Union, List, Optional
from ..linter import LinterDiagnostic, _ensure_installed


class MyPy:
    """Implements the Linter protocol to execute Mypy and parse its stdout."""

    _MYPY_REGEX = re.compile(
        r"^(?P<path>.+?):"
        r"(?P<line>\d+):"
        r"(?:(?P<col>\d+):)?\s*(?P<severity>error|note|warning):"
        r"\s*(?P<msg>.*?)\s*(?:\[(?P<code>.*)])?$"
    )

    def __init__(
        self, executable: Optional[Union[str, List[str]]] = None, excludes: Optional[List[str]] = None
    ) -> None:
        self._executable = executable
        self._excludes = set(excludes) if excludes else set()

    @property
    def name(self) -> str:
        return "Mypy"

    def register_excludes(self, excludes: List[str]) -> None:
        self._excludes.update(excludes)

    def check(self, target: Union[str, Path]) -> List["LinterDiagnostic"]:
        cmd = self._build_command(target)
        process = self._execute_subprocess(cmd, target)
        self._guard_process_success(process, cmd)
        try:
            diagnostics = self._parse_stdout(process.stdout)
        except ValueError as error:
            raise self._process_error(process, cmd, "Unrecognized analysis output") from error
        if process.returncode == 1 and not any(item.severity == "error" for item in diagnostics):
            raise self._process_error(process, cmd, "Error status without recognized error diagnostics")
        return diagnostics

    def _build_command(self, target: Union[str, Path]) -> List[str]:
        exe_cmd = self._resolve_executable()
        cmd = exe_cmd + ["--show-error-codes", "--no-error-summary"]
        if self._excludes and isinstance(target, Path):
            for excl in self._excludes:
                cmd.extend(["--exclude", f"(?i){excl}"])
        return cmd

    def _parse_stdout(self, stdout: str) -> List[LinterDiagnostic]:
        diagnostics = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            match = self._MYPY_REGEX.match(line)
            if match is None:
                raise ValueError(f"Unrecognized Mypy diagnostic: {line}")
            diagnostics.append(self._diagnostic(match.groupdict()))
        return diagnostics

    def _diagnostic(self, groups: dict) -> LinterDiagnostic:
        return LinterDiagnostic(
            file_path=groups["path"], linter_name=self.name,
            rule_id=groups.get("code") or "type-error",
            line=int(groups["line"]),
            column=int(groups["col"]) if groups["col"] else 0,
            message=groups["msg"], severity=groups["severity"],
        )

    def _resolve_executable(self) -> List[str]:
        if isinstance(self._executable, list):
            return self._executable
        if isinstance(self._executable, str):
            return [self._executable]
        return _ensure_installed("mypy", "QB_CUBIE_MYPY_PATH")

    @staticmethod
    def _execute_subprocess(cmd: List[str], target: Union[str, Path]) -> subprocess.CompletedProcess:
        if isinstance(target, str):
            cmd.extend(["-c", target])
            return subprocess.run(cmd, text=True, capture_output=True)
        cmd.append(str(target))
        return subprocess.run(cmd, text=True, capture_output=True)

    @staticmethod
    def _guard_process_success(process: subprocess.CompletedProcess, cmd: List[str]) -> None:
        """Accept only successful analysis (0) or reported diagnostics (1)."""
        if process.returncode not in (0, 1):
            raise MyPy._process_error(process, cmd, "Invalid process status")

    @staticmethod
    def _process_error(process: subprocess.CompletedProcess, cmd: List[str], reason: str) -> RuntimeError:
        return RuntimeError(
            f"Linter 'Mypy' failed with exit code {process.returncode}: {reason}.\n"
            f"Command: {' '.join(cmd)}\nStdout: {process.stdout}\nStderr: {process.stderr}"
        )
