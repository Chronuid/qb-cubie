# EBT-Abnahmecases für Phase 10.5: Messbetrieb

> Phasenbezogener Entwicklungsnachweis. Zahlen, Rotphasen und offene Folgearbeiten
> beziehen sich auf den jeweils beschriebenen Stand. Einordnung und spätere
> Nachweise: [Übersicht](README.md). Befehle werden aus der Repositorywurzel ausgeführt.

Stand: 10. November 2026. **Produktfunktionen implementiert; die ursprüngliche
Rotphase bleibt unten dokumentiert.** Die Cases unter
[benchmarks/phase5](../benchmarks/phase5) prüfen den Messbetrieb mit Gates und
eingefrorenen Konfigurationen. Nutzung: [Benchmark-Leitfaden](../../docs/GUIDE_Benchmarks.md#messbetrieb-gates-und-ci).
Neue öffentliche Schnittstellen werden erst innerhalb der Cases aufgelöst.
Ihr Fehlen erzeugt einen Testfehlschlag und verhindert nicht die Sammlung.

Alle Operationsprüfungen verwenden die vorhandenen EBT-Helfer
[`accepted` und `rejected`](../benchmarks/contracts.py). Diese prüfen ausdrücklich
`RunTrace.evaluation` und den einzelnen Auswertungstrace. Ergänzende Assertions
prüfen Archive, Belegdateien und Seiteneffekte. Es gibt keine Ersatzimplementierung
von Planner, Runner, Gates oder Freeze-Funktion in den Tests.

## Kriterienzuordnung

| Kriterium und Bezug | Abnahmecases |
| --- | --- |
| Konfigurierbare Gates pro Metrik und Typ (§9, §10.5) | [test_gate_planning.py](../benchmarks/phase5/test_gate_planning.py): Schwellen und Auswahl bleiben im Plan; unbekannte Metriken, Operatoren, leere/ungültige Filter, leere Populationen, doppelte IDs und unzulässige Zahlen scheitern vor dem Start. Ein Prozesscase prüft ausdrücklich, dass auch kein Fähigkeiten-Handshake stattfindet. |
| Vollständigkeit und Qualitätsfreigabe getrennt (§7.2, §9) | [test_gate_evaluation.py](../benchmarks/phase5/test_gate_evaluation.py): korrekte und falsche Reviews, exakte Schwellengrenzen, fehlende Versuche, offene Bewertungen und unbekannte Werte; ohne Gates bleibt der Lauf reine Berichterstattung. |
| Qualität, Prozess und Aufwand getrennt (§5.2, §9) | Recall-Gates für einen Fehlerfall; undefinierte Präzision und Recall bestehen selbst eine Nullschwelle nicht. Ein fachlich korrektes Projekt ohne gültiges Rot scheitert am Prozessgate. Kosten werden nur bei vollständiger Beobachtung summiert; die Obergrenze ist inklusive. |
| Nachprüfbare Berichte und CI-Entscheidungen (§7.2, §8, §9) | [test_measurement_reporting.py](../benchmarks/phase5/test_measurement_reporting.py): JSON, öffentlicher Gate-Aufruf und Markdown berichten dieselbe Entscheidung samt Schwelle, Istwert, Grund und Belegen. Exitcodes unterscheiden Konfiguration, Ausführung und Qualität. |
| Eingefrorene Messkonfiguration und reproduzierbare Sets (§3.2, §7.2, §10.5) | [test_frozen_measurements.py](../benchmarks/phase5/test_frozen_measurements.py): Seed, Reihenfolge, Budgets, Gates, Quellen, Referenzen, Agentenkonfiguration und lokaler Adaptercode werden vor dem Start gebunden. Identische Eingaben haben dieselbe Identität; jede geprüfte Änderung erzeugt eine neue. |
| Ausführung des tatsächlich eingefrorenen Stands (§7.2, §10.5) | Ein verschobenes Bundle läuft nach Löschung der ursprünglichen Eingaben. Beschädigte, fehlende, zusätzliche oder ausbrechende Dateien verhindern den Start. Ergebnisse und Adapter-Arbeitsdateien dürfen das Bundle nicht verändern. Bestehende Bundles werden nicht überschrieben. |
| Extern bereitgestellte zurückgehaltene Aufgaben (§6.1, §6.2, §8, §10.5) | [test_held_out_material.py](../benchmarks/phase5/test_held_out_material.py): separat versioniertes Paket mit `held_out`-Katalog, Herkunftsbindung, verschobenen Pfaden und unverändertem Core. Öffentliche Basisfälle dürfen nicht bloß zum ungesehenen Messmaterial umdeklariert werden. |
| Evaluator und Agentenexport getrennt (§5.3, §6.1) | Ein privater Evaluator-Sentinel bleibt außerhalb von Workspace, Export und JSONL-Anfragen, wird aber beim Evaluator archiviert. Ein Prozesslauf wird weiterhin ausschließlich als Infrastrukturbeleg ausgewiesen. |
| Standardtests bleiben offline (§8, §10.5) | [test_offline_opt_in.py](../benchmarks/phase5/test_offline_opt_in.py): echte pytest-Unterprozesse sammeln ohne Adapterstart und überspringen markierte Episoden ohne Freischaltung; eine Markerwahl allein genügt nicht. Fehlende Konfiguration oder Adapter sind bei Freischaltung Fehler. |
| Eigener begrenzter Messjob (§8, §10.5) | [test_measurement_workflow.py](../benchmarks/phase5/test_measurement_workflow.py): eigener manuell auslösbarer Workflow, keine Push-/PR-Auslösung, begrenzte Laufzeit, gesperrte Abhängigkeiten und Archivierung auch bei Fehlschlägen. |
| Eigene CI-Nutzung und Produktmessung dokumentiert (§9, §10.5) | Die installierte Anleitung muss Gates, Freeze, Ausführung, Exitcodes, zurückgehaltene Aufgaben und die Grenzen von Produktmessungen auffindbar erklären. |

## Öffentlicher Vertrag

Die folgenden Erweiterungen sind im Produktcode implementiert. Die methodische
Abnahme realer Agenten- und Produktmessungen bleibt gesonderte Arbeit.

### Gates in Sets

```toml
[[gates]]
id = "payment-quality"
metric = "quality_pass_rate"
operator = "gte"
threshold = 1.0
select.types_any = ["team/payment"]

[[gates]]
id = "developer-process"
metric = "process_pass_rate"
operator = "gte"
threshold = 1.0
select.benchmarks = ["developer_agent"]

[[gates]]
id = "cost-limit"
metric = "cost"
operator = "lte"
threshold = 10.0
```

Ein Gate hat eine nichtleere, innerhalb des Sets eindeutige `id`, eine unterstützte
`metric`, einen Operator `gte` oder `lte` und eine endliche numerische `threshold`.
Boolesche Werte und Zahlstrings sind keine Schwellen. Raten liegen zwischen null
und eins; Kosten sind nichtnegativ. Die initiale Metrikmenge umfasst
`quality_pass_rate`, `process_pass_rate`, `precision`, `recall` und `cost`.

Die optionale `select`-Tabelle verwendet die vorhandene Set-Filtersemantik,
einschließlich `ids`, `types_any` und `benchmarks`. Die Population wird aus den
bereits geplanten Versuchen ermittelt. Mehrfachtypen vervielfachen sie nicht.
Eine leere Population und unbekannte Filter sind Konfigurationsfehler.
Ohne `select` gilt das Gate für alle geplanten Versuche. Prozessgates werden auf
Developer-Versuche eingeschränkt. Planung prüft Gates, bevor ein Agent gestartet
oder ein Fähigkeiten-Handshake ausgeführt wird, und archiviert sie unter `gates`
im aufgelösten Plan.

Die Qualitäts- und Prozessrate ist der Anteil positiver Urteile in der gewählten
Population. `precision` und `recall` verwenden definierte, kompatible
`per_scenario`-Ratiometriken als arithmetisches Mittel dieser Population.
Die primäre familiengewichtete Pilotberichterstattung bleibt unverändert;
CI-Gates auf solche Einzelmetriken ersetzen sie nicht. `cost` ist die Summe
aller Kostenwerte der gewählten Population in derselben Kosteneinheit wie die
archivierten Nutzungsangaben. Die Testkosten sind synthetische Zahlen.

Ein Gate verlangt für jeden seiner geplanten Versuche eine abgeschlossene,
gültige Bewertung und einen definierten Pflichtwert. `not_started`, Abbrüche,
`pending_adjudication` und unbekannte Werte können kein Gate erfüllen, selbst
wenn dessen numerische Schwelle null ist. Fehlen Pflichtwerte, ist der
Gesamtwert `None`; vorhandene Teildaten werden über Zähler sichtbar. Insbesondere
sind unbekannte Kosten nicht null und undefinierte Präzision ist kein Erfolg.

### Gate-Auswertung und Berichte

```python
evaluate_gates(archive_path) -> dict
```

Die Funktion liest und prüft ein vorhandenes Archiv über dieselben
Integritätsregeln wie Vergleich und Pilotzusammenfassung. Sie startet keinen
Agenten und verändert das Archiv nicht. Das gilt auch nach Verschieben des
Archivs. Sie berechnet die Entscheidung aus Plan und Beobachtungen erneut und
vertraut keiner früher gespeicherten Gate-Entscheidung.

Das Ergebnis enthält:

- `schema_version=1`;
- `execution_complete`: wahr genau dann, wenn alle geplanten Versuche den
  Ausführungsstatus `completed` erreicht haben; offene fachliche Nachbewertung
  ist eine andere Dimension;
- `gate_status`: `not_configured`, `passed` oder `failed`;
- `gates` in Deklarationsreihenfolge, mit `id`, `metric`, `value`, `passed`,
  `required_count`, `observed_count`, `reason` und relativen `evidence`-Pfaden.

`required_count` zählt die gewählte geplante Population; `observed_count` nur
deren gültige, vollständig bewertete Pflichtwerte. Bei fehlenden Beobachtungen
werden der Nenner und die Schwelle nicht stillschweigend angepasst.
Ein fehlgeschlagenes Gate hat einen nichtleeren Grund. Ohne konfigurierte Gates
bleibt die Liste leer; das ist keine automatische Qualitätsfreigabe.

`run_suite` und `run_frozen_suite` geben dasselbe Objekt zusätzlich unter
`gate_evaluation` im Rückgabewert und in `results.json` aus. Markdown erklärt
Fehlschläge mit Gate-ID, Metrik, Schwelle, Istwert, Grund und vorhandenen
Belegverweisen. Die CLI verwendet:

| Exitcode | Bedeutung |
| --- | --- |
| 0 | Vollständig ausgeführt; konfigurierte Gates bestanden oder keine Gates konfiguriert. |
| 2 | Konfigurations-/Planungsfehler, einschließlich ungültiger Gates. |
| 3 | Unvollständige oder fehlerhafte Ausführung; hat Vorrang vor einem Gatefehlschlag. |
| 4 | Vollständige Ausführung, aber mindestens ein Qualitäts-/Vollständigkeitsgate verfehlt. |

Der pytest-Runner verwendet seine eigenen Standardcodes; dort ist Code 4 ein
Konfigurations-/Nutzungsfehler und kein Benchmark-Qualitätsurteil.

### Eingefrorene Messungen

```python
freeze_suite(suite_path, destination) -> dict
run_frozen_suite(bundle_path, output_path) -> dict
```

```text
cubie-bench freeze --suite sets/team.toml --destination frozen/team --format json
cubie-bench run-frozen frozen/team --output results/team --format json
```

`freeze_suite` erzeugt ein neues Bundle, ohne den Agenten zu starten. Der
Rückgabewert enthält `schema_version=1`, den absoluten `path` und
`measurement_sha256`. Letzterer ist der SHA-256 der Bytes von `measurement.json`.
Dieser Manifestinhalt ist bei denselben Eingaben unabhängig vom Zielverzeichnis
identisch; Zeitstempel und Zielpfade dürfen die Identität nicht verändern.

`measurement.json` enthält `schema_version`, den aufgelösten `plan`, `runtime`
und `files`. Das Dateiverzeichnis ordnet ausschließlich relativen enthaltenen
Pfaden ihre SHA-256 zu. Es bindet alle für die lokale Ausführung verwendeten
Konfigurations-, Aufgaben-, Herkunfts-, Referenz- und Adapterdateien. Es umfasst
auch lokale Skripte aus der Agentenanbindung; die ursprüngliche Skriptdatei nur
weiter zu referenzieren genügt nicht. Das Manifest ist nicht sein eigener
Dateieintrag. Zusätzliche ausführungsrelevante Dateien nach dem Einfrieren sind
ebenfalls unzulässige Änderungen.

`runtime` enthält `python_version`, `wheel_sha256` und
`dependency_lock_sha256`, zusätzlich `source_sha256` als Fingerprint der
ausführenden Cubie-Pythonquellen. Python-Version und Quellfingerprint sind
Pflichtangaben; bekannte Runtime-Identitäten müssen bei der Ausführung passen.
Fehlende optionale Informationen bleiben explizit `None`, etwa
ein Wheel-Hash beim Quellcheckout. Die Cases verlangen keine erfundenen
Reproduzierbarkeitsangaben. Ein produktiver Messjob muss die benötigte Umgebung
zusätzlich über gesperrte Abhängigkeiten bzw. ein festgelegtes Image bereitstellen.

`run_frozen_suite` prüft das Bundle vollständig vor Start und benutzt die
eingefrorenen Eingaben. Ausgabeort und neue Lauf-IDs gehören zum Ergebnislauf,
nicht zur eingefrorenen Konfiguration. Adapter-Arbeitsdateien müssen ebenfalls
im neuen Lauf entstehen. Das Eingabebundle bleibt unverändert; ein Ergebnisziel
darin wird abgelehnt. Der Lauf archiviert seine `measurement_sha256` im Manifest
und übernimmt geplante Versuchseinheiten, Reihenfolge, Budgets und Gates.
Die CLI und Python-API haben dieselbe Bedeutung.

Unter `inputs.measurement` verweist das Ergebnismanifest auf die ebenfalls
archivierten und gehashten Bytes von `measurement.json`. Die Identität allein
ohne das zugehörige eingefrorene Manifest genügt nicht als späterer Beleg.

SHA-256 bindet Inhalte und macht Änderungen erkennbar. Diese Cases verlangen
keine Signatur oder Authentifizierung eines von Dritten absichtlich komplett
neu gehashten Bundles. Modellantworten werden durch das Einfrieren nicht
deterministisch; die Identität beschreibt die eingefrorene Konfiguration.

### Zurückgehaltenes Material

Ein separat bereitgestelltes Szenariopaket kann einen Katalog mit
`publication_status="held_out"` deklarieren. Seine Szenarien haben
`split="held_out"`; der Katalog enthält weiter Herkunft, Lizenz, Entwurfsgruppe,
Domäne, `assessment` und `potentially_known`. Die synthetische Gegenprobe setzt
letzteres auf `False`. Dies ist deklarative Testmetadatenprüfung und kein
technischer Nachweis, dass niemand das Material zuvor kannte.

Die Paketversion, alle Materialien und der Herkunftskatalog gehen in Plan,
Archiv und eingefrorene Identität ein. Das Paket wird zur Laufzeit von außen
bereitgestellt; dafür sind keine Core-Änderungen erforderlich. Die vorhandene
Regel für öffentliche Kataloge gilt weiter: veröffentlichte Basisfälle bleiben
potenziell bekanntes Entwicklungsmaterial. Ein bloßer Wechsel ihres `split`
macht sie nicht zu neuen zurückgehaltenen Aufgaben.

Der Agent erhält den sichtbaren Auftrag und Quellstand. Private Referenzen,
Testdaten und der Sentinel der Gegenprobe bleiben beim Evaluator. Die Cases
prüfen die exportierten Dateien und JSONL-Anfragen; sie behaupten keine
OS-Isolation gegenüber einem bösartigen lokalen Prozess. Diese folgt weiter
aus den Anforderungen an die Ausführungsumgebung in Abschnitt 7.3 des Konzepts.

### Offline-Standard und CI

Das explizit ladbare Plugin `qb_cubie.benchmarks.pytest_plugin` registriert
`agent_benchmark`, `review_agent` und `developer_agent` sowie
`--run-agent-benchmarks` und `--suite`. Ohne Freischaltung werden echte Episoden
übersprungen. `-m agent_benchmark` hebt diese Sperre nicht auf. Sammlung und
Markerauflistung brauchen keinen Agenten und dürfen keinen Adapter starten.
Eine ausdrückliche Freischaltung mit fehlender Suite oder nicht verfügbarem
Adapter endet vor dem Episodenkörper mit pytest-Code 4.

Die Cases laden das Plugin mit `-p` in isolierten pytest-Unterprozessen.
Ihr Episodenkörper schreibt lediglich eine Sentineldatei. Damit werden
Freischaltung, Skip und Fehlerpolitik ohne Provideraufruf geprüft.
Der spätere Repository-Messlauf muss das Plugin ebenfalls ausdrücklich laden,
beispielsweise über die Benchmark-`tests/conftest.py`; die deterministischen
Abnahmecases dieser Phase tragen selbst keine Agentenmarker.

Der vorgesehene eigene Workflow heißt `.github/workflows/benchmarks.yml` und
ist manuell auslösbar; ein geplanter Lauf ist zusätzlich möglich. Er führt ein
bereitgestelltes eingefrorenes Bundle mit explizitem Ausgabeziel aus, begrenzt
die Joblaufzeit und installiert gesperrte Abhängigkeiten. Seine Upload-Schritte
bewahren Belege auch bei nichtnull Exitcode (`always()`). Gatefehler werden
nicht durch `continue-on-error: true` unterdrückt. Die Cases prüfen diese
Eintrittsbedingungen textuell; sie starten weder GitHub Actions noch prüfen sie
die vollständige Workflow-Semantik eines entfernten Systems.

Die installierte Anleitung soll Team-CI und Produktmessung unterscheiden.
Für Produktmessungen gelten weiterhin: Referenzaufnahme und realer Pilot,
vorab festgelegte primäre Kennzahlen, Mindestvorteil beim Aufwand und tolerierte
Qualitätsabweichung vor Sichtung neuer zurückgehaltener Ergebnisse. Ein lokales
CI-Gate und ein Fake-Erfolg ersetzen diese methodische Abnahme nicht.

## Belegmaterial und Grenzen

Die Fixtures erzeugen echte Runnerarchive mit korrekten und absichtlich falschen
Reviews sowie einem fachlich korrekten Developer-Projekt ohne Rotbeleg.
Gate-Prüfungen nutzen diese Archive und tatsächliche Ergebnisdateien.
Fehlende Versuche, offene Bewertungen und bekannte Kostenzahlen werden
ausdrücklich als simulierte Beobachtungen eingefügt und ihre Archivhashes
erneuert. Sie sind keine gemessenen Providerkosten oder echten Infrastrukturausfälle.

Das zurückgehaltene Paket wird ausschließlich temporär aus vorhandenen
öffentlichen Testvorlagen aufgebaut und als **synthetische Metadaten-Gegenprobe**
gekennzeichnet. Die Ergänzung veröffentlicht keinen echten privaten Messsatz
und behauptet keine unbekannten Aufgaben. Offizielle Referenzen bleiben
`author_checked`; ihre unabhängige menschliche Aufnahme wird nicht vorgetäuscht.

Die Workflow-Prüfungen und die Prüfung auffindbarer Anleitungsinhalte sind
notwendige Strukturkontrollen. Die Bedienbarkeit durch externe Entwickler,
die tatsächliche Unabhängigkeit der Referenzen und reale Agentenleistung
bleiben separat abzunehmen. Für diesen Testentwurf wurde kein Modell angefragt.

## Erste Rotphase

```bash
.venv/bin/python -m pytest tests/benchmarks/phase5 -q --tb=short
```

Ergebnis am 10. November 2026: **11 bestanden, 71 fehlgeschlagen** bei insgesamt
**82 Cases**, ohne Sammlungs- oder Fixture-Setupfehler. Die Fehlschläge betreffen:

- 17 Cases: fehlende Freeze-/Frozen-Run-Schnittstellen und CLI;
- 21 Cases: fehlende öffentliche Gate-Auswertung;
- 14 Cases: Gates fehlen im Plan bzw. werden vor dem Start nicht validiert;
- 4 Cases: fehlende Unterstützung externer `held_out`-Kataloge bzw. ihrer Bindung;
- 4 Cases: Gate-Exitcodes, Gateberichte und Anleitung;
- 3 Cases: fehlender eigener Messworkflow;
- 8 Cases: fehlendes pytest-Plugin und dessen Freischaltungsvertrag.

Die elf grünen Kontrollen bestätigen die Verwendbarkeit eines echten Archivs,
die bestehenden Regeln für Szenariosplits und öffentliche Kataloge, die
Zurückweisung nichtendlicher Zahlen, vorhandene CLI-Statuscodes sowie den
synthetischen pytest-Probekörper. Produktcode und vorhandene Abnahmecases
wurden für diese Rotphase nicht verändert.

Die bestehenden Benchmark- und Styleguide-Prüfungen bleiben grün:

```bash
.venv/bin/python -m pytest tests/benchmarks tests/test_styleguide.py --ignore=tests/benchmarks/phase5 -q
.venv/bin/python -m ruff check tests/benchmarks/phase5 --output-format concise
git diff --check
```

Ergebnis: **458 bestanden, ein bestehender Skip** (ausgesetzte Modulgrößenregel).
Ruff und die Prüfung auf Whitespacefehler sind ohne Befund. Die separate
Sammlung der neuen Phase findet alle 82 Cases. Ein vollständiger Repository-
oder Wheel-Lauf wurde für diese ausschließlich testseitige Rotphase nicht
ausgeführt. Die Abnahme nach Produktumsetzung steht aus.

## Produktumsetzung und ergänzende Gegenproben

Die öffentlichen APIs `evaluate_gates`, `freeze_suite` und `run_frozen_suite`
sind in `qb_cubie.benchmarks` exportiert. Die CLI ergänzt `evaluate-gates`,
`freeze` und `run-frozen`. Planung und Archivbewertung verwenden dieselbe
Gate- und Filtersemantik. JSON, Textausgabe und Markdown erklären Gateurteile;
die dokumentierten Exitcodes werden durchgesetzt.

Die Freeze-Implementierung liegt unter
[`measurement`](../../src/qb_cubie/benchmarks/measurement). Sie veröffentlicht das
Bundle erst nach erfolgreicher Aufnahme und Prüfung der Eingaben. Agenten
werden dabei nicht gestartet. Das Manifest bindet auch Dateimodi und den
ausführenden Cubie-Quellcode. Lokale Adapterressourcen lassen sich ausdrücklich
mit `adapter_files` deklarieren; leere Ressourcenverzeichnisse bleiben erhalten.
Ein Aufruf über den laufenden Python-Interpreter wird auf dessen Namen in der
provisionierten Laufumgebung normalisiert. Ein absoluter Pfad des ursprünglichen
Hosts ist dadurch keine Voraussetzung für den Umzug.

Ein Bundle darf neben den deklarierten Szenarien im eigenen Projekt liegen,
jedoch nicht innerhalb der Szenariomaterialien oder des Adapter-Arbeitsordners.
Die Ausführung prüft eine vollständige Kopie, plant sie erneut und vergleicht
deren Semantik mit dem eingefrorenen Plan. Adapter-Arbeitsdateien entstehen
in einer zweiten temporären Kopie. Das Ergebnisarchiv erhält das unveränderte
Bundle einschließlich seiner Manifestbytes. Vergleich, Pilotzusammenfassung
und Gateprüfung kontrollieren diese Bindung erneut.

Die elf Cases in
[test_measurement_integrity.py](../benchmarks/phase5/test_measurement_integrity.py)
prüfen ergänzend deklarierte Ressourcen, Dateimodi, fünf Runtime-Gegenproben,
verfälschte Messidentitäten, teilweise bekannte Kosten und die Portabilität
von Bundleort und Interpreter. Zusammen mit den ursprünglichen Cases und den
ergänzten Text-, Fixture- und Workflowprüfungen umfasst Phase 10.5 jetzt
**96 Repository-Cases**. Die Anforderungen der ursprünglichen 82 Cases wurden
nicht abgeschwächt.

Das Plugin
[`pytest_plugin.py`](../../src/qb_cubie/benchmarks/pytest_plugin.py) ist im
Repository eingebunden und kann extern ausdrücklich geladen werden.
Die zwei neuen echten Review-/Developer-Einstiegstests bleiben im Standardlauf
übersprungen. Die gemeinsame Ergebnisfixture ist auch dann gegen ungewollten
Start abgesichert, wenn ein eigener Test seinen Agentenmarker vergessen hat.

Der separate
[CI-Messjob](../../.github/workflows/benchmarks.yml) erhält ein vorab bereitgestelltes
Tar-Bundle samt erwartetem Manifest-Hash. Er prüft die Identität, stellt die
passende Python-Version bereit und installiert gesperrte Abhängigkeiten sowie
gegebenenfalls ein separat bereitgestelltes, per Hash geprüftes Wheel.
Tar-Archive erhalten die für die Nachprüfung erforderlichen Dateimodi auch
beim GitHub-Artefakttransport. Uploads nach Fehlern bewahren Belege,
Checkout-Commit und Lockfile. Ein zusätzlicher EBT-Case führt die drei
Python-Schritte des tatsächlichen Workflows lokal mit einem echten Bundle aus
und prüft anschließend dessen Ausführbarkeit. Die IDE meldet keine YAML-Fehler.
Ein entfernter GitHub-Job wurde nicht ausgelöst.

Die [installierte Anleitung](../../docs/GUIDE_Benchmarks.md#messbetrieb-gates-und-ci)
beschreibt Gates, Exitcodes, Freeze, CI-Provisionierung, zurückgehaltene Pakete
und die Voraussetzungen für Produktmessungen. Ihr mitgeliefertes Ressourcenexemplar
ist identisch mit der Dokumentation im Repository.

Vier neue
[Wheel-Cases](../wheel/benchmark_measurement_installed.py) prüfen die Installation
außerhalb des Checkouts: verschobene Fake-Messungen mit Wheelprovenienz und
archivierter Messidentität, den Qualitäts-Exitcode, die standardmäßige
pytest-Sperre und einen aus eingefrorenen Dateien gestarteten JSONL-Prozess
nach Löschung seines ursprünglichen Beispielprojekts. Der Wheel-Harness
führt diese Cases zusätzlich zu den bisherigen Profilen aus.

Diese Umsetzung führt keinen echten Modellaufruf durch und veröffentlicht
keinen privaten Messsatz. Unabhängige menschliche Referenzaufnahme und reale
Pilotmessung bleiben offen. Der lokale Runner setzt weiterhin vertrauenswürdige
Agenten und Evaluatoren voraus; er implementiert keine Containerisolation.
Harte Token-/Providerkostenlimits und die automatische Provisionierung
beliebiger Adapterabhängigkeiten bleiben außerhalb dieses Umfangs.

## Prüfung nach Implementierung

```bash
.venv/bin/python -m pytest tests/benchmarks/phase5 tests/test_styleguide.py tests/test_lint.py -q
```

Der abschließende gezielte Lauf besteht mit **118 bestandenen Tests und einem
bestehenden Skip** (ausgesetzte Modulgrößenregel). Er enthält alle **96 Cases
aus Phase 10.5**, Styleguide sowie Ruff, Mypy und Pylint für den gesamten
Produktcode. Ruff für die neuen Testdateien und `git diff --check` sind ebenfalls
ohne Befund. Beide Exemplare der installierten Anleitung sind bytegleich.

Der vollständige Repositorylauf mit `.venv/bin/python -m pytest -q` besteht mit
**1859 bestandenen Tests, 14 Skips und sechs bestehenden IPC-Warnungen** in
474,06 Sekunden. Zwei Skips sind die neuen bewusst gesperrten echten
Agenteneinstiegstests. Dieser Lauf begann vor den letzten ergänzten Gegenproben;
diese sind vollständig im abschließenden gezielten Lauf enthalten.

`uv build --offline` erzeugt Source-Archiv und Wheel einschließlich der
Messbetriebsmodule und Anleitung. Der Wheel-Harness prüft die Installation
außerhalb des Checkouts einschließlich der vier neuen Messbetriebscases.
Alle **64 Wheel-Prüfungen** bestehen: 22 Core-, 22 Linter-, acht bisherige
Benchmark-, fünf eigene-Agenten-, drei Basisdatensatz- und vier
Messbetriebsprüfungen. Der neue Wheel-Hash wird sowohl im eingefrorenen Bundle
als auch im Ergebnisarchiv gegen das tatsächlich installierte Artefakt geprüft.
Der ergänzende gesamte Benchmark-/Styleguide-/Linterlauf besteht mit
**560 Tests und drei Skips**; die danach ergänzten drei Gegenproben sind im
oben genannten abschließenden Lauf mit 118 bestandenen Tests enthalten.
Die Dokumentation beschreibt die ursprüngliche Rotphase und die nun
implementierten Produktfunktionen getrennt. Reale Modellmessungen und die
unabhängige Aufnahme der Referenzen werden durch diese Prüfungen nicht behauptet.
