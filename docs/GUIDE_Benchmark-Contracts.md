# Benchmark-Verträge und Offline-Smoke-Läufe

`qb_cubie.benchmarks` bietet die Datenverträge für Phase 10.1 und den
installierbaren Offline-Durchstich aus Phase 10.2 und die Prozessanbindung aus Phase 10.3 des
[Benchmark-Konzepts](BENCHMARK_KONZEPT.md#101-öffentliche-verträge-und-referenzen).
Laden, Planen und Nachrichtenvalidierung benötigen keine zusätzlichen
Abhängigkeiten und führen keinen Szenariocode aus. CLI und Runner sind ebenfalls
installierbar; für die pytest-Unterprozesse wird das Extra `benchmarks` benötigt.
Der Runner unterstützt den eingebauten Fake und externe JSONL-Prozesse.
[Das Tutorial für eigene Agenten und Szenarien](GUIDE_Benchmark-Custom.md)
beschreibt Vorlagen, Fähigkeitenaustausch, Referenzprüfung und Laufvergleich.
Mit `cubie-bench guide` ist es auch im installierten Wheel verfügbar.
Der Fake und der exportierbare Beispielprozess benötigen keinen Modellzugang.

## Installieren und ausführen

Diese Befehle funktionieren in einem eigenen Arbeitsverzeichnis ohne Checkout:

```bash
python -m pip install 'qb-cubie[benchmarks]'
cubie-bench init-suite ./sets/smoke.toml --preset smoke --fake
cubie-bench plan --suite ./sets/smoke.toml
cubie-bench plan --suite ./sets/smoke.toml --format json
cubie-bench run --suite ./sets/smoke.toml
```

Die Initialisierung erzeugt `sets/smoke.toml`, `agents/fake.toml` und
`scenarios/smoke/`. Vorhandene Ziele werden nicht überschrieben. Die relativen
Pfade bleiben nach einem gemeinsamen Umzug gültig. Das Paket enthält zwei
Review-Fälle und die Erstentwicklung des Dokumentindex. Die Wartungs- und
Diagnosevorlagen aus Phase 10.1 bleiben separates Referenzmaterial.

Der Plan zeigt IDs, Paketversionen, Agent, Bedingung, Wiederholung, Evaluator,
Typen/Tags und Budgets. JSON und Python-API verwenden denselben Plan. Unter
`results/<run_id>/` entstehen:

- `report.md`: Kriterien, Phasen und Links zu Belegen;
- `results.json`: Ausführungsstatus sowie Qualitäts- und Prozessurteile;
- `manifest.json`: eingefrorener Plan, Eingabeidentitäten und Artefakthashes;
- `inputs/`: archiviertes Set, Agentenkonfiguration und Szenariopaket;
- `episodes/`: getrennte Ausgangsstände, Workspaces, Phasensnapshots,
  Anfragen/Antworten und unabhängige Evaluatorbeobachtungen.

`completed` bedeutet, dass die Bewertung ausgeführt wurde. `quality_passed`
und `process_passed` sind getrennt zu lesen: Eine fachlich richtige Lösung ohne
nachgewiesene Rotphase erfüllt den Entwicklungsprozess nicht. Eine korrekte
Ablehnung fehlerhaften Codes kann die Review-Aufgabe bestehen. Ein Fake-Erfolg
prüft die Infrastruktur und misst keine Modellleistung.

Ohne Qualitätsgate liefert eine vollständig durchgeführte Messung Exitcode 0,
auch bei fachlichem Durchfallen. Exitcode 2 bezeichnet Konfigurationsfehler,
Exitcode 3 ungültige oder unterbrochene Ausführungen. Unbekannte Modell-, Token-
und Kostenwerte bleiben `null`.

## Python-Aufruf und Gegenproben

```python
from pathlib import Path
from qb_cubie.benchmarks import init_smoke_suite, run_suite

suite = Path("./sets/smoke.toml")
init_smoke_suite(suite)
result = run_suite(suite)
print(result["output"])
```

Die Agentenkonfiguration verwendet `command = ["builtin:fake"]`. Im Abschnitt
`[fake]` kann `behavior = "reference"` durch `"mutant"` mit
`mutant = "wrong-return"` ersetzt werden. Die unabhängige Abnahme muss dann
`returns_none` ablehnen. Weitere Gegenproben beschreibt der
[Abnahmevertrag](../tests/BENCHMARK_CASES_10_2.md#deterministische-gegenproben-des-fake-adapters).

Die Cubie-Bedingung führt echte EBT-Agententests und RBT mit aufzeichnendem
Reporter aus. `cubie-vs-pytest` kann dieselben deterministischen Abgaben auch mit
reinen pytest-Agententests ausführen. Die Review-Auswertung vergleicht im
Durchstich strukturierte Referenzfelder; ein allgemeines semantisches Matching
frei formulierter Antworten ist weiterhin nicht enthalten.

Die Ausführung ist für vertrauenswürdige lokale Smoke-Materialien gedacht.
Unterprozesse erhalten keine Provider-Schlüssel oder geerbten Python-/pytest-
Konfigurationen. Das Laufzeitbudget und das Budget der vom Runner gestarteten
Werkzeuge werden durchgesetzt; interne Werkzeugaufrufe eines externen Dienstes
sind damit nicht gemessen. Bei Timeout
wird unter POSIX die Prozessgruppe beendet, unter Windows über `taskkill /T`.
Die lokale Ausführung bietet noch keine Container-Sicherheitsgrenze für fremden
Code. Harte Token-/Kostenbudgets werden vor dem Start abgelehnt. Das globale
Zeitlimit verhindert weitere Starts mit Status `not_started`.

Ausführbare Projekt-Referenzen ergänzen die private Vorlage `acceptance_tests`
und den relativen Pfad `submission_module`. Der Fake benötigt außerdem `agent_tests`
und für die pytest-Bedingung `pytest_agent_tests`; externe Prozesse reichen ihre
Tests selbst ein. Der unabhängige Evaluator aggregiert
`test_<criterion_id>` einschließlich Parametrisierungen; eine fehlende Prüfung
ist ein Infrastrukturfehler. Vorlagen für Agententests und Evaluator bleiben
außerhalb des exportierten sichtbaren Baums.

## Einstieg

```python
from pathlib import Path
from qb_cubie.benchmarks import load_package, plan_suite

package = load_package(Path("./my-scenarios"))
for scenario in package["scenarios"]:
    print(scenario["qualified_id"], scenario["benchmark"], scenario["types"])

plan = plan_suite(Path("./sets/smoke.toml"))
print(len(plan["runs"]), plan["total_wall_time_seconds"])
```

Ein Paketbeispiel mit fünf Szenarien liegt im Repository unter
[tests/benchmarks/fixtures/phase1](../tests/benchmarks/fixtures/phase1/package.json).
Sein Set ist ausschließlich zum Planen geeignet: Das deklarierte Agentenkommando
existiert absichtlich nicht. Für ausführbare Vorlagen dient `init_smoke_suite`.

Alle Rückgaben sind JSON-kompatible Dictionaries und Listen. Jede Nachricht
wird als eigene Momentaufnahme zurückgegeben; die Validierung verändert ihre
Eingabe nicht. Fehlerhafte Konfigurationen und Nachrichten erzeugen `ValueError`
mit betroffenem Feld und Ursache. NaN, Infinity, nicht unterstützte
Schemaversionen und doppelte JSON-Schlüssel werden abgelehnt.

## Szenariopakete

`load_package(path: str | Path) -> dict` liest `package.json` und die darin
explizit aufgeführten Szenariomanifeste. Es gibt keine automatische
Codeentdeckung oder Ausführung von Importen.

| Manifest | Pflichtfelder |
| --- | --- |
| Paket | `schema_version = 1`, `namespace`, `version`, `license`, `provenance`, nichtleere Liste `scenarios` mit relativen Manifestpfaden |
| Szenario | `schema_version = 1`, `id`, `title`, `benchmark`, `group_id`, `split`, `task`, `visible`, nichtleere `criteria`, `evaluator` |
| Evaluator | `kind`, relativer Pfad `reference` |

IDs und Namespaces bestehen aus Buchstaben, Ziffern, Punkt, Unterstrich und
Bindestrich und beginnen mit einem Buchstaben oder einer Ziffer. Eine
qualifizierte Szenariokennung lautet `namespace/id`. IDs sind innerhalb eines
Pakets eindeutig. `benchmark` ist `review_agent` oder `developer_agent`;
`split` ist `development` oder `held_out`. Szenarien derselben Gruppe müssen
denselben Split besitzen.

`types` und `tags` sind optionale Listen frei benennbarer, eindeutiger Strings;
ihr Standard ist `[]`. Sie steuern ausschließlich Auswahl und Gruppierung.
`requires` enthält explizite qualifizierte Vorgängerkennungen, standardmäßig
`[]`. Optionale `budgets` überschreiben die Werte des Sets für dieses Szenario.

Diese Version unterstützt `builtin.review_reference_v1` für Reviews und
`builtin.pytest_project_v1` für Entwicklerepisoden. Unbekannte oder zum Benchmark
unpassende Evaluatortypen werden abgelehnt; eigene Evaluatorkommandos folgen im
weiteren Ausbau.

Paketpfade beziehen sich auf das Paketverzeichnis, Materialpfade auf das
jeweilige Szenariomanifest. Material muss existieren und innerhalb seines
Wurzelverzeichnisses bleiben. Der sichtbare Baum darf durch Symlinks keine
privaten Referenzen oder anderen Dateien außerhalb dieses Baums einbeziehen.
Referenzdatei, Projektlösung und Mutanten dürfen nicht im sichtbaren Baum liegen.
Die Rückgabe ergänzt jedes Szenario um `qualified_id`, den paketrelativen
Manifestpfad `manifest` sowie normalisierte `types`, `tags` und `requires`.

Die Referenz ist selbst ein versioniertes JSON-Objekt. `criterion_results`
deckt alle sichtbaren Kriterien genau einmal mit `pass`, `fail` oder `abstain`
ab. `validation_status` und `human_reviews` halten den Prüfstand fest.
`author_checked` bedeutet keine unabhängige menschliche Freigabe.

Review-Referenzen besitzen `findings` für die als fehlerhaft bewerteten
Kriterien. Ein Finding benennt `criterion_id`, sichtbaren `path`, `symbol`,
`mechanism`, `impact`, optionale `allowed_alternatives` und gegebenenfalls ein
`counterexample` mit unterschiedlichen Werten für `expected` und `actual`.
Projekt-Referenzen deklarieren eine `solution`, benannte `mutants` und deren
Zuordnung `mutant_criteria`. Der Loader prüft diese Verweise und Kriterien,
führt aber keine Lösung oder Gegenprobe aus. Die EBT-Referenzprüfungen führen
die mitgelieferten vertrauenswürdigen Beispiele gesondert aus.

## Sets und Laufpläne

`plan_suite(path: str | Path) -> dict` liest ein TOML-Set. Pflichtfelder sind
`schema_version = 1`, `name`, `profile`, positive ganzzahlige `repetitions`,
`agents`, `sources` und `output`. Relative Quell-, Agenten- und Ausgabepfade
beziehen sich auf die Set-Datei. Kommandoargumente werden als Daten unverändert
gelesen; eine Ausführungsumgebung legt erst der Runner fest.

Diese erste Version unterstützt lokale Quellen `[[sources]]` mit `path`.
Installierte Szenariopakete und `builtin:...`-Quellen gehören zum späteren
Ausbau und werden derzeit ausdrücklich als nicht unterstützte Quellen gemeldet.
Inhaltlich identische Quellen desselben Namespace werden zusammengeführt;
unterschiedliche Inhalte oder Versionen desselben Namespace werden abgelehnt.
Die Paketidentität verwendet SHA-256 über sortierte relative Pfade, Modus,
Symlinkziel und Dateiinhalte der Szenarien sowie `package.json`, jeweils mit
Längenrahmung. Verzeichnissymlinks werden beim Planen nicht unterstützt.

Ein Agenten-TOML enthält `schema_version = 1`, eindeutige `id`, nichtleere
`command`-Argumentliste und eine Liste `capabilities`. Der Planner liest das
Kommando als Daten und prüft seine Ausführbarkeit noch nicht. Für Reviews ist
`review_output` erforderlich, für Entwickler-Episoden `workspace_changes` und
`phased_submission`. Hinzu kommen `cancel` und die Fähigkeiten zur Durchsetzung
der gewählten Budgets: `wall_time`, `tool_calls`, `token_usage`, `cost`.
Eine Deklaration dieser Fähigkeiten ersetzt noch keine Adapter-Vertragstests.

`profile = "agent-evaluation"` erzeugt die Bedingung `cubie`.
`profile = "cubie-vs-pytest"` erzeugt je einen Versuch für `cubie` und `pytest`.
Für jeden Agenten, jede Wiederholung, Bedingung und ausgewähltes Szenario gibt
es genau einen Versuch. Wiederholungen werden ab 1 gezählt; Vorgänger stehen
innerhalb jeder Folge vor ihren Nachfolgern. Zyklen und fehlende Vorgänger sind
Konfigurationsfehler. Vorgänger werden nicht automatisch hinzugefügt.

Optionale `[select]`-Filter:

| Filter | Bedeutung |
| --- | --- |
| `ids`, `benchmarks`, `splits` | Mindestens ein Wert muss passen. |
| `exclude_ids` | Jede passende ID wird ausgeschlossen. |
| `types_any`, `tags_any` | Mindestens ein genannter Wert muss passen. |
| `types_all`, `tags_all` | Alle genannten Werte müssen passen. |
| `types_none`, `tags_none` | Kein genannter Wert darf vorkommen. |

Verschiedene Felder werden mit UND verknüpft; Ausschlüsse haben Vorrang.
Fehlende Filter schränken nicht ein, explizit leere Filterlisten sind ungültig.
Unbekannte explizite IDs, positive Typ-/Tagfilter ohne irgendeinen Treffer und
eine leere Gesamtauswahl führen zum Fehler mit verfügbaren Werten.
Mehrere passende Typen erzeugen keine zusätzlichen Versuche.

Budgets werden in der Reihenfolge Voreinstellung, Set, Szenario aufgelöst.
Review-Voreinstellung: 300 Sekunden und 20 Werkzeugaufrufe;
Developer-Voreinstellung: 1800 Sekunden und 100 Werkzeugaufrufe.
Unterstützte Felder sind `wall_time_seconds`, `tool_calls`, `input_tokens`,
`output_tokens` und `cost`. Grenzen sind positiv und endlich; Aufruf- und
Tokenzahlen sind ganzzahlig. Ein Kostenbudget setzt eine passende deklarierte
Mess- und Begrenzungsfähigkeit des Adapters voraus.

`[limits]` setzt `max_runs` und `max_total_wall_time_seconds`; ohne Angabe gelten
1000 Versuche und 36000 Sekunden. Der Plan muss vollständig in beide Grenzen
passen. Die Laufzeitobergrenze ist die Summe aller aufgelösten Versuchbudgets;
Parallelität verringert diese konservative Summe nicht. Es gibt kein stilles
Kürzen und keine vorzeitige Ausführung.

Der Plan enthält `schema_version`, `name`, `profile`, absolutes `output`,
`packages`, `runs` und die globalen Grenzen einschließlich
`total_wall_time_seconds`. Jeder Versuch benennt Szenario, Agent, Wiederholung,
Bedingung, Benchmark, Typen/Tags, Split, Gruppe, Paketidentität, Evaluator,
benötigte Fähigkeiten und aufgelöste Budgets. Die Rückgabe ist eine von den
Eingaben getrennte JSON-Momentaufnahme.

## Agenten- und Evaluatornachrichten

Die vollständigen Beispiele stehen in den
[Protokoll-Cases](../tests/benchmarks/test_protocol_contracts.py).
Alle Nachrichten tragen `schema_version = 1`, `run_id` und `scenario_id`.
Die Validierungsfunktionen geben gültige Nachrichten ohne erfundene Werte
zurück; Ergebniskennungen müssen zur mitgegebenen Anfrage passen.

| Funktion | Weitere Pflichtangaben |
| --- | --- |
| `validate_agent_request(payload)` | `benchmark`, `phase`, `task`, absoluter `workspace`, `criteria`, `output_format`, nichtleere `budgets` |
| `validate_agent_event(payload, request)` | Anfragephase `phase`, `status`, `artifacts`, `usage`; bei Unterbrechung `reason` |
| `validate_evaluator_request(payload)` | `evaluator_id`, `evaluator_version`, getrennte absolute `submitted_workspace` und `reference_workspace`, `criteria`, nichtleeres `artifact_hashes` |
| `validate_evaluation(payload, request)` | `status`, `evaluation_status`, `criterion_results`, `metrics`, `evidence`; bei Unterbrechung `reason` |

Die beiden Evaluatorworkspaces müssen ohne Überschneidung getrennt sein.
Pfadnormalisierung berücksichtigt POSIX und Windows; verschiedene Schreibweisen
desselben Pfades gelten nicht als getrennte Verzeichnisse. Physische
Symlinkauflösung in der tatsächlichen Ausführungsumgebung bleibt Aufgabe des
ausführenden Runners.

Review-Anfragen verwenden Phase `review` und Format `review_v1`;
Entwickleranfragen Phasen `test_design`, `red`, `green`, `refactor` und Format
`project_v1`. Phasenreihenfolge und tatsächliche Rot-/Grün-Belege prüft erst
der ausführende Runner.

`status` unterscheidet `completed`, `agent_timeout`, `budget_exceeded`,
`invalid_output`, `infrastructure_error`, `not_started`. Ein abgeschlossenes
Evaluatorergebnis braucht `evaluation_status = "complete"` oder
`"pending_adjudication"`; unterbrochene Ausführungen bleiben `"not_evaluated"`.
Vollständige Ergebnisse müssen alle angefragten Kriterien abdecken. Teilurteile
bleiben bei unvollständiger Bewertung zulässig; fremde Kriterien werden immer
abgelehnt. `abstain` wird nicht zu einer Freigabe.

`artifacts` und `evidence` sind Listen relativer POSIX-Pfade ohne `..`, leere
Segmente oder Laufwerksangaben. Abgeschlossene Abgaben/Bewertungen benötigen
mindestens einen solchen Verweis. `artifact_hashes` ordnet Artefaktpfaden
SHA-256-Werte aus 64 kleinen Hexadezimalzeichen zu. Ob Dateien existieren,
die Hashes stimmen und die Inhalte zur Abgabe gehören, prüft der ausführende
Evaluator. Die Strukturvalidierung bietet dafür keine Abnahme.

`usage` enthält `input_tokens`, `output_tokens`, `cost`. Unbekannte Werte bleiben
`null`; bekannte Werte sind endlich und nichtnegativ. Eine Metrik deklariert
`name`, `value`, `unit`, `direction` (`higher`, `lower`, `neutral`) und
`aggregation`. Unbestimmte Werte bleiben `null`; bei offenen oder nicht
bewerteten Ergebnissen sind numerische Qualitätswerte unzulässig.


## Paketstruktur

Die öffentliche API bleibt unter `qb_cubie.benchmarks` verfügbar. `cli.py` und
`runner.py` bilden die zentralen Einstiegspunkte. Die Fachmodule sind gruppiert:

| Unterpaket | Aufgabe |
| --- | --- |
| `contracts` | Paket-, Referenz- und Nachrichtenvalidierung |
| `planning` | Auswahl, Budgets und vollständige Laufpläne |
| `execution` | Episoden, Phasen, Prozesse und unabhängige Bewertung |
| `adapters` | Deterministische Fake-Abgaben |
| `reporting` | Dateiidentitäten, Archive und lesbare Berichte |
| `scaffolding` | Erzeugung eigenständiger Smoke-Vorlagen |

Die installierten Vorlagendaten bleiben unter `data/`. Interne Funktionen und
Methoden besitzen erklärende Docstring-Einzeiler; die Styleguide-Prüfung sichert
auch deren Vollständigkeit im Benchmark-Paket.
