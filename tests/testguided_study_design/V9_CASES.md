# EBT-Abnahmereihe zum Agentendesign v9

**Grundlage:** [AGENTENDESIGN-V9.md](../../experiments/testguided-study/AGENTENDESIGN-V9.md),
Stand 12. November 2026, insbesondere die technischen Abnahmen V9-A01–A14.

**Status:** 41 Casegruppen, 134 pytest-Nodes. Acht Kalibrierungen bestehen;
126 Controllerfälle sind am fehlenden v9-Einstieg rot. Die Reihe konkretisiert
Abnahmen vor der Implementierung; sie ist keine Qualifikation eines fertigen v9.
Es gibt keine Xfails oder Skips, die einen implementierten Controller vortäuschen.

Die Cases verwenden echte temporäre Dateien und `EBT(...).run()` mit expliziter
Prüfung von `result.evaluation is True`. Der Beobachtungsadapter delegiert an den
Produktionscontroller. Er implementiert weder Rollenrechte noch Gedächtnis,
Kontextauswahl, Übergänge, Versionsprüfung oder Abschlussregeln. In C31 laufen
die Zieltests zusätzlich als echte pytest-Unterprozesse. C40 und C41 funktionieren
bereits ohne v9 und kalibrieren Orakel beziehungsweise Runner-Port.

Die Beispielanforderung lautet unverändert: `double(1)` ergibt `2`, `double(2)`
ergibt `4`. Ausgangsproduktion ist `value * 2 - 1`, Reparatur `value * 2`.
Der Fokus prüft Eingabe 2, die Bestandsregression Eingabe 1. C40 prüft beide
Eingabe-/Erwartungspaare einzeln; eine vertauschte Zuordnung muss zweimal rot sein.

## Zuordnung zu den technischen Abnahmen

| Designabnahme | Casegruppen | Konkreter Prüfpunkt |
| --- | --- | --- |
| V9-A01 | C01, C10 | Read/Suche und Rollenbefund erreichen QA ohne Kontextregistrierung. |
| V9-A02 | C02, C12–C13, C39 | Antwort und Quellen bleiben über Rückfragen erhalten; Auftrag/Deadline bleiben gleich; ungelöste Fragen bleiben offen. |
| V9-A03 | C03–C04 | Überlappung, Cache und Historyabbau erhalten Originalbelege und Materialindex. |
| V9-A04 | C05, C28–C29 | Historische Quelle bleibt abrufbar; geänderte Artefakte entwerten alte Qualifikation. |
| V9-A05 | C14–C15 | Alle Rollen lesen unzugewiesenen öffentlichen Code; private und äußere Quellen bleiben gesperrt. |
| V9-A06 | C16, C23, C25 | Direkte Dispatcheraufrufe setzen Schreibrechte, Versionshandle und Dateierzeugung durch. |
| V9-A07 | C17–C18 | Alte Cursorvarianten ändern das Suchergebnis nicht; andere Schemafehler bleiben Fehler. |
| V9-A08 | C19–C22 | Wurzelscope, fehlende Pfade, öffentliche Vorschläge, 50er-Grenze, exakte Literale. |
| V9-A09 | C06–C07, C11, C26 | Vier Markdownabschnitte in allen Auftragsarten; umfangreiche Baseline bleibt knapp, Fehlerdetails abrufbar; QA-Guide nur für QA. |
| V9-A10 | C08–C09 | Speicherfehler bestätigt keinen Teilerfolg; wiederholtes Finish erzeugt keine doppelte Lieferung. |
| V9-A11 | C26–C31, C37–C38, C41 | Echtes Rot/Grün, finale Suite gegen beide Produktionsstände, keine Reproduktion durch Setup oder Collection. |
| V9-A12 | C12, C32–C34, C39 | QA weist falsche Abschwächung begründet zurück; Fehleridentitäten und offene Fragen verhindern falsche Freigabe. |
| V9-A13 | C06, C30–C31, C35, C40–C41 | Gleicher Replayanschluss für beide Arme; Cubie-Evaluation muss ausgeführt und geprüft sein. |
| V9-A14 | C02, C35–C36 | Gemeinsame 1800 Sekunden; Deadline in Recherche, Rückfrage oder laufender Prüfung sichert einen unvollständigen Stand. |

## Anforderungs- und Casematrix

Die Abschnitte beziehen sich auf das v9-Design. `test_v9_01_…` bezeichnet C01;
parametrisierte Varianten sind in den pytest-Node-IDs sichtbar.

### Automatisches Gedächtnis und Kontext

Datei: [test_v9_memory_ebt.py](test_v9_memory_ebt.py), **24 Nodes**.

| Case | Abschnitt | Setup / Auslöser | Erwartete Beobachtung | Nodes |
| --- | --- | --- | --- | ---: |
| C01 | 3, 6 | Analyse liest Funktion, beendet mit Hypothese ohne weitere Kontextaktion. | QA erhält exakten Text, Pfad, Zeilen, Belegreferenz und Befund mit Rollenherkunft. | 1 |
| C02 | 3, 6–7 | QA bzw. Dev fragt; Analyse liest Literal und antwortet nach 123 Sekunden; zweite Frage folgt. | Derselbe ursprüngliche Auftrag wird fortgesetzt; Deadline bleibt 1800; Antwort und exakter Ausschnitt sind auch im nächsten Analyseauftrag vorhanden. | 2 |
| C03 | 3 | Reads 1–2 und 2–3; zweiter Read wird wiederholt. | Gemeinsame Zeile einmal in aktueller Ansicht, gleicher Cachebeleg, beide Originalausschnitte separat abrufbar. | 1 |
| C04 | 3–4 | Zwölf unterschiedliche Reads mit je etwa 3000 Zeichen, 18.000 Eingabebytes. | Höchstens vier Historydialoge, Originalaufgabe und Index aller Dateien erhalten, ausgelassener Volltext abrufbar; tatsächliche Nachrichten plus Schema bleiben im Bytebudget. | 1 |
| C05 | 3, 7 | Dev ändert zuvor gelesene Funktion und liest erneut. | Alter Beleg historisch, neuer Beleg aktuell; aktueller Prompt enthält neue Quelle; ohne neue Prüfungen kein Abschluss. | 1 |
| C06 | 2, 4 | Fünf Auftragsarten in beiden Armen; initiale Baseline mit 500 Diagnosezeilen. | Genau vier Hauptabschnitte; Originalaufgabe; passender Guide ausschließlich bei QA; keine Hashes/Rohledger in Prompt und History; kurze Baseline, vollständige Diagnose per Beleg. | 10 |
| C07 | 3 | Pflichtpaket hat nur 16 Bytes Budget. | Konkreter Kontextfehler mit zu großem Bestandteil, kein gezählter Modellaufruf. | 1 |
| C08 | 3 | Speicherport wirft bei neuem Read bzw. Finish; danach erneuter Versuch. | Expliziter Speicherfehler; Auftrag und Lieferungen unverändert; keine gespeicherte Teiltransaktion; Wiederholung erfolgreich. | 2 |
| C09 | 3, 6 | Identische Analyselieferung nochmals direkt dispatchen. | Genau eine gespeicherte Lieferung, identischer QA-Folgeauftrag; Wiederholung darf bestätigt oder abgewiesen werden. | 1 |
| C10 | 3 | Treffer- und Leersuche ohne Read, dann Finish. | Suchbelege einschließlich negativem Ergebnis abrufbar; Fundstelle wird übergeben, ungelesener Funktionskörper nicht erfunden. | 1 |
| C11 | 2, 4 | Gelesene Datei enthält eine Aufforderung zur Rollenüberschreitung. | Text als Quelldatum im Userkontext; nicht im Systemauftrag; QA behält genau ihre Werkzeuge. | 1 |
| C12 | 3, 6 | Analyse lässt Orakelfrage ausdrücklich ungelöst, beantwortet danach andere Frage. | Erste Frage bleibt in beiden Folgekontexten und im offenen Fragenbestand. | 1 |
| C13 | 3, 6 | Identische beantwortete Frage; anschließend Änderung ihrer gelesenen Quelle. | Unveränderte Antwort wird wiederverwendet; nach Quellenänderung neuer Analyseauftrag. | 1 |

### Navigation und Schreibgrenzen

Datei: [test_v9_tools_ebt.py](test_v9_tools_ebt.py), **64 Nodes**.

| Case | Abschnitt | Setup / Auslöser | Erwartete Beobachtung | Nodes |
| --- | --- | --- | --- | ---: |
| C14 | 2, 5 | Jede Rolle sucht und liest eine öffentliche Datei außerhalb bisheriger Quellen und Schreibklassifikationen. | Glob, Inhaltssuche und Read liefern die echte Datei. | 3 |
| C15 | 2, 5 | Drei Rollen × drei Navigationswerkzeuge × private, äußere und Symlinkgrenze. | Ablehnung bzw. leere öffentliche Globmenge; kein privater/äußerer Inhalt; Workspace unverändert. | 27 |
| C16 | 2 | Analyse schreibt; QA schreibt Produktion; Dev schreibt Tests, Fixtures oder Konfiguration, jeweils mit echtem Readhandle. | Serverseitige Ablehnung vor Edit-I/O; alle Bytes unverändert. | 9 |
| C17 | 5 | Zwei Suchwerkzeuge, jeweils ohne Cursor und mit `"0"`, `0`, `""`, ungültigem Token oder privatem Cursorpfad. | Identische Treffer unter explizitem Scope/Glob; weder Schema noch Ausgabe oder Modellhistory enthalten Cursorfelder. | 10 |
| C18 | 5 | Legacycursor plus zusätzliches `offset`, `start` oder unbekanntes Feld. | Schemafehler wird nicht durch Kompatibilitätsadapter toleriert. | 3 |
| C19 | 5 | Scope `""` bzw. `"."`; öffentliche und private identische Literale. | Nur öffentliche Treffer, exakt nach Pfad/Zeile sortiert. | 2 |
| C20 | 5 | Fehlender Scope bzw. existierender Scope ohne Treffer. | `scope_not_found` mit geprüfter Eingabe und höchstens fünf öffentlichen Kandidaten gegenüber `completed` mit leerer Liste; kein Ersatzscope. | 2 |
| C21 | 5 | Exakt 50 bzw. 51 Inhaltstreffer; 51 Globtreffer in umgekehrter Erstellungsreihenfolge. | Maximal 50 deterministische Treffer; nur bei Kürzung sichtbarer Hinweis; keine Pagination. | 3 |
| C22 | 3, 5 | Literalsuche nach `\d+[x]`; Read von Zeile 2 bis hinter EOF. | Nur echter Literaltreffer; Backslash und Anführungszeichen exakt; tatsächlicher inklusiver Bereich 2–3. | 1 |
| C23 | 2, 5 | Datei ändert sich nach Read, dann Edit mit altem Handle. | Versionskonflikt liefert aktuellen Text ohne Schreibaufruf; frischer Read erlaubt Reparatur. | 1 |
| C24 | 5 | Zweimal identische erfolglose Suche ohne Änderung. | Gleicher Cachebeleg und konkreter Entscheidungsauftrag; Suche bleibt verfügbar; Lauf aktiv und nicht freigegeben. | 1 |
| C25 | 2 | QA bzw. Dev liest neuen zulässigen Pfad und editiert mit leerem Handle. | Neue Datei entsteht über gewöhnlichen rollenabhängigen Editvertrag; kein weiteres Erzeugungswerkzeug. | 2 |

### Qualifikation, Review und Deadline

Datei: [test_v9_workflow_ebt.py](test_v9_workflow_ebt.py), **38 Nodes**.

| Case | Abschnitt | Setup / Auslöser | Erwartete Beobachtung | Nodes |
| --- | --- | --- | --- | ---: |
| C26 | 6–7 | Import-, Syntax-, Fixture- oder Environmentfehler ohne ausgeführten Case. | Kein fachliches Rot, keine Freigabe; aktuelle genaue Fehlerdiagnose im Prompt. | 4 |
| C27 | 6–7 | Nur Collection, anschließend direkt gefälschter Analyseabschluss. | Keine Rot-/Grünqualifikation, keine Freigabe. | 1 |
| C28 | 3, 6–7 | Nach Rot/Patch/Grün ändert QA Test, Fixture oder Konfiguration. | Alte Qualifikation ungültig; finale Tests bytegleich gegen Originalproduktion in getrennter Kopie und gegen Reparatur ausgeführt. | 3 |
| C29 | 3, 7 | Nach Grün ändert sich Produktion, Test oder Environment. | Review mit alten Belegen darf nicht abschließen. | 3 |
| C30 | 7 | Beide Arme mit Runnernachweis ohne EBT, nur Ausführung, nur Evaluation oder geprüfter Evaluation. | Cubie akzeptiert ausschließlich vollständigen Nachweis; pytest benötigt keinen EBT-Nachweis. | 8 |
| C31 | 6–8 | Echter pytest-Unterprozess: Rot, Produktionspatch, fokussiertes Grün, Bestandsregression, Analyse liest Diff und Details. | Interner Abschluss `submitted`, richtige Produktionsbytes und archivierte Pflicht zu separater privater Evaluation in beiden Armen. | 2 |
| C32 | 6 | Dev verlangt Erwartung 3, weil defekte Produktion 3 liefert. QA lehnt mit REQ-1 ab. | QA sieht Wunsch samt Beleg; Ablehnungsbefund erreicht Dev; Testbytes unverändert; kein automatischer Abschluss. | 1 |
| C33 | 7 | Ein Baselinefehler, danach identischer Fehler oder neuer Fehler bei gleicher Anzahl. | Nur passende Identität kann `verified_with_baseline_failures` erlauben; neuer Fehler blockiert. | 2 |
| C34 | 6–7 | Rot/Patch/Fokusgrün ohne vereinbarte Regression. | Verifikation abgewiesen; explizite Reviewnacharbeit aktiviert Dev mit konkretem Prüfauftrag. | 1 |
| C35 | 7 | Beide Arme: Deadline in Recherche, Rückfrage oder laufender Prüfung von Sekunde 1799 bis 1801. | `incomplete`, Deadline 1800, Patch/Belege/offene Fragen gesichert; auch spät eingetroffenes Grün archiviert; keine Freigabe. | 6 |
| C36 | 7 | 110 verschiedene Reads und Modellanfragen; Zeit 120/720/1799 Sekunden. | Keine alten Aufruf- oder Phasenlimits; gemeinsamer Lauf bleibt aktiv. | 3 |
| C37 | 7 | Bereits korrekte Originalproduktion, erster Lauf grün ohne begründete Ausnahme. | Kein erfundenes Rot und keine automatische Abschlussfreigabe. | 1 |
| C38 | 6 | QA liefert ein nicht gesammeltes Ziel oder Mischung mit gültigem Ziel. | Ablehnung ohne Rollen- oder Auftragswechsel. | 2 |
| C39 | 6–7 | Vollständige grüne Belege, anschließend ausdrücklich ungelöste Orakelfrage. | Frage bleibt offen; grüner Review kann nicht abschließen. | 1 |

### Unabhängig ausführbare Kalibrierung

Datei: [test_v9_calibration_ebt.py](test_v9_calibration_ebt.py), **8 Nodes**.

| Case | Abschnitt | Setup / Auslöser | Erwartete Beobachtung | Nodes |
| --- | --- | --- | --- | ---: |
| C40 | 6, 8 | Beide Arme × richtige Produktion, Off-by-one und vertauschte Ergebnisse. | Je zwei korrelierte Fälle; richtig zweimal grün, jede Mutation zweimal fachlich rot; keine Setupfehler/Skips. Cubie führt EBT aus und prüft Evaluation. | 6 |
| C41 | 8 | Runner-Port direkt mit echten temporären Dateien gegen defekte und reparierte Produktion in beiden Armen. | Reales pytest/JUnit liefert Rot/Grün, genau einen ausgeführten Fokusfall und nodebezogene Ergebnisse. | 2 |

## Vorgeschlagener Python-Anschluss

Das Design spezifiziert das Verhalten, aber keine Pythonklasse und kein exaktes
Snapshotformat. [v9_support.py](v9_support.py) schlägt deshalb bewusst einen
eigenen Anschluss vor:

```python
from testguided_study.team_v9 import V9TeamController

team = V9TeamController(
    workspace=workspace, artifact_dir=archive, mode="cubie",
    issue=original_issue, guides=guides, manifest=manifest,
    policy={"wall_seconds": 1800, "context_bytes": 80000,
            "history_dialogs": 4, "search_limit": 50},
    execute=io_port, persist=persistence_port, clock=clock,
    # optional: baseline=initial_trusted_runner_observation,
)
team.dispatch(role, {"action": "finish", "notes": "..."})
team.request()
team.snapshot()
team.advance()
```

Ein dünner Adapter darf gleichwertige Produktionsnamen und Ergebnisformate
abbilden. Er darf keine erwarteten Zustände liefern oder die geprüfte Policy
selbst implementieren. Die Detailnamen sind **Testanschlussvorschläge**, keine
zusätzlichen Anforderungen an die interne Architektur.

- `request()` liefert tatsächlich für die Inferenz bestimmte `messages`,
  das JSON-Aktionsschema `schema`, kompakte `history`, `job`, die Anzahl
  `omitted_materials` und bei vorhandener Baseline `baseline_ref`. Der erste
  Usertext ist der vierteilige Markdownkontext. Historydialoge sind auch in den
  tatsächlich gesendeten Nachrichten fachlich gekürzt. Das Bytebudget wird in
  C04 unabhängig über JSON-kodierte Nachrichten einschließlich Schema gemessen.
- Gemeinsame Navigation entspricht dem v9-Design. Readantworten liefern `text`,
  `line_start`, `line_end`, `evidence_id`, `current` und einen versionsgebundenen
  `handle`; `read_evidence(ref)` liefert den Originalbeleg einschließlich
  Historienkennzeichnung. Suchantworten liefern `paths` oder `hits`,
  `evidence_id`, `truncated` und gegebenenfalls einen verständlichen `hint`.
- `finish(notes)` orientiert oder beantwortet den gespeicherten
  Informationsauftrag ohne explizite Quellenliste. `unresolved=True` ist im
  vorgeschlagenen Anschluss die ausdrückliche Kennzeichnung einer offenen
  Informationsantwort. Die gelesenen Quellen werden automatisch gebunden.
- QA liefert `finish(test_targets, regressions, notes)`. Caseeingabe, Erwartung
  und Begründung stehen im normalen Test und in den Notizen. Der Helper
  verlangt weder `cases`-Datenbank noch Anforderungsregistrierung oder
  modellgenerierte Fall-IDs. Der Runner identifiziert Ergebnisse durch
  eingesammelte pytest-Nodes; interne Fall-IDs erzeugt der Controller.
- Dev nutzt `request_test_change(reason, case, evidence)` mit Testnode und echten
  Belegreferenzen. Devs `finish(notes)` ordnet Tests und Patch automatisch zu
  und liefert `diff_ref`. Analyse liest Diff und Belege und liefert
  `finish(verdict="verified", notes=...)` oder
  `finish(verdict="rework", next_role=..., notes=...)`.
- `snapshot()` enthält `role`, `status`, `active_job`, `budget.deadline`,
  `metrics.model_calls`, `qualifications`, `completion.allowed`, `deliveries`,
  `open_questions`, `test_observations` und gegebenenfalls
  `verification_status="verified_with_baseline_failures"`. Lieferungen enthalten
  eine Controller-ID, Auftragszuordnung und die ursprünglichen `notes`.
- `persist(transaction)` ist eine injizierbare Speichergrenze. Der Testport
  schreibt vollständige JSON-Transaktionen in echte temporäre Dateien oder wirft
  vor dem Schreiben `OSError`. Aufbau und Zusammenfassung der Transaktion sowie
  Commit des Controllerzustands gehören zur Produktion. Der Port erhält keine
  Entscheidungshoheit über Rollen, Evidenz oder Übergaben.
- Der optionale `baseline`-Konstruktorparameter ist eine vertrauenswürdige
  initiale Runnerbeobachtung, keine Modellaktion. Er ermöglicht umfangreiche
  Startdiagnosen schon vor der ersten Inferenz. Der Controller bindet sie an
  den Ausgangsstand und archiviert die vollständige Diagnose. C33 erhebt seine
  Vergleichsbaseline stattdessen über eine tatsächliche `run_tests`-Aktion am
  Runner-Port gegen Originalproduktion.
- `archive/team.json` und `archive/full.patch` konkretisieren die dauerhafte
  Laufzusammenfassung. `submitted` bezeichnet den intern verifizierten Lauf;
  `incomplete` den unvollständigen Endstand. Private Evaluation bleibt separat.

## Aussagekraft und Grenzen

Der Helper importiert aus den bestehenden v6-/v8-Tests ausschließlich EBT-Aufruf,
Uhr, Datenkonstanten und permissive Datei-/Runner-Ports. Er erbt **keinen**
v8-Harness und keinen Controller. Die alten Verbote eigenständiger Suche,
`update_context` und Cursorpagination werden nicht übernommen. Historische
Designs, Produktionscode und bestehende Abnahmen bleiben unverändert.

Die meisten Controllerfälle verwenden vorgegebene Runnerantworten. C31 und C41
erheben Ergebnisart und Fehler aus realem pytest/JUnit. Auch dort sind die
Frameworknutzungszähler des Ports vorgegebene Grenzportdaten, keine echte
Laufzeitinstrumentierung. C40 belegt separat reale EBT-Ausführung einschließlich
expliziter Evaluationsprüfung. C32 prüft den Transport einer begründeten
QA-Ablehnung, nicht die Fähigkeit eines Modells, sie selbst zu finden. C11 prüft
Datendarstellung und Werkzeugrechte, keine empirische Prompt-Injection-Resistenz.

Noch gesondert zu qualifizieren sind insbesondere:

- Tatsächliches Tokenbudget einschließlich reservierter Ausgabe und
  Provider-Tokenizer; das Bytebudget ersetzt diese Laufzeitprüfung nicht.
- Speicherfehler nach begonnenem Edit, Prozessabbruch mitten im Commit,
  Wiederanlauf aus Archiv und Replay einer Lieferung nach Neustart.
- Korrektur widersprüchlicher Rollenbefunde, explizite Fragenauflösung und
  Wiedereröffnung durch semantisch widersprüchliche Antworten; kein fachliches
  Wahrheitsurteil allein durch `finish` oder Textähnlichkeit.
- Zusätzliche Backend-/Ausgabelimits der Suche; öffentliche Pfadkandidaten bei
  vielen ähnlichen privaten Namen; absolute Pfade und weitere Aliasformen.
- Mehrere relevante Cases mit nur teilweise vorhandener EBT-Instrumentierung,
  begründeter Abschluss bei grüner Ausgangssuite sowie flaky Wiederholungen.
- Vollständiger Providerreplay mit eingefrorenen echten Prompts, v9-Auswahl im
  Studienrunner, Freeze/Monitor/Bericht und private Evaluation nach Abbruch.
- Empirische Hypothesen V9-H1–H4, Orakelqualität auf weiteren Aufgabengruppen,
  Reparaturqualität und unabhängiger Frameworkvergleich.

Die Matrix liefert somit konkrete Beispiele zu allen 14 Abnahmen, keinen
Vollständigkeitsbeweis für sämtliche Eingaben oder Studienhypothesen.

## Ausführung und beobachteter Ausgangsstand

```bash
.venv/bin/python -m pytest -q tests/testguided_study_design/test_v9_*_ebt.py
.venv/bin/python -m pytest -q tests/testguided_study_design/test_v9_calibration_ebt.py
.venv/bin/ruff check tests/testguided_study_design/v9_support.py tests/testguided_study_design/test_v9_*.py
```

Am 12. November 2026:

- Gesamtreihe: **134 gesammelt, 8 bestanden, 126 rot am fehlenden
  `testguided_study.team_v9.V9TeamController`**.
- Kalibrierung C40/C41: **8 bestanden**, inklusive echter pytest-Unterprozesse.
- Vorhandene v7-/v8-Controller-, Laufzeit-, Werkzeug-, Abschluss- und
  Vorlagenabnahmen: **133 bestanden**.
- Ruff für die neuen Pythondateien und Whitespaceprüfung ohne Befund.
