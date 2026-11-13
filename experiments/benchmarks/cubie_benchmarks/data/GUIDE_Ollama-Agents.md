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

## Kalibrierung und eingefrorene Messung

Für ein ausgewähltes Set zuerst `repetitions=2` mit ausreichend großen
Gesamtbudgets konfigurieren und ausführen. Anschließend das Pilotset mit
`repetitions=5` vorbereiten. Nach der Kalibrierung sind Parameteranpassungen
erlaubt; Aufgaben, Bedingungen und fachliche Referenzen bleiben gleich.

```bash
python -m ollama_agents.pilot --suite sets/pilot.toml \
  --calibration results/calibration/ARCHIV-ID --destination frozen-pilot
cubie-bench run-frozen frozen-pilot --output results/pilot --format json
cubie-bench summarize-pilot results/pilot/ARCHIV-ID --format json
```

Die Freigabe prüft alle übergebenen Kalibrierungsarchive einschließlich erfolgloser
Versuche. Sie verlangt zwei tatsächlich gestartete Wiederholungen je Aufgabe,
Agent und Bedingung sowie genau fünf geplante Messwiederholungen. Weitere Runden,
Dubletten, beschädigte Archive und veränderte Aufgaben werden abgewiesen.
Kalibrierungsergebnisse gehen nicht in die Pilotstatistik ein. Das Messpaket
enthält vollständige Kopien der Kalibrierungsarchive und deren Hashbindung.

Offizielle Piloten erlauben `author_checked`-Referenzen ohne menschliche
Prüfungen je Fall. Diese Prüfungen sind optional und keine Voraussetzung für
Vollständigkeit. `independently_checked` erfordert weiterhin zwei verschiedene
menschliche Zustimmungen mit privaten Belegdateien. Das Pilotmanifest weist
diesen Status nur aus, wenn alle ausgewählten Referenzen ihn tragen; sonst
steht dort `author_checked`. Die Einzelstatus bleiben erhalten.
`--exploratory` kennzeichnet das Messziel unabhängig vom Prüfstatus. Die
Funktion erfindet keine menschlichen Belege.

Die öffentlichen Smokes lassen sich als vollständig archivierte explorative
Messreihe mit zwei Kalibrierungs- und anschließend fünf Messwiederholungen ausführen:

```bash
python -m ollama_agents.pilot.live /absoluter/neuer/studienpfad --exploratory
```

Das startet echte Modellaufrufe: zwei unbewertete Vorprüfungen, 6 Kalibrierungs-
und 15 Mess-Episoden, seriell mit identischen Rollenparametern. Der Ablauf legt
neue Sets an, friert sie vor Ausführung ein und speichert Modellmetadaten,
Ladezustand, GPU-Beobachtungen an Stapelgrenzen, Rohantworten, interne Aufrufe,
Runnerbelege und getrennte Zusammenfassungen. Der neue Zielpfad darf nicht
existieren. `study.json` und `interrupted.json` dokumentieren den Ablauf auch
bei Abbruch; Fehler werden nicht durch automatische Ersatzversuche verdeckt.

Externe Adapterarchive liegen absichtlich dauerhaft unter dem absoluten
Studienpfad, außerhalb temporärer Ausführungskopien. Gemeinsam mit allen
Runnerarchiven, Messpaketen und dem installierten Wheel aufbewahren. Ein
verschobenes Studienarchiv bleibt anhand relativer Hashmanifeste prüfbar;
für eine erneute Ausführung müssen absolute Belegziele ausdrücklich neu
konfiguriert und unter einer neuen Messidentität eingefroren werden.

Die Messreihe verwendet bekannte öffentliche Entwicklungsaufgaben und ist
explorativ. Eine offizielle Referenzaufnahme, unabhängige unbekannte Aufgaben,
blinde semantische Finding-Nachbewertung und allgemeine Leistungsaussagen sind
damit nicht verbunden.
