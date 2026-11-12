# Kritische Analyse und Mängelrüge zur Paper-Submission „qb-cubie and Floor-Effect Analysis“

**Herkunft der Analyse:** Antigravity (Gemini-3.8-Flash)  
**Datum der Untersuchung:** 12. November 2026  
**Untersuchte Dokumente und Daten:**
- Primäres Prüfdokument: [G4DA Paper Submission - qb-cubie and Floor-Effect Analysis.pdf](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/G4DA%20Paper%20Submission%20-%20qb-cubie%20and%20Floor-Effect%20Analysis.pdf) (synthetisiert via Gemini-App / Gemini-4-Argon)
- Rohdaten, Konfigurationen und Laufarchive in [experiments/testguided-study/](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/)
- Paketkonfiguration und Codebasis des Hauptprojekts [cubie](file:///home/symphonie/PycharmProjects/cubie/)

---

## 1. Executive Summary & Gesamteinschätzung

Das untersuchte PDF-Dokument fasst die Entwicklungs- und Pilotläufe der Testguided-Studie (Generationen v1 bis v5 sowie die Multi-Agenten-Nachfolgeläufe v6 bis v9) für eine Einreichung im *G4DA Paper Track* zusammen.

Während die quantitativen Messwerte (Laufzeiten, Modell- und Werkzeugaufrufe, Tokenerfassung und Aufgabenresultate) in weiten Teilen exakt aus den Rohdatenarchiven unter [`experiments/testguided-study/runs/`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/) und den Voranalysen ([`ANALYSE-GENERATIONEN-V6-V9.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md), [`PAPER.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md)) übernommen wurden, enthält das Paper **schwerwiegende inhaltliche Falschbehauptungen, konzeptionelle Fehlinformationen sowie auffällige typografische Mängel**, die auf eine unzureichend redigierte LLM-Synthese (durch Gemini-4-Argon) zurückzuführen sind:

1. **Falschbehauptung zum Datensatzursprung:** Das Paper behauptet fälschlich, die Benchmark-Aufgaben stammten aus einem *„swegemma pool“*. In Wirklichkeit stammt der Datensatz aus dem etablierten **SWE-bench**-Ökosystem bzw. folgt strikt dessen Datenformat.
2. **Fehlbehauptung bzgl. `swegemma` im Projekt:** Das Paper stellt `swegemma` als festen internen Bestandteil des Versuchsaufbaus und der Evaluator-Brücke dar. **Tatsächlich ist `swegemma` in diesem Projekt (`cubie`) überhaupt nicht vorhanden** (weder in [`pyproject.toml`](file:///home/symphonie/PycharmProjects/cubie/pyproject.toml) noch in der Projektumgebung installiert).
3. **Krasse typografische Leerstellen und Textzerstörungen:** An mehreren Schlüsselstellen (Abstract, Abschnitt 1.1, Abschnitt 7.2) weist das PDF Textabrisse, Leerzeilen anstelle von Begriffen, versprengte Wörter und eine fehlerhafte Nummerierung auf (5 Listenpunkte für 4 Generationen).
4. **Kausale Fehlschlüsse bei der Ursachenanalyse:** Das 0:0-Ergebnis in v9 wird im Abstract und Fazit einseitig dem Sprachmodell zugeschrieben („repetitive orientation loops“). Dabei wird verschwiegen, dass das Harness-Design in v9 die `qb-cubie`-Anleitung erst bei der Rolle QA injiziert, QA wegen eines Controller-Fehlers aber nie aufgerufen wurde – das Testframework wurde dem Modell folglich gar nicht vorgelegt.

---

## 2. Detaillierte Mängelrüge der Falschbehauptungen & Fehlinformationen

### 2.1. Falschbehauptung: Datenursprung von „swegemma“ statt SWE-bench

#### Beanstandete Stelle im Paper
> *Abschnitt 2 (Seite 3, Zeilen 120–123):*  
> „The benchmark tasks originate from the local Gemma Developer Agent pool used with swegemma (Data Documentation, 2026). The source pool comprises 129 tasks across four Python repositories: 67 from FastAPI, 48 from Rich, 13 from Requests, and 1 from HTTPX. Because these tasks derive from public repositories, results do not represent an official SWE-bench Verified leaderboard submission (Study Report, 2026).“

#### Richtigstellung anhand der Projektrealität
1. **`swegemma` ist kein Datensatz:** `swegemma` (Version 0.2.11) war ein lokales Ausführungs- und Evaluierungswerkzeug (Harness) eines externen Projekts ([`devagent-comp`](file:///home/symphonie/PycharmProjects/devagent-comp/)), kein Schöpfer oder Eigentümer von Datensätzen.
2. **Der Datensatz folgt dem SWE-bench-Standard:** Die 129 Aufgaben aus den vier Repositories (`fastapi/fastapi`, `Textualize/rich`, `psf/requests`, `encode/httpx`) sind reale GitHub-Pull-Requests und -Issues, die exakt im Datenformat von **SWE-bench** strukturiert sind (`instance_id`, `repo`, `base_commit`, `patch`, `test_patch`, `problem_statement`, `hints_text`).
3. **Nativer SWE-bench-Benchmark in `cubie` vorhanden:** Das Repository [`cubie`](file:///home/symphonie/PycharmProjects/cubie/) verfügt über ein eigenes, voll ausgestattetes Benchmark-Paket unter [`src/qb_cubie/benchmarks/swebench/`](file:///home/symphonie/PycharmProjects/cubie/src/qb_cubie/benchmarks/swebench/) mit dem Vertrag `swebench-v1` und nativer Anbindung an die offiziellen HuggingFace-Datensätze (`SWE-bench/SWE-bench`, `SWE-bench_Lite`, `SWE-bench_Verified`).
4. **Fehlattribution:** Die Behauptung im Paper verwechselt ein externes Testwerkzeug mit der Datenquelle und verschleiert den eigentlichen Bezug zu SWE-bench.

---

### 2.2. Falschbehauptung: Vorhandensein und Rolle von `swegemma` im Projekt `cubie`

#### Beanstandete Stellen im Paper
> *Abstract (Seite 1, Zeilen 20–22):*  
> „An independent evaluator assesses exclusively the filtered production patch in a fresh, Cubie-free container...“  
> *Abschnitt 3.1 (Seite 4, Zeilen 212–214):*  
> „Using swegemma 0.2.11 , the production filter strips all modifications to visible test files and protected runner configurations.“  
> *Abschnitt 3.2 (Seite 5, Zeilen 265–266):*  
> „evaluator bridge via swegemma 0.2.11“

#### Richtigstellung anhand der Projektrealität
1. **`swegemma` ist in diesem Projekt gar nicht vorhanden:**
   - In [`pyproject.toml`](file:///home/symphonie/PycharmProjects/cubie/pyproject.toml) existiert weder unter `dependencies`, `optional-dependencies` noch `dependency-groups` ein Eintrag für `swegemma`.
   - In der virtuellen Umgebung von `cubie` (`.venv`) ist `swegemma` nicht installiert (`importlib.util.find_spec('swegemma')` liefert `None` / `False`).
2. **Lokaler Host-Shell-Trick verschleiert:** Der Start-Wrapper [`./study`](file:///home/symphonie/PycharmProjects/cubie/study) suchte per Shell-Skript explizit in *benachbarten* Projektverzeichnissen (`../devagent-comp/.venv/bin/python`) nach einer Python-Installation, die zufällig `swegemma` enthielt:
   ```bash
   for candidate in "$study_root/.venv/bin/python" "$study_root/../start-local-devagent/.venv/bin/python" "$study_root/../devagent-comp/.venv/bin/python"; do
     if [[ -x "$candidate" ]] && "$candidate" -c "import importlib.util; raise SystemExit(importlib.util.find_spec('swegemma') is None)" 2>/dev/null; then
       study_python="$candidate"
       break
     fi
   done
   ```
   Dies war ein reiner lokaler Workaround auf dem Entwicklerrechner und keine Projekteigenschaft von `cubie`.
3. **Autarke Multi-Agenten-Architektur ab v6:** In den Multi-Agenten-Generationen v6 bis v9 ([`testguided_study/team_workspace.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_workspace.py), [`testguided_study/team_v9.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v9.py)) wird `swegemma` für die Agentenausführung gar nicht mehr importiert oder aufgerufen; die Workspace-Verwaltung läuft rein über native `subprocess`-Aufrufe von `git` und Standard-Container.
4. **Wissenschaftliche Unredlichkeit:** Die Nennung von `swegemma 0.2.11` als offizieller Systembestandteil im Paper spiegelt unreflektierte Übernahmen aus fremden Notizen wider und widerspricht der tatsächlichen Repository-Struktur von `cubie`.

---

### 2.3. Typografische Entstellungen, Textlöcher und Rendering-Defekte (Gemini-4-Argon)

Die Synthese durch Gemini-4-Argon hat zu gravierenden Textababrissen und Layout-Defekten geführt:

| Stelle im PDF | Text im PDF | Tatsächlicher Inhalt / Fehlerursache |
| :--- | :--- | :--- |
| **Abstract (S. 1, Z. 15–17 u. 40)** | `...declarative quality assurance framework`<br>*(große Leerzeile)*<br>`—including its Example-Based Testing...`<br>*(Zeile 40 isoliert:)* `qb-cubie` | Der Name des Studiengegenstands `qb-cubie` wurde aus dem einleitenden Satz gerissen und isoliert am Ende des Abstracts platziert. |
| **Abschnitt 1.1 (S. 2, Z. 61–64 u. 75–76)** | `The open-source package`<br>*(Leerzeile)*<br>`(evaluated at version 0.0.3 , commit`<br>*(Leerzeile)*<br>`) integrates declarative...` | Paketname `qb-cubie` und Commit-Hash `5e50d22f80db90c4e8ae6e3aeedab6acdb981230` fehlen im Satz und stehen erst unterhalb der mathematischen Formel. |
| **Abschnitt 7.2 (S. 10, Z. 807)** | `...confirming Counter-Hypothesis V6-H8 (handoff overhead blocking progress) ().` | Leere Zitationsklammer `()`; Quellenreferenz ging bei der LLM-Synthese verloren. |
| **Abschnitt 7.2 (S. 11, Z. 812–834)** | Listeneintrag `2. publish_context → handoff v6 Pilot Analyses, 2026`<br>gefolgt von `3. v7`, `4. v8`, `5. v9` | Textfetzen aus v6 wurde zu Listenelement `2.` erhoben. Dadurch werden die **vier** Generationen v6–v9 als **fünf** Punkte (1 bis 5) nummeriert. |
| **Tabelle 7.1 (S. 9–10)** | `Generatio n& Archive ID`, `Dominant Terminatio n Cause`, `finishe d`, `stagnati on`, `ValueErr or`, `interrup ted`, `budget_e xhausted` | Zerstörte Worttrennungen und Spaltenausrichtungen durch mangelhafte Tabellenformatierung in der Synthese. |
| **Tabelle v5 (S. 7)** | Verrutschte Tabellenzellen | Laufzeiten, Aufrufzahlen und Abbruchgründe driften horizontal und vertikal auseinander. |

---

### 2.4. Brüche in der Dokumentenkette und Referenzierung

1. **Veralteter Stand von Referenz 1 ([`PAPER.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md)):**  
   Das Paper führt in Abschnitt 9 als Hauptbeleg `Study Report (2026): experiments/testguided-study/PAPER.md, data cutoff: November 11, 2026` an.  
   *Tatsache:* [`PAPER.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md) endet am 11.11.2026 mit Pilot v5. Die in Abschnitt 7 des Papers ausführlich dargestellten Multi-Agenten-Generationen v6 bis v9 existieren in [`PAPER.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md) überhaupt nicht. Sie wurden erst am 12.11.2026 in [`ANALYSE-GENERATIONEN-V6-V9.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md) niedergelegt. Das Paper erweckt den falschen Eindruck eines einheitlichen Gesamtreports.
2. **Fehlende Pfadgenauigkeit bei Referenz 20 ([`GUTACHTEN.md`](file:///home/symphonie/PycharmProjects/cubie/GUTACHTEN.md)):**  
   Das externe Gutachten wird ohne Pfad zitiert. Es liegt im Projekt-Wurzelverzeichnis [`GUTACHTEN.md`](file:///home/symphonie/PycharmProjects/cubie/GUTACHTEN.md), nicht im Studienordner.
3. **Widerspruch zur Open-Source-Reproduzierbarkeitsbehauptung:**  
   Das Paper wirbt prominent mit vollständiger Open-Source-Reproduzierbarkeit auf GitHub. Die vorbereitenden Artefakte ([`DATEN.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/DATEN.md), [`candidate-selection.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/candidate-selection.json)) verweisen jedoch auf lokale Festplattenpfade (`/home/symphonie/PycharmProjects/devagent-comp/...`), die externen Nutzern nicht zur Verfügung stehen.

---

### 2.5. Methodische Verzerrungen bei der Interpretation des Floor-Effects

1. **Verschleierung des Interface-Versagens in Generation v9:**  
   Das Paper argumentiert in Abschnitt 7.2 und im Fazit, dass in v9 trotz perfekter Infrastruktur (0 Cursor-Fehler, 0 Werkzeug-Fehler) das Modell versagt habe, weil es in einer 82,6%igen Orientierungsschleife gefangen blieb.  
   *Tatsächliche Ursache:*
   - In [`team_v9.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v9.py) wurde der Zwangswechsel (`forced handoff` bei `repeat_count >= 3`) aus v8 gelöscht.
   - Das Werkzeug `finish` wurde im Systemprompt mit Review-Parametern (`verdict="verified"|"rework"`) überladen, wodurch das Modell es in der Orientierungsphase für unpassend hielt und nie aufrief.
   - Da die Anleitung für `qb-cubie` in v9 erst bei der Aktivierung der QA-Rolle geladen wird (`team_v9.py:615`), QA aber nie betreten wurde, **konnte das Modell `qb-cubie` gar nicht verwenden**. Dies als Beleg für die Unwirksamkeit des Frameworks unter Floor-Bedingungen darzustellen, ist ein methodischer Zirkelschluss.
2. **Unterdrückung der extremen EBT-Nichtnutzungsrate:**  
   Das Paper hebt hervor, dass in revised v3 (`180702`) eine Lösung mit `qb-cubie` gelang (6 EBT-Verträge ausgeführt). Im Abstract und Fließtext wird jedoch nur beiläufig erwähnt, dass über **alle 21 Cubie-Läufe der Generationen v1–v5 hinweg nur in 2 einzigen Läufen (9,5 %) überhaupt ein EBT-Vertrag ausgeführt wurde**. In 90,5 % der Fälle kam es nie zur Anwendung des Testframeworks.

---

## 3. Datenverifikations-Matrix (Paper vs. Rohdaten)

| Parameter / Kennzahl | Angabe im PDF | Tatsächlicher Wert in Rohdaten | Bewertung |
| :--- | :--- | :--- | :--- |
| **Geprüfte Aufgaben im Katalog** | 39 geprüft (26 Kandidaten, 9 bedingt, 3 zurückgestellt, 1 ausgeschlossen, 90 ungeprüft) | 39 geprüft (26 candidate, 9 conditional, 3 deferred, 1 excluded, 90 unreviewed) | **Korrekt** ([`candidate-catalog.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/candidate-catalog.json)) |
| **Private Tests: `fastapi_9425`** | 1 FAIL_TO_PASS / 8 PASS_TO_PASS | 1 F2P / 8 P2P (Base: `F........`, Gold: `.........`) | **Korrekt** ([`preflight/references.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/20261111-200641/frozen/preflight/references.json)) |
| **Private Tests: `requests_6589`** | 1 FAIL_TO_PASS / 11 PASS_TO_PASS | 1 F2P / 11 P2P (Base: `F...........`, Gold: `............`) | **Korrekt** ([`preflight/references.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/20261111-200641/frozen/preflight/references.json)) |
| **Private Tests: `rich_3278`** | 16 FAIL_TO_PASS / 7 PASS_TO_PASS | 16 F2P / 7 P2P (Base: 16x `F`, 7x `.`, Gold: 23x `.`) | **Korrekt** ([`preflight/references.json`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/20261111-200641/frozen/preflight/references.json)) |
| **Laufanzahl Single-Agent (v1–v5)** | 7 Piloten, 42 Agentenläufe, 1 Vorbereitung | 7 fertige Archive (132401, 160158, 163110, 171515, 180702, 192412, 200641) + 180104 | **Korrekt** |
| **Verifizierte Lösungen (v1–v5)** | 3 von 42 (7,1 %): pytest in 163110 u. 192412, Cubie in 180702 | 3 von 42: pytest in 163110 u. 192412, Cubie in 180702 | **Korrekt** |
| **Auditierte SHA-256 Hashes** | 5.563 Referenzen geprüft (100 % Übereinstimmung) | 5.563 Referenzen in Manifesten und `ready.json` | **Korrekt** ([`PAPER.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md#L269)) |
| **Laufzeit v5 Pilot (200641)** | 4.476,4 s (74,6 min) | Summe aller 6 Läufe: 727,4 + 681,4 + 829,3 + 900,1 + 653,5 + 684,7 = 4.476,4 s | **Korrekt** |
| **Aufrufe v5 Pilot (200641)** | 67 Modellaufrufe, 55 Werkzeugaufrufe | 67 Modellaufrufe (32 pytest, 35 Cubie), 55 Werkzeugaufrufe | **Korrekt** |
| **Output-Token-Verlust in v5** | 11 Calls am Limit (8.192 Tokens), 90.112 Tokens (87,3 %) | 11 Truncations: 11 * 8.192 = 90.112 von 103.235 Tokens = 87,288 % | **Korrekt** |
| **Multi-Agenten Läufe (v6–v9)** | 17 ausgeführte Läufe, 1.441 Modell-Calls, 1.432 Tool-Calls | Exakt 1.441 Modell-Calls, 1.432 Tool-Calls, 0 gelöst | **Korrekt** ([`ANALYSE-GENERATIONEN-V6-V9.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md#L36-L44)) |
| **Duplikate in Generation v9** | 974 Duplikate (82,6 %) | 974 von 1.179 Aktionen redundant | **Korrekt** ([`ANALYSE-GENERATIONEN-V6-V9.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md#L42)) |
| **Präsenz von swegemma im Projekt** | Behauptet als interne Bridge | **Nicht vorhanden** (`False`) | **FALSCHBEHAUPTUNG** |
| **Datensatz-Herkunft** | „swegemma pool“ | **SWE-bench / GitHub PRs** | **FEHLINFORMATION** |

---

## 4. Handlungsempfehlungen zur Bereinigung der Paper-Fassung

1. **Klarstellung der Datenherkunft (SWE-bench):**
   Ersetzen aller Formulierungen wie *„swegemma pool“* durch *„SWE-bench benchmark instances (FastAPI, Requests, Rich, HTTPX) adapted for test-guided evaluation“*.
2. **Entfernung der Falschbehauptung bzgl. `swegemma` als interner Bridge:**
   Klarstellen, dass `cubie` ein autarkes Open-Source-Framework ist, dessen native Benchmark-Architektur auf `qb_cubie.benchmarks.swebench` aufbaut, und dass die Auswertung in isolierten Docker-Containern gegen private Test-Suiten erfolgte.
3. **Reparatur der typografischen Defekte im PDF:**
   - Abstract: `qb-cubie` an der korrekten syntaktischen Stelle wieder einfügen.
   - Abschnitt 1.1: Paketnamen `qb-cubie` und Commit-Hash `5e50d22f80db90c4e8ae6e3aeedab6acdb981230` im Fließtext verankern.
   - Abschnitt 7.2: Zitat `Counter-Hypothesis V6-H8` vervollständigen und die fehlerhafte Aufzählung bereinigen (exakt 4 Punkte für die Generationen v6, v7, v8, v9).
   - Tabellen 4.1, 5 und 7.1 im Satzspiegel sauber formatieren, um Silbenabbrüche zu vermeiden.
4. **Präzisierung der Referenzen:**
   Referenz 1 und 24 klar abgrenzen: [`PAPER.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/PAPER.md) dokumentiert die Single-Agent-Reihe v1–v5; [`ANALYSE-GENERATIONEN-V6-V9.md`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md) dokumentiert die Multi-Agent-Reihe v6–v9.

---
*Persistiert im Projekt unter:* `experiments/testguided-study/KRITISCHE-ANALYSE-PAPER-SUBMISSION.md`  
*Analysiert und erstellt durch Antigravity (Gemini-3.8-Flash).*
