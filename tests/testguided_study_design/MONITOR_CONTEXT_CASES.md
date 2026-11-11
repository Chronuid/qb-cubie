# EBT-Verträge für die vereinfachte Kontextansicht

Die Studienwarte bietet nur noch den Tab „Kontext“. Die Tabs „Aktion“,
„Werkzeug“ und „Antwort“ sowie die zusätzliche vollständige Agenten-JSON-Ansicht
entfallen. Kontext, Lauf-/Schrittauswahl, Pause, Kopieren und Zeilenumbruch bleiben
erhalten. Eine kurze Fehlerdiagnose und der Abbruchgrund bleiben sichtbar.

Die [elf Cases in acht Gruppen](test_monitor_context_ebt.py) verwenden
`EBT(..., reporter=None).run()` mit expliziter Prüfung von
`result.evaluation is True`.

| Gruppe | Abgesicherte Eigenschaft | Cases |
| --- | --- | ---: |
| Struktur | Nur Kontext ist als Tab vorhanden; Tab und Panel sind zugänglich verknüpft; kein zusätzlicher Rohdatenbereich | 1 |
| Live-Kontext | Neue tatsächlich gesendete Nachrichten erscheinen; nicht gesendete Aktionen, Werkzeugergebnisse und Antworten werden nicht als Kontext dargestellt | 1 |
| Leerzustand | Fehlender, leerer oder falsch geformter Kontext bleibt als Leerzustand erkennbar; Kopieren ist deaktiviert und kopiert keine Ersatzdaten | 3 |
| Pause | Polling läuft weiter; die Ansicht bleibt fixiert und zeigt nach Fortsetzen die aktuelle Anfrage | 1 |
| Archivwechsel | Ein fixierter Archivschritt bleibt beim Polling stabil; Rückkehr zur Live-Ansicht zeigt den aktuellen Kontext | 1 |
| Kopieren | Live- und Archivansicht kopieren ausschließlich die ausgewählten gesendeten Nachrichten als JSON; Unicode und Quelltext bleiben erhalten | 2 |
| Leseposition | Neue Live-Anfragen erhalten Scrollposition und gewählten Zeilenumbruch | 1 |
| Fehlerhinweis | Kurzdiagnose und Abbruchgrund bleiben sichtbar, ohne Verweis auf entfernte Ansichten oder Darstellung der Rohantwort als Kontext | 1 |

```bash
.venv/bin/python -m pytest \
  tests/testguided_study_design/test_monitor_context_ebt.py \
  tests/testguided_study_design/test_pilot_monitor_ebt.py \
  experiments/testguided-study/tests/test_monitor.py \
  experiments/testguided-study/tests/test_monitor_poll_ebt.py -q
```

Die Strukturprüfung liest das tatsächliche HTML. Die anderen Cases führen das
ausgelieferte JavaScript mit Node.js, deterministischem Transport und einem
minimalen DOM aus. Dessen `getElementById` liefert nur im HTML vorhandene
Elemente; veraltete Zugriffe auf entfernte Elemente werden dadurch sichtbar.
Bei fehlendem Node.js werden nur die JavaScript-Cases übersprungen. Es werden
keine Modellinferenz, Dockercontainer oder aktiven Studienarchive benötigt.
Das ersetzt keine Browserprüfung.

## Prüfung der vorhandenen Suite

Es gibt keine bestehenden EBT-Cases für das Umschalten auf die drei entfernten
Tabs. Daher wurde kein Case gelöscht. Die bestehenden Verträge P17/P18 für
Archivaktualisierung, fixierte Schritte und sichtbare Schrittnummern bleiben
erhalten. Ebenso bleiben die Polling-, Verbindungs- und Abschlussfälle relevant.

P12/P13/P21 prüfen Rohantworten, Tokenverbrauch und Fehlerpersistenz in
Monitorzustand beziehungsweise Archiv-API. Diese Belege bleiben erhalten und
sind unabhängig von den entfernten Tabs. Ihre Tests wurden deshalb nicht
gelöscht oder abgeschwächt. Auch die Evaluator-/Ergebnisanzeigefälle
A12–A16 gehören weiterhin zur separaten Anforderungssuite.

## Verifikation

- Elf neue Kontext-Cases: bestanden.
- Neue und bestehende Monitorprüfungen aus dem obigen Befehl: 32 bestanden.
- Gemeinsame Design- und Experimenttests nach Umsetzung der Laufzeitkorrekturen:
  270 bestanden, drei Docker-Fälle übersprungen; auch A01–A16 sind grün.
- Ruff, JavaScript-Syntaxprüfung und Diff-Prüfung der betroffenen Dateien sind sauber.
