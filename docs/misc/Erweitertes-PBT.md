# Erweitertes Property-Based Testing: konzeptionelle Einordnung

**Status: konzeptioneller Vorschlag, keine implementierte Cubie-API.** Die frühere Bezeichnung „ePBT“ fasste unterschiedliche Qualitätssicherungsverfahren zusammen. Sie bezeichnet hier keinen etablierten Beweiskalkül und keine automatisch nachgewiesenen universellen Eigenschaften. Die vorhandene Cubie-Semantik steht in der [Vertragsreferenz](../GUIDE_Contract-Semantics.md).

## Verfahren sinnvoll verbinden

Property-Based Testing beschreibt Eigenschaften und prüft erzeugte Eingaben dagegen. Endliche generierte Ausführungen können Gegenbeispiele finden, belegen aber nicht automatisch die Eigenschaft für alle zulässigen Werte. Fuzzing und PBT können sich überschneiden; ihre Verwendung macht eine Prüfung weder zu Logik höherer Stufe noch zu einer vollständigen Exploration.

Typprüfer untersuchen Verträge innerhalb ihres Typmodells und ihrer Konfiguration. Linter beziehungsweise Syntaxbaumregeln untersuchen bestimmte strukturelle Merkmale. Laufzeitverträge prüfen die tatsächlich erreichten Aufrufe. Diese Verfahren ergänzen sich, liefern aber jeweils nur die durch Methode und Annahmen gedeckten Aussagen. Sie sind nicht allein durch ihre Kombination ein allgemeiner Korrektheitsbeweis.

| Verfahren | Beobachtung oder Analyse | Grenze |
| --- | --- | --- |
| EBT | Konkrete Eingaben gegen deklarierte Zielmuster | Ungeprüfte Eingaben und unzutreffende Sollwerte bleiben möglich |
| PBT / generative Tests | Erzeugte Fälle gegen eine Eigenschaft | Generator und Eigenschaft können lückenhaft oder falsch sein |
| Statische Analyse | Eigenschaften im Modell des jeweiligen Werkzeugs | Aussage hängt von Regeln, Konfiguration und Annahmen ab |
| Laufzeitverträge | Bedingungen bei tatsächlich erreichten Aufrufen | Nicht erreichte Zustände bleiben ungeprüft |
| RBT | Entscheidung eines Reviewers anhand eines Prüfauftrags | Kontext, Material und Beurteilung begrenzen die Aussage |

## Umgang mit Funden

Ein generativ gefundenes Gegenbeispiel kann nach fachlicher Prüfung als reproduzierbarer Regressionstest übernommen werden. Ein kuratiertes Beispiel besitzt aber nicht automatisch höhere Autorität als eine Property. Bei einem Widerspruch müssen Eingabe, Sollwert, Eigenschaft, Generator und Implementierung geprüft werden.

Cubie implementiert keinen eigenen allgemeinen PBT-Generator und keine Rangordnung zwischen „absoluten Fakten“ und „Hypothesen“. Eine Verbindung mit externen Generatoren ist eine mögliche Integration. Für jedes Ergebnis müssen Prüfumfang, Bedingungen und offene Einschränkungen sichtbar bleiben.
