# `class EBT`

Die `EBT`-Klasse ist die zentrale Orchestrierungs-Engine des Frameworks. Sie dient als direkte architektonische Übersetzung des formalen $\{P\}S\{Q\}$ Paradigmas in ausführbaren Code und orchestriert die Zustände.

## Kern-Verantwortlichkeiten

**Auto-Inferenz:**  
Um die Entwickler-Erfahrung (DX) schlank zu halten und Boilerplate-Code zu minimieren, unterstützt das Framework Shorthand-Eingaben. Die `EBT`-Klasse delegiert die komplexe Logik der automatischen Typen-Inferenz (das Umwandeln von primitiven Datentypen in standardisierte `WorldState`-Objekte) jedoch vollständig an die dedizierte `ConventionMap`. Details hierzu sind im entsprechenden DEV-GUIDE der `ConventionMap` dokumentiert.

**Erweiterte Formallogische Engine:**  
  Die Klasse steuert den iterativen Prüfprozess für komplexe Lösungsräume. Sie verwaltet dabei drei fundamentale Zustands-Säulen auf Augenhöhe:
* **`pre` (Vorbedingung):** Definiert den Ausgangszustand. Werden Listen übergeben, wendet die Engine deterministisch das Prinzip des beschränkten Allquantors ($\forall$) an und führt für jeden deklarierten Zustand einen isolierten Prüfdurchlauf aus.
* **`_outcome` (Tatsächliches Resultat):** Repräsentiert die ungeschönte Realität *nach* der Ausführung des Targets. Das Handling und die physische Aggregation dieses Zustands (insbesondere von topologischen Mutationen und Seiteneffekten) wird in Zusammenarbeit mit der isolierten `Arena` und deren `Arena-Protokoll` erzeugt und verwaltet.
* **`post` (Nachbedingung):** Definiert den erwarteten Soll-Zustand. Werden Listen übergeben, wendet die Engine das Prinzip des beschränkten Existenzquantors ($\exists$) an. Der Testzyklus gilt als bestanden, sobald das `_outcome` mit mindestens einem der definierten `post`-Zustände übereinstimmt (ODER-Verknüpfung).

---

## EBT-Attribute

### EBT-Objekt-Attribute

#### `EBT.arena`
Definiert den isolierten Ausführungsraum (die Sandbox), in dem das Programmsegment ($S$) operiert. Wird die Arena hier auf Ebene der `EBT`-Klasse definiert, dient sie als konstanter, unveränderlicher Ausführungsraum für die gesamte Transformation. Sie kann lokal auf `WorldState`-Ebene überschrieben werden, wenn das Target explizit die Aufgabe hat, seine Umgebung selbst zu mutieren.

#### `EBT.target`
Repräsentiert das auszuführende Programmsegment ($S$), welches die Transformation von der Vorbedingung zur Nachbedingung vornimmt. Das Attribut akzeptiert direkte Callables (Python-Funktionen, Klassen oder Methoden), die in das Testmodul importiert und als direkte Referenz übergeben werden.

### EBT-Konfigurations-Attribute

#### `EBT.custom_id` und `EBT._run_id`
Dienen der eindeutigen Identifikation eines Testdurchlaufs. `custom_id` erlaubt es dem Entwickler, dem Lauf einen semantischen Namen zu geben, während `_run_id` intern als eindeutiger Identifier (inklusive UUID) für Tracing, Logging und Debugging der iterativen Quantoren-Schritte generiert wird.

#### `EBT.expect`
Ein boolescher Modifikator (Standard: `True`), der die formallogische Erwartungshaltung des gesamten Testlaufs invertiert. Wird `expect` auf `False` gesetzt, deklariert dies einen expliziten Negativ-Test – der Test leuchtet grün, wenn die Ausführung *fehlschlägt* bzw. die Assertions *nicht* zutreffen.  Sie kann lokal auf `WorldState`-Ebene überschrieben werden, um die Zustands-Deklarationen granular invertieren zu können.

### EBT-Zustands-Attribute

#### `EBT.pre`: `List[WorldState]`
Definiert das $P$ (Pre-Condition) im Hoare-Tripel. Es kapselt die Eingabewerte (`args`, `kwargs`) und topologischen Ausgangsstrukturen (`fs`), mit denen die `Arena` und das `target` vorbereitet werden. 

#### `EBT._outcome`: `List[WorldState]`
Das Resultat der Ausführung. Es fungiert als Trägerobjekt für die tatsächliche Realität nach der Ausführung des Targets. Es kapselt die direkten funktionalen Rückgabewerte (`returns`), sowie die Filesystem-Zustände `fs` und die durch die Environment-Seiteneffekte `arena` (.venv), um sie generisch gegen die `post`-Zustände abgleichen zu können.

#### `EBT.post`: `List[WorldState]`
Definiert das $Q$ (Post-Condition) im Hoare-Tripel. Es fungiert als reines Assertion-Objekt, gegen welches das generierte `_outcome`-Attribut durch die EBT-Engine verifiziert wird. 

### EBT-Prozessierungs-Attribute

#### `EBT._traces`: `List[EvaluationTrace]`
Eine interne Liste, welche die vollständige Historie und Evaluation aller Teilschritte eines Testlaufs aufzeichnet. Jedes `EvaluationTrace`-Objekt kapselt exakt einen $\forall$-$\exists$-Vergleich (bestehend aus Target, spezifischem `pre`, erwartetem `post`, generiertem `_outcome` und dem booleschen Match-Ergebnis). Diese Traces bilden das Fundament für die finale Fehler-Aggregation in der `_report()`-Phase.

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

### Lebenszyklus

#### Steps
Ein Step repräsentiert exakt einen $\{P\}S\{Q\}$ Durchlauf für einen spezifischen Ausgangszustand (Index $i$) und operiert als in sich geschlossene Mikro-Pipeline. Er durchläuft seine eigenen drei Mikro-Phasen:
1. **Mikro-Arrange:** Zuweisung des deterministischen Ausgangszustands `pre[i]` und der zugehörigen Zielzustände `post[n]`. Die Abbildung gegen eine Menge $n$ ist essenziell, da im Falle eines Existenzquantors mehrere valide Endzustände für ein einzelnes `_outcome` existieren können.
2. **Mikro-Validate:** Aufbau der physischen Arena, synchrone Ausführung des Targets und das rein wertungsfreie Erfassen der entstandenen Realität in ein `_outcome[i]`-Objekt.
3. **Mikro-Report:** Der sofortige Abgleich des `_outcome[i]`-Objekts mit den erwarteten `post[n]`-Zuständen (inkl. I/O-lastigem Byte-Diffing). Hierbei wird auch das **lokale `expect`-Attribut** des jeweiligen `WorldState`-Objekts berücksichtigt, um gezielte Negativ-Evaluationen (Invertierung der Erwartungshaltung) direkt auf Mikro-Ebene sauber aufzulösen. Die Ergebnisse werden als rohe `EvaluationTrace`-Objekte verpackt. 
Das macht den Step extrem ressourceneffizient und ermöglicht es, hunderte Steps sicher parallel zu orchestrierenä

#### Runs
Ein Run ist die Makro-Ebene und aggregiert die gesamte Menge aller definierten Steps einer `EBT`-Instanz. Er steuert den übergeordneten Lebenszyklus. Er garantiert, dass alle Zustände geordnet vorbereitet werden, triggert die (zukünftig parallele) Abarbeitung der Mikro-Steps und konsolidiert am Ende die gesammelten, rohen Evaluations-Daten, um formallogische Quantoren auf das Gesamtbild anzuwenden.

### Phasen-Verantwortlichkeiten

#### Arrange (Mapping und Vorbereitung)
Diese Makro-Phase sichert die formale Integrität des gesamten Runs. Sie validiert die Ausführbarkeit, delegiert die Shorthand-Inferenz an die `ConventionMap` und normalisiert Datentypen. Ihre primäre Verantwortung ist es, die Listen-Strukturen für `pre` und `post` aufzubauen, um die Index-Topologie für die Steps bereitzustellen.

#### Validate (Ausführung & Mikro-Evaluation)
Die Validate-Phase agiert als Orchestrator für die Mikro-Steps. Sie iteriert über die vorbereiteten Listen und triggert die Transformationen.
Innerhalb dieser Makro-Phase finden die gesamten `Mikro-Validate` und `Mikro-Report` Lebenszyklen der Steps statt.  
* **Mikro-Arrange:** Aufbau der Arena. 
* **Mikro-Validate:** Ausführung des Targets in der Arena. Die Daten der Arenen-Zustände werden als WorldState-Objekt auf Klassen-Ebene im `_outcome`-Attribut gesammelt. 
* **Mikro-Report:** Abschließend findet die Mikro-Evaluation und der direkte Abgleich gegen die `post[n]`-Zustände (inklusive deren lokaler `expect`-Regeln) statt. Die resultierenden, rohen `EvaluationTrace`-Objekte werden auf Klassen-Ebene im `_traces`-Attribut gesammelt.

#### Report (Auswertung der Ergebnisse, Formatierung zum Bericht und Assertion)
Die finale Makro-Phase ist vollständig von der Ausführung und den Dateisystemen entkoppelt (keinerlei I/O-Last). Rein konzeptuell sollte es dennoch während der Report-Phase möglich sein, basierend auf den `self.pre`-, `self._outcome`-, und `self.post`-Listen, die Evaluation erneut durchzuführen. In der Praxis verlassen wir uns in der Makro-Report-Phase im Regelfall auf die reine Konsolidierung der rohen `EvaluationTrace`-Liste.
Anhand dieser Traces wendet die Phase rein logische Operationen (die Auflösung von All- und Existenzquantoren, $\forall$ und $\exists$) an, bereitet basierend auf dem **globalen `expect`-Modifikator** der `EBT`-Klasse die finale Assertion vor, erzeugt potentiell noch einen Diff und formatiert den Bericht für die Assertion, um den run mit der Übergabe an PyTest abzuschließen.

---

## 4. Architektonische Visualisierung

Um das Zusammenspiel zwischen Makro-Orchestrierung (Runs) und Mikro-Ausführung (Steps) sowie die topologische Datenbindung zu verdeutlichen, lassen sich die internen Datenflüsse visuell darstellen.

### 4.1 Anatomie des EvaluationTrace

![Alternativtext](docs/assets/EvaluationTrace.jpg "Error while trying to load the image")

### 4.2 Die Makro-/Mikro-Orchestrierung (Runs & Steps)

![Alternativtext](docs/assets/runs_and_steps.jpg "Error while trying to load the image")