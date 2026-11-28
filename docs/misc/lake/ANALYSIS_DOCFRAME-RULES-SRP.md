<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Hydrogen" effort="Medium" -->
# Analyse: SRP-Regel-Interfaces & konfigurierbare `foot`-Zone (`DocFrame` & `DocEnsurance`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Hydrogen
- **Reasoning-Effort:** Medium
- **Analysedatum:** 28. November 2026, ~04:56 (CET)
- **Synthesebasis:** `src/qb_cubie/core/services/doc_frame/*`, `src/qb_cubie/core/services/doc_ensurance/*`, `src/qb_cubie/core/services/__init__.py`, `tests/test_doc_frame.py`, `tests/test_doc_ensurance.py`, `tests/tests_core/tests_service_core/test_rules_and_docframe.py`, `tests/tests_core/tests_services/tests_doc_frame/test_docframe_rules_and_guards.py`
- **Stand:** qb-cubie (`v0.1.2`, Branch `main`, Commit `5702806e`)
- **Git-Log:** `5702806e` ("Tried to prepare RUN-003.")

---

```text
Scope: Rein lesende Ist-Vermessung (NODE_ANALYSIS) für RUN-3 (`docframe-rules-srp`).
Keine Änderungen an `src/`, `tests/` oder produktiven Handbüchern unter `docs/`.
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **`[BLOCKER]` Keine granulare Per-Preset-Regelkonfiguration in `DocFrame`:** `CUBIE_DOCFRAME_RULES` in `src/qb_cubie/core/services/doc_frame/doc_frame_rules.py` (L321–326) ist ein globales 4er-Tupel ohne Preset-Bindung. `DocFrame.check()` (L100–120 in `doc_frame.py`) und `tests/test_doc_frame.py` (L16–24) wenden dieselben Regel-Instanzen pauschal auf alle drei Presets (`CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2`, `CUBIE_DOC_FRAME_3`) an.
2. **`[ABWEICHUNG]` Fehlende atomare `foot`-Link-Listen-Regel:** `DocFrameMissing` (L166–190) prüft aktuell nur das Vorhandensein der Zonen `head`, `foot` und ggf. `router` (`_has_missing_zones`, L36–49). `DocFrameOutdated` (L256–313) vergleicht den kompletten gerenderten Zonen-Inhalt, und `DocFrameBrokenRoute` (L224–253) prüft vorhandene Link-Ziele. Eine dedizierte, pro Preset mit `severity` (`"error"` vs. `"warning"`) konfigurierbare Regel für fehlende Link-Listen in `zone="foot"` existiert noch nicht.
3. **`[RISIKO]` Asymmetrie & Doppelpflege zwischen `DocFrame` und `DocEnsurance`:** Beide Services nutzen `RuleRegistry` bzw. `FileCheckRunner` aus `service_core.rules`, definieren ihre Standard-Regelsets (`CUBIE_DOCFRAME_RULES` vs. `CUBIE_DOC_RULES`) jedoch als flache globale Tupel ohne einheitliches Profil-/Preset-Bindungs-Interface.
4. **`[HINWEIS]` Bestehende Gates & Baseline sind grün:** `test_styleguide.py`, `test_doc_frame.py`, `test_doc_ensurance.py`, `test_rules_and_docframe.py` (29 passed) sowie `test_lint.py` (9 passed) und `mypy --warn-unreachable src/qb_cubie` (0 Fehler in 55 Dateien) laufen sauber durch.

---

## 1. Ist-Vermessung ($Q_{\text{Ist}}$)

### 1.1 `DocFrame`-Regeln & Orchestrierung (`src/qb_cubie/core/services/doc_frame/`)

| Fundstelle | Beobachteter Ist-Zustand (`Ist`) | Relevanz für `Q_Soll` |
| :--- | :--- | :--- |
| `doc_frame_rules.py:118-162` | `_DocFrameRuleBase` kapselt `context_key = "doc_frame"`, `prepare_workspace()` und `check_file()` mit `FileContextCache`. | Saubere Basis für atomare Einzelregeln mit geteiltem Span-Parse-Cache. |
| `doc_frame_rules.py:165-314` | Vier Regelklassen: `DocFrameMissing` (`DOCFRAME-MISSING`), `DocFrameProvenanceIncomplete` (`DOCFRAME-PROVENANCE-INCOMPLETE`), `DocFrameBrokenRoute` (`DOCFRAME-BROKEN-ROUTE`), `DocFrameOutdated` (`DOCFRAME-OUTDATED`). Alle haben `severity: str = "error"`. | Alle prüfen global über alle `FramePattern`-IDs hinweg; keine Regel hat ein `pattern_ids`-/Preset-Scoping oder eine spezifische `foot`-Link-Listen-Prüfung. |
| `doc_frame_rules.py:321-326` | `CUBIE_DOCFRAME_RULES` instanziiert alle 4 Regeln mit `severity="error"`. | Pauschale globale Konfiguration ohne Preset-Differenzierung. |
| `doc_frame.py:100-120` | `DocFrame.check(target, pattern, rules, excludes, reporter)` übergibt `CUBIE_DOCFRAME_RULES if rules is None else rules` direkt an `FileCheckRunner`. | `FileCheckRunner` ruft `RuleRegistry` auf; flacht Sequenzen ab und überschreibt bei gleicher `rule_id` ohne Merge-Hook! |
| `presets.py:31-51, 138-166` | `FramePattern(id, head, foot, router)` definiert die Zonen-Blöcke; `CUBIE_DOC_FRAME_1..3` nutzen alle `foot=STD_FOOTER_BLOCKS`. | `FramePattern` ist rein strukturell (Rendering) und enthält keine Regel- oder `severity`-Logik (gute Trennung). |
| `__init__.py` & `services/__init__.py` | Re-exportieren `CUBIE_DOCFRAME_RULES` sowie die 4 Regelklassen und ihre `*Rule`-Aliase. | Neue öffentliche Interfaces müssen hier ebenfalls sauber exportiert werden. |

### 1.2 `DocEnsurance`-Regeln & Interface-Symmetrie (`src/qb_cubie/core/services/doc_ensurance/`)

| Fundstelle | Beobachteter Ist-Zustand (`Ist`) | Symmetrie-Befund (`Ist` vs. `Soll`) |
| :--- | :--- | :--- |
| `doc_rules.py:23-180` | Vier gefrorene Dataclass-Regeln (`NoOutput`, `HighComplexity`, `LargeOutput`, `RawTraceback`) mit `severity` (`validate_severity`), `rule_id`, `check()` und `CUBIE_DOC_RULES` (`Final[tuple[DocRuleProtocol, ...]]`). | Ähnliche Struktur wie `doc_frame_rules.py`, aber ohne eigenes Regel-Profil-/Preset-Interface. |
| `doc_ensurance.py:134, 146-158` | `DocEnsurance._build_rules()` nutzt `RuleRegistry` mit `_merge_doc_rule`, wodurch `DocLinterRule` zusammengeführt und andere Regeln per `rule_id` überschrieben werden. | `DocFrame.check()` nutzt `FileCheckRunner` ohne benutzerdefinierten `merge`-Hook; bei zwei Regeln mit gleicher `rule_id` für verschiedene Presets würde die zweite die erste still überschreiben! |
| `tests/test_doc_ensurance.py:18-24` | Übergibt `pattern=CUBIE_DOC_STYLE, rules=CUBIE_DOC_RULES, excludes=DOC_EXCLUDES`. | Symmetrisch zu `tests/test_doc_frame.py`. |

### 1.3 Aufrufer- & Test-Inventar (`Q_Ist` vs. `Q_Soll`)

| Datei | Nutzung / Kopplung (`Ist`) | Migrations-/Prüfbedarf |
| :--- | :--- | :--- |
| `tests/test_doc_frame.py:14-24` | Übergibt global `pattern=(CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3)` und `rules=CUBIE_DOCFRAME_RULES`. | Soll künftig granulare, pro Rahmen-Preset konfigurierte Regeln übergeben. |
| `tests/test_doc_ensurance.py:18-24` | Übergibt `rules=CUBIE_DOC_RULES`. | Interface-Parität zu `test_doc_frame.py` herstellen / verifizieren. |
| `tests/tests_core/tests_service_core/test_rules_and_docframe.py:476-655` | Testet `DocFrame.check()` (Single-Parse M3, Subprozess-Isolation M4 ohne `doc_ensurance`, Dummy-Methoden-Freiheit, Span-Kaskaden, `DocEnsurance`-Brücke mit `CUBIE_DOCFRAME_RULES`). | Bestehende Verträge & `CUBIE_DOCFRAME_RULES`-Abwärtskompatibilität müssen grün bleiben. |
| `tests/tests_core/tests_services/tests_doc_frame/test_docframe_rules_and_guards.py` | Testet `CUBIE_DOCFRAME_RULES` in `DocEnsurance` (`DOCFRAME-MISSING`, `DOCFRAME-OUTDATED`, `DOCFRAME-BROKEN-ROUTE`, `DOCFRAME-PROVENANCE-INCOMPLETE`, `STATE-GUARD`s). | Abwärtskompatibilität für `CUBIE_DOCFRAME_RULES` sicherstellen. |

---

## 2. Hypothesen & Evidenzlücken

* **Hypothese 1 (Semantik `foot`-Link-Liste vs. `zone="foot"`):** In `DocFrame` besteht eine fehlende Link-Liste in der `foot`-Zone darin, dass entweder eine `zone="foot"` im Dokument gänzlich fehlt oder deren Inhalt keine Standard-Markdown-Links (`[...](...)`) enthält. Für `CUBIE_DOC_FRAME_1` muss beides ein harter `error` bleiben; für `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` soll eine fehlende Link-Liste in `foot` auf `warning` abgeschwächt werden, während vorhandene kaputte Links in `foot` weiterhin durch `DocFrameBrokenRoute` (`error`) gemeldet werden.
* **Hypothese 2 (`RuleRegistry`-Kollisionsfalle):** Da `FileCheckRunner` intern `RuleRegistry` ohne `merge`-Hook nutzt (`service_core/rules.py:241`), darf eine per-Preset-Konfiguration entweder nicht einfach mehrere Instanzen mit identischer `rule_id` ungemerged übergeben, oder `DocFrame`/Profil-Regeln bündeln die Preset-Zuordnung sauber in einem eigenen Regel-/Profil-Interface.
* **Evidenzlücke:** In `docs/` wurde noch nicht für jede einzelne `CUBIE_DOC_FRAME_2`- und `CUBIE_DOC_FRAME_3`-Datei geprüft, ob aktuell alle eine `foot`-Zone mit Links besitzen (beobachtend: `test_doc_frame.py` läuft aktuell grün, daher haben alle aktiven nicht-exkludierten `docs/`-Dateien derzeit eine synchronisierte `foot`-Zone).

---

## 3. Verifikationstabelle (Ist-Baseline)

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Pre-Flight Git-Status | `git status --short && git log -n 1 --oneline` | Sauber (`5702806e Tried to prepare RUN-003.`) |
| Styleguide & Core-DocFrame-Tests | `.venv/bin/python -m pytest -q tests/test_styleguide.py tests/test_doc_frame.py tests/test_doc_ensurance.py tests/tests_core/tests_service_core/test_rules_and_docframe.py` | `29 passed in 23.11s` |
| Lint-Gate (`ruff`, `pylint`, `mypy`) | `.venv/bin/python -m pytest -q -o addopts="" tests/test_lint.py` | `9 passed in 7.54s` |
| MyPy Strict Unreachable | `MYPYPATH=src .venv/bin/mypy --warn-unreachable src/qb_cubie` | `Success: no issues found in 55 source files` |

---

## 4. Leitfragen für `NODE_HYPOTHESIS`

1. Welches SRP-Interface-Design (A vs. B vs. C) trennt **Rahmen-Spezifikation (`FramePattern`)**, **atomare Einzelregeln (mit `severity` & optionalem Preset-Filter)** und **Regel-Profile / Preset-Bindungen** am saubersten, ohne `RuleRegistry`-Überschreibungen auszulösen und ohne `doc_ensurance`-Importe in `doc_frame` einzuführen?
2. Wie wird die Abschwächung der `foot`-Zone-Link-Liste für `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` auf `"warning"` (bei Beibehaltung von `"error"` für `CUBIE_DOC_FRAME_1` und `"error"` für defekte Links) exakt mit `DocFrameMissing` und `DocFrameOutdated` koordiniert, damit keine Widersprüche oder Subsumtionen entstehen?
3. Wie erreichen `DocFrame` und `DocEnsurance` maximale Interface-Symmetrie bei voller Abwärtskompatibilität für `CUBIE_DOCFRAME_RULES` und `CUBIE_DOC_RULES`?

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../../../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../../GUIDE_TGD.md)  

[↦ | Service-Core | ↤](../../../services/GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../../../README.md)  
[↦ | Core-Dokumentation | ↤](../../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../../../dev/README.md)  
[↦ | Core-Internals | ↤](../../../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../../README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../../feature-drafts/virtualization/README.md)  

[↦ | Analyse: SRP-Regel-Interfaces & konfigurierbare `foot`-Zone (`DocFrame` & `DocEnsurance`) | ↤](./ANALYSIS_DOCFRAME_RULES_SRP.md)  

</div>
<!-- /qb:frame -->
