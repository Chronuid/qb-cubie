# Lokale explorative Agentenmessung: Kalibrierung und Pilot (§5.5)

Stand: 10. November 2026. **Tatsächlich ausgeführte Modellmessung auf öffentlichen
Entwicklungsaufgaben, keine offizielle Pilotabnahme.** Der Nutzer hat die
explorative Messung bei weiterhin offener menschlicher Referenzaufnahme
ausdrücklich gewählt. Der [Abnahmevertrag](../../tests/docs_tmp/AGENTEN_CASES_5_5.md)
dokumentiert die davon getrennte Produktimplementierung und Offline-Prüfung.

## Versuchsaufbau

Aus einem frisch installierten Wheel wurden außerhalb des Checkouts beide
Rollen, ihre Konfigurationen und das öffentliche Versandkostenpaket exportiert.
Alle Modellaufrufe liefen seriell gegen das lokale Ollama. Die Rollenprozesse
und Testprozesse verwendeten isoliertes Python und die installierte Cubie-Version.
Die Agenten erhielten keine Referenzformulierungen oder privaten Abnahmetests.
Die bestehende Vertrauensannahme des lokalen Runners gilt weiterhin; eine
Containerisolation wurde nicht eingeführt.

Ausgewählt waren die zwei Reviewer-Fälle `shop/review-boundary` und
`shop/review-correct` sowie die Developer-Episode `shop/fee-initial` in der
Cubie-Bedingung. Dies sind dieselben öffentlichen Entwicklungsaufgaben wie beim
Installationsnachweis; sie sind potenziell bekannt und kein zurückgehaltener
Datensatz. Pro Rolle gibt es eine Projektgruppe. Wiederholungen erhöhen die
Zahl unabhängiger Projekte nicht. Ein Cubie-/pytest-Vergleich wurde nicht ausgeführt.

Die Reihenfolge war vorgegeben: Reviewer-Kalibrierung mit vier Versuchen,
Developer-Kalibrierung mit zwei Episoden, Einfrieren beider Pilotsets,
Reviewer-Pilot mit zehn Versuchen, Developer-Pilot mit fünf Episoden. Das ergibt
je Aufgabe und Bedingung zwei Kalibrierungs- und fünf Messwiederholungen.
Keine Episode wurde ersetzt, ausgeschlossen oder automatisch erneut gestartet.
Nach der Kalibrierung wurden keine Parameter oder Rollenprompts geändert.

| Konfiguration | Tatsächlicher Wert |
| --- | --- |
| Python / Ollama | 3.13.12 / 0.40.2 |
| Modell / Quantisierung | `gemma4:12b` / `Q4_K_M` |
| Modelldigest | `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| GPU | NVIDIA GeForce RTX 4060 Ti, 16380 MiB |
| Temperatur / Seed / Kontext | 0 / 42 / 16384 |
| Ausgabelimit Reviewer / Developer | 2048 / 4096 pro Aufruf |
| Denken / Transport | `think=false`, `stream=false`, JSON-Schema |
| Reviewer-Budget | 300 s, 20 Runner-Werkzeuge; intern 6 Modell- und 12 Werkzeugaufrufe |
| Developer-Budget | 1800 s, 100 Runner-Werkzeuge; intern 12 Modell- und 40 Werkzeugaufrufe |
| Reihenfolge | Set-Seed 42, frischer Rollenprozess und Workspace je Episode |

Reviewer: `ollama-reviewer-v2-jsonl-1`, Prompt-SHA-256
`e30bfe0631caf8529daeec4a769c59e524096985a9b80e2147117af35242d1cc`.
Developer: `ollama-developer-v4-jsonl-1`, Prompt-SHA-256
`36c657ac7ca1327d4c8593b50d1918793fe630568ca4a10b03e76f3c5e204368`.

Die Gesamtausführung begann um **10:54:44.835950 UTC** und endete um
**11:00:33.184681 UTC**. Das Reviewer-Pilotset wurde um **10:56:24.068823 UTC**,
das Developer-Pilotset um **10:56:24.305082 UTC** eingefroren, jeweils nach Ende
beider Kalibrierungen und vor dem ersten Pilotversuch. Die Hashbindung der
eingefrorenen Pakete bleibt in den jeweiligen Runnerarchiven erhalten.

## Vorprüfung, Hardware und Messgrenzen

Zwei unbewertete Schema-Vorprüfungen liegen separat unter `preflight/`.
Der erste Aufruf dauerte **5.522 s**, davon meldete Ollama **5.121 s** Ladezeit;
der Developer-Vorprüfungsaufruf dauerte **0.714 s**, mit **0.002 s** gemeldeter
Ladezeit. Beide lieferten gültige JSON-Ausgaben mit je 27 Eingabe- und 6
Ausgabetokens. Diese Aufrufe gehören weder zu den Episodenzahlen noch zu den
untenstehenden Token- und Zeitwerten.

Vor und nach jedem Stapel wurden Digest und Ollama-Version erneut geprüft.
`/api/ps` meldete nach dem Laden das ausgewählte Modell mit aktiver Kontextlänge
16384 und 8389698518 Bytes VRAM. Die GPU-/Ladezustände und Rohmetadaten sind
archiviert. Die GPU-Auslastung wurde an Stapelgrenzen erfasst, nicht kontinuierlich;
damit wird konkurrierende Nutzung nicht ausgeschlossen. Offline-Regressionen
und Wheel-Prüfungen liefen zeitweise parallel auf der CPU. Die Laufzeiten sind
deskriptive Beobachtungen dieser lokalen Umgebung, keine Messung unter
kontrolliertem Rechnerleerlauf.

Kosten bleiben `null`. Es gab kein Kostenmodell und keine harten Tokenlimits.
Temperatur 0 und Seed 42 machten die Wiederholungen nicht vollständig identisch:
die Developer-Pilotepisoden verbrauchten zwischen 10693 und 14185 Eingabetokens
und zwischen 459 und 686 Ausgabetokens.

## Kalibrierungsergebnisse

Alle sechs begonnenen Kalibrierungsepisoden endeten technisch mit `completed`.
Die fachlichen Bewertungen beziehen sich auf die vorhandenen Autorreferenzen.

| Rolle | Versuche | Kriteriumsentscheidungen korrekt | Runner-Qualität bestanden | Prozess bestanden | Modellaufrufe | Werkzeugergebnisse | Eingabe-/Ausgabetokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Reviewer | 4 | 4/4 | 2/4 | nicht anwendbar | 4 | 0 | 2676 / 714 |
| Developer | 2 | 2/2 | 2/2 | 2/2 | 12 | 8 | 24690 / 958 |

Die Developer-Kalibrierungen bestanden jeweils die vollständige Folge
`test_design → red → green → refactor` mit eingefrorenen Tests, tatsächlich
beobachtetem fachlichem Rot und unabhängig ausgeführter Projektabnahme.
Die Reviewer-Kriterien wurden korrekt entschieden; beim fehlerhaften Stand
blieb die bekannte Grenze des exakten Finding-Matchers sichtbar. Das war kein
Anlass, Referenzformulierungen in den Modellkontext zu geben.

## Pilotergebnisse

Alle **15** begonnenen Mess-Episoden sind enthalten und technisch `completed`.
Keine blieb `not_started`; es gab keinen Timeout, Budgetabbruch, Format- oder
Infrastrukturfehler in dieser Messrunde. Die Kalibrierungen sind aus diesen
Pilotwerten ausgeschlossen.

| Rolle / Fall | Messungen | Kriterien korrekt | Runner-Qualität bestanden | Prozess bestanden | Dauer: Mittel ± Stichprobenstandardabweichung |
| --- | ---: | ---: | ---: | ---: | ---: |
| Reviewer, Grenzfehler | 5 | 5/5 (`fail`) | 0/5 | nicht anwendbar | 12.985 ± 0.107 s |
| Reviewer, konform | 5 | 5/5 (`pass`) | 5/5 | nicht anwendbar | 3.093 ± 0.057 s |
| Developer | 5 | 5/5 (`fee=pass`) | 5/5 | 5/5 | 33.444 ± 4.390 s |

| Rolle | Modellaufrufe | Werkzeugergebnisse | Eingabetokens | Ausgabetokens |
| --- | ---: | ---: | ---: | ---: |
| Reviewer-Pilot | 10 | 0 | 6690 | 1785 |
| Developer-Pilot | 30 | 20 | 61938 | 2577 |

Die Developer-Episoden lieferten jeweils Produktionscode, ausführbare EBT-Tests
und Nutzungshinweise. Die unabhängige fachliche und die Prozessabnahme bestanden
in allen fünf Wiederholungen. Je Episode wurden sechs Modellaufrufe und vier
Werkzeugergebnisse archiviert. Diese Ergebnisse gelten für die ausgewählte
kleine Aufgabe und diese Autorreferenz.

Der Reviewer entschied alle zehn Kriterien wie die Autorreferenz. Die fünf
Grenzfehlerberichte verwenden jedoch andere Findingformulierungen als die
Referenz. Der v1-Evaluator wertet dies als exakte Precision/Recall von 0 und
`quality_passed=false`; die konformen Fälle bestehen. Daraus lässt sich keine
semantische Finding-Präzision oder -Recall ableiten. Eine blinde menschliche
Zuordnung wurde nicht durchgeführt. Die getrennten Kriteriumsentscheidungen
bleiben sichtbar und ersetzen diese Nachbewertung nicht.

Insgesamt enthalten Kalibrierung und Pilot **56** interne Modellaufrufe mit
**95994 Eingabe- und 6034 Ausgabetokens**. Mit den zwei separat archivierten
Vorprüfungen wurden **58 echte Inferenzaufrufe** durchgeführt. Ein Gesamtscore
über beide Rollen wird nicht berechnet. Die fünf Wiederholungen derselben
Aufgaben erlauben keine allgemeine Modell- oder Produktleistungsbehauptung.

## Nachweise und Wiederholung

Der tatsächlich ausgeführte Aufruf aus `/tmp` war:

```bash
/tmp/cubie-agent-5-5-runtime/bin/python -I -m ollama_agents.pilot.live \
  /home/symphonie/.local/share/cubie/agent-5-5-20261110 --exploratory
```

Das Studienverzeichnis enthält `study.json`, die vier vollständigen
Runnerarchive, vier eingefrorene Sets einschließlich Kalibrierungskopien,
21 externe Adapterarchive, Vorprüfungen, Hardware-/Providerbeobachtungen,
Konfigurationen und getrennte Zusammenfassungen. Das abschließende
`evidence-manifest.json` bindet **1756 Dateien** per SHA-256. Alle vier
Runnerarchive, ihre Einzelfallbelege und sämtliche 21 über stderr gebundenen
externen Manifeste wurden nachgeprüft.

Gemessenes Wheel: SHA-256
`f14b47b0a1baa89043f05a9da07febb577feea532fa6da0f5ec30046e066ef28`.
Der gemessene Stand bleibt mit diesem Wheel unverändert erhalten. Die
abschließende Produktfassung enthält zusätzlich strengere Prüfungen von
Kalibrierungsstatus und Dateimodi sowie aufgeteilte Export-/CLI-Funktionen und
den erweiterten Leitfaden. Rollenadapter, Prompts und Parameter sind identisch;
die laufende Messung wurde dafür nicht verändert oder neu gestartet.

Abschließendes Wheel: SHA-256
`caab3d7de8d6b98331ce6fc7ff6acb6c15f8db695f8b98207ceb9169f3d959b9`.

Die Rohdaten werden dauerhaft außerhalb des Repositories unter
`/home/symphonie/.local/share/cubie/agent-5-5-20261110` aufbewahrt. Die
maschinelle Ergebnistabelle liegt daneben unter `agent-5-5-analysis.json`.
Das gemessene und das abschließende Wheel werden getrennt zusammen mit
Prüflogs und den Rohdaten archiviert. Die Archivkennung und abschließenden
Prüfergebnisse stehen im [§5.5-Abnahmenachweis](../../tests/docs_tmp/AGENTEN_CASES_5_5.md).

Die Produktfunktion ist offline und aus dem Wheel geprüft; die tatsächliche
explorative Messung ist durchgeführt. **Menschliche Referenzaufnahme, blinde
semantische Nachbewertung und offizielle methodische Pilotabnahme bleiben offen.**
