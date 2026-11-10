# Kritisches Gutachten zum Cubie-Projekt

**Stand:** 10. November 2026

**Untersuchter Code:** Commit `83577ec72be39ebd54223c52f940904cd7229b20`, Projektversion `0.0.3`, Python `3.13.12`, lokaler Linux-Rechner.

Dieses Dokument ersetzt das Gutachten vom 9. November 2026. Es bewertet den aktuellen Code und unterscheidet bestätigte Fehler, dokumentierte Entwurfsentscheidungen und gutachterliche Einschätzungen. Die neue Bewertung behebt keine Implementierungsfehler.

**Nachtrag zur Umsetzung von 9.1:** B1–B5 wurden anschließend im Produktivcode korrigiert und durch [ausführbare Vertragsfälle](tests/CONTRACT_CASES_9_1.md) abgesichert. Die folgenden Befunde und Untersuchungsergebnisse dokumentieren weiterhin den oben genannten untersuchten Commit; sie sind keine erneute Bewertung des korrigierten Arbeitsstands. Die aktuelle Vertragssemantik und verbleibenden Einschränkungen stehen im README und in den Handbüchern.

**Nachtrag zur Umsetzung von 9.2:** Kernfunktionen laden Tk nicht mehr; Dateiinhalte werden ohne persistenten Vergleichscache geprüft. PyVenv passt unterstützte POSIX-Python-Einstiegsskripte an den Klon an und lehnt nicht unterstützte Launcher vor dem Target-Aufruf ab. Native Windows-Konsolenlauncher sind ausdrücklich ausgeschlossen. Die drei historischen Testdateien wurden für die Standardsammlung umbenannt; der generative Prozess-Test behält 100 Beispiele und verwendet eine lokale Ausnahme von der Hypothesis-Zeitfrist. Dokumentationskorrekturen und die neue Abnahme stehen in den [Vertragsfällen zu 9.2](tests/CONTRACT_CASES_9_2.md). Die nachfolgenden historischen Befunde bleiben als Ausgangsstand erhalten.

## 1. Gesamturteil

Cubie hat einen tragfähigen Kern als Werkzeug für deklarative Akzeptanztests, besonders für Datei-Workflows. Eingaben, erwartete Rückgaben und Dateisystemergebnisse gemeinsam zu beschreiben, kann wiederholte Testeinrichtung und Vergleichslogik vereinfachen. Die technische Substanz geht deutlich über ein Konzeptprojekt hinaus.

Für eine verlässliche CI-Qualitätsschranke benötigt das Projekt weitere Korrekturen. Trotz umfangreicher Regressionstests lassen sich weiterhin falsche Erfolge und leere Diagnoselisten nach fehlgeschlagenen Analysen erzeugen. Der praktische Vorteil gegenüber gewöhnlichem pytest hängt stark vom Einsatzfall ab und ist bislang nicht durch unabhängige Produktivitätsmessungen belegt.

**Empfehlung:** Für ausgewählte interne Datei-Workflows mit vertrauenswürdigem Code pilotieren. Eine breite Freigabe als verlässliche Qualitätsinstanz von der Behebung der wesentlichen Fehler abhängig machen. Der größte Entwicklungsnutzen liegt derzeit in einem korrekten, verständlichen Prüfkern und einer einfacheren API.

## 2. Auftrag, Methode und Aussagegrenzen

Untersucht wurden README und Handbücher, Projektkonfiguration, öffentliche Exporte, EBT- und RBT-Kern, Protokolle, Reporter, TempFS, PyVenv, Hydrierung, Prozesslimits, IPC-Codecs, Multiprocessing, Linter-Anbindungen, Anwendungstests sowie Paketierungs- und CI-Konfiguration.

Die vollständige Repository-Testsuite wurde mit `.venv/bin/python -m pytest -q` ausgeführt:

```text
1168 passed, 12 skipped, 6 warnings in 252.27s (0:04:12)
```

Zusätzliche Gegenproben untersuchten Vertragsmutation, Dateivergleich, Phantom-Importe, kopierte Konsolenskripte, fehlendes Tk, den Lebenszyklus des grafischen Reviewers und Fehlerausgaben der Linter. Die Pylint-Probe beendete einen kontrollierten Kindprozess tatsächlich mit SIGKILL. Die Windows-MyPy-Probe verwendete eine kontrollierte Werkzeugausgabe unter Linux; sie ersetzt keinen Windows-Lauf. Beim GUI-Lebenszyklus wurde der Fensteraufruf ersetzt; eine echte Fensterinteraktion wurde nicht geprüft.

Die Prüfung enthält keine vollständige Sicherheitsanalyse, keine Marktstudie und keine erneute lokale Abnahme der gebauten Distribution. Die vorhandenen Installationsprüfungen und die CI-Matrix wurden im Code untersucht; daraus wird kein Nachweis tatsächlich erfolgreicher externer CI-Läufe abgeleitet. Am Implementierungscode wurden während der Untersuchung keine Reparaturen vorgenommen.

Der vorgefundene Git-Arbeitsstand war sauber. Die hier dokumentierten Testergebnisse stammen aus der Untersuchung vor der anschließenden Überarbeitung dieses Dokuments und des README-Abschnitts „Bekannte Einschränkungen“.

## 3. Idee und konzeptionelle Tragfähigkeit

### 3.1 Das tragfähige Zentrum

`WorldState` beschreibt Eingaben oder Erwartungen. EBT führt das Target aus und vergleicht Rückgaben, Dateien und gegebenenfalls Arena-Bestandteile. Werte, Typen, Unions, reguläre Ausdrücke, Prädikate und verschachtelte Strukturen bieten eine flexible Mustersprache. RBT ergänzt ausdrücklich formulierte Kriterien, die ein injizierter Reviewer beurteilt.

Das passt besonders zu CSV-Exporten, Dokumentkonvertern und Generatoren: Eingabedateien bereitstellen, Operation ausführen und Rückgabe sowie erzeugte Dateien prüfen. Der Mehrwert entsteht durch gemeinsame Konventionen, wiederverwendbare Einrichtung und standardisierte Berichte.

### 3.2 Aussagegrenzen

Die aktuelle [Qualitätssicherungsdokumentation](docs/GUIDE_Quality-Assurance.md) unterscheidet beobachtete Konformität, Abdeckung und Beweis angemessen. Die früher beanstandete Überhöhung mathematischer Analogien ist damit wesentlich entschärft.

Die Vorstellung, Tests würden mögliche Programme wie eine Suchanfrage eingrenzen, bleibt eine Metapher. Cubie implementiert keine Programmsuche, Synthese oder formale Verifikation. Die Beispiele und ihre Sollwerte können unvollständig oder falsch sein. Eine erfolgreiche Reviewer-Entscheidung ist ebenfalls eine Beurteilung unter bestimmten Bedingungen.

Cubie enthält keinen eigenen allgemeinen PBT-Generator. Hypothesis kann ergänzend Eingaben einschließlich Randfällen generieren; die Verwendung eines Prädikats als EBT-Rückgabemuster allein bewirkt diese Exploration nicht. Siehe die [Hypothesis-Dokumentation](https://hypothesis.readthedocs.io/en/latest/).

### 3.3 Gemeinsame Zielmengen statt korrelierter Fälle

Die endliche Auswertungsregel ist nachvollziehbar: Jeder Eingang muss mindestens ein positives Muster erfüllen, sofern positive Muster vorliegen, und darf kein negatives Muster erfüllen. Dieselbe Zielmenge gilt jedoch für jeden Eingang.

Bei Eingängen `1` und `2` sowie erlaubten Ausgaben `2` und `4` akzeptiert Cubie auch `f(1)=4` und `f(2)=2`. Das ist dokumentiertes Verhalten, kein neuer Implementierungsfehler. Für gewöhnliche Funktionstests ist eine ausdrückliche Zuordnung von Eingabe und Erwartung aber oft natürlicher. Eine komfortable API für solche Paare wäre eine wichtige Verbesserung. Bis dahin sind getrennte Verträge nötig.

Auch eine Liste aller Würfelergebnisse prüft nur die beobachtete Ausgabe. Sie kontrolliert weder Zufälligkeit noch Verteilung.

## 4. Praktischer Nutzen und Positionierung

| Einsatzfall | Bewertung | Grenze |
| --- | --- | --- |
| Datei- und Verzeichnistransformationen | Stärkster erkennbarer Nutzen | Zuverlässige Inhalts- und Topologievergleiche erforderlich |
| Wiederkehrende strukturierte Rückgabeprüfungen | Nützlich bei gemeinsamer Teamkonvention | Zusätzliche Mustersprache muss verstanden werden |
| Einfache reine Funktionen | Häufig geringer Zusatznutzen | Direkte Assertions sind oft kürzer |
| Tests mit verschiedenen Python-Abhängigkeiten | Sinnvoller Ansatz | PyVenv hat relevante Grenzen bei kopierten Umgebungen |
| Manuelle Abnahmen | Einfacher gemeinsamer Ablauf vorhanden | Nachweisverwaltung und Abbruchsemantik unzureichend |
| Automatische Bewertung generierten Codes | Als Bestandteil einer Prüfkette denkbar | Keine fertige Bewertungsplattform oder OS-Sicherheitsgrenze |

Für eine einfache Berechnung ist `assert calculate_tax(100, 19) == 119` leichter zu lesen als ein eigener EBT-Vertrag. pytest bietet bereits [Parametrisierung](https://docs.pytest.org/en/latest/example/parametrize.html) und [temporäre Verzeichnisse](https://pytest.org/en/stable/how-to/tmp_path.html). Cubie muss seinen Zusatznutzen deshalb an wiederkehrenden, komplexeren Abläufen zeigen.

Die vorhandenen [Anwendungstests](tests/tests_user_workflows/test_order_export.py) sind ein guter Anfang. Sie untersuchen etwa falsche Inhalte, fehlende und zusätzliche Dateien sowie unerwartete Rückgaben. Teilweise wird das tatsächliche Anwendungsverhalten unabhängig von Cubie beobachtet. Das ist aussagekräftiger als eine reine API-Demonstration. Einen allgemeinen Produktivitätsgewinn oder erfolgreiche Nutzung in unabhängigen Projekten belegt es noch nicht.

Die Positionierung „Deklarative Akzeptanztests für Python-Funktionen und Datei-Workflows“ ist konkret und dem vorhandenen Produkt angemessen.

## 5. Technische Umsetzung

### 5.1 Stärken

- **Klare Erweiterungspunkte:** Arena, Reviewer, Reporter, IPCC und Multiprocessor sind als Schnittstellen beschrieben und injizierbar.
- **Trennung von Fehlerarten:** Erwartete Target-Ausnahmen werden von Infrastrukturfehlern unterschieden. Die Ausnahmeübertragung über Prozesse wird gezielt geprüft.
- **Historische Ergebnisse:** EBT setzt Laufdaten zurück und trennt aufgezeichnete Daten mittels Kopien von späteren Änderungen.
- **Prozessbasierte TempFS-Ausführung:** Das Arbeitsverzeichnis des Elternprozesses bleibt unverändert.
- **Hydrierungsgrenzen:** Zielpfade und verschiedene Symlink-Ausbrüche werden geprüft.
- **Ressourcen- und Fehlerprüfungen:** Tests berücksichtigen Prozessnachkommen, Ausgabegrenzen, verzögerte Multiprocessing-Fehler und mögliche Wiederholung von Seiteneffekten.
- **Persistente Berichte:** JsonReporter ersetzt seine Zieldatei erst nach erfolgreicher Serialisierung und vollständigem Schreiben.
- **Installation außerhalb des Checkouts:** Die [Wheel-Prüfung](scripts/check_wheel.py) untersucht Kerninstallation und optionale Werkzeuge getrennt.
- **Offline-Verhalten:** Die [Offline-Tests](tests/test_offline_core.py) prüfen auch ihren eigenen Schutzmechanismus.

### 5.2 Bestätigte wesentliche Fehler

P1 bezeichnet einen wesentlichen Funktions- oder Zuverlässigkeitsfehler; P2 eine begrenztere Zuverlässigkeits- oder Wartbarkeitsschwäche. Die Einstufungen beziehen sich auf die beschriebenen Einsatzbedingungen.

| ID | Priorität | Befund | Fundstelle |
| --- | --- | --- | --- |
| B1 | P1 | Bewertung verwendet veränderliche Erwartungen, Trace dokumentiert den älteren Stand | [ebt.py](src/qb_cubie/ebt.py), `_observe_task`, `_task_traces` |
| B2 | P1 | Import-Phantome können relevante Aufrufe wirkungslos machen | [pyvenv.py](src/qb_cubie/arenas/pyvenv.py), `_decontams`; [phantom_hook.py](src/qb_cubie/arenas/phantom_hook.py) |
| B3 | P1 | Abgestürzter Pylint-Prozess kann leere Diagnoseliste liefern | [pylint.py](src/qb_cubie/linters/pylint.py), `_guard_process_success` |
| B4 | P1 | MyPy-Meldungen mit absoluten Windows-Pfaden werden verworfen | [mypy.py](src/qb_cubie/linters/mypy.py), `_MYPY_REGEX` |
| B5 | P1 | Grafischer Reviewer kann alte Freigabe und alten Bericht übernehmen | [rbt.py](src/qb_cubie/rbt.py), `HumanReviewer.review` |
| B6 | P1 | Fehlendes Tk blockiert bereits den Paketimport | [__init__.py](src/qb_cubie/__init__.py), [rbt.py](src/qb_cubie/rbt.py) |
| B7 | P1 für betroffene CLI-Workflows | Kopierte Konsolenskripte können die Basisumgebung statt des Klons verwenden | [pyvenv.py](src/qb_cubie/arenas/pyvenv.py), `setup` |

#### B1: Bewertung und dokumentierter Vertrag können auseinanderlaufen

EBT kopiert Erwartungen vor der Target-Ausführung, vergleicht danach aber gegen die veränderlichen Originalobjekte. Erst anschließend ersetzt es die Erwartung im Trace durch die vorher angefertigte Kopie.

Diese Gegenprobe verwendet die öffentliche API:

```python
from qb_cubie import EBT, WorldState

post = WorldState(returns=7)


def change_expectation():
    post.returns = 42
    return 42


trace = EBT(change_expectation, post=post, reporter=None).run()
print(trace.evaluation)                       # True
print(trace.traces[0].post.returns)           # 7
print(trace.traces[0].outcome.returns)        # 42
```

Der abgeschlossene Trace dokumentiert einen Erfolg für eine nicht erfüllte aufgezeichnete Erwartung. Gemeinsame veränderliche Objekte können ähnliche Effekte unbeabsichtigt auslösen; dies ist kein Argument für eine Sicherheitsgrenze gegenüber absichtlich manipulierendem Code.

**Empfehlung:** Gegen denselben vor Ausführung festgelegten Vertragsstand bewerten, der anschließend dokumentiert wird. Identitätsprädikate und andere nicht kopierbare Erwartungen benötigen dabei eine ausdrücklich definierte Semantik. Eine Regression muss die Übereinstimmung zwischen Entscheidungsgrundlage und Trace prüfen.

#### B2: Import-Phantome verändern die fachliche Semantik

PyVenv ersetzt standardmäßig `pytest`, `_pytest` und `loky` durch Phantome. Attributzugriffe und Methodenaufrufe werden absorbiert. Eine Gegenprobe mit einem Modul, das auf Modulebene `pytest` importiert und im Target `pytest.fail(...)` aufruft, bestand auch mit dem Standardcodec MSGspecCodec: Der ausdrückliche Fehleraufruf blieb wirkungslos. Mit PickleCodec ließ sich dies auch bei einem Import innerhalb des Targets beobachten.

Ein vorhandener Test erwartet einen Fehler, wenn ein Phantom-Ergebnis anschließend in einer Rechenoperation verwendet wird. Daraus folgt aber nicht, dass jeder relevante Laufzeitaufruf eines Phantoms fehlschlägt.

**Empfehlung:** Ersatzabhängigkeiten ausdrücklich wählen und eng begrenzen. Relevante Laufzeitaufrufe dürfen nicht unbemerkt verschwinden. Importhilfen für Testmodule und tatsächliche Target-Abhängigkeiten müssen unterscheidbar sein; ergänzende Gegenproben sollten ignorierte Rückgaben und Prüfaufrufe abdecken.

#### B3: Pylint-Abbruch wird zu Diagnosefreiheit

Der Prozesswächter erhebt bei einem Fehlercode nur dann eine Ausnahme, wenn stdout leer ist und stderr Text enthält. Ein tatsächlich mit SIGKILL beendeter Kindprozess ohne Ausgabe wurde über `Pylint.check()` als `[]` zurückgegeben.

Eine Qualitätsschranke, die eine leere Diagnoseliste verlangt, kann dadurch bestehen, obwohl keine abgeschlossene Analyse vorliegt.

**Empfehlung:** Signalabbrüche und nicht gültige Werkzeugstatus unabhängig von Textausgaben als Infrastrukturfehler behandeln. Gültige Pylint-Diagnosestatus und ihre JSON-Ausgaben getrennt prüfen; die Bitmasken-Semantik des Werkzeugs berücksichtigen.

#### B4: MyPy-Diagnosen mit Windows-Laufwerkspräfix gehen verloren

Der reguläre Ausdruck akzeptiert vor der Zeilennummer keinen Doppelpunkt im Dateipfad. Eine kontrollierte Ausgabe wie `C:\work\example.py:1: error: Incompatible types in assignment [assignment]` wurde bei Exitcode 1 vollständig verworfen. Die öffentliche Methode `MyPy.check()` lieferte `[]`.

Dies ist eine bestätigte Parserlücke anhand kontrollierter Prozessausgabe unter Linux. Eine vollständige Windows-Abnahme wurde nicht durchgeführt.

**Empfehlung:** Dateipfade mit Laufwerkspräfix unterstützen und einen gemeldeten Analysefehler ohne erkannte Diagnosen nicht stillschweigend in eine leere Liste umwandeln. Windows-Prüfungen müssen auch echte Dateipfade statt ausschließlich In-Memory-Quelltext verwenden.

#### B5: Wiederverwendeter HumanReviewer übernimmt die vorherige Entscheidung

`HumanReviewer.review()` setzt `_passed` und `_report_text` vor dem nächsten Fensteraufruf nicht zurück. Nach einer Freigabe kann das Schließen des nächsten Fensters ohne Entscheidung deshalb die alte Freigabe und den alten Bericht zurückgeben.

Die Gegenprobe ersetzte den GUI-Aufruf: Zunächst wurden Freigabe und Bericht gesetzt, beim zweiten Aufruf blieb die Entscheidung aus. Beide Ergebnisse waren positiv und enthielten denselben Bericht. Der normale Fenster-Schließpfad setzt ebenfalls keine neue Entscheidung.

**Empfehlung:** Jeden Review mit frischem Zustand beginnen. Fensterabbruch ausdrücklich als Abbruch oder Ablehnung behandeln. Wiederverwendung und Schließen ohne Entscheidung automatisiert prüfen.

#### B6: Tk ist eine versteckte Voraussetzung des gesamten Paketimports

Der Paketimport lädt `rbt`, und `rbt` importiert unmittelbar `tkinter`. Bei fehlendem Tk scheitert damit bereits `from qb_cubie import EBT`, obwohl kein grafischer Reviewer verwendet wird. Ein gezielt blockierter Tk-Import reproduzierte den Fehler.

**Empfehlung:** Tk erst bei Nutzung des grafischen Reviewers laden und dort einen Installationshinweis geben. Eine Kernimport-Prüfung ohne verfügbares Tk ergänzen.

#### B7: Venv-Kopien sind für Konsolenskripte nicht zuverlässig relocierbar

PyVenv kopiert die Basisumgebung mit `shutil.copytree(..., symlinks=True)`. Absolute Interpreterpfade in Konsolenskripten werden dadurch nicht angepasst.

In einer Gegenprobe mit einer lokal erzeugten Basis und einem Konsolenskript mit absoluter Shebang lief das Target im Klon. Dasselbe Target startete über PATH das kopierte Skript; dessen `sys.prefix` zeigte weiterhin auf die ursprüngliche Basis. Umgebungsmutationen und Abhängigkeitstests können dadurch eine andere Umgebung betreffen als erwartet.

Python dokumentiert virtuelle Umgebungen als im Allgemeinen nicht verschiebbar oder kopierbar; installierte Skripte enthalten absolute Interpreterpfade. Siehe die [venv-Dokumentation](https://docs.python.org/3.13/library/venv.html).

**Empfehlung:** Eine geeignete Provisionierungsstrategie für neue Pfade verwenden oder die Unterstützung kopierter Umgebungen ausdrücklich einschränken und prüfen. Konsolenskripte müssen Teil der Abnahme sein; ein korrektes VIRTUAL_ENV allein belegt die verwendete Umgebung nicht.

### 5.3 Weitere technische und API-Grenzen

**P2: Dateivergleich mit Cache.** `filecmp.cmp(..., shallow=False)` verwendet weiterhin einen Cache. Nach einem erfolgreichen Vergleich ließ sich eine gleich lange Inhaltsänderung bei wiederhergestellter mtime im erneuten Vergleich derselben Pfade verbergen: `good` und `evil` wurden als gleich bewertet. Dies wurde direkt an `_compare_paths` geprüft. Frische Pfade der eingebauten Arenen reduzieren die praktische Häufigkeit; daraus folgt kein allgemeiner Fehler jedes wiederholten EBT-Laufs. Ein Prüfkern sollte einen Vergleich ohne diese Cache-Abhängigkeit erwägen. Das Cache-Verhalten beschreibt die [Python-Dokumentation](https://docs.python.org/3.13/library/filecmp.html).

**Mehrdeutige Zustandsrollen.** WorldState dient als Eingabe, Erwartungsmuster und Beobachtung. Felder wie `arena`, `fs` und `expect` haben rollenabhängige Bedeutungen. Breite Any-Typen verschieben viele Fehler in die Laufzeit. Getrennte Datentypen oder klarere Konstruktoren könnten ungültige Verträge früher erkennbar machen.

**Reporter und Fehlerpolitik sind gekoppelt.** JsonReporter persistiert, erhebt aber keine fachliche Assertion. Wer ihn anstelle des Standardreporters verwendet, verändert damit auch die Qualitätsschranke. Dieses Verhalten ist dokumentiert; es bleibt ein überraschendes Bedienkonzept. Ausgabe und Entscheidung über einen fehlgeschlagenen Test sollten unabhängig konfigurierbar sein.

**RBT ist ein kleiner Delegationsmechanismus.** RBT beschafft keine Quellen und führt das Target nicht aus. Ein fertiger LLM-Adapter ist nicht vorhanden. Für nachvollziehbare Abnahmen fehlen ein standardisierter Review-Kontext und eine feste Bindung an den geprüften Quellstand, etwa über dessen Hash.

**Komplexität und Wartbarkeit.** Die Schnittstellen sind sinnvoll, die Gesamtkombination aus Mustersprache, Arenen, mehreren Codecs, Multiprocessing und Reviewern verlangt aber erhebliches Kontextwissen. Die starre Begrenzung auf zwölf Codezeilen pro Funktionskörper fördert sehr kleine Hilfsmethoden; ihr Beitrag zur Lesbarkeit sollte anhand realer Wartungsaufgaben geprüft werden. Das ist eine Entwurfseinschätzung, kein festgestellter Funktionsfehler oder Verstoß gegen den geltenden Styleguide.

**Aufwand der Ausführung.** Jeder Arena-Lauf verursacht Prozess- und Serialisierungsaufwand; PyVenv kopiert zusätzlich die Umgebung. EBT erzeugt für jeden Eingang Vergleiche gegen die gesamte Zielmenge und entsprechende Traces. Große Matrizen und große Datenmengen können daher teuer werden. Diese strukturelle Beobachtung ersetzt keinen repräsentativen Leistungsbenchmark.

## 6. Ausführungsgrenzen und Eignung für fremden Code

TempFS und PyVenv behalten die OS-Rechte des aufrufenden Benutzers. Temporäre Arbeitsverzeichnisse, Importfilter, Codecs und virtuelle Umgebungen sind keine OS-Sicherheitsgrenzen. Pickle und Cloudpickle setzen vertrauenswürdige Daten voraus.

Die aktuelle README beschreibt diese Grenze ausdrücklich. Das ist eine sachgerechte Produkteinschränkung. Docker- und VM-Arenen sind als Entwürfe abgegrenzt und gehören nicht zur öffentlichen API.

Die vorhandenen Laufzeit- und Ausgabelimits verbessern die Betriebssicherheit, ersetzen aber weder vollständige Ressourcenisolation noch eine sichere Ausführungsplattform für potenziell schädlichen Code. Eine Bewertung generierten Codes muss diese Grenze in ihrer übergeordneten Architektur berücksichtigen.

## 7. Testbasis, Paketierung und Dokumentation

### 7.1 Gute Regressionstestbasis mit verbleibenden Lücken

Die 1168 bestandenen Tests sind ein positives Indiz. Besonders wertvoll sind echte Kindprozesse, kontrollierte Werkzeugfehler und Anwendungstests mit unabhängigen Beobachtungen. Die zusätzlichen Gegenproben zeigen zugleich, dass positive Regressionsergebnisse die Korrektheit der Bewertungsinstanz nicht vollständig absichern.

Zwölf Tests wurden übersprungen, unter anderem eine manuelle GUI-Prüfung, die vorübergehend ausgesetzte Modulgrößenregel und bestimmte Kombinationen mit unerwünschten Host-Dateisystemmutationen. Die übersprungenen Fälle sind nicht als bestanden zu zählen.

### 7.2 Vierzehn Tests werden regulär nicht eingesammelt

Die damaligen Dateien [mp_hypothesis.py](tests/tests_multiprocessors/test_mp_hypothesis.py), [tests_mypy.py](tests/tests_linter/test_mypy.py) und [tests_linter.py](tests/tests_linter/test_linter.py) entsprachen nicht den Standard-Dateinamenmustern der Testsammlung. Eine abweichende Sammlungskonfiguration oder reguläre Einbindung dieser Dateien wurde zum Untersuchungszeitpunkt nicht gefunden. Die Links führen inzwischen zu den für 9.2 umbenannten Dateien.

Die ausdrückliche Sammlung dieser drei Dateien ergab 14 Tests. Sie sind nicht in den 1180 regulär eingesammelten Fällen enthalten; ihre erfolgreiche Ausführung wird hier nicht behauptet. Darunter befinden sich generative Tests, die für ungewöhnliche Datenstrukturen hilfreich sein könnten.

**Empfehlung:** Dateien passend benennen oder ihre Einbindung ausdrücklich konfigurieren. Den Unterschied zwischen einsammelbaren und tatsächlich regulär ausgeführten Tests sichtbar halten.

### 7.3 Plattform- und Installationsaussagen

Die [CI-Konfiguration](.github/workflows/ci.yml) sieht vollständige Repository-Tests unter Linux mit Python 3.13 und 3.14 vor. Unter Linux, macOS und Windows laufen zusätzlich Wheel-Prüfungen. Diese prüfen Installation außerhalb des Checkouts, Kern- und Linterprofile sowie ausgewählte Workflows.

Das ist eine gute Grundlage, bedeutet aber keine vollständige Plattformabnahme. Insbesondere werden MyPy-Prüfungen im Wheel-Smoke-Test mit In-Memory-Quelltext ausgeführt. Die Parserlücke für absolute Windows-Dateipfade kann dadurch unentdeckt bleiben.

### 7.4 Dokumentation und Implementierung laufen auseinander

Zum Untersuchungszeitpunkt behauptete der README-Abschnitt „Bekannte Einschränkungen“ noch, leere Zustandslisten könnten bestehen und wiederholte EBT-Läufe würden Ergebnisse vermischen. Beides entspricht dem aktuellen Code nicht mehr. Die Semantikreferenz beschreibt diese inzwischen behobenen Punkte bereits zutreffend. Der README-Abschnitt wird zusammen mit diesem Gutachten aktualisiert.

Einzelne weitere Dokumente und Testkommentare beziehen sich noch auf das Gutachten vom 9. November und dessen Prioritätsnummern. Diese Verweise sind als historische Entstehungsreferenzen zu lesen. Insbesondere die frühere Aussage zu allgemein verschluckten MyPy-Prozessabbrüchen darf nicht mit dem aktuellen, getrennten Windows-Parserbefund verwechselt werden.

## 8. Fortschritt gegenüber dem Gutachten vom 9. November 2026

Die folgenden Punkte ordnen auch die noch in Tests erwähnten früheren Abschnitt-8-Prioritäten ein. Sie sind keine offenen Empfehlungen mit unverändertem Status.

| Frühere Referenz | Aktueller Stand |
| --- | --- |
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

Ein [Konzept für die Benchmarks ReviewAgent und DeveloperAgent](docs/BENCHMARK_KONZEPT.md) beschreibt ein allgemein nutzbares Prüfwerkzeug für eigene Agentensysteme mit erweiterbaren Szenariopaketen und konfigurierbaren Benchmark-Sets. Ein optionales Vergleichsprofil konkretisiert die Produktnutzenmessung; Review-Nachweise werden an Quellstand und Kontext gebunden. Es ist ein Implementierungsentwurf; Messergebnisse liegen damit noch nicht vor.

1. Eingabe-Erwartungs-Paare und klarere Zustandsrollen anbieten.
2. Ausgabeform und Fehlerpolitik unabhängig konfigurierbar machen.
3. Mehrere unabhängige Datei-Workflows mit gewöhnlichem pytest vergleichen: Einrichtungsaufwand, Verständlichkeit, Fehlersuche und Wartungsaufwand erfassen.
4. RBT-Nachweise an den tatsächlich geprüften Quellstand und Review-Kontext binden.
5. Neue Arenen und weitere Abstraktionen erst anhand konkreter Anwendungsbedürfnisse priorisieren.

Cubies stärkste Entwicklungsperspektive ist eine kleine, gut verständliche und nachweislich zuverlässige Akzeptanztest-Schicht. Der vorhandene Kern trägt diese Richtung; die Verlässlichkeit positiver Ergebnisse ist dafür die entscheidende nächste Voraussetzung.
