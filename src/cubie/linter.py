import subprocess, json, os, shutil, sys, importlib.util
from pathlib import Path
_SMUGGLED_LIBCST = Path(__file__).parent / "linters" / "libcst_tool"
if importlib.util.find_spec("libcst") is None:
    if _SMUGGLED_LIBCST.exists(): sys.path.insert(0, str(_SMUGGLED_LIBCST.resolve()))
    else: raise RuntimeError(
            "CST-Linter fehlgeschlagen: 'libcst' wurde nicht gefunden.\n"
            "-> Tipp: Führe 'uv add libcst' oder 'uv pip install libcst' aus."
        )
from .protocols import LinterDiagnostic, LinterProfile
import libcst as cst
from libcst.metadata import PositionProvider
from typing import Union

def _parse_ruff(stdout: str, linter_name: str) -> list[LinterDiagnostic]:
    diagnostics = []
    if not stdout.strip(): return diagnostics
    for error in json.loads(stdout):
        diagnostics.append(LinterDiagnostic(
            linter_name=linter_name,
            rule_id=error.get("code", "UNKNOWN"),
            line=error["location"]["row"],
            column=error["location"]["column"],
            message=error.get("message", ""),
            severity="error"
        ))
    return diagnostics


def _parse_pylint(stdout: str, linter_name: str) -> list[LinterDiagnostic]:
    diagnostics = []
    if not stdout.strip(): return diagnostics
    for error in json.loads(stdout):
        diagnostics.append(LinterDiagnostic(
            linter_name=linter_name,
            rule_id=error.get("message-id", "UNKNOWN"),
            line=error.get("line", 0),
            column=error.get("column", 0),
            message=error.get("message", ""),
            severity=error.get("type", "error")
        ))
    return diagnostics


# --- Linter-Factories (Die Registrierungen) ---

def _ensure_installed(tool_name: str, env_var: str) -> list[str]:
    """
    State-Guard: Prüft, ob das Tool existiert.
    Wirft andernfalls eine nutzerfreundliche Fehlermeldung.
    """
    env_path = os.getenv(env_var)
    if env_path:  return [env_path]
    tool_path = shutil.which(tool_name)
    if tool_path: return [tool_path]
    if importlib.util.find_spec(tool_name): return [sys.executable, "-m", tool_name]
    raise RuntimeError(
        f"Linter-Check fehlgeschlagen: '{tool_name}' wurde in der Umgebung nicht gefunden.\n"
        f"-> Bitte stelle sicher, dass das Paket installiert ist.\n"
        f"-> Tipp: Führe 'uv add {tool_name}' (fürs Projekt) oder 'uv pip install {tool_name}' (temporär) aus.\n"
        f"-> Alternativ kannst du den Pfad über die Umgebungsvariable {env_var} setzen."
    )


def ruff(executable: Union[str, list[str], None] = None) -> LinterProfile:
    if executable: exe_cmd = [executable] if isinstance(executable, str) else executable
    else: exe_cmd = _ensure_installed("ruff", "CUBIE_RUFF_PATH")

    return LinterProfile(
        name="Ruff",
        base_cmd=exe_cmd + ["check", "--output-format=json"],
        stdin_args=["-"],
        json_parser=_parse_ruff
    )


def pylint(executable: Union[str, list[str], None] = None) -> LinterProfile:
    if executable: exe_cmd = [executable] if isinstance(executable, str) else executable
    else: exe_cmd = _ensure_installed("pylint", "CUBIE_PYLINT_PATH")
    return LinterProfile(
        name="Pylint",
        base_cmd=exe_cmd + ["-f", "json"],
        stdin_args=["--from-stdin", "mock_module"],
        json_parser=_parse_pylint
    )


class AstLinter:
    def __init__(self, linter: list[LinterProfile]):
        self.linters = linter

    def check(self, target: Union[str, Path]) -> list['LinterDiagnostic']:
        all_diagnostics = []
        for profile in self.linters:
            cmd = list(profile.base_cmd)
            if isinstance(target, str):
                cmd.extend(profile.stdin_args)  # .extend statt .append
                process = subprocess.run(cmd, input=target, text=True, capture_output=True)
            else:
                cmd.append(str(target))
                process = subprocess.run(cmd, text=True, capture_output=True)
            if process.returncode != 0 and not process.stdout.strip(): raise RuntimeError(
                    f"Linter '{profile.name}' ist abgestürzt oder nicht installiert.\n"
                    f"Befehl: {' '.join(cmd)}\n"
                    f"Stderr: {process.stderr.strip()}"
                )
            diagnostics = profile.json_parser(process.stdout, profile.name)
            all_diagnostics.extend(diagnostics)
        return all_diagnostics

# ----------------------------------------------------------------------------------------------------------------------

class CstRule(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)
    def __init__(self):
        super().__init__()
        self.diagnostics: list[LinterDiagnostic] = []

    def add_diagnostic(
            self,
            node: cst.CSTNode,
            rule_id: str,
            message: str,
            severity: str = "error"
    ):
        """
        Die Convenience-Methode für die Child-Klassen.
        Nimmt den fehlerhaften Knoten entgegen und extrahiert selbstständig die Koordinaten.
        """
        pos = self.get_metadata(PositionProvider, node).start
        self.diagnostics.append(LinterDiagnostic(
            linter_name=self.__class__.__name__,
            rule_id=rule_id,
            line=pos.line,
            column=pos.column,
            message=message,
            severity=severity
        ))


class CstLinter:
    def __init__(self, rules: list[CstRule]):
        self.rules = rules

    def check(self, target: Union[str, Path]) -> list[LinterDiagnostic]:
        if isinstance(target, Path): source_code = target.read_text(encoding="utf-8")
        else: source_code = target
        tree = cst.parse_module(source_code)
        wrapper = cst.metadata.MetadataWrapper(tree)
        all_diagnostics = []
        for rule in self.rules:
            wrapper.visit(rule)
            all_diagnostics.extend(rule.diagnostics)
        return all_diagnostics

# --- Nutzung in EBT ---
# linter = CstLinter(rules=[ForbidEvalRule(), ReturnTypeRule()])
# result = linter.check("eval('1+1')")