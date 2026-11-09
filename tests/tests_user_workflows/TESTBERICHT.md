# Nutzerexperimente mit Cubie: unabhängige EBT-Regressionen

**Nachtrag vom 10. November:** Zusätzliche Fälle zur FS-Diagnose, der ursprüngliche
Fehlerstand und die anschließende Produktionskorrektur sind im
[ergänzenden FS-Testbericht](FS_TESTBERICHT.md) dokumentiert. Die folgenden
Laufzahlen beschreiben den ursprünglichen Stand.

**Datum:** 9. November 2026. **Ausgangspunkt:** Commit `01cb8bd`, Cubie
`0.0.3`, Python `3.13.12`, pytest `9.2.0`, Linux.
**Auftrag:** [GUTACHTEN.md, Abschnitt 8, Priorität 1.5](../../GUTACHTEN.md),
mit den Fällen aus 1.1 bis 1.4.

## Vorgehen und Unabhängigkeit

Die Frage dieser Versuche lautet: Kann ich mit Cubie einfache Aufgaben meines
eigenen Projekts absichern und bemerke ich dabei typische Implementierungsfehler?
Die vier kleinen Anwendungen in [targets.py](targets.py) importieren Cubie nicht.
Die EBT-Verträge wurden aus fachlichen Erwartungen formuliert. Für diese Arbeit
wurde kein Produktivcode geändert; Cubie wird über seine öffentlichen APIs benutzt.

Beim Export und beim Konfigurationspaket läuft dieselbe Anwendungsvariante zunächst
direkt in einem eigenen temporären Verzeichnis. Gewöhnliche pytest-Assertions
vergleichen Rückgabe und Dateibytes mit ausdrücklich vorgegebenen Sollwerten.
Erst danach folgt der EBT-Lauf in `TempFS`. Beim Lager werden konkrete Zählerstände
und historische Ergebnisse geprüft. Beim Typprüfungs-Gate liefert zusätzlich ein
direkt gestarteter Prozess einen von Cubies Auswertung unabhängigen Exitcode.

Jeder normale Akzeptanzvertrag wird mit dem Standardreporter und mit
`reporter=None` ausgeführt. Im ersten Modus muss ein fachlicher Fehler eine
`AssertionError` auslösen; im zweiten muss die nicht negierte `evaluation` exakt
`False` sein. Auch der erste Modus prüft zusätzlich `run_trace.evaluation`.
Kein Vertrag verwendet `EBT(expect=False)` als Beweis für seine eigene Korrektheit.
Es gibt keine Patches an Vergleich, Reporter oder Prozessausführung und keine
`xfail`-Markierungen.

Ein zusätzlicher pytest-Kindprozess führt fünf echte Nutzerbeispiele aus:
eine korrekte Anwendung und vier fehlerhafte. Die äußere Regression prüft dessen
Exitcode und JUnit-Datei: genau ein Erfolg und vier EBT-Assertion-Fehlschläge;
Importfehler, andere Ausführungsfehler oder übersprungene Fälle zählen nicht als
erfolgreiche Fehlererkennung. Die inneren Beispiele werden im normalen Testlauf
nicht unmittelbar gesammelt, sondern über diesen Regressionstest gestartet.

## Verlauf der Experimente

### 1. Buchhaltung: bezahlte Aufträge als CSV exportieren

**Anforderung:** Von einem bezahlten und einem unbezahlten Auftrag wird nur der
bezahlte exportiert. Zwei Stück zu 125 Cent ergeben 250 Cent. Ohne bezahlten Auftrag
enthält die Ausgabe nur die Kopfzeile. Der Exportbefehl liefert ausdrücklich `None`.
Die Eingabedatei bleibt erhalten, weitere Dateien sind nicht vorgesehen.

Zunächst wurde ein reiner Dateivertrag ausprobiert. Ein Export mit korrekter Datei
und der Rückgabe `0` besteht damit. Das ist eine bewusste Kontrollbeobachtung:
Ein ausgelassenes `returns` darf keine Erwartung an die Rückgabe erfinden. Der
vollständige Vertrag ergänzt deshalb `returns=None`. Mit `fs={".": referenz}`
werden außerdem alle Dateien im Workspace erfasst; ein Mapping nur für die
Ausgabedatei würde zusätzliche Dateien außerhalb dieses Pfads nicht prüfen.

Danach wurden vier gezielt fehlerhafte Varianten jeweils mit und ohne bezahlten
Auftrag ausprobiert:

| Variante | Unabhängige Beobachtung | Ergebnis des vollständigen EBT-Vertrags |
| --- | --- | --- |
| Korrekt | Richtige CSV, Rückgabe `None`, keine Zusatzdatei | Akzeptiert |
| Auftragsanzahl zurückgeben | Dateien richtig, Rückgabe `1` bzw. `0` | Abgelehnt; Meldung enthält erwartetes `None` und tatsächliche Anzahl |
| Unbezahlte Aufträge einschließen | Zusätzliche CSV-Zeilen | Abgelehnt, FS-Abweichung |
| Exportdatei nicht schreiben | `paid.csv` fehlt | Abgelehnt, FS-Abweichung |
| Debugdatei zurücklassen | Zusätzliche `debug.txt` | Abgelehnt, FS-Abweichung |

**Erkenntnis:** Rückgabe und Dateien müssen gemeinsam zum Vertrag passen. Ein
richtiger Teil darf einen falschen Teil nicht verdecken. Gerade der leere Export
prüft den Unterschied zwischen „Rückgabe nicht angegeben“ und „`None` erwartet“
mit einer falschen, aber falsy Rückgabe `0`.

**Nebenbefund zur Fehlersuche:** Beim unmittelbar ausgeführten Nutzerbeispiel
`test_unpaid_order_exported` mit einzeln gemappter Ausgabedatei erkennt Cubie die
falsche CSV korrekt. Die Konsolenmeldung nennt jedoch `FS: Mismatch` zusammen mit
`Details: -0 Missing | +0 Unexpected | ~0 Modified`, ohne die betroffene Datei
anzugeben. Für mich als Nutzer ist diese Detailzusammenfassung irreführend: Die
Datei wurde nachweislich verändert. Der tatsächliche Ausschnitt ist im
[Protokoll des direkten pytest-Laufs](results/acceptance-pytest.txt) festgehalten.
Das ist ein offener Befund zur FS-Diagnose; die Rückgabediagnosen aus Punkt 1.4
sind davon getrennt und bestehen die hier formulierten Anforderungen.

### 2. Lager: denselben Vertrag erneut prüfen und alte Belege aufheben

**Anforderung:** Bei zwei vorhandenen Einheiten bleibt nach einer Reservierung
eine übrig. Dieselbe EBT-Instanz wird erneut aufgerufen, während das Lager weiter
abnimmt. Der Vertrag bleibt zunächst unverändert.

Der erste Lauf beobachtet `{"remaining": [1]}` und besteht. Der zweite beobachtet
`{"remaining": [0]}`, der dritte `{"remaining": [-1]}`; beide müssen scheitern.
Die negativen Bestände sind hier ein absichtlich einfacher Fehlerfall des
Beispieltargets, keine empfohlene Lagerlogik. Jeder Lauf muss genau eine eigene
Trace und eine eigene Lauf-ID besitzen.

Die Anwendung verwendet für ihre Rückgabe dasselbe veränderliche Ledger-Objekt.
Trotzdem muss das erste Ergebnis nach weiteren Reservierungen, nach einer Änderung
der ursprünglichen Erwartungsdaten und nach einem wieder erfolgreichen Lauf
unverändert bleiben. Geprüft werden sowohl die vollständige erste Momentaufnahme
als auch die konkreten alten Ledger-Werte.

Zusätzlich werden vier alltägliche Leerwerte ausprobiert: Bestand `0`, Lieferbarkeit
`False`, offene Positionen `[]` und nächste Artikelnummer `""`. Die korrekten
Funktionen bestehen. Varianten mit `1`, `True`, `["SKU-1"]` und `"SKU-1"` scheitern;
die Reportermeldung muss den erwarteten und tatsächlichen Wert enthalten.

**Ergebnis:** Ein früherer Erfolg verdeckt spätere Fehler nicht. Die historischen
Ergebnisse bleiben stabil, und alle vier Leerwertfehler werden erkannt und berichtet.

### 3. Shop: zwei gleichnamige Konfigurationsdateien zusammenführen

**Anforderung:** `shop/settings.json` liefert die Währung `EUR`,
`shipping/settings.json` die Versandregion `EU`. Das Paket muss
`{"currency": "EUR", "region": "EU"}` liefern und als JSON-Datei schreiben.

Eine Quellenliste mit beiden Hostdateien ist wegen der identischen Basenames
mehrdeutig. Diese Kurzform wurde sowohl als `pre.fs` als auch als `post.fs`
ausprobiert. Beide Aufbauten müssen mit `ValueError` scheitern, beide Quellpfade
nennen und dürfen das Target nicht aufrufen. Explizite Zielpfade lösen die
Mehrdeutigkeit; das korrekte Paket besteht dann.

Eine Mutation liest für die Versandregion versehentlich erneut die Shopdatei.
Sie liefert und schreibt `DE` statt `EU`. Unabhängige Assertions erkennen beides;
EBT lehnt ebenfalls Rückgabe und Datei ab.

Als weiterer Nutzerfehler werden aus einer externen Falltabelle erzeugte Zustände
ausprobiert: eine leere Liste und eine nicht konvertierte String-Zeile, jeweils
für `pre` und `post`. Sie müssen mit `ValueError` bzw. `TypeError` scheitern, bevor
die Anwendung läuft. Auch eine nach einem erfolgreichen Lauf geleerte Eingangsliste
muss scheitern und darf keinen alten Erfolg als aktuelles `run_trace` anbieten.

**Ergebnis:** Mehrdeutige Dateiquellen und unbrauchbare Falltabellen werden
ausdrücklich abgewiesen. Der erfolgreiche, explizit gemappte Fall belegt, dass
nicht bloß jeder Aufbau fehlschlägt.

### 4. CI: eine Typprüfung als Freigabe-Gate verwenden

**Anforderung:** Eine kleine Preisfunktion besteht die Typprüfung. Eine als `int`
deklarierte Funktion mit String-Rückgabe wird nicht freigegeben. Ein abgebrochenes
Werkzeug darf keine leere, vermeintlich erfolgreiche Diagnoseliste liefern.

Zunächst wird ein echtes MyPy über den vorhandenen Python-Interpreter gestartet,
mit eigener Konfiguration und temporärem Cache. Der direkte Prozess liefert für
die korrekte Datei Exitcode `0`, für die falsche Exitcode `1` und `return-value`.
Der gleiche Aufruf über `MyPy.check` als EBT-Target erwartet `returns=[]`:
Die korrekte Datei besteht; die fehlerhafte wird mit genau einer Diagnose in Zeile
2 abgelehnt. Die Reporterdiagnose muss auch das erwartete leere `[]` zeigen.

Danach werden drei tatsächlich ausgeführte Fehlerprozesse über den öffentlichen
Parameter `MyPy(executable=...)` eingesetzt: stille Beendigung mit Code `2`,
Code `127` und auf POSIX Selbstbeendigung durch `SIGKILL` (`-9`). Das sind explizite
Fehlerinjektoren, keine Behauptung, dass MyPy selbst in diesen Versuchen abstürzte.
Eine Markerdatei belegt jeweils den Prozessstart auch beim EBT-Aufruf. Die Prozesse
schreiben weder stdout noch stderr. Alle drei müssen als `RuntimeError` mit
Prozesscode und Werkzeugpfad propagieren; `run_trace` darf keinen Erfolg enthalten.

**Ergebnis:** Eine fachliche Typdiagnose führt zu einem roten Vertrag; ein
Werkzeugabbruch führt zu einem Werkzeugfehler. Beides verhindert die Freigabe.

## Zuordnung zu Priorität 1 des Gutachtens

| Punkt | Neue unabhängige Nutzerprobe |
| --- | --- |
| 1.1: ausgelassen vs. `None` | Dateivertrag ohne Rückgabeprüfung und vollständiger Exportvertrag; falsche Rückgaben `0`/`1` |
| 1.2: frische Läufe und stabile Historie | Reservierungen `1 → 0 → -1 → 1`, geteiltes Ledger, spätere Änderung der Erwartungsdaten |
| 1.3: Zustandslisten und FS-Kollisionen | Leere/ungültige Falltabellen, nachträglich leere Liste, zwei `settings.json`, explizite Zielpfade |
| 1.4: Werkzeugabbrüche und vollständige Rückgabemeldung | Reale stille Fehlerprozesse, echte MyPy-Diagnose, Meldungen für `None`, `0`, `False`, `[]`, `""` |
| 1.5: unabhängige Regressionen | Direkte fachliche Orakel, unnegierte RunTrace-Prüfung, echte pytest-Fehlschläge im Kindprozess |

## Ausführung und Nachweise

Vom Repository-Wurzelverzeichnis:

```bash
.venv/bin/python -m pytest -q tests/tests_user_workflows --tb=short
.venv/bin/python -m ruff check tests/tests_user_workflows
```

Die vier absichtlich fehlerhaften Beispiele lassen sich auch unmittelbar ansehen.
**Dieser Befehl soll Exitcode 1 sowie vier Fehlschläge und einen Erfolg liefern:**

```bash
PYTHONPATH=src:tests .venv/bin/python -m pytest -q --tb=short \
  tests/tests_user_workflows/examples/acceptance_cases.py
```

Die Ergebnisse der abschließenden Läufe sind unter [results](results) als
Textprotokolle festgehalten. Ein erster Lauf der vier Szenarien ergab **56 bestanden**
in 5,81 Sekunden; nach Ergänzung der unabhängigen pytest-Prozessprüfung waren es
**57 bestanden** in 6,22 Sekunden. Danach kamen die beiden Kontrollfälle mit
ausgelassener Rückgabeerwartung hinzu. Bei Ruff wurden zunächst Importreihenfolge
und fehlendes explizites `check=False` beanstandet und anschließend korrigiert.

Der abschließende Package-Lauf ergibt **59 bestanden** in **11,46 Sekunden**
([Einzelfälle](results/package-pytest.txt)). Der direkt ausgeführte Satz an
Nutzerbeispielen liefert wie gefordert **4 fehlgeschlagen, 1 bestanden**, Exitcode
`1`, in **0,33 Sekunden** ([Fehlerberichte](results/acceptance-pytest.txt)).
Die vier Fehlschläge sind die gewollte Beobachtung der fehlerhaften Targets;
der äußere Regressionstest prüft sie und besteht. Ruff meldet
**All checks passed!** ([Protokoll](results/ruff.txt)). Die Laufzeiten dienen nur
der Dokumentation; der Package-Lauf fand parallel zur Gesamtsuite statt.

| Datei | Gesammelte Fälle |
| --- | ---: |
| [test_order_export.py](test_order_export.py) | 22 |
| [test_stock.py](test_stock.py) | 18 |
| [test_settings_bundle.py](test_settings_bundle.py) | 11 |
| [test_quality_gate.py](test_quality_gate.py) | 7 |
| [test_pytest_process.py](test_pytest_process.py) | 1 |
| **Summe** | **59** |

Die anschließende Auswertung des vollständigen Projektlaufs
`.venv/bin/python -m pytest -q --tb=short --junitxml=/tmp/cubie-user-workflows-full.xml`
ergibt **746 bestanden, 11 übersprungen, 6 Warnungen** in **178,69 Sekunden**,
Exitcode `0`. Alle 59 neuen Regressionen sind darin enthalten. Die Warnungen
betreffen bestehende TempFS- und PyVenv-Tests; das neue Package erzeugt keine
Warnung. Die Zahlen und die Namen der übersprungenen Tests sind im
[Gesamtprotokoll](results/full-suite.txt) festgehalten und gegen die erzeugte
JUnit-Datei geprüft.

In den untersuchten Fällen wurde kein falscher Erfolg des Prüfkerns beobachtet.
Die gezielt fehlerhaften Anwendungen scheitern zuverlässig unter den hier
geprüften Bedingungen. Offen bleibt die oben beschriebene, irreführende
Detailzusammenfassung bei einem FS-Fehler.

## Aussagegrenzen

Die Unabhängigkeit betrifft fachliche Sollwerte und das äußere Urteil, nicht ein
zweites Testframework: pytest bleibt Cubies vorgesehener Reporter-Unterbau.
Es wurden vier kleine, deterministische Anwendungen betrachtet, keine vollständige
Verifikation des Prüfkerns und keine Messung eines Produktivitätsvorteils.
Die Tests beanspruchen keine Installations-, Netzwerk- oder OS-Isolationsgarantie.
Sie verwenden die vorhandene Entwicklungsumgebung, `TempFS`, die Standardbibliothek
und das bereits installierte MyPy; zusätzliche Pakete oder Arena-Basen werden für
dieses Package nicht provisioniert. Der SIGKILL-Fall wird auf Nicht-POSIX-Systemen
übersprungen. Gleichzeitige Läufe derselben EBT-Instanz werden nicht untersucht.
