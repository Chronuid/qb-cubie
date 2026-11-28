<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Hydrogen" effort="Medium" -->
# Hypothese: SRP-Regel-Interfaces & konfigurierbare `foot`-Zone (`DocFrame` & `DocEnsurance`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Hydrogen
- **Reasoning-Effort:** Medium
- **Analysedatum:** 28. November 2026, ~04:58 (CET)
- **Synthesebasis:** `docs/misc/runs/docframe-rules-srp/ANALYSIS_DOCFRAME_RULES_SRP.md`, `src/qb_cubie/core/services/doc_frame/*`, `src/qb_cubie/core/services/doc_ensurance/*`, `src/qb_cubie/core/service_core/rules.py`
- **Stand:** qb-cubie (`v0.1.2`, Branch `main`, Commit `5702806e`)
- **Git-Log:** `5702806e` ("Tried to prepare RUN-003.")

---

```text
Modus: Modus A (Pre-Red-Entwurf) für RUN-3 (`docframe-rules-srp`).
Scope: Rein dokumentarischer Entwurf & Vier-Säulen-Meta-QA; 0 Änderungen an `src/`, `tests/` oder `docs/`.
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **Empfohlenes Makro-Konzept (Option B — Explizite SRP-Interfaces & Profil-Container):** Trennung in **Rahmen-Spezifikation** (`FramePattern`), **atomare Einzelregeln** (inkl. neuer Regel `DocFrameFootLinks` / `DOCFRAME-FOOT-LINKS`) und **Regel-Bindung/Profile** (`FrameRuleProfile`, `DocFrameRuleSet` in `doc_frame`; symmetrisches `DocRuleSet` in `doc_ensurance`).
2. **Semantik der `foot`-Zone:** `DocFrameFootLinks` prüft, ob `zone="foot"` mindestens einen Standard-Markdown-Link (`[...](...)`) enthält. Für `CUBIE_DOC_FRAME_1` bleibt `severity="error"`; für `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` wird `severity="warning"` konfiguriert (und `DocFrameOutdated` unterdrückt keinen `error`, solange eine `foot`-Zone ohne Links bewusst als Warnungs-Fall toleriert wird). Vorhandene defekte Links werden unabhängig davon durch `DocFrameBrokenRoute` (`error`) gemeldet.
3. **Kollisionsfreiheit in `RuleRegistry`:** Jedes `FrameRuleProfile` trägt eine eindeutige `rule_id` (`f"DOCFRAME-PROFILE:{pattern_id}"`), sodass mehrere Presets mit unterschiedlichen `DocFrameFootLinks(severity=...)`-Instanzen koexistieren können, ohne dass `FileCheckRunner` / `RuleRegistry` sie still überschreibt.

---

## 1. Konkurrierende Makro-Konzepte (A vs. B vs. C)

| Kriterium | Option A: `frame_ids`-Filter direkt auf Einzelregeln + Merge-Hook | Option B: Explizite SRP-Profile (`FrameRuleProfile`, `DocFrameRuleSet`, `DocRuleSet`) *(Empfohlen)* | Option C: Umbau von `service_core.RuleRegistry` auf Composite-Keys |
| :--- | :--- | :--- | :--- |
| **SRP-Reinheit** | Vermischt Prüfverantwortung mit Preset-Routing in jeder Regelklasse | Strikt getrennt: Spezifikation (`FramePattern`), Prüfung (Einzelregel), Bindung (`FrameRuleProfile`) | Sauber in `RuleRegistry`, aber überdimensioniert |
| **Ergonomie in `tests/test_doc_*.py`** | Unübersichtlich (viele `frame_ids`-Tupel wiederholt) | Deklarativ, selbsterklärend pro Preset konfigurierbar | Mittel |
| **Symmetrie `DocFrame` $\leftrightarrow$ `DocEnsurance`** | Gering | Hoch (`DocFrameRuleSet` $\leftrightarrow$ `DocRuleSet`) | Hoch |
| **Eingriffsradius / Risiko** | Gering | Gering–Mittel (lokal auf `doc_frame` & `doc_ensurance`) | `[RISIKO]` Hoch (ändert `service_core` für alle Services) |
| **Gate-Kompatibilität (`FUNCTION_LIMIT = 12`)** | Mittel | Hoch (kleine, einzeilig dokumentierte Dataclasses) | Mittel |

---

## 2. Falsifizierbare Kernhypothesen

### Hypothese H1: Granulare Per-Preset-Bindung über `FrameRuleProfile` & `DocFrameRuleSet`
* **Ist-Befund:** `CUBIE_DOCFRAME_RULES` ist ein flaches 4er-Tupel ohne Preset-Differenzierung; `FileCheckRunner` überschreibt Regeln mit identischer `rule_id`.
* **Soll-Skizze:** `FrameRuleProfile(pattern, rules)` bindet ein `FramePattern` (oder dessen `id`) an eine geordnete Regel-Sequenz und implementiert `WorkspaceCheckRuleProtocol` mit `rule_id = f"DOCFRAME-PROFILE:{self.pattern_id}"`. `DocFrameRuleSet(profiles)` bündelt mehrere Profile.
* **Gegenhypothese / Risiko:** Wenn ein Dokument eine `frame_id` nutzt, für die kein Profil existiert, könnte es still ungeprüft bleiben (*Vacuous Pass*).
* **Falsifikationskriterium:** Ein Testlauf mit einem Dokument ohne passendes Profil oder mit leerem `DocFrameRuleSet` muss entweder durch `STATE-GUARD` (`ValueError`) abgewiesen werden oder bei fehlender `head`-Zone weiterhin `DOCFRAME-MISSING` auslösen.

### Hypothese H2: Atomare `DocFrameFootLinks`-Regel (`error` vs. `warning`) ohne `DocFrameOutdated`-Konflikt
* **Ist-Befund:** `DocFrameOutdated` meldet jeden `foot`-Inhalt als `error`, der vom gerenderten `STD_FOOTER_BLOCKS` abweicht; eine reine Link-Listen-Regel fehlt.
* **Soll-Skizze:** `DocFrameFootLinks(severity="error")` (`rule_id = "DOCFRAME-FOOT-LINKS"`) prüft, ob in `zone="foot"` mindestens ein Standard-Markdown-Link (`[...](...)`) vorhanden ist. Ist `DocFrameFootLinks` im Profil mit `severity="warning"` (für `FRAME_2`/`FRAME_3`) aktiv und `zone="foot"` hat keine Links, meldet `DocFrameFootLinks` eine `warning` und `DocFrameOutdated` überspringt die `foot`-Sync-Prüfung auf diesem Span (oder wird für `foot` ohne Links nicht als `error` gewertet), während `DocFrameBrokenRoute` bestehende defekte Links weiterhin als `error` meldet.
* **Gegenhypothese / Risiko:** Wenn `DocFrameOutdated` weiterhin `error` auf einer leeren `foot`-Zone in `FRAME_2`/`FRAME_3` feuert, bleibt `DocFrame.check()` rot statt nur zu warnen.
* **Falsifikationskriterium:** Ein `CUBIE_DOC_FRAME_2`- oder `CUBIE_DOC_FRAME_3`-Dokument mit gültigem `head` (und `router` bei `FRAME_3`) sowie leerer `foot`-Zone muss bei `DocFrame.check()` `passed == True` und exakt eine `warning` (`DOCFRAME-FOOT-LINKS`) liefern; mit einem defekten Link in `foot` muss `passed == False` (`DOCFRAME-BROKEN-ROUTE`, `error`) auftreten.

### Hypothese H3: Interface-Symmetrie in `DocEnsurance` (`DocRuleSet`)
* **Ist-Befund:** `tests/test_doc_ensurance.py` übergibt das globale Tupel `CUBIE_DOC_RULES`.
* **Soll-Skizze:** `DocRuleSet(rules=...)` in `doc_ensurance/doc_rules.py` kapselt validierte `DocRuleProtocol`-/`WorkspaceCheckRuleProtocol`-Regeln als explizites Profil-Interface, das `DocEnsurance` nativ akzeptiert und in `tests/test_doc_ensurance.py` analog zu `DocFrameRuleSet` verwendet wird (`CUBIE_DOC_RULES` bleibt abwärtskompatibel erhalten).
* **Gegenhypothese / Risiko:** `DocEnsurance._build_rules()` könnte `DocRuleSet` als unbekannten Typ per `STATE-GUARD` ablehnen oder stille Doppelregeln erzeugen.
* **Falsifikationskriterium:** `DocEnsurance(rules=DocRuleSet(CUBIE_DOC_RULES))` verhält sich identisch zu `DocEnsurance(rules=CUBIE_DOC_RULES)` und weist ungültige Eingaben (`bool`, leere Sequenz, Nicht-Regel-Objekte) per `STATE-GUARD` ab.

---

## 3. Vier-Säulen-Meta-QA & Mutanten-Matrix

* **Säule 1 (Subsumtion):** `DocFrameMissing` (prüft fehlende Zonen-Tags) subsumiert nicht `DocFrameFootLinks` (prüft Link-Liste innerhalb `zone="foot"`), und `DocFrameBrokenRoute` (prüft Ziel-Existenz vorhandener Links) subsumiert nicht `DocFrameFootLinks` (prüft Vorhandensein mindestens eines Links).
* **Säule 2 (Tautologien):** Keine `or`-Tautologien; jede Regel prüft eine atomare Bedingung (fehlender Link vs. kaputtes Ziel vs. fehlende Zone).
* **Säule 3 (*Vacuous Passes*):** Leere `rules=()` in `FrameRuleProfile`, leere `profiles=()` in `DocFrameRuleSet` und leere `rules=()` in `DocRuleSet` werden per `ValueError("STATE-GUARD: ...")` abgewiesen; `bool` statt String/Objekt wird per `TypeError("STATE-GUARD: ...")` abgewiesen.
* **Säule 4 (Mutanten-Überlebens-Matrix):**

| Mutant | Defekt-Szenario | Pflicht-Test, der deterministisch fehlschlagen muss |
| :--- | :--- | :--- |
| **M1** | `CUBIE_DOC_FRAME_1` verliert versehentlich den `error`-Schutz bei fehlenden `foot`-Links | `test_ebt_docframe_foot_links_strict_error_on_frame_1` (`passed is False`, `severity == "error"`) |
| **M2** | `CUBIE_DOC_FRAME_2` oder `CUBIE_DOC_FRAME_3` wirft weiterhin `error` ohne `foot`-Links | `test_ebt_docframe_foot_links_warning_on_frame_2_and_3` (`passed is True`, `severity == "warning"`) |
| **M3** | Defekte Links in `foot` bei `FRAME_2`/`FRAME_3` werden durch die Abschwächung still verschluckt | `test_ebt_docframe_broken_route_still_errors_on_frame_2_and_3` (`DOCFRAME-BROKEN-ROUTE`, `error`) |
| **M4** | `RuleRegistry` überschreibt zwei `FrameRuleProfile`s mit unterschiedlichen Presets | `test_ebt_docframe_rule_set_preserves_distinct_preset_severities` |
| **M5** | `STATE-GUARD` akzeptiert `bool`, leere Profile oder ungültige `severity` | `test_ebt_docframe_srp_rule_state_guards` |
| **M6** | `DocFrame.check()` importiert `doc_ensurance` (Isolationsbruch) | Bestehender Subprozess-Test `test_doc_frame_check_runs_with_doc_ensurance_blocked` |

---

## 4. Entscheidungsmatrix (`E1..E4`) für *Consent-by-Exception*

| ID | Fragestellung | **Standard-Empfehlung** | Auswirkung bei Abweichung |
| :--- | :--- | :--- | :--- |
| **E1** | Name und Schnittstelle der neuen `foot`-Link-Regel | **`DocFrameFootLinks`** (`rule_id="DOCFRAME-FOOT-LINKS"`, Alias `DocFrameFootLinksRule`, `severity="error"`) | Andere Benennung müsste in Exports und Tests angepasst werden |
| **E2** | Preset-Bindungs-Interfaces in `doc_frame` | **`FrameRuleProfile(pattern, rules)`** + **`DocFrameRuleSet(profiles)`** + Default **`CUBIE_DOCFRAME_RULE_SET`** (`CUBIE_DOCFRAME_RULES` bleibt erhalten) | Ohne `FrameRuleProfile` drohen `RuleRegistry`-Kollisionen |
| **E3** | Verhalten von `DocFrameOutdated` bei `FRAME_2`/`FRAME_3` ohne `foot`-Links | Wenn `foot` keine Links hat und `DocFrameFootLinks` mit `severity="warning"` konfiguriert ist, unterdrückt das Profil `DOCFRAME-OUTDATED` auf diesem `foot`-Span (oder `DocFrameOutdated(allow_empty_foot=True)`), sodass nur die `warning` erscheint | Sonst schlägt `DocFrame.check()` weiter mit `DOCFRAME-OUTDATED` (`error`) fehl |
| **E4** | Symmetrie-Interface in `doc_ensurance` | **`DocRuleSet(rules)`** in `doc_ensurance/doc_rules.py` (re-exportiert über `doc_ensurance` & `services`), genutzt in `tests/test_doc_ensurance.py` | Geringere Interface-Symmetrie zwischen beiden Services |

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
[↦ | Hypothese: SRP-Regel-Interfaces & konfigurierbare `foot`-Zone (`DocFrame` & `DocEnsurance`) | ↤](./HYPOTHESIS_DOCFRAME_RULES_SRP.md)  

</div>
<!-- /qb:frame -->
