<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Hydrogen" effort="Medium" -->
# TGD-Protokoll: Lösung von BUG-003 (`CstLinter.check()` gibt für nicht existierende Pfade stumm `[]` zurück)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Hydrogen
- **Reasoning-Effort:** Medium
- **Analysedatum:** 24. November 2026, ~20:17 (CET)
- **Synthesebasis:** `GEMINI.md`, `KNOWN_ISSUES.md`, `src/qb_cubie/core/linter.py`, `tests/tests_core/tests_linters/test_linter_cst.py`, `docs/GUIDE_TGD.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md`, `docs/dev/Style-Guide.md`, `docs/misc/lake/SOLVED_ISSUES.md`
- **Stand:** qb-cubie (`v0.1.0`, Branch `main`, Commit `6ce7dca8`)
- **Git-Log:** `6ce7dca8` ("Tried a fully autonomous TGD-Flow for BUG-002.")

---

```text
commit 6ce7dca80c3623e70375d1f067dd2ef7a5880844 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Tue Nov 24 20:10:39 2026 +0100

    Tried a fully autonomous TGD-Flow for BUG-002.

Auftrag (GEMINI.md):
- Lösung von BUG-003 mittels voll-autonomen TGD-Flow.
- Dokumentation des Verlaufs in AGENT_REPORT-2.md.
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **`[BEFUND & URSACHE]` (`src/qb_cubie/core/linter.py:218-229`):** `CstLinter.check()` unterschied bei `Path`-Zielen nur zwischen `target.is_file()` und `target.is_dir()`. Bei nicht existierenden Pfaden (z. B. `Path('/nicht/vorhanden.py')`, fehlenden Verzeichnissen, defekten Symlinks) sowie bei existierenden Sonderdateien (weder Datei noch Verzeichnis, z. B. FIFO) griffen beide Zweige nicht, sodass die Methode stumm `[]` zurückgab.
2. **`[PHASE RED]` (`tests/tests_core/tests_linters/test_linter_cst.py:100-156`):** Neue Äquivalenzklassen- und Positiv-Kontroll-Tests (`test_cstlinter_rejects_nonexistent_path` für `missing_file`, `missing_dir`, `broken_symlink`, `test_cstlinter_rejects_unsuitable_path` via `os.mkfifo` sowie `test_cstlinter_valid_path_targets` für gültige Dateien, leere Verzeichnisse und `excludes`) ergänzt. Red-Nachweis gegen den unreparierten Core: exakt **4 FAILED** (alle 4 Negativ-Verträge liefen stumm mit normalem Return durch) und **5 PASSED** bei **100 % grünen Meta-Gates** (`84 passed`).
3. **`[PHASE GREEN]` (`src/qb_cubie/core/linter.py:218-239`):** Bei eingefrorener Test-Suite wurde `CstLinter.check()` um `_check_path()` und `_check_directory()` erweitert. Nicht existierende `Path`-Ziele lösen `FileNotFoundError("STATE-GUARD: Target path does not exist: ...")` aus, ungeeignete bestehende `Path`-Ziele lösen `ValueError("STATE-GUARD: Target path is neither a file nor a directory: ...")` aus. Alle 4 zuvor roten Verträge sprangen ohne `GREEN_AUDIT`-Rücksprung auf **`PASSED`**.
4. **`[PHASE LIVING-DOCUMENTATION]` (`KNOWN_ISSUES.md`, `docs/misc/lake/SOLVED_ISSUES.md`, `CHANGELOG.md`, `AGENT_REPORT-2.md`):** `[BUG-003]` aus `KNOWN_ISSUES.md` nach `docs/misc/lake/SOLVED_ISSUES.md` archiviert, im `CHANGELOG.md` unter `[Unreleased]` dokumentiert und die Dokumentrahmen via `DocFrame` sowie `test_doc_frame.py` / `test_doc_ensurance.py` verifiziert.

---

## 1. Stützrad 1 & 2: `ANALYSIS` & `HYPOTHESIS`

### 1.1 Analyse des Ist-Zustands ($Q_{\text{Ist}}$) vs. Soll-Spezifikation ($Q_{\text{Soll}}$)

* **Beobachtetes Verhalten ($Q_{\text{Ist}}$):** Der Reproduktionsaufruf `.venv/bin/python -c "from pathlib import Path; from qb_cubie import CstLinter; print(CstLinter([]).check(Path('/nicht/vorhanden.py')))"` gab vor dem Fix `[]` mit Exit-Code `0` zurück. In `CstLinter.check()` fiel jedes `Path`-Objekt, für das weder `is_file()` noch `is_dir()` zutraf, still auf `return all_diagnostics` (`[]`) durch.
* **Spezifiziertes Verhalten ($Q_{\text{Soll}}$):**
  * `str`-Eingaben bleiben unverändert In-Memory-Quelltext (`"IN_MEMORY"`).
  * Existierende `Path`-Dateien und -Verzeichnisse (inkl. leerer Verzeichnisse ohne `.py`-Dateien oder vollständig ausgeschlossener Verzeichnisse) liefern weiterhin die erwarteten Diagnosen bzw. `[]`.
  * Nicht existierende `Path`-Ziele (`not target.exists()`, inkl. fehlender Dateien, fehlender Verzeichnisse und defekter Symlinks) müssen explizit mit `FileNotFoundError` (`STATE-GUARD:`) abgelehnt werden.
  * Existierende, aber ungeeignete `Path`-Ziele (weder `is_file()` noch `is_dir()`, z. B. FIFO/Socket) müssen explizit mit `ValueError` (`STATE-GUARD:`) abgelehnt werden.

### 1.2 Falsifikationshypothesen (`HYPOTHESIS`)

1. **Hypothese H1 (Stilles Verschlucken bei nicht existierenden/ungeeigneten `Path`-Zielen):** Gegen den unreparierten Core schlagen `missing_file`, `missing_dir`, `broken_symlink` (`FileNotFoundError`) und `named_pipe` (`ValueError`) deterministisch fehl, weil `CstLinter.check()` normal `[]` zurückgibt.
2. **Hypothese H2 (Invarianz gültiger Eingaben):** `str`-Inputs, gültige Dateien, leere Verzeichnisse sowie Verzeichnisse mit `excludes` bleiben vor und nach dem Fix invariant (`PASSED`).
3. **Hypothese H3 (Styleguide- & Mypy-Konformität):** Durch Aufteilung in `check()` (3 Body-Zeilen), `_check_path()` (7 Body-Zeilen) und `_check_directory()` (5 Body-Zeilen) bleiben alle Methoden innerhalb von `FUNCTION_LIMIT = 12` und ohne `mypy --warn-unreachable`-Befunde.

---

## 2. Schritt 2–4: `Phase Red` (Äquivalenzklassen & Test-Freeze)

In `tests/tests_core/tests_linters/test_linter_cst.py` wurden ausschließlich unter `tests/` folgende `1x1`-`EBT`-Verträge ergänzt:

1. **`test_cstlinter_rejects_nonexistent_path` (`missing_file`, `missing_dir`, `broken_symlink`):** Erwartet `ExceptionExpectation(FileNotFoundError, match=r"STATE-GUARD:")`.
2. **`test_cstlinter_rejects_unsuitable_path` (`os.mkfifo` auf POSIX):** Erwartet `ExceptionExpectation(ValueError, match=r"STATE-GUARD:")`.
3. **`test_cstlinter_valid_path_targets`:** Positiv-Kontrolle für saubere Datei (`[]`), leeres Verzeichnis (`[]`) und Paketverzeichnis mit `.venv`-Ausschluss (`CST001`).

* **Red-Nachweis & Freeze:** `.venv/bin/python -m pytest -q tests/tests_core/tests_linters/test_linter_cst.py` ergab **`4 failed, 5 passed in 0.31s`**; `.venv/bin/python -m pytest -q tests/tests_meta/` ergab **`84 passed in 17.73s`**. Anschließend wurde `tests/` eingefroren.

---

## 3. Schritt 5: `Phase Green` & `Phase Living-Documentation`

### 3.1 Core-Reparatur in `src/qb_cubie/core/linter.py`

Ohne Änderungen an `tests/` wurde `CstLinter.check()` in `src/qb_cubie/core/linter.py` um `_check_path()` und `_check_directory()` ergänzt:

* `CstLinter.check()` delegiert `Path`-Ziele an `self._check_path(target)`.
* `CstLinter._check_path()` prüft `not target.exists()` $\to$ `FileNotFoundError("STATE-GUARD: ...")`, anschließend `target.is_file()` und `target.is_dir()`, und weist sonstige bestehende `Path`-Objekte mit `ValueError("STATE-GUARD: ...")` ab.
* `CstLinter._check_directory()` kapselt den Verzeichnis-Crawl.
* Ein `GREEN_AUDIT`-Rücksprung war nicht erforderlich.

### 3.2 Synchronisation der Living Documentation

* **`KNOWN_ISSUES.md` & `docs/misc/lake/SOLVED_ISSUES.md`:** `[BUG-003]` aus den offenen Bugs entfernt und mit Ursache & Lösung in `docs/misc/lake/SOLVED_ISSUES.md` archiviert.
* **`CHANGELOG.md`:** Fix unter `## [Unreleased] -> ### Behoben` dokumentiert.
* **`AGENT_REPORT-2.md` & `DocFrame`:** Bericht im `CUBIE_DOC_FRAME_2`-Format erstellt und über `DocFrame` synchronisiert.

---

## 4. Verifikationsprotokoll

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Baseline vor Eingriff | `.venv/bin/python -m pytest -q tests/tests_core/tests_linters/test_linter_cst.py tests/tests_meta/ tests/test_styleguide.py tests/test_lint.py` | `100 passed, 1 skipped, 9 deselected` |
| Reproduktion vor Fix | `.venv/bin/python -c "from pathlib import Path; from qb_cubie import CstLinter; print(CstLinter([]).check(Path('/nicht/vorhanden.py')))"` | `[]` (Exit-Code `0`) |
| Phase Red (`test_linter_cst.py`) | `.venv/bin/python -m pytest -q tests/tests_core/tests_linters/test_linter_cst.py` | `4 failed, 5 passed` |
| Phase Red (Meta-Gates) | `.venv/bin/python -m pytest -q tests/tests_meta/` | `84 passed` |
| Reproduktion nach Fix | `.venv/bin/python -c "from pathlib import Path; from qb_cubie import CstLinter; CstLinter([]).check(Path('/nicht/vorhanden.py'))"` | `FileNotFoundError: STATE-GUARD: Target path does not exist: /nicht/vorhanden.py` |
| Finale Verifikation (Linter, Meta, Styleguide, Lint, Docs) | `.venv/bin/python -m pytest -q tests/tests_core/tests_linters/test_linter_cst.py tests/tests_meta/ tests/test_styleguide.py tests/test_lint.py tests/test_doc_frame.py tests/test_doc_ensurance.py` | `107 passed, 1 skipped, 9 deselected` |

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
