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
