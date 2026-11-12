# EBT-Abnahmecases für Agentendesign v8

Grundlage: [AGENTENDESIGN-V8.md](../../experiments/testguided-study/AGENTENDESIGN-V8.md),
Stand 12. November 2026, insbesondere die zehn Replay-Abnahmen in Abschnitt 7.
Die Reihe umfasst **39 Casegruppen mit 92 parametrisierten pytest-Nodes**.
Jeder Node führt seinen Beobachtungsadapter über `EBT(...).run()` aus und
verlangt `result.evaluation is True`. Adapter rufen den Produktionscontroller
auf; sie implementieren dessen Entscheidungen nicht selbst.

**Implementierungsstand:** Der V8-Controller ist implementiert; alle 92 ursprünglichen
Nodes bestehen. Zusätzliche Grenzfälle und echte Provider-/Workspace-/Probe-Replays
stehen in `test_v8_boundaries.py` und `test_v8_runtime.py`. Anschluss, Integration
und Grenzen beschreibt [IMPLEMENTIERUNG-V8.md](../../experiments/testguided-study/IMPLEMENTIERUNG-V8.md).
Die folgenden Angaben zum Ausgangsstand dokumentieren die Entwicklung vor der Implementierung.

**Ausgangsstand: 6 grün, 86 rot, keine Collectionfehler.** Die sechs grünen
Vorlagenprüfungen führen echte lokale pytest-Unterprozesse aus, darunter echte
EBT-Verträge. Alle 86 roten Nodes melden denselben fehlenden Einstieg
`testguided_study.team_v8.V8TeamController`. Das sind offene Abnahmeverträge,
keine 86 unabhängig nachgewiesenen Defekte. Ihre weiteren Schritte müssen nach
Implementierung erneut geprüft werden. Es gibt keine `skip`-/`xfail`-Markierungen
und keinen Ersatz des v8-Controllers durch v6, v7 oder einen Testcontroller.

## Ausführen

```bash
# Gesamte Reihe einschließlich der noch roten v8-Abnahmen.
.venv/bin/python -m pytest tests/testguided_study_design/test_v8_*_ebt.py -q --tb=short

# Schon ausführbare QA-Vorlagenkalibrierung.
.venv/bin/python -m pytest tests/testguided_study_design/test_v8_case_forms_ebt.py -q

# Vollständige Collection unabhängig vom Implementierungsstand.
.venv/bin/python -m pytest tests/testguided_study_design/test_v8_*_ebt.py --collect-only -q
```

Alle Workspaces, Testberichte, Baselinekopien und Archive liegen unter `tmp_path`.
Es werden weder Ollama noch Docker, Netzwerkzugriffe oder private Studienaufgaben
benötigt. Unterprozesse verwenden den laufenden Python-Interpreter und das lokale
Cubie, deaktivieren externe pytest-Plugins und besitzen 30 Sekunden Timeout.
Der Timeout schützt die lokale Testausführung; er ist keine v8-Phasendeadline.

## Zuordnung zu den zehn Designabnahmen

Die IDs V8-C01 bis V8-C39 sind lokale IDs dieses Katalogs, keine zusätzlichen
Anforderungsnummern des Designs. Im Funktionsnamen entspricht `test_v8_01_…`
der Casegruppe V8-C01. Varianten stehen in den pytest-Node-IDs.

| Abnahme aus Abschnitt 7 | Casegruppen |
| --- | --- |
| Erster Analyseauftrag ohne Frameworkkurs und Rohtelemetrie | C01, C12–C13 |
| Kontextlieferung aktiviert QA atomar, Unsicherheit bleibt sichtbar | C02–C03, C14 |
| Rückfragen sichern Auftrag und setzen ihn mit aktuellem Kontext fort | C07–C09 |
| Teständerungen laufen über QA und erneuern betroffene Belege | C10–C11, C28 |
| Wiederholungen führen zu kurzer Darstellung und konkreter neuer Entscheidung | C21–C24, C36 |
| Fehlende Pfade und veraltete Editversionen ergeben nutzbare Fehler | C15–C20 |
| Nach Testrevision reichen ältere Rot-/Grün-Belege nicht | C28–C30 |
| Kontrollierter vollständiger Reparaturfall in beiden Armen | C32, separat Vorlagenkalibrierung C37 |
| Rollenüberschreitungen und Abschluss ohne Nachweis werden abgewiesen | C04–C06, C25–C27, C29–C31, C38–C39 |
| Deadline während Rückfrage oder Testlauf sichert unvollständige Artefakte | C33–C35 |

## Anforderungs- und Casematrix

Die Spalte „Abschnitt“ verweist jeweils auf das v8-Design. Eingaben und
Sollbeobachtungen stammen aus der Anforderung; die kleinen Fixture-Dateien
konkretisieren die Beispiele. Die gemeinsame Beispielaufgabe lautet ausdrücklich:
`double(1)` ergibt `2`, `double(2)` ergibt `4`. Die Ausgangsproduktion liefert
`value * 2 - 1`; der Patch korrigiert sie zu `value * 2`.

### Rollen, Übergaben und Kontext

Datei: [test_v8_controller_ebt.py](test_v8_controller_ebt.py).

| Case | Abschnitt | Setup / Auslöser | Sollbeobachtung | Nodes |
| --- | --- | --- | --- | ---: |
| C01 | 2–3 | Erzeuge Aufträge für alle drei Rollen in beiden Armen | Nur Rollenwerkzeuge; Originalaufgabe und Startwissen vorhanden; nur QA bekommt ihren Frameworkguide; keine private Quelle oder ausgewählte Rohtelemetriefelder | 6 |
| C02 | 3–4, 7 | `finish` mit gültigem Kontext, fehlender Anforderung, erfundener oder veralteter Quellenreferenz | Gültig: eine Kontextrevision und QA-Auftrag einschließlich offener Frage; ungültig: weder Auftrag noch Kontextrevision geändert | 4 |
| C03 | 4 | QA liefert gesammelte Suite mit C-1 und Testziel über `finish` | Dev ist direkt aktiv; Fall, Erwartung `4` und Anforderung bleiben erhalten | 1 |
| C04 | 2 | Analyse schreibt; QA schreibt Produktion; Dev schreibt Test, Fixture oder Konfiguration; jeweils echter Lesehandle | Vor Schreib-I/O abgewiesen; alle Dateien unverändert | 9 |
| C05 | 2, 5 | QA liest äußeren, absoluten, traversierenden oder Symlinkpfad | Vor I/O abgewiesen; Dateien unverändert | 4 |
| C06 | 2, 6 | Jede Rolle liest eine private Sentinel-Datei | Vor I/O abgewiesen; kein privater Dateiinhalt im Ergebnis | 3 |
| C07 | 4, 6 | QA bzw. Dev fragt; Analyse antwortet nach 123 Sekunden mit Quellenbeleg | Dieselbe Rolle und Auftrags-ID; ursprüngliche gemeinsame Deadline; Antwort im Folgekontext | 2 |
| C08 | 3–4 | Identische beantwortete Frage, danach Änderung ihrer Quelle | Zuerst gültige Antwort wiederverwendet ohne Rollenwechsel; nach Änderung erneute Analyse | 1 |
| C09 | 4 | Analyse ruft `ask_analysis` auf | Ablehnung ohne neuen Auftrag | 1 |
| C10 | 4 | Dev sendet Fall, Ergebnis, vermuteten Testfehler und Rotbeleg | QA erhält Änderungsbedarf und Testwerkzeug; kein Produktionswerkzeug | 1 |
| C11 | 4 | Je ein Pflichtbestandteil des Teständerungswunsches fehlt | Abweisung; Dev-Auftrag bleibt aktiv | 4 |
| C12 | 3 | Acht verschiedene Lesedialoge bei begrenztem Kontext | Originalaufgabe, nötiger Code und offene Frage bleiben erhalten; höchstens vier Historydialoge | 1 |
| C13 | 3 | Nur 16 Bytes Eingabebudget | Expliziter Kontextfehler vor einem gezählten Modellaufruf | 1 |
| C14 | 4 | QA liefert Fall ohne Eingabe, Erwartung, Begründung oder Anforderungsreferenz | Keine Suiteübergabe oder Registrierung des unvollständigen Falls | 4 |

### Werkzeuge und Recovery

Datei: [test_v8_tools_ebt.py](test_v8_tools_ebt.py).

| Case | Abschnitt | Setup / Auslöser | Sollbeobachtung | Nodes |
| --- | --- | --- | --- | ---: |
| C15 | 5 | Suche ohne Treffer in fehlendem bzw. vorhandenem Scope | `scope_not_found` mit öffentlicher Korrekturgrundlage gegenüber gültiger leerer Treffermenge | 2 |
| C16 | 3, 5 | Suche wörtlich nach `\d+[x]` über JSON; lese Zeilen 2–3 | Exakt Zeile 2; Backslashes, Anführungszeichen und einschließlich begrenzte Zeilen erhalten | 1 |
| C17 | 5 | `find_paths("def double")`, dann Inhaltssuche | Keine heimliche Textsuche im Pfadwerkzeug; Hinweis auf Inhaltssuche; diese findet reale Quelle | 1 |
| C18 | 5 | Fünf Treffer, Seitengröße zwei; Cursor unverändert bzw. mit geänderter Quelle, Query oder Werkzeug | Exakt Zeilen 1–5 ohne Verlust/Duplikate; sonst Cursorfehler ohne Treffer | 4 |
| C19 | 5 | Numerischer/erfundener Cursor oder alter Offsetparameter | Explizite Abweisung ohne scheinbare Treffer | 3 |
| C20 | 5 | Produktion ändert sich nach Lesen, dann Edit mit altem Handle | Aktueller Ausschnitt im Konflikt, kein Schreibaufruf; erneutes Lesen erlaubt kleinen Patch | 1 |
| C21 | 5 | Zweimal dieselbe Lesung bei unveränderten Bytes | Ergebnis/Referenz wiederverwendet; ein Historydialog; Entscheidungsauftrag; Suche bleibt verfügbar; Lauf bleibt aktiv | 1 |
| C22 | 5 | Dieselbe ergebnislose Suche mit anderer freier Notiz | Zwei vollständige Archiveinträge, ein Historydialog, Entscheidung erforderlich, Suchwerkzeug erhalten | 1 |
| C23 | 5–6 | Orientierung wiederholt nach Recovery dieselbe Suche; Karte hat offene Frage | Vorhandenes Wissen geht mit Unsicherheit an QA; kein Taskabbruch und keine Erfolgsfreigabe | 1 |
| C24 | 3, 5 | Identische Lesung nach Änderung ihrer Datei | Neuer Inhalt und neue Belegreferenz statt altem Cachetreffer | 1 |

### Abschluss, Deadline und QA-Vorlage

Datei: [test_v8_completion_ebt.py](test_v8_completion_ebt.py),
für C37: [test_v8_case_forms_ebt.py](test_v8_case_forms_ebt.py).

| Case | Abschnitt | Setup / Auslöser | Sollbeobachtung | Nodes |
| --- | --- | --- | --- | ---: |
| C25 | 4, 6 | Import-, Syntax-, Fixture- oder Umgebungsfehler ohne ausgeführten Fall | Setupfehler bleibt sichtbar; weder fachliche Reproduktion noch Abschlussfreigabe | 4 |
| C26 | 4, 6 | Ausschließlich erfolgreiche Collection | Keine Reproduktions-/Verifikationsqualifikation | 1 |
| C27 | 4, 6 | Testdienst meldet grüne Ausgangsproduktion | Kein erfundenes Rot, kein automatischer Produktionspatch, keine Abschlussfreigabe allein aus Grün | 1 |
| C28 | 4–6 | Nach Rot, Patch und Grün ändert QA Test, Fixture oder Konfiguration | Alte Qualifikation ungültig; neue Gegenprobe nutzt getrennte Kopie mit Originalproduktion und bytegleicher finaler Suite | 3 |
| C29 | 4, 6 | Cubie-Dienst meldet keine EBT-Nutzung, nur Ausführung, nur Evaluation oder ausdrücklich geprüfte Evaluation | Nur vollständiger Frameworknachweis erlaubt den sonst vollständig belegten Abschluss | 4 |
| C30 | 3, 6 | Nach Grün ändert sich Produktion, Test oder Environment | Review mit alten Belegen darf nicht abschließen | 3 |
| C31 | 6–7 | Analyse behauptet ohne Suite oder Belege vollständiges Grün | Abweisung, keine Freigabe und keine Dateiänderung | 1 |
| C32 | 4, 6–7 | Reale pytest-Unterprozesse: fachliches Rot, Produktionspatch, fokussiertes Grün, Regression, Analyse liest Belege und Diff | `submitted`, aktuelle Qualifikation, echte korrigierte Bytes, archivierte Pflicht zur separaten privaten Evaluation | 2 |
| C33 | 6–7 | Deadline 1800 während QA-/Dev-Rückfrage; Dev hat schon Patch | Unvollständiges Ende, ursprüngliche Deadline, offene Frage und vorhandener Patch gesichert; private Evaluation bleibt erforderlich | 2 |
| C34 | 6–7 | Test beginnt bei 1799 und endet bei 1801 Sekunden | Ergebnis und Patch archiviert, kein erfolgreicher Abschluss nach Deadline | 1 |
| C35 | 6 | 100 Modellanfragen, dann 120/720/1799 Sekunden | Lauf bleibt aktiv bis zur gemeinsamen Deadline; kein altes Aufruf-/Phasenlimit | 3 |
| C36 | 5 | Testlauf, identische Wiederholung, dann ausdrücklich frische Flakinessprüfung | Cache ausgewiesen mit derselben Beleg-ID; nur frische Ausführung erzeugt neuen unabhängigen Beleg | 1 |
| C37 | 4 | Je Arm richtige Produktion, Off-by-one-Defekt und vertauschte Ausgaben für Eingaben 1/2 | Zwei korrelierte Fälle; korrekt beide grün, beide Mutationen je zweimal fachlich rot; keine Collection-/Setupfehler oder Skips | 6 |
| C38 | 6 | Fokussiertes Rot/Patch/Grün und Modellreview ohne vereinbarte Regressionen | Keine Abschlussfreigabe | 1 |
| C39 | 3, 6 | Vollständige grüne Belege, aber anforderungsblockierende Frage in aktueller Karte | Keine Abschlussfreigabe | 1 |

## Vorgeschlagener Testanschluss

Das Design benennt Werkzeugverträge, aber noch keine implementierte Python-API.
[v8_support.py](v8_support.py) schlägt daher folgenden Anschluss vor:

```python
from testguided_study.team_v8 import V8TeamController

team = V8TeamController(
    workspace=workspace, artifact_dir=archive, mode="cubie",
    issue=original_issue, guides=guides, manifest=manifest,
    policy={"wall_seconds": 1800, "context_bytes": 80000},
    execute=io_port, clock=clock,
)
team.dispatch(role, {"action": "finish", "delivery": {...}})
team.request()   # messages, schema, history, job; zählt vorbereiteten Modellaufruf
team.snapshot()  # vom Controller abgeleiteter Zustand, keine Modellbehauptungen
team.advance()   # Deadline prüfen, ohne weiteren Modellaufruf
```

Eine andere interne Architektur kann über einen dünnen Testadapter angeschlossen
werden. Dieser darf keine erwarteten Zustände zurückgeben oder die getesteten
Rollen-, Versions-, Budget- und Abschlussregeln selbst implementieren.
Die Reihe verlangt keinen zusätzlichen Case-Compiler, keine Modell-generierten
IDs und keine alten `publish_context`-/`handoff`-/`confirm_requirements`-Aktionen.
Die Cases stehen als Metadaten bei der normalen Python-Suite und ihrer Lieferung.

### Lieferungen und Beobachtungen des Anschlusses

- Analyseorientierung: `finish(delivery={requirements, facts, source_refs,
  test_paths, test_command, baseline, hypotheses, open_questions})`. Hypothesen
  dürfen leer und fachlich nicht benötigte Punkte ausdrücklich offen sein.
  `update_context(context=...)` pflegt dieselbe Karte ohne Rollenwechsel.
- Informationsantwort: `finish(delivery={answer, refs, unresolved})`. Die
  Zuordnung zur gespeicherten Frage übernimmt der Controller. `ask_analysis`
  liefert eine controllerseitige `request_id`; gültige Wiederverwendung ist
  durch `cached=True` kenntlich.
- QA: `finish(delivery={cases, targets, regressions})`. Die konkreten
  Strukturfelder eines Falls sind in `CASE` des Helpers sichtbar. Der Controller
  validiert ihre Vollständigkeit, nicht automatisch die fachliche Wahrheit.
- Dev: `finish(delivery={summary, evidence_refs, open_points})`. Der Controller
  erzeugt eine `diff_ref`, über die Analyse den relevanten Patch lesen kann.
- Analyseabschluss: `finish(delivery={verdict, requirement_ids, reason,
  evidence_refs, open_points})`. `verdict="verified"` ist ein Modellurteil;
  es ersetzt weder aktuelle Runnerbelege noch das serverseitige Abschlussgate.
- `read_file` liefert `text`, `evidence_id` und einen versionsgebundenen
  `handle`; Edits verwenden `handle/new_text/reason`. Bei Konflikt liefert das
  vorgeschlagene Format `status="rejected"`, `code="edit_conflict"` und
  `current_text`. Gleichwertige Fehlerformate können im Adapter abgebildet werden.
- `request().schema.oneOf` beschreibt die Rollenwerkzeuge. `history` enthält
  nur unterschiedliche jüngste Werkzeugdialoge. `job.decision_required` weist
  die Recoveryentscheidung aus. Die vier Dialoge sind eine gewählte
  Startkonfiguration dieses Anschlusses, kein universeller Größenbeweis.
- Der Snapshot enthält `role`, `status`, `active_job.id`, `context_revision`,
  `cases`, `budget.deadline`, `metrics.model_calls`, `qualifications`,
  `completion.allowed`, `open_questions`, `test_observations` und
  `private_evaluation_required`. `submitted` bezeichnet den intern verifizierten,
  `incomplete` den unvollständigen Endzustand.
- `archive/team.json`, `archive/full.patch` und `archive/actions/*.json`
  konkretisieren die beobachtbare Archivierung. Referenzen und Versionen werden
  ausschließlich von der Produktion erzeugt und geprüft.

### I/O-Port und Aussagekraft der Replays

Der Helper teilt nur Uhr, EBT-Aufruf und permissives Datei-I/O mit der bestehenden
v6-Testinfrastruktur. Er übernimmt weder deren Policy noch deren Controller.
Das I/O akzeptiert aufgelöste Lese-/Editoperationen; Rechte müssen bereits davor
im v8-Controller geprüft sein. Baselinekopie, deren Pfad und Versionszuordnung
werden ebenfalls vom Controller erzeugt. Der Port liest die tatsächlichen Bytes
der übergebenen Arbeitskopie, um Originalproduktion und finale Tests zu prüfen.

Für kleine Controllerfälle liefert der Testdienst deterministische Runnerantworten
mit Fall- und Frameworknachweisen. Das prüft die Verarbeitung dieser Nachweise,
nicht ihre Erhebung durch einen echten Runner. In C32 werden Testergebnisse aus
echten pytest-Unterprozessen/JUnit gewonnen. **Die EBT-Nutzungszähler dieses
Ports bleiben auch dort vorgegebene Grenzportdaten.** Die Vorlage C37 belegt
separat echte EBT-Ausführung einschließlich expliziter Prüfung der Evaluation.
C32 ist ein Controllerreplay und kein vollständiger Provider-/Studienrunnerlauf.

## Verifikation des Ausgangsstands

- Gesamtreihe: **92 gesammelt, 6 bestanden, 86 am fehlenden v8-Einstieg rot**.
- Reales Test-I/O zusätzlich direkt gegen defekte und korrigierte Produktion
  geprüft: beide Arme erkennen Rot/Grün und die passenden pytest-Node-IDs.
- Bestehende v7-Controller- und Laufzeitabnahmen: **41 bestanden**.
- Ruff für alle fünf neuen Python-Dateien und `git diff --check` ohne Befund.

## Grenzen und nächste Qualifikation

Die Reihe konkretisiert jede der zehn Designabnahmen mit Beispielen. Sie
qualifiziert noch keinen v8-Produktionsstand und beweist weder die Hypothesen
V8-H1–H8 noch einen Frameworkvorteil oder die Richtigkeit beliebiger Testorakel.

Weitere wichtige Varianten sind offen:

- QA lehnt unbegründete Erwartungsabschwächung ab; Analyse löst den fachlichen
  Widerspruch anhand öffentlicher Quellen; Dev darf ihn nicht selbst umgehen.
- Recovery während QA-/Dev-Arbeit, Informationsantwort und Abschlussprüfung;
  wechselnde erfolglose Suchen; gültige Auflösung und spätere neue Episode.
- Inkrementelle Pflege der vier Wissenskartenabschnitte, Markierung veralteter
  Fundstellen, vollständiges Eingabebudget einschließlich Schema und Ausgabe,
  Repositorytexte mit Anweisungen als Daten und rollenfremde History.
- Vergleich identischer vorbestehender Suitefehler gegen neue Fehler mit gleicher
  Fehleranzahl; explizite Abschlussbegründung für Aufgaben ohne reproduzierbares Rot.
- Unbegrenzte Rückfrage-/Revisionsfolgen und ungültige Modellausgaben; Übergabe
  der verbleibenden Deadline an einen laufenden Provider und an echte Testprozesse.
- Tatsächliche EBT-Instrumentierung, v8-Auswahl im bestehenden Runner,
  serieller deterministischer Providerreplay, Freeze-/Monitorintegration,
  unabhängige private Evaluation auch nach unvollständigem v8-Lauf und vollständige
  Gleichheit des Steuerungskerns in beiden Studienarmen.

Erst danach folgen Modellpiloten und eingefrorene empirische Vergleiche.
Historische Designs, Freezes, laufende Standards und Produktionscode werden
durch diese Abnahmereihe nicht geändert.
