"""Meta-Gate 4: Enforce service architecture, strict isolation, and core-promotion contracts."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import Final

import libcst as cst
import pytest

from qb_cubie import EBT, CstLinter, CstRule, LinterDiagnostic, WorldState

ISOLATION_RULE_ID: Final[str] = "META-SERVICE-ISOLATION"
PURE_IO_RULE_ID: Final[str] = "META-SERVICE-PURE-DOMAIN-IO"
DOMAIN_COUPLING_RULE_ID: Final[str] = "META-SERVICE-DOMAIN-COUPLING"
SERVICE_MODULE_LINE_LIMIT: Final[int] = 500
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
SERVICES_ROOT: Final[Path] = PROJECT_ROOT / "src" / "qb_cubie" / "core" / "services"

pytestmark = [pytest.mark.meta, pytest.mark.services]
SCAN_EXCLUDES: Final[list[str]] = [".arenas", ".venv", "__pycache__", ".git", ".pytest_cache"]
SERVICE_PREFIXES: Final[tuple[str, ...]] = ("qb_cubie.core.services", "qb_cubie.services")
PURE_DOMAIN_FILENAMES: Final[frozenset[str]] = frozenset({"models.py", "protocols.py", "engine.py", "rules.py"})
FORBIDDEN_IO_CALLS: Final[frozenset[str]] = frozenset({"open", "print"})
FORBIDDEN_IO_ATTR_CALLS: Final[frozenset[str]] = frozenset(
    {"open", "read_text", "write_text", "read_bytes", "write_bytes"}
)
FORBIDDEN_DOC_FRAME_SYMBOLS: Final[frozenset[str]] = frozenset(
    {"DocFrame", "FramePattern", "DocumentCatalog", "render_zone"}
)


def _discover_service_packages() -> list[str]:
    """Return sorted names of all concrete service packages under src/qb_cubie/core/services/."""
    return sorted(
        entry.name
        for entry in SERVICES_ROOT.iterdir()
        if entry.is_dir() and not entry.name.startswith("_") and (entry / "__init__.py").is_file()
    )


def _format_diagnostics(diagnostics: list[LinterDiagnostic]) -> str:
    """Format linter diagnostics with file, line, rule ID, and message."""
    return "\n".join(
        f"{d.file_path}:{d.line}:{d.column} [{d.rule_id}] {d.message}"
        for d in diagnostics
    )


def _service_depth_from_file(file_path: str, service_name: str, default_level: int = 2) -> int:
    """Compute the relative-import dot count that reaches qb_cubie.core.services from file_path."""
    if not file_path or file_path in {"<string>", "IN_MEMORY"}:
        return default_level
    try:
        rel = Path(file_path).resolve().relative_to((SERVICES_ROOT / service_name).resolve())
    except ValueError:
        return default_level
    return len(rel.parts) + 1


def _extract_sibling_from_absolute(module_path: str, service_name: str) -> str | None:
    """Return the imported sibling service name if module_path targets another service."""
    for prefix in SERVICE_PREFIXES:
        if module_path == prefix:
            return None
        if module_path.startswith(f"{prefix}."):
            remainder = module_path[len(prefix) + 1 :]
            target_service = remainder.split(".", 1)[0]
            if target_service and target_service != service_name:
                return target_service
    return None


def _imported_names(node: cst.ImportFrom) -> list[str]:
    """Return the top-level symbol names imported by a 'from ... import ...' node."""
    if isinstance(node.names, cst.ImportStar):
        return ["*"]
    return [alias.name.value for alias in node.names if isinstance(alias.name, cst.Name)]


class ServiceIsolationImportRule(CstRule):
    """Detect any cross-service import from a sibling package under qb_cubie.core.services."""

    def __init__(self, service_name: str, *, default_services_level: int = 2) -> None:
        super().__init__()
        self.service_name = service_name
        self.default_services_level = default_services_level

    def _report_cross_import(self, node: cst.CSTNode, target: str) -> None:
        """Record a META-SERVICE-ISOLATION diagnostic for a forbidden sibling import."""
        self.add_diagnostic(
            node=node,
            rule_id=ISOLATION_RULE_ID,
            message=(
                f"Service '{self.service_name}' darf keinen Geschwister-Service '{target}' "
                "importieren (DEV-GUIDE_Services.md: Null Querkopplung)."
            ),
            node_name=target,
        )

    def visit_Import(self, node: cst.Import) -> None:
        """Inspect direct 'import ...' statements for sibling service references."""
        if not self._module:
            return
        for alias in node.names:
            module_path = self._module.code_for_node(alias.name)
            sibling = _extract_sibling_from_absolute(module_path, self.service_name)
            if sibling is not None:
                self._report_cross_import(alias, module_path)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Inspect absolute and relative 'from ... import ...' statements for sibling imports."""
        if not self._module:
            return
        module_path = self._module.code_for_node(node.module) if node.module is not None else ""
        if node.relative:
            self._check_relative_import(node, len(node.relative), module_path)
        else:
            self._check_absolute_from_import(node, module_path)

    def _check_relative_import(self, node: cst.ImportFrom, level: int, module_path: str) -> None:
        """Flag relative imports that step up to services/ and enter a sibling service."""
        services_level = _service_depth_from_file(
            self._current_file_path, self.service_name, self.default_services_level
        )
        if level != services_level:
            return
        if module_path:
            target_service = module_path.split(".", 1)[0]
            if target_service != self.service_name:
                self._report_cross_import(node, f"{'.' * level}{module_path}")
            return
        for imported in _imported_names(node):
            if imported != self.service_name:
                self._report_cross_import(node, f"{'.' * level}{imported}")

    def _check_absolute_from_import(self, node: cst.ImportFrom, module_path: str) -> None:
        """Flag absolute 'from qb_cubie.core.services...' imports targeting a sibling."""
        sibling = _extract_sibling_from_absolute(module_path, self.service_name)
        if sibling is not None:
            self._report_cross_import(node, module_path)
            return
        if module_path in SERVICE_PREFIXES:
            for imported in _imported_names(node):
                if imported != self.service_name:
                    self._report_cross_import(node, f"{module_path}.{imported}")


def build_service_isolation_linter(service_name: str, *, default_services_level: int = 2) -> CstLinter:
    """Create the configured CstLinter instance for Meta-Gate 4 service isolation checks."""
    rule = ServiceIsolationImportRule(service_name, default_services_level=default_services_level)
    return CstLinter(rules=[rule], excludes=SCAN_EXCLUDES)


class PureDomainIoRule(CstRule):
    """Detect forbidden I/O imports, file/console calls, and sys.argv in pure domain modules."""

    def _report_io(self, node: cst.CSTNode, symbol: str) -> None:
        """Record a META-SERVICE-PURE-DOMAIN-IO diagnostic for forbidden I/O usage."""
        self.add_diagnostic(
            node=node,
            rule_id=PURE_IO_RULE_ID,
            message=(
                f"Verbotene I/O-Operation '{symbol}' im reinen Domain-Modul "
                "(DEV-GUIDE_Services.md: Functional Core / Imperative Shell)."
            ),
            node_name=symbol,
        )

    def visit_Import(self, node: cst.Import) -> None:
        """Flag 'import subprocess' inside pure domain modules."""
        if not self._module:
            return
        for alias in node.names:
            module_path = self._module.code_for_node(alias.name)
            if module_path == "subprocess" or module_path.startswith("subprocess."):
                self._report_io(alias, module_path)

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Flag 'from subprocess import ...' inside pure domain modules."""
        if not self._module or node.relative or node.module is None:
            return
        module_path = self._module.code_for_node(node.module)
        if module_path == "subprocess" or module_path.startswith("subprocess."):
            self._report_io(node, module_path)

    def visit_Call(self, node: cst.Call) -> None:
        """Flag direct open()/print() and Path file-I/O method calls in pure domain modules."""
        if isinstance(node.func, cst.Name) and node.func.value in FORBIDDEN_IO_CALLS:
            self._report_io(node, node.func.value)
        elif isinstance(node.func, cst.Attribute) and node.func.attr.value in FORBIDDEN_IO_ATTR_CALLS:
            self._report_io(node, node.func.attr.value)

    def visit_Attribute(self, node: cst.Attribute) -> None:
        """Flag direct sys.argv access in pure domain modules."""
        if isinstance(node.value, cst.Name) and node.value.value == "sys" and node.attr.value == "argv":
            self._report_io(node, "sys.argv")


def build_pure_domain_io_linter() -> CstLinter:
    """Create the configured CstLinter instance for pure domain I/O checks."""
    return CstLinter(rules=[PureDomainIoRule()], excludes=SCAN_EXCLUDES)


# ========== 1. WÄCHTER-KALIBRIERUNG: SERVICE-ISOLATION (CLEAN / FAULT / FILE PROBES) ==================================


@pytest.mark.parametrize(
    "clean_source",
    [
        "import re\nfrom pathlib import Path\n",
        "from qb_cubie import EBT, WorldState\n",
        "from qb_cubie.core.protocols import Arena, Reporter\n",
        "from ...linter import DEFAULT_EXCLUDES\n",
        "from ...protocols import Reporter\n",
        "from .protocols import DocFrameReport\n",
        "from qb_cubie.core.services.doc_frame.protocols import DocumentCatalog\n",
        'note = "from ..doc_ensurance.protocols import DocDiagnostic"\n',
    ],
    ids=[
        "stdlib-imports",
        "top-level-qb_cubie",
        "core-protocols-absolute",
        "core-linter-relative",
        "core-protocols-relative",
        "same-service-relative",
        "same-service-absolute",
        "string-literal-only",
    ],
)
def test_service_isolation_rule_accepts_clean_probes(clean_source: str) -> None:
    """Clean probe: stdlib, core, same-service, and string-only sources yield zero diagnostics."""
    linter = build_service_isolation_linter("doc_frame")
    EBT(
        target=linter.check,
        pre=WorldState(args=(clean_source,)),
        post=WorldState(returns=[]),
        reporter=None,
    ).run()


@pytest.mark.parametrize(
    "bad_source, expected_line, expected_node",
    [
        (
            "from ..doc_ensurance.protocols import DocDiagnostic\n",
            1,
            "..doc_ensurance.protocols",
        ),
        (
            "def _run():\n    from ..doc_frame.doc_frame import DocFrame\n",
            2,
            "..doc_frame.doc_frame",
        ),
        (
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
            "    from ..doc_ensurance.protocols import DocDiagnostic\n",
            3,
            "..doc_ensurance.protocols",
        ),
        (
            "from qb_cubie.core.services.doc_ensurance.protocols import DocDiagnostic\n",
            1,
            "qb_cubie.core.services.doc_ensurance.protocols",
        ),
        (
            "import qb_cubie.core.services.doc_ensurance\n",
            1,
            "qb_cubie.core.services.doc_ensurance",
        ),
        (
            "import os, qb_cubie.core.services.doc_ensurance as de\n",
            1,
            "qb_cubie.core.services.doc_ensurance",
        ),
        (
            "from .. import doc_ensurance\n",
            1,
            "..doc_ensurance",
        ),
        (
            "from qb_cubie.core.services import doc_ensurance\n",
            1,
            "qb_cubie.core.services.doc_ensurance",
        ),
    ],
    ids=[
        "relative-sibling-top-level",
        "relative-sibling-lazy-function",
        "relative-sibling-type-checking",
        "absolute-from-sibling",
        "absolute-import-sibling",
        "multi-import-sibling-alias",
        "relative-parent-import-sibling",
        "absolute-services-import-sibling",
    ],
)
def test_service_isolation_rule_detects_fault_probes(
    bad_source: str,
    expected_line: int,
    expected_node: str,
) -> None:
    """Fault probe: any cross-service import triggers META-SERVICE-ISOLATION with exact line."""
    service_name = "doc_ensurance" if "doc_frame" in bad_source else "doc_frame"
    linter = build_service_isolation_linter(service_name)

    def has_expected_diagnostic(diagnostics: list[LinterDiagnostic]) -> bool:
        if len(diagnostics) != 1:
            return False
        diag = diagnostics[0]
        return (
            diag.rule_id == ISOLATION_RULE_ID
            and diag.line == expected_line
            and diag.node_name == expected_node
        )

    EBT(
        target=linter.check,
        pre=WorldState(args=(bad_source,)),
        post=WorldState(returns=has_expected_diagnostic),
        reporter=None,
    ).run()


def test_service_isolation_rule_reports_file_path_on_disk(tmp_path: Path) -> None:
    """File probe: diagnostics report the concrete file path and line on disk."""
    bad_file = tmp_path / "broken_service_module.py"
    bad_file.write_text(
        "import re\nfrom ..doc_ensurance.protocols import DocDiagnostic\n",
        encoding="utf-8",
    )
    diagnostics = build_service_isolation_linter("doc_frame").check(bad_file)
    assert len(diagnostics) == 1, _format_diagnostics(diagnostics)
    assert diagnostics[0].file_path == str(bad_file)
    assert diagnostics[0].rule_id == ISOLATION_RULE_ID
    assert diagnostics[0].line == 2


# ========== 2. WÄCHTER-KALIBRIERUNG: PURE DOMAIN I/O (CLEAN / FAULT PROBES) ===========================================


@pytest.mark.parametrize(
    "clean_source",
    [
        "from pathlib import Path\ndef norm(p: str) -> str:\n    return Path(p).as_posix()\n",
        "from dataclasses import dataclass\n@dataclass(frozen=True)\nclass Item:\n    name: str\n",
        'hint = "Use print(result) or Path.read_text() in adapters."\n',
    ],
    ids=[
        "pure-path-manipulation",
        "frozen-dataclass",
        "string-literal-mentioning-io",
    ],
)
def test_pure_domain_io_rule_accepts_clean_probes(clean_source: str) -> None:
    """Clean probe: pure path logic, dataclasses, and strings yield zero diagnostics."""
    linter = build_pure_domain_io_linter()
    EBT(
        target=linter.check,
        pre=WorldState(args=(clean_source,)),
        post=WorldState(returns=[]),
        reporter=None,
    ).run()


@pytest.mark.parametrize(
    "bad_source, expected_line, expected_symbol",
    [
        ("import subprocess\n", 1, "subprocess"),
        ("from subprocess import run\n", 1, "subprocess"),
        ("def load(p):\n    return open(p)\n", 2, "open"),
        ("def load(p):\n    return p.read_text()\n", 2, "read_text"),
        ("def save(p, text):\n    p.write_text(text)\n", 2, "write_text"),
        ("def debug(x):\n    print(x)\n", 2, "print"),
        ("import sys\nARGS = sys.argv[1:]\n", 2, "sys.argv"),
    ],
    ids=[
        "import-subprocess",
        "from-subprocess",
        "builtin-open",
        "path-read-text",
        "path-write-text",
        "builtin-print",
        "sys-argv",
    ],
)
def test_pure_domain_io_rule_detects_fault_probes(
    bad_source: str,
    expected_line: int,
    expected_symbol: str,
) -> None:
    """Fault probe: forbidden I/O operations trigger META-SERVICE-PURE-DOMAIN-IO."""
    linter = build_pure_domain_io_linter()

    def has_expected_diagnostic(diagnostics: list[LinterDiagnostic]) -> bool:
        if len(diagnostics) != 1:
            return False
        diag = diagnostics[0]
        return (
            diag.rule_id == PURE_IO_RULE_ID
            and diag.line == expected_line
            and diag.node_name == expected_symbol
        )

    EBT(
        target=linter.check,
        pre=WorldState(args=(bad_source,)),
        post=WorldState(returns=has_expected_diagnostic),
        reporter=None,
    ).run()


# ========== 3. REPOSITORY GATES: SERVICE-ISOLATION, PURE DOMAIN, BUDGET & CORE PROMOTION ==============================


@pytest.mark.parametrize("service_name", _discover_service_packages())
def test_repository_services_have_no_cross_service_imports(service_name: str) -> None:
    """Repository gate (Section 1 & 5.1): a service must never import a sibling service."""
    service_dir = SERVICES_ROOT / service_name
    diagnostics = build_service_isolation_linter(service_name).check(service_dir)
    assert diagnostics == [], (
        f"Cross-service imports found in service '{service_name}':\n"
        f"{_format_diagnostics(diagnostics)}"
    )


@pytest.mark.parametrize("service_name", _discover_service_packages())
def test_repository_service_pure_domain_modules_have_no_io(service_name: str) -> None:
    """Repository gate (Section 2 & 5.1): pure domain modules must not perform I/O."""
    service_dir = SERVICES_ROOT / service_name
    pure_files = [
        path
        for path in sorted(service_dir.rglob("*.py"))
        if path.name in PURE_DOMAIN_FILENAMES or path.name.endswith("_rules.py")
    ]
    linter = build_pure_domain_io_linter()
    diagnostics: list[LinterDiagnostic] = []
    for path in pure_files:
        diagnostics.extend(linter.check(path))
    assert diagnostics == [], (
        f"Forbidden I/O found in pure domain modules of '{service_name}':\n"
        f"{_format_diagnostics(diagnostics)}"
    )


@pytest.mark.parametrize("service_name", _discover_service_packages())
def test_service_imports_in_isolation_with_siblings_blocked(service_name: str) -> None:
    """Isolation probe (Section 5.2): importing one service must succeed with all siblings blocked."""
    siblings = [name for name in _discover_service_packages() if name != service_name]
    probe_script = (
        "import importlib, sys\n"
        f"BLOCKED = {tuple(f'qb_cubie.core.services.{s}' for s in siblings)!r}\n"
        "class _SiblingBlocker:\n"
        "    def find_spec(self, fullname, path, target=None):\n"
        "        for prefix in BLOCKED:\n"
        "            if fullname == prefix or fullname.startswith(prefix + '.'):\n"
        "                raise ModuleNotFoundError(f'Blocked sibling service: {fullname}')\n"
        "        return None\n"
        "sys.meta_path.insert(0, _SiblingBlocker())\n"
        f"importlib.import_module('qb_cubie.core.services.{service_name}')\n"
        "leaked = [m for m in sys.modules if any(m == b or m.startswith(b + '.') for b in BLOCKED)]\n"
        "assert not leaked, f'Leaked sibling modules: {leaked}'\n"
    )

    def run_isolation_probe() -> int:
        proc = subprocess.run(
            [sys.executable, "-c", probe_script],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"Service '{service_name}' failed isolated import (siblings blocked: {siblings}):\n"
                f"{proc.stdout}\n{proc.stderr}"
            )
        return proc.returncode

    EBT(
        target=run_isolation_probe,
        post=WorldState(returns=0),
        reporter=None,
    ).run()


def _internal_module_edges(service_dir: Path, service_name: str) -> dict[str, set[str]]:
    """Build the directed internal import graph across non-facade modules of one service."""
    modules = {
        path.stem: path
        for path in sorted(service_dir.glob("*.py"))
        if path.name not in {"__init__.py", "__main__.py"}
    }
    graph: dict[str, set[str]] = {name: set() for name in modules}
    abs_prefix = f"qb_cubie.core.services.{service_name}."
    for mod_name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level == 1 and node.module:
                    target = node.module.split(".", 1)[0]
                    if target in modules and target != mod_name:
                        graph[mod_name].add(target)
                elif node.level == 0 and node.module and node.module.startswith(abs_prefix):
                    target = node.module[len(abs_prefix) :].split(".", 1)[0]
                    if target in modules and target != mod_name:
                        graph[mod_name].add(target)
    return graph


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Return a directed cycle path if the internal module graph is cyclic, else None."""
    state: dict[str, int] = {}
    stack: list[str] = []

    def dfs(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for neighbor in sorted(graph.get(node, ())):
            if state.get(neighbor, 0) == 1:
                return [*stack[stack.index(neighbor) :], neighbor]
            if state.get(neighbor, 0) == 0:
                cycle = dfs(neighbor)
                if cycle is not None:
                    return cycle
        stack.pop()
        state[node] = 2
        return None

    for mod in sorted(graph):
        if state.get(mod, 0) == 0:
            cycle = dfs(mod)
            if cycle is not None:
                return cycle
    return None


@pytest.mark.parametrize("service_name", _discover_service_packages())
def test_service_internal_import_graph_is_acyclic(service_name: str) -> None:
    """Layer audit (Section 2 & 5.3): internal module imports inside a service must be acyclic."""
    graph = _internal_module_edges(SERVICES_ROOT / service_name, service_name)
    cycle = _find_cycle(graph)
    assert cycle is None, f"Cyclic internal import in service '{service_name}': {' -> '.join(cycle)}"


@pytest.mark.parametrize("service_name", _discover_service_packages())
def test_service_module_size_budget(service_name: str) -> None:
    """Budget audit (Section 2 & 5.3): service modules must stay within 500 lines."""
    service_dir = SERVICES_ROOT / service_name
    violations: list[str] = []
    for path in sorted(service_dir.rglob("*.py")):
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > SERVICE_MODULE_LINE_LIMIT:
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            violations.append(
                f"{rel}:1: {line_count} lines (maximum {SERVICE_MODULE_LINE_LIMIT} for services)"
            )
    assert not violations, "\n" + "\n".join(violations)


def test_core_provides_promoted_diagnostic_primitives() -> None:
    """Core promotion (Section 3 & 4): domain-neutral Diagnostic & validate_severity live in Core."""
    from qb_cubie.core import protocols as core_protocols

    missing = [
        symbol
        for symbol in ("Diagnostic", "VALID_SEVERITIES", "validate_severity")
        if not hasattr(core_protocols, symbol)
    ]
    assert not missing, (
        "Core protocols missing promoted domain-neutral primitives "
        f"(DEV-GUIDE_Services.md Section 3 & 4): {missing}"
    )

    validate_severity = core_protocols.validate_severity
    diagnostic_cls = core_protocols.Diagnostic
    assert validate_severity("error") == "error"
    assert validate_severity("warning") == "warning"
    with pytest.raises(ValueError, match="STATE-GUARD"):
        validate_severity("fatal")
    diag = diagnostic_cls(file_path="doc.md", rule_id="CORE-TEST", line=1, message="msg")
    assert diag.severity == "error"
    with pytest.raises(ValueError, match="STATE-GUARD"):
        diagnostic_cls(file_path="doc.md", rule_id="CORE-TEST", line=1, message="msg", severity="invalid")


def test_doc_ensurance_has_no_doc_frame_domain_coupling() -> None:
    """Domain cleanup (Section 4): doc_ensurance must not contain DocFrame/FramePattern special logic."""
    doc_ensurance_dir = SERVICES_ROOT / "doc_ensurance"
    hits: list[str] = []
    for path in sorted(doc_ensurance_dir.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in FORBIDDEN_DOC_FRAME_SYMBOLS:
                hits.append(f"{rel}:{node.lineno}: [{DOMAIN_COUPLING_RULE_ID}] Name '{node.id}'")
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in FORBIDDEN_DOC_FRAME_SYMBOLS:
                hits.append(f"{rel}:{node.lineno}: [{DOMAIN_COUPLING_RULE_ID}] String '{node.value}'")
            elif isinstance(node, ast.ImportFrom) and node.module and "doc_frame" in node.module:
                hits.append(f"{rel}:{node.lineno}: [{DOMAIN_COUPLING_RULE_ID}] Import '{node.module}'")
    assert not hits, (
        "DocFrame-specific domain coupling found in doc_ensurance "
        "(DEV-GUIDE_Services.md Section 4):\n" + "\n".join(hits)
    )
