# EBT: Entwicklerübersicht

EBT orchestriert konkrete Ausführungen und Ergebnisvergleiche. Die Anordnung von Ausgangsdaten, Operation und Zielmustern erinnert an Hoare-Tripel, implementiert aber keine formale Programmverifikation. Maßgeblich ist die [Vertragssemantik](../GUIDE_Contract-Semantics.md).

## Komponenten

- `EBT` normalisiert Zustandslisten, führt je Eingang eine Aufgabe aus und aggregiert deren Vergleiche.
- `WorldState` ist eine veränderliche Dataclass für Argumente, Rückgabemuster, Dateien und Arena-Konfiguration. Primitive `pre`-/`post`-Werte werden nicht automatisch in solche Objekte konvertiert.
- `Arena` beschreibt Aufbau, Ausführung, Zustandserfassung und Aufräumen einer Umgebung. `TempFS` nutzt den Host-Interpreter, `PyVenv` eine kopierte virtuelle Umgebung; beide laufen in Kindprozessen ohne OS-Sicherheitsgrenze.
- `EvaluationTrace` enthält einen rohen Vergleich zwischen einem beobachteten Ergebnis und einem Zielmuster. `RunTrace` bündelt Vergleiche und aggregiertes Ergebnis. Beide sind veränderlich.
- `Reporter` konsumiert das Ergebnis. `PytestReporter` erzeugt die Assertion; mit `reporter=None` muss der Aufrufer `evaluation` selbst auswerten. Ausführungsfehler propagieren trotzdem.

## Ablauf und Grenzen

`run()` ruft `_arrange()`, `_validate()` und `_report()` auf. Die Zustände werden als `WorldState` oder Listen davon übergeben. Für jeden Eingang gilt dieselbe Zielmenge; es gibt keine paarweise Zuordnung. Bei regulärem Abschluss wird der `RunTrace` zurückgegeben. Target- oder Reporter-Exceptions können die Rückgabe verhindern.

Der Aufruf ist synchron. EBT wartet Coroutine-Targets nicht automatisch ab; bei Bedarf muss ein synchroner Wrapper die asynchrone Ausführung übernehmen. Ohne Arena läuft das Callable im aufrufenden Prozess und dessen Zustand bleibt zwischen Eingangsschritten erhalten.

Bekannte Fehler betreffen unter anderem nicht geprüfte `None`-Rückgaben, leere Zustandslisten und die Wiederverwendung einer EBT-Instanz. Frühere Traces können nach einem weiteren Lauf verändert werden. Die vollständigen Einschränkungen stehen in der zentralen Referenz; diese Übersicht verspricht keine unveränderliche Historie oder allgemeine Korrektheit.

## Weiterführende Dokumentation

- [EBT-Klasse und Ausführung](DEV-GUIDE_2-1_EBT-Class.md)
- [WorldState](DEV-GUIDE_2-2_WorldState-Class.md)
- [Arenen und Codecs](DEV-GUIDE_2-3_Arenas.md)
- [Multiprocessing](DEV-GUIDE_2-4_Multiprocessors.md)
