"""**Tries to** verify CUBIE_DOC_FRAME_1..3 presets, slot protection, and idempotence in DocFrame.update()."""

from pathlib import Path
from typing import Any

from qb_cubie import EBT, TempFS, WorldState
from qb_cubie.core.services import (
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
    DocFrame,
)

_FRAME_1_DOC = (
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-banner.png" -->\n'
    '<div align="center">\n\n# Mein Handbuch-Titel\n\n'
    "![Error while trying to load the image](wrong/path/cubie-banner.png)\n\n"
    "Geschützter Einführungstext mit wichtigen Erklärungen.\n\n---\n\n"
    "> Geschützter Disclaimer-Hinweis für dieses Handbuch.\n\n---\n\n"
    "[Veraltet](old.md)\n\n</div>\n<!-- /qb:frame -->\n\n"
    "## Kapitel 1\n\nGeschützter Haupttext außerhalb der Rahmen.\n\n"
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n'
    '<center>\n![Error while trying to load the image](.assets/cubie-small.png)\n</center>\n'
    "<!-- /qb:frame -->\n"
)

_FRAME_2_DOC = (
    '<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Gemini-CLI" model="Gemini-4-Argon" effort="High" -->\n'
    "# Pilot-Gutachten v9\n\n"
    "**Dokument-Informationen & Herkunft:**\n"
    "- **Plattform / Umgebung:** Veraltet\n"
    "- **Modell:** Alt\n"
    "- **Reasoning-Effort:** Low\n"
    "- **Analysedatum:** 16. November 2026\n"
    "- **Synthesebasis:** `STUDY.md`\n\n"
    "---\n\n"
    "Geschützte Leitfrage im PromptSlot vor dem Rumpf.\n"
    "<!-- /qb:frame -->\n\n"
    "Manueller Befundbericht im Dokumentkörper.\n\n"
    '<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->\n<!-- /qb:frame -->\n'
)

_FRAME_3_INDEX_DOC = (
    '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" banner="cubie-logo-written.png" -->\n'
    '<div align="center">\n\n# Hintergrund-Hub\n\n![Cubie](../.assets/cubie-logo-written.png)\n\n'
    "---\n\n---\n\n</div>\n<!-- /qb:frame -->\n\n"
    "Manueller Einleitungstext vor dem Router-Block.\n\n"
    '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->\n'
    "| Dokument | Inhalt und Geltung |\n| :--- | :--- |\n| [Veraltet](./old.md) | Alt |\n"
    "<!-- /qb:frame -->\n\n"
    "| Externe Tabelle | Hinweis |\n| --- | --- |\n| Bleibt erhalten | 100% |\n\n"
    '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->\n<!-- /qb:frame -->\n'
)

_ESSAY_DOC = (
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->\n'
    '<div align="center">\n\n# Clean-Code Pragmatismus\n\n![Cubie](../.assets/cubie-logo-written.png)\n\n'
    "Dieser Essay diskutiert pragmatische Clean-Code-Prinzipien.\n\n---\n\n---\n\n</div>\n"
    "<!-- /qb:frame -->\n\nEssay-Rumpf.\n\n"
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n'
)


def _seed_presets_workspace(root: Path) -> None:
    """Creates a synthetic workspace containing FRAME_1, FRAME_2, and FRAME_3 documents."""
    (root / "pyproject.toml").write_text("[project]\nname = 'cubie-presets'\n", encoding="utf-8")
    for folder in ("docs/.assets", "docs/services", "docs/misc"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for asset in ("cubie-banner.png", "cubie-logo-written.png", "cubie-small.png"):
        (root / "docs" / ".assets" / asset).write_bytes(b"PNG")
    (root / "README.md").write_text(_FRAME_1_DOC, encoding="utf-8")
    (root / "docs" / "GUIDE_Quality-Assurance.md").write_text(_FRAME_1_DOC, encoding="utf-8")
    (root / "docs" / "services" / "GUIDE_DocEnsurance.md").write_text(_FRAME_1_DOC, encoding="utf-8")
    (root / "docs" / "AUDIT_Report.md").write_text(_FRAME_2_DOC, encoding="utf-8")
    (root / "docs" / "misc" / "README.md").write_text(_FRAME_3_INDEX_DOC, encoding="utf-8")
    (root / "docs" / "misc" / "Clean-Code-Pragmatism.md").write_text(_ESSAY_DOC, encoding="utf-8")


def _run_preset_update_scenario(preset_kind: str) -> dict[str, Any]:
    """Runs DocFrame.update() in TempFS and projects slot preservation and frame updates."""
    root = Path.cwd()
    _seed_presets_workspace(root)
    patterns = (CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3)
    DocFrame.update(target=root, pattern=patterns)
    if preset_kind == "frame_1":
        return _inspect_frame_1(root / "docs" / "GUIDE_Quality-Assurance.md")
    if preset_kind == "frame_2":
        return _inspect_frame_2(root / "docs" / "AUDIT_Report.md")
    return _inspect_frame_3(root / "docs" / "misc" / "README.md")


def _inspect_frame_1(path: Path) -> dict[str, Any]:
    """Extracts slot preservation and footer normalization flags from a CUBIE_DOC_FRAME_1 file."""
    text = path.read_text(encoding="utf-8")
    return {
        "preserves_title": "# Mein Handbuch-Titel" in text,
        "preserves_intro": "Geschützter Einführungstext mit wichtigen Erklärungen." in text,
        "preserves_disclaimer": "> Geschützter Disclaimer-Hinweis für dieses Handbuch." in text,
        "preserves_body": "## Kapitel 1\n\nGeschützter Haupttext außerhalb der Rahmen." in text,
        "fixes_banner_and_alt": "![Cubie](.assets/cubie-banner.png)" in text,
        "fixes_footer_alt": "![Cubie](.assets/cubie-small.png)" in text,
        "removes_error_alt": "Error while trying to load the image" not in text,
        "uses_div_align_center": text.count('<div align="center">') == 2,
    }


def _inspect_frame_2(path: Path) -> dict[str, Any]:
    """Extracts provenance synchronization and slot preservation flags from a CUBIE_DOC_FRAME_2 file."""
    text = path.read_text(encoding="utf-8")
    return {
        "preserves_title": "# Pilot-Gutachten v9" in text,
        "syncs_env": "- **Plattform / Umgebung:** Gemini-CLI" in text,
        "syncs_model": "- **Modell:** Gemini-4-Argon" in text,
        "syncs_effort": "- **Reasoning-Effort:** High" in text,
        "preserves_custom_date": "- **Analysedatum:** 16. November 2026" in text,
        "preserves_custom_basis": "- **Synthesebasis:** `STUDY.md`" in text,
        "preserves_prompt": "Geschützte Leitfrage im PromptSlot vor dem Rumpf." in text,
        "preserves_body": "Manueller Befundbericht im Dokumentkörper." in text,
    }


def _inspect_frame_3(path: Path) -> dict[str, Any]:
    """Extracts router regeneration and manual body preservation flags from a CUBIE_DOC_FRAME_3 file."""
    text = path.read_text(encoding="utf-8")
    expected_row = (
        "| [Clean-Code Pragmatismus](./Clean-Code-Pragmatism.md) "
        "| Dieser Essay diskutiert pragmatische Clean-Code-Prinzipien. |"
    )
    return {
        "rebuilds_router_table": expected_row in text,
        "removes_stale_row": "[Veraltet](./old.md)" not in text,
        "preserves_pre_text": "Manueller Einleitungstext vor dem Router-Block." in text,
        "preserves_manual_table": "| Externe Tabelle | Hinweis |\n| --- | --- |\n| Bleibt erhalten | 100% |" in text,
    }


def _run_idempotence_scenario() -> dict[str, Any]:
    """Executes DocFrame.update() twice in succession and checks that the second pass changes nothing."""
    root = Path.cwd()
    _seed_presets_workspace(root)
    first_report = DocFrame.update(target=root)
    snapshot = {p.as_posix(): p.read_text(encoding="utf-8") for p in sorted(root.rglob("*.md"))}
    second_report = DocFrame.update(target=root)
    after = {p.as_posix(): p.read_text(encoding="utf-8") for p in sorted(root.rglob("*.md"))}
    return {
        "first_updated_non_empty": len(first_report.updated_files) > 0,
        "second_updated_files": list(second_report.updated_files),
        "snapshots_identical": snapshot == after,
    }


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: DIE DREI RAHMEN-PRESETS, SLOT-SCHUTZ & IDEMPOTENZ
# ======================================================================================================================
def test_ebt_cubie_doc_frame_1_updates_nav_and_preserves_slots() -> None:
    """Verifies that CUBIE_DOC_FRAME_1 updates nav/footer and protects title, intro, disclaimer, and body."""
    keys = (
        "preserves_title", "preserves_intro", "preserves_disclaimer", "preserves_body",
        "fixes_banner_and_alt", "fixes_footer_alt", "removes_error_alt", "uses_div_align_center",
    )
    EBT(
        target=_run_preset_update_scenario,
        arena=TempFS(),
        pre=WorldState(args=("frame_1",)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id="docframe_preset_1_slot_protection",
    ).run()


def test_ebt_cubie_doc_frame_2_syncs_provenance_and_preserves_extra_slots() -> None:
    """Verifies that CUBIE_DOC_FRAME_2 syncs env/model/effort attributes while keeping custom bullets and prompt."""
    keys = (
        "preserves_title", "syncs_env", "syncs_model", "syncs_effort",
        "preserves_custom_date", "preserves_custom_basis", "preserves_prompt", "preserves_body",
    )
    EBT(
        target=_run_preset_update_scenario,
        arena=TempFS(),
        pre=WorldState(args=("frame_2",)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id="docframe_preset_2_provenance_sync",
    ).run()


def test_ebt_cubie_doc_frame_3_updates_router_and_protects_manual_content() -> None:
    """Verifies that CUBIE_DOC_FRAME_3 rebuilds zone='router' tables without touching manual tables or prose."""
    keys = ("rebuilds_router_table", "removes_stale_row", "preserves_pre_text", "preserves_manual_table")
    EBT(
        target=_run_preset_update_scenario,
        arena=TempFS(),
        pre=WorldState(args=("frame_3",)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id="docframe_preset_3_router_update",
    ).run()


def test_ebt_docframe_update_idempotence() -> None:
    """Verifies that running DocFrame.update() a second time produces zero file modifications."""
    expected = {"first_updated_non_empty": True, "second_updated_files": [], "snapshots_identical": True}
    EBT(
        target=_run_idempotence_scenario,
        arena=TempFS(),
        pre=WorldState(),
        post=WorldState(returns=expected),
        custom_id="docframe_update_idempotence",
    ).run()
