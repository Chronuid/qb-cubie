## `class RBT`

Das `RBT` fungiert als Brücke zwischen unscharfen Anforderungen und dem harten, automatisierten Test-System. Die Klasse delegiert die eigentliche Prüfung an ein injiziertes Reviewer-Objekt.

**Kern-Verantwortlichkeiten:**

* **Target-Auswertung:** Wenn `target` nicht definiert ist, bezieht sich die Prüfung implizit auf das gesamte Projekt. Direkte Python-Objekte werden dynamisch zu String-Repräsentationen evaluiert. Strings werden direkt übergeben.

* **Pytest-Orchestrierung & Lebenszyklus:** 
  * Sobald der RBT-Knoten erreicht wird, friert der Testlauf ein und lässt dem Reviewer Zeit zur Prüfung. 
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
