<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Neon" effort="Medium" -->
# TGD-Protokoll: Behebung der 4 fehlschlagenden `DocFrame`-Tests (`test_docframe_presets_and_update.py`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** Medium
- **Analysedatum:** 24. November 2026, ~20:45 (CET)
- **Synthesebasis:** `GEMINI.md`, `tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py`, `src/qb_cubie/core/services/doc_frame/presets.py`, `src/qb_cubie/core/services/doc_frame/frame_blocks.py`, `src/qb_cubie/core/services/__init__.py`, `docs/GUIDE_TGD.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md`, `docs/dev/DEV-GUIDE_DocFrame-Conventions.md`, `docs/services/GUIDE_DocFrame.md`, `docs/dev/services/DEV-GUIDE_DocFrame.md`, `git log -p 40f43487`
- **Stand:** qb-cubie (`v0.1.0`, Branch `main`, Commit `f9332722`)
- **Git-Log:** `f9332722` ("Tried a fully autonomous TGD-Flow for BUG-003.")

---

```text
commit f9332722ca4c7cf9ff4745853a00eabb336debca (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Tue Nov 24 20:26:47 2026 +0100

    Tried a fully autonomous TGD-Flow for BUG-003.

Auftrag (GEMINI.md):
- Lösung der 4 fehlschlagenden Tests in tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py mittels voll-autonomen TGD-Flow.
- Dokumentation des Verlaufs in AGENT_REPORT-3.md.
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **`[BEFUND & URSACHE]` (Fallibilismus / SSOT-Verletzung im Testmodul `test_docframe_presets_and_update.py:15-26`):** Alle 4 Fehlschläge entstanden **nicht** durch einen Bug im Produktionscode (`src/`), sondern durch eine in Commit `40f43487` („Addressed BUG-007.“) entstandene Drift zwischen dem zentralen SSOT-Objekt `EPISTEMIC_NOTICE_TEXT` in `src/qb_cubie/core/services/doc_frame/presets.py:79-89` und einer im Testmodul hartkodierten Prosa-Kopie `_CANONICAL_EPISTEMIC_NOTICE`. Nach der bewussten Mutation des Hinweistexts in `presets.py` (Entfernung einer leeren Zitatzeile `>\n` vor `*Wenn du ...` sowie Ergänzung eines Leerzeichens in `... heißt`) schlugen alle 4 Tests fehl, die gegen die veraltete Kopie prüften.
2. **`[TGD-RÜCKWÄRTSTÜR / PHASE RED]` (`test_docframe_presets_and_update.py`):** Im Sinne von Karl Poppers Fallibilismus (`GUIDE_TGD.md`) wurde die fehlbare Test-Annahme repariert statt den Produktionscode zurückzudrehen: `_CANONICAL_EPISTEMIC_NOTICE` wurde durch den direkten Import von `EPISTEMIC_NOTICE_TEXT` aus `qb_cubie.core.services` (SSOT) ersetzt. Gleichzeitig wurden echte technische Invarianten geschärft (`isinstance(..., str)`, nicht-leer, enthält den Deduplizierungs-Marker `"erkenntnistheoretischen Grenzen"`, `EPISTEMIC_NOTICE.text == EPISTEMIC_NOTICE_TEXT`, Re-Export-Identität in `qb_cubie.core.services` sowie Upgrade-Nachweis einer veralteten Altbestands-Formulierung `_LEGACY_EPISTEMIC_NOTICE_VARIANT` auf den aktuellen SSOT-Text ohne Duplikate).
3. **`[NEBENBEFUND IM WORKING TREE]` (`tests/test_doc_frame.py::test_docs_frames`):** 8 Dateien unter `docs/misc/` meldeten `DOCFRAME-OUTDATED`, weil im Working Tree zuvor ein `DocFrame.update()` ohne `DOC_EXCLUDES` (`deep-research-report.md`, `CI-Data.md`) gelaufen war. Durch `DocFrame.update(excludes=DOC_EXCLUDES)` wurden alle 8 Dateien sauber synchronisiert.
4. **`[PHASE LIVING-DOCUMENTATION]` (`DEV-GUIDE_DocFrame-Conventions.md`, `GUIDE_DocFrame.md`, `DEV-GUIDE_DocFrame.md`, `AGENT_REPORT-3.md`):** Die fehlende Dokumentation zur zentralen Pflege von `EPISTEMIC_NOTICE_TEXT` (inkl. technischer Invariante `_EPISTEMIC_MARKER = "erkenntnistheoretischen Grenzen"` und Rollout via `DocFrame.update()`) wurde in allen drei DocFrame-Handbüchern ergänzt; zudem wurde die veraltete `DisclaimerSlot`-Beschreibung in `DEV-GUIDE_DocFrame.md` auf den BUG-007-Stand aktualisiert.

---

## 1. Stützrad 1 & 2: `ANALYSIS` & `HYPOTHESIS`

### 1.1 Analyse des Ist-Zustands ($Q_{\text{Ist}}$) vs. Soll-Spezifikation ($Q_{\text{Soll}}$)

* **Beobachtete Fehlschläge ($Q_{\text{Ist}}$):** `.venv/bin/python -m pytest -q tests/tests_core/tests_services/tests_doc_frame/` ergab `4 failed, 26 passed`:
  1. `test_ebt_cubie_doc_frame_1_updates_nav_and_preserves_slots`: `injects_epistemic_notice=False` (trotz `epistemic_notice_count=1`).
  2. `test_ebt_cubie_doc_frame_3_updates_router_and_protects_manual_content`: `injects_epistemic_notice=False`.
  3. `test_ebt_bug_007_epistemic_notice_preserved_injected_and_deduplicated`: `has_canonical_epistemic_notice=False` (trotz `epistemic_count_exactly_one=True`).
  4. `test_ebt_central_presets_module_serves_as_single_source_of_truth`: `has_canonical_notice_text=False`, `reexported_in_services=False`.
* **Forensischer Beleg (`git log -p -n 2 -- src/qb_cubie/core/services/doc_frame/presets.py`):**
  * Bereits in Commit `40f43487` („Addressed BUG-007.“) enthielt `presets.py:79-89` den mutierten Wortlaut ohne `>\n` vor `*Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …` und mit `... heißt das dann`.
  * `test_docframe_presets_and_update.py:15-26` kopierte hingegen den ursprünglichen Prosa-String in `_CANONICAL_EPISTEMIC_NOTICE` (mit `>\n` und `...heißt`) und brach damit genau das SSOT-Prinzip, das der Test `test_ebt_central_presets_module_serves_as_single_source_of_truth` eigentlich absichern sollte.
* **Spezifiziertes Verhalten ($Q_{\text{Soll}}$):**
  * `src/qb_cubie/core/services/doc_frame/presets.py::EPISTEMIC_NOTICE_TEXT` ist die **einzige** Wahrheitsquelle (SSOT) für den Wortlaut des Hinweises; redaktionelle Änderungen dort dürfen keine brüchigen String-Snapshots in `tests/` brechen.
  * Die Test-Suite prüft stattdessen die harten technischen Verträge:
    1. `EPISTEMIC_NOTICE_TEXT` ist ein nicht-leerer `str` und enthält den für `DisclaimerSlot` zwingenden Erkennungsmarker `"erkenntnistheoretischen Grenzen"` (`frame_blocks._EPISTEMIC_MARKER`).
    2. `EPISTEMIC_NOTICE` ist ein `StaticBlock`, dessen `.text` exakt `EPISTEMIC_NOTICE_TEXT` entspricht.
    3. `qb_cubie.core.services.EPISTEMIC_NOTICE_TEXT` re-exportiert identisch dasselbe Objekt (`is`).
    4. `DocFrame.update()` injiziert `EPISTEMIC_NOTICE_TEXT` exakt in `FRAME_1`/`FRAME_3`-Header, bewahrt eigene Disclaimer in 4-Segment-Headern und migriert Altbestands-Formulierungen mit `"erkenntnistheoretischen Grenzen"` in 3-Segment-Headern dedupliziert auf den aktuellen SSOT-Text.

### 1.2 Falsifikationshypothesen (`HYPOTHESIS`)

1. **Hypothese H1 (Test-Architekturfehler statt Core-Bug):** Der Produktionscode in `src/qb_cubie/core/services/doc_frame/` ist fehlerfrei (`Scope`: kein Eingriff in `src/` erforderlich). Die gezielte Umstellung von `test_docframe_presets_and_update.py` von der Prosa-Kopie auf SSOT + Strukturinvarianten behebt alle 4 Fehlschläge dauerhaft und schärft gleichzeitig den Migrations-Test für veraltete Altbestands-Hinweise.
2. **Hypothese H2 (Repo-Rahmen-Drift im Working Tree):** Ein Lauf von `DocFrame.update(excludes=DOC_EXCLUDES)` synchronisiert die 8 betroffenen Dateien unter `docs/misc/` und stellt `tests/test_doc_frame.py::test_docs_frames` wieder auf `PASSED`.
3. **Hypothese H3 (Living Documentation):** Die Ergänzung der Pflegeanleitung für `EPISTEMIC_NOTICE_TEXT` in den drei DocFrame-Guides schließt die vom Nutzer benannte Dokumentationslücke und besteht `DocEnsurance` (`test_doc_ensurance.py`) sowie `DocFrame` (`test_doc_frame.py`) fehlerfrei.

---

## 2. TGD-Durchführung (`GREEN_AUDIT` $\to$ `Phase Red` $\to$ `Phase Living-Documentation`)

### 2.1 Kontrollierter Rücksprung in `Phase Red` (`tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py`)

Da die Analyse belegte, dass das Zielverhalten im Produktionscode (`src/`) bereits $Q_{\text{Soll}}$ entspricht und der Fehler im Testmodul lag, wurde gemäß `GUIDE_TGD.md` die kontrollierte Reparatur in `tests/` durchgeführt:

* `_CANONICAL_EPISTEMIC_NOTICE` entfernt; stattdessen Import von `EPISTEMIC_NOTICE_TEXT` aus `qb_cubie.core.services` und Definition von `_EPISTEMIC_ANCHOR_MARKER = "erkenntnistheoretischen Grenzen"`.
* `_FRAME_1_LEGACY_3_SEGMENT_EPISTEMIC_DOC` nutzt nun bewusst eine abweichende Altbestands-Formulierung (`_LEGACY_EPISTEMIC_NOTICE_VARIANT`), die den Marker trägt — so wird aktiv geprüft, dass `DocFrame.update()` veraltete Formulierungen dedupliziert und auf das aktuelle SSOT-Preset aktualisiert.
* `_inspect_central_presets_module()` prüft nun Struktur- und Identitätsinvarianten (`isinstance`, `strip()`, `_EPISTEMIC_ANCHOR_MARKER in notice_text`, `notice_block.text == notice_text`, `services_mod.EPISTEMIC_NOTICE_TEXT is notice_text`) statt eines fragilen Prosa-Literals.
* **Kein Produktionscode unter `src/` verändert.**

### 2.2 `Phase Living-Documentation`

* **[`docs/dev/DEV-GUIDE_DocFrame-Conventions.md`](./docs/dev/DEV-GUIDE_DocFrame-Conventions.md):** Abschnitt `CUBIE_DOC_FRAME_1` um den zentralen Pflegehinweis für `EPISTEMIC_NOTICE_TEXT` (`presets.py`), die Marker-Invariante und den Rollout-Befehl ergänzt.
* **[`docs/services/GUIDE_DocFrame.md`](./docs/services/GUIDE_DocFrame.md):** In Abschnitt 4.1 einen `[!NOTE]`-Block zur zentralen Pflege von `EPISTEMIC_NOTICE_TEXT` (SSOT) ergänzt.
* **[`docs/dev/services/DEV-GUIDE_DocFrame.md`](./docs/dev/services/DEV-GUIDE_DocFrame.md):** Veraltete `DisclaimerSlot`-Beschreibung (`segments[1]`) auf das tatsächliche BUG-007-Verhalten (`segments[1:-1]`, Filterung via `_EPISTEMIC_MARKER`, `_dedupe_dividers`) sowie den Pflegehinweis aktualisiert.
* **Rahmen-Synchronisation:** `DocFrame.update(excludes=DOC_EXCLUDES)` synchronisierte die 8 abweichenden Dateien unter `docs/misc/` sowie `AGENT_REPORT-3.md`.

---

## 3. Verifikationsprotokoll

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Baseline (`tests_doc_frame/`) | `.venv/bin/python -m pytest -q tests/tests_core/tests_services/tests_doc_frame/` | `4 failed, 26 passed` |
| Baseline (Docs, Meta, Styleguide, Lint) | `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py tests/tests_meta/ tests/test_styleguide.py tests/test_lint.py` | `1 failed, 97 passed, 1 skipped, 9 deselected` (`test_docs_frames`: 8 Dateien unter `docs/misc/` veraltet) |
| DocFrame-Sync & Verifikation (`tests_doc_frame/`, Docs, Meta, Styleguide, Lint) | `.venv/bin/python -c "from qb_cubie.core.services import DocFrame; from tests.test_doc_ensurance import DOC_EXCLUDES; DocFrame.update(excludes=DOC_EXCLUDES)" && .venv/bin/python -m pytest -q tests/tests_core/tests_services/tests_doc_frame/ tests/test_doc_frame.py tests/test_doc_ensurance.py tests/tests_meta/ tests/test_styleguide.py tests/test_lint.py` | `128 passed, 1 skipped, 9 deselected in 43.61s` |
| Finale DocFrame- & DocEnsurance-Prüfung (inkl. `AGENT_REPORT-3.md`) | `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` | `2 passed` |

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./docs/GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./docs/README.md)  
[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./docs/dev/README.md)  
[↦ | Core-Internals | ↤](./docs/dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
