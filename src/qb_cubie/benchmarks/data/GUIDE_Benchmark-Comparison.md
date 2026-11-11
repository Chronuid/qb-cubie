# Den Nutzen von Cubie mit gespiegelten Developer-Aufgaben messen

`cubie-vs-pytest` führt dieselben ausgewählten Aufgaben mit denselben Budgets,
Wiederholungen, sichtbaren Ausgangsdateien und unabhängigen Abnahmetests aus.
Mit `agent_pairs` lassen sich pro Bedingung eigene Agenten einsetzen und vor
dem Einfrieren getrennt überarbeiten: Prompts, Werkzeuge, Modelle und Images.
Ein Paar ersetzt das bisherige `agents`-Feld:

```toml
schema_version = 1
name = "developer-benefit"
profile = "cubie-vs-pytest"
repetitions = 3
seed = 17
output = "../results"

[[agent_pairs]]
id = "specialists-v1"
cubie = "../agents/developer-cubie.toml"
pytest = "../agents/developer-pytest.toml"

[[sources]]
path = "../package"

[select]
benchmarks = ["developer_agent"]

[budgets]
wall_time_seconds = 1800
tool_calls = 100

[limits]
max_runs = 100
max_total_wall_time_seconds = 180000
```

Jeder Pfad ist relativ zur Suite. Die Agenten-TOMLs haben unterschiedliche `id`
und dürfen unterschiedliche Kommandos, Modellmetadaten und Images enthalten.
Mehrere `[[agent_pairs]]` erlauben mehrere explizite Vergleiche. Die Paar-ID wird
als `agent_pair_id` in Plan und Ergebnissen archiviert. Gleiche Paar-IDs dürfen
innerhalb einer Suite nicht mehrfach vorkommen. Ohne `agent_pairs` bleibt der
bisherige Vergleich desselben Agenten in beiden Bedingungen verfügbar.

Eine Suite für zwei vorhandene Agenten lässt sich erzeugen:

```bash
cubie-bench init-suite ./sets/comparison.toml --preset smoke \
  --agent ./agents/developer-cubie.toml \
  --pytest-agent ./agents/developer-pytest.toml --package ./package
```

Die Vorlage wählt Developer-Aufgaben und verdoppelt die Laufgrenzen. Ihre kurzen
Smoke-Budgets anschließend für die eigentliche Messung anpassen. Fachliche
Aufträge sollen frameworkneutral formuliert sein; die Agentenkonfiguration
bestimmt, ob EBT oder reguläres Pytest verwendet wird. Das mitgelieferte
Basispaket ist dafür geeignet. Aufgaben und private Referenzen werden nicht
automatisch umgeschrieben.

## Zugriffstrennung

Ein externer Developer-Agent in der Bedingung `pytest` benötigt zwingend
`container_image` mit einem unveränderlichen Image-Digest. Sein Image enthält
Python, Pytest, Projektabhängigkeiten und den Vergleichsadapter, aber weder das
Cubie-Paket noch einen Cubie-Checkout. Eine bloße Promptanweisung genügt nicht.
Beim Start prüft der Runner, dass `qb_cubie` nicht importierbar ist; ein Image mit
installiertem Cubie wird abgelehnt. Die Prüfung gilt für Capability-Probe,
Agentensitzung und die unabhängigen Pytest-Beobachtungen.

In die Agentensitzung werden ausschließlich das sichtbare Aufgabenworkspace
und ein eigenes Belegverzeichnis eingebunden. Host-Checkout, private
Evaluatorablage, andere Episoden, Git-Objekte und Docker-Socket bleiben außerhalb
des Containers. Prozesse laufen mit Ressourcenlimits und auf Unix mit der
Host-UID/GID. Vor der privaten Abnahme wird der gesamte Agentencontainer beendet.
Phasentests und Abnahme laufen in frischen Containern desselben Images ohne
Netzwerk. Dafür braucht auch das Pytest-Image sämtliche Testabhängigkeiten.

Auch für den Cubie-Agenten ist ein eigenes Image empfehlenswert; ein konfiguriertes
`container_image` wird für Sitzung und Tests verwendet. Cubie darf darin als
installiertes Wheel liegen. Der Benchmark-Runner selbst bleibt auf dem Host und
darf Cubie zur Steuerung und Auswertung verwenden.

Der Modellzugang der Agentensitzung benötigt weiterhin Netzwerk. Daher sind die
Images und Adapter Teil des Messvertrags: keine Cubie-Quellen hineinbauen oder
während des Vergleichslaufs nachladen. Die Importprüfung ist keine Suche nach
beliebig versteckten Quellkopien im Image. Builtin-Fakes dienen ausschließlich
dem Offline-Test der Infrastruktur und unterliegen dieser Containerpflicht nicht.

## Beispiel mit den mitgelieferten Ollama-Agenten

Zunächst mit `cubie-bench init-ollama ./study --endpoint ... --model ...` ein
Beispiel exportieren. Der Developer unterstützt bereits `mode="cubie"` und
`mode="pytest"`; seine lokalen Pytest-Werkzeuge benötigen selbst kein Cubie.
Zwei getrennte Laufzeitkonfigurationen erzeugen, bevor die Images gebaut werden:

```python
import copy
import json
import sys
from pathlib import Path

root = Path("study").resolve()
sys.path.insert(0, str(root / "adapter"))
from ollama_agents.developer.process import prompt_hash

original = json.loads((root / "adapter/developer.json").read_text())
for mode in ("cubie", "pytest"):
    config = copy.deepcopy(original)
    config.update(agent_id=f"developer-{mode}", mode=mode,
                  archive_root="/agent-evidence",
                  endpoint="http://host.docker.internal:11434")
    config["model"]["prompt_sha256"] = prompt_hash(mode)
    (root / f"adapter/developer-{mode}.json").write_text(json.dumps(config, indent=2))
```

Die beiden JSON-Dateien können getrennt angepasst werden. Der Modus bindet das
jeweilige Frameworkwissen in den Modellprompt ein. Für weitergehende
Prompt-/Werkzeugänderungen jeweils eigene Adapterkopien und Images verwenden und
die Prompt-/Adaptermetadaten aktualisieren. Bei Veränderungen nach dem Imagebau
müssen die Images neu gebaut und ihre neuen Digests in die Agenten-TOMLs übernommen
werden. Für gleichen fachlichen Kontext sollten Modell und Inferenzbudgets
möglichst gleich bleiben.

Die Dockerfiles unter `examples/developer-comparison` kopieren nur den
exportierten Adapter. Nur das Cubie-Image erhält zusätzlich ein Wheel:

```bash
python -m pip wheel --no-deps . --wheel-dir ./study/wheels
docker build -f examples/developer-comparison/Dockerfile.cubie -t developer-cubie ./study
docker build -f examples/developer-comparison/Dockerfile.pytest -t developer-pytest ./study
docker image inspect --format '{{.Id}}' developer-cubie
docker image inspect --format '{{.Id}}' developer-pytest
```

Die ausgegebenen `sha256:…`-Digests anschließend in zwei Agenten-TOMLs einsetzen:

```toml
schema_version = 1
id = "developer-pytest"
transport = "jsonl-v1"
container_image = "sha256:<tatsächlicher Imagehash>"
command = ["python", "-I", "/opt/adapter/process.py", "--role", "developer", "--config", "/opt/adapter/developer-pytest.json"]
capabilities = ["workspace_changes", "phased_submission", "cancel", "wall_time", "tool_calls"]
```

Für Cubie `id`, Image und JSON-Pfad entsprechend auf `developer-cubie` setzen.
Den vollständigen `[model]`-Block aus der ursprünglichen Developer-TOML jeweils
übernehmen und `prompt_sha256` aus der zugehörigen neuen JSON-Konfiguration
einsetzen. So wird die tatsächliche Modellsignatur im Handshake geprüft und
archiviert. Projektabhängigkeiten bei Bedarf in beide Images aufnehmen.

## Freeze, Messung und Abgleich

```bash
cubie-bench plan --suite ./study/sets/comparison.toml
cubie-bench freeze --suite ./study/sets/comparison.toml --destination ./study/frozen-v1
cubie-bench run-frozen ./study/frozen-v1 --output ./study/results
cubie-bench compare ARCHIV ARCHIV \
  --before-condition cubie --after-condition pytest \
  --before-agent developer-cubie --after-agent developer-pytest
cubie-bench summarize-pilot ARCHIV
```

`ARCHIV` ist der ausgegebene Laufordner mit `manifest.json` und `results.json`.
Der Vergleich liest vorhandene Ergebnisse, ohne Agenten erneut zu starten.
Beide Bedingungen müssen explizit ausgewählt werden; der bisherige Vergleich
von Agentenversionen paart weiterhin nur dieselbe Bedingung. Verglichen werden
identische Aufgaben, Paketversionen, Ausgangsbäume, Evaluatoren, Budgets,
Wiederholungen und Paar-IDs. Unpassende Zellen bleiben als unvollständiger oder
inkompatibler Vergleich sichtbar. Bei mehreren Agenten je Bedingung sind die
Agenten-IDs explizit auszuwählen.

Qualität, beobachteter TDD-Prozess und Fehlerstatus stehen für beide Versuche im
Ergebnis. `effort_deltas` zeigt zusätzlich Laufzeit, Werkzeugaufrufe, Token und
Kosten als **nachher minus vorher**; unbekannte Messungen bleiben `null`.
Bei `cubie → pytest` bedeutet ein positiver Aufwandunterschied also höheren
Aufwand für Pytest. `summarize-pilot` zeigt Erfolgsquoten und Aufwand getrennt
nach Agent und Bedingung. Unterschiedliche Spezialisten messen den Nutzen der
konfigurierten Arbeitsweisen; der Unterschied ist nicht ausschließlich dem
Framework zurechenbar. Wiederholungen und mehrere unabhängige Projektgruppen
sind für belastbare Aussagen nötig.

## SWE-bench als Datenquelle der regulären Developer-Benchmark

Der [SWE-bench-Import](GUIDE_Benchmark-SWEbench.md) lädt Datensätze in reguläre
Szenariopakete mit `benchmark="developer_agent"`. Solche Pakete können dieselbe
Suite und dieselben `agent_pairs` verwenden. Unter `[[sources]]` zusätzlich den
erfolgreich gebundenen `reference_report` angeben. Beide Agenten benötigen für
diese Aufgaben `project_patch` statt `phased_submission` und geben einen
vollständigen `submission.patch` ab. Ihre unveränderlichen Images bleiben
getrennt konfigurierbar.

Importierte Reparaturen behalten `process_profile="issue_resolution"` und die
unabhängige FAIL-/PASS-TO-PASS-Abnahme. Sie erhalten keine erfundene TDD-Gutschrift
und erfordern keine künstlichen Einmodul-Mutanten. Ein separates Messsystem für
SWE-bench ist dafür nicht erforderlich. Öffentliche Datensätze und mögliche
Modellbekanntheit bleiben in der Herkunft dokumentiert.

## Technische Nachweise

Offline-Verträge: `python -m pytest tests/benchmarks/test_mirrored_developer.py`.
Der echte Docker-Durchstich ist ausdrücklich zuschaltbar:

```bash
CUBIE_TEST_BASELINE_IMAGE=<lokales-Python-mit-Pytest-Image> \
  python -m pytest tests/benchmarks/test_mirrored_developer_container.py
```

Er baut aus dem lokalen Image einen temporären synthetischen Vergleichsagenten,
prüft die Dateisystem-/Importgrenzen und führt beide Bedingungen samt Abnahme
und Archivvergleich aus. Er startet kein Modell und liefert keinen fachlichen
Nutzenbeleg für Cubie.
