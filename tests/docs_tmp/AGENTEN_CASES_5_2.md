# EBT-Abnahmecases: Reviewer-Durchstich (§5, Schritt 2)

> Phasenbezogener Entwicklungsnachweis. Zahlen, Rotphasen und offene Folgearbeiten
> beziehen sich auf den jeweils beschriebenen Stand. Einordnung und spätere
> Nachweise: [Übersicht](README.md). Befehle werden aus der Repositorywurzel ausgeführt.

Stand: 10. November 2026. **Reviewer-Kern implementiert und offline geprüft.** Die 68 ursprünglichen Cases unter
[ollama_agents/reviewer](../ollama_agents/reviewer) konkretisieren Schritt 2 aus
[AGENTEN_KONZEPT.md](../../docs/misc/AGENTEN_KONZEPT.md#5-umsetzung-und-abnahme).
Sie ergänzen die [Unterbau-Abnahme](AGENTEN_CASES_5_1.md).

Alle 68 ursprünglichen Cases bestehen unverändert. Zwölf zusätzliche Gegenproben
prüfen ungültige Anfragen, den Ablauf der Episodenzeit nach einer Modellantwort,
den Austausch einer Quelle durch einen Symlink, archivierte Validierungsfehler
und die tatsächliche Beendigung eines hängenden Testprozesses. Damit bestehen
**80 Reviewer-Cases und 109 Unterbau-Cases**, insgesamt **189 Cases**.
Die ursprüngliche Rotphase bleibt unten dokumentiert. Historische Beispiele
und die öffentliche Cubie-API bleiben unverändert.

## Neue Aufgaben und unabhängige Erwartungen

Die Aufgabenfamilie **Markup-Text** enthält zwei neue kleine vollständige
Quellstände. `renderer.py` verwendet `escaping.escape_text`; beide Module,
`task.md` und die sichtbaren Tests gehören zum exportierten Kontext.

| Fall | `markup_escaping` | `unicode_preserved` | Konkreter Nachweis |
| --- | --- | --- | --- |
| Konform | `pass` | `pass` | `A&B` → `<span>A&amp;B</span>`, `<&>` → `<span>&lt;&amp;&gt;</span>`, `&amp;` → `<span>&amp;amp;</span>`; Unicode, Leerzeichen, Zeilenumbrüche und Anführungszeichen bleiben erhalten. |
| Fehlerhaft | `fail` | `pass` | `escape_text` maskiert `&` nicht. Tatsächlich ergibt `A&B` den Text `<span>A&B</span>`. Die Ursache liegt im Hilfsmodul, die Auswirkung wird über `render` beobachtet. |
| Fehlende fachliche Evidenz | `abstain` | `pass` | Eine separate Laufvariante lässt die fachliche Vorgabe zur Zeichenmaskierung ausdrücklich offen. Enthaltung bleibt eine fachliche Entscheidung im abgeschlossenen Bericht. |

Die sichtbaren Tests prüfen Unicode und spitze Klammern. Sie bestehen bei beiden
Quellständen; die fehlerhafte Variante darf dadurch keine automatische Freigabe
erhalten. Die Gegenproben in
[test_fixture_oracles.py](../ollama_agents/reviewer/test_fixture_oracles.py)
prüfen die konkreten Ein-/Ausgaben unabhängig mit EBT und führen die sichtbaren
Testfunktionen tatsächlich aus.

Die Fixtures liegen unter
[fixtures](../ollama_agents/reviewer/fixtures). Dateien mit `.txt` werden erst im
Test nach Python-Dateien materialisiert; dadurch sammelt pytest die eingebetteten
sichtbaren Beispiele nicht als Repositorytests. Nur `fixtures/visible` wird
exportiert, für den Fehlerfall wird ausschließlich `escaping.py` ausgetauscht.
`reference.json` und `semantic_paraphrase.json` bleiben außerhalb des Workspaces.
Die Referenzen sind bewusst veröffentlichte Entwicklungsfixtures, keine
unabhängige menschliche Referenzaufnahme und keine zurückgehaltenen Messfälle.

## Kriterienmatrix

| Konzeptbezug | Cases und verbindliche Beobachtung |
| --- | --- |
| Neue konforme/fehlerhafte Fälle (§5.2, §3.1) | [test_decisions.py](../ollama_agents/reviewer/test_decisions.py): vollständiges `review_v1`, beide Kriterien, konkrete Quellen und Befunde, unveränderte Originalbytes. `pass` und `fail` können jeweils erfolgreich abgeschlossene Reviews sein. |
| Enthaltung (§3.1–3.2, §5.2) | `abstain` bleibt im Bericht erhalten und wird weder `fail` noch `pass`. Die RBT-Gegenprobe bestätigt: Nur ausschließlich `pass` ergibt `ReviewData(passed=True)`. |
| Vollständige Kriterien und Befunde (§3.1–3.2) | Fehlende/fremde Kriterien, unbekannte Entscheidungen, `fail` ohne Befund, Widerspruch zwischen `pass` und Befund, unbekannte Pfade/Symbole sowie leere Ursachen/Auswirkungen werden abgewiesen. |
| Tatsächlicher vollständiger Kontext (§2.4, §3.2, §5.2) | [test_sources.py](../ollama_agents/reviewer/test_sources.py): Inhalte und unabhängig berechnete Hashes sämtlicher Originaldateien müssen in den tatsächlichen HTTP-Modellnachrichten stehen. Dieselben Nachrichten müssen im Belegarchiv liegen. |
| Quellenliste (§3.2) | Leere/partielle Quellen, fehlende `task.md`, Duplikate, privater Pfad oder `review.json` als Quelle sind ungültig. Die Reihenfolge der Quellen ist kein fachliches Kriterium; die Replays reichen die vollständige sortierte Liste ein. |
| Quelländerung (§3.1, §5.2) | Während der Inferenz geänderte Quellen oder Aufträge, entfernte Dateien und neu hinzugefügte Dateien blockieren die Veröffentlichung. Es entsteht kein `review.json`; externe Änderungen werden nicht zurückgeschrieben. Zusätzlich weist der bestehende unabhängige Runner veränderte Quellhashes zurück. |
| Sichtbarkeitsgrenzen (§2.1, §2.4) | Private Geschwisterdateien erscheinen nicht im Modellkontext. Symlink-Quellen und ungültiges UTF-8 scheitern vor der Inferenz. Kontextüberlauf wird als `budget_exceeded` ohne Modellaufruf gemeldet. |
| Lokale Werkzeuge (§3.1) | [test_tools.py](../ollama_agents/reviewer/test_tools.py): `list_files`, `read_file` und `search_text` liefern reale sichtbare Ergebnisse zurück ins Modell und ins Belegarchiv. |
| Testausführung in Kopie (§3.1) | `run_visible_tests` führt die sichtbaren Tests tatsächlich aus. Beide Varianten melden zwei bestandene Beispiele. Eine zusätzliche Gegenprobe verändert in der Testkopie absichtlich Quellcode und erzeugt eine Markerdatei; Originalbaum, Caches und Originalhashes bleiben unverändert. |
| Keine Reviewer-Schreibrechte (§2.1, §3.1) | Schreibaktionen, private/absolute Leseziele und frei vorgegebene Shellkommandos sind ungültig. Anweisungen in Quellkommentaren erweitern keine Rechte. Nur der Adapter darf abschließend `review.json` veröffentlichen. |
| Einmalige Korrektur (§2.4) | [test_recovery.py](../ollama_agents/reviewer/test_recovery.py): konkreter Validierungsfehler geht an genau einen Korrekturaufruf; zweiter Fehlversuch endet ohne dritten Aufruf. Fehlantwort und gültige Abgabe bleiben archiviert. |
| Fehler und Budgets (§2.3–2.4, §3.1) | Timeout → `agent_timeout`, Providerausfall → `infrastructure_error`, wiederholt ungültige Ausgabe/Längenabbruch → `invalid_output`, ausgeschöpftes Modell-/Werkzeugbudget → `budget_exceeded`. Keine Unterbrechung wird als abgeschlossene Enthaltung ausgegeben. Reparaturen teilen dieselben Grenzen. |
| Verbrauch und Artefakte (§2.3) | Tokenverbrauch summiert Erstversuch und Reparatur; fehlende Messung bleibt `null`, Kosten bleiben `null`. Das Abschlussereignis erfüllt den vorhandenen Protokollvalidator, nennt genau `review.json` und den unabhängig nachgehashten tatsächlichen Dateistand. Die Reviewmethode schreibt nichts auf stdout. |
| Semantisch gleichwertige Befunde (§3.3, §5.2) | Freie Formulierungen bleiben unverändert. Die unabhängige Evaluator-Gegenprobe zeigt für die deutsche Paraphrase korrekte Kriterienentscheidungen, aber exakte Precision/Recall von `0.0`. Das ist kein semantisches Urteil; das separate Nachbewertungsverfahren steht unten. |

## Implementierter Adaptervertrag

Die Schnittstelle wird erst während der Testausführung aufgelöst. Sammlung und
bestehende Unterbau-Cases benötigen den Reviewer nicht. Das Beispiel stellt den
aufrufbaren Einstieg `ReviewerAdapter` in `examples/ollama-agents/reviewer.py`
bereit. Dieser Vertrag betrifft nur das eigenständige Beispiel, nicht
die öffentliche Cubie-API:

```python
ReviewerAdapter(client=..., budget=..., evidence=..., context_max_bytes=65536)
adapter.review(request)  # genau ein öffentliches v1-Abschlussereignis als dict
```

`client`, `budget` und `evidence` sind echte Instanzen des bestehenden Unterbaus.
`request` ist eine reguläre v1-Reviewanfrage mit absolutem Workspacepfad,
Auftrag, Kriterien, `review_v1` und Runnerbudgets. Der Adapter erfasst den
sichtbaren Bestand pro Anfrage selbst; die Tests geben keine Lesefreigabeliste
und keine Referenz an den Reviewer weiter. Im kleinen Erstkontext werden alle
Originale einschließlich Metadaten aufgenommen oder der Kontext wird vollständig
abgelehnt. Das bereits vom Unterbau berechnete Budget enthält Prompt und
Ausgabereserve; 65536 Bytes sind hier eine Aufnahmegrenze, keine Tokenmessung.

Die Modellantworten verwenden die folgenden internen Aktionen:

```json
{"action": "list_files"}
{"action": "read_file", "path": "escaping.py"}
{"action": "search_text", "query": "escape_text"}
{"action": "run_visible_tests"}
{"action": "submit_review", "review": {"schema_version": 1, "criterion_results": {}, "findings": [], "sources": []}}
```

Das letzte Beispiel zeigt nur die Aktionshülle; leere Kriterien und Quellen
sind keine gültige Abgabe. Keine Aktion nimmt Shelltext oder Schreibziele an.
Werkzeugaktionen liefern Ergebnisse an einen weiteren Modellschritt zurück.
Die Syntax des Aktionsschemas wird durch den echten `OllamaClient` validiert;
der Rollenadapter prüft zusätzlich Kriterien, Befundquellen, Symbole und
unveränderte Originalhashes. Der Testwerkzeugbeleg enthält mindestens
`exit_code`, `stdout` und `stderr`; die feste pytest-Ausführung muss für die
Seiteneffektgegenprobe auch ausgegebenen Text erfassen, etwa mit `-s`.
Werkzeugbelege bleiben im existierenden `record_step`-Format. Die Archivprüfung
verwendet den bereits vorhandenen unabhängigen Manifestprüfer aus §5.1.

Bei einem korrigierbaren Format-/Aktions-/Berichtsfehler erlaubt ein
Arbeitsauftrag genau eine Modellkorrektur. Bei erneutem Fehler lautet der
Abschlussstatus `invalid_output`. Pfad-/Schemafehler werden ohne Ausführung der
verbotenen Aktion korrigierbar zurückgewiesen. Quelländerungen, Transportfehler
und Budgetabbrüche werden direkt beendet. Fehlereignisse enthalten einen
nichtleeren `reason`, leere `artifacts`/`artifact_hashes` und kein veröffentlichtes
`review.json`. Verbrauch bleibt unabhängig vom fachlichen Ergebnis erhalten.

Nur die externe HTTP-Transportgrenze wird mit `ReplayTransport` ersetzt.
Der Replay parst keine Antworten, validiert keine Reviews, entscheidet nicht
über Quellen und simuliert keine lokalen Werkzeugergebnisse. Eine geerbte
automatische Fixture sperrt Netzverbindungen auch beim späteren Adapterimport.

## Separate semantische Nachbewertung

Der bestehende Evaluator vergleicht weiterhin alle fünf Finding-Felder exakt.
Der Case `test_semantic_paraphrase_keeps_correct_decisions_but_exact_match_scores_zero`
führt diesen Evaluator tatsächlich aus. Er bestätigt gleichzeitig korrekte
Kriterienentscheidungen, unveränderte freie Befunde und null exakte Treffer.
Weder der Adapter noch die Tests sollen Formulierungen auf Referenztexte
umschreiben oder diese dem Modell vorlegen.

Für spätere echte Reviews wird eine separate Datei `review-adjudication-v1.json`
außerhalb des sichtbaren Workspaces geführt. Folgende Vorlage ist ein manueller
Arbeitsvertrag, keine neue Runnerfunktion und kein bereits erhobenes Urteil:

```json
{
  "schema_version": 1,
  "rubric_version": "review-semantic-v1",
  "assessment_id": "<verblindete Kennung>",
  "evaluation_status": "pending_adjudication",
  "submission_sha256": "<Hash der unveränderten review.json>",
  "reference_sha256": "<Hash der unabhängig erhobenen Referenz>",
  "source_hashes": {"<Quellpfad>": "<SHA-256>"},
  "exact_matcher": "criterion_id,path,symbol,mechanism,impact",
  "matches": [],
  "unmatched_submission_findings": null,
  "unmatched_reference_findings": null,
  "adjudicator_id": null
}
```

Eine Person erhält Quellen, Auftrag, unveränderte Befunde und die unabhängige
Referenz ohne Agentenidentität oder Modellkonfiguration. Ein semantischer Treffer
verlangt dasselbe Kriterium, dieselbe Fehlerstelle, denselben ursächlichen
Mechanismus und dieselbe fachliche Auswirkung; reine Wortähnlichkeit genügt
nicht. Ein Referenzbefund darf nur einmal zugeordnet werden. Jede Zuordnung
nennt Einreichungs-/Referenzindex und eine Begründung; unzugeordnete Befunde und
übersehene Referenzfehler werden getrennt festgehalten. Erst nach abgeschlossener
Zuordnung werden `evaluation_status="complete"`, die offenen Indexlisten und
`adjudicator_id` eingetragen. Originalbericht und exakte Metriken bleiben erhalten.

Die deutsche Entwicklungsparaphrase in
[semantic_paraphrase.json](../ollama_agents/reviewer/fixtures/semantic_paraphrase.json)
beschreibt denselben fehlenden Ampersand-Ersatz und dieselbe Wirkung wie die
englische Referenz. Sie ist ein vorab konstruiertes Zuordnungsbeispiel; eine
unabhängige verblindete menschliche Bewertung wird hier nicht behauptet.

## Ausführung und Ergebnis

```bash
.venv/bin/python -m pytest tests/ollama_agents/reviewer --collect-only -q
.venv/bin/python -m pytest tests/ollama_agents/reviewer -q --tb=short
.venv/bin/python -m pytest tests/ollama_agents/reviewer/test_fixture_oracles.py -q
.venv/bin/python -m pytest tests/ollama_agents --ignore=tests/ollama_agents/reviewer -q
.venv/bin/python -m ruff check tests/ollama_agents/reviewer
```

**Ursprüngliche Rotphase:** Die initiale Sammlung fand **68 Cases ohne Import-/Sammlungsfehler**.
Der damalige Lauf ergab **17 bestandene Gegenproben und 51 erwartete Fehlschläge** am
expliziten Fehlstand des Reviewer-Einstiegs. Der JUnit-Bericht bestätigt, dass
keine anderen Fehlerursachen, Fixturefehler oder Skips vorkommen. Die **109
bestehenden Unterbau-Cases** bestehen weiterhin. Die gesamte Repositorysammlung
findet **2057 Tests ohne Fehler**. Ruff und `git diff --check` bestehen.
Es wird kein Modell geladen oder kontaktiert.

**Nach Implementierung:** Alle 189 Agenten-Cases bestehen. Weitere 66 bestehende
Protokoll- und EBT-Rückgabeverträge bestehen ebenfalls. Ruff für Beispiel und
Tests, Mypy für alle 18 Beispieldateien sowie Pylint auf unerreichbaren Code
bestehen. Die neuen Funktionskörper halten die 12-Zeilen-Regel ein.
Der Reviewer-Kern ist damit offline abgenommen; es erfolgte kein Modellaufruf.
JSONL-Prozessstart und tatsächliche Ereignisemission, Handshake/Modellnachweis,
versionierte Prompts, Agenten-TOML, exportierbare Benchmark-Smoke-Sets sowie
Wheel-Installation und echte lokale Modellläufe sind damit noch nicht geprüft.
Die hier angelegten kleinen Quellen dienen als Grundlage der späteren Smoke-Sets.

Ein separater, ausdrücklich freizuschaltender
[EBT-Smoke mit echten Ollama-Aufrufen](../live_ollama/README.md) ergänzt inzwischen
die Offline-Abnahme. Am 10. November 2026 bestanden beide neuen Rendererfälle
mit `gemma4:12b`; beim konformen Fall wurde eine Modellkorrektur benötigt.
Die noch unzureichend konkrete Auswirkungsbeschreibung im Fehlerfall ist dort
als Grenze dokumentiert. Dies ersetzt weder die semantische Nachbewertung noch
die ausstehende JSONL-/Wheel-Abnahme.

Die anschließende Überarbeitung `reviewer-v2` schließt die beobachtete Lücke bei
reinen Schweregradangaben: Fünf zusätzliche EBT-Cases prüfen Ablehnung und
Korrektur solcher Nicht-Erklärungen. Damit bestehen 85 Reviewer-Cases und 109
Unterbau-Cases, insgesamt 194 Offline-Cases. Der echte EBT-Vertrag verlangt jetzt
auch konkrete Maskierungsbelege im Auswirkungstext; Entscheidungen und Quellen
allein reichen für den Smoke nicht mehr aus.

Ein weiterer [echter Pipeline-EBT](../live_ollama/test_benchmark_rbt_live.py) verbindet
inzwischen den öffentlichen Benchmark-Runner über den neuen JSONL-Prozess mit
Ollama, der unabhängigen Evaluation und der tatsächlichen RBT-Aufzeichnung.
Er prüft eine konforme Episode samt Modellmetadaten und Manifesthashes. Fünf
Offline-Gegenproben sichern den Prozess-Handshake, unveränderte Arbeitsverzeichnisse,
veraltete Konfigurationen und JSONL-Eingabegrenzen ab. Damit bestehen 199
Offline-Agenten-Cases. Der zuvor offene Reviewer-Prozessanschluss ist dadurch für
diesen einen Fall nachgewiesen; Wheel- und vollständige Smoke-Set-Abnahme bleiben
weiterhin offen.
