# Agentendesign v5: verbindliche Analysephasen und Thinking

Neue Freezes verwenden `testguided-core-v5`, Spezialisierungen `pytest-guide-v5`
und `cubie-guide-v5`. Beide Bedingungen erhalten identische Werkzeuge, Analysephasen,
Budgets und Feedbackregeln. Die Frameworkanleitung bleibt die Behandlung.

## Drei verbindliche Entscheidungspunkte

Die neue Aktion `analyze` enthält die Phase, eine Anforderung, ein konkretes Beispiel,
eine beobachtete Evidenz/Zusammenfassung, die Entscheidungskategorie und den nächsten
Schritt. Textfelder sind auf jeweils 600 Zeichen begrenzt. Das sind kurze
Entscheidungsprotokolle, keine Aufforderung zu ausführlichen Gedankengängen.

1. **Reproduktion:** Erst nach einem erfolgreichen Lesen verfügbar; vor der ersten
   Dateiänderung erforderlich. Die Anforderung muss mit einer konkreten Eingabe,
   erwarteter Beobachtung und öffentlicher Code-/Testevidenz verbunden werden.
   Lesen, Navigation und Baseline-Tests bleiben währenddessen möglich.
2. **Diagnose:** Nach einem ausgeführten Test mit Assertion-, sonstigem Test- oder
   Setup/Collection-Fehler sind Dateiänderungen bis zur Diagnose gesperrt. Die
   Kategorien sind `issue`, `test`, `setup`, `unclear` und `verified`. Der Agent soll
   die Fehlerstelle gegen die Anforderung prüfen, bevor er eine Reparatur wählt.
   Reine Collection-Proben gelten nicht als ausgeführte Tests. Ein Fehler vor der
   ersten Reproduktionsanalyse lässt zunächst die Reproduktionsphase offen.
3. **Abschluss:** `submit` wird erst nach einer Reviewanalyse angeboten. Änderungen
   und ausgeführte Tests/Baseline-Prüfungen machen ein vorheriges Review ungültig.
   Fehlende Verifikation muss ausdrücklich benannt werden; der Runner erfindet
   weder Grün noch Reproduktionsevidenz und verlangt kein künstliches Rot.

Der Controller filtert das Schema pro Turn. Phasen werden damit durch beobachtete
Aktionen ausgelöst, nicht durch das frei wählbare `stage`-Label. Modellbewertungen
liegen separat unter `ledger.analysis.records`; Runner-Evidenz bleibt unter
`ledger.evidence`. Die Analyseaktion mit Ergebnis wird wie andere Aktionen in
`steps/` archiviert. Die drei letzten Phasenbewertungen bleiben auch beim
Kontextfallback erhalten. Die Analyseschritte zählen als Modell- und Werkzeugaufrufe.

Eine formal vollständige Diagnose beweist keine fachliche Richtigkeit. v5 erzwingt
Entscheidungspunkte und deren Dokumentation; es prüft nicht automatisch den Sollwert
und verhindert auch nicht jede falsche Folgerung oder Suchschleife.

## Thinking und Budgets

`think=true` ist in `study.toml` und den Profilen `pilot`, `three-hours` und
`six-hours` aktiviert. Der vorhandene Ollama-Adapter übermittelt diese Einstellung.
Die finale JSON-Aktion wird aus `message.content` validiert. Providerantworten
inklusive eines vorhandenen `message.thinking` bleiben im archivierten `raw`;
Thinking wird nicht als Runner-Evidenz in den nächsten Kontext übernommen.

Zeit-, Kontext- und Ausgabebudgets bleiben unverändert, insbesondere
`num_predict=8192`. Neue Modellläufe müssen zeigen, ob mehr Analyse bei diesen
Budgets die Lösungsquote verbessert oder Zeit und Ausgabe für die Aktionen fehlen.
Die Tests verwenden deterministische Clients und starten keinen Modelllauf.

## Historische Designs und Experimente

`default_design(..., version=3)` und `version=4` bleiben auswählbar. Ihre bisherigen
Schemas und Laufpfade bleiben erhalten. Thinking ist eine unabhängige Konfiguration:
Ein historisches Design mit aktueller Konfiguration bedeutet nicht automatisch
`think=false`. Alte Freeze-Artefakte werden nicht umgeschrieben.

Für die Trennung der Effekte sind v4/v5 jeweils mit `think=false/true` vergleichbar.
Die Varianten können wie bisher als explizite Design-JSON-Dateien eingefroren werden;
eine automatische Vier-Varianten-Kampagne ist nicht Teil dieser Änderung.

## Validierung

Die neuen Integrationstests führen beide Bedingungen durch Lesen, Reproduktionsanalyse,
Regressionstest, Rot, Diagnose, Produktionsänderung, Grün, Review und Einreichung.
Sie prüfen die Thinking-Weitergabe, Archivierung, eingeschränkten Schemas und die
Invalidierung eines Reviews nach Änderungen. Bestehende historische Replays nennen
ihre Designversion explizit; der Studienstart-Replay durchläuft die neuen Phasen.

```bash
.venv/bin/python -m pytest experiments/testguided-study/tests experiments/tests/testguided_study_design -q
.venv/bin/python -m ruff check experiments/testguided-study experiments/tests/testguided_study_design
```
