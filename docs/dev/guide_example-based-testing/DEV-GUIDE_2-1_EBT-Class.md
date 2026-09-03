# `class EBT`

Die `EBT`-Klasse dient als direkte architektonische Übersetzung des formalen $\{P\}S\{Q\}$ Paradigmas in ausführbaren Code und orchestriert die Zustände.

## Kern-Verantwortlichkeiten

#### **Auto-Inferenz:**  
Um die Entwickler-Erfahrung (DX) schlank zu halten und Boilerplate-Code zu minimieren, unterstützt das Framework Shorthand-Eingaben. Die `EBT`-Klasse delegiert die komplexe Logik der automatischen Typen-Inferenz (das Umwandeln von primitiven Datentypen in standardisierte `WorldState`-Objekte) jedoch vollständig an die dedizierte `ConventionMap`. Details hierzu sind im entsprechenden DEV-GUIDE der `ConventionMap` dokumentiert.

#### **Erweiterte Formallogische Engine:**  
  Die Klasse steuert den iterativen Prüfprozess für komplexe Lösungsräume. Sie verwaltet dabei drei fundamentale Zustands-Säulen auf Augenhöhe:
* **`pre` (Vorbedingung):** Definiert den Ausgangszustand. Werden Listen übergeben, wendet die Engine deterministisch das Prinzip des beschränkten Allquantors ($\forall$) an und führt für jeden deklarierten Zustand einen isolierten Prüfdurchlauf aus.
* **`_outcome` (Tatsächliches Resultat):** Repräsentiert die ungeschönte Realität *nach* der Ausführung des Targets. Das Handling und die physische Aggregation dieses Zustands (insbesondere von topologischen Mutationen und Seiteneffekten) wird in Zusammenarbeit mit der isolierten `Arena` und deren `Arena-Protokoll` erzeugt und verwaltet.
* **`post` (Nachbedingung):** Definiert den erwarteten Soll-Zustand. Werden Listen übergeben, wendet die Engine das Prinzip des beschränkten Existenzquantors ($\exists$) an. Der Testzyklus gilt als bestanden, sobald das `_outcome` mit mindestens einem der definierten `post`-Zustände übereinstimmt (ODER-Verknüpfung).

---

---

## EBT-Attribute

### EBT-Objekt-Attribute

#### `EBT.arena`
Definiert den isolierten Ausführungsraum (die Sandbox), in dem das Programmsegment ($S$) operiert. Wird die Arena hier auf Ebene der `EBT`-Klasse definiert, dient sie als konstanter, unveränderlicher Ausführungsraum für die gesamte Transformation. Sie kann lokal auf `WorldState`-Ebene überschrieben werden, wenn das Target explizit die Aufgabe hat, seine Umgebung selbst zu mutieren.

#### `EBT.target`
Repräsentiert das auszuführende Programmsegment ($S$), welches die Transformation von der Vorbedingung zur Nachbedingung vornimmt. Das Attribut akzeptiert direkte Callables (Python-Funktionen, Klassen oder Methoden), die in das Testmodul importiert und als direkte Referenz übergeben werden.

#### `EBT.reporter`
Dient als Dependency-Injection-Mechanismus für die externe Fehlerbehandlung und das finale Reporting. Es akzeptiert jedes Objekt, das dem `Reporter`-Protokoll entspricht (standardmäßig der `PytestReporter`). Dieses Attribut entkoppelt die formallogische Auswertung der Engine vollständig von spezifischen Test-Frameworks. Wird hier `None` deklariert, operiert die EBT-Instanz im lautlosen "Headless Mode" und delegiert keine Assertions nach außen.

---

### EBT-Konfigurations-Attribute

#### `EBT.custom_id` und `EBT._run_id`
Dienen der eindeutigen Identifikation eines Testdurchlaufs. `custom_id` erlaubt es dem Entwickler, dem Lauf einen semantischen Namen zu geben, während `_run_id` intern als eindeutiger Identifier (inklusive UUID) für Tracing, Logging und Debugging der iterativen Quantoren-Schritte generiert wird.

#### `EBT.expect`
Ein boolescher Modifikator (Standard: `True`), der die formallogische Erwartungshaltung des gesamten Testlaufs invertiert. Wird `expect` auf `False` gesetzt, deklariert dies einen expliziten Negativ-Test – der Test leuchtet grün, wenn die Ausführung *fehlschlägt* bzw. die Assertions *nicht* zutreffen.  Sie kann lokal auf `WorldState`-Ebene überschrieben werden, um die Zustands-Deklarationen granular invertieren zu können.

#### `EBT.FS_IGNORES` und `EBT.ARENA_IGNORES`

Beides sind Set-basierte Konfigurations-Attribute (`Set[str]`), welche das strikte Byte-by-Byte-Diffing während der Validierungsphase steuern. Sie definieren präzise, welche Dateien oder Verzeichnisse bei der Evaluation der Zielzustände ignoriert werden, um Test-Flakiness durch flüchtige Daten oder erwartete, aber bedeutungslose Seiteneffekte zu verhindern.

* **`EBT.FS_IGNORES`:** Dieses Set ist standardmäßig leer (`{""}`). Es greift tief in der `_evaluate_fs`-Methode. Wenn ein Pfad-Segment (Datei oder Ordnername) in diesem Set gelistet ist, wird das entsprechende Element mitsamt aller rekursiv darin verschachtelten Unterordner vollständig vom Dateisystem-Abgleich ausgeschlossen. Das ist ideal, um irrelevante Build-Artefakte (z. B. `build/`) oder dynamisch generierte Dateien aus der Gleichung zu nehmen, ohne die formale Logik des Tests zu brechen.
* **`EBT.ARENA_IGNORES`:** Dieses Set enthält standardmäßig eine kuratierte Liste von flüchtigen Metadaten und umgebungsspezifischen Pfaden (z. B. `bin`, `Scripts`, `pyvenv.cfg`, `__pycache__`, `_virtualenv.py`). Es wird durch die `_evaluate_arena`-Methode (bzw. `_compare_venv_contents`) beim Abgleich isolierter Umgebungen wie der `PyVenv`-Arena herangezogen. Dies garantiert kompromisslos, dass systembedingte Varianzen, Caches oder flüchtige Paket-Hashes (wie `.dist-info`) die Evaluation des funktionalen Zustands nicht destabilisieren.

#### `EBT.MULTIPROCESSING`
Ein boolesches Konfigurations-Attribut (Standard: `False`), das die Skalierungs- und Ausführungsstrategie der zentralen Validierungsphase (`_validate`) steuert. 

* **`EBT.MULTIPROCESSING=False` (Singleprocessing):** Die Engine iteriert sequenziell über alle definierten `pre`-Zustände. Dies ist das robuste Standardverhalten, ideal für einfache Tests und essenziell für lineares Debugging von fehlschlagenden Transformationen.
* **`EBT.MULTIPROCESSING=True` (Multiprocessing):** Aktiviert die parallele Abarbeitung der Tasks mittels eines `ProcessPoolExecutor`. Die Engine teilt die Menge aller Eingabezustände (den beschränkten Allquantor $\forall$) dynamisch in Chunks auf und verteilt sie auf die verfügbaren System-Kerne (`os.cpu_count()`).

**Architektonische Grundlage:** 
Das parallele Ausführen ist nur deshalb sicher und stabil möglich, weil das Framework eine strikt zustandslose Mikro-Pipeline (`_process_single_task`) nutzt. Jeder einzelne Task orchestriert sein eigenes `Arena`-Setup, die Target-Ausführung, die Evaluation und das abschließende `Arena`-Teardown völlig isoliert in seinem Worker-Prozess. So können selbst komplexe Testläufe mit I/O-lastigem Byte-Diffing und isolierten Virtual-Environments kollisionsfrei und extrem performant skaliert werden.

---

### EBT-Zustands-Attribute

#### `EBT.pre`: `List[WorldState]`
Definiert das $P$ (Pre-Condition) im Hoare-Tripel. Es kapselt die Eingabewerte (`args`, `kwargs`) und topologischen Ausgangsstrukturen (`fs`), mit denen die `Arena` und das `target` vorbereitet werden. 

#### `EBT._outcome`: `List[WorldState]`
Das Resultat der Ausführung. Es fungiert als Trägerobjekt für die tatsächliche Realität nach der Ausführung des Targets. Es kapselt die direkten funktionalen Rückgabewerte (`returns`), sowie die Filesystem-Zustände `fs` und die durch die Environment-Seiteneffekte `arena` (.venv), um sie generisch gegen die `post`-Zustände abgleichen zu können.

#### `EBT.post`: `List[WorldState]`
Definiert das $Q$ (Post-Condition) im Hoare-Tripel. Es fungiert als reines Assertion-Objekt, gegen welches das generierte `_outcome`-Attribut durch die EBT-Engine verifiziert wird. 

---

### EBT-Prozessierungs-Attribute

#### `EBT._traces`: `List[EvaluationTrace]`
Eine interne Liste, welche die vollständige Historie und Evaluation aller Teilschritte eines Testlaufs aufzeichnet. Jedes `EvaluationTrace`-Objekt kapselt exakt einen $\forall$-$\exists$-Vergleich (bestehend aus Target, spezifischem `pre`, erwartetem `post`, generiertem `_outcome`, den vorberechneten `diffs` und dem booleschen Match-Ergebnis). Diese Traces bilden das Fundament für die finale Konsolidierung.

#### `EBT._run_duration`: `Optional[float]`
Erfasst die exakte Ausführungszeit der gesamten Validierungs-Makro-Phase, um saubere Performance-Metriken für den Abschlussbericht bereitzustellen.

#### `EBT._run_evaluation`: `Optional[bool]`
Speichert das absolute, formallogische Endergebnis des gesamten Testlaufs. Dieser Wert wird in der `_evaluate_run`-Pipe berechnet, indem die Quantoren-Logik der Mikro-Steps zusammengeführt und der globale `expect`-Modifikator der `EBT`-Klasse angewendet wird.

#### `EBT.run_trace`: `Optional[RunTrace]`
Das finale, unveränderliche Trägerobjekt der Auswertung. Es bündelt den gesamten Kontext des Runs: Alle rohen `EvaluationTrace`-Objekte, die `_run_duration` und die finale `_run_evaluation`. Dieses Objekt wird als unteilbarer Fakt an den deklarierten `reporter` übergeben und bildet immer den verbindlichen Rückgabewert der öffentlichen `run()`-Methode.

---

---

## EBT-Design

### Pattern

#### Allgemeine Muster
Die Architektur des EBT-Moduls ist eine direkte softwaretechnische Manifestation der deterministischen Hoare-Logik ($\{P\}S\{Q\}$). Das Design folgt einem strikten Pipeline-Muster, das sich fraktal verhält: Die großen Makro-Phasen des gesamten Testlaufs spiegeln sich in isolierten Mikro-Phasen für jede einzelne Zustands-Transformation wider. 
Ein zentrales Muster ist dabei die **Index-Topologie** (Objekt-Synchronität). Die Zustände existieren als Listen, die fest miteinander verankert sind: Ein `pre[i]` führt zwingend zu einem `_outcome[i]`, welches anschließend gegen eine Menge definierter Zielzustände `post[n]` validiert wird. Diese Entkopplung von Ausführung und Evaluation legt das Fundament für asynchrone Parallelisierungen.

#### Komponenten
Die Klasse strukturiert ihre internen Methoden nach einem klaren Paradigma:
* **Services:** Die öffentliche API der Klasse (primär die `run()`-Methode), welche den globalen Lebenszyklus initiiert.
* **Pipes:** Die zentralen Phasen-Orchestratoren (`_arrange`, `_validate`, `_report`), welche den sequenziellen Datenfluss durch die Makro-Architektur steuern.
* **Utilities:** Isolierte, zustandslose Hilfsfunktionen (wie Pfad-Normalisierungen, Byte-Diffing-Algorithmen oder formallogische Evaluatoren), die von den Pipes aufgerufen werden, um spezifische Teilaufgaben zu lösen.

---

### Lebenszyklus

#### Steps
Ein Step repräsentiert exakt einen $\{P\}S\{Q\}$ Durchlauf für einen spezifischen Ausgangszustand (Index $i$) und operiert als in sich geschlossene Mikro-Pipeline. Er durchläuft seine eigenen drei Mikro-Phasen:
1. **Mikro-Arrange:** Zuweisung des deterministischen Ausgangszustands `pre[i]` und der zugehörigen Zielzustände `post[n]`. Die Abbildung gegen eine Menge $n$ ist essenziell, da im Falle eines Existenzquantors mehrere valide Endzustände für ein einzelnes `_outcome` existieren können.
2. **Mikro-Validate:** Aufbau der physischen Arena, synchrone Ausführung des Targets und das rein wertungsfreie Erfassen der entstandenen Realität in ein `_outcome[i]`-Objekt.
3. **Mikro-Report:** Der sofortige Abgleich des `_outcome[i]`-Objekts mit den erwarteten `post[n]`-Zuständen (inkl. I/O-lastigem Byte-Diffing). Hierbei wird auch das **lokale `expect`-Attribut** des jeweiligen `WorldState`-Objekts berücksichtigt, um gezielte Negativ-Evaluationen (Invertierung der Erwartungshaltung) direkt auf Mikro-Ebene sauber aufzulösen. Die Ergebnisse werden als rohe `EvaluationTrace`-Objekte verpackt. 
Das macht den Step extrem ressourceneffizient und ermöglicht es, hunderte Steps sicher parallel zu orchestrieren.

#### Runs
Ein Run ist die Makro-Ebene und aggregiert die gesamte Menge aller definierten Steps einer `EBT`-Instanz. Er steuert den übergeordneten Lebenszyklus. Er garantiert, dass alle Zustände geordnet vorbereitet werden, triggert die (zukünftig parallele) Abarbeitung der Mikro-Steps, konsolidiert am Ende die gesammelten Evaluations-Daten in einem formallogischen `RunTrace`-Objekt und delegiert dieses an den injizierten Reporter. Den Abschluss des Lebenszyklus bildet immer die verbindliche Rückgabe dieses `RunTrace`-Objekts an das aufrufende System.

---

### Phasen-Verantwortlichkeiten

#### Arrange (Mapping und Vorbereitung)
Diese Makro-Phase sichert die formale Integrität des gesamten Runs. Sie validiert die Ausführbarkeit, delegiert die Shorthand-Inferenz an die `ConventionMap` und normalisiert Datentypen. Ihre primäre Verantwortung ist es, die Listen-Strukturen für `pre` und `post` aufzubauen, um die Index-Topologie für die Steps bereitzustellen.

#### Validate (Ausführung & Mikro-Evaluation)
Die Validate-Phase agiert als Orchestrator für die Mikro-Steps. Sie iteriert über die vorbereiteten Listen und triggert die Transformationen.
Innerhalb dieser Makro-Phase finden die gesamten `Mikro-Validate` und `Mikro-Report` Lebenszyklen der Steps statt.  
* **Mikro-Arrange:** Aufbau der Arena. 
* **Mikro-Validate:** Ausführung des Targets in der Arena. Die Daten der Arenen-Zustände werden als WorldState-Objekt auf Klassen-Ebene im `_outcome`-Attribut gesammelt. 
* **Mikro-Report:** Abschließend findet die Mikro-Evaluation und der direkte Abgleich gegen die `post[n]`-Zustände (inklusive deren lokaler `expect`-Regeln) statt. Die resultierenden, rohen `EvaluationTrace`-Objekte werden auf Klassen-Ebene im `_traces`-Attribut gesammelt.

#### Evaluate & Report (Auswertung, Konsolidierung und Delegation)
Die finale Makro-Phase ist vollständig von der Ausführung und den Dateisystemen entkoppelt (keinerlei I/O-Last). Mit der Souveränität der Engine teilt sich dieser Abschlussbereich glasklar in zwei separate Verantwortlichkeiten auf:

* **Die `_evaluate_run`-Logik (Fakten-Konsolidierung):** Anhand der gesammelten `EvaluationTrace`-Objekte wendet diese Phase rein logische Operationen an (die Auflösung von All- und Existenzquantoren, $\forall$ und $\exists$) und berechnet basierend auf dem **globalen `expect`-Modifikator** der `EBT`-Klasse das absolute Endergebnis. Diese Auswertung wird völlig wertungsfrei als Fakt in einer unveränderlichen `RunTrace`-Datenstruktur deklariert.
* **Die `_report`-Pipe (Delegation):** Diese Phase übernimmt die Orchestrierung nach außen. Sie triggert die Evaluation und übergibt das fertige `RunTrace`-Objekt an den injizierten Reporter (standardmäßig den `PytestReporter`). Alle Pytest-spezifischen Assertions, String-Formatierungen und Diff-Reports sind vollständig in diesen Reporter ausgelagert. Wird `None` als Reporter deklariert, bleibt die Phase lautlos.

Abschließend retourniert die öffentliche `run()`-Service-Methode das `RunTrace`-Objekt, um eine programmatische Weiterverarbeitung zu ermöglichen.

---

---

## 4. Architektonische Visualisierung

Um das Zusammenspiel zwischen Makro-Orchestrierung (Runs) und Mikro-Ausführung (Steps) sowie die topologische Datenbindung zu verdeutlichen, lassen sich die internen Datenflüsse visuell darstellen.

### 4.1 Anatomie des EvaluationTrace

![Alternativtext](docs/assets/EvaluationTrace.jpg "Error while trying to load the image")

### 4.2 Die Makro-/Mikro-Orchestrierung (Runs & Steps)

![Alternativtext](docs/assets/runs_and_steps.jpg "Error while trying to load the image")