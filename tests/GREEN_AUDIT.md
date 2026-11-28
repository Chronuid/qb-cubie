# GREEN_AUDIT: Fixture-Defekt in `_seed_preset_workspace` (`CUBIE_DOC_FRAME_3`)

- **Auslöser:** `PHASE_GREEN` für `RUN-3` (`docframe-rules-srp`)
- **Betroffener Test:** `tests/tests_core/tests_service_core/test_rules_and_docframe.py::test_ebt_docframe_foot_links_warning_on_frame_2_and_3[CUBIE_DOC_FRAME_3-README.md]`

## 1. `AUDIT-REPRO` (Unabhängige Reproduktion)

Kommando:
```bash
.venv/bin/python -m pytest -q tests/tests_core/tests_service_core/test_rules_and_docframe.py -k "CUBIE_DOC_FRAME_3-README.md"
```
Ergebnis:
- `1 failed` (`DOCFRAME-OUTDATED` auf `README.md` zusätzlich zur erwarteten `DOCFRAME-FOOT-LINKS`-Warnung).
- Ursache: `_seed_preset_workspace` schreibt für `CUBIE_DOC_FRAME_3` eine synthetische `docs/idx/README.md`, deren `zone="head"` weder `EPISTEMIC_NOTICE_TEXT` noch `HEADER_QUICK_NAV` enthält (Verstoß gegen Fixture-Hygiene F1). Dadurch meldet `DocFrameOutdated` die `head`-Zone als veraltet.

## 2. `AUDIT-VERDICT` & `AUDIT-FIX`

- **Urteil:** `CONFIRMED` (reiner Fixture-Defekt; **0 Assertion-Edits** am Testvertrag).
- **Minimal-Invasiver Fix:** In `_seed_preset_workspace` wird `docs/idx/README.md` zunächst mit `DocFrame.update(target=root, excludes=("experiments",))` synchronisiert und anschließend ausschließlich `zone="foot"` auf `foot_inner` gesetzt.

## 3. `AUDIT-CLOSE`

- **Status:** `Status: RESOLVED`
- **Schreibgrenze:** Ausschließlich `tests/tests_core/tests_service_core/test_rules_and_docframe.py` (Fixture) und `tests/GREEN_AUDIT.md` geändert; `0` Änderungen an Assertions, `src/` oder `docs/`.
