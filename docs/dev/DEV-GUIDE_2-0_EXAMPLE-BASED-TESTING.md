<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# EBT: Entwicklerübersicht

![Cubie](../.assets/cubie-logo-written.png)

EBT orchestriert konkrete Ausführungen und Ergebnisvergleiche. Die Anordnung von Ausgangsdaten, Operation und Zielmustern erinnert an Hoare-Tripel, implementiert aber keine formale Programmverifikation. Maßgeblich ist die [Vertragssemantik](../GUIDE_Contract-Semantics.md).

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Komponenten

- `EBT` normalisiert Zustandslisten, führt je Eingang eine Aufgabe aus und aggregiert deren Vergleiche.
- `WorldState` ist eine veränderliche Dataclass für Argumente, Rückgabemuster, Dateien und Arena-Konfiguration. Primitive `pre`-/`post`-Werte werden nicht automatisch in solche Objekte konvertiert.
- `Arena` beschreibt Aufbau, Ausführung, Zustandserfassung und Aufräumen einer Umgebung. `TempFS` nutzt den Host-Interpreter, `PyVenv` eine kopierte virtuelle Umgebung; beide laufen in Kindprozessen ohne OS-Sicherheitsgrenze.
- `EvaluationTrace` enthält einen rohen Vergleich zwischen einem beobachteten Ergebnis und einem Zielmuster. `RunTrace` bündelt Vergleiche und aggregiertes Ergebnis. Beide sind veränderlich.
- `Reporter` konsumiert das Ergebnis. `PytestReporter` erzeugt die Assertion; mit `reporter=None` muss der Aufrufer `evaluation` selbst auswerten. Ausführungsfehler propagieren trotzdem.

## Ablauf und Grenzen

`run()` ruft `_arrange()`, `_validate()` und `_report()` auf. Die Zustände werden als `WorldState` oder Listen davon übergeben. Für jeden Eingang gilt dieselbe Zielmenge; es gibt keine paarweise Zuordnung. Bei regulärem Abschluss wird der `RunTrace` zurückgegeben. Target- oder Reporter-Exceptions können die Rückgabe verhindern.

Der Aufruf ist synchron. EBT wartet Coroutine-Targets nicht automatisch ab; bei Bedarf muss ein synchroner Wrapper die asynchrone Ausführung übernehmen. Ohne Arena läuft das Callable im aufrufenden Prozess und dessen Zustand bleibt zwischen Eingangsschritten erhalten.

Explizites `returns=None` verlangt eine None-Rückgabe; ausgelassenes `returns` lässt die Rückgabe offen. Leere Zustandslisten werden vor der Ausführung abgelehnt. Jeder Lauf setzt die Laufdaten zurück und erzeugt unabhängige historische Traces. Target-Seiteneffekte und bereits veränderte Eingaben werden dabei nicht zurückgesetzt. Die vollständigen Einschränkungen stehen in der zentralen Referenz; erfolgreiche Beispiele beweisen keine allgemeine Korrektheit.

## Weiterführende Dokumentation

- [EBT-Klasse und Ausführung](DEV-GUIDE_2-1_EBT-Class.md)
- [WorldState](DEV-GUIDE_2-2_WorldState-Class.md)
- [Arenen und Codecs](DEV-GUIDE_2-3_Arenas.md)
- [Multiprocessing](DEV-GUIDE_2-4_Multiprocessors.md)

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](../GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
