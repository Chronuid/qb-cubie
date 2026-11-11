<center>

# Kritisches Gutachten zum Cubie-Projekt

![Cubie](./docs/.assets/cubie-logo-written.png)

Dieses Gutachten bewertet Implementierung, Aussagegrenzen und Entwicklungsbedarf des Cubie-Projekts.
**Stand:** 10. November 2026

---
**Untersuchter Code:** Commit `83577ec72be39ebd54223c52f940904cd7229b20`, Projektversion `0.0.3`, Python `3.13.12`, lokaler Linux-Rechner.

</center>

**Stand:** 9. November 2026  
**Untersuchter Stand:** Arbeitsverzeichnis auf Basis von Commit `f3a7f17`, Projektversion `0.0.3`, Python `3.13.12`.
Dieses Dokument ersetzt das Gutachten vom 9. November 2026. Es bewertet den aktuellen Code und unterscheidet bestätigte Fehler, dokumentierte Entwurfsentscheidungen und gutachterliche Einschätzungen. Die neue Bewertung behebt keine Implementierungsfehler.

## 1. Gesamturteil

Cubie ist ein interessantes, bereits substanziell implementiertes Werkzeug für deklarative Qualitätssicherung. Sein überzeugendster Nutzen liegt in der gemeinsamen Beschreibung von Eingaben, erwarteten Rückgaben und Dateisystemzuständen. Gerade für Datei-Transformationen und wiederkehrende Akzeptanzszenarien kann das die Testdefinition vereinfachen. Die austauschbaren Arenen, Reviewer und Reporter ergeben eine nachvollziehbare Erweiterungsarchitektur.
Cubie hat einen tragfähigen Kern als Werkzeug für deklarative Akzeptanztests, besonders für Datei-Workflows. Eingaben, erwartete Rückgaben und Dateisystemergebnisse gemeinsam zu beschreiben, kann wiederholte Testeinrichtung und Vergleichslogik vereinfachen. Die technische Substanz geht deutlich über ein Konzeptprojekt hinaus.

Dem stehen erhebliche Schwächen gegenüber: Der theoretische Anspruch übersteigt die tatsächlich nachgewiesenen Garantien. Mehrere reproduzierbare Fehler können Tests unbeabsichtigt bestehen lassen. Die Ausführungsumgebungen sind keine Sicherheitsgrenzen, die Installation und Repository-Struktur sind noch nicht ausreichend auf fremde Rechner ausgerichtet. Der praktische Mehrwert gegenüber gewöhnlichen pytest-Tests ist für einfache Funktionen gering; für komplexere Szenarien muss er durch belastbare Anwendungsbeispiele erst belegt werden.
Für eine verlässliche CI-Qualitätsschranke benötigt das Projekt weitere Korrekturen. Trotz umfangreicher Regressionstests lassen sich weiterhin falsche Erfolge und leere Diagnoselisten nach fehlgeschlagenen Analysen erzeugen. Der praktische Vorteil gegenüber gewöhnlichem pytest hängt stark vom Einsatzfall ab und ist bislang nicht durch unabhängige Produktivitätsmessungen belegt.

**Empfehlung:** Als experimentelles Werkzeug für vertrauenswürdigen Code weiterentwickeln und gezielt pilotieren. Als allgemeine, verlässliche Qualitätsinstanz oder Ausführungsplattform für nicht vertrauenswürdigen generierten Code derzeit nicht freigeben. Vor einer Verbreiterung des Funktionsumfangs muss die Korrektheit des Prüfkerns Vorrang erhalten.
**Empfehlung:** Für ausgewählte interne Datei-Workflows mit vertrauenswürdigem Code pilotieren. Eine breite Freigabe als verlässliche Qualitätsinstanz von der Behebung der wesentlichen Fehler abhängig machen. Der größte Entwicklungsnutzen liegt derzeit in einem korrekten, verständlichen Prüfkern und einer einfacheren API.

## 2. Auftrag, Methode und Aussagegrenzen

Untersucht wurden README, Projektkonfiguration, öffentliche Exporte, EBT- und RBT-Kern, Protokolle, Reporter, beide ausführbaren Arenen, IPC-Codecs, Multiprocessing, Linter-Anbindungen sowie ausgewählte Entwickler- und Nutzungshandbücher. Zusätzlich wurden die vorhandene Testsuite und kleine, vom Projekt unabhängige Reproduktionsskripte ausgeführt. Die unten beschriebenen Stichproben verwenden die vorhandenen APIs; am Implementierungscode wurden keine Reparaturen vorgenommen.
Untersucht wurden README und Handbücher, Projektkonfiguration, öffentliche Exporte, EBT- und RBT-Kern, Protokolle, Reporter, TempFS, PyVenv, Hydrierung, Prozesslimits, IPC-Codecs, Multiprocessing, Linter-Anbindungen, Anwendungstests sowie Paketierungs- und CI-Konfiguration.

Die vollständige Repository-Testsuite wurde mit `.venv/bin/python -m pytest -q` ausgeführt:

Das Gutachten bewertet den vorhandenen lokalen Stand. Es enthält keine Marktstudie, keine vollständige Sicherheitsprüfung, keinen Test einer veröffentlichten Distribution und keine Messung realer Produktivitätsgewinne. Aussagen zum Nutzen und zur Positionierung sind gutachterliche Einschätzungen, keine empirischen Kundenbefunde. Die Versionsnummer allein bestimmt nicht die Reife.
```text
1168 passed, 12 skipped, 6 warnings in 252.27s (0:04:12)
```

Im Arbeitsverzeichnis bestanden bereits Änderungen an `pyproject.toml`, `uv.lock` und der versionierten `.venv`; außerdem war eine frühere `GUTACHTEN.md` zur Löschung vorgemerkt. Bewertet wird der tatsächlich vorgefundene Code, nicht ausschließlich der letzte Commit. Das hier geschriebene Gutachten wird nicht automatisch gestagt oder committet.
Zusätzliche Gegenproben untersuchten Vertragsmutation, Dateivergleich, Phantom-Importe, kopierte Konsolenskripte, fehlendes Tk, den Lebenszyklus des grafischen Reviewers und Fehlerausgaben der Linter. Die Pylint-Probe beendete einen kontrollierten Kindprozess tatsächlich mit SIGKILL. Die Windows-MyPy-Probe verwendete eine kontrollierte Werkzeugausgabe unter Linux; sie ersetzt keinen Windows-Lauf. Beim GUI-Lebenszyklus wurde der Fensteraufruf ersetzt; eine echte Fensterinteraktion wurde nicht geprüft.

Die Prüfung enthält keine vollständige Sicherheitsanalyse, keine Marktstudie und keine erneute lokale Abnahme der gebauten Distribution. Die vorhandenen Installationsprüfungen und die CI-Matrix wurden im Code untersucht; daraus wird kein Nachweis tatsächlich erfolgreicher externer CI-Läufe abgeleitet. Am Implementierungscode wurden während der Untersuchung keine Reparaturen vorgenommen.

Der vorgefundene Git-Arbeitsstand war sauber. Die hier dokumentierten Testergebnisse stammen aus der Untersuchung vor der anschließenden Überarbeitung dieses Dokuments und des README-Abschnitts „Bekannte Einschränkungen“.

## 3. Idee und konzeptionelle Tragfähigkeit

### 3.1 Das tragfähige Zentrum

Cubie behandelt Tests als explizite Verträge zwischen Ausgangs- und Zielzuständen. `WorldState` bündelt Funktionsparameter, Rückgabemuster und Dateisystemabbildungen. EBT führt die Zieloperation aus und vergleicht deren Ergebnis mit einem oder mehreren erlaubten beziehungsweise verbotenen Zielzuständen. Reviewer ergänzen Prüfungen, deren Kriterien eine menschliche oder externe Beurteilung benötigen.

Diese Verbindung ist sinnvoll: Ein Dokumentkonverter lässt sich beispielsweise über Eingabedateien, einen Rückgabevertrag und erwartete Ausgabedateien beschreiben. Das kann übersichtlicher sein als wiederholt eigene Fixture-Kopien, temporäre Verzeichnisse und Vergleichslogik zu programmieren. Die standardisierten Diagnosedaten der Linter und die injizierbaren Reporter bieten zusätzliche Integrationsmöglichkeiten.
`WorldState` beschreibt Eingaben oder Erwartungen. EBT führt das Target aus und vergleicht Rückgaben, Dateien und gegebenenfalls Arena-Bestandteile. Werte, Typen, Unions, reguläre Ausdrücke, Prädikate und verschachtelte Strukturen bieten eine flexible Mustersprache. RBT ergänzt ausdrücklich formulierte Kriterien, die ein injizierter Reviewer beurteilt.

Der wesentliche Wert liegt damit in **Konventionen, Wiederverwendung und einheitlicher Orchestrierung**. Der Code implementiert keine Suche im Raum aller Programme und keinen Codegenerator. Die Suchraum-Metapher beschreibt eine Motivation; sie ist keine implementierte Produkteigenschaft.
Das passt besonders zu CSV-Exporten, Dokumentkonvertern und Generatoren: Eingabedateien bereitstellen, Operation ausführen und Rückgabe sowie erzeugte Dateien prüfen. Der Mehrwert entsteht durch gemeinsame Konventionen, wiederverwendbare Einrichtung und standardisierte Berichte.

### 3.2 Formale Sprache schafft keine formale Verifikation
### 3.2 Aussagegrenzen

README und `docs/GUIDE_Quality-Assurance.md` beziehen sich stark auf Hoare-Logik, Quantoren und verifizierte Lösungsmengen. Die Analogie zur Anordnung „Ausgangszustand – Operation – Zielzustand“ ist didaktisch brauchbar. Sie trägt jedoch keine Behauptung allgemeiner Korrektheit:
Die aktuelle [Qualitätssicherungsdokumentation](docs/GUIDE_Quality-Assurance.md) unterscheidet beobachtete Konformität, Abdeckung und Beweis angemessen. Die früher beanstandete Überhöhung mathematischer Analogien ist damit wesentlich entschärft.

- Ein `WorldState` ist ein konkreter Datensatz beziehungsweise ein Ergebnismuster, kein allgemein bewiesenes Zustandsprädikat.
- EBT prüft endlich viele Ausführungen. Es gibt weder einen Beweiskalkül noch eine vollständige Exploration aller zulässigen Eingaben.
- Das Vorhandensein mehrerer unterschiedlicher Beispiele belegt keine „Orthogonalität“. Dafür fehlen ein definiertes Merkmalsmodell und ein Nachweis unabhängiger Dimensionen.
- Ein erfolgreicher Review ist eine Beurteilung unter bestimmten Bedingungen. Er wird durch ein boolesches Ergebnis nicht zum mathematischen Beweis.
Die Vorstellung, Tests würden mögliche Programme wie eine Suchanfrage eingrenzen, bleibt eine Metapher. Cubie implementiert keine Programmsuche, Synthese oder formale Verifikation. Die Beispiele und ihre Sollwerte können unvollständig oder falsch sein. Eine erfolgreiche Reviewer-Entscheidung ist ebenfalls eine Beurteilung unter bestimmten Bedingungen.

Die Dokumentation sollte ausdrücklich zwischen beobachteter Konformität, Testabdeckung und bewiesenen Eigenschaften unterscheiden. Besonders Aussagen, fehlerhafter Code könne dem aufgespannten Raum nicht mehr entkommen, vermitteln eine nicht gedeckte Sicherheit.
Cubie enthält keinen eigenen allgemeinen PBT-Generator. Hypothesis kann ergänzend Eingaben einschließlich Randfällen generieren; die Verwendung eines Prädikats als EBT-Rückgabemuster allein bewirkt diese Exploration nicht. Siehe die [Hypothesis-Dokumentation](https://hypothesis.readthedocs.io/en/latest/).

### 3.3 Was die Quantoren tatsächlich bedeuten
### 3.3 Gemeinsame Zielmengen statt korrelierter Fälle

Für jeden ausgeführten Eingang prüft EBT, ob mindestens ein positiver Zielzustand passt und kein negativer passt. Danach müssen alle Eingangsschritte erfolgreich sein. Vereinfacht:
Die endliche Auswertungsregel ist nachvollziehbar: Jeder Eingang muss mindestens ein positives Muster erfüllen, sofern positive Muster vorliegen, und darf kein negatives Muster erfüllen. Dieselbe Zielmenge gilt jedoch für jeden Eingang.

`für jeden Eingang: (mindestens ein erlaubtes Ergebnis) UND (kein verbotenes Ergebnis)`.
Bei Eingängen `1` und `2` sowie erlaubten Ausgaben `2` und `4` akzeptiert Cubie auch `f(1)=4` und `f(2)=2`. Das ist dokumentiertes Verhalten, kein neuer Implementierungsfehler. Für gewöhnliche Funktionstests ist eine ausdrückliche Zuordnung von Eingabe und Erwartung aber oft natürlicher. Eine komfortable API für solche Paare wäre eine wichtige Verbesserung. Bis dahin sind getrennte Verträge nötig.

Diese endliche Mengenlogik ist nützlich, aber ihre Grenzen sollten sichtbar bleiben. Bei mehreren Ein- und Ausgängen entsteht keine automatische paarweise Zuordnung. Für `f(1)=2` und `f(2)=4` erlaubt eine gemeinsame Zielmenge `{2, 4}` auch eine vertauschte Implementierung. Korrelierte Fälle benötigen getrennte Verträge oder eine explizite Paarstruktur.
Auch eine Liste aller Würfelergebnisse prüft nur die beobachtete Ausgabe. Sie kontrolliert weder Zufälligkeit noch Verteilung.

Das Würfelbeispiel prüft nur, ob eine einzelne beobachtete Ausgabe in der erlaubten Menge liegt. Eine Funktion, die immer `1` liefert, besteht ebenfalls. Vollständigkeit des Ergebnisraums, Zufälligkeit und Verteilung werden damit nicht getestet. EBT ersetzt weder generative Tests noch statistische Prüfungen.
## 4. Praktischer Nutzen und Positionierung

## 4. Praktischer Nutzen und Einsatzgrenzen

| Einsatzfall | Einschätzung | Voraussetzung oder Grenze |
| Einsatzfall | Bewertung | Grenze |
| --- | --- | --- |
| Datei- und Verzeichnistransformationen | Größtes erkennbares Potenzial | Klare Vergleichssemantik und robuste Fixtures |
| Wiederholte strukturierte Ergebnisprüfungen | Nützlich | Team akzeptiert die zusätzliche Muster-Sprache |
| Einfache reine Funktionen | Begrenzter Zusatznutzen | Ein gewöhnlicher Assertion-Test ist oft kürzer |
| Strukturierte manuelle Abnahme | Sinnvoll für Experimente | Reviewer-Entscheidung bleibt subjektiv |
| CI mit RBT | Nur mit explizitem automatisiertem Reviewer | Standardreviewer fragt synchron nach Eingaben |
| Bewertung generierten Codes | Als Teil einer Prüfkette denkbar | Unabhängige Testdaten und echte Ausführungsisolation nötig |
| Ausführung fremden, potenziell schädlichen Codes | Derzeit ungeeignet | TempFS und PyVenv begrenzen keine OS-Rechte |
| Datei- und Verzeichnistransformationen | Stärkster erkennbarer Nutzen | Zuverlässige Inhalts- und Topologievergleiche erforderlich |
| Wiederkehrende strukturierte Rückgabeprüfungen | Nützlich bei gemeinsamer Teamkonvention | Zusätzliche Mustersprache muss verstanden werden |
| Einfache reine Funktionen | Häufig geringer Zusatznutzen | Direkte Assertions sind oft kürzer |
| Tests mit verschiedenen Python-Abhängigkeiten | Sinnvoller Ansatz | PyVenv hat relevante Grenzen bei kopierten Umgebungen |
| Manuelle Abnahmen | Einfacher gemeinsamer Ablauf vorhanden | Nachweisverwaltung und Abbruchsemantik unzureichend |
| Automatische Bewertung generierten Codes | Als Bestandteil einer Prüfkette denkbar | Keine fertige Bewertungsplattform oder OS-Sicherheitsgrenze |

Eine produktive Positionierung wäre: **„Deklarative Akzeptanztests für Python-Funktionen und Datei-Workflows auf Basis von pytest“**. Das ist konkret, prüfbar und näher am vorhandenen Produkt als die umfassende Suchraum- und Verifikationsrhetorik.
Für eine einfache Berechnung ist `assert calculate_tax(100, 19) == 119` leichter zu lesen als ein eigener EBT-Vertrag. pytest bietet bereits [Parametrisierung](https://docs.pytest.org/en/latest/example/parametrize.html) und [temporäre Verzeichnisse](https://pytest.org/en/stable/how-to/tmp_path.html). Cubie muss seinen Zusatznutzen deshalb an wiederkehrenden, komplexeren Abläufen zeigen.

Ein Reviewer-Protokoll ist noch keine fertige LLM-Integration. Im untersuchten Kern existieren Terminal- und Tkinter-Reviewer, aber kein integrierter Modelladapter mit Quellenübergabe, Modellversionierung, Wiederholungsstrategie und Bewertungsnachweisen. RBT führt das Target nicht aus und lädt auch nicht automatisch eine übergebene Quelldatei; `_evaluate()` reicht einen String beziehungsweise Namen weiter. Diese Arbeit muss der Reviewer leisten.
Die vorhandenen [Anwendungstests](tests/tests_user_workflows/test_order_export.py) sind ein guter Anfang. Sie untersuchen etwa falsche Inhalte, fehlende und zusätzliche Dateien sowie unerwartete Rückgaben. Teilweise wird das tatsächliche Anwendungsverhalten unabhängig von Cubie beobachtet. Das ist aussagekräftiger als eine reine API-Demonstration. Einen allgemeinen Produktivitätsgewinn oder erfolgreiche Nutzung in unabhängigen Projekten belegt es noch nicht.

Die Positionierung „Deklarative Akzeptanztests für Python-Funktionen und Datei-Workflows“ ist konkret und dem vorhandenen Produkt angemessen.

## 5. Technische Umsetzung

### 5.1 Stärken

- **Klare Erweiterungspunkte:** `Arena`, `Reviewer`, `Reporter`, `IPCC` und `Multiprocessor` beschreiben wesentliche Schnittstellen. Konkrete Implementierungen lassen sich injizieren.
- **Nachvollziehbare Ausführungsspuren:** `EvaluationTrace` und `RunTrace` erfassen erwartete und beobachtete Zustände, Ergebnisse und Laufzeiten. Das ist eine brauchbare Grundlage für bessere Berichte.
- **Breite Ergebnismuster:** Werte, Typen, Unions, reguläre Ausdrücke, Prädikate und verschachtelte Strukturen unterstützen viele praktische Prüfungen.
- **Aufräumen auch bei Fehlern:** EBT versucht Arena-Ressourcen bei Ausnahmen freizugeben und ergänzt Aufräumfehler als Notiz zur ursprünglichen Ausnahme.
- **TempFS schützt den Host-CWD vor Nebenwirkungen:** Das Target läuft in einem eigenen Prozess mit temporärem Arbeitsverzeichnis. Der Elternprozess muss seinen Arbeitsordner nicht wechseln.
- **Substanzielle Regressionstests:** Es gibt reale Subprozess- und Offline-Szenarien sowie Tests für verzögert auftretende Multiprocessing-Fehler. Die Offline-Tests prüfen auch ihren eigenen Schutzmechanismus.
- **Ehrliche Abgrenzung geplanter Virtualisierung:** Docker- und VM-Entwürfe liegen außerhalb der öffentlichen API und sind ausdrücklich als nicht implementiert dokumentiert.
- **Klare Erweiterungspunkte:** Arena, Reviewer, Reporter, IPCC und Multiprocessor sind als Schnittstellen beschrieben und injizierbar.
- **Trennung von Fehlerarten:** Erwartete Target-Ausnahmen werden von Infrastrukturfehlern unterschieden. Die Ausnahmeübertragung über Prozesse wird gezielt geprüft.
- **Historische Ergebnisse:** EBT setzt Laufdaten zurück und trennt aufgezeichnete Daten mittels Kopien von späteren Änderungen.
- **Prozessbasierte TempFS-Ausführung:** Das Arbeitsverzeichnis des Elternprozesses bleibt unverändert.
- **Hydrierungsgrenzen:** Zielpfade und verschiedene Symlink-Ausbrüche werden geprüft.
- **Ressourcen- und Fehlerprüfungen:** Tests berücksichtigen Prozessnachkommen, Ausgabegrenzen, verzögerte Multiprocessing-Fehler und mögliche Wiederholung von Seiteneffekten.
- **Persistente Berichte:** JsonReporter ersetzt seine Zieldatei erst nach erfolgreicher Serialisierung und vollständigem Schreiben.
- **Installation außerhalb des Checkouts:** Die [Wheel-Prüfung](scripts/check_wheel.py) untersucht Kerninstallation und optionale Werkzeuge getrennt.
- **Offline-Verhalten:** Die [Offline-Tests](tests/test_offline_core.py) prüfen auch ihren eigenen Schutzmechanismus.

### 5.2 Reproduzierte Korrektheitsprobleme
### 5.2 Bestätigte wesentliche Fehler

| Priorität | Befund und Fundstelle | Auswirkung | Empfehlung |
P1 bezeichnet einen wesentlichen Funktions- oder Zuverlässigkeitsfehler; P2 eine begrenztere Zuverlässigkeits- oder Wartbarkeitsschwäche. Die Einstufungen beziehen sich auf die beschriebenen Einsatzbedingungen.

| ID | Priorität | Befund | Fundstelle |
| --- | --- | --- | --- |
| P0 | `EBT._calculate_diffs()` prüft Rückgaben nur bei `post.returns is not None` | `WorldState(returns=None)` akzeptiert auch `42` | Eigenen Sentinel für „nicht angegeben“ verwenden |
| P0 | `EBT.run()` setzt `_traces` und `_outcome` nicht zurück; Schritt-IDs bleiben identisch | Ein früherer Erfolg kann einen späteren Fehler desselben Objekts über die ODER-Logik verdecken | Pro Lauf frischen Zustand und unabhängige Traces erzeugen oder Wiederverwendung ausdrücklich ablehnen |
| P1 | `pre=[]` und `post=[]` erzeugen keine Vergleichsspuren; `all([])` wird wahr | Grün ohne Target-Ausführung beziehungsweise ohne Ergebnisprüfung | Leere Listen ablehnen oder explizit als ungeprüft ausweisen |
| P1 | `MyPy._guard_process_success()` lehnt nur Exitcode 2 mit stderr ab | Ein abgebrochener Prozess mit Returncode `-9` und leerer Ausgabe wird als leere Diagnoseliste behandelt | Bekannte Erfolg-/Diagnosecodes erlauben, alle übrigen als Werkzeugfehler melden |
| P1 | `AstLinter._has_native_config()` wertet bereits die Existenz einer beliebigen `pyproject.toml` als native Konfiguration | Standardausschlüsse entfallen auch ohne Linter-Konfiguration; beim CST-Backend bleibt das Ausschlussset leer | Backend-Konfiguration gezielt prüfen und Schutz-Ausschlüsse separat behandeln |
| P2 | `PytestReporter._format_trace_details()` nutzt Wahrheitswerte der Rückgaben | Bei erwarteten `0`, `False`, `[]` oder `""` fehlen die entscheidenden Rückgabedetails im Fehlerbericht | Angegebene Werte statt Truthiness prüfen |
| P2 | `EBT._collect_topology()` erfasst ausschließlich Dateien | Fehlende leere Verzeichnisse bleiben unbemerkt | Verzeichnissemantik ausdrücklich definieren und gegebenenfalls mitvergleichen |
| B1 | P1 | Bewertung verwendet veränderliche Erwartungen, Trace dokumentiert den älteren Stand | [ebt.py](src/qb_cubie/ebt.py), `_observe_task`, `_task_traces` |
| B2 | P1 | Import-Phantome können relevante Aufrufe wirkungslos machen | [pyvenv.py](src/qb_cubie/arenas/pyvenv.py), `_decontams`; [phantom_hook.py](src/qb_cubie/arenas/phantom_hook.py) |
| B3 | P1 | Abgestürzter Pylint-Prozess kann leere Diagnoseliste liefern | [pylint.py](src/qb_cubie/linters/pylint.py), `_guard_process_success` |
| B4 | P1 | MyPy-Meldungen mit absoluten Windows-Pfaden werden verworfen | [mypy.py](src/qb_cubie/linters/mypy.py), `_MYPY_REGEX` |
| B5 | P1 | Grafischer Reviewer kann alte Freigabe und alten Bericht übernehmen | [rbt.py](src/qb_cubie/rbt.py), `HumanReviewer.review` |
| B6 | P1 | Fehlendes Tk blockiert bereits den Paketimport | [__init__.py](src/qb_cubie/__init__.py), [rbt.py](src/qb_cubie/rbt.py) |
| B7 | P1 für betroffene CLI-Workflows | Kopierte Konsolenskripte können die Basisumgebung statt des Klons verwenden | [pyvenv.py](src/qb_cubie/arenas/pyvenv.py), `setup` |

P0 bezeichnet hier Fehler im zentralen Vertrauensversprechen des Testwerkzeugs, keine Aussage über eine ausnutzbare Sicherheitslücke.
#### B1: Bewertung und dokumentierter Vertrag können auseinanderlaufen

Der Wiederholungsfehler ist besonders schwerwiegend: Nach zwei Läufen wuchs auch die Trace-Liste des bereits zurückgegebenen ersten `RunTrace` mit. Die Ergebnisse sind damit keine stabilen historischen Momentaufnahmen.
EBT kopiert Erwartungen vor der Target-Ausführung, vergleicht danach aber gegen die veränderlichen Originalobjekte. Erst anschließend ersetzt es die Erwartung im Trace durch die vorher angefertigte Kopie.

### 5.3 Reproduktionsbeispiele

Mit `PYTHONPATH=src .venv/bin/python` lassen sich die wichtigsten Befunde ohne Arena oder Netzverbindung zeigen:
Diese Gegenprobe verwendet die öffentliche API:

```python
from cubie import EBT, WorldState
from qb_cubie import EBT, WorldState

post = WorldState(returns=7)

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
def change_expectation():
    post.returns = 42
    return 42

# Zweiter Lauf liefert 2 statt 1 und bleibt trotzdem erfolgreich.
values = iter([1, 2])
test = EBT(
    target=lambda: next(values),
    post=WorldState(returns=1), reporter=None,
)
assert test.run().evaluation is True
assert test.run().evaluation is True

trace = EBT(change_expectation, post=post, reporter=None).run()
print(trace.evaluation)                       # True
print(trace.traces[0].post.returns)           # 7
print(trace.traces[0].outcome.returns)        # 42
```

Dass `reporter=None` keinen Assertion-Fehler auslöst, ist vorgesehen. Problematisch sind hier die falschen positiven `evaluation`-Werte, die auch der Standardreporter als Erfolg behandelt.
Der abgeschlossene Trace dokumentiert einen Erfolg für eine nicht erfüllte aufgezeichnete Erwartung. Gemeinsame veränderliche Objekte können ähnliche Effekte unbeabsichtigt auslösen; dies ist kein Argument für eine Sicherheitsgrenze gegenüber absichtlich manipulierendem Code.

**Empfehlung:** Gegen denselben vor Ausführung festgelegten Vertragsstand bewerten, der anschließend dokumentiert wird. Identitätsprädikate und andere nicht kopierbare Erwartungen benötigen dabei eine ausdrücklich definierte Semantik. Eine Regression muss die Übereinstimmung zwischen Entscheidungsgrundlage und Trace prüfen.

#### B2: Import-Phantome verändern die fachliche Semantik

PyVenv ersetzt standardmäßig `pytest`, `_pytest` und `loky` durch Phantome. Attributzugriffe und Methodenaufrufe werden absorbiert. Eine Gegenprobe mit einem Modul, das auf Modulebene `pytest` importiert und im Target `pytest.fail(...)` aufruft, bestand auch mit dem Standardcodec MSGspecCodec: Der ausdrückliche Fehleraufruf blieb wirkungslos. Mit PickleCodec ließ sich dies auch bei einem Import innerhalb des Targets beobachten.

Ein vorhandener Test erwartet einen Fehler, wenn ein Phantom-Ergebnis anschließend in einer Rechenoperation verwendet wird. Daraus folgt aber nicht, dass jeder relevante Laufzeitaufruf eines Phantoms fehlschlägt.

### 5.4 API und Modellierung
**Empfehlung:** Ersatzabhängigkeiten ausdrücklich wählen und eng begrenzen. Relevante Laufzeitaufrufe dürfen nicht unbemerkt verschwinden. Importhilfen für Testmodule und tatsächliche Target-Abhängigkeiten müssen unterscheidbar sein; ergänzende Gegenproben sollten ignorierte Rückgaben und Prüfaufrufe abdecken.

`WorldState` ist klein, aber durch zahlreiche `Any`-Felder schwach spezifiziert. `arena` bezeichnet je nach Kontext eine ausführbare Arena oder einen Vergleichspfad. `fs` kann mehrere Darstellungen annehmen und wird bei der Normalisierung im übergebenen Objekt verändert. Das erleichtert Kurzformen, erschwert aber Validierung, Wiederverwendung und Fehlermeldungen.
#### B3: Pylint-Abbruch wird zu Diagnosefreiheit

Weitere relevante Grenzen:
Der Prozesswächter erhebt bei einem Fehlercode nur dann eine Ausnahme, wenn stdout leer ist und stderr Text enthält. Ein tatsächlich mit SIGKILL beendeter Kindprozess ohne Ausgabe wurde über `Pylint.check()` als `[]` zurückgegeben.

- `args=[1, 2]` bedeutet zwei Positionsargumente; eine Liste als einzelnes Argument muss als `args=([1, 2],)` verpackt werden. Das benötigt klare Beispiele.
- Die Zusammenführung von Dateiquellen nach Basename kann gleichnamige Quellen überschreiben. Kollisionen sollten nicht stillschweigend verschwinden.
- Erwartete Exceptions besitzen kein eigenes Feld. Target-Ausnahmen propagieren; ein negativer Vertrag ist kein Ersatz für eine präzise Ausnahmeerwartung.
- Listen und Tupel gelten beim rekursiven Vergleich als austauschbar; Regex-Prüfungen verwenden `match()` auf `str(actual)`. Das sind legitime Entscheidungen, sofern sie als Vertragssemantik dokumentiert sind.
- Der eingefrorene `EBTContext` enthält weiterhin veränderliche Listen, Sets und Objekte. Er ist keine tiefe Zustandsisolation.
Eine Qualitätsschranke, die eine leere Diagnoseliste verlangt, kann dadurch bestehen, obwohl keine abgeschlossene Analyse vorliegt.

## 6. Arenen, Sicherheit und Reproduzierbarkeit
**Empfehlung:** Signalabbrüche und nicht gültige Werkzeugstatus unabhängig von Textausgaben als Infrastrukturfehler behandeln. Gültige Pylint-Diagnosestatus und ihre JSON-Ausgaben getrennt prüfen; die Bitmasken-Semantik des Werkzeugs berücksichtigen.

### 6.1 Sicherheitsgrenzen
#### B4: MyPy-Diagnosen mit Windows-Laufwerkspräfix gehen verloren

Die README benennt korrekt, dass TempFS und PyVenv keine OS-Sicherheitsgrenze bieten. Andere Formulierungen im Code, etwa „sandbox at the OS level“ in `_activate_arena_env()`, widersprechen dem: `PATH` und `VIRTUAL_ENV` verändern die Umgebung, entziehen aber keine Zugriffsrechte.
Der reguläre Ausdruck akzeptiert vor der Zeilennummer keinen Doppelpunkt im Dateipfad. Eine kontrollierte Ausgabe wie `C:\work\example.py:1: error: Incompatible types in assignment [assignment]` wurde bei Exitcode 1 vollständig verworfen. Die öffentliche Methode `MyPy.check()` lieferte `[]`.

Beide Arenen starten Prozesse mit den Rechten des aufrufenden Benutzers. Targets können grundsätzlich absolute Hostpfade, geerbte Umgebungsvariablen und verfügbare Netzwerkzugänge nutzen. Die FS-Hydrierung begrenzt Zielpfade nicht auf das temporäre Verzeichnis; absolute Pfade und `..` sind nicht ausgeschlossen. Das ist eine zusätzliche Konfigurationsgefahr, auch bei versehentlichen Fehlangaben.
Dies ist eine bestätigte Parserlücke anhand kontrollierter Prozessausgabe unter Linux. Eine vollständige Windows-Abnahme wurde nicht durchgeführt.

Pickle und Cloudpickle deserialisieren ausführbare Objektbeschreibungen im Host. Deshalb ist die Rückübertragung aus einer nicht vertrauenswürdigen Ausführung selbst Teil des Sicherheitsproblems. MessagePack reduziert diesen konkreten Deserialisierungsangriff, schützt aber weder das Host-Dateisystem noch vor gefälschten Ergebnissen eines bösartigen Targets.
**Empfehlung:** Dateipfade mit Laufwerkspräfix unterstützen und einen gemeldeten Analysefehler ohne erkannte Diagnosen nicht stillschweigend in eine leere Liste umwandeln. Windows-Prüfungen müssen auch echte Dateipfade statt ausschließlich In-Memory-Quelltext verwenden.

Die Import-„Dekontamination“ erzeugt Scheinmodule über `PhantomFinder`. Das kann bestimmte Importabhängigkeiten überbrücken, ist aber keine Isolation und kann Fehler verschlucken oder Testbedingungen verändern. Bei `CloudpickleCodec` ist `_apply_dependency_isolation()` ausdrücklich ein leerer Platzhalter. Der Parameter `isolation=1` suggeriert deshalb mehr implementiertes Verhalten, als vorhanden ist.
#### B5: Wiederverwendeter HumanReviewer übernimmt die vorherige Entscheidung

### 6.2 Betrieb und Ressourcen
`HumanReviewer.review()` setzt `_passed` und `_report_text` vor dem nächsten Fensteraufruf nicht zurück. Nach einer Freigabe kann das Schließen des nächsten Fensters ohne Entscheidung deshalb die alte Freigabe und den alten Bericht zurückgeben.

Die Arena-Subprozesse haben keine konfigurierbare Ausführungsfrist. Ein hängendes Target kann den Testlauf unbegrenzt blockieren. PyVenv puffert außerdem stdout und stderr vollständig. Für zuverlässige CI-Nutzung fehlen Grenzen für Laufzeit und Ausgabe sowie kontrolliertes Beenden von Prozessbäumen.
Die Gegenprobe ersetzte den GUI-Aufruf: Zunächst wurden Freigabe und Bericht gesetzt, beim zweiten Aufruf blieb die Entscheidung aus. Beide Ergebnisse waren positiv und enthielten denselben Bericht. Der normale Fenster-Schließpfad setzt ebenfalls keine neue Entscheidung.

PyVenv kopiert eine vorhandene virtuelle Umgebung und kann bei fehlenden Codec-Abhängigkeiten die Basisumgebung durch `uv pip install` verändern. Das verursacht versteckte Schreiboperationen, mögliche Netzabhängigkeit und bei paralleler Nutzung Konkurrenz auf einer gemeinsamen Basis. Die neuen Anforderungsprüfungen reduzieren unnötige Installationen und sind positiv zu bewerten; reproduzierbares Provisionieren ersetzen sie nicht.
**Empfehlung:** Jeden Review mit frischem Zustand beginnen. Fensterabbruch ausdrücklich als Abbruch oder Ablehnung behandeln. Wiederverwendung und Schließen ohne Entscheidung automatisiert prüfen.

Das mitgelieferte Basisverzeichnis enthält eine konkrete Python-3.13-Umgebung, aber Git führt dort kein `bin/python`. Ein transportabler Standardpfad lässt sich daraus für einen frischen Checkout nicht ableiten. Die Windows-Auflösung ist ebenfalls uneinheitlich: `_environment_python()` sucht `python.exe`, `_get_python_exe()` dagegen `python` im Scripts-Verzeichnis. Plattformunterstützung benötigt echte Installationstests.
#### B6: Tk ist eine versteckte Voraussetzung des gesamten Paketimports

### 6.3 Multiprocessing
Der Paketimport lädt `rbt`, und `rbt` importiert unmittelbar `tkinter`. Bei fehlendem Tk scheitert damit bereits `from qb_cubie import EBT`, obwohl kein grafischer Reviewer verwendet wird. Ein gezielt blockierter Tk-Import reproduzierte den Fehler.

Die austauschbaren Backends und Tests für spät auftretende Iteratorfehler sind sinnvoll. Allerdings richtet sich die Workerzahl nach allen gemeldeten CPUs, statt nach Aufgabenzahl oder Benutzerlimit. Zusammen mit pytest-xdist und Arena-Unterprozessen droht eine erhebliche Überbelegung.
**Empfehlung:** Tk erst bei Nutzung des grafischen Reviewers laden und dort einen Installationshinweis geben. Eine Kernimport-Prüfung ohne verfügbares Tk ergänzen.

Der automatische Backend-Fallback fängt Ausführungsfehler allgemein ab und kann die gesamte Aufgabenmenge erneut ausführen. Dadurch können fachliche Target-Fehler wie Backend-Probleme wirken; bereits ausgeführte Seiteneffekte können wiederholt werden. Die Wiederholungssemantik sollte explizit sein und Infrastrukturfehler von Target-Ausnahmen unterscheiden. Für reine Funktionen ist das weniger kritisch als für Datei-, Netzwerk- oder Datenbankoperationen.
#### B7: Venv-Kopien sind für Konsolenskripte nicht zuverlässig relocierbar

## 7. Tests, Dokumentation und Auslieferung
PyVenv kopiert die Basisumgebung mit `shutil.copytree(..., symlinks=True)`. Absolute Interpreterpfade in Konsolenskripten werden dadurch nicht angepasst.

### 7.1 Qualität der Nachweise
In einer Gegenprobe mit einer lokal erzeugten Basis und einem Konsolenskript mit absoluter Shebang lief das Target im Klon. Dasselbe Target startete über PATH das kopierte Skript; dessen `sys.prefix` zeigte weiterhin auf die ursprüngliche Basis. Umgebungsmutationen und Abhängigkeitstests können dadurch eine andere Umgebung betreffen als erwartet.

Die Testsuite ist deutlich umfangreicher als ein reiner Demonstrator: Die Sammlung ergab **432 Tests**. Positiv sind insbesondere `tests/test_offline_core.py`, gezielte TempFS-Isolationstests und die Prüfung verzögerter Multiprocessing-Ergebnisse.
Python dokumentiert virtuelle Umgebungen als im Allgemeinen nicht verschiebbar oder kopierbar; installierte Skripte enthalten absolute Interpreterpfade. Siehe die [venv-Dokumentation](https://docs.python.org/3.13/library/venv.html).

**Ausgeführte Prüfung:** `.venv/bin/python -m pytest -q --tb=short` lieferte innerhalb der eingeschränkten Sandbox zunächst **411 bestanden, 10 fehlgeschlagen, 11 übersprungen**, bei 6 Warnungen und 159,35 Sekunden Laufzeit. Acht Fehlschläge betrafen `uv pip install/uninstall` in Arena-Mutationstests; zwei betrafen einen durch Berechtigungen blockierten Multiprocessing-Manager. Die gezielte Wiederholung der zehn fehlgeschlagenen Tests außerhalb der Sandbox mit `.venv/bin/python -m pytest --lf -q --tb=short` ergab **10 bestanden** in 3,10 Sekunden (zusätzlich 1 deselected). Damit bestanden über beide Läufe alle 421 ausgeführten Tests; 11 blieben übersprungen. Es wurde kein weiterer vollständiger Lauf ohne Sandbox durchgeführt.
**Empfehlung:** Eine geeignete Provisionierungsstrategie für neue Pfade verwenden oder die Unterstützung kopierter Umgebungen ausdrücklich einschränken und prüfen. Konsolenskripte müssen Teil der Abnahme sein; ein korrektes VIRTUAL_ENV allein belegt die verwendete Umgebung nicht.

Die anfänglichen zehn Fehlschläge werden deshalb **nicht als bestätigte Implementierungsfehler gewertet**. Die in Abschnitt 5.2 dokumentierten Fehler stammen aus zusätzlichen gezielten Stichproben und bestehen unabhängig davon. Gerade diese Kombination – grüne vorhandene Tests und falsche Erfolge in einfachen Gegenproben – zeigt die Lücken der bisherigen Absicherung. Ausführungsprotokolle dieser Untersuchung liegen lokal unter `/tmp/cubie-gutachten-pytest.log` und `/tmp/cubie-gutachten-recheck.log`; diese temporären Dateien sind kein dauerhafter Projektbestandteil.
### 5.3 Weitere technische und API-Grenzen

Die Aussagekraft ist dennoch begrenzt:
**P2: Dateivergleich mit Cache.** `filecmp.cmp(..., shallow=False)` verwendet weiterhin einen Cache. Nach einem erfolgreichen Vergleich ließ sich eine gleich lange Inhaltsänderung bei wiederhergestellter mtime im erneuten Vergleich derselben Pfade verbergen: `good` und `evil` wurden als gleich bewertet. Dies wurde direkt an `_compare_paths` geprüft. Frische Pfade der eingebauten Arenen reduzieren die praktische Häufigkeit; daraus folgt kein allgemeiner Fehler jedes wiederholten EBT-Laufs. Ein Prüfkern sollte einen Vergleich ohne diese Cache-Abhängigkeit erwägen. Das Cache-Verhalten beschreibt die [Python-Dokumentation](https://docs.python.org/3.13/library/filecmp.html).

- Viele Tests prüfen EBT mit EBT. Das ist für Integration legitim, kann aber gemeinsame Bewertungsfehler verdecken. Der Prüfkern benötigt unabhängige Assertions und bewusst fehlerhafte Implementierungen als Gegenproben.
- `tests/tests_arena/test_security_arena_codec.py` verschluckt alle normalen Ausnahmen. Ein nicht ausführbarer Aufbau kann beim erwarteten „nicht kompromittiert“-Ergebnis bereits zum Bestehen führen. Die erfolgreiche Target-Ausführung muss vor der Sicherheitsbewertung nachgewiesen werden.
- Tests erwarten lokale Umgebungen wie `tests/.arenas/cowsay_env` und `tests/.arenas/empty_venv`. Deren Bereitstellung ist nicht durchgängig als reproduzierbarer Fixture-Lebenszyklus gekapselt.
- `tests/tests_multiprocessors/mp_hypothesis.py` entspricht nicht dem Standard-Dateimuster von pytest und wird beim normalen Lauf nicht gesammelt. Die vorhandene generative Testidee wirkt deshalb nicht automatisch als Regressionstor.
- `tests/conftest.py` verändert global den Arbeitsordner und erweitert `sys.path`. Das erleichtert lokale Ausführung, weist aber keine korrekte Installation des Pakets nach.
**Mehrdeutige Zustandsrollen.** WorldState dient als Eingabe, Erwartungsmuster und Beobachtung. Felder wie `arena`, `fs` und `expect` haben rollenabhängige Bedeutungen. Breite Any-Typen verschieben viele Fehler in die Laufzeit. Getrennte Datentypen oder klarere Konstruktoren könnten ungültige Verträge früher erkennbar machen.

### 7.2 Einstieg und öffentliche API
**Reporter und Fehlerpolitik sind gekoppelt.** JsonReporter persistiert, erhebt aber keine fachliche Assertion. Wer ihn anstelle des Standardreporters verwendet, verändert damit auch die Qualitätsschranke. Dieses Verhalten ist dokumentiert; es bleibt ein überraschendes Bedienkonzept. Ausgabe und Entscheidung über einen fehlgeschlagenen Test sollten unabhängig konfigurierbar sein.

Der README-Quickstart ist in der gezeigten Form nicht funktionsfähig: `WorldState` ist nicht importiert, und der EBT-Konstruktion fehlt `.run()`. Nach Ergänzung des Imports würde dieser Test nur ein Objekt anlegen und ohne Ausführung grün bleiben. Das ist bei einem Testframework ein besonders unglücklicher Einstiegsfehler.
**RBT ist ein kleiner Delegationsmechanismus.** RBT beschafft keine Quellen und führt das Target nicht aus. Ein fertiger LLM-Adapter ist nicht vorhanden. Für nachvollziehbare Abnahmen fehlen ein standardisierter Review-Kontext und eine feste Bindung an den geprüften Quellstand, etwa über dessen Hash.

Auch das RBT-Beispiel verwendet `qb.RBT`, obwohl `cubie.__init__` die Klasse nicht exportiert. Der vorhandene Zugriff lautet `from cubie.rbt import RBT`. Ausführbare Dokumentationsbeispiele sollten Teil der Tests sein.
**Komplexität und Wartbarkeit.** Die Schnittstellen sind sinnvoll, die Gesamtkombination aus Mustersprache, Arenen, mehreren Codecs, Multiprocessing und Reviewern verlangt aber erhebliches Kontextwissen. Die starre Begrenzung auf zwölf Codezeilen pro Funktionskörper fördert sehr kleine Hilfsmethoden; ihr Beitrag zur Lesbarkeit sollte anhand realer Wartungsaufgaben geprüft werden. Das ist eine Entwurfseinschätzung, kein festgestellter Funktionsfehler oder Verstoß gegen den geltenden Styleguide.

Die Dokumentation ist engagiert und erklärt viele innere Strukturen. Sie verwendet jedoch viel mathematische und bildhafte Sprache, bevor der Anwender Installation, einfache Verträge, typische Fehler und Garantien klar erfährt. Eine kürzere Anleitung mit lauffähigen Fällen und einer einzigen verbindlichen Semantiktabelle wäre hilfreicher. Historische oder geplante Aussagen sollten durchgängig als solche markiert werden.
**Aufwand der Ausführung.** Jeder Arena-Lauf verursacht Prozess- und Serialisierungsaufwand; PyVenv kopiert zusätzlich die Umgebung. EBT erzeugt für jeden Eingang Vergleiche gegen die gesamte Zielmenge und entsprechende Traces. Große Matrizen und große Datenmengen können daher teuer werden. Diese strukturelle Beobachtung ersetzt keinen repräsentativen Leistungsbenchmark.

### 7.3 Repository und Paketierung
## 6. Ausführungsgrenzen und Eignung für fremden Code

`git ls-files .venv` ergab **889 versionierte Dateien**; das lokale Verzeichnis umfasst ungefähr 129 MiB. Zusätzlich liegen 48 versionierte Dateien unter `src/cubie/arenas/arena_envs`. Diese Zahlen beschreiben den vorgefundenen Stand, keine Größe einer gebauten Distribution.
TempFS und PyVenv behalten die OS-Rechte des aufrufenden Benutzers. Temporäre Arbeitsverzeichnisse, Importfilter, Codecs und virtuelle Umgebungen sind keine OS-Sicherheitsgrenzen. Pickle und Cloudpickle setzen vertrauenswürdige Daten voraus.

Versionierte Entwicklungsumgebungen bringen maschinen- und interpreterabhängige Artefakte, fremde Metadaten und unnötiges Änderungsrauschen mit. Eine Root-`.gitignore` fehlt. Umgebungsvorlagen sollten über deklarative Anforderungen reproduziert werden, nicht über eingecheckte installierte Pakete.
Die aktuelle README beschreibt diese Grenze ausdrücklich. Das ist eine sachgerechte Produkteinschränkung. Docker- und VM-Arenen sind als Entwürfe abgegrenzt und gehören nicht zur öffentlichen API.

Die `pyproject.toml` führt pytest, mehrere Analysewerkzeuge und Prozess-/Serialisierungsbibliotheken als Pflichtabhängigkeiten. Harte Versionsbindungen bei zahlreichen Werkzeugen vergrößern das Konfliktpotenzial in konsumierenden Projekten. Sinnvoll wären ein kleiner Kern und optionale Extras für Linter und Entwicklungswerkzeuge. Python ≥3.13 kann eine bewusste Entscheidung sein, begrenzt aber den Einsatz in älteren Projekten.
Die vorhandenen Laufzeit- und Ausgabelimits verbessern die Betriebssicherheit, ersetzen aber weder vollständige Ressourcenisolation noch eine sichere Ausführungsplattform für potenziell schädlichen Code. Eine Bewertung generierten Codes muss diese Grenze in ihrer übergeordneten Architektur berücksichtigen.

Eine explizite `[build-system]`-Sektion fehlt. Das beweist für sich genommen keinen Buildfehler, lässt den vorgesehenen Build-Vertrag aber unnötig offen. Eine saubere Wheel-Erzeugung und Installation in einer leeren Umgebung sollten als Releaseprüfung festgelegt werden.
## 7. Testbasis, Paketierung und Dokumentation

Im untersuchten Repository fehlen eine eigene Projektlizenz und eine versionierte CI-Konfiguration. Lizenzen mitgelieferter Fremdpakete ersetzen keine Lizenz für Cubie. Vor breiter externer Nutzung sollten Nutzungsbedingungen, automatisierte Prüfungen und eine kleine unterstützte Plattformmatrix geklärt sein.
### 7.1 Gute Regressionstestbasis mit verbleibenden Lücken

## 8. Priorisierte Weiterentwicklung
Die 1168 bestandenen Tests sind ein positives Indiz. Besonders wertvoll sind echte Kindprozesse, kontrollierte Werkzeugfehler und Anwendungstests mit unabhängigen Beobachtungen. Die zusätzlichen Gegenproben zeigen zugleich, dass positive Regressionsergebnisse die Korrektheit der Bewertungsinstanz nicht vollständig absichern.

### Priorität 1: Der Prüfkern muss verlässlich entscheiden
Zwölf Tests wurden übersprungen, unter anderem eine manuelle GUI-Prüfung, die vorübergehend ausgesetzte Modulgrößenregel und bestimmte Kombinationen mit unerwünschten Host-Dateisystemmutationen. Die übersprungenen Fälle sind nicht als bestanden zu zählen.

1. Sentinel für nicht spezifizierte Rückgaben einführen; `None` als echten erwarteten Wert unterstützen.
2. Jeden Lauf mit frischem Zustand ausführen und unveränderliche historische Ergebnisse sicherstellen.
3. Leere und ungültige Zustandslisten sowie FS-Namenskollisionen ausdrücklich behandeln.
4. Werkzeugabbrüche von leeren Diagnoselisten unterscheiden; falsche Rückgaben vollständig berichten.
5. Unabhängige Regressionstests für diese Fälle schreiben. Gezielt fehlerhafte Targets müssen zuverlässig scheitern.
### 7.2 Vierzehn Tests werden regulär nicht eingesammelt

### Priorität 2: Einen frischen Checkout zuverlässig ausführbar machen
Die Dateien [mp_hypothesis.py](tests/tests_multiprocessors/mp_hypothesis.py), [tests_mypy.py](tests/tests_linter/tests_mypy.py) und [tests_linter.py](tests/tests_linter/tests_linter.py) entsprechen nicht den Standard-Dateinamenmustern der Testsammlung. Eine abweichende Sammlungskonfiguration oder reguläre Einbindung dieser Dateien wurde nicht gefunden.

1. Entwicklungsumgebungen aus der Versionsverwaltung entfernen und eine Root-`.gitignore` pflegen.
2. Arena-Basen in Fixtures oder einem dokumentierten Provisionierungsschritt erzeugen; Laufzeit und Installation trennen.
3. README-Beispiele reparieren und automatisiert ausführen.
4. Wheel in einer leeren Umgebung testen; eine CI mit klarer Python-/OS-Matrix einrichten.
5. Eigene Lizenz, Build-Konfiguration und Abhängigkeitsstrategie vervollständigen.
Die ausdrückliche Sammlung dieser drei Dateien ergab 14 Tests. Sie sind nicht in den 1180 regulär eingesammelten Fällen enthalten; ihre erfolgreiche Ausführung wird hier nicht behauptet. Darunter befinden sich generative Tests, die für ungewöhnliche Datenstrukturen hilfreich sein könnten.

### Priorität 3: Betriebsverhalten und Vertrag schärfen
**Empfehlung:** Dateien passend benennen oder ihre Einbindung ausdrücklich konfigurieren. Den Unterschied zwischen einsammelbaren und tatsächlich regulär ausgeführten Tests sichtbar halten.

1. Timeouts, begrenzte Ausgabe und Prozessbaum-Abbruch ergänzen.
2. Workerzahl konfigurierbar machen und an die Aufgabenzahl anpassen.
3. Backend-Fallback auf geeignete Infrastrukturfehler begrenzen und Wiederholungen dokumentieren.
4. Pfadgrenzen für Hydrierung prüfen; vertrauenswürdige und nicht vertrauenswürdige Nutzung deutlich abgrenzen.
5. Rückgaben, Ausnahmeerwartungen, FS-Topologie und persistente Berichte eindeutig modellieren.
### 7.3 Plattform- und Installationsaussagen

### Priorität 4: Den Nutzen nachweisen
Die [CI-Konfiguration](.github/workflows/ci.yml) sieht vollständige Repository-Tests unter Linux mit Python 3.13 und 3.14 vor. Unter Linux, macOS und Windows laufen zusätzlich Wheel-Prüfungen. Diese prüfen Installation außerhalb des Checkouts, Kern- und Linterprofile sowie ausgewählte Workflows.

Vor weiteren Arena-Typen oder einer umfassenden Agentenplattform sollten zwei bis drei reale Datei- und Akzeptanzworkflows umgesetzt werden. Jeweils dieselben Anforderungen einmal mit gewöhnlichem pytest und einmal mit Cubie prüfen. Vergleichskriterien: Einrichtungsaufwand, Lesbarkeit, Fehlersuche, Laufzeit und Wartung nach einer Anforderungsänderung. Erst daraus lässt sich belastbar entscheiden, wo Cubie eine eigene Abstraktion rechtfertigt.
Das ist eine gute Grundlage, bedeutet aber keine vollständige Plattformabnahme. Insbesondere werden MyPy-Prüfungen im Wheel-Smoke-Test mit In-Memory-Quelltext ausgeführt. Die Parserlücke für absolute Windows-Dateipfade kann dadurch unentdeckt bleiben.

## 9. Abschließende Bewertung
### 7.4 Dokumentation und Implementierung laufen auseinander

| Dimension | Urteil |
Zum Untersuchungszeitpunkt behauptete der README-Abschnitt „Bekannte Einschränkungen“ noch, leere Zustandslisten könnten bestehen und wiederholte EBT-Läufe würden Ergebnisse vermischen. Beides entspricht dem aktuellen Code nicht mehr. Die Semantikreferenz beschreibt diese inzwischen behobenen Punkte bereits zutreffend. Der README-Abschnitt wird zusammen mit diesem Gutachten aktualisiert.

Einzelne weitere Dokumente und Testkommentare beziehen sich noch auf das Gutachten vom 9. November und dessen Prioritätsnummern. Diese Verweise sind als historische Entstehungsreferenzen zu lesen. Insbesondere die frühere Aussage zu allgemein verschluckten MyPy-Prozessabbrüchen darf nicht mit dem aktuellen, getrennten Windows-Parserbefund verwechselt werden.

## 8. Fortschritt gegenüber dem Gutachten vom 9. November 2026

Die folgenden Punkte ordnen auch die noch in Tests erwähnten früheren Abschnitt-8-Prioritäten ein. Sie sind keine offenen Empfehlungen mit unverändertem Status.

| Frühere Referenz | Aktueller Stand |
| --- | --- |
| Problemrelevanz | Hoch: nachvollziehbare Verträge und reproduzierbare Prüfungen sind praktisch wichtig |
| Konzeptionelle Eigenständigkeit | Eher in der Kombination und Bedienung als in einem neuen Prüfverfahren |
| Nachgewiesener praktischer Mehrwert | Plausibel für Datei-Workflows, bislang nicht quantitativ belegt |
| Architektur | Gut erweiterbar, stellenweise unnötig dynamisch und zustandsreich |
| Korrektheit des Prüfkerns | Wegen reproduzierter falscher Erfolge derzeit unzureichend abgesichert |
| Sicherheitsisolation | Keine OS-Sicherheitsgrenze vorhanden |
| Auslieferungs- und Betriebsreife | Experimentell; erheblicher Bedarf bei sauberer Installation, CI und Ressourcensteuerung |
| 1.1: Explizite None-Rückgaben | UNSPECIFIED unterscheidet ausgelassene Rückgabeverträge von explizitem None. |
| 1.2: Wiederholte Läufe und historische Daten | Laufdaten werden zurückgesetzt, IDs erneuert und historische Ergebnisse kopiert. B1 betrifft eine andere Lücke während des laufenden Vergleichs. |
| 1.3: Zustandsvalidierung und FS-Kollisionen | Leere und ungültige Zustandslisten sowie mehrdeutige FS-Kurzformen werden abgelehnt. |
| 1.4: Reporting und MyPy-Prozessstatus | Rückgabeberichte wurden verbessert; MyPy akzeptiert nur Exitcode 0 oder 1. B3 betrifft Pylint, B4 den MyPy-Parser. |
| 2: Nutzbarkeit, Dokumentation und Distribution | Aussagegrenzen sind wesentlich klarer; Anwendungstests und isolierte Installationsprüfungen sind vorhanden. Einzelne Dokumentationsreste bleiben. |
| 3.1: Prozesslimits | Laufzeit- und Ausgabebudgets mit gezielten Nachkommenprüfungen vorhanden; Plattform- und Geltungsgrenzen bleiben. |
| 3.2: Worker-Begrenzung | max_workers begrenzt den jeweiligen Pool; mehrere Pools können sich weiterhin addieren. |
| 3.3: Multiprocessing-Fallback | Fehlerherkunft und Wiederholungssemantik sind wesentlich besser abgesichert. |
| 3.4: Hydrierungsgrenzen | Prüfungen für Workspace-Ausbrüche und verschiedene Linkkonstellationen vorhanden. |
| 3.5: Ausnahmeverträge | ExceptionExpectation und die Trennung von Target-Beobachtung und Infrastrukturfehlern vorhanden. |

Cubie verdient eine fokussierte Weiterentwicklung. Voraussetzung ist eine nüchterne Produktdefinition: ein hilfreiches Testwerkzeug mit klaren, begrenzten Garantien. Entscheidend für seinen Erfolg werden verlässliche negative Testergebnisse, ein reibungsloser Einstieg und nachgewiesene Vorteile in konkreten Arbeitsabläufen sein.
Diese Verbesserungen rechtfertigen eine günstigere Bewertung der technischen Reife als im älteren Gutachten. Sie beseitigen die neu bestätigten Befunde nicht.


## 9. Priorisierte Weiterentwicklung

### 9.1 Unmittelbar: falsche Erfolge verhindern

1. B1 beheben: Bewertung und aufgezeichneter Vertrag müssen übereinstimmen.
2. B2 beheben: relevante Phantom-Aufrufe dürfen nicht stillschweigend wirkungslos sein.
3. B3 und B4 beheben: fehlgeschlagene oder nicht verstandene Analysen dürfen keine Diagnosefreiheit ergeben.
4. B5 beheben: jede manuelle Abnahme braucht eine neue ausdrückliche Entscheidung.


Geeignete übergreifende Regressionseigenschaften sind: Ein Reporterwechsel verändert die fachliche Entscheidung nicht; ein Werkzeugabbruch wird niemals als saubere Analyse ausgegeben; Aufzeichnung und Entscheidung beziehen sich auf denselben Vertrag; ein Arenenwechsel verändert bei gleichen Abhängigkeiten nicht unbemerkt das fachliche Verhalten.


### 9.2 Danach: Umgebungsausführung und Abnahme absichern
1. B6 beheben: Kernimport ohne Tk ermöglichen.
2. B7 beheben oder den unterstützten Umfang kopierter Umgebungen überprüfbar einschränken.
3. Dateivergleiche gegen veraltete Cache-Ergebnisse absichern.
4. Die 14 bislang regulär nicht eingesammelten Tests einbinden und ihre Ergebnisse auswerten.
5. Windows-Dateipfade, fehlendes Tk und den GUI-Abbruch in die passenden Prüfungen aufnehmen.
6. Weitere historische Dokumentationsaussagen mit dem aktuellen Verhalten abgleichen.


### 9.3 Produktnutzen anschließend gezielt nachweisen


1. Eingabe-Erwartungs-Paare und klarere Zustandsrollen anbieten.
2. Ausgabeform und Fehlerpolitik unabhängig konfigurierbar machen.
3. Mehrere unabhängige Datei-Workflows mit gewöhnlichem pytest vergleichen: Einrichtungsaufwand, Verständlichkeit, Fehlersuche und Wartungsaufwand erfassen.
4. RBT-Nachweise an den tatsächlich geprüften Quellstand und Review-Kontext binden.
5. Neue Arenen und weitere Abstraktionen erst anhand konkreter Anwendungsbedürfnisse priorisieren.

Cubies stärkste Entwicklungsperspektive ist eine kleine, gut verständliche und nachweislich zuverlässige Akzeptanztest-Schicht. Der vorhandene Kern trägt diese Richtung; die Verlässlichkeit positiver Ergebnisse ist dafür die entscheidende nächste Voraussetzung.

---

---

<center>

## Dokumentation

![Error while trying to load the image](./docs/.assets/cubie-small.png)

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./docs/GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./docs/GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./docs/GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./docs/GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)
</center>