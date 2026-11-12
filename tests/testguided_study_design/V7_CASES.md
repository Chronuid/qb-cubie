> Aktualisierte Budgetanforderung: 30 Minuten gemeinsame Taskzeit. Die früheren
> Aufruf-, Phasen-, Reserve- und Reparaturlimits in diesem Designkatalog sind
> aufgehoben. Die ausführbaren Budgettests prüfen stattdessen Fortsetzung bis
> zur gemeinsamen Deadline; erfolgreich geprüfte Einreichungen bleiben möglich.

# EBT-Abnahmecases für Agentendesign v7

Grundlage: [AGENTENDESIGN-V7.md](../../experiments/testguided-study/AGENTENDESIGN-V7.md),
Stand 12. November 2026, insbesondere Abschnitte 3–9 und V7-A01 bis V7-A14.

Diese Reihe enthält **41 ausführbare pytest-Nodes** mit expliziten EBT-Verträgen
und anschließender Prüfung von `result.evaluation is True`. Es gibt weder
`xfail` noch übersprungene Fälle und keinen automatischen Rückfall auf v6.
Produktionscode, Standardversion, Studienkonfiguration und historische Freezes
werden nicht verändert.

Der gemessene Ausgangsstand ist **41 rot**: Alle Fälle scheitern im ausgeführten
EBT-Target an `default_design(..., version=7)` mit
`ValueError: Unsupported default design version`. Collection funktioniert.
Dies belegt den fehlenden Versionseinstieg, nicht 41 unabhängige Defekte.
Die darunterliegenden Assertions und Replays sind bis zur v7-Implementierung
unqualifizierte Abnahmeverträge; sie müssen danach erneut ausgeführt werden.
Die 98 ursprünglichen v6-Abnahmen (Controller, Caseformen, Evaluation) bestehen
im selben Arbeitsstand weiterhin. Ruff prüft die drei neuen Python-Dateien
ohne Befund.

## Ausführung

```bash
.venv/bin/python -m pytest \
  tests/testguided_study_design/test_v7_controller_ebt.py \
  tests/testguided_study_design/test_v7_runtime_ebt.py --collect-only -q

.venv/bin/python -m pytest \
  tests/testguided_study_design/test_v7_controller_ebt.py \
  tests/testguided_study_design/test_v7_runtime_ebt.py -q --tb=short
```

Alle Workspaces, Git-Repositories und Archive entstehen unter `tmp_path`.
Netzwerk, Docker, Ollama, Downloads und private Benchmarkdaten sind unnötig.
Git und der aktuelle Python-Interpreter genügen für die lokalen Runner-Replays.
Die vorhandenen [v6-Abnahmen](V6_CASES.md) bleiben zusätzlich Regressionen.

## Testaufbau und Aussagegrenzen

[v7_support.py](v7_support.py) erzeugt einen kleinen öffentlichen Workspace mit
defektem `double(2) == 3`, einer Anforderung `double(2) == 4`, Tests, Fixture,
Konfiguration und einem Requests-artigen `src/`-Layout. Eine private Sentineldatei
prüft die Grenze des öffentlichen Inventars. Der Ursprung des Sollwerts ist
die öffentliche Aufgabe; beobachtete Produktion wird nicht zum Orakel.

Der Harness verwendet den echten `TeamController`, echte temporäre Dateien,
eine kontrollierbare monotone Uhr und den permissiven I/O-Port aus v6. Er
implementiert keine Übergangs-, Rechte-, Budget-, Recovery- oder Freigaberegeln.
Die einzige Übersetzung bildet neue `line_start`/`line_end` auf die internen
Zeilenparameter des vorhandenen Testports ab. Öffentliche Navigation und
Versionsprüfung bleiben Produktionsverantwortung.

Die 39 Controller-Nodes verwenden vorgegebene Testdienstresultate, um
Collectionfehler, fachliches Rot und Grün gezielt einzuspeisen. Diese Resultate
sind keine real ausgeführten Tests des kleinen Beispielprojekts. Die zwei
zusätzlichen Nodes in [test_v7_runtime_ebt.py](test_v7_runtime_ebt.py) verlangen
dagegen den echten Runner, dessen Dateiwerkzeuge, Git-Baseline und lokale
pytest-Unterprozesse mit echtem Rot, Produktionsänderung und Grün. Nur der
Modellprovider liefert deterministisch vorgegebene Antworten. Der vorhandene
HostContainer-Testadapter ersetzt Containerwurzel und Interpreter. Auch diese
Replays belegen keine Modellfähigkeit und keine private Lösungsquote.

## Vorgeschlagene Produktionsschnittstelle

Das Design definiert Modellaktionen und Verhalten, aber nicht alle Python-
Methoden oder Archivschlüssel. Folgende Konkretisierungen sind **Vorschläge
dieser Abnahmereihe**, keine Behauptungen über bereits vorhandene v7-APIs:

- `default_design(mode, guides, version=7)` liefert ein explizites Design mit
  v7-Policy; `TeamController(..., design=design)` verwendet es. Historische
  v6-Schemas behalten ihre Parameter.
- `TeamController.advance()` verarbeitet fällige Fristen, Reserve und automatische
  Übergänge ohne Inferenz. Der Runner ruft dieselbe Grenzprüfung vor einer
  neuen Anfrage und nach einer Antwort auf. Ein Poll verbraucht keinen
  Modellaufruf; tatsächlich ausgelöste Controllerwerkzeuge bleiben budgetiert.
- `request()` liefert neben dem zustandsabhängigen `schema` ein
  `timeout_seconds`, begrenzt durch Antwort-, Auftrags- und Gesamtfrist.
- `finish_orientation` verwendet die Felder aus Abschnitt 3.2. Anforderungen
  tragen `id`, `text`, `refs`, `status`; die bestehende öffentliche Referenz
  `issue:REQ-1` bezeichnet die Runneraufgabe. Ein erneuter identischer Abschluss
  kann bestätigt oder abgewiesen werden, erzeugt jedoch keinen zweiten Auftrag.
- `confirm_requirements(requirements=[{id, text, refs}])` bestätigt die fachliche
  Ableitung. `context.json` kennzeichnet den mechanischen Fallback mit
  `provisional=true`; ohne Modellbestätigung bleibt `requirements=[]`.
- Suchantworten verwenden `hits` mit `path` und einbasierter `line`, ferner
  `next_cursor`, `truncated`, `scope_exists`, `files_searched`, `files_skipped`
  und bei fehlendem Scope `candidates`. Ungültige Cursor melden `cursor_error`;
  Schemafehler dürfen `rejected` melden. Ein bekannter verbotener Anfragepfad
  darf im Fehler wiederholt werden, jedoch nicht als öffentlicher Kandidat.
- `search_page_size=2` ist eine injizierbare Policy für kleine Paginationfixtures,
  kein vom Modell erfundener Offset. Die normale Produktionsseitengröße bleibt
  eine Implementierungsentscheidung.
- `snapshot().progress.read_lines` zählt erstmals gelesene Zeilen.
  `recovery_episodes` enthält Diagnosen;
  `metrics.controller_tool_calls` weist automatische Werkzeugkosten aus.
  Diese Felder konkretisieren die Beobachtbarkeit aus Abschnitt 8.
- `budget_exhausted` ist der gemeinsame v7-Endgrund bei Gesamtbudgetende.
  Das bereits bestehende Archivlayout und die v6-Case-/Suite-/Reviewaktionen
  werden für den Replay weiterverwendet.

Andere gleichwertige interne Darstellungen sind möglich; bei deren Auswahl
muss der Testadapter angepasst werden, ohne die fachlichen Orakel zu ändern.

## Anforderungs- und Casematrix

Alle Zeilen sind durch die genannte Designabnahme öffentlich begründet.
Der Funktionsname bezeichnet den Node ohne seine Parametervarianten.
Die ersten 18 Zeilen liegen in
[test_v7_controller_ebt.py](test_v7_controller_ebt.py).

| Bezug / Abschnitt | Setup und Auslöser | Sollbeobachtung | Testfunktion | Nodes |
| --- | --- | --- | --- | ---: |
| A01 / 3.2, 6 | Nur Navigation; sechs Anfragen oder Uhr auf 120 s | Ohne Abschlussinferenz QA aktiv; vorläufiger Kontext ohne erfundene Anforderungen; Erfolg gesperrt | `test_a01_orientation_limit_hands_public_evidence_to_qa` | 2 |
| A02 / 3.2 | Gültiger, unbekannter, doppelter oder nach Dateiänderung veralteter Beleg | Eine Übergabe; ungültige Pakete ändern weder Kontextrevision noch Nachrichten oder Auftrag | `test_a02_finish_is_atomic_versioned_and_idempotent` | 4 |
| A03 / 4.1 | `requests/utils.py` fehlt, `src/requests/utils.py` existiert | Expliziter Pfadfehler, höchstens fünf Kandidaten, keine stille Umleitung; richtige Suche findet reale Quelle | `test_a03_missing_scope_suggests_real_src_path_without_redirect` | 1 |
| A04 / 4.1 | Vorhandenes Verzeichnis ohne Treffer, fehlende Datei, privater und äußerer Pfad | Unterschiedliche Status, keine privaten Treffer oder Kandidaten | `test_a04_scope_outcomes_and_private_boundary` | 4 |
| A04 / 4.1 | Nicht dekodierbare Datei im vorhandenen Scope | Lesbare Dateien durchsucht; Auslassung explizit statt scheinbar vollständigem Negativbefund | `test_a04_undecodable_file_is_explicitly_skipped` | 1 |
| A05 / 4.2 | `start=860`, numerischer oder erfundener Cursor | Schema-/Cursorfehler ohne Treffer | `test_a05_search_rejects_legacy_offsets_and_invented_cursors` | 3 |
| A05 / 4.2 | Fünf Treffer auf Seiten mit zwei Treffern; Inhalt, Query oder Werkzeug geändert | Unverändert exakt Zeilen 1–5, sonst Cursorfehler | `test_a05_cursor_is_bound_and_pages_have_no_loss_or_duplicates` | 4 |
| A05 / 4.2 | Literal `\d+[x]` über JSON; Einzelzeile lesen | Nur wörtlicher Treffer; inklusive einbasierte Zeilengrenzen | `test_a05_literal_escapes_survive_json_and_inclusive_line_reads` | 1 |
| A06 / 5.1–5.2 | Dieselbe Lesung zweimal, dann überlappende Erweiterung | Duplikatkennzeichnung, kein zweites Backendlesen, nur eine neue Zeile; beide Werkzeugversuche budgetiert | `test_a06_duplicate_read_avoids_backend_and_only_new_lines_count` | 1 |
| A07 / 5.2 | Zwei verschiedene ergebnislose Suchen | Eine Recovery mit Diagnose, verändertem Schema und sichtbaren Controllerkosten | `test_a07_two_empty_searches_trigger_diagnosis_and_schema_change` | 1 |
| A08 / 3.2 | Mechanisches Paket; Suiteversuch vor Bestätigung, danach öffentliche Bestätigung und Case | Erst Ablehnung, danach Suiteübergabe; keine automatische Reproduktionsqualifikation | `test_a08_provisional_context_needs_public_requirement_confirmation` | 1 |
| A09 / 3.4, 6 | QA-Frist mit gültiger gesammelter Suite bzw. ohne Suite | Gültige Lieferung an Dev; sonst nach 45 s Recovery `suite_incomplete` | `test_a09_qa_deadline_only_hands_off_an_existing_valid_suite` | 2 |
| A10 / 3.4, 7 | Collectionfehler, grüner Ursprung oder passendes Assertion-Rot; anschließend Edit | Nur passendes Rot öffnet Produktion; kein künstliches Rot aus Grün | `test_a10_only_matching_behavioral_red_unlocks_production` | 3 |
| A11 / 3.3, 6 | QA oder Dev fragt Analysis, erhält unbekannte Antwort und fragt identisch erneut | Derselbe Auftrag und Gesamtdeadline; keine zweite Zustellung; offene Frage sperrt Erfolg | `test_a11_information_roundtrip_preserves_job_budget_and_deduplicates` | 2 |
| A12 / 6 | Anfrage bei 0 bzw. 100 s Orientierung | Antworttimeout 60 bzw. 20 s; Gesamtdeadline 900 s | `test_a12_request_timeout_obeys_response_and_orientation_deadlines` | 2 |
| A12 / 6 | Uhr direkt auf 900 s | Gesamtende vor Autoübergabe; Patcharchiv und Pflicht zur privaten Evaluation erhalten | `test_a12_global_exhaustion_precedes_automatic_handoff` | 1 |
| A13 / 6 | Reserve bei 720 s aus Orientierung, QA, Implementierung oder Review | Keine weitere Revisionsrunde; Reserve und Artefaktsicherung sichtbar | `test_a13_reserve_blocks_new_repair_and_preserves_artifacts` | 4 |
| A14 / 2, 7 | Vollständige skriptgesteuerte Controllerfolge in beiden Armen | Fachlich qualifizierter interner Abschluss; öffentliche Grenze und getrennte Evaluation erhalten | `test_a14_complete_scripted_contract_keeps_public_boundary` | 2 |
| A14 / 7, 9 | Echter Runner mit deterministischem Provider, je Arm | Reales fachliches Rot, echter Patch, zwei grüne Testläufe, Review, Submission; Cubie-Test prüft Evaluation | `test_a14_real_runner_reproduces_repairs_and_verifies_in_both_arms` | 2 |

## Noch nicht vollständig abgedeckt

Die Reihe konkretisiert alle 14 Abnahmen, schöpft deren Varianten aber noch
nicht aus. Vor einer vollständigen v7-Qualifikation sind insbesondere weitere
Fälle nötig für:

- Startkartengröße, Baselineinhalt und automatische Startkosten;
- Cursorbindung an Inventaränderungen und Pagination von `find_paths`;
- Recoveryabschluss nach behobener Ursache, spätere unabhängige Episode und
  Schutz gegen erneute identische Recovery nach Rollenwechsel;
- Anforderungswidersprüche, Abschwächungsversuche und fallbezogene Invalidierung
  nach `confirm_requirements`;
- QA-Aufrufgrenze und lokale Frist während Informationsunterbrechungen;
- Antworttimeout während laufender Inferenz, genau eine budgetierte
  Ausgabereparatur und tatsächliche Weiterleitung des Timeouts zum Provider;
- Reserveverifikation vorhandener Artefakte einschließlich der Gegenprobe,
  dass sie weiter erlaubt bleibt;
- vollständige Gleichheit der Rechte-/Budgetregeln beider Arme,
  versionsgleiche finale Baseline nach Testrevision und unabhängige private
  Evaluation eines unvollständigen v7-Laufs.

Die passenden v6-Verträge dienen dabei als Regressionen, ersetzen aber keinen
erneuten Nachweis unter v7. Technische Replay-Ergebnisse ersetzen zudem nicht
die im Design verlangten echten Entwicklungsversuche und manuelle Orakelprüfung.
