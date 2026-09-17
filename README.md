<center>

# `Cubie: Quality-Bench`
![Alternativtext](docs/assets/cubie-banner.png "Error while trying to load the image")

**Cubie ist ein Framework für strukturierte Qualitätssicherung.**  
*Es behandelt Code nicht als etwas, das geschrieben wird, sondern als etwas, das im unendlichen Suchraum aller Möglichkeiten ($\Sigma^*$) gefunden wird. Cubie liefert die Werkzeuge, um diesen Lösungsraum durch explizite Code-Verträge und orthogonale Datenpunkte so präzise abzustecken, dass du deine gesuchten Funktionen finden kannst!*
</center>

---

## 🚀 Quickstart

Installiere das Framework via pip:

```bash
uv pip install cubie
```

In deinem Code nutzt du das etablierte, zweistellige Shorthand für maximalen Flow ohne Boilerplate:

```python
import cubie as qb
from my_module import calculate_tax

# Ein simpler EBT-Vertrag
def test_01(): qb.EBT(target=calculate_tax, pre=(100, 19), post=119).run()

```

---

## 🧠 Core Paradigms

Cubie basiert auf fundamentaler Prädikatenlogik. Das Spektrum der Qualitätssicherung teilt sich in zwei essenzielle Säulen auf: **Example-Based Testing (EBT)** und **Review-Based Testing (RBT)**.

### 1. Example-Based Testing (EBT)

EBT ist das unbestechliche Fundament zur Definition deterministischer Realitäten ("Golden Masters"). Es basiert auf dem klassischen Hoare-Tripel $\{P\}S\{Q\}$. Die Zustände vor der Ausführung ($P$) und danach ($Q$) werden als passive `WorldState`-Objekte deklariert.

**In-Memory API (Shorthands)**
Für reine Funktionen ohne Seiteneffekte verzichtet Cubie auf Boilerplate. Primitive Datentypen, Tupel und Dictionaries werden automatisch als `args` oder `kwargs` inferiert.

```python
def test_math(): qb.EBT(target=my_func, pre=(1, 2), post=3).run()
def test_dict(): qb.EBT(target=my_func, pre={"x": 1, "y": 2}, post=3).run()

```

**Mengen-Mappings (Quantoren)**
Cubie nutzt Python-Listen in den Zustands-Deklarationen, um formallogische Quantoren aufzulösen und Lösungsräume abzustecken:
* **Der beschränkte Allquantor $\forall$ (N:1-Mapping):** Mehrere chaotische Eingangszustände werden auf exakt denselben Zielzustand überführt.
* **Der beschränkte Existenzquantor $\exists$ (1:N-Mapping):** Ein diskreter Input mappt auf eine erlaubte Zielmenge. Der Test besteht, sobald ein Match vorliegt.



```python
# Allquantor: Alle definierten Eingänge MÜSSEN im selben Zielzustand enden.
def test_forall():
    qb.EBT(
        target=normalize_text,
        pre=[
            WorldState(args=" TEXT "), 
            WorldState(args="text_"), 
            WorldState(args="TeXt")
        ],
        post=WorldState(returns="text")
    ).run()

# Existenzquantor: Ein fixer Eingang MUSS in mindestens einem der erlaubten Zielzustände enden.
def test_exists():
    qb.EBT(
        target=roll_dice,
        pre=WorldState(args=(1, 6)),
        post=[
            WorldState(returns=1), 
            WorldState(returns=2),
            WorldState(returns=3), 
            WorldState(returns=4),
            WorldState(returns=5), 
            WorldState(returns=6)
        ]
    ).run()

```

**Dynamic Typing & Prädikate (Agnostic Typing)**
In realen Systemen sind Rückgabewerte oft volatil (z. B. Zeitstempel, dynamische Payloads). Anstatt einer starren Werte-Gleichheit (`==`) iteriert die Engine rekursiv und akzeptiert native Typen, Unions, `re.Pattern` oder zustandslose Callables zur semantischen Validierung.

```python
import re
from typing import Any, Union

def test_dynamic_payload():
    qb.EBT(
        target=my_api_client,
        post=WorldState(
            returns={
                "task_id": re.compile(r"^REQ-\d{4}$"),    # Pattern Matching
                "duration": float,                        # Native Typ-Prüfung
                "metadata": Any,                          # Wildcard (Existenz reicht)
                "next_page": Union[str, None],            # Optionale Typen (str | None)
                "status": lambda x: x in ["OK", "WARN"]   # Callable als Prädikat
            }
        )
    ).run()

```

**Filesystem & Arena API**
Trennt funktionale Inputs strikt von topologischen Dateisystem-Zuständen ab und isoliert die Ausführung in deterministischen Arenen (wie `TempFS` oder vollständigen virtuellen Umgebungen).

```python
def test_cleaner(): 
    qb.EBT(
        target="cleaner.py:my_func",
        pre=WorldState(
            args=["kalkuel.md"], 
            fs={"fixtures/pre/kalkuel.md"}
        ),
        post=WorldState(
            returns="Erfolgreich bereinigt", 
            fs={"fixtures/post/kalkuel.md"}
        )
    ).run()

```

### 2. Review-Based Testing (RBT)

RBT fungiert als qualitative Brücke zwischen dem unendlichen Suchraum und dem automatisierten Testsystem. Es deckt das Bootstrapping und subjektive Anforderungen ab (UI-Stil, Security-Audits), die sich harten mathematischen Assertions entziehen.

Der Test-Lebenszyklus friert die Ausführung ein und blockiert synchron. Die Verifikation wird an einen injizierten Reviewer delegiert:

* **Human-in-the-Loop:** Ein menschlicher Tester verifiziert den Zustand direkt am Terminal oder über eine GUI.
* **LLM-Agents:** Ein vollautomatisierter KI-Agent trifft die binäre Entscheidung (passed: y/n) und reichert das `ReviewData`-Objekt mit strukturierten Berichten an.



```python
qb.RBT(
    target="auth_module.py",
    check="Wird das Passwort niemals im Klartext geloggt?"
).run()

```

---

## 📚 Dokumentation & Guides

Um die internen Mechanismen und komplexen Patterns tiefgehend zu verstehen, konsultiere die dedizierten Developer-Guides:

* **[EBT Usage-Patterns](docs/GUIDE_EBT-Usage-Pattern.md):** Ausführliche Beispiele für $\forall$- und $\exists$-Mappings, Dictionary-Patterns, Agnostic Typing und Umgebungs-Mutationen.
* **[EBT Orchestration Engine](docs/dev/example-based-testing/DEV-GUIDE_2-1_EBT-Class.md):** Architektur der Makro-/Mikro-Pipelines, Shorthand-Inferenz und das dynamische Evaluierungs-Routing.