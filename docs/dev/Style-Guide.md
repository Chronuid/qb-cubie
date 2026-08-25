# Styleguide

Um einen einheitlichen, testbaren und pflegbaren Code im gesamten Projekt zu haben, gelten folgende Styleguide-Richtlinien: 

### Kurze, prägnante und eindeutige Methoden- und Variablen-Namen
Bezeichner für Funktionen und Variablen sind auf das Wesentliche zu reduzieren. Sie bestehen idealerweise aus einem einzelnen, aussagekräftigen Wort. Der tiefere Bedeutungskontext ergibt sich implizit aus der umgebenden Klasse oder dem Modul. Zu lange, mit Underscores verkettete Beschreibungen (Bandwurmnamen) sind zu vermeiden. Zusätzlicher Kontext gehört in den Docstring oder in Inline-Kommentare.

### Docstring-Beschreibungen als Einzeiler
Docstrings bestehen aus exakt einem Satz und erklären ausschließlich das Was, niemals das Wie. Die korrekte Bedienung einer Funktion muss zwingend aus ihrem Interface und ihrer Signatur hervorgehen, anstatt im Docstring erklärt zu werden. Lässt sich eine Funktion nicht in einem einzigen, simplen Satz beschreiben, ist das ein starkes Indiz für eine zu hohe Komplexität. In diesem Fall ist die Funktion in eine Kompositionsfunktion und kleinere Hilfsfunktionen zu zerlegen.
 
### Maximal 7-12 Zeilen pro Funktion
Funktionskörper dürfen maximal 7 bis 12 Zeilen lang sein (Interfaces und Docstrings werden nicht mitgezählt). Um dieses Limit zu halten, müssen interne Logikzweige (Schleifen, komplexe Bedingungen) zwingend als eigenständige Blöcke in separate Hilfsfunktionen ausgelagert werden. Die Hauptfunktion fungiert anschließend als reine Kompositionsfunktion, die diese Blöcke lediglich aufruft und orchestriert.

### Maximal 300 Zeilen pro Modul
Die aktuelle Code-Basis ist modular aufgebaut und wächst organisch. Das harte Limit für Dateigrößen liegt bei 300 Zeilen. Wird dieses Limit erreicht, diktiert die Logik des Codes die Aufspaltung in neue logische Sub-Module.

### Narrative Programming (Top-Down-Lesbarkeit)
Beim Lesen vom Code sollte man schnell das Wichtigste erfassen und sich leicht zurechtfinden können. Die Haupt-Funktionen einer Klasse (Services) stehen immer ganz oben in der Datei oder Klasse und agieren als Kompositionsfunktionen (das "Inhaltsverzeichnis", um den Code wie eine logische Geschichte von oben nach unten zu lesen) von Hilfs-Funktionen. 
Die detaillierten Hilfsfunktionen folgen erst darunter, sodass der Leser sich von der groben Abstraktionsebene stufenlos in die technischen Details hinabarbeiten kann.

---

## Statische und dynamische Konventionen
In Python gilt beim Thema Sichtbarkeit und Veränderbarkeit oft das Prinzip der „consenting adults“ (einverständlichen Erwachsenen). Das bedeutet: Python zwingt dich fast nie durch feste Compiler-Regeln (wie `private` oder `const` in Java oder C++), Dinge nicht zu tun. Stattdessen verlässt sich die Sprache massiv auf **Namenskonventionen** und (mittlerweile) **Type Hints**, um die Absicht des Codes zu kommunizieren.

Hier ist die Aufschlüsselung, wie deine Definitionen in der Python-Welt typischerweise umgesetzt werden:

### 1. "Statisch" (Fest, Konfiguration, Immutable)

Wenn ein Wert fest sein soll oder als globale/klassenweite Konfiguration dient, nutzt man folgende Konventionen:

* **Großschreibung (UPPER_CASE):** Laut dem Python-Standard PEP 8 werden Konstanten komplett groß und mit Unterstrichen geschrieben. Das signalisiert jedem Entwickler: *„Fass das nicht an, das ist eine feste Konfiguration.“*
* **Der `Final` Type Hint:** Seit Python 3.8 kannst du Konstanten explizit als unveränderlich markieren. Das hindert Python zwar zur Laufzeit nicht daran, den Wert zu ändern, aber dein Linter (wie mypy oder Pyright) wird meckern.
* **Klassenattribute:** Variablen, die direkt in der Klasse (außerhalb von `__init__`) definiert werden. Sie teilen sich ihren Wert über alle Instanzen hinweg.
* **Frozen Dataclasses:** Wenn du ein ganzes Konfigurationsobjekt hast, das nach der Erstellung "immutable" (unveränderlich) sein soll, nutzt man heute oft den `@dataclass(frozen=True)` Dekorator.

### 2. "Dynamisch" (Wandelbar, Zustand, Mutable)

Wenn es um den laufenden Zustand eines Objekts geht, der sich durch Methodenaufrufe ändert, gelten diese Regeln:

* **Instanzattribute (`self.variable`):** Zustand wird immer in der `__init__`-Methode an `self` gebunden. Diese Variablen gehören nur dieser einen speziellen Instanz.
* **Der "Protected" Unterstrich (`_variable`):** Wenn ein dynamischer Zustand nur für den internen Gebrauch der Klasse (und ihrer Subklassen) gedacht ist, stellst du einen einfachen Unterstrich voran. Das ist ein reines Gentlemen's Agreement: *„Du kannst diesen Wert von außen ändern, aber wenn dann etwas kaputtgeht, ist es dein Problem.“*
* **Properties (`@property`):** Wenn ein dynamischer Wert beim Lesen oder Schreiben eine bestimmte Logik durchlaufen muss (z. B. Validierung), machst du ihn nicht direkt zugänglich. Du nutzt stattdessen den `@property`-Dekorator, um den Zugriff wie eine normale Variable aussehen zu lassen, obwohl im Hintergrund eine Methode läuft.

### **Zusammenfassend:**
Nutze `GROSSBUCHSTABEN` und `typing.Final` für Dinge, die du als "statisch" betrachtest. Nutze `self._variablenname` für internen wandelbaren Zustand und kontrolliere den Zugriff von außen, wenn nötig, über `@property`.

---

### "State-Guard Pattern" (Statische Typensicherheit in Pipelines)

* **Der Kontext:** In Klassen mit strikter Pipeline-Abarbeitung werden Instanzvariablen in der `__init__` oft mit `None` vorbelegt (`Optional[...]`), da ihr echter Zustand erst in einer späteren Phase berechnet wird.
* **Das Problem:** Statische Typ-Prüfer (Linter) meckern in nachgelagerten Methoden, weil sie nicht garantieren können, dass vorherige Methoden bereits aufgerufen wurden.
* **Die Regel / Erkenntnis:** Anstatt Typisierungen aufzuweichen oder überall mit `assert` zu pfuschen, empfiehlt sich die Nutzung expliziter **State-Guards** am Methoden-Anfang (z.B. `if self._root is None: raise RuntimeError(...)`).
* **Der Mehrwert:** Es befriedigt nicht nur den Linter restlos, sondern dient gleichzeitig als harter Laufzeitschutz gegen unvollständige Pipelines (Connascence of Execution), in welcher man Erklärungen formulieren kann, welche definieren was an jenen Stellen für einen sauberen Lauf erwartet wird.