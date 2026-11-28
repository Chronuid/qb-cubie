<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Hydrogen" effort="Medium" -->
# Analyse: Drift- & Bestandsinventur für Release `v0.1.3` (`RUN-4`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Hydrogen
- **Reasoning-Effort:** Medium
- **Analysedatum:** 28. November 2026, ~05:28 (CET)
- **Synthesebasis:** `git log v0.1.2..HEAD`, `README.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md`, `pyproject.toml`, `.github/workflows/ci.yml`, `docs/**/*.md`, `src/qb_cubie/core/services/doc_frame/*`, `src/qb_cubie/core/services/doc_ensurance/*`, `tests/test_styleguide.py`, `tests/test_doc_frame.py`, `tests/test_doc_ensurance.py`
- **Stand:** qb-cubie (`v0.1.2`, Branch `main`, Commit `14bca3f0`)
- **Git-Log:** `14bca3f0` ("Tried to prepare RUN-004")

---

```text
Scope: Rein lesende Bestandsinventur (NODE_ANALYSIS) vor NODE_LIVING_DOCS für RUN-4 (`release-0-1-3-docs`).
Keine Änderungen an `src/` oder `tests/`.
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **`[ABWEICHUNG]` Veraltete `pytest`-Kommandos & Gate-Beschreibungen in Einstiegs- und Dev-Docs:** `README.md` (L182), `docs/dev/README.md` (L154) und `docs/dev/DEV-GUIDE_Release-Preparation.md` (L213) verweisen für `DocEnsurance`/`DocFrame` noch auf `tests/test_styleguide.py` statt auf `tests/test_doc_frame.py` und `tests/test_doc_ensurance.py`. Zudem nennt `docs/dev/Style-Guide.md` (L31–32) ein ausgesetztes 500-Zeilen-Limit, während `tests/test_styleguide.py` (L9–10) aktuell `FUNCTION_LIMIT = 12` und `MODULE_LIMIT = 777` aktiv prüft.
2. **`[ABWEICHUNG]` Fehlende Dokumentation der `RUN-3`-Interfaces in Entwickler- und Service-Referenzen:** `docs/dev/services/DEV-GUIDE_DocFrame.md` (L48, L69) führt `rule_profiles.py` (`FrameRuleProfile`, `DocFrameRuleSet`, `CUBIE_DOCFRAME_RULE_SET`) und `DocFrameFootLinks` noch nicht in der Paket-Topologie; `docs/dev/services/DEV-GUIDE_DocEnsurance.md` (L42) fehlt `DocRuleSet` unter `doc_rules.py`.
3. **`[ABWEICHUNG]` Veraltete Ticket-Terminologie in `docs/misc/runs/README.md`:** Zeile 3 spricht noch von `Minimal-Tickets (GEMINI-*.md)` statt von plattformunabhängigen `RUN-*.md`-Lauf-Dokumenten (`RUN-3` / `DEV-GUIDE_TGD-Workflow.md`).
4. **`[HINWEIS]` Reale Code-Befunde für `KNOWN_ISSUES.md` bestätigt:** `DocFrameOutdated._should_skip_span` (`doc_frame_rules.py` L309–320), `_has_missing_zones` (L37–50), die 1-Tupel-Übergabe in `DocFrame.check()`/`DocEnsurance` (`tests/test_doc_frame.py` L67, `tests/test_doc_ensurance.py` L39) sowie die ungefilterte CI-Matrix in `.github/workflows/ci.yml` (L3–62) wurden direkt am Code verifiziert.
5. **`[HINWEIS]` Nachgelagerte Abschluss-Hygiene (`E5a`):** `tests/GREEN_AUDIT.md` (`Status: RESOLVED` aus `RUN-3`) sowie abgeschlossene Lauf-Ordner unter `docs/misc/runs/` bleiben in `RUN-4` gemäß Schreibgrenze unberührt und werden im Abschlussbericht zur nachgelagerten Archivierung ausgewiesen.

---

## 1. Ist-Vermessung ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$)

### 1.1 Dokumentations-Drift (`README.md` & `docs/`)

| Fundstelle | Beobachteter Ist-Zustand (`Ist`) | Ziel-Zustand (`Soll`) |
| :--- | :--- | :--- |
| `README.md` L182 | Verweist für `DocEnsurance` auf `tests/test_styleguide.py` | Auf `tests/test_doc_frame.py tests/test_doc_ensurance.py` aktualisieren |
| `docs/dev/README.md` L154 | Verweist unter *Pflege dieses Routing-Dokuments* auf `tests/test_styleguide.py` | Auf `tests/test_doc_frame.py tests/test_doc_ensurance.py` aktualisieren |
| `docs/dev/Style-Guide.md` L31–32 | Nennt `500 physische Modulzeilen (vorübergehend ausgesetzt)` | Aktiven Stand in `tests/test_styleguide.py` (`MODULE_LIMIT = 777`, `FUNCTION_LIMIT = 12` aktiv; `500` als Ziel-/Service-Richtwert) präzisieren |
| `docs/dev/DEV-GUIDE_Release-Preparation.md` L213 | Ordnet `test_docs_code_examples` noch `tests/test_styleguide.py` zu | Korrekt `tests/test_doc_frame.py` & `tests/test_doc_ensurance.py` nennen |
| `docs/dev/services/DEV-GUIDE_DocFrame.md` L48, L69 | `rule_profiles.py` (`FrameRuleProfile`, `DocFrameRuleSet`, `CUBIE_DOCFRAME_RULE_SET`) und `DocFrameFootLinks` fehlen in der Modultabelle | Um `rule_profiles.py` und `DocFrameFootLinks` ergänzen |
| `docs/dev/services/DEV-GUIDE_DocEnsurance.md` L42 | `DocRuleSet` fehlt in der `doc_rules.py`-Tabellenzeile | Um `DocRuleSet` ergänzen |
| `docs/misc/runs/README.md` L3 | Nennt `GEMINI-*.md` | Auf plattformunabhängige `RUN-*.md`-Dokumente aktualisieren |

### 1.2 Evidenzlücken

- `pyproject.toml` steht aktuell weiterhin auf `version = "0.1.2"` (gemäß Schreibgrenze in `RUN-4` unverändert); daher bleibt die aktive Versionsreferenz `Cubie 0.1.2` in `docs/core/GUIDE_Contract-Semantics.md` (L8) konsistent zum Paketstand, bis der eigentliche Versions-Bump erfolgt.

---

## 2. Verifikation der Baseline

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Git-Historie seit `v0.1.2` | `git log v0.1.2..HEAD --oneline` | `9` Commits (`dad64a5c` bis `14bca3f0`) |
| Doku-Test-Gates (Baseline) | `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` | `2 passed in 21.16s` (`Exit-Code 0`) |

---

## 3. Übergabe an `NODE_LIVING_DOCS`

1. Neue Bugs `[BUG-008]` und `[BUG-009]` im Format von `DEV-GUIDE_Write-down-the-bugs.md` in `KNOWN_ISSUES.md` eintragen.
2. Alle identifizierten Drift-Stellen in `README.md` und `docs/` synchronisieren.
3. Abschnitt `## [0.1.3]` in `CHANGELOG.md` ergänzen.
4. `qb-cubie docframe update` idempotent über `docs/` und den Analysebericht ausführen und alle Doku-Gates verifizieren.

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

[↦ | Analyse: Drift- & Bestandsinventur für Release `v0.1.3` (`RUN-4`) | ↤](./ANALYSIS_RELEASE_0_1_3_DOCS.md)  

</div>
<!-- /qb:frame -->
