# Techniknachweis vom 11.11.2026

Die Nachweise beschreiben **keine Ergebnisse einer Nutzenstudie**.

## Version 2: Aufgabentypen und konfigurierbare Umfänge

Der [aktuelle maschinenlesbare Nachweis](validation-v2.json) ergänzt die erste
Validierung um Auswahl, Stundenplanung und Typauswertung:

- **30 Tests bestanden** einschließlich echter swegemma-/Docker-Integration
  in 39,71 Sekunden. Dabei werden ausschließlich die Modellantworten wiedergegeben.
- Kurze und längere Auswahl bleibt bei identischem Pool und Seed ein Präfix;
  verwandte und gegensätzliche historische Fixes werden nicht doppelt ausgewählt.
- Freeze und Bericht bewahren Typ-/Änderungsmetadaten und konfigurierte Anzahl;
  Messaufgaben ohne Typangaben oder mit falschem Repository werden abgewiesen.
- Berichte je Typ enthalten Ergebnisse, Ressourcen und echte Testbeobachtungen;
  fehlende Läufe und unbekannte Tokenwerte bleiben sichtbar.
- 39 Aufgaben fachlich geprüft, davon 24 zusätzlich zur ersten Auswahl.
  Aktuell sind 26 fachliche Kandidaten zur technischen Aufbereitung geeignet;
  neun sind bedingt, drei zurückgestellt und eine ausgeschlossen. Die übrigen
  90 Aufgaben sind semantisch ungeprüft. Die vollständige Bestandsliste bleibt erhalten.
- Die drei konkreten Profile und Pläne wurden offline erzeugt: Pilot mit drei,
  Hauptprofile mit fünf bzw. zehn Aufgaben. Die Hauptprofile haben identische
  Agentenbudgets. Reale Aufgaben bleiben technisch unzugelassen.

Die Codeänderung erfordert neue Freezes. Der Smoke `local/smoke-ready/` aus
Version 1 ist damit überholt. Der neu erzeugte Smoke liegt unter
`local/smoke-types-v2-ready/`; seine Vorprüfung enthält die aktuellen Codehashes.

## Version 1: Ursprüngliche Schnittstellen- und Isolationsprüfung

Der [ursprüngliche maschinenlesbare Nachweis](validation.json) hält die damals
ausgeführten Prüfungen und verwendeten Versionen fest:

- 20 Offline-Tests bestanden; zwei Containerprüfungen sind dort bewusst ausgeschaltet.
- Mit Docker und der vorhandenen swegemma-0.2.11-Umgebung: **22 Tests bestanden**
  in 39,67 Sekunden. Nur die Modellantworten wurden in diesen Tests wiedergegeben.
- Echte Container belegen Teständerungen vor und nach Grün in beiden Bedingungen.
  Die private Evaluation lehnt eine falsche Lösung trotz vereinfachter grüner
  sichtbarer Tests ab. Gleichnamige Tests in verschiedenen Dateien werden bei
  der zusätzlichen Prüfung der privaten Node-IDs unterschieden.
- Vorprüfung gegen das tatsächlich installierte Ollama 0.40.2 und `gemma4:12b`
  erfolgreich. Modell-Digest beginnt mit `4eb23ef187e2`; vollständig im JSON.
  Im Pytest- und Evaluatorimage fehlt Cubie, im Cubie-Image funktioniert EBT.
  Beide verwenden Python 3.13.18 und pytest 9.2.0.
- Ein einzelner echter API-Aufruf lieferte eine gültige Aktion
  `list_files` mit `stage=inspect`: 5,742 Sekunden, 48 gemeldete Eingabe- und
  15 Ausgabetokens. Das prüft Schnittstelle und Aktionsschema, keine Aufgabenlösung.
- Wheel mit angepassten `experiments/ollama-agents`-Paketpfaden gebaut und im
  Cubie-Image installiert; Ruff und `uv lock --check --offline` bestanden.

Der aktuelle lokal eingefrorene **synthetische Smoke** ist mit folgendem Befehl
ausführbar, solange Code und Modellidentität unverändert bleiben. Darin wurden
noch keine Agentenläufe gestartet:

```bash
/home/symphonie/PycharmProjects/start-local-devagent/.venv/bin/python \
  experiments/testguided-study/study.py run \
  experiments/testguided-study/local/smoke-types-v2-ready
```

Dieser Befehl führt zwei echte Modellläufe aus und unterliegt den Budgets der
eingefrorenen TOML. Bei Codeänderungen einen neuen Freeze und neue Vorprüfung
erstellen. Generierte lokale Archive sind absichtlich nicht im Git enthalten;
der reproduzierbare Aufruf für einen neuen Smoke steht im README.

Für die fachliche Studie ist der [Kandidatenplan samt Zulassungsschritten](DATEN.md)
vorbereitet. Reale Aufgaben wurden noch nicht zugelassen oder gemessen.
