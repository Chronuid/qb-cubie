# Kleiner EBT-Smoke-Test mit echtem Ollama

Aus dem Repositorywurzelverzeichnis ausdrücklich starten:

```bash
CUBIE_RUN_OLLAMA_SMOKE=1 .venv/bin/python -m pytest tests/live_ollama -q
```

Voraussetzungen: erreichbares Ollama, installiertes `gemma4:12b`, die normale
Projekt-Testumgebung. Optional setzt `CUBIE_OLLAMA_ENDPOINT` den Server statt
`http://localhost:11434`. Der Test lädt kein anderes Modell und installiert nichts.
Ohne Freischaltung werden beide Cases übersprungen; die bestehenden Offline-Tests
behalten ihre Netzwerksperre. Sammlung führt keine HTTP-Aufrufe aus.

Zwei konkrete EBT-Verträge prüfen den vorhandenen konformen und fehlerhaften
Markup-Renderer. Erwartet werden `pass/pass` beziehungsweise `fail/pass`, die
vollständige Quellenliste, unveränderte Originalhashes, der korrekte Hash des
Reviewartefakts und gemessene positive Tokenzahlen. Der aktuelle Vertrag verlangt zusätzlich
für jeden Fehlerbefund im `impact` sowohl `&amp;` als erwartete Maskierung als auch
ein weiteres unmaskiertes `&` als Eingabe-/Verhaltensbeleg. Beim Fehlerfall muss der Befund
`markup_escaping` am Symbol `escaping.py:escape_text` liegen. Formulierungen werden
nicht mit privaten Referenztexten abgeglichen. Der bestehende v1-Protokollvalidator
prüft zusätzlich das Abschlussereignis.

Der echte `OllamaClient` verwendet den normalen HTTP-Transport, ohne Replay oder
Mock. Die Optionen sind `temperature=0`, `seed=42`, `num_ctx=16384`,
`num_predict=2048`, `think=false`. Je Fall gelten 300 Sekunden, maximal sechs
Modellaufrufe und zwölf lokale Werkzeugaufrufe; Reparaturen zählen mit.

Im pytest-Tempverzeichnis bleiben `provider.json` (Version, Modellliste mit Digest,
Ladezustand und Optionen), `provider-after.json`, `archive.json`, das vollständige
Adapterarchiv sowie der Originalworkspace mit `review.json` erhalten. Neben dem
Workspace liegen `event.json` und der persistierte EBT-Bericht `ebt.json`, auch bei
einem abgeschlossenen negativen EBT-Ergebnis. Zur bewussten Aufbewahrung kann man
`--basetemp=/tmp/mein-eindeutiger-smoke-lauf` ergänzen; pytest leert ein bereits
vorhandenes Basistempverzeichnis beim nächsten Lauf. Für jeden Versuch einen neuen
Pfad verwenden und die Belege bei Bedarf dauerhaft kopieren.

## Erster tatsächlicher Lauf am 10. November 2026

Beide Cases bestanden mit Ollama **0.40.2**, `gemma4:12b`, Quantisierung
**Q4_K_M**, Digest
`4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
Gesamte pytest-Laufzeit: **33,98 Sekunden**.

| Fall | Modellaufrufe | Eingabe-/Ausgabetokens | Ergebnis |
| --- | --- | --- | --- |
| Konform | 2 | 2210 / 458 | `pass/pass`; eine ungültige Befundzuordnung wurde in der erlaubten Korrektur behoben. |
| Fehlerhaft | 1 | 1090 / 201 | `fail/pass`; fehlende Ampersand-Maskierung am richtigen Symbol erkannt. |

Die Belege dieses Laufs liegen lokal unter
`/tmp/cubie-reviewer-live-20261110-a`. Der Test ist ein Anschlussnachweis für zwei
veröffentlichte Beispiele, kein repräsentativer Modellvergleich. Der fehlerhafte
Fall enthält als `impact` lediglich `High`: Die Kriterienentscheidung und Ursache
stimmen, eine konkrete fachliche Auswirkung ist damit noch nicht ausreichend
beschrieben. Der Smoke-Vertrag prüft die Entscheidungs- und Quellenbindung;
semantische Befundqualität bleibt separat menschlich zu bewerten.

## Überarbeitung zu `reviewer-v2`

Der ursprüngliche Befund `impact="High"` war fachlich unzureichend. Fünf neue
Offline-EBT-Cases reproduzieren diese Lücke und prüfen Ablehnung oder erfolgreiche
Korrektur von Schweregraden/Platzhaltern. Der Prompt und die Feldbeschreibungen
verlangen jetzt Ursache, Eingabe, tatsächliches Verhalten und erwartetes Verhalten;
der Korrekturschritt sieht die abgewiesene Antwort samt konkretem Fehler.

Der Live-EBT prüft nun zusätzlich die oben beschriebene inhaltliche Mindestevidenz.
Das ist eine konkrete Erwartung für diese Aufgabenfamilie und keine automatische
semantische Bewertung beliebiger Freitexte. Die menschliche Nachbewertung bleibt
für die allgemeine Befundqualität maßgeblich.

Der abschließende echte Lauf mit dem verschärften Vertrag bestand mit **2 Cases
in 16,35 Sekunden**, je einem Modellaufruf und ohne Korrektur. Der konforme Fall
verbrauchte 1184/111 Eingabe-/Ausgabetokens, der fehlerhafte 1180/241. Im Fehlerfall
nennt das Modell die Eingabe `A & B`, die tatsächliche Ausgabe
`<span>A & B</span>` und die erforderliche Maskierung `&amp;`. Ursache und Ort sind
die fehlende Ersetzung in `escaping.py:escape_text`.
Belege: `/tmp/cubie-reviewer-live-20261110-v2-b`.

## Ein vollständiger Benchmark–Ollama–RBT-Lauf

Nur diesen zusätzlichen EBT-Test starten:

```bash
CUBIE_RUN_OLLAMA_SMOKE=1 .venv/bin/python -m pytest \
  tests/live_ollama/test_benchmark_rbt_live.py -q
```

Der Test erstellt ein temporäres Szenariopaket aus dem konformen Markup-Fall,
eine Agenten-TOML und eine Laufzeitkonfiguration. Dann ruft sein EBT-Target die
öffentliche Funktion `run_suite` auf. Der echte Runner startet
`examples/ollama-agents/reviewer_process.py` als JSONL-Prozess, bestätigt im
Handshake Modellkennung, lokalen Digest, Ollama-Version, Adapterversion,
Parameter und Hash des Prompt-/Schema-/Werkzeugpakets. Beim Handshake erfolgt
keine Inferenz. Erst die Reviewanfrage startet den echten Modellaufruf.

Konkrete Erwartungen sind `completed`, abgeschlossene unabhängige Bewertung,
`quality_passed=True`, die beiden `pass`-Entscheidungen und `rbt.json` mit
`passed=True`. Der an RBT übergebene Bericht muss vollständig mit dem unabhängig
ausgewerteten Bericht übereinstimmen. Zusätzlich prüft der EBT-Vertrag sämtliche
Runner-Manifesthashes, positive gemessene Tokens und echte Ollama-Rohantworten im
separaten Adapterarchiv. Es werden weder Runner, Evaluator noch RBT ersetzt.
Das Zeitbudget beträgt 180 Sekunden für eine Episode, mit maximal sechs
Modell- und zwölf internen Werkzeugaufrufen.

Der Fall ist bewusst konform: Er prüft die vollständige Verbindung ohne den
bekannten exakten Freitextabgleich von Fehlerbefunden. Fehlererkennung bleibt in
den beiden direkten Live-Cases und den Offline-Gegenproben geprüft. Dieser Test
belegt keinen durchgehenden Fehlerfall mit semantischer Nachbewertung und keine
Wheel-Installation außerhalb des Checkouts.

Der abschließende echte Pipeline-Lauf am 10. November 2026 bestand in **4,96
Sekunden**, mit `gemma4:12b` und einer regulären RBT-Freigabe. Der EBT-Bericht,
die vollständigen Runner-Artefakte und das separate Modellarchiv liegen lokal
unter `/tmp/cubie-reviewer-pipeline-20261110-c`. Die Offline-Abnahme umfasst jetzt
199 bestandene Agenten-Cases; ohne Freischaltung werden drei Live-Cases übersprungen.
