"""Tries to verify target resolution, project root discovery, exclusions, and TTL timeouts in DocEnsurance."""

from pathlib import Path
from typing import Any, Sequence

from qb_cubie import EBT, ExceptionExpectation, TempFS, WorldState
from qb_cubie.services import CUBIE_DOC_STYLE, DocEnsurance

_VALID_DOC = (
    "Ausreichend lange Erklärung für ein valides Code-Beispiel.\n\n"
    "```python\n"
    "print('ok')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nok\n```\n</details>"
)

_BROKEN_DOC = (
    "Dieses Dokument enthält einen absichtlichen Laufzeitfehler.\n\n"
    "```python\n"
    "raise RuntimeError('should have been excluded')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)

_BLOCKING_INPUT_DOC = (
    "Dieses Dokument blockiert ohne TTL-Timeout dauerhaft bei einer Konsoleneingabe.\n\n"
    "```python\n"
    "import time\n"
    "time.sleep(5)\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)

_INFINITE_WAIT_DOC = (
    "Dieses Dokument hängt in einer Endlosschleife fest.\n\n"
    "```python\n"
    "while True:\n"
    "    pass\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)


def _seed_project_tree(root: Path) -> None:
    """Creates a synthetic project layout with valid and broken Markdown files."""
    (root / "pyproject.toml").write_text("[project]\nname = 'dummy'\n", encoding="utf-8")
    for folder in ("docs", "docs/drafts", "experiments", ".venv"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guide.md").write_text(_VALID_DOC, encoding="utf-8")
    (root / "docs" / "drafts" / "wip.md").write_text(_BROKEN_DOC, encoding="utf-8")
    (root / "experiments" / "study.md").write_text(_BROKEN_DOC, encoding="utf-8")
    (root / "GUTACHTEN.md").write_text(_BROKEN_DOC, encoding="utf-8")
    (root / ".venv" / "ignored.md").write_text(_BROKEN_DOC, encoding="utf-8")


def _run_config_scenario(
    target: str | Path | None, excludes: Sequence[str] | None = None
) -> dict[str, Any]:
    """Hydrates a project tree in CWD and runs DocEnsurance with the given config."""
    _seed_project_tree(Path.cwd())
    report = DocEnsurance(
        target=target, pattern=CUBIE_DOC_STYLE, excludes=excludes, reporter=None
    ).run()
    return {
        "passed": report.passed,
        "session_count": len(report.sessions),
        "diagnostics": [d.rule_id for d in report.diagnostics],
    }


# ======================================================================================================================
# 1. PROJEKT-ROOT-DISCOVERY (target=None) & KOMBINIERTE EXCLUDES
# ======================================================================================================================
def test_ebt_default_project_scan_and_excludes() -> None:
    """Verifies that target=None scans the project root and honors folder, file, and subpath excludes."""
    EBT(
        target=_run_config_scenario,
        arena=TempFS(),
        pre=[
            WorldState(args=(None, ("experiments", "docs/drafts", "GUTACHTEN.md"))),
            WorldState(args=("docs", ("drafts",))),
            WorldState(args=(Path("docs"), ("docs/drafts",))),
        ],
        post=WorldState(returns={"passed": True, "session_count": 1, "diagnostics": []}),
        custom_id="doc_config_project_scan_and_excludes",
    ).run()


def test_ebt_unexcluded_broken_files_trigger_alarm() -> None:
    """Verifies that omitting an exclude exposes the broken Markdown files in the project tree."""
    EBT(
        target=_run_config_scenario,
        arena=TempFS(),
        pre=WorldState(args=(None, ("experiments", "docs/drafts"))),
        post=WorldState(returns={"passed": False, "session_count": 2, "diagnostics": ["DOC-EXEC"]}),
        custom_id="doc_config_missing_exclude_alarm",
    ).run()


# ======================================================================================================================
# 2. GEZIELTE EINZELDATEI-PRÜFUNG (STRING & PATH)
# ======================================================================================================================
def test_ebt_single_file_target_resolution() -> None:
    """Verifies that single Markdown files can be checked via str or Path."""
    EBT(
        target=_run_config_scenario,
        arena=TempFS(),
        pre=[
            WorldState(args=("docs/guide.md",)),
            WorldState(args=(Path("docs/guide.md"),)),
        ],
        post=WorldState(returns={"passed": True, "session_count": 1, "diagnostics": []}),
        custom_id="doc_config_single_file_targets",
    ).run()


# ======================================================================================================================
# 3. ELTERNPFAD-ISOLATION BEI EXCLUDES
# ======================================================================================================================
def _parent_collision_scenario() -> dict[str, Any]:
    """Runs DocEnsurance inside a root folder whose own parent is named like an exclude."""
    nested_root = Path.cwd() / "experiments" / "subproject"
    nested_root.mkdir(parents=True, exist_ok=True)
    (nested_root / "guide.md").write_text(_VALID_DOC, encoding="utf-8")
    report = DocEnsurance(target=nested_root, excludes=("experiments",), reporter=None).run()
    return {"passed": report.passed, "session_count": len(report.sessions)}


def test_ebt_exclude_does_not_match_parent_directories_above_root() -> None:
    """Verifies that excludes only match relative to the scan root, never parent segments above it."""
    EBT(
        target=_parent_collision_scenario,
        arena=TempFS(),
        pre=WorldState(),
        post=WorldState(returns={"passed": True, "session_count": 1}),
        custom_id="doc_config_parent_path_isolation",
    ).run()


# ======================================================================================================================
# 4. TIPPFEHLER BEI STRING-PFADEN (VERZEICHNIS & DATEI EXISTIEREN NICHT)
# ======================================================================================================================
def test_ebt_missing_string_or_path_targets_raise_file_not_found() -> None:
    """Verifies that non-existent directory or file strings raise FileNotFoundError instead of passing."""
    EBT(
        target=_run_config_scenario,
        arena=TempFS(),
        pre=[
            WorldState(args=("docs_typo",)),
            WorldState(args=("docs/missing_subfolder",)),
            WorldState(args=("docs/missing folder",)),
            WorldState(args=("docs/missing_guide.md",)),
            WorldState(args=(Path("docs_typo"),)),
        ],
        post=WorldState(raises=ExceptionExpectation(FileNotFoundError, match=r"STATE-GUARD:")),
        custom_id="doc_config_missing_target_guards",
    ).run()


# ======================================================================================================================
# 5. KONFIGURIERBARE TTL-TIMEOUTS & STATE-GUARDS
# ======================================================================================================================
def _run_with_ttl_timeout(
    doc: str, timeout: Any, custom_arena: Any = None
) -> dict[str, Any]:
    """Runs DocEnsurance with a configured TTL timeout and returns the execution status."""
    service = DocEnsurance(target=doc, arena=custom_arena, timeout=timeout, reporter=None)
    report = service.run()
    return {"passed": report.passed, "arena_timeout": getattr(service.arena, "timeout", None)}


def test_ebt_configurable_ttl_timeout_execution_and_propagation() -> None:
    """Verifies that TTL timeouts propagate to arenas and abort blocking snippets with TimeoutError."""
    EBT(
        target=_run_with_ttl_timeout,
        pre=[
            WorldState(args=(_VALID_DOC, 2.5)),
            WorldState(args=(_VALID_DOC, 2.5, TempFS())),
        ],
        post=WorldState(returns={"passed": True, "arena_timeout": 2.5}),
        custom_id="doc_config_ttl_timeout_propagation",
    ).run()
    EBT(
        target=_run_with_ttl_timeout,
        pre=[
            WorldState(args=(_BLOCKING_INPUT_DOC, 0.15)),
            WorldState(args=(_INFINITE_WAIT_DOC, 0.15)),
            WorldState(args=(_INFINITE_WAIT_DOC, 0.15, TempFS())),
        ],
        post=WorldState(raises=ExceptionExpectation(TimeoutError, match=r"timed out")),
        custom_id="doc_config_ttl_timeout_enforcement",
    ).run()


def test_ebt_invalid_ttl_timeout_state_guards() -> None:
    """Verifies that non-positive, non-finite, or non-numeric timeouts trigger STATE-GUARDs."""
    EBT(
        target=_run_with_ttl_timeout,
        pre=[
            WorldState(args=(_VALID_DOC, 0)),
            WorldState(args=(_VALID_DOC, -1.5)),
            WorldState(args=(_VALID_DOC, float("inf"))),
            WorldState(args=(_VALID_DOC, float("nan"))),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD: timeout")),
        custom_id="doc_config_ttl_timeout_value_guards",
    ).run()
    EBT(
        target=_run_with_ttl_timeout,
        pre=[
            WorldState(args=(_VALID_DOC, False)),
            WorldState(args=(_VALID_DOC, "5s")),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD: timeout")),
        custom_id="doc_config_ttl_timeout_type_guards",
    ).run()