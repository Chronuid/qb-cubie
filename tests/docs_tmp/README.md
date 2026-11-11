# Entwicklungs- und Abnahmenachweise

Dieser Ordner enthält Dokumentation, keine ausführbaren Tests. Der Name
`docs_tmp` kennzeichnet die Ablage; er bedeutet nicht, dass die Nachweise
automatisch erzeugt oder entbehrlich sind.

Die Dokumente bewahren die Entwicklungsgeschichte: Erst eine bewusst rote
Testsammlung, danach Umsetzung und ergänzende Gegenproben. Angaben wie „noch
nicht implementiert“, Testzahlen und Prüflogs gelten für den jeweiligen
Abschnitt und damaligen Stand. Sie sind keine aktuelle Gesamtsammlung und
keine Aufforderung, heute rote Tests zu erwarten. Auch Nachweise vom selben
Kalendertag können aufeinanderfolgende Entwicklungsstände beschreiben.

| Dokumentgruppe | Einordnung und weiterführender Stand |
| --- | --- |
| [CONTRACT_CASES_9_1](CONTRACT_CASES_9_1.md), [9_2](CONTRACT_CASES_9_2.md) | Vertragskorrekturen und Betriebsnachweise zum [historischen Gutachten](../../GUTACHTEN.md). |
| [BENCHMARK_CASES_10_1](BENCHMARK_CASES_10_1.md), [10_2](BENCHMARK_CASES_10_2.md), [10_3](BENCHMARK_CASES_10_3.md) | Öffentliche Verträge, installierter Durchstich und eigene Prozessagenten. Angekündigte spätere Phasen sind in den folgenden Nachweisen umgesetzt. |
| [BENCHMARK_CASES_10_4](BENCHMARK_CASES_10_4.md), [10_5](BENCHMARK_CASES_10_5.md) | Basisdatensatz, Auswertung und Messbetrieb. Offline-Erfolge ersetzen keinen offiziellen realen Pilot. |
| [BENCHMARK_CASES_SWE_BENCH](BENCHMARK_CASES_SWE_BENCH.md) | Loadervertrag, ursprüngliche Rotphase und implementierte Offline-Abnahme; reale Download-/Container-Integrationsnachweise offen. |
| [AGENTEN_CASES_5_1](AGENTEN_CASES_5_1.md), [5_2](AGENTEN_CASES_5_2.md), [5_3](AGENTEN_CASES_5_3.md) | Unterbau und Rollenkerne. Damals noch ausstehende Prozess-/Wheel-Prüfungen folgen in §5.4. |
| [AGENTEN_CASES_5_4](AGENTEN_CASES_5_4.md) | Installationsnachweis und echte Smokes beider Rollen. |
| [AGENTEN_CASES_5_5](AGENTEN_CASES_5_5.md) | Pilotfreigabe und tatsächliche explorative Zwei-/Fünf-Messreihe; [Messung und Ergebnisgrenzen](../../experiments/ollama-agents/README.md#explorative-messung-vom-10-november-2026). |

Für weiterhin offene Arbeiten gelten die [aktuellen Abschlusskriterien](../../docs/GUIDE_Benchmarks.md#noch-benötigte-praktische-nachweise).
Für die Nutzung gelten die [aktuellen Leitfäden](../../docs/README.md).
Die ursprünglichen Testverzeichnisse und Modulnamen wurden durch die Ablage
der Markdown-Dateien nicht geändert. Shellbefehle sind aus der Repositorywurzel
auszuführen. Historische `/tmp`-Pfade und Prüflogs können inzwischen fehlen;
ihre Nennung garantiert keine dauerhafte Verfügbarkeit.
