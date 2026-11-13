<center>

# `Multiprocessors`

![Cubie](../.assets/cubie-logo-written.png)

Diese Entwicklerreferenz beschreibt Multiprozess-Ausführung und die zugehörigen Schnittstellen.

---

</center>

Das `multiprocessors`-Modul ist die Architektur-Ebene hinter der parallelen Skalierung von Cubie. Es entkoppelt die Auswertung konkreter EBT-Beispiele vollständig von den physischen Details der Prozess-Erstellung, Inter-Prozess-Kommunikation (IPC) und Serialisierung.

---

---

### Kern-Verantwortlichkeiten

* **Abstrakte Parallelisierung:** Verteilung von $N$ unabhängigen `pre`-Zuständen auf asynchrone System-Worker, ohne die Makro-Pipeline der `EBT`-Engine mit Threading- oder Subprocess-Logik zu belasten.
* **Auto-Routing (State Inspection):** Dynamische Analyse der übergebenen Zustände zur Laufzeit, um die Serialisierungs-Strategie zu wählen (z.B. Wechsel auf `cloudpickle`, sobald unpickelbare `lambda`-Funktionen entdeckt werden).
* **Dependency Injection (DI) Bereitstellung:** Öffnung der Ausführungsschicht durch Protokolle, sodass Entwickler das Standard-Verhalten durch eigene Backends (wie `Celery`, `Ray` oder `joblib`) personalisieren können.
* **Backend-Fallback:** Nur definierte Infrastrukturfehler erlauben einen Backendwechsel. Target- und Konfigurationsfehler propagieren ohne Wiederholung. Bei einem zulässigen Fallback kann die gesamte Aufgabenmenge erneut laufen; die Warnung benennt mögliche doppelte Seiteneffekte.

---

### Design und Pattern

Das Modul ist modular aufgebaut und nutzt klassische Entwurfsmuster um Flexibilität, Resilienz und Entkopplung zu fördern:

* **Strategy-Pattern & Chain of Responsibility:** Die Auswahl des richtigen Prozessors erfolgt über eine dynamische Kette von eigenständigen Objekten, die anhand ihrer Priorität und ihrer Eignung (`check_condition`) bewertet werden.
* **Finite-State-Machine (FSM) & Fallback:** Der Kern-Manager agiert als fehlertoleranter Zustandsautomat. Bei Abstürzen der Worker-Pools deaktiviert der Kontrollfluss das fehlerhafte Glied in der Kette, springt nahtlos auf den Startzustand zurück und evaluiert die verbleibenden Ausführungswege neu.
* **Object Composition (ContextManager-Mapper):** Die eigentlichen Executor-Pools (z. B. `ProcessPoolExecutor`) werden nicht vererbt, sondern in zustandslose Mapper-Objekte gewrappt, die als eigene ContextManager (`__enter__`, `__exit__`) fungieren. Das kapselt den Lebenszyklus (Teardown) der Worker ab.

---

## Haupt-Klassen

Die operative Ausführung ist in drei logische Instanzen unterteilt:

### Manager

Der `MultiprocessManager` ist das **Zentrum der Ausführung** und arbeitet intern als fehlertoleranter Zustandsautomat. Er wird in der `_validate_multiprocess`-Phase der `EBT`-Klasse aufgerufen und zirkuliert so lange durch vier feste Zustände, bis ein finales Ergebnis (`SUCCESS`) oder ein absoluter Fehlschlag (`FAIL`) erreicht wird:

1. **INITIAL:** Setzt Prozessor, Runner und Teilergebnis zurück. Die letzte Infrastruktur-Ausnahme bleibt für einen abschließenden Fehlerbericht erhalten.
2. **RESOLVE:** Beauftragt den `Resolver`, den am höchsten priorisierten und geeigneten Prozessor aus der Registry zu ermitteln.
3. **SETUP:** Instanziiert den `Runner` über den gewählten Prozessor.
4. **EXECUTE:** Führt die physische Multiprocessing-Last aus.

**Begrenzter Fallback:** Der Runner unterscheidet Fehler beim Poolaufbau, der Aufgabenbearbeitung und dem Aufräumen. Nur als Infrastrukturfehler klassifizierte Ausnahmen erreichen die Fallback-Behandlung des Managers. Dieser warnt, setzt die `priority` des Prozessors in der Registry auf `0` und kehrt nach `INITIAL` zurück. Gibt es kein geeignetes Ersatzbackend, endet der Lauf mit `RuntimeError("STATE-GUARD: All Processors failed")`; dessen Ursache ist die letzte Infrastruktur-Ausnahme. Fehler aus `check_condition()` propagieren direkt.

### Resolver

Der `MultiprocessResolver` ist eine **zustandslose Logik-Maschine**. Er erhält die Liste der verfügbaren Prozessoren und ermittelt den aktuell zuständigen Kandidaten:

1. **Sortierung:** Die Liste wird absteigend nach dem Attribut `priority` sortiert.
2. **Filterung:** Prozessoren mit einer Priorität von `0` (entweder manuell deaktiviert oder durch die FSM wegen Absturzes markiert) gelten als inaktiv und werden ignoriert.
3. **Prüfung:** Durch Aufruf der `check_condition(pre, post)`-Methode wird verifiziert, ob der Prozessor für die vorliegenden Daten geeignet ist. **State-Guard:** Findet der Resolver keinen fähigen Kandidaten, wirft er einen `RuntimeError`, um einen `FAIL`-State im Manager zu triggern und Endlosschleifen zu verhindern.

### Runner

Der `MultiprocessRunner` ist der **Arbeiter**. Er instanziiert den vom Resolver gelieferten `Mapper` und verwaltet dessen ContextManager-Lebenszyklus (`__enter__` / `__exit__`).

### Fehlerherkunft und Wiederholungssemantik

| Herkunft / Phase | Verhalten |
| --- | --- |
| Factory oder Context-Eintritt: `OSError` oder `BrokenProcessPool` | Infrastruktur-Fallback zulässig |
| `map()` oder Ergebnisiterator: `BrokenProcessPool` oder `pickle.PicklingError` außerhalb des Task-Aufrufs | Infrastruktur-Fallback zulässig |
| Ausnahme innerhalb des Tasks, einschließlich Target, Arena und Ergebnisprüfung | Ursprüngliche Ausnahme weitergeben, ohne Fallback; auch bei `OSError`, `PicklingError` oder `BrokenProcessPool` |
| Andere Backend-, Konfigurations- oder Hook-Fehler | Direkt weitergeben, ohne Fallback |
| Aufräumfehler nach abgeschlossener Verarbeitung | Direkt weitergeben, ohne Wiederholung |
| Aufräumfehler während eines anderen Fehlers | Primäre Ausnahme erhalten, Aufräumfehler als Notiz ergänzen; kein Fallback |

Ein interner, serialisierbarer Task-Wrapper markiert die Herkunft einer Ausnahme.
Der Elternprozess entpackt sie vor dem Context-Austritt; bei echten Workern bleibt
der vom Executor gelieferte entfernte Traceback als Ursache verfügbar. Kann eine
Task-Ausnahme nicht serialisiert oder rekonstruiert werden, wird ein beschreibender
`RuntimeError` mit ursprünglichem Typ und Meldung ohne Fallback ausgegeben.
Eigene Mapper müssen den übergebenen Task aufrufen und dessen Ausnahmen unverändert
transportieren. Sie dürfen sie weder verschlucken noch als Backendfehler ersetzen.
Der Runner unterdrückt Ausnahmen auch dann nicht, wenn `__exit__` einen wahren Wert liefert.

Bei einem zulässigen Fallback werden partielle Ergebnisse verworfen und **alle
Eingänge erneut ausgeführt**, sofern ein weiteres geeignetes Backend existiert.
Die Standard-Mapper warten beim Context-Austritt auf bereits laufende Aufgaben. Ein fehlendes
Ergebnis beweist nicht, dass der zugehörige Task noch nicht lief. Die Warnung nennt
deshalb vollständige Wiederholung und mögliche **doppelte Seiteneffekte** auch dann,
wenn noch kein Ergebnis empfangen wurde. Es gibt weder Rollback noch eine
Exactly-once-Garantie; Targets mit Datei-, Netzwerk- oder Datenbankeffekten müssen
Wiederholungen entsprechend vertragen. Das Workerlimit bleibt beim Wechsel erhalten.

Die Auswahl prüft weiterhin nur die Zustände heuristisch. Allgemeine `AttributeError`
oder `TypeError` werden auch bei vermuteten Serialisierungsproblemen nicht pauschal
zu Fallback-Signalen. Ein tatsächlich verlorener Worker gilt als Infrastrukturfehler;
der Manager kann nicht feststellen, ob ein Target den Prozess absichtlich beendet hat.

---

## Multiprocessor (Protokoll) und Implementierungen

### Multiprocessor (Protokoll)
Dieses Protokoll (definiert in `protocols.py`) ist der verbindliche Vertrag für alle Parallelisierungs-Strategien. Ein valider Prozessor benötigt:
* `priority: int`: Bestimmt die Rangfolge im Resolver.
* `@staticmethod check_condition(pre_states, post_states) -> bool`: Entscheidet, ob der Prozessor den aktuellen Datenfluss handhaben kann.
* `@staticmethod create_handler(n_tasks: int, *, max_workers: int | None = None) -> Mapper`: Liefert einen ContextManager mit `.map()` und berücksichtigt ein gesetztes Workerlimit. Der Manager reicht das Limit auch bei einem Backend-Fallback weiter. Ohne explizites Limit ruft der Runner die Factory nur mit `n_tasks` auf; bisherige eigene Prozessoren bleiben so nutzbar. Bei einem expliziten Limit müssen sie das Schlüsselwort unterstützen und die Grenze einhalten. Eine fehlende Unterstützung propagiert als `TypeError` ohne Fallback; das Limit wird nicht verworfen.

### PickleProcessor
Der **Fast-Path** der Cubie-Engine (Priority `1`). 
Er nutzt die native `multiprocessing`-Bibliothek und deren `ProcessPoolExecutor`. Da der Standard-Pickler keine dynamischen Speicheradressen serialisieren kann, gibt seine `check_condition` nur `True` zurück, wenn der interne `StateInspector` *keine* lokalen Closures oder `lambda`-Funktionen in den WorldStates findet. Der konkrete Aufwand hängt von Daten, Plattform und Aufgaben ab; ein maximaler Durchsatz ist nicht nachgewiesen.

### LokyProcessor
Der **Slow-Path** der Cubie-Engine (Priority `1`).
Er nutzt das externe `loky`-Backend (auf Basis von `cloudpickle`). Seine `check_condition` ist exklusiv zum `PickleProcessor` invertiert: Er meldet sich *nur* dann freiwillig, wenn der `StateInspector` unpickelbare Elemente (wie Lambdas für formallogische Prädikate) aufspürt. Er rettet den Testlauf durch tiefe Bytecode-Serialisierung, erzeugt aber durch den robusten Start-Kontext einen entsprechenden Overhead.

---

---

## Entwicklungs-Leitfaden: Multiprocessor DI 

Die Architektur ist strikt nach dem Open-Closed-Prinzip gestaltet. Um ein eigenes Backend (z. B. über `ThreadPoolExecutor` oder verteilte Cluster-Berechnungen wie `Ray`) einzubinden, müssen keine Framework-Klassen verändert werden. 

---

### Schritt 1: Den Mapper (ContextManager) definieren
Der Mapper kapselt die physische Interaktion mit dem Backend. Hier werden architektonische Herausforderungen wie Teardown und Chunking isoliert gelöst.

* **Lebenszyklus-Kapselung:** Durch das `__enter__` und `__exit__` Protokoll wird sichergestellt, dass externe Verbindungen oder Subprozesse (wie `pool.shutdown()`) auch bei Exceptions in der EBT-Pipeline abgeräumt werden.
* **Laufzeit-Heuristiken (Chunking):** `PickleMapper` und `LokyMapper` begrenzen die Workerzahl auf `min(os.cpu_count() or 1, n_tasks)` und gegebenenfalls `max_workers`. Die Task-Blöcke richten sich nach der effektiven Workerzahl: `chunksize = max(1, n_tasks // (n_worker * 4))`. Ein Pool benötigt mindestens eine Aufgabe.
* **Das Mapping-Interface:** Die `.map()`-Methode nimmt das auszuführende Target und die entpackten `WorldState`-Iterables entgegen und liefert die Ergebnisse an die EBT-Engine zurück.

Dieses Beispiel kapselt einen `ThreadPoolExecutor` als eigenen Context-Manager-Mapper:

```python session=custom_mp
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterable


class ThreadMapper:
    def __init__(self, n_tasks: int, max_workers: int | None = None):
        self.n_tasks = n_tasks
        self.max_workers = max_workers or min(4, max(1, n_tasks))
        self._executor: ThreadPoolExecutor | None = None

    def __enter__(self) -> "ThreadMapper":
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=True)

    def map(self, fn: Callable[..., Any], *iterables: Iterable[Any]) -> list[Any]:
        assert self._executor is not None
        return list(self._executor.map(fn, *iterables))
```

<details>
<summary>Ergebnis</summary>

```text

```
</details>

---

### Schritt 2: Den Prozessor (Hook) definieren

Der eigentliche Prozessor agiert primär als Filter oder Trigger (Hook) und als Factory für den Mapper. Die Methode `create_handler` reicht hierbei lediglich die Task-Anzahl sowie das optionale `max_workers`-Limit an die Mapper-Instanz weiter. Das eigentliche Routing durch die Responsibility Chain wird durch die Kombination aus Priorität und der `check_condition`-Funktion umgesetzt.

* **Der Hook (Spezifischer Trigger):** mit spezifischen `check_condition` (z.B. Scannen der `pre_states` nach einem bestimmten Datentyp oder einer spezifischen Arena), kann man Prozessoren bauen, die nur bei ganz bestimmten Testfällen eingreifen.
* **Priority-Chain** man kann die spezifischen Trigger breiter setzen und über die priority die Evaluation des Objekts in der Kette beeinflussen. Setzt man eine sehr hohe Priorität für einen Multiprocessor, überwiegt dieser in seiner Wertung für die Auswahl gegenüberen weniger hoch priorisierten Multiprocessors in der Registry, insofern beide check_condition-Prüfungen zutreffen.
* **Der Total-Override:** Gibt die `check_condition` immer `True` zurück, übernimmt dieser Prozessor die Priorität stets die Ausführung, insofern dessen priority-Wert am höchsten ist.

Die folgende Prozessor-Klasse bindet den Mapper über `priority`, `check_condition` und `create_handler` ein:

```python session=custom_mp
class ThreadProcessor:
    priority = 99  # Überschreibt Pickle (1) und Loky (1)

    @staticmethod
    def check_condition(pre_states: list, post_states: list) -> bool:
        return True

    @staticmethod
    def create_handler(n_tasks: int, *, max_workers: int | None = None) -> ThreadMapper:
        return ThreadMapper(n_tasks, max_workers=max_workers)
```

<details>
<summary>Ergebnis</summary>

```text

```
</details>

---

### Schritt 3: Dependency Injection (DI) bei der Ausführung

Die Injection erfolgt direkt im Konstruktor der `EBT`-Engine.

```python session=custom_mp
import qb_cubie as qb


def square(x: int) -> int:
    return x * x


my_proc = ThreadProcessor()
my_proc.priority = 150  # Mutability zur Laufzeit

result = qb.EBT(
    target=square,
    pre=[qb.WorldState(args=(3,)), qb.WorldState(args=(4,))],
    post=[qb.WorldState(returns=9), qb.WorldState(returns=16)],
    multiprocessing=True,
    multiprocessors=[my_proc],  # DI-Hook
).run()
print(result.evaluation)
```

<details>
<summary>Ergebnis</summary>

```text
True
```
</details>

**⚠️ Architektur-Disclaimer zum EBT-Standard (`MULTIPROCESSORS`):**
Wenn das Argument `multiprocessors=[...]` übergeben wird, nutzt die `EBT`-Klasse intern ein "Gentleman's Agreement" via `.extend()`. Das bedeutet, die injizierten Prozessoren werden *zusätzlich* zu den nativen Standards (`Pickle` und `Loky`) in die Hook-Registry geladen. Der Resolver wählt dann den besten Kandidaten anhand der Priorität.
Sollte ein absoluter Blackbox-Modus nötig sein, in dem die nativen Fallbacks physisch nicht existieren dürfen (z. B. für strenge Unit-Tests der DI-Logik), kann das Klassen-Attribut nach der Instanziierung der EBT-Klasse (z.B. als `engine`) einfach überschrieben werden: `engine.MULTIPROCESSORS = [MyCustomProcessor()]`, bevor der eigentliche Testlauf mit `engine.run()` gestartet wird.

---

---



---
## Betriebsgrenzen

Pickle und Loky begrenzen die Workerzahl je Lauf auf CPUs, Eingangszustände und das optionale `EBT(max_workers=...)`-Limit. Ohne erkennbare CPU-Zahl wird ein Worker verwendet. `max_workers=1` erhält die Ausführung im Kindprozess. Die Grenze gilt pro EBT-Instanz; pytest-xdist-Worker und Arena-Unterprozesse erhalten kein gemeinsames Ressourcenbudget. Für diese Kombinationen muss das Benutzerlimit entsprechend gewählt werden.

Fallback ist keine Exactly-once-Garantie: Die gesamte Aufgabenmenge kann erneut laufen, auch wenn zuvor einzelne Targets schon Seiteneffekte erzeugt haben. Die heuristische Backend-Auswahl garantiert weder Serialisierbarkeit aller Targets noch Ausführungsisolation. Siehe [Vertragssemantik](../GUIDE_Contract-Semantics.md).

---

---

<center>

![Error while trying to load the image](../.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](../GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
