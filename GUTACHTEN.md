<center>

# Kritisches Gutachten zum Cubie-Projekt

![Cubie](./docs/.assets/cubie-logo-written.png)

Dieses Gutachten bewertet Implementierung, Aussagegrenzen und Entwicklungsbedarf des Cubie-Projekts.

---

</center>

**Stand:** 9. November 2026  
**Untersuchter Stand:** Arbeitsverzeichnis auf Basis von Commit `f3a7f17`, Projektversion `0.0.3`, Python `3.13.12`.

## 1. Gesamturteil

Cubie ist ein interessantes, bereits substanziell implementiertes Werkzeug für deklarative Qualitätssicherung. Sein überzeugendster Nutzen liegt in der gemeinsamen Beschreibung von Eingaben, erwarteten Rückgaben und Dateisystemzuständen. Gerade für Datei-Transformationen und wiederkehrende Akzeptanzszenarien kann das die Testdefinition vereinfachen. Die austauschbaren Arenen, Reviewer und Reporter ergeben eine nachvollziehbare Erweiterungsarchitektur.

Dem stehen erhebliche Schwächen gegenüber: Der theoretische Anspruch übersteigt die tatsächlich nachgewiesenen Garantien. Mehrere reproduzierbare Fehler können Tests unbeabsichtigt bestehen lassen. Die Ausführungsumgebungen sind keine Sicherheitsgrenzen, die Installation und Repository-Struktur sind noch nicht ausreichend auf fremde Rechner ausgerichtet. Der praktische Mehrwert gegenüber gewöhnlichen pytest-Tests ist für einfache Funktionen gering; für komplexere Szenarien muss er durch belastbare Anwendungsbeispiele erst belegt werden.

**Empfehlung:** Als experimentelles Werkzeug für vertrauenswürdigen Code weiterentwickeln und gezielt pilotieren. Als allgemeine, verlässliche Qualitätsinstanz oder Ausführungsplattform für nicht vertrauenswürdigen generierten Code derzeit nicht freigeben. Vor einer Verbreiterung des Funktionsumfangs muss die Korrektheit des Prüfkerns Vorrang erhalten.

## 2. Auftrag, Methode und Aussagegrenzen

Untersucht wurden README, Projektkonfiguration, öffentliche Exporte, EBT- und RBT-Kern, Protokolle, Reporter, beide ausführbaren Arenen, IPC-Codecs, Multiprocessing, Linter-Anbindungen sowie ausgewählte Entwickler- und Nutzungshandbücher. Zusätzlich wurden die vorhandene Testsuite und kleine, vom Projekt unabhängige Reproduktionsskripte ausgeführt. Die unten beschriebenen Stichproben verwenden die vorhandenen APIs; am Implementierungscode wurden keine Reparaturen vorgenommen.

Das Gutachten bewertet den vorhandenen lokalen Stand. Es enthält keine Marktstudie, keine vollständige Sicherheitsprüfung, keinen Test einer veröffentlichten Distribution und keine Messung realer Produktivitätsgewinne. Aussagen zum Nutzen und zur Positionierung sind gutachterliche Einschätzungen, keine empirischen Kundenbefunde. Die Versionsnummer allein bestimmt nicht die Reife.

Im Arbeitsverzeichnis bestanden bereits Änderungen an `pyproject.toml`, `uv.lock` und der versionierten `.venv`; außerdem war eine frühere `GUTACHTEN.md` zur Löschung vorgemerkt. Bewertet wird der tatsächlich vorgefundene Code, nicht ausschließlich der letzte Commit. Das hier geschriebene Gutachten wird nicht automatisch gestagt oder committet.

## 3. Idee und konzeptionelle Tragfähigkeit

### 3.1 Das tragfähige Zentrum

Cubie behandelt Tests als explizite Verträge zwischen Ausgangs- und Zielzuständen. `WorldState` bündelt Funktionsparameter, Rückgabemuster und Dateisystemabbildungen. EBT führt die Zieloperation aus und vergleicht deren Ergebnis mit einem oder mehreren erlaubten beziehungsweise verbotenen Zielzuständen. Reviewer ergänzen Prüfungen, deren Kriterien eine menschliche oder externe Beurteilung benötigen.

Diese Verbindung ist sinnvoll: Ein Dokumentkonverter lässt sich beispielsweise über Eingabedateien, einen Rückgabevertrag und erwartete Ausgabedateien beschreiben. Das kann übersichtlicher sein als wiederholt eigene Fixture-Kopien, temporäre Verzeichnisse und Vergleichslogik zu programmieren. Die standardisierten Diagnosedaten der Linter und die injizierbaren Reporter bieten zusätzliche Integrationsmöglichkeiten.

Der wesentliche Wert liegt damit in **Konventionen, Wiederverwendung und einheitlicher Orchestrierung**. Der Code implementiert keine Suche im Raum aller Programme und keinen Codegenerator. Die Suchraum-Metapher beschreibt eine Motivation; sie ist keine implementierte Produkteigenschaft.

### 3.2 Formale Sprache schafft keine formale Verifikation

README und `docs/GUIDE_Quality-Assurance.md` beziehen sich stark auf Hoare-Logik, Quantoren und verifizierte Lösungsmengen. Die Analogie zur Anordnung „Ausgangszustand – Operation – Zielzustand“ ist didaktisch brauchbar. Sie trägt jedoch keine Behauptung allgemeiner Korrektheit:

- Ein `WorldState` ist ein konkreter Datensatz beziehungsweise ein Ergebnismuster, kein allgemein bewiesenes Zustandsprädikat.
- EBT prüft endlich viele Ausführungen. Es gibt weder einen Beweiskalkül noch eine vollständige Exploration aller zulässigen Eingaben.
- Das Vorhandensein mehrerer unterschiedlicher Beispiele belegt keine „Orthogonalität“. Dafür fehlen ein definiertes Merkmalsmodell und ein Nachweis unabhängiger Dimensionen.
- Ein erfolgreicher Review ist eine Beurteilung unter bestimmten Bedingungen. Er wird durch ein boolesches Ergebnis nicht zum mathematischen Beweis.

Die Dokumentation sollte ausdrücklich zwischen beobachteter Konformität, Testabdeckung und bewiesenen Eigenschaften unterscheiden. Besonders Aussagen, fehlerhafter Code könne dem aufgespannten Raum nicht mehr entkommen, vermitteln eine nicht gedeckte Sicherheit.

### 3.3 Was die Quantoren tatsächlich bedeuten

Für jeden ausgeführten Eingang prüft EBT, ob mindestens ein positiver Zielzustand passt und kein negativer passt. Danach müssen alle Eingangsschritte erfolgreich sein. Vereinfacht:

`für jeden Eingang: (mindestens ein erlaubtes Ergebnis) UND (kein verbotenes Ergebnis)`.

Diese endliche Mengenlogik ist nützlich, aber ihre Grenzen sollten sichtbar bleiben. Bei mehreren Ein- und Ausgängen entsteht keine automatische paarweise Zuordnung. Für `f(1)=2` und `f(2)=4` erlaubt eine gemeinsame Zielmenge `{2, 4}` auch eine vertauschte Implementierung. Korrelierte Fälle benötigen getrennte Verträge oder eine explizite Paarstruktur.

Das Würfelbeispiel prüft nur, ob eine einzelne beobachtete Ausgabe in der erlaubten Menge liegt. Eine Funktion, die immer `1` liefert, besteht ebenfalls. Vollständigkeit des Ergebnisraums, Zufälligkeit und Verteilung werden damit nicht getestet. EBT ersetzt weder generative Tests noch statistische Prüfungen.

## 4. Praktischer Nutzen und Einsatzgrenzen

| Einsatzfall | Einschätzung | Voraussetzung oder Grenze |
| --- | --- | --- |
| Datei- und Verzeichnistransformationen | Größtes erkennbares Potenzial | Klare Vergleichssemantik und robuste Fixtures |
| Wiederholte strukturierte Ergebnisprüfungen | Nützlich | Team akzeptiert die zusätzliche Muster-Sprache |
| Einfache reine Funktionen | Begrenzter Zusatznutzen | Ein gewöhnlicher Assertion-Test ist oft kürzer |
| Strukturierte manuelle Abnahme | Sinnvoll für Experimente | Reviewer-Entscheidung bleibt subjektiv |
| CI mit RBT | Nur mit explizitem automatisiertem Reviewer | Standardreviewer fragt synchron nach Eingaben |
| Bewertung generierten Codes | Als Teil einer Prüfkette denkbar | Unabhängige Testdaten und echte Ausführungsisolation nötig |
| Ausführung fremden, potenziell schädlichen Codes | Derzeit ungeeignet | TempFS und PyVenv begrenzen keine OS-Rechte |

Eine produktive Positionierung wäre: **„Deklarative Akzeptanztests für Python-Funktionen und Datei-Workflows auf Basis von pytest“**. Das ist konkret, prüfbar und näher am vorhandenen Produkt als die umfassende Suchraum- und Verifikationsrhetorik.

Ein Reviewer-Protokoll ist noch keine fertige LLM-Integration. Im untersuchten Kern existieren Terminal- und Tkinter-Reviewer, aber kein integrierter Modelladapter mit Quellenübergabe, Modellversionierung, Wiederholungsstrategie und Bewertungsnachweisen. RBT führt das Target nicht aus und lädt auch nicht automatisch eine übergebene Quelldatei; `_evaluate()` reicht einen String beziehungsweise Namen weiter. Diese Arbeit muss der Reviewer leisten.

## 5. Technische Umsetzung

### 5.1 Stärken

- **Klare Erweiterungspunkte:** `Arena`, `Reviewer`, `Reporter`, `IPCC` und `Multiprocessor` beschreiben wesentliche Schnittstellen. Konkrete Implementierungen lassen sich injizieren.
- **Nachvollziehbare Ausführungsspuren:** `EvaluationTrace` und `RunTrace` erfassen erwartete und beobachtete Zustände, Ergebnisse und Laufzeiten. Das ist eine brauchbare Grundlage für bessere Berichte.
- **Breite Ergebnismuster:** Werte, Typen, Unions, reguläre Ausdrücke, Prädikate und verschachtelte Strukturen unterstützen viele praktische Prüfungen.
- **Aufräumen auch bei Fehlern:** EBT versucht Arena-Ressourcen bei Ausnahmen freizugeben und ergänzt Aufräumfehler als Notiz zur ursprünglichen Ausnahme.
- **TempFS schützt den Host-CWD vor Nebenwirkungen:** Das Target läuft in einem eigenen Prozess mit temporärem Arbeitsverzeichnis. Der Elternprozess muss seinen Arbeitsordner nicht wechseln.
- **Substanzielle Regressionstests:** Es gibt reale Subprozess- und Offline-Szenarien sowie Tests für verzögert auftretende Multiprocessing-Fehler. Die Offline-Tests prüfen auch ihren eigenen Schutzmechanismus.
- **Ehrliche Abgrenzung geplanter Virtualisierung:** Docker- und VM-Entwürfe liegen außerhalb der öffentlichen API und sind ausdrücklich als nicht implementiert dokumentiert.

### 5.2 Reproduzierte Korrektheitsprobleme

| Priorität | Befund und Fundstelle | Auswirkung | Empfehlung |
| --- | --- | --- | --- |
| P0 | `EBT._calculate_diffs()` prüft Rückgaben nur bei `post.returns is not None` | `WorldState(returns=None)` akzeptiert auch `42` | Eigenen Sentinel für „nicht angegeben“ verwenden |
| P0 | `EBT.run()` setzt `_traces` und `_outcome` nicht zurück; Schritt-IDs bleiben identisch | Ein früherer Erfolg kann einen späteren Fehler desselben Objekts über die ODER-Logik verdecken | Pro Lauf frischen Zustand und unabhängige Traces erzeugen oder Wiederverwendung ausdrücklich ablehnen |
| P1 | `pre=[]` und `post=[]` erzeugen keine Vergleichsspuren; `all([])` wird wahr | Grün ohne Target-Ausführung beziehungsweise ohne Ergebnisprüfung | Leere Listen ablehnen oder explizit als ungeprüft ausweisen |
| P1 | `MyPy._guard_process_success()` lehnt nur Exitcode 2 mit stderr ab | Ein abgebrochener Prozess mit Returncode `-9` und leerer Ausgabe wird als leere Diagnoseliste behandelt | Bekannte Erfolg-/Diagnosecodes erlauben, alle übrigen als Werkzeugfehler melden |
| P1 | `AstLinter._has_native_config()` wertet bereits die Existenz einer beliebigen `pyproject.toml` als native Konfiguration | Standardausschlüsse entfallen auch ohne Linter-Konfiguration; beim CST-Backend bleibt das Ausschlussset leer | Backend-Konfiguration gezielt prüfen und Schutz-Ausschlüsse separat behandeln |
| P2 | `PytestReporter._format_trace_details()` nutzt Wahrheitswerte der Rückgaben | Bei erwarteten `0`, `False`, `[]` oder `""` fehlen die entscheidenden Rückgabedetails im Fehlerbericht | Angegebene Werte statt Truthiness prüfen |
| P2 | `EBT._collect_topology()` erfasst ausschließlich Dateien | Fehlende leere Verzeichnisse bleiben unbemerkt | Verzeichnissemantik ausdrücklich definieren und gegebenenfalls mitvergleichen |

P0 bezeichnet hier Fehler im zentralen Vertrauensversprechen des Testwerkzeugs, keine Aussage über eine ausnutzbare Sicherheitslücke.

Der Wiederholungsfehler ist besonders schwerwiegend: Nach zwei Läufen wuchs auch die Trace-Liste des bereits zurückgegebenen ersten `RunTrace` mit. Die Ergebnisse sind damit keine stabilen historischen Momentaufnahmen.

### 5.3 Reproduktionsbeispiele

Mit `PYTHONPATH=src .venv/bin/python` lassen sich die wichtigsten Befunde ohne Arena oder Netzverbindung zeigen:

```python
from cubie import EBT, WorldState

# Erwartetes None wird nicht geprüft.
assert EBT(
    target=lambda: 42,
    post=WorldState(returns=None), reporter=None,
).run().evaluation is True

# Kein Eingang, keine Ausführung, dennoch Erfolg.
assert EBT(
    target=lambda: 42, pre=[],
    post=WorldState(returns=99), reporter=None,
).run().evaluation is True

# Zweiter Lauf liefert 2 statt 1 und bleibt trotzdem erfolgreich.
values = iter([1, 2])
test = EBT(
    target=lambda: next(values),
    post=WorldState(returns=1), reporter=None,
)
assert test.run().evaluation is True
assert test.run().evaluation is True
```

Dass `reporter=None` keinen Assertion-Fehler auslöst, ist vorgesehen. Problematisch sind hier die falschen positiven `evaluation`-Werte, die auch der Standardreporter als Erfolg behandelt.

### 5.4 API und Modellierung

`WorldState` ist klein, aber durch zahlreiche `Any`-Felder schwach spezifiziert. `arena` bezeichnet je nach Kontext eine ausführbare Arena oder einen Vergleichspfad. `fs` kann mehrere Darstellungen annehmen und wird bei der Normalisierung im übergebenen Objekt verändert. Das erleichtert Kurzformen, erschwert aber Validierung, Wiederverwendung und Fehlermeldungen.

Weitere relevante Grenzen:

- `args=[1, 2]` bedeutet zwei Positionsargumente; eine Liste als einzelnes Argument muss als `args=([1, 2],)` verpackt werden. Das benötigt klare Beispiele.
- Die Zusammenführung von Dateiquellen nach Basename kann gleichnamige Quellen überschreiben. Kollisionen sollten nicht stillschweigend verschwinden.
- Erwartete Exceptions besitzen kein eigenes Feld. Target-Ausnahmen propagieren; ein negativer Vertrag ist kein Ersatz für eine präzise Ausnahmeerwartung.
- Listen und Tupel gelten beim rekursiven Vergleich als austauschbar; Regex-Prüfungen verwenden `match()` auf `str(actual)`. Das sind legitime Entscheidungen, sofern sie als Vertragssemantik dokumentiert sind.
- Der eingefrorene `EBTContext` enthält weiterhin veränderliche Listen, Sets und Objekte. Er ist keine tiefe Zustandsisolation.

## 6. Arenen, Sicherheit und Reproduzierbarkeit

### 6.1 Sicherheitsgrenzen

Die README benennt korrekt, dass TempFS und PyVenv keine OS-Sicherheitsgrenze bieten. Andere Formulierungen im Code, etwa „sandbox at the OS level“ in `_activate_arena_env()`, widersprechen dem: `PATH` und `VIRTUAL_ENV` verändern die Umgebung, entziehen aber keine Zugriffsrechte.

Beide Arenen starten Prozesse mit den Rechten des aufrufenden Benutzers. Targets können grundsätzlich absolute Hostpfade, geerbte Umgebungsvariablen und verfügbare Netzwerkzugänge nutzen. Die FS-Hydrierung begrenzt Zielpfade nicht auf das temporäre Verzeichnis; absolute Pfade und `..` sind nicht ausgeschlossen. Das ist eine zusätzliche Konfigurationsgefahr, auch bei versehentlichen Fehlangaben.

Pickle und Cloudpickle deserialisieren ausführbare Objektbeschreibungen im Host. Deshalb ist die Rückübertragung aus einer nicht vertrauenswürdigen Ausführung selbst Teil des Sicherheitsproblems. MessagePack reduziert diesen konkreten Deserialisierungsangriff, schützt aber weder das Host-Dateisystem noch vor gefälschten Ergebnissen eines bösartigen Targets.

Die Import-„Dekontamination“ erzeugt Scheinmodule über `PhantomFinder`. Das kann bestimmte Importabhängigkeiten überbrücken, ist aber keine Isolation und kann Fehler verschlucken oder Testbedingungen verändern. Bei `CloudpickleCodec` ist `_apply_dependency_isolation()` ausdrücklich ein leerer Platzhalter. Der Parameter `isolation=1` suggeriert deshalb mehr implementiertes Verhalten, als vorhanden ist.

### 6.2 Betrieb und Ressourcen

Die Arena-Subprozesse haben keine konfigurierbare Ausführungsfrist. Ein hängendes Target kann den Testlauf unbegrenzt blockieren. PyVenv puffert außerdem stdout und stderr vollständig. Für zuverlässige CI-Nutzung fehlen Grenzen für Laufzeit und Ausgabe sowie kontrolliertes Beenden von Prozessbäumen.

PyVenv kopiert eine vorhandene virtuelle Umgebung und kann bei fehlenden Codec-Abhängigkeiten die Basisumgebung durch `uv pip install` verändern. Das verursacht versteckte Schreiboperationen, mögliche Netzabhängigkeit und bei paralleler Nutzung Konkurrenz auf einer gemeinsamen Basis. Die neuen Anforderungsprüfungen reduzieren unnötige Installationen und sind positiv zu bewerten; reproduzierbares Provisionieren ersetzen sie nicht.

Das mitgelieferte Basisverzeichnis enthält eine konkrete Python-3.13-Umgebung, aber Git führt dort kein `bin/python`. Ein transportabler Standardpfad lässt sich daraus für einen frischen Checkout nicht ableiten. Die Windows-Auflösung ist ebenfalls uneinheitlich: `_environment_python()` sucht `python.exe`, `_get_python_exe()` dagegen `python` im Scripts-Verzeichnis. Plattformunterstützung benötigt echte Installationstests.

### 6.3 Multiprocessing

Die austauschbaren Backends und Tests für spät auftretende Iteratorfehler sind sinnvoll. Allerdings richtet sich die Workerzahl nach allen gemeldeten CPUs, statt nach Aufgabenzahl oder Benutzerlimit. Zusammen mit pytest-xdist und Arena-Unterprozessen droht eine erhebliche Überbelegung.

Der automatische Backend-Fallback fängt Ausführungsfehler allgemein ab und kann die gesamte Aufgabenmenge erneut ausführen. Dadurch können fachliche Target-Fehler wie Backend-Probleme wirken; bereits ausgeführte Seiteneffekte können wiederholt werden. Die Wiederholungssemantik sollte explizit sein und Infrastrukturfehler von Target-Ausnahmen unterscheiden. Für reine Funktionen ist das weniger kritisch als für Datei-, Netzwerk- oder Datenbankoperationen.

## 7. Tests, Dokumentation und Auslieferung

### 7.1 Qualität der Nachweise

Die Testsuite ist deutlich umfangreicher als ein reiner Demonstrator: Die Sammlung ergab **432 Tests**. Positiv sind insbesondere `tests/test_offline_core.py`, gezielte TempFS-Isolationstests und die Prüfung verzögerter Multiprocessing-Ergebnisse.

**Ausgeführte Prüfung:** `.venv/bin/python -m pytest -q --tb=short` lieferte innerhalb der eingeschränkten Sandbox zunächst **411 bestanden, 10 fehlgeschlagen, 11 übersprungen**, bei 6 Warnungen und 159,35 Sekunden Laufzeit. Acht Fehlschläge betrafen `uv pip install/uninstall` in Arena-Mutationstests; zwei betrafen einen durch Berechtigungen blockierten Multiprocessing-Manager. Die gezielte Wiederholung der zehn fehlgeschlagenen Tests außerhalb der Sandbox mit `.venv/bin/python -m pytest --lf -q --tb=short` ergab **10 bestanden** in 3,10 Sekunden (zusätzlich 1 deselected). Damit bestanden über beide Läufe alle 421 ausgeführten Tests; 11 blieben übersprungen. Es wurde kein weiterer vollständiger Lauf ohne Sandbox durchgeführt.

Die anfänglichen zehn Fehlschläge werden deshalb **nicht als bestätigte Implementierungsfehler gewertet**. Die in Abschnitt 5.2 dokumentierten Fehler stammen aus zusätzlichen gezielten Stichproben und bestehen unabhängig davon. Gerade diese Kombination – grüne vorhandene Tests und falsche Erfolge in einfachen Gegenproben – zeigt die Lücken der bisherigen Absicherung. Ausführungsprotokolle dieser Untersuchung liegen lokal unter `/tmp/cubie-gutachten-pytest.log` und `/tmp/cubie-gutachten-recheck.log`; diese temporären Dateien sind kein dauerhafter Projektbestandteil.

Die Aussagekraft ist dennoch begrenzt:

- Viele Tests prüfen EBT mit EBT. Das ist für Integration legitim, kann aber gemeinsame Bewertungsfehler verdecken. Der Prüfkern benötigt unabhängige Assertions und bewusst fehlerhafte Implementierungen als Gegenproben.
- `tests/tests_arena/test_security_arena_codec.py` verschluckt alle normalen Ausnahmen. Ein nicht ausführbarer Aufbau kann beim erwarteten „nicht kompromittiert“-Ergebnis bereits zum Bestehen führen. Die erfolgreiche Target-Ausführung muss vor der Sicherheitsbewertung nachgewiesen werden.
- Tests erwarten lokale Umgebungen wie `tests/.arenas/cowsay_env` und `tests/.arenas/empty_venv`. Deren Bereitstellung ist nicht durchgängig als reproduzierbarer Fixture-Lebenszyklus gekapselt.
- `tests/tests_multiprocessors/mp_hypothesis.py` entspricht nicht dem Standard-Dateimuster von pytest und wird beim normalen Lauf nicht gesammelt. Die vorhandene generative Testidee wirkt deshalb nicht automatisch als Regressionstor.
- `tests/conftest.py` verändert global den Arbeitsordner und erweitert `sys.path`. Das erleichtert lokale Ausführung, weist aber keine korrekte Installation des Pakets nach.

### 7.2 Einstieg und öffentliche API

Der README-Quickstart ist in der gezeigten Form nicht funktionsfähig: `WorldState` ist nicht importiert, und der EBT-Konstruktion fehlt `.run()`. Nach Ergänzung des Imports würde dieser Test nur ein Objekt anlegen und ohne Ausführung grün bleiben. Das ist bei einem Testframework ein besonders unglücklicher Einstiegsfehler.

Auch das RBT-Beispiel verwendet `qb.RBT`, obwohl `cubie.__init__` die Klasse nicht exportiert. Der vorhandene Zugriff lautet `from cubie.rbt import RBT`. Ausführbare Dokumentationsbeispiele sollten Teil der Tests sein.

Die Dokumentation ist engagiert und erklärt viele innere Strukturen. Sie verwendet jedoch viel mathematische und bildhafte Sprache, bevor der Anwender Installation, einfache Verträge, typische Fehler und Garantien klar erfährt. Eine kürzere Anleitung mit lauffähigen Fällen und einer einzigen verbindlichen Semantiktabelle wäre hilfreicher. Historische oder geplante Aussagen sollten durchgängig als solche markiert werden.

### 7.3 Repository und Paketierung

`git ls-files .venv` ergab **889 versionierte Dateien**; das lokale Verzeichnis umfasst ungefähr 129 MiB. Zusätzlich liegen 48 versionierte Dateien unter `src/cubie/arenas/arena_envs`. Diese Zahlen beschreiben den vorgefundenen Stand, keine Größe einer gebauten Distribution.

Versionierte Entwicklungsumgebungen bringen maschinen- und interpreterabhängige Artefakte, fremde Metadaten und unnötiges Änderungsrauschen mit. Eine Root-`.gitignore` fehlt. Umgebungsvorlagen sollten über deklarative Anforderungen reproduziert werden, nicht über eingecheckte installierte Pakete.

Die `pyproject.toml` führt pytest, mehrere Analysewerkzeuge und Prozess-/Serialisierungsbibliotheken als Pflichtabhängigkeiten. Harte Versionsbindungen bei zahlreichen Werkzeugen vergrößern das Konfliktpotenzial in konsumierenden Projekten. Sinnvoll wären ein kleiner Kern und optionale Extras für Linter und Entwicklungswerkzeuge. Python ≥3.13 kann eine bewusste Entscheidung sein, begrenzt aber den Einsatz in älteren Projekten.

Eine explizite `[build-system]`-Sektion fehlt. Das beweist für sich genommen keinen Buildfehler, lässt den vorgesehenen Build-Vertrag aber unnötig offen. Eine saubere Wheel-Erzeugung und Installation in einer leeren Umgebung sollten als Releaseprüfung festgelegt werden.

Im untersuchten Repository fehlen eine eigene Projektlizenz und eine versionierte CI-Konfiguration. Lizenzen mitgelieferter Fremdpakete ersetzen keine Lizenz für Cubie. Vor breiter externer Nutzung sollten Nutzungsbedingungen, automatisierte Prüfungen und eine kleine unterstützte Plattformmatrix geklärt sein.

## 8. Priorisierte Weiterentwicklung

### Priorität 1: Der Prüfkern muss verlässlich entscheiden

1. Sentinel für nicht spezifizierte Rückgaben einführen; `None` als echten erwarteten Wert unterstützen.
2. Jeden Lauf mit frischem Zustand ausführen und unveränderliche historische Ergebnisse sicherstellen.
3. Leere und ungültige Zustandslisten sowie FS-Namenskollisionen ausdrücklich behandeln.
4. Werkzeugabbrüche von leeren Diagnoselisten unterscheiden; falsche Rückgaben vollständig berichten.
5. Unabhängige Regressionstests für diese Fälle schreiben. Gezielt fehlerhafte Targets müssen zuverlässig scheitern.

### Priorität 2: Einen frischen Checkout zuverlässig ausführbar machen

1. Entwicklungsumgebungen aus der Versionsverwaltung entfernen und eine Root-`.gitignore` pflegen.
2. Arena-Basen in Fixtures oder einem dokumentierten Provisionierungsschritt erzeugen; Laufzeit und Installation trennen.
3. README-Beispiele reparieren und automatisiert ausführen.
4. Wheel in einer leeren Umgebung testen; eine CI mit klarer Python-/OS-Matrix einrichten.
5. Eigene Lizenz, Build-Konfiguration und Abhängigkeitsstrategie vervollständigen.

### Priorität 3: Betriebsverhalten und Vertrag schärfen

1. Timeouts, begrenzte Ausgabe und Prozessbaum-Abbruch ergänzen.
2. Workerzahl konfigurierbar machen und an die Aufgabenzahl anpassen.
3. Backend-Fallback auf geeignete Infrastrukturfehler begrenzen und Wiederholungen dokumentieren.
4. Pfadgrenzen für Hydrierung prüfen; vertrauenswürdige und nicht vertrauenswürdige Nutzung deutlich abgrenzen.
5. Rückgaben, Ausnahmeerwartungen, FS-Topologie und persistente Berichte eindeutig modellieren.

### Priorität 4: Den Nutzen nachweisen

Vor weiteren Arena-Typen oder einer umfassenden Agentenplattform sollten zwei bis drei reale Datei- und Akzeptanzworkflows umgesetzt werden. Jeweils dieselben Anforderungen einmal mit gewöhnlichem pytest und einmal mit Cubie prüfen. Vergleichskriterien: Einrichtungsaufwand, Lesbarkeit, Fehlersuche, Laufzeit und Wartung nach einer Anforderungsänderung. Erst daraus lässt sich belastbar entscheiden, wo Cubie eine eigene Abstraktion rechtfertigt.

## 9. Abschließende Bewertung

| Dimension | Urteil |
| --- | --- |
| Problemrelevanz | Hoch: nachvollziehbare Verträge und reproduzierbare Prüfungen sind praktisch wichtig |
| Konzeptionelle Eigenständigkeit | Eher in der Kombination und Bedienung als in einem neuen Prüfverfahren |
| Nachgewiesener praktischer Mehrwert | Plausibel für Datei-Workflows, bislang nicht quantitativ belegt |
| Architektur | Gut erweiterbar, stellenweise unnötig dynamisch und zustandsreich |
| Korrektheit des Prüfkerns | Wegen reproduzierter falscher Erfolge derzeit unzureichend abgesichert |
| Sicherheitsisolation | Keine OS-Sicherheitsgrenze vorhanden |
| Auslieferungs- und Betriebsreife | Experimentell; erheblicher Bedarf bei sauberer Installation, CI und Ressourcensteuerung |

Cubie verdient eine fokussierte Weiterentwicklung. Voraussetzung ist eine nüchterne Produktdefinition: ein hilfreiches Testwerkzeug mit klaren, begrenzten Garantien. Entscheidend für seinen Erfolg werden verlässliche negative Testergebnisse, ein reibungsloser Einstieg und nachgewiesene Vorteile in konkreten Arbeitsabläufen sein.

---

---

<center>

![Error while trying to load the image](./docs/.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./docs/GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./docs/GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./docs/GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./docs/GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
