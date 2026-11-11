# EBT-Verträge für die technischen Pilotbefunde

Grundlage: [Technikanalyse des Piloten 20261111-171515](../../experiments/testguided-study/TECHNIKANALYSE-20261111-171515.md).
Die Anforderungssuite enthält 32 parametrisierte Cases in 21 Vertragsgruppen.
Die [ergänzende Reihe zum aktiven Piloten 20261111-180702](PILOT_180702_CASES.md)
definiert separat 48 weitere Cases für die neu beobachteten Auffälligkeiten,
einschließlich Evaluator-Einstufung und Monitoranzeige von Lauf 0004.
Jeder Case führt `EBT(..., reporter=None).run()` aus und prüft explizit
`result.evaluation is True`. Die Cases wurden zuerst rot angelegt und sind inzwischen gegen die überarbeitete
Laufzeitimplementierung grün. Es gibt keine `xfail`-Markierungen; historische
Archive bleiben unverändert.

Aus dem Repository:

```bash
.venv/bin/python -m pytest \
  tests/testguided_study_design/test_pilot_technical_ebt.py \
  tests/testguided_study_design/test_pilot_monitor_ebt.py -q
```

Kein Docker, keine Modellinferenz, keine historischen Archive und keine echten
Netzwerkzugriffe. Die Tests verwenden temporäre Workspaces und deterministische
Antworten an den Modell- und Evaluatorgrenzen. Dateitools, Sessionloop, Controller,
Kontextaufbau, EBT und Diagnosecode laufen tatsächlich. Collection und
Pluginisolation verwenden zusätzlich echte lokale pytest-Unterprozesse.
Die Monitor-Cases führen das ausgelieferte JavaScript mit einem minimalen DOM und
deterministischem Transport aus. Dazu ist Node.js nötig; nur diese Cases werden
bei fehlendem Node.js übersprungen. Das ersetzt keine Browserprüfung.

## Vertragsmatrix

| Gruppe | Abgesteckte Eigenschaft | Varianten | Aktueller Stand |
| --- | --- | ---: | --- |
| P01 | Große Testergebnisse erlauben nächste Anfrage; Counts bleiben sichtbar, vollständiger JUnit-Beleg bleibt archiviert | 2 Frameworks | grün |
| P02 | Komprimierung verändert die vollständigen Originalbelege nicht | 1 | grün |
| P03 | Aus dem Kontext verdrängter Dateitext darf erneut gelesen werden | 1 | grün |
| P04 | Wiederholte Fehlpfade stoppen weiterhin begrenzt und ohne Mutation | 1 | grün |
| P05 | Testauswahl erzeugt keine Produktionsänderung; tatsächliche Mutation wird am richtigen Aufruf erkannt | 2 | grün |
| P06 | Diagnosen nennen korrekte Modul-/Klassen-IDs und erhalten parametrisierte Sonderzeichen | 3 | grün |
| P07 | Das an das Modell gesendete Schema erklärt Zeilennummer, Trefferoffset und Glob-Syntax | 3 | grün |
| P08 | Literalsuche findet den ersten Treffer und paginiert vollständig | 1 | grün |
| P09 | Zulassung speichert eine sichtbare Ausgangsbasis getrennt von privaten Prüftests | gesund, Snapshotdefekt, Netzwerkfehler | grün |
| P10 | Längenabbruch erzeugt eine spezifische Aufforderung zu einer kleinen Folgeaktion | 1 | grün |
| P11 | Zwei abgeschnittene Antworten stoppen begrenzt, archivieren beide Antworten und führen keine Teilmutation aus | 1 | grün |
| P12 | Der aktuelle Monitorzustand enthält bei abgelehnter Antwort Rohdaten und Tokenverbrauch | 1 | grün |
| P13 | Archivabfrage der Monitor-API liefert Fehlantwort und Rohdaten ohne erfundene gültige Aktion | 1 | grün |
| P14 | Ein unbeteiligtes globales Plugin kann einen fokussierten Test nicht beschädigen | mit/ohne defektes Plugin | grün/grün |
| P15 | Änderungskonflikt erfordert weiterhin erneutes Lesen | 1 | grün |
| P16 | Eine zu große obligatorische Aufgabenbeschreibung scheitert explizit | 1 | grün |
| P17 | Ausgewählter aktiver Lauf lädt „Neuester“ nach; expliziter historischer Schritt bleibt fixiert | neuester/fixierter Schritt | grün/grün |
| P18 | Sichtbare Schrittnummer stimmt mit der Nummer des Modellaufrufs überein | 1 | grün |
| P19 | Fehlendes Testziel und leere Collection sind maschinenlesbar unterscheidbar | fehlender Pfad/Produktionsmodul | grün |
| P20 | Erfolgreiche Collection zählt gesammelte Fälle, aber keine bestandenen Ausführungen | 1 | grün |
| P21 | Beginn des Reparaturaufrufs lässt die vorherige Fehlantwort für Monitorabfragen erhalten | 1 | grün |

## Bewusst festgelegte neue Beobachtungsverträge

P09 verlangt ein neues Artefakt `admission/visible-baseline.json` mit
`diagnostics.collected` und `diagnostics.counts.failed`. Sein Inhalt beschreibt
die **ursprünglichen sichtbaren Tests vor dem privaten Testpatch**. Der kleine
Workspace enthält zwei sichtbare Fälle; nach dem privaten Testpatch sind es drei.
Dadurch genügt es nicht, einfach nachträglich alle Tests einschließlich der
privaten Tests zu zählen. Die private Goldprüfung muss zusätzlich bestehen.
Der Netzwerkfehler ist ein deterministisch geworfener `OSError`, keine Verbindung.
Die Cases schreiben keine generelle Ablehnung aller Aufgaben mit Ausgangsfehlern
vor; sie verlangen deren getrennte Erfassung.

P19 legt die Kategorien `target_not_found` und `no_tests_collected` fest; sie
können im Ergebnisfeld `code` oder in `diagnostics.category` stehen. Es darf
weder fachliches Rot noch erfolgreiche Testausführung behauptet werden.

P21 schreibt keinen Namen für ein neues Feld im Monitorzustand vor. Die letzte
Fehlantwort muss jedoch samt `status=invalid_output` und Rohdaten während der
Folgeanfrage erreichbar bleiben. Der Fehlerzustand darf daher nicht ausschließlich
in einem kurzlebigen Ereignis zwischen zwei Statusabfragen existieren.

P07 und P10 prüfen die an das Modell übermittelte Erklärung bzw. Reparaturanweisung.
Sie belegen keine verbesserte Modellleistung. Eine solche Wirkung braucht einen
gesonderten Entwicklungsversuch mit Modellinferenz. P09 ersetzt auch keine Prüfung
des ursprünglichen Snapshotpools oder einen vollständigen Imagevergleich.

## Verifikation

- Ausgangsstand vor den Laufzeitänderungen: **23 rot, 9 grün**.
- Nach der Implementierung: **32 bestanden**.
- Zusätzlich prüft `test_pilot_runtime_ebt.py` acht Integrationsfälle für paginierte
  Fehlerdetails, Kontextverkleinerung, originale Test-IDs und Baselineweitergabe.
- Gemeinsame lokale Suite der Design- und Experimenttests: **185 bestanden**,
  drei Docker-Fälle ohne explizite Aktivierung übersprungen.
- Ruff und JavaScript-Syntaxprüfung erfolgreich.

Die Gegenfälle schützen die bereits funktionierenden Grenzen bei weiteren
Überarbeitungen. Docker-Integration wird zusätzlich mit wiedergegebenen
Modellantworten und echten Containern geprüft.

Die [Kontextansicht-Verträge](MONITOR_CONTEXT_CASES.md) ergänzen elf Cases für
die auf einen Tab reduzierte Oberfläche. P12/P13/P21 bleiben bestehen: Sie
prüfen Zustand und Archivdaten der Monitor-API, keine entfernten UI-Tabs.
