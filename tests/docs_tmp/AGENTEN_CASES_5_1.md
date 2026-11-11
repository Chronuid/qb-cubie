# EBT-Abnahmecases: Gemeinsamer Unterbau (§5, Schritt 1)

> Phasenbezogener Entwicklungsnachweis. Zahlen, Rotphasen und offene Folgearbeiten
> beziehen sich auf den jeweils beschriebenen Stand. Einordnung und spätere
> Nachweise: [Übersicht](README.md). Befehle werden aus der Repositorywurzel ausgeführt.

Stand: 10. November 2026. **Gemeinsamer Unterbau implementiert und offline geprüft;
die ursprüngliche Rotphase bleibt unten dokumentiert.** Die **97 ursprünglichen
Cases** unter [ollama_agents](../ollama_agents) konkretisieren den gemeinsamen Unterbau der
[Rollen- und Ablaufbeschreibung](../../experiments/ollama-agents/README.md).
Mit zwölf ergänzenden Gegenproben bestehen jetzt **109 Cases**.
Die Implementierung liegt unter [examples/ollama-agents](../../examples/ollama-agents/README.md).
Das historische Ollama-Beispiel und seine Archive bleiben unverändert.

Die Schnittstellen werden erst während eines Tests aufgelöst. Fehlender
Produktcode würde einen regulären Testfehlschlag mit explizitem Hinweis auf
§5.1 verursachen; Sammlung und Import der bestehenden Tests funktionieren
weiterhin. Die ursprünglichen Verträge wurden für die Umsetzung nicht
abgeschwächt. Die Cases sind weder übersprungen noch als `xfail` markiert.

## Kriterienzuordnung

| Kriterium und Konzeptbezug | Cases und beobachtetes Verhalten |
| --- | --- |
| Offline-Replays, Ollama-Client, Schemas (§2.2, §5.1) | [test_client_replays.py](../ollama_agents/test_client_replays.py): korrekter POST mit festem Modell, Optionen, `stream=false`, `think=false`, Nachrichten, JSON-Schema und Timeout; validierte Aktion, Tokenwerte und Rohantwort bleiben erhalten. |
| Fehlformate und Längenabbruch (§2.2, §5.1) | Ungültiges JSON/UTF-8, falsche Antworttypen, fehlende Inhalte, falsche Rolle, unvollständiger Abschluss, unbekannter Abschlussgrund, Modellwechsel, Schemafehler, Markdown, doppelte JSON-Schlüssel und nichtendliche Zahlen werden abgewiesen. `done_reason=length` scheitert auch bei syntaktisch vollständigem Aktions-JSON. Kein stilles Abschneiden, Reparieren, Typumwandeln oder zusätzlicher HTTP-Aufruf. |
| Timeout und Fehlerklassifikation (§2.3–2.4, §5.1) | Transporttimeout → `agent_timeout`; Provider-/Transportausfall → `infrastructure_error`; Format-/Rechtefehler → `invalid_output`; ausgeschöpfte interne Grenzen → `budget_exceeded`. Nichtpositive HTTP-Zeit verhindert bereits den Transportstart. |
| Verbotene Pfade und explizite Rechte (§2.1, §5.1) | [test_workspace_policy.py](../ollama_agents/test_workspace_policy.py): absolute Pfade, Traversal, Pfadalias, nicht freigegebene private Referenzen und Archive scheitern beim Lesen, Schreiben und Hashen. Auch eine explizite Freigabeliste darf absolute oder ausbrechende Ziele nicht legitimieren. |
| Symlink-Eltern und erneute Prüfung (§2.1, zusätzliche Gegenproben in §5) | Sowohl Blatt- als auch Elternsymlink werden trotz ausdrücklicher Freigabe abgewiesen. Ein erst nach Erzeugung der Policy ausgetauschter Elternpfad wird vor dem Zugriff erneut geprüft. Private Sentinelbytes bleiben unverändert. |
| Phasenrechte und unveränderte Tests (§2.1, §4.1) | Fünf explizite Freigabesätze repräsentieren `test_design`, `red`, `green`, `refactor` und Reviewer-Werkzeuge. Der Unterbau setzt die vorgegebene Dateimenge durch; die spätere automatische Auswahl durch den Rollenadapter ist hier noch nicht Gegenstand. Anweisungen im Quelltext erweitern keine Rechte. |
| Mehrteilige Schreibfehler (§2.1, zusätzliche Gegenproben in §5) | Ein unzulässiges zweites Ziel verhindert sämtliche Änderungen. Ein injizierter I/O-Fehler bei der Veröffentlichung einer weiteren Datei stellt Originalbytes wieder her und entfernt neue Dateien und Verzeichnisse. |
| Bytegenaue Dateihashes (§2.3, §5.1) | Erfolgreicher Mehrdateivorschlag enthält Unicode und CRLF. Die Abnahme vergleicht geschriebene Bytes und unabhängig berechnete SHA-256-Werte. Nach externer Änderung müssen Hashes neu berechnet werden. |
| Zeit- und Aufrufbudget (§2.4, zusätzliche Gegenproben in §5) | [test_budget_ledger.py](../ollama_agents/test_budget_ledger.py): feste Uhr, HTTP-/Werkzeugtimeout aus Restzeit abzüglich Runnerreserve, inklusive Aufrufgrenzen, unabhängige Modell-/Werkzeugzähler und Ablehnung ab Reservegrenze. Phasenwechsel setzt die Episodengrenzen nicht zurück. |
| Verbrauch und frische Sitzungen (§2.3–2.4, zusätzliche Gegenproben in §5) | No-op → Tokenzahl `0`; Kosten bleiben JSON-`null`. Alle initialen und Reparaturaufrufe werden summiert. Ein unbekannter Tokenwert macht die entsprechende Phasensumme unbekannt, ohne die andere Summe zu verlieren. Neue Instanzen teilen weder Uhrbeginn, Zähler noch Verbrauch. |
| Kontextüberlauf und Quellenbindung (§2.4, zusätzliche Gegenproben in §5) | [test_context_boundaries.py](../ollama_agents/test_context_boundaries.py): sortierter sichtbarer Bestand, Pfade/Inhalte/Hashes, erneutes Lesen geänderter Quellen, ungültiges UTF-8, verbotene explizite Nachladeziele und Quellanweisungen als Daten. Kapazität berücksichtigt Kontextmetadaten, UTF-8-Bytes, Prompt und getrennte Ausgabereserve; exakte Grenze besteht, ein Byte darüber scheitert ausdrücklich. |
| Belegprotokoll und getrenntes Archiv (§2.3, §5.1) | [test_evidence_replays.py](../ollama_agents/test_evidence_replays.py): Anfrage, Rohantwort, Aktion bzw. Validierungsfehler, Werkzeugergebnis, Dateihashes, Dauer und Verbrauch werden vollständig archiviert. Jedes Manifest wird gegen alle tatsächlichen Archivdateien unabhängig nachgehasht. |
| Begrenzte Diagnosen und frische Archive (§2.3, zusätzliche Gegenproben in §5) | Kein stdout; stderr nennt Archivkennung und Manifesthash. Mehr als 4 MiB Rohbeleg bleiben im Archiv, Diagnosen unter 64 KiB. Archive innerhalb des Workspaces oder über dorthin führende Elternsymlinks scheitern. Zwei Sitzungen behalten getrennte Belege. |
| Zusammenspiel des Unterbaus (§5.1) | Ein kombinierter Replay führt Modellbudget, echten Client, explizite Schreibfreigabe, geschriebenen Dateistand, Verbrauch und externes Belegmanifest zusammen. Die Abnahme prüft Dateibytes und archivierte Aktion erneut unabhängig. |
| Ergänzende Gegenproben der Implementierung | [test_transport_and_recovery.py](../ollama_agents/test_transport_and_recovery.py): tatsächlicher Standardbibliothek-Transport mit ersetztem `urlopen`, eingepackter Timeout, HTTP-Ausfall und abgebrochener Response; Fehlerverbrauch und Rohantwort, verlustfreie Archivierung ungültiger UTF-8-Bytes und ungepaarter Unicode-Surrogate, Ablehnung nicht unterstützter Schemas vor Inferenz, Rücknahme einer bereits neu angelegten Datei, ungültige Textkodierung vor dem ersten Write und manipulationsgeschützte Finalisierung. |

## Implementierte Schnittstelle

Ein kleines Einstiegsmodul `examples/ollama-agents/common.py` exportiert die
folgenden aufrufbaren Fabriken. Die Implementierung ist nach Verantwortlichkeit
im Unterpaket `ollama_agents` aufgeteilt und verwendet nur die Standardbibliothek.
Die hier gewählten Methoden und Rückgabeformen gehören zum eigenständigen
Beispiel und erweitern nicht die öffentliche Cubie-API.

### Client und Fehler

```python
OllamaClient(endpoint, model, options, think, transport)
client.chat(messages=..., schema=..., timeout=...)
# {"action": <validiertes JSON>, "usage": {...}, "raw": <Ollama-Antwort>}
```

Die Transportgrenze nimmt `urllib.request.Request` sowie das Schlüsselwort
`timeout` entgegen und liefert HTTP-Antwortbytes. Ausschließlich diese externe
Grenze wird durch [ReplayTransport](../ollama_agents/conftest.py) ersetzt. Er
zeichnet Requests auf und liefert vorbereitete Antworten oder Ausnahmen; er
enthält keine Adaptervalidierung oder Reparaturlogik. Der Client erzeugt den
Request, dekodiert und validiert die Antwort selbst.

Das minimale Aktionsschema der Cases erlaubt ein nichtleeres `files`-Objekt mit
Stringinhalten und verbietet zusätzliche Felder. Damit wird lokale
Schemavalidierung geprüft, ohne bereits die rollenabhängigen Werkzeug- und
Abgabeaktionen festzulegen. Die Transportfunktion führt keine Wiederholungen
aus. Die spätere gesteuerte Modellkorrektur ist Aufgabe des Rollenablaufs.

Erwartete Adapterfehler sind `ValueError`-Unterklassen mit einem `status`-Attribut
und verständlicher Meldung. Die Cases prüfen den Status exakt und passende
Begriffe in der Meldung, ohne einen vollständigen Meldungstext vorzuschreiben.
`usage` enthält stets `input_tokens`, `output_tokens`, `cost`. Fehlende Messungen
bleiben `None`; boolesche, negative, gebrochene oder als String gelieferte
Tokenzahlen sind ungültig. Es wird kein lokales Kostenmodell erfunden.

### Workspace und Kontext

```python
WorkspacePolicy(root=..., readable=[...], writable=[...])
policy.read_file(relative_path)           # unveränderte bytes
policy.write_files({relative_path: text}) # {Pfad: SHA-256 der geschriebenen Bytes}
policy.artifact_hashes([relative_path])   # frisch vom Dateisystem gelesen

ContextBuilder(policy=...)
context.inventory()                      # sortierte Liste {path, sha256}
context.build(paths=..., max_bytes=..., prompt_bytes=..., output_reserve_bytes=...)
# {"files": [{"path": ..., "sha256": ..., "content": ...}], "truncated": False}
```

Die Dateimengen sind explizite relative Einzelpfade. Sie vergeben keine Rechte
auf Eltern oder Geschwister. Writes kodieren Text als UTF-8 ohne
Zeilenendentransformation. Der Mehrdateivorschlag wird vollständig geprüft,
bevor Dateien oder Verzeichnisse angelegt werden. Für den deterministischen
I/O-Gegenfall ist `os.replace` die injizierbare Grenze beim Veröffentlichen
vorbereiteter Dateien. Geprüft wird das Zurückrollen behandelbarer Fehler im
laufenden Prozess; ein Stromausfall oder konkurrierende fremde Prozesse werden
dadurch nicht simuliert. Die Adaptergrenze ist weiterhin keine OS-Isolation.

Der Kontext-Byteumfang ist für diese Cases die UTF-8-Länge des vollständigen
Ergebnisobjekts unter
`json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))`.
Promptbytes und Ausgabereserve kommen hinzu. Das ist eine deterministische
Aufnahmegrenze für den Unterbau, keine Behauptung über Ollamas Tokenisierung.
Die Modellkontextgröße muss später separat kalibriert werden. Die erste
Umsetzung lehnt Überlauf ab; markierte Teilkontexte und begrenzte nachladbare
Werkzeugausgaben können später separat ergänzt werden.

### Budget und Belege

```python
BudgetLedger(wall_time_seconds=..., max_model_calls=..., max_tool_calls=...,
             reserve_seconds=..., clock=...)  # monotone Uhr, bei Erzeugung gestartet
budget.claim_model()                        # erlaubt Aufruf; liefert Resttimeout
budget.claim_tool()                         # separater Zähler; liefert Resttimeout
budget.record_usage(input_tokens=..., output_tokens=...)
budget.usage()                              # aktueller Phasenverbrauch
budget.begin_phase()                        # nur Phasenverbrauch zurücksetzen

EvidenceWriter(archive_root=..., workspace=...)
writer.record_step(phase=..., request=..., raw_response=..., action=...,
                   tool_result=..., artifact_hashes=..., duration_seconds=...,
                   usage=..., status=...)
writer.finalize()                           # archive_id, manifest_path, manifest_sha256
```

`claim_*` verbraucht je einen internen Aufruf vor dessen Ausführung. Timeouts
verwenden die verbleibende Episodezeit abzüglich Runnerreserve. Eine Reparatur
verbraucht denselben Zähler wie der Erstversuch. Es gibt hier keine behauptete
harte Token- oder Kostenbegrenzung. Die Uhr und Limits werden durch
`begin_phase()` nicht erneuert.

Jeder Writer erhält unter dem externen `archive_root` sein eigenes Archiv.
Das Manifest enthält `schema_version=1`, `archive_id`, eine geordnete `steps`-Liste
mit relativen JSON-Dateipfaden und `artifact_hashes` für sämtliche Belegdateien.
Das Manifest selbst wird über den zurückgegebenen `manifest_sha256` gebunden.
Die Schrittdaten werden vollständig gespeichert, auch bei `invalid_output` und
`action=None`. `finalize()` nennt Archivkennung und Manifesthash auf stderr;
stdout bleibt für das spätere JSONL-Protokoll frei.

## Abnahme und Grenzen

Die Operationsprüfungen nutzen EBT über den vorhandenen
[`accepted`](../benchmarks/contracts.py)-Helfer und den ergänzten
[`failed`](../ollama_agents/contracts.py)-Helfer. Beide prüfen das Gesamtergebnis
und `traces[0].evaluation is True`. `failed` beobachtet Status und Meldung einer
Adapterausnahme als Rückgabe eines EBT-Targets. Unerwartete Erfolge, falsche
Fehlerstatus und fremde Ausnahmetypen bestehen diesen Vertrag nicht.
Weitere Assertions prüfen Seiteneffekte, Dateihashes und Archivinhalt.

Eine automatische Fixture sperrt Netzverbindungen während sämtlicher Cases,
einschließlich des späteren Modulimports. Sammlung lädt den Adapter überhaupt
nicht. Es wird weder Ollama gestartet noch ein Modell benötigt. Die Replays
sind synthetische Transportbeispiele und keine neuen Modellmessungen.

```bash
.venv/bin/python -m pytest tests/ollama_agents --collect-only -q
.venv/bin/python -m pytest tests/ollama_agents -q --tb=short
.venv/bin/python -m ruff check examples/ollama-agents tests/ollama_agents
.venv/bin/python -m mypy --check-untyped-defs --warn-unreachable examples/ollama-agents
```

**Ursprüngliche Rotphase:** Die Sammlung fand **97 Cases** ohne Import-/Sammlungsfehler. Der Testlauf
ergab **97 erwartete Fehlschläge**, weil `common.py` noch fehlte. Ruff bestand.
Der JUnit-Bericht wurde darauf geprüft, dass sämtliche Fehlschläge ausschließlich
an diesem expliziten Fehlstand scheitern, ohne Fehler bei Fixture-Aufbau oder
Sammlung. Die gesamte Repositorysammlung findet **1977 Tests** ohne Fehler.
Ein ergänzender Lauf der bestehenden Protokollverträge und EBT-Rückgabeverträge
(`tests/benchmarks/test_protocol_contracts.py` und
`tests/tests_ebt/test_ebt_contract_returns.py`) besteht mit **66 Tests**.

**Nach Implementierung:** Alle **109 Cases** bestehen, darunter unverändert die
97 ursprünglichen Abnahmen und zwölf zusätzliche Gegenproben. Ruff für Beispiel
und Tests sowie Mypy mit `--check-untyped-defs --warn-unreachable` für alle zwölf
Python-Dateien des Beispiels bestehen. Pylint meldet keine unerreichbaren
Anweisungen. Es wurde kein Modell aufgerufen.

Das ausführbare Offline-Beispiel aus der README wurde zusätzlich in ein fremdes
temporäres Verzeichnis kopiert und dort mit `python -I -S` ausgeführt. Es benötigt
weder den Checkout noch Drittanbieterpakete oder einen Cubie-Import. Die
Funktionskörper des Beispiels erfüllen ebenfalls die 12-Zeilen-Regel; seine
Docstrings sind einzeilig. Dies ist ein Standalone-Nachweis für den Unterbau,
kein vorgezogener Wheel- oder Rollen-Smoke-Nachweis aus Schritt 4.

Der vollständige Repositorylauf mit `.venv/bin/python -m pytest -q` besteht mit
**1974 bestandenen Tests, 14 bestehenden Skips und sechs bestehenden Warnungen**
in 455,32 Sekunden. Dieser Lauf wurde vor der letzten zusätzlichen
Unicode-Gegenprobe gestartet. Der abschließende gezielte Lauf prüft den finalen
Unterbau einschließlich dieser Gegenprobe mit **109 bestandenen Cases**.
`git diff --check` ist ohne Befund.

Rollensteuerung, einmalige Modellkorrektur je Arbeitsauftrag, begrenzte
Testwerkzeugprozesse, JSONL-Handshake und Abschlussereignisse, versionierte
Prompts/Modellmetadaten, Reviewer-/Developer-Smoke-Sets und Wheel-Installation
gehören zu den folgenden Umsetzungsschritten und werden hier nicht als
abgenommen ausgewiesen.
