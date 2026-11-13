> Aktualisierte Budgetanforderung: 30 Minuten gemeinsame Taskzeit. Die früheren
> Aufruf-, Phasen-, Reserve- und Reparaturlimits in diesem Designkatalog sind
> aufgehoben. Die ausführbaren Budgettests prüfen stattdessen Fortsetzung bis
> zur gemeinsamen Deadline; erfolgreich geprüfte Einreichungen bleiben möglich.

# EBT-Abnahmecases für Agentendesign v6

Grundlage ist [AGENTENDESIGN-V6.md](../../testguided-study/AGENTENDESIGN-V6.md),
Stand 11. November 2026, insbesondere die Abnahmen V6-A01 bis V6-A18 in Abschnitt 9.
Die Reihe enthält **98 ausführbare pytest-Nodes**. Jeder Node führt einen
expliziten EBT-Vertrag aus und verlangt `result.evaluation is True`.
Es gibt keine `xfail`-Markierungen und keine übersprungenen Cases.

Der Ausgangsstand ist **66 rot und 32 grün**. 64 rote Nodes scheitern an dem noch
fehlenden `testguided_study.controller.TeamController`; zwei an der Ablehnung
von `default_design(..., version=6)`. Das sind fehlende Implementierungseinstiege,
keine 66 unabhängig nachgewiesenen Funktionsfehler. Die dahinterliegenden
Controller-Verträge müssen nach Implementierung erneut ausgeführt werden.
v5 und historische Archive werden durch diese Reihe nicht geändert.

Die 28 grünen Vorlagenprüfungen führen echte lokale pytest-Unterprozesse aus.
Die weiteren vier grünen Integrationsprüfungen belegen den bereits vorhandenen
unabhängigen Evaluatorpfad mit vorgegebenem unvollständigem Teamergebnis.
Sie qualifizieren noch keinen ausführbaren v6-Teamrunner.

## Implementierungsstand 12. November 2026

Die ursprünglichen 98 Nodes bestehen mit dem implementierten v6-Teamcontroller.
Der oben dokumentierte Rotstand bleibt der historische Ausgangsbefund.
[test_v6_runtime.py](test_v6_runtime.py) ergänzt 25 Laufzeitprüfungen:
vollständige serielle Teamläufe in beiden Bedingungen mit echten Dateiwerkzeugen
und pytest-Unterprozessen; dynamische Bereichs-Handles; explizite EBT-Prüfung
gegenüber totem Assertioncode; verschachtelte Rückfragen und Analyse-Prüfaufträge;
Drei-/Sechs-Rundengrenzen; fallbezogene Versionsinvalidierung; Freeze und Monitor;
Stillstand trotz Kontextumformulierungen sowie Baselinekopien mit finaler
Konfiguration und Erkennung einer manipulierten Git-Ausgangsreferenz.

Ein kompletter gepaarter Studienstart führt außerdem zwei echte v6-Teamrunner
bis zum unvollständigen Ende nach begrenzter Ausgabereparatur. Die gesicherten
Produktionspatches erreichen trotzdem die unabhängige Evaluation; interner Status,
private Lösung und vollständiger Workspacepatch bleiben getrennt archiviert.
Container- und Evaluatorgrenzen werden dabei durch lokale deterministische Ports
vertreten. Docker- und Modellpiloten bleiben eine eigene Qualifikation.

Die Ausführung verwendet `agent_version = 6` oder ein ausdrücklich erzeugtes
`default_design(..., version=6)`. Der reguläre Standard bleibt v5. Einstieg,
Konfiguration und Artefakte stehen in der [README](../../testguided-study/README.md#weiterentwicklung-der-agenten).

## Ausführen

```bash
# Ursprüngliche v6-Abnahmen plus Laufzeitintegration.
.venv/bin/python -m pytest \
  experiments/tests/testguided_study_design/test_v6_controller_ebt.py \
  experiments/tests/testguided_study_design/test_v6_case_forms_ebt.py \
  experiments/tests/testguided_study_design/test_v6_evaluation_ebt.py \
  experiments/tests/testguided_study_design/test_v6_runtime.py -q --tb=short

# Nur die bereits ausführbaren Referenzvorlagen und der Evaluatorpfad.
.venv/bin/python -m pytest \
  experiments/tests/testguided_study_design/test_v6_case_forms_ebt.py \
  experiments/tests/testguided_study_design/test_v6_evaluation_ebt.py -q
```

Collection importiert keine fehlende v6-Klasse. Erst das ausgeführte EBT-Target
löst sie auf und meldet das fehlende Produktions-API ausdrücklich als Fehler.
Alle Workspaces und Archive entstehen unter pytest-`tmp_path`. Die Unterprozesse
verwenden denselben Interpreter, das lokale Cubie und isolierte pytest-Plugins.
Docker, Ollama, Downloads, historische Archive und Netzwerkzugriffe sind unnötig.

## Anforderungs- und Casematrix

Die IDs V6-A… stammen aus dem Design. V6-C… und REQ-F… sind lokale Ableitungen
dieser Reihe. Jede Tabellenzeile benennt Anforderungsbezug, konkretes Setup,
Sollbeobachtung und Node. Parameter ergänzen den angegebenen Node um `[variant]`.
Für alle Cases gilt die Bereinigung durch `tmp_path`; Unterprozesse haben ein
Timeout von 30 Sekunden. Öffentliche Begründungsreferenz ist jeweils der genannte
Abschnitt des [Designs](../../testguided-study/AGENTENDESIGN-V6.md).

Die folgenden Controller-Nodes liegen in [test_v6_controller_ebt.py](test_v6_controller_ebt.py).

| Case / Anforderung | Abschnitt | Setup und Auslöser | Erwartete Beobachtung | pytest-Funktion | Nodes |
| --- | --- | --- | --- | --- | ---: |
| V6-A01 | 2–4 | Neuer Lauf in `pytest` und `cubie`; Analyse liest Quelle, veröffentlicht Kontext und QA-Auftrag | `analysis/orient` wird `qa/specify`; Auftrags-ID, Kontextrevision und Workspaceversionen bleiben gebunden | `test_a01_analysis_starts_and_qa_receives_versioned_context` | 2 |
| V6-A02 | 3–5 | QA veröffentlicht C-1 mit REQ-1 und konkretem Testziel | `dev/reproduce`, `suite_ready`, unveränderter Anforderungsbezug; eindeutige Runner-Nachrichten-IDs | `test_a02_suite_handoff_preserves_cases_targets_and_runner_ids` | 1 |
| V6-A03a | 2 | Analyse schreibt Produktion/Tests; QA schreibt Produktion; Dev schreibt Tests, Fixture, pytest-Konfiguration oder löscht Test als Quelle | Ablehnung vor I/O; alle Dateiinhalte unverändert | `test_a03_dispatch_rejects_cross_role_mutations_before_io` | 7 |
| V6-A03b | 2 | QA verwendet `../escape.py`, absoluten temporären Pfad, `tests/../src/new.py` oder Symlink `alias/new.py` | Keine Umgehung des Pfadmanifests; keine Mutation und kein Backendaufruf | `test_a03_canonical_paths_and_symlinks_cannot_bypass_manifest` | 4 |
| V6-A04a | 3–4 | QA beziehungsweise Dev fragt nach der Quelldatei; Analyse antwortet adressiert | `answer_information`; danach ursprüngliche Rolle, Zustand und Auftrags-ID; korrektes `reply_to`; Weiterleitung kostet keinen Modellaufruf | `test_a04_information_roundtrip_resumes_same_job_and_role` | 2 |
| V6-A04b | 2–3 | Analyse kann eine anforderungsrelevante Frage öffentlich nicht beantworten | Frage bleibt offen; keine Abschlussfreigabe | `test_a04_unknown_answer_preserves_dependent_open_question` | 1 |
| V6-A05 | 2–4 | Dev sendet Teständerungsauftrag mit Case, Anforderung und unveränderter Rot-Beleg-ID | QA wird in `revise_tests` aktiv; Nachricht ist ein belegter Arbeitsauftrag | `test_a05_test_change_request_is_addressed_to_qa_with_evidence` | 1 |
| V6-A06 | 2–4 | Dev will Sollwert 4 allein wegen beobachteter 3 abschwächen; QA lehnt ab | Gültiger Case bleibt erhalten; offener Dissens geht zu Analyse und sperrt Abschluss | `test_a06_qa_rejects_unsupported_weakening_and_escalates_dissent` | 1 |
| V6-A07 | 4, 7 | Nach Rot und Produktionsänderung revidiert QA Testdatei, `conftest.py` oder `pytest.ini` | Altes Rot ungültig; finale Tests/Fixture/Konfiguration identisch gegen Original und aktuelle Produktion; Baseline tatsächlich in anderer Kopie mit ursprünglichen Produktionsbytes | `test_a07_revision_invalidates_red_and_requires_final_suite_baseline` | 3 |
| V6-A08 | 3–4, 7 | Nach erfolgreichem Review ändert ein externer Vorgang Code oder Environmentdatei | `submit` abgewiesen; Verifikation und Freigabe invalidiert | `test_a08_change_after_review_invalidates_current_completion` | 2 |
| V6-A09a | 6 | Datei ändert sich nach Bereichslesung; zwei Edits mit altem Handle, dann erneutes Lesen und lokaler Edit | Beide alten Edits ohne I/O abgewiesen; erst frisches Handle erlaubt Änderung | `test_a09_stale_handle_requires_reread_before_one_new_edit` | 1 |
| V6-A09b | 6 | Dev ersetzt einen gelesenen Bereich durch `return (` | Python-Syntaxfehler vor Mutation; Originalbytes bleiben erhalten | `test_a09_invalid_python_is_rejected_atomically` | 1 |
| V6-A10 | 5, 7 | Cubie-Testdienst meldet keine EBT-Ausführung, nur Ausführung, Evaluation ohne explizite Prüfung oder vollständig geprüfte Evaluation | Nur letzte Variante erlaubt Abschluss; Ausführung/Evaluation/Prüfung bleiben verschieden | `test_a10_cubie_execution_evaluation_and_explicit_check_are_distinct` | 4 |
| V6-A12 | 4, 7 | Nur Collection, null Tests, Skip, Xfail oder Produktionsimportfehler | Weder passende Reproduktion noch verifizierter Abschluss | `test_a12_non_execution_never_qualifies_as_behavioral_red_or_green` | 5 |
| V6-A13 | 7 | Ein bekannter Altfehler bleibt gleich oder wird bei gleicher Gesamtanzahl durch neuen Fehler ersetzt | Identischer Altfehler erlaubt `verified_with_baseline_failures`; neuer Fehler ergibt `incomplete` | `test_a13_baseline_identity_matters_even_when_failure_counts_match` | 2 |
| V6-A14a | 6 | Nach Rollenwechseln werden 900 Sekunden, 48 Modellaufrufe oder 96 Werkzeugaufrufe erreicht | Gemeinsame Grenze; spezifischer Budgetgrund; keine Überschreitung. Unterschiedliche Quelldateien verhindern eine Verwechslung mit Stillstand | `test_a14_team_budget_is_shared_across_role_changes` | 3 |
| V6-A14b | 6 | Zeit erreicht 720 Sekunden oder 42 Modellaufrufe wurden verbraucht | Reserve aktiv; keine neue Reparaturrunde, Testverifikation weiterhin möglich; Deadline bleibt 900 | `test_a14_reserve_allows_verification_but_no_new_repair_round` | 2 |
| V6-A14c | 6 | Wiederholte identische Leseaktion mit umformulierten Hypothesennotizen | Genau eine gezielte Recovery, danach unvollständiges Ende ohne Freigabe | `test_a14_rephrased_notes_do_not_reset_stagnation` | 1 |
| V6-A15a | 2, 7 | QA oder Dev versucht nach aktuellem Grün selbst einzureichen | Ablehnung; kein `submitted` | `test_a15_only_analysis_can_submit_even_after_current_green` | 2 |
| V6-A15b | 7 | Analyse reicht nach passendem Rot, Reparatur, aktuellem Zielgrün und Regressionen ein | `submitted` mit `verified_green` | `test_a15_valid_analysis_submission_records_verified_green` | 1 |
| V6-A15c | 7 | Analyse behauptet ohne Testausführung Erfolg | Ablehnung; Modellnotiz ersetzt keinen Testbeleg | `test_a15_analysis_claim_without_execution_cannot_open_completion_gate` | 1 |
| V6-A16 | 4, 7 | Zentraler Case ist schon auf Originalproduktion grün | Kein künstliches Rot und keine erfundene Produktionsänderung; Analyse muss fehlende Reproduktion einordnen | `test_a16_green_original_is_visible_and_does_not_manufacture_reproduction` | 1 |
| V6-A17 | 8 | Derselbe Start in beiden Testbedingungen | Gleiche Rollen, Policy und initiale Werkzeugschemata | `test_a17_both_arms_share_permissions_policy_and_roles` | 1 |
| V6-A18a | 6–7, 9 | Nach Produktionspatch Deadline oder zweimal ungültige Ausgabe | `incomplete`; Patch und Teamstand gespeichert; genau ein Ausgabereparaturversuch; beide Rohantworten archiviert; private Evaluation bleibt erforderlich | `test_a18_incomplete_exit_preserves_patch_and_raw_evidence` | 2 |
| V6-C01 | 5 | Case ohne `case_id`, `requirement_id`, `reason_ref`, `target`, `expected` oder `pytest_node` | Strukturprüfung lehnt ab; keine registrierten Cases oder Dateiänderungen | `test_c01_case_structure_is_validated_without_inventing_an_oracle` | 6 |
| V6-C02 | 2 | Jede der drei Rollen liest einen unter `evaluator/` platzierten privaten Sentinel | Abweisung vor I/O; Sentinel wird nicht ausgegeben | `test_c02_private_paths_are_unreadable_to_every_role` | 3 |
| V6-C03a | 3 | Tatsächliche Request-Erzeugung für jede Rolle | Originalissue und ganzer Cubie-Guide vorhanden; nur rollenbezogene Werkzeuge | `test_c03_actual_role_request_preserves_mandatory_context` | 3 |
| V6-C03b | 3, 6 | Nur 16 Bytes Kontextkapazität | Explizites `context_error` vor erstem Modellaufruf | `test_c03_oversized_mandatory_context_fails_explicitly` | 1 |
| V6-C04 | 9 | `default_design(mode, guides, version=6)` für beide Bedingungen | Design wird erzeugt und durch gemeinsame Komposition validiert | `test_c04_v6_is_an_explicitly_supported_design_version` | 2 |

### V6-A11: konkrete, ausführbare QA-Vorlagen

[v6_templates.py](v6_templates.py) enthält sieben geprüfte Referenzformen mit
jeweiliger Anforderungs-ID, öffentlicher Begründung, Setup, Target, Argumenten,
Sollwert und einer gezielten Produktionsmutation. [fixtures/v6/app.py](fixtures/v6/app.py)
ist die kleine öffentliche Beispielproduktion. Adapter rufen diese Produktion
auf und lesen Rückgabe, Objektzustand oder Seiteneffekt aus. Die Sollwerte stehen
im Vertrag und werden nicht durch den Adapter zurückgegeben.

Alle Nodes liegen in [test_v6_case_forms_ebt.py](test_v6_case_forms_ebt.py), Funktion
`test_a11_reference_form_distinguishes_real_production_behavior`.
Die Node-ID lautet `[defective|corrected-pytest|cubie-F01|…|F07]`, konkret
beispielsweise `[defective-cubie-F04]`. Jede Form hat vier Nodes.

| Case / Anforderung | Eingabe und Target | Sollbeobachtung | Gezielter Defekt |
| --- | --- | --- | --- |
| F01 / REQ-F01 | `double(1)` und `double(2)` | Je ein korrelierter Vertrag mit 2 beziehungsweise 4 | Ausgaben vertauscht: `6 - value * 2`; beide Nodes im Unterprozess scheitern |
| F02 / REQ-F02 | `greet("Ada", prefix="Grüß dich, ")` | `"Grüß dich, Ada"` | Keywordargument wird durch englisches Standardpräfix ersetzt |
| F03 / REQ-F03 | `divide(1, 0)` | `ValueError`, Meldung exakt `denominator must be nonzero` | Normale Rückgabe 0 statt Exception |
| F04 / REQ-F04 | pytest-Fixture `Counter(2)`, `add(3)` über Beobachtungsadapter | Rückgabe und gespeicherter Zustand `(5, 5)` | Zuweisung statt Addition ergibt `(3, 3)` |
| F05 / REQ-F05 | WSGI-Aufruf für `GET /health` ohne Server oder Netzwerk | `200 OK`, `application/json`, Body `b'{"status":"ok"}'` | Body wird durch `{}` ersetzt |
| F06 / REQ-F06 | `render_status` auf frischem `StringIO` | Exakt `"READY\n"` | Falsche Statuszeile `WAIT` |
| F07 / REQ-F07 | `write_report` im temporären Verzeichnis, Text `"Grüße\n"` | Datei existiert; Unicode und abschließender Zeilenumbruch erhalten | `strip()` entfernt den Zeilenumbruch |

In Cubie verwendet jede Vorlage `EBT(...).run()` und prüft dessen
`evaluation is True`. Die pytest-Variante verwendet für dieselben Eingaben
und Sollbeobachtungen normale Assertions beziehungsweise `pytest.raises`.
F03 verwendet `ExceptionExpectation`; `returns` und `raises` werden nicht
im selben Postzustand kombiniert. F01 erzeugt zwei getrennte Verträge statt
einer gemeinsamen, unkorrelierten Postmenge. Die äußere EBT-Abnahme prüft
Exitcode und JUnit: tatsächliche Testanzahl, fachliche Assertionfehler bei der
defekten Produktion, keine Collectionfehler oder Skips, Grün nach Korrektur.

### V6-A18b: unabhängige Evaluation trotz unvollständigem Teamende

Vier Nodes in [test_v6_evaluation_ebt.py](test_v6_evaluation_ebt.py), Funktion
`test_a18_private_evaluation_runs_despite_incomplete_internal_result`,
kombinieren `wall_budget`/`invalid_output` mit `unsolved`/`solved`.
Der Agentengrenzport liefert `status=incomplete` und entweder einen leeren
oder den korrekten synthetischen Patch. Der echte automatische Studienstart,
Freeze und `execution.run` müssen beide geplanten Bedingungen ausführen,
deren Patches unverändert an den separaten Evaluator übergeben, Ergebnisse
archivieren und Containerports aufräumen. Beide internen Ergebnisse bleiben
unvollständig; die private Lösung wird unabhängig davon `False` oder `True`.
Der deterministische Evaluatorport benötigt keine privaten echten Aufgaben.

## Vorgeschlagene Python-Schnittstelle für die roten Controller-Cases

Das Design benennt konzeptionelle Werkzeuge, aber noch keine Python-Klasse.
Diese Reihe schlägt **einen Testanschluss** für die erste Implementierung vor:

```python
controller.TeamController(
    workspace=Path(...), artifact_dir=Path(...), mode="cubie",
    issue=original_issue, guides={"pytest": "...", "cubie": "..."},
    manifest={"src": "production", "tests": "tests", ...},
    policy={...}, execute=io_callback, clock=monotonic_clock,
)
team.dispatch(role, action)  # completed/rejected; keine erwarteten Ergebnisse injizieren
team.snapshot()            # tatsächlich vom Controller abgeleiteter JSON-Stand
team.request()             # aktive Rolle: messages/schema; zählt Modellaufrufgrenze
team.reject_output(raw=..., usage=...)  # Providerfehler samt Tokens, begrenzte Recovery
```

Die Schnittstelle ist ein **Implementierungsvorschlag dieser Abnahmereihe**,
keine bereits zugesagte Laufzeit-API des Designs. Bei einer anderen internen
Architektur kann ein dünner Anschluss im Testhelper die Aufrufe weiterreichen.
Er darf keine Rollen-, Versions-, Budget- oder Abschlussregeln selbst ausführen
und keine erwarteten Beobachtungen anstelle der Produktion erzeugen.

[v6_support.py](v6_support.py) enthält nur temporäre Beispieldateien, Uhr,
I/O-Port, vorbereitete Testdienstantworten und kurze Aufrufsequenzen. Das
Workspace-I/O ist bewusst permissiv: Nur der Produktionscontroller darf Rechte,
Pfadmanifest, aktive Rolle, Bereichs-Handles und Syntax prüfen. Abgewiesene
Aktionen dürfen diesen Port gar nicht erreichen. `read_file` liefert Text,
Dateihash und Bereich; der Controller erzeugt das opake Handle und die Beleg-ID.
Ein aufgelöstes `replace_region` übergibt `path/start/end/new_text` an I/O.

Die Testdienstantworten sind deterministische **Runner-Grenzports**, keine
Modellnotizen. Der Controller ergänzt selbst Versionen und Beleg-IDs. Bei
`check_baseline` muss er eine getrennte Kopie bereitstellen; `workspace` im
Backendauftrag benennt deren Pfad absolut oder relativ zum temporären Elternordner.
Der Port liest dort die echten Produktions-, Test-, Fixture- und Konfigurationsbytes.
Die Tests vergleichen sie mit Originalproduktion und finaler Suite.

Für den beobachtbaren Snapshot werden folgende Felder vorgeschlagen:

| Bereich | Felder / Bedeutung |
| --- | --- |
| Ablauf | `role`, `roles`, `state`, `status`, `reason`, `active_job.id`, `pending_requests`, `open_questions` |
| Bindung | `context_revision`, `versions.production/tests/environment`, `cases`, `messages` |
| Nachrichten | `id`, `reply_to`, `sender`, `recipient`, `type`, `context_revision`, `versions`, `payload`, `evidence_refs` |
| Qualifikation | `qualifications.reproduced/verified`, `completion.allowed/status`; Statuswerte aus Abschnitt 7 des Designs |
| Ressourcen | `policy`, `budget.reserve_active/deadline`, `metrics.model_calls/tool_calls/recoveries/output_repairs/first_production_change_call` |
| Ende | `private_evaluation_required`, archivierte `full.patch` und `team.json` |

Die Beispielpolicy verwendet die noch einzufrierenden v6-Entwicklungswerte:
900 Sekunden, 48 Modell- und 96 Werkzeugaufrufe; Reserve 180 Sekunden und sechs
Modellaufrufe. Die Policy enthält auch drei QA/Dev-Runden und sechs
Informationsanfragen; deren exakte Grenzfallqualifikation ist noch zu ergänzen.
Ein deterministischer Controlleraufruf allein ist kein Modellaufruf.
`request()` bezeichnet den tatsächlich vorbereiteten Provideraufruf; reine
Nachrichtenweiterleitung darf ihn nicht auslösen.

## Aussagegrenzen und weitere Qualifikation

Die Reihe prüft konkrete Beispiele. Die grünen Vorlagen belegen funktionierende
Beobachtungsformen, aber noch keinen v6-Casegenerator oder dessen Einbindung in
Rollenaufträge. Die Controller-Cases prüfen nach Implementierung mechanische
Verträge; sie beweisen weder die Richtigkeit eines beliebigen QA-Orakels noch
höhere Modellleistung. Das Rollenschema ist gegen direkte Dispatch-Aufrufe
abgesichert; echte Containerisolation benötigt weiterhin eigene Integrationstests.

Noch erforderlich sind insbesondere vollständige serialisierte Teamläufe mit
deterministischen Modellclients, Monitor-/Freeze-Integration einschließlich
Designidentität, verschachtelte Rückfragen, explizite Drei-/Sechs-Runden-Grenzen,
Xpass-/fehlende-Einzelcase-Belege und die Inhalteprüfung der Testpassung.
V6-A17 deckt zunächst Startpolicy und initiales Schema ab, keinen vollständigen
gepaarten Studienlauf. V6-A18b erhält den bestehenden Evaluatorpfad; der Anschluss
eines echten v6-Teams bleibt separat zu qualifizieren.
Danach folgen eingefrorene Modellpiloten und die im Design vorgesehene
kontrollierte Studie auf neuen Aufgaben. Private Lösungsquote, Prozessraten und
Zeit-/Tokenaufwand dürfen nicht aus diesen mechanischen Abnahmen abgeleitet werden.

## Verifikation des Ausgangsstands

- Neue Reihe: **98 gesammelt, 32 bestanden, 66 rot**; keine Collectionfehler.
- Rote Einstiege: 64-mal fehlender `TeamController`, zweimal nicht unterstützte Designversion 6.
- Bestehende Laufverwaltung und v5-Abnahmen: **27 bestanden**.
- Ruff für alle neuen Python-Dateien erfolgreich; `git diff --check` ohne Befund.
