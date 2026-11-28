# RUN-3: SRP-Regel-Interfaces & konfigurierbare `foot`-Zone (`CUBIE_DOC_FRAME_2` / `3`) — Voll-autonomer TGD-Durchlauf

- **Modus:** Voll-autonomer TGD-Durchlauf (`ANALYSIS` $\to$ `HYPOTHESIS` $\to$ `PHASE_RED` $\to$ `PHASE_GREEN` $\to$ `LIVING_DOCS`, mit optionaler Rückwärtstür `GREEN_AUDIT`)
- **Knoten-Handbücher:** [TGD-Baukasten (docs/tgd/README.md)](../../tgd/README.md) · [ANALYSIS](../../tgd/NODE_ANALYSIS.md) · [HYPOTHESIS](../../tgd/NODE_HYPOTHESIS.md) · [PHASE_RED](../../tgd/NODE_PHASE_RED.md) · [PHASE_GREEN](../../tgd/NODE_PHASE_GREEN.md) · [LIVING_DOCS](../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil:** [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
- **Run / Zyklus:** `docframe-rules-srp` *(Ablage: `docs/misc/runs/docframe-rules-srp/RUN-3.md`)*
- **Ausgangs-Commit (`HEAD`):** `348b8ed0` *("Reactivated the 12-Line-Gate for function-bodies.")*
- **Ziel-Artefakte:** `src/qb_cubie/core/services/doc_frame/` (und ggf. `doc_ensurance/` für Interface-Parität), `tests/test_doc_frame.py`, `tests/test_doc_ensurance.py`, zugehörige Core-/Service-Tests unter `tests/` sowie betroffene Doku-Guides unter `docs/`
- **Herkunft:** `Mensch (Huiuiuii) + Gemini-App (Modell: Hydrogen, Reasoning-Effort: High)`

## 1. Ziel (Scope dieses Durchlaufs)
Gestalte die Regel-Konfiguration für `DocFrame` (im Einklang mit `DocEnsurance`) nach dem **Single Responsibility Principle (SRP)** und klaren, expliziten Objekt-Interfaces neu (*„Jedes Objekt im Modul ist ein Interface“*), sodass Regeln granular und pro Rahmen-Preset direkt in `tests/test_doc_frame.py` und `tests/test_doc_ensurance.py` konfiguriert werden können. Konfiguriere darauf aufbauend die Prüfung der Link-Liste in der `foot`-Zone so, dass sie für **`CUBIE_DOC_FRAME_2`** (Berichte/optionale Runs) und **`CUBIE_DOC_FRAME_3`** (Index-Dokumente) abgeschwächt wird (**Warnung statt hartem Error** bei fehlender Link-Liste, während bestehende Links weiterhin als Standard-Markdown-Links validiert werden) und für **`CUBIE_DOC_FRAME_1`** (Produkt-Handbücher) strikt (`error`) bleibt.

## 2. Kontext-Delta (seit letztem Knoten)
- In `RUN-2` (`348b8ed0`) wurde das 12-Zeilen-Limit für Funktionskörper (`tests/test_styleguide.py::test_function_size`, `FUNCTION_LIMIT = 12`) wieder scharfgeschaltet (`1977 passed`, `13 passed` in `test_styleguide.py`, `0` MyPy-Fehler). Alle neuen oder geänderten Funktionen in `src/qb_cubie/` müssen das 12-Zeilen-Limit in `PHASE_GREEN` daher unmittelbar einhalten.
- Aktuell übergibt `tests/test_doc_frame.py` eine einzige, pauschale Regel-Sammlung (`rules=CUBIE_DOCFRAME_RULES`) global über alle drei Presets `(CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3)`. Eine differenzierte Konfiguration pro Frame-Typ oder Regel-Instanz (z. B. `severity="warning"` vs. `"error"` wie bei `CUBIE_DOC_RULES` in `DocEnsurance`) fehlt noch.
- In `DEV-GUIDE_TGD-Workflow.md` (§3 & §4) sind Standard-Markdown-Links in der `foot`-Zone sowie die konfigurierbare Abschwächung für `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` bereits als nächste Ausbaustufe festgehalten.

## 3. Freigabe, Leitlinien & Phasen-Fahrplan (`Consent-by-Exception`)
- **Basis:** `EMPFEHLUNGEN: ALLE` (sämtliche Invarianten, Schreibgrenzen und Gate-Regeln aus `docs/tgd/README.md`, `docs/tgd/NODE_*.md`, `docs/dev/DEV-GUIDE_TGD-Workflow.md` und `docs/dev/Style-Guide.md` gelten verbindlich). Im voll-autonomen Modus bestätigt die Orchestrierung die in `HYPOTHESIS` ausgearbeiteten Standard-Empfehlungen automatisch, sofern alle hier genannten Leitplanken eingehalten sind.
- **Verbindliche Leitplanken für Architektur & Interfaces:**
  1. **Jedes Objekt im Modul ist ein öffentliches Interface (SRP):**
     - Trenne klar zwischen **Rahmen-/Zone-Spezifikation** (`DocFrame`-Presets/Blöcke), **atomaren Einzelregeln** (eine klare Prüfverantwortung pro Regel-Klasse/Objekt, explizites `severity`-Verhalten `"error"` vs. `"warning"`, saubere Repräsentation) und **Regel-Bindung / Profilen** (Zuordnung konkreter Regel-Sets zu einzelnen Presets wie `CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2`, `CUBIE_DOC_FRAME_3`).
     - Vermeide aufgeblähte „Gott-Klassen“, unstrukturierte `dict`-Konfigurationen oder boolesche Flag-Friedhöfe. Exportiere die öffentlichen Regel- und Konfigurations-Interfaces sauber über die jeweiligen `__init__.py`-Schnittstellen (`qb_cubie.core.services` / `doc_frame` / `doc_ensurance`).
     - Prüfe `DocEnsurance` (`CUBIE_DOC_RULES` / `tests/test_doc_ensurance.py`) auf Interface-Symmetrie zu `DocFrame`, damit beide Services in den Repo-Testmodulen konsistent, selbsterklärend und ergonomisch konfiguriert werden können.
  2. **Semantik der `foot`-Zone & Link-Prüfung:**
     - **`CUBIE_DOC_FRAME_1`:** Fehlende oder unvollständige Link-Liste in der `foot`-Zone bleibt ein harter Fehler (`error`).
     - **`CUBIE_DOC_FRAME_2` & `CUBIE_DOC_FRAME_3`:** Fehlende Link-Liste in der `foot`-Zone wird auf **`warning`** abgeschwächt (kein Abbruch von `DocFrame.check()` / `pytest`, aber sichtbare Warnung). Sind hingegen Links in der `foot`-Zone vorhanden, werden defekte oder ungültige Links weiterhin gemeldet.
     - **Link-Syntax:** Ausschließlich Standard-Markdown-Links (keine plattformspezifischen `@`-Referenzen in `DocFrame`).
  3. **Sauberer TGD-Phasen-Fahrplan:**
     - **Schritt 1 — `ANALYSIS` (nur Analysebericht):** Vermesse `src/qb_cubie/core/services/doc_frame/`, `src/qb_cubie/core/services/doc_ensurance/`, `tests/test_doc_frame.py`, `tests/test_doc_ensurance.py` und `tests/tests_core/tests_service_core/test_rules_and_docframe.py` auf aktuelle Regel-Kopplungen, `severity`-Mechanismen und bestehende Aufrufer.
     - **Schritt 2 — `HYPOTHESIS` (nur Hypothesenbericht):** Vergleiche mindestens drei SRP-Interface-Designs (A vs. B vs. C), prüfe bestehende Aufrufer auf Abwärtskompatibilität bzw. Migrationsbedarf, führe die Vier-Säulen-Meta-QA inkl. Mutanten-Matrix (`M1..Mn`, z. B. Mutant *„`CUBIE_DOC_FRAME_1` verliert versehentlich den `error`-Schutz“* und Mutant *„`CUBIE_DOC_FRAME_2`/`3` wirft weiterhin `error` ohne `foot`-Links“*) durch und lege Standard-Empfehlungen fest.
     - **Schritt 3 — `PHASE_RED` (nur `tests/`):**
       - Implementiere die neuen Vertrags-, `STATE-GUARD`- (`type(x) is bool`, ungültige `severity`-, leere/inkonsistente Regel-Bindungen) und `foot`-Zone-Warnungstests in den Unit-/Service-Tests **sowie** die gewünschte Ziel-Konfiguration in `tests/test_doc_frame.py` und `tests/test_doc_ensurance.py`.
       - Beachte strikt die Fixture-Hygiene **F1–F3** (Bestands-Fixture-Parität, SSOT-Konstanten-Import wie `EPISTEMIC_NOTICE_TEXT` & `DOC_EXCLUDES`, `ruff check` + `MYPYPATH=src mypy` mit `0` Fehlern vor Freeze).
       - Belege das zweistufige Differenzsignal (Bestand grün, neue Vertrags- und Konfigurations-Tests deterministisch rot) und setze den Test-Freeze (`src/` = 0, `docs/` = 0).
     - **Schritt 4 — `PHASE_GREEN` (nur `src/`):**
       - Setze die SRP-Regel-Interfaces und die per-Preset-Konfiguration in `src/qb_cubie/` um.
       - Halte alle Styleguide- und Statik-Gates von Beginn an ein: `FUNCTION_LIMIT = 12` physische Body-Zeilen, `MODULE_LIMIT = 777`, einzeilige Docstrings, `ruff`, `pylint` (`tests/test_lint.py`) und `mypy --warn-unreachable` ohne Befunde.
       - Führe den beobachtenden Doku-Check (`pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py`) durch, ohne `docs/` anzufassen (`tests/**/*.py` = 0, `docs/` = 0). Bei unerwarteten Test-Widersprüchen greift `tests/GREEN_AUDIT.md` gemäß [`NODE_GREEN_AUDIT.md`](../../tgd/NODE_GREEN_AUDIT.md).
     - **Schritt 5 — `LIVING_DOCS` (nur `docs/`):**
       - Synchronisiere die betroffenen Doku-Guides streng nach *Code as Source of Truth* (insbesondere `docs/services/GUIDE_DocFrame.md`, `docs/dev/DEV-GUIDE_DocFrame-Conventions.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md` und `docs/dev/DEV-GUIDE_TGD-Workflow.md` — dort auch die geplante `foot`-Zone-Notiz in §4 auf den neuen Ist-Stand umstellen und die zwei verdrehten Platzhalter-Zeilen in der `RUN-*.md`-Vorlage in §3 glattziehen).
       - Verifiziere `qb-cubie docframe update` (2× idempotent, 2. Lauf `Updated 0 file(s)`), `docframe check`, `docensurance check` und `pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` (`src/` = 0, `tests/` = 0).

## 4. Relevante Referenzen
- **TGD-Regelwerk & Knoten-Handbücher:**
  - [TGD-Knoten-Übersicht (docs/tgd/README.md)](../../tgd/README.md)
  - [NODE_ANALYSIS.md](../../tgd/NODE_ANALYSIS.md)
  - [NODE_HYPOTHESIS.md](../../tgd/NODE_HYPOTHESIS.md)
  - [NODE_PHASE_RED.md](../../tgd/NODE_PHASE_RED.md)
  - [NODE_PHASE_GREEN.md](../../tgd/NODE_PHASE_GREEN.md)
  - [NODE_GREEN_AUDIT.md](../../tgd/NODE_GREEN_AUDIT.md)
  - [NODE_LIVING_DOCS.md](../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil & Styleguide:**
  - [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
  - [Style-Guide.md](../../dev/Style-Guide.md)
- **Service- & Rahmen-Dokumentation:**
  - [GUIDE_DocFrame.md](../../services/GUIDE_DocFrame.md)
  - [GUIDE_DocEnsurance.md](../../services/GUIDE_DocEnsurance.md)
  - [DEV-GUIDE_DocFrame-Conventions.md](../../dev/DEV-GUIDE_DocFrame-Conventions.md)
  - [DEV-GUIDE_Agent-Reports.md](../../dev/DEV-GUIDE_Agent-Reports.md)
- **Betroffene Test- & Quellcode-Bereiche:**
  - [tests/test_doc_frame.py](../../../tests/test_doc_frame.py)
  - [tests/test_doc_ensurance.py](../../../tests/test_doc_ensurance.py)
  - [tests/tests_core/tests_service_core/test_rules_and_docframe.py](../../../tests/tests_core/tests_service_core/test_rules_and_docframe.py)
  - [src/qb_cubie/core/services/doc_frame/](../../../src/qb_cubie/core/services/doc_frame/)
  - [src/qb_cubie/core/services/doc_ensurance/](../../../src/qb_cubie/core/services/doc_ensurance/)