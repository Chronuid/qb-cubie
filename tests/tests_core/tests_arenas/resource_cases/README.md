# EBT-Cases zu Gutachten 8, Priorität 3.1

Diese Cases bilden die Kritik aus Abschnitt 6.2 und die Empfehlung
„Timeouts, begrenzte Ausgabe und Prozessbaum-Abbruch ergänzen“ in
`GUTACHTEN.md` ab. Sie entstanden zunächst als rote Akzeptanzfälle und prüfen
jetzt die Implementierung ohne `xfail`, einschließlich Kontrollfällen und
unabhängiger Watchdog-Selbsttests.

## Implementierter Vertrag

Beide Arenen akzeptieren dieselben optionalen Konstruktorparameter:

- `timeout`: maximale Dauer einer Target-Ausführung in Sekunden; umfasst
  Runner-Start, Target und Ergebnisübertragung, nicht das Klonen der Umgebung.
- `max_output_bytes`: gemeinsames Budget für stdout und stderr in Bytes.
  Genau das Budget ist erlaubt; Überschreitung bricht die Ausführung ab.
  Auch native Ausgabe über Dateideskriptoren zählt. Die Überwachung muss
  während der Ausführung erfolgen und ihren Speicherverbrauch begrenzen.

Ausgelassene Limits erhalten das bisherige Verhalten. Beide Limits sind
standardmäßig `None`; ihre Unterstützung erfordert POSIX-Prozessgruppen.
Timeouts propagieren als `TimeoutError` (oder Unterklasse), Ausgabeüberschreitungen
als `RuntimeError` (oder Unterklasse) mit einer kurzen Meldung, die „output“
und „limit“ enthält. Ein Abbruch liefert keinen erfolgreichen `RunTrace`;
auch `EBT(expect=False)` macht einen Timeout nicht zum fachlichen Erfolg.
EBT räumt Workspace und IPC-Dateien auf. Der Target-Prozess und seine normalen
Kinder und Enkel müssen beendet werden, auch bei ignoriertem `SIGTERM`.
Gezielt aus der Prozessgruppe ausgebrochene Prozesse sind nicht Gegenstand
dieser Cases; die Arenen werden dadurch keine Sicherheitsgrenze.

## Abdeckung

| Case | Beobachtbares Kriterium |
| --- | --- |
| Bestehendes Verhalten | Target tatsächlich ausgeführt, Rückgabe geprüft, aufgeräumt |
| Erfolgsfall mit Limits | Kleine Ausgaben beider Streams erlauben grünen EBT-Lauf |
| Hängendes Target | Rechtzeitiger Timeout, auch bei negiertem EBT |
| Ausgabeüberschreitung | stdout, stderr und gemeinsame Summe lösen Fehler aus, trotz korrekter Rückgabe |
| Laufende Überwachung | Ausgabeüberschreitung wird vor späterem Timeout erkannt |
| Bytegrenze | UTF-8-Ausgabe am Limit erlaubt, zwei Bytes darüber abgelehnt |
| Prozessbaum | Target, Kind und Enkel beendet; geerbte Pipes blockieren nicht |
| Eskalation | Auch Kind/Enkel mit ignoriertem SIGTERM werden beendet |
| Beendeter Runner | Timeout beendet auch Nachkommen, wenn der Runner bereits beendet ist |
| Direkte Arena-Nutzung | `arena.run()` räumt nach beiden Abbrucharten auf |
| Null-Byte-Budget | Stille Targets erlaubt, jede Ausgabe abgelehnt |
| Watchdog-Selbsttest | Limitloser Prozessbaum wird unabhängig abgebrochen und aufgeräumt |
| Beobachter-Selbsttest | Lebende Nachkommen werden vor der Notbereinigung erkannt |

Alle Arena-Cases laufen gegen TempFS und PyVenv. PyVenv bekommt eine kleine,
temporäre Basis aus `venv` und lokal kopiertem Cloudpickle samt Paketmetadaten;
kein Installer, kein Netzwerk und keine versionierte Arena-Basis sind nötig.

## Ausführung und Aussagegrenzen

```bash
.venv/bin/python -m pytest tests/tests_arena/test_ebt_resource_limits.py -q --tb=short
```

Der äußere pytest-Prozess kontrolliert die EBT-Ergebnisse unabhängig und startet
jeden Case in einem eigenen Watchdog-Prozess. Dieser beobachtet lebende PIDs
**vor** seiner eigenen Notbereinigung. PID und Kernel-Startzeit verhindern,
dass wiederverwendete PIDs fremde Prozesse treffen. Ein Selbsttest prüft, dass
der Watchdog einen wirklich gestarteten, hängenden Prozessbaum beendet.
Die Notbereinigung entfernt Prozesse; verbliebene Arena-Dateien liegen unter
pytest-Tempverzeichnissen und werden als Vertragsverletzung berichtet.

Diese Harness benötigt Linux `/proc`; auf anderen Plattformen werden die Cases
explizit übersprungen. Sie prüft beobachtbares Verhalten, nicht den maximalen
RSS-Verbrauch oder eine harte Echtzeitgarantie. `test_process_limits.py` prüft
zusätzlich den Python-Allokationsbedarf bei großer Ausgabe, ungültige Limits,
binäre Ausgabe und Targets, die beide Kanäle schließen und weiterlaufen.
Die Laufzeitgrenzen enthalten Spielraum für CI; der äußere Watchdog ist kein
Ersatz für den Timeout der Arena.
