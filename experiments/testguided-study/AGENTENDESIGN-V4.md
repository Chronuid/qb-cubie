# Agentendesign v4 aus Pilot 20261111-180702

v4 ist der Standard für neue Freezes beider Bedingungen. Gemeinsamer Kern:
`testguided-core-v4`, Spezialisierungen `pytest-guide-v4` und `cubie-guide-v4`.
Historische Freeze-Artefakte bleiben erhalten; v3 ist mit `default_design(...,
version=3)` ausdrücklich auswählbar. v4 nutzt Kontextvertrag Version 4 mit
weiterhin evidenzbasiertem Kontext. Beide Bedingungen haben identische Budgets,
Werkzeuge, Schutzmechanismen und Feedbackregeln; nur die Testanleitung variiert.

## Befunde und Änderungen

| Pilotbefund | Umsetzung | Grenze |
| --- | --- | --- |
| FastAPI/pytest verwechselt `"None"`, `None` und `Any` | Prompt und beide Guides verlangen Anforderung, konkrete Eingabe und erwartete Beobachtung vor einem Regressionstest; Fehlermeldung gegen dieses Beispiel prüfen | Fachliche Richtigkeit bleibt Modellaufgabe; Notizen sind keine verifizierten Fakten |
| Falsch kopierte Datei-Hashes verhindern Änderungen | v4-Aktionsschema enthält keinen Modell-Hash. Controller bindet `replace_text` an den Hash der letzten erfolgreichen Leseaktion; Workspace prüft weiterhin gegen die aktuelle Datei | Nach Änderung oder Editkonflikt erneut lesen; auch externe Änderungen führen weiter zum Konflikt |
| Ganze Funktionen werden ungenau rekonstruiert | Ersatzanker höchstens 1200, Ersatztext höchstens 1600 Zeichen; Dateischreiben höchstens 2400 Zeichen. Prompt verlangt lokale Änderungen | Größere Änderungen in mehreren gelesenen und geprüften Schritten |
| Rich/Cubie wiederholt grüne Bestandstests | Runner-Evidenz enthält nach Grün ohne beobachtete Produktionsänderung einen expliziten nächsten Schritt: Testabdeckung mit Issue vergleichen und fehlende Reproduktion ergänzen | Kein automatischer Beweis, dass ein neuer Test relevant ist; Wiederholungs- und Stillstandsschutz bleiben aktiv |
| Rich/pytest erzeugt zweimal eine abgeschnittene Dateiaktion | Nach ungültiger Ausgabe erlaubt der einmalige Reparaturaufruf ausschließlich `read_file`; nach erfolgreicher Aktion wieder vollständiges Schema | Modell kann weiterhin ungültig antworten; keine Erfolgsgarantie |

Die bereits vorhandene atomare Syntaxprüfung vor Python-Dateiänderungen bleibt
bestehen. Evaluationsklassifikation und Erfolgsdefinition werden nicht verändert.
Das Design enthält keine aufgabenspezifischen Lösungspatches oder privaten Tests.

## Nachvollziehbarkeit

Modellaktionen bleiben unverändert in `response` und `action` archiviert.
`executed_action` dokumentiert zusätzlich den vom Runner eingesetzten Datei-Hash.
Bei abgewiesenen Aktionen wird diese vorbereitete Aktion nicht ausgeführt.
Der Reparaturauftrag steht im archivierten Request; das eingeschränkte Schema
wird aus dem eingefrorenen Design und dem vorherigen Fehler deterministisch
abgeleitet. Beide Versionszweige behalten denselben Evaluator.

## Validierung

Neue Tests prüfen die Bindung und Invalidierung von Datei-Versionen, gezieltes
Feedback nach Grün sowie die Einschränkung und Wiederherstellung des Schemas
nach ungültiger Ausgabe. Workspace-Integrationstests führen für beide Bedingungen
mehrere echte Dateiänderungen mit erzwungenem Neulesen aus. Historische
Pilot-Replays mit Modell-Hashes prüfen ausdrücklich v3.

Prüfung:

```bash
.venv/bin/python -m pytest experiments/testguided-study/tests tests/testguided_study_design -q
.venv/bin/python -m ruff check experiments/testguided-study tests/testguided_study_design
```

Diese Tests prüfen Implementierungsverträge. Eine höhere Lösungsquote muss ein
neuer Modelllauf zeigen; im Rahmen dieser Änderung wurde keiner gestartet.
