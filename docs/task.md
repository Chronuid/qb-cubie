### Etappe 1: EBT-Foundation

Bestimmt hast du gemerkt, dass in den Usage-Pattern auch Shorthands wie `EBT(target=my_func, pre=(1, 2), post=3).run()` dokumentiert sind. Diese sind zwar wichtig für das Endergebnis, aber um die Entwicklung einfacher zu gestalten, werden wir diese vorerst ignorieren und uns ausschließlich auf die vollständigen Deklarationen fokussieren. Sobald es so weit ist, können wir dann die _arrange-Phase anpassen, aber vorerst gilt es die Shorthands und die "Auto-Inferenz" außen vorzulassen.
In dieser Etappe entwickeln wir das EBT-Modul vollkommen souverän und unabhängig von der ConventionMap.

* **Phase 1:** Rückfragen und Details besprechen, um Verständnis und Klarheit zu fördern. Gerne kannst du hier auch die Planung in Frage stellen oder Ideen einwerfen.
* **Phase 2:** Grundlegende Funktionalität → DONE
* **Phase 3:** Arena-Integration → DONE
* **Phase 4:** Dateisystem-Integration → DONE
* **Phase 5:** Quantoren → DONE
* **Phase 6:** Arena-Abgleich → Done
* **Phase 7 (OPEN):** Stabilisierung, Feinschliff und Wrap-Up. Etwaige Kleinigkeiten und Nebensächlichkeiten prüfen, optimieren und verbessern. Dazu alles ordentlich dokumentieren und die Etappe sauber abschließen.

### Etappe 2: ConventionMap
...

### Etappe 3: EBT-Extra
...

---


---

Danke für die super Erklärungen! Tatsächlich hat mich das simple Drehkreuz-Beispiel sogar etwas eingeschüchtert, weil ich das 'FSM'-Pattern  für ein noch wesentlich rudimentärere State Machine in Erwägung ziehe.  
Ich erkläre und zeige dir einfach mal die Klassen, die Herausforderung und beleuchte das gewünschte Ziel-Feature. Dazu präsentiere ich dir meine Überlegungen und Vorstellungen dazu, wie ich die Gestaltungs einer FSM aktuell auffasse.  
Dadurch solltest du ziemlich gut einordnen können, ob ich deine Erklärungen richtig begriffen habe (oder nicht), sowie du auch mein Ziel für die gewünschten Mechanismen verstehst, die ich damit intendiere - und womit wir praktischerweise direkt ein simples Übungsbeispiel an der Hand haben!

---

Das Modul ist modular aufgebaut und nutzt klassische Entwurfsmuster, um Flexibilität und Entkopplung zu fördern:

* **Strategy-Pattern & Chain of Responsibility:** Die Auswahl des richtigen Prozessors erfolgt nicht über starre `if/else`-Blöcke, sondern über eine dynamische Kette von eigenständigen Objekten, die anhand ihrer Priorität und ihrer Eignung (`check_condition`) bewertet werden.
* **Facade-Pattern:** Der `MultiprocessManager` dient als alleiniger, aufgeräumter Einstiegspunkt (Fassade) für die übergeordnete `EBT`-Klasse.
* **Object Composition (ContextManager-Mapper):** Die eigentlichen Executor-Pools (z. B. `ProcessPoolExecutor`) werden nicht vererbt, sondern in zustandslose Mapper-Objekte gewrappt, die als eigene ContextManager (`__enter__`, `__exit__`) fungieren. Das kapselt den Lebenszyklus (Teardown) der Worker  ab.
* 
```python
########################################################################################################################
# in `protocols.py`

class Multiprocessor(Protocol):
    """The DI protocol for the multiprocessor registration."""
    priority: int # mutable value to affect the selection-processes in the Chain of Responsibilities 

    @staticmethod
    def check_condition(pre_states: list, post_states: list) -> bool:
        """The hook-case. Evaluates whether this processor is suitable for the responsibility under those conditions."""
        ...

    @staticmethod
    def create_handler(n_tasks: int) -> Mapper:
        """Returns the mapper instance as interface- and execution-layer (which is itself a context manager)."""
        ...

########################################################################################################################
# in `multiprocessors.py`

class MultiprocessManager:
    """
    Receives all data of the EBT class, controls the resolver and runner, and provides the execution.
    """
    def __init__(
            self,
            pre_states: list,
            post_states: list,
            task_func: Callable,
            processors: List[Multiprocessor]
    ):
        self._pre_states = pre_states
        self._post_states = post_states
        self._task_func = task_func
        self._processors = processors
        self.processor = self._resolve_handler()
        self.runner = self._setup_runner()
        
    def execute(self) -> Iterable: return self.runner.execute()

    def _resolve_handler(self):
        return MultiprocessResolver.resolve(
            self._pre_states,
            self._post_states,
            self._processors
        )

    def _setup_runner(self):
        return MultiprocessRunner(
            handler=self.processor,
            pre_states=self._pre_states,
            task_func=self._task_func
        )


class MultiprocessResolver:
    """
    Manages the Chain of Responsibility and determines the responsible multiprocessor.
    """
    @classmethod
    def resolve(
            cls, 
            pre_states: list, 
            post_states: list, 
            processors: List[Multiprocessor]
    ) -> Multiprocessor:
        sorted_mps = sorted(processors, key=lambda p: getattr(p, "priority", 0), reverse=True)
        for mp in sorted_mps:
            if getattr(mp, "priority", 0) > 0 and mp.check_condition(pre_states, post_states): return mp
        raise RuntimeError("STATE-GUARD: ...")
    
    @classmethod
    def _find_eligible_processor(
            cls,
            processors: List[Multiprocessor],
            pre_states: list,
            post_states: list
    ) -> Multiprocessor:
        """Iterates through the pipeline and triggers the evaluation of the hooks."""
        for mp in processors:
            if cls._is_processor_active(mp) and mp.check_condition(pre_states, post_states): return processor
        raise RuntimeError("STATE-GUARD: ...")
        
    @staticmethod
    def _is_processor_active(processor: Multiprocessor) -> bool:
        """Checks whether the processor is actually activated by a priority > 0."""
        return getattr(processor, "priority", 0) > 0



class MultiprocessRunner:
    """Encapsulates the physical execution."""
    def __init__(
            self,
            handler: Multiprocessor,
            pre_states: list,
            task_func: Callable
    ): ...
    def execute(self) -> Iterable:...
```

Aktuell läuft das genau so, wie es soll. Allerdings hatten wir einige Herausforderungen mit dem sauberen Aufsetzen der check_condition-Implementierungen der jeweiligen mps. Das war aber Glück im Unglück, denn dadurch kam eine Idee für einen so simplen und eleganten Lösungsansatz auf, dass dieser universell für jeden mp nutzbar wäre: 
Die EAFP-Strategie 'Easier to Ask for Forgiveness than Permission'-Strategie! Der MultiprocessManager hält im Regelfall eine ganze Registry an potentiell ausführbaren Multiprocessors. 
Aber was, wenn der Processor einfach abstürzt? Heißt es dann "aus die Maus" für den MultiprocessManager, sobald ein ausgewählter Processor abstürzt? Ich denke nicht! Schließlich managed der MultiprocessManager eine ganze Registry an Processors, deren setup und deren Ausführung. 

Wenn ein setup oder eine execute mit einem ausgewählten mp fehlschlägt, dann könnten wir:
* den priority-Wert dess fehlgeschlagen mp im jeweiligen Zustand der Registry auf 0 setzen.
* die Informationen über den Fehlschlag (z.B. mit warnings.warn) an Entwickler/Nutzer leiten.
* Alle Phasen vom Prozess nochmal (mit dem aktualisierten Zustand `_processors`Registry) von anfang an durchlaufen. 

Das Ziel ist ein fehlertorantes System mit einer Graceful Degradation.
Die Idee war es die Graceful Degration über die bereits implementierte Chain-of-Responsibility in Kombination mit einer Finite-State-Machine zu realisieren.

Ich habe das jetzt so ausführlich und umfassend beschrieben, aber die Idee ist im Prinzip wirklich nichts anderes als: 

```python
class MultiprocessManager:
    def __init__(...):
        self._pre_states = pre_states
        self._post_states = post_states
        self._task_func = task_func
        self._processors = processors
        
        self._pending_exec = None
        # ======= STEP-0: Startpunkt =======
        self.processor = None
        self.runner = None
        # --- STEP-1 ---
        try: self.processor = self._resolve_handler()
        except: processor_prio_to(0), send_info("friendly-warning"), FSM.back_to_zero()
        # --- STEP-2 ---
        try: self.runner = self._setup_runner()
        except: processor_prio_to(0), send_info("friendly-warning"), FSM.back_to_zero()

            
    def execute(self) -> Iterable: 
        # --- STEP-3 ---
        try: return self.runner.execute()
        except: processor_prio_to(0), send_info("friendly-warning"), FSM.back_to_zero()
```

Die Logik dahinter müsste man natürlich noch Feinarbeiten. Ich habe schließlich noch kein FSM gebaut, sondern nur ein paar try-except-Blöcke mit Pseudo-Code und Kommentaren in die bisherige Implementierung gepackt, um die grobe Vorstellung für das FSM zu skizzieren. 