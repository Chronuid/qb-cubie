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

Die folgende Kurzfassung ordnet die historischen Messbelege ein.
Unter `evidence/` liegen zwei unveränderte Ergebnisarchive, die beiden eingesetzten
Agentenversionen und der JSON-Laufvergleich. Absolute Pfade darin bezeichnen die
ursprünglichen Versuchsorte; relative Beleglinks bleiben verwendbar. Die Archive
sind Messbelege, keine erneut auszuführenden Sets. Neue Läufe landen in `results/`.

## Nutzungsexperiment vom 10. November 2026

Der Nutzungstest prüfte eigene Aufgaben und einen echten Prozessagenten ohne
Core-Änderung aus qb-cubie 0.0.3 als lokal gebautem Wheel, außerhalb des Checkouts.
Verwendet wurden Python 3.14.3, Ollama 0.40.2 und `gemma4:12b` (`Q4_K_M`),
Digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`,
Temperatur 0, Seed 42, `think=false`, maximal 4096 Ausgabetokens und vom Server
gemeldete 4096 Kontexttokens. Nach zwei wegen VRAM-Belegung abgebrochenen
frühen Versuchen wurde das Modell neu geladen; die folgenden Archive stammen
aus GPU-Läufen. Die Abbrüche begründen kein Qualitätsurteil.

`validate-agent`, Referenzvalidierung einschließlich je eines Grenzmutanten,
`plan`, `run` und `compare` funktionierten aus der Installation. Typ-/Tagfilter
wählten genau die zwei eigenen Aufgaben, jeweils einmal in der Cubie-Bedingung.
Aufbewahrung verlangt eine inklusive Ablaufgrenze, Abrechnung ganzzahliges
Aufrunden auch bei großen Zahlen; negative Eingaben müssen `ValueError` ergeben.

| Archiv | Beobachtung |
| --- | --- |
| [V1](evidence/76b469c2c0ce4832afb36256e47402c6/report.md) | Freies JSON lieferte einen unerlaubten Dateipfad bzw. ungültiges JSON. Der Adapter verweigerte die Abgabe; Cubie meldete Infrastrukturfehler, Exitcode 3. |
| [V2](evidence/0553435a98a04a74a1634504eaf18465/report.md) | JSON-Schema und festes Dateiziel ermöglichten beide Abgaben. Produktionscode bestand die private Abnahme, beide Prozessurteile waren negativ; Exitcode 0. |

V2 benötigte für Abrechnung 36,8 s und 1518/869 Eingabe-/Ausgabetokens, für
Aufbewahrung 17,2 s und 1045/369 Tokens. Kosten blieben `null`. Bei der Abrechnung
enthielten die Modelltests falsche Orakel für große Ganzzahlen und blieben trotz
korrekter Produktion rot: ein tatsächlicher Agentenfehler. Bei der Aufbewahrung
wurden dagegen fachlich scheiternde `pytest.raises`-Tests als `test_error`
eingestuft, obwohl anschließend alle sechs Tests und die unabhängige Abnahme
bestanden: ein damaliger Fehler der Prozessklassifikation.

Dieser Klassifikationsfehler wurde später korrigiert. Bericht und Textvergleich
zeigen inzwischen Qualität und Prozess ausdrücklich; die
[Regressionsabnahme](../../tests/docs_tmp/BENCHMARK_CASES_10_3.md#ergänzung-regressionen-aus-dem-nutzungsexperiment)
dokumentiert zehn deterministische Gegenproben. Die Archive bewahren den damaligen
Stand und sind keine Aussage über unverändert bestehende Produktfehler.
Der [Laufvergleich](evidence/comparison.json) meldet `full` für vergleichbare
Aufgaben; das bedeutet keinen Qualitätserfolg. Beide historischen Adapter
meldeten dieselbe ID und Version 1.0.0; `agent-v1.py` und `agent-v2.py` sichern
ihre tatsächlichen Codevarianten. Für neue Studien sind Adaptervarianten,
Modell-Digest, Provider und Parameter getrennt zu versionieren.

Das Experiment belegt die praktische Anbindung eigener kleiner Developer-Aufgaben.
Reviews, alle Filtervarianten, OS-Isolation und harte Kosten-/Tokenbudgets wurden
nicht geprüft. Referenzen sind nur `author_checked`; ein Grenzmutant je Aufgabe
ist keine vollständige Mutationsabdeckung. Wiederholungen und ein Produktvergleich
fehlen, daher folgt daraus keine Modellrangliste oder allgemeine Nutzenaussage.
Das spätere [Ollama-Rollenbeispiel](../ollama-agents/README.md) ergänzt begrenzte
Reparaturschleifen, Modellnachweise und Messbetrieb.
