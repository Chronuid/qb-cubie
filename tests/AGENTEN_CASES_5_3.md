# EBT-Abnahmecases: Developer-Durchstich (§5, Schritt 3)

Stand: 10. November 2026. **Developer-Kern implementiert und offline geprüft.**
Die [36 neuen Cases](ollama_agents/developer) konkretisieren den Developer-Durchstich
in [AGENTEN_KONZEPT.md](../docs/AGENTEN_KONZEPT.md#5-umsetzung-und-abnahme)
und die Regeln aus §4.1–4.3. Sie ergänzen die Unterbau- und Reviewer-Abnahme.
Die ursprüngliche Rotphase bleibt unten dokumentiert. Der Produktionsadapter
erfüllt inzwischen alle ursprünglichen Cases; der Prozessanschluss bleibt Folgearbeit.

## Aufgabe und unabhängiges Orakel

Das kleine neue Projekt besteht aus `pricing/__init__.py`, `pricing/policy.py`,
`task.md` und einer vorhandenen `README.md`. Es prüft damit auch, dass der
Adapter Produktionscode in einem Paket findet. Der sichtbare Auftrag verlangt
`fee(amount)` für ganzzahlige Beträge:

| Eingabe | Erwartung |
| --- | --- |
| 0, 99 | 7 |
| 100, 101 | 0 |
| -1, -100 | `ValueError` |

Der Ausgangsstand gibt immer 7 zurück. Er ist importierbar und erzeugt fachliches
Rot ohne einen ungefangenen Stubfehler. Die vorgeschlagenen Agententests führen
für jedes Ein-/Ausgabepaar EBT aus und prüfen `trace.evaluation is True`;
Exceptionfälle verwenden `pytest.raises`. Die äußeren Abnahmecases verwenden
die bestehenden EBT-Helfer `accepted` einschließlich Trace-Prüfung.

Ein reparierbarer Vorschlag verwendet `> 100` statt `>= 100`. Ein zweiter
Vorschlag korrigiert ausschließlich Produktionscode und ergänzt `USAGE.md`.
Ein bewusst falsches Testorakel erwartet an der Grenze 100 die Gebühr 7.
Die unabhängigen Gegenproben zeigen beide Richtungen: Dieses Orakel lehnt
korrekten Code ab und akzeptiert den Grenzwertfehler. Die Referenzimplementierung
und das falsche Orakel sind veröffentlichte Entwicklungsdaten in `support.py`,
keine zurückgehaltene Benchmark-Referenz und kein Nachweis von Modellleistung.
Nur der explizit im Replay vorgeschlagene Testinhalt wird in den Workspace
übertragen; Hilfsdateien und Referenzcode sind keine Adaptereingaben.

## Kriterienmatrix

| Kriterium | Ausführbarer Nachweis |
| --- | --- |
| Gültiges Rot einschließlich `pytest.raises` | `test_design_preserves_originals_and_red_is_immutable_noop`: EBT-Grenzfälle und separates reines Exceptionpaket. Originaldateien bleiben bytegleich. `test_real_runner_classifies_business_red_and_execution_errors` führt den vorhandenen pytest-Runner mit echtem JUnit aus. |
| Fachliches Rot von Ausführungsfehlern trennen | Derselbe Runner-Case prüft Syntax-/Importfehler und ungefangenes `NotImplementedError`. Der Adapter-Replay verlangt Testreparaturen bei Syntaxfehlern, Importfehlern und vollständig grünen Tests. |
| Eingefrorene Tests | Nach `test_design` sind Tests in Rot, Grün und Refactor bytegleich. Fremde nachträgliche Teständerungen blockieren Grün vor einem Modellaufruf. |
| Korrigierbarer Implementierungsfehler | `test_green_repairs_locally_without_changing_frozen_tests`: erster Grünvorschlag scheitert an 100; tatsächlicher Testname gelangt in den nächsten HTTP-Modellaufruf und ins Archiv. Zweiter Vorschlag besteht, enthält Nutzungshinweise und verändert keinen Test. |
| Falsches Testorakel sichtbar | `test_false_oracle_remains_visible_and_frozen_on_correct_implementation`: drei korrekte Implementierungsvorschläge scheitern am eingefrorenen falschen Orakel; der letzte zulässige Stand und die roten Grünbelege bleiben erhalten. Kein vierter Vorschlag und keine heimliche Testkorrektur. |
| Verbotene Teständerung sichtbar | `test_forbidden_test_rewrite_rejected_atomically`: kombinierter Test-/Produktionsvorschlag wird in Grün und Refactor vollständig abgewiesen. Nach einmaliger Korrekturchance endet Wiederholung als `invalid_output`. |
| Phasenrechte und Reihenfolge | Bestehende Quellen, README und Auftrag sowie absolute und ausbrechende Pfade sind im Testentwurf verboten. Rot/Grün/Refactor ohne Testentwurf werden vor dem Modellaufruf abgewiesen. |
| Tatsächliche Tests in Kopie | `test_visible_tests_execute_in_copy_with_real_evidence`: die eingereichte Testsuite schreibt beim Import eine Markerdatei. Marker und Testcaches dürfen nicht im Originalprojekt entstehen; Testnamen und Artefakthash müssen im versiegelten Archiv stehen. |
| Belege und öffentliches Ereignis | Jede beobachtete Phase durchläuft EBT und den vorhandenen v1-Ereignisvalidator. Artefakte werden unabhängig aus den geschriebenen Bytes nachgehasht. Die Archivprüfung verwendet den vorhandenen Manifestprüfer. stdout bleibt beim vollständigen Durchlauf leer. |
| Begrenzung und Verbrauch | Zwei Testentwurfsaufrufe verbrauchen das gemeinsame Modellbudget; Grün darf es nicht zurücksetzen. Rot ist ein No-op mit null Tokens. Grünverbrauch enthält auch den gescheiterten Vorschlag; Phasenverbrauch wird getrennt gemeldet. |
| Fehlerstatus | Provider-Timeout und Verbindungsfehler ergeben `agent_timeout` bzw. `infrastructure_error`, kein fachliches Rot. Fehlerereignisse enthalten Begründung und keine Artefakte. |

## Implementierter Adaptervertrag

Der Einstieg wird erst im Testkörper aufgelöst. Es gibt keine Importfehler bei
der Sammlung und kein `skip`/`xfail`, das die fehlende Implementierung versteckt:

```python
# examples/ollama-agents/developer.py
DeveloperAdapter(client=..., budget=..., evidence=..., context_max_bytes=65536,
                 mode="cubie")
adapter.develop(request)  # genau ein v1-Abschlussereignis als dict pro Phase
```

Dies ist ein Vertrag für das Beispiel, keine neue öffentliche Cubie-API.
Client, BudgetLedger und EvidenceWriter stammen unverändert aus dem echten
Unterbau. Eine Adapterinstanz bearbeitet dieselbe Episode über
`test_design → red → green → refactor`; die Anfrage enthält die regulären
v1-Felder, `benchmark="developer_agent"`, `output_format="project_v1"` und
keine erfundenen Runner-Testresultate. Der Modus kommt aus der Konfiguration.

Die minimalen internen Replayaktionen lauten:

```json
{"action": "write_files", "files": {"tests/test_policy.py": "<vollständiger Inhalt>"}}
{"action": "submit_phase"}
```

Ein Schreibvorschlag wird zuerst vollständig auf Schema, Pfade, Phasenrechte
und Python-Syntax geprüft. Zulässige Änderungen werden atomar übernommen;
der Adapter führt die sichtbaren Tests automatisch in einer temporären Kopie
aus. Das echte Ergebnis samt Testnamen, Exitcode, stdout und stderr wird dem
nächsten Modellaufruf und dem Belegarchiv zugänglich. Ein Schreibvorschlag ist
noch kein öffentliches Abschlussereignis. Nach erfolgreicher lokaler Prüfung
beendet `submit_phase` die Phase. Nichtfachliches Rot oder vollständig grüne
Tests dürfen den Testentwurf nicht erfolgreich abschließen.

Ein ungültiger Vorschlag erhält genau eine Korrekturchance mit konkretem
Fehler. Import-/Syntaxfehler werden vor Testabgabe repariert. Der Teststand wird
bei erfolgreicher Testabgabe eingefroren und vor jeder Folgephase kontrolliert.
`red` verändert nichts und benötigt keinen Modellaufruf. Grün erlaubt höchstens
drei Implementierungsvorschläge einschließlich Erstversuch. Ist der dritte
zulässige Vorschlag weiterhin rot, beendet der Adapter die Phase mit dem letzten
Stand ohne zusätzlichen Modellaufruf. `completed` bezeichnet hier die fertige
Abgabe, keine bestandene Prozessabnahme; die archivierte Testausführung bleibt
rot. Das entspricht §4.2. Ein erschöpftes Gesamtbudget endet dagegen als
`budget_exceeded`. Refactor darf mit `submit_phase` unverändert abgeben.

Nur die HTTP-Transportgrenze wird durch den vorhandenen `ReplayTransport`
ersetzt. Tests, Dateiprüfung, Syntaxprüfung, Reparatursteuerung, EBT und Belege
sind keine Replayentscheidungen. Die geerbte automatische Netzsperre gilt auch
beim späteren Adapterimport. Es wird kein Ollama-Modell benötigt oder geladen.
Die Ausführungskopie ist keine OS-Sandbox.

## Ausführung und belegte Rotphase

```bash
.venv/bin/python -m pytest tests/ollama_agents/developer --collect-only -q
.venv/bin/python -m pytest tests/ollama_agents/developer -q --tb=short
.venv/bin/python -m pytest tests/ollama_agents/developer/test_oracles.py -q
.venv/bin/python -m pytest tests/ollama_agents --ignore=tests/ollama_agents/developer -q
.venv/bin/python -m ruff check tests/ollama_agents/developer
```

Ergebnis: **36 Cases ohne Sammlungsfehler**, davon **13 bestanden** und
**23 erwartete Fehlschläge** ausschließlich an der expliziten Prüfung des
fehlenden `examples/ollama-agents/developer.py`. Der JUnit-Bericht wurde auf
Fehlerursachen geprüft; keine Fixturefehler, Skips oder sonstigen Ausnahmen.
Alle **199 bisherigen Offline-Agentencases** bestehen. Ruff besteht.

Die 23 roten Fälle spezifizieren die noch zu implementierende Adapterfunktion;
die 13 grünen Gegenproben belegen bereits heute die Aufgabe und die Grenzen des
bestehenden Runners. JSONL-Prozessanschluss, Modellkonfigurationen, Wheel-Nachweis,
Live-Smoke, weitere Budgets/Grenzfälle und unabhängige private Abnahme bleiben
separate Folgearbeit. Die Rotphase ist keine abgeschlossene §5.3-Implementierung.


## Ergebnis nach Implementierung

Alle **36 ursprünglichen Cases** bestehen unverändert. **Neun zusätzliche
Gegenproben** in [test_boundaries.py](ollama_agents/developer/test_boundaries.py)
prüfen explizite Framework-Dokumentation für beide Modi, null Werkzeugbudget,
fremde Shellaktionen und Zusatzfelder, Symlinks vor Inferenz, unbekannte
Tokenmessungen über weitere Aufrufe, eine reparierte Refactor-Regression und die
fehlende Nutzungsdokumentation nach drei Vorschlägen. Ein vierter
Implementierungsvorschlag wird nicht übernommen. Refactor darf keine roten Tests
als erfolgreiches Verhaltenserhaltungsresultat abgeben.

Damit bestehen **45 Developer-Cases und 199 bisherige Agenten-Cases**, insgesamt
**244 Offline-Cases**. Die Implementierung verwendet eine installierte Cubie-
Version und den existierenden Runner für echte pytest/JUnit-Beobachtungen.
Die Testkopie verwendet isoliertes Python; weder Modellzugriff noch der neue
Produktionsadapter werden durch die Replays ersetzt. Ruff, Mypy für alle
27 Beispieldateien und Pylint auf unerreichbaren Code bestehen.

Der Developer-Kern ist damit offline abgenommen. JSONL-Prozessstart, versionierte
Agenten-TOMLs, Wheel-Installation und tatsächliche Developer-Modellläufe sind
damit noch nicht nachgewiesen. Die unabhängige private Prozess-/Qualitätsabnahme
bleibt beim Benchmark-Runner; eine fertige rote Grünabgabe ist keine Freigabe.

Die gemeinsame Regression mit `tests/ollama_agents tests/benchmarks` ergibt
**785 bestanden, 2 übersprungen**. Der separate abschließende Developer-Lauf
ergibt **45 bestanden**. `git diff --check` besteht.
