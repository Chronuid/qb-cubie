from __future__ import annotations
import os, shutil, sys, importlib.util
from pathlib import Path
try:
    import libcst as cst
    from libcst.metadata import PositionProvider
    _CstVisitorBase = cst.CSTVisitor
except ImportError:
    cst = None
    PositionProvider = None
    _CstVisitorBase = object
from typing import Union, List, Optional, Protocol, Final, Any
import dataclasses

def _ensure_installed(tool_name: str, env_var: str) -> list[str]:
    """
    State-Guard: Checks whether the tool exists. - Throws a user-friendly error message otherwise.
    """
    env_path = os.getenv(env_var)
    if env_path:  return [env_path]
    tool_path = shutil.which(tool_name)
    if tool_path: return [tool_path]
    if importlib.util.find_spec(tool_name): return [sys.executable, "-m", tool_name]
    raise RuntimeError(
        f"Linter check failed: '{tool_name}' was not found in the environment.\n"
        f"-> Please ensure that the package is installed.\n"
        f"-> Tip: Run 'uv add {tool_name}' (for the project) or 'uv pip install {tool_name}' (temporarily).\n"
        f"-> Alternatively, you can set the path via the environment variable {env_var}."
    )

# ========== LINTER ====================================================================================================

@dataclasses.dataclass
class LinterDiagnostic:
    file_path: str
    linter_name: str
    rule_id: str
    line: int
    column: int
    message: str
    severity: str
    node_type: str = ""
    node_name: str = ""
    suggestions: List[str] | str | None = None


class Linter(Protocol):
    """
    Defines the uniform execution contract for static code analysis tools.
    """
    @property
    def name(self) -> str:
        """Provides the display name of the integrated linter."""
        ...

    def register_excludes(self, excludes: list[str]) -> None:
        """Merges new directory patterns into the internal exclusion registry."""
        ...

    def check(self, target: Union[str, Path]) -> list[LinterDiagnostic]:
        """Executes the analysis on the given target and returns structured diagnostics."""
        ...


DEFAULT_EXCLUDES: Final = [".venv", "__pycache__", ".git"]


# ========== ABSTRACT-SYNTAX-TREE ======================================================================================

class AstLinter:
    """
    Orchestrates multiple linter backends and aggregates their diagnostic results.
    """
    def __init__(self, *linters: Union[Linter, List[Linter], type]):
        self.linters: List[Linter] = []
        for item in linters:
            if isinstance(item, type): self.linters.append(item())
            elif isinstance(item, list): self.linters.extend(item)
            else: self.linters.append(item)

    def check(self, target: Optional[Union[str, Path]] = None) -> List[LinterDiagnostic]:
        """Runs all registered linters against the resolved target and merges diagnostics."""
        resolved_target = self._resolve_target(target)
        self._propagate_excludes(resolved_target)
        all_diagnostics = []
        for linter in self.linters: all_diagnostics.extend(linter.check(resolved_target))
        return all_diagnostics

    def _propagate_excludes(self, target: Union[str, Path]) -> None:
        """Injects default exclusions into all linters if no native configuration exists."""
        if not self._has_native_config(target):
            for linter in self.linters: linter.register_excludes(DEFAULT_EXCLUDES)

    @staticmethod
    def _resolve_target(target: Optional[Union[str, Path]]) -> Union[str, Path]:
        """Resolves the given target or falls back to the current working directory."""
        if target is not None: return target
        return Path.cwd()

    @staticmethod
    def _has_native_config(target: Union[str, Path]) -> bool:
        """Checks if a pyproject.toml exists in the target context."""
        if isinstance(target, str): return Path("pyproject.toml").exists()
        if target.is_dir(): return (target / "pyproject.toml").exists()
        return (target.parent / "pyproject.toml").exists()


# ========== CONCRETE-SYNTAX-TREE ======================================================================================

# ---------- CST-RULE --------------------------------------------------------------------------------------------------

class CstRule(_CstVisitorBase):
    METADATA_DEPENDENCIES = (PositionProvider,) if PositionProvider else ()
    def __init__(self):
        if cst is None:
            raise RuntimeError("libcst is required to use CstRule. Please ensure libcst is installed.")
        super().__init__()
        self.diagnostics: List['LinterDiagnostic'] = []
        self._module: Optional[Any] = None
        self._current_file_path: str = "IN_MEMORY"

    def reset(self, file_path: str, module: cst.Module) -> None:
        """Resets the diagnostic state and sets the context for a new file visit."""
        self.diagnostics = []
        self._current_file_path = file_path
        self._module = module

    def add_diagnostic(
            self,
            node: cst.CSTNode,
            rule_id: str,
            message: str,
            severity: str = "error",
            node_name: str = "",
            replacement_node: Union[cst.CSTNode, List[cst.CSTNode], None] = None
    ) -> None:
        """Extracts node coordinates and metadata to generate a rich diagnostic."""
        pos = self.get_metadata(PositionProvider, node).start
        suggestions = self.route_suggestions(self._module, replacement_node)
        self.diagnostics.append(LinterDiagnostic(
            file_path=self._current_file_path,
            linter_name=self.__class__.__name__,
            rule_id=rule_id,
            line=pos.line,
            column=pos.column,
            message=message,
            severity=severity,
            node_type=type(node).__name__,
            node_name=node_name,
            suggestions=suggestions
        ))

    @staticmethod
    def route_suggestions(
            module: cst.Module | None,
            replacement: cst.CSTNode | list[cst.CSTNode] | None
    ) -> None | list[str] | str:
        suggest = None
        if replacement is not None and module is not None:
            if isinstance(replacement, list): suggest = [module.code_for_node(n) for n in replacement]
            else: suggest = module.code_for_node(replacement)
        return suggest


# ---------- CST-LINTER ------------------------------------------------------------------------------------------------

class CstLinter:
    """
    Implements the Linter protocol to execute CST-based Python validation.
    """
    def __init__(
            self,
            rules: List[CstRule],
            excludes: Optional[List[str]] = None
    ) -> None:
        if cst is None:
            raise RuntimeError("libcst is required to use CstLinter. Please ensure libcst is installed.")
        self.rules = rules
        self._excludes = set(excludes) if excludes else set()

    @property
    def name(self) -> str:
        """Provides the display name of the integrated linter."""
        return "CST-Linter"

    def register_excludes(self, excludes: List[str]) -> None:
        """Merges new directory patterns into the internal exclusion registry."""
        self._excludes.update(excludes)

    def check(self, target: Union[str, Path]) -> List[LinterDiagnostic]:
        """Executes CST rules on a file, in-memory string, or recursively on a directory."""
        all_diagnostics = []
        if isinstance(target, str):
            all_diagnostics.extend(self._analyze_source(target, "IN_MEMORY"))
        elif target.is_file():
            all_diagnostics.extend(self._analyze_source(target.read_text(encoding="utf-8"), str(target)))
        elif target.is_dir():
            for file_path in self._crawl_directory(target):
                source = file_path.read_text(encoding="utf-8")
                all_diagnostics.extend(self._analyze_source(source, str(file_path)))
        return all_diagnostics

    def _crawl_directory(self, root: Path) -> List[Path]:
        """Recursively yields Python files while respecting the exclusion registry."""
        py_files = []
        for path in root.rglob("*.py"):
            if not any(excluded in path.parts for excluded in self._excludes): py_files.append(path)
        return py_files

    def _analyze_source(self, source_code: str, file_path: str) -> List['LinterDiagnostic']:
        """Parses the source and runs all registered rules against the syntax tree."""
        try:
            tree = cst.parse_module(source_code)
            wrapper = cst.metadata.MetadataWrapper(tree)
        except cst.ParserSyntaxError as error: return [self._create_syntax_error(file_path, error)]
        diagnostics = []
        for rule in self.rules:
            rule.reset(file_path, tree)
            wrapper.visit(rule)
            diagnostics.extend(rule.diagnostics)
        return diagnostics

    def _create_syntax_error(self, file_path: str, error: cst.ParserSyntaxError) -> LinterDiagnostic:
        """Generates a fallback diagnostic if the CST parser crashes on invalid syntax."""
        return LinterDiagnostic(
            file_path=file_path,
            linter_name=self.name,
            rule_id="E999",
            line=error.raw_line,
            column=error.raw_column,
            message=error.message,
            severity="fatal"
        )