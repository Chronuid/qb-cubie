# EBT-Cases zu Phase 10.1: Öffentliche Verträge und Referenzen

Status: **Öffentliche Schnittstellen implementiert**, 10. November 2026.
Diese Cases konkretisieren die erste Phase aus
[BENCHMARK_KONZEPT.md, Abschnitt 10](../docs/BENCHMARK_KONZEPT.md#10-entwicklungsplan-und-abnahme).
Die beschriebenen Python-Schnittstellen sind in
[`qb_cubie.benchmarks`](../src/qb_cubie/benchmarks/__init__.py) implementiert.
Der ausführende Benchmark-Runner folgt in Phase 2.

Alle Cases werden regulär gesammelt, ohne `xfail`, Freischaltoptionen oder
Modellzugriff. Die ursprüngliche Rotphase bleibt unten dokumentiert. Die Implementierung
wird gegen dieselben Cases sowie ergänzende Gegenproben für Validierungsgrenzen
geprüft; die vollständige Sammlung benötigt weiterhin keine Agentenanbindung.

## Kriterien und Cases

| Kriterium aus Phase 1 | Cases | Konkreter Sollvertrag |
| --- | --- | --- |
| Paket-/Szenarioschema | [test_public_packages.py](benchmarks/test_public_packages.py) | Version, Identität, Lizenz, Herkunft, Materialien, Kriterien und Evaluator sind explizit. Ungültige Felder, fehlende Referenzen, doppelte IDs und Splitwechsel innerhalb einer Gruppe sind Konfigurationsfehler. |
| Typen und Ablauf getrennt | [test_public_packages.py](benchmarks/test_public_packages.py), [test_protocol_contracts.py](benchmarks/test_protocol_contracts.py) | Fehlende Typen/Tags werden zu leeren Listen; freie eigene Typen ändern weder Benchmark noch Evaluator. `benchmark` bestimmt zulässige Phasen. |
| Agenten-/Evaluatorprotokoll | [test_protocol_contracts.py](benchmarks/test_protocol_contracts.py) | Versionierte Anfragen und Antworten; getrennte Agenten- und Evaluatorinputs; Bindung an Lauf und Szenario; Status, Kriteriumsentscheidungen und offene Nachbewertung bleiben unterscheidbar. |
| Set-Semantik | [test_suite_semantics.py](benchmarks/test_suite_semantics.py) | ODER innerhalb eines Filters, UND zwischen Filtern, Vorrang von Ausschlüssen, keine doppelten Läufe durch Mehrfachtypen; Fehler bei leeren Filtern, unbekannten IDs, Leerauswahl und fehlenden Voraussetzungen. |
| Planbarkeit | [test_suite_semantics.py](benchmarks/test_suite_semantics.py) | Relative Pfade beziehen sich auf die Set-Datei. Wiederholungen bilden eigene Versuche. Globale Grenzen führen zum Fehler statt zur Kürzung. Planen startet kein Agentenkommando. |
| Zwei eindeutige Review-Fälle | [test_reference_cases.py](benchmarks/test_reference_cases.py) | Konformer und dateiübergreifend fehlerhafter Fall; vollständige Kriterienurteile; ausführbares Gegenbeispiel; unveränderte echte Quellen werden geprüft. |
| Datei-Projekt mit drei Episoden | [test_reference_cases.py](benchmarks/test_reference_cases.py) | Erstentwicklung, Wartung und Diagnose haben eigene Ausgangsstände, Referenzen und Fehlervarianten. Rückgabe, Inhalt, Sortierung und vollständige Dateimenge werden gemeinsam geprüft. |
| Unabhängige Referenzkontrolle | [test_reference_cases.py](benchmarks/test_reference_cases.py) | Direkter Python-Aufruf und Dateibaumvergleich bestimmen das erwartete Urteil; anschließend muss die EBT-Auswertung damit übereinstimmen. Keine Referenz wird aus der Ausgabe des Targets erzeugt. |

## Öffentlicher Python-Vertrag

Alle Funktionen werden aus `qb_cubie.benchmarks` importiert. Pfadargumente
akzeptieren `pathlib.Path`. Rückgaben bestehen aus JSON-kompatiblen Dictionaries
und Listen. Ungültige Eingaben führen zu `ValueError`; die Fehlermeldung benennt
das betroffene Feld, die unbekannte ID oder die verletzte Grenze. Ein
Konfigurationsfehler wird nicht als fachliche Ablehnung zurückgegeben.

| Funktion | Eingabe | Rückgabe / Verpflichtung |
| --- | --- | --- |
| `load_package(path)` | Paketverzeichnis mit `package.json` | `schema_version`, `namespace`, `version`, `scenarios`; jedes Szenario enthält zusätzlich `qualified_id` und normalisierte `types`/`tags`. Manifestpfade beziehen sich auf das Paket, Material-/Referenzpfade auf das Szenario. |
| `plan_suite(path)` | TOML-Set mit Quellen, Agenten, Budgets und Auswahl | `runs`, absolut aufgelöstes `output`, `max_total_wall_time_seconds`; jeder Versuch enthält `scenario_id`, `agent_id`, ab 1 gezählte `repetition` und aufgelöste `budgets`. Voraussetzungen stehen vor ihren Nachfolgern. |
| `validate_agent_request(payload)` | Versionierte Agentenanfrage | Unveränderte gültige Nutzlast; `benchmark`, `phase`, Auftrag, Workspace, Kriterien, Ausgabeformat und Budgets sind explizit. |
| `validate_agent_event(payload, request)` | Agentenereignis plus zugehörige Anfrage | Unveränderte gültige Nutzlast; fremde Lauf-/Szenariokennungen werden abgelehnt. Abgeschlossene Abgaben benötigen relative Artefaktpfade innerhalb des Workspace. |
| `validate_evaluator_request(payload)` | Eigene versionierte Evaluatoranfrage | Unveränderte gültige Nutzlast mit Evaluator-ID/-Version, Abgabe- und Referenzworkspace, Kriterien und SHA-256-Manifest der Artefakte. Referenzmaterial gehört in die Evaluatoranfrage. |
| `validate_evaluation(payload, request)` | Evaluatorergebnis plus Evaluatoranfrage | Unveränderte gültige Nutzlast mit Ausführungsstatus, Bewertungsstatus, Kriterienurteilen, Metriken und Belegpfaden. Fehlende Kriterien oder fremde Kriterien sind bei vollständiger Bewertung ungültig. |

Die konkreten Nachrichten stehen als feste Beispiele in
[test_protocol_contracts.py](benchmarks/test_protocol_contracts.py).
Version 1 ist der einzige hier zugesicherte Schemastand. Review-Anfragen verwenden
`review`; Developer-Anfragen `test_design`, `red`, `green`, `refactor`.
Diese Phasenbezeichnungen spezifizieren das Nachrichtenformat; ihre Reihenfolge
und Beweispflichten muss erst der Runner durchsetzen.

`status` unterscheidet `completed`, `agent_timeout`, `budget_exceeded`,
`invalid_output`, `infrastructure_error`, `not_started`.
`evaluation_status` unterscheidet `complete`, `not_evaluated` und
`pending_adjudication`. Kriterienurteile sind `pass`, `fail`, `abstain`.
Unbekannte Nutzungswerte bleiben `null`, ebenso noch nicht bestimmbare Metriken.
Eine Enthaltung wird nicht in `pass` umgeschrieben. Unterbrochene Ausführungen
behalten ihren Fehlerstatus und können ohne Kriterienbewertung gemeldet werden.

Die Validierung prüft Struktur, IDs und relative Belegpfade. Ob ein Artefakt
wirklich existiert, sein Hash stimmt und seine Beobachtung zur Abgabe gehört,
ist zusätzlich durch den späteren Evaluator/Runner zu prüfen. Die Schemaprüfung
beweist auch keine Qualität einer Agentenantwort.

## Neue öffentliche Referenzmaterialien

Das Paket unter [fixtures/phase1](benchmarks/fixtures/phase1/package.json) hat
Namespace `phase1`, Version `1.0.0`, MIT-Lizenz und ausschließlich Split
`development`. Die Review-Varianten teilen `group_id=paid-balance`, die drei
Entwicklerepisoden `group_id=document-index`. Beide Review-Fälle kommen bewusst
ohne `types` und `tags` aus. Das Smoke-Set enthält alle fünf Szenarien und nur
eine Agentenkonfiguration; ein Vergleichsagent oder Produktvergleich ist unnötig.

Das Agentenkommando im Fixture existiert absichtlich nicht. Laden und Planen
müssen mit dieser Deklaration funktionieren, ohne es auszuführen. Das ist kein
bereits implementierter Fake-Adapter und kein ausführbares Agenten-Smoke-Set.

**Review:** `balance.total(rows)` muss ganzzahlige Centbeträge ausschließlich
bezahlter Positionen summieren. Der konforme Fall erfüllt `paid_only` und
`exact_cents`. Im fehlerhaften Fall lässt `policy.eligible` unbezahlte Positionen
zu; das Gegenbeispiel ergibt 125 statt 0. Der Defekt erstreckt sich über
`balance.py` und `policy.py`. `exact_cents` bleibt auch im fehlerhaften Fall
bestanden. Leere Eingaben, gemischte Statuswerte und eine Summe oberhalb exakter
Floatdarstellung werden zusätzlich geprüft. Pfad, Symbol, Ursache, Auswirkung,
Gegenbeispiel und zulässige alternative Lokalisierung sind in der Referenz
festgehalten. Es gibt keine erfundenen Findings für den konformen Fall.

**Dokumentindex:** `build_index(source, output)` kopiert Dateien bytegetreu,
schreibt einen lexikografisch sortierten Index relativer POSIX-Pfade und gibt
`None` zurück. Quelldateien bleiben erhalten; der Ergebnisbaum enthält genau
die verlangten Dateien. Die Dateimenge wird einschließlich der Quellen gegen
einen unabhängig aufgebauten Erwartungsbaum geprüft. Leere Verzeichnisse sind
hier kein Abnahmekriterium.

| Episode | Sichtbarer Anfang | Geforderte Änderung | Fehlervarianten |
| --- | --- | --- | --- |
| `index-initial` | Importierbarer Stub mit `NotImplementedError` | Unmittelbare Dateien kopieren und indexieren; Unterverzeichnisse ignorieren | Falsche Rückgabe, fehlende Kopie, falscher Inhalt, zusätzliche Datei, umgekehrte Sortierung |
| `index-maintenance` | Geprüfte Referenz der Erstentwicklung | Rekursive Verarbeitung und ausschließliche Auswahl von `.txt` | Vorige fünf sowie fehlende Rekursion/Filterung und Einschluss anderer Dateitypen |
| `index-diagnosis` | Rekursive Lösung mit absichtlich umgekehrter Sortierung | Sortierfehler beheben und übrige Eigenschaften erhalten | Dieselben sieben gezielten Gegenproben wie bei Wartung |

Die explizite Folge wird über `requires` beschrieben. Die Wartung und Diagnose
beginnen trotzdem jeweils mit einem festgelegten Quellstand statt mit einer
zufälligen vorigen Agentenabgabe. Auswahl ohne die deklarierten Vorgänger wird
abgelehnt und nicht heimlich erweitert.

Lösungen, Ausgangsmodule und Mutanten des Datei-Projekts sind Python-Textfixtures
mit Endung `.py.txt`. Sie werden ausdrücklich geladen, nicht von pytest als
weitere Tests gesammelt. Ein späterer Export muss das sichtbare Modul als
`indexer.py` bereitstellen; Evaluatormaterial wird dabei nicht mit exportiert.
Die Texte sind noch kein installierbares Projektpaket. Installation und
Wheel-Prüfung gehören zum Durchstich in Phase 2.

Jede der **17 Fehlervarianten** besitzt eine Zuordnung zu sichtbaren Kriterien
in `evaluator/reference.json`. Der belegte Datensatz enthält mehrere Dateien,
einen Unterordner und einen ausgeschlossenen Dateityp; alle Mutanten müssen
mindestens daran scheitern. Weitere Datensätze prüfen Leerfälle, tiefe Pfade,
case-sensitive Endungen und Binärinhalte. Ein Mutant darf einen nicht
unterscheidenden Leerfall bestehen; entscheidend ist das feste Gegenbeispiel.

Die Referenzen sind als `author_checked` mit leerer Liste `human_reviews`
gekennzeichnet. Die automatischen Direktprüfungen sind unabhängig von EBT,
ersetzen aber **keine zweite menschliche Prüfung**. Die im Konzept geforderte
unabhängige menschliche Aufnahmeprüfung steht aus. Die technische Implementierung ersetzt diese Aufnahmeprüfung nicht; die
Referenzen bleiben bis dahin ausdrücklich `author_checked`.

## Ausführung und Grenzen

```bash
# Bereits ausführbare Referenzen, Gegenbeispiele und Mutanten
.venv/bin/python -m pytest -q tests/benchmarks/test_reference_cases.py

# Alle öffentlichen Verträge und Referenzprüfungen
.venv/bin/python -m pytest -q tests/benchmarks

# Lint-Prüfung der neuen Dateien
.venv/bin/python -m ruff check tests/benchmarks
```

Alle erwarteten API-Ergebnisse bzw. Konfigurationsfehler werden über EBT mit
`WorldState` und gegebenenfalls `ExceptionExpectation` geprüft. Der Reporter
ist deaktiviert; pytest prüft `RunTrace.evaluation` ausdrücklich. Gezielt
fehlerhafte Referenzprogramme müssen eine **unnegierte** EBT-Auswertung von
`False` liefern. Kein Fehler wird mit `EBT(expect=False)` zu einem scheinbar
bestandenen fachlichen Vertrag umgedeutet.

Noch nicht Gegenstand dieses ersten Schritts sind CLI, JSONL-Transport,
Prozessadapter, Wheel-Installation, kontrollierte Rot-/Grün-Ausführung,
Finding-Matching/Metriken, Hash-/Artefaktverifikation, Container und reale
Modellläufe. Die Tests behaupten für diese Bestandteile keinen Erfolg.

## Historischer Ausgangsstand vor Implementierung

Lokaler Linux-Lauf am 10. November 2026:

| Gruppe | Bestanden | Fehlgeschlagen |
| --- | ---: | ---: |
| Referenzlösungen, Review-Gegenbeispiele, Startstände und Mutanten | 85 | 0 |
| Statische Episodenvoraussetzungen im Fixture | 1 | 0 |
| Öffentliche Paket-, Set- und Protokollverträge | 0 | 106 |
| **Gesamt** | **86** | **106** |

Alle 106 Fehlschläge haben denselben kontrolliert geprüften Grund:
`public qb_cubie.benchmarks API is not implemented`. Der JUnit-Bericht enthält
keine Setup-/Sammlungsfehler und keine übersprungenen Cases. Die damaligen roten Cases belegten die fehlende API, noch keine einzelnen
Fehler der späteren Implementierung. Ruff akzeptiert alle neuen Python-Dateien. Die vollständige
Repository-Sammlung ist mit **1528 Tests** möglich; ein vollständiger Lauf der
bestehenden Suite wurde für diese ausschließlich ergänzten Tests nicht ausgeführt.


## Implementierter Umfang

Die sechs öffentlichen Funktionen sind ohne zusätzliche Abhängigkeit und ohne
Modell-/Netzwerkzugriff verfügbar. Der Loader validiert Material und
Referenzabdeckung; er führt keine Referenzprogramme aus. Der Planner verwendet
dieselbe Validierung, löst Budgets und Agentenfähigkeiten auf und erstellt einen
vollständigen Plan. Auch eine übergroße Zahl von Wiederholungen wird vor dem
Erzeugen der Versuche gegen die globalen Grenzen geprüft.

[Ergänzende Gegenproben](benchmarks/test_contract_boundaries.py) prüfen unter
anderem Zyklen, fehlende Messfähigkeiten, numerisch ungültige Budgets, doppelte
JSON-Schlüssel, Referenzen im sichtbaren Material und getrennte Ergebnis-
Momentaufnahmen. Evaluatortypen müssen zum Benchmark passen; Evaluatorworkspaces dürfen sich
auch bei alternativer POSIX-/Windows-Schreibweise nicht überschneiden.
Unterbrochene oder offene Bewertungen dürfen keine numerischen
Qualitätswerte behaupten. Negative Werte abgeschlossener eigener Metriken sind
zulässig, etwa für Zeitdifferenzen.

Die [API-Anleitung](../docs/GUIDE_Benchmark-Contracts.md) dokumentiert die
verfügbaren Eingaben, Voreinstellungen und Grenzen. Die noch ausstehende
menschliche Referenzfreigabe und der ausführende Durchstich bleiben separat
sichtbar.


## Prüfung nach Implementierung

Die ursprünglichen **192 Cases bestehen unverändert**. Hinzu kommen **41**
Gegenproben für Validierungs- und Planungsgrenzen, insgesamt **233 bestandene
Benchmark-Cases**. Der abschließende gezielte Lauf einschließlich Styleguide und
aller drei Quellcode-Linter ergibt:

```text
254 passed, 1 skipped in 16.79s
```

Der Skip ist die bereits ausgesetzte Modulgrößenprüfung; die Prüfung auf maximal
12 Codezeilen je Funktionskörper bleibt aktiv und besteht.

Der vollständige Regressionslauf ergibt:

```text
1551 passed, 12 skipped, 6 warnings in 342.31s (0:05:42)
```

Dieser Lauf enthält die ursprünglichen 192 Benchmark-Cases und die ersten 35
zusätzlichen Grenzfälle. Die sechs zuletzt ergänzten Gegenproben für inkompatible
Evaluatoren und überlappende Workspaces sind im abschließenden gezielten Lauf
enthalten. Ruff akzeptiert zusätzlich alle neuen Quell- und Testdateien.
Die zwölf übersprungenen Tests des vollständigen Laufs sind keine neuen
Benchmark-Skips; die sechs Warnungen stammen aus bestehenden TempFS- und
IPC-Rehydrationstests. Eine menschliche Freigabe der Referenzen oder einen
installierten CLI-/Agentenlauf belegen diese Ergebnisse nicht.
