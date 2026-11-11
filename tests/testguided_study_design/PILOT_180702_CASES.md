# EBT-Verträge zu den Auffälligkeiten im Piloten 20261111-180702

Diese neue Reihe ergänzt die [bestehenden technischen Pilotverträge](PILOT_TECHNICAL_CASES.md)
um **48 Cases in 16 Vertragsgruppen**. Grundlage ist die Untersuchung des noch
aktiven Laufs vom 11. November 2026, Stand 18:33 Uhr: drei abgeschlossene
Teilläufe und der damals aktive Cubie-Requests-Lauf. Die Reihe wurde als
vorgezogene Abnahme angelegt; die Laufzeitkorrekturen sind inzwischen implementiert
und alle 48 Cases bestehen ohne geänderte Erwartungen oder `xfail`.
Die Erweiterung A12–A16 berücksichtigt zusätzlich das inzwischen abgeschlossene
Ergebnis von Lauf 0004: pytest-Exitcode 4 durch einen agentenverursachten
Einrückungsfehler, `resolved=null` im Gesamtergebnis und „Noch offen“ im Monitor.

Die [Datei-/Session-Cases](test_pilot_180702_ebt.py) und die
[Evaluator-/Monitor-Cases](test_pilot_180702_evaluation_ebt.py) verwenden echtes
`EBT(..., reporter=None).run()` und verlangen `result.evaluation is True`.
Es gibt keine `xfail`-Markierungen. Laufzeitquellen und historische wie aktive
Archive werden nicht verändert oder als Testabhängigkeit gelesen.

```bash
.venv/bin/python -m pytest \
  tests/testguided_study_design/test_pilot_180702_ebt.py \
  tests/testguided_study_design/test_pilot_180702_evaluation_ebt.py -q
```

## Vertragsmatrix

| Gruppe | Abnahme | Cases | Ausgangsstand |
| --- | --- | ---: | --- |
| A01 | Ungültiger Python-Ersatz wird vor dem Schreiben abgelehnt; Bytes, Änderungszeit und Workspaceversion bleiben identisch | 3 Fehlerarten | rot |
| A02 | Gültige Python-Edits und Änderungen an Nicht-Python-Dateien funktionieren weiterhin | 2 | grün |
| A03 | Eine bereits syntaktisch defekte Python-Datei lässt sich in einen gültigen Zustand reparieren | 1 | grün |
| A04 | Änderungskonflikte unterscheiden falschen Hash, fehlenden und mehrdeutigen Anker; aktueller Hash, Trefferzahl und Reparaturhinweis bleiben verfügbar | 3 | rot |
| A05 | Nach Konflikt, erneutem Lesen und einem korrigierten kleinen Edit erreicht die Session die Abgabe; die erste Produktionsänderung wird korrekt gezählt | 2 Konflikte × 2 Frameworks | grün |
| A06 | Unveränderte Konflikt-/Leseschleifen stoppen weiterhin begrenzt, ohne Produktionsmutation | 1 | grün |
| A07 | Import- und Syntaxfehler bei Collection liefern einen existierenden Dateipfad; nach Reparatur lässt sich dieser direkt als Testziel ausführen | 2 | rot |
| A08 | Bei unbekanntem Collectionursprung wird keine ausführbar aussehende Test-ID erfunden | 1 | rot |
| A09 | Tatsächlich aufgezeichnete Test-IDs behalten kleingeschriebene Klassen und parametrisierte Sonderzeichen | 1 | grün |
| A10 | Ursachen und Counts der ursprünglichen Baseline bleiben bei Kontextreduktion neben Herkunftshinweis, Aufgabe und Guide sichtbar | 3 Ursachen × 2 Kontextgrößen | normal grün, reduziert rot |
| A11 | Ein abgelehnter Syntax-Edit erreicht den nächsten Modellkontext als Werkzeugfehler, erlaubt eine Korrektur und erzeugt keine vorzeitige Produktionsänderungsmetrik | 2 Frameworks | rot |
| A12 | Agentenverursachte Syntax-, Einrückungs- und Importfehler zählen bis in Ergebnis, Monitorzähler und Berichtsaggregation als nicht gelöst; Assertionfehler und Erfolg bleiben korrekt | 5 | 3 rot, 2 grün |
| A13 | Ungültige pytest-Option, Verifier-Timeout und Verbindungsabbruch bleiben nicht verfügbar; Container werden aufgeräumt | 3 | grün |
| A14 | Abgeschlossene Versuche ohne Auswertung zeigen „Nicht verfügbar“ samt finaler Dauer, während die Gesamtstudie weiterläuft | 9 Endzustände | 8 rot, 1 grün |
| A15 | Ausstehende und laufende Versuche bleiben von bekannten Erfolgen und Misserfolgen unterscheidbar | 4 | grün |
| A16 | Polling aktualisiert Ergebnis und Zähler beim Übergang von laufender Auswertung zu nicht verfügbar und anschließend zu bekanntem Misserfolg | 1 | rot |

## Festgelegte Reparaturverträge

**A01/A11:** Die Syntax des vollständigen Änderungskandidaten muss vor einer
Mutation geprüft werden. Ein fehlgeschlagener Kandidat liefert ein strukturiertes
Werkzeugergebnis mit `status="tool_error"` und einer verständlichen `error`-Ursache.
Die Cases schreiben keinen neuen Fehlercode vor. Sie umfassen Syntax-, Einrückungs-
und Stringfehler. A03 verhindert, dass eine Prüfung des alten Dateiinhalts dessen
Reparatur blockiert. A02 begrenzt die Syntaxpflicht auf Python-Dateien.

**A04:** Der bestehende Code `edit_conflict` bleibt erhalten. Das zusätzliche Feld
`conflict_reason` unterscheidet `hash_mismatch`, `anchor_missing` und
`anchor_ambiguous`. Dies ist ein neu definierter maschinenlesbarer Vertrag, der
passende Reparaturanweisungen ermöglicht. Er ersetzt weder den Ausgangshash noch
die Eindeutigkeitsprüfung. Konflikte werden nicht automatisch überschrieben.
A05/A06 sichern erfolgreiche Erholung und begrenzte erfolglose Wiederholungen
gegeneinander ab; die Stagnationsschwelle wird nicht pauschal gelockert.

**A07/A08:** Für Fehler während der Modulcollection ist der relative Dateipfad
das ausführbare Ziel. Eine noch nicht gesammelte Testfunktion muss nicht erfunden
werden. Fehlt eine belastbare Zuordnung, ist `id` leer beziehungsweise `null`;
Ursache und Phase müssen trotzdem erhalten bleiben. A07 benutzt reale lokale
pytest-Prozesse und führt den zurückgegebenen Zielwert nach einer Reparatur
tatsächlich aus. A09 schützt unabhängig davon aufgezeichnete Laufzeit-Node-IDs.

**A10:** Kontextreduktion darf bei bekannten Ausgangsfehlern nicht nur Counts
übriglassen. Mindestens die hier jeweils einzige repräsentative Ursache muss
erhalten bleiben: fehlendes Paket, Netzwerkisolation oder Snapshotdefekt.
Die vollständige Baseline wird dabei nicht verändert. Das Beispielbudget ist
1.800 Bytes; optionale alte Notizen erzwingen den verkleinerten Kontextpfad.
Die Fälle verlangen weder eine automatische Paketinstallation noch das Abschalten
der Netzwerkisolation. Sie verbieten auch keine ausdrücklich begründete breite
Testausführung. Ob das Modell mit diesen Informationen bessere Testziele wählt,
muss später mit echter Modellinferenz geprüft werden.

**A12/A13:** Jeder Verifier startet auf einer synthetischen, nachweislich grünen
Ausgangssuite. Für A12 wird anschließend ein echter Produktionspatch mit
`git apply` angewendet. Ein Importabbruch durch diesen Patch muss als
`evaluation.available=true` und `resolved=false` im Gesamtergebnis ankommen.
Ein gestagnierter Agentenlauf ändert daran nichts. Der Fall wird im Monitor als
fehlgeschlagen gezählt und bleibt in der Berichtsaggregation ein verfügbarer
Versuch. Das archivierte Evaluatorergebnis muss mit dem eingebetteten Ergebnis
übereinstimmen. Alle angelegten Sandboxmanager müssen aufgeräumt werden.

Ein pauschales Freigeben jedes Exitcodes 4 genügt ausdrücklich nicht: Eine
unbekannte pytest-Option erzeugt ebenfalls diesen Code, aber keinen belastbaren
Lösungstest. Dieser Fall sowie Timeout und Verbindungsabbruch behalten
`resolved=null`, erhöhen den Nicht-verfügbar-Zähler und zählen im Bericht nicht
als verfügbare Versuche. Es wird kein bestimmtes neues Diagnosefeld vorgegeben.

**A14–A16:** Eine endliche `total_seconds` und ein abgeschlossener Lauf mit
unbekanntem Ergebnis dürfen nicht als „Noch offen“ erscheinen. Abgedeckt sind
`stalled`, `submitted`, `context_budget`, `invalid_output`, `wall_budget`,
`model_budget`, `tool_budget`, `infrastructure_error` und der bereits korrekt
behandelte Zustand `unavailable`. Die Studie insgesamt bleibt in den Beispielen
aktiv; der Monitor darf daher nicht nur auf den Studienabschluss reagieren.
Eine tatsächlich noch laufende Auswertung bleibt „Noch offen“. Bei bekannten
booleschen Ergebnissen haben „Gelöst“ und „Nicht gelöst“ Vorrang. Die
Pollingfolge prüft das Nachladen der Tabellenzelle und der Zähler mit demselben
ausgelieferten JavaScript, das der Monitor benutzt; die Ergebnislogik wird nicht
im Test nachgebaut. Der letzte Übergang ist eine synthetische UI-Zustandsfolge,
keine automatische Neuauswertung historischer Archive.

## Ausführung und Grenzen

Die Reihe benötigt keine Modellinferenz, kein Docker, keinen Browser und keinen
Netzwerkdienst. Dateitools, Sessionloop, Controller, Kontextaufbau, EBT und
Diagnosecode laufen tatsächlich. Für A07 und A12/A13 laufen zusätzlich echte
pytest-Prozesse in temporären Workspaces. A12/A13 ersetzen die swegemma-
Orchestrierung und Containergrenze, führen aber den realen Evaluatoradapter,
Studienrunner, Observer und die Berichtsaggregation aus. Timeout und
Verbindungsabbruch werden deterministisch an der Verifiergrenze simuliert.
A14–A16 führen das ausgelieferte Monitor-JavaScript mit Node.js und einem
minimalen DOM aus; bei fehlendem Node.js werden nur diese Cases übersprungen.
Das ersetzt keine Browserprüfung. A05/A06/A11 verwenden deterministische Modellantworten;
sie sind technische Ablaufverträge und kein Nachweis verbesserter Modellleistung.

Der ausgeführte Ausgangsstand war **26 rot, 22 grün**: die ursprünglichen
26 Cases ergeben 14 rot und zwölf grün; die 22 zusätzlichen Cases ergeben
zwölf rot und zehn grün. Nach den Laufzeitkorrekturen sind **48 Cases grün**.
Die Erwartungen wurden nicht abgeschwächt. Syntaxprüfungen kompilieren den
vollständigen Änderungskandidaten vor dem Schreiben und erkennen dadurch auch
`return` außerhalb einer Funktion oder doppelte Parameternamen. Collector-IDs
stammen aus dem pytest-Probeplugin, nicht aus einer Rückübersetzung von Punktnotation.
Bei Kontextreduktion bleiben bis zu drei unterschiedliche Baseline-Ursachen neben
Counts und Herkunft sichtbar. Der Evaluator ordnet Exitcode 4 nur dann als
verfügbaren Misserfolg ein, wenn ein erfasster conftest-Importtraceback auf eine
Datei des effektiven Produktionspatches verweist. Unklare Fehler bleiben nicht
verfügbar. Abgeschlossene Monitorzeilen werden anhand ihrer finalen Laufzeit
erkannt; eine laufende Auswertung bleibt offen.

Zehn zusätzliche [Regressionsfälle](test_pilot_repair_regressions.py) sichern
Compiler-Syntaxfehler, verschachtelte Collectorpfade, Punkte in Dateinamen sowie
die Abgrenzung zu unveränderten Dateien, Drittanbieterpaketen und CLI-Fehlern ab.

Gemeinsame lokale Design- und Experimenttests einschließlich der neuen
Kontextansicht-Verträge: **270 bestanden, drei Docker-Fälle übersprungen**.
Die drei Docker-/swegemma-Integrationsfälle wurden anschließend mit
`CUBIE_STUDY_DOCKER=1` und der vorhandenen swegemma-0.2.11-Umgebung separat
ausgeführt: **drei bestanden**, ohne Modellinferenz.
Ruff, JavaScript-Syntaxprüfung und Diff-Prüfung der betroffenen Dateien sind sauber.
Geänderte Laufzeitquellen erfordern einen neuen Freeze für weitere Studienläufe.
Die abgeschlossenen Pilotarchive werden nicht verändert oder nachträglich neu bewertet.
