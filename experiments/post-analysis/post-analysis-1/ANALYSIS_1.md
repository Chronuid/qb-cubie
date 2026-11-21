<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Hydrogen" effort="XHigh" -->
# Post-Hoc Audit 1

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Hydrogen
- **Reasoning-Effort:** XHigh
- **Analysedatum:** 17. November 2026, ~ 07:15 (CET)
- **Synthesebasis:** `../../testguided-study`

---

---
<!-- /qb:frame -->

# Post-Studien-Audit: Dimension B – Forschungsmethodik, Praktiken und Dynamiken in `../../testguided-study`

## 1. Zielsetzung, Abgrenzung und empirische Gesamtdatenlage

Dieser Audit untersucht wertungsfrei die Forschungsansätze, die agilen Entwicklungspraktiken, die epistemischen Kontrollmechanismen und die strukturellen Dynamiken in [`../../testguided-study`](../../testguided-study). Der Schwerpunkt liegt auf **Dimension B („Die Forschung selbst“)** und ihren fünf Sub-Dimensionalitäten **B.1 bis B.5**, einschließlich der aus technischen Freeze-Gründen nach [`../../tests/testguided_study_design`](../../tests/testguided_study_design) ausgelagerten Design-Testsuite. Die Dimensionen **A** (`runs/` und `local/`) sowie **C** (synthetische Paper-Erzeugung und Gutachten) werden als empirische Synthesebasis bzw. Verwertungsschnittstelle von Dimension B eingeordnet und gegengeprüft.

### 1.1 Makro-Einordnung der drei Dimensionalitäten (`A`, `B`, `C`)

| Dimensionalität | Gegenstand & Ablageort | Empirischer Umfang (direkt geprüft) | Kernfunktion im Gesamtprozess |
| :--- | :--- | :--- | :--- |
| **A: Experimente (Gemma-4-Agent)** | `../../testguided-study/runs` (13 Verzeichnisse) und `local/` (11 Vor-/Smoke-Ordner) | 7 abgeschlossene Single-Agent-Archive (42 Läufe, v1–v5) + 1 `--prepare-only`-Archiv (`20261111-180104`); 5 Multi-Agent-Archive (17 ausgeführte von 30 geplanten Läufen, v6–v9); alle mit `gemma4:12b`, Seed 42 auf denselben 3 Aufgaben (`fastapi_9425`, `requests_6589`, `rich_3278`); **0 Läufe** in `phase = "measurement"` | Erzeugung der unveränderlichen Lauf-, Schritt-, Token-, Patch- und Evaluationsartefakte unter `runs/`. |
| **B: Forschung selbst (Audit-Fokus)** | Flach in `../../testguided-study` sowie `testguided_study/`, `tests/`, `guides/` und `experiments/tests/testguided_study_design/` | **B.1:** 7 Analyseberichte (1.577 Z.) + 5 Protokoll-/Setup-Texte (1.223 Z.)<br>**B.2:** 5 Hypothesenpapiere (722 Z.)<br>**B.3:** 7 Design-Dokumente (1.957 Z.)<br>**B.4:** 3 Implementierungsberichte (333 Z.) + 8 `*_CASES.md`-Spezifikationen (1.311 Z.)<br>**B.5:** 35 Quellmodule (7.361 LOC) + 50 Testdateien (8.033 LOC, 768 Nodes) | Iterative Wissenssynthese: Rohdaten prüfen (B.1) → Ursachen hypothetisieren (B.2) → Soll-Architektur spezifizieren (B.3) → EBT-Abnahmen ableiten (B.4) → lauffähigen Studien- und Testcode umsetzen (B.5). |
| **C: Paper-Synthese & Begutachtung** | `PAPER.md` (803 Z.), `g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md` (134 Z.), 5 PDF-Revisionen (`...Analysis.pdf` bis `...-4.pdf`), `KRITISCHE-ANALYSE-PAPER-SUBMISSION.md`, `GUTACHTEN-PAPER-SUBMISSION-1/2/4.md`, `STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md` | 2 Hauptmanuskript-Linien (11.11. v1–v5 vs. 12.11. v1–v9), 5 PDF-Stände, 5 kritische/evaluative Prüfberichte gegen `Developer-Agent-Paper.md` | Verdichtung und Wettbewerbsaufbereitung der Befunde aus A und B inklusive mehrstufiger KI-gestützter Eigenbegutachtung. |

### 1.2 Empirische Referenzdaten aus Dimension A (Grundlage zur Überprüfung von B.1)

Zur Faktenprüfung der Dokumente in Dimension B wurden alle 13 Archive unter `runs/` direkt über `configured.toml`, `launch.json`, `failure.json`, `report.json`, `agent.json`, `team.json`, `actions/*.json`, `steps/*` und `evaluation/result.json` ausgewertet:

| Run-ID | Profil / Version | Modus / Phase | Geplant / Ausgef. | `pytest` gelöst | `cubie` gelöst | Dominantes Ende & direkte Rohdatenbeobachtung |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `20261111-132401` | v1 (`think=false`, 600 s, 24 Calls, 16k) | `pilot` / `pilot` | 6 / 6 | 0 / 3 | 0 / 3 | 5× `model_budget`, 1× `invalid_output`; 0 Bytes `full.patch` in allen 6 Läufen |
| `20261111-160158` | v1 (`think=false`, 600 s, 24 Calls, 16k) | `pilot` / `pilot` | 6 / 6 | 0 / 3 | 0 / 3 | 5× `model_budget`, 1× `invalid_output`; 0 Bytes `full.patch` |
| `20261111-163110` | v2 (`think=false`, 600 s, 24 Calls, 16k) | `pilot` / `pilot` | 6 / 6 | **1 / 3** | 0 / 3 | `0003` (`requests_6589`/pytest) `submitted` & gelöst; 3× `model_budget`, 2× `stalled` |
| `20261111-171515` | v3 (`think=false`, 600 s, 24 Calls, 16k) | `pilot` / `pilot` | 6 / 6 | 0 / 3 | 0 / 3 | 3× `stalled`, 2× `context_budget`, 1× `invalid_output`; 0 EBT ausgeführt |
| `20261111-180104` | v3 (`think=false`, 900 s, unlim., 32k) | `pilot` / `pilot` | 6 / 0 | — | — | `launch.json`: `"prepare_only": true`; kein Agentenlauf gestartet |
| `20261111-180702` | v3 rev. (`think=false`, 900 s, unlim., 32k) | `pilot` / `pilot` | 6 / 6 | 0 / 3 | **1 / 3** *(1 unavail.)* | `0001` (`fastapi_9425`/cubie) gelöst (6 EBT ausgeführt/eval., 5 passed); `0004` (`requests_6589`/cubie) 3 EBT, aber `IndentationError` (pytest Exitcode 4 → `resolved: null`) |
| `20261111-192412` | v4 (`think=false`, 900 s, unlim., 32k) | `pilot` / `pilot` | 6 / 6 | **1 / 3** | 0 / 3 | `0002` (`fastapi_9425`/pytest) `stalled`, aber privat gelöst; 5× `stalled`, 1× `invalid_output` |
| `20261111-200641` | v5 (`think=true`, 900 s, unlim., 32k) | `pilot` / `pilot` | 6 / 6 | 0 / 3 | 0 / 3 | 5× `invalid_output`, 1× `agent_timeout`; 11/67 Calls `done_reason="length"` (90.112 von 103.235 Out-Tokens = 87,3 %) |
| `20261112-002038` | v6 (`think=false`, temp 0.15, 900 s, 48/96 Calls) | `development` | 6 / 6 | 0 / 3 | 0 / 3 | 66 Req / 66 Resp / 65 Tool-Steps (`53 search_content`, `12 read_file`); 6× `stagnation` in `analysis/orient` |
| `20261112-013246` | v7 (`think=false`, temp 0.15, 900 s, 48/96 Calls) | `development` | 6 / 3 | 0 / 3 | 0 / 0 | Abbruch vor `0004` (`ValueError`: Code nach Freeze geändert); `0001–0003` erreichten QA nach `orient`-Limit (`6` Calls), alle 3 `create_case` und 1 `collect_tests` `rejected` |
| `20261112-015457` | v7 (`think=false`, temp 0.15, 1800 s, unlim.) | `development` | 6 / 1 | 0 / 1 | 0 / 0 | `0001` manuell abgebrochen: 81 Req / 80 Resp / 80 Tool-Steps (`38 find_paths`, `38 read_file`, `4 search_content`), 100 % `analysis/orient` |
| `20261112-030527` | v8 (`think=false`, temp 0.15, 1800 s, unlim.) | `development` | 6 / 1 | 0 / 0 | 0 / 1 | `0001` manuell abgebrochen (`job-20`): 64 Req / 63 Resp / 63 Tool-Steps (61 `analysis`, 2 `qa`/`ask_analysis`), 38× `cursor_error` |
| `20261112-035522` | v9 (`think=false`, temp 0.15, 1800 s, unlim.) | `development` | 6 / 6 | 0 / 3 | 0 / 3 | 1.184 Req / 1.184 Resp / 1.179 Tool-Steps; 974 Duplikate (82,6 %); 0× `finish`; 6× `budget_exhausted`; 6.980.998 In / 44.845 Out-Tokens |

---

## 2. Zeitliche Entwicklungsdynamik und Akteursarchitektur in Dimension B

Die Git-Historie (`eda23718` am 11.11.2026 um 16:05 Uhr bis `32434293` am 13.11.2026 um 23:15 Uhr MEZ) belegt in Verbindung mit den Zeitstempeln in `runs/` eine hochgradig komprimierte, zweiphasige Sprint-Dynamik:

### 2.1 Chronologische Verdichtung (18-Stunden-Fenster)

1. **Tag 1 – Single-Agent-Iterationen v1 bis v5 (11.11.2026, ~13:24 bis 21:55 Uhr MEZ):**
   Zwischen dem Start von `20261111-132401` und dem Commit `5e50d22f` („Pre-Conclusion“, 21:54:53 Uhr) entstanden in rund 8,5 Stunden sieben ausgeführte Pilotläufe über fünf Designgenerationen (`v1` → `v2` → `v3` → `v3 rev.` → `v4` → `v5`), die gesamte Studieninfrastruktur samt Zulassung (`PROTOKOLL.md`, `DATEN.md`, `KANDIDATEN.md`, `VALIDIERUNG.md`), mehrere Pilotanalysen, zwei parallele Ursachenanalysen und ein 803 Zeilen umfassender vorläufiger Gesamtbericht ([PAPER.md](../../testguided-study/PAPER.md)).
2. **Nacht auf Tag 2 – Multi-Agent-Iterationen v6 bis v9 (12.11.2026, ~00:20 bis 14:00 Uhr MEZ):**
   Innerhalb von rund 3,5 Stunden vor dem Start von `v9` (`03:55:22 Uhr`) wurden vier komplette Multi-Agenten-Generationen entworfen, in Hunderte deterministische Akzeptanztests übersetzt, implementiert und im Live-Betrieb auf `gemma4:12b` geprüft:
   - `00:20–00:44`: v6-Lauf (`20261112-002038`) → `01:10:19` Commit `8bd7f57b` (`AGENTENDESIGN-V6.md` **und** `AGENTENDESIGN-V7.md`, beide Pilotanalysen, `HYPOTHESIS-V6`, `team.py`).
   - `01:32–02:28`: v7-Läufe (`013246` nach Quellenänderung abgebrochen; `015457` nach Live-Dump-Analyse bei Call 74 manuell abgebrochen) → `02:35:20` Commit `5976fc90` (`IMPLEMENTIERUNG-V7.md`, `HYPOTHESIS-V7`, `team_v7.py`).
   - `03:05–03:25`: v8-Lauf (`030527` nach Live-Analyse von `job-12`/`job-20` manuell abgebrochen) → `03:34:58` Commit `10169e57` (`AGENTENDESIGN-V8.md`, `IMPLEMENTIERUNG-V8.md`, `HYPOTHESIS-V8`, `team_v8.py`).
   - `03:55–07:01`: v9-Lauf (`20261112-035522`, 3h 06m Laufzeit) → `14:00:01` Commit `08792e32` (`AGENTENDESIGN-V9.md`, `IMPLEMENTIERUNG-V9.md`, `PILOTANALYSE-V9`, `ANALYSE-GENERATIONEN-V6-V9.md`, `team_v9.py` sowie erste Paper-PDFs und Gutachten).

### 2.2 Arbeitsteilige Multi-KI- und HITL-Rollenverteilung

Dimension B wurde nicht von einem einzelnen Modell erzeugt, sondern durch ein spezialisiertes Gefüge aus menschlicher Steuerung und drei verschiedenen KI-Systemen (soweit explizit im Header ausgewiesen bzw. aus der konsistenten Dokumenten- und Zitierkette nachvollziehbar):

- **Menschlicher Projektverantwortlicher (`Chronuid`):** Definierte die Ausgangsfragestellung, brachte eine ursprüngliche „25-Zeilen-Skizze“ der Drei-Agenten-Idee ein (belegt in `HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md:12` und `AGENTENDESIGN-V8.md:5`), führte die Live-Läufe auf lokaler Hardware aus, übermittelte Monitor-Live-Dumps (`Call 74`, `job-12`/`job-20`) ad hoc an die Beratungs-KI, brach stagnierende Läufe manuell ab und steuerte Prioritätswechsel (z. B. Entfernung der Phasengrenzen zwischen `v7-1` und `v7-2`, Commit `af62a3bb`).
- **Codex (`GPT-6.1-Sol`, Reasoning: High):** Explizit ausgewiesen in [`URSACHENANALYSE-CODEX-20261111.md`](../../testguided-study/URSACHENANALYSE-CODEX-20261111.md) und [`PILOTANALYSE-V6-20261112-002038-CODEX.md`](../../testguided-study/PILOTANALYSE-V6-20261112-002038-CODEX.md). Die konsistente Sprach-, Tabellen-, Vertrags- und Verweisstruktur (`D01–D08`, `V6-A01..A18`, `V7-A01..A14`, `V9-A01..A14`, durchgehende Rückverweise auf „Codex-Nachrechnung“ bzw. Abgrenzungen gegen Antigravity/Gemini-Dokumente) ordnet die gesamte Design-, QA- und Implementierungslinie (`PROTOKOLL.md`, `AGENTENDESIGN*.md`, `IMPLEMENTIERUNG-*.md`, `*_CASES.md`, `testguided_study/*.py`, `../../../tests`) demselben technischen Hauptautor zu *(als strukturell abgeleitete Zuordnung für die unsignierten Dateien kenntlich gemacht)*.
- **Antigravity (`Gemini-3.8-Flash`):** Explizit signiert als Autor von [`HYPOTHESEN-URSACHENANALYSE-20261111.md`](../../testguided-study/HYPOTHESEN-URSACHENANALYSE-20261111.md), [`PILOTANALYSE-20261112-002038.md`](../../testguided-study/PILOTANALYSE-20261112-002038.md), [`PILOTANALYSE-V9-20261112-035522.md`](../../testguided-study/PILOTANALYSE-V9-20261112-035522.md) und [`ANALYSE-GENERATIONEN-V6-V9.md`](../../testguided-study/ANALYSE-GENERATIONEN-V6-V9.md) in Dimension B sowie sämtlicher fünf Paper-Prüfgutachten in Dimension C.
- **Gemini-App (`Gemini-4-Argon`, Reasoning: High):** Explizit signiert in [`HYPOTHESIS-V6-GEMINI-ARGON-HIGH.md`](../../testguided-study/HYPOTHESIS-V6-GEMINI-ARGON-HIGH.md), [`HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md`](../../testguided-study/HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md) und [`HYPOTHESIS-V8-GEMINI-ARGON-HIGH.md`](../../testguided-study/HYPOTHESIS-V8-GEMINI-ARGON-HIGH.md) als konversationeller Live-Kritiker und Richtungsgeber in B.2 sowie als Paper-Synthetisierer in Dimension C.

---

## 3. Empirischer Audit der Sub-Dimensionalitäten B.1 bis B.5

### 3.1 B.1: KI-generierte Datenanalyse & deskriptive Audits

**Dokumentenbestand:** [`TECHNIKANALYSE-20261111-171515.md`](../../testguided-study/TECHNIKANALYSE-20261111-171515.md) (255 Z.), [`PILOTANALYSE-20261111.md`](../../testguided-study/PILOTANALYSE-20261111.md) (349 Z.), [`PILOTANALYSE-20261111-192412.md`](../../testguided-study/PILOTANALYSE-20261111-192412.md) (318 Z.), [`PILOTANALYSE-20261112-002038.md`](../../testguided-study/PILOTANALYSE-20261112-002038.md) (171 Z.), [`PILOTANALYSE-V6-20261112-002038-CODEX.md`](../../testguided-study/PILOTANALYSE-V6-20261112-002038-CODEX.md) (136 Z.), [`PILOTANALYSE-V9-20261112-035522.md`](../../testguided-study/PILOTANALYSE-V9-20261112-035522.md) (152 Z.), [`ANALYSE-GENERATIONEN-V6-V9.md`](../../testguided-study/ANALYSE-GENERATIONEN-V6-V9.md) (196 Z.); flankiert durch das vorlaufende Methodik- und Katalog-Set [`PROTOKOLL.md`](../../testguided-study/PROTOKOLL.md) (284 Z.), [`DATEN.md`](../../testguided-study/DATEN.md) (79 Z.), [`KANDIDATEN.md`](../../testguided-study/KANDIDATEN.md) (147 Z.), [`VALIDIERUNG.md`](../../testguided-study/VALIDIERUNG.md) (68 Z.) und [`../../../README.md`](../../testguided-study/README.md) (645 Z.).

#### Beobachtete Stärken und methodische Konventionen
1. **Kryptographische Verifikation vor Dateninterpretation:** Die B.1-Berichte verifizierten systematisch SHA-256-Manifeste gegen Archivdateien und Quellcode-Freezes (`TECHNIKANALYSE`: 484 Einträge; `PILOTANALYSE-20261111`: 668 Archiv- + 53 Quelleinträge; `PILOTANALYSE-20261111-192412`: 14 Freeze- + 626 Run-Einträge).
2. **Direkte Schritt-Aggregation bei fehlenden Berichtsaggregaten:** In `20261112-035522` (`v9`) meldete `report.json` für beide Arme `measured_total_tokens: null`, weil jeweils mindestens ein Schritt per Timeout ohne `usage` abbrach und `report.py:measured()` bei jedem `None` die Gesamtsumme unterdrückt. [`PILOTANALYSE-V9-20261112-035522.md`](../../testguided-study/PILOTANALYSE-V9-20261112-035522.md) rekonstruierte die Tokenverbräuche direkt aus den 1.184 `steps/*-response.json` auf das einzelne Token genau (Summe über alle sechs Läufe verifiziert: **6.980.998 Input- / 44.845 Output-Tokens**).
3. **Konsequente Differenzierung von Erfolgsachsen:** Interne Einreichung (`submitted`), beobachtetes Testverhalten (`assertion_failure` vs. `pass`) und unabhängige private Evaluation (`resolved`) wurden in allen B.1-Texten sauber getrennt (z. B. Einstufung des privat erfolgreichen `v4`-FastAPI-Laufs `192412/0002` als fehlerhaften Testprozess wegen Überschreibens von 1.114 auf 45 Testzeilen).

#### Direkt gegen `runs/` festgestellte Diskrepanzen, Zählabweichungen und blinde Flecken

Die Nachprüfung jeder zentralen Kennzahl in B.1 gegen die Roharchive in `runs/` deckt fünf empirische Auffälligkeiten auf:

1. **Zähl- und Bezugsdifferenz im v6-Parallel-Audit (`20261112-002038`):**
   - [`PILOTANALYSE-V6-20261112-002038-CODEX.md`](../../testguided-study/PILOTANALYSE-V6-20261112-002038-CODEX.md) weist exakt die in `steps/*-tool.json` und `actions/*.json` protokollierten **53 `search_content`** und **12 `read_file`** (65 Aktionen, 66 Modellaufrufe) sowie die vollständigen privaten Testergebnisse (`1/12` Requests, `16/23` Rich) aus.
   - [`PILOTANALYSE-20261112-002038.md`](../../testguided-study/PILOTANALYSE-20261112-002038.md) (Antigravity) nennt dagegen **51 `search_content`** und **14 `read_file`** (Verzerrung um ±2 Aktionen) und berichtet als private Evaluationsergebnisse `0/1 Tests` (Requests) bzw. `0/16 Tests` (Rich), womit stillschweigend nur die `FAIL_TO_PASS`-Teilmenge statt der Gesamtzahl privater Tests (12 bzw. 23) als Nenner angegeben wird.
2. **Vermischung von abgesendeten Requests und abgeschlossenen Antworten (`ANALYSE-GENERATIONEN-V6-V9.md`):**
   In der Übersichtstabelle (Z. 36–44) zählt Antigravity bei den abgebrochenen Läufen `20261112-015457` (`v7-2`) und `20261112-030527` (`v8`) die Anzahl der `*-request.json`-Dateien als „Modellaufrufe“ (`81` bzw. `64`), obwohl durch den manuellen Abbruch jeweils der letzte Aufruf ohne `*-response.json` blieb (tatsächliche Antworten: **80** bzw. **63**; Gesamtsumme v6–v9: **1.441 Requests** gegenüber **1.439 Responses**). Diese leicht erhöhte Zahl (`1.441`) wanderte anschließend ungeprüft in Dimension C.
3. **Fehlinterpretation der QA-Aktivierung und Case-Erstellung in `v7-1` (`20261112-013246`):**
   [`ANALYSE-GENERATIONEN-V6-V9.md`](../../testguided-study/ANALYSE-GENERATIONEN-V6-V9.md) schreibt in Z. 79, `v7-1` habe „3 Testcases definiert und 1 `collect_tests` ausgeführt“, und in Z. 178, nur ein Zwangsangriff (`v8`) oder „fehlerhafte Freeze-Zustände (`v7-1`)“ hätten QA aktiviert. Die Roharchive in `runs/20261112-013246/frozen/runs/0001..0003/actions/*.json` zeigen:
   - Alle drei `create_case`-Aufrufe (`0001/0016`, `0003/0012`, `0003/0016`) sowie der einzige `collect_tests`-Aufruf (`0003/0021`) endeten mit **`status: "rejected"`**; kein einziger Case wurde erstellt oder gesammelt.
   - Die QA-Rolle wurde in `0001`–`0003` nicht durch einen fehlerhaften Freeze aktiviert, sondern regulär durch den v7-Controller nach Erreichen der Orientierungs-Phasengrenze (`6` Modellaufrufe, jeweils nachdem `finish_orientation` abgelehnt worden war). Der Freeze-Fehler (`Agent/study implementation changed since freeze`) verhinderte erst den Start von Lauf `0004`, nachdem `0001`–`0003` bereits regulär als `incomplete / suite_incomplete` beendet waren.
4. **Übersehene `scope_not_found`-Fehler und Fehlattribution der FastAPI-Latenz in `v9` (`20261112-035522`):**
   - [`PILOTANALYSE-V9-20261112-035522.md`](../../testguided-study/PILOTANALYSE-V9-20261112-035522.md) (Z. 139, 150) übernimmt pauschal `tool_errors = 0` aus `report.json:process_metrics`. Lauf `0002` weist jedoch in `steps/*-tool.json` vier und in `report.json:team_process_metrics` ebenfalls **`scope_not_found: 4`** auf (vom v9-Reporting getrennt von `tool_errors` geführt).
   - Zur niedrigen Schrittzahl bei FastAPI (`72` bzw. `79` Calls in `1.800 s` gegenüber `355`/`302` Calls bei Requests) schreibt `PILOTANALYSE-V9` (Z. 117): *„Die Inferenz auf dem lokalen Ollama-Setup benötigte dadurch ca. 20–25 Sekunden pro Aufruf.“* Die direkte Überprüfung der `agent.json`-Zeitsummen und Dateizeitstempel zeigt dagegen:
     - In Lauf `0001` (`fastapi_9425`, Cubie) summierte sich `model_seconds` auf lediglich **557,5 s** (~7,7 s pro Aufruf) und `tool_seconds` auf **128,3 s**; die gemessene Gesamtdauer betrug jedoch **1.810,6 s**.
     - Stichproben an `steps/*` (`0005`, `0020`, `0040`) belegen pro Schritt ~5,8–10,6 s für `req → resp`, ~7,7–9,9 s für `resp → tool` und konstante **~6,3–6,4 s für `tool → next_req`** (Aufbau des nächsten Prompts). Ursache dieses ~1.125 s (62 % der Gesamtzeit!) großen Zeitblocks außerhalb der Modellinferenz sind wiederholte `V9RemoteWorkspace.inventory()`-Aufrufe per Docker-`exec` (vollständiger SHA-256-Dateibaum-Scan in `_refresh()`, `_source_materials()`, `request()` und `_navigate()`), was in FastAPI rund 20× langsamer läuft als im kleinen `requests`-Baum (`tool → next_req = 0,32 s`). Dieser Infrastruktur-Engpass blieb in B.1 vollständig unentdeckt.
5. **Rollendiffusion in frühen Analysen vs. späte Ausdifferenzierung:**
   Während [`PILOTANALYSE-20261111.md`](../../testguided-study/PILOTANALYSE-20261111.md) (B.1 + v3-Zielentwurf B.3) und [`PILOTANALYSE-20261111-192412.md`](../../testguided-study/PILOTANALYSE-20261111-192412.md) (B.1 + v5-Hypothese B.2) deskriptive Analyse, Kausalhypothese und Entwurf noch in Einzeldokumenten bündelten, trennte der spätere Arbeitsablauf (ab `21:54 Uhr` und am `12.11.`) explizit zwischen reinen Ist-Audits (B.1) und spekulativen Hypothesen (B.2).

---

### 3.2 B.2: KI-generierte Hypothesen (Ist-Erklärung → Soll-Ableitung)

**Dokumentenbestand:** [`HYPOTHESEN-URSACHENANALYSE-20261111.md`](../../testguided-study/HYPOTHESEN-URSACHENANALYSE-20261111.md) (Antigravity, 263 Z.), [`URSACHENANALYSE-CODEX-20261111.md`](../../testguided-study/URSACHENANALYSE-CODEX-20261111.md) (Codex, 321 Z.), [`HYPOTHESIS-V6-GEMINI-ARGON-HIGH.md`](../../testguided-study/HYPOTHESIS-V6-GEMINI-ARGON-HIGH.md) (Gemini-4-Argon, 39 Z.), [`HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md`](../../testguided-study/HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md) (Gemini-4-Argon, 29 Z.), [`HYPOTHESIS-V8-GEMINI-ARGON-HIGH.md`](../../testguided-study/HYPOTHESIS-V8-GEMINI-ARGON-HIGH.md) (Gemini-4-Argon, 70 Z.).

#### Beobachtete Muster und epistemische Divergenzen
1. **Zwei kontrastierende Hypothesenstile auf identischer Datenbasis (`11.11.`):**
   - **Kaskaden- und Schutzrahmen-Stil (Antigravity):** Formuliert das „Bodeneffekt“-Narrativ (*Cascading Bottlenecks* über fünf Systemebenen), nutzt deterministische Zuschreibungen („geschätzter Anteil >99 %“, „der Grund liegt in…“) und setzt scharfe Erfolgsvorhersagen (`>75 %` EBT-Ausführung durch dediziertes Tool, `-50 %` Stalling durch Test-Isolation, `>30 %` Lösung bei 30B+-Modellen). In Teilhypothese H1 (Z. 217) erscheint die rechnerisch nicht herleitbare Ausgangsquote **„73,3 %“** für `invalid_output` mit `done_reason: length` (tatsächlich `11/67` Aufrufe = 16,4 % bzw. `5/6` Läufe = 83,3 %).
   - **Falsifikations- und Gegenbefund-Stil (Codex):** Benennt konsequent zu jeder Teilhypothese explizite **Gegenbefunde** und **Grenzen** (z. B. dass `requests_6589/pytest` in v2 und `fastapi_9425/cubie` in v3 eine grundsätzliche Modellunfähigkeit widerlegen), führt eine quantitative Sensitivitätsrechnung zur Exitcode-4-Klassifikation durch (`+50,0` vs. `+33,3` PP) und benennt explizit die *konkurrierende* Nullhypothese zu Cubie (dass zusätzliche EBT-API-Regeln das Modell selbst belasten könnten).
2. **Echtzeit-Konversation als agiler Hypothesentreiber (`12.11.`):**
   Die drei `GEMINI-ARGON-HIGH`-Dokumente dokumentieren ein direktes **Live-Steering**:
   - `V6` lieferte vier „chirurgische Quick-Fixes“ vor einem geplanten Nachtlauf.
   - `V7` reagierte direkt um ~02:28 Uhr auf einen hineinkopierten Live-Dump von Call 74 (`20261112-015457`), riet zum sofortigen Abbruch, diagnostizierte „Few-Shot-Selbsthypnose“ durch wiederholte Assistant/User-Paare und deckte die Diskrepanz zwischen der ursprünglichen 25-Zeilen-Idee und der komplexen v6/v7-Implementierung auf.
   - `V8` entstand um ~03:25 Uhr direkt aus zwei Live-Monitor-Ausschnitten (`job-12` und `job-20` aus `20261112-030527`), enthielt im ursprünglichen Commit `10169e57` jedoch per Copy-Paste noch die v7-Lauf-ID `20261112-015457` im Kopf (später in `AGENTENDESIGN-V9.md` Z. 17 beanstandet und in Commit `08792e32` entfernt).
3. **Klaffende Lücke zwischen postulierter Ablation und realer Ausführung:**
   Alle B.2-Dokumente forderten ausdrücklich isolierte Einzelfaktor-Prüfungen (Codex-Studien A–D in `URSACHENANALYSE-CODEX`; schrittweise v8→v9-Ablation in `AGENTENDESIGN-V9`). In der Praxis wurde **zwischen je zwei Läufen immer ein Bündel mehrerer Faktoren gleichzeitig verändert** (`v4 → v5`: Phasen-Gate + `think=true`; `v5 → v6`: `think=false` + temp `0.15` + 3-Rollen-System + neue Tools; `v7-1 → v7-2`: Aufhebung von Phasendeadlines und Aufrufbudgets; `v8 → v9`: Cursor-Entfernung + Auto-Memory + Lese-Symmetrie + Markdown + Entfernung `forced handoff`). Kausale Wirkungsisolationen auf Faktor-Ebene fanden empirisch nicht statt.

---

### 3.3 B.3: KI-generierte Software-Design-Dokumente

**Dokumentenbestand:** [`AGENTENDESIGN.md`](../../testguided-study/AGENTENDESIGN.md) (317 Z.), [`AGENTENDESIGN-V4.md`](../../testguided-study/AGENTENDESIGN-V4.md) (49 Z.), [`AGENTENDESIGN-V5.md`](../../testguided-study/AGENTENDESIGN-V5.md) (75 Z.), [`AGENTENDESIGN-V6.md`](../../testguided-study/AGENTENDESIGN-V6.md) (512 Z.), [`AGENTENDESIGN-V7.md`](../../testguided-study/AGENTENDESIGN-V7.md) (512 Z.), [`AGENTENDESIGN-V8.md`](../../testguided-study/AGENTENDESIGN-V8.md) (217 Z.), [`AGENTENDESIGN-V9.md`](../../testguided-study/AGENTENDESIGN-V9.md) (275 Z.) — insgesamt **1.957 Zeilen**.

#### Gemeinsame Muster in B.3
1. **Strukturelle Ausdifferenzierung von In-place-Edits zu unveränderlichen Versionsdokumenten:**
   [`AGENTENDESIGN.md`](../../testguided-study/AGENTENDESIGN.md) vereint noch historisch nacheinander v1-Befund, v2-Zielarchitektur (`D01–D08`), v2-Umsetzungsstand und einen v3-Nachtrag. Ab v4 etablierte sich ein sauberes Append-only-Dokumentenmodell mit expliziten Statusmarkierungen („Konzept, noch nicht implementiert“ vs. „implementiert“) und Rückwärtskompatibilität historischer Freezes.
2. **Epistemisches Gatekeeping zwischen B.2 und B.3:**
   Die Design-Dokumente übernahmen Hypothesen aus B.2 nicht unkritisch, sondern wirkten als Korrektiv:
   - `AGENTENDESIGN-V6.md` (Z. 49–63) wies Antigravitys unbelegte `73,3 %`-Angabe zurück, relativierte den „über 99 % pytest-Prior“ sowie eine „30B-Mindestgröße“ zu bloßen Hypothesen und integrierte Codex’ Präzisierungen.
   - `AGENTENDESIGN-V7.md` (Z. 50–67) glich die abweichenden Zählungen von Antigravity (51/14) und Codex (53/12) ab, wählte transparent die aktenkundigen Codex-Summen und stellte klar, dass die `requests/utils.py`-Hypothese technisch `TeamController._navigate` und nicht bloß `workspace.py` betrifft.
   - `AGENTENDESIGN-V9.md` (Z. 17–24) berichtigte die falsche Archiv-ID in `HYPOTHESIS-V8` (`20261112-015457` → `20261112-030527`), verifizierte die konkreten Schritte (`0021`, `0023`, `0030`, `0063`) im Archiv und stufte Totalitätsaussagen („Gedächtnisverlust verschwinde vollständig“) zu prüfbaren Erwartungen herab.
3. **Asymmetrie zwischen Spezifikationskomplexität und 12B-Modellkapazität (Pendelbewegung Autonomie vs. Zwang):**
   - Obwohl `AGENTENDESIGN-V6.md` das Leitmotiv *„Komplexität reduzieren, Fokus schärfen“* im Titel trug, entstand auf 512 Zeilen eine hochgradig formale Sieben-Zustands-Maschine (`orient`, `specify`, `reproduce`, `implement`, `revise_tests`, `verify`, `review`) mit 8 Nachrichtentypen und 18 Abnahmegruppen (`V6-A01..A18`), was später in `HYPOTHESIS-V7` zur Konfrontation zwischen Live-Kritik und Design-Übersetzung führte.
   - Über v6–v9 pendelte das Design ungelöst zwischen Controller-Zwang und Modellautonomie:
     - *v6:* zweistufiges manuelles Übergabeprotokoll (`publish_context` + `handoff`) → **0/6 Übergänge**.
     - *v7:* lokale Phasengrenzen + mechanisches Fallback (`6` Calls in `orient`) → **3/3 QA-Aktivierungen in `v7-1`**, anschließend Streichung der Phasengrenzen zwischen `v7-1` und `v7-2` → **0/1 Übergang in `v7-2`**.
     - *v8:* erzwungener Übergang bei `repeat_count >= 3` → **QA erreicht**, jedoch Blockade durch Amnesie (`update_context`) und `cursor_error`.
     - *v9:* bewusster Rückbau des Zwangsübergangs zugunsten autonomer `finish`-Entscheidung → wegen Schemaüberladung (`verdict` in `FINISH`) erneut **0/6 Übergänge** (`0` `finish`-Aufrufe in 1.184 Schritten).

---

### 3.4 B.4: KI-generierte QA-Dokumente (Design → Operationsfähige Test-Module)

**Dokumentenbestand:**
- **Vorab-QA-Kontraktspezifikationen (RED-First)** in [`../../tests/testguided_study_design`](../../tests/testguided_study_design): [`PILOT_TECHNICAL_CASES.md`](../../tests/testguided_study_design/PILOT_TECHNICAL_CASES.md) (98 Z., 32 Cases), [`PILOT_180702_CASES.md`](../../tests/testguided_study_design/PILOT_180702_CASES.md) (147 Z., 48 Cases), [`MONITOR_CONTEXT_CASES.md`](../../tests/testguided_study_design/MONITOR_CONTEXT_CASES.md) (58 Z., 11 Cases), [`RUN_MANAGEMENT_CASES.md`](../../tests/testguided_study_design/RUN_MANAGEMENT_CASES.md) (118 Z., 32 Cases), [`V6_CASES.md`](../../tests/testguided_study_design/V6_CASES.md) (243 Z., 98 Nodes), [`V7_CASES.md`](../../tests/testguided_study_design/V7_CASES.md) (162 Z., 41 Nodes), [`V8_CASES.md`](../../tests/testguided_study_design/V8_CASES.md) (244 Z., 92 Nodes), [`V9_CASES.md`](../../tests/testguided_study_design/V9_CASES.md) (241 Z., 134 Nodes) — **1.311 Zeilen**.
- **Nachgelagerte Implementierungs- und Verifikationsprotokolle (GREEN-Abschluss)** flach in `../../testguided-study`: [`IMPLEMENTIERUNG-V7.md`](../testguided-study/IMPLEMENTIERUNG-V7.md) (78 Z.), [`IMPLEMENTIERUNG-V8.md`](../testguided-study/IMPLEMENTIERUNG-V8.md) (137 Z.), [`IMPLEMENTIERUNG-V9.md`](../testguided-study/IMPLEMENTIERUNG-V9.md) (118 Z.) — **333 Zeilen**.

#### Strukturelle Muster in B.4
1. **Disziplinierte Test-First-Übersetzungskette (`B.3 → B.4 RED → B.5 GREEN → B.4 GREEN`):**
   Jede Generation ab v2 (am explizitesten v6–v9) wurde zunächst in ein verbindliches `*_CASES.md`-Dokument samt ausführbarer, bewusst roter EBT-Suite übersetzt. Der Ausgangsstand wurde dabei ohne `skip` oder `xfail` als messbare rote Sammlung festgehalten (`V6_CASES`: 66 rot / 32 grün; `V7_CASES`: 41 rot; `V8_CASES`: 6 grün / 86 rot; `V9_CASES`: 8 Kalibrierungen grün / 126 Controllerfälle rot). Erst nach Umsetzung der Produktionsmodule folgte das jeweilige `IMPLEMENTIERUNG-V*.md` mit den verifizierten grünen Gesamtzahlen (`439` → `555` → `698+` / `146 V9-Nodes`).
2. **Physische Ablage-Spaltung durch Infrastruktur-Nebenwirkung:**
   Weil `artifacts.sources()` ursprünglich sämtliche Python-Dateien unterhalb von `../../testguided-study` hashte und `execution.run()` bei Hash-Abweichungen abbrach, dokumentierte bereits [`AGENTENDESIGN.md`](../testguided-study/AGENTENDESIGN.md) (Z. 199–204) die bewusste Verlagerung der Design-Testmodule nach `experiments/tests/testguided_study_design/`. So entstanden zwei räumlich getrennte QA-Schichten (flache `IMPLEMENTIERUNG-*.md` im Studienordner vs. `*_CASES.md` und Testmodule außerhalb des Hash-Baums).
3. **Strikte Aussagebegrenzung – und implizite Budgetmutation:**
   Alle `*_CASES.md`- und `IMPLEMENTIERUNG-*.md`-Texte weisen ausdrücklich darauf hin, dass deterministische Replays nur Controllermechanik prüfen und keine Modellleistung belegen. Zugleich dokumentieren `V6_CASES.md`, `V7_CASES.md` und `IMPLEMENTIERUNG-V7.md` am Kopf nachträglich geänderte Budgetregeln (Aufhebung von Aufruflimits, Phasendeadlines, Reserve und Stagnationsabbrüchen auf 30 Minuten gemeinsame Taskzeit), was zwischen `v7-1` und `v7-2` direkt in das veränderte Laufzeitverhalten von Dimension A eingriff.

---

### 3.5 B.5: KI-generierte Test-Suites und Quell-Codes

**Bestand und eigene Laufzeitprüfung (Stand `7e08e2ac`):**

| Schicht / Pfad | Dateien | Codeumfang (LOC) | Gesammelte Nodes (Pytest) | EBT-Nutzung (`EBT(` / `contract(`) |
| :--- | :---: | :---: | :---: | :--- |
| `../../testguided-study/testguided_study` | 35 | **7.361** | — | Produktcode (inkl. `caseforms.py` & `backend.py` EBT-Metriken) |
| `../../testguided-study/tests` | 10 | **983** | **67** | 3 von 41 Testfunktionen / **17 von 67 Nodes (25,4 %)** |
| `../../tests/testguided_study_design` | 40 | **7.050** | **701** | 223 von 306 Testfunktionen / **533 von 701 Nodes (76,0 %)** |
| **Gesamt (Test-Suites `B.5`)** | **50** | **8.033** | **768** | **550 von 768 Nodes (71,6 %) direkt über `qb_cubie.EBT`** |

- **Eigene Ausführung:** `.venv/bin/python -m pytest experiments/testguided-study/tests experiments/tests/testguided_study_design -q` ergab **765 passed, 3 skipped** in 194,99 s (die 3 übersprungenen Fälle sind die nur mit `CUBIE_STUDY_DOCKER=1` aktiven Live-Docker-Tests in `test_docker_bridge.py`); `.venv/bin/python -m ruff check experiments/testguided-study experiments/tests/testguided_study_design` bestand ohne Befunde (**All checks passed**).

#### Beobachtete Konstruktions- und Qualitätsmuster in B.5
1. **Testcode übersteigt Produktcode (Test-to-Code-Ratio 1,09 : 1):**
   Mit **8.033 LOC** Test- und Supportcode auf **7.361 LOC** Studienquellcode (und **768** Test-Nodes) übersteigt das Verifikationsgerüst den Umfang des eigentlichen Laufzeitcodes.
2. **Freeze-getriebene Parallel-Vererbung (`team*.py`):**
   Da bestehende Freeze-Archive reproduzierbar bleiben sollten, wurden ältere Controller nicht ersetzt, sondern kumulativ beerbt und parallel vorgehalten:
   - `TeamController` (`team.py`, 805 LOC, 37 Methoden)
   - `V7TeamController(TeamController)` (`team_v7.py`, 573 LOC, 29 Methoden)
   - `V8TeamController(TeamController)` (`team_v8.py`, 850 LOC, 38 Methoden)
   - `V9TeamController(V8TeamController)` (`team_v9.py`, 709 LOC, 24 Methoden)
   Allein die Multi-Agenten-Schicht (`team*.py`, `team_*_design.py`, `team_workspace.py`, `team_agent.py`, `team_probe.py`, `caseforms.py`) macht **3.994 LOC (54,3 %)** von `testguided_study/` aus. V9 erbt damit durch eine dreistufige Klassenhierarchie (`V9 → V8 → V6`).
3. **Wirkliche EBT-Nutzung im eigenen Testbau (Widerlegung der Nicht-Zirkularitäts-Behauptung aus C):**
   Über `v6_support.contract(target, expected)` — das intern `EBT(target=target, post=WorldState(returns=expected), reporter=None).run()` und `assert result.evaluation is True` ausführt — nutzen **533 von 701 Nodes** in `testguided_study_design/` sowie **17 von 67 Nodes** in `../../../tests` (insgesamt **550 von 768 Nodes**) direkt `qb_cubie.EBT`.
4. **Systemische Blindstellen der deterministischen Replay-Suites gegenüber Dimension A:**
   Trotz 765 bestandener Tests verdeckte das B.5-Testdesign genau die zwei realen Versagensmechanismen von `v9` (`20261112-035522`):
   - **Schema- und Prompt-Blinde beim Modellverhalten:** Die V9-Tests (z. B. `v9_support.py:136–138` `Harness.orient()`) riefen `finish` programmgesteuert im Test-Harness auf oder spielten feste Modellantworten ein. So blieb ungetestet, wie ein 12B-Modell auf `team_v9_design.py:47–51` reagiert, wo ein einziges `FINISH`-Schema mit sechs unmarkierten Review-/QA-/Dev-Feldern (`verdict`, `next_role`, `test_targets`, `regressions`, `unresolved`, `existing_coverage_reason`) angeboten wird und `PROMPTS['analysis']` (Z. 18–23) zwar `finish verdict=verified/rework` syntaktisch vorführt, `team_v9.py:381–383` aber bei `verdict` in `orient` sofort `ValueError('Orientation cannot verify a repair')` wirft.
   - **Skalierungs-Blinde beim Remote-Container-I/O:** Die Runtime-Replays prüften `V9TeamController` gegen `V9LocalWorkspace` auf einem 9-Datei-Mini-Repository (`src/calc.py` etc.). Der produktive Docker-Pfad über `V9RemoteWorkspace` ruft jedoch in `team_v9.py` pro Schritt mehrfach `self.store.inventory()` auf (`_refresh`, `_navigate`, `_source_materials`, `request`), was jeweils einen kompletten Docker-`exec`-Prozess mit SHA-256-Hashing aller Projektdateien auslöst (`team_workspace.py:265–276`) und in `fastapi_9425` über **62 % des 1.800-s-Zeitbudgets (~15–16 s pro Schritt)** band.

---

## 4. Gemeinsame Muster und Dynamiken über Dimension B (inkl. Schnittstellen zu A und C)

Über die fünf Teilbereiche **B.1 bis B.5** und deren Einbettung zwischen **A** und **C** treten fünf übergreifende empirische Muster hervor:

### Muster 1: Die „Grüne-Suite / Null-Lösungs“-Schere (*Error Domain Migration* unter agiler Über-Spezifikation)
Die Iteration von v1 bis v9 zeigt eine stetig steigende **technische Prüf- und Infrastrukturreife** bei gleichzeitig stagnierender bzw. auf **0/17** sinkender **Lösungsquote in Dimension A**:
- B.4 und B.5 wuchsen von 57 Tests (Initial-Commit) über 128 (v2), 145 (v3), 439 (v7), 555 (v8) auf **768 gesammelte Nodes** (765 bestanden, 3 Docker-Skips).
- Gleichzeitig wanderte der Ausfallgrund in Dimension A bei `gemma4:12b` lediglich von Stufe zu Stufe (*Token Starvation* in v5 → zweistufige Handoff-Hürde in v6 → Kontextballast & Tool-Entzug in v7 → `cursor_error` & Amnesie in v8 → überladenes `finish`-Schema & 82,6 % Orientierungs-Duplikate in v9).
- Jede Iteration schloss einen *technisch* identifizierten Defekt per Replay-Vertrag, schuf dabei aber mit wachsenden Zustandsautomaten und parallel vererbten Controller-Schichten neue semantische Hürden für das 12B-Modell, ohne eine einzige Ablation der Vorgängergeneration isoliert abzuschließen.

### Muster 2: Rekursive Asymmetrie der Testmethodik (`EBT` in B vs. `EBT` in A)
Während in **Dimension A** das untersuchte Studienmodell `gemma4:12b` in 19 von 21 Single-Agent-Cubie-Läufen (90,5 %) und in 100 % der Multi-Agent-Läufe v6/v7-2/v8/v9 **keinen einzigen EBT-Vertrag ausführte** (in v9 gelangte die auf `qa` beschränkte Cubie-Anleitung in `team_v9.py:615` gar nicht in den Prompt), praktizierten die an **Dimension B** arbeitenden KI-Systeme exakt jene Test-First-/EBT-Entwicklungskette (`B.3 Design → B.4 rote *_CASES.md → B.5 Umsetzung → grüne Abnahme`) selbst in **550 von 768 Nodes (71,6 %)** über das `qb_cubie`-Paket. Die Methodik funktionierte hochgradig verlässlich als *Entwicklungsvertrag zwischen Design- und Implementierungs-KI*, scheiterte jedoch beim Transfer als *autonomes Problemlösungswerkzeug eines lokalen 12B-Modells* auf unvertrauten Repositories.

### Muster 3: Multi-KI-Gegenkontrolle als internes Korrektiv – und ihre Grenzen an Dokumentübergängen
Innerhalb von **Dimension B** erzeugte das Zusammenspiel von drei verschiedenen Modellperspektiven (`Codex`, `Antigravity`, `Gemini-4-Argon`) nachweisliche Selbstkorrekturen:
- `Codex` dämpfte und bereinigte in B.2 (`URSACHENANALYSE-CODEX`) und B.3 (`AGENTENDESIGN-V6`, `-V7`, `-V9`) ungedeckte Quoten (`73,3 %`), Zählfehler (`51/14` vs. `53/12`) und falsche Laufzuordnungen (`20261112-015457` → `030527`).
- `Gemini-4-Argon` deckte per Live-Dump-Diagnose (`HYPOTHESIS-V7`, `-V8`) kognitive Überfrachtung auf, die in deterministischen Unit-Tests unsichtbar geblieben war (`Working ledger`, Rollenkontamination, `cursor: "0"`-Falle).
- **Grenze der Selbstkorrektur:** Diese Korrekturen blieben oft lokal in jüngeren Dokumenten stehen, während veraltete oder fehlerhafte Angaben in früheren Dateien (`PAPER.md` §10.1 behielt `73,3 %`) oder aggregierten Übersichten (`ANALYSE-GENERATIONEN-V6-V9.md`: `1.441` Requests als Modellaufrufe, `v7-1`-Fehldeutung) persistierten.

### Muster 4: Quellen- und Faktendrift beim Übergang von Dimension B zu Dimension C
In **Dimension C** (Synthese der Einreichungs-PDFs durch `Gemini-4-Argon` und deren Begutachtung durch `Antigravity` in `KRITISCHE-ANALYSE-PAPER-SUBMISSION.md`, `GUTACHTEN-PAPER-SUBMISSION-1/2/4.md` und `STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md`) zeigt das Material zwei dokumentierte Fälle von **sekundärer Fehlattribution trotz umfangreicher „Exakt-bestätigt“-Tabellen**:
1. **Unzutreffende „Nicht-zirkuläre Pytest-Verifikation“:** [`g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md`](../../testguided-study/g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md) (Z. 34) behauptet, alle 698+ Controller-Testknoten seien zur Vermeidung zirkulärer Validierung mit Standard-Pytest-Assertions statt EBT-Verträgen implementiert worden. [`GUTACHTEN-PAPER-SUBMISSION-2.md`](../../testguided-study/GUTACHTEN-PAPER-SUBMISSION-2.md) (Z. 51), [`GUTACHTEN-PAPER-SUBMISSION-4.md`](../../testguided-study/GUTACHTEN-PAPER-SUBMISSION-4.md) (Z. 44) und [`STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md`](../../testguided-study/STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md) (Z. 63) kennzeichnen dies als *„Exakt bestätigt“* (bei einem Verifiability-Score von 5,0/5,0), weil der Prüfer nach `assert`-Statements zählte, ohne die Wrapper-Funktion `v6_support.contract()` aufzulösen, die tatsächlich `EBT(...).run()` in **533 von 701 Nodes** aufruft.
2. **Fehlgeleitete Verdrängung der realen `swegemma`-Provenienz:** In [`KRITISCHE-ANALYSE-PAPER-SUBMISSION.md`](../../testguided-study/KRITISCHE-ANALYSE-PAPER-SUBMISSION.md) (Abschn. 2.1–2.2) beanstandete `Antigravity` die Nennung von `swegemma 0.2.11` und des lokalen `swegemma`-Aufgabenpools im Erstentwurf als *„Falschbehauptung“* und *„Wissenschaftliche Unredlichkeit“*, weil `swegemma` nicht in `../../../pyproject.toml` oder `.venv` installiert war und das Repository unter `src/qb_cubie/benchmarks/swebench/` ein eigenes Benchmark-Paket führt. Tatsächlich importiert [`testguided_study/backend.py`](../testguided-study/testguided_study/backend.py) (Z. 1–52) zwingend **`swegemma == 0.2.11`** über die von `./study` gefundene Umgebung `STUDY_PYTHON`, und [`PROTOKOLL.md`](../testguided-study/PROTOKOLL.md) (Z. 84–86, 273–276) sowie [`DATEN.md`](../testguided-study/DATEN.md) (Z. 12–15) grenzen die Studie ausdrücklich von `qb_cubie.benchmarks` ab. Dennoch führte das Gutachten in [`GUTACHTEN-PAPER-SUBMISSION-1.md`](../testguided-study/GUTACHTEN-PAPER-SUBMISSION-1.md) (Z. 60) dazu, dass `swegemma` aus den Revisionen `-1` bis `-4` entfernt wurde.

### Muster 5: Kontext- und Pfadartefakte durch spontanes Wachstum („aus dem Stegreif“)
Die Architektur von `../../testguided-study` trägt die Spuren ungeplanter Sofortanpassungen unter Zeitdruck:
- Doppelte Testablage (`../../../tests` innerhalb des Hash-Baums vs. `experiments/tests/testguided_study_design/` außerhalb von `artifacts.sources()`), deren nachträgliche Verschiebung noch am 13.11. (Commit `32434293`) Pfadkorrekturen in sieben historischen Design- und Implementierungsdokumenten erforderte.
- Kumulative Dokumentstruktur in [`../../../README.md`](../../testguided-study/README.md) (645 Z.) und [`AGENTENDESIGN.md`](../../testguided-study/AGENTENDESIGN.md) (317 Z.), in denen ältere Stände unterhalb neuerer Einleitungen bzw. unterhalb neuerer Nachträge stehenblieben.
- Fehlen einer durchgeführten `measurement`-Phase: Sämtliche 13 Archive in `runs/` entstammen Entwicklungs- und Pilotiterationen (`pilot` bzw. `development`) auf den drei verbrauchten Aufgabenpaaren mit einem einzigen Seed (`42`); das in [`PROTOKOLL.md`](../../testguided-study/PROTOKOLL.md) und [`campaign.py`](../../testguided-study/testguided_study/campaign.py) vorbereitete Messungs- und Qualifikationsgatter wurde durch die Vorstufe (B.3–B.5) vollständig ausgearbeitet, aber in Dimension A nie erreicht.
