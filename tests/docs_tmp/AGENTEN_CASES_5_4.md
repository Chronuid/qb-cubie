# §5.4: Installationsnachweis

> Phasenbezogener Entwicklungsnachweis. Zahlen, Rotphasen und offene Folgearbeiten
> beziehen sich auf den jeweils beschriebenen Stand. Einordnung und spätere
> Nachweise: [Übersicht](README.md). Befehle werden aus der Repositorywurzel ausgeführt.

Stand: 10. November 2026. Der Installationsweg ist implementiert und mit einem
aus der Quelldistribution gebauten Wheel außerhalb des Checkouts geprüft.
Die automatischen HTTP-Replays und die tatsächlichen Ollama-Versuche werden
getrennt ausgewiesen. Keiner dieser kleinen öffentlichen Fälle ist eine
Kalibrierungs- oder Pilotmessreihe.

## Lieferung und Wiederholung

Das Wheel enthält das Beispielpaket `ollama_agents` aus
`examples/ollama-agents/ollama_agents`. Die Paketkonfiguration bindet diese
Quellen direkt ein; es gibt keine separat gepflegte Implementierungskopie.
`cubie-bench init-ollama ZIEL` exportiert aus der Installation:

- beide Rollenprozesse und deren gemeinsame Bibliothek;
- Agenten-TOMLs und Laufzeit-JSON mit identischer Modellkonfiguration;
- ein Reviewer-Set mit konformem und fehlerhaftem Versandgrenzfall;
- ein Developer-Set mit einer vollständigen Entwicklungsepisode;
- Rohmetadaten des Providers, deren Hash und den installierten Wheel-Hash;
- einen [eigenständigen Nutzungsleitfaden](../../experiments/benchmarks/cubie_benchmarks/data/GUIDE_Ollama-Agents.md).

Die Prozesse bestätigen Modell-Digest, Provider-/Adapterversion, Prompt-Hash
und Parameter im Handshake. Die Initialisierung erfasst zusätzlich Quantisierung
und Ladezustand, ohne Inferenz oder automatischen Modelldownload. Das Ziel darf
nicht existieren. Relative Adapter-/Archivpfade erlauben einen anschließenden
Umzug des Beispiels; der Interpreter bleibt explizit gebunden.

```bash
uv build --out-dir /tmp/cubie-agent-5-4-dist
.venv/bin/python scripts/check_wheel.py /tmp/cubie-agent-5-4-dist
```

Der Wheel-Harness erzeugt eine frische Umgebung ohne Hostpakete, bereinigt
Python-/pytest-Pfade und führt die Installationstests außerhalb des Checkouts
mit `-I` aus. Die Ollama-Cases werden erst im Profil `benchmarks` gestartet.
Der lokale HTTP-Server ersetzt ausschließlich Ollama; Rollenprozesse,
Dateiänderungen, pytest/EBT, Rot-/Grün-Beobachtung, Evaluatoren und Archive sind real.
Es werden keine Repository-Fixtures oder Repository-`tests/conftest.py` verwendet.

## Abnahmematrix

| Nachweis | Case | Geprüftes Verhalten |
| --- | --- | --- |
| Wheel, Export, Umzug | `test_installed_export_handshakes_and_plans_do_not_infer` | Installierter Modulpfad, verschobenes Beispiel, gültige Referenzen, beide Handshakes und Pläne, identische Modellkonfigurationen, Wheel-/Provider-Hash; kein Chat und kein Belegarchiv vor dem Lauf; Überschreiben abgewiesen. |
| Beide Smoke-Sets | `test_both_installed_smoke_sets_keep_model_calls_usage_and_hash_bound_evidence` | Zwei Reviews und eine komplette Developer-Episode; unabhängige Qualität, Prozessfreigabe, tatsächlich beobachtetes Rot/Grün; sieben HTTP-Modellaufrufe, exakt summierte Tokens, geprüfte Runner-/Adapterhashes und Bindung über archiviertes stderr. |
| Fehlendes Modell | `test_unavailable_model_fails_without_creating_an_example_or_inference` | Konfigurationsfehler ohne Zielverzeichnis, Inferenz oder Ersatzmodell. |
| Developer-Handshake | `test_handshake_has_no_inference_or_archive` | Identität ohne Modell- oder Dateizugriff; verschiedene Prompt-Hashes für Cubie und pytest. |
| Veraltete Identität | `test_stale_identity_rejected_before_handshake` (2 Varianten) | Falscher Prompt-Hash oder falsche Adapterversion wird vor dem Handshake abgewiesen. |
| Falsche Startphase | `test_wrong_first_phase_creates_no_archive` | Grün vor Testentwurf erzeugt keine Episode. |
| Phasenzustand und Belege | `test_episode_shares_state_and_seals_on_completion_failure_or_eof` (3 Varianten) | Vollständige Folge, falsche Folge und EOF; Tests bleiben unverändert, Rot verbraucht null Tokens, Belege werden jeweils finalisiert. |
| Konkrete Phasenrechte | `test_model_sees_test_directory_grant_and_actionable_path_correction` | Prompt nennt `..` und Abgabe nach fachlichem Rot; unerlaubter Root-Test erhält einen konkreten Korrekturhinweis und bleibt ungeschrieben. |
| Ausführbares Dokumentationsbeispiel | `test_documented_ebt_example_produces_business_red_inside_a_test_function` | Das dem Modell gezeigte EBT-Beispiel wird für die sichtbare Aufgabe instanziiert und erzeugt fachliches Rot in zwei gesammelten Testfällen. |

Die drei Wheel-Cases stehen in
[`tests/wheel/ollama_agents_installed.py`](../wheel/ollama_agents_installed.py),
neun Prozess-/Promptcases in
[`tests/ollama_agents/developer/test_process.py`](../ollama_agents/developer/test_process.py).
Mit den bisherigen 244 Offline-Cases bestehen **253 Agenten-Cases**.
Zusätzlich bestanden die Benchmark-Regressionen (**541 bestanden, 2 übersprungen**).
Ruff und MyPy für das Agentenbeispiel sind erfolgreich.

## Tatsächliche Modellversuche

Alle Versuche liefen seriell mit Python **3.13.12**, Ollama **0.40.2** und
`gemma4:12b`, Quantisierung **Q4_K_M**, Digest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
Die exportierten Kalibrierungswerte blieben unverändert: Temperatur 0, Seed 42,
Kontext 16384, `think=false`, Ausgabelimit 2048 beziehungsweise 4096.
Handshake, Planung und Lauf wurden über den installierten `cubie-bench` aus
`/tmp` ausgeführt, ohne `PYTHONPATH=src` oder Zugriff auf Checkout-Fixtures.

Die frühen Developer-Versuche sind ausdrücklich keine erfolgreichen Abnahmen:

| Prompt | Ergebnis | Beobachtung |
| --- | --- | --- |
| `developer-v1` | `invalid_output`, 2 Modellaufrufe, 2023/806 Eingabe-/Ausgabetokens | Zweimal unerlaubter Root-Test `test_design.py`; keine Datei übernommen. |
| `developer-v2` | `invalid_output`, 3 Modellaufrufe, 8809/656 Tokens | Neue Tests unter `..` erzeugen echtes fachliches Rot. Danach wurden Produktionscode und Nutzungshinweise noch im Testentwurf vorgeschlagen und korrekt abgewiesen. |
| `developer-v3` | `invalid_output`, 2 Modellaufrufe, 2742/342 Tokens | EBT-Assertions auf Modulebene verursachten einen Sammelfehler; die anschließende Abgabe ohne gültiges Rot wurde abgewiesen. |

Der daraus entstandene `developer-v4` benennt die erlaubten Testpfade und die
Abgabe mit `submit_phase` nach erwartetem fachlichem Rot ausdrücklich. Sein
Dokumentationspaket zeigt EBT vollständig innerhalb einer parametrisierten
pytest-Testfunktion und unterscheidet Sammelfehler von fachlichem Rot.
Die Schreibrechte und Budgets wurden nicht erweitert. Alle Versuche bleiben
einschließlich ihrer Rohantworten und Ablehnungsgründe erhalten.

Der abschließende Lauf mit `developer-v4` besteht die vollständige Episode:

| Fall | Status | Kriterien / unabhängige Qualität | Modellaufrufe | Eingabe-/Ausgabetokens |
| --- | --- | --- | --- | --- |
| Reviewer, Grenzfehler | `completed` | `free_threshold=fail`; exakter Finding-Abgleich nicht bestanden | 1 | 666 / 306 |
| Reviewer, konform | `completed` | `free_threshold=pass`; Qualität bestanden | 1 | 672 / 51 |
| Developer | `completed` | `fee=pass`; Qualität und Prozess bestanden | 6 | 12284 / 479 |

Der Developer beobachtet fachliches Rot im Testentwurf, meldet den unveränderten
Stand in Rot ohne Modellaufruf und besteht die eingefrorenen Tests in Grün und
Refactor. Die tatsächlichen lokalen Testergebnisse, Nutzungshinweise und die
unabhängigen Abnahmen liegen im Archiv. Runner- und Adapterhashes sowie die
Bindung der externen Manifeste über archiviertes stderr wurden zusätzlich geprüft.
Die vollständige Wheel-Prüfung besteht **67 Cases** über Kern-, Linter- und
Benchmarkprofile einschließlich der drei neuen Installationscases.

Gemessenes Wheel: SHA-256
`4af92e0d56621d9f910166af95f16ba5e032b78a8b5dd8686caa616a7090bac0`.
Developer-Adapter: `ollama-developer-v4-jsonl-1`, Prompt-Hash
`36c657ac7ca1327d4c8593b50d1918793fe630568ca4a10b03e76f3c5e204368`.

Der Reviewer bleibt bei `reviewer-v2`. Er entschied in jedem dieser
Installationsläufe `free_threshold=fail` für die strikte Grenzprüfung und `pass`
für den konformen Stand (jeweils ein Aufruf, 666/306 beziehungsweise 672/51 Tokens).
Der konforme Fall besteht die unabhängige Abnahme; beim fehlerhaften Fall bleibt
`quality_passed=false`, weil der v1-Evaluator freie Finding-Texte exakt mit der
Referenz vergleicht. Diese Grenze wird nicht durch Vorgabe von Referenzformulierungen
an das Modell umgangen. Der Lauf ist technisch `completed`; eine semantische
Nachbewertung bleibt separat erforderlich.

Lokale Rohbelege liegen unter `/tmp/cubie-agent-5-4-live`,
`/tmp/cubie-agent-5-4-live-v2`, `/tmp/cubie-agent-5-4-live-v3` und
`/tmp/cubie-agent-5-4-live-v4`.
Sie enthalten exportierten Adaptercode, Modellmetadaten, Konfigurationen,
CLI-Ausgaben, Runnerarchive und die zugehörigen externen Adapterarchive.
Diese temporären Artefakte sind nicht Teil des Git-Repositories und müssen
bei weiterer Verwendung zusammen mit dem gemessenen Wheel gesichert werden.
Ein gemeinsames lokales Archiv einschließlich des abschließend gemessenen Wheels
und der Build-/Wheel-Prüflogs liegt unter
`/tmp/cubie-agent-5-4-evidence.tar.gz`, SHA-256
`347dd2ab13cab41141c5b43289ab6ce79d12ad7d2df54d14629879f8eb57674e`.
