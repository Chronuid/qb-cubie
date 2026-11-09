# Example-Based Testing: Beispiele und Aussagegrenzen

EBT führt konkrete Eingaben aus und vergleicht die beobachteten Ergebnisse mit deklarierten Mustern. Das unterstützt besonders wiederkehrende Akzeptanzszenarien mit Rückgaben und Dateien. Die genaue API definiert die [Vertragssemantik](GUIDE_Contract-Semantics.md); ausführbare Fälle stehen im [Nutzungshandbuch](GUIDE_EBT-Usage-Pattern.md).

## Ausgangsdaten und Zielmuster

In `pre` beschreibt ein `WorldState` Argumente und gegebenenfalls Dateien, die eine explizit gewählte Arena bereitstellt. In `post` beschreibt er aktivierte Vergleiche für Rückgabe, Dateien und gegebenenfalls eine virtuelle Umgebung. EBT führt die Operation tatsächlich aus; es gleicht nicht nur statisch zwei Vorlagen ab.

Eine Dateitransformation kann etwa `input.md` einlesen und `output.md` schreiben. Die Ausgangsdatei ist eine Eingabevorlage, die erwartete Ausgabedatei ein Referenzwert. Diese Vorlagen legen das Ergebnis des konkreten Falls fest. Sie zeigen weder, wie alle anderen Dokumente behandelt werden, noch ob der Referenzwert fachlich richtig ist.

Ein Verzeichnisvergleich erfasst Dateien und Inhalte innerhalb der angegebenen Vergleichswurzel. Er validiert keine vollständige Projektarchitektur, Paketauflösung oder Laufzeitfunktion. Leere Unterverzeichnisse, Rechte und Metadaten sind kein vollständiger Bestandteil dieses Vergleichs.

## Unterspezifikation

Der Fall `2 → 4` lässt unter anderem `x * 2`, `x + 2` und eine konstante Rückgabe `4` zu. Ein weiterer, getrennt definierter Fall `3 → 6` widerlegt einige dieser Implementierungen. Er erzwingt jedoch keine allgemeine Verdopplung: Auch eine Falltabelle kann beide Tests bestehen.

Gemeinsame Listen `pre=[WorldState(args=2), WorldState(args=3)]` und `post=[WorldState(returns=4), WorldState(returns=6)]` bilden diese Zuordnung nicht ab. Jeder Eingang dürfte jedes erlaubte Ergebnis liefern. Verwende separate EBT-Instanzen, beispielsweise mit `pytest.mark.parametrize`.

## Beispiele gezielt erweitern

Wähle Fälle entlang benannter Anforderungen und Merkmale: leere Inhalte, Unicode, Grenzen numerischer Werte oder wechselnde Dateiformate. Ein neuer Fall kann eine bekannte fehlerhafte Implementierung ausschließen. Er beweist keine mathematische Unabhängigkeit der Beispiele und verhindert nicht alle verbleibenden Fehler.

Bei einer Textformatierung können einfache Wörter und Wörter mit Apostrophen unterschiedliche Anforderungen sichtbar machen. Der erwartete Umgang mit Apostrophen muss fachlich festgelegt werden; ein grüner Test macht diese Entscheidung nicht automatisch richtig.

Kuratierte Referenzdaten müssen konsistent und überprüfbar sein. Ergänze sie bei Bedarf durch generative Tests, unabhängige Assertions und Reviews. Ein Würfeltest mit erlaubten Werten `1` bis `6` prüft nur die einzelne beobachtete Ausgabe. Auch ein Generator, der immer `1` liefert, besteht; Verteilung und Zufälligkeit benötigen eigene Prüfungen.

## Grenzen des aktuellen Prüfkerns

Verwende pro Ausführung eine neue EBT-Instanz, nichtleere Zustandslisten und explizite Erwartungen. `returns=None` prüft derzeit keinen Sollwert; nutze dafür ein Prädikat. Diese und weitere Fehler sind in der [Semantikreferenz](GUIDE_Contract-Semantics.md) und im [Gutachten](../GUTACHTEN.md) dokumentiert. Erfolgreiche Beispiele sind begrenzte Beobachtungen, keine allgemeine Korrektheitsgarantie.
