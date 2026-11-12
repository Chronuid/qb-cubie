# Testguided-Vergleichsstudie

V7 ist als explizite Entwicklungsvariante verfügbar. Konzept und Hypothesen
stehen in [AGENTENDESIGN-V7.md](AGENTENDESIGN-V7.md), Implementierung und
technische Abnahmen in [IMPLEMENTIERUNG-V7.md](IMPLEMENTIERUNG-V7.md),
die Konfiguration in [v7.toml](v7.toml).
Die Ursachenanalyse zum v7-Pilotabbruch `20261112-015457` dokumentiert
[HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md](HYPOTHESIS-V7-GEMINI-ARGON-HIGH.md) (Gemini-4-Argon).
Pro Task und Behandlung gelten 30 Minuten Gesamtzeit und unbegrenzte
Modell- und Werkzeugaufrufe. Nur erfolgreich geprüfte Lösungen enden vorzeitig;
Stagnation und ungültige Antworten verbrauchen die verbleibende Taskzeit weiter.

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

Der Freeze ist dabei ein automatischer interner Schritt. Auch nach Änderungen
an Agentenquellen oder Guides genügt wieder `./study --mode pilot`; separate
`freeze`-/`preflight`-Befehle sind für diesen Einstieg nicht erforderlich.
Die [EBT-Verträge zur automatischen Laufverwaltung](../../tests/testguided_study_design/RUN_MANAGEMENT_CASES.md)
sichern diesen Ablauf auch bei Starts in derselben Sekunde, beim Archivschutz
abgewiesener Low-Level-Neustarts und beim Wheel-Cache nach einem Versionswechsel
ab. Automatische Archivnamen erhalten bei Kollisionen selbstständig einen freien
Suffix; ausdrücklich angegebene bestehende Ausgabeziele bleiben geschützt.

| Modus | Zweck | Standardumfang |
| --- | --- | --- |
| `smoke` | synthetischer Techniklauf, kein Nutzenbeleg | 1 Aufgabe, 2 Agentenläufe, je höchstens 1800 Sekunden |
| `pilot` | fachlicher Pilot mit getrennten Pilotaufgaben | 3 Aufgaben, 6 Agentenläufe |
| `short` | Hauptstudie, Profilname `short` | 5 Aufgaben, 10 Agentenläufe |
| `long` | Hauptstudie, Profilname `long` | 10 Aufgaben, 20 Agentenläufe |

```bash
./study --mode smoke
./study --mode short --tasks 5 --agent-seconds 1800 --seeds 42 --keep-monitor
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
- den tatsächlich gesendeten Kontext samt aktuellem Guide im einzigen Tab
  „Kontext“, mit Kopierfunktion und umschaltbarem Zeilenumbruch;
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

## Weiterentwicklung der Agenten

Das [Konzept für Generation v6](AGENTENDESIGN-V6.md) aggregiert die bisherigen
Ursachenhypothesen und entwirft ein Multi-Agenten-System aus Analyse-, QA- und
Dev-Agent. Es beschreibt Rollenwerkzeuge und Schreibrechte, Kontextübergaben,
EBT-Cases, Teständerungsschleifen, gemeinsame Budgets und einen beleggebundenen
Abschluss durch den Analyse-Agenten. v6 ist als ausdrückliche Designversion
implementiert; der Standard bleibt v5. Ein neuer Entwicklungslauf startet mit:

```bash
./study --mode pilot --config experiments/testguided-study/v6.toml
```

Die Konfiguration setzt `agent_version = 6`, `think = false` und 1800 Sekunden
Gesamtzeit pro Task und Behandlung. Alle Rollen teilen diese Deadline. Modell-
und Werkzeugaufrufe, Rückfragen, Revisionen und Ausgabereparaturen sind unbegrenzt.
Es gibt keine vorgezogene Verifikationsreserve und keine lokalen Rollen- oder
Antwortdeadlines. Wiederholungen erzeugen Diagnosehinweise, aber keinen Abbruch.
Ein unvollständiger Task läuft bis zur Deadline weiter; eine erfolgreich geprüfte
Lösung kann vorher eingereicht werden. Quellen, Rollenprompts, Schemas und
Vorlagenrevision gehen weiterhin in den Freeze ein. Das konfigurierte Zeitbudget
gilt auch bei älteren Designs mit kürzeren oder numerischen Limits.

`team.json`, `messages.json`, `contexts/`, `evidence/`, `actions/` und `steps/`
enthalten Teamstand, öffentliche Übergaben, Kontextrevisionen, Testbelege sowie
unveränderte Modellantworten einschließlich ungültiger Ausgaben. `full.patch`
erhält den Workspacepatch; `production.patch` enthält die an den unabhängigen
Evaluator übergebene Produktionsänderung. Interner Abschluss und private Lösung
bleiben getrennt, auch bei einem unvollständigen Teamende. Der Monitor zeigt
aktive Rolle, Auftrag, Kontext-/Suiteversion, Rückfragen, Reserve und Abschlussstatus.

QA kann vorhandene Nodes registrieren oder mit `create_case` fehlende Testdateien
aus strukturierten Cases erzeugen. `setup.code` enthält Imports, Hilfsfunktionen
und Fixtures; `setup.fixtures` benennt Testargumente und `setup.body` lokale
Beobachtungsadapter, die auf diese Fixtures zugreifen. `expected` enthält genau
`returns` oder `raises` mit `type` und optionalem `match`. Korrelierte Wertepaare
bleiben separate Cases. Fachliche Orakel und Adapter werden weiterhin inhaltlich
von QA und Analyse beurteilt; die Strukturprüfung beweist ihre Richtigkeit nicht.

Die [v6-EBT-Abnahmereihe](../../tests/testguided_study_design/V6_CASES.md)
konkretisiert V6-A01 bis V6-A18 mit 98 ausführbaren Cases, darunter geprüfte
Referenzvorlagen und Controllerverträge. Ergänzende [Laufzeittests](../../tests/testguided_study_design/test_v6_runtime.py)
prüfen komplette serialisierte Teamläufe mit deterministischen Modellclients,
echten Dateiwerkzeugen und pytest-Unterprozessen, Freeze, Monitor und EBT-Probe.
Das qualifiziert die Mechanik, keine höhere Lösungsquote. Modellpiloten und die
kontrollierte Studie stehen weiterhin aus.

Die [Analyse des letzten Piloten vom 11. November 2026](PILOTANALYSE-20261111.md)
wertet den abgeschlossenen v2-Lauf `20261111-163110` aus: ein gelöster
pytest-Lauf, kein gelöster Cubie-Lauf und keine ausgeführte EBT-Prüfung.
Sie entwickelt daraus ein Konzept für einen gemeinsamen Kern v3 und verbesserte
Frameworkspezialisierungen mit priorisierten Abnahmen. Der Kern v3 und die neuen Guides sind implementiert; eine höhere
Lösungsquote muss in neuer Modellinferenz geprüft werden.

Der [Designvorschlag zur iterativen Agentenentwicklung](AGENTENDESIGN.md) erläutert
Pilotbefunde, Architektur und Abnahmeverträge. Neue Freezes verwenden den
Agentenkern v3 mit Aktionsnotizen, beobachteter Ablaufsteuerung,
Aktionsreparatur bis zur Taskdeadline, getrennter Pfad-/Inhaltssuche und verankerten Änderungen mit
Ausgangshash. Wiederholte erfolglose Aktionen werden auch bei wechselnden
Notizen erkannt; nach einem Änderungskonflikt ist erneutes Lesen erforderlich. Die historischen Archive
werden nicht migriert. Geänderte Laufzeitquellen erfordern weiterhin einen neuen
Freeze; Testdateien gehören nicht mehr zum Laufzeitmanifest.

`collect_tests` bestätigt Testziele, `check_baseline` führt die aktuellen
sichtbaren Tests mit ursprünglichem Produktionscode in einer separaten Kopie aus.
Beide Aktionen nutzen die gemeinsame Taskzeit. V3-Qualifikation verlangt
zusätzlich identische Testversionen zwischen Rot und Grün; nach späteren
Teständerungen ist eine erneute Reproduktion erforderlich. Fehlerdiagnosen und
Framework-Laufzeitbelege bleiben archiviert. `ebt_executed`, `ebt_evaluated` und
`ebt_passed` im Bericht unterscheiden Ausführung und Vertragsresultat; sie beweisen
nicht, dass der Test das Issue vollständig abdeckt oder jedes Ergebnis assertiert.
Das Kontextbudget reserviert Schema und Ausgabe anhand einer konservativen
Byteschätzung, die im Ergebnis ausdrücklich als Schätzung ausgewiesen wird.

Die technischen Befunde des Piloten `20261111-171515` sind inzwischen durch
[32 EBT-Verträge](../../tests/testguided_study_design/PILOT_TECHNICAL_CASES.md)
und zusätzliche Integrationsfälle abgesichert. Große Testergebnisse liefern
verdichtete Counts und Fehlerursachen; `read_test_details(step, start)` liest
vollständige Diagnosen aus früheren sichtbaren Testschritten seitenweise nach.
`step` ist dabei die angezeigte Schrittnummer ab 1, `start` ein Fehleroffset ab 0.
Die vollständigen JUnit-Belege bleiben im Archiv. Bei knappem Kontext wird
optionale Historie bzw. Dateiausgabe gekürzt und als gekürzt gekennzeichnet;
Aufgabe und Frameworkanleitung bleiben obligatorisch. Erfolgreiche Leseaktionen
dürfen wiederholt werden, während identische erfolglose Aktionen weiter begrenzt
werden. Testziele beeinflussen die Produktionsversionsmetrik nicht mehr.

Die [48 Abnahmefälle zum Piloten `20261111-180702`](../../tests/testguided_study_design/PILOT_180702_CASES.md)
sind ebenfalls umgesetzt. Python-Änderungen werden vor dem Schreiben kompiliert;
Änderungskonflikte unterscheiden falschen Hash, fehlenden und mehrdeutigen Anker.
Collectiondiagnosen verwenden tatsächlich aufgezeichnete Collector-IDs. Bei
Kontextkürzung bleiben repräsentative Ursachen bekannter Ausgangsfehler erhalten.
Ein agentenverursachter conftest-Importabbruch mit pytest-Exitcode 4 zählt als
„Nicht gelöst“, wenn der erfasste Traceback eine Datei des effektiven
Produktionspatches nennt. CLI-, Timeout- und Verbindungsfehler bleiben nicht
verfügbar. Beendete Monitorzeilen zeigen bei unbekanntem Ergebnis „Nicht verfügbar“.
Für neue Studien ist ein neuer Freeze erforderlich; alte Archive bleiben unverändert.

Zulassung und Vorprüfung erfassen zusätzlich die ursprüngliche sichtbare Suite
in einem eigenen Container **vor** privaten Testpatches. `visible-baseline.json`
und `visible-baseline.xml` dokumentieren vorhandene Snapshot- und Umgebungsfehler.
Die Vorprüfungsbelege sind an `ready.json` gebunden; beide Agenten erhalten eine
verdichtete Zusammenfassung derselben Ausgangsbasis. Vorhandene Suitefehler
werden dokumentiert, nicht automatisch repariert oder als neue Agentenregression
ausgegeben. Die private Rot-/Grün-Zulassung bleibt separat erforderlich.
pytest-Plugins werden explizit je Aufgabe aktiviert; `pytest_httpbin` wird nur
für Requests geladen. Die Netzwerkisolation bleibt bestehen.

Der Monitor zeigt eine Kurzdiagnose der letzten fehlgeschlagenen Modellantwort
und den Abbruchgrund. Rohantworten und Tokenverbrauch bleiben in der Monitor-API
und im Belegarchiv verfügbar. Eigene Tabs für Aktionen, Werkzeugergebnisse und
Antworten sowie die vollständige JSON-Ansicht der Agentenbelege entfallen.
Aktionen und Werkzeugbeobachtungen, die tatsächlich Teil einer späteren
Modellanfrage sind, bleiben in deren Kontext sichtbar.
„Neuester“ lädt auch für einen ausgewählten aktiven Lauf
neue Schritte nach; ein ausdrücklich gewählter historischer Schritt bleibt
fixiert. Alle angezeigten Schritte beginnen bei 1; die Archivdateien und
API-Schrittindizes bleiben zur Kompatibilität nullbasiert. Laufzeitänderungen
erfordern einen neuen Freeze. Das geänderte Basisimage wird beim nächsten Start
neu gebaut; alte Laufarchive werden nicht migriert.

Für Entwicklungsversuche in der TOML `phase = "development"` setzen; diese Phase
akzeptiert Pilot- und Entwicklungsaufgaben. Die vorhandenen Launcher-Modi regeln
weiterhin Umfang und Vorbereitung. Mit `--config` lässt sich eine eigene TOML
nutzen. Jeder Freeze speichert `designs/pytest.json`, `designs/cubie.json` und die
Design-/Kern-IDs im Laufplan. Ergebnisse und `report.by_design` führen diese IDs.

Eigene Varianten werden als JSON mit `core` und `specialization` konfiguriert:

```toml
# Optional; Pfade relativ zu dieser TOML.
[designs]
pytest = "variants/pytest-v3.json"
cubie = "variants/cubie-v3.json"
```

Eine Ausgangsvariante lässt sich offline exportieren:

```bash
PYTHONPATH=experiments/testguided-study .venv/bin/python - <<'PYTHON'
import json
from pathlib import Path
from testguided_study.design import default_design
root = Path("experiments/testguided-study")
guides = {mode: (root / "guides" / f"{mode}.md").read_text() for mode in ("pytest", "cubie")}
for mode in guides:
    print(json.dumps(default_design(mode, guides), ensure_ascii=False, indent=2))
PYTHON
```

Bei expliziten Designs stammen Prompt und Frameworkanleitung vollständig aus
diesen JSON-Dateien. Die gemeinsamen Regeln stehen in `core`; `specialization`
erlaubt ausschließlich `id`, `mode`, `guide` und `examples`. Inhaltsänderungen
ändern die SHA-256-Identität auch ohne neues Versionslabel. Für den Vergleich
müssen beide Bedingungen denselben Kern verwenden.

Eine Hauptmessung verlangt jetzt zusätzlich eine Kampagnendatei. Den Verweis
auf oberster Ebene der TOML vor den Tabellen eintragen:

```toml
phase = "measurement"
campaign = "campaign.json"
```

```json
{
  "hypothesis": "Die eingefrorenen Varianten erfüllen die Qualifikation",
  "parent_revision": "vorherige Design-ID",
  "development_archives": ["runs/development-01/frozen"]
}
```

Archivpfade sind relativ zur Kampagnendatei. Alle für die Entwicklung verbrauchten
Aufgabenarchive angeben: ihre Aufgaben und verwandten Gruppen sind für die Messung
gesperrt. Diese Liste ist die explizite Herkunftsangabe des Studienautors; außerhalb
dieser Liste durchgeführte Experimente kann der Runner nicht entdecken.

Die feste Qualifikationsschwelle verlangt je Bedingung zwei unabhängig gelöste
reale Aufgabengruppen mit beobachtetem Assertion-Rot und anschließendem Grün
auf denselben Testzielen bei geändertem Workspace. Synthetische Smokes zählen
nicht. Ein beitragendes Entwicklungsarchiv muss vollständig verfügbar sein und
dieselben Designs, Budgets, Modelloptionen und Images verwenden. Die Vorprüfung
vergleicht zusätzlich konkrete Modell-, Image- und swegemma-Identitäten.
Ein selbst gesetztes `qualification: true` ersetzt keine Belege.
`campaign.json` im Freeze hält Zulassung und Belegmomentaufnahmen fest.

Die 29 ursprünglichen EBT-Verträge unter `tests/testguided_study_design` sind
um Session-, Freeze-, Berichts-, Qualifikations- und Workspace-Integrationstests
ergänzt. Diese Tests und deterministische Modell-Replays belegen technische
Eigenschaften. Eine höhere Lösungsquote muss erst in neuen Entwicklungsversuchen
mit echter Modellinferenz gezeigt werden.

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
| Pilot | 3 | 1 | 6 | 30 Minuten | 3:36 Stunden |
| Drei Stunden | 5 | 1 | 10 | 30 Minuten | 6:00 Stunden |
| Sechs Stunden | 10 | 1 | 20 | 30 Minuten | 12:00 Stunden |

Alle Standardprofile sowie v6 und v7 verwenden 1800 Sekunden pro Agent und Aufgabe.
`model_calls` und `tool_calls` bleiben als Kompatibilitätsfelder mit Wert `0`
erhalten. Positive Werte aus älteren Konfigurationen und `--model-calls` werden
ignoriert; Aufrufzahlen können das Zeitbudget nicht verkürzen. Ausbleibender
Fortschritt und wiederholte ungültige Ausgaben beenden den Task ebenfalls nicht.
Die Modelloption `num_predict = 8192` begrenzt die **Ausgabe** pro Antwort;
`num_ctx = 32768` ist das Gesamtfenster, `context_bytes = 80000` die zusätzliche
hostseitige Kontextgrenze. Die Laufzeit reserviert weiterhin Platz für Schema
und Ausgabe, sodass das tatsächlich nutzbare Eingabebudget kleiner ist.

Die Aufgabenzahlen bleiben unverändert. Mit dem höheren Zeitbudget können die
bisherigen Drei-/Sechs-Stunden-Profile ihre nominellen Planungsziele überschreiten;
`fits_allowance` weist dies aus. Für die bisherigen Zeitzielwerte passen nach der
bisherigen Planungsformel zwei bzw. fünf Aufgaben. Sichtbare Baselineprofile,
Imagebau und tatsächliche Setups können zusätzlichen Aufwand verursachen.

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


## Agentendesign v4 (historisch)

v4 verwendet `testguided-core-v4` mit `pytest-guide-v4` beziehungsweise
`cubie-guide-v4`. [Entwurf und Begründung](AGENTENDESIGN-V4.md) dokumentieren die
Änderungen aus Pilot `20261111-180702`: vom Runner gebundene Datei-Versionen,
kleine Änderungen, explizite Prüfung des Testorakels, Reproduktionsfeedback nach
Grün ohne Produktionsänderung und ein eingeschränktes Reparaturschema nach
ungültiger Modellausgabe. Historische Freezes werden nicht verändert.


## Agentendesign v5

Neue Freezes verwenden `testguided-core-v5` mit identischer Steuerung für beide
Testbedingungen. [Design und Validierung](AGENTENDESIGN-V5.md) beschreiben drei
verbindliche Analysephasen: Reproduktion vor Dateiänderungen, Diagnose nach
fehlgeschlagenen Tests und Abschlussprüfung vor `submit`. Strukturierte
Modellbewertungen bleiben von Runner-Evidenz getrennt.

`think = true` ist in `study.toml` und allen drei Profilen aktiviert. Modell-,
Kontext-, Ausgabe- und Zeitbudgets bleiben unverändert. v3/v4 sind weiterhin über
`default_design(..., version=3)` bzw. `version=4` auswählbar. Thinking ist unabhängig
von der Designversion konfigurierbar; Variantenvergleiche müssen beide Einstellungen
explizit einfrieren. Historische Archive werden nicht geändert.
