# EBT-Verträge für automatische Studienstarts und Laufverwaltung

Der normale Einstieg ist `./study` beziehungsweise `./study --mode pilot`.
Dieser Starter übernimmt Auswahl, Vorbereitung, Imagebereitstellung, Zulassung,
einen neuen Freeze, Vorprüfung, Agentenläufe, Monitor und Bericht bereits selbst.
Ein manueller `freeze`-Befehl gehört nicht zum normalen Startablauf. Die getrennten
Low-Level-Befehle bleiben für Diagnose und ausdrücklich vorbereitete Studien nutzbar.

Die [Start-/Archiv-Cases](test_run_management_ebt.py) und die
[Build-/Cache-Cases](test_run_image_management_ebt.py) enthalten **32 EBT-Cases in
zwölf Vertragsgruppen**. Sie sichern diesen Einstieg ab und formulieren die
Anforderungen für kollisionsfreie Starts und unveränderte Altarchive. Die Cases
verwenden `EBT(..., reporter=None).run()` und verlangen explizit
`result.evaluation is True`; es gibt keine `xfail`-Markierung.

```bash
.venv/bin/python -m pytest \
  tests/testguided_study_design/test_run_management_ebt.py \
  tests/testguided_study_design/test_run_image_management_ebt.py -q
```

| Gruppe | Vertrag | Cases | Ausgangsstand |
| --- | --- | ---: | --- |
| M01 | CLI-Aufruf ohne Argumente erledigt den vollständigen Pilotablauf bis zum Bericht; eigener Archivpfad, Imagebereitstellung und sechs gepaarte Teilversuche entstehen automatisch | 1 | grün |
| M02 | Zwei direkte Starts in derselben Sekunde erhalten unterschiedliche vollständige Archive; das erste bleibt unverändert | Smoke/Pilot | rot |
| M03 | Zwei gleichzeitige automatische Starts reservieren unterschiedliche Archivpfade und erhalten jeweils einen zugelassenen Freeze | 1 | rot |
| M04 | Neuer Start übernimmt aktuelle Guides, Quellidentität, Modellidentität, Imageidentität, Budgetüberschreibung und Aufgabeneingaben automatisch | 6 | grün |
| M05 | Fehlgeschlagene Imagebereitstellung, Zulassung oder Vorprüfung archiviert den Fehler ohne Modellaufruf; ein neuer Start gelingt ohne Bereinigungs- oder Reparaturbefehle | 3 | grün |
| M06 | Unterbrechung erhält Teilversuch und Belege, räumt Container auf und verhindert einen unabhängigen neuen Start nicht | 1 | grün |
| M07 | `--prepare-only` führt keine Inferenz aus; ein späterer Normalstart benötigt kein manuelles Fortsetzen oder Umwidmen des vorbereiteten Archivs | 1 | grün |
| M08 | Ein ausdrücklich angegebenes bestehendes Ausgabeziel wird weder überschrieben noch unbemerkt auf einen anderen Pfad umgeleitet | leer/belegt | grün |
| M09 | Ein abgewiesener Low-Level-Neustart eines abgeschlossenen Freezes verändert keinerlei Archivdateien | 1 | rot |
| M10 | Ein automatisch angelegter Monitor gehört zum neuen Archiv und wird bei Erfolg, Startfehler, Imagefehler, Vorprüfungsfehler und Unterbrechung geschlossen | 5 | grün |
| M11 | Wheel-Cache wird unverändert wiederverwendet und nach fehlender Datei, Beschädigung oder Versionswechsel ohne manuelles Aufräumen erneuert | 4 | 3 grün, Versionswechsel rot |
| M12 | Unveränderte Images werden wiederverwendet; Änderungen an Basisrecipe, Abhängigkeiten, Cubie-Quellen oder Cubie-Recipe bauen nur die nötigen Images neu und archivieren deren aktuelle Identitäten | 5 | grün |

## Festgelegte Anforderungen

**Automatischer Freeze:** Jeder neue Versuch benötigt weiterhin eine eigene
unveränderliche Momentaufnahme. Deren Erzeugung ist Aufgabe des Starters. Der
Benutzer muss weder Archivnamen erfinden noch alte Freigaben entfernen, Quellen
manuell einfrieren oder nach Änderungen einen bestehenden Freeze reparieren.
M01/M04 führen den echten Freeze und die echte Vorprüfung aus. Modell- und
Imageidentitäten werden erneut erfasst; ein vorhandenes `ready.json` wird nicht
als Freibrief für geänderte Eingaben verwendet. M04 vergleicht sämtliche
Dateihashes des vorherigen Archivs vor und nach dem nächsten Start.

**Kollisionsfreie automatische Ziele:** Die Uhrzeit allein ist keine eindeutige
Laufidentität. M02/M03 frieren den Zeitwert absichtlich ein. Ohne `--output`
muss der Starter auch dann selbst einen freien Pfad reservieren. Ein bestimmtes
Namensschema oder Suffix wird nicht vorgeschrieben. Die Reservierung muss bei
gleichzeitigen Starts funktionieren. Ein ausdrücklich gesetztes `--output`
behält dagegen den Überschreibschutz aus M08.

**Archivschutz und Fehlererholung:** Fehlversuche bleiben als solche lesbar.
Ein normaler neuer Start erzeugt einen neuen Versuch, statt Daten zu löschen,
einen Teilversuch stillschweigend fortzusetzen oder Inferenz im Hintergrund
automatisch zu wiederholen. M09 verlangt außerdem, dass schon die Ablehnung
eines unzulässigen Neustarts ohne Schreibzugriff auf das alte Archiv erfolgt.
Die Implementierung prüft vorhandene Teilversuche jetzt vor dem Anlegen eines
Observers und vor dem Schreiben eines Monitorzustands.

**Reproduzierbarkeit:** Gleiche Einstellungen dürfen dieselbe Aufgabenauswahl
und dieselben Seeds ergeben. Das ist kein Grund, zwei Versuche in dasselbe
Archiv zu schreiben. Image- und Modelländerungen zwischen Versuchen werden neu
erfasst; die bestehenden Identitätsprüfungen innerhalb eines laufenden Versuchs
werden durch diese Anforderungen nicht gelockert. Ebenso bleiben die
Qualifikationsanforderungen für eine Messkampagne erhalten.

**Automatische Buildverwaltung:** Der Aufruf des Starters soll nach einem
Versionswechsel keinen manuellen Cacheeingriff verlangen. M11 lässt deshalb
das alte Wheel im Buildcache liegen, während das Buildwerkzeug eine neue Version
erzeugt. Der Starter muss das aktuelle Artefakt auswählen und dessen Hash im
Receipt speichern können. Der Vertrag schreibt nicht vor, ob alte Cachedateien
behalten oder kontrolliert entfernt werden. Die Implementierung wählt jetzt
das gebaute Wheel zur aktuellen Projektversion aus; ältere Versionen im Cache
blockieren den Start nicht mehr.

M12 verwendet die echte Signatur- und Cachelogik. Eine Änderung gemeinsamer
Imageeingaben verlangt ein neues Basisimage und darauf aufbauend ein neues
Cubie-Image. Eine Änderung nur an Cubie-Quellen verlangt ein neues Wheel und
Cubie-Image; eine Änderung nur an der Cubie-Recipe verlangt lediglich dessen
Neubau. Die Images beider Versuchsbedingungen behalten dieselbe gemeinsame
Basis. Frühere Buildbelege eines Versuchs dürfen dabei nicht überschrieben werden.

## Ausführung und Aussagegrenzen

CLI-Parsing, Auswahl, Snapshotaufbereitung, Zulassungslogik, Freeze,
Vorprüfung, Identitäts-/Hashprüfungen, Sessionloop, Laufmanifeste, Observer und
Bericht laufen tatsächlich. Die Testdaten bestehen aus drei synthetischen,
ausdrücklich nicht fachlich aussagekräftigen Pilotaufgaben. Smoke verwendet
weiterhin genau eine Aufgabe. Es wird weder auf aktuelle noch auf historische
Studienarchive zugegriffen.

Container, Modell, Evaluator und Monitorserver sind deterministische
Ports ohne externe Dienste. M01–M10 ersetzen die Imagebereitstellung als Port;
M11/M12 führen die echte Wheel-/Imagesignatur-, Cache-, Neubauentscheidungs- und
Receiptlogik aus. Dort sind nur uv-/Docker-Kommandos und die Docker-Inspektion
durch deterministische Ports ersetzt; es werden keine echten Images gebaut.
Die Quelländerungsvariante M04 ergänzt die echte
Quellhashliste um eine veränderliche Testidentität; sie bearbeitet keine
Repositoryquellen während des Tests. Die Nebenläufigkeitsprüfung verwendet zwei
Threads, die denselben Startcode gleichzeitig aufrufen. Sie prüft keine
prozessübergreifenden Docker- oder Imagebausperren. Die Reihe benötigt keine
Modellinferenz und keine Netzwerkverbindung.

Der verifizierte Ausgangsstand war **fünf rot, 27 grün**. Die drei
Kollisionsfälle M02/M03, der Archivschutzfall M09 und der Versionswechsel im
Wheel-Cache aus M11 sind inzwischen im Produktivcode behoben. Automatische
Archivpfade werden mit exklusivem `mkdir` reserviert; bei einer Kollision wird
ein freier numerischer Suffix versucht. Der Überschreibschutz expliziter Ziele
bleibt erhalten. Alle 32 Cases bestehen mit unveränderten Erwartungen.

Gemeinsame Design- und Experimenttests einschließlich dieser Anforderungssuite:
**302 bestanden, drei Docker-Fälle übersprungen**. Ruff und die Diff-Prüfung
der betroffenen Dateien sind sauber.
Die drei Docker-/swegemma-Integrationsfälle wurden separat mit
`CUBIE_STUDY_DOCKER=1` ausgeführt: **drei bestanden**, ohne Modellinferenz.
