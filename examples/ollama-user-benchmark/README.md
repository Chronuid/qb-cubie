# Eigener Ollama-Agent für Cubie

Dieses eigenständige Nutzerbeispiel enthält einen echten Modellagenten und zwei
selbst verfasste Szenarien. Es benötigt keine Änderung an Cubie und außer
`qb-cubie[benchmarks]` keine weiteren Python-Pakete. Ollama muss lokal auf
`http://localhost:11434` das Modell `gemma4:12b` bereitstellen.

In einer Python-Umgebung ab 3.13, in der Cubie installiert ist:

```bash
python configure.py
cubie-bench validate-agent agent.toml
cubie-bench list --package package
cubie-bench validate package --check-references
cubie-bench plan --suite suite.toml
cubie-bench run --suite suite.toml
```

Die Befehle im Verzeichnis dieses Beispiels ausführen. `configure.py` trägt den
absoluten Pfad des aktiven Interpreters ein. Nach Verschieben oder Wechsel der
Umgebung erneut ausführen. Für den Test wurde Cubie aus dem Repository als Wheel
gebaut und in `/tmp/cubie-user-env` installiert; das Beispiel lief separat unter
`/tmp/cubie-user-external`, ohne Repository-Imports.

Der Agent liest sichtbare Python-Dateien und den Auftrag. In `test_design`
erstellt Gemma EBT-Tests, in `green` die Implementierung. `red` und `refactor`
geben den unveränderten Bestand ab. Der Agent ist bewusst ein einfacher
Zweischritt-Agent ohne Reparaturschleife, Shellwerkzeug oder Zugriff auf private
Referenzen. Refactoring ist ein No-op. Produktionscode und Tests sind vollständig
modellgeneriert; Referenzlösungen werden nicht als Modellkontext verwendet.
Dateiziele bestimmt der Adapter; das Modell liefert Quelltext über JSON-Schema.
Die JSONL-Sitzung bleibt bestehen, der Modellkontext wird je Aufruf aus den
sichtbaren Dateien aufgebaut. Ein LangChain-Framework ist hierfür nicht nötig.

Die Capability `cancel` entspricht hier der Beendbarkeit des Prozesses durch den
Runner, `tool_calls` dessen Werkzeugzählung. Es gibt kein eigenes Cancel-RPC und
keine behauptete Begrenzung interner Modellaufrufe. Pro Episode erfolgen zwei
HTTP-Aufrufe mit jeweils 240 Sekunden Timeout; das Runnerbudget beträgt 300 Sekunden.
Tokens stammen aus Ollamas `prompt_eval_count` und `eval_count`; Kosten bleiben
unbekannt. Diagnosen einschließlich Modellantwort gehen ausschließlich an stderr.

Aufgaben: Backup-Aufbewahrung mit inklusiver Ablaufgrenze und Telefonabrechnung
mit ganzzahligem Aufrunden. Beide verlangen ValueError für negative Eingaben.
Die private Abnahme und je ein gezielter Grenzmutant sind handgeschrieben und
`author_checked`, ohne unabhängige menschliche Freigabe.

Die vollständige Auswertung steht in
[EXPERIMENT_Benchmark-10-3.md](../../docs/misc/EXPERIMENT_Benchmark-10-3.md).
Unter `evidence/` liegen zwei unveränderte Ergebnisarchive, die beiden eingesetzten
Agentenversionen und der JSON-Laufvergleich. Absolute Pfade darin bezeichnen die
ursprünglichen Versuchsorte; relative Beleglinks bleiben verwendbar. Die Archive
sind Messbelege, keine erneut auszuführenden Sets. Neue Läufe landen in `results/`.
