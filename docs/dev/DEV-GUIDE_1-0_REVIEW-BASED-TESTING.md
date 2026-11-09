# Review-Based-Testing (RBT)

Das Review-Based-Testing nimmt innerhalb des Cubie-Frameworks eine besondere Stellung ein. Während andere Test-Typen deterministische oder formallogische Grenzen abstecken, fungiert das RBT als Brücke zwischen der Unendlichkeit des Sigma-Sterns und dem harten, automatisierten Test-System.

Es ist das ideale Werkzeug für das Bootstrapping von Projekten. Bevor komplexe, automatisierte Assertions geschrieben werden, lässt sich eine Anforderung einfach als sprachliche Direktive formulieren. RBT ist konzeptionell die Schnittmenge aus *allen Testverfahren* (Any) und dem jeweiligen Prüfverfahren (Reviewer).

---

## 1. Das Kernkonzept (MVP)

Um die Komplexität zu Beginn minimal zu halten, ist die erste Iteration des RBT (Minimum Viable Product) radikal auf den Menschen als primären "Reviewer" zugeschnitten.

In seiner primitivsten Form benötigt das RBT nur zwei Informationen:

* **Target:** Das Objekt oder Programmsegment, das geprüft werden soll. (wenn nichts angegeben wird, wird das gesamte Projekt als target interpretiert.)
* **Check:** Ein String, der die Prüfregel oder Frage formuliert.

### Der Ausführungs-Lebenszyklus

1. **Pausierung:** Das Framework pfuscht nicht im Capturing von Pytest herum. Wenn ein RBT-Knoten erreicht wird, ruft der Test den HumanReviewer auf und blockiert einfach (wartet synchron).
2. **Präsentation:** Dem Reviewer (in diesem Fall dem Entwickler vor dem Terminal) wird das Target und die Direktive über die Konsole präsentiert.
3. **Interaktion:** Das System nutzt ein klassisches Schritt-für-Schritt-Fragespiel. Es blockiert und wartet auf eine binäre Entscheidung (`y/n`) zur Korrektheit sowie auf einen optionalen schriftlichen Report.
4. **Fortsetzung:** Die Eingabe wird ausgewertet. Der Test leuchtet in Pytest entsprechend grün oder rot, und der optionale schriftliche Report wird als Payload dem regulären Pytest-Report übergeben.

Diese simple Terminal-Interaktion ist extrem effizient, vermeidet Kontextwechsel während der Entwicklung und bildet das absolute Fundament der RBT-Architektur.

---

## 2. Die `ReviewData` Datenklasse (Der Vertrag)

Um die `RBT`-Engine dumm, aber das Reporting grenzenlos flexibel zu halten, wird ein hybrides Datenpaket als universeller Vertrag zwischen dem Prüfverfahren (Reviewer) und dem Framework (QPytest) etabliert.

Die `ReviewData`-Datenklasse stellt sicher, dass Pytest harte Assertions auswerten kann, öffnet aber gleichzeitig ein unstrukturiertes Tor für beliebige Metadaten.

```python
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ReviewData:
    passed: bool  # Der harte Vertrag für die RBT-Engine (Grün oder Rot)
    report: Dict[str, Any] = field(default_factory=dict) # Das offene "JSON" für alles andere (Text, Metadaten, Signaturen, etc.)
```

* **`passed`:** Das einzige Attribut, das die `RBT`-Engine intern zwingend auswertet, um zu entscheiden, ob der Test in Pytest fehlschlägt oder durchläuft.
* **`report`:** Ein offenes Dictionary, das als Payload fungiert. Ein menschlicher Tester kann hier sein schriftliches Feedback als simplen String unter `{"text": "..."}` ablegen. Ein maschineller Agent kann strukturierte Felder wie verwendete Tokens, Model-Versionen oder generierte Gedichte anfügen. Die `RBT`-Engine reicht den Inhalt vollständig als Pytest-Report durch.

---

## 3. Das `Reviewer`-Protokoll (Dependency Injection)

 Die `RBT`-Klasse selbst führt keine Prüfungen durch, ruft keine APIs auf und rendert keine Terminal-Prompts. Sie delegiert die gesamte Ausführungs-Phase an ein injiziertes Reviewer-Objekt.

Damit dieses System skalierbar bleibt, müssen alle Reviewer (ob Mensch oder Maschine) einem simplen Protokoll folgen: Sie nehmen die Test-Direktiven entgegen und müssen zwingend ein validiertes `ReviewData`-Objekt zurückgeben.

### Das strukturelle Interface (Konzept)

Ein Reviewer muss mindestens eine ausführende Methode (z.B. `review`) bereitstellen, welche die Brücke zwischen dem definierten Test und der Pytest-Realität schlägt:

```python
from typing import Protocol

class Reviewer(Protocol):
    def review(self, target: str, check: str) -> ReviewData:
        """
        Nimmt das Target und die Direktive entgegen, 
        führt den spezifischen Workflow aus (z.B. Terminal-Input oder LLM-API) 
        und gibt das standardisierte ReviewData-Paket zurück.
        """
```

* **Der Default (HumanReviewer):** Wird dem RBT-Test kein expliziter Reviewer übergeben, injiziert die Engine implizit einen menschlichen Terminal-Reviewer. Dieser übernimmt das Pausieren des Testlaufs, das Rendering des `checks` im Terminal und fängt die `y/n`-Eingaben sowie den optionalen Text ab, um daraus das `ReviewData`-Objekt zu konstruieren.
* **Custom Reviewer:** Jeder Entwickler kann eigene Reviewer-Klassen schreiben und dem RBT-Test als `reviewer`-Attribut übergeben. Solange die Klasse das Protokoll erfüllt und am Ende ein `ReviewData`-Objekt zurückgibt, bleibt der architektonische Vertrag von Cubie gewahrt.