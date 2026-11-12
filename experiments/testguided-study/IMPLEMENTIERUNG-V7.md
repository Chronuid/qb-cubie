> Aktuelle Budgetregel: 30 Minuten gemeinsame Taskzeit, keine Grenzen für Modell-
> oder Werkzeugaufrufe, Rückfragen, Revisionen oder Reparaturversuche. Lokale
> Phasendeadlines, Reserve und automatische Stagnationsabbrüche sind aufgehoben.
> Erfolgreich verifizierte Tasks dürfen vorzeitig eingereicht werden.

# Implementierung von Agentendesign V7

Die explizite Variante `default_design(mode, guides, version=7)` implementiert
den Ablauf aus [AGENTENDESIGN-V7.md](AGENTENDESIGN-V7.md). Der bestehende
`TeamController` wählt anhand des Designs den V7-Controller. V6 bleibt mit seinen
historischen Schemas ladbar; die Standardauswahl bleibt V5. Alte Freezes werden
nicht verändert. Neue Freezes schließen V7-Policy, Rollen, Schemas, Vorlagenrevision
und die Implementierungsdateien in ihre Identität ein.

Die fachlichen Gates für Cases, Testrechte, versionsgebundene Änderungen,
Baseline-Gegenproben, Rot/Grün, Cubie-Evaluation und Abschluss verwenden weiterhin
den gemeinsamen Teamkern. Automatische Übergaben bestätigen keine fachliche
Reproduktion oder Verifikation.

| Bereich | Implementierung |
| --- | --- |
| Rollen, Schemas und eingefrorene Grenzen | [team_v7_design.py](testguided_study/team_v7_design.py) |
| Startkarte, atomare Orientierung, QA-Bestätigung, Aufträge und Recovery | [team_v7.py](testguided_study/team_v7.py) |
| Providerfristen, Ausgabereparatur und Artefaktsicherung | [team_agent.py](testguided_study/team_agent.py) |
| Versionsauswahl und Freeze | [design.py](testguided_study/design.py), [iteration.py](testguided_study/iteration.py), [artifacts.py](testguided_study/artifacts.py) |
| Meilensteine und getrennte Controllerkosten | `team.json`, `actions/*.json`, Monitor und [report.py](testguided_study/report.py) |

Orientierung endet nach sechs Modellaufrufen oder 120 Sekunden. Ihr letzter
Aufruf bietet nur Abschluss oder Blockademeldung an. Ohne gültiges Modellpaket
entsteht aus öffentlicher Evidenz ein vorläufiger QA-Auftrag mit leerer
Anforderungsliste. QA muss diese Anforderungen fachlich bestätigen. Ihre zehn
Aufrufe beziehungsweise 180 Sekunden laufen auch während Rückfragen weiter;
eine notwendige QA-Recovery erhält höchstens zwei weitere Aufrufe/45 Sekunden.
Informationsaufträge teilen vier Aufrufe und insgesamt 60 Sekunden aktiver
Bearbeitungszeit. Keine dieser Grenzen setzt das gemeinsame Budget zurück.

Suche und Pagination gelten lokal und im Container: `scope` muss öffentlich
vorhanden sein, die Inhaltssuche ist wörtlich, und Cursor gehören zu Werkzeug,
Parametern und Inventar-/Inhaltsstand. `read_file` verwendet einschließlich
`line_start` und `line_end` einbasierte Zeilen. Identische lesende Aktionen und
Testläufe am gleichen Stand verwenden archivierte Belege; auch dieser
Werkzeugversuch zählt. Recovery führt eine budgetierte Diagnose aus und ändert
das zulässige Schema. Reine Kommentar-/Formatänderungen an Python-Produktion
zählen nicht als Arbeitsfortschritt.

Die 41 ursprünglichen [V7-EBT-Abnahmen](../../tests/testguided_study_design/V7_CASES.md)
umfassen Controllerverträge und zwei echte Runner-Replays, jeweils mit
pytest-Unterprozessen, fachlichem Rot, Produktionspatch und Grün. Weitere
[Grenzprüfungen](../../tests/testguided_study_design/test_v7_boundaries.py)
decken unter anderem Provider-Timeouts, verspätete Antworten, Reparaturschemas,
unterbrochene QA-Fristen, Recovery, Reserve und Berichtsnenner ab.
[Runtime-Regressionen](../../tests/testguided_study_design/test_v6_runtime.py)
prüfen zusätzlich die unabhängige private Evaluation intern unvollständiger
V6- und V7-Läufe in beiden Armen.

```bash
.venv/bin/python -m pytest \
  tests/testguided_study_design/test_v7_controller_ebt.py \
  tests/testguided_study_design/test_v7_runtime_ebt.py \
  tests/testguided_study_design/test_v7_boundaries.py \
  tests/testguided_study_design/test_v6_runtime.py -q
```

Technischer Prüfstand vom 12. November 2026: Die vollständige Suite
`tests/testguided_study_design` besteht mit **439 Tests**, darunter alle
41 ursprünglichen V7-EBT-Abnahmen und 27 zusätzliche V7-Grenzprüfungen. Ruff
meldet für den Studiencode und die geänderten Tests keine Befunde. Die lokalen
asyncio-Evaluationsprüfungen wurden außerhalb der Sandbox ausgeführt, nachdem
ihre Thread-Signalisierung innerhalb der Sandbox hängen blieb.

[v7.toml](v7.toml) bleibt `phase="development"` und verwendet dieselben Modell-
und Gesamtbudgetwerte wie V6. Ein späterer Entwicklungsversuch kann ausdrücklich
über `./study --mode pilot --config experiments/testguided-study/v7.toml`
gestartet werden. Die bekannten Aufgaben bleiben verbrauchte Entwicklungsaufgaben.

Deterministische technische Replays ersetzen weder reale Modellversuche noch
die manuelle Prüfung von Testpassung und Orakeln. Mit dieser Implementierung
wird keine Modellkampagne gestartet und kein Lösungsgewinn behauptet.
