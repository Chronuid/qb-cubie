# Gutachten und wissenschaftliches Grounding zur Paper-Submission „qb-cubie and Floor-Effect Analysis“ (Revision -1)

**Herkunft der Analyse:** Antigravity, Gemini-3.8-Flash (High Reasoning)  
**Datum des Gutachtens:** 12. November 2026  
**Untersuchte Dokumente und Datenquellen:**
- **Revidiertes Prüfdokument:** [`experiments/testguided-study/G4DA Paper Submission - qb-cubie and Floor-Effect Analysis-1.pdf`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/G4DA%20Paper%20Submission%20-%20qb-cubie%20and%20Floor-Effect%20Analysis-1.pdf)
- **Ursprüngliches Prüfdokument (Referenz):** [`experiments/testguided-study/G4DA Paper Submission - qb-cubie and Floor-Effect Analysis.pdf`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/G4DA%20Paper%20Submission%20-%20qb-cubie%20and%20Floor-Effect%20Analysis.pdf)
- **Wettbewerbsanforderungen & Bewertungsrubrik:** [`experiments/testguided-study/Developer-Agent-Paper.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/Developer-Agent-Paper.md) (Google – The Gemma 4 Developer Agent Competition, Paper Track)
- **Implementierungsbasis & Studiencode:** Alle 35 Python-Module unter [`experiments/testguided-study/testguided_study/`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/) (insbesondere `team_v9.py`, `team_v9_design.py`, `team_v8.py`, `team_v7.py`, `team.py`, `team_workspace.py`, `agent.py`, `controller.py`, `admission.py`, `corpus.py`, `workspace.py`, `artifacts.py`, `telemetry.py`)
- **Laufarchive (Rohdaten & Telemetrie):** Alle 13 Verzeichnisse in [`experiments/testguided-study/runs/`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/) (v1–v5: 7 abgeschlossene Piloten mit 42 Durchläufen; v6–v9: 5 Archive mit 17 ausgeführten Durchläufen)
- **Aufgaben- & Kandidatendaten:** [`candidate-catalog.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/candidate-catalog.json), [`candidate-selection.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/candidate-selection.json), [`DATEN.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/DATEN.md), [`KANDIDATEN.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/KANDIDATEN.md)
- **Voranalysen & Audit-Dokumente:** [`KRITISCHE-ANALYSE-PAPER-SUBMISSION.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/KRITISCHE-ANALYSE-PAPER-SUBMISSION.md), [`ANALYSE-GENERATIONEN-V6-V9.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md), [`PAPER.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md), [`PILOTANALYSE-V9-20261112-035522.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PILOTANALYSE-V9-20261112-035522.md)

---

## 1. Executive Summary & Gesamturteil

Die vorliegende Begutachtung untersucht das überarbeitete Einreichungsdokument `G4DA Paper Submission - qb-cubie and Floor-Effect Analysis-1.pdf` (im Folgenden: **Revision -1**) im direkten Abgleich mit den Rohdaten des Studienpakets `testguided_study` und den offiziellen Anforderungen des *Google Gemma 4 Developer Agent Paper Track* (`Developer-Agent-Paper.md`).

### 1.1 Wesentliche Fortschritte der Revision -1 gegenüber der Erstfassung
Die Autoren haben auf die vorangegangene Mängelrüge ([`KRITISCHE-ANALYSE-PAPER-SUBMISSION.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/KRITISCHE-ANALYSE-PAPER-SUBMISSION.md)) konstruktiv reagiert und entscheidende inhaltliche Falschdarstellungen korrigiert:
1. **Richtigstellung der Datensatzprovenienz:** Der fälschliche Begriff eines „swegemma pool“ wurde getilgt. Das Paper benennt nun korrekt die 129 realen GitHub-PRs aus vier Repositories (`fastapi`, `rich`, `requests`, `httpx`) im Standardformat von **SWE-bench** (Abschnitt 2).
2. **Entflechtung von `cubie` und `swegemma`:** In Abschnitt 3.1 wurde eine transparente Klarstellung zur Autonomie des Repositories ergänzt. Es wird klargestellt, dass `cubie` keinerlei Paketabhängigkeit zu `swegemma` aufweist und die Multi-Agenten-Orchestrierung ab v6 vollständig autonom via nativer Git-Subprozesse und Docker-Container arbeitet.
3. **Kausale Differenzierung in v9:** Die Fehlattribution des v9-Ergebnisses wurde korrigiert. Das Paper erläutert nun präzise, dass das Ausbleiben von EBT-Verträgen in v9 primär darauf zurückzuführen ist, dass der Controller die `qb-cubie`-Anleitung erst bei Aktivierung der QA-Rolle injiziert (`team_v9.py:615`), diese Rolle jedoch infolge eines Controller-Interface-Konflikts nie erreicht wurde.

### 1.2 Kritische Restmängel & Formale Risiken
Trotz dieser inhaltlichen Verbesserungen weist das Dokument in seiner jetzigen PDF-Fassung **zwei gravierende formale und typografische Mängel** auf, die eine erfolgreiche Begutachtung im Wettbewerb massiv gefährden:
1. **Dramatische Überschreitung des Wortlimits (K.O.-Kriterium):**
   - Vorgabe in `Developer-Agent-Paper.md`: **Maximal 3.000 Wörter** („Scope: 3,000 words maximum, reporting original, unpublished research“).
   - Ist-Zustand des PDF-Textes: **5.478 Wörter** (+82,6 % Überschreitung). Dies begründet ein akutes Risiko einer formalen Disqualifikation (Desk Rejection).
2. **Krasse typografische Zerstörungen & Textinversionen durch Rendering-Abrisse:**
   - **Seitenübergang 3 → 4:** Textfragmente und Zitate wurden aus Klammern herausgerissen; oben auf Seite 4 steht ein unzusammenhängender Textblock (`Data Documentation, 2026Submission Audit, 2026cubieBenchmark Guide, 2026Submission Audit, 2026Single-Agent Report, 2026`), während im Text leere Klammern `(; )` verbleiben.
   - **Seitenübergang 11 → 12:** Auslassung von Messwerten („infrastructural errors dropped to , and...“) und ein **semantischer Inversionsfehler** in Zeile 666 („causing the model to invoke finish across 1,184 steps“ statt „zero times“). Die fehlenden Wörter wurden auf Seite 12 als verstümmelter Listenpunkt `6.` eingefügt.
   - **Fehlende Schriftart-Abstände:** Im gesamten Dokument kleben Formatierungsfragmente zusammen (`ultiAgent`, `xampleBased`, `stLinter`, `yVenv`, `orldState`).

### 1.3 Gesamtbewertung nach der Wettbewerbsrubrik (Skala 0 bis 5)
- **Novelty:** **4,0 / 5,0** (Herausragende, schonungslose Offenlegung realer Floor-Effekte und Reasoning-Token-Starvation bei 12B-Modellen).
- **Quality:** **3,5 / 5,0** (Kryptografisch eingefrorene Zero-Leakage-Methodik; eingeschränkt durch kleine Stichprobe und 0:0-Bodeneffekte).
- **Relevance:** **4,5 / 5,0** (Höchste Praxisrelevanz für lokale Open-Weights-Coding-Agenten auf Consumer-Hardware).
- **Verifiability:** **4,8 / 5,0** bezüglich Code/Daten (100 % Reproduzierbarkeit); **3,8 / 5,0** bezüglich PDF-Präsentation (Zitierungsabbrüche).
- **Clarity:** **2,5 / 5,0** (Aufgrund von Wortlimitüberschreitung, Layoutdefekten und fehlenden Standardkapiteln `Introduction` / `Related Works`).
- **Gesamtpunktzahl:** **3,66 / 5,0** (Mit Behebung der Layoutfehler und Straffung auf 3.000 Wörter steigerbar auf **4,4 / 5,0**).

---

## 2. Detailliertes Daten-Grounding der Studie (`testguided_study`)

Jede quantitative Behauptung und jede architektonische Beschreibung in Revision -1 wurde gegen den Code in [`experiments/testguided-study/testguided_study/`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/) und die Laufarchive in [`experiments/testguided-study/runs/`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/) geprüft.

### 2.1 Datenbasis, Aufgabenkatalog und Testsuiten (Abschnitt 2)

| Parameter / Kennzahl | Behauptung im Paper | Verifizierter Befund in Code & Daten | Status |
| :--- | :--- | :--- | :---: |
| **Gesamtaufgabenpool** | 129 Aufgaben aus 4 Repositories | [`candidate-catalog.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/candidate-catalog.json): `tasks`-Länge = 129; `fastapi/fastapi`: 67, `Textualize/rich`: 48, `psf/requests`: 13, `encode/httpx`: 1 | **Exakt bestätigt** |
| **Fachliches Audit** | 39 auditiert: 26 qualifiziert, 9 bedingt, 3 zurückgestellt, 1 ausgeschlossen; 90 ungeprüft | [`KANDIDATEN.md:106-109`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/KANDIDATEN.md#L106-L109) & [`candidate-catalog.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/candidate-catalog.json): 39 manuell geprüft, 26 fachliche Kandidaten, 90 ungeprüft verbleibend | **Exakt bestätigt** |
| **Ausgewählte Pilotaufgaben** | 3 Aufgaben: `fastapi_9425`, `requests_6589`, `rich_3278` mit Seed 42 | [`DATEN.md:110`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/DATEN.md#L110) & [`runs/20261111-200641/selection.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/20261111-200641/selection.json): Aufgaben eindeutig fixiert | **Exakt bestätigt** |
| **`fastapi_9425` Testumfang** | FAIL_TO_PASS: 1, PASS_TO_PASS: 8 | `runs/20261111-200641/admission/0000/admission.json`: `FAIL_TO_PASS` = 1, `PASS_TO_PASS` = 8 | **Exakt bestätigt** |
| **`requests_6589` Testumfang** | FAIL_TO_PASS: 1, PASS_TO_PASS: 11 | `runs/20261111-200641/admission/0002/admission.json`: `FAIL_TO_PASS` = 1, `PASS_TO_PASS` = 11 | **Exakt bestätigt** |
| **`rich_3278` Testumfang** | FAIL_TO_PASS: 16, PASS_TO_PASS: 7 | `runs/20261111-200641/admission/0001/admission.json`: `FAIL_TO_PASS` = 16, `PASS_TO_PASS` = 7 | **Exakt bestätigt** |
| **Ausgangsbelastung sichtbare Tests** | FastAPI: 8 Sammlungsfehler; Requests: 577 p, 5 f, 15 s; Rich: 746 p, 65 f, 24 s | [`TECHNIKANALYSE-20261111-171515.md:52-68`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/TECHNIKANALYSE-20261111-171515.md#L52-L68): Vorbelastung exakt dokumentiert | **Exakt bestätigt** |

### 2.2 Single-Agent-Entwicklungsreihe v1–v5 (Abschnitte 4 & 5)

| Kennzahl / Ereignis | Behauptung im Paper | Verifizierter Befund in den Laufarchiven | Status |
| :--- | :--- | :--- | :---: |
| **Umfang der Pilotreihe** | 7 abgeschlossene Piloten, 42 Einzelläufe, 1 vorbereitetes Archiv (`180104`) | Verzeichnisse unter `runs/`: `132401`, `160158`, `163110`, `171515`, `180104` (nur prepared), `180702`, `192412`, `200641` | **Exakt bestätigt** |
| **Kryptografische Integrität** | 5.563 geprüfte SHA-256 Hashreferenzen, 100 % Übereinstimmung | [`PAPER.md:269-270`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md#L269-L270): 5.563 Hashreferenzen über alle 8 Archive lückenlos auditiert | **Exakt bestätigt** |
| **Erfolgreiche Reparaturen** | 3 von 42 Läufen gelöst (7,1 %): 2x pytest (v2, v4), 1x cubie (rev. v3) | `163110` (v2, pytest auf Requests gelöst); `180702` (v3 rev., Cubie auf FastAPI gelöst); `192412` (v4, pytest auf FastAPI gelöst) | **Exakt bestätigt** |
| **EBT-Nichtnutzung (v1–v5)** | In 19 von 21 Cubie-Läufen (90,5 %) kein EBT ausgeführt; nur 2 Läufe mit EBT | EBT-Ausführungen traten ausschließlich in `180702` auf (Lauf 0001: 6 EBTs; Lauf 0004: 3 EBTs). In allen 19 anderen Cubie-Läufen: `ebt_executed = 0` | **Exakt bestätigt** |
| **v5 Reasoning Token Starvation** | 11 von 67 Modellaufrufen erreichten Limit (8.192 Tokens), 0 JSON-Aktionen | `runs/20261111-200641/frozen/runs/`: Exakt 11 Responses mit `done_reason = length`, `eval_count = 8192` und `message.content = ""` | **Exakt bestätigt** |
| **v5 Token- und Zeitverbrauch** | 90.112 Tokens (87,3 % aller Ausgabetokens); 79,6 % der summierten Agentenzeit | 11 * 8.192 = 90.112 Tokens von 103.235 summierten Output-Tokens (= 87,29 %); Zeitanteil in [`URSACHENANALYSE-CODEX-20261111.md:122`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/URSACHENANALYSE-CODEX-20261111.md#L122) | **Exakt bestätigt** |

### 2.3 Multi-Agent-Nachfolgestudie v6–v9 (Abschnitt 7)

| Kennzahl / Ereignis | Behauptung im Paper | Verifizierter Befund in Code & Daten | Status |
| :--- | :--- | :--- | :---: |
| **Umfang der Multi-Agent-Reihe** | 5 Archive, 17 ausgeführte Läufe, 1.441 Modellaufrufe, 1.432 Werkzeugschritte | [`ANALYSE-GENERATIONEN-V6-V9.md:37`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md#L37): v6 (6), v7-1 (3), v7-2 (1), v8 (1), v9 (6) = 17 Läufe; 1.441 Modell- / 1.432 Werkzeugaufrufe | **Exakt bestätigt** |
| **Token-Gesamtvolumen** | 8.554.438 Input-Tokens, 75.250 Output-Tokens | Exakte Summe aus den Transaktionsdaten der 5 Archive | **Exakt bestätigt** |
| **Werkzeugverteilung** | `search_content`: 795 (55,5 %), `read_file`: 504 (35,2 %), `read_evidence`: 72, `find_paths`: 52, `finish`: 0 | [`ANALYSE-GENERATIONEN-V6-V9.md:46-55`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md#L46-L55): 100 % identisch | **Exakt bestätigt** |
| **v6 Stagnationsabbrüche** | 6x Stagnationsstopp im Orientierungszustand nach 45 s bis 531 s | `runs/20261112-002038/report.json`: Alle 6 Läufe endeten via Controller-Stagnation | **Exakt bestätigt** |
| **v7-2 `find_paths`-Schleife** | Werkzeugentzug führte zu 32 bzw. 36x fehlerhafter `find_paths`-Nutzung | [`AGENTENDESIGN-V7.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/AGENTENDESIGN-V7.md) & [`ANALYSE-GENERATIONEN-V6-V9.md:73`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md#L73): Glob-Werkzeug für Codeinhalte missbraucht | **Exakt bestätigt** |
| **v8 Forced Handoff & Cursor Traps** | `repeat_count >= 3` zwang zu QA; 30+ `cursor_error`-Abweisungen | [`testguided_study/team_v8.py:692-695`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v8.py#L692-L695): Automatischer Übergang bei 3 Wiederholungen; Paginierungsfehler in `ask_analysis` | **Exakt bestätigt** |
| **v9 Entkopplung & Aktionsduplikate** | 0 Infrastrukturfehler; 974 Duplikate (82,6 %) bei 1.179 Aktionen; 0x `finish` | [`testguided_study/team_v9.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v9.py) & [`PILOTANALYSE-V9-20261112-035522.md:104`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PILOTANALYSE-V9-20261112-035522.md#L104): 974 Duplikate; `finish` 0-mal aufgerufen | **Exakt bestätigt** |
| **v9 Guide-Injektions-Barriere** | Guide wird erst bei QA injiziert; QA nie erreicht → Modell sah Cubie-Guide nie | [`testguided_study/team_v9.py:614-615`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v9.py#L614-L615): `if self.role == 'qa': system += '\nFramework guide:\n' + self.guide` | **Exakt bestätigt** |

---

## 3. Kritische Mängelanalyse von Revision -1

Während die fachliche Korrektheit der Zahlen und die Validität der Kausalketten vollends überzeugen, weist das Dokument gravierende Mängel in der Textverarbeitung, der Typografie und der formalen Regeltreue auf.

### 3.1 Gravierender Textinversionsfehler in Abschnitt 7.2 (Seite 11, Zeilen 666–667)
In Abschnitt 7.2 (Punkt 5 zu Generation v9) heißt es wörtlich im PDF:
> *„[...] causing the model to invoke finish across 1,184 steps and fall into 974 duplicate actions (82.6%) [...]“*

**Befund:** Dies ist eine **kontrafaktische Inversion der Tatsachen**.  
Tatsächlich hat das Modell in allen 1.184 Schritten die Aktion `finish` **kein einziges Mal (0 Aufrufe, 0,0 %)** aufgerufen ([`PILOTANALYSE-V9-20261112-035522.md:87`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PILOTANALYSE-V9-20261112-035522.md#L87)).  
**Ursache des Fehlers:** Beim Erzeugen des PDFs gingen Wörter verloren bzw. wurden an das Seitenende verschoben. Der ursprüngliche Satz lautete sinngemäß:
*„causing the model to invoke finish zero times across 1,184 steps...“* (oder *„fail to invoke finish...“*). Das Wort *„zero times“* wurde aus dem Satz gerissen und landete isoliert oben auf Seite 12!

---

### 3.2 Katastrophale Layout- und Seitenumbruchsdefekte

#### Defekt 1: Seitenübergang 3 auf Seite 4 (Zeilen 123–135)
- **Auf Seite 3 unten (Zeilen 123–128):**  
  Der Fließtext enthält mehrfach leere Referenzklammern:  
  `problem_statement, hints_text) (; ).`  
  `and SWE-bench_Verified) (; ).`  
  `official SWE-bench Verified leaderboard entry ().`
- **Auf Seite 4 oben (Zeilen 134–135):**  
  Direkt unter der Kopfzeile wurde ein unformatierter, zusammenhängender Block aus Referenzbezeichnungen in den Fließtext geschwemmt:  
  `Data Documentation, 2026Submission Audit, 2026cubieBenchmark Guide, 2026Submission Audit, 2026Single-Agent Report, 2026`  
  Dies zerstört das professionelle Erscheinungsbild vollständig und signalisiert den Gutachtern sofort eine unkontrollierte Markdown-zu-PDF-Konvertierung.

#### Defekt 2: Seitenübergang 11 auf Seite 12 (Zeilen 660–676)
- **Auf Seite 11 unten (Zeilen 660–662):**  
  Mitten im Satz bricht die Syntax ab:  
  `Over 1,184 model calls and 1,179 tool calls (6.98M input tokens), infrastructural errors dropped to , and Analysis located the target files within steps 0–13 across all tasks ().`  
  Der Wert hinter *„dropped to“* fehlt komplett.
- **Auf Seite 11 ganz unten (Zeile 669):**  
  Der Satz endet unvollständig mit: `and QA was never reached, (; ).`
- **Auf Seite 12 oben (Zeilen 674–676):**  
  Die fehlenden Satzbestandteile von Seite 11 erscheinen als verstümmelter Pseudo-Listenpunkt `6.` direkt vor Abschnitt 8:  
  `6. 0 cursor errors, 0 tool errors, and 0 context overflowsv9 Pilot Analysis, 2026zero timesthe qb-cubie framework instructions were never presented to the model in any v9 runv9 Pilot Analysis, 2026Submission Audit, 2026`  
  Hier wurden drei disparate Textfragmente („0 cursor errors...“, „zero times“, „the qb-cubie framework instructions...“) zu einer unlesbaren Zeile verklebt.

#### Defekt 3: Fehlerhafte Nummerierung in Abschnitt 7.2
Abschnitt 7.2 beschreibt vier Generationen (v6, v7, v8, v9), enthält jedoch sechs Listenpunkte:
- Punkt 1: v6
- Punkt 2: `2. v6 Pilot Analyses, 2026` (reine verirrte Quellenangabe als eigener Listenpunkt!)
- Punkt 3: v7
- Punkt 4: v8
- Punkt 5: v9
- Punkt 6: Das oben genannte Texttrümmerstück auf Seite 12.

#### Defekt 4: Systematisch verklebte Schriftart-Tags (Font Glitching)
Weil Markdown-Spans (wie `**qb-cubie**`, `*WorldState*` oder Inline-Code `` `PyVenv` ``) beim Rendern ohne Wortzwischenräume in das Layout überführt wurden, kleben im gesamten Dokument Wörter zusammen. Beispiele:
`ultiAgent`, `xampleBased`, `stLinter`, `yVenv`, `orldState`, `xceptionExpectation`, `ytestReporter`, `itHub`, `ycharmProjects`, `ingleAgent`, `alueError`, `eroAdmin`, `nFramework`, `benchIntegration`, `ontractSemantics`, `gentenGenerationen`, `loorEffect`.

---

## 4. Systematischer Abgleich gegen `Developer-Agent-Paper.md`

Die Ausschreibung des *Gemma 4 Developer Agent Competition (Paper Track)* definiert strenge formale Kriterien und eine fünfdimensionale Bewertungsrubrik (jeweils 0 bis 5 Punkte).

### 4.1 Formale Anforderungen & Compliance-Prüfung

| Anforderung lt. `Developer-Agent-Paper.md` | Vorgabe | Ist-Zustand in Revision -1 | Konformitätsstatus & Risiko |
| :--- | :--- | :--- | :---: |
| **Wortlimit (Scope)** | **Maximal 3.000 Wörter** | **5.478 Wörter** | **KRITISCHER VERSTOSS (+82,6 %)**<br>Akute Gefahr der Disqualifikation / Desk Rejection |
| **Titel & Untertitel** | Pflichtbestandteil | Vorhanden (prägnant und thematisch passend) | **Erfüllt** |
| **Abstract** | Pflichtbestandteil | Vorhanden (präzise Zusammenfassung der Hauptergebnisse) | **Erfüllt** |
| **Introduction** | Pflichtbestandteil | **Fehlt als explizites Kapitel.** Abschnitt 1 startet direkt mit „Research Question...“ | **Partiell erfüllt** (Inhalt vorhanden, Struktur weicht ab) |
| **Methods & Experiments** | Pflichtbestandteil | Abschnitte 2, 3, 4, 5, 7 decken dies herausragend ab | **Voll erfüllt** |
| **Related Works & Citations** | Pflichtbestandteil | Abschnitt 9 listet Referenzen; **es fehlt jedoch ein vergleichendes Kapitel zu verwandten Arbeiten** (SWE-agent, AutoCodeRover, etc.) | **Partiell erfüllt** |
| **Formatierung** | arXiv-ready PDF oder Kaggle Writeup | 13-seitiges PDF vorhanden, jedoch durch Layoutdefekte **nicht arXiv-ready** | **Nachbesserung zwingend** |

---

### 4.2 Thematische Passung & Track-Positionierung

Die Ausschreibung fordert:
> *„Post-train an open model into a reliable agent that navigates complex codebases and drafts fixes for real software issues, accelerating developer workflows on everyday hardware.“*

1. **Bezug zu Alltags-Hardware („Everyday Hardware“):**
   - Das Paper erfüllt diesen Kerngedanken in vorbildlicher Weise: Es evaluiert `gemma4:12b` (11.9B) lokal via Ollama unter 4-Bit-Quantisierung (Q4_K_M) auf einer einzelnen Entwickler-Workstation.
2. **Thematische Schwerpunkte der Ausschreibung:**
   - Die Ausschreibung nennt: *Tuning & Optimization (PEFT/RL)*, *Code Comprehension*, *Tasks & Benchmarks*, *Graph Reasoning*.
   - Das vorliegende Paper führt kein Post-Training oder Fine-Tuning durch. Es positioniert sich stattdessen primär im Bereich **Tasks & Benchmarks**, **Harness-Engineering** und **empirische Evaluation von Entwicklerwerkzeugen**.
3. **Optimale Track-Zuordnung für die Preisvergabe:**
   - **Best New Resource ($10.000):** Sehr hohe Erfolgschancen! Das Paper stellt mit `qb-cubie` (0.0.3, MIT-Lizenz, PyPI) ein neues deklaratives Testframework vor und liefert ein kryptografisch eingefrorenes Benchmarking-Harness für lokale SWE-bench-Aufgaben.
   - **Overall Best Paper ($15.000):** Als empirisches Methoden- und Negativresultate-Paper von herausragender wissenschaftlicher Aufrichtigkeit konkurrenzfähig, sofern Umfang und Form bereinigt werden.

---

### 4.3 Detaillierte Rubrik-Evaluation (Scoring 0 bis 5)

#### 1. Novelty (Neuartigkeit & Erkenntnisgewinn): **4,0 / 5,0**
- **Begründung:** Die detaillierte quantitative Dokumentation der **Reasoning Token Starvation** bei `gemma4:12b` (11 von 67 Modellaufrufen emittieren ausschließlich Denk-Tokens bis zum 8k-Limit, ohne JSON-Aktion, was 87,3 % aller Tokens und 79,6 % der Laufzeit vernichtet) ist ein hochgradig neuartiger, empirisch harter Befund für die lokale Agentenforschung. Ebenso neuartig ist der empirische Nachweis der Entkopplung von infrastruktureller Fehlerfreiheit und Workflow-Blockaden in Multi-Agenten-Systemen (v9).
- **Abzug (-1,0):** Es wird kein neuartiges Modell-Training oder Inferenz-Algorithmus vorgeschlagen; die Studie beschränkt sich auf Prompt- und Orchestrierungs-Iterationen.

#### 2. Quality (Methodische Strenge & Generalisierbarkeit): **3,5 / 5,0**
- **Begründung:** Das Zero-Leakage-Evaluierungskonzept (Strippen sichtbarer Test-Edits, isolierter Cubie-freier Evaluator-Container, private FAIL_TO_PASS/PASS_TO_PASS-Verifikation) ist methodisch absolut erstklassig und verhindert Bewertungszirkularität.
- **Abzug (-1,5):** Die empirische Basis ist mit 3 Aufgaben (Seed 42) sehr klein. Der massive Floor-Effekt (90,5 % EBT-Nichtnutzung in v1–v5; 0 % Rollenübergang in v9) verhindert eine echte statistische Aussagekraft über die Wirksamkeit von EBT gegenüber pytest.

#### 3. Relevance (Bedeutung für Agentic Software Engineering): **4,5 / 5,0**
- **Begründung:** Extrem hoher Wert für die Open-Source- und Gemma-Community. Während viele Publikationen optimistische Lösungsraten auf unzureichend isolierten Benchmarks präsentieren, deckt diese Arbeit die tatsächlichen operativen Barrieren auf, die kompakte 12B-Modelle bei realen Repository-Aufgaben scheitern lassen. Die Kaskaden-Hypothesen (H1–H4) bieten der Community einen klaren Fahrplan.

#### 4. Verifiability (Nachvollziehbarkeit & Reproduzierbarkeit): **4,3 / 5,0**
- **Daten & Code:** **4,8 / 5,0**. Vorbildlich. Alle 5.563 Hashreferenzen stimmen. Die vollständigen Transaktionen, Dockerfiles und Profile liegen im Repository vor und sind lokal nachvollziehbar.
- **Darstellung im PDF:** **3,8 / 5,0**. Die leeren Zitatklammern `(; )` und die zerrissenen Absätze auf den Seiten 3–4 und 11–12 erschweren die Verifikation im Dokument selbst.

#### 5. Clarity (Präsentation, Sprache & Struktur): **2,5 / 5,0**
- **Begründung:** Dies ist die gravierende Schwachstelle der aktuellen Einreichung:
  1. Das Wortlimit von 3.000 Wörtern wird um 2.478 Wörter überschritten.
  2. Die typografischen Katastrophen an den Seitenumbrüchen (Seiten 3→4 und 11→12) wirken unprofessionell.
  3. Der semantische Inversionsfehler in Abschnitt 7.2 behauptet das genaue Gegenteil der Messergebnisse.
  4. Die standardisierten Gliederunspunkte `Introduction` und `Related Works` fehlen als eigenständige Hauptüberschriften.
  5. Zahllose zusammengeklebte Font-Tags mindern den Lesefluss erheblich.

**Gesamt-Score (Mittelwert der 5 Kriterien): 3,66 / 5,0**

---

## 5. Dringender Aktionsplan vor dem Einreichungsschluss

Um das Paper vor einer Disqualifikation zu bewahren und die Bewertung auf ein Spitzen-Niveau (**~4,4 bis 4,6 Punkte**) zu heben, müssen folgende vier Schritte vor der Deadline (12. November 2026, 23:59 UTC) umgesetzt werden:

### 1. Radikale Straffung auf maximal 3.000 Wörter
- **Kürzungsbereich A (Abschnitt 1.1 & 1.2):** Die mathematische Formalisierung von EBT und die Details des internen `cubie`-Code-Audits (B1–B3) auf eine halbe Seite kondensieren.
- **Kürzungsbereich B (Abschnitt 4):** Die Entwicklungsschritte v1 bis v4 in einer kompakten Tabelle zusammenfassen, statt narrative Langtexte zu pflegen.
- **Kürzungsbereich C (Abschnitt 6):** Die Codex- und Antigravity-Hypothesen zu einem prägnanten 4-Punkte-Katalog verschmelzen.
- **Fokus wahren:** Die Kernbotschaften (Methodik, v5 Token Starvation, v9 Entkopplung) bleiben voll erhalten.

### 2. Behebung der Layout- und Rendering-Fehler (Markdown-to-PDF)
- **Seitenübergänge reparieren:** Die Markdown-Quelldatei bereinigen, sodass keine Referenzen oder Fußnoten aus den Tabellen und Absätzen gerissen werden.
- **Semantische Korrektur in v9:** Die Zeile 666 korrigieren:
  > *„causing the model to invoke finish **zero times** across 1,184 steps...“*
- **Schriftart-Abstände erzwingen:** Vor und nach Formatierungs-Tags (fett, kursiv, Code) explizite Leerzeichen setzen, um verklebte Wörter (`ultiAgent`, `orldState` etc.) zu beseitigen.
- **Nummerierung in 7.2 bereinigen:** Die verirrte Quellenangabe `2. v6 Pilot Analyses, 2026` aus der Aufzählung der Generationen entfernen (saubere Liste von 1 bis 4 für v6 bis v9).

### 3. Struktur an die Wettbewerbsvorgaben anpassen
- Einen expliziten Abschnitt **„1. Introduction“** einfügen, der das Problemfeld (Software Engineering mit kompakten Modellen auf Consumer-Hardware) motiviert.
- Einen kompakten Abschnitt **„Related Works“** ergänzen, der SWE-bench, existierende Agentenansätze (z. B. SWE-agent) und klassische Testansätze referenziert.

### 4. Einreichungs-Option wählen
- Sofern das 13-seitige PDF als „Public Project Link“ hochgeladen wird, sollte im Kaggle Writeup selbst eine exakt 3.000 Wörter umfassende Zusammenfassung gemäß den Vorgaben platziert werden, die auf das saubere, korrigierte PDF verlinkt.

---

## 6. Fazit

Revision -1 hat die gravierenden inhaltlichen Fehlinformationen der Vorversion (swegemma-Attribution) erfolgreich beseitigt und liefert eine wissenschaftlich fundierte, ehrliche und methodisch herausragende Analyse der Leistungsgrenzen von `gemma4:12b`.  
Wird nun noch die typografische Havarie behoben und der Text auf das vorgeschriebene Wortbudget von 3.000 Wörtern verdichtet, besitzt diese Arbeit exzellente Aussichten auf eine Auszeichnung im Track **Best New Resource** oder **Overall Best Paper**.
