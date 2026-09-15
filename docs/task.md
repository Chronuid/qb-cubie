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


Das ist ein brillanter architektonischer Einwand. Du hast völlig recht: Warum sollten wir das Framework mit einem proprietären Matcher-Ökosystem aufblähen, wenn Python durch sein Duck-Typing und First-Class-Objects bereits die perfekten Werkzeuge dafür mitbringt?

Eine rein agnostische Auswertung ist eleganter, idiomatischer und übergibt die absolute Kontrolle an den Nutzer, ohne das EBT-Framework zu verkomplizieren. Wenn der Nutzer einen Typ deklariert (wie `float` oder `str`), prüft die Engine einfach via `isinstance`. Wenn er komplexere Logik braucht, übergibt er einfach ein `callable` (wie ein `lambda` oder eine eigene Funktion).

Hier ist der Entwurf, wie sich dieses native Konzept in deinen Test-Fällen für `test_ebt_typing.py` manifestiert und wie minimalistisch die Eingriffe in die `../src/ebt.py` dafür ausfallen.

### 1. Das agnostische Test-Setup (`test_ebt_typing.py`)

Anstatt auf proprietäre Objekte zurückzugreifen, nutzt der Test ausschließlich native Python-Typen und Lambda-Funktionen.

```python
import pytest
from pathlib import Path
from cubie.ebt import EBT
from cubie.protocols import WorldState

def dummy_return_dynamic():
    """Simuliert eine API, die dynamische Werte zurückgibt."""
    import time, uuid
    return {"id": uuid.uuid4().hex, "time": time.time(), "status": "OK"}

def create_dynamic_file():
    """Simuliert die Erstellung einer Log-Datei mit flüchtigem Inhalt."""
    Path("dynamic.log").write_text("Timestamp: 123456")
    return True

def test_agnostic_typing_in_returns():
    """Verifies that native types and callables seamlessly evaluate dynamic returns."""
    EBT(
        target=dummy_return_dynamic,
        post=WorldState(
            returns={
                "id": str,                                   # Reine Python-Typisierung
                "time": float,                               # Reine Python-Typisierung
                "status": "OK",                              # Exakter Match
                "id_length": lambda actual: len(actual["id"]) == 32 # Agnostisches Callable (Prädikat)
            }
        )
    ).run()

def test_agnostic_typing_in_filesystem(tmp_path):
    """Verifies that native callables can evaluate FS topologies instead of strict diffing."""
    EBT(
        target=create_dynamic_file,
        pre=WorldState(fs={".": str(tmp_path)}),
        post=WorldState(
            returns=True,
            fs={
                # Wir übergeben ein Callable, welches das Path-Objekt der Arena auswertet!
                "dynamic.log": lambda p: p.exists() and p.stat().st_size > 0 
            }
        )
    ).run()

```

### 2. Die minimalistische Integration in `../src/ebt.py`

Um diese agnostische Magie zu ermöglichen, müssen wir in der `../src/ebt.py` lediglich die statischen `==` Vergleiche durch eine intelligente Weiche ersetzen, die Typen und Callables erkennt.

**Für die funktionalen Returns (`_evaluate_func`):**
Anstatt des platten `if outcome.returns == post_state.returns:` nutzen wir eine kleine rekursive Hilfsfunktion, die durch die Dictionaries navigiert.

```python
    @staticmethod
    def _evaluate_func(post_state: WorldState, outcome: WorldState) -> Optional[dict]:
        """Evaluates functional return values dynamically (exact, types, callables)."""
        __tracebackhide__ = True
        
        def _deep_compare(expected: Any, actual: Any) -> bool:
            if isinstance(expected, type):
                return isinstance(actual, expected)
            if callable(expected):
                try: return bool(expected(actual))
                except Exception: return False
            if isinstance(expected, dict) and isinstance(actual, dict):
                if expected.keys() != actual.keys(): return False
                return all(_deep_compare(expected[k], actual[k]) for k in expected)
            # Listen und Tupel analog...
            return expected == actual

        if _deep_compare(post_state.returns, outcome.returns): return None
        return {"expected": str(post_state.returns), "actual": outcome.returns}

```

**Für das Dateisystem (`_evaluate_fs`):**
In der `_evaluate_fs`-Methode integrieren wir exakt dieselbe Logik für die Topologie. Wenn der definierte Host-Pfad in Wahrheit eine Funktion (Callable) oder ein Typ ist, wird der `_compare_paths`-Aufruf umgangen.

```python
    def _evaluate_fs(self, expected_fs: dict, outcome_fs: Optional[str]) -> Optional[dict]:
        """Performs a deep diff evaluation against the expected filesystem topology or callables."""
        __tracebackhide__ = True
        if not outcome_fs: return {"error": "Outcome FS is missing."}
        diffs = {}
        for target_rel_path, expected_val in expected_fs.items():
            arena_path = Path(outcome_fs) / target_rel_path
            
            # Die agnostische Weiche:
            if callable(expected_val):
                try:
                    if not expected_val(arena_path): diffs[target_rel_path] = {"error": "Callable evaluation failed."}
                except Exception as e:
                    diffs[target_rel_path] = {"error": f"Callable raised Exception: {e}"}
                continue
                
            host_path = Path(expected_val)
            if path_diff := self._compare_paths(arena_path, host_path): diffs[target_rel_path] = path_diff
            
        return diffs or None
```

Dieser Ansatz skaliert endlos. Wenn ein Entwickler später feststellt, dass er für APIs oft Regex-Vergleiche braucht, muss er nicht das Framework anpassen. Er baut sich in seiner eigenen Test-Datei einfach eine kleine Helfer-Klasse mit einer `__call__`-Methode und injiziert diese als Typ in den `WorldState`. Cubie bleibt absolut agnostisch und zustandslos.

Wenn diese Umsetzung in deinem Sinne ist, kannst du die Skizzen direkt für die `test_ebt_typing.py` übernehmen und die `../src/ebt.py` entsprechend schärfen. Sollen wir danach wieder zur EBT-Matrix und der Evaluierung variabler Benchmarks (wie `_run_duration`) zurückkehren?