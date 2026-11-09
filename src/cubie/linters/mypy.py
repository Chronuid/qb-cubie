import re, subprocess
from pathlib import Path
from typing import Union, List, Optional
from ..linter import LinterDiagnostic, _ensure_installed


class MyPy:
    """
    Implements the Linter protocol to execute Mypy and parse its stdout.
    """
    _MYPY_REGEX = re.compile(
        r"^(?P<path>[^:]+):"
        r"(?P<line>\d+):"
        r"(?:(?P<col>\d+):)?\s*(?P<severity>error|note|warning):"
        r"\s*(?P<msg>.*?)\s*(?:\[(?P<code>.*)])?$"
    )

    def __init__(
            self,
            executable: Optional[Union[str, List[str]]] = None,
            excludes: Optional[List[str]] = None
    ) -> None:
        self._executable = executable
        self._excludes = set(excludes) if excludes else set()

    @property
    def name(self) -> str: return "Mypy"

    def register_excludes(self, excludes: List[str]) -> None:
        self._excludes.update(excludes)

    def check(self, target: Union[str, Path]) -> List['LinterDiagnostic']:
        cmd = self._build_command(target)
        process = self._execute_subprocess(cmd, target)
        self._guard_process_success(process, cmd)
        return self._parse_stdout(process.stdout)

    def _build_command(self, target: Union[str, Path]) -> List[str]:
        exe_cmd = self._resolve_executable()
        cmd = exe_cmd + ["--show-error-codes", "--no-error-summary"]
        if self._excludes and isinstance(target, Path):
            for excl in self._excludes: cmd.extend(["--exclude", f"(?i){excl}"])
        return cmd

    def _parse_stdout(self, stdout: str) -> List['LinterDiagnostic']:
        diagnostics = []
        for line in stdout.splitlines():
            match = self._MYPY_REGEX.match(line)
            if not match: continue
            groups = match.groupdict()
            diagnostics.append(LinterDiagnostic(
                file_path=groups["path"],
                linter_name=self.name,
                rule_id=groups.get("code") or "type-error",
                line=int(groups["line"]),
                column=int(groups["col"]) if groups["col"] else 0,
                message=groups["msg"],
                severity=groups["severity"]
            ))
        return diagnostics

    def _resolve_executable(self) -> List[str]:
        if isinstance(self._executable, list): return self._executable
        if isinstance(self._executable, str): return [self._executable]
        return _ensure_installed("mypy", "CUBIE_MYPY_PATH")

    @staticmethod
    def _execute_subprocess(cmd: List[str], target: Union[str, Path]) -> subprocess.CompletedProcess:
        if isinstance(target, str):
            cmd.extend(["-c", target])
            return subprocess.run(cmd, text=True, capture_output=True)
        cmd.append(str(target))
        return subprocess.run(cmd, text=True, capture_output=True)

    @staticmethod
    def _guard_process_success(process: subprocess.CompletedProcess, cmd: List[str]) -> None:
        if process.returncode == 2 and process.stderr.strip():
            raise RuntimeError(
                f"Linter 'Mypy' crashed or is missing.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Stderr: {process.stderr.strip()}"
            )