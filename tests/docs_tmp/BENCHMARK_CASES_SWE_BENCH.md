# EBT-Abnahmecases: automatisierter SWE-bench-Loader

Stand: 11. November 2026. **Produktimplementierung vorhanden; die ursprüngliche
Rotphase bleibt unten als Historie dokumentiert. Keine reale SWE-bench-Messung.**
Der [Nutzungsleitfaden](../../docs/GUIDE_Benchmark-SWEbench.md) beschreibt den
Developer-Agent-Durchstich und seine Laufzeitvoraussetzungen.

Maßgeblich sind die [Loader-Anforderungen SBL-01 bis SBL-08](../../docs/misc/SWE_BENCH_LOADER_ANFORDERUNGEN.md).
Der Ausbau ist im [Benchmark-Konzept §10.6](../../docs/misc/BENCHMARK_KONZEPT.md#106-datensatzausbau-durch-swe-bench)
und in der [Liste offener Punkte](../../docs/misc/OFFENE_PUNKTE_Benchmarks-Agenten.md#datensätze-verbessern-automatisierter-swe-bench-import)
verlinkt. Er ersetzt weder die Basisdatensatz-Abnahme noch unverbrauchte Messaufgaben.

## Öffentlicher Vertrag

```python
plan_swebench_import(config, *, source=None) -> dict
import_swebench(config, destination, *, source=None) -> dict
validate_swebench_references(package, *, executor=None) -> dict
```

Die Funktionen sind über `qb_cubie.benchmarks` erreichbar. Planer und
Import führen keinen Projektcode aus; nur die ausdrückliche Referenzvalidierung
darf den begrenzten externen Executor starten. Der Export benötigt Erweiterungen
der bestehenden Paketvalidierung für `external.swebench_v1`, den Referenzstatus
`unvalidated` und `process_profile="issue_resolution"`.

Die neuen [ausführbaren Cases](../benchmarks/swebench) verwenden die bestehenden
EBT-Hüllen `accepted` und `rejected`, `WorldState` und `ExceptionExpectation`.
Beide Hüllen prüfen `RunTrace.evaluation` und das Urteil der einzelnen Spur.
Fehlende öffentliche Funktionen erzeugen normale Assertion-Fehlschläge;
es gibt keine Skips, `xfail`, Platzhalterimplementierungen oder neu eingeführten
Produktfunktionen. Die Absicht ist eine echte rote Abnahmesammlung vor der Umsetzung.

## Kriterienzuordnung

| Anforderung | Ausführbare Cases und Gegenproben |
| --- | --- |
| **SBL-01: Automatische Beschaffung** | [test_source_adapter.py](../benchmarks/swebench/test_source_adapter.py), 5 Cases: gepinnter Abruf mit Revision/Split/Cache, Verwendung des gelieferten Snapshots beim Paketexport, kein Aufruf des entfernten Adapters im Offlinefehlerfall, diagnostischer Transferabbruch ohne veröffentlichtes Ziel, Zurückweisung einer falschen Quellrevision. |
| **SBL-02: Schema und Quellintegrität** | [test_selection.py](../benchmarks/swebench/test_selection.py): drei offizielle Quellen, native und JSON-kodierte Testlisten, ungültige Pflichtfelder und Commitwerte, leere/ungültige/doppelte Test-IDs, überlappende Testmengen, doppelte Instanzen, fehlende Lizenzen, beschädigte Quelldatei und falsche Revision. |
| **SBL-03: Auswahl und Identität** | Dieselbe Datei: UND-Verknüpfung von Filtern, unbekannte explizite IDs auch bei `skip`, reproduzierbare begrenzte Auswahl nach Zeilenumordnung mit dokumentierter Auslassung, Bindung der Planidentität an Gold-/Test-Patch, Harness und Hints; Fehler für veränderliche Revisionen, falsche Typen, nichtpositive Limits und ungeeignetes Prozessprofil. Insgesamt 41 Auswahl-/Schemacases. |
| **SBL-04: Ausgangsstand und Referenzschutz** | [test_import.py](../benchmarks/swebench/test_import.py): echter Basiscommit statt späterem Git-HEAD, unveränderter Quellcheckout, keine Git-Historie oder nachträglichen Gold-Tests im sichtbaren Baum; Gold-/Test-Patches privat, Hints nur nach ausdrücklicher Aktivierung, Evaluationsskripte und unbekannte Zusatzfelder bleiben privat. |
| **SBL-05: Paket und Herkunft** | Dieselbe Datei: Cubie-`development` bei erhaltenem Upstream-`test`, potenzielle Bekanntheit, Lizenz-/Quellangaben, gemeinsame Projektgruppe für Issues desselben Repositorys, externer Evaluator statt erfundener Review-/Mutantenreferenzen, zunächst `unvalidated`, Unicode-Erhalt, verschiebbares Paket ohne Hostpfade, identische Paketbytes und Integritätsfehler bei nachträglich geändertem Gold-Patch. |
| **SBL-06: Fehler und Transaktionen** | Dieselbe Datei: vorhandene eigene Inhalte bleiben unverändert; fehlender Commit hinterlässt kein Teilpaket; `skip` berichtet Instanz, Stage und Ursache und liefert `partial`; vollständiges Scheitern liefert kein leeres Paket; Pfadausbruch, unsicherer Symlink und Git-Submodule werden abgelehnt. Insgesamt 15 Importcases. |
| **SBL-07: Referenzprüfung** | [test_reference_validation.py](../benchmarks/swebench/test_reference_validation.py), 19 Cases: getrennte Basis-/Gold-Läufe, vollständige Testmengen, gebundene Belege und Image-Digest; bereits grüner Basisstand, rotes Gold, Regression, fehlende/übersprungene Tests, Timeout, Setup-/Patch-/Collectionfehler, fremde Instanz, veraltete Antwort, fehlende/manipulierte/ausbrechende Belege und veränderliches Image erhalten keine Gutschrift. Neue IDs bei erneuter Prüfung; Quellpaket bleibt unverändert; Strukturprüfung führt keine Referenz aus; fehlende Containerlaufzeit verbietet Hostfallback. |
| **Gegenprobe der Fixture** | [test_fixture_material.py](../benchmarks/swebench/test_fixture_material.py), 2 Cases: Der tatsächliche lokale Test-Patch ergibt am Basiscommit einen fachlichen Fehler bei bestandener Regression; der tatsächliche Gold-Patch macht beide Tests grün. Die Ergebnisse werden ebenfalls über EBT geprüft. |

## Belegmaterial und Aussagegrenzen

Die [Fixture](../benchmarks/swebench/conftest.py) erzeugt in pytest-Temporärablagen
ein echtes lokales Git-Repository mit defektem Basisstand und späterem
Lösungscommit. Drei synthetische Issue-Zeilen teilen sich dieses Projekt;
standardmäßig werden zwei importiert. Diese Wiederverwendung ist beabsichtigt,
um eine künstliche Vergrößerung der unabhängigen Projektzahl zu erkennen.
Das Material ist keine Kopie realer SWE-bench-Aufgaben. Die Quell-/Harnessrevisionen
und Lizenzangaben sind ausdrücklich synthetische Testdaten.

Das Basisprojekt enthält zusätzlich eine `setup.py`, die bei Ausführung sofort
scheitert. Planen/Importieren müssen sie ausschließlich als Datei behandeln.
Gold-Lösung, private Tests, Hints und zusätzliche private Quellfelder enthalten
unterschiedliche Sentinels. Exportprüfungen suchen sie im sichtbaren Projekt
und Auftrag. Dies prüft den erzeugten Exportbaum; der tatsächliche spätere
Agentenprozess und dessen Dateisystemzugriff werden damit noch nicht geprüft.

Python-Socketverbindungen sind in dieser Sammlung gesperrt. Die Quellanbindung
wird durch einen lokalen Snapshotlieferanten ersetzt; kein Hugging-Face- oder
GitHub-Download wird behauptet. Die Referenzcases verwenden einen synthetischen
Executor, der Teststatus und gehashte Belegdateien liefert. Sie prüfen die
Loaderauswertung dieser Antworten, keine reale Containerisolation oder echte
Harness-Ausführung. Nur die beiden Fixture-Kontrollen führen das kleine lokale
Testprojekt tatsächlich per pytest aus; fremder Code wird nicht bezogen.

## Erste Ausführung

Aus der Repositorywurzel:

```bash
.venv/bin/python -m pytest tests/benchmarks/swebench -q --tb=short
```

Ergebnis: **2 bestanden, 80 fehlgeschlagen** in 3,22 Sekunden;
**82 Cases gesammelt**, keine Sammlungs- oder Setupfehler. Die zwei grünen
Cases bestätigen das echte Rot/Grün-Verhalten des synthetischen Materials.
Die 80 roten Cases verlangen die noch fehlenden Loader-APIs und deren
Integration; sie sind keine Behauptung bereits implementierter Funktionalität.

```bash
.venv/bin/ruff check tests/benchmarks/swebench
git diff --check
```

Beide Prüfungen sind ohne Befund. Die gesamte neue Sammlung ist bewusst Teil
der regulären Testsammlung; bis zur Produktumsetzung bleibt sie rot.

Die bestehende Benchmark-Sammlung wurde getrennt geprüft:

```bash
.venv/bin/python -m pytest tests/benchmarks --ignore=tests/benchmarks/swebench -q
```

Ergebnis: **554 bestanden, zwei bestehende Skips** in 132,22 Sekunden. Für diese
Anforderungsergänzung wurde kein Produktcode verändert und kein neuer Wheel-
oder vollständiger Repositorylauf ausgeführt. Die relativen Dateilinks der
neuen Spezifikation und Abnahmematrix wurden auf vorhandene Ziele geprüft.

## Weitere Abnahme nach Implementierung

Die folgenden Anforderungen sind spezifiziert, aber noch nicht durch ausführbare
End-to-End-Cases oder einen realen Betriebsnachweis abgedeckt. Die vollständige
Lieferung darf nicht allein anhand der oben genannten Offline-Cases freigegeben werden:

| Offener Nachweis | Erforderlicher Befund |
| --- | --- |
| Produktiver Downloadadapter (SBL-01) | Tatsächlicher revisionsgebundener Abruf aller unterstützten Quellen, kontrollierte Transferabbrüche/Wiederholungen und atomare Cacheveröffentlichung; identische Offlinewiederholung. |
| Weitere Normalisierungs-/Auswahlgrenzen (SBL-02/03) | Fehlende/leere optionale Setupcommits, leere zulässige `PASS_TO_PASS`-Menge, sichere interne Symlinks, Dateimodi und exakt dokumentierte Hashrangfolge mit festem Erwartungsvektor. |
| Containerharness (SBL-07) | Reale Basis-/Gold-Abnahme, falscher Agentenpatch und sicher unterscheidbare Infrastrukturfehler; Netzwerk-/Mount-/Ressourcengrenzen, Ende aller Kindprozesse und keine veraltete Cacheantwort. |
| Runner/Planner/Freeze/Reporting (SBL-08) | Mehrdateien-Reparatur mit getrenntem Evaluator; keine Referenzen in Requests oder Workspace; gebundene Referenzfreigabe vor Agentenstart; Erkennung überlappender Full-/Lite-/Verified-Instanzen auch über Namespaces; Qualität getrennt von `process_passed=null`; Herkunft und Gruppen im eingefrorenen Archiv. |
| Installation (SBL-08) | Durchstich aus installiertem Wheel außerhalb des Checkouts, einschließlich Export, Verschieben, Laden, Einfrieren, Ausführen und Auswerten eines importierten Pakets. |

Eine Modellantwort ist für diese technischen Nachweise nicht notwendig.
Eine anschließende Leistungsstudie benötigt zusätzlich begründete Fallauswahl,
eingefrorene Konfiguration und die bestehenden methodischen Nachweise.

## Produktimplementierung und aktuelle Offline-Nachweise

Der Produktcode exportiert die drei Loader-APIs und integriert
`external.swebench_v1` sowie `issue_resolution` in Paketprüfung, Suite,
Referenzfreigabe, Freeze, JSONL-Abgabe und Reporting. Der mitgelieferte
Ollama-Developer besitzt einen getrennten Reparaturmodus mit vollständiger
Patch-Abgabe. Der [Leitfaden](../../docs/GUIDE_Benchmark-SWEbench.md) beschreibt
Konfiguration und Laufzeitvoraussetzungen.

Ergänzende Cases liegen in
[test_boundaries.py](../benchmarks/swebench/test_boundaries.py),
[test_runtime_policy.py](../benchmarks/swebench/test_runtime_policy.py) und
[test_repair.py](../ollama_agents/developer/test_repair.py). Sie prüfen unter
anderem den dokumentierten Hashrang, leere Setup-/Regressionsangaben, sichere
Git-Symlinks und Dateimodi beim Import, Git-Ersetzungsreferenzen und fremde
Git-Umgebungsvariablen, private Manifesthashes, gebundene Referenzberichte,
Überlappung über Namespaces, verschiebbare Belege und Freeze ohne Agentenstart.
Ein weiterer Durchstich verwendet den echten Runner und echten JSONL-Transport
mit ausdrücklich synthetischen Container-/Executorgrenzen: Import →
Referenzbericht → Freeze → Patch-Abgabe → Auswertung → Pilotbericht. Seine
Kontrollen schließen Referenzmaterial in Request und sichtbarem Workspace aus
und bestätigen eine einzige unabhängige Repositorygruppe ohne TDD-Gutschrift.
Docker-Kommandotests prüfen Netzwerk-, Mount-, Ressourcen- und Abbruchpolitik;
sie ersetzen keinen realen Containernachweis.

Geprüft:

- `pytest tests/benchmarks tests/ollama_agents -q --tb=short`:
  **984 bestanden, zwei bestehende Skips**, 183,48 Sekunden. Danach ergänzte
  Git-/Requestbindungs- und vollständige Runner-Cases wurden gesondert geprüft.
- `pytest tests/benchmarks/swebench tests/ollama_agents/developer/test_repair.py -q --tb=short`:
  **101 bestanden**, 6,32 Sekunden am abschließenden Produktstand.
- Wheel gebaut und in ein eigenes Verzeichnis unter `/tmp` installiert.
  Dieselben **101 Offline-Cases bestanden in 6,18 Sekunden** außerhalb des
  Checkouts gegen die installierten Cubie- und Repair-Module; dies bleibt eine
  synthetische Integration.
- Ruff für alle in dieser Umsetzung geänderten Python-Dateien und
  `git diff --check`: ohne Befund. Zwei bereits vorhandene Importsortierbefunde
  außerhalb dieser Umsetzung (`execution/_pytest.py`, `measurement/_bundle.py`)
  wurden nicht verändert.

Reale Hugging-Face-/GitHub-Beschaffung aller drei Quellen, tatsächliche
Containergrenzen und der komplette installierte Modelllauf bleiben getrennte
Integrationsnachweise. Die Herkunfts-/Lizenzprüfung, provisionierten
Harnessimages und das Digest-Image des Reparaturadapters sind dabei echte
Voraussetzungen und werden durch die synthetischen Belege nicht ersetzt.
