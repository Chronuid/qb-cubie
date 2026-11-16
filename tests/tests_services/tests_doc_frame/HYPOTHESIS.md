<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Argon" effort="High" routable="false" -->
# Feldbericht & Hypothesensystem zu `DocFrame` (Step 1) und Meta-QA der Test-Suite

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 16. November 2026 (~05:22 Uhr)
- **Synthesebasis:** `GUIDE_Quality-Assurance.md`, `DEV-GUIDE_DocFrame.md`, `META_QUESTION.md`, `tests/tests_services/tests_doc_frame/GEMINI.md` (Commit `03d7a0dd`)

---
<!-- /qb:frame -->

Die Auswertung des ersten Implementierungsschritts von `DocFrame` (`03d7a0dd`) im Abgleich mit dem `make test-all`-Protokoll (`1428 passed, 2 failed in 395.56s`), dem QA-Handbuch und der Meta-QA-Analyse (`META_QUESTION.md`) zeigt: Die neue `tests_doc_frame`-Suite setzt die verschärften TGD-Leitlinien bereits konsequent und frei von Quantoren-Fallen um. Die verbleibenden Brüche resultieren aus zwei statischen Typ-/Import-Inkonsistenzen an der Schnittstelle `DocEnsurance`/`DocFrame`, einem noch ausstehenden Rollout von Step 2 auf den realen Dokumentationsbestand sowie historischen Altlasten in `tests_doc_ensurance/`.

---

## 1. Empirischer Befund aus dem `make test-all`-Lauf (`GEMINI.md`)

* **Befund A – Unbenutzter Import bricht `test_src_lint[ruff]` (`F401`):**
  In `src/qb_cubie/services/doc_ensurance/doc_ensurance.py` (Zeile 14) wird `Linter` aus `...linter` importiert, nach der Auslagerung der Regel-Koerzierung aber im Modul selbst nicht mehr referenziert.

* **Befund B – Statische Typverengung bricht `test_src_lint[mypy]` (`[unreachable]` & `[return-value]`):**
  1. In `src/qb_cubie/services/doc_frame/doc_frame.py` (Zeile 263–271) ist `_normalize_patterns` mit `pattern: FramePattern | Sequence[FramePattern] | None` annotiert. Nach `isinstance(pattern, FramePattern)` verengt `mypy --warn-unreachable` den Typ von `items` auf `Sequence[FramePattern]`. Da `str` (`Sequence[str]`) und `bytes` (`Sequence[int]`) aufgrund inkompatibler Methodenauflösung (MRO) keine Unterklasse mit `Sequence[FramePattern]` bilden können, stuft `mypy` den Laufzeit-`STATE-GUARD` `isinstance(items, (str, bytes))` als unerreichbar (`[unreachable]`) ein.
  2. In `src/qb_cubie/services/doc_ensurance/doc_ensurance.py` (Zeile 170–183) prüft `_split_patterns` die übergebenen Pattern-Objekte mittels `hasattr(p, "scan")`. Da `hasattr` für `mypy` keine Typverengung (`TypeGuard`) auf `DocPatternProtocol` durchführt, behält `primary` den unpräzisen Typ `DocPatternProtocol | Any | Sequence[Any]` und verletzt den Rückgabetyp `tuple[DocPatternProtocol, tuple[Any, ...] | None]`.

* **Befund C – Methodische Konformität der neuen `tests_doc_frame`-Suite:**
  Alle 22 EBT-Verträge in `test_docframe_catalog_and_routing.py`, `test_docframe_presets_and_update.py` und `test_docframe_rules_and_guards.py` bestehen im isolierten `TempFS`. Im Gegensatz zu den älteren Suiten vermeidet `tests_doc_frame` das Kreuzprodukt heterogener Vor- und Nachbedingungen vollständig (`1 pre -> 1 post` bzw. `@pytest.mark.parametrize`), bündelt `pre=[...]` nur bei identischem `STATE-GUARD`-Zielzustand und hält das 12-Zeilen-Funktionslimit aus `test_styleguide.py` strikt ein.

* **Befund D – Fortbestehende Anomalien in den Bestands-Tests (`META_QUESTION.md`):**
  1. **Disjunktive Abschwächung & Laufzeit-Amplifikation (`tests_doc_ensurance/`):** Über 25 `EBT`-Aufrufe in `tests_doc_ensurance/` nutzen weiterhin heterogene `pre=[...]`- und `post=[...]`-Listen ($N \times M$-Kreuzprodukt), was sowohl die Spezifikationsschärfe auf $\forall i \exists j$ reduziert als auch die Gesamtlaufzeit (`395.56s`) durch redundante Arena-Läufe aufbläht.
  2. **Isolierte und subsumierte `expect=False`-Klauseln:** Red-Phase-Relikte ohne positiven Anker in `test_doc_rule_edge_cases.py` und `test_doc_ensurance_configs.py` sowie redundante Negativ-Assertions in `test_doc_linter_feedback.py` sind weiterhin aktiv.
  3. **Deaktivierter `slow`-Marker in `test_styleguide.py`:** `#@pytest.mark.slow` über `test_docs_code_examples()` (Zeile 99) ist auskommentiert, wodurch `conftest.py` den Repository-weiten `DocEnsurance`-Lauf automatisch als `fast` einstuft.
  4. **Gespaltener Modul-Namespace (`src.qb_cubie` vs. `qb_cubie`):** `test_headless_reviewer.py`, `test_rbt_reporter.py` und `test_rbt_demo.py` importieren weiterhin über `src.qb_cubie`.
  5. **Verwaiste `__pycache__`-Artefakte:** Durch das Re-Packaging in Commit `174b048f` liegen verwaiste `.pyc`-Dateien in `src/qb_cubie/services/__pycache__/`, `tests/tests_services/__pycache__/` sowie `tests/__pycache__/`.

* **Befund E – Unsynchronisierter Ist-Bestand für `DocFrame` Step 2 & Exclude-Grenzen:**
  Die realen Markdown-Dokumente unter `docs/` und `README.md` wurden noch nicht mit `DocFrame.update()` synchronisiert (enthalten im Footer weiterhin `![Error while trying to load the image]` sowie statische 10er-Listen; `docs/misc/README.md` nutzt noch `CUBIE_DOC_FRAME_1` statt `CUBIE_DOC_FRAME_3`). Zudem enthält `DEFAULT_EXCLUDES` (`[".venv", "__pycache__", ".git"]`) weder `.pytest_cache` noch `tests` (inkl. `tests/.arenas/`), sodass eine unreflektierte Aktivierung von `CUBIE_DOCFRAME_RULES` auf dem Repository-Root ohne angepasste `excludes` auf technische Hilfsdateien (`CHANGELOG.md`, `.pytest_cache/README.md`, `tests/**/*.md`) anschlagen würde.

---

## 2. Konsolidiertes Hypothesensystem für Step 2 & Suite-Härtung

| ID | Hypothese | Erwarteter Nachweis / Prüf-Gate |
| :--- | :--- | :--- |
| **H1 (Statische Typ- & Import-Schärfung)** | Wenn in `doc_ensurance.py` der ungenutzte `Linter`-Import entfernt, in `_split_patterns` `isinstance(p, DocPatternProtocol)` statt `hasattr` genutzt und in `doc_frame.py::_normalize_patterns` (sowie `_normalize_excludes`) die Eingabesignatur für Laufzeit-Guards auf `Any` gesetzt wird, laufen `test_src_lint[ruff]`, `test_src_lint[pylint]` und `test_src_lint[mypy]` unter `--warn-unreachable` vollständig grün. | `pytest tests/test_lint.py` $\to$ `8 passed` |
| **H2 (Exclude-Abgrenzung beim Rollout)** | Wenn technische Verzeichnisse und Nicht-Guide-Artefakte (`.pytest_cache`, `tests`, `experiments`, `GUTACHTEN.md`, `CHANGELOG.md`) explizit exkludiert (bzw. Feldberichte wie `META_QUESTION.md` mit `CUBIE_DOC_FRAME_2` gerahmt) und `docs/misc/README.md` auf `CUBIE_DOC_FRAME_3` gehoben werden, konvergiert `DocFrame.update()` über dem gesamten Repository idempotent im zweiten Durchlauf (`updated_files == ()`). | `DocFrame.update()` + `CUBIE_DOCFRAME_RULES` in `test_styleguide.py` $\to$ `passed=True` |
| **H3 (Entkopplung heterogener Kreuzprodukte)** | Wenn die heterogenen `pre=[...]`/`post=[...]`-Aufrufe in `tests_doc_ensurance/` analog zu `tests_doc_frame/` in parametrisierte Einzelverträge (`1 pre -> 1 post`) und die redundanten `expect=False`-Subsumtionen in `test_doc_linter_feedback.py` aufgelöst werden, steigt die Fehlererkennungsschärfe von $\forall i \exists j$ auf $\bigwedge_i \{P_i\} S \{Q_i\}$ bei gleichzeitiger drastischer Reduktion der Arena-Subprozesse. | Rückgang der `trace.traces`-Kreuzprodukte von $N^2$ auf $N$; deutliche Laufzeitreduktion in `make test-all` |
| **H4 (Namespace- & Collection-Hygiene)** | Wenn `src.qb_cubie`-Imports in den RBT-Tests auf `qb_cubie` normiert, `@pytest.mark.slow` an `test_docs_code_examples` reaktiviert und verwaiste `__pycache__`-Verzeichnisse bereinigt werden, verschwinden doppelte Modul-Identitäten in `sys.modules` und `make test-fast` hält wieder den in `README.md` zugesicherten Schnellstart-Vertrag ein. | `pytest -m "meta or reviewer"` $\to$ `passed` ohne `src.qb_cubie` in `sys.modules` |

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->
<!-- /qb:frame -->
