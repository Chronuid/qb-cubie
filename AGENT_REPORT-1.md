<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Argon" effort="Medium" -->
# TGD-Protokoll: Lösung von BUG-002 (`PytestReporter` verliert Assertions unter optimiertem Python `python -O`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Argon
- **Reasoning-Effort:** Medium
- **Analysedatum:** 24. November 2026, ~19:58 (CET)
- **Synthesebasis:** `GEMINI.md`, `KNOWN_ISSUES.md`, `GUTACHTEN.md`, `src/qb_cubie/core/reporter.py`, `tests/tests_core/test_rbt_reporter.py`, `tests/tests_core/tests_ebt/test_ebt_return_reporting.py`, `docs/GUIDE_Quality-Assurance.md`, `docs/GUIDE_Contract-Design.md`, `docs/GUIDE_Expect-Flags.md`, `docs/GUIDE_Quantifiers.md`, `docs/GUIDE_TGD.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md`, `docs/dev/DEV-GUIDE_Write-down-the-bugs.md`, `docs/dev/Style-Guide.md`, `docs/misc/lake/SOLVED_ISSUES.md`
- **Stand:** qb-cubie (`v0.1.0`, Branch `main`, Commit `40f43487`)
- **Git-Log:** `40f43487` ("Addressed BUG-007.")

---

```text
commit 40f4348787dc4cc1b180c4110681d65732e94e74 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Tue Nov 24 19:45:14 2026 +0100

    Addressed BUG-007.

Auftrag (GEMINI.md):
- Lösung von BUG-002 mittels voll-autonomen TGD-Flow.
- Dokumentation des Verlaufs in AGENT_REPORT.md.
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **`[BEFUND & URSACHE]` (`src/qb_cubie/core/reporter.py:44-57`):** `PytestReporter.report()` verwendete drei reguläre Python-`assert`-Statements zur Durchsetzung fehlgeschlagener `ReviewData`- (`RBT`), `ServiceReportProtocol`- (`DocEnsurance` / Services) und `RunTrace`-Ergebnisse (`EBT`). Beim Start des Interpreters mit `-O` oder `-OO` (`__debug__ == False`) entfernt der Python-Bytecode-Compiler sämtliche `assert`-Anweisungen, sodass fehlgeschlagene Verträge (`evaluation is False` bzw. `passed is False`) stumm ohne `AssertionError` durchliefen.
2. **`[PHASE RED]` (`tests/tests_core/test_rbt_reporter.py:166-291`):** Schlanker, zustandsfreier Subprozess-Testadapter `run_reporter_under_python_optimize(kind, opt_flag)` und 8 parametrisierte `EBT`-Verträge (`test_pytest_reporter_enforces_assertions_under_python_optimize`) für `EBT` (positiv/negativ, `-O` und `-OO`), `RBT` und `ServiceReportProtocol` (Fehlschläge + Positiv-/Warning-Kontrollen) ergänzt. Red-Nachweis gegen den unreparierten Core: exakt **5 FAILED** (alle 5 Negativ-Fälle liefen unter `-O`/`-OO` fälschlich mit Exit-Code `0` durch) und **3 PASSED** (Positiv-Kontrollen) bei **100 % grünen Meta-Gates** (`96 passed`).
3. **`[PHASE GREEN]` (`src/qb_cubie/core/reporter.py:44-63`):** Bei eingefrorener Test-Suite wurden die drei `assert`-Anweisungen in `PytestReporter.report()` durch explizite `raise AssertionError(...)`-Auslösungen (über den `__tracebackhide__`-geschützten Helper `PytestReporter._fail_if()`) ersetzt. Alle 8 neuen Verträge sowie sämtliche Bestands- und Styleguide-Checks (`FUNCTION_LIMIT <= 12` Zeilen) wechselten ohne `GREEN_AUDIT`-Rücksprung auf **`PASSED`**.
4. **`[PHASE LIVING-DOCUMENTATION]` (`KNOWN_ISSUES.md`, `docs/misc/lake/SOLVED_ISSUES.md`, `CHANGELOG.md`, `AGENT_REPORT.md`):** `[BUG-002]` aus `KNOWN_ISSUES.md` in das Archiv `docs/misc/lake/SOLVED_ISSUES.md` verschoben, im `CHANGELOG.md` unter `[Unreleased]` vermerkt und alle `qb:frame`-Dokumentrahmen via `DocFrame.update()` sowie `test_doc_frame.py` und `test_doc_ensurance.py` verifiziert.

---

## 1. Stützrad 1 & 2: `ANALYSIS` & `HYPOTHESIS`

### 1.1 Analyse des Ist-Zustands ($Q_{\text{Ist}}$) vs. Soll-Spezifikation ($Q_{\text{Soll}}$)

Eine repository-weite Suche nach `\bassert\b` unter `src/` ergab exakt drei Fundstellen im gesamten Produktionscode — alle drei in `src/qb_cubie/core/reporter.py` innerhalb von `PytestReporter.report()` (Zeilen 48, 52 und 57):

```text
src/qb_cubie/core/reporter.py:48:            assert trace.passed, self._generate_review_report(trace)
src/qb_cubie/core/reporter.py:52:            assert trace.passed, self._generate_service_report(trace)
src/qb_cubie/core/reporter.py:57:            assert False, report_msg
```

* **Beobachtetes Verhalten ($Q_{\text{Ist}}$):** Unter `python -O` (oder `python -OO` / `PYTHONOPTIMIZE=1`) setzt Python `__debug__ = False` und kompiliert `assert`-Statements nicht in den Bytecode. Ein reproduzierender Lauf bestätigte, dass sowohl `EBT(target=lambda: 1, post=WorldState(returns=2)).run()` als auch `RBT(check='check', target='target', reviewer=HeadlessReviewer(answer=False)).run()` ohne Exception mit `EBT eval: False RBT passed: False` zurückkehren.
* **Spezifiziertes Verhalten ($Q_{\text{Soll}}$):** `PytestReporter.report()` muss bei `ReviewData(passed=False)`, `ServiceReportProtocol(passed=False)` und `RunTrace(evaluation=False)` unabhängig vom Python-Optimierungsflag (`__debug__`) deterministisch einen `AssertionError` mit dem formatierten Diagnosebericht auslösen, während erfolgreiche Läufe (`passed=True` bzw. `evaluation=True`) sowie reine Service-Warnungen (`severity="warning"`, `passed=True`) weiterhin ohne `AssertionError` durchlaufen.

### 1.2 Falsifikationshypothesen (`HYPOTHESIS`)

1. **Hypothese H1 (Bytecode-Eliminierung in allen drei Reporter-Pfaden):** In einem mit `sys.executable -O` bzw. `-OO` gestarteten Kindprozess (`__debug__ is False`) schlagen alle drei Fehlermodi von `PytestReporter.report()` (`ebt_fail`, `ebt_negative_fail`, `rbt_fail`, `service_fail`) gegen den unreparierten Core fehl, weil der Kindprozess mit `returncode == 0` statt `AssertionError` endet.
2. **Hypothese H2 (Erhalt der Positiv- und Warning-Invarianz):** Erfolgreiche `EBT`-, `RBT`- und Service-Warning-Läufe (`ebt_pass`, `rbt_pass`, `service_warning_pass`) enden unter `python -O` vor und nach dem Fix mit `returncode == 0` (kein Vacuous Fail; `UserWarning` wird weiterhin emittiert).
3. **Hypothese H3 (Styleguide-Konformität unter `FUNCTION_LIMIT = 12`):** Durch Auslagerung der Bedingungsprüfung in eine statische Hilfsmethode `_fail_if(failed: bool, message: str) -> None` mit `__tracebackhide__ = True` bleibt `PytestReporter.report()` bei exakt `12` physischen Body-Zeilen (`FUNCTION_LIMIT = 12` in `tests/test_styleguide.py`).

---

## 2. Schritt 2–4: `Phase Red` (Adapter, Äquivalenzklassen & Test-Freeze)

In `tests/tests_core/test_rbt_reporter.py` wurden ausschließlich unter `tests/` folgende Ergänzungen vorgenommen:

1. **Zustandsfreier Test-Adapter (`run_reporter_under_python_optimize`):** Startet `sys.executable` mit `opt_flag` (`"-O"` oder `"-OO"`), stellt über `if __debug__: raise RuntimeError(...)` sicher, dass der Optimierungsmodus tatsächlich aktiv ist, führt das jeweilige Testszenario aus und verdichtet das Ergebnis auf das Dictionary `{"failed": bool, "has_assertion_error": bool, "has_expected_marker": bool}`.
2. **Abgedeckte Äquivalenzklassen (`test_pytest_reporter_enforces_assertions_under_python_optimize`):**
   * `ebt-fail-O`: Regulärer `EBT`-Mismatch unter `-O` $\to$ `AssertionError` mit `"EBT-Assert failed"`.
   * `ebt-negative-fail-O`: Negierter `EBT(..., expect=False)`-Mismatch unter `-O` $\to$ `AssertionError` mit `"EBT-Negative-Assert failed"`.
   * `ebt-fail-OO`: Regulärer `EBT`-Mismatch unter `-OO` (Docstring-Stripping + Assert-Stripping) $\to$ `AssertionError`.
   * `rbt-fail-O`: Abgelehnter `RBT`-Review (`HeadlessReviewer(answer=False)`) unter `-O` $\to$ `AssertionError` mit `"--- Report ---"`.
   * `service-fail-O`: Fehlgeschlagener `ServiceReportProtocol`-Bericht (`passed=False`, `severity="error"`) unter `-O` $\to$ `AssertionError` mit `"[DOC-OUT] docs/sample.md:7: Mismatch"`.
   * `ebt-pass-O`, `rbt-pass-O`, `service-warning-pass-O`: Positiv- und `UserWarning`-Gegenproben unter `-O` $\to$ kein `AssertionError` (`failed=False`).
3. **Einhaltung der Vertrags- und Meta-Gates:** Durch die Parametrisierung via `@pytest.mark.parametrize` prüft jeder `EBT`-Aufruf exakt ein `1x1`-Paar (`pre=WorldState(...)`, `post=WorldState(...)`). Alle drei Meta-Gates (`META-CANONICAL-IMPORT`, `META-EBT-CROSS-PRODUCT`, `META-EBT-LONELY-NEGATION`) liefen in der Red-Phase mit `0` Diagnosen grün.
4. **Red-Nachweis & Freeze:** Gegen den unreparierten Core schlugen exakt die 5 Negativ-Verträge rot fehl (`5 failed, 96 passed`), woraufhin `tests/` eingefroren wurde.

---

## 3. Schritt 5: `Phase Green` & `Phase Living-Documentation`

### 3.1 Core-Reparatur in `src/qb_cubie/core/reporter.py`

Ohne jede Änderung an `tests/` wurde `PytestReporter.report()` in `src/qb_cubie/core/reporter.py` auf explizite `AssertionError`-Auslösung umgestellt und um `_fail_if()` ergänzt:

```text
    def report(self, trace: RunTrace | ReviewData | ServiceReportProtocol) -> None:
        """Evaluates the final run status and raises an assertion with formatted trace details on failure."""
        __tracebackhide__ = True
        if isinstance(trace, ReviewData):
            self._fail_if(not trace.passed, self._generate_review_report(trace))
            return
        if not isinstance(trace, RunTrace):
            self._emit_service_warnings(trace)
            self._fail_if(not trace.passed, self._generate_service_report(trace))
            return
        if trace.evaluation is False:
            ctx = ReportContext(verbosity=self.verbosity, max_diff_items=self.max_diff_items)
            raise AssertionError(self._generate_report(trace, ctx))

    @staticmethod
    def _fail_if(failed: bool, message: str) -> None:
        """Raises an explicit AssertionError independent of Python optimization flags."""
        __tracebackhide__ = True
        if failed:
            raise AssertionError(message)
```

* Alle 5 zuvor roten Tests sprangen sofort auf `PASSED` (`19 passed` in `test_rbt_reporter.py`).
* Ein `GREEN_AUDIT`-Rücksprung war nicht erforderlich.
* Die physische Body-Zeilen-Prüfung (`body_lines` aus `tests/test_styleguide.py`) bestätigt für `reporter.py` ein Maximum von `12` Zeilen (`FUNCTION_LIMIT = 12`).

### 3.2 Synchronisation der Living Documentation

* **`KNOWN_ISSUES.md` & `docs/misc/lake/SOLVED_ISSUES.md`:** `[BUG-002]` wurde gemäß `DEV-GUIDE_Write-down-the-bugs.md` aus den offenen Bugs entfernt und mit Ursachen- und Lösungsbeschreibung in `docs/misc/lake/SOLVED_ISSUES.md` archiviert.
* **`CHANGELOG.md`:** Fix unter `## [Unreleased] -> ### Behoben` dokumentiert.
* **`AGENT_REPORT.md` & `DocFrame.update()`:** Dieser TGD-Verlaufsbericht wurde im `CUBIE_DOC_FRAME_2`-Format erstellt und über `DocFrame` mit dem Dokumentationskatalog synchronisiert.

---

## 4. Verifikationsprotokoll

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Bug-Reproduktion (`Ist`) | `.venv/bin/python -O -c "from qb_cubie import EBT, WorldState ..."` | `EBT eval: False RBT passed: False` ohne `AssertionError` |
| **Phase Red** (`test_rbt_reporter.py` + `tests_meta/`) | `.venv/bin/python -m pytest -q tests/tests_core/test_rbt_reporter.py tests/tests_meta/` | **`5 failed, 96 passed`** (exakt die 5 neuen `-O`/`-OO`-Fehlernachweise rot, alle Meta-Gates grün) |
| **Phase Green** (`test_rbt_reporter.py` + `test_styleguide.py`) | `.venv/bin/python -m pytest -q tests/tests_core/test_rbt_reporter.py tests/test_styleguide.py` | **`29 passed, 1 skipped`** (`reporter.py` max. `12` Body-Zeilen) |
| **Phase Living-Documentation** (`DocFrame` + `DocEnsurance` + `test_lint.py`) | `.venv/bin/python -m pytest -m "" -q tests/test_doc_frame.py tests/test_doc_ensurance.py tests/test_lint.py` | **Alle Doku-, Rahmen- und Linter-Gates (`ruff`, `pylint`, `mypy`) grün** |
| Schnelle Gesamtsuite (`make test`) | `.venv/bin/python -m pytest -q` | **Komplette Fast-Suite (`not slow`) grün** |

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
