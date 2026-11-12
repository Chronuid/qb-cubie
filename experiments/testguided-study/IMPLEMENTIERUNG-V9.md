# Implementierung der Agentengeneration V9

V9 ist eine separat auswählbare Entwicklungsvariante auf Basis von
[AGENTENDESIGN-V9.md](AGENTENDESIGN-V9.md). Die historische Aussage im Entwurf,
dass noch keine Implementierung vorliegt, beschreibt den Ausgangsstand.
Die technische Abnahme ersetzt keine empirische Qualifikation mit einem Modell.

```bash
./study start --mode pilot --config experiments/testguided-study/v9.toml
```

Das Profil übernimmt Modell, Images, Seeds und Ressourcenparameter von V8:
1800 Sekunden gemeinsame Taskzeit, unbegrenzte Aufrufe innerhalb dieser Zeit,
`think=false` und dieselben Kontext- und Ausgabebudgets. Frühere Profile und
versionierte Rollenverträge bleiben auswählbar.

## Quellcode und Schnittstellen

- `testguided_study/team_v9_design.py`: kurze Rollenprompts, gemeinsame Navigation,
  cursorfreie Schemas und gewöhnliche, zustandsabhängig geprüfte `finish`-Aktionen.
- `testguided_study/team_v9.py`: Controller, lokale und entfernte öffentliche
  Workspaceadapter, Transaktionen, automatischer Evidenztransport und expliziter
  Markdownrenderer. V8 liefert weiterhin sichere Handles, Testausführung,
  Fallinstrumentierung und die Fortsetzung gespeicherter Informationsaufträge.
- `design.py`, `iteration.py`, `artifacts.py`, `team.py`, `agent.py` und
  `team_agent.py`: Versionsauswahl, Freeze und Laufzeit. Der bestehende Monitor
  und Bericht konsumieren dieselben archivierten Prompts und Teamzustände.

`V9TeamController` akzeptiert die vorhandenen Workspace-/Runnerports sowie
optional `persist(transaction)` und eine sichtbare `baseline`. Jede bestätigte
Aktion speichert Ergebnis, neue Originalbelege und den resultierenden Teamzustand
in einer Transaktion. Der Standardport schreibt atomare JSON-Dateien unter
`transactions/`. Bei einem Speicherfehler bestätigt der Controller keine
Übergabe und stellt den vorherigen Auftrag wieder her. Externe Werkzeugwirkungen
wie bereits ausgeführte Tests oder Dateiedits lassen sich durch einen Ausfall des
Speichermediums nicht zurücknehmen; sie werden beim nächsten Versionsabgleich
erkannt und berechtigen ohne passende Belege zu keinem Abschluss.

## Gedächtnis und Kontext

Reads einschließlich Handles, Suchen, Testläufe und Rollenlieferungen werden
automatisch bewahrt. Überlappende aktuelle Ausschnitte erscheinen zusammengeführt;
Originalbelege bleiben separat über `read_evidence` erreichbar. Dateiversionen
trennen historische von aktuellen Quellen. Produktion, Suite und Environment
binden Testbelege und Review an denselben Stand. Nach einer Testrevision führt
der Baselineport die finale Suite in einer getrennten Kopie mit Originalproduktion
aus. Neue unklassifizierte Ausgabedateien des Runners zählen als Laufartefakte;
bereits vorhandene Projektdateien bleiben versionsrelevant.

Der initiale Userkontext besitzt genau vier Hauptabschnitte. Er enthält
Rollenbefunde mit Herkunft, aktuelle Quellen, einen Materialindex, offene Fragen,
aktuelle Fehlerdetails und Referenzen historischer Ausführungen. Der vollständige
Diff ist im Review ausdrücklich über `read_evidence` verfügbar. Höchstens vier
unterschiedliche Werkzeugdialoge ergänzen den Kontext mit benutzbaren Handles und
kompakten Ergebnissen. Frameworkanleitungen erhält ausschließlich QA. Interne
Hashes und Rohzustände werden nicht als Modellkontext serialisiert.

Das Bytebudget umfasst Nachrichten und aktives Schema. Weitere Quellen werden
nur bei ausreichendem Platz zugestellt; sie bleiben im Index auffindbar. Ein
zu großes Pflichtpaket erzeugt vor dem Modellaufruf `context_budget_exceeded`.
Die Laufzeit reserviert wie V8 Ausgabetokens und verwendet für die Vorabgrenze die
bestehende konservative Bytes-pro-Token-Schätzung; das ist keine exakte
modellabhängige Tokenisierung. Tatsächliche Providerverbräuche werden archiviert. Überschreiten gemessene
Eingabetokens plus reservierte Ausgabe das Modellbudget, führt der Lauf keine
Werkzeugaktion dieser Antwort aus und endet mit einem Kontextfehler.

## Navigation, Rechte und Abschluss

Alle Rollen können öffentliche Dateien unabhängig von früheren Zuweisungen
lesen und wörtlich durchsuchen. Private Pfadbestandteile, Traversal und Symlinks
bleiben gesperrt. Unklassifizierte öffentliche Pfade werden durch Lesen nicht
schreibbar. QA schreibt Tests, Fixtures und Testkonfiguration, Dev Produktion;
Analyse hat keine Schreibrechte. Neue zulässige Dateien verwenden leere
Lesehandles. Bestehende Produktion verlangt zunächst einen aktuellen Fokustestlauf.

Suchen liefern höchstens 50 deterministisch sortierte Treffer und kennzeichnen
eine Begrenzung. Nur alte zusätzliche `cursor`-Felder werden verworfen; andere
Schemafehler bleiben Fehler. Diese Normalisierung erfolgt sowohl im Dispatcher
als auch vor der Validierung tatsächlicher Ollamaantworten. Der an Ollama
übermittelte Vertrag enthält kein Cursorfeld; Rohantworten bleiben archiviert.

Collection allein qualifiziert keinen Abschluss. Fachliches Rot verlangt eine
ausgeführte Assertion gegen Originalproduktion und finale Suite; Setupfehler
zählen nicht. Fokusgrün, vereinbarte Regressionen, passende Fehleridentitäten bei
Baselineausfällen, gelesener Diff und Ausführungsdetails sind Abschlussbedingungen.
Im Cubie-Arm wird zusätzlich pro Case die tatsächliche EBT-Ausführung, Evaluation
und explizite Prüfung der Evaluation verlangt. Offene Fachfragen oder spätere
Artefaktänderungen blockieren `verified`. Zeitablauf sichert `incomplete`, Patch,
Fragen und Belege. Private Lösungsevaluation bleibt eine separate Ergebnisachse.

## Reproduzierbare Prüfung

```bash
.venv/bin/python -m pytest tests/testguided_study_design/test_v9_memory_ebt.py \
  tests/testguided_study_design/test_v9_tools_ebt.py \
  tests/testguided_study_design/test_v9_workflow_ebt.py \
  tests/testguided_study_design/test_v9_calibration_ebt.py \
  tests/testguided_study_design/test_v9_runtime.py -q
.venv/bin/python -m pytest tests/testguided_study_design -q
```

Die ursprünglichen 134 Nodes sind in [V9_CASES.md](../../tests/testguided_study_design/V9_CASES.md)
beschrieben; dessen roter Status dokumentiert die Situation vor dieser Umsetzung.
Zusätzliche Laufzeitreplays prüfen Freeze/Load, das V9-Profil, echte öffentliche
Workspaceoperationen und die echte EBT-Instrumentierung in beiden Armen. Ein
negativer Cubie-Replay ohne Evaluationsassertion muss unvollständig bleiben.
Providerfixtures prüfen die Cursornormalisierung, ohne das übermittelte Schema
zu erweitern. Diese Prüfungen verwenden deterministische Modellantworten und
Hostprozesse, keinen echten Docker-/Ollama-Pilot und keine private Lösungswertung.

Validierungsstand dieser Umsetzung: Alle **146 V9-Nodes** bestehen, darunter die
134 ursprünglichen Abnahmen und zwölf zusätzliche Laufzeit-/Providerfälle.
Ruff und `git diff --check` sind sauber. Der während der letzten Bearbeitung
angelaufene Gesamtlauf meldete 698 bestandene Nodes und einen erwartungsgemäßen
Freeze-Schutzabbruch wegen zwischenzeitlich veränderter Agentenquellen. Nach Ende
der Quellenänderungen bestand die gezielte Wiederholung der betroffenen
End-to-End-Replays für V6, V7 und V8 vollständig (drei Nodes). Die zwei zuletzt
ergänzten Pfadfälle sind im vollständigen grünen V9-Lauf enthalten.
