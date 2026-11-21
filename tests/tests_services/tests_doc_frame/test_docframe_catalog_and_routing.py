"""**Tries to** verify Pass 1 catalog extraction and Pass 2 relative path routing in DocFrame."""

from pathlib import Path
from typing import Any

from qb_cubie import EBT, TempFS, WorldState
from qb_cubie.services import DocFrame

_ASSET_BANNERS = ("cubie-banner.png", "cubie-logo-written.png", "cubie-small.png")

_ROOT_README = (
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-banner.png" -->\n'
    '<div align="center">\n\n# qb-cubie Root\n\n![Cubie](./docs/.assets/cubie-banner.png)\n\n'
    "Kurze Beschreibung des Hauptprojekts für den Katalog.\n\n---\n\n---\n\n</div>\n"
    "<!-- /qb:frame -->\n\nRumpf der Wurzel.\n\n"
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n'
)


def _make_guide(
    title: str,
    summary: str = "Standard-Zusammenfassung unterhalb des Banners.",
    attrs: str = 'banner="cubie-logo-written.png"',
    frame_id: str = "CUBIE_DOC_FRAME_1",
) -> str:
    """Builds a synthetic Markdown document with head and foot frame markers."""
    para = f"\n\n{summary}" if summary else ""
    attr_str = f" {attrs.strip()}" if attrs.strip() else ""
    return (
        f'<!-- qb:frame id="{frame_id}" zone="head"{attr_str} -->\n'
        f'<div align="center">\n\n# {title}\n\n![Cubie](.assets/cubie-logo-written.png){para}\n\n'
        "---\n\n---\n\n</div>\n<!-- /qb:frame -->\n\nBody text.\n\n"
        f'<!-- qb:frame id="{frame_id}" zone="foot" -->\n<!-- /qb:frame -->\n'
    )


def _make_index_readme(mode: str = "table") -> str:
    """Builds a CUBIE_DOC_FRAME_3 index document with head, router, and foot zones."""
    return (
        '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" banner="cubie-logo-written.png" -->\n'
        '<div align="center">\n\n# Bereichs-Index\n\n![Cubie](../.assets/cubie-logo-written.png)\n\n'
        "---\n\n---\n\n</div>\n<!-- /qb:frame -->\n\nVorwort.\n\n"
        f'<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="{mode}" dir="." recursive="false" -->\n'
        "<!-- /qb:frame -->\n\nNachwort.\n\n"
        '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->\n<!-- /qb:frame -->\n'
    )


def _seed_base_tree(root: Path) -> None:
    """Creates a synthetic multi-depth documentation tree with assets in TempFS."""
    (root / "pyproject.toml").write_text("[project]\nname = 'cubie-test'\n", encoding="utf-8")
    for folder in ("docs/.assets", "docs/services", "docs/dev/services", "docs/misc", ".venv"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    for asset in _ASSET_BANNERS:
        (root / "docs" / ".assets" / asset).write_bytes(b"PNG")
    (root / "README.md").write_text(_ROOT_README, encoding="utf-8")
    (root / "docs" / "GUIDE_Quality-Assurance.md").write_text(_make_guide("QA Handbuch"), encoding="utf-8")
    (root / "docs" / "services" / "GUIDE_DocEnsurance.md").write_text(_make_guide("DocEnsurance"), encoding="utf-8")


def _inspect_catalog_scenario(mode: str) -> dict[str, Any]:
    """Seeds a custom scenario in TempFS and projects the Pass 1 DocumentCatalog to a dict."""
    root = Path.cwd()
    _seed_base_tree(root)
    _apply_catalog_variation(root, mode)
    catalog = DocFrame.scan_catalog(target=root, excludes=("experiments",))
    if mode == "zero_config":
        meta = catalog.by_path("docs/GUIDE_Quality-Assurance.md")
        return {"title": meta.title, "label": meta.label, "summary": meta.summary, "routable": meta.routable}
    if mode == "no_summary":
        meta = catalog.by_path("docs/GUIDE_Bare.md")
        return {"title": meta.title, "summary": meta.summary, "routable": meta.routable}
    entries = catalog.select("docs/misc", glob="*.md", exclude=())
    return {"ordered_paths": [e.path for e in entries], "labels": [e.label for e in entries]}


def _apply_catalog_variation(root: Path, mode: str) -> None:
    """Populates mode-specific Markdown files for catalog extraction and sorting checks."""
    if mode == "no_summary":
        (root / "docs/GUIDE_Bare.md").write_text(_make_guide("Ohne Absatz", summary=""), encoding="utf-8")
    elif mode == "explicit_order":
        (root / "docs/misc/Z_Last.md").write_text(_make_guide("Z", attrs='label="Zuerst" order="10"'), encoding="utf-8")
        (root / "docs/misc/A_First.md").write_text(_make_guide("A", attrs='label="Danach" order="20"'), encoding="utf-8")
        (root / "docs/misc/README.md").write_text(_make_guide("Misc Index"), encoding="utf-8")
    elif mode == "default_sort":
        (root / "docs/misc/Zebra.md").write_text(_make_guide("Zebra"), encoding="utf-8")
        (root / "docs/misc/Alpha.md").write_text(_make_guide("Alpha"), encoding="utf-8")
        (root / "docs/misc/README.md").write_text(_make_guide("Misc Readme"), encoding="utf-8")


def _run_routing_scenario(mode: str) -> dict[str, Any]:
    """Seeds a routing scenario, executes DocFrame.update(), and extracts routed link targets."""
    root = Path.cwd()
    _seed_base_tree(root)
    _seed_routing_files(root)
    DocFrame.update(target=root)
    return _project_routing_result(root, mode)


def _seed_routing_files(root: Path) -> None:
    """Seeds dev guides, misc essays, an unroutable scratchpad, and a dynamic new guide."""
    (root / "docs/GUIDE_New.md").write_text(_make_guide("Neuer Guide"), encoding="utf-8")
    (root / "docs/GUIDE_Scratch.md").write_text(_make_guide("Scratchpad", attrs='routable="false"'), encoding="utf-8")
    (root / "docs/dev/README.md").write_text(_make_index_readme(mode="table"), encoding="utf-8")
    (root / "docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md").write_text(_make_guide("Dev EBT"), encoding="utf-8")
    (root / "docs/dev/DEV-GUIDE_2-5_Linter.md").write_text(_make_guide("Dev Linter"), encoding="utf-8")
    (root / "docs/dev/services/DEV-GUIDE_DocFrame.md").write_text(_make_guide("Dev DocFrame"), encoding="utf-8")
    (root / "docs/misc/README.md").write_text(_make_index_readme(mode="table"), encoding="utf-8")
    (root / "docs/misc/Essay_A.md").write_text(_make_guide("Essay Alpha", "Inhalt Alpha."), encoding="utf-8")
    (root / "docs/misc/Essay_B.md").write_text(_make_guide("Essay Beta", "Inhalt Beta."), encoding="utf-8")


def _project_routing_result(root: Path, mode: str) -> dict[str, Any]:
    """Dispatches routing projection by scenario mode."""
    dispatch = {
        "depth_links": _project_depth_links,
        "dynamic_and_routable": _project_dynamic_and_routable,
        "sibling_top_level": _project_sibling_top_level,
        "sibling_subfolder": _project_sibling_subfolder,
        "catalog_table": _project_catalog_table,
    }
    return dispatch[mode](root)


def _project_depth_links(root: Path) -> dict[str, Any]:
    """Projects relative link depths from root and nested developer documentation."""
    root_txt = (root / "README.md").read_text(encoding="utf-8")
    deep_txt = (root / "docs/dev/services/DEV-GUIDE_DocFrame.md").read_text(encoding="utf-8")
    return {
        "root_has_dot_docs": "./docs/GUIDE_Quality-Assurance.md" in root_txt,
        "deep_has_three_up": "../../../README.md" in deep_txt,
        "deep_has_two_up_asset": "../../.assets/cubie-small.png" in deep_txt,
    }


def _project_dynamic_and_routable(root: Path) -> dict[str, Any]:
    """Projects dynamic FolderRouter discovery and routable='false' visibility flags."""
    qa_txt = (root / "docs/GUIDE_Quality-Assurance.md").read_text(encoding="utf-8")
    scratch_txt = (root / "docs/GUIDE_Scratch.md").read_text(encoding="utf-8")
    return {
        "new_guide_in_footer": "[↦ | Neuer Guide | ↤](./GUIDE_New.md)" in qa_txt,
        "scratch_hidden_in_others": "GUIDE_Scratch.md" not in qa_txt,
        "scratch_own_footer_updated": "[↦ | QA Handbuch | ↤](./GUIDE_Quality-Assurance.md)" in scratch_txt,
    }


def _project_sibling_top_level(root: Path) -> dict[str, Any]:
    """Projects top-level SiblingRouter hub links and hidden subfolder siblings."""
    qa_txt = (root / "docs/GUIDE_Quality-Assurance.md").read_text(encoding="utf-8")
    return {
        "has_dev_hub": "./dev/README.md" in qa_txt,
        "has_misc_hub": "./misc/README.md" in qa_txt,
        "hides_dev_sibling": "DEV-GUIDE_2-5_Linter.md" not in qa_txt,
        "hides_misc_sibling": "Essay_A.md" not in qa_txt,
    }


def _project_sibling_subfolder(root: Path) -> dict[str, Any]:
    """Projects expanded sibling routes inside a subfolder document."""
    dev_txt = (root / "docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md").read_text(encoding="utf-8")
    return {
        "expands_dev_linter": "[↦ | Dev Linter | ↤](./DEV-GUIDE_2-5_Linter.md)" in dev_txt,
        "expands_dev_ebt": "[↦ | Dev EBT | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)" in dev_txt,
    }


def _project_catalog_table(root: Path) -> dict[str, Any]:
    """Projects table-mode CatalogRouter output from docs/misc/README.md."""
    misc_txt = (root / "docs/misc/README.md").read_text(encoding="utf-8")
    return {
        "has_table_header": "| Dokument | Inhalt und Geltung |" in misc_txt,
        "has_essay_a_row": "| [Essay Alpha](./Essay_A.md) | Inhalt Alpha. |" in misc_txt,
        "has_essay_b_row": "| [Essay Beta](./Essay_B.md) | Inhalt Beta. |" in misc_txt,
        "excludes_self_readme": "[Bereichs-Index]" not in misc_txt,
    }


def _run_catalog_links_mode() -> dict[str, Any]:
    """Seeds a CUBIE_DOC_FRAME_3 index in mode='links' and verifies generated route links."""
    root = Path.cwd()
    _seed_base_tree(root)
    (root / "docs/misc/README.md").write_text(_make_index_readme(mode="links"), encoding="utf-8")
    (root / "docs/misc/Essay_A.md").write_text(_make_guide("Essay Alpha", "Inhalt Alpha."), encoding="utf-8")
    DocFrame.update(target=root)
    misc_txt = (root / "docs/misc/README.md").read_text(encoding="utf-8")
    return {
        "has_link_item": "[↦ | Essay Alpha | ↤](./Essay_A.md)" in misc_txt,
        "preserves_surrounding": "Vorwort." in misc_txt and "Nachwort." in misc_txt,
    }


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: PASS 1 – ZERO-CONFIG-EXTRAKTION & DOCUMENT-CATALOG
# ======================================================================================================================
def test_ebt_catalog_zero_config_extraction() -> None:
    """Verifies that Pass 1 automatically extracts H1 title, label, and first summary paragraph."""
    summary = "Standard-Zusammenfassung unterhalb des Banners."
    expected = {"title": "QA Handbuch", "label": "QA Handbuch", "summary": summary, "routable": True}
    EBT(
        target=_inspect_catalog_scenario,
        arena=TempFS(),
        pre=WorldState(args=("zero_config",)),
        post=WorldState(returns=expected),
        custom_id="docframe_catalog_zero_config",
    ).run()


def test_ebt_catalog_handles_missing_summary_paragraph() -> None:
    """Verifies that a document without a paragraph below the banner receives an empty summary."""
    EBT(
        target=_inspect_catalog_scenario,
        arena=TempFS(),
        pre=WorldState(args=("no_summary",)),
        post=WorldState(returns={"title": "Ohne Absatz", "summary": "", "routable": True}),
        custom_id="docframe_catalog_missing_summary",
    ).run()


def test_ebt_catalog_explicit_label_and_order_override() -> None:
    """Verifies that label and order marker attributes override H1 titles and alphabetical sorting."""
    expected = {
        "ordered_paths": ["docs/misc/README.md", "docs/misc/Z_Last.md", "docs/misc/A_First.md"],
        "labels": ["Misc Index", "Zuerst", "Danach"],
    }
    EBT(
        target=_inspect_catalog_scenario,
        arena=TempFS(),
        pre=WorldState(args=("explicit_order",)),
        post=WorldState(returns=expected),
        custom_id="docframe_catalog_explicit_order_and_label",
    ).run()


def test_ebt_catalog_default_sorting_puts_readme_first() -> None:
    """Verifies deterministic alphabetical sorting with README.md always on position 1."""
    expected = {
        "ordered_paths": ["docs/misc/README.md", "docs/misc/Alpha.md", "docs/misc/Zebra.md"],
        "labels": ["Misc Readme", "Alpha", "Zebra"],
    }
    EBT(
        target=_inspect_catalog_scenario,
        arena=TempFS(),
        pre=WorldState(args=("default_sort",)),
        post=WorldState(returns=expected),
        custom_id="docframe_catalog_default_sorting",
    ).run()


# ======================================================================================================================
# 2. ÄQUIVALENZKLASSE: PASS 2 – RELATIVES PFAD-ROUTING & DYNAMISCHE ROUTER
# ======================================================================================================================
def test_ebt_relative_path_depth_resolution() -> None:
    """Verifies exact ./, ../, ../../, and ../../../ link and banner resolution across directory depths."""
    keys = ("root_has_dot_docs", "deep_has_three_up", "deep_has_two_up_asset")
    EBT(
        target=_run_routing_scenario,
        arena=TempFS(),
        pre=WorldState(args=("depth_links",)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id="docframe_routing_depth_resolution",
    ).run()


def test_ebt_folder_router_dynamic_discovery_and_routable_false() -> None:
    """Verifies that FolderRouter discovers new guides automatically while hiding routable='false' docs."""
    keys = ("new_guide_in_footer", "scratch_hidden_in_others", "scratch_own_footer_updated")
    EBT(
        target=_run_routing_scenario,
        arena=TempFS(),
        pre=WorldState(args=("dynamic_and_routable",)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id="docframe_routing_dynamic_and_routable_false",
    ).run()


def test_ebt_sibling_router_top_level_shows_only_hubs() -> None:
    """Verifies that top-level guides in docs/ only show subfolder hubs in their footer."""
    keys = ("has_dev_hub", "has_misc_hub", "hides_dev_sibling", "hides_misc_sibling")
    EBT(
        target=_run_routing_scenario,
        arena=TempFS(),
        pre=WorldState(args=("sibling_top_level",)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id="docframe_sibling_router_top_level",
    ).run()


def test_ebt_sibling_router_subfolder_expands_siblings() -> None:
    """Verifies that documents inside a subfolder automatically expand all sibling documents in the footer."""
    EBT(
        target=_run_routing_scenario,
        arena=TempFS(),
        pre=WorldState(args=("sibling_subfolder",)),
        post=WorldState(returns={"expands_dev_linter": True, "expands_dev_ebt": True}),
        custom_id="docframe_sibling_router_subfolder",
    ).run()


def test_ebt_catalog_router_table_mode() -> None:
    """Verifies that CatalogRouter builds Markdown index tables with summaries in zone='router'."""
    keys = ("has_table_header", "has_essay_a_row", "has_essay_b_row", "excludes_self_readme")
    EBT(
        target=_run_routing_scenario,
        arena=TempFS(),
        pre=WorldState(args=("catalog_table",)),
        post=WorldState(returns=dict.fromkeys(keys, True)),
        custom_id="docframe_catalog_router_table_mode",
    ).run()


def test_ebt_catalog_router_links_mode() -> None:
    """Verifies that CatalogRouter builds route link lists in mode='links' while preserving body text."""
    EBT(
        target=_run_catalog_links_mode,
        arena=TempFS(),
        pre=WorldState(),
        post=WorldState(returns={"has_link_item": True, "preserves_surrounding": True}),
        custom_id="docframe_catalog_router_links_mode",
    ).run()
