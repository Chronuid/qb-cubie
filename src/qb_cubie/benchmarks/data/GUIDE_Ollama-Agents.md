# Installierte Ollama-Agenten verwenden

Voraussetzungen: Python ab 3.13, `qb-cubie[benchmarks]` und ein laufender
Ollama-Server mit explizit installiertem `gemma4:12b`.

Außerhalb des Cubie-Checkouts ausführen:

```bash
python -m pip install '/absoluter/pfad/qb_cubie-0.0.3-py3-none-any.whl[benchmarks]'
cubie-bench init-ollama ./ollama-demo
cd ollama-demo
cubie-bench validate package --check-references
cubie-bench validate-agent agents/reviewer.toml
cubie-bench validate-agent agents/developer.toml
cubie-bench plan --suite sets/reviewer.toml
cubie-bench plan --suite sets/developer.toml
# Ab hier echte Inferenz, seriell ausführen:
cubie-bench run --suite sets/reviewer.toml --format json
cubie-bench run --suite sets/developer.toml --format json
```

`init-ollama` akzeptiert `--endpoint` und `--model`. Es liest `/api/version`,
`/api/tags`, `/api/ps` und `/api/show`, ohne Modellladen oder Inferenz.
Die Rohmetadaten einschließlich Quantisierung und Ladezustand stehen in
`provider.json`; `installation.json` bindet sie per SHA-256 und vermerkt das
installierte Wheel. Unbekannte Modellnamen führen zum Fehler, ohne Ersatzmodell
oder automatischen Download. Ein vorhandenes Ziel wird nicht überschrieben.

Die Modellparameter sind Kalibrierungswerte: Temperatur 0, Seed 42,
Kontext 16384, Ausgabelimit 2048 (Reviewer) beziehungsweise 4096 (Developer),
`think=false`. Unterstützung und Laufzeit sind vor Messungen separat zu prüfen.
Nach Modellwechsel oder Adapteränderung ein neues Beispiel exportieren.
Modell-Digest, Ollama-Version, Adapterversion, Parameter und Prompt-Hash sind in
Agenten-TOML und Laufzeit-JSON identisch; der Handshake bestätigt diese Werte
ohne Inferenz. Die Beobachtung bei Export ist keine laufende Überwachung des
Serverzustands. Vorwärmen und konkurrierende GPU-Nutzung separat dokumentieren.

Das Reviewer-Set enthält den korrekten und den fehlerhaften Versandgrenzfall;
das Developer-Set enthält eine vollständige Entwicklungsepisode mit EBT-Tests.
Diese kleinen öffentlichen Aufgaben sind Installations-Smokes und keine neue
unabhängige Modellmessreihe. Ihre Referenzen sind `author_checked`.
Der Reviewer-Evaluator gleicht freie Finding-Texte exakt ab: Ein fachlich
richtiger anders formulierter Befund kann deshalb `quality_passed=false`
erhalten. Exitcode 4 bedeutet fehlgeschlagene Qualitätsgates, Exitcode 3 einen
unvollständigen Lauf. Beides mit den einzelnen Berichten untersuchen.

`results/` enthält Runner-Belege, Kriterienentscheidungen, unabhängige Abnahmen
und Rot-/Grün-Nachweise. `adapter-evidence/` enthält je Episode die konkreten
Modellanfragen, Rohantworten, Aktionen, Werkzeugergebnisse, Tokens und Hashes.
Die kurzen stderr-Einträge im Runnerarchiv binden die externen Manifeste.
Beide Verzeichnisse gemeinsam mit `provider.json`, `installation.json`, den
Konfigurationen und dem verwendeten Wheel aufbewahren. Interne Aufrufe lassen
sich anhand der Schritte mit Modellantwort beziehungsweise Werkzeugergebnis
nachzählen; Phasenverbräuche stehen zusätzlich in den Runner-Ereignissen.

Das Beispiel verwendet relative Pfade für Adapter und Archive und kann auf
demselben Rechner verschoben werden. Der Python-Interpreter im Agentenkommando
ist bewusst absolut gebunden; bei Umgebungswechsel neu exportieren.
Das exportierte `adapter/process.py` lädt ausschließlich den ausdrücklich
exportierten Adapterpfad unter isoliertem Python (`-I`). Tests laufen in Kopien
und verwenden die installierte Cubie-Version.

Die automatischen Wheel-Cases verwenden einen lokalen HTTP-Replay ohne Modell.
Sie weisen Installation und Protokoll nach; tatsächliche Modellleistung muss
mit obigen expliziten Inferenzaufrufen separat beobachtet werden.
