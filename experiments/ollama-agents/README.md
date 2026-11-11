# Lokale Ollama-Agenten aus Checkout und Wheel

Dieses Beispiel implementiert den gemeinsamen Ollama-Unterbau, einen Reviewer
mit Quellenbindung und einen Developer mit kontrollierten Test-/Implementierungsphasen
sowie Wheel-Export, Kalibrierung und Pilotfreigabe. Die
[Abnahmenachweise](../../tests/docs_tmp/README.md) dokumentieren die fünf Entwicklungsschritte.
Der gemeinsame Unterbau und der Reviewer verwenden die Python-Standardbibliothek;
der Developer nutzt zusätzlich den installierten Cubie-Testausführer und pytest.
Python ab 3.13 wird benötigt. Import und Offline-Prüfungen starten weder Ollama noch ein
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

Die Implementierung liegt im Paket `ollama_agents/`. Der Reviewer-Kern komponiert die Dienste. Sie führen keine Modellkorrekturschleifen
aus und starten keine frei erzeugten Shellbefehle. Beide Rollen besitzen einen
JSONL-Prozessanschluss. Das installierte Wheel exportiert über `cubie-bench init-ollama`
die Adapter, eingefrorene Agenten-TOMLs und getrennte Rollen-Smoke-Sets.

## Aus installiertem Wheel (§5.4)

```bash
python -m pip install '/absoluter/pfad/qb_cubie-0.0.3-py3-none-any.whl[benchmarks]'
cubie-bench init-ollama ./ollama-demo
cd ollama-demo
cubie-bench validate-agent agents/reviewer.toml
cubie-bench validate-agent agents/developer.toml
cubie-bench plan --suite sets/reviewer.toml
cubie-bench plan --suite sets/developer.toml
# Echte Modellaufrufe:
cubie-bench run --suite sets/reviewer.toml
cubie-bench run --suite sets/developer.toml
```

`init-ollama` liest lokale Modellmetadaten ohne Inferenz und friert Digest,
Ollama-Version, Parameter, Adapterversion und Prompt-Hash ein. `--endpoint` und
`--model` wählen Server und Modell explizit. Das Ziel darf noch nicht existieren.
Der vollständige [installierte Leitfaden](../../src/qb_cubie/benchmarks/data/GUIDE_Ollama-Agents.md)
wird als `README.md` mitexportiert. [Abnahme und tatsächliche Läufe](../../tests/docs_tmp/AGENTEN_CASES_5_4.md)
trennen deterministische Wheel-Replays von echten Modell-Smokes.

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

Die [Kriterienmatrix](../../tests/docs_tmp/AGENTEN_CASES_5_1.md) beschreibt den Vertrag
und die ursprüngliche Rotphase. Sämtliche Cases laufen ohne Modell; während
der Tests sind echte Netzwerkverbindungen gesperrt. Der zusätzliche
HTTP-Transporttest ersetzt ausschließlich `urlopen()` und führt die tatsächliche
Request-/Responseverarbeitung des Clients aus.

## Reviewer-Kern (§5.2)

`reviewer.py` exportiert jetzt `ReviewerAdapter`. Der Kern nimmt eine vorhandene
v1-Reviewanfrage entgegen und liefert ein einzelnes Abschlussereignis als Python-
Dictionary. Er liest den gesamten kleinen Originalkontext samt Hashes, validiert
freie Befunde und Quellen, erlaubt genau eine Modellkorrektur und schreibt nach
erneuter Quellenprüfung ausschließlich `review.json`. Die Implementierung liegt
in `ollama_agents/reviewer/`; Prompt und Aktionsschema sind als `reviewer-v2`
versioniert. Die Dateiliste und die Leserechte werden aus dem Workspace ermittelt.
Das Unterpaket exportiert `ReviewerAdapter` direkt über
`from ollama_agents.reviewer import ReviewerAdapter`.

| Modul im Unterpaket `reviewer` | Aufgabe |
| --- | --- |
| `adapter.py` | Reviewablauf, Korrekturen, Budgets und Schrittbelege |
| `process.py` | JSONL-Prozessanschluss, Konfiguration und Handshake |
| `request.py` | Validierung der Benchmark-Anfrage |
| `schema.py` | Versionierter Prompt und Aktionsschema |
| `sources.py` | Quellbestand, Änderungsprüfung und Befundvalidierung |
| `tools.py` | Lesewerkzeuge und Testausführung in einer Kopie |

Die gemeinsam genutzten Dienste bleiben im übergeordneten Paket `ollama_agents`.

Nach expliziter Modellkonfiguration kann der Aufrufer den Kern so verwenden
(`review-request.json` enthält eine gültige v1-Anfrage des Runners):

```python
import json
from pathlib import Path

from common import BudgetLedger, EvidenceWriter, OllamaClient
from reviewer import ReviewerAdapter

request = json.loads(Path("review-request.json").read_text(encoding="utf-8"))
budget = BudgetLedger(wall_time_seconds=request["budgets"]["wall_time_seconds"],
                      max_model_calls=6, max_tool_calls=12, reserve_seconds=5)
evidence = EvidenceWriter(archive_root=Path("review-evidence").absolute(),
                          workspace=request["workspace"])
client = OllamaClient(endpoint="http://localhost:11434", model="gemma4:12b",
                      options={"temperature": 0, "seed": 42, "num_ctx": 16384,
                               "num_predict": 2048}, think=False)
adapter = ReviewerAdapter(client=client, budget=budget, evidence=evidence)
try:
    event = adapter.review(request)
finally:
    archive = evidence.finalize()
```

Dieser Aufruf führt echte Inferenz aus. Die Standardwerte sind weiterhin
Kalibrierungswerte; vor Messungen müssen Modellidentität und Einstellungen
separat geprüft und eingefroren werden. Der Aufrufer bewahrt das externe
Belegarchiv auf und übernimmt die JSONL-Ausgabe des Ereignisses. Der Kern selbst
schreibt nichts auf stdout und lädt bei Import kein Modell.

Die Lesewerkzeuge sind `list_files`, `read_file` und die literale Suche
`search_text`. `run_visible_tests` nutzt eine frische temporäre Kopie, den
aktuellen Python-Interpreter und ein festes pytest-Kommando ohne Shell.
pytest muss dort installiert sein; Cubie wird für den Kern nicht importiert.
Umgebungsvariablen zur Python-Pfadsuche und pytest-Plugininjektion werden entfernt.
Ausgaben werden begrenzt und Auslassungen markiert. Bei Timeout wird unter POSIX
wie beim lokalen Runner die gesamte Testprozessgruppe beendet und eingesammelt.
Die Kopie ist keine OS-Isolation für fremden Code.

Die [Reviewer-Kriterienmatrix](../../tests/docs_tmp/AGENTEN_CASES_5_2.md) dokumentiert
90 bestandene Reviewer-Cases einschließlich 22 ergänzender Gegenproben.
Zusammen mit den 109 Unterbau-Cases bestehen 199 Offline-Cases. Der JSONL-Prozess
mit Handshake und Modellmetadaten ist im zusätzlichen Pipeline-EBT unten geprüft.
Die vollständigen Smoke-Sets und der Wheel-Nachweis sind in §5.4 ergänzt. Menschliche semantische Nachbewertung folgt
dem dort dokumentierten Verfahren; der bestehende Evaluator vergleicht weiterhin
exakte Finding-Felder.

## Kleinen echten EBT-Smoke ausführen

```bash
CUBIE_RUN_OLLAMA_SMOKE=1 .venv/bin/python -m pytest tests/live_ollama -q
```

Aus dem Repositorywurzelverzeichnis prüft dies zwei konkrete Fälle mit echten
Aufrufen an das installierte `gemma4:12b`: Freigabe des konformen Renderers und
Erkennung des Ampersand-Fehlers. Standardmäßig bleiben die Tests ausgeschaltet.
[Aufruf, Belege und erster tatsächlicher Lauf](../../tests/live_ollama/README.md)
dokumentieren die Erwartungen und die Grenzen der semantischen Befundqualität.

Der Promptstand `reviewer-v2` verlangt bei Befunden eine auslösende Eingabe,
das beobachtete Verhalten und die fachlich erwartete Ausgabe. Reine
Schweregradangaben und bekannte Platzhalter werden für `mechanism` und `impact`
abgewiesen und innerhalb des bestehenden Korrekturbudgets zurückgegeben.
Die abgewiesene Antwort wird dem Korrekturschritt ebenfalls vorgelegt. Diese
lokale Prüfung erkennt bekannte Nicht-Erklärungen; sie ersetzt keine semantische
Bewertung beliebiger Befunde. Der echte EBT-Smoke verlangt für den Ampersandfall
zusätzlich konkrete Belege zur unmaskierten Eingabe und zur erwarteten Maskierung.

## JSONL-Anschluss an den Benchmark-Runner

`reviewer_process.py --config /absoluter/pfad/runtime.json` stellt jetzt den
Reviewer als JSONL-v1-Prozess bereit. Die Konfiguration enthält `agent_id`,
`endpoint`, ein externes `archive_root` und die vollständige öffentliche
`model`-Deklaration. `model.parameters` enthält die Ollama-Optionen einschließlich
`think`. `model.adapter_version` muss der exportierten Konstante `VERSION` aus
`ollama_agents.reviewer.process` entsprechen; `prompt_sha256` wird mit dessen
`prompt_hash()` berechnet. Der Prozess verwirft abweichende Versionen oder Hashes
bereits vor dem Handshake und startet dort kein Modell.

Eine vollständig ausführbare Konfigurationserzeugung samt Agenten-TOML zeigt
[test_benchmark_rbt_live.py](../../tests/live_ollama/test_benchmark_rbt_live.py).
Der Test friert lokale Modellmetadaten explizit ein und führt eine einzelne
konforme Episode mit dem echten Benchmark-Runner aus. Seine EBT-Abnahme prüft
unabhängige Evaluation, RBT-Aufzeichnung und die Identität beider Berichte.
Aufruf und Grenzen stehen in der [Live-Testbeschreibung](../../tests/live_ollama/README.md).
Dieser Prozessanschluss ersetzt den zuvor noch offenen JSONL-Nachweis für den
Reviewer. Die Wheel-Installation und vollständigen Rollen-Smoke-Sets sind oben beschrieben.

## Developer-Kern (§5.3)

`developer.py` exportiert `DeveloperAdapter`. Der Kern implementiert die Folge
`test_design → red → green → refactor` für eine Episode. Dieselbe Instanz nimmt
über `develop(request)` nacheinander reguläre v1-Developer-Anfragen entgegen und
liefert pro Anfrage genau ein Abschlussereignis als Dictionary. Der Aufrufer
übernimmt dessen JSONL-Ausgabe und finalisiert das externe EvidenceWriter-Archiv
nach der letzten Phase oder einem Abbruch. `developer_process.py --config runtime.json`
übernimmt dies als JSONL-Prozess; sein implementierter Vertrag wird auch aus dem
installierten Wheel exportiert.

Die Konstruktorparameter entsprechen dem Reviewer, ergänzt um `mode="cubie"`
oder `mode="pytest"`. Für den Developer sind anfänglich 1800 Sekunden,
12 Modellaufrufe, 40 interne Werkzeugaufrufe und `num_predict=4096` vorgesehen.
Budget und Adapter werden pro Episode einmal angelegt. Modus, Promptstand
`developer-v4` und Werkzeugbeschreibung müssen vor Messungen eingefroren werden.
Dieser Prompt verlangt ausdrücklich neue Tests unter `tests/` und nach
beobachtetem fachlichem Rot `submit_phase`, bevor der Runner Grün anfordert.
Das Cubie-Dokumentationspaket zeigt EBT innerhalb einer parametrisierten
pytest-Testfunktion, damit ein erwartetes Rot keinen Sammelfehler erzeugt.

Die Implementierung liegt unter `ollama_agents/developer/`: `adapter.py` steuert
Phasen und Reparaturen, `sources.py` vergibt Dateirechte und überwacht den
akzeptierten Stand, `schema.py` definiert Prompt und Aktionsschema, `tools.py`
führt reale Tests aus. Der Developer benötigt neben der Standardbibliothek eine
installierte Cubie-Version und pytest. Er verwendet den vorhandenen
Benchmark-Testausführer und dessen JUnit-Klassifikation. Isoliertes Python
(`-I`) in einer temporären Projektkopie verhindert einen versehentlichen Import
des Repository-Checkouts. Die Kopie stellt keine OS-Sandbox dar.

Im Testentwurf sind neue Python-Dateien unter `tests/` erlaubt; bestehende
Originaldateien bleiben unverändert. Syntax-/Importfehler und vollständig grüne
Tests erhalten konkrete Korrekturhinweise. Bei fachlichem Rot kann der Agent
abgeben; der akzeptierte Teststand bleibt danach unveränderlich. Die Rotphase
meldet diesen Stand ohne Modellaufruf. Grün und Refactor dürfen ausschließlich
die ermittelten Produktionsmodule und ein neues Nutzungsdokument ändern.
Standardziel ist `USAGE.md`; existiert es bereits, wird ein freier Name wie
`USAGE.agent-1.md` gewährt und im Modellkontext genannt.

Jeder erlaubte Schreibvorschlag wird atomar übernommen und in einer Kopie
getestet. Tatsächliche Testergebnisse gelangen ins Belegarchiv und zurück ins
Modell. Maximal drei Implementierungsvorschläge teilen dieselben Episodenlimits.
Nach dem dritten Vorschlag wird der letzte zulässige Grünstand abgegeben,
auch wenn die Tests wegen eines falschen Orakels weiterhin scheitern.
`completed` bedeutet eine fertige Abgabe; die unabhängige Prozessabnahme bleibt
beim Runner. Refactor muss weiterhin grüne Tests vorweisen. Ein No-op ist erlaubt.
Verbotene Dateiziele und ungültige Modellantworten erhalten eine einzige
Korrekturchance pro Phase. Budgetabbrüche werden separat gemeldet.

Die [Developer-Kriterienmatrix](../../tests/docs_tmp/AGENTEN_CASES_5_3.md) dokumentiert die
36 ursprünglichen Abnahmecases und neun ergänzende Gegenproben. Diese Offline-
Replays prüfen die Adapterfunktion, keine Modellleistung. Der Installationsweg
ergänzt Prozessgegenproben und beide Smoke-Sets mit unabhängiger Runner-Abnahme.
Die tatsächlichen Modell-Läufe und deren Grenzen stehen im §5.4-Nachweis.

## Kalibrierung und Pilot (§5.5)

Die installierte Funktion `ollama_agents.pilot.freeze_pilot` verlangt zwei
vollständig archivierte Kalibrierungswiederholungen und friert anschließend fünf
Messwiederholungen je ausgewählter Aufgabe, Agent und Bedingung ein. Fachliche
Fehlschläge und Infrastrukturfehler werden mitgezählt. Nicht gestartete Zellen,
doppelte Archive, zusätzliche Runden und geänderte Aufgaben verhindern die
Freigabe. Budgets und Modellparameter dürfen vor dem Einfrieren angepasst werden.
Aufnahmebelege dürfen ergänzt werden; Änderungen am fachlichen Referenzurteil
oder an privaten Abnahmetests erfordern eine neue Kalibrierung.

```bash
# Kalibrierungsset mit repetitions=2 ausführen und Ergebnisarchiv aufbewahren.
cubie-bench run --suite sets/calibration.toml --format json
# Pilotset enthält repetitions=5 und ausreichende Gesamtbudgets.
python -m ollama_agents.pilot --suite sets/pilot.toml \
  --calibration results/calibration/ARCHIV-ID --destination frozen-pilot
cubie-bench run-frozen frozen-pilot --output results/pilot --format json
cubie-bench summarize-pilot results/pilot/ARCHIV-ID --format json
```

Auch offizielle Piloten erlauben `author_checked` ohne menschliche Prüfungen
je Fall. Diese sind optional und keine Voraussetzung für Vollständigkeit.
`independently_checked` verlangt weiterhin zwei dokumentierte menschliche
Zustimmungen. Das Manifest meldet diesen Status nur, wenn alle ausgewählten
Referenzen ihn tragen, sonst `author_checked`. Der Schalter `--exploratory`
kennzeichnet unabhängig davon das Messziel; dessen Manifest
vermerkt `study_kind=exploratory`. Es werden keine Prüfbelege erzeugt oder
Referenzstatus umgeschrieben. Das vorhandene Freeze-Format bindet Quellen,
Prompts, Agenten, Modellkonfiguration und die mitkopierten Kalibrierungsarchive.
Der UTC-Einfrierzeitpunkt liegt nach dem Ende aller Kalibrierungsversuche.

Für die wiederholte Messung der öffentlichen Reviewer-/Developer-Smokes gibt es
einen eigenen, ausdrücklich freizuschaltenden Ablauf:

```bash
python -m ollama_agents.pilot.live /absoluter/neuer/studienpfad --exploratory
```

Dieser Ablauf exportiert das installierte Beispiel, prüft und wärmt das Modell
mit unbewertetem Material vor und führt seriell 6 Kalibrierungs- und danach 15
Mess-Episoden aus. Er prüft Digest und Provider-Version an den Stapelgrenzen,
erfasst GPU-/Ladezustand und archiviert Runner- und externe Adapterbelege unter
dem Studienpfad. Modellaufrufe und Werkzeugergebnisse werden nachgezählt und
gegen die gehashten Belege geprüft. `study.json` wird vor jedem Stapel aktualisiert;
abgebrochene Studien bleiben einschließlich vorhandener Fragmente erhalten.
Der Ablauf wiederholt keine gescheiterte Episode automatisch.

Die öffentlichen Aufgaben sind bekannte Entwicklungsdaten. Diese Messung liefert
keinen offiziellen Goldstandard oder Nachweis für unbekannte Projekte. Kosten
bleiben unbekannt; Reviewer-Findingtexte unterliegen weiterhin dem exakten
Matcher. Menschliche Aufnahme und blinde semantische Nachbewertung bleiben offen.
Das [§5.5-Protokoll](../../tests/docs_tmp/AGENTEN_CASES_5_5.md) trennt Offline-Abnahme und
tatsächliche Modellmessungen.

## Explorative Messung vom 10. November 2026

Aus einem frisch installierten Wheel außerhalb des Checkouts wurden mit lokalem
Ollama beide Rollen seriell gemessen: die Reviewer-Fälle `shop/review-boundary`
und `shop/review-correct` sowie `shop/fee-initial` als Developer-Episode unter
Cubie. Zwei Kalibrierungs- und danach fünf Messwiederholungen je Aufgabe ergaben
6 Kalibrierungs- und 15 Pilotepisoden. Die Pilotsets wurden nach beiden
Kalibrierungen eingefroren; danach blieben Prompts und Parameter unverändert.
Alle 21 begonnenen Episoden sind enthalten und `completed`; keine wurde ersetzt,
ausgeschlossen oder automatisch wiederholt. Zwei unbewertete Vorprüfungen
werden getrennt gezählt.

Gemessen wurde mit Python 3.13.12, Ollama 0.40.2 und `gemma4:12b` (`Q4_K_M`),
Digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`,
auf einer RTX 4060 Ti mit 16380 MiB. Temperatur 0, Seed 42, Kontext 16384,
`think=false`, `stream=false` und JSON-Schema galten für beide Rollen.
Reviewer/Developer hatten 2048/4096 Ausgabetokens pro Aufruf, 300/1800 Sekunden,
20/100 Runner-Werkzeuge sowie intern 6/12 Modell- und 12/40 Werkzeugaufrufe
als Grenzen. Adapterstände waren `ollama-reviewer-v2-jsonl-1` und
`ollama-developer-v4-jsonl-1`; konkrete Prompts und Konfigurationen sind archiviert.

| Pilotfall | Wiederholungen | Kriterien korrekt | Runner-Qualität bestanden | Prozess bestanden | Dauer: Mittel ± Stichprobenstandardabweichung |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reviewer, Grenzfehler | 5 | 5/5 | 0/5 | entfällt | 12.985 ± 0.107 s |
| Reviewer, konform | 5 | 5/5 | 5/5 | entfällt | 3.093 ± 0.057 s |
| Developer | 5 | 5/5 | 5/5 | 5/5 | 33.444 ± 4.390 s |

Die Kalibrierung ergab beim Reviewer 4/4 korrekte Kriterienentscheidungen und
2/4 bestandene Qualitätsabnahmen, beim Developer 2/2 bestandene Qualitäts-
und Prozessabnahmen. In den fünf Developer-Pilotepisoden wurden eingefrorene
Tests, fachliches Rot, Grün und Refactoring tatsächlich beobachtet; die private
Projektabnahme bestand unabhängig davon. Die fünf Grenzfehlerreviews scheiterten
am exakten Vergleich anders formulierter Findingtexte. Das belegt keine
semantische Precision/Recall von null. Eine blinde semantische Nachbewertung
steht aus; Referenzformulierungen wurden dem Modell nicht vorgelegt.

Kalibrierung und Pilot umfassen 56 Modellaufrufe mit 95994 Eingabe- und 6034
Ausgabetokens; mit Vorprüfungen waren es 58 echte Inferenzaufrufe. Kosten sind
`null`, harte Tokenlimits wurden nicht durchgesetzt. Zeiten sind lokale
Beobachtungen bei zeitweise parallel laufenden CPU-Prüfungen; GPU-Zustände
wurden nur an Stapelgrenzen erfasst. Die öffentlichen Aufgaben sind potenziell
bekannt, mit nur einer Projektgruppe je Rolle. Wiederholungen schaffen keine
zusätzlichen Projekte. Ein Cubie-/pytest-Vergleich wurde nicht ausgeführt.
Die Messung ersetzt weder den Basisdatensatz-Pilot noch einen unabhängigen
Goldstandard oder einen allgemeinen Modell-/Produktleistungsnachweis.

Die Rohdaten liegen außerhalb des Repositorys unter
`/home/symphonie/.local/share/cubie/agent-5-5-20261110`, die Auswertung daneben
in `agent-5-5-analysis.json`. `evidence-manifest.json` bindet 1756 Dateien;
vier Runnerarchive und 21 externe Adapterarchive wurden nachgeprüft.
Das gemeinsame Archiv `agent-5-5-evidence-20261110.tar.gz` im selben Elternordner
hat SHA-256 `4028ab93d49d83b1c64f4afffa6242816ccc5c5b8a165d84cb1882d76cb19036`.
Es bewahrt Konfigurationen, Rohantworten, Provider-/Hardwarebelege und Wheels.
Das gemessene Wheel hat SHA-256
`f14b47b0a1baa89043f05a9da07febb577feea532fa6da0f5ec30046e066ef28`;
das abschließende Produktwheel
`caab3d7de8d6b98331ce6fc7ff6acb6c15f8db695f8b98207ceb9169f3d959b9`
enthält zusätzliche Produktprüfungen bei identischen Rollenprompts und Parametern.
Die Archivangabe ist kein Nachweis einer getrennten Sicherung und Wiederherstellung.
[Offline-Abnahme und Archivprüfung](../../tests/docs_tmp/AGENTEN_CASES_5_5.md)
bleiben getrennt von der Modellmessung dokumentiert. Menschliche Referenzprüfungen
wurden nicht durchgeführt und bleiben optional; für Aussagen zur semantischen
Findingqualität fehlt weiterhin eine dokumentierte Nachbewertung.
