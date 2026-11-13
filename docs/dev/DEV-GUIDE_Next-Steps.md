# DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes

## 1. Einordnung der vergangenen Entwicklung (Sprint zu v0.0.3)

Die bisherige Historie des Repositorys gliedert sich in den gewachsenen Framework-Kern und die unter Zeitdruck entstandenen Wettbewerbs-Artefakte in Version `0.0.3`.

### 1.1 Der architektonische Kern von `qb-cubie`

Im Zentrum von `qb-cubie` steht ein deklaratives Qualitätssicherungs- und Verifikations-Framework für Python. Es vereint Example-Based Testing (EBT) über `WorldState`-Dataclasses (inspiriert durch Hoare-Tripel $\{P\}\ S\ \{Q\}$ als konkrete Datenmuster), Review-Based Testing (RBT), Ausführungs-Arenen (`TempFS`, `PyVenv`) sowie statische Linter (`AstLinter`, `CstLinter`). Vor dem Wettbewerbs-Sprint war dieser Kern durch rund 300 manuell kuratierte und geprüfte EBT-Verträge abgesichert.

### 1.2 Der Wettbewerbs-Sprint und seine Artefakte

Für den *Google Gemma 4 Developer Agent Competition Paper Track* wurde das Projekt in kürzester Zeit um eine Evaluations- und Experimentier-Umgebung ergänzt:

* **Benchmark-Subsystem:** `qb_cubie.benchmarks` (`cubie-bench`) und der Zero-Leakage-Harness trennen echte Code-Reparaturen strikt von manipulierten Agenten-Tests.


* **Agenten-Iterationen (`v1`–`v9`):** 42 Single-Agent- und 17 Multi-Agent-Läufe legten die vorgelagerten Bottlenecks von `gemma4:12b` offen, während die bauenden und prüfenden Agenten (`Antigravity`, `Codex`) selbst unter Beobachtung standen.


* **Test-Inflation:** Über 698 `pytest`-Nodes für Studien-Controller sowie synthetische Edge-Case-Tests ließen die Suite sprunghaft von ~300 handgeprüften EBT-Cases auf über 2.000 Tests anwachsen.



## 2. Phase 1: Aufbau des neuen Feature-Zweigs `qb_cubie.services`

Der nächste Entwicklungsschritt beginnt bewusst nicht mit manuellem Aufräumen, sondern mit dem neuen Feature-Zweig **`qb_cubie.services`**. Während die Kernmodule die Grundbausteine für Verträge, Arenen und AST/CST-Analysen liefern, stellt `services` allgemein wiederverwendbare, sofort einsatzbereite Prüf-Dienstleistungen bereit. Diese Services bieten allen Nutzern fertige Qualitäts-Garantien und liefern gleichzeitig das präzise Prüfwerkzeug für die anschließende Bereinigung des eigenen Repositorys.

### 2.1 Verifikation von Dokumentations-Beispielen (`DocEnsurance`)

Den Auftakt in `qb_cubie.services` bildet ein Service zur automatisierten Verifikation der Funktionalität von Code-Beispielen in Dokumentationen (wie `docs/GUIDE_*.md`):

* **Protokoll-Design:** Über erweiterbare Strukturen wie *ZUM BEISPIEL* `DocEnsurance(protocol: CodeExampleProtocol, arena: ...)` wird festgelegt, wie Code-Snippets, Vorbedingungen und erwartete Ergebnisse in der Dokumentation ausgezeichnet werden.



### 2.2 Semantisches Test-Linting & Styleguide-Services

Darauf aufbauend folgen weitere Services auf Basis von `AstLinter` und `CstLinter`, die allgemeine Struktur- und Abdeckungsregeln kapseln:

* **Test-Abdeckungs-Linter:** Prüft anhand der Code-Struktur, ob bestimmte Funktions-Archetypen nachweislich durch die geforderten EBT-Verträge und Test-Kategorien abgesichert sind.


* **Wiederverwendbare Styleguide-Checks:** Bündelt konfigurierbare Architektur- und Linter-Prüfungen als fertige Services, die sich ohne eigenen Boilerplate-Code in jede Test-Suite einklinken lassen.

## 3. Phase 2: Analyse und Aufräumarbeiten der Sprint-Artefakte

Sobald die neuen Prüf-Services aus Phase 1 bereitstehen, werden sie eingesetzt, um die im Sprint entstandenen Artefakte systematisch zu analysieren, auszudünnen und neu zu ordnen:

* **Analyse der synthetischen Test-Suite:** Die ~300 handgeprüften EBT-Verträge werden als Referenzkern isoliert, während die 2.000+ generierten Tests (inklusive der 698+ `pytest`-Nodes) mithilfe der neuen Linter-Services geprüft, potentiell von Redundanzen befreit und in kompakte EBT-Verträge überführt werden.


* **Neuordnung des Benchmark-Subsystems:** Das unter Zeitdruck gewachsene Subsystem (`qb_cubie.benchmarks` sowie `experiments/testguided-study/` mit den Controllern `v1`–`v9`) wird analysiert und wahrscheinlich entweder ausgelagert oder als saubere Schnittstelle für externe Agenten neu aufgebaut.

* **Gezielte Pflege von Plattform-Spezifika:** Bekannte plattformspezifische Abweichungen (wie in der eingefrorenen Windows-CI) werden weiterhin nicht stillschweigend ausgeblendet, sondern sauber dokumentiert und schrittweise aufgelöst.

## 4. Phase 3: Abarbeitung der Punkte aus dem Gutachten (`GUTACHTEN.md`)

Im Anschluss an die strukturelle Bereinigung werden die drei im internen Audit (`./GUTACHTEN.md`) dokumentierten und ursprünglich für die Version `0.0.4` vorgemerkten Randfälle im bereinigten Kern analysiert.