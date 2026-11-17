<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Hydrogen" effort="XHigh" -->
# Post-Hoc Audit 2

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Hydrogen
- **Reasoning-Effort:** XHigh
- **Analysedatum:** 17. November 2026, ~ 08:15 (CET)
- **Synthesebasis:**
  - `../../testguided-study`
  - `../post-analysis-1/ANALYSIS_1.md`
- **Stand:** qb-cubie (v0.0.7)
- **Git-Log:** `git log -n 1`
```text
commit 7e08e2ac7a39586fe4ce9dfff209ee11810ea0ca (HEAD -> main, origin/main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Mon Nov 16 08:50:29 2026 +0100

    Double-Check
```

---

---

<!-- /qb:frame -->

# Post-Studien-Audit: Praktiken, Muster und Konventionen in `../../testguided-study`

## 1. Gegenstand, Synthesebasis und Abgrenzung zu Audit 1

Dieser zweite wertungsfreie Audit untersucht auf Basis von [`../../testguided-study`](../../testguided-study), der zugehörigen Test-Suite [`../../tests/testguided_study_design`](../../tests/testguided_study_design), der Repository-Historie sowie [Post-Hoc Audit 1](../post-analysis-1/ANALYSIS_1.md) gezielt die **Praktiken, wiederkehrenden Muster und Konventionen**, die sich während dieser agilen („aus dem Stegreif“ entstandenen) Studie herauskristallisierten.

Während [Audit 1](../post-analysis-1/ANALYSIS_1.md) schwerpunktmäßig die Datenlage und die Faktentreue von Dimension **B** gegen `runs/` prüfte, kartiert Audit 2 den gesamten Bogen über alle drei Dimensionalitäten (**A**: Experimente mit `gemma4:12b`; **B**: KI-gestützte Forschung, Design, QA und Code/Tests `B.1–B.5`; **C**: synthetische Paper-Erzeugung und Begutachtung) einschließlich ihrer Vorlaufwurzeln und ihrer späteren Formalisierung in `qb_cubie` (`v0.0.4`–`v0.0.7`).

### 1.1 Unabhängige Verifikation und Präzisierung der Synthesebasis

Alle quantitativen Befunde aus Audit 1 wurden vor der Auswertung direkt an den Rohdaten, Quelltexten, PDF-Extrakten und der AST-/Pytest-Sammlung gegengeprüft. Dabei bestätigten sich die Hauptbefunde aus Audit 1; an drei Stellen ergaben die Rohdaten weiterführende Präzisierungen:

1. **Tatsächliche EBT-Nutzungsquote in B.5 (`77,7 %` statt `71,6 %`):**  
   Audit 1 erfasste über die Suche nach `EBT(` und `v6_support.contract()` insgesamt `550` von `768` gesammelten Pytest-Nodes (`71,6 %`). Eine vollständige AST-Auswertung aller Hilfs-Wrapper in [`../../tests/testguided_study_design`](../../tests/testguided_study_design) zeigt, dass auch [`test_session_integration.py:84-86`](../../tests/testguided_study_design/test_session_integration.py#L84-L86) (`check()`, genutzt in `test_session_integration.py` und `test_unlimited_budgets_ebt.py`) sowie [`test_iteration_ebt.py:31-34`](../../tests/testguided_study_design/test_iteration_ebt.py#L31-L34) (`rejects()`) intern jeweils `EBT(...).run()` aufrufen. Damit führen in `testguided_study_design/` **236 von 305 Testfunktionen (580 von 701 Nodes = 82,7 %)** und in `testguided-study/tests/` **3 von 41 Testfunktionen (17 von 67 Nodes = 25,4 %)** direkt `qb_cubie.EBT` aus — insgesamt **239 von 346 Testfunktionen (69,1 %)** bzw. **597 von 768 gesammelten Pytest-Nodes (77,7 %)**. Der leichte Dateizähl-Unterschied in `testguided_study_design/` (`41` `.py`-Dateien / `7.087` LOC gegenüber `40` / `7.050` LOC in Audit 1) ergibt sich aus der Fixture [`fixtures/v6/app.py`](../../tests/testguided_study_design/fixtures/v6/app.py) (`37` LOC).
2. **Dreistufige Erosion der `swegemma`-Zuschreibung in Dimension C:**  
   Anders als die verkürzte Darstellung in Audit 1 („dass `swegemma` aus den Revisionen `-1` bis `-4` entfernt wurde“) zeigen die aus allen fünf Einreichungs-PDFs extrahierten Texte eine schrittweise Abwehr-Mutation: Die Ausgangsfassung (`Analysis.pdf`, `3` Treffer) benannte `swegemma 0.2.11` korrekt als Evaluator-Brücke; die Revisionen `-1` (`3` Treffer), `-2` (`2` Treffer) und `-3` (`2` Treffer) hielten `swegemma` in einem defensiven Abschnitt (*„Repository Autonomy“*) als angeblich bloßes v1–v5-Host-Relikt aufrecht (obwohl [`execution.py:130, 137`](../../testguided-study/testguided_study/execution.py#L130-L137) und [`team_workspace.py:212`](../../testguided-study/testguided_study/team_workspace.py#L212) auch in v6–v9 weiter auf `swegemma` und `_swegemma_baseline` aufsetzen). Erst Revision `-4` und [`g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md`](../../testguided-study/g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md) strichen den Begriff vollständig (`0` Treffer).
3. **Differenzierung der `local/`-Infrastruktur (`12` Ordner):**  
   Unter [`../../testguided-study/local`](../../testguided-study/local) liegen neben `build/` exakt elf chronologisch gestaffelte Vorlauf-, Smoke- und Launch-Prüfverzeichnisse (`api-probe`, `smoke-*`, `launch-real-check*`, `pilot-launch-final`, `live-pilot-validation`), die eine eigenständige operative Pre-Flight-Praxis vor dem ersten Produktivlauf (`20261111-132401`) dokumentieren.

---

## 2. Entwicklungsbogen der Studienpraktiken (Vorlauf → Sprint → Nachhärtung)

Die in `../../testguided-study` beobachtbaren Konventionen entstanden nicht im Vakuum innerhalb der 35 Stunden vom 11. bis 12. November 2026, sondern bilden die mittlere Phase einer dreistufigen Entwicklungskette im Repository:

| Phase & Zeitraum | Git-Anker | Zentrale Artefakte | Prägende Praktiken und Konventionen |
| :--- | :--- | :--- | :--- |
| **Phase 0: Vorlauf** (bis 10.11.2026, vor `eda23718`) | `b8d536eb`–`5d962834`, historisch sichtbar in `c5ea5538^` | `tests/docs_tmp/` (`AGENTEN_CASES_5_1..5_5.md`, `BENCHMARK_CASES_10_1..10_5.md`, `CONTRACT_CASES_9_1..9_2.md`), [`GUTACHTEN.md`](../../../GUTACHTEN.md) | Phasenbezogene `*_CASES_*.md`-Verträge (mit In-place-Statusänderung von Rot auf Grün), striktes Verbot von `xfail`/Abschwächung, Replay-Transportgrenzen, manuelle Snapshot-Commits (`Random Checkpoint`, `Gutachten-Empfehlung Nr. ...`). |
| **Phase 1: Agiler Studiensprint** (11.–13.11.2026) | `eda23718` (11.11. 16:05) bis `32434293` (13.11. 23:15) | `runs/` (13 Archive), `local/` (12 Ordner), flache Analyse-/Hypothesen-/Design-Markdowns, `*_CASES.md`, 5 PDFs + Gutachten | Ausdifferenzierung in getrennte Rollen/Modelle (`Chronuid`, `Codex / GPT-6.1-Sol`, `Antigravity / Gemini-3.8-Flash`, `Gemini-App / Gemini-4-Argon`), Übergang zu unveränderlichen Versionsdokumenten (`-V4`..`-V9`), Live-Dump-Hypothesen mit `Dokument-Informationen & Herkunft`, parallele Controller-Vererbung, Kaggle-Paper-Audits. |
| **Phase 2: Nachhärtung in `qb_cubie`** (13.–16.11.2026) | `32434293` bis `7e08e2ac` (HEAD) | [`DocEnsurance`](../../../src/qb_cubie/services/doc_ensurance/), [`DocFrame`](../../../src/qb_cubie/services/doc_frame/), [`GUIDE_Quality-Assurance.md`](../../../docs/GUIDE_Quality-Assurance.md), [`DEV-GUIDE_Next-Steps.md`](../../../docs/dev/DEV-GUIDE_Next-Steps.md), [`META_QUESTION.md`](../../../META_QUESTION.md) | Generalisierung von Provenance-Köpfen (`CUBIE_DOC_FRAME_2`), lebenden Guide-Beispielen (`CUBIE_DOC_STYLE`), TGD-5-Schritt-Regeln ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$) und 1:1-Orakel-Paarung in produktive Paket-Services bei bewusster Quarantäne von `experiments/` und `GUTACHTEN.md`. |

Eine in der Git-Historie archivierte Selbstreflexion des Maintainers (`docs/misc/klarstellung-commit-historie.md`, in Commit `03bdcadf` vor der späteren Löschung in `a8b22b57`) ordnet dabei die Entstehungspraxis explizit ein: Rund **99 %** des Quellcodes seien durch KI-Agenten entstanden, während rund **95 %** der Git-Commits manuell durch das Hochzählen im Terminal (`Pfeiltaste-Hoch` bei `Checkpoint`- und `Gutachten`-Meldungen) erfolgten und nur rund **5 %** (darunter ausgerechnet formale `chore:`/`release:`-Meldungen) eng begleitet von Agenten abgesetzt wurden.

---

## 3. Praktiken, Muster und Konventionen in Dimension A (Experimente, Pre-Flight & Laufzeitverhalten)

### 3.1 Gestufte Pre-Flight- und Gatekeeping-Kultur (`local/`, `admission.py`, `smoke.py`, `campaign.py`)

Bevor am 11. November 2026 um `13:24:01` der erste vollständige Pilotlauf gestartet wurde, durchlief der Studienaufbau innerhalb einer Stunde (`12:18` bis `13:19 Uhr`) eine explizite **Stufen-Eskalation lokaler Technikproben** in [`../../testguided-study/local`](../../testguided-study/local):

1. **Protokoll-Handshake (`api-probe`, `12:20`):** Ein einzelner minimierter Ollama-Aufruf (`48` Input-Tokens, `15` Output-Tokens, `num_ctx=4096`, `temperature=0`, `seed=42`) prüfte zunächst ausschließlich, ob `gemma4:12b` mit `think=false` ein schema-konformes JSON (`{"action": "list_files", "stage": "inspect"}`) zurückgibt.
2. **Synthetischer Infrastruktur-Smoke (`smoke-input` → `smoke-ready`, `12:18–12:19`, wiederholt als `smoke-types-v2-*`, `12:38`):** [`smoke.py`](../../testguided-study/testguided_study/smoke.py) generiert ein synthetisches Mini-Repository (`bounds.py`), markiert es maschinenlesbar mit `study_id = "plumbing-smoke-not-evidence"`, `task_type = "infrastructure_smoke"` sowie dem Rückgabezweck `"Synthetic infrastructure smoke, never study evidence"` ([`smoke.py:57`](../../testguided-study/testguided_study/smoke.py#L57)) und schließt es hart aus jeder späteren Qualifikation aus ([`campaign.py:79`](../../testguided-study/testguided_study/campaign.py#L79)).
3. **Reale Zulassungs-Iterationen (`launch-real-check` → `-v2` → `-v3` → `-v4`, `13:09–13:13`):** Die erhaltenen `failure.json`-Artefakte dokumentieren eine schrittweise Fehlerisolierung vor der Modellinferenz: Image-Build-Fehler (`v1`) → korrupter Patch bei `git apply /tmp/tests.patch` (`v2`) → fehlgeschlagene automatische Task-Zulassung für `rich_3882` (`v3`) → erfolgreicher Freeze (`v4`) → Abschlussprüfung (`pilot-launch-final`, `13:16`) → 60-Sekunden-Mini-Live-Validierung mit `report.json` (`live-pilot-validation`, `13:19`).

Aus dieser Startpraxis etablierten sich vier dauerhafte **Schutzkonventionen in Dimension A**:

- **Anti-Kontaminations-Stripping im Treatment-Image:** [`Dockerfile.cubie:8`](../../testguided-study/Dockerfile.cubie#L8) entfernt nach der Installation von `qb_cubie` im Docker-Container gezielt die experimentellen Daten- und Agentenpakete (`cubie_benchmarks`, `ollama_agents`, `/usr/local/bin/cubie-bench`), sodass im Treatment-Container ausschließlich die Prüf-API ohne historische Benchmarkdaten vorliegt.
- **Hermetische Container- und Plugin-Isolierung:** [`Dockerfile.pytest:8-9`](../../testguided-study/Dockerfile.pytest#L8-L9) deaktiviert das automatische Pytest-Plugin-Laden (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) und legt ein Dummy-`/sandbox/setup.py` (`raise SystemExit(0)`) an; [`backend.py:45-46, 169-171`](../../testguided-study/testguided_study/backend.py#L45-L46) blockiert Host-Setup-Skripte und lädt gezielt nur task-spezifische Plugins (`pytest_httpbin.plugin` ausschließlich für `psf/requests`). [`artifacts.py:151-160`](../../testguided-study/testguided_study/artifacts.py#L151-L160) lehnt Snapshots mit `.git`, Symlinks oder privaten Pfadnamen (`evaluator`, `secret`, `evidence`) vor dem Freeze ab.
- **Kryptographisch erzwungenes Qualifikations-Gate (`campaign.py`):** Die Hauptmessphase (`phase = "measurement"`) lässt sich nicht über ein Konfigurationsflag freischalten ([`campaign.py:1`](../../testguided-study/testguided_study/campaign.py#L1): *„Bind measurement admission to archived development evidence, never to a flag“*). [`campaign.py:27-106`](../../testguided-study/testguided_study/campaign.py#L27-L106) verlangt verifizierte Entwicklungsarchive, schließt alle zuvor genutzten Tasks und deren `related_group` für Messungen aus und fordert pro Studienarm mindestens zwei unabhängig gelöste Gruppen inklusive beobachtetem `behavior_cycle` (Assertion-Rot → unveränderte Testversion → Produktionsänderung → Grün).
- **Nachgelagerte Baseline-Protokollierung (`visible-baseline.json`):** Nachdem [`TECHNIKANALYSE-20261111-171515.md:84-119`](../../testguided-study/TECHNIKANALYSE-20261111-171515.md#L84-L119) `65` vorbestehende Fehler in Rich und `8` Collection-Fehler in FastAPI aufgedeckt hatte, protokollierte der Preflight-Schritt ab Lauf `20261111-180702` in allen acht verbliebenen Läufen vorab `frozen/preflight/visible-baseline.json`, um Altlasten von Agentenregressionen zu trennen.

### 3.2 Artefakt-Architektur, Monitor-Hygiene und Konfigurations-Drift

Jedes Laufarchiv unter `runs/<YYYYMMDD-HHMMSS>/` folgt einem stabilen Layout aus Vorab-Verifikation (`admission/`, `prepared/`, `setup/`), kryptographischem Freeze (`frozen/manifest.json`, `ready.json`, `designs/*.json`), Live-Telemetrie (`monitor/`) und Einzelschritt-Transkripten (`frozen/runs/0001..0006/steps/NNNN-{request,response,tool}.json`, ab v6 ergänzt um `actions/` und ab v9 um `transactions/`).

Im Live-Monitor ([`monitor.py`](../../testguided-study/testguided_study/monitor.py), [`monitor.html`](../../testguided-study/testguided_study/monitor.html)) galt als Konvention **strikte Nicht-Einmischung und Darstellungsehrlichkeit**: Der Server bindet ausschließlich lokal (`127.0.0.1`), erlaubt keinerlei Eingriffe in laufende Agenten, liefert keine privaten Dateien aus und simuliert ausdrücklich kein Token-Streaming ([`README.md:96-100`](../../testguided-study/README.md#L96-L100)), während die UI `1`-basierte Schrittnummern auf `0`-basierte Archivindizes abbildet.

Gleichzeitig zeigt der direkte Vergleich von `configured.toml`, TOML-Profilen und Git-Historie zwei typische **Konfigurations-Konventionen des schnellen Iterierens**:

1. **Stehenbleibende `study_id`-Etiketten:** Sämtliche acht Single-Agent-Archive `20261111-132401` (v1) bis `20261111-200641` (v5) tragen in `configured.toml` unverändert `study_id = "cubie-testguided-pilot-v2"`; die faktische Generation ist nur über `frozen/designs/*.json` und `agent_version` rekonstruierbar.
2. **Retroaktives Überschreiben von Budget-TOMLs und Hard-Override im Loader:** Nach Abbruch von `v7-1` (`20261112-013246`, mit `wall_seconds = 900, model_calls = 48, tool_calls = 96`) wurden im Commit `5976fc90` sowohl `profiles/pilot.toml` als auch bereits eingecheckte [`v6.toml:27-29`](../../testguided-study/v6.toml#L27-L29) rückwirkend auf `1800 / 0 / 0` geändert. Zusätzlich überschreibt [`artifacts.py:107-108`](../../testguided-study/testguided_study/artifacts.py#L107-L108) beim Laden pauschal jeden älteren Budgeteintrag:
   ```python
   # Accept old configuration files, but never reinstate call-count limits.
   config['budgets'].update(model_calls=0, tool_calls=0)
   ```
   Dadurch bleiben historische Freeze-Archive in `runs/` unverändert, während das Nachladen alter TOML-Dateien über die aktuelle Codebasis stillschweigend andere Budgetregeln erzwingt.

### 3.3 Wiederkehrende Verhaltensmuster von `gemma4:12b` auf Steuerungskonventionen

Die direkte Auswertung aller Schritt- und Team-Protokolle über die 13 Archive in `runs/` macht vier empirische Reaktionsmuster des lokalen 12B-Modells auf die wechselnden Agentenkonventionen sichtbar:

| Konventions-Mechanismus | Generationen | Beobachtete Modellreaktion in `runs/` |
| :--- | :--- | :--- |
| **Selbstberichts- & Metadaten-Pflicht** (`stage`, `update_ledger`, `note`, `analyze`, `update_context`) | v1–v8 | In v2 (`163110`) beanspruchte `update_ledger` **39 von 111** Modellaufrufen (**35,1 %**) und maskierte Stillstand; optionale `note`-Felder sanken von **66,2 %** (`49/74`, v3 `171515`) und **56,2 %** (`50/89`, v3 rev. `180702`) auf **8,1 %** (`8/99`, v4) und **0,0 %** (`0/67`, v5); in v6 sprangen sie auf **98,5 %** (`65/66`), führten aber in keine Übergabe; in v8 unterblieb manuelles `update_context` trotz korrekter Codefunde (`job-12` → `job-20` mit `materials: []`). |
| **Erweiterte Navigations- und Steuerungs-Schemas** | v6–v9 | Von `1.432` Werkzeugaktionen entfielen **90,7 %** (`795` `search_content`, `504` `read_file`) auf bloßes Suchen und Lesen; in v9 wurde `finish` in `1.184` Schritten **0-mal** aufgerufen (**82,6 %** Duplikate, `974/1.179`). |
| **Textuelle Recovery-Hinweise ohne Controller-Übergang** | v6, v7-2, v9 | In keinem einzigen Fall über alle Läufe löste ein in den User-Prompt injizierter Recovery-Text eine Rollenübergabe oder einen Richtungswechsel aus; wiederholte identische Dialoge in der History verstärkten im Gegenteil repetitive Muster (`32×` `find_paths` in v7-2, `62×` identischer Read in v9/`0003`). |
| **Container-I/O-Skalierung bei großen Repositories** | v9 (`20261112-035522`) | Durch ungecachte `V9RemoteWorkspace.inventory()`-SHA-256-Scans per Docker-`exec` ([`team_v9.py:580`](../../testguided-study/testguided_study/team_v9.py#L580), [`team_workspace.py:265-276`](../../testguided-study/testguided_study/team_workspace.py#L265-L276)) lag die Nicht-Modell-Zeit in `fastapi_9425` (`0001`, Laufzeit `1.810,6 s`, davon `557,5 s` Modell und `128,3 s` Tool-Ausführung) in Stichproben bei ~`6,3–6,4 s` für `tool → next_req` und ~`7,7–9,9 s` für `resp → tool`, gegenüber `0,33 s` bzw. `0,37 s` in `requests_6589` (`0003`). |

---

## 4. Praktiken, Muster und Konventionen in Dimension B (Forschung, Wissenssynthese & Test-Engineering)

### 4.1 Benennungs-, Sprach- und Provenance-Konventionen (`B.1`–`B.4`)

In Dimension B bildete sich eine scharfe, weitgehend stabile **Dokumenten- und Sprachtaxonomie** heraus:

1. **Dateinamen-Konventionen nach Funktion und Autorenschaft:**
   - **Grundlagen- und Statuspapiere:** Deutsche Großbuchstaben-Nomen im Studien-Root (`PROTOKOLL.md`, `DATEN.md`, `KANDIDATEN.md`, `VALIDIERUNG.md`, `PAPER.md`), flache Kleinschreibungs-Guides unter `guides/` (`cubie.md`, `pytest.md`).
   - **B.1 Deskriptive Analysen:** Verknüpfung von Analysetyp und Laufarchiv-ID (`TECHNIKANALYSE-20261111-171515.md`, `PILOTANALYSE-20261111.md`, `PILOTANALYSE-20261111-192412.md`, `PILOTANALYSE-20261112-002038.md`), ab der Multi-Agenten-Nacht erweitert um Generation und KI-System (`PILOTANALYSE-V6-20261112-002038-CODEX.md`, `PILOTANALYSE-V9-20261112-035522.md`, `ANALYSE-GENERATIONEN-V6-V9.md`).
   - **B.2 Hypothesenpapiere:** Formale Gesamtsynthesen mit Datum (`HYPOTHESEN-URSACHENANALYSE-20261111.md`, `URSACHENANALYSE-CODEX-20261111.md`) gegenüber nächtlichen Live-Dump-Diagnosen im englischen Benennungsschema `<HYPOTHESIS>-<GEN>-<PROVIDER>-<MODEL>-<EFFORT>.md` (`HYPOTHESIS-V6-GEMINI-ARGON-HIGH.md`, `HYPOTHESIS-V7-...`, `HYPOTHESIS-V8-...`).
   - **B.3/B.4 Design & QA:** `AGENTENDESIGN.md` (v1–v3) und `AGENTENDESIGN-V4..V9.md`; `IMPLEMENTIERUNG-V7..V9.md` im Studien-Root; `<SCOPE>_CASES.md` (`PILOT_TECHNICAL_CASES.md`, `PILOT_180702_CASES.md`, `MONITOR_CONTEXT_CASES.md`, `RUN_MANAGEMENT_CASES.md`, `V6_CASES.md`..`V9_CASES.md`) getrennt in [`../../tests/testguided_study_design`](../../tests/testguided_study_design).
   - **B.5 Testmodule:** Rollenspezifische Suffixe (`test_*_ebt.py`, `test_*_runtime.py` / `test_*_runtime_ebt.py`, `test_*_boundaries.py`, `test_*_integration.py`, `v6..v9_support.py`, `fixtures/*.cjs`).
2. **Zweisprachige Schnittstellen-Konvention:**  
   Die gesamte Forschungs-, Design- und Abnahmedokumentation (`PROTOKOLL`, Analysen, Hypothesen, Designs, `*_CASES.md`, `IMPLEMENTIERUNG-*.md`) ist auf **Deutsch** verfasst (mit englischen Feld- und Schema-Bezeichnern). Umgekehrt sind sämtliche an das Studienmodell gesendeten Prompts (`guides/*.md`, `design.py`, `team*_design.py`), Controller-Fehlermeldungen und Python-Testfunktionen/-Docstrings strikt auf **Englisch** gehalten (mit einem einzigen verbliebenen deutschen Hinweisstring in [`team_v9.py:342`](../../testguided-study/testguided_study/team_v9.py#L342): `'Ergebnis begrenzt; Scope oder Suchtext eingrenzen.'`).
3. **Evolution der Provenance-Köpfe (`Dokument-Informationen & Herkunft`):**  
   Während Foundations, B.3-Designs, B.4-Texte und frühe B.1-Analysen ohne KI-Autor-Signatur im neutralen Repo-Stil (`Status`, `Stand`, `Grundlage`) blieben, entwickelten die explizit KI-verfassten B.1/B.2-Berichte vier Varianten von Herkunftsköpfen:
   - *GitHub-Alert-Block* in [`HYPOTHESEN-URSACHENANALYSE-20261111.md:3-10`](../../testguided-study/HYPOTHESEN-URSACHENANALYSE-20261111.md#L3-L10) (`> [!IMPORTANT]` mit `System`, `Modell`, `Reasoning-Effort`, `Erstellungszeitpunkt`).
   - *Zweizeiler mit KI-Disclaimer* in [`URSACHENANALYSE-CODEX-20261111.md:3-13`](../../testguided-study/URSACHENANALYSE-CODEX-20261111.md#L3-L13) (ausdrückliche Abgrenzung von KI-Analyse und Projektverantwortlichem; Modellstring dort `GPT-6.1-Sol`, in [`PILOTANALYSE-V6-20261112-002038-CODEX.md:3`](../../testguided-study/PILOTANALYSE-V6-20261112-002038-CODEX.md#L3) invertiert als `GPT-Sol-6.1`).
   - *Zweizeiler ohne Effort-Angabe* in `PILOTANALYSE-V9-...` und `ANALYSE-GENERATIONEN-V6-V9.md`.
   - *Standardisierter Aufzählungsblock* `**Dokument-Informationen & Herkunft:**` mit den drei Pflichtfeldern `Plattform / Umgebung`, `Modell`, `Reasoning-Effort` sowie Zusatzfeldern (`Analysedatum`, `Untersuchter Pilotlauf`, `Synthesebasis`) in `HYPOTHESIS-V6..V8-GEMINI-ARGON-HIGH.md` — genau jene Struktur, die fünf Tage später in [`CUBIE_DOC_FRAME_2`](../../../src/qb_cubie/services/doc_frame/doc_frame.py#L135-L144) zum maschinenprüfbaren Repository-Preset wurde.

### 4.2 Dokumenten-Mutationsmuster unter Sprintdruck

Die Git-Historie dokumentiert vier charakteristische Schreibpraktiken, mit denen auf schnelle Spezifikationswechsel bei laufendem Betrieb reagiert wurde:

1. **Übergang von In-Place-Fortschreibung zu Append-Only-Versionsdokumenten:**  
   [`AGENTENDESIGN.md`](../../testguided-study/AGENTENDESIGN.md) vereinigt noch historisch Befund (v1), Zielarchitektur (`D01–D08`, v2), Umsetzungsstand (v2) und v3-Nachtrag in einer Datei. Ab `AGENTENDESIGN-V4.md` ging die Arbeit konsequent zu pro Generation getrennten, rückwirkend unmodifizierten Versionsdokumenten über.
2. **Umgekehrter Prepend-Stapel in [`README.md`](../../testguided-study/README.md):**  
   Die `645` Zeilen lange Studien-`README.md` wuchs gleichzeitig von drei Ankerpunkten aus: Neueste Generationen (`v9` Z. `1–14`, `v8` Z. `15–28`, `v7` Z. `29–37`) wurden direkt unter dem H1-Titel vorangestellt; `v6`, `PILOTANALYSE-20261111` und `AGENTENDESIGN.md` wurden unter der Zwischenüberschrift `## Weiterentwicklung der Agenten` (Z. `154–344`) in umgekehrter Reihenfolge eingeschoben; frühe Ergänzungen (`v4`, `v5` und später das Download-Skript in Commit `eff909ff`) hängen am Dateiende (`Z. 605–645`).
3. **Pre-Title-Blockquote-Addenda mit inkonsistenten Alt-Tabellen:**  
   Als Commit `5976fc90` (`v7`, 12.11. `02:35 Uhr`) die Aufruf-, Phasen-, Reserve- und Reparaturlimits strich, erhielten [`V6_CASES.md:1-4`](../../tests/testguided_study_design/V6_CASES.md#L1-L4), [`V7_CASES.md:1-4`](../../tests/testguided_study_design/V7_CASES.md#L1-L4) und [`IMPLEMENTIERUNG-V7.md:1-4`](../../testguided-study/IMPLEMENTIERUNG-V7.md#L1-L4) ein vierzeiliges `> Aktualisierte Budgetanforderung`-Zitat **oberhalb** der `#`-Hauptüberschrift. Die darunterstehenden Casematrizen und Funktionstabellen wurden jedoch nicht bereinigt: `V6_CASES.md:99-101, 210-213` beschreibt weiter 900 s / 48 Calls / Reserve und den alten Testnamen `test_a14_team_budget_is_shared_across_role_changes`, obwohl [`test_v6_controller_ebt.py:253-276`](../../tests/testguided_study_design/test_v6_controller_ebt.py#L253-L276) die Funktionen in `test_a14_only_wall_budget_limits_role_changes` und `test_a14_no_early_reserve_shortens_work` umbenannte und ihre Erwartungstupel invertierte. Ähnliches gilt für `V7_CASES.md:119, 130-135` und `IMPLEMENTIERUNG-V7.md:28-35`.
4. **Unmarkierte Provenance-Korrektur vs. transparente Konservierung:**  
   Die in [`HYPOTHESIS-V8-GEMINI-ARGON-HIGH.md`](../../testguided-study/HYPOTHESIS-V8-GEMINI-ARGON-HIGH.md) per Copy-Paste aus v7 übernommene falsche Lauf-ID `20261112-015457` wurde nach der ausdrücklichen Beanstandung in [`AGENTENDESIGN-V9.md:17-22`](../../testguided-study/AGENTENDESIGN-V9.md#L17-L22) in Commit `08792e32` still aus dem Kopf von `HYPOTHESIS-V8` gelöscht, ohne dass die korrigierte Lauf-ID (`20261112-030527`) dort nachgetragen wurde.

### 4.3 Multi-KI-Arbeitsteilung, epistemische Gatekeeper und ID-Taxonomien (`B.1`–`B.3`)

Im Zusammenspiel zwischen menschlicher Steuerung und den drei KI-Systemen etablierten sich **komplementäre epistemische Rollen**:

- **Live-Diagnose als Konversations-Artefakt (`Gemini-4-Argon`, High):**  
  Der Projektverantwortliche fütterte Live-Monitor-Auszüge (`Call 74` aus `v7-2`, `job-12`/`job-20` aus `v8`) ad hoc in Konversationen und speicherte die Antworten unverändert als `HYPOTHESIS-V*-GEMINI-ARGON-HIGH.md` ab (inklusive direkter Rückfragen an den Nutzer um ~02:28 Uhr zu GPU/OpenAI-Credits in [`HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md:29`](../../testguided-study/HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md#L29)). Diese ungeschönten Live-Protokolle deckten zweimal Phänomene auf, die in statischen Unit-Tests unsichtbar blieben: erstens die **„25-Zeilen-Skizzen-Drift“** in `v6`/`v7` (die Implementation durch [`team.py:214, 218`](../../testguided-study/testguided_study/team.py#L214-L218) und [`team_v7.py:191`](../../testguided-study/testguided_study/team_v7.py#L191) hatte die kurze 3-Rollen-Skizze über `super().request()` wieder mit 45 Zeilen Cubie-Guide in `analysis`, PyPI-Classifiern, SHA-256-Hashes und abgeschnittenem Dialogkontext überladen); zweitens die **epistemische Amnesie** (`update_context`-Verlust) und die **`"cursor": "0"`-Falle** in `v8`.
- **Falsifikations- vs. Kaskadenstil in der Ursachenanalyse (`Codex` vs. `Antigravity`):**  
  Auf identischer Single-Agent-Datenbasis (`v1–v5`) trennten beide Systeme Methodik und Stil sichtbar: Codex ([`URSACHENANALYSE-CODEX-20261111.md`](../../testguided-study/URSACHENANALYSE-CODEX-20261111.md), [`PILOTANALYSE-V6-20261112-002038-CODEX.md`](../../testguided-study/PILOTANALYSE-V6-20261112-002038-CODEX.md)) trennte konsequent Archiv- von Arbeitsstand, benannte Gegenbefunde (`requests_6589/pytest` in v2 und `fastapi_9425/cubie` in v3 als Widerlegung allgemeiner Unfähigkeit), rechnete Exitcode-4-Sensitivitäten aus (`+50,0` vs. `+33,3` PP), enthielt sich bei unklaren Logs (`requests/utils.py`) jeder ungedeckten Ursache und warnte explizit vor fehlinterpretierten Token-Summen. Antigravity ([`HYPOTHESEN-URSACHENANALYSE-20261111.md`](../../testguided-study/HYPOTHESEN-URSACHENANALYSE-20261111.md), `ANALYSE-GENERATIONEN-V6-V9.md`) lieferte strukturierende 5-Ebenen-Kaskaden und quantitative Erfolgswetten (`>75 %`, `>30 %`), produzierte dabei aber gelegentlich ungedeckte Nenner (`73,3 %` in H1) oder Request/Response-Vermischungen (`1.441` statt `1.439` abgeschlossener Modellantworten).
- **B.3 als epistemisches Filtertor (Gatekeeping):**  
  Die Design-Dokumente übernahmen keine B.2-Hypothese ungeprüft, sondern fungierten in jeder Generation als Korrektiv anhand der Rohdaten:
  - [`AGENTENDESIGN-V6.md:49-63, 318-321, 460-462`](../../testguided-study/AGENTENDESIGN-V6.md#L49-L63) verwarf `73,3 %` (ersetzt durch `11/67 = 16,4 %`), stufte „>99 % pytest-Prior“ und „30B-Mindestgröße“ zu Hypothesen herab, wies persönliche Nutzererfahrungen (`PAPER.md` §9) als Nicht-Evidenz zurück und lehnte das zu enge Quick-Fix-Tool `create_ebt_contract` zugunsten von `create_case` ab.
  - [`AGENTENDESIGN-V7.md:48-71`](../../testguided-study/AGENTENDESIGN-V7.md#L48-L71) schied den Zählkonflikt zwischen Antigravity (`51/14`) und Codex (`53/12`) zugunsten Codex und deckte im Code auf, dass `TeamController._navigate` (nicht nur `workspace.py`) die `scope`-Prüfung fehlte.
  - [`AGENTENDESIGN-V8.md:17-19`](../../testguided-study/AGENTENDESIGN-V8.md#L17-L19) überprüfte `steps/0073-request.json` direkt und widerlegte damit Gemini-4-Argons Behauptung einer dauerhaften Sperre von `search_content` bei Call 74.
  - [`AGENTENDESIGN-V9.md:17-25, 157`](../../testguided-study/AGENTENDESIGN-V9.md#L17-L25) korrigierte die Archiv-ID (`015457` → `030527`), dämpfte „verschwindet vollständig“-Versprechen und lehnte Gemini-4-Argons automatisches Überschreiben von `scope` durch einen Pfad im Feld `cursor` ab.
- **Ungeplante Spec-zu-Code-Divergenzen:**  
  Trotz dieses Gatekeepings wichen reale Implementierungen unter Zeitdruck zweimal folgenreich von ihren eigenen B.3-Dokumenten ab: In v8 setzte [`team_v8.py:688-704`](../../testguided-study/testguided_study/team_v8.py#L688-L704) einen harten Zwangsübergang bei `repeat_count >= 3` um, obwohl [`AGENTENDESIGN-V8.md:155-160`](../../testguided-study/AGENTENDESIGN-V8.md#L155-L160) dies nur allgemein als Änderung des Arbeitsauftrags beschrieb, und [`team_v8.py:789-806`](../../testguided-study/testguided_study/team_v8.py#L789-L806) sendete entgegen der Markdown-Vorgabe aus `AGENTENDESIGN-V8.md:78` weiterhin `json.dumps(payload)` mit rohem `visible_baseline`-JSON. In v9 folgte die differenzielle Vererbung (`team_v7_design.py` via `V6_COMMON`/`V6_POLICY`, `V9TeamController(V8TeamController)`), deren prompt-seitige Beschreibung von `finish` mit Review-Parametern (`verdict`) auf die harte Controller-Sperre in [`team_v9.py:381-383`](../../testguided-study/testguided_study/team_v9.py#L381-L383) (`ValueError('Orientation cannot verify a repair')`) traf.

#### Durchgängige ID-Systematiken in B.2–B.4

| ID-Serie | Abgedeckte Ebene / Herkunft | Zugeordnete Test-Funktionen / Artefakte |
| :--- | :--- | :--- |
| **`D01`–`D08`** | Kern-Iterationsfassade ([`AGENTENDESIGN.md`](../../testguided-study/AGENTENDESIGN.md)) | `test_iteration_ebt.py`: `test_d01_...`–`test_d08_...` (`29` Nodes) |
| **`P01`–`P21`** | Technik-Fixes nach `171515` ([`PILOT_TECHNICAL_CASES.md`](../../tests/testguided_study_design/PILOT_TECHNICAL_CASES.md)) | `test_pilot_technical_ebt.py` (`30` Nodes) + `test_pilot_monitor_ebt.py` (`2` Nodes) |
| **`A01`–`A16`** | Befunde aus `180702` ([`PILOT_180702_CASES.md`](../../tests/testguided_study_design/PILOT_180702_CASES.md)) | `test_pilot_180702_ebt.py` + `test_pilot_180702_evaluation_ebt.py` (`48` Nodes) |
| **`M01`–`M12`** | Ein-Befehl-Start & Image-Cache ([`RUN_MANAGEMENT_CASES.md`](../../tests/testguided_study_design/RUN_MANAGEMENT_CASES.md)) | `test_run_management_ebt.py` + `test_run_image_management_ebt.py` (`32` Nodes) |
| **`V6-A01`–`V6-A18`**, **`V6-C01`–`C04`**, **`F01`–`F07`** | v6-Designabnahmen & 7 QA-Referenzformen ([`V6_CASES.md`](../../tests/testguided_study_design/V6_CASES.md)) | `test_v6_controller_ebt.py`, `test_v6_case_forms_ebt.py`, `test_v6_evaluation_ebt.py` (`98` Nodes) |
| **`V7-A01`–`V7-A14`** | v7-Designabnahmen ([`V7_CASES.md`](../../tests/testguided_study_design/V7_CASES.md)) | `test_v7_controller_ebt.py`, `test_v7_runtime_ebt.py` (`41` Nodes) |
| **`V8-C01`–`V8-C39`** | 10 v8-Designverträge über 39 Casegruppen ([`V8_CASES.md`](../../tests/testguided_study_design/V8_CASES.md)) | `test_v8_controller_ebt.py`, `test_v8_tools_ebt.py`, `test_v8_completion_ebt.py`, `test_v8_case_forms_ebt.py` (`92` Nodes) |
| **`V9-A01`–`V9-A14`**, **`C01`–`C41`** | 14 v9-Verträge über 41 Casegruppen ([`V9_CASES.md`](../../tests/testguided_study_design/V9_CASES.md)) | `test_v9_memory_ebt.py`, `test_v9_tools_ebt.py`, `test_v9_workflow_ebt.py`, `test_v9_calibration_ebt.py` (`134` Nodes) |
| **`H1–H4`**, **`V6–V9-H*`**, **`Untersuchung A–D`** | Hypothesen- & Faktorprogramme | B.2-Dokumente, `PAPER.md` §10, `AGENTENDESIGN-V6..V9` |

### 4.4 QA- und Engineering-Praktiken in `B.4` und `B.5`

1. **Disziplinierte RED-First → GREEN-Protokollkette mit Basis-Konservierung:**  
   Jede Generation definierte vor dem Produktcode ein `*_CASES.md` und eine ausführbare EBT-Suite. Um saubere Pytest-Sammlung (`--collect-only`) ohne `skip` oder `xfail` sicherzustellen, wurden fehlende Zielklassen über **Lazy Imports innerhalb der `observe()`-Funktion** aufgelöst ([`test_iteration_ebt.py:20-23`](../../tests/testguided_study_design/test_iteration_ebt.py#L20-L23), [`V6_CASES.md:65-66`](../../tests/testguided_study_design/V6_CASES.md#L65-L66)). Die roten Ausgangszahlen blieben dokumentiert (`29` rot in `AGENTENDESIGN.md`; `23/9` in `PILOT_TECHNICAL_CASES`; `26/22` in `PILOT_180702_CASES`; `66/32` in `V6_CASES`; `41` rot in `V7_CASES`; `6/86` in `V8_CASES`; `8/126` in `V9_CASES`), bevor `IMPLEMENTIERUNG-V7..V9.md` den grünen Endstand festhielt (`439` → `555` → `698+` / `146` V9-Nodes; aktuell `768` Nodes mit `765 passed, 3 skipped` bei `CUBIE_STUDY_DOCKER=0`).
2. **Infrastruktur-bedingte Testauslagerung:**  
   Weil `artifacts.sources()` ursprünglich alle `.py`-Dateien unterhalb von `experiments/testguided-study` hashte und `20261112-013246` (`v7-1`) durch laufende Quelländerungen mit `ValueError: Agent/study implementation changed since freeze` abbrach, wanderte die gesamte Design-Suite aus dem Hash-Baum heraus nach `experiments/tests/testguided_study_design/` ([`AGENTENDESIGN.md:199-204`](../../testguided-study/AGENTENDESIGN.md#L199-L204)).
3. **Vier eigene Verifikations-Techniken in B.5:**
   - *Zustandslose Support-Ports (`v6..v9_support.py`):* Kapseln `IO`, `Clock`, `Harness` und `contract()` strikt ohne Rollen-/Berechtigungs-/Budgetlogik, damit diese Regeln ausschließlich im getesteten Produktionscontroller liegen.
   - *Selbst-kalibrierende Mutations-Orakel:* [`V6_CASES.md:114-145`](../../tests/testguided_study_design/V6_CASES.md#L114-L145) (`F01–F07`), [`V8_CASES.md:127`](../../tests/testguided_study_design/V8_CASES.md#L127) (`C37`) und [`test_v9_calibration_ebt.py:13-47`](../../tests/testguided_study_design/test_v9_calibration_ebt.py#L13-L47) (`C40`) prüfen in beiden Armen reale Pytest-Subprozesse gegen eine korrekte (`FIXED`), eine `off-by-one`-defekte (`BROKEN`) und eine vertauscht gepaarte (`swapped: 6 - value * 2`) Funktion, wobei Zeile 61–63 ausdrücklich `*.pyc`-Dateien löscht, um Import-Cache-Kollisionen bei schnellen Überschreibungen gleich großer Dateien abzufangen.
   - *AST-gekoppelte EBT-Anti-Gaming-Sonden (`team_probe.py` & `test_v6_runtime.py`):* [`team_probe.py:20-68`](../../testguided-study/testguided_study/team_probe.py#L20-L68) kombiniert `EBT.run`-Monkeypatching mit `RunTrace.__getattribute__` und `ast.parse`, um `ebt_executed`, `ebt_evaluated`, `ebt_passed` und `ebt_evaluation_checked` (tatsächliche Prüfung über `assert ...evaluation is True`) getrennt zu zählen; [`test_v6_runtime.py:141-144`](../../tests/testguided_study_design/test_v6_runtime.py#L141-L144) prüft ausdrücklich auch toten Code (`if False: assert result.evaluation is True`).
   - *Node.js-DOM-Harnesses für Browser-UI:* [`monitor_poll.cjs`](../../testguided-study/tests/fixtures/monitor_poll.cjs) und [`monitor_context.cjs`](../../tests/testguided_study_design/fixtures/monitor_context.cjs) extrahieren `<script>...</script>` direkt aus `monitor.html`, lesen reale HTML-`id`-Attribute aus und testen Polling, Pause, Archiv-Pinning und `</script>`-Escaping per `vm.runInNewContext` ohne Browser-Overhead.
4. **Strukturelle Sprint-Schulden und Replay-Blinde in B.5:**  
   Um alte Freezes reproduzierbar zu halten, wuchsen die Controller über eine dreistufige Parallel-Vererbung (`TeamController` `805` LOC → `V7TeamController(TeamController)` `573` LOC; `TeamController` → `V8TeamController` `850` LOC → `V9TeamController(V8TeamController)` `709` LOC), während `experiments/` vom Core-Styleguide (`src/` $\le 777$ LOC/Modul, $\le 12$ LOC/Funktion) ausgenommen blieb ([`tests/test_styleguide.py:116`](../../../tests/test_styleguide.py#L116)). Zudem verdeckten deterministische Replays systematisch zwei reale v9-Ausfälle, weil Test-Harnesses `finish` programmgesteuert aufriefen (statt das 12B-Modell mit dem `FINISH`-Schema in `team_v9_design.py:47-51` zu konfrontieren) und gegen ein 9-Datei-Mini-Repo statt gegen einen FastAPI-Container testeten.

---

## 5. Praktiken, Muster und Konventionen in Dimension C (Synthetische Paper-Erzeugung & Begutachtung)

### 5.1 Wettbewerbs-Pipeline und iterative Kompaktierung

Dimension C entstand unter dem harten Zeitfenster der *Google Gemma 4 Developer Agent Competition (Paper Track)* ([`Developer-Agent-Paper.md`](../../testguided-study/Developer-Agent-Paper.md), Abgabefrist: `12. November 2026, 23:59 UTC`, Limit: `3.000 Wörter`, fünf gleichgewichtete Bewertungskriterien `0–5`: *Novelty, Quality, Relevance, Verifiability, Clarity*). Der Prozess bildete eine vierstufige Produktions- und Audit-Schleife:

1. **Manuskript-Synthese (`Gemini-4-Argon`):** Erzeugte aus [`PAPER.md`](../../testguided-study/PAPER.md) (v1–v5, 11.11.) und [`ANALYSE-GENERATIONEN-V6-V9.md`](../../testguided-study/ANALYSE-GENERATIONEN-V6-V9.md) (v6–v9, 12.11.) fünf aufeinanderfolgende PDF-Revisionen (`Analysis.pdf` bis `Analysis-4.pdf`).
2. **Automatisierte / KI-gestützte Audit-Kette (`Antigravity / Gemini-3.8-Flash`):** Prüfte die PDFs in fünf formalisierten Gutachten ([`KRITISCHE-ANALYSE-PAPER-SUBMISSION.md`](../../testguided-study/KRITISCHE-ANALYSE-PAPER-SUBMISSION.md), [`GUTACHTEN-PAPER-SUBMISSION-1.md`](../../testguided-study/GUTACHTEN-PAPER-SUBMISSION-1.md), [`-2.md`](../../testguided-study/GUTACHTEN-PAPER-SUBMISSION-2.md), [`-4.md`](../../testguided-study/GUTACHTEN-PAPER-SUBMISSION-4.md), [`STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md`](../../testguided-study/STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md)) mit standardisierten Grounding-Matrizen (`Korrekt` / `Exakt bestätigt` vs. `FALSCHBEHAUPTUNG` / `FEHLINFORMATION`, `Partiell erfüllt` / `Vollständig geheilt`) und Rubrik-Bewertungen.
3. **Konvergenz über 5 Revisionen:**  
   `Rev-0` (`5.390` Wörter) → `Rev-1` (`5.478` Wörter, 13 S., Rubrik **3,66**) → `Rev-2` (`3.536` Wörter gesamt / `2.851` Body-Wörter, 9 S., Ergänzung von *Introduction* & *Related Works*, Rubrik **4,40**) → `Rev-3` (`3.452` Wörter, 8 S.) → `Rev-4` (`2.925` Wörter gesamt / `2.454` Body-Wörter, 7 S., Rubrik **4,84**).
4. **Menschliche Schlussredaktion (`af62a3bb`, 13.11. `00:02:57`):** Der Projektverantwortliche redigierte [`g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md`](../../testguided-study/g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md) manuell (*„based purely on my personal and therefore subjective preferences“*), ergänzte die explizite Offenlegung der rekursiven Beobachtung (`Z. 22`) sowie den Abschnitt **`Threats to Validity`** (*Custom Evaluation Harness*, *Exploratory Iterative Progression*, *AI-Assisted Provenance*, `Z. 119`).

### 5.2 Empirische Muster und Pathologien der KI-Eigenbegutachtung

Die direkte Nachprüfung aller fünf PDF-Fassungen und der fünf Gutachten gegen den Quellcode offenbart vier wiederkehrende Fehlermuster in der synthetischen Audit-Schleife:

1. **Oberflächen-Verifikation („Grep-Theater“) mit falschen „100 % Exakt bestätigt“-Zertifikaten:**
   - **Nicht-Zirkularitäts-Mythos (`assert` vs. `contract()`):** Nachdem [`GUTACHTEN.md:74`](../../../GUTACHTEN.md#L74) reguläre Assertions in `test_order_export.py` gegen Zirkularität gelobt hatte, verallgemeinerte das Paper dies auf die `698+` Controller-Nodes (`g4da_paper_submission...md:34`: *„authored with standard pytest assertions rather than EBT contracts“*). [`GUTACHTEN-PAPER-SUBMISSION-2.md:51`](../../testguided-study/GUTACHTEN-PAPER-SUBMISSION-2.md#L51) bestätigte dies als *„Exakt bestätigt“* unter Verweis auf `IMPLEMENTIERUNG-V9.md:114` (das überhaupt nichts über Standard-Assertions sagt); [`STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md:63`](../../testguided-study/STAGE2-TECHNICAL-VERIFICATION-ASSESSMENT.md#L63) zählte `275+` `assert`-Statements (tatsächlich `281` in `testguided_study_design/*.py`), ohne die `240` direkten Aufrufe der EBT-Wrapper (`213 contract()`, `15 check()`, `5 rejects()`, `7 EBT()`, d. h. **82,7 %** der Design-Nodes) aufzulösen. Auch das menschliche Lektorat (`af62a3bb`) übernahm diesen Satz ungeprüft.
   - **Fehlschluss bei `swegemma`:** Weil `swegemma` nicht in `pyproject.toml` oder `.venv` installiert war, wertete `KRITISCHE-ANALYSE` seine Erwähnung als *„Falschbehauptung“* (`importlib.util.find_spec('swegemma') == None`), und `STAGE2:83` sowie `GUTACHTEN-2:52` bestätigten für v6–v9 *„zero runtime dependency on swegemma“* anhand von `team_workspace.py`, obwohl `execution.py:130, 137` und `team_workspace.py:212` weiter auf `backend.py` (`swegemma 0.2.11`) und `_swegemma_baseline` liefen.
2. **Prüfskript-Artefakte und Selbst-Korrektur (`Font Glitching`):**  
   In `GUTACHTEN-1:137-140` schlug ein unmaskierter Substring-Check (`if g in text`) falsch-positiv auf `itHub`, `alueError`, `stLinter`, `yVenv`, `orldState` an; erst `GUTACHTEN-2:133-140` widerlegte den Befund per Regex-Prüfung gegen den PDF-Extrakt als eigene Prüfskript-Unschärfe.
3. **Konvertierungsdefekte, Rubrik-Drift und interne Audit-Widersprüche:**  
   - In `Rev-1` riss der PDF-Satz beim Seitenumbruch 11→12 das Wort *„zero times“* aus dem Satz, sodass das Gegenteil gedruckt wurde (*„invoke finish across 1,184 steps“*).
   - `Rev-2` wurde durch Umdeutung des Kaggle-Limits (`3,000 words maximum` auf reinen *Body Word Count* `2.851` statt Gesamttext `3.536`) als *„punktgenau konform“* eingestuft, bevor `Rev-4` auch insgesamt auf `2.925` Wörter sank.
   - In `GUTACHTEN-4` stieg `Verifiability` auf **5,0 / 5,0** und die Gesamtnote auf **4,84 / 5,00**, obwohl das Gutachten selbst zwei neue Zitationsabbrüche in `Rev-4` dokumentierte (`prompt []`, `[, ].6410`), sie als tolerierbar einstufte (`Z. 199`) und in `Z. 165` selbst Zeichensalat enthielt (*„Makroer чорfung“*).
   - Im selben Commit `1e771f55` prüfte `STAGE2` zudem noch `Rev-2`, während bereits `Rev-3` und `Rev-4` eingecheckt wurden.
   - Sämtliche vier Gutachten empfahlen entgegen der expliziten Entweder-oder-Regel in [`Developer-Agent-Paper.md:60`](../../testguided-study/Developer-Agent-Paper.md#L60) (*„instead of writing your paper in the Kaggle Writeup, you can also upload an arXiv-ready ... PDF“*), sowohl das Writeup-Textfeld als auch den PDF-Link parallel zu befüllen.

---

## 6. Gemeinsame Muster und Rückfluss in die Repository-Architektur (`v0.0.4`–`v0.0.7`)

Über die Dimensionalitäten **A**, **B** und **C** hinweg treten fünf übergreifende Strukturmuster hervor, die über den eigentlichen Studienabschluss hinaus unmittelbar die Weiterentwicklung von `qb-cubie` prägten:

### Muster 1: Zwei-Geschwindigkeits-Regime (Harte Code-Gates vs. pragmatische Text-Abkürzungen)
Dort, wo Anforderungen in ausführbaren Python-Code gegossen wurden (`admission.py`, `campaign.py`, `artifacts.py`, `team_probe.py`, `*_ebt.py`), herrschte maximale Strenge (kryptographische Hash-Ketten, Verbot von `skip`/`xfail`, Unveränderlichkeit historischer Archive). Dort hingegen, wo Begleitdokumente mit der Geschwindigkeit der Sprint-Iterationen Schritt halten mussten, bildeten sich pragmatische Abkürzungen: vorangestellte `README`-Stapel, Pre-Title-Addenda über veralteten Tabellen (`V6_CASES`, `V7_CASES`), stehende `study_id`-Etiketten (`v2` bis v5) und rückwirkende `v6.toml`-Mutationen.

### Muster 2: Rekursive Spiegelung derselben Failure-Modes auf zwei Modell-Ebenen
Sowohl das untersuchte `12B`-Modell in **Dimension A** als auch die steuernden und prüfenden Frontier-Modelle in **Dimension B und C** zeigten strukturell verwandte Grenzphänomene auf unterschiedlichen Abstraktionsebenen:
- Wie `gemma4:12b` in v6–v9 durch überladene Spezifikationen/Schemas (`Working ledger`, `FINISH` mit `verdict`) blockiert wurde, erzeugte die „25-Zeilen-Skizzen-Übersetzung“ in B.3 zunächst eine 512-Zeilen-Bürokratie, die sich als inkompatibel mit einem kompakten Modell erwies.
- Wie `gemma4:12b` unter kognitiver Last auf starke Pre-Training-Priors (`pytest`) zurückfiel, verließen sich die prüfenden KI-Gutachter in Dimension C auf oberflächliche Heuristiken (Greppen nach `assert` und `pyproject.toml`), statt tiefergehende Aufrufketten (`contract()`, `backend.py`) zu verfolgen.

### Muster 3: Komplementäre Multi-KI-Selbstkorrektur mit nachlassender Reichweite an Systemgrenzen
Innerhalb der geschlossenen Faktenbasis (`B.1–B.3`) korrigierte das Dreieck aus `Codex` (Falsifikation/Zähltreue), `Antigravity` (Struktur/Systematisierung) und `Gemini-4-Argon` (Live-Dump-Synthese) nachweislich Rechenfehler (`73,3 %`), Zähldifferenzen (`51/14` vs. `53/12`), Fehlzuschreibungen (`015457` → `030527`) und Code-Orte (`_navigate`). Sobald Artefakte jedoch über Systemgrenzen hinweg synthetisiert wurden (B → C in `PAPER.md` → `Analysis*.pdf` → `GUTACHTEN-*`), blieben lokale Korrekturen isoliert oder wurden durch defensive Umdeutungen (`swegemma`, `698+ pytest assertions`) überlagert.

### Muster 4: Unmittelbare Kodifizierung der Sprint-Praktiken in produktive `qb_cubie`-Services
Die Nach-Sprint-Commits (`32434293` bis `7e08e2ac`) belegen einen direkten Transfer der im Sprint spontan entstandenen Konventionen in wiederverwendbare Software-Services des Hauptpakets:

| Spontane Studien-Konvention (Phase 1) | Nachfolgende Formalisierung in `qb_cubie` (Phase 2) | Fundstelle im aktuellen Stand (`7e08e2ac`) |
| :--- | :--- | :--- |
| `**Dokument-Informationen & Herkunft:**` mit `Plattform / Umgebung`, `Modell`, `Reasoning-Effort` (`HYPOTHESIS-V6..V8`) | `CUBIE_DOC_FRAME_2` (`TitleSlot`, `ProvenanceBlock`, `PromptSlot`) + Fehlerregel `DOCFRAME-PROVENANCE-INCOMPLETE` | [`doc_frame.py:135-144`](../../../src/qb_cubie/services/doc_frame/doc_frame.py#L135-L144), [`frame_blocks.py:354-410`](../../../src/qb_cubie/services/doc_frame/frame_blocks.py#L354-L410), [`doc_frame_rules.py:118-152`](../../../src/qb_cubie/services/doc_frame/doc_frame_rules.py#L118-L152) |
| Ausführbare Guide-Prüfung (`guides/cubie.md` in `test_v3.py`) | `DocEnsurance` + `CUBIE_DOC_STYLE` + `CUBIE_DOC_RULES` | [`GUIDE_DocEnsurance.md`](../../../docs/services/GUIDE_DocEnsurance.md), [`tests/test_styleguide.py:108-120`](../../../tests/test_styleguide.py#L108-L120) |
| Trennung von Ist-Beobachtung vs. Soll-Gesetz & 1:1-Orakel-Paarung (`V9_CASES` `C40`, `guides/cubie.md:49`) | 5-Schritt-TGD-Verfahren (`Q_Ist` vs. `Q_Soll`, `expect=False`-Inversion, Anti-Pattern Kreuzprodukt) | [`GUIDE_Quality-Assurance.md:38-196`](../../../docs/GUIDE_Quality-Assurance.md#L38-L196) |
| Fehler-Injektions-Sonden (`if False: assert ...`, `test_v9_calibration_ebt.py`) | `"Tries to"`-Testmodule, Linter-Fehlsonden (`W0101`/`F821`), Isomorphie-Tests | [`tests/test_lint.py:35-45`](../../../tests/test_lint.py#L35-L45), [`tests/tests_services/`](../../../tests/tests_services/) |
| Sprint-Artefakt-Quarantäne und geplante Bereinigung (`~300` → `2.000+` Tests) | Explizite Aufräum-Roadmap & Ausschlusskommentare für `experiments` und `GUTACHTEN.md` | [`DEV-GUIDE_Next-Steps.md:17-74`](../../../docs/dev/DEV-GUIDE_Next-Steps.md#L17-L74), [`tests/test_styleguide.py:116-117`](../../../tests/test_styleguide.py#L116-L117) |

### Muster 5: Persistente Lücke zwischen Meta-Diagnose und automatischer Durchsetzung
Selbst in der Nach-Sprint-Phase wiederholte sich das Spannungsfeld aus Dimension B/C: [`META_QUESTION.md`](../../../META_QUESTION.md) deckte am fertigen Kern sieben strukturelle Test-Anomalien auf (darunter die Kreuzprodukt-Falle in `pre=[...]`/`post=[...]` und den auskommentierten `#@pytest.mark.slow`-Marker in [`tests/test_styleguide.py:107`](../../../tests/test_styleguide.py#L107)) und formulierte vier konkrete automatische Meta-Gates (`MetaImportRule`, `EBT-in-EBT`-Disjunktionswächter, `No-Lonely-Negation-Guard`, `slow`-Marker-Vertragstest). Während `src.qb_cubie`-Doppelimporte, `HumanReviewer()` und einzelne isolierte `expect=False`-Fälle im HEAD-Stand (`7e08e2ac`) behoben sind, wurde keines der vier automatisierten Meta-Gates implementiert, und `#@pytest.mark.slow` in `test_styleguide.py:107` nach einer kurzzeitigen Aktivierung (`db8eb74d`) in Commit `05e9945b` erneut auskommentiert — während das explizite Ausschlussprinzip in `test_styleguide.py:117` (*„No Cubie-Rules apply to Inspectors“*) konsequent eine institutionelle Schutzgrenze für unabhängige Audits zieht.
