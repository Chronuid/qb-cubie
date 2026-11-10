# EBT-Cases zu Phase 10.3: Eigene Agenten und Szenarien

Stand: **10. November 2026, öffentliche Prozessanbindung implementiert.**
Diese Cases konkretisieren Phase 3 aus
[BENCHMARK_KONZEPT.md](../docs/BENCHMARK_KONZEPT.md#103-eigene-agenten-und-szenarien).
Sie ergänzen die Verträge aus [10.1](BENCHMARK_CASES_10_1.md) und
[10.2](BENCHMARK_CASES_10_2.md). Die ursprüngliche Rotphase ist unten dokumentiert.
Alle ursprünglichen Cases bleiben reguläre Prüfungen ohne `xfail` oder Skips.
Sie benötigen weder Modellzugriff noch einen
zweiten Agenten oder den Cubie-/pytest-Produktvergleich.

## Kriterienzuordnung

| Lieferung / Abnahmekriterium | Cases | Beobachtbarer Sollvertrag |
| --- | --- | --- |
| Prozessadapter | [test_process_adapter.py](benchmarks/phase3/test_process_adapter.py) | Ein echtes externes Programm empfängt JSONL, liest sichtbares Material und reicht gehashte Artefakte ein. Ein eigener Agent bewertet beide Review-Varianten in der Cubie-Bedingung. Der unabhängige Evaluator erkennt eine konstante Freigabe als Fehler. |
| Fähigkeiten und Konfigurationsfehler | [test_authoring.py](benchmarks/phase3/test_authoring.py), [test_process_adapter.py](benchmarks/phase3/test_process_adapter.py) | Tatsächlicher Fähigkeitenaustausch statt Vertrauen auf TOML-Angaben. Falsche Protokollversion und fehlende Fähigkeiten verhindern Aufgabenstart und Laufartefakte. Ein Review-Agent ohne Phasenabgabe wird nicht für Entwicklung eingeplant. |
| Agentenvorlage | [test_authoring.py](benchmarks/phase3/test_authoring.py) | `init-agent` liefert bearbeitbare Prozesskonfiguration; `validate-agent` prüft den realen Peer ohne Szenarioausführung. Bestehende Dateien werden nicht überschrieben. |
| Tutorial aus installiertem Wheel | [benchmark_custom_installed.py](wheel/benchmark_custom_installed.py) | Agent initialisieren und konfigurieren, Verbindung prüfen, externes Paket validieren und entdecken, Set anlegen, planen, zweimal ausführen, gespeicherte Läufe vergleichen. Nur installierte öffentliche API und CLI, externes Arbeitsverzeichnis, kein Checkout. Die CLI-Hilfe verweist auf `GUIDE_Benchmark-Custom`; `guide` zeigt die installierte Anleitung. |
| Externes Beispielpaket | [fixtures/phase3](benchmarks/fixtures/phase3/package.json), [test_external_packages.py](benchmarks/phase3/test_external_packages.py) | Eigener Namespace, neue Fachdomäne, MIT-Lizenz, Quellen und getrennte Referenzen. Bestehende Evaluatoren genügen; keine Registrierung und keine Core-Änderung. Verschieben und Aufruf aus anderem Arbeitsverzeichnis funktionieren. |
| Szenariovorlagen und Referenzprüfung | [test_authoring.py](benchmarks/phase3/test_authoring.py) | Vollständige Vorlagen für Review und Entwicklung. Strukturelle Validierung führt keinen Szenariocode aus; ausdrücklich eingeschaltete Referenzprüfung akzeptiert die Lösung und erkennt den Mutanten. Fehlerhafte Lösung und wirkungsloser Mutant verhindern Validierung. |
| Typ-/Tagfilter | [test_external_packages.py](benchmarks/phase3/test_external_packages.py) | Freie Typen wie `shop/shipping`, kombinierte Filter und Ausschlüsse, untypisierter Fall, keine doppelten Versuche bei mehreren Typen. Bestehendes und eigenes Paket passen in denselben Plan. Unbekannte Auswahl und fehlende Vorgänger scheitern vor Prozessstart. |
| CLI/API-Gleichheit | [test_authoring.py](benchmarks/phase3/test_authoring.py), [test_comparison.py](benchmarks/phase3/test_comparison.py) | Externe Pläne und Vergleiche sind in CLI-JSON und Python identisch. Initialisierung und Planung starten den Agenten nicht. |
| Kontrollierte Entwicklerphasen | [test_process_adapter.py](benchmarks/phase3/test_process_adapter.py) | Dieselbe Sitzung innerhalb einer Episode, frische Sitzung je Versuch. Runner beobachtet fachliches Rot, Grün und Refactoring mit eingefrorenen Tests. Vorzeitige Implementierung, Importfehler und nachträglich geänderte Tests erfüllen den Prozess nicht. |
| Fehler und Nachweise | [test_process_adapter.py](benchmarks/phase3/test_process_adapter.py) | Ungültiges JSON, fremde IDs/Phasen, falsche Hashes, fehlende oder ausbrechende Artefakte, fehlende Quellenbelege und geänderte Quellen/Aufträge ergeben keinen Erfolg. Absturz, EOF und echter Timeout bleiben unterscheidbar. JSONL und stderr werden archiviert. Unbekannte Nutzung bleibt `null`. |
| Laufvergleich | [test_comparison.py](benchmarks/phase3/test_comparison.py) | Vergleich archivierter Läufe verschiedener Agentenkonfigurationen; Aufgaben-, Paket-, Bedingungs- und Budgetbindung; sichtbarer Teilvergleich bei geänderter Auswahl; kein Vergleich ungleicher Bedingungen. Mehrfachtypen vervielfachen keine Paare. Rückgang des Recalls und undefinierte Präzision bleiben erkennbar. |
| Unabhängige Gegenproben | [test_fixture_peer.py](benchmarks/phase3/test_fixture_peer.py), [test_external_packages.py](benchmarks/phase3/test_external_packages.py) | JSONL-Peer erfüllt bestehende Nachrichtenverträge. Direkte Funktionsaufrufe und ein separater pytest-Prozess unterscheiden korrekte Lösung, Grenzmutant und Stub ohne neue Runner-Funktionen. |

## Neues externes Material

Das Beispielpaket `shop`, Version `1.0.0`, beschreibt Versandkosten in
ganzzahligen Centbeträgen: Ab einschließlich 5000 Cent ist der Versand
kostenlos; darunter kostet er 499 Cent.

| Szenario | Ausgangsstand und Abnahme |
| --- | --- |
| `shop/review-correct` | `shipping.is_free` verwendet `>= 5000`; Kriterium `free_threshold` erfüllt. Ohne Typen und Tags. |
| `shop/review-boundary` | `> 5000` verletzt die Grenze. Gegenbeispiel: 5000 Cent, erwartet `true`, tatsächlich `false`. Typen `correctness`, `shop/shipping`; Tags `shipping`, `boundary`. |
| `shop/fee-initial` | `shipping.fee` liefert zunächst `-1`. Testentwurf, Rot, Implementierung und Refactoring sollen die geforderten Rückgaben erreichen. Die Referenz besteht auch bei 0, 4999, 5001 und 9000 Cent; der Grenzmutant scheitert bei 5000. |

Die unabhängige Projektabnahme verwendet direkte pytest-Assertions. Die vom
Testagenten eingereichten Tests führen EBT tatsächlich aus und prüfen dessen
Auswertung. Prozesskonformität und fachliche Ergebnisqualität bleiben getrennte
Dimensionen; ein korrektes Endergebnis allein belegt keine gültige Rotphase.

Alle Referenzen bleiben `author_checked` mit leerer Liste `human_reviews`.
Die automatischen Gegenproben ersetzen keine menschliche Aufnahmeprüfung.
Das Paket ist ein öffentliches Entwicklungsbeispiel, kein zurückgehaltener
Messdatensatz und kein Nachweis einer Agentenleistung.

## Öffentliche Schnittstellen

Die folgenden Funktionen werden aus `qb_cubie.benchmarks` importiert.
Pfadargumente akzeptieren `Path` und `str`, Ergebnisse sind JSON-kompatibel.
Ungültige Konfiguration und fehlgeschlagene Validierung führen zu `ValueError`
mit betroffenen Feldern bzw. IDs. Laufprobleme nach erfolgreicher Vorprüfung
stehen im Ergebnis von `run_suite`.

| Funktion | Sollvertrag |
| --- | --- |
| `init_agent(path)` | Erzeugt Elternverzeichnisse und TOML-Prozessvorlage mit `schema_version=1`, `id`, `transport="jsonl-v1"`, `command` als Argumentliste und `capabilities`. Rückgabe: `agent` als absoluter Pfad. Kein Agentenstart; kein Überschreiben. |
| `validate_agent(path)` | Startet den konfigurierten Prozess ausschließlich für den Fähigkeitenaustausch. Rückgabe enthält `schema_version=1`, `valid=true`, `agent_id`, `agent_version`, tatsächlich bestätigte `capabilities`. Nicht bestätigte deklarierte Fähigkeiten und fremde Versionen sind Fehler. |
| `init_scenario(path, benchmark)` | Erstellt ein eigenständiges Paket mit genau einem Szenario für `review_agent` oder `developer_agent`, sichtbarem Auftrag, Ausgangsmodul und passender Referenz. `package` enthält den absoluten Paketpfad. Vorhandenes Material bleibt erhalten. |
| `validate_package(path, check_references=False)` | Prüft strukturell ohne Codeausführung. Rückgabe enthält `schema_version=1`, `valid=true`, `references_checked=false`. Mit `check_references=True` werden ausführbare Referenzen und Mutanten unabhängig geprüft; Rückgabe enthält `scenarios` mit `scenario_id` und Validierungsstand. Für das Entwicklerbeispiel: `reference_passed=true`, `mutants=[{"id":"wrong-return","detected":true,"criterion_results":{"fee":"fail"}}]`. |
| `compare_runs(before, after)` | Liest zwei archivierte Laufverzeichnisse ohne erneute Ausführung. Liefert `schema_version=1`, `scope`, `warnings`, `pairs`. Originaldateien bleiben bytegleich. Der Vergleich funktioniert nach Entfernen der ursprünglichen Set- und Agentenkonfiguration. |

Für Review-Referenzen ohne ausführbaren Prüfvertrag darf die Referenzvalidierung
keine erfolgreiche fachliche Ausführung erfinden. Struktur, Kriterienabdeckung
und hinterlegte Gegenbeispiele bleiben prüfbar. Die Cases verlangen den
ausführbaren Lösungs-/Mutantennachweis konkret für das Entwicklerbeispiel.

Ergänzende CLI-Verträge:

```text
cubie-bench init-agent PATH
cubie-bench validate-agent PATH
cubie-bench init-scenario --benchmark {review_agent,developer_agent} PATH
cubie-bench validate PACKAGE [--check-references]
cubie-bench list --package PACKAGE
cubie-bench init-suite PATH --preset smoke --agent AGENT --package PACKAGE
cubie-bench compare BEFORE AFTER
```

Alle Kommandos unterstützen `--format json`. `list` liefert `namespace`,
`scenarios` mit qualifizierten IDs und normalisierten Typen/Tags sowie deren
verfügbare Vereinigungen `types` und `tags`. Der Aufruf startet keinen Code.
`init-suite` mit explizitem Agent und Paket erzeugt ein Set mit einer
Wiederholung, Profil `agent-evaluation` und genau dieser Agentenkonfiguration.
Das vorhandene `init-suite --preset smoke --fake` bleibt gültig.
Die Exitcodes aus 10.2 bleiben bestehen.

## JSONL-Prozessvertrag für die Cases

Der Testpeer [jsonl_agent.py.txt](benchmarks/fixtures/phase3/agents/jsonl_agent.py.txt)
verwendet ausschließlich die Standardbibliothek. Der Testaufbau exportiert ihn
als `jsonl_agent.py`; er importiert keine Cubie-Interna und liest keine
Evaluatorreferenzen. Nur seine eingereichten Entwicklertests importieren die
öffentliche EBT-API.

`command` ist eine Argumentliste ohne Shell. `cwd` wird relativ zur ursprünglichen
Agentenkonfiguration aufgelöst; `cwd="."` erlaubt relative Skriptpfade auch aus
einem fremden Arbeitsverzeichnis. Die Argumente bleiben unverändert, damit
Leerzeichen funktionieren. Die archivierte Konfiguration darf diese Basis
nicht versehentlich in den Ergebnisordner verschieben.

Transport: UTF-8, ein JSON-Objekt je Zeile, stdout ausschließlich für das
Protokoll, stderr für Diagnose. Der Runner sendet zuerst:

```json
{"schema_version": 1, "type": "capabilities"}
```

Die Antwort enthält `type="capabilities"`, `schema_version=1`, `agent_id`,
`agent_version` und `capabilities`. Deklarierte und für den Plan erforderliche
Fähigkeiten müssen tatsächlich bestätigt sein. Handshake und Abbruch müssen
zeitlich begrenzt sein. Eine fehlgeschlagene Vorprüfung sendet keine Aufgabe
und erzeugt kein scheinbar begonnenes Ergebnisarchiv.

Aufgaben verwenden `type="request"` und den bestehenden
`validate_agent_request`-Vertrag: IDs, Benchmark, Phase, Auftrag, absoluter
Workspace, Kriterien, Ausgabeformat und Budgets. Antworten verwenden
`type="event"` mit den Feldern aus `validate_agent_event`, zusätzlich
`artifact_hashes`. Der Runner prüft Bindung an Lauf, Szenario und Phase sowie
Existenz, relativen Pfad und Hash jedes Artefakts selbst. Eine `completed`-Meldung
ersetzt keine fachliche Prüfung.

Reviews schreiben `review.json` mit `criterion_results`, `findings` und `sources`
im bestehenden Format `review_v1`. Entwickler reichen Tests, Produktionsmodul
und kurze Nutzungserklärung ein. Der Runner fordert die vier Phasen
`test_design → red → green → refactor` in derselben Sitzung an, friert Tests ein
und führt Prüfungen selbst aus. Jeder weitere Versuch beginnt mit einer neuen
Sitzung. Unbekannte Modellkennung und Token-/Kostenwerte bleiben `null`;
`agent_kind="process"` und die bestätigte Agentenversion kennzeichnen den Lauf.

Ungültige Nutzlast, EOF ohne Abgabe, fehlende Quellenbelege, veränderte
Review-Quellen/Aufträge und unzulässige Artefakte ergeben `invalid_output`.
Ein nicht erfolgreicher Prozessabschluss ergibt `infrastructure_error`;
ein tatsächlich blockierender Prozess `agent_timeout`. Der Timeout-Case hat
zusätzlich eine äußere 12-Sekunden-Grenze und prüft unter POSIX, dass der
gestartete Peer anschließend nicht mehr lebt. Bei unbrauchbarer Abgabe bleiben
`criterion_results` leer, `evaluation_status="not_evaluated"` und
`quality_passed=false`. Unbekannte Qualitätsmetriken sind `null`.

Rohe JSONL-Nachrichten und stderr-Diagnosen werden als `.jsonl` bzw. `.log`
archiviert und durch die bestehenden Artefakthashes abgedeckt. Sichtbar sind
nur Auftrag und exportierter Code; keine Referenzverzeichnisse oder Lösungen.
Ein gesetztes Test-Zugangsdatenmerkmal wird weder an den Prozess vererbt noch
im Archiv abgelegt. Das ist eine Prüfung der Export- und Umgebungsgrenze,
kein Nachweis einer OS-Sandbox. Containerisolation und Ausführung unvertrauten
Codes bleiben gesonderte Infrastrukturarbeit aus Abschnitt 7.3.

## Vergleichssemantik

`scope` ist `full`, `partial` oder `incompatible`. Ein Paar enthält mindestens
`scenario_id`, `condition`, `repetition`, `before`, `after` und `metric_deltas`.
Beide Seiten erhalten Agentenkennung, Ausführungs-/Bewertungsstatus und
`quality_passed`. `metric_deltas` bildet Metriknamen auf `after - before` ab;
ein undefinierter oder nicht bewertbarer Wert erzeugt `null`, niemals null
Punkte oder einen erfundenen Fortschritt.

Paarung erfolgt nach aufgelöster Aufgabe einschließlich Paketversion/-hash und
Evaluator, Bedingung, Wiederholung und Budgets. Die Agentenkennung darf sich
unterscheiden, damit zwei Versionen eines Agentensystems vergleichbar sind.
Typen und Tags vervielfachen keine Paare. Ein anderer Set-Name allein verändert
das Experiment nicht. Derselbe Name verbirgt keine geänderten Budgets oder
Materialien. Bei geändertem Paketinhalt ist ohne gesonderten
Kompatibilitätsnachweis keine Gleichheit zugesichert.

Eine geänderte Auswahl oder zusätzliche Vergleichsbedingung führt zu
`partial` mit Warnung; nur gemeinsame kompatible Versuche erscheinen als Paare.
Ohne kompatible Versuche gilt `incompatible`, ebenfalls mit Warnung.
Abgebrochene Versuche bleiben sichtbar, ihre Qualitätsdifferenzen bleiben
undefiniert. Ein fremder `run_id` gegenüber dem Laufmanifest ist ein
Validierungsfehler. Der lesbare CLI-Bericht benennt den Teilvergleich und
die verglichenen Szenarien ausdrücklich.

## Ausführung und Ausgangsstand

```bash
.venv/bin/python -m pytest -q tests/benchmarks/phase3
.venv/bin/python -m pytest -q tests/benchmarks --ignore=tests/benchmarks/phase3
.venv/bin/python -m ruff check tests/benchmarks/phase3 tests/wheel/benchmark_custom_installed.py scripts/check_wheel.py
```

Der [Wheel-Harness](../scripts/check_wheel.py) kopiert das Beispielpaket aus dem
Repository in seine externe Testumgebung und führt zusätzlich
`benchmark_custom_installed.py` aus. Die ursprünglichen vier Wheel-Cases sowie
ein ergänzender Export-/Tutorialcase prüfen die implementierten CLI-Kommandos.

Historischer Ausgangsstand vor Implementierung am 10. November 2026:

| Neue Gruppe | Bestanden | Fehlgeschlagen |
| --- | ---: | ---: |
| Authoring und CLI | 1 | 15 |
| Laufvergleich | 1 | 13 |
| Externe Pakete und Filter | 22 | 0 |
| Unabhängige Referenz-/Peerprüfung | 5 | 0 |
| Prozessadapter | 1 | 24 |
| **Repository-Cases gesamt** | **30** | **52** |
| Neue Wheel-Cases | 0 | 4 |

Alle **86 neuen Cases** werden gesammelt und ausgeführt, ohne Setup-/Sammlungsfehler
oder Skips. 25 Repository-Cases scheitern an noch fehlenden öffentlichen
Funktionen, sechs an den fehlenden CLI-Kommandos bzw. Hilfetexten und 21 an
der bisherigen Beschränkung auf `builtin:fake`. Die vier neuen Wheel-Cases
scheitern ebenfalls an den fehlenden CLI-Kommandos. Diese roten Cases an
fehlenden Einstiegspunkten spezifizieren noch keine beobachteten Einzeldefekte
einer späteren Implementierung.

Die komplementäre Benchmark-Regression ohne `phase3` ergibt **276 bestanden**.
Ein offline neu gebautes Wheel wurde in eine frische venv außerhalb des
Checkouts installiert; die acht bisherigen Wheel-Benchmark-Cases bestehen,
die vier neuen sind wie beschrieben rot. Hierfür wurden die beiden
Benchmark-Installationsdateien separat in einer externen Umgebung ausgeführt;
ein vollständiger Durchlauf der Core-/Linter-Profile des Wheel-Harness war
nicht Bestandteil dieser Prüfung.

Die vollständige Repository-Sammlung umfasst **1695 Tests** ohne Sammlungsfehler.
Ruff für die neuen Python-Dateien und den angepassten Wheel-Harness sowie
`git diff --check` bestehen. Die vollständige übrige Repository-Suite wurde
für diesen Testentwurf nicht erneut ausgeführt.

## Implementierter Umfang und ergänzende Gegenproben

Die öffentlichen Funktionen, CLI-Kommandos und der JSONL-Prozessadapter sind
implementiert. `init_example` bzw. `cubie-bench init-example` exportiert ein
eigenständiges Paket aus dem Wheel ohne Repository-Fixtures. `cubie-bench guide`
zeigt das mitgelieferte [Tutorial](../docs/GUIDE_Benchmark-Custom.md).
Der Prozess wird vor der unabhängigen Schlussbewertung beendet; ein Absturz
nach gültiger Abgabe bleibt ein Infrastrukturfehler. Rohe Nachrichten und
Diagnosen werden archiviert, Sitzungen bei Fehlern und Timeouts aufgeräumt.

Die neun [zusätzlichen Grenzprüfungen](benchmarks/phase3/test_boundaries.py)
prüfen den installierbaren Export und die Anleitung, frühe Ablehnung harter
Kostenlimits, nachträglichen Prozessabsturz, verschiebbare Konfiguration,
wiederholte Kommandoargumente und den Ausschluss generierter Python-/pytest-
Caches aus Paketidentität und Agentenexport. Die Referenzvalidierung erkennt
auch eine fehlende Ausgabedatei als fachlichen Mutantenfehler, ohne Import-,
Fixture- oder übersprungene Prüfungen als Gegenbeispiel zu akzeptieren.

Damit umfasst Phase 10.3 **91 Repository-Cases und fünf Wheel-Cases**.
Ein Szenario mit mehreren Typen erzeugt weiterhin nur einen Versuch.
Mehrdeutige Vergleiche von Multi-Agenten-Archiven benötigen eine explizite
Auswahl mit `before_agent`/`after_agent` bzw. den entsprechenden CLI-Optionen.
Vergleiche prüfen archivierte Bytes, Plan und Evaluatorversion; unbekannte
oder unvollständige Metriken bleiben undefiniert.

Die lokale Ausführung setzt weiterhin vertrauenswürdige Agenten, Szenarien
und Evaluatoren voraus. Werkzeugbudgets begrenzen Runner-Aufrufe und messen
keine internen Werkzeugaufrufe externer Dienste. Containerisolation,
allgemeines semantisches Review-Matching und reale Agentenmessungen sind
dadurch nicht implementiert. Die Referenzen bleiben `author_checked`.

Abschließender gezielter Lauf mit sämtlichen Benchmark-Cases, Styleguide,
Ruff, Mypy und Pylint:

```text
389 passed, 1 skipped in 58.04s
```

Enthalten sind **367 bestandene Benchmark-Cases**: 276 bisherige und alle
91 aus Phase 10.3. Der Skip ist die bereits ausgesetzte Modulgrößenprüfung.
Die ursprünglichen Abnahme-Cases bestehen ohne Abschwächung.

`uv build --offline` erzeugt Source-Archiv und Wheel. Der vollständige
`scripts/check_wheel.py`-Lauf gegen dieses Wheel besteht außerhalb des Checkouts:

| Installiertes Profil | Bestanden |
| --- | ---: |
| Core | 22 |
| Linters | 22 |
| Benchmarks, bestehender Durchstich | 8 |
| Benchmarks, eigene Agenten/Szenarien | 5 |

Alle **57 Wheel-Prüfungen** bestehen. Das Wheel enthält den Tutorialtext und
das eigenständig exportierbare Paket; die geprüften Paketdateien stimmen mit
dem abschließenden Quellstand überein. Die vollständige Sammlung des aktuellen
Repositories umfasst **1704 Tests** ohne Sammlungsfehler.

Der vollständige Repository-Regressionslauf ergibt:

```text
1689 passed, 12 skipped, 6 warnings in 380.76s (0:06:20)
```

Dieser Lauf wurde vor den letzten drei ergänzten Grenzprüfungen gestartet.
Diese Prüfungen für fehlende Ausgabedateien, generierte Caches und wiederholte
Argumente sind im abschließenden gezielten Lauf mit 389 bestandenen Tests
enthalten. Die Skips und Warnungen stammen aus bestehenden Tests.
Ruff für sämtliche ergänzten Python-Dateien und `git diff --check` bestehen.

## Ergänzung: Regressionen aus dem Nutzungsexperiment

Die Cases in
[test_experiment_regressions.py](benchmarks/phase3/test_experiment_regressions.py)
konkretisieren die priorisierten Befunde aus
[EXPERIMENT_Benchmark-10-3.md](../docs/EXPERIMENT_Benchmark-10-3.md).
Die Abnahme wurde zunächst mit bewusst sichtbarer Rotphase ergänzt.
Die nachfolgende Produktkorrektur ist unten dokumentiert; die archivierten
Ollama-Belege bleiben unverändert.
Keine `xfail`-Marker, Skips, Modellaufrufe oder Netzwerkabhängigkeiten.

Der vorhandene externe JSONL-Peer reicht im temporären Paket neue Testentwürfe
ein. Der sichtbare Versandkostenvertrag und die unabhängige Referenzabnahme
werden dort um `ValueError` bei negativen Beträgen ergänzt. Damit sind die
Exceptiontests fachlich begründet. Die Referenzlösung erfüllt auch diesen
Zusatzvertrag. Die EBT-Hülle prüft `run_suite` über die öffentliche API;
die eingereichten Tests laufen tatsächlich als separate pytest-Prozesse.

| Kriterium des Experiments | Neue Cases / Sollverhalten |
| --- | --- |
| Fehlende erwartete Exception ist fachliches Rot | `test_missing_expected_exception_is_business_red`: einmal ausschließlich `pytest.raises`, einmal zusammen mit einer EBT-Assertion. JUnit belegt `DID NOT RAISE`; Rot zählt als `assertion_failure`, Grün und Refactoring bestehen bei identischem eingefrorenem Testbaum; Qualität und Prozess bestehen. |
| Echte Fehler dürfen durch fachliches Rot nicht verdeckt werden | `test_real_test_errors_override_business_failures`: Laufzeitfehler und Fixture-Setupfehler neben fachlichen Fehlern bleiben `test_error`; Syntax- und Importfehler bleiben `import_error`. Ein Laufzeitfehler enthält absichtlich die Texte `AssertionError` und `DID NOT RAISE`, um eine bloße Teilstringsuche als Fehlklassifikation aufzudecken. |
| Falsche Agentenorakel bleiben Prozessfehler | `test_wrong_agent_oracle_stays_a_process_failure_despite_correct_product`: fachlich korrekte Produktion besteht die unabhängige Abnahme, falscher Agententest bleibt in Grün und Refactoring rot; `process_passed=false`. |
| Bericht trennt Qualität und Prozess sichtbar | `test_report_names_quality_and_process_separately`: Markdown nennt `quality_passed: true` und ausdrücklich `process_passed: false`. |
| `full` bedeutet vergleichbar, nicht erfolgreich | `test_text_comparison_exposes_status_quality_and_process`: zwei vollständig vergleichbare Entwicklerläufe mit gleichem Qualitäts-, aber unterschiedlichem Prozessurteil. CLI zeigt Status, Qualität und Prozess statt ausschließlich leerer Metrikdifferenzen. |
| Exitcode 0 ist kein Prozessabnahmenachweis | `test_cli_exit_zero_does_not_hide_process_failure`: abgeschlossener Lauf mit Prozessfehler behält Exitcode 0 und zeigt beide Ergebnisfelder ausdrücklich an. |

Reproduktion:

```bash
.venv/bin/python -m pytest tests/benchmarks/phase3/test_experiment_regressions.py -q
```

Das lokale Modell-Tutorial sowie die Sicherung von Modell-Digest,
Provider-/Adapterversion und Aufrufparametern bleiben nachgelagerte Arbeit.
Diese deterministischen Cases behaupten weder einen realen Modellaufruf noch
Reproduzierbarkeit identischer Modellantworten. Die vorhandenen Fähigkeits-,
Filter-, Referenzvalidierungs- und Wheel-Cases gelten weiterhin.

Erste Ausführung am 10. November 2026: **6 bestanden, 4 fehlgeschlagen**.
Die beiden Exception-Cases erhalten noch `test_error` statt `assertion_failure`.
Im Markdown fehlt das explizite Prozessfeld; der Textvergleich zeigt weiterhin
nur `{}`. Alle sechs Gegenproben bestehen. Die bisherigen Prozessadapter- und
Vergleichscases bestehen unverändert (**39 bestanden**). Ruff meldet für das
neue Testmodul keine Befunde.

Nach der Produktkorrektur am 10. November 2026 bestehen **alle zehn neuen
Cases**. Die Klassifikation prüft den abschließenden pytest-Fehlertyp statt
beliebiger Vorkommen von `AssertionError` im Traceback. Fehlende erwartete
Exceptions werden als fachliches Rot akzeptiert; andere Testfehler behalten
Vorrang. Bericht und Textvergleich zeigen das Prozessurteil ausdrücklich.

Abschließende Prüfung mit
`pytest tests/benchmarks tests/test_styleguide.py -q`: **390 bestanden,
1 bestehender Skip** (temporär ausgesetzte Modulgrößenregel).
Ruff für den Benchmark-Produktcode und das neue Testmodul sowie
`git diff --check` sind ohne Befund.
