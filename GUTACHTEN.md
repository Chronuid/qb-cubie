# Kritisches Gutachten zu qb-cubie

**Stand:** 11. November 2026  
**Untersuchter Commit:** `5e50d22f80db90c4e8ae6e3aeedab6acdb981230`  
**Projektversion:** `0.0.3`  
**Lokale Prüfumgebung:** Linux, Python 3.13.12

Dieses Dokument ersetzt das bisherige Gutachten. Es beschreibt den untersuchten Stand und unterscheidet reproduzierte Implementierungsfehler, dokumentierte Einschränkungen und gutachterliche Einschätzungen. Die Untersuchung hat keine Implementierungsfehler behoben.

## 1. Gesamturteil

qb-cubie hat einen sinnvollen Kern für deklarative Akzeptanztests, besonders bei Datei-Workflows. Sein praktischer Vorteil gegenüber gewöhnlichen pytest-Tests ist bislang nicht belastbar belegt. Technisch ist das Projekt substanziell umgesetzt, enthält aber weiterhin Fehler, die Testbedingungen verändern oder Fehlschläge verbergen können.

**Urteil: Für ausgewählte interne Anwendungen mit vertrauenswürdigem Code pilotierbar. Vor einer breiten Verwendung als Qualitätsschranke sind Korrekturen erforderlich.**

Der größte nächste Entwicklungsgewinn liegt in einem verlässlicheren und leichter verständlichen Prüfkern sowie nachgewiesenem Nutzen für konkrete Datei-Workflows. Eine weitere Verbreiterung des Funktionsumfangs hat geringere Priorität.

## 2. Auftrag, Methode und Aussagegrenzen

Untersucht wurden Projektbeschreibung, Vertragssemantik, EBT/RBT, Reporter, Arenen, Serialisierung, Multiprocessing, Linter, Paketierung, CI-Konfiguration, Anwendungstests und ausgewählte Benchmarkbelege. Zusätzlich wurden die vollständige Repository-Testsuite und unabhängige Gegenproben ausgeführt.

Die vollständige Testsuite wurde mit `.venv/bin/python -m pytest -q` gestartet:

```text
2569 passed, 18 skipped, 6 warnings in 550.50s (0:09:10)
```

Die sechs Warnungen betrafen fünfmal die Verwendung von TempFS mit einer Arena-Konfiguration und einmal die experimentelle Wiederherstellung einer Instanz im MSGspecCodec. Die zusätzlich beschriebenen Fehler wurden durch separate Gegenproben reproduziert; sie werden durch das erfolgreiche Ergebnis der bestehenden Suite nicht entkräftet.

Der Git-Arbeitsstand war vor und nach der Untersuchung sauber. Erst die anschließende Persistierung dieses Gutachtens verändert `GUTACHTEN.md`. Es wurden keine Produktivdateien oder Tests korrigiert und keine Änderungen gestagt oder committet.

Die Untersuchung ist keine vollständige Sicherheitsprüfung, Marktstudie oder plattformübergreifende Releaseabnahme. Die konfigurierte CI-Matrix wurde im Code untersucht; daraus wird kein Nachweis erfolgreicher externer CI-Läufe abgeleitet. Die gebaute Distribution wurde in dieser Untersuchung nicht erneut vollständig abgenommen. Aussagen zum praktischen Nutzen sind gutachterliche Einschätzungen, soweit keine Messbelege ausdrücklich genannt werden.

## 3. Idee und konzeptionelle Tragfähigkeit

### 3.1 Das tragfähige Zentrum

Die Grundidee ist brauchbar: Eingaben, erwartete Rückgaben und Dateisystemergebnisse werden als gemeinsamer Vertrag beschrieben. Dadurch lassen sich wiederkehrende Testabläufe vereinheitlichen.

Ein Exportprogramm kann durch Eingabedateien, eine erwartete Rückgabe und einen vollständigen Ausgabeverzeichnisbaum beschrieben werden. Cubie übernimmt Einrichtung, Ausführung, Vergleich und Diagnose. Gerade bei vielen ähnlichen Exporten oder Generatoren kann diese gemeinsame Sprache helfen.

Der wesentliche Mehrwert liegt in wiederverwendbaren Konventionen und standardisierten Vergleichen. Für einfache Berechnungen ist der Nutzen deutlich geringer:

```python
assert calculate_tax(100, 19) == 119
```

ist leichter zu erfassen als der entsprechende EBT-Vertrag. pytest stellt bereits [Parametrisierung](https://docs.pytest.org/en/stable/how-to/parametrize.html) und [temporäre Verzeichnisse](https://docs.pytest.org/en/stable/how-to/tmp_path.html) bereit. Cubie muss seinen zusätzlichen Lern- und Integrationsaufwand durch bessere wiederkehrende Abläufe rechtfertigen.

### 3.2 Aussagegrenzen

Die aktuelle [Qualitätsdokumentation](docs/GUIDE_Quality-Assurance.md) grenzt die Aussagekraft angemessen ein: Erfolgreiche Beispiele liefern beobachtete Konformität. Sie beweisen weder allgemeine Korrektheit noch vollständige Abdeckung.

Hoare-Logik und Suchraumvorstellungen bleiben Analogien. Cubie implementiert keine formale Verifikation, Programmsynthese oder vollständige Exploration zulässiger Eingaben. Ein Rückgabeprädikat erzeugt keine zusätzlichen Testeingaben. Eine positive Reviewerentscheidung wird durch ihre boolesche Darstellung nicht zu einem Beweis.

### 3.3 Gemeinsame Zielmengen

Ein konzeptioneller Schwachpunkt bleibt die gemeinsame Zielmenge mehrerer Eingänge. Eingänge `1, 2` und erlaubte Rückgaben `2, 4` bedeuten keine Zuordnung `1 → 2, 2 → 4`. Auch vertauschte Ergebnisse können bestehen. Für korrelierte Fälle sind getrennte Verträge erforderlich.

Das ist dokumentiertes und implementierungskonformes Verhalten, entspricht aber häufig nicht der Erwartung eines Testautors. Eine ausdrückliche API für zusammengehörige Ein-/Ausgabefälle wäre deshalb wertvoller als eine weitere Verbreiterung der Mustersprache. Die verbindliche Bedeutung beschreibt die [Semantikreferenz](docs/GUIDE_Contract-Semantics.md).

## 4. Praktischer Nutzen und seine Grenzen

| Einsatzfall | Gutachterliche Einschätzung |
| --- | --- |
| CSV-Exporte, Dokumentkonverter, Generatoren | Stärkster erkennbarer Nutzen |
| Wiederkehrende strukturierte Rückgabeprüfungen | Nützlich bei gemeinsamer Teamkonvention |
| Einfache reine Funktionen | Häufig geringer Zusatznutzen |
| Prüfung unterschiedlicher Python-Abhängigkeiten | Brauchbarer Ansatz mit relevanten Einschränkungen |
| Manuelle Abnahmen | Einfacher gemeinsamer Ablauf, begrenzte Nachweisführung |
| Bewertung von KI-generiertem Code | Als Bestandteil einer unabhängigen Prüfkette denkbar |
| Ausführung nicht vertrauenswürdigen Codes | Durch die Core-Arenen nicht abgesichert |

Die [Anwendungstests](tests/tests_user_workflows/test_order_export.py) sind positiv hervorzuheben. Sie demonstrieren Fehler wie falsche Inhalte, fehlende Dateien, zusätzliche Dateien und falsche Rückgaben. Teilweise wird dieselbe Anwendung zusätzlich direkt mit gewöhnlichen Assertions geprüft. Das verringert die Gefahr, dass Cubie lediglich seine eigene Auswertungslogik bestätigt.

Diese Fälle belegen funktionale Brauchbarkeit. Sie messen keine eingesparte Entwicklungszeit, bessere Verständlichkeit oder geringeren Wartungsaufwand. Auch die Bezeichnung als Nutzerexperiment ersetzt keine Untersuchung unabhängiger Anwender in fremden Projekten.

### 4.1 Stand der Agentenexperimente

Die Agentenexperimente liefern bislang keinen belastbaren Nutzenbeleg. Laut aktuellem [Studienbericht](experiments/testguided-study/PAPER.md) wurden sieben Piloten mit jeweils sechs Versuchen durchgeführt, durchgehend auf denselben drei Aufgaben mit Seed 42. Die Agentendesigns änderten sich zwischen den Piloten.

Im jüngsten dort dokumentierten Pilot lösten beide Bedingungen keine der drei Aufgaben. Kein Versuch führte einen EBT-Vertrag aus. Daraus folgt:

- Ein allgemeiner Vorteil von Cubie ist nicht nachgewiesen.
- Eine generelle Wirkungslosigkeit ist ebenfalls nicht nachgewiesen.
- Die Ergebnisse betreffen vor allem das Gesamtsystem aus Modell, Anleitung und Agentensteuerung.
- Wiederholte Läufe auf denselben Aufgaben ersetzen keine unabhängigen Aufgaben.
- Ohne tatsächliche EBT-Nutzung lässt sich die Wirkung ausgeführter EBT-Verträge kaum beurteilen.

Die Studie benennt diese Grenzen selbst deutlich. Die investierte Messinfrastruktur sollte nicht mit empirisch bestätigtem Produktnutzen verwechselt werden. Die archivierten Agentenläufe wurden für dieses Gutachten nicht erneut ausgeführt; bewertet wurden ausgewählte vorhandene Berichte und Belege.

## 5. Technische Stärken

Die Umsetzung geht erheblich über einen Prototyp mit einigen Beispielen hinaus.

- **Klare Erweiterungspunkte:** Arenen, Reviewer, Reporter, Codecs und Multiprocessing-Backends besitzen definierte Schnittstellen.
- **Strukturierte Ergebnisse:** `EvaluationTrace` und `RunTrace` erfassen Erwartungen, Beobachtungen, Abweichungen und Laufzeiten.
- **Breite Vergleichsmöglichkeiten:** Werte, Typen, Unions, reguläre Ausdrücke, Prädikate und verschachtelte Strukturen sind vorhanden.
- **Bewusste Fehlerbehandlung:** Target-Ausnahmen, Infrastrukturfehler und Aufräumfehler werden an vielen Stellen unterschieden.
- **Aktuelle Dateivergleiche:** Inhalte werden erneut blockweise gelesen; ein persistenter Vergleichscache kann keine veraltete Gleichheit vortäuschen.
- **Ernsthafte Regressionstests:** Die Suite umfasst echte Kindprozesse, negative Gegenproben und Installationsprüfungen.
- **Durchdachte Paketprüfung:** Die CI-Konfiguration prüft gebaute Wheels außerhalb des Checkouts und mit unterschiedlichen optionalen Abhängigkeiten.

Wesentliche Quellen sind der [EBT-Kern](src/qb_cubie/ebt.py), die [Protokolle](src/qb_cubie/protocols.py), der [Dateivergleich](src/qb_cubie/_files.py), die [CI-Konfiguration](.github/workflows/ci.yml) und die [Wheel-Prüfung](scripts/check_wheel.py).

## 6. Bestätigte technische Befunde

P1 bezeichnet einen wesentlichen Fehler, der vor einer breiten Verwendung als Qualitätsschranke behoben werden sollte. P2 bezeichnet einen begrenzteren Fehler mit praktischer Relevanz. Die Einstufung berücksichtigt Auswirkung und Auslösebedingungen.

| Kennung | Priorität | Befund | Auswirkung |
| --- | --- | --- | --- |
| B1 | P1 | PyVenv kollidiert mit bereitgestellten Dateinamen | Testeingaben werden überschrieben oder gelöscht |
| B2 | P1 | Reporter verliert Assertions unter `python -O` | Fehlerhafte Tests können erfolgreich enden |
| B3 | P2 | CstLinter akzeptiert nicht existierende Pfade stumm | Keine Analyse erscheint als leere Diagnoseliste |

### 6.1 B1: PyVenv verändert Testdaten durch eigene IPC-Dateien

[PyVenv](src/qb_cubie/arenas/pyvenv.py) legt seine Austauschdateien mit festen Namen direkt im geprüften Workspace ab:

```text
ipc_in.pkl
ipc_out.pkl
_cubie_phantom.py
```

Die Dateiendungen der Austauschdateien hängen vom Codec ab. Das grundlegende Problem besteht unabhängig davon: Infrastruktur und Testdaten teilen denselben Namensraum.

Zwei Gegenproben mit `PickleCodec` ergaben:

1. Eine über `pre.fs` bereitgestellte `ipc_in.pkl` mit drei Bytes war beim Target-Aufruf bereits durch die IPC-Nutzlast ersetzt. Das Target `os.path.getsize` beobachtete in dieser Probe 64 Bytes. Diese konkrete Größe hängt von der serialisierten Nutzlast ab.
2. Eine bereitgestellte `ipc_out.pkl` fehlte nach der Ausführung des Targets `int`, weil die IPC-Bereinigung sie entfernte. Der Dateivergleich meldete `Path not found. Arena: False, Host: True`.

Damit prüft Cubie unter diesen Bedingungen eine andere Ausgangslage als deklariert. Dies ist kein bloßes Darstellungsproblem des Reports und erfordert keinen bösartigen Target-Code.

Zusätzlich erzeugen `.venv` und Hilfsdateien unerwartete Einträge beim vollständigen Workspacevergleich. Ein Vergleich eines nach fachlicher Operation leeren Arbeitsbereichs gegen ein leeres Referenzverzeichnis scheitert in PyVenv an Infrastrukturartefakten. Das ist eine zusätzliche Integrationsschwäche derselben fehlenden Trennung.

**Empfohlene Korrektur:** IPC-Dateien und Hilfsmodule außerhalb des fachlichen Workspace halten, wie TempFS dies für seine IPC-Dateien bereits tut. Laufzeitumgebung und geprüfte Dateiausgabe sollten getrennte Verzeichnisse erhalten. Regressionstests müssen Namenskollisionen sowie vollständige Verzeichnisvergleiche ausdrücklich abdecken. Falls Namen reserviert werden, müssen Konflikte vor Änderungen an den Testdaten ausdrücklich abgelehnt werden; stilles Überschreiben ist unzulässig.

### 6.2 B2: Fehlerweitergabe verschwindet unter optimiertem Python

Der [PytestReporter](src/qb_cubie/reporter.py) verwendet normale `assert`-Anweisungen zur Durchsetzung negativer Ergebnisse. Unter `python -O` entfallen diese.

Diese Gegenprobe verwendet den Standardreporter:

```python
from qb_cubie import EBT, WorldState

result = EBT(
    target=lambda: 1,
    post=WorldState(returns=2),
).run()
```

Unter optimiertem Python war `result.evaluation` zwar `False`, der Aufruf warf aber keine Ausnahme. Auch ein RBT mit `HeadlessReviewer(answer=False)` lief ohne Fehler durch.

In einem separaten pytest-Prozess unter `python -O -m pytest` wurde ein Test mit dem falschen EBT-Vertrag tatsächlich als Erfolg gemeldet:

```text
1 passed, 1 warning
Exitcode: 0
```

pytest warnte, dass Assertions außerhalb umgeschriebener Testmodule beziehungsweise Plugins ignoriert werden. Der Qualitätsentscheid blieb trotzdem erfolgreich.

Der Auslöser ist eine besondere Betriebsart, der Fehlermodus aber wesentlich: Eine Qualitätsschranke verliert ihre Durchsetzung. Die erfolgreiche reguläre Suite prüft diesen Betriebsmodus nicht durch die hier ausgeführte Gegenprobe ab.

**Empfohlene Korrektur:** Explizit `raise AssertionError(...)` verwenden. Die Fehlerweitergabe einer Bibliothek sollte nicht vom Optimierungsmodus abhängen. Ein Regressionstest muss EBT und abgelehntes RBT in einem optimierten Kindprozess prüfen; zusätzlich sollte ein echter pytest-Aufruf einen von null verschiedenen Exitcode liefern.

### 6.3 B3: Fehlende Linterziele werden als leeres Ergebnis zurückgegeben

[CstLinter.check()](src/qb_cubie/linter.py) verarbeitet Dateien und Verzeichnisse. Existiert ein übergebener `Path` nicht, greift keiner der Zweige; zurückgegeben wird `[]`.

Reproduziert wurde dies mit einem garantiert fehlenden Pfad in einem temporären Verzeichnis. Die folgende Schreibweise illustriert denselben Fall:

```python
from pathlib import Path
from qb_cubie import CstLinter

CstLinter([]).check(Path('/nicht/vorhanden.py'))
# []
```

Die leere Regelliste hält die Probe minimal. Der fehlende Pfad erreicht unabhängig von den registrierten Regeln keine Analyse.

Ein falscher Pfad kann damit dieselbe Ergebnisform erzeugen wie eine erfolgreiche Analyse ohne Befunde. Wenn ein Verbraucher eine leere Diagnoseliste als positives Gate wertet, bleibt eine Fehlkonfiguration unbemerkt.

**Empfohlene Korrektur:** Nicht existierende oder ungeeignete Pfade ausdrücklich ablehnen. Für Verzeichnisprüfungen wäre außerdem eine erkennbare Unterscheidung zwischen „keine Dateien untersucht“ und „Dateien ohne Befund untersucht“ hilfreich.

## 7. Architektur und Wartbarkeit

### 7.1 Mehrere Rollen in einem Datensatz

Die größte technische Herausforderung ist die wachsende Zahl miteinander wechselwirkender Regeln.

`WorldState` beschreibt Eingaben, Erwartungen und beobachtete Ergebnisse. Dadurch tragen dieselben Felder je nach Position unterschiedliche Bedeutungen. `arena` kann Ausführungsobjekt, Basisumgebung oder Vergleichsvorlage sein. Auch `expect` wirkt auf Vertrags- und Zustandsebene unterschiedlich.

Diese Wiederverwendung spart zunächst Typen, verlagert Komplexität aber in Interpretation, Validierung und Dokumentation. Für den langfristigen Ausbau wären getrennte Rollen für Eingaben, Erwartungen und Beobachtungen leichter zu prüfen.

### 7.2 Dokumentierte Bedienungsrisiken

Weitere Stolperstellen sind dokumentiert:

- Ein leeres `fs` prüft keinen leeren Workspace.
- Einzelne Dateimappings prüfen keine zusätzlichen Dateien außerhalb ihres Bereichs.
- `JsonReporter` persistiert negative Ergebnisse, erhebt aber keine Assertion.
- Historische Traces archivieren keine Dateiinhalte.
- Tiefenkopien frieren Closures und externe Ressourcen nicht ein.
- Eine RBT-Zielbezeichnung bewirkt keine automatische Quellenbeschaffung.

Dokumentation macht diese Regeln nachvollziehbar. Sie beseitigt deren Bedienungsrisiko nicht.

Bewertung und verbindlicher Testentscheid sollten deutlicher getrennte, ausdrücklich benannte Operationen sein. Der Wechsel des Reporters verändert derzeit auch, ob ein fachlicher Fehler als Testfehler wirksam wird. Für eine Testbibliothek ist das ein überraschender Zusammenhang.

### 7.3 Kopierte Python-Umgebungen

PyVenv besitzt strukturelle Kosten: Für jeden Eingang wird die Basisumgebung kopiert. Relocation-Code muss anschließend unterstützte Einstiegsskripte anpassen. Die Untersuchung hat keine systematische Laufzeitmessung dieser Kosten vorgenommen.

Python behandelt virtuelle Umgebungen grundsätzlich als neu zu erstellende, nicht allgemein verschiebbare oder kopierbare Artefakte. Die dokumentierten Grenzen von Cubie sind daher wesentlich. Siehe die [Python-Dokumentation zu venv](https://docs.python.org/3.13/library/venv.html).

Die vorhandene Anpassung unterstützter Launcher ist sinnvoll, schafft aber keine allgemeine Portabilität beliebiger installierter Pakete oder absoluter Anwendungspfade. Die Zusage sollte auf explizit geprüfte Umgebungen begrenzt bleiben.

### 7.4 Multiprocessing

Multiprocessing bringt zusätzliche Wartungskosten durch Backendwahl, Serialisierung, Ausnahmeübertragung und Wiederholungen. Der dokumentierte Fallback kann alle Tasks erneut ausführen und Seiteneffekte verdoppeln. Das ist kein verdeckter Fehler, verlangt aber geeignete Targets und kontrollierte Ressourcen.

`max_workers` begrenzt den jeweiligen EBT-Pool. Es ist keine globale Ressourcenobergrenze über pytest-xdist, mehrere EBT-Instanzen und zusätzliche Arena-Prozesse hinweg. Die Parallelisierung sollte anhand realer Lastfälle gerechtfertigt werden.

### 7.5 Umfang und Produktgrenzen

Die Abgrenzung des experimentellen Benchmarkbereichs vom Core ist in der Dokumentation sinnvoll. Gleichzeitig verbleiben Benchmark- und Agentenbestandteile in derselben Paketierungs- und Entwicklungslandschaft. Das erhöht den Pflegeumfang und kann die Konzentration auf den eigentlichen Akzeptanztestkern erschweren.

Die Core-Qualität sollte unabhängig von der Funktionsbreite der Agentenexperimente beurteilt werden. Ein umfangreicher Messapparat ersetzt weder eine zuverlässige Vergleichssemantik noch eine verständliche öffentliche API.

## 8. Sicherheits- und Reifeeinschätzung

TempFS und PyVenv behalten Benutzerrechte und Hostzugriffsmöglichkeiten. Sie bieten temporäre Arbeitsbereiche beziehungsweise Python-Abhängigkeitsumgebungen. Die inzwischen klar dokumentierte fehlende OS-Sicherheitsgrenze muss bei jeder Integration berücksichtigt werden.

Die Hydrierung enthält sinnvolle Pfadprüfungen. Diese schützen gegen bestimmte Fehlkonfigurationen beim Kopieren. Sie begrenzen nicht die Rechte des anschließend ausgeführten Targets. Pickle und Cloudpickle setzen ebenfalls vertrauenswürdige Daten voraus.

Für vertrauenswürdigen internen Code ist das ein vertretbarer Einsatzrahmen. Für fremden oder potenziell schädlichen generierten Code braucht die Prüfkette eine zusätzliche Ausführungsgrenze. Die experimentelle Studieninfrastruktur mit Containern ändert die Eigenschaften der Core-Arenen nicht.

Die CI-Konfiguration sieht vollständige Repositorytests unter Linux vor; Windows und macOS erhalten begrenzte Wheel-Prüfungen. Das ist ein sinnvoller Aufbau, aber keine vollständige Plattformabnahme. Das hier selbst ausgeführte Testergebnis gilt für die lokale Linux-Umgebung mit Python 3.13.12.

Die Anzahl erfolgreicher Tests zeigt eine erhebliche Regressionstiefe. Sie ist keine eigenständige Reifegarantie: Die bestätigten Gegenproben betreffen Verhalten, das die aktuelle Suite offenbar nicht ausreichend absichert.

## 9. Empfohlene Prioritäten

### Priorität 1: Prüfzuverlässigkeit korrigieren

- IPC-Kollisionen und Veränderungen bereitgestellter Dateien verhindern.
- Fehlerweitergabe von optimierungsabhängigen Assertions lösen.
- Nicht existierende Linterziele ausdrücklich ablehnen.
- Für diese Fälle unabhängige Regressionstests einschließlich realer Prozess-Exitcodes ergänzen.

**Abnahmekriterium:** Bereitgestellte Dateien bleiben ohne Target-Eingriff unverändert; negative EBT-/RBT-Entscheidungen scheitern auch unter `python -O`; ungültige Linterziele können nicht als erfolgreiche Analyse erscheinen.

### Priorität 2: API vereinfachen

- Zusammengehörige Ein-/Ausgabefälle ausdrücklich modellieren.
- Eingaben, Erwartungen und Beobachtungen klarer unterscheiden.
- Verbindlichen Testentscheid vom Ausgabeformat des Reporters entkoppeln.
- Fachlichen Workspace und Ausführungsinfrastruktur trennen.

**Abnahmekriterium:** Typische Nutzerfälle lassen sich ohne Kenntnis impliziter Rollenwechsel und ohne unbeabsichtigt abgeschaltete Assertions formulieren.

### Priorität 3: Datei-Workflows als Schwerpunkt schärfen

Wenige überzeugende Produktionsbeispiele mit vollständigen Verzeichnisprüfungen, verständlichen Fehlerdiagnosen und realistischen Änderungen entwickeln. Exporte, Konfigurationspakete und Dokumentgeneratoren sind geeignete Kandidaten.

**Abnahmekriterium:** Der Vorteil gegenüber einer gut geschriebenen pytest-Variante ist am gesamten Lebenszyklus nachvollziehbar: Erstellung, fachliche Änderung, Fehlerdiagnose und Review.

### Priorität 4: Nutzen direkt messen

Dieselben realistischen Aufgaben mit Cubie und gewöhnlichem pytest vergleichen. Geeignete Messgrößen sind Erstellungszeit, Änderungsaufwand, Erkennung gezielt eingebauter Fehler und Reviewverständlichkeit. Reihenfolge und Vorerfahrung müssen berücksichtigt werden.

**Abnahmekriterium:** Ein klar abgegrenzter Anwendungsfall zeigt einen reproduzierbaren Vorteil, der den zusätzlichen Lern- und Integrationsaufwand rechtfertigt.

### Priorität 5: Agentenstudien stabilisieren

Zunächst ausreichende Aufgabenlösungsfähigkeit und tatsächliche Cubie-Nutzung erreichen. Anschließend neue unabhängige Aufgaben verwenden und das Design vor der Hauptmessung festlegen. Bibliothekswirkung und Anleitungseinfluss müssen bei der Interpretation getrennt bleiben.

**Abnahmekriterium:** Die Messung untersucht eine tatsächlich genutzte Intervention auf neuen Aufgaben und erlaubt Aussagen über den angegebenen Geltungsbereich.

## 10. Entscheidungsempfehlung

Die Weiterentwicklung ist gerechtfertigt. Der stärkste Produktkern sind deklarative Akzeptanztests für vertrauenswürdige Python-Funktionen und Datei-Workflows.

Für ausgewählte interne Pilotprojekte ist qb-cubie brauchbar, sofern die dokumentierten Grenzen verstanden und die bestätigten Fehler berücksichtigt werden. Eine breite Empfehlung als verlässliche Qualitätsschranke sollte von der Korrektur der wesentlichen Fehler abhängig bleiben.

Der nächste Fortschritt sollte an drei Ergebnissen gemessen werden: zuverlässige Fehlersignale, eine leichter verständliche Vertrags-API und ein belastbarer Nutzenbeleg für konkrete wiederkehrende Datei-Workflows.
