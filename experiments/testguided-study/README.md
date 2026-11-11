# Testguided-Vergleichsstudie

## Direkt starten und live verfolgen

Aus dem Repository genügt jetzt ein Befehl:

```bash
./study --mode pilot
```

Der Starter findet die vorhandene lokale swegemma-Python-Umgebung, bereinigt die
vorab gewählten Snapshots, baut fehlende bzw. geänderte Studienimages, ermittelt
die privaten Reparatur-/Regressionstest-IDs durch echte Referenzläufe, friert die
Studie ein und führt beide Agenten aus. Ein neuer Archivpfad und die lokale
Monitor-URL werden ausgegeben. Der erste Imagebau kann Paketdownloads benötigen;
es gibt keine Cloud-Inferenz und keinen automatischen Modell-Download.

| Modus | Zweck | Standardumfang |
| --- | --- | --- |
| `smoke` | synthetischer Techniklauf, kein Nutzenbeleg | 1 Aufgabe, 2 Agentenläufe, je höchstens 180 Sekunden |
| `pilot` | fachlicher Pilot mit getrennten Pilotaufgaben | 3 Aufgaben, 6 Agentenläufe |
| `short` | Hauptstudie für ungefähr drei Stunden | 5 Aufgaben, 10 Agentenläufe |
| `long` | Hauptstudie für ungefähr sechs Stunden | 10 Aufgaben, 20 Agentenläufe |

```bash
./study --mode smoke
./study --mode short --tasks 5 --agent-seconds 600 --seeds 42 --keep-monitor
./study --mode long --tasks 3 --task-type parsing_encoding --monitor terminal
./study --mode pilot --prepare-only
./study start --help
```

Zu große Anzahlen innerhalb eines Typfilters werden abgewiesen. `--prepare-only`
führt alle Vorbereitungs- und Zulassungsprüfungen ohne Modellinferenz durch.
Für vorbereitete eigene Aufgaben: `--tasks-manifest /pfad/tasks.json`; für eine
andere TOML: `--config /pfad/study.toml`. `--source`, `--snapshots`, `--catalog`
und `STUDY_PYTHON=/pfad/python` erlauben andere lokale Ablagen. Flags überschreiben
die TOML **vor** dem Freeze. Alle Startoptionen stehen anschließend in `launch.json`.
Eigene Imagekonfigurationen verwenden `--no-build-images` und werden vorab geprüft.

`--monitor web` ist der Standard. Der Monitor bindet nur an `127.0.0.1`, lädt keine
externen Ressourcen und bietet keine Eingriffsmöglichkeit in den Agentenlauf.
Eine feste lokale Portnummer lässt sich mit `--port 8765` wählen. Er zeigt:

- Gesamtphase, geplante und abgeschlossene Läufe, Erfolge, Fehler und Ausfälle;
- aktuellen Agenten, Aufgabe, Typ, Seed, Aufrufe und Agentenzeit;
- den tatsächlich gesendeten Kontext samt aktuellem Guide, validierte Aktionen,
  Werkzeug-/Testbeobachtungen und die erhaltene Modellantwort;
- frühere Läufe und Schritte zur getrennten Betrachtung sowie eine Pausenfunktion.

Während Ollama rechnet, ist ausdrücklich der Wartezustand sichtbar. Die verwendete
API liefert abgeschlossene Antworten; der Monitor behauptet keine Ausgabe einzelner
Tokens und zeigt keine erfundenen Zwischenschritte. Seine Pausenfunktion pausiert
nur die Ansicht. Private Referenzpatches und private Evaluatorverzeichnisse werden
nicht über die Monitor-API bereitgestellt. Der Monitor liest keine beliebigen Dateien.

Zusätzlich oder nachträglich in einem zweiten Terminal, mit dem ausgegebenen Archivpfad:

```bash
./study status /pfad/zum/studienarchiv
./study status /pfad/zum/studienarchiv --watch
./study status /pfad/zum/studienarchiv --watch --view context
./study status /pfad/zum/studienarchiv --json
./study monitor /pfad/zum/studienarchiv --port 8765
```

`--monitor terminal` protokolliert die Phasen ohne Browserserver; `--monitor none`
verzichtet auf die Live-Anzeige. Zustandsdatei und Ereignisjournal bleiben in
beiden Fällen erhalten. Am Studienende schließt der automatisch gestartete Server;
`--keep-monitor` hält ihn bis Strg+C offen. `monitor ARCHIV` öffnet abgeschlossene
oder fehlgeschlagene Archive erneut. Beim automatischen Schließen erhält eine
verbundene Ansicht bis zu zwei Sekunden Gelegenheit, den letzten Stand zu laden;
danach beendet sie ihre Abfragen und zeigt „Monitor beendet“. Verpasst eine
Ansicht diese Meldung, bleibt ein bereits empfangener Abschluss-, Fehler-,
Unterbrechungs- oder Vorbereitungsstatus auch nach dem Verbindungsende erhalten.
Bei unerwartetem Verbindungsverlust bleiben
der letzte Stand und dessen Laufzeit sichtbar. Nach zehn erfolglosen Abfragen
endet die automatische Wiederverbindung; erneutes Laden der Seite startet sie neu.
Strg+C während einer Studie beendet den Lauf
und erhält seine Belege; ein vorhandenes Archiv wird nicht überschrieben.

Bei fehlgeschlagener Zulassung stoppt der Starter **vor** Modellinferenz und nennt
das Fehlerarchiv. Aufgaben werden nicht unbemerkt ersetzt. Die sichtbaren Issues
stehen zusätzlich unter `prepared/inputs/*/issue.md`, sodass sie sich vor einem
fachlichen Lauf mit `--prepare-only` auch in Ruhe prüfen lassen.

## Studienaufbau und weiterführende Vorbereitung

Startpunkt ist das [Studienprotokoll](PROTOKOLL.md): Fragestellung, Agentendesign,
Aufgabenauswahl, Messgrößen und Aussagegrenzen. Dieser separate Versuchsaufbau
verwendet swegemma 0.2.11 und lokale Ollama-Inferenz. Er benötigt weder
`cubie-bench` noch dessen Szenariopakete oder bisherigen Developer-Agenten.

Der [Datenplan](DATEN.md) enthält bereits reproduzierbar ausgewählte Kandidaten
aus dem vorhandenen lokalen Pool und die noch nötigen Zulassungsschritte.
Die [Einzelprüfung und Aufgabentypen](KANDIDATEN.md) dokumentieren 39 fachlich
geprüfte Aufgaben sowie Ausschlüsse, verwandte Fixes und Belegarten.
Der [Techniknachweis](VALIDIERUNG.md) trennt bestandene Implementierungsprüfungen
von der noch ausstehenden fachlichen Studie.

Beide Agenten laufen mit demselben [Basisprompt und Aktionsschema](testguided_study/design.py).
Sichtbare Tests sind in jeder Arbeitsphase bearbeitbar. Nur die Bibliothek und
die eingefrorene [pytest-](guides/pytest.md) bzw. [Cubie-Anleitung](guides/cubie.md)
unterscheiden sich. Der Pytest-Container enthält kein Cubie und erhält keinen
Checkout-/Host-Mount. Die Modellverbindung läuft ausschließlich vom Host zu Ollama;
Aufgaben- und Evaluatorcontainer haben kein Netzwerk. Generierte Python-Tests
laufen im jeweiligen Container; die Dateitools allein sind keine Sicherheitsgrenze.

## Umgebung und Images

Host: Python ab 3.11 mit einer funktionsfähigen swegemma-0.2.11-Installation samt
deren Abhängigkeiten, Docker-Zugriff und Ollama. Cubie selbst muss auf dem Host
nicht installiert sein. Die Container benötigen Python ab 3.13. Keine Cloud-API
und kein API-Key sind nötig. Die vorhandene lokale Umgebung kann beispielsweise
so gewählt werden, ohne sie zu verändern:

```bash
# Alle Befehle aus dem cubie-Repository:
STUDY_PYTHON=/home/symphonie/PycharmProjects/start-local-devagent/.venv/bin/python
STUDY=experiments/testguided-study/study.py
"$STUDY_PYTHON" "$STUDY" --help
```

Alternativ in einer eigenen Host-Umgebung die verfügbaren swegemma-,
adk-submission- und adk-eval-core-Wheels installieren. Die Bridge prüft Version
und Python-Dateihashes der tatsächlich importierten swegemma-Installation.
Der benachbarte Quellordner ist nicht automatisch die installierte Version.

```bash
uv build --wheel
docker build -f experiments/testguided-study/Dockerfile.pytest -t cubie-study-pytest:local .
docker build -f experiments/testguided-study/Dockerfile.cubie -t cubie-study-cubie:local .
```

Die Cubie-Variante baut auf **demselben** Pytest-Image auf. Historische
Benchmarkdaten werden aus dem Cubie-Image entfernt. Für reale Aufgaben vorher
die benötigten Projektabhängigkeiten in das gemeinsame Basisimage aufnehmen;
dessen Aufgaben-Setup `/sandbox/setup.py` muss auf beiden Seiten gleich sein.
Das enthaltene No-op-Setup genügt nur für den synthetischen Smoke und bereits
vollständig vorbereitete Images. Während der Läufe keine Pakete nachinstallieren.
Die Vorprüfung vergleicht gemeinsame Paketversionen, Python und pytest sowie
Cubie-Verfügbarkeit; anschließend werden konkrete lokale Image-IDs verwendet.

Builds können Downloads benötigen. Alle Messungen laufen danach lokal.
Ollama muss `gemma4:12b` bereits enthalten. Es gibt keinen automatischen Pull,
Ersatz durch ein anderes Modell oder implizite Wiederholung.

## Zuerst die Technik prüfen

```bash
"$STUDY_PYTHON" "$STUDY" make-smoke /tmp/cubie-study-smoke-input
"$STUDY_PYTHON" "$STUDY" freeze /tmp/cubie-study-smoke-input/study.toml /tmp/cubie-study-smoke
"$STUDY_PYTHON" "$STUDY" preflight /tmp/cubie-study-smoke
# Erst dieser Befehl führt echte Modellinferenz aus:
"$STUDY_PYTHON" "$STUDY" run /tmp/cubie-study-smoke
"$STUDY_PYTHON" "$STUDY" report /tmp/cubie-study-smoke
```

Ziele müssen neu sein. Der Smoke erzeugt eine einfache Begrenzungsfunktion mit
sichtbarem Bestandstest und getrennten privaten Randfalltests. Er ist **kein
Nutzenbeleg**. `freeze` arbeitet offline. `preflight` prüft Modellmetadaten ohne
Inferenz sowie echte Container und Ausgangs-/Referenzläufe. Ohne erfolgreiche
Vorprüfung startet `run` keine Inferenz. Der Beispielsmoke hat zwei Agentenläufe;
auch hier gelten die Budgets der erzeugten TOML. Vor `freeze` bei Bedarf ändern.

## Echte Aufgaben einrichten

### Anzahl, Aufgabentypen und Stundenplanung

Die Profile [Pilot](profiles/pilot.toml), [drei Stunden](profiles/three-hours.toml)
und [sechs Stunden](profiles/six-hours.toml) sind anpassbare TOML-Konfigurationen.
Kandidatenplanung benötigt weder Docker noch Modellinferenz:

```bash
"$STUDY_PYTHON" "$STUDY" plan experiments/testguided-study/profiles/three-hours.toml \
  --catalog experiments/testguided-study/candidate-catalog.json
"$STUDY_PYTHON" "$STUDY" plan experiments/testguided-study/profiles/six-hours.toml \
  --catalog experiments/testguided-study/candidate-catalog.json \
  --output /tmp/cubie-study-six-hours-plan.json
```

| Profil | Aufgaben | Seeds je Aufgabe | Agentenläufe | Budget je Agent | Planung einschließlich Referenzprüfung und Rüstzeit |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pilot | 3 | 1 | 6 | 10 Minuten | 1:36 Stunden |
| Drei Stunden | 5 | 1 | 10 | 10 Minuten | 2:40 Stunden |
| Sechs Stunden | 10 | 1 | 20 | 10 Minuten | 5:20 Stunden |

Die beiden Hauptprofile verwenden dieselben Modell- und Agentenbudgets. Ein
einzelner API-Smoke kalibriert keine typische Aufgabenlaufzeit. Die Zahlen sind
Planungswerte mit 120 Sekunden pro privater Prüfung und angenommenen 60 Sekunden
Rüstzeit pro Container. Builds, Image-Probes, manuelle Datenzulassung und längere
Setups kommen hinzu; frühe Abgaben verkürzen die Zeit. `planning.hours` ist ein
Planungsziel, kein harter Laufzeitabbruch. `task_capacity_for_target` und
`fits_allowance` zeigen, ob die konfigurierte Zahl in diesen Ansatz passt.

Für andere Umfänge vor dem Freeze ändern:

```toml
[selection]
task_count = 5
seed = 20261111
task_types = [] # leer: alle zulässigen Typen; z.B. ["parsing_encoding", "api_schema"]

[planning]
hours = 3
setup_seconds_per_run = 60
```

Die Auswahl mischt reproduzierbar innerhalb von Typ und Repository und zieht
rundenweise Aufgaben aus den Typen, mit wechselnden Repositories innerhalb eines
Typs. Pro Verwandtschaftsgruppe wird höchstens eine Aufgabe gewählt. Zu große
Anzahlen oder Typfilter ohne passende Aufgaben erzeugen einen Fehler. Bei gleichem Pool und Seed
bleiben kürzere Umfänge Präfixe der längeren. Ohne `[selection]` werden wie bisher
alle explizit eingetragenen Aufgaben verwendet; dann ist der Manifestautor für
Unabhängigkeit und Zusammensetzung verantwortlich.

Ein Katalogplan hat den Status `candidates_not_admitted`: Er ist eine Auswahl
für die Aufbereitung und lässt sich noch nicht ausführen. Danach auf dem fertig
vorbereiteten Aufgabenmanifest noch einmal **ohne** `--catalog` planen:

```bash
"$STUDY_PYTHON" "$STUDY" plan experiments/testguided-study/profiles/three-hours.toml
"$STUDY_PYTHON" "$STUDY" freeze experiments/testguided-study/profiles/three-hours.toml /tmp/cubie-study-three-hours
"$STUDY_PYTHON" "$STUDY" preflight /tmp/cubie-study-three-hours
"$STUDY_PYTHON" "$STUDY" run /tmp/cubie-study-three-hours
"$STUDY_PYTHON" "$STUDY" report /tmp/cubie-study-three-hours
```

Die Profile verweisen für den manuellen Ablauf auf `tasks-pilot.json` bzw.
`tasks-measurement.json` im Studienverzeichnis. Der Starter erzeugt sein eigenes
Manifest im neuen Studienarchiv und benötigt diese Dateien nicht.
Ein geänderter Pool, etwa nach einem technischen Ausschluss, erfordert erneute
Planprüfung; die Planung speichert seinen Hash. Nicht während der Messung nach
Erfolgen weitere Aufgaben ergänzen oder einen Agenten vor seinem gepaarten
Gegenlauf stoppen. Einen bereits gestarteten kurzen Lauf nicht nachträglich als
unabhängigen Teil einer größeren Studie doppelt zählen.

### Aufgabenmanifest und private Records

`study.toml` ist eine bewusst noch nicht mit Messaufgaben befüllte Vorlage.
Für reale Aufgaben eine private Arbeitsablage außerhalb des Agenten-Workspaces
anlegen und die Auswahl nach dem Protokoll festlegen. Sie enthält:

```json
[
  {
    "id": "repository__issue-123",
    "split": "pilot",
    "repo": "organization/repository",
    "task_type": "parsing_encoding",
    "change_kind": "bugfix",
    "test_scope": "unit",
    "related_group": "unique-issue-group",
    "record": "records/issue-123.json",
    "snapshot": "snapshots/issue-123.tar.gz"
  }
]
```

Dieses `tasks.json` wird in der TOML relativ zu deren Verzeichnis eingetragen.
Die Typangaben werden aus der fachlichen Prüfung übernommen und für Messaufgaben
verlangt. `repo` muss zum privaten Record passen. Die Metadaten bleiben im
Laufplan, Ergebnis und Bericht erhalten; der Agent erhält sie nicht als zusätzliche
Anleitung. `task-distribution.json` hält die eingefrorene Zusammensetzung fest.
`record` und `snapshot` sind relativ zur `tasks.json`. Der private Record hat
die Felder von `swegemma.models.Task`:

```json
{
  "instance_id": "repository__issue-123",
  "repo": "organization/repository",
  "base_commit": "EXAKTER_AUSGANGSCOMMIT",
  "problem_statement": "Vollständige fachliche Aufgabe",
  "patch": "privater Git-Diff der Referenzlösung",
  "test_patch": "privater Git-Diff der unabhängigen Prüftests",
  "FAIL_TO_PASS": ["tests/test_issue.py::test_regression"],
  "PASS_TO_PASS": ["tests/test_issue.py::test_existing_behavior"]
}
```

Die Patches müssen echte anwendbare Git-Diffs sein. Der Snapshot enthält den
sichtbaren Ausgangsbaum auf Archivebene, ohne `.git`, private Lösung/Prüftests,
Belegarchive, Cubie-Anleitungen oder Symlinks. Vorhandene Symlinks bei der
Vorbereitung prüfen und materialisieren. Deduplizierte swegemma-Snapshots vorher
zum aufgabenspezifischen Ausgangsbaum rekonstruieren. Die Bridge lädt keine
Datensätze und trifft keine fachliche Aufgabenauswahl anhand von Modellresultaten.

Für Messungen `phase = "measurement"` setzen und ausschließlich vorher ungenutzte
Aufgaben mit `split = "measurement"` auswählen. Studien-ID, Seeds, Budgets, Images,
Modelloptionen und Guides vorab festlegen. Dann dieselben fünf Schritte wie oben
mit der eigenen Konfiguration ausführen. Vorprüfungsfehler zuerst beheben und
einen neuen Freeze anlegen; historische Fehlbelege behalten.

## Belege und Auswertung

Der Freeze kopiert private Eingaben und Guides, erzeugt den gepaarten Laufplan
und bindet ihn an Codehashes. `ready.json` bindet Modell-, Image- und
Referenzprüfungen daran. Jeder Lauf erhält ein eigenes Verzeichnis mit:

- Anfragen, Rohantworten, gemessenen Tokens, Aktionen und Werkzeugbeobachtungen;
- JUnit-Belegen und Zwischenpatches nach Testläufen und Änderungen;
- `full.patch` mit allen Teständerungen sowie separat `evaluation/evaluated.patch`;
- unabhängiger Evaluation, Ergebnis und Hashmanifest.

Das private Recordobjekt wird nicht in den Modellkontext übernommen; nur
`problem_statement` gelangt dorthin. Das Modell kann ausschließlich den
sichtbaren Containerbaum über die angebotenen Werkzeuge untersuchen.
Vor jedem Lauf wird die Modell-/Runneridentität erneut geprüft. Abgebrochene
Versuche werden nicht automatisch fortgesetzt oder überschrieben. Für eine
Wiederholung einen neuen, als solchen dokumentierten Freeze verwenden.

`report` liefert JSON mit Erfolgsquoten, Ausfallzahlen, gepaarten Differenzen,
Aufgaben-Bootstrapintervall und Ressourcen. Unbekannte Tokenwerte bleiben `null`.
Es gibt keinen automatischen Gewinnerentscheid. Prozessqualität und tatsächliche
Cubie-Nutzung anhand der Belege nach dem Protokoll prüfen. Der Bericht ist ein
explorativer Bericht der angepassten swegemma-Prüfung, kein offizielles
SWE-bench-Leaderboard-Ergebnis.

Ollamas [Chat-API](https://docs.ollama.com/api/chat) liefert JSON-Ausgaben und
die Zähler `prompt_eval_count`/`eval_count`; die
[Parameterreferenz](https://docs.ollama.com/modelfile) beschreibt unter anderem
`seed`, `temperature` und `num_ctx`. Der vorhandene HTTP-Client archiviert diese
Antworten und validiert jede Aktion lokal.

## Verifikation der Implementierung

```bash
.venv/bin/python -m pytest experiments/testguided-study/tests -q
.venv/bin/python -m ruff check experiments/testguided-study
# Echte swegemma-/Docker-Integration, nur Modellantworten werden wiedergegeben:
CUBIE_STUDY_DOCKER=1 "$STUDY_PYTHON" -m pytest experiments/testguided-study/tests -q
```

Die zusätzlichen EBT-Verträge in `tests/test_lifecycle_ebt.py` prüfen sechs
gepaarte Agentenläufe bis zum Bericht einschließlich einzelner Container-,
Modellverbindungs- und Evaluationsausfälle, Aufräumen und Überschreibschutz.
Sie verwenden echte Freeze-, Agenten-, Beleg-, Monitor- und Berichtsfunktionen;
Docker und Modellantworten sind ersetzt. Die HTTP-Abschlussprüfung deckt
Abschluss, Fehler, Unterbrechung und `--prepare-only` ab.
`tests/test_monitor_poll_ebt.py` führt das ausgelieferte JavaScript mit Node.js
gegen ein minimales DOM und deterministische Verbindungsfolgen aus: Serverende, verpasste Schließmeldung nach Abschluss/Fehler/Unterbrechung/Vorbereitung,
fehlender Server, Abbruch nach erfolgreicher Verbindung, Wiederverbindung und
ungültige Daten. Ohne Node.js werden diese Fälle übersprungen. Diese Prüfungen
ersetzen keinen echten Browser- oder Docker-/Ollama-Dauerlauf.

Die Docker-Gegenprobe überschreibt vorhandene Tests, beobachtet Rot/Grün und
überarbeitet sie **nach Grün** erneut, in beiden Varianten. Eine zweite Probe
zeigt, dass eine nur auf `assert True` reduzierte sichtbare Suite die private
Prüfung einer falschen Lösung nicht bestehen lässt. Diese Proben sind
Infrastrukturnachweise; sie messen keine Modellleistung.
