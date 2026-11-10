# Eigene Agenten und Szenarien

Mit `qb-cubie[benchmarks]` können Sie einen eigenen Prozessadapter und eigene
Szenariopakete verwenden. Ein Agent mit einer Wiederholung genügt. Ein zweiter
Agent und der Produktvergleich Cubie/pytest sind optional. Das vollständige
Tutorial ist auch nach einer Wheel-Installation mit `cubie-bench guide` verfügbar.

## Installieren und ein vollständiges Beispiel ausführen

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

## Einen eigenen Agenten anschließen

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

## Nachrichten und Phasen

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

## Ein eigenes Szenario entwickeln und auswählen

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

Typen und Tags sind frei wählbar, optional und ändern den Evaluator nicht.
Beispielauswahl im TOML-Set für das Versandkostenpaket:

```toml
[select]
types_any = ["shop/shipping", "correctness"]
tags_all = ["shipping", "boundary"]
benchmarks = ["review_agent"]
```

Innerhalb von `*_any` gilt ODER, zwischen Filtern UND. `*_all` verlangt alle
Werte, `*_none` und `exclude_ids` schließen aus. Mehrere Typen vervielfachen
keine Versuche. Ein Fall ohne Typ bleibt ohne positiven Typfilter auswählbar.
Unbekannte IDs, leere Auswahl und fehlende explizite Vorgänger scheitern vor
Agentenstart. Weitere lokale Pakete können als zusätzliche `[[sources]]`
eingetragen werden; eine Core-Änderung oder Registrierung ist unnötig.

## Bericht und Laufvergleich lesen

Jeder Lauf schreibt einen eigenen Ergebnisordner. `report.md` nennt pro
Szenario Kriterien, Prozessurteil und Beleglinks. `results.json` enthält
dieselben Beobachtungen maschinenlesbar. `manifest.json` bindet den
aufgelösten Plan an Konfiguration und archivierte Bytes. Rohes JSONL,
stderr, Phasensnapshots und tatsächliche Testergebnisse bleiben erhalten.

`completed` bedeutet eine ausgeführte Bewertung, keine Qualitätsfreigabe.
`quality_passed` beschreibt die fachliche Aufgabe, `process_passed` den
Entwicklungsprozess. Ohne Qualitätsgate bedeutet Exitcode 0 einen vollständig
ausgeführten Lauf. Konfigurationsfehler liefern 2, unterbrochene oder ungültige
Versuche 3. Fehlgeschlagene Qualitätskriterien allein ändern den Exitcode nicht.

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
die Aufnahme durch zwei Menschen und reale Pilotmessergebnisse stehen aus.

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
menschliche Aufnahme. `dataset.json` dokumentiert Herkunft, Lizenz, Domäne und
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

## Messbetrieb: Gates, eingefrorene Konfiguration und CI

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

Der CLI-Exitcode ist **0** bei vollständiger Ausführung mit bestandenen oder
nicht konfigurierten Gates, **2** bei Konfigurationsfehlern, **3** bei
unvollständiger/fehlerhafter Ausführung und **4** bei vollständiger Ausführung
mit verfehlten Gates. Code 3 hat Vorrang vor Code 4. Daher kann die CI Qualität
und Laufprobleme getrennt behandeln und trotzdem in beiden Fällen Belege sichern.

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
`dependency_lock_sha256` bleibt derzeit ausdrücklich unbekannt; das Bundle
provisioniert keine Abhängigkeiten. Installieren Sie diese in Ihrer CI mit
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
und Evaluatoren voraus; Containerisolation gemäß Konzeptabschnitt 7.3 bleibt
gesonderte Infrastruktur.

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

Für eine bestätigende Produktmessung folgen auf unabhängige menschliche
Referenzaufnahme und einen realen Pilot vorab festgelegte primäre Kennzahlen,
ein praktisch relevanter Mindestvorteil beim Aufwand und eine tolerierte
Qualitätsabweichung. Diese Festlegungen werden vor Sichtung neuer
zurückgehaltener Ergebnisse eingefroren. Qualität, Prozess und Aufwand bleiben
getrennt; Wiederholungen erhöhen nicht die Zahl unabhängiger Projekte.
Ein grünes Team-Gate oder ein deterministischer Fake-Lauf ersetzt diesen
Produktnachweis nicht. Die Grenzen und offenen methodischen Abnahmen aus dem
Benchmark-Konzept gelten weiter.
