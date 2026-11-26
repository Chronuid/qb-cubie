# GREEN_AUDIT — Zyklus 2, Phase Green (`qb_cubie.core.service_core`)

Gemäß [`docs/GUIDE_TGD.md`](../docs/GUIDE_TGD.md) (Schritt 5: *Unantastbarkeit der Tests & Rückwärtstür `GREEN_AUDIT`*) wurde während der Phase Green **keine Datei unter `tests/**/*.py` verändert**. Alle 49 von 51 ursprünglich roten Cycle-2-Tests, alle Bestands-, Linter- (`ruff`, `pylint`, `mypy`), Styleguide-, Living-Documentation- (`DocEnsurance`, `DocFrame`) und Architektur-Gate-Tests laufen nach der Implementierung in `src/` grün.

Die verbleibenden **2 Fehlschläge** gehen auf einen reproduzierbaren Widerspruch in der synthetischen Test-Fixture `_seed_docframe_workspace` aus der Phase Red zurück.

---

## Befund 1: Unvollständige synthetische Workspace-Fixture in `test_cli_spec_and_lazy_cli.py`

### Betroffene Stellen (`tests/` — in Phase Green eingefroren)
- **Fixture:** `tests/tests_core/tests_service_core/test_cli_spec_and_lazy_cli.py:32-47` (`_seed_docframe_workspace`)
- **Fehlschlagender Test 1:** `tests/tests_core/tests_service_core/test_cli_spec_and_lazy_cli.py:281-337` (`test_ebt_cli_docframe_check_passes_and_fails_with_distinct_exit_codes`)
- **Fehlschlagender Test 2:** `tests/tests_core/tests_service_core/test_cli_spec_and_lazy_cli.py:509-533` (`test_ebt_cli_docframe_does_not_import_sibling_services`)

### Ursache & Reproduktionsbeleg

`_seed_docframe_workspace(root, synced=True)` legt ausschließlich **eine einzige Markdown-Datei** (`README.md`) mit dem Preset `CUBIE_DOC_FRAME_1` an (`test_cli_spec_and_lazy_cli.py:40-46`):

```python
(root / "README.md").write_text(
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Demo\n<!-- /qb:frame -->\n\n'
    'Body text.\n\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
    encoding="utf-8",
)
if synced:
    DocFrame.update(target=root)
```

Das Preset `CUBIE_DOC_FRAME_1` (`src/qb_cubie/core/services/doc_frame/presets.py:82-88, 123-142`) enthält über `STD_HEAD_BLOCKS` fest den Baustein `HEADER_QUICK_NAV` (`CompactNav`), der immer folgende drei Links rendert:

```markdown
[README](./README.md) • [QA-Handbuch](./docs/GUIDE_Quality-Assurance.md) • [DocEnsurance](./docs/services/GUIDE_DocEnsurance.md)  
```

Beim anschließenden `qb-cubie docframe check <clean_root>` prüft `DocFrameBrokenRoute` (`src/qb_cubie/core/services/doc_frame/doc_frame_rules.py:71-86`, vertraglich abgesichert durch `tests/tests_core/tests_services/tests_doc_frame/test_docframe_rules_and_guards.py:215-219`) korrekt alle gerenderten Links gegen `WorkspaceView` und meldet deterministisch:

```text
Diagnostic(
  file_path='.../README.md',
  rule_id='DOCFRAME-BROKEN-ROUTE',
  line=1,
  message="Broken route or asset reference in frame (head): './docs/GUIDE_Quality-Assurance.md' not found.",
  severity='error',
  context=None,
)
```

Deshalb liefert `docframe check` auf `clean_root` korrekt `passed=False` und `exit_code=1` (statt der vom Test erwarteten `passed=True` und `exit_code=0`).

### Vergleich mit der korrekten Zyklus-1-Fixture

In Zyklus 1 (`tests/tests_core/tests_service_core/test_rules_and_docframe.py:123-135`, `_seed_synced_docframe_workspace`) wurden genau diese beiden Ziel-Dokumente von `HEADER_QUICK_NAV` explizit mit angelegt:

```python
(root / "README.md").write_text(_framed_doc("Root", "cubie-banner.png"), encoding="utf-8")
(root / "docs" / "GUIDE_Quality-Assurance.md").write_text(_framed_doc("QA"), encoding="utf-8")
(root / "docs" / "services" / "GUIDE_DocEnsurance.md").write_text(_framed_doc("Service"), encoding="utf-8")
```

### Klärungs- & Reparaturvorschlag für den Rücksprung in Phase Red

Zwei saubere Optionen stehen zur Auswahl (ohne bestehende Produktions-Verträge in `CompactNav` oder `DocFrameBrokenRoute` aufzuweichen):

1. **Option A (Empfohlen — konsistent mit Zyklus 1):** `_seed_docframe_workspace` legt wie `_seed_synced_docframe_workspace` zusätzlich `docs/GUIDE_Quality-Assurance.md` und `docs/services/GUIDE_DocEnsurance.md` mit `CUBIE_DOC_FRAME_1` an; entsprechend werden in `test_ebt_cli_docframe_check_passes_and_fails_with_distinct_exit_codes` `ok_files_checked: 3` (und ggf. `fail_rule_ids` als eindeutige Menge bzw. `["DOCFRAME-OUTDATED", ...]`) sowie in `test_ebt_cli_docframe_update_json_uses_schema_v1_and_keeps_compat_keys` `changed_files` / `updated_files` (3 Dateien) und `catalog_entries: 3` angepasst.
2. **Option B (Minimal-Fixture mit 1 Datei):** `_seed_docframe_workspace` nutzt für `README.md` das Preset `CUBIE_DOC_FRAME_2` mit vollständigen Provenance-Attributen (`env="CLI" model="Test" effort="Low"`), da `CUBIE_DOC_FRAME_2` kein `HEADER_QUICK_NAV` enthält und `STD_FOOTER_BLOCKS` nur tatsächlich vorhandene Routen sowie `docs/.assets/cubie-small.png` referenziert. Dann bleiben `ok_files_checked: 1`, `changed_files: ["README.md"]` und `catalog_entries: 1` unverändert bei 1 Datei.
