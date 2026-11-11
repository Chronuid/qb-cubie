# SWE-bench für Developer-Agent-Benchmarks

Cubie importiert Python-Reparaturaufgaben aus den offiziellen Full-, Lite- und
Verified-Datensätzen als eigene Szenariopakete. Der durchgängige Weg ist:
Import → Basis-/Gold-Referenzprüfung → Suite → Freeze → Developer-Agent →
unabhängige Patch-Abnahme. Die drei öffentlichen APIs stehen im installierten
Paket unter `qb_cubie.benchmarks` zur Verfügung.

Die importierten Datensätze sind Quellen der regulären Developer-Agent-Benchmark.
Sie unterstützen auch `cubie-vs-pytest` mit getrennt spezialisierten
`agent_pairs`; siehe [gespiegelte Developer-Aufgaben](GUIDE_Benchmark-Comparison.md).
Dabei bleiben Reparaturprofil, Referenzfreigabe und unabhängige Patch-Abnahme
erhalten.

## Import

```python
from qb_cubie.benchmarks import import_swebench, plan_swebench_import

config = {
    "schema_version": 1,
    "dataset_name": "SWE-bench/SWE-bench_Lite",
    "revision": dataset_commit,  # vollständiger geprüfter 40-stelliger Commit
    "split": "test",
    "cache_dir": "/data/swebench-cache",
    "offline": False,
    "namespace": "swebench-lite-study",
    "version": "1.0.0",
    "instance_ids": selected_instance_ids,
    "seed": 17,
    "include_hints": False,
    "on_error": "fail",
    "process_profile": "issue_resolution",
    "harness_revision": harness_commit,
}
plan = plan_swebench_import(config)
result = import_swebench(config, "/data/scenarios/swebench-lite-study")
```

Der Downloadadapter benötigt `qb-cubie[swebench]` für Parquet. Er liest die
Metadaten und Parquetdateien an der exakten Hugging-Face-Revision, beschafft die
Git-Objekte von GitHub und veröffentlicht geprüfte Snapshots atomar im Cache.
Fehlende eindeutige Datensatz- oder Repositorylizenzen blockieren den Abruf;
der Adapter erfindet keine Lizenz. Repositorylizenzen werden für die bezogenen
Commits über die GitHub-Lizenzmetadaten geprüft. GitHub-Ratenlimits können die
Beschaffung großer Quellen begrenzen. Unbekannte Parquetlayouts werden abgelehnt.
Der aktuelle Adapter beschafft die Git-Objekte des ganzen verlangten Splits;
eine Auswahl reduziert anschließend den Export, nicht diesen Beschaffungsaufwand.

Ein vollständiger lokaler Snapshot im Format der
[Anforderungen](misc/SWE_BENCH_LOADER_ANFORDERUNGEN.md) kann mit `snapshot`
angegeben werden. Dafür werden weder Parquetbibliothek noch Docker benötigt.
`offline=True` ist der Standard und verwendet ausschließlich lokale Daten.
Ein wiederholter Import braucht ein neues Zielverzeichnis.

Das Paket enthält den versionierten Basisstand ohne `.git`. Gold-Patch,
Test-Patch und Rohdaten bleiben privat unter `evaluator/`. Issue-Text und
sichtbare Basistests gehen an den Agenten; optionale Hints sind eine ausdrücklich
andere Messbedingung. `load_package` prüft Dateiinventar, Hashes, Modi und
Symlinkziele. Verschieben verändert die Gültigkeit nicht.
Der bestehende Messpfad verlangt derzeit reguläre Dateien: sichere interne
Symlinks sind importierbar, werden für eine Messung aber ausdrücklich abgelehnt.

## Ausführende Referenzfreigabe

```python
from qb_cubie.benchmarks import validate_swebench_references

reference = validate_swebench_references(result["package"])
assert reference["valid"]
print(reference["report"])  # separate dauerhafte Belegablage
```

Der Standardexecutor setzt Docker, einen aus exakt `harness_commit`
installierten offiziellen `swebench`-Harness mit VCS-Provenienz und vorher
provisionierte Instanzimages voraus. Das Harness wird separat installiert,
beispielsweise mit `pip install "swebench @ git+https://github.com/SWE-bench/SWE-bench.git@<commit>"`.
Seine Provisionierungswerkzeuge erzeugen bzw. beziehen die benötigten Images.
Cubie installiert keine Repositoryabhängigkeiten auf dem Host und baut beim
Referenzaufruf keine Images implizit. Fehlende Images und inkompatible
Harness-/Datensatzschemata führen zu einer Diagnose. Unterstützt sind die
metadatenbasierten Harness-Schnittstellen `harness.utils.make_test_spec` sowie
die ältere Python-Schnittstelle `harness.test_spec.test_spec.make_test_spec`.
Teilweise deklarierte Ausführungsmetadaten werden abgelehnt.

Basis und Gold erhalten frische Container und neue Versuchskennungen. Tests
laufen ohne Netzwerk, Hostmounts oder Daemon-Socket; CPU, Speicher, Prozesszahl
und Laufzeit sind begrenzt. Der tatsächlich aufgelöste Imagehash wird vor dem
Start an den Request gebunden und bei der Messung erneut geprüft. Fehlende,
übersprungene oder fehlerhafte Tests geben keine Referenzfreigabe. Referenzbericht
und Belege liegen getrennt vom unveränderten Paket. Die Belegablage sollte in
den eigenen dauerhaften Studienbereich aufgenommen werden; die API legt sie in
einem Geschwisterverzeichnis `<paketname>.reference-reports/attempt-…` ab und
löscht sie nicht selbst.

## Developer-Agent und Suite

Ein Reparaturadapter benötigt `project_patch`, `workspace_changes`, `wall_time`,
`tool_calls` und `cancel`. Er erhält eine einzige JSONL-Anfrage mit
`phase="repair"`, `process_profile="issue_resolution"`, `output_format="patch_v1"`.
Er liefert `submission.patch` als einziges Artefakt mit SHA-256. Der Patch kann
mehrere Produktionsdateien betreffen. Private Tests werden unabhängig vom
Agentenworkspace im Evaluator angewendet. Änderungen an Tests oder
Collectionkonfiguration werden in dieser ersten Stufe abgelehnt.

Der mitgelieferte Ollama-Developer unterstützt dafür `mode="repair"` in seiner
JSON-Konfiguration. `prompt_hash("repair")` aus
`ollama_agents.developer.process` bindet den eigenen Prompt und die Implementierung.
Dieser Modus erkundet große Repositorys mit paginierten Dateilisten,
Dateiausschnitten und Textsuche. Er schreibt ausschließlich den Patch und behauptet
keine beobachtete TDD-Phase. Die bisherigen Modi `cubie` und `pytest` bleiben für
die bisherigen Entwicklungsaufgaben verfügbar.

Reparaturadapter laufen in einem eigenen Image mit unveränderlicher Identität.
Das Image enthält Adaptercode und Konfiguration. Der Runner bindet nur den
sichtbaren Workspace und eine anfangs leere Belegablage nach `/agent-evidence`
ein; Paket, Evaluator und Git-Cache werden nicht eingebunden. Setze
`archive_root="/agent-evidence"` in der Ollama-Konfiguration. Ein auf dem Host
bereitgestelltes Ollama kann über `host.docker.internal` erreicht werden, sofern
der Dienst Verbindungen aus dem Docker-Netz annimmt. Seine Modellparameter und
Identität werden wie bei den bisherigen Agenten eingefroren.

Ein [Dockerfile](../examples/ollama-agents/swebench/Dockerfile) liegt bei.
Baue zuerst das Cubie-Wheel nach `dist/` und lege `repair-config.json` mit
explizitem Modell, Endpoint, Parametern, Adapterversion und Repair-Prompthash in
der Repositorywurzel ab. Dann beispielsweise:

```bash
docker build -f examples/ollama-agents/swebench/Dockerfile -t cubie-repair-adapter .
docker image inspect cubie-repair-adapter --format '{{.Id}}'
```

Der ausgegebene tatsächliche Digest wird in `agent.toml` eingetragen:

```toml
schema_version = 1
id = "ollama-repair"
transport = "jsonl-v1"
container_image = "sha256:<64-stelliger tatsächlicher Imagehash>"
command = ["python", "-c", "from ollama_agents.developer.process import main; raise SystemExit(main('/adapter/config.json'))"]
capabilities = ["project_patch", "workspace_changes", "wall_time", "tool_calls", "cancel"]
```

Die Suite verweist zusätzlich auf den erfolgreichen Referenzbericht:

```toml
schema_version = 1
name = "swebench-lite-study"
profile = "agent-evaluation"
repetitions = 1
output = "results"
agents = ["agent.toml"]
sources = [{path = "package", reference_report = "reference-evidence/report.json"}]
```

```python
from qb_cubie.benchmarks import freeze_suite, run_frozen_suite

freeze_suite("suite.toml", "frozen-study")
results = run_frozen_suite("frozen-study", "results")
```

Freeze archiviert das Paket, die Referenzbelege und die Digestkonfiguration des
Adapters. Das Adapterimage selbst bleibt eine separat bereitzustellende
Laufzeitvoraussetzung. Eine fehlende Freigabe, andere Paketbytes oder überlappende
Full-/Lite-/Verified-Instanzen werden vor Agentenstart abgelehnt. Die Prüfung
unterscheidet fachlich rote Tests von fehlgeschlagener Infrastruktur. Berichte
zeigen `process_passed=null`, Repositorygruppen, Herkunft, Bekanntheit,
Ausschlüsse und fehlende Regressionsabdeckung. Reparaturqualität wird getrennt
von TDD- und Review-Ergebnissen ausgewiesen.

## Nachweisgrenze

Die regulären Tests verwenden synthetische lokale Git-Repositories und
kontrollierte Executor-/Modellantworten. Sie belegen keine reale SWE-bench-
Leistung. Reale Downloads aller drei Quellen, echte Containergrenzen und ein
vollständiger Modelllauf sind gesonderte Integrationen gemäß der
[Abnahmematrix](../tests/docs_tmp/BENCHMARK_CASES_SWE_BENCH.md).
