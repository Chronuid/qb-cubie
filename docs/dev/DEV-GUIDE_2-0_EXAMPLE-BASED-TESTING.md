<center>

# `EXAMPLE-BASED-TESTING`

![Error while trying to load the image](docs/.assets/cubie-logo-written.png) 

Das Example-Based-Testing (EBT) fungiert als kompromisslose Basis der Qualitätssicherung, indem es deterministische Realitäten als "Golden Master" definiert. Basierend auf dem klassischen Hoare-Tripel $\{P\}S\{Q\}$ spannt das Konzept den Raum von einfachen In-Memory-Funktionen bis hin zu komplexen Datei- und Ordner-Transformationen auf.
</center>


---

---

## `class EBT`
Die `EBT`-Klasse ist die zentrale Orchestrierungs-Engine des Frameworks. Sie dient als direkte architektonische Übersetzung des formalen P S Q Paradigmas in ausführbaren Code. Die Klasse selbst agiert dabei als direktes Interface für die Definition der Test-Fälle.

**Kern-Verantwortlichkeiten:**

* **Auto-Inferenz:**
Um die Entwickler-Erfahrung (DX) schlank zu halten und Boilerplate-Code zu minimieren, fungiert die Klasse als intelligenter Übersetzer. Sie nimmt Datentypen entgegen und konvertiert diese implizit in vollumfängliche, standardisierte `WorldState`-Objekte.

* **Erweiterte Formallogische Engine (Quantoren-Auflösung):**
Die Klasse steuert den iterativen Prüfprozess für komplexe Lösungsräume.
   * Werden Vorbedingungen (`pre`) als WorldState-Listen übergeben, wendet die Klasse deterministisch das Prinzip des beschränkten Allquantors ($\forall$) an, führt jeden Zustand isoliert aus und verknüpft die Assertions mit einem logischen UND.
   * Werden Nachbedingungen (`post`) als WorldState-Listen übergeben, schaltet die Engine auf das Prinzip des beschränkten Existenzquantors ($\exists$) um und bewertet den Test als bestanden (ODER-Verknüpfung), sobald der Output mit einem Element der Zielmenge übereinstimmt.

---

## `class WorldState`

Die `WorldState`-Klasse ist ein Zustands-Deklarator, der alle Variablen einer Test-Welt kapselt. Sie dient als standardisierte Datenstruktur zur Definition von Zuständen. Seien es nun Vorbedingungen ($P$) oder Nachbedingungen ($Q$) innerhalb des EBT-Paradigmas.
Die Klasse ist konzeptionell die Antwort auf die Frage, wie man komplexe Tests sauber abbildet, ohne den Code mit Boilerplate zu überladen. 
Sie fungiert als das einheitliche Ziel-Schema, in welches die übergeordnete `EBT`-Klasse alle primitiven Eingaben (Shorthands) implizit konvertiert.

* **Die Kernidentität:** Die Klasse fungiert als strikter "Zustands-Deklarator". Sie ist das standardisierte Objekt, das eine konkrete "Welt" (sei es $P$ oder $Q$) kapselt.

* **Die Trennung der Ebenen:** Ihre wichtigste strukturelle Eigenschaft ist die klare Trennung: Sie separiert die funktionale Ausführungsebene, wie Code-Inputs (`args`) oder Outputs (`returns`), strikt von der topologischen Dateisystem-Ebene (`fs`).

* **Das Normalisierungs-Ziel:** Das `WorldState`-Objekt ist das interne Zielformat der `EBT`-Klasse. Die `EBT`-Klasse nutzt Auto-Inferenz, um einfache Datentypen (Shorthands) unter der Haube implizit in vollumfängliche `WorldState`-Objekte umzuwandeln.

---

## `class Arena(Protocol)`

Während die `EBT`-Klasse die formallogische Makro-Orchestrierung übernimmt und `WorldState` die Datenstruktur deklariert, ist das Arena-Protokoll für die physische Realität zuständig. Arenen kapseln die eigentliche Ausführung (das $S$ im Hoare-Tripel) und isolieren Seiteneffekte vom Host-System.

* **Trennung von Orchestrierung und Ausführung:** Die EBT-Engine delegiert die Erschaffung der Testumgebung, die Ausführung des Targets und das Einsammeln der Resultate vollständig an die Arena.
* **State-Injection:** Die Arena empfängt über ihre `setup(state: WorldState)`-Methode den deklarierten Ausgangszustand, projiziert diesen in einen isolierten Workspace und liefert nach der Ausführung über `get_state() -> WorldState` die veränderte, ungeschönte Realität an die Engine zurück.
* **Spezialisierung:** Cubie bietet standardmäßig `PyVenv` für vollständige Laufzeit-Isolation (via Subprozesse und `uv`) und `TempFS` als extrem leichtgewichtige In-Memory-Alternative für reine Dateioperationen.

---

## `class RunTrace` und `EvaluationTrace`

Die `RunTrace`-Datenklasse fungiert, zusammen mit den von ihr gekapselten `EvaluationTrace`-Objekten, als universeller, unveränderlicher Ergebnisträger eines Testlaufs. Anstatt Ergebnisse direkt zu assertieren oder flüchtig zu verarbeiten, gießt die `EBT`-Engine die gesamte formallogische Evaluation in diese feste Datenstruktur.

* **Die Souveränität der Engine:** Die EBT-Klasse berechnet ausschließlich formallogische Fakten (die Auflösung der Quantoren $\forall$ und $\exists$) und speichert das finale Ergebnis im Attribut `evaluation`. 
* **Historie und Nachvollziehbarkeit:** Eine `RunTrace` bündelt den gesamten Kontext eines Durchlaufs: Sie enthält Metadaten wie die Laufzeit (`duration`), den Modifikator (`expect`) und eine detaillierte Auflistung aller durchgeführten Mikro-Steps in Form von `EvaluationTrace`-Objekten.
* **Prä-kalkulierte Diffs:** Jeder `EvaluationTrace` speichert bereits die ermittelten Abweichungen (Returns, Dateisystem-Topologie, Arena-State) im `diffs`-Attribut ab. Das macht nachgelagerte Analysen hochperformant, da keine Werte ein zweites Mal verglichen werden müssen.

---

## `class Reporter(Protocol)`

Um die Kern-Architektur des Cubie-Frameworks vollständig von spezifischen Test-Runnern (wie Pytest) zu entkoppeln, wurde das `Reporter`-Protokoll etabliert. Reporter sind reine Konsumenten der `RunTrace`-Datenstruktur.

* **Trennung von Evaluation und Assertion:** Während die `EBT`-Klasse die Logik auswertet, übernimmt ein injizierter Reporter (z. B. der `PytestReporter`) ausschließlich die Formatierung von Fehlermeldungen und das Auslösen framework-spezifischer Assertions (z. B. `assert False`), sofern `trace.evaluation is False` gilt.
* **Meta-Testing und Headless Runs:** Wird der EBT-Instanz `None` als Reporter übergeben, arbeitet die Engine völlig lautlos. In diesem "Headless Mode" wirft die Ausführung keine Exceptions, sondern die `run()`-Methode gibt am Ende schlicht das `RunTrace`-Objekt zurück. 
* **Programmatische Weiterverwendung:** Dieser geräuschlose Rückfluss ermöglicht komplexe Architektur-Szenarien, wie beispielsweise Meta-Testing (eine EBT-Instanz testet eine andere EBT-Instanz) oder die Anbindung der Evaluationsdaten an grafische Benutzeroberflächen (z. B. via Tkinter für Review-Workflows) oder die Konstruktion von PBT- und Benchmark-Verfahren.

---

---

## Weiteres

### Target-Execution (S) & Asynchronität
Das EBT-Modul kümmert sich nicht darum, ob eine Funktion synchron oder asynchron aufgerufen wird. Sie kümmert sich lediglich um die Vorbedingungen und Nachbedingungen der Funktion.

Es reicht nicht nur für den MVP, wenn die _validate-Phase dieses Callable rein synchron via self.target(*args, **kwargs) aufgerufen wird.
Zudem gilt auch für die Zukunft, dass asynchrone Funktionen nicht von der EBT-Klasse selbst berücksichtigt werden müssen. Dementsprechend gilt, dass die EBT-Klasse keine await oder asyncio.run Implementierungen  benötigt, sondern die Verantwortung und Authorität über die Art des Aufrufs von Funktionen und die Art der Gestaltung der Systeme und Datensätze beim Nutzer liegen.
Ein rein synchroner Aufruf via `self.target(*args, **kwargs)` ist völlig ausreichend.

### Quantoren-Orchestrierung
Für Existenz- und All-Quantoren muss während der `_arrange`-Phase erfasst werden, welche Art von Zustands-Deklarationen vorliegen. Diese werden über die pre- und post-Attribute deklariert, indem entweder einzelne World-State-Objekte, oder Listen von WorldState-Objekten definiert werden (`[WorldState]`). Die Frage, welche die `_arrange`-Phase beantworten soll, lautet: "Was genau liegt hier vor?"

Darauf basierend gilt es eine Orchestrierungs-Strategie für die Testläufe zu deduzieren. 
Die Details der Orchestrierungs-Strategien müssen als Hilfsfunktionen gestaltet werden. 
* Wenn eine WorldState-Liste im `pre`-Attribut vorliegt, benötigen wir eine Allquantor-Logik, welche für jeden WorldState im `pre`-Attribute einen eigenen Testlauf ausführt und einen Fehler wirft, wenn auch nur ein einziger Lauf nicht mit dem erwarteten `post`-Zustand übereinstimt.
* Wenn eine WorldState-Liste im `post`-Attribut vorliegt, benötigen wir eine Existenzquantor-Logik, welche den Fehler nur dann wirft, wenn kein einziger der erwarteten `post`-Zustände zutrifft.
* Wenn eine WorldState-Liste sowohl im `pre`-Attribut, als auch im `post`-Attribut vorliegt, dann gilt logischerweise beides: Für jedes Objekt in der WorldState-Liste vom pre-Attribut wird ein Testlauf in einer iterativen Schleife geführt, welche einen Fehler wirft, wenn auch nur ein einziger Lauf nicht mit einem der definierten Zustände im `post`-Attribut zutrifft.

---

<center>

![Error while trying to load the image](docs/.assets/cubie-small.png) 


---
## Weiterführende Dokumentation der Kernkomponenten

Um die interne Funktionsweise und die architektonischen Details der einzelnen Komponenten tiefgehender zu verstehen, existieren dedizierte Spezifikationen:
</center>



* **[EBT Orchestration Engine (DEV-GUIDE_2-1)](DEV-GUIDE_2-1_EBT-Class.md):** Details zur Auto-Inferenz, Quantoren-Auflösung ($\forall$ und $\exists$) sowie den Kaskadierungs-Mechanismen der Arenen.
* **[WorldState Deklarator (DEV-GUIDE_2-2)](DEV-GUIDE_2-2_WorldState-Class.md):** Spezifikation der Zustandsobjekte, der topologischen Dateisystem-Ebene (`fs`) und der kontextuellen Dualität zwischen Pre- und Post-Phasen.
* **[Arenen & Sandbox-Protokolle (DEV-GUIDE_2-3)](DEV-GUIDE_2-3_Arenas.md):** Spezifikation des Arena-Protokolls, der `PyVenv` / `TempFS` Klassen sowie des dynamischen Provisionings durch den `ArenaBuilder`.
* **[Multiprocessors (DEV-GUIDE_2-4)](DEV-GUIDE_2-4_Multiprocessors.md):**
Design des Multiprocessings und Handbuch zur Entwicklung und Integration eigener Multiprocessing-Verfahren.