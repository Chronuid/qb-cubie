# Eigenes Benchmark-Paket: Versandkosten

Dieses eigenständige MIT-Beispiel ist Abnahmematerial für Phase 10.3.
Es verwendet Namespace `shop`, eigene Typen/Tags und vorhandene Evaluatoren.
Die Referenzen sind `author_checked`, keine unabhängige menschliche Freigabe.

Enthalten sind ein korrekter Review, ein Review mit Grenzfehler und eine
Erstentwicklung mit unabhängiger pytest-Abnahme. Bei 5000 Cent Warenwert muss
der Versand kostenlos sein; darunter kostet er 499 Cent. Die fehlerhaften
Varianten verwenden einen strikten Vergleich und scheitern an dieser Grenze.

Der deterministische Peer unter `agents/jsonl_agent.py.txt` enthält eigene
Antworten und Tests, keine Modellanbindung. Er liest keine Evaluatordaten.
Sein Erfolg belegt ausschließlich die Integration. Der Testaufbau kopiert das
Paket in ein temporäres Verzeichnis außerhalb des Checkouts und benennt das
Skript in `jsonl_agent.py` um. Auftrag und sichtbarer Code werden getrennt von
den Evaluatordaten an den Agenten exportiert.

Für die Produktabnahme gilt dieser Ablauf:

```bash
cubie-bench init-agent ./agents/current.toml
# command, cwd und capabilities auf den eigenen Prozess einstellen
cubie-bench validate-agent ./agents/current.toml
cubie-bench validate . --check-references
cubie-bench list --package .
cubie-bench init-suite ./sets/team.toml --preset smoke --agent ./agents/current.toml --package .
cubie-bench plan --suite ./sets/team.toml
cubie-bench run --suite ./sets/team.toml
cubie-bench compare ./results/BEFORE ./results/AFTER
```

Diese Kommandos sind implementiert. Das installierte Paket exportiert mit
`cubie-bench init-example ./shipping-demo` ein entsprechendes ausführbares
Beispiel samt Konfiguration und Set. `cubie-bench guide` zeigt das Tutorial.
Details und Fehlerfälle stehen in `../../../docs_tmp/BENCHMARK_CASES_10_3.md` des
Cubie-Repositories. Die lokale Ausführung setzt vertrauenswürdigen Code voraus.
