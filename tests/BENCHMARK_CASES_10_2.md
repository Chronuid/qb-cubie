# EBT-Cases zu Phase 10.2: Installierbarer Durchstich ohne Modell

Stand: **10. November 2026, öffentlicher Offline-Durchstich implementiert.**
Diese Cases konkretisieren Phase 2 aus
[BENCHMARK_KONZEPT.md, Abschnitt 10](../docs/BENCHMARK_KONZEPT.md#102-installierbarer-durchstich-ohne-modell).
CLI, Fake-Adapter, Phasensteuerung, unabhängige Evaluatoren und Ergebnisarchiv sind implementiert.
Die bestehenden [Phase-10.1-Verträge](BENCHMARK_CASES_10_1.md) bleiben gültig.

## Kriterienzuordnung

| Lieferung / Abnahmekriterium | Cases | Beobachtbare Verpflichtung |
| --- | --- | --- |
| CLI und installierbares Extra | [benchmark_installed.py](wheel/benchmark_installed.py) | `benchmarks` ist in den Distributionsmetadaten deklariert; `cubie-bench` ist ein ausführbarer Entry Point. Hilfe nennt Initialisierung, Planung und Ausführung. |
| Smoke-Set aus Wheel ohne Checkout | [benchmark_installed.py](wheel/benchmark_installed.py) | Frische venv, installierte Module unter `sys.prefix`, externer Arbeitsordner, keine Root-conftest oder Quellpfade. Ein Agent und eine Wiederholung decken Review und Entwicklung ab. |
| Vorlagen | [test_execution.py](benchmarks/phase2/test_execution.py), [benchmark_installed.py](wheel/benchmark_installed.py) | Initialisierung erzeugt ein eigenständiges, verschiebbares Set mit Paket und Fake-Konfiguration; vorhandene Dateien werden nicht überschrieben. Leerzeichen und ein anderes Arbeitsverzeichnis funktionieren. |
| Derselbe Planner | [test_results.py](benchmarks/phase2/test_results.py), [benchmark_installed.py](wheel/benchmark_installed.py) | Python-API, CLI-JSON und archivierter Laufplan stimmen überein. Unbekannte Szenario-IDs verhindern den Start und erzeugen keine Laufartefakte. |
| Fake-Adapter ohne Modell | [test_execution.py](benchmarks/phase2/test_execution.py), [test_results.py](benchmarks/phase2/test_results.py) | Referenzläufe funktionieren ohne Provider-Schlüssel und bei blockierten Socketverbindungen im Testprozess. Nutzung und Modellkennung bleiben unbekannt statt erfunden. |
| Korrekte Lösung besteht, falsche fällt durch | [test_execution.py](benchmarks/phase2/test_execution.py) | Unabhängiger Evaluator akzeptiert Referenzlösungen und lehnt falsche Rückgabe, fehlende/beschädigte Kopie, zusätzliche Datei und falsche Sortierung am jeweiligen Kriterium ab. |
| Review-Auswertung | [test_execution.py](benchmarks/phase2/test_execution.py) | Konformer und fehlerhafter Review-Fall unterscheiden konstante Freigabe, konstante Ablehnung und Enthaltung. Doppelte Findings erhöhen Recall nicht über eins. |
| Phasensteuerung | [test_execution.py](benchmarks/phase2/test_execution.py) | `test_design → red → green → refactor`; beobachteter Assertion-Fehlschlag, danach erfolgreiche Tests; identischer Testbaum in allen Phasen. Fehlende Rotphase, Importfehler, rote Grünphase und geänderte Tests erfüllen den Prozess nicht. |
| Fehlende oder fremde Belege | [test_execution.py](benchmarks/phase2/test_execution.py) | Fehlende Datei, fehlende Quellenbelege, fremde Laufkennung, falscher Artefakthash und veränderter Review-Kontext ergeben `invalid_output`, niemals einen Erfolg. |
| Timeouts und Infrastrukturfehler | [test_execution.py](benchmarks/phase2/test_execution.py) | Selbst gemeldeter Timeout, tatsächlich blockierender Fake und Absturz bleiben unterscheidbar. Der Hängefall wird zusätzlich durch einen äußeren 15-Sekunden-Prozess-Timeout begrenzt. |
| Ergebnisdateien und Nachprüfbarkeit | [test_results.py](benchmarks/phase2/test_results.py) | JSON entspricht der API-Rückgabe; Markdown nennt Kriterium und existierende Belegdateien; SHA-256 stimmt mit archivierten Bytes überein. Eingaben, Quell-/Kontextkennung und Plan bleiben erhalten. |
| Frische Versuche | [test_execution.py](benchmarks/phase2/test_execution.py) | Wiederholte Aufrufe haben verschiedene Laufkennungen, Ausgabeverzeichnisse und Workspaces; der erste Bericht bleibt bytegleich erhalten. |
| CLI-Ergebnissemantik | [benchmark_installed.py](wheel/benchmark_installed.py) | Konfigurationsfehler: Exitcode 2; abgebrochene Ausführung: 3; vollständig durchgeführte Messung ohne Qualitätsgate: 0, auch wenn die Lösung fachlich durchfällt. |

Die neuen Cases verwenden EBT mit `WorldState` und deaktiviertem Reporter für
öffentliche Aufrufe bzw. CLI-Prozesse. Die EBT-Auswertung wird ausdrücklich
geprüft; zusätzliche pytest-Assertions kontrollieren Kriterien, Phasen und
persistierte Dateien. Erwartete Konfigurationsfehler verwenden den bestehenden
`ExceptionExpectation`-Helper. Ein fachlich gescheiterter Benchmark-Versuch ist
ein erfolgreich beobachtetes Negativbeispiel; sein Bericht muss ausdrücklich
`quality_passed = false` enthalten. Es gibt kein `expect=False`, `xfail` oder
Überspringen bei fehlender Implementierung.

## Öffentlicher Vertrag für Phase 2

Diese Schnittstellen sind im installierbaren Produktpaket implementiert. Die Funktionen werden aus `qb_cubie.benchmarks`
importiert und ergänzen die vorhandene API:

| Funktion | Vertrag |
| --- | --- |
| `init_smoke_suite(path: str \| Path) -> dict` | Erzeugt die TOML-Set-Datei am angegebenen Pfad einschließlich Elternverzeichnissen, Fake-Agentenkonfiguration und lokalem Szenariopaket. Rückgabe enthält `suite` als absoluten Pfad. Vorhandene Zieldateien führen zu `ValueError` mit `exist` oder `overwrite` in der Meldung. |
| `run_suite(path: str \| Path) -> dict` | Verwendet `plan_suite`, führt die Versuchseinheiten mit dem konfigurierten Adapter aus und schreibt Ergebnisse unter `<plan.output>/<run_id>/`. Konfigurationsfehler führen vor Ausführungsbeginn zu `ValueError`; Laufprobleme stehen im Ergebnis. |

Das Smoke-Paket übernimmt die fachlich geprüften Fälle aus Phase 10.1:
zwei Review-Varianten und den Dokumentindex. Mindestens die Erstentwicklung
ist enthalten. Weitere Episoden dürfen aufgenommen werden, sofern die
Voraussetzungen vollständig bleiben und die hier verwendeten fünf Mutanten
für jede enthaltene Entwicklerepisode vorhanden sind. Rückgabe, Dateibaum und
Kriterien richten sich nach den vorhandenen Referenzen; es wird keine zweite
fachliche Aufgabenbeschreibung erfunden. Der Referenzstand bleibt
`author_checked`; automatisches Bestehen ist keine menschliche Aufnahmefreigabe.

Die Vorlage verwendet eine Agentenkonfiguration nach dem vorhandenen Schema:
`schema_version = 1`, `id`, `command`, `capabilities`. Für den eingebauten Fake
ist die Kommandoargumentliste `["builtin:fake"]` reserviert; sie startet kein
externes Programm. Der eigentliche Prozessadapter gehört weiterhin zu Phase 3.
Das Set besitzt explizite `[budgets]`, insbesondere `wall_time_seconds`, eine
Wiederholung und Profil `agent-evaluation`; es benötigt kein Qualitätsgate.
Quell-, Agenten- und Ausgabepfade sind relativ zum Set und bleiben nach einem
Umzug des erzeugten Verzeichnisses gültig.

```bash
python -m pip install 'qb-cubie[benchmarks]'
cubie-bench init-suite ./sets/smoke.toml --preset smoke --fake
cubie-bench plan --suite ./sets/smoke.toml --format json
cubie-bench run --suite ./sets/smoke.toml
```

`--fake` ist eine ausdrückliche Wahl des deterministischen Referenzadapters.
Der Aufruf behauptet keine Agentenleistung. Ohne Qualitätsgate bedeutet
Exitcode 0 ausschließlich, dass die Messung vollständig ausgeführt wurde.
Eine ungültige/unterbrochene Abgabe ist ein Laufproblem mit Exitcode 3;
ein Konfigurationsfehler hat Exitcode 2. Qualitätsgates bleiben Phase 5 vorbehalten.

## Deterministische Gegenproben des Fake-Adapters

Die Cases ändern ausschließlich den Abschnitt `[fake]` der erzeugten
Agentenkonfiguration. `behavior` bezeichnet einen kontrollierten Eingriff,
keine schon vorgegebene Runner-Bewertung. Der Runner muss die Folgen selbst
beobachten. Der Fake darf sein erwartetes Urteil nicht anstelle der
unabhängigen Bewertung liefern.

| `behavior` | Abgabe / Eingriff |
| --- | --- |
| `reference` | Korrekte Review-Antworten und Projektlösungen samt echten Testphasen. |
| `mutant` | Projektlösung durch die mit `mutant` benannte vorhandene Fehlervariante ersetzen. |
| `wrong_solution` | Mindestens eine fachlich falsche Projektlösung abgeben; CLI-Gegenprobe. |
| `approve_all`, `reject_all`, `abstain` | Konstante Review-Entscheidung für beide Review-Fälle. |
| `duplicate_findings` | Dasselbe belegte Finding mehrfach abgeben. |
| `missing_red` | Nur grüne Tests bzw. eine Behauptung ohne beobachtete Rotphase. |
| `red_import_error` | Rotphase scheitert am Import statt an der fachlichen Assertion. |
| `green_failure` | Nach Implementierungsabgabe scheitert weiterhin eine Assertion. |
| `modify_tests` | Nach dem eingefrorenen Testentwurf den Testbaum ändern. |
| `missing_artifact` | Eine nicht vorhandene Ergebnisdatei melden. |
| `missing_evidence` | Fachlich passende Review-Entscheidung ohne erforderliche Quellenbelege. |
| `foreign_run` | Artefakt/Ereignis einer fremden Laufkennung einreichen. |
| `tampered_artifact` | Artefaktinhalt passt nicht zum eingereichten Hash. |
| `mutate_context` | Sichtbaren Quellenkontext während des Reviews verändern. |
| `timeout` | Timeout als Adapterereignis melden. |
| `hang` | Tatsächlich über das Laufzeitbudget hinaus blockieren; nicht selbst `agent_timeout` zurückgeben. |
| `crash` | Adapterausführung mit Infrastrukturfehler abbrechen. |

Die private Fake-Provisionierung darf Referenzabgaben vorbereiten. Der
exportierte Agentenworkspace enthält ausschließlich Aufgabe, Kriterien,
sichtbaren Code und seine späteren Abgaben. Evaluatorverzeichnis und
`reference.json` dürfen dort nicht liegen. `.py.txt`-Material wird als
ausführbares `.py`-Modul exportiert. Das ist eine Prüfung der Exportgrenze,
kein Nachweis einer OS-Sandbox.

## Ergebnisse und Archive

Die API-Rückgabe ist JSON-kompatibel und enthält `schema_version = 1`,
`run_id`, absolutes `output` und `runs`. `results.json` enthält genau diese
Rückgabe. Jede Versuchseinheit übernimmt `scenario_id`, `agent_id`,
`condition`, `repetition` und `budgets` unverändert aus dem Plan.

Zusätzlich werden je Versuchseinheit geprüft:

- `benchmark`, `status`, `evaluation_status`, `criterion_results`, `metrics`,
  `evidence`, `quality_passed`;
- `agent_kind = "fake"`, `model_id = null`, `usage` mit `input_tokens`,
  `output_tokens`, `cost` jeweils `null` bei unbekannten Werten;
- absoluter, eigener `workspace` und `export_manifest` als relativer
  Archivpfad; das Exportmanifest enthält `task`, `criteria`, `files`;
- `source_tree_sha256`, `submitted_tree_sha256`, `task_sha256`,
  `context_sha256` als SHA-256-Kennungen;
- bei Entwicklerfällen `process_passed`, bei Prozessverletzung
  `process_reason`; `phases` mit `phase`, `test_outcome`, `test_tree_sha256`
  und `evidence`.

`test_outcome` unterscheidet mindestens `passed`, `assertion_failure` und
`import_error`. Die Grün-/Refactor-Prüfung verwendet die eingefrorenen Tests.
Der Hash über den logischen Testbaum bleibt deshalb in allen vier
Phaseneinträgen gleich. Eine behauptete Rotphase genügt nicht.

`quality_passed` beurteilt die Erfüllung der Benchmark-Aufgabe: Beim Review
kann eine korrekte Ablehnung fehlerhaften Codes bestehen, obwohl ein
Quellcode-Kriterium `fail` lautet. Bei nicht bewertbarer Abgabe ist
`quality_passed = false` keine erfundene fachliche Bewertung: `criterion_results`
bleibt leer und `evaluation_status` ist `not_evaluated`. Unbekannte Metriken
bleiben `null`. Ein fachlich falsches, aber regulär ausgewertetes Projekt hat
dagegen `status = completed`, `evaluation_status = complete` und konkrete
fehlgeschlagene Kriterien.

`manifest.json` enthält `schema_version`, `run_id`, den vollständigen `plan`,
`suite_sha256`, `resolved_plan_sha256`, `python_version`, `wheel_sha256`,
`artifact_hashes` und `inputs`. `inputs` ordnet `suite`, `plan`, `agent` und
`packages` nichtleere Listen archivierter relativer Dateipfade zu. Die
Hashliste deckt diese Eingaben sowie alle Ergebnisbelege ab und stimmt mit
deren tatsächlichen Bytes überein. Das Manifest selbst benötigt keinen
selbstreferenziellen Hash. Beim Quelllauf darf `wheel_sha256` unbekannt sein;
beim Wheel-Lauf muss es dem tatsächlich installierten Wheel entsprechen.
Der Testprozess kennt dessen erwarteten Hash über
`QB_CUBIE_TEST_WHEEL_SHA256`; die Produktimplementierung muss ihre Herkunft
selbst erfassen.

`report.md` nennt Szenariokennung, fehlgeschlagenes Kriterium und verlinkt
existierende Belege innerhalb des Laufarchivs. Der Bericht bleibt gemeinsam
mit `results.json` und Manifest nach einem weiteren Lauf erhalten.

## Ausführung und beobachtete Rotphase

```bash
# Reguläre Offline-Abnahmecases
.venv/bin/python -m pytest -q tests/benchmarks

# Ausschließlich die neuen Cases
.venv/bin/python -m pytest -q tests/benchmarks/phase2

# Lint
.venv/bin/python -m ruff check tests/benchmarks/phase2 \
  tests/wheel/benchmark_installed.py scripts/check_wheel.py

# Wheel bauen und alle installierten Profile prüfen
uv build --wheel --out-dir /tmp/cubie-wheel
.venv/bin/python scripts/check_wheel.py /tmp/cubie-wheel
```

Der Wheel-Harness kopiert die Cases in ein temporäres Verzeichnis und startet
pytest mit `-I`, eigener Konfiguration und deaktivierter Plugin-Autoladung.
`benchmark_installed.py` wird bewusst nicht im normalen Checkout gesammelt.
Der vorhandene Wheel-Harness erhält das zusätzliche Profil `benchmarks`;
`MANIFEST.in` nimmt die neue Abnahmedatei auch ins Source-Archiv auf.
Installation im allgemeinen Harness kann Netzwerk benötigen; die Cases selbst
benötigen kein Modell und keine Netzwerkverbindung.

### Historischer Ausgangsstand vor Implementierung

Lokale Prüfung am 10. November 2026:

| Gruppe | Bestanden | Fehlgeschlagen | Setup-/Sammlungsfehler | Übersprungen |
| --- | ---: | ---: | ---: | ---: |
| Bestehende Benchmark-Cases zu Phase 10.1 | 233 | 0 | 0 | 0 |
| Neue Repository-Cases zu Phase 10.2 | 0 | 34 | 0 | 0 |
| Neue Cases gegen separat installiertes Wheel | 0 | 8 | 0 | 0 |

Die 34 Repository-Fehlschläge benennen ausschließlich die fehlenden öffentlichen
Funktionen `init_smoke_suite` und `run_suite`. Die acht Wheel-Fehlschläge benennen
das fehlende Extra `benchmarks` bzw. den fehlenden Entry Point `cubie-bench`.
Die JUnit-Berichte wurden auf Fehlergründe, Setupfehler und Skips geprüft.
Diese Ergebnisse sind eine kontrollierte Rotphase; die dahinterliegenden
Detailassertions können erst mit vorhandener Implementierung ausgeführt werden.

Das Wheel wurde mit `uv build --offline --wheel` neu gebaut und mit
`uv pip install --offline` in eine frische venv unter `/tmp` installiert;
pytest wurde ausdrücklich als Prüftreiber installiert. Die Installation meldet
korrekt, dass das Extra noch nicht existiert; der Metadatentest lehnt diese
unvollständige Installation ab. Die neue Wheel-Datei wurde separat mit `-I`,
eigener pytest-Konfiguration und ohne Checkout-conftest ausgeführt. Der gesamte
mehrstufige `check_wheel.py`-Lauf einschließlich Core-/Linter-Profilen wurde
hierbei nicht wiederholt.

Ruff und `git diff --check` bestehen. Die vollständige Repository-Sammlung
umfasst **1603 Tests** ohne Sammlungsfehler; ein vollständiger Regressionslauf
außerhalb der Benchmark-Cases wurde für diese Testergänzung nicht ausgeführt.
Fehlende APIs/Entry Points verursachen normale Testfehlschläge;
Sammlungs- und Setupfehler wären Fehler der Cases selbst.

Die Cases prüfen zunächst den vollständigen kleinen Durchstich. JSONL-Transport,
reale Modelle, Container-Ressourcenbegrenzung, Gates und statistische
Agentenvergleiche gehören weiterhin zu den späteren Phasen. Die vorhandenen
Referenz-/Mutantentests aus Phase 10.1 bleiben die unabhängige fachliche
Gegenkontrolle. Die damalige Rotphase wies fehlende Infrastruktur nach, noch keine
beobachteten Fehler eines implementierten Runners.


## Implementierter Umfang und ergänzende Gegenproben

Die ursprünglichen 34 Repository- und acht Wheel-Cases bleiben unverändert.
Neun zusätzliche [Grenzfälle](benchmarks/phase2/test_execution_boundaries.py)
prüfen erschöpfte Werkzeugbudgets, nicht unterstützte Adapter, unabhängiges
Wiederholen archivierter Rot-/Grün-Phasen, tatsächliche RBT-Ergebnisse, die
Cubie-/pytest-Integrationsbedingungen, Ergebnisverzeichnisse außerhalb der
Szenarien, fehlende Evaluatorkriterien, globale Laufzeitgrenzen und private
Evaluatorvorlagen außerhalb des sichtbaren Baums.

Die Implementierung liegt unter
[`src/qb_cubie/benchmarks`](../src/qb_cubie/benchmarks): `scaffolding/templates.py` erzeugt
Vorlagen aus installierten Ressourcen, `runner.py` führt denselben öffentlichen
Plan aus, `adapters/fake.py` provisioniert Abgaben, `execution/evaluators.py` bewertet sie und
`reporting/results.py` schreibt das Archiv. Die internen Module trennen Prozesssteuerung,
Dateiidentitäten, Nachrichtenaustausch, Entwicklerphasen und RBT-Aufzeichnung.
Die unabhängige Projektabnahme verwendet eigene pytest-Tests mit mehreren
Datensätzen einschließlich Leerfall und Binärinhalt. Die Cubie-Agententests
führen echte EBT-Verträge aus; RBT erhält einen expliziten Reviewer und Reporter.

Zeit- und Werkzeugbudgets werden vom Runner kontrolliert. Laufzeitabbrüche
bewahren Beobachtungen und Rohdaten; weitere Versuche bleiben bei erschöpftem
globalem Zeitbudget als `not_started` sichtbar. Unter POSIX beendet ein Timeout
die gesamte gestartete Prozessgruppe. Subprozesse erben keine Zugangsdaten.
Die lokale Ausführung vertraut Szenario- und Evaluatorcode und ist keine
Container-Sicherheitsgrenze. Nicht unterstützte Adapter und Token-/Kostenlimits
führen vor Agentenstart zu Konfigurationsfehlern. Der Fake-Reviewmatcher ist für
strukturierte Referenzabgaben vorgesehen; frei formulierte Modellreviews bleiben
außerhalb dieses Umfangs.

## Prüfung nach Implementierung

Die ursprünglichen Cases bestehen unverändert. Zusammen mit den neun neuen
Grenzfällen ergeben sich **276 bestandene Benchmark-Cases**: 233 aus Phase 10.1
und 43 aus Phase 10.2. Der abschließende Lauf einschließlich Styleguide und
aller drei Quellcode-Linter ergibt:

```text
297 passed, 1 skipped in 41.13s
```

Der Skip ist die bereits ausgesetzte Modulgrößenprüfung. Funktionsgrößenprüfung,
Ruff, Mypy und Pylint bestehen. Der komplementäre Regressionslauf mit
`--ignore=tests/benchmarks` ergibt:

```text
1324 passed, 12 skipped, 6 warnings in 340.34s
```

Damit wurden die vollständige Repository-Suite in zwei komplementären Läufen
sowie die zusätzlichen Lint-/Styleprüfungen ausgeführt. Die Skips und Warnungen
stammen aus bestehenden Tests.

`uv build --offline` erzeugt sowohl ein Source-Archiv als auch das Wheel.
Der vollständige `scripts/check_wheel.py`-Lauf gegen dieses neue Wheel besteht:

| Installiertes Profil | Bestanden |
| --- | ---: |
| Core | 22 |
| Linters | 22 |
| Benchmarks | 8 |

Die acht Wheel-Cases prüfen die echte installierte CLI und das verschiebbare
Smoke-Set außerhalb des Checkouts; der protokollierte Wheel-Hash stimmt mit dem
installierten Artefakt überein. Die produktive Implementierung übernimmt den
Hash nicht aus der Testumgebung. Ruff für alle ergänzten Dateien und
`git diff --check` bestehen ebenfalls.
