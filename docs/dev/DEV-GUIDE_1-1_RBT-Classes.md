## `class RBT`

Das `RBT` fungiert als Brücke zwischen unscharfen Anforderungen und dem harten, automatisierten Test-System. Die Klasse delegiert die eigentliche Prüfung an ein injiziertes Reviewer-Objekt.

**Kern-Verantwortlichkeiten:**

* **Target-Auswertung:** Wenn `target` nicht definiert ist, bezieht sich die Prüfung implizit auf das gesamte Projekt. Direkte Python-Objekte werden dynamisch zu String-Repräsentationen evaluiert. Strings werden direkt übergeben.

* **Pytest-Orchestrierung & Lebenszyklus:** 
  * Das Framework pfuscht nicht im Capturing von Pytest herum. Wenn ein RBT-Knoten erreicht wird, ruft der Test den HumanReviewer auf und blockiert einfach (wartet synchron).
  * Nach der Prüfung durch den Reviewer reicht sie das Test-Ergebnis und -Bericht nahtlos als Pytest-Ergebnis und -Report weiter.

### `RBT.target`

Repräsentiert das Objekt oder Programmsegment, das geprüft werden soll (z.B. `"rbt.py:RBT"`).

### `RBT.check`

Ein String, der die Prüfregel, die Direktive oder eine subjektive Frage formuliert.

### `RBT.reviewer`

Ermöglicht das dynamische Austauschen der Prüfinstanz (Dependency Injection).
* RBT.reviewer müssen die beiden Strings `RBT.target` und `RBT.check` entgegen nehmen und zu einem ReviewData-Objekt transformieren können.
* Nimmt automatisierte Instanzen wie `AgentReviewer` oder `CustomReport` für autonome Workflows entgegen.
* Wird kein Reviewer übergeben, injiziert die Engine standardmäßig den `HumanReviewer`.


### `RBT.tags`

Eine Liste von Strings (z.B. `tags=["exploration"]`). Die Tags bleiben von Pytest-Marken differenzierbar, um zukünftige Plugins sauber anzudocken.

Das Aufräumen der Mock-Klassen ist ein guter Schritt für die Code-Hygiene. Für Tests des Frameworks selbst reicht es später völlig, diese bei Bedarf isoliert im Test-Verzeichnis hochzuziehen.

Hier sind die formulierten Abschnitte für deinen `DEV-GUIDE_1-1_RBT-Classes.md`. Sie greifen exakt unsere architektonischen Entscheidungen, das Pipeline-Pattern und die Gründe für das Wiring auf:


### `RBT.run()` & Wiring

Die `run()`-Methode ist der primäre Einstiegspunkt und fungiert als Top-Down-Kompositionsfunktion. Sie implementiert ein striktes Pipeline-Pattern, das den Testlauf in drei klar definierte Phasen unterteilt:

* **`_arrange()`:** Bereitet die Eingabedaten vor. Hier wird das übergebene Zielobjekt (`target`) dynamisch zu seiner String-Repräsentation evaluiert.
* **`_review()`:** Delegiert die eigentliche Prüfung an das injizierte Reviewer-Objekt und wartet synchron auf die Rückgabe des `ReviewData`-Pakets.
* **`_report()`:** Formatiert das offene Dictionary in einen maschinenlesbaren, aber visuell ansprechenden JSON-Payload und übergibt das finale Prüfergebnis über eine harte `assert`-Anweisung an Pytest.

**Die Verkabelung (Wiring):**
Der Datenaustausch zwischen diesen Phasen erfolgt konsequent über geschützte Instanz-Attribute (wie `self._target_string`, `self._result` und `self._raw_json`). Dies vermeidet tiefe Parameterketten, wahrt eine extrem hohe Kohäsion und etabliert die Klasse selbst als dedizierten State-Container für den jeweiligen Testlauf.
Zudem nutzt die Pipeline gezielt das Pytest-Feature `__tracebackhide__ = True`. Dadurch werden interne Framework-Aufrufe im Stacktrace ausgeblendet, sodass der Entwickler bei einem fehlgeschlagenen RBT-Knoten direkt zu seinem Test-Aufruf geleitet wird, anstatt sich durch Framework-Schichten graben zu müssen.


---

## `class ReviewData`

Das `ReviewData`-Paket ist eine hybride Datenklasse und dient als universeller Vertrag zwischen dem Prüfverfahren (Reviewer) und dem Framework.

### `ReviewData.passed`

Ein `bool`-Wert für die binäre Entscheidung (Bestanden/Fehlgeschlagen). Dies ist das einzige Attribut, das die `RBT`-Engine zwingend auswertet, um den Pytest-Status (Grün/Rot) zu bestimmen.

### `ReviewData.report`

Ein offenes Dictionary (`Dict[str, Any]`), das als unstrukturierter Payload fungiert.
* Nimmt simple Texte (z.B. `{"text": "..."}`) von menschlichen Testern oder Metadaten von Agents auf.
* Wird von der RBT-Engine ohne Strukturvorgaben als Pytest-Report durchgereicht.



---

## `class HumanReviewer`

Der `HumanReviewer` ist auf das manuelle Bootstrapping ausgelegt und dient als Standard-Prüfinstanz für das interaktive Testing (Human-in-the-Loop).
**Wichtig:** Die Klasse ist vollständig von Pytest entkoppelt. Sie kennt ausschließlich die von `RBT` übergebenen Attribute (`target`, `check`) und führt rein den Prüf-Algorithmus aus.

**Ausführungs-Lebenszyklus:**
* **Präsentation:** Rendert das Target und die Direktive im Terminal.
* **Interaktion:** Das System blockiert und wartet auf eine binäre Entscheidung (`y/n`) zur Korrektheit sowie auf einen optionalen schriftlichen Report.
* **Rückgabe:** Konstruiert aus den Eingaben ein validiertes `ReviewData`-Objekt und gibt dieses an die übergeordnete `RBT`-Instanz zurück.

> **Architektur-Hinweis (Tkinter):** Die Entscheidung, für das interaktive Testing auf die Standardbibliothek `tkinter` zu setzen, dient als robuster Bypass für das aggressive `stdin`/`stdout`-Capturing von Pytest. Anstatt innerhalb der Konsole gegen den Test-Runner zu kämpfen, spawnt das Framework ein leichtgewichtiges OS-Fenster. Dies entkoppelt die Eingabe vollständig vom Runner und blockiert den Ausführungsthread auf natürliche Weise.

### `HumanReviewer.review()` & Wiring

Ähnlich wie die RBT-Hauptklasse nutzt auch der `HumanReviewer` das Pipeline-Pattern, bei dem die `review()`-Methode den gesamten Lebenszyklus der Interaktion von oben nach unten orchestriert.

* **Setup:** Die injizierten `target`- und `check`-Parameter werden in den internen Zustand überführt.
* **`_run_gui()`:** Initialisiert das Tkinter-Fenster (forciert im Vordergrund via `-topmost`), delegiert das Rendern der UI an untergeordnete Kompositionsfunktionen (`_build_widgets`, `_build_buttons`) und friert den Thread anschließend über `wait_window()` synchron ein, bis der Nutzer interagiert.
* **`_finalize()`:** Wird durch die Button-Events (`_on_pass` / `_on_fail`) getriggert. Diese Methode liest den Text-Report aus der UI aus, speichert ihn im Zustand und zerstört das Fenster, woraufhin die Pipeline fortgesetzt wird.

**Die Verkabelung (Wiring):**
Die Logik ist strikt von der Darstellung getrennt. Der valide Zustand der Prüfung (`self._passed`, `self._report_text`) wird flach in den Attributen der Instanz gehalten. Die GUI-Methoden dienen ausschließlich dazu, diese Attribute zu visualisieren und am Ende des Lebenszyklus mit den Eingaben des Nutzers zu befüllen. Statische Typen-Guards sichern die Pipeline ab, um das System zur Laufzeit zu schützen und statische Linter zufriedenzustellen. Sobald das Fenster geschlossen ist, konstruiert die Hauptmethode aus diesem sauberen internen Zustand das geforderte `ReviewData`-Objekt.
