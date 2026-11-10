<center>

# Qualitätssicherung mit Cubie

![Cubie](.assets/cubie-logo-written.png)

Cubie bündelt deklarative Akzeptanztests, Review-Aufträge und Linter-Diagnosen. Sein praktischer Nutzen liegt in wiederverwendbaren Konventionen für Eingaben, Rückgaben und Dateien sowie in einer gemeinsamen Orchestrierung. Die [Vertragssemantik](GUIDE_Contract-Semantics.md) ist die zentrale Referenz für das vorhandene Verhalten und bekannte Fehler.

---

</center>

## Beobachtung, Abdeckung und Beweis

**Beobachtete Konformität** bedeutet: Die ausgeführten Fälle passen unter den jeweiligen Testbedingungen zu den aktivierten Sollmustern. Die Aussage hängt von korrekten Testdaten, einem zutreffenden Vergleich und einem funktionierenden Prüfkern ab. Das [Gutachten](../GUTACHTEN.md) benennt Fehler, die derzeit falsche Erfolge ermöglichen.

**Testabdeckung** beschreibt, welche Anforderungen, Eingabeklassen oder Codebereiche untersucht wurden. Unterschiedliche Beispiele können die Abdeckung verbessern; ihre Anzahl allein belegt weder Vollständigkeit noch unabhängige Dimensionen. Cubie berechnet aus einer Liste von `WorldState`-Objekten keine Abdeckungsmetrik.

**Bewiesene Eigenschaften** benötigen einen angegebenen Geltungsbereich, Annahmen und eine tragfähige Begründung durch ein geeignetes Beweisverfahren. EBT und RBT liefern keinen solchen allgemeinen Nachweis. Ein boolesches Testergebnis macht eine Beobachtung oder Beurteilung nicht zum Beweis.

## EBT und die Hoare-Analogie

EBT beschreibt konkrete Ausgangsdaten, führt eine Operation aus und vergleicht das Ergebnis mit Mustern. Die Anordnung „Ausgangszustand – Operation – Zielzustand“ erinnert an ein Hoare-Tripel `{P} S {Q}`. Das ist eine didaktische Analogie: Ein `WorldState` ist ein Datensatz oder Muster, kein allgemein bewiesenes Zustandsprädikat. Cubie enthält weder einen Hoare-Beweiskalkül noch eine vollständige Exploration zulässiger Eingaben. Eine Gleichsetzung mit einem Funktionstyp `S: P → Q` beschreibt die implementierten Garantien nicht angemessen.

Die Begriffe All- und Existenzquantor beziehen sich ausschließlich auf endliche, explizite Zustandslisten: Jeder ausgeführte Eingang muss mindestens ein positives Muster erfüllen, sofern solche vorhanden sind, und darf kein negatives Muster erfüllen. Eine gemeinsame Zielmenge stellt keine paarweise Zuordnung her. Details und Sonderfälle stehen in der [Semantikreferenz](GUIDE_Contract-Semantics.md).

## Auswahl von Beispielen

Ein kuratierter Referenzdatensatz („Golden Dataset“) enthält bewusst gewählte Sollwerte. Auch diese Werte können falsch, widersprüchlich oder unvollständig sein. Synthetisch erzeugte Fälle benötigen ebenfalls eine begründete Erwartung; ihre Herkunft allein bestimmt keine höhere oder niedrigere Autorität.

Beispiele sollten unterschiedliche fachliche Merkmale und Randfälle abdecken. Der frühere Ausdruck „orthogonal“ war dafür zu stark: Ohne ein definiertes Merkmalsmodell und einen Nachweis unabhängiger Dimensionen ist Vielfalt keine mathematische Orthogonalität. Kein endlicher Datensatz verhindert allgemein fehlerhafte Implementierungen oder Overfitting. Cubie erzwingt auch keine Abstraktion aus den Beispielen.

Property-Based Testing kann mit Generatoren zusätzliche Eingaben gegen Eigenschaften prüfen; Linter und Typprüfer ergänzen statische Analysen. Diese Verfahren werden nicht allein durch ihre Verwendung zu formalen Beweisen oder zu Logik höherer Stufe. Cubie implementiert keinen eigenen allgemeinen PBT-Generator.

## RBT und zusätzliche Kriterien

RBT übergibt eine Prüfregel und eine Zielbezeichnung synchron an einen Reviewer. Dieser muss Quellen und Kontext selbst beschaffen und beurteilen. Standardmäßig fragt ein Terminal-Reviewer nach einer Entscheidung. Ein eigener automatisierter Reviewer ist möglich; ein integrierter LLM-Adapter ist nicht vorhanden.

Eine Reviewer-Entscheidung ist unter Angabe von Kriterien, Prüfer und verfügbarem Material einzuordnen. Sie belegt weder universelle Sicherheit noch alle nichtfunktionalen Eigenschaften. Laufzeit- und Speicherbudgets werden durch eine sprachliche Prüfregel nicht automatisch gemessen oder durchgesetzt.

## Suchraum als Motivation

Die Vorstellung, Tests würden mögliche Implementierungen eingrenzen, ist als Denkmodell nützlich. Cubie durchsucht jedoch weder `Σ*` noch erzeugt es Code oder berechnet eine Menge verifizierter Lösungen. Die Essays unter `misc` erläutern konzeptionelle Ideen; sie definieren keine Produkteigenschaften. Geplante Funktionen werden als Entwürfe geführt.

Für Datei-Workflows können deklarierte Vorlagen wiederholte Einrichtung und Vergleichslogik vereinfachen. Bei einfachen Funktionen ist eine gewöhnliche pytest-Assertion oft kürzer. Ein allgemeiner Produktivitätsgewinn ist bislang nicht empirisch belegt. Arenen dürfen dabei nur für vertrauenswürdigen Code eingesetzt werden: Die vorhandenen Implementierungen bieten keine OS-Sicherheitsgrenze.

---

---

<center>

![Error while trying to load the image](.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
