"""**Tries to** verify CUBIE_DOCFRAME_RULES in DocEnsurance, layer orthogonality, excludes, and STATE-GUARDs."""

from pathlib import Path
import re
from typing import Any

import pytest

from qb_cubie import EBT, ExceptionExpectation, PytestReporter, TempFS, WorldState
from qb_cubie.services import (
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
    CUBIE_DOC_RULES,
    CUBIE_DOC_STYLE,
    CUBIE_DOCFRAME_RULES,
    DocEnsurance,
    DocFrame,
)


def _framed_doc(title: str, banner: str = "cubie-logo-written.png", body: str = "Textkörper.") -> str:
    """Creates a minimal framed Markdown document for test scenarios."""
    return (
        f'<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="{banner}" -->\n'
        f'<div align="center">\n\n# {title}\n\n![Cubie](.assets/{banner})\n\n'
        "Kurze Beschreibung des Dokuments.\n\n---\n\n---\n\n</div>\n<!-- /qb:frame -->\n\n"
        f"{body}\n\n"
        '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n'
    )


def _seed_synced_tree(root: Path) -> None:
    """Creates a valid project layout and synchronizes all frames via DocFrame.update()."""
    (root / "pyproject.toml").write_text("[project]\nname = 'cubie-rules'\n", encoding="utf-8")
    for folder in ("docs/.assets", "docs/services", "experiments", ".venv"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for asset in ("cubie-banner.png", "cubie-logo-written.png", "cubie-small.png"):
        (root / "docs" / ".assets" / asset).write_bytes(b"PNG")
    (root / "README.md").write_text(_framed_doc("Root", "cubie-banner.png"), encoding="utf-8")
    (root / "docs" / "GUIDE_Quality-Assurance.md").write_text(_framed_doc("QA"), encoding="utf-8")
    (root / "docs" / "services" / "GUIDE_DocEnsurance.md").write_text(_framed_doc("Service"), encoding="utf-8")
    (root / "experiments" / "unframed.md").write_text("# Ohne Rahmen im Exclude\n", encoding="utf-8")
    (root / "GUTACHTEN.md").write_text("# Gutachten im Exclude\n", encoding="utf-8")
    (root / ".venv" / "ignored.md").write_text("# Venv Exclude\n", encoding="utf-8")
    DocFrame.update(target=root, excludes=("experiments", "GUTACHTEN.md"))


def _run_docframe_check(fault: str = "clean") -> dict[str, Any]:
    """Seeds a synced tree, injects a specific fault, and runs DocEnsurance with CUBIE_DOCFRAME_RULES."""
    root = Path.cwd()
    _seed_synced_tree(root)
    _inject_fault(root, fault)
    patterns = [CUBIE_DOC_STYLE, CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3]
    rules = (CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES)
    report = DocEnsurance(
        target=root, pattern=patterns, rules=rules, excludes=("experiments", "GUTACHTEN.md"), reporter=None
    ).run()
    return {
        "passed": report.passed,
        "diagnostics": [(d.rule_id, d.severity, Path(d.file_path).name) for d in report.diagnostics],
    }


def _inject_fault(root: Path, fault: str) -> None:
    """Injects a targeted frame or code fault into the workspace before verification."""
    qa = root / "docs" / "GUIDE_Quality-Assurance.md"
    if fault == "missing_foot":
        qa.write_text('<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# QA\n<!-- /qb:frame -->\n', encoding="utf-8")
    elif fault == "missing_router_zone":
        qa.write_text(qa.read_text(encoding="utf-8").replace("CUBIE_DOC_FRAME_1", "CUBIE_DOC_FRAME_3"), encoding="utf-8")
    elif fault == "empty_file":
        (root / "docs" / "EMPTY.md").write_text("", encoding="utf-8")
    elif fault == "unclosed_tag":
        qa.write_text('<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# QA\n', encoding="utf-8")
    elif fault != "clean":
        _inject_secondary_fault(root, qa, fault)


def _inject_secondary_fault(root: Path, qa: Path, fault: str) -> None:
    """Injects outdated, broken-route, provenance, or orthogonal code faults."""
    if fault == "outdated_alt":
        old_img = "![Error while trying to load the image](.assets/cubie-small.png)"
        qa.write_text(qa.read_text(encoding="utf-8").replace("![Cubie](.assets/cubie-small.png)", old_img), encoding="utf-8")
    elif fault == "outdated_new_file":
        (root / "docs" / "GUIDE_Added.md").write_text(qa.read_text(encoding="utf-8"), encoding="utf-8")
    elif fault == "broken_banner":
        (root / "docs" / ".assets" / "cubie-small.png").unlink()
    elif fault == "provenance_incomplete":
        _write_incomplete_provenance_doc(root, qa)
    elif fault == "orthogonal_frame_and_code":
        _write_orthogonal_broken_doc(qa)


def _write_incomplete_provenance_doc(root: Path, qa: Path) -> None:
    """Writes a CUBIE_DOC_FRAME_2 file with a missing required Model value."""
    foot_part = qa.read_text(encoding="utf-8").split('<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->')[1]
    content = (
        '<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" -->\n'
        "**Dokument-Informationen & Herkunft:**\n- **Plattform / Umgebung:** Linux\n- **Modell:** \n\n---\n"
        '<!-- /qb:frame -->\n\nBody.\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->' + foot_part
    )
    (root / "docs" / "REPORT.md").write_text(content, encoding="utf-8")


def _write_orthogonal_broken_doc(qa: Path) -> None:
    """Overwrites a guide with both missing frames and a failing Python code example."""
    bad_code = (
        "# QA\n\n"
        "Ausreichend lange Erklärung vor einem fehlerhaften Python-Beispiel.\n\n"
        "```python\nprint(21 * 2)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n99\n```\n</details>\n"
    )
    qa.write_text(bad_code, encoding="utf-8")


def _run_pytest_reporter_on_fault() -> None:
    """Runs DocEnsurance with default PytestReporter on a workspace with a missing frame."""
    root = Path.cwd()
    _seed_synced_tree(root)
    (root / "docs" / "BROKEN.md").write_text("# Ohne Rahmen\n", encoding="utf-8")
    DocEnsurance(
        target=root,
        rules=CUBIE_DOCFRAME_RULES,
        excludes=("experiments", "GUTACHTEN.md"),
        reporter=PytestReporter(),
    ).run()


def _trigger_state_guard(case: str) -> Any:
    """Triggers a specific STATE-GUARD configuration error in DocFrame."""
    root = Path.cwd()
    _seed_synced_tree(root)
    if case == "missing_path":
        return DocFrame.update(target=root / "non_existent_folder")
    if case == "invalid_target_type":
        return DocFrame.update(target=12345)  # type: ignore[arg-type]
    if case == "invalid_pattern_type":
        return DocFrame.update(target=root, pattern=["not_a_pattern"])  # type: ignore[list-item]
    return _trigger_value_state_guard(root, case)


def _trigger_value_state_guard(root: Path, case: str) -> Any:
    """Triggers ValueError STATE-GUARDs for unknown frame IDs, invalid zones, or empty directories."""
    qa = root / "docs" / "GUIDE_Quality-Assurance.md"
    if case == "unknown_frame_id":
        qa.write_text('<!-- qb:frame id="UNKNOWN_FRAME_99" zone="head" -->\n<!-- /qb:frame -->\n', encoding="utf-8")
        return DocFrame.update(target=root, excludes=("experiments", "GUTACHTEN.md"))
    if case == "invalid_zone_name":
        qa.write_text('<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="middle" -->\n<!-- /qb:frame -->\n', encoding="utf-8")
        return DocFrame.update(target=root, excludes=("experiments", "GUTACHTEN.md"))
    return DocFrame.update(target=root, excludes=("README.md", "docs", "experiments", "GUTACHTEN.md"))


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: DIAGNOSE-REGELN (`CUBIE_DOCFRAME_RULES`) & ORTHOGONALITÄT
# ======================================================================================================================
def test_ebt_synced_workspace_passes_docframe_rules_cleanly() -> None:
    """Verifies that a synchronized project tree passes CUBIE_DOCFRAME_RULES with zero diagnostics."""
    EBT(
        target=_run_docframe_check,
        arena=TempFS(),
        pre=WorldState(args=("clean",)),
        post=WorldState(returns={"passed": True, "diagnostics": []}),
        custom_id="docframe_rules_clean_pass",
    ).run()


@pytest.mark.parametrize(
    "fault, expected_file",
    [
        ("missing_foot", "GUIDE_Quality-Assurance.md"),
        ("missing_router_zone", "GUIDE_Quality-Assurance.md"),
        ("empty_file", "EMPTY.md"),
        ("unclosed_tag", "GUIDE_Quality-Assurance.md"),
    ],
)
def test_ebt_docframe_missing_rule_cases(fault: str, expected_file: str) -> None:
    """Verifies that DOCFRAME-MISSING flags missing head/foot/router zones, 0-byte files, and unclosed tags."""
    EBT(
        target=_run_docframe_check,
        arena=TempFS(),
        pre=WorldState(args=(fault,)),
        post=WorldState(
            returns={"passed": False, "diagnostics": [("DOCFRAME-MISSING", "error", expected_file)]}
        ),
        custom_id=f"docframe_rule_missing_{fault}",
    ).run()


def test_ebt_docframe_outdated_rule_on_stale_alt_text() -> None:
    """Verifies that DOCFRAME-OUTDATED flags stale footer alt text before DocFrame.update() runs."""
    expected = {"passed": False, "diagnostics": [("DOCFRAME-OUTDATED", "error", "GUIDE_Quality-Assurance.md")]}
    EBT(
        target=_run_docframe_check,
        arena=TempFS(),
        pre=WorldState(args=("outdated_alt",)),
        post=WorldState(returns=expected),
        custom_id="docframe_rule_outdated_alt",
    ).run()


def test_ebt_docframe_broken_route_rule_on_missing_asset() -> None:
    """Verifies that DOCFRAME-BROKEN-ROUTE flags missing banner or route target files in the workspace."""
    expected_diags = [
        ("DOCFRAME-BROKEN-ROUTE", "error", "README.md"),
        ("DOCFRAME-BROKEN-ROUTE", "error", "GUIDE_Quality-Assurance.md"),
        ("DOCFRAME-BROKEN-ROUTE", "error", "GUIDE_DocEnsurance.md"),
    ]
    EBT(
        target=_run_docframe_check,
        arena=TempFS(),
        pre=WorldState(args=("broken_banner",)),
        post=WorldState(returns={"passed": False, "diagnostics": expected_diags}),
        custom_id="docframe_rule_broken_route",
    ).run()


def test_ebt_docframe_provenance_incomplete_rule() -> None:
    """Verifies that DOCFRAME-PROVENANCE-INCOMPLETE flags missing or empty required provenance keys."""
    expected = {"passed": False, "diagnostics": [("DOCFRAME-PROVENANCE-INCOMPLETE", "error", "REPORT.md")]}
    EBT(
        target=_run_docframe_check,
        arena=TempFS(),
        pre=WorldState(args=("provenance_incomplete",)),
        post=WorldState(returns=expected),
        custom_id="docframe_rule_provenance_incomplete",
    ).run()


def test_ebt_orthogonality_between_docframe_and_doc_ensurance_code_rules() -> None:
    """Verifies that frame errors and Python snippet output errors are reported together without muting."""
    expected_diags = [
        ("DOCFRAME-MISSING", "error", "GUIDE_Quality-Assurance.md"),
        ("DOC-OUT", "error", "GUIDE_Quality-Assurance.md"),
    ]
    EBT(
        target=_run_docframe_check,
        arena=TempFS(),
        pre=WorldState(args=("orthogonal_frame_and_code",)),
        post=WorldState(returns={"passed": False, "diagnostics": expected_diags}),
        custom_id="docframe_rules_orthogonality",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: PYTEST-REPORTER & EXPLIZITE STATE-GUARDS
# ======================================================================================================================
def test_ebt_pytest_reporter_surfaces_docframe_diagnostics() -> None:
    """Verifies that PytestReporter raises an AssertionError with file and rule_id on DOCFRAME errors."""
    EBT(
        target=_run_pytest_reporter_on_fault,
        arena=TempFS(),
        pre=WorldState(),
        post=WorldState(
            raises=ExceptionExpectation(
                AssertionError, match=r"\[DOCFRAME-MISSING\].*BROKEN\.md:1:"
            )
        ),
        custom_id="docframe_pytest_reporter_integration",
    ).run()


def test_ebt_state_guard_missing_path() -> None:
    """Verifies that non-existent target paths trigger a FileNotFoundError STATE-GUARD."""
    EBT(
        target=_trigger_state_guard,
        arena=TempFS(),
        pre=WorldState(args=("missing_path",)),
        post=WorldState(raises=ExceptionExpectation(FileNotFoundError, match=r"STATE-GUARD:")),
        custom_id="docframe_guard_missing_path",
    ).run()


def test_ebt_state_guards_invalid_types() -> None:
    """Verifies that invalid target or pattern types trigger a TypeError STATE-GUARD."""
    EBT(
        target=_trigger_state_guard,
        arena=TempFS(),
        pre=[
            WorldState(args=("invalid_target_type",)),
            WorldState(args=("invalid_pattern_type",)),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="docframe_guard_invalid_types",
    ).run()


def test_ebt_state_guards_on_unknown_frame_id_zone_and_empty_dir() -> None:
    """Verifies that unknown frame IDs, invalid zone names, and empty targets raise ValueError STATE-GUARDs."""
    EBT(
        target=_trigger_state_guard,
        arena=TempFS(),
        pre=[
            WorldState(args=("unknown_frame_id",)),
            WorldState(args=("invalid_zone_name",)),
            WorldState(args=("all_excluded",)),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="docframe_guard_invalid_values",
    ).run()
