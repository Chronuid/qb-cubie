<center>

# `Multiprocessors` 

![Alternativtext](docs/assets/cubie-logo-written.png "Error while trying to load the image") 

Das `multiprocessors`-Modul ist die Architektur-Ebene hinter der parallelen Skalierung von Cubie. Es entkoppelt die formallogische Auswertung (EBT) vollständig von den physischen Details der Prozess-Erstellung, Inter-Prozess-Kommunikation (IPC) und Serialisierung.
</center>

### Kern-Verantwortlichkeiten 

* **Abstrakte Parallelisierung:** Verteilung von $N$ unabhängigen `pre`-Zuständen auf asynchrone System-Worker, ohne die Makro-Pipeline der `EBT`-Engine mit Threading- oder Subprocess-Logik zu belasten.
* **Auto-Routing (State Inspection):** Dynamische Analyse der übergebenen Zustände zur Laufzeit, um die Serialisierungs-Strategie zu wählen (z.B. Wechsel auf `cloudpickle`, sobald unpickelbare `lambda`-Funktionen entdeckt werden).
* **Dependency Injection (DI) Bereitstellung:** Öffnung der Ausführungsschicht durch Protokolle, sodass Entwickler das Standard-Verhalten durch eigene Backends (wie `Celery`, `Ray` oder `joblib`) personalisieren können.


### Design und Pattern

Das Modul ist modular aufgebaut und nutzt klassische Entwurfsmuster, um Flexibilität und Entkopplung zu fördern:

* **Strategy-Pattern & Chain of Responsibility:** Die Auswahl des richtigen Prozessors erfolgt nicht über starre `if/else`-Blöcke, sondern über eine dynamische Kette von eigenständigen Objekten, die anhand ihrer Priorität und ihrer Eignung (`check_condition`) bewertet werden.
* **Facade-Pattern:** Der `MultiprocessManager` dient als alleiniger, aufgeräumter Einstiegspunkt (Fassade) für die übergeordnete `EBT`-Klasse.
* **Object Composition (ContextManager-Mapper):** Die eigentlichen Executor-Pools (z. B. `ProcessPoolExecutor`) werden nicht vererbt, sondern in zustandslose Mapper-Objekte gewrappt, die als eigene ContextManager (`__enter__`, `__exit__`) fungieren. Das kapselt den Lebenszyklus (Teardown) der Worker  ab.

---

## Haupt-Klassen

Die operative Ausführung ist in drei logische Instanzen unterteilt:

### Manager
Der `MultiprocessManager` ist die **Fassade** des Moduls. Er wird in der `_validate_multiprocess`-Phase der `EBT`-Klasse aufgerufen und nimmt alle erforderlichen Daten (Zustände, Target-Funktion, Registry-Liste) entgegen. Er orchestriert den internen Ablauf, indem er zuerst den `Resolver` beauftragt und anschließend den Sieger-Prozessor an den `Runner` zur finalen Ausführung übergibt.

### Resolver
Der `MultiprocessResolver` ist eine **zustandslose Logik-Maschine**. Er erhält die Liste der verfügbaren Prozessoren und ermittelt den zuständigen Kandidaten:
1. **Sortierung:** Die Liste wird absteigend nach dem Attribut `priority` sortiert.
2. **Filterung:** Prozessoren mit einer Priorität von `0` gelten als deaktiviert und werden ignoriert.
3. **Prüfung:** Durch Aufruf der `check_condition(pre, post)`-Methode wird verifiziert, ob der Prozessor für die vorliegenden Daten geeignet ist. Der erste Prozessor, der `True` liefert, gewinnt.
4. **State-Guard:** Findet der Resolver keinen fähigen Kandidaten, wirft er einen `RuntimeError`, um stille Systemausfälle zu verhindern.

### Runner
Der `MultiprocessRunner` ist der **Arbeiter**. Er instanziiert den vom Resolver gelieferten `Mapper` über das ContextManager-Protokoll (`with ... as mapper:`) und delegiert die Target-Ausführung an ihn.

---

## Multiprocessor (Protokoll) und Implementierungen

### Multiprocessor (Protokoll)
Dieses Protokoll (definiert in `protocols.py`) ist der verbindliche Vertrag für alle Parallelisierungs-Strategien. Ein valider Prozessor benötigt:
* `priority: int`: Bestimmt die Rangfolge im Resolver.
* `@staticmethod check_condition(pre_states, post_states) -> bool`: Entscheidet, ob der Prozessor den aktuellen Datenfluss handhaben kann.
* `@staticmethod create_handler(n_tasks: int) -> Mapper`: Liefert ein Objekt zurück, das das `ContextManager`-Protokoll erfüllt und eine `.map()` Methode besitzt. Hier greifen auch Laufzeit-Heuristiken, wie etwa das dynamische Berechnen der optimalen `chunksize` basierend auf `os.cpu_count()` und der Menge der Tasks.

### PickleProcessor
Der **Fast-Path** der Cubie-Engine (Priority `1`). 
Er nutzt die native `multiprocessing`-Bibliothek und deren `ProcessPoolExecutor`. Da der Standard-Pickler keine dynamischen Speicheradressen serialisieren kann, gibt seine `check_condition` nur `True` zurück, wenn der interne `StateInspector` *keine* lokalen Closures oder `lambda`-Funktionen in den WorldStates findet. Er liefert maximalen Durchsatz bei minimalem RAM-Overhead.

### LokyProcessor
Der **Slow-Path** der Cubie-Engine (Priority `1`).
Er nutzt das externe `loky`-Backend (auf Basis von `cloudpickle`). Seine `check_condition` ist exklusiv zum `PickleProcessor` invertiert: Er meldet sich *nur* dann freiwillig, wenn der `StateInspector` unpickelbare Elemente (wie Lambdas für formallogische Prädikate) aufspürt. Er rettet den Testlauf durch tiefe Bytecode-Serialisierung, erzeugt aber durch den robusten Start-Kontext einen entsprechenden Overhead.

---

---

## Entwicklungs-Leitfaden: Multiprocessor DI 

Die Architektur ist strikt nach dem Open-Closed-Prinzip gestaltet. Um ein eigenes Backend (z. B. für verteilte Cluster-Berechnungen via `Ray`) einzubinden, müssen keine Framework-Klassen verändert werden. 

---

### Schritt 1: Den Mapper (ContextManager) definieren
Der Mapper kapselt die physische Interaktion mit dem Backend. Hier werden architektonische Herausforderungen wie Teardown und Chunking isoliert gelöst.

* **Lebenszyklus-Kapselung:** Durch das `__enter__` und `__exit__` Protokoll wird sichergestellt, dass externe Verbindungen oder Subprozesse (wie `pool.shutdown()`) auch bei Exceptions in der EBT-Pipeline abgeräumt werden.
* **Laufzeit-Heuristiken (Chunking):** Der Mapper erhält bei Instanziierung `n_tasks`. Dies ermöglicht es ihm, intelligente Heuristiken anzuwenden. Beispielsweise berechnen `PickleMapper` und `LokyMapper` die Task-Blöcke (`chunksize = max(1, n_tasks // (os.cpu_count() * 4))`), um den IPC-Overhead durch chunking zu reduzieren.
* **Das Mapping-Interface:** Die `.map()`-Methode nimmt das auszuführende Target und die entpackten `WorldState`-Iterables entgegen und liefert die Ergebnisse an die EBT-Engine zurück.

```python
from typing import Callable, Iterable, Any

class RayMapper:
    def __init__(self, n_tasks: int):
        self.n_tasks = n_tasks
        
    def __enter__(self) -> 'RayMapper':
        import ray
        ray.init(ignore_reinit_error=True) # Aufbau des Backends
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        import ray
        ray.shutdown() # Garantiertes Teardown
        
    def map(self, fn: Callable, *iterables: Iterable) -> Iterable[Any]:
        import ray
        # Ray benötigt kein iteratives Chunking, es nutzt Remote-Graphen
        remote_fn = ray.remote(fn)
        futures = [remote_fn.remote(*args) for args in zip(*iterables)]
        return ray.get(futures)

```

---

### Schritt 2: Den Prozessor (Hook) definieren

Der eigentliche Prozessor agiert primär als Filter oder Trigger (Hook) und als Factory für den Mapper. Die Methode `create_handler` reicht hierbei lediglich die Task-Anzahl an die Mapper-Instanz weiter. Das eigentliche Routing durch die Responsibility Chain wird durch die Kombination aus Priorität und der `check_condition`-Funktion umgesetzt.

* **Der Hook (Spezifischer Trigger):** mit spezifischen `check_condition` (z.B. Scannen der `pre_states` nach einem bestimmten Datentyp oder einer spezifischen Arena), kann man Prozessoren bauen, die nur bei ganz bestimmten Testfällen eingreifen.
* **Priority-Chain** man kann die spezifischen Trigger breiter setzen und über die priority die Evaluation des Objekts in der Kette beeinflussen. Setzt man eine sehr hohe Priorität für einen Multiprocessor, überwiegt dieser in seiner Wertung für die Auswahl gegenüberen einem weniger hoch priorisierten Multiprocessors in der Registry, insofern beide check_condition-Prüfungen zutreffen.
* **Der Total-Override:** Gibt die `check_condition` immer `True` zurück, übernimmt dieser Prozessor die Priorität stets die Ausführung, insofern dessen priority-Wert am höchsten ist.

```python
class RayProcessor:
    priority = 99  # Überschreibt Pickle (1) und Loky (1)
    
    @staticmethod
    def check_condition(pre_states: list, post_states: list) -> bool:
        # Ein Total-Override: Ray soll in diesem Projekt IMMER greifen
        return True  
        
    @staticmethod
    def create_handler(n_tasks: int) -> RayMapper:
        return RayMapper(n_tasks)

```

---

### Schritt 3: Dependency Injection (DI) bei der Ausführung

Die Injection erfolgt direkt im Konstruktor der `EBT`-Engine.

```python
import cubie as qb

my_ray_proc = RayProcessor()
my_ray_proc.priority = 150 # Mutability zur Laufzeit

qb.EBT(
    target=my_heavy_function,
    pre=[...],
    post=[...],
    multiprocessing=True,
    multiprocessors=[my_ray_proc] # DI-Hook
).run()

```

**⚠️ Architektur-Disclaimer zum EBT-Standard (`MULTIPROCESSORS`):**
Wenn das Argument `multiprocessors=[...]` übergeben wird, nutzt die `EBT`-Klasse intern ein "Gentleman's Agreement" via `.extend()`. Das bedeutet, die injizierten Prozessoren werden *zusätzlich* zu den nativen Standards (`Pickle` und `Loky`) in die Hook-Registry geladen. Der Resolver wählt dann den besten Kandidaten anhand der Priorität.
Sollte ein absoluter Blackbox-Modus nötig sein, in dem die nativen Fallbacks physisch nicht existieren dürfen (z. B. für strenge Unit-Tests der DI-Logik), kann das Klassen-Attribut nach der Instanziierung der EBT-Klasse (z.B. als `engine`) einfach überschrieben werden: `engine.MULTIPROCESSORS = [MyCustomProcessor()]`, bevor der eigentliche Testlauf mit `engine.run()` gestartet wird.

---

<center>

![Alternativtext](docs/assets/cubie-small.png "Error while trying to load the image") 

</center>

---