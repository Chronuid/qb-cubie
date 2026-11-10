# Gemeinsamer Unterbau für lokale Ollama-Agenten

Dieses eigenständige Beispiel implementiert Schritt 1 aus
[AGENTEN_KONZEPT.md](../../docs/AGENTEN_KONZEPT.md#5-umsetzung-und-abnahme).
Es verwendet ausschließlich die Python-Standardbibliothek und benötigt
Python ab 3.13. Import und Offline-Prüfungen starten weder Ollama noch ein
Modell. Das historische Beispiel unter `../ollama-user-benchmark/` bleibt
unverändert.

`common.py` exportiert sechs Einstiegspunkte:

| Dienst | Aufgabe |
| --- | --- |
| `OllamaClient` | Ein nichtstreamender HTTP-Aufruf mit explizitem Modell, Optionen und JSON-Schema; lokale Ausgabevalidierung und gemessene Tokens. |
| `WorkspacePolicy` | Explizite Lese-/Schreibfreigaben je Datei, Pfad- und Symlinkprüfung, Mehrdateivorschläge mit Rollback und frische Dateihashes. |
| `ContextBuilder` | Sortierter sichtbarer Bestand und vollständige ausgewählte Kontextblöcke mit Pfad, Hash und Text. |
| `BudgetLedger` | Gemeinsame Episodenuhr, Runnerreserve, getrennte Modell-/Werkzeuggrenzen und Phasenverbrauch. |
| `EvidenceWriter` | Vollständige Schrittbelege in einem separaten Archiv mit überprüfbarem Manifest und kurzen stderr-Diagnosen. |
| `AdapterError` | `ValueError` mit `status` und gegebenenfalls Rohantwort und Verbrauch. |

Die Implementierung liegt im Paket `ollama_agents/`. Die Dienste werden vom
späteren Rollenadapter komponiert. Sie führen keine Modellkorrekturschleifen
aus und starten keine frei erzeugten Shellbefehle. Reviewer-/Developer-Prozesse,
Prompts, Agenten-TOMLs und Smoke-Sets folgen in den nächsten Konzeptschritten.

## Offline verwenden

Die folgenden Beispiele werden aus diesem Verzeichnis ausgeführt:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from common import BudgetLedger, ContextBuilder, EvidenceWriter, WorkspacePolicy

with TemporaryDirectory() as temporary:
    root = Path(temporary)
    workspace = root / "workspace"
    workspace.mkdir()
    (workspace / "task.md").write_text("Return a fee of 2.\n", encoding="utf-8")
    policy = WorkspacePolicy(root=workspace, readable=["task.md"], writable=["fee.py"])
    budget = BudgetLedger(wall_time_seconds=30, reserve_seconds=5,
                          max_model_calls=2, max_tool_calls=3)
    context = ContextBuilder(policy=policy).build(
        paths=["task.md"], max_bytes=8192, prompt_bytes=512, output_reserve_bytes=2048,
    )
    evidence = EvidenceWriter(archive_root=root / "archives", workspace=workspace)
    budget.claim_tool()
    action = {"files": {"fee.py": "def fee():\n    return 2\n"}}
    hashes = policy.write_files(action["files"])
    evidence.record_step(
        phase="green", request={"context": context}, raw_response=None, action=action,
        tool_result={"written": sorted(hashes)}, artifact_hashes=hashes,
        duration_seconds=0, usage=budget.usage(), status="completed",
    )
    summary = evidence.finalize()
    assert (workspace / "fee.py").read_bytes() == b"def fee():\n    return 2\n"
```

In einem echten Lauf muss `duration_seconds` aus einer monotonen Zeitmessung
stammen. Das Beispiel verwendet eine Dauer von null für die lokale Demonstration.
Das Archiv muss vor dem Aufräumen temporärer Verzeichnisse dauerhaft gesichert
werden; `finalize()` liefert seinen Manifestpfad und Hash.

## Ollama anbinden

Nur ein ausdrücklicher `chat()`-Aufruf kontaktiert den konfigurierten Server:

```python
from common import AdapterError, OllamaClient

client = OllamaClient(
    endpoint="http://localhost:11434", model="gemma4:12b",
    options={"temperature": 0, "seed": 42, "num_ctx": 16384, "num_predict": 4096},
    think=False,
)
schema = {
    "type": "object", "properties": {"code": {"type": "string"}},
    "required": ["code"], "additionalProperties": False,
}
# Erst nach separater Modellkonfiguration und Vorprüfung ausführen:
# result = client.chat(messages=[{"role": "user", "content": "..."}],
#                      schema=schema, timeout=budget.claim_model())
```

`think=None` lässt die Einstellung ausdrücklich aus, wenn die eingefrorene
Konfiguration sie nicht unterstützt. Es gibt keinen stillen Modellwechsel,
keine Transportwiederholung und keine Reparatur abgeschnittener Ausgabe.
Der Standardtransport begrenzt Antworten auf 32 MiB. Sein Timeout gilt für
die HTTP-Socketoperationen; die harte Episodenzeit bleibt beim Runner.

Der lokale Validator unterstützt Objekte, Arrays und primitive Typen,
`properties`, `required`, `additionalProperties`, `items`, `enum`, `const`,
`anyOf`, `oneOf`, Größen- und Zahlenbounds sowie Python-Regex unter `pattern`.
Unbekannte Schlüssel, etwa `$ref`, werden vor dem Modellaufruf als
Konfigurationsfehler abgewiesen. Es wird kein vollständiger JSON-Schema-Validator
behauptet. Titel, Beschreibung und andere im Code aufgelistete Annotationen
beeinflussen die Validierung nicht.

## Rechte, Budgets und Nachweise

Dateifreigaben verwenden einzelne kanonische relative POSIX-Pfade. Schreibrecht
umfasst keine Eltern oder Geschwister. Hashen ist für lesbare und schreibbare
Dateien erlaubt; `read_file()` benötigt eine ausdrückliche Lesefreigabe.
Symlinks werden auch in Elternverzeichnissen bei jedem Zugriff erneut geprüft.
Das ersetzt keine OS-Isolation für fremden generierten Code.

Alle neuen Inhalte werden vor dem Schreiben geprüft und vorbereitet. Scheitert
eine Veröffentlichung, werden bereits ersetzte Dateien mit ursprünglichem
Dateimodus und Änderungszeit wiederhergestellt und neue Dateien/Verzeichnisse entfernt. Scheitert
auch die Wiederherstellung, meldet der Unterbau `infrastructure_error` mit dem
Pfad der erhaltenen Recoverydateien. Crashkonsistenz und gleichzeitige Änderungen
durch andere Prozesse sind außerhalb dieses lokalen Vertrags.

`claim_model()` und `claim_tool()` verbrauchen Aufrufe vor der Ausführung und
liefern die Restzeit abzüglich Runnerreserve. Der Rollenadapter muss diese Zeit
an den jeweiligen Aufruf weitergeben und jede Antwort einschließlich Reparaturen
mit `record_usage()` erfassen. Bei ungültiger Modellausgabe enthält `AdapterError`
unter `raw` die Antwort und unter `usage` die zuvor ermittelten Tokenwerte.
Fehlende Messungen bleiben unbekannt, ein No-op meldet null Tokens als Zahl `0`.
Kosten sind immer `None`. `begin_phase()` setzt nur den Phasenverbrauch zurück.

Der Kontext hat eine explizite Bytegrenze einschließlich Metadaten, Prompt und
Ausgabereserve. Überlauf wird als `budget_exceeded` gemeldet. Diese Grenze ist
keine Tokenmessung; die nutzbare Modellkontextgröße muss separat kalibriert werden.

Jede Writerinstanz erhält ein eigenes externes Archiv. Schritte und Manifest
werden atomar geschrieben; Finalisierung prüft sämtliche archivierten Hashes.
Auch ungültige Rohbytes lassen sich verlustfrei als Base64-Objekt archivieren.
Ein finales Archiv nimmt keine weiteren Schritte an. stdout bleibt frei;
stderr enthält nur Archivkennung, Manifestpfad und Manifesthash.

## Prüfen

Aus dem Repositorywurzelverzeichnis:

```bash
.venv/bin/python -m pytest tests/ollama_agents -q
.venv/bin/python -m ruff check examples/ollama-agents tests/ollama_agents
.venv/bin/python -m mypy --check-untyped-defs --warn-unreachable examples/ollama-agents
```

Die [Kriterienmatrix](../../tests/AGENTEN_CASES_5_1.md) beschreibt den Vertrag
und die ursprüngliche Rotphase. Sämtliche Cases laufen ohne Modell; während
der Tests sind echte Netzwerkverbindungen gesperrt. Der zusätzliche
HTTP-Transporttest ersetzt ausschließlich `urlopen()` und führt die tatsächliche
Request-/Responseverarbeitung des Clients aus.
