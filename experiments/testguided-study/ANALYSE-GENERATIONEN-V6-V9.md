# Deskriptive Analyse und vergleichende Gesamtschau der Agenten-Generationen v6, v7, v8 und v9

**Herkunft der Analyse: Antigravity, Gemini-3.8-Flash**  
**Datum der Erstellung:** 12. November 2026  
**Untersuchungsgegenstand:** Studiendaten und Implementierungen der Agentengenerationen v6 bis v9 im Projektpfad [`experiments/testguided-study/testguided_study`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study) sowie die zugehörigen Laufarchive in [`experiments/testguided-study/runs/`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/runs/).

---

## 1. Einleitung, Datengrundlage und methodischer Rahmen

Die vorliegende Analyse untersucht die empirischen Verläufe, Kontrollstrukturen und Systemdynamiken der vier aufeinanderfolgenden Multi-Agenten-Generationen **v6**, **v7**, **v8** und **v9** der Testguided-Studie im Repository *Cubie*.

Alle vier Generationen basieren auf einer gemeinsamen architektonischen Leitidee: der Aufteilung der Software-Reparaturaufgabe auf drei spezialisierte Rollen:
1. **Analysis** (Erschließen von Problembeschreibung und Codebasis, Orientierung, Wissenspflege, Abschlussprüfung),
2. **QA** (Erstellung von reproduzierenden und abgrenzenden Testfällen im jeweils vorgegebenen Framework `pytest` oder `cubie`),
3. **Dev** (Diagnose des Fehlverhaltens, Code-Modifikation und Verifikation gegen die Testsuite).

### Einheitliche Versuchs- und Inferenzrahmenbedingungen

Über alle vier Generationen hinweg blieben die Kernparameter der Inferenz und der Testaufgaben identisch konfiguriert (fixiert in den Profilen [`v6.toml`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/v6.toml), [`v7.toml`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/v7.toml), [`v8.toml`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/v8.toml) und [`v9.toml`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/v9.toml)):
- **Basis-Sprachmodell:** `gemma4:12b` via lokalem Ollama-Dienst (`http://localhost:11434`).
- **Inferenzparameter:** `think = false`, `temperature = 0.15`, Kontextfenster `num_ctx = 32768`, Ausgabelimit `num_predict = 8192`.
- **Aufgabenkatalog:** Drei Standard-Aufgabenpaare aus realen Open-Source-Repositories mit Seed 42:
  - `fastapi_9425` (Repository: `fastapi/fastapi`, Issue zu Typannotationen mit `None`/String-Rückgabewerten),
  - `requests_6589` (Repository: `psf/requests`, Issue zur Längenberechnung encodeter Strings in `super_len`),
  - `rich_3278` (Repository: `Textualize/rich`, Issue zur Unterdrückung privater ANSI-Escape-Sequenzen).
- **Studienarme:** Jede Aufgabe wurde jeweils im Arm `cubie` (Evidence-based Testing / EBT) und im Arm `pytest` (klassisches Python-Testframework) ausgeführt (6 Durchläufe `0001` bis `0006` pro vollständigem Studienlauf).
- **Zeitbudget:** Maximal 1800 Sekunden (30 Minuten) Wall-Clock-Zeit je Versuchsdurchlauf.

---

## 2. Quantitative Gesamtschau der Generationen v6 bis v9

Die folgende Tabelle fasst die primären quantitativen Kennzahlen der fünf relevanten Laufarchive aus dem Verzeichnis `experiments/testguided-study/runs/` zusammen:

| Generation & Lauf-ID | Status des Laufs | Geplante / Ausgef. Durchläufe | Modellaufrufe | Werkzeugschritte | Verarbeitete Tokens (Input / Output) | Erreichte Rollen | Dominante Abbruchursache | Gelöste Aufgaben |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- | :---: |
| **v6** (`20261112-002038`) | `finished` | 6 / 6 | 66 | 65 | 422.512 / 16.749 | Analysis (100 %) | 6x `stagnation` (Controller-Abbruch nach 3+3 unproduktiven Schritten) | 0 / 6 (0,0 %) |
| **v7-1** (`20261112-013246`) | `failed` | 6 / 3 | 46 | 45 | 316.839 / 5.649 | Analysis (18), QA (27) | `ValueError` (Code-Änderung nach Studien-Freeze) | 0 / 3 (0,0 %) |
| **v7-2** (`20261112-015457`) | `interrupted` | 6 / 1 | 81 | 80 | 638.637 / 5.705 | Analysis (100 %) | Manueller Abbruch (Endlosschleife `find_paths` nach Werkzeugentzug) | 0 / 1 (0,0 %) |
| **v8** (`20261112-030527`) | `interrupted` | 6 / 1 | 64 | 63 | 195.452 / 2.302 | Analysis (61), QA (2) | Manueller Abbruch (Endlosschleife `cursor_error` in `ask_analysis`) | 0 / 1 (0,0 %) |
| **v9** (`20261112-035522`) | `finished` | 6 / 6 | 1.184 | 1.179 | 6.980.998 / 44.845 | Analysis (100 %) | 6x `budget_exhausted` (Zeitbudget 1800 s erschöpft) | 0 / 6 (0,0 %) |
| **Gesamtsumme** | – | **30 / 17** | **1.441** | **1.432** | **8.554.438 / 75.250** | **Analysis dominiert** | – | **0 / 17 (0,0 %)** |

### Verteilung der ausgeführten Werkzeuge über alle Generationen

| Werkzeug | v6 (`002038`) | v7-1 (`013246`) | v7-2 (`015457`) | v8 (`030527`) | v9 (`035522`) | Gesamtanzahl | Anteil |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `search_content` | 53 | 8 | 4 | 56 | 674 | **795** | **55,5 %** |
| `read_file` | 12 | 16 | 38 | 5 | 433 | **504** | **35,2 %** |
| `find_paths` | 0 | 14 | 38 | 0 | 0 | **52** | **3,6 %** |
| `read_evidence` | 0 | 0 | 0 | 0 | 72 | **72** | **5,0 %** |
| `ask_analysis` | 0 | 0 | 0 | 2 | 0 | **2** | **0,1 %** |
| `finish_orientation` | 0 | 3 | 0 | 0 | 0 | **3** | **0,2 %** |
| `create_case` | 0 | 3 | 0 | 0 | 0 | **3** | **0,2 %** |
| `collect_tests` | 0 | 1 | 0 | 0 | 0 | **1** | **0,1 %** |
| `finish` | 0 | 0 | 0 | 0 | 0 | **0** | **0,0 %** |
| **Summe** | **65** | **45** | **80** | **63** | **1.179** | **1.432** | **100,0 %** |

---

## 3. Detailanalysen der einzelnen Generationen

### Generation v6 (Lauf `20261112-002038`)
- **Implementierungsbasis:** [`testguided_study/team.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team.py), [`testguided_study/team_design.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_design.py).
- **Architektur:** Serieller Dreier-Ablauf (`Analysis` -> `QA` -> `Dev` -> `Analysis Review`). Strenge funktionale Gewaltenteilung: Nur Analysis darf suchen und Kontext veröffentlichen; nur QA darf Testfälle erstellen; nur Dev darf Produktionscode editieren.
- **Ablaufdynamik:**
  1. Alle sechs Durchläufe starteten im Zustand `orient` mit der Rolle `analysis`.
  2. Der Agent formulierte rasch zutreffende Suchen (`search_content`) und las relevante Codeabschnitte (`read_file`).
  3. Bei Pfadabweichungen (z. B. Repository-Struktur `src/requests/utils.py` vs. Suchanfrage in `requests/utils.py`) lieferte der Workspace valide, aber leere Ergebnisse (`hits: []`). Das Modell wiederholte die Suche mit minimalen Variationen (`def super_len` -> `super_len` -> `len`).
  4. Die Stagnationskontrolle des Controllers registrierte Aktionen ohne neue Evidenz (`idle += 1`). Nach 3 unproduktiven Schritten wurde eine Recovery-Warnung injiziert (`idle = 0`, `recovery_active = True`).
  5. Da das Modell sein Suchmuster nicht grundsätzlich änderte, erreichte `idle` erneut den Schwellenwert 3. Der Controller beendete den Lauf deterministisch mit `self._stop('stagnation')`.
  6. **Ergebnis:** Alle 6 Läufe endeten vorzeitig nach 45 bis 531 Sekunden (Median: ~124 s). Die Rollen `qa` und `dev` verzeichneten 0 Aufrufe. Es wurden 0 Patches und 0 Tests generiert.

### Generation v7 (Läufe `20261112-013246` und `20261112-015457`)
- **Implementierungsbasis:** [`testguided_study/team_v7.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v7.py), [`testguided_study/team_v7_design.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v7_design.py).
- **Änderungsziel:** Verhinderung des verfrühten Stagnationsabbruchs aus v6. Aufhebung der harten Aufruf- und Stagnationsgrenzen; Einführung von Startkarten, Phasenbudgets und QA-Bestätigung.
- **Ablaufdynamik in Lauf `20261112-013246` (v7-1):**
  - In drei Läufen erreichte das System erstmals die Rolle `qa` (27 Aufrufe), definierte 3 Testcases und führte 1 `collect_tests` aus.
  - Der Lauf brach nach Lauf 3 ab, da Quellcode nach dem Einfrieren der Studie modifiziert worden war (`Agent/study implementation changed since freeze`).
- **Ablaufdynamik in Lauf `20261112-015457` (v7-2):**
  - **Kontextüberladung:** Dem Modell wurde im Prompt ein umfangreicher, unformatierter JSON-Ledger übergeben (inklusive SHA-256-Hashes, PyPI-Classifiern und Fließkomma-Laufzeitmetriken).
  - **Rollenkontamination:** Im System-Prompt für die Rolle `analysis` befand sich eine mehrseitige Anleitung für das Framework `qb_cubie` samt Python-Codeblöcken, obwohl der Analyse-Agent laut Schema keine Tests schreiben durfte.
  - **History-Truncation:** Ältere Interaktionen wurden abgeschnitten (`"55 older tool exchanges omitted"`), wodurch der Agent zuvor gelesenen Code vergaß.
  - **Werkzeugentzug und Few-Shot-Schleife:** Nach wiederholten Suchen entzog die Recovery-Logik dem Agenten das Werkzeug `search_content`. Um die gewünschte Funktion zu finden, wich das Modell auf `find_paths` aus (`pattern: "def get_route_info"`). Da ein Dateiglob-Tool keine Funktionsdefinitionen finden kann, lieferte es 0 Treffer. Mangels Stagnationsabbruch wiederholte das Modell diese Aktion 32-mal in Folge, bis der Versuch bei Call 81 durch den Operator manuell abgebrochen wurde (`interrupted`).

### Generation v8 (Lauf `20261112-030527`)
- **Implementierungsbasis:** [`testguided_study/team_v8.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v8.py), [`testguided_study/team_v8_design.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v8_design.py).
- **Änderungsziel:** Bereinigung des Systemprompts, Entfernung des JSON-Ledgers, Einführung von `finish` als direkter Übergabe-Aktion sowie Implementierung eines deterministischen Zwangswechsels (`forced handoff` bei `repeat_count >= 3`).
- **Ablaufdynamik:**
  - Nach initialen Lese- und Suchaktionen in der Analyse-Rolle griff bei wiederholten Abfragen der Controller-Zwangsübergang und aktivierte die Rolle `qa`.
  - Da QA laut v8-Schema keine eigenen Suchwerkzeuge (`search_content`, `find_paths`) besaß, stellte der QA-Agent zwei Rückfragen an die Analyse (`ask_analysis`).
  - Der Analyse-Agent wurde zur Beantwortung reaktiviert. In den gekürzten v8-Prompts war die semantische Erläuterung des Parameters `cursor` entfallen.
  - Das Modell belegte `cursor` fälschlich mit dem Wert `"0"` (als vermeintlichem Paginierungs-Offset) oder einem Dateipfad.
  - Das Backend wies ungültige Cursor strikt mit `status: "cursor_error"` ab.
  - Es bildete sich eine Schleife aus über 30 aufeinanderfolgenden `cursor_error`-Abbrüchen.
  - Zudem erforderte das Gedächtnis eine manuelle Aktualisierung (`update_context`), die das Modell nicht absetzte, sodass zuvor gelesener Code verloren ging. Der Lauf wurde bei Schritt 64 manuell abgebrochen (`interrupted`).

### Generation v9 (Lauf `20261112-035522`)
- **Implementierungsbasis:** [`testguided_study/team_v9.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v9.py), [`testguided_study/team_v9_design.py`](file:///home/symphonie/PycharmProjects/cubie/experiments/testguided-study/testguided_study/team_v9_design.py).
- **Änderungsziel:** Beseitigung der Werkzeugfallen (Entfernung von `cursor` aus dem Schema), Einführung eines automatischen Transaktionsgedächtnisses ("Zero-Admin Memory"), symmetrische Lese- und Suchrechte für alle Rollen, strukturierter Markdown-Kontext. Bewusster Rückbau des Controller-Zwangsübergangs (`forced handoff`), um die Übergabe autonom dem Modell über die Aktion `finish` zu überlassen.
- **Ablaufdynamik:**
  - Die technische Infrastruktur funktionierte fehlerfrei: Über 1.184 Aufrufe hinweg traten 0 Cursorfehler, 0 Schemaabweichungen und 0 unkontrollierte Kontextüberläufe auf.
  - Das Modell rief die Aktion `finish` in der Orientierungsphase **kein einziges Mal** (0 Aufrufe) auf.
  - Der Systemprompt beschrieb `finish` primär im Kontext des finalen Reviews (`verdict="verified"` oder `verdict="rework"`), während der Controller in der Orientierungsphase bei Vorhandensein eines `verdict` eine Ausnahme auslöste (`Orientation cannot verify a repair`). Die fortlaufende Aufgabenstellung im Prompt lautete: `Task: Locate sources and a first justified test case.`
  - In Ermangelung eines Zwangsübergangs oder eines verstandenen Übergangstriggers verblieb das Modell in allen 6 Läufen über die gesamten 1800 Sekunden in der Rolle `analysis`.
  - Es bildeten sich deterministische Schleifen identischer Such- und Leseoperationen (974 von 1.179 Aktionen waren Duplikate, d. h. 82,6 %).
  - Alle 6 Läufe endeten durch Zeitablauf (`status: incomplete`, `reason: budget_exhausted`). QA und Dev wurden nie aktiviert.

---

## 4. Allgemeine Abläufe und emergente Systemdynamiken

Beim vergleichenden Blick auf die vier Generationen treten übergeordnete Kontroll- und Verhaltensdynamiken zutage:

```
                  ┌────────────────────────────────────────────────────────┐
                  │ 1. Orientierungsphase (Rolle: Analysis)                │
                  │    - Schnelle, zielgerichtete Quelltextlokalisierung    │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
         [Harter Übergang / Zwang]                   [Autonomer Modell-Übergang]
         (v8: forced handoff)                        (v6: publish/handoff, v9: finish)
                       │                                           │
         ┌─────────────┴─────────────┐               ┌─────────────┴─────────────┐
         ▼                           ▼               ▼                           ▼
   QA wird erreicht            Scheitert an    Modell erkennt             Modell verharrt in
   (v7-1: 3 Fälle;            Folgefehlern:   Übergang nicht             Endlosschleifen
    v8: 1 Fall)               - cursor_error  (v6: Protokollhürde;       (v6: Stagnation;
                              - Amnesie       v9: fehlender Trigger)     v7: find_paths;
                              - Schema-Strenge                           v9: budget_exhausted)
```

### Dynamik 1: Die Pendelbewegung zwischen Controller-Zwang und Modell-Autonomie
Die Architektur schwankte über die vier Generationen zwischen externer Bevormundung und freier Modellsteuerung:
- **v6** setzte auf strikte Formalismen (`publish_context` vor `handoff`). Das Modell schaffte diesen zweistufigen Vertrag nicht autonom; die strikte Stagnationskontrolle stoppte die Versuche frühzeitig.
- **v7** lockerte die Abbruchkontrolle vollständig, was bei fehlerhaften Aktionen in ungebremste Schleifen mündete.
- **v8** führte einen erzwungenen Rollenwechsel (`repeat_count >= 3 -> activate QA`) ein. Dies überwand zwar die Übergangsschwelle zu QA, verlagerte die Blockade jedoch unmittelbar in die nachgelagerten Informationsrückfragen (`ask_analysis`).
- **v9** beseitigte den Controller-Zwang wieder vollständig, um dem Modell Autonomie zu gewähren. Ohne den Zwangsübergang verharrte das Modell erneut zu 100 % in der Ausgangsrolle.

### Dynamik 2: Verschiebung der Fehlerdomänen (Error Domain Migration)
Während die technische Infrastruktur von Generation zu Generation robuster wurde, wanderte der Flaschenhals schrittweise durch das Gesamtsystem:
1. *Inferenz- und Formatstabilität (v5 zu v6):* Gelöst durch `think = false` und kompakte Aktionsformate.
2. *Protokollkomplexität (v6 zu v7):* Vereinfacht, führte jedoch zu Kontextüberfrachtung und widersprüchlichen Prompt-Instruktionen.
3. *Kontextgröße und Gedächtnis (v7 zu v8):* Bereinigt, deckte aber strikte Schemarestriktionen (`cursor_error`) und Kontextverlust zwischen Aufträgen auf.
4. *Robuste Werkzeuge und Wissenspersistenz (v8 zu v9):* Vollständig gelöst; der verbliebene Engpass lag rein in der semantischen Kommunikation der Rollenwechsel-Bedingung (`finish` in `orient`).

### Dynamik 3: Informationslokalisierung vs. Phasenwechselkompetenz
Über alle Generationen hinweg zeigte das 12B-Modell eine bemerkenswerte Stärke bei der initialen Identifikation relevanter Quelltexte:
- Bei `requests_6589` wurden `super_len` und `test_super_len` stets innerhalb der ersten 5 Schritte gefunden.
- Bei `fastapi_9425` wurden `APIRoute` und Annotation-Hilfsfunktionen stets frühzeitig eingelesen.
- Bei `rich_3278` wurden ANSI-Escape-Routinen zuverlässig lokalisiert.

Die Limitation der Modelle lag nicht im Finden und Verstehen der Problemstelle, sondern im prozeduralen Vollzug des Phasenwechsels vom explorativen Lesen zur konstruktiven Handlung (Schreiben von Tests oder Patches bzw. formales Beenden der Erkundung).

### Dynamik 4: Repetitive Attraktoren und Few-Shot-Fixierung
Sobald identische Aktionen oder leere Rückmeldungen in die Dialoghistorie eingingen, entwickelte das autoregressive Modell eine starke Tendenz zur Selbstverstärkung:
- In v6 wiederholte das Modell bis zu viermal dieselbe erfolglose Suche.
- In v7 erzeugte das Modell 32 identische `find_paths`-Befehle in Folge.
- In v8 erzeugte das Modell über 30 identische `search_content`-Befehle mit ungültigem Cursor.
- In v9 las das Modell identische Codezeilen bis zu 62-mal erneut ein (Duplikatsrate: 82,6 %).

---

## 5. Gemeinsame Muster über alle Generationen (Invarianzen)

Bei der vergleichenden Betrachtung lassen sich sechs generationenübergreifende Invarianzen destillieren:

1. **Frühe Quell- und Testlokalisierung:**  
   In jedem einzelnen Lauf (unabhängig von Generation oder Aufgabe) identifizierte der Analysis-Agent die betroffenen Quell- und Testdateien innerhalb kurzer Zeit. Die funktionale Orientierungsaufgabe war stets informationell frühzeitig abgeschlossen.

2. **Verengung des genutzten Aktionsraums:**  
   Obwohl den Agenten je nach Generation vielfältige Werkzeuge angeboten wurden (`repo_overview`, `classify_path`, `read_environment`, `update_context`), konzentrierte sich das reale Nutzungsverhalten zu über 90 % auf die zwei Basiswerkzeuge `search_content` und `read_file`.

3. **Die Rollenübergangsschwelle als primärer System-Flaschenhals:**  
   In den regulär abgeschlossenen Generationen v6 und v9 sowie dem Teillauf v7-2 vollzog das System in 100 % der Fälle keinen erfolgreichen regulären Rollenübergang. Die Architektur blieb vollständig in der ersten Phase (`analysis`) blockiert. Nur ein technischer Zwangseingriff (v8) oder fehlerhafte Freeze-Zustände (v7-1) aktivierten die QA-Rolle.

4. **Wirkungslosigkeit natürlicher textueller Recovery-Meldungen:**  
   Hinweise des Controllers im User- oder Ledger-Prompt (z. B. *"Read a different relevant source or run a focused diagnostic"* in v6 oder *"Read existing findings, narrow the search or finish the delivery"* in v9) bewirkten in keinem einzigen dokumentierten Fall eine Verhaltensänderung oder einen Phasenwechsel des Modells.

5. **Empirische Invarianz zwischen den Studienarmen (Cubie vs. Pytest):**  
   Da die Testphase (Rolle `qa` und `dev`) in keinem regulären Lauf aktiv gestaltend erreicht wurde, blieben die Frameworkanweisungen für `cubie` bzw. `pytest` wirkungslos. Die Unterschiede in Laufzeiten, Tokengrößen und Einzelschritten zwischen den beiden Studienarmen beruhten ausschließlich auf der stochastischen Varianz der Modellgenerierung.

6. **Null-Modifikation der Arbeitskopie (Erfolgsquote 0,0 %):**  
   Über alle 17 durchgeführten Läufe der Generationen v6 bis v9 hinweg wurden in keinem Fall Änderungen am Produktionscode vorgenommen (0 Bytes Patches). Keine der privaten Gold-Suiten wurde gelöst (`resolved: false` in 100 % der Fälle).

---

## 6. Zusammenfassendes Fazit

Die vergleichende Analyse der Agenten-Generationen v6, v7, v8 und v9 belegt eine deutliche Entkopplung zwischen **Infrastrukturreife** und **Ablaufwirksamkeit**:

- **Auf der Infrastrukturebene** gelang über die Generationen hinweg eine kontinuierliche Verfeinerung des Systems: Formatbrüche (v5) wurden eliminiert (v6), Kontextgrößen und Prompt-Bürokratie (v7) wurden bereinigt (v8), und Werkzeug-Schnittstellen sowie Kontextgedächtnisse wurden fehlertolerant und transparent auf reine Markdown-Strukturen umgestellt (v9).
- **Auf der Steuerungsebene** blieb das Kernproblem über alle vier Generationen hinweg unverändert bestehen: Die Unfähigkeit eines kompakten 12B-Modells, ohne expliziten externen Steuerungsanreiz den Übergang von der passiven Informationsaufnahme (Suchen und Lesen) zum aktiven Phasenabschluss (`finish` / Handoff) eigenständig zu initiieren.
