"""Meta-Gate 1: Enforce canonical 'qb_cubie' imports without 'src.' prefix."""

from pathlib import Path

import libcst as cst
import pytest

from qb_cubie import EBT, CstLinter, CstRule, LinterDiagnostic, WorldState

RULE_ID = "META-CANONICAL-IMPORT"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCAN_EXCLUDES = [".arenas", ".venv", "__pycache__", ".git", ".pytest_cache"]


def _is_non_canonical_module(module_path: str) -> bool:
    """Return True if the module path references the non-canonical 'src' namespace."""
    return (
        module_path == "src"
        or module_path == "src.qb_cubie"
        or module_path.startswith("src.qb_cubie.")
    )


class CanonicalImportRule(CstRule):
    """Detect imports targeting 'src' or 'src.qb_cubie' instead of canonical 'qb_cubie'."""

    def _report_if_non_canonical(self, node: cst.CSTNode, module_path: str) -> None:
        """Record a diagnostic when an import targets the split 'src' namespace."""
        if _is_non_canonical_module(module_path):
            self.add_diagnostic(
                node=node,
                rule_id=RULE_ID,
                message=f"Verwende 'qb_cubie' statt '{module_path}'.",
                node_name=module_path,
            )

    def visit_Import(self, node: cst.Import) -> None:
        """Inspect direct 'import ...' statements for non-canonical 'src' paths."""
        if not self._module:
            return
        for alias in node.names:
            module_path = self._module.code_for_node(alias.name)
            self._report_if_non_canonical(alias, module_path)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Inspect absolute 'from ... import ...' statements for non-canonical 'src' paths."""
        if not self._module or node.relative or node.module is None:
            return
        module_path = self._module.code_for_node(node.module)
        self._report_if_non_canonical(node, module_path)


def build_canonical_import_linter() -> CstLinter:
    """Create the configured CstLinter instance for Meta-Gate 1."""
    return CstLinter(rules=[CanonicalImportRule()], excludes=SCAN_EXCLUDES)


def _format_diagnostics(diagnostics: list[LinterDiagnostic]) -> str:
    """Format linter diagnostics with file, line, rule ID, and message."""
    return "\n".join(
        f"{d.file_path}:{d.line}:{d.column} [{d.rule_id}] {d.message}"
        for d in diagnostics
    )


@pytest.mark.parametrize(
    "clean_source",
    [
        "import qb_cubie\n",
        "from qb_cubie import EBT, WorldState\n",
        "from qb_cubie.core.rbt import RBT\n",
        "import src_helper\n",
        "from .src import helper\n",
        "from .src.qb_cubie import helper\n",
        'example = "from src.qb_cubie.core.rbt import RBT"\n',
    ],
    ids=[
        "import-qb_cubie",
        "from-qb_cubie",
        "from-qb_cubie-submodule",
        "unrelated-src-prefix",
        "relative-src",
        "relative-src-submodule",
        "string-literal",
    ],
)
def test_canonical_import_rule_accepts_clean_probes(clean_source: str) -> None:
    """Clean probe: canonical, relative, and string-only sources yield zero diagnostics."""
    linter = build_canonical_import_linter()
    EBT(
        target=linter.check,
        pre=WorldState(args=(clean_source,)),
        post=WorldState(returns=[]),
        reporter=None,
    ).run()


@pytest.mark.parametrize(
    "bad_source, expected_line, expected_module",
    [
        ("from src.qb_cubie.core.rbt import RBT\n", 1, "src.qb_cubie.core.rbt"),
        ("from src.qb_cubie import EBT\n", 1, "src.qb_cubie"),
        ("from src import qb_cubie\n", 1, "src"),
        ("import src.qb_cubie\n", 1, "src.qb_cubie"),
        ("import src\n", 1, "src"),
        ("import os, src.qb_cubie.core.ebt as ebt\n", 1, "src.qb_cubie.core.ebt"),
        ("# Kommentar\nfrom src.qb_cubie.core.linter import CstLinter\n", 2, "src.qb_cubie.core.linter"),
    ],
    ids=[
        "from-src-submodule",
        "from-src-qb_cubie",
        "from-src-import-qb_cubie",
        "import-src-qb_cubie",
        "import-src",
        "multi-import-alias",
        "line-number-offset",
    ],
)
def test_canonical_import_rule_detects_fault_probes(
    bad_source: str,
    expected_line: int,
    expected_module: str,
) -> None:
    """Fault probe: non-canonical 'src' imports trigger META-CANONICAL-IMPORT with exact line."""
    linter = build_canonical_import_linter()

    def has_expected_diagnostic(diagnostics: list[LinterDiagnostic]) -> bool:
        if len(diagnostics) != 1:
            return False
        diag = diagnostics[0]
        return (
            diag.rule_id == RULE_ID
            and diag.line == expected_line
            and diag.node_name == expected_module
            and "qb_cubie" in diag.message
        )

    EBT(
        target=linter.check,
        pre=WorldState(args=(bad_source,)),
        post=WorldState(returns=has_expected_diagnostic),
        reporter=None,
    ).run()


def test_canonical_import_rule_reports_file_path_on_disk(tmp_path: Path) -> None:
    """File probe: diagnostics report the concrete file path and line on disk."""
    bad_file = tmp_path / "broken_import_sample.py"
    bad_file.write_text("import os\nfrom src.qb_cubie import EBT\n", encoding="utf-8")
    diagnostics = build_canonical_import_linter().check(bad_file)
    assert len(diagnostics) == 1, _format_diagnostics(diagnostics)
    assert diagnostics[0].file_path == str(bad_file)
    assert diagnostics[0].rule_id == RULE_ID
    assert diagnostics[0].line == 2


@pytest.mark.parametrize("directory", ["tests", "src"])
def test_repository_uses_canonical_qb_cubie_imports(directory: str) -> None:
    """Repository gate: no Python file under tests/ or src/ imports via 'src'."""
    target_dir = PROJECT_ROOT / directory
    diagnostics = build_canonical_import_linter().check(target_dir)
    assert diagnostics == [], (
        f"Non-canonical imports found in: {directory}/ :\n"
        f"{_format_diagnostics(diagnostics)}"
    )
