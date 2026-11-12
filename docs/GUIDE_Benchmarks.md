# Benchmarks: Einstieg, eigene Agenten und Messbetrieb

Stand: 11. November 2026.

> **Experimentell · kein Bestandteil des qb-cubie Core.** Der gesamte
> Benchmark-Bereich ist ein separater experimenteller Bereich. Dazu gehören
> `qb_cubie.benchmarks`, die CLI `cubie-bench`, die Extras `benchmarks` und
> `swebench`, Agentenadapter, Szenariodatensätze sowie Vergleichs-, Bewertungs-
> und CI-Messfunktionen. Sie werden derzeit im selben Paket ausgeliefert;
> daraus folgt keine Zugehörigkeit zum Core.

Dieser Guide führt vom modellfreien Beispiel bis zum eingefrorenen Messlauf.
Ein eigener Agent mit einer Wiederholung genügt; mehrere Agenten, der Vergleich
Cubie/Pytest und SWE-bench sind optionale Erweiterungen. Die vollständige
Anleitung ist nach einer Wheel-Installation mit `cubie-bench guide` verfügbar.

Ein **Szenario** ist eine Review- oder Entwicklungsaufgabe mit sichtbarem
Auftrag und privater Bewertungsreferenz. Ein **Paket** bündelt versionierte
Szenarien. Ein **Set** (Suite) wählt Pakete, Agenten, Wiederholungen und Budgets.
Der **Plan** löst diese Auswahl in einzelne Versuche auf; das **Ergebnisarchiv**
enthält deren Antworten, Bewertungen und Belege.

| Ziel | Einstieg |
| --- | --- |
| Die Infrastruktur ohne Modellzugang ausprobieren | [Schnellstart](#schnellstart) |
| Ein eigenes Agentensystem anschließen | [Agenten und Modellkonfiguration](#agenten-und-modellkonfiguration) |
| Eigene Aufgaben und Abnahmen schreiben | [Szenarien und Referenzen](#szenarien-und-referenzen) |
| Aufgaben auswählen und Aufwand begrenzen | [Sets, Auswahl und Budgets](#sets-auswahl-und-budgets) |
| Ergebnisse und Versionen vergleichen | [Berichte und Laufvergleich](#berichte-und-laufvergleich) |
| Wiederholungen und Pilotdaten auswerten | [Basisdatensatz und Pilot](#basisdatensatz-und-pilot) |
| Cubie und Pytest gegenüberstellen | [Gespiegelte Developer-Aufgaben](#gespiegelte-developer-aufgaben) |
| Öffentliche Reparaturaufgaben importieren | [SWE-bench](#swe-bench) |
| Messungen einfrieren und in CI ausführen | [Messbetrieb, Gates und CI](#messbetrieb-gates-und-ci) |
| Nachbewertungen und Belege verwalten | [Nachbewertung und Betriebsregeln](#nachbewertung-und-betriebsregeln) |
| Datenverträge und Python-API nachschlagen | [Technische Referenz](#technische-referenz) |

Beispiele ohne expliziten Repositorypfad funktionieren in einem eigenen
Arbeitsverzeichnis. Relative Konfigurationspfade beziehen sich auf die jeweilige
Set- oder Agentendatei. Verlinkte Dockerfiles und Abnahmematrizen beziehen
sich auf den Quellcheckout; sie sind im installierten CLI-Text nur Pfadverweise.

## Schnellstart

```bash
python -m pip install 'qb-cubie[benchmarks]'
cubie-bench init-example ./shipping-demo
cubie-bench validate-agent ./shipping-demo/agents/current.toml
cubie-bench list --package ./shipping-demo
cubie-bench validate ./shipping-demo --check-references
cubie-bench plan --suite ./shipping-demo/sets/team.toml
cubie-bench run --suite ./shipping-demo/sets/team.toml
```

Diese Schritte funktionieren außerhalb des Cubie-Repositories. `init-example`
exportiert ein eigenständiges Versandkostenpaket mit zwei Reviews, einer
Entwicklungsepisode, einem JSONL-Beispielagenten und einem ausführbaren Set.
Bestehende Ziele werden nicht überschrieben. Der Beispielagent ist ein
deterministischer Protokollpeer ohne Modellaufrufe: Sein Erfolg prüft die
Integration und ist keine gemessene Modellleistung.

Bei 5000 Cent Warenwert muss der Versand kostenlos sein. Der konforme Review
wird freigegeben, die Variante mit `> 5000` wird mit einem konkreten Finding
abgelehnt. Beide Reviews können damit ihre jeweilige Benchmark-Aufgabe
bestehen. Die Entwicklungsepisode beginnt mit einem falschen Rückgabewert;
der Agent reicht EBT-Tests ein, der Runner beobachtet Rot und anschließend
Grün. Eine getrennte pytest-Abnahme prüft das Ergebnis unabhängig von EBT.

`validate` prüft zunächst nur Dateien, Schemastand und Kriterien. Erst
`--check-references` führt private Projektabnahmen aus, testet die Lösung und
kontrolliert, ob die angegebenen Mutanten an ihren Kriterien scheitern.
Bei Review-Referenzen ohne ausführbaren Vertrag bleibt
`reference_check="structural_only"` und `reference_passed=null` sichtbar.
Alle Beispielreferenzen sind `author_checked`; automatische Prüfungen sind
keine unabhängige menschliche Aufnahmefreigabe.

### Kleiner Smoke-Lauf mit eingebautem Fake

Wer nur den Runner prüfen möchte, kann statt des Versandkostenbeispiels ein
kleines Paket mit zwei Reviews und einer Dokumentindex-Entwicklung erzeugen:

```bash
cubie-bench init-suite ./sets/smoke.toml --preset smoke --fake
cubie-bench plan --suite ./sets/smoke.toml --format json
cubie-bench run --suite ./sets/smoke.toml
```

Dabei entstehen `sets/smoke.toml`, `agents/fake.toml` und `scenarios/smoke/`.
Vorhandene Ziele werden nicht überschrieben. Der Agent verwendet
`command = ["builtin:fake"]`. Für eine Gegenprobe lässt sich in `[fake]`
`behavior = "reference"` durch `behavior = "mutant"` und
`mutant = "wrong-return"` ersetzen: Die unabhängige Abnahme muss dann
`returns_none` ablehnen. Beide Beispiele prüfen die Infrastruktur; sie liefern
keinen Nachweis über Modellleistung oder den Nutzen von Cubie.

## Agenten und Modellkonfiguration

```bash
cubie-bench init-agent ./agents/current.toml
```

Passen Sie Kommando, Arbeitsverzeichnis, ID und Fähigkeiten an Ihren Adapter an.
Die Vorlage enthält den Python-Interpreter der aktiven Installation. Beispiel:

```toml
schema_version = 1
id = "own-agent"
transport = "jsonl-v1"
command = ["/absolute/path/to/python", "-I", "agent.py"]
cwd = "."
capabilities = ["review_output", "workspace_changes", "phased_submission", "cancel", "wall_time", "tool_calls"]
```

`cwd` bezieht sich auf die Konfigurationsdatei, auch nach deren Archivierung.
Kommandos sind Argumentlisten und werden ohne Shell gestartet. `cwd="."`
erlaubt relative Skriptnamen. Gemeinsames Verschieben von Agent, Paket und Set
erhält deren relative Pfade; der konfigurierte Interpreter muss auf dem
Zielrechner verfügbar sein.

Als ausführbare Protokollvorlage dient
`shipping-demo/agents/jsonl_agent.py`. Dieser Beispielagent kennt ausschließlich
die Versandkostenaufgabe. Er lässt sich durch einen Adapter für das eigene
Agentensystem ersetzen. Providerzugang kann etwa ein separat betriebener
Agentendienst vermitteln; geerbte Provider-Schlüssel, Python-/pytest-Konfiguration
und sonstige Umgebungsvariablen werden nicht an den Prozess weitergegeben.
Konfiguration, Kommandoargumente und protokollierte Antworten enthalten keine
Zugangsdaten.

```bash
cubie-bench validate-agent ./agents/current.toml
cubie-bench init-suite ./sets/team-smoke.toml --preset smoke \
  --agent ./agents/current.toml --package ./shipping-demo
cubie-bench plan --suite ./sets/team-smoke.toml --format json
cubie-bench run --suite ./sets/team-smoke.toml
```

`validate-agent` startet nur den Fähigkeitenaustausch, keinen Auftrag.
`plan` startet überhaupt keinen Agenten. Vor `run` werden Konfiguration,
Ausführbarkeit und die tatsächlich bestätigten Fähigkeiten geprüft. Fehler
verhindern den Aufgabenstart. Ein reiner Reviewer muss nicht
`workspace_changes` oder `phased_submission` anbieten, wenn das Set
ausschließlich Reviews auswählt.

### Modellkonfiguration nachweisen

Ein Prozessadapter ohne Modellangaben bleibt eine Infrastrukturbeobachtung.
Für einen nachvollziehbaren Modellversuch kann die Agentenkonfiguration folgende
vollständige Deklaration enthalten; ersetzen Sie die Beispielwerte durch die
verwendete Konfiguration:

```toml
[model]
model_id = "my-model"
revision = "immutable-model-revision-or-digest"
provider = "my-provider"
provider_version = "recorded-provider-version"
adapter_version = "my-adapter-1"
prompt_sha256 = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

[model.parameters]
temperature = 0.0
```

Der JSONL-Handshake muss dasselbe Objekt unter `model` zurückgeben, einschließlich
`parameters`. Abweichende oder unvollständige Deklarationen werden vor einer
Aufgabenanfrage abgelehnt. Der Runner archiviert Konfiguration, rohen Handshake
und `model_provenance` pro Versuch. `model_id` wird nur aus dieser übereinstimmenden
Deklaration übernommen. Ein Abbruch nach erfolgreichem Handshake bewahrt sie und
bereits gemeldete Nutzungswerte.

Die Zusammenfassung kennzeichnet passende Prozessversuche als `agent_evaluation`,
gemischte Archive als `mixed` und reine Fakes oder Prozesse ohne Modellnachweis
als `infrastructure_only`. Die Angaben bleiben eine Deklaration des Adapters;
die Übereinstimmung mit der Konfiguration beweist keinen tatsächlichen
Provideraufruf. Der Bericht nennt diese Grenze ausdrücklich. Archivieren Sie
zusätzliche Providerbelege in Ihrem Versuchsaufbau, soweit verfügbar. Die
mitgelieferten deterministischen Beispiele liefern keine Modellleistungsnachweise.

### Nachrichten und Phasen

Der Prozess liest UTF-8-JSONL auf stdin und schreibt ausschließlich JSONL auf
stdout. Jede Nachricht endet mit einem Zeilenumbruch. Diagnosen gehören auf
stderr. Die erste Anfrage ist:

```json
{"schema_version": 1, "type": "capabilities"}
```

Die Antwort hat denselben Typ und Schemastand und nennt `agent_id`,
`agent_version` und `capabilities`. Die ID muss zur Konfiguration passen.
Deklarierte Fähigkeiten müssen tatsächlich bestätigt sein. Der Handshake
hat eine Grenze von fünf Sekunden; der Runner beendet und erntet die Sitzung.

Danach folgen `type="request"` mit `run_id`, `scenario_id`, `benchmark`,
`phase`, `task`, absolutem `workspace`, `criteria`, `output_format` und `budgets`.
Der Agent erhält ausschließlich exportierten Auftrag und sichtbare Dateien.
Er liest weder Referenzen noch Ergebnisse früherer Versuche.

Eine abgeschlossene Abgabe antwortet mit `type="event"`, `schema_version=1`,
denselben IDs und derselben Phase, `status="completed"`, relativen
`artifacts`, einer vollständigen Zuordnung `artifact_hashes` und `usage`:

```json
{"input_tokens": null, "output_tokens": null, "cost": null}
```

Unbekannte Werte bleiben `null`. Gemessene Phasenwerte werden aufsummiert;
fehlt eine Messung, bleibt der entsprechende Gesamtwert unbekannt.
Der Runner verifiziert Dateien und SHA-256 selbst. Absolute Pfade,
Elternverweise, Symlinks, fehlende Dateien, falsche Hashes und fremde IDs/Phasen
sind ungültig. Nachrichten sind auf 1 MiB je Zeile begrenzt, stderr wird bis
4 MiB archiviert. Die Sitzung endet innerhalb des Laufzeitbudgets; bei Timeout
beendet der Runner unter POSIX die gesamte Prozessgruppe.

Reviews liefern `review.json` im vorhandenen `review_v1`-Format:
`schema_version`, `criterion_results`, `findings` und `sources`. `sources`
nennt den vollständigen exportierten Quellkontext einschließlich `task.md`.
Jedes Finding enthält `criterion_id`, `path`, `symbol`, `mechanism` und
`impact`. Dieser Evaluator gleicht strukturierte Referenzfelder ab; er ist
kein semantischer Richter für beliebige frei formulierte Reviews.

Entwicklungsaufträge verwenden eine gemeinsame Sitzung für
`test_design → red → green → refactor`. Der Agent reicht zuerst ausführbare
Tests ein und lässt Produktionscode unverändert. Der Runner friert den
Testbaum ein und führt jede Prüfphase selbst aus. Fachliches Scheitern in Rot
und bestandene Regressionen in Grün/Refactoring sind erforderlich.
Import-/Syntaxfehler, eine vorzeitige Implementierung oder geänderte Tests
erfüllen den Prozess nicht. Unabhängige Abnahmetests bleiben im Evaluatorbaum.
Vor der abschließenden Bewertung wird der Agentenprozess beendet.
Jeder weitere Versuch startet mit einer frischen Sitzung und einem frischen
Workspace.

Die lokale Ausführung setzt vertrauenswürdige Agenten-, Szenario- und
Evaluatorprogramme voraus. Workspace-Export und Umgebungsfilter sind keine
Containerisolation. Das Zeitbudget umfasst die Episode einschließlich Prüfungen;
`tool_calls` begrenzt die vom Runner gestarteten Werkzeuge. Interne Aufrufe
eines externen Agentendienstes werden dadurch nicht gemessen. Harte Token- und
Kostenobergrenzen werden derzeit vor Agentenstart abgelehnt.

### Erwartetes Stub-Rot

Assertion-Fehler und fehlende erwartete Exceptions in `pytest.raises` zählen
als fachliches Rot (`assertion_failure`). Zusätzliche Laufzeit-, Setup-, Syntax-
oder Importfehler verhindern eine gültige Rotphase.

Eine Developer-Referenz kann `expected_red_exception` mit `module` und `message`
deklarieren. `module` muss dem Produktionsmodul `submission_module` entsprechen
und im sichtbaren Material vorhanden sein. Nur in der Rotphase gilt eine
`NotImplementedError` mit exakt dieser Meldung und abschließendem Traceback im
benannten Produktionsmodul als fachlicher Fehlschlag. Setup-/Importfehler,
andere Exceptions und derselbe Stub in Grün bleiben Fehler. Die initialen
Stub-Aufgaben im Basisdatensatz enthalten diese Deklaration. Das öffentliche
Prozessergebnis nennt fachliches Rot weiterhin `assertion_failure`.

## Szenarien und Referenzen

```bash
cubie-bench init-scenario --benchmark review_agent ./my-reviews
cubie-bench init-scenario --benchmark developer_agent ./my-development
```

Jede Vorlage ist ein vollständiges Paket mit einem Szenario, sichtbarem Auftrag,
Ausgangsmodul und passenden privaten Referenzen. Bearbeiten Sie
`package.json`, `scenarios/.../scenario.json`, `task.md`, `visible/` und
`evaluator/`. Verwenden Sie einen eigenen Namespace und erhöhen Sie die
Paketversion bei Änderungen. Die mitgelieferte Lösung dient als Vorlage und
gehört ausschließlich in den Evaluatorbaum.

Für Entwickler definiert `submission_module` das Produktionsmodul und
`acceptance_tests` die unabhängige pytest-Abnahme. Benennen Sie die
Abnahmetests `test_<criterion_id>`; Parametrisierung ist erlaubt. Ein
fehlendes Kriterium ist ein Infrastrukturfehler, kein bestandener Test.
`agent_tests` und `pytest_agent_tests` sind nur für den eingebauten Fake
erforderlich. Ein eigener Prozess reicht seine Tests selbst ein.

```bash
cubie-bench validate ./my-development --check-references
cubie-bench init-suite ./sets/own.toml --preset smoke \
  --agent ./agents/current.toml --package ./my-development
```

Details zu Manifesten, Pfaden und Referenzstatus stehen im
[Paket- und Referenzvertrag](#paket--und-referenzvertrag).

## Sets, Auswahl und Budgets

`plan_suite(path: str | Path) -> dict` liest ein TOML-Set. Pflichtfelder sind
`schema_version = 1`, `name`, `profile`, positive ganzzahlige `repetitions`,
`agents` (alternativ `agent_pairs`), `sources` und `output`. Relative Quell-, Agenten- und Ausgabepfade
beziehen sich auf die Set-Datei. Kommandoargumente werden als Daten unverändert
gelesen; eine Ausführungsumgebung legt erst der Runner fest.

Unterstützt sind lokale Quellen `[[sources]]` mit `path`.
Installierte Szenariopakete und `builtin:...`-Quellen gehören zum späteren
Ausbau und werden derzeit ausdrücklich als nicht unterstützte Quellen gemeldet.
Inhaltlich identische Quellen desselben Namespace werden zusammengeführt;
unterschiedliche Inhalte oder Versionen desselben Namespace werden abgelehnt.
Die Paketidentität verwendet SHA-256 über sortierte relative Pfade, Modus,
Symlinkziel und Dateiinhalte der Szenarien sowie `package.json`, jeweils mit
Längenrahmung. Verzeichnissymlinks werden beim Planen nicht unterstützt.

Der Planner liest Agentenkommandos als Daten und prüft ihre Ausführbarkeit
noch nicht. Benötigte Fähigkeiten richten sich nach dem Auftrag:

| Auftrag | Aufgabenbezogene Fähigkeiten |
| --- | --- |
| Review | `review_output` |
| Phasenbasierte Entwicklung | `workspace_changes`, `phased_submission` |
| SWE-bench-Reparatur | `workspace_changes`, `project_patch` |

Dazu kommen `cancel` und die Fähigkeiten für die gewählten Budgets
(`wall_time`, `tool_calls`, gegebenenfalls `token_usage` und `cost`).
Deklarationen ersetzen keine Adapter-Vertragstests.

`profile = "agent-evaluation"` erzeugt die Bedingung `cubie`.
`profile = "cubie-vs-pytest"` erzeugt je einen Versuch für `cubie` und `pytest`.
Optionale `[[agent_pairs]]` mit `id`, `cubie` und `pytest` ersetzen `agents` und
ordnen jeder Bedingung eine eigene Agenten-TOML zu. Externe Pytest-Developer
benötigen ein Cubie-freies Digest-Image. Der Abschnitt
[Gespiegelte Developer-Aufgaben](#gespiegelte-developer-aufgaben) beschreibt
Zugriffstrennung, Spezialisierung, Freeze und den Abgleich beider Bedingungen.
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

Der aktuelle Runner liest Auswahl und Budgets aus der Set-Datei; zusätzliche
CLI-Overrides gibt es nicht. Szenariobudgets überschreiben Set-Budgets, globale
harte Grenzen bleiben bindend. Harte Token- und Kostenbudgets lassen sich im
Schema beschreiben, werden vom lokalen Runner aber vor Agentenstart abgelehnt.
Vor einer eigentlichen Messung wird die endgültige Suite geplant und eingefroren.

## Berichte und Laufvergleich

Jeder Lauf schreibt einen eigenen Ergebnisordner. Rohes JSONL, stderr,
Phasensnapshots und tatsächliche Testergebnisse bleiben erhalten.
Unter `results/<run_id>/` liegen die folgenden Belege:

| Pfad | Inhalt |
| --- | --- |
| `report.md` | Kriterien, Phasen, Qualitäts-/Prozessurteil und Beleglinks |
| `results.json` | Maschinenlesbare Ergebnisse und Gate-Entscheidungen |
| `manifest.json` | Plan, Eingabeidentitäten und Artefakthashes |
| `inputs/` | Archivierte Suite, Agentenkonfiguration und Szenariopakete |
| `episodes/` | Ausgangsstände, Workspaces, Phasensnapshots, Nachrichten und Evaluatorbeobachtungen |

`completed` bedeutet eine ausgeführte Bewertung, keine Qualitätsfreigabe.
`quality_passed` beschreibt die fachliche Aufgabe, `process_passed` den
Entwicklungsprozess. Eine richtige Lösung ohne nachgewiesene Rotphase kann
fachlich bestehen und den Prozess verfehlen; ohne Prozessbewertung bleibt
`process_passed=null`. Ohne Qualitätsgate bedeutet Exitcode 0 einen vollständig ausgeführten Lauf;
fachliches Durchfallen allein ändert ihn nicht. Die vollständige
[Exitcode-Tabelle](#exitcodes) berücksichtigt zusätzlich Gates.

Führen Sie dasselbe Set nach einer Änderung erneut aus. Verwenden Sie die
beiden vom Kommando ausgegebenen Ergebnisverzeichnisse:

```bash
cubie-bench compare ./results/BEFORE ./results/AFTER
cubie-bench compare ./results/BEFORE ./results/AFTER --format json
```

Der Vergleich liest nur Archive und startet keine Agenten. Er prüft ihre
Dateihashes und den gespeicherten Plan. Paarungen berücksichtigen Aufgabe,
Paketinhalt und Version, Quell-/Auftragskontext, Evaluatorversion, Bedingung,
Wiederholung und Budgets. Agentenkennungen dürfen sich unterscheiden.
Bei mehreren Agenten wählen `--before-agent` und `--after-agent` jeweils die
Konfiguration aus; ohne eindeutige Auswahl wird der Vergleich abgelehnt.

`full` bezeichnet dieselben aufgelösten Versuche, `partial` nur die gemeinsamen
kompatiblen Versuche und `incompatible` das Fehlen kompatibler Paare.
Geänderte Auswahl, Materialien oder Budgets werden sichtbar gemeldet.
Metrikdifferenzen sind `after - before`; fehlende Messungen, offene Bewertungen
und undefinierte Präzision/Recall bleiben `null`. Es gibt keinen künstlichen
Gesamtscore über Review und Entwicklung.

## Basisdatensatz und Pilot

`base-v1` enthält 24 Reviews aus sechs Familien und vier unabhängig entworfene
Projekte mit je drei separat auswählbaren Episoden. Abrechnungs-Export,
Konfigurationspaket und Dokumentindex verwenden Dateien; die Funktionskontrolle
prüft korrelierte Eingabe-/Erwartungspaare. Alle Fälle sind öffentliche
Entwicklungsfälle und potenziell bekannt. Referenzen stehen auf `author_checked`;
menschliche Prüfungen je Fall sind optional. Reale Pilotmessergebnisse stehen aus.

Exportieren und prüfen Sie die installierten Materialien:

```bash
cubie-bench init-base ./scenarios/base
cubie-bench validate ./scenarios/base --check-references
cubie-bench list --package ./scenarios/base
```

Die Referenzprüfung führt vertrauenswürdige Szenarioprogramme in temporären
Arbeitsverzeichnissen aus. Objektive Reviews werden durch eigene pytest-Tests
gegen das jeweilige Referenzurteil geprüft; Developer-Lösungen müssen bestehen
und ihre Mutanten an den benannten Kriterien scheitern. Manuelle
Wartbarkeitsurteile bleiben `manual_required`. Die Programmprüfung ersetzt keine
menschliche Aufnahme; diese ist auch für offizielle Fälle keine Voraussetzung
für Vollständigkeit. `dataset.json` dokumentiert Herkunft, Lizenz, Domäne und
Entwurfsgruppen und wird zusammen mit den Aufgaben gehasht und archiviert.

Erstellen Sie ein Set für Ihren bereits konfigurierten Prozessadapter:

```bash
cubie-bench init-suite ./sets/pilot.toml --preset smoke \
  --agent ./agents/current.toml --package ./scenarios/base
```

`--preset smoke` erzeugt hier die Set-Vorlage für das ausdrücklich angegebene
Paket. Passen Sie Auswahl, Wiederholungen und Grenzen vor der Ausführung an.
Ein begrenztes Review-Set kann beispielsweise so aussehen:

```toml
schema_version = 1
name = "base-review-pilot"
profile = "agent-evaluation"
repetitions = 5
seed = 17
agents = ["../agents/current.toml"]
output = "../results/pilot"

[[sources]]
path = "../scenarios/base"

[select]
ids = ["base-v1/review-correctness-warehouse-correct", "base-v1/review-correctness-warehouse-faulty"]

[budgets]
wall_time_seconds = 300
tool_calls = 20

[limits]
max_runs = 10
max_total_wall_time_seconds = 3000
```

Zwei Wiederholungen eignen sich für die Kalibrierung, fünf sind der vorgesehene
Pilotumfang. Diese Zahlen sind keine Schätzung statistischer Aussagekraft.
`seed` ordnet Projektgruppen reproduzierbar, berücksichtigt explizite Vorgänger
und balanciert beim Profil `cubie-vs-pytest` die zuerst ausgeführte Bedingung je
Aufgabe aus. Modellantworten bleiben möglicherweise nichtdeterministisch.
Der Vergleich verdoppelt die Laufzahl; setzen Sie die globalen Grenzen passend.
Der Plan wird bei unzureichenden Grenzen abgelehnt und niemals gekürzt.
Ohne `seed` bleibt die bisherige deterministische Ausführungsreihenfolge erhalten.

```bash
cubie-bench plan --suite ./sets/pilot.toml --format json
cubie-bench run --suite ./sets/pilot.toml
cubie-bench summarize-pilot ./results/pilot/RUN_ID
cubie-bench summarize-pilot ./results/pilot/RUN_ID --format json
```

`summarize-pilot` liest ausschließlich vollständige Archive. Mehrere Pfade sind
zulässig; dieselbe Versuch-ID darf nicht doppelt vorkommen. Geänderte Quellen,
Evaluatoren, Budgets oder Agentenkonfigurationen unter denselben Kennungen werden
als inkompatibel abgelehnt. Eine geänderte Agentenkonfiguration benötigt eine
andere Agenten-ID. Eigenständige Wiederholungsversuche mit neuen Lauf-IDs bleiben
als zusätzliche Versuche erhalten. Erstversuche werden nicht überschrieben.

Der Bericht trennt Benchmark, Agent und Bedingung sowie fachliche Qualität und
beobachteten Entwicklerprozess. Wiederholungen erhöhen nicht die Zahl unabhängiger
Projektgruppen. Review-Metriken werden erst je Familie und dann gleichgewichtet
über definierte objektive Familienmittel aggregiert. Wartbarkeitsurteile bleiben
separat. Fehlende Werte bleiben `null`; Streuung ist die
Stichprobenstandardabweichung und bei nur einer Beobachtung undefiniert.

Alle begonnenen Versuche bleiben im Nenner der deskriptiven Erfolgsquote.
Infrastrukturfehler werden separat ausgewiesen. `not_started` zählt nur als
geplant. Offene Bewertungen erhalten keine Qualitätsgutschrift; ihre Belege
bleiben unter `pending_adjudications` auffindbar. Kostenberichte unterscheiden
bekannte Teilsummen von vollständigen Gesamtsummen. Der Adapter legt die
Kosteneinheit fest; unbekannte Kosten werden nicht als kostenlose Ausführung
ausgegeben. Harte Token-/Kostenlimits bleiben im lokalen Runner ununterstützt.

## Gespiegelte Developer-Aufgaben

`cubie-vs-pytest` führt dieselben ausgewählten Aufgaben mit denselben Budgets,
Wiederholungen, sichtbaren Ausgangsdateien und unabhängigen Abnahmetests aus.
Mit `agent_pairs` lassen sich pro Bedingung eigene Agenten einsetzen und vor
dem Einfrieren getrennt überarbeiten: Prompts, Werkzeuge, Modelle und Images.
Ein Paar ersetzt das bisherige `agents`-Feld:

```toml
schema_version = 1
name = "developer-benefit"
profile = "cubie-vs-pytest"
repetitions = 3
seed = 17
output = "../results"

[[agent_pairs]]
id = "specialists-v1"
cubie = "../agents/developer-cubie.toml"
pytest = "../agents/developer-pytest.toml"

[[sources]]
path = "../package"

[select]
benchmarks = ["developer_agent"]

[budgets]
wall_time_seconds = 1800
tool_calls = 100

[limits]
max_runs = 100
max_total_wall_time_seconds = 180000
```

Jeder Pfad ist relativ zur Suite. Die Agenten-TOMLs haben unterschiedliche `id`
und dürfen unterschiedliche Kommandos, Modellmetadaten und Images enthalten.
Mehrere `[[agent_pairs]]` erlauben mehrere explizite Vergleiche. Die Paar-ID wird
als `agent_pair_id` in Plan und Ergebnissen archiviert. Gleiche Paar-IDs dürfen
innerhalb einer Suite nicht mehrfach vorkommen. Ohne `agent_pairs` bleibt der
bisherige Vergleich desselben Agenten in beiden Bedingungen verfügbar.

Eine Suite für zwei vorhandene Agenten lässt sich erzeugen:

```bash
cubie-bench init-suite ./sets/comparison.toml --preset smoke \
  --agent ./agents/developer-cubie.toml \
  --pytest-agent ./agents/developer-pytest.toml --package ./package
```

Die Vorlage wählt Developer-Aufgaben und verdoppelt die Laufgrenzen. Ihre kurzen
Smoke-Budgets anschließend für die eigentliche Messung anpassen. Fachliche
Aufträge sollen frameworkneutral formuliert sein; die Agentenkonfiguration
bestimmt, ob EBT oder reguläres Pytest verwendet wird. Das mitgelieferte
Basispaket ist dafür geeignet. Aufgaben und private Referenzen werden nicht
automatisch umgeschrieben.

### Zugriffstrennung

Ein externer Developer-Agent in der Bedingung `pytest` benötigt zwingend
`container_image` mit einem unveränderlichen Image-Digest. Sein Image enthält
Python, Pytest, Projektabhängigkeiten und den Vergleichsadapter, aber weder das
Cubie-Paket noch einen Cubie-Checkout. Eine bloße Promptanweisung genügt nicht.
Beim Start prüft der Runner, dass `qb_cubie` nicht importierbar ist; ein Image mit
installiertem Cubie wird abgelehnt. Die Prüfung gilt für Capability-Probe,
Agentensitzung und die unabhängigen Pytest-Beobachtungen.

In die Agentensitzung werden ausschließlich das sichtbare Aufgabenworkspace
und ein eigenes Belegverzeichnis eingebunden. Host-Checkout, private
Evaluatorablage, andere Episoden, Git-Objekte und Docker-Socket bleiben außerhalb
des Containers. Prozesse laufen mit Ressourcenlimits und auf Unix mit der
Host-UID/GID. Vor der privaten Abnahme wird der gesamte Agentencontainer beendet.
Phasentests und Abnahme laufen in frischen Containern desselben Images ohne
Netzwerk. Dafür braucht auch das Pytest-Image sämtliche Testabhängigkeiten.

Auch für den Cubie-Agenten ist ein eigenes Image empfehlenswert; ein konfiguriertes
`container_image` wird für Sitzung und Tests verwendet. Cubie darf darin als
installiertes Wheel liegen. Der Benchmark-Runner selbst bleibt auf dem Host und
darf Cubie zur Steuerung und Auswertung verwenden.

Der Modellzugang der Agentensitzung benötigt weiterhin Netzwerk. Daher sind die
Images und Adapter Teil des Messvertrags: keine Cubie-Quellen hineinbauen oder
während des Vergleichslaufs nachladen. Die Importprüfung ist keine Suche nach
beliebig versteckten Quellkopien im Image. Builtin-Fakes dienen ausschließlich
dem Offline-Test der Infrastruktur und unterliegen dieser Containerpflicht nicht.

### Beispiel mit den mitgelieferten Ollama-Agenten

Zunächst mit `cubie-bench init-ollama ./study --endpoint ... --model ...` ein
Beispiel exportieren. Der Developer unterstützt bereits `mode="cubie"` und
`mode="pytest"`; seine lokalen Pytest-Werkzeuge benötigen selbst kein Cubie.
Zwei getrennte Laufzeitkonfigurationen erzeugen, bevor die Images gebaut werden:

```python
import copy
import json
import sys
from pathlib import Path

root = Path("study").resolve()
sys.path.insert(0, str(root / "adapter"))
from ollama_agents.developer.process import prompt_hash

original = json.loads((root / "adapter/developer.json").read_text())
for mode in ("cubie", "pytest"):
    config = copy.deepcopy(original)
    config.update(agent_id=f"developer-{mode}", mode=mode,
                  archive_root="/agent-evidence",
                  endpoint="http://host.docker.internal:11434")
    config["model"]["prompt_sha256"] = prompt_hash(mode)
    (root / f"adapter/developer-{mode}.json").write_text(json.dumps(config, indent=2))
```

Die beiden JSON-Dateien können getrennt angepasst werden. Der Modus bindet das
jeweilige Frameworkwissen in den Modellprompt ein. Für weitergehende
Prompt-/Werkzeugänderungen jeweils eigene Adapterkopien und Images verwenden und
die Prompt-/Adaptermetadaten aktualisieren. Bei Veränderungen nach dem Imagebau
müssen die Images neu gebaut und ihre neuen Digests in die Agenten-TOMLs übernommen
werden. Für gleichen fachlichen Kontext sollten Modell und Inferenzbudgets
möglichst gleich bleiben.

Die Dockerfiles unter `experiments/developer-comparison` kopieren nur den
exportierten Adapter. Nur das Cubie-Image erhält zusätzlich ein Wheel:

```bash
python -m pip wheel --no-deps . --wheel-dir ./study/wheels
docker build -f experiments/developer-comparison/Dockerfile.cubie -t developer-cubie ./study
docker build -f experiments/developer-comparison/Dockerfile.pytest -t developer-pytest ./study
docker image inspect --format '{{.Id}}' developer-cubie
docker image inspect --format '{{.Id}}' developer-pytest
```

Die ausgegebenen `sha256:…`-Digests anschließend in zwei Agenten-TOMLs einsetzen:

```toml
schema_version = 1
id = "developer-pytest"
transport = "jsonl-v1"
container_image = "sha256:<tatsächlicher Imagehash>"
command = ["python", "-I", "/opt/adapter/process.py", "--role", "developer", "--config", "/opt/adapter/developer-pytest.json"]
capabilities = ["workspace_changes", "phased_submission", "cancel", "wall_time", "tool_calls"]
```

Für Cubie `id`, Image und JSON-Pfad entsprechend auf `developer-cubie` setzen.
Den vollständigen `[model]`-Block aus der ursprünglichen Developer-TOML jeweils
übernehmen und `prompt_sha256` aus der zugehörigen neuen JSON-Konfiguration
einsetzen. So wird die tatsächliche Modellsignatur im Handshake geprüft und
archiviert. Projektabhängigkeiten bei Bedarf in beide Images aufnehmen.

### Freeze, Messung und Abgleich

```bash
cubie-bench plan --suite ./study/sets/comparison.toml
cubie-bench freeze --suite ./study/sets/comparison.toml --destination ./study/frozen-v1
cubie-bench run-frozen ./study/frozen-v1 --output ./study/results
cubie-bench compare ARCHIV ARCHIV \
  --before-condition cubie --after-condition pytest \
  --before-agent developer-cubie --after-agent developer-pytest
cubie-bench summarize-pilot ARCHIV
```

`ARCHIV` ist der ausgegebene Laufordner mit `manifest.json` und `results.json`.
Der Vergleich liest vorhandene Ergebnisse, ohne Agenten erneut zu starten.
Beide Bedingungen müssen explizit ausgewählt werden; der bisherige Vergleich
von Agentenversionen paart weiterhin nur dieselbe Bedingung. Verglichen werden
identische Aufgaben, Paketversionen, Ausgangsbäume, Evaluatoren, Budgets,
Wiederholungen und Paar-IDs. Unpassende Zellen bleiben als unvollständiger oder
inkompatibler Vergleich sichtbar. Bei mehreren Agenten je Bedingung sind die
Agenten-IDs explizit auszuwählen.

Qualität, beobachteter TDD-Prozess und Fehlerstatus stehen für beide Versuche im
Ergebnis. `effort_deltas` zeigt zusätzlich Laufzeit, Werkzeugaufrufe, Token und
Kosten als **nachher minus vorher**; unbekannte Messungen bleiben `null`.
Bei `cubie → pytest` bedeutet ein positiver Aufwandunterschied also höheren
Aufwand für Pytest. `summarize-pilot` zeigt Erfolgsquoten und Aufwand getrennt
nach Agent und Bedingung. Unterschiedliche Spezialisten messen den Nutzen der
konfigurierten Arbeitsweisen; der Unterschied ist nicht ausschließlich dem
Framework zurechenbar. Wiederholungen und mehrere unabhängige Projektgruppen
sind für belastbare Aussagen nötig.

### Technische Nachweise

Offline-Verträge: `python -m pytest tests/benchmarks/test_mirrored_developer.py`.
Der echte Docker-Durchstich ist ausdrücklich zuschaltbar:

```bash
CUBIE_TEST_BASELINE_IMAGE=<lokales-Python-mit-Pytest-Image> \
  python -m pytest tests/benchmarks/test_mirrored_developer_container.py
```

Er baut aus dem lokalen Image einen temporären synthetischen Vergleichsagenten,
prüft die Dateisystem-/Importgrenzen und führt beide Bedingungen samt Abnahme
und Archivvergleich aus. Er startet kein Modell und liefert keinen fachlichen
Nutzenbeleg für Cubie.

## SWE-bench

Cubie importiert Python-Reparaturaufgaben aus den offiziellen Full-, Lite- und
Verified-Datensätzen als eigene Szenariopakete. Der durchgängige Weg ist:
Import → Basis-/Gold-Referenzprüfung → Suite → Freeze → Developer-Agent →
unabhängige Patch-Abnahme. Die drei öffentlichen APIs stehen im installierten
Paket unter `qb_cubie.benchmarks` zur Verfügung.

Die importierten Datensätze sind Quellen der regulären Developer-Agent-Benchmark.
Sie unterstützen auch `cubie-vs-pytest` mit getrennt spezialisierten
`agent_pairs`; siehe [gespiegelte Developer-Aufgaben](#gespiegelte-developer-aufgaben).
Dabei bleiben Reparaturprofil, Referenzfreigabe und unabhängige Patch-Abnahme
erhalten.

### Import

```python
from qb_cubie.benchmarks import import_swebench, plan_swebench_import

config = {
    "schema_version": 1,
    "dataset_name": "SWE-bench/SWE-bench_Lite",
    "revision": dataset_commit,  # vollständiger geprüfter 40-stelliger Commit
    "split": "test",
    "cache_dir": "/data/swebench-cache",
    "offline": False,
    "namespace": "swebench-lite-study",
    "version": "1.0.0",
    "instance_ids": selected_instance_ids,
    "seed": 17,
    "include_hints": False,
    "on_error": "fail",
    "process_profile": "issue_resolution",
    "harness_revision": harness_commit,
}
plan = plan_swebench_import(config)
result = import_swebench(config, "/data/scenarios/swebench-lite-study")
```

Für Download und anschließende Messung installieren Sie
`python -m pip install 'qb-cubie[benchmarks,swebench]'`; der Downloadadapter
benötigt das Extra `swebench` für Parquet. Er liest die
Metadaten und Parquetdateien an der exakten Hugging-Face-Revision, beschafft die
Git-Objekte von GitHub und veröffentlicht geprüfte Snapshots atomar im Cache.
Fehlende eindeutige Datensatz- oder Repositorylizenzen blockieren den Abruf;
der Adapter erfindet keine Lizenz. Repositorylizenzen werden für die bezogenen
Commits über die GitHub-Lizenzmetadaten geprüft. GitHub-Ratenlimits können die
Beschaffung großer Quellen begrenzen. Unbekannte Parquetlayouts werden abgelehnt.
Der aktuelle Adapter beschafft die Git-Objekte des ganzen verlangten Splits;
eine Auswahl reduziert anschließend den Export, nicht diesen Beschaffungsaufwand.

Ein vollständiger lokaler Snapshot im [unten beschriebenen Format](#loadervertrag-und-lokaler-snapshot)
kann mit `snapshot` angegeben werden. Dafür werden weder Parquetbibliothek noch Docker benötigt.
`offline=True` ist der Standard und verwendet ausschließlich lokale Daten.
Ein wiederholter Import braucht ein neues Zielverzeichnis.

Das Paket enthält den versionierten Basisstand ohne `.git`. Gold-Patch,
Test-Patch und Rohdaten bleiben privat unter `evaluator/`. Issue-Text und
sichtbare Basistests gehen an den Agenten; optionale Hints sind eine ausdrücklich
andere Messbedingung. `load_package` prüft Dateiinventar, Hashes, Modi und
Symlinkziele. Verschieben verändert die Gültigkeit nicht.
Der bestehende Messpfad verlangt derzeit reguläre Dateien: sichere interne
Symlinks sind importierbar, werden für eine Messung aber ausdrücklich abgelehnt.

### Loadervertrag und lokaler Snapshot

`plan_swebench_import` und `import_swebench` verwenden dieselbe Konfiguration.
Unbekannte Felder werden abgelehnt. Neben den Feldern im Beispiel gelten:

| Feld | Regel |
| --- | --- |
| `schema_version`, `dataset_name` | Version `1`; ausschließlich die offiziellen Python-Quellen `SWE-bench/SWE-bench`, `SWE-bench/SWE-bench_Lite`, `SWE-bench/SWE-bench_Verified`. |
| `revision`, `harness_revision`, `split` | Vollständige 40-stellige hexadezimale Commits; expliziter vorhandener Quellsplit. |
| `snapshot`, `cache_dir`, `offline` | Optionaler vollständiger lokaler Snapshot; lokaler Cache; Offlinebetrieb standardmäßig `true`. Fehlende lokale Daten ergeben dann einen Fehler ohne entfernten Abruf. |
| `namespace`, `version` | Eigene Cubie-Paketidentität; nichtleere Version. |
| `instance_ids`, `repositories` | Eindeutige Listen; fehlend/leer bedeutet alle. Filter werden mit UND verknüpft, unbekannte explizite IDs sind Fehler. Repositoryform ist `owner/name`. |
| `limit`, `seed` | Optionales positives ganzzahliges Limit; ganzzahliger Seed, Standard `0`. Boolesche Werte gelten nicht als Zahlen. |
| `include_hints`, `on_error` | Hints standardmäßig `false`; Fehlerpolitik standardmäßig `fail`, alternativ ausdrücklich `skip`. |
| `process_profile` | Ausschließlich `issue_resolution`. |

Ein Snapshot enthält `source.json`, `records.jsonl` und lokale Git-Speicher unter
`repos/`. `source.json` enthält `schema_version=1`, `dataset_name`, `revision`,
`split`, `records_sha256`, `dataset_license`, `repository_licenses` (Repo → Lizenz)
und `repositories` (Repo → relativer Git-Speicherpfad). Quelle und Konfiguration
müssen übereinstimmen; der JSONL-Hash wird vor dem Parsen geprüft. Repositorypfade
dürfen auch nach Symlinkauflösung den Snapshot nicht verlassen.

Jede JSONL-Zeile benötigt nichtleere Strings für `instance_id`, `repo`,
`base_commit`, `version`, `problem_statement`, `patch` und `test_patch`.
`instance_id` ist eine sichere einzelne Cubie-ID, Commits sind vollständige
40-stellige Hexwerte. `environment_setup_commit` ist optional; fehlend/leer
wird `null`, andernfalls muss auch dieser Commit lokal verfügbar sein.
`FAIL_TO_PASS` und `PASS_TO_PASS` sind Listen oder JSON-kodierte Listen eindeutiger
nichtleerer Test-IDs ohne Überschneidung. `FAIL_TO_PASS` darf nicht leer sein;
leeres `PASS_TO_PASS` wird als fehlende Regressionsabdeckung ausgewiesen.
Doppelte Instanzen, ungültige Pflichtfelder und ungeklärte Lizenzen sind Fehler.
Zusatzfelder bleiben gehasht im privaten Rohdatensatz und gelangen nicht
automatisch zum Agenten; eine inkompatible Harnessauswertung scheitert sichtbar.

Nach Quell-/Schemaprüfung und Filtern werden Kandidaten nach ID sortiert.
Bei einem Limit entscheidet `SHA256(UTF8(str(seed) + "\n" + instance_id))`,
bei Gleichstand die ID; die Auswahl wird wieder nach ID ausgegeben. Der Plan
enthält `source`, `selection`, begründete `excluded`-Einträge und `plan_sha256`.
Der Hash bindet Quellbytes, normalisierte Datensätze, Auswahl, Hints, Harness,
Paketidentität und Loadervertragsversion, aber keine absoluten lokalen Pfade.
Plan und Importmanifest enthalten private Evaluationsdaten.

Der Import veröffentlicht das vollständige geprüfte Paket atomar und überschreibt
kein vorhandenes Ziel. `skip` erlaubt ausschließlich einzelne Materialisierungsfehler
nach erfolgreicher Planung; Schema-, Lizenz-, Integritäts- und Pfadfehler bleiben
fatal. Jede Auslassung nennt Instanz, Stage und Grund; ein leeres Paket gilt als
Fehler. Die Rückgabe enthält `package`, `plan_sha256`, sortierte `imported`,
`skipped` und `status="complete"` bzw. `"partial"`.

Der sichtbare Baum stammt exakt aus `base_commit`, ohne Git-Historie oder
Submodule. Gold-/Test-Patches und nachträgliche Tests bleiben beim Evaluator.
`swebench-import.json` bindet Quelle, Plan und das Dateiinventar. Der Katalog
kennzeichnet öffentliche Fälle als potenziell bekannte `development`-Daten;
Upstream-`test` erzeugt kein `held_out`. Issues desselben Repositorys bilden eine
Projektgruppe. Überlappende Instanzen aus Full/Lite/Verified werden vor einer
gemeinsamen Messung erkannt. Referenzen beginnen mit `unvalidated` und leeren
`human_reviews`; der Name Verified ersetzt keine unabhängige Prüfung.

### Ausführende Referenzfreigabe

```python
from qb_cubie.benchmarks import validate_swebench_references

reference = validate_swebench_references(result["package"])
assert reference["valid"]
print(reference["report"])  # separate dauerhafte Belegablage
```

Der Standardexecutor setzt Docker, einen aus exakt `harness_commit`
installierten offiziellen `swebench`-Harness mit VCS-Provenienz und vorher
provisionierte Instanzimages voraus. Das Harness wird separat installiert,
beispielsweise mit `pip install "swebench @ git+https://github.com/SWE-bench/SWE-bench.git@<commit>"`.
Seine Provisionierungswerkzeuge erzeugen bzw. beziehen die benötigten Images.
Cubie installiert keine Repositoryabhängigkeiten auf dem Host und baut beim
Referenzaufruf keine Images implizit. Fehlende Images und inkompatible
Harness-/Datensatzschemata führen zu einer Diagnose. Unterstützt sind die
metadatenbasierten Harness-Schnittstellen `harness.utils.make_test_spec` sowie
die ältere Python-Schnittstelle `harness.test_spec.test_spec.make_test_spec`.
Teilweise deklarierte Ausführungsmetadaten werden abgelehnt.

Basis und Gold erhalten frische Container und neue Versuchskennungen. Tests
laufen ohne Netzwerk, Hostmounts oder Daemon-Socket; CPU, Speicher, Prozesszahl
und Laufzeit sind begrenzt. Der tatsächlich aufgelöste Imagehash wird vor dem
Start an den Request gebunden und bei der Messung erneut geprüft. Fehlende,
übersprungene oder fehlerhafte Tests geben keine Referenzfreigabe. Referenzbericht
und Belege liegen getrennt vom unveränderten Paket. Die Belegablage sollte in
den eigenen dauerhaften Studienbereich aufgenommen werden; die API legt sie in
einem Geschwisterverzeichnis `<paketname>.reference-reports/attempt-…` ab und
löscht sie nicht selbst.

### Developer-Agent und Suite

Ein Reparaturadapter benötigt `project_patch`, `workspace_changes`, `wall_time`,
`tool_calls` und `cancel`. Er erhält eine einzige JSONL-Anfrage mit
`phase="repair"`, `process_profile="issue_resolution"`, `output_format="patch_v1"`.
Er liefert `submission.patch` als einziges Artefakt mit SHA-256. Der Patch kann
mehrere Produktionsdateien betreffen. Private Tests werden unabhängig vom
Agentenworkspace im Evaluator angewendet. Änderungen an Tests oder
Collectionkonfiguration werden in dieser ersten Stufe abgelehnt.

Der mitgelieferte Ollama-Developer unterstützt dafür `mode="repair"` in seiner
JSON-Konfiguration. `prompt_hash("repair")` aus
`ollama_agents.developer.process` bindet den eigenen Prompt und die Implementierung.
Dieser Modus erkundet große Repositorys mit paginierten Dateilisten,
Dateiausschnitten und Textsuche. Er schreibt ausschließlich den Patch und behauptet
keine beobachtete TDD-Phase. Die bisherigen Modi `cubie` und `pytest` bleiben für
die bisherigen Entwicklungsaufgaben verfügbar.

Reparaturadapter laufen in einem eigenen Image mit unveränderlicher Identität.
Das Image enthält Adaptercode und Konfiguration. Der Runner bindet nur den
sichtbaren Workspace und eine anfangs leere Belegablage nach `/agent-evidence`
ein; Paket, Evaluator und Git-Cache werden nicht eingebunden. Setze
`archive_root="/agent-evidence"` in der Ollama-Konfiguration. Ein auf dem Host
bereitgestelltes Ollama kann über `host.docker.internal` erreicht werden, sofern
der Dienst Verbindungen aus dem Docker-Netz annimmt. Seine Modellparameter und
Identität werden wie bei den bisherigen Agenten eingefroren.

Ein [Dockerfile](../experiments/ollama-agents/swebench/Dockerfile) liegt bei.
Baue zuerst das Cubie-Wheel nach `dist/` und lege `repair-config.json` mit
explizitem Modell, Endpoint, Parametern, Adapterversion und Repair-Prompthash in
der Repositorywurzel ab. Dann beispielsweise:

```bash
docker build -f experiments/ollama-agents/swebench/Dockerfile -t cubie-repair-adapter .
docker image inspect cubie-repair-adapter --format '{{.Id}}'
```

Der ausgegebene tatsächliche Digest wird in `agent.toml` eingetragen:

```toml
schema_version = 1
id = "ollama-repair"
transport = "jsonl-v1"
container_image = "sha256:<64-stelliger tatsächlicher Imagehash>"
command = ["python", "-c", "from ollama_agents.developer.process import main; raise SystemExit(main('/adapter/config.json'))"]
capabilities = ["project_patch", "workspace_changes", "wall_time", "tool_calls", "cancel"]
```

Die Suite verweist zusätzlich auf den erfolgreichen Referenzbericht:

```toml
schema_version = 1
name = "swebench-lite-study"
profile = "agent-evaluation"
repetitions = 1
output = "results"
agents = ["agent.toml"]
sources = [{path = "package", reference_report = "reference-evidence/report.json"}]
```

```python
from qb_cubie.benchmarks import freeze_suite, run_frozen_suite

freeze_suite("suite.toml", "frozen-study")
results = run_frozen_suite("frozen-study", "results")
```

Freeze archiviert das Paket, die Referenzbelege und die Digestkonfiguration des
Adapters. Das Adapterimage selbst bleibt eine separat bereitzustellende
Laufzeitvoraussetzung. Eine fehlende Freigabe, andere Paketbytes oder überlappende
Full-/Lite-/Verified-Instanzen werden vor Agentenstart abgelehnt. Die Prüfung
unterscheidet fachlich rote Tests von fehlgeschlagener Infrastruktur. Berichte
zeigen `process_passed=null`, Repositorygruppen, Herkunft, Bekanntheit,
Ausschlüsse und fehlende Regressionsabdeckung. Reparaturqualität wird getrennt
von TDD- und Review-Ergebnissen ausgewiesen.

### Nachweisgrenze

Die regulären Tests verwenden synthetische lokale Git-Repositories und
kontrollierte Executor-/Modellantworten. Sie belegen keine reale SWE-bench-
Leistung. Reale Downloads aller drei Quellen, echte Containergrenzen und ein
installierter Messdurchstich sind noch nachzuweisen. Zur technischen Abnahme
gehören eine eingefrorene kleine Auswahl aus jeder der drei Quellen mit
archivierten Revisionen und Lizenzen, identische Offline-Wiederholungsimporte
sowie echte Basis-Rot-/Gold-Grün-Containerläufe. Gegenproben müssen falsche Patches,
fehlende Tests, Netzwerk-/Dateisystemgrenzen, Ressourcenabbrüche und neue
Versuchskennungen ohne veraltete Cacheerfolge zeigen. Ein Wheel-Durchstich muss
ein verschobenes Mehrdateienpaket laden, einfrieren und mit einem Agenten messen;
Referenzlecks, fehlende Referenzberichte und Doppelauswahl werden geprüft.
Reparaturqualität bleibt ohne TDD-Gutschrift. Eine echte Modellinferenz ist für
diese technische Abnahme nicht erforderlich. Die
[Abnahmematrix](../tests/docs_tmp/BENCHMARK_CASES_SWE_BENCH.md) dokumentiert die
Offline-Gegenproben; sie ersetzt diese Integrationsnachweise nicht.

### SWE-bench im Cubie-/Pytest-Vergleich

Die importierten Pakete verwenden denselben Messpfad mit
`benchmark="developer_agent"`. Sie können in einer `cubie-vs-pytest`-Suite mit
getrennten `agent_pairs` stehen. Unter `[[sources]]` wird zusätzlich der gebundene
`reference_report` angegeben. Beide Adapter benötigen `project_patch` und geben
einen vollständigen `submission.patch` ab; ihre Digest-Images bleiben getrennt.
`process_profile="issue_resolution"` und die unabhängige FAIL-/PASS-TO-PASS-Abnahme
bleiben erhalten. Es gibt dafür keine TDD-Gutschrift und keine künstlichen
Einmodul-Mutanten. Öffentliche Herkunft und mögliche Modellbekanntheit bleiben
im Archiv dokumentiert.

## Messbetrieb, Gates und CI

Ein Team kann einen einzelnen Agenten regelmäßig mit seinem eigenen Set prüfen.
Ein zweiter Agent oder ein Cubie-/pytest-Vergleich ist dafür nicht erforderlich.
Der Plan legt Aufgaben, Bedingungen, Wiederholungen, Reihenfolge und Budgets
fest. `run` und `run-frozen` unterscheiden vollständige Ausführung und
erreichte Qualitätsgrenzen.

### Qualitätsgrenzen im Set

Ergänzen Sie eine oder mehrere Gate-Tabellen in Ihrer Suite:

```toml
[[gates]]
id = "shipping-quality"
metric = "quality_pass_rate"
operator = "gte"
threshold = 1.0
select.types_any = ["shop/shipping"]

[[gates]]
id = "developer-process"
metric = "process_pass_rate"
operator = "gte"
threshold = 1.0
select.benchmarks = ["developer_agent"]
```

`select` verwendet dieselben Typ-, Tag-, ID- und Splitfilter wie die Suite.
Ein Gate betrachtet nur bereits geplante Versuche. Mehrfachtypen vervielfachen
keine Beobachtung. Prozessgates betrachten Developer-Versuche; ihre Population
darf nicht leer sein. Unbekannte Metriken, unzulässige Schwellen, doppelte IDs
und leere Populationen werden schon vor einem Fähigkeiten-Handshake abgelehnt.

Unterstützt sind `quality_pass_rate`, `process_pass_rate`, `precision`, `recall`
und `cost`, jeweils mit `gte` oder `lte` einschließlich Gleichheit.
Raten liegen zwischen null und eins. Präzision und Recall werden als Mittel
der gewählten kompatiblen Einzelbeobachtungen geprüft; die familiengewichtete
Pilotzusammenfassung bleibt eine gesonderte Auswertung. Kosten sind die Summe
der gewählten Kostenangaben, deren Einheit Ihr Adapter konsistent halten muss.
Ein Kostengate bewertet archivierte Kosten; es setzt keine harte
Ausgabengrenze beim Provider durch. Der lokale Runner setzt Laufzeit und seine
eigenen Werkzeugaufrufe durch; harte Token- oder Providerkostenlimits werden
weiterhin nicht unterstützt.

Alle Pflichtwerte müssen vorhanden und abgeschlossen bewertet sein. Fehlende
Versuche, Timeouts, offene Nachbewertungen und undefinierte Metriken bestehen
kein Gate. Eine fehlende Präzision ist nicht eins und eine unbekannte
Kostenangabe ist nicht null. Ohne Gates bleibt ein vollständig ausgeführter
Lauf reine Berichterstattung und erhält keine automatische Qualitätsfreigabe.

`results.json` enthält `gate_evaluation` mit `execution_complete`, `gate_status`
und den einzelnen Gates samt Istwert, Grund, Beobachtungszahlen und Belegen.
`report.md` erklärt dieselben Entscheidungen mit relativen Links.
Eine bestehende Messung lässt sich schreibgeschützt erneut prüfen:

```bash
cubie-bench evaluate-gates results/LAUF-ID --format json
```

### Exitcodes

| Code | Bedeutung |
| --- | --- |
| `0` | Vollständige Ausführung; Gates bestanden oder nicht konfiguriert |
| `2` | Konfigurationsfehler |
| `3` | Unvollständige, ungültige oder fehlerhafte Ausführung |
| `4` | Vollständige Ausführung, aber mindestens ein Gate verfehlt |

Code 3 hat Vorrang vor Code 4. So kann die CI Qualitäts- und Laufprobleme
getrennt behandeln und in beiden Fällen Belege sichern.

### Konfiguration vor der Messung einfrieren

```bash
cubie-bench plan --suite sets/team.toml --format json
cubie-bench freeze --suite sets/team.toml --destination frozen/team --format json
cubie-bench run-frozen frozen/team --output results/team --format json
```

`freeze` führt weder Agenten noch Fähigkeiten-Handshakes aus. Das neue Bundle
enthält Aufgaben, sichtbare Quellen, Evaluatorreferenzen, Herkunftskataloge,
Agentenkonfigurationen und lokal referenzierte Adapterdateien. Zusätzliche
lokale Helfermodule oder Ressourcen werden im Agenten-TOML ausdrücklich mit
`adapter_files = ["helpers", "settings.json"]` angegeben. Die Pfade beziehen
sich auf `cwd`; sie müssen darin bleiben und dürfen keine Symlinks sein.
Nur ausdrücklich referenzierte Dateien werden übernommen. Geben Sie dort
keine Zugangsdaten oder geheimen Konfigurationsdateien an. Interpreter,
installierte Adapterpakete und weitere externe Dienste werden durch die
bereitgestellte Laufumgebung bestimmt.
Ein Adapteraufruf über Cubies eigenen Python-Interpreter wird dabei auf den
bereitgestellten Laufzeit-Interpreter umgestellt; sein ursprünglicher absoluter
Hostpfad wird nicht als Voraussetzung in das Bundle übernommen.

Das Manifest `measurement.json` bindet die Dateiinhalte und ihre Modi,
den aufgelösten Plan einschließlich Seed, Budgets und Gates sowie die
Laufumgebung. Die Ausgabe von `freeze` enthält `measurement_sha256`, den Hash
dieses Manifests. Derselbe Eingabestand erzeugt unabhängig vom Zielverzeichnis
dieselbe Identität. Ein bestehendes Bundle wird nicht überschrieben.
Zusätzliche, fehlende oder veränderte Dateien verhindern den späteren Start.

Das Bundle kann verschoben und ohne die Originaleingaben ausgeführt werden.
`run-frozen` arbeitet mit temporären Kopien; Ergebnisse dürfen nicht in das
Bundle geschrieben werden. Jeder Lauf erhält ein eigenes Ergebnisverzeichnis.
Das vollständige Bundle wird darin unter `measurement/` archiviert und das
Laufmanifest bindet dessen Identität. Vergleich, Gateprüfung und Pilotbericht
prüfen diese Bindung erneut. Hashes ermöglichen Nachprüfung, sind aber keine
Signatur eines fremden Herausgebers.

Python-Version, Cubie-Quellcodefingerprint und ein bekannter Wheel-Hash müssen
zur Laufumgebung passen. Beim Quellcheckout kann `wheel_sha256` unbekannt sein.
Ein gefundener Checkout-Lock wird als `dependency_lock_sha256` erfasst; ohne
Checkout bleibt er unbekannt. Ein Fingerprint installierter Distributionsnamen
und Versionen wird zusätzlich gebunden. Die Übereinstimmung der Installation
mit dem Lock ist damit noch nicht bewiesen (`dependency_lock_verified=false`).
Das Bundle provisioniert keine Abhängigkeiten. Installieren Sie diese in Ihrer CI mit
einem vorab festgelegten Lockfile oder Image. Ein Seed fixiert die Planung,
nicht die Antworten externer Modelle.

### Eigener CI-Messjob

Der Repository-Workflow `.github/workflows/benchmarks.yml` wird ausdrücklich
per `workflow_dispatch` gestartet, getrennt von Push- und Pull-Request-Tests.
Er erwartet ein zuvor bereitgestelltes Artefakt aus demselben Repository und
den vorab geprüften `measurement_sha256`. Verpacken Sie das Bundle als Tar,
damit beim Artefakttransport Dateimodi erhalten bleiben:

```bash
tar -cf measurement.tar -C frozen/team .
```

Stellen Sie `measurement.tar` über einen eigenen Provisionierungsjob als
GitHub-Artefakt bereit. Beim manuellen Start wählen Sie dessen Lauf-ID,
Artefaktname und Manifest-Hash. Der Messjob stellt die eingefrorene
Python-Version bereit, installiert die gesperrten Entwicklungsabhängigkeiten
und startet `run-frozen` mit einem expliziten Ergebnisziel. Der Checkout muss
dem eingefrorenen Cubie-Quellstand entsprechen. Bei einem aus einem Wheel
erzeugten Bundle geben Sie zusätzlich `wheel_artifact_name` an: ein Artefakt
aus demselben Provisionierungslauf mit genau diesem Wheel. Der Job prüft den
Wheel-Hash und installiert es ohne erneute Abhängigkeitsauflösung.
Provideranbindung und benötigte Dienste provisionieren Sie in Ihrer
vertrauenswürdigen Messumgebung; sie gehören nicht als Zugangsdaten in das
Bundle. Der Job hat ein Zeitlimit von 60 Minuten. Planen Sie Laufbudgets so,
dass anschließend Zeit für die Archivierung bleibt.

Ein `always()`-Upload bewahrt Rohdaten, Berichte und eingefrorene Konfiguration
auch bei einem Gatefehlschlag oder abgebrochenen Lauf. Der Exitcode wird nicht
unterdrückt. Die Belege liegen in `benchmark-evidence.tar`, damit auch beim
Download ihre für die Integritätsprüfung relevanten Dateimodi erhalten bleiben.
Das Archiv enthält außerdem Checkout-Commit, Lockfile und gegebenenfalls das
bereitgestellte Wheel. Für eine andere CI gelten dieselben Schritte: geprüften Stand
bereitstellen, Umgebung fixieren, Bundle prüfen und ausführen, Belege auch bei
Fehlern sichern. Der lokale Runner setzt weiterhin vertrauenswürdige Agenten
und Evaluatoren voraus; eine allgemeine Containerisolation für lokale Läufe bleibt
gesonderte Infrastruktur. Die verpflichtenden Containerpfade für externe
Pytest-Developer und SWE-bench sind in den jeweiligen Abschnitten beschrieben.

Die echte pytest-Ausführung bleibt ausdrücklich freizuschalten:

```bash
python -m pytest tests/benchmarks -m agent_benchmark \
  --run-agent-benchmarks --suite sets/team.toml
```

Im Cubie-Repository ist das Plugin bereits eingebunden. Für eigene Tests laden
Sie `-p qb_cubie.benchmarks.pytest_plugin` und markieren die Episoden mit
`agent_benchmark`, zusätzlich optional `review_agent` oder `developer_agent`.
Ohne Freischaltung werden sie übersprungen, auch bei einer Markerwahl.
Sammlung startet keinen Adapter. Bei tatsächlicher Freischaltung führen eine
fehlende Suite oder ein nicht verfügbarer Adapter zum pytest-Nutzungsfehler
(pytest-Exitcode 4). Die optionale Fixture `agent_benchmark_result` führt das
konfigurierte Set einmal je pytest-Sitzung aus.

### Zurückgehaltene Aufgaben und Produktmessung

Eigene zurückgehaltene Pakete werden separat versioniert und erst zur Messung
bereitgestellt. Ihr Herkunftskatalog deklariert
`publication_status = "held_out"`; die Szenarien haben `split = "held_out"`.
Herkunft, Lizenz, Entwurfsgruppe und `potentially_known` bleiben explizit.
Der Katalog geht in Paketidentität, eingefrorene Konfiguration und Archiv ein.
Der Agent erhält den sichtbaren Auftrag und Quellen; Referenzen, Mutanten und
zusätzliche Testdaten bleiben beim Evaluator. Diese Exporttrennung ist keine
OS-Sicherheitsgrenze gegenüber einem bösartigen lokalen Agenten.

Veröffentlichte Basisfälle bleiben potenziell bekanntes Entwicklungsmaterial.
Eine bloße Änderung ihres Splits macht sie nicht zu ungesehenen Messfällen.
Auch eine Deklaration `potentially_known = false` beweist keine Unbekanntheit.
Die mitgelieferten Testfixtures simulieren diese Metadaten und veröffentlichen
keinen tatsächlichen privaten Messdatensatz.

Für eine bestätigende Produktmessung folgen auf dokumentierte
Referenzvalidierung und einen realen Pilot vorab festgelegte primäre Kennzahlen,
ein praktisch relevanter Mindestvorteil beim Aufwand und eine tolerierte
Qualitätsabweichung. Diese Festlegungen werden vor Sichtung neuer
zurückgehaltener Ergebnisse eingefroren. Qualität, Prozess und Aufwand bleiben
getrennt; Wiederholungen erhöhen nicht die Zahl unabhängiger Projekte.
Ein grünes Team-Gate oder ein deterministischer Fake-Lauf ersetzt diesen
Produktnachweis nicht. Die Grenzen und offenen methodischen Abnahmen aus dem
Benchmark-Konzept gelten weiter.

## Nachbewertung und Betriebsregeln

### Nachbewertung

`apply_adjudication(archive_path, decisions_path, destination)` aus
`qb_cubie.benchmarks` veröffentlicht ein neues, separat prüfbares Archiv.
Das Ursprungsarchiv bleibt unverändert. Die Entscheidung muss folgende Form haben:

```json
{
  "schema_version": 1,
  "manifest_sha256": "SHA-256 des Ursprungsmanifests",
  "evaluator_id": "Name und Konfiguration des Bewertungsverfahrens",
  "version": "1",
  "runs": {
    "RUN-ID": {
      "evaluation_sha256": "SHA-256 von episodes/.../review-evaluation.json",
      "reason": "Begründete Bewertung von Mechanismus und Auswirkung",
      "matches": [0, null, 0]
    }
  }
}
```

`matches` enthält für jedes Finding der Originalantwort den nullbasierten Index
seines Referenzfehlers oder `null` für einen unbestätigten Befund. Mehrfachnennungen
desselben Referenzfehlers erhöhen Trefferzahl und Recall nicht. Kriterienkennung,
Pfad und Symbol müssen übereinstimmen. Mechanismus und Auswirkung beurteilt das
angegebene Verfahren; der Import selbst ist kein semantischer Evaluator.
Neue plausible Fehler erfordern zuerst eine versionierte Referenzkorrektur und
die Neubewertung aller davon betroffenen Antworten. Nicht importierte Läufe
behalten ihren Bewertungsstand. Unvollständige Zuordnungen werden nicht importiert.

Die Bewertung soll Modell und Bedingung nicht kennen; Zuordnungen können
automatisch oder optional menschlich erstellt werden. Die ursprünglichen
Antworten und Bewertungsbelege bleiben erhalten. `adjudication.json` bindet den
neuen Stand an die ursprünglichen Bytes; `adjudication-parent.json` erhält
ursprüngliches Manifest und Ergebnis. `results.json`, Bericht und Gates werden
neu berechnet. `evaluate_gates`, `summarize_pilot` und Archivprüfung können das
abgeleitete Archiv wie andere Ergebnisarchive lesen. In einer Auswertung darf
nur ein Bewertungsstand desselben Versuchs verwendet werden.

### Laufprovenienz

Freeze und Ergebnismanifest erfassen Repository-Commit und Dirty-Status getrennt.
Ein Diffhash bindet Git-Status und versioniertes Diff; Inhalte unversionierter
Dateien erfasst er nicht. Szenario-, Adapter- und Quellhashes binden das tatsächlich
verwendete Material. Ohne Checkout bleiben Git-Angaben unbekannt.
Lockfile-Hash und Fingerprint installierter Distributionen sind unter
[Konfiguration einfrieren](#konfiguration-vor-der-messung-einfrieren) beschrieben.
Ein Image-Digest bleibt ohne Container-Runner unbekannt.

### Abbruch und Wiederholung

1. Vor dem ersten Modellaufruf ein Studienjournal außerhalb der temporären
   Arbeitsverzeichnisse anlegen. Studienkennung, geplante Zellen, Versuchskennung,
   Startzeit und Zielpfade für Runner- und Adapterarchive erfassen.
2. Nach einem Abbruch Fragmente unverändert sichern und als `interrupted_unsealed`
   kennzeichnen. Ein Fragment ohne gültiges Manifest ist kein vollständig
   prüfbares Runnerarchiv und darf nicht in die Pilotfreigabe importiert werden.
3. Lokale Prozessbäume beenden. Bei HTTP-Abbruch über den Provider prüfen, ob die
   Inferenz beendet ist. Ohne Nachweis keinen überlappenden Ersatzversuch starten.
4. Eine Wiederholung erhält eine neue Versuchskennung und den Verweis
   `retry_of` auf den ursprünglichen Versuch sowie einen Grund. Sie überschreibt
   weder Fragmente noch gültige Archive. Ein Journal mit zusätzlichen gestarteten
   Versuchen erfüllt das strikte Zwei-/Fünf-Protokoll nicht automatisch; dazu ein
   neues Studiendesign mit vollständig ausgewiesenen Versuchen festlegen.
5. Vor Auswertung Journal gegen alle Runner- und Adapterarchive abgleichen.
   Fehlende Belege und nicht gestartete Zellen ausweisen. Die vorhandene
   Pilotfreigabe prüft nur übergebene Archive, nicht dieses externe Journal.

### Belegaufbewahrung

Für weiter verwendete Ergebnisse gilt als lokale Standardregel:

- Primärablage unter `artifacts/benchmarks/STUDIENKENNUNG/` außerhalb von `/tmp`;
  Runnerarchive, Adapterarchive, Messbundles, Journal und Entscheidungen gemeinsam.
- Nur ausführende Person bzw. CI-Dienst dürfen schreiben. Bewertende erhalten
  Lesezugriff; private Referenzen und zurückgehaltene Aufgaben bleiben separat
  zugriffsbeschränkt. Zugangsdaten gehören nicht in Belege.
- Nach Abschluss eine zweite, getrennte Ablage mit unveränderlichen Archivkopien
  und SHA-256-Inventar erzeugen. Studienverantwortliche dokumentieren Ziel und Datum.
- Vor Ergebnisverwendung die Kopie in ein frisches Verzeichnis wiederherstellen,
  Inventar und `read_archive` prüfen; Datum und Ergebnis im Journal festhalten.
- Belege mindestens zwölf Monate nach letzter Ergebnisverwendung behalten;
  projektspezifisch längere Vorgaben gehen vor. Löschung ist eine separate
  bewusste Entscheidung und kein automatischer Teil eines Messlaufs.

Diese Regeln sind festgelegt, aber keine Behauptung über bereits erfolgte
Sicherungen, externe Zugriffsrechte oder Wiederherstellung alter `/tmp`-Belege.

### Noch benötigte praktische Nachweise

Für reale Pilotmessungen sind ein erreichbarer Provider, eine festgelegte
Agentenkonfiguration, kontrollierte serielle Laufbedingungen und ein geeignetes
Basisdatensatz-Set nötig. Vorläufige Laufzeiten aus parallelen Tests sind keine
Vergleichsmessungen. Zahl unabhängiger Projekte anhand der Pilotstreuung planen;
Wiederholungen ersetzen keine Projekte. Wartbarkeit, offene Bewertungen,
Fehler, Enthaltungen und unbekannte Kosten getrennt ausweisen.

CI-Betrieb benötigt einen tatsächlichen Lauf in der Ziel-CI mit Providerzugriff,
Gatefehler und wiederherstellbaren Artefakten. Ein externer Nutzertest benötigt
eine tatsächlich unvorbereitete Person. Zurückgehaltene Aufgaben benötigen eine
kontrollierte private Herkunft und dürfen nicht durch Umbenennen öffentlicher
Aufgaben entstehen. Diese praktischen Nachweise und eine allgemeine Containerisolation für lokale
Läufe bleiben offen. Verpflichtende Containerpfade für Vergleichs- und
SWE-bench-Aufgaben sind in den jeweiligen Abschnitten beschrieben.

Die bisherige [explorative Ollama-Messung](../experiments/ollama-agents/README.md#explorative-messung-vom-10-november-2026)
umfasst 6 Kalibrierungs- und 15 Pilotepisoden auf öffentlichen Versandkostenaufgaben.
Sie belegt keinen Pilot auf `base-v1`. Für dessen Abnahme sind die versionierten
Referenzen und technischen Gegenproben nachvollziehbar zu prüfen, eine geeignete
Auswahl aus den 24 Reviews und zwölf Developer-Episoden zu begründen und reale
Kalibrierung, Freeze und Messung durchzuführen. `author_checked` genügt;
menschliche Prüfungen sind optional. Ungeklärte Referenzwidersprüche dürfen keine
bestätigten Qualitätsaussagen begründen. Freie Reviewer-Findings benötigen für
semantische Kennzahlen eine dokumentierte Nachbewertung ohne Kenntnis von Modell
und Bedingung, automatisch oder optional menschlich. Der Import versionierter
Zuordnungen ist implementiert; vorhandene reale Antworten sind noch zu bewerten.

Laufprovenienz erfasst Commit, Dirty-Status, Diffhash, gefundenen Lockhash und
installierte Distributionsversionen. Eine nachgewiesene Installation gemäß Lock
und tatsächliche Sicherungs-/Wiederherstellungsbelege vorhandener Archive stehen
aus. Für fremden Code bleibt die allgemeine lokale Containergrenze mit getrenntem
Evaluator und Ressourcenlimits umzusetzen. Temporäre Verzeichnisse und isoliertes
Python bilden keine OS-Sicherheitsgrenze.

Zusätzliche Messziele erfordern eigene Nachweise: Ein Produktvergleich braucht
gepaarte reale Cubie-/pytest-Läufe mit getrennten Agenten-IDs und Prompt-Hashes;
ein kausaler Nutzen der Review-Struktur eine gesonderte Ablation. Bestätigende
Produktnutzenbehauptungen benötigen vorab eingefrorene Kennzahlen und ausreichend
unabhängige, unverbrauchte Projekte. Große Reviewer-Kontexte benötigen ein
belegbares Auswahl-/Auslassungsverfahren. Harte Token-/Kostenlimits,
automatische Provisionierung beliebiger Adapter, Mehrfachfehler-Reviews,
fortlaufende freie Entwicklung und die Zusammenarbeit von Developer und Reviewer
sind zusätzliche Erweiterungen des lokalen Durchstichs. Maßgeblich sind geplante
und eingefrorene Konfigurationsdateien; zusätzliche CLI-Overrides sind nicht
zugesagt.

### Umfang einer Entwicklungsepisode

Implementiert ist ein Inkrement mit eingefrorenen Tests je Episode. Mehrere
Inkremente und fachlich begründete Testrevisionen sind noch nicht implementiert.

## Technische Referenz

Die experimentelle Python-API liegt unter `qb_cubie.benchmarks`. Laden, Planen
und Nachrichtenvalidierung benötigen keine zusätzlichen Abhängigkeiten und
führen keinen Szenariocode aus. Für pytest-Unterprozesse braucht der Runner
das Extra `benchmarks`. Alle Rückgaben sind JSON-kompatible Dictionaries und
Listen. Die Validierung liefert getrennte Momentaufnahmen und verändert die
Eingabe nicht. Fehlerhafte Werte erzeugen `ValueError` mit Feld und Ursache;
NaN, Infinity, doppelte JSON-Schlüssel und unbekannte Schemaversionen werden
abgelehnt.

### Python-Einstieg

```python
from pathlib import Path
from qb_cubie.benchmarks import init_smoke_suite, load_package, plan_suite, run_suite

suite = Path("./sets/python-smoke.toml")
init_smoke_suite(suite)
plan = plan_suite(suite)
print(len(plan["runs"]), plan["total_wall_time_seconds"])
result = run_suite(suite)
print(result["output"])

package = load_package(Path("./scenarios/smoke"))
for scenario in package["scenarios"]:
    print(scenario["qualified_id"], scenario["benchmark"], scenario["types"])
```

Ein reines Planungsbeispiel mit fünf Szenarien liegt unter
[tests/benchmarks/fixtures/phase1](../tests/benchmarks/fixtures/phase1/package.json).
Sein Agentenkommando existiert absichtlich nicht. Für ausführbare Vorlagen dienen
`init_smoke_suite` oder `init-example`.

### Paket- und Referenzvertrag

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

Reviews verwenden `builtin.review_reference_v1`, phasenbasierte
Entwicklerepisoden `builtin.pytest_project_v1`. SWE-bench-Reparaturen verwenden
`external.swebench_v1` mit `process_profile="issue_resolution"`; sie sind
unabhängige Episoden ohne `requires`. Unbekannte oder zum Benchmark unpassende
Evaluatortypen werden abgelehnt. Frei konfigurierbare Evaluatorkommandos sind
noch nicht implementiert.

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
`author_checked` ist auch für offizielle Fälle zulässig. Menschliche Prüfungen
je Fall sind optional und keine Voraussetzung für Vollständigkeit.
`independently_checked` verlangt weiterhin zwei verschiedene zustimmende
Prüferkennungen und private Belegdateien; dieser Status wird nicht automatisch
vergeben. Das Pilotmanifest meldet `reference_admission=independently_checked`
nur, wenn alle ausgewählten Referenzen diesen Status tragen, sonst
`author_checked`. Die Einzelstatus bleiben im eingefrorenen Paket erhalten.

Review-Referenzen besitzen `findings` für die als fehlerhaft bewerteten
Kriterien. Ein Finding benennt `criterion_id`, sichtbaren `path`, `symbol`,
`mechanism`, `impact`, optionale `allowed_alternatives` und gegebenenfalls ein
`counterexample` mit unterschiedlichen Werten für `expected` und `actual`.
Projekt-Referenzen deklarieren eine `solution`, benannte `mutants` und deren
Zuordnung `mutant_criteria`. Der Loader prüft diese Verweise und Kriterien,
führt aber keine Lösung oder Gegenprobe aus. Die EBT-Referenzprüfungen führen
die mitgelieferten vertrauenswürdigen Beispiele gesondert aus.

### Agenten- und Evaluatornachrichten

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
`project_v1`. Für Reparaturen gelten `repair` und `patch_v1`. Phasenreihenfolge und
tatsächliche Rot-/Grün-Belege prüft erst der ausführende Runner.

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

### Paketstruktur

Die experimentelle API liegt unter `qb_cubie.benchmarks`. `cli.py` und
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

---

## Experimentdaten und Reproduzierbarkeit

Die vollständigen Rohdaten der empirischen Vergleichsstudie (`experiments/testguided-study/runs/`, ca. 1,1 GB entpackt) werden separat über die GitHub Releases bereitgestellt.

### Download- und Verifikationsskript

Mit [scripts/download_study_runs.py](../scripts/download_study_runs.py) können die Daten mit Fortschrittsanzeige heruntergeladen, per SHA-256 verifiziert und entpackt werden:

```bash
# Automatischer Download vom GitHub-Release v0.0.3 und Entpacken nach experiments/testguided-study/runs:
python scripts/download_study_runs.py

# Optional: Lokale Archivdatei manuell prüfen und entpacken:
python scripts/download_study_runs.py --from-file dist/testguided-study-runs.tar.gz

# Benutzerdefiniertes Zielverzeichnis:
python scripts/download_study_runs.py --target-dir /pfad/zu/runs
```

Erwarteter SHA-256-Hash des Archivs `testguided-study-runs.tar.gz`:
`3234d440dd3d2df85299ccc98bfe42a2c34b9fa266b7be9d7918f51217277278`
