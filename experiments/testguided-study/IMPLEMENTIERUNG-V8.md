# Implementierung von Agentendesign V8

V8 ist eine ausdrücklich auswählbare Entwicklungsvariante des
[Agentendesigns](AGENTENDESIGN-V8.md). Der eigene Controller implementiert den
seriellen Ablauf Analyse → QA → Dev → Analyse. Historische Designs und die
bisherige Standardauswahl bleiben erhalten. Ein Modellpilot wurde hierdurch
nicht gestartet; bessere Problemlösungsfähigkeit ist damit nicht nachgewiesen.

```bash
./study start --mode pilot --config experiments/testguided-study/v8.toml
```

Das [Profil](v8.toml) übernimmt Modell, `think=false`, Kontextfenster,
Ausgabebudget und 1800 Sekunden gemeinsame Taskzeit aus dem V7-Profil.
Rückfragen, Revisionen, Recovery, Provideranfragen und Tests teilen diese Zeit.
Es gibt keine Aufruflimits oder lokalen Phasendeadlines.

## Quellcode und Verträge

- [team_v8_design.py](testguided_study/team_v8_design.py) enthält kurze Rollenprompts,
  getrennte Aktionsschemas und die versionsgebundene Policy. Nur QA erhält den
  Guide der jeweiligen Frameworkbedingung. Beide Arme verwenden denselben Controller.
- [team_v8.py](testguided_study/team_v8.py) setzt Rollenrechte, Pfadgrenzen,
  Wissenskarte, Übergaben, Rückfragen, Recovery und Abschluss durch. Der bestehende
  `TeamController` wählt ihn für Designversion 8 aus.
- [team_agent.py](testguided_study/team_agent.py) verbindet Provider, Monitor und
  vorhandenen Workspace-/Testdienst mit V8. Designauswahl, Konfigurationsprüfung,
  Freeze und Implementierungsidentität berücksichtigen Version 8.
- [team_workspace.py](testguided_study/team_workspace.py) liefert öffentliche
  Bestandslisten, Environmentdaten und getrennte Baselinekopien. Der lokale
  V8-Store archiviert sämtliche öffentlichen Änderungen; zur privaten Evaluation
  wird ausschließlich der Produktionspatch übergeben.

`finish(delivery=...)` speichert eine vollständige Lieferung und aktiviert direkt
den nächsten Auftrag. Analyse liefert zunächst Anforderungen, Fakten mit aktuellen
Referenzen, Quellen, Testeinstiege, Baselinewissen, Hypothesen und offene Fragen.
`update_context` kann anschließend einzelne Abschnitte ersetzen. Neue unklare
Pfade können mit `path_assignments` und öffentlichen Belegen klassifiziert werden;
bestehende Produktions-/Testgrenzen dürfen dabei nicht umetikettiert werden.

QA liefert gewöhnliche Python-Tests und Fallmetadaten mit konkreter Eingabe,
Erwartung, Anforderungsbezug und Begründung. Ein eigener Case-Compiler ist nicht
vorgeschaltet. Nach aktueller Collection aktiviert ihre Lieferung Dev. Neue
Dateien entstehen durch Lesen eines leeren Bereichs mit Zeile 1–1 und anschließendes
`edit_tests` beziehungsweise `edit_source` auf dem erzeugten Handle.

Dev muss die fokussierten Tests vor der Produktionsänderung ausführen.
Teständerungen gehen mit Fall, Beobachtung, vermutetem Testfehler und Beleg an QA.
QA kann eine unbegründete Änderung ablehnen oder den Widerspruch an Analyse geben.
Informationsfragen sichern Rolle, Auftrag und Deadline; eine Antwort setzt den
unterbrochenen Auftrag fort. Gültige belegte Antworten werden wiederverwendet,
veränderte Quellen oder ungelöste Fragen erlauben erneute Recherche. Ungelöste
Informationsfragen lassen sich durch eine neue Wissenskarte nicht ausblenden.

## Werkzeuge, Kontext und Abschluss

Pfadprüfung und Rollenrechte greifen vor dem I/O-Port. Private, absolute,
traversierende und Symlinkpfade bleiben unzugänglich. QA/Dev lesen zugewiesene
Quellen sowie den Testbereich; zusätzliche Informationen beschaffen sie über
Analyse. Edits binden sich an gelesene Dateiversionen und Bereiche. Konflikte
liefern den aktuellen Ausschnitt; ein durch die Ausgabegrenze gekürzter Read
berechtigt nicht zur Änderung ungelesener Folgezeilen.

Pfadsuche bleibt Glob-Suche, Inhaltssuche bleibt wörtliche Textsuche. Fehlende
Scopes werden von gültigen leeren Ergebnissen unterschieden. Cursor sind an
Werkzeug, Parameter und öffentlichen Workspacezustand gebunden. Identische
Aktionen am gleichen Stand werden wiederverwendet und einzeln archiviert;
History und Modellkontext enthalten höchstens vier unterschiedliche Dialoge.
Die zweite Wiederholung fordert eine konkrete Entscheidung, weitere identische
Aktionen ändern den Rollenauftrag. Die Werkzeuge bleiben verfügbar. Ausdrücklich
frische Testläufe mit Begründung erzeugen neue unabhängige Belege.

Der Modellkontext verwendet eine Positivliste: Originalaufgabe, Rollenauftrag,
fachliche Wissenskarte, referenzierte Quellen und jüngste Rollendialoge.
Veraltete Quellen werden gekennzeichnet. Bei Platzmangel fallen ältere Dialoge
zuerst weg; der letzte Dialog und die Pflichtmaterialien werden nicht still
entfernt. Die gesamte serialisierte Anfrage einschließlich aktivem Schema wird
gegen das Eingabebudget geprüft; der Runner reserviert Ausgabeplatz. Ein unmögliches
Eingabebudget ergibt einen expliziten Kontextfehler vor der Inferenz.

Nur Analyse kann einen verifizierten Abschluss liefern. Dafür müssen aktueller
Diff und relevante Belege gelesen, alle Anforderungen durch Fälle abgedeckt und
blockierende Fragen geklärt sein. Fokussiertes Grün und die vereinbarten
Regressionen müssen zur finalen Produktion, Suite, Fallbeschreibung und Umgebung
passen. Eine behauptete Reproduktion benötigt fachliches Rot mit derselben finalen
Suite gegen Originalproduktion. Neue Test-, Fixture-, Konfigurations- oder
Fallmetadaten machen ältere Gegenproben ungültig. Import-/Setupfehler und Collection
qualifizieren keine Reproduktion.

Für Aufgaben mit bereits grüner Ausgangssuite erlaubt das Review ein ausdrücklich
begründetes `existing_coverage_reason`, zusammen mit gelesenen grünen Ausgangs-
und Abschlussbelegen und tatsächlichem Produktionspatch. Dabei bleibt
`reproduced=False`; es wird kein Rot erfunden. Vorbestehende Regressionsfehler
benötigen einen vergleichbaren Baselinelauf mit denselben Fehleridentitäten und
werden als `verified_with_baseline_failures` ausgewiesen. Cubie benötigt pro
fokussiertem Fall echte EBT-Ausführung, Evaluation und ausdrücklich ausgeführte
Prüfung von `result.evaluation is True`.

Nach Deadline werden Patch, vorhandene Testergebnisse und offene Fragen als
unvollständiger Lauf gesichert. Das Archiv enthält `team.json`, `context.json`,
`actions/*.json`, referenzierte Belege, Provideranfragen/-antworten und Patches.
Meilensteine, Rollenzeit, Kontextumfang und Wiederholungen stehen für den Monitor
und Bericht bereit. Interner Abschluss und private Evaluation bleiben getrennt;
auch unvollständige Läufe gelangen zur privaten Prüfung.

## Deterministische Verifikation

```bash
.venv/bin/python -m pytest tests/testguided_study_design/test_v8_* -q
.venv/bin/python -m pytest tests/testguided_study_design -q
```

Verifiziert am 12. November 2026: **555 Studien-Tests bestanden**, darunter
**107 V8-Abnahmen und Erweiterungen**. Die zusätzlichen Lifecycle-/Monitor-Tests
unter `experiments/testguided-study/tests` ergeben **64 bestanden, 3 übersprungen**.
Ruff und `git diff --check` sind ohne Befund.

Die ursprüngliche [EBT-Abnahmereihe](../../tests/testguided_study_design/V8_CASES.md)
umfasst 92 Nodes. Zusätzliche Grenzfälle prüfen unter anderem inkrementelle
Kontextpflege, nicht löschbare Informationslücken, Fallmetadatenrevisionen,
Teständerungsablehnung und begründete Aufgaben ohne reproduzierbares Rot.

Die Providerreplays in
[test_v8_runtime.py](../../tests/testguided_study_design/test_v8_runtime.py)
führen die tatsächlichen Workspace-Skripte, git-Baselines, pytest-Unterprozesse,
EBT-Instrumentierung, Design-Freeze und Monitoransicht aus. Die Testklammer passt
nur Containerpfad und Python-Interpreter an. Sie belegt außerdem, dass ausgeführte
EBT-Verträge ohne explizite Evaluationsprüfung keinen erfolgreichen Abschluss
erhalten. Der gemeinsame Studienreplay prüft für V6, V7 und V8 die unabhängige
private Evaluation nach unvollständiger Entwicklung einschließlich Patch und
mehrerer ungültiger Providerantworten.

Diese Replays prüfen den Ablauf und die Erhebung von Ausführungsbelegen. Die
fachliche Wahrheit beliebiger Orakel, Nutzen der drei Rollen, Qualität der
Wissenskarte und Vergleichbarkeit auf neuen Studienaufgaben benötigen weiterhin
Inhaltsprüfung und eingefrorene Modellversuche. Der Controller behandelt Portdaten
als vertrauenswürdige Runnerbelege; Modellbehauptungen ersetzen sie nicht.
