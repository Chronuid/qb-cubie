# Ergänzung: Wahrheitsgehalt der Dateisystemberichte

**Fortschreibung:** Der unten dokumentierte Fehlerstand wurde anschließend im
Produktionscode korrigiert. Umsetzung und aktuelle Nachweise stehen im Abschnitt
[Produktionskorrektur](#produktionskorrektur). Die ursprünglichen roten Protokolle
bleiben als Nachweis erhalten.

**Datum:** 10. November 2026. **Umgebung:** unverändert Cubie `0.0.3`, Python
`3.13.12`, pytest `9.2.0`, Linux, auf Basis von Commit `01cb8bd`.
**Anlass:** Der im [ersten Bericht](TESTBERICHT.md) beobachtete Widerspruch zwischen
`FS: Mismatch` und `0 Modified` soll durch zusätzliche EBT-Cases eingegrenzt werden.

Die neuen Fälle stehen in [test_fs_reporting.py](test_fs_reporting.py). Sie
formulierten zunächst das gewünschte Verhalten, ohne den bekannten Reporterfehler
zu reparieren oder mit `xfail` auszublenden. **Das Package war mit diesen neuen
Anforderungen zunächst rot.** Die früheren grünen Ergebnisse
im ersten Bericht bleiben historische Ergebnisse vor dieser Ergänzung.

## Mit den Fällen festgelegte Aussagen

„Modified“ bedeutet eine Inhaltsabweichung gegenüber `post.fs` an einem auf beiden
Seiten vorhandenen Dateipfad. Es bezeichnet keine Schreiboperation des Targets.
Eine fachlich richtige Transformation aus einem anderen Vorzustand und das erneute
Schreiben identischer Bytes sind deshalb keine Abweichung.

Im gemeinsamen FS-Bericht zählen unterschiedliche relative Workspace-Dateipfade.
Fehlende Dateien, zusätzliche Dateien und inhaltlich veränderte Dateien bleiben
getrennte Kategorien. Eine Umbenennung ohne Inhaltsänderung ist ein fehlender alter
und ein zusätzlicher neuer Pfad; die Fälle verlangen keine Erkennung von Renames.
Überlappende Vergleichsbereiche dürfen denselben Dateipfad nicht doppelt zählen.
Die Liste nennt Workspace-Pfade einschließlich ihres Vergleichsbereichs, nicht
die Namen der Host-Referenzdateien. Dateien außerhalb eines ausdrücklich begrenzten
Mappings gehören nicht in dessen Abweichungsbericht.

Für den gemeinsamen FS-Abschnitt fordern diese Tests eine Gesamtzusammenfassung.
Eine Begrenzung durch `max_diff_items` kürzt nur die Pfadliste. Die Gesamtzahlen
bleiben vollständig, und die Anzahl ausgelassener Einträge muss stimmen. Dies
ist die mit den neuen Fällen festgelegte Sollsemantik, insbesondere für mehrere
und überlappende Mappings.

Ein nicht vergleichbarer Pfad, etwa eine fehlende einzeln gemappte Datei oder
ein Verzeichnis anstelle einer Datei, muss mit Grund und betroffenem Zielpfad
erklärt werden. Eine reine Null-Zusammenfassung ist dafür keine ausreichende
Diagnose. Das ist von einem regulären rekursiven Diff mit bekannten Dateilisten
zu unterscheiden.

## Versuchsraum

Die folgende Matrix enthält ausdrücklich vorgegebene Sollwerte. Die Zahlen stehen
für **fehlend / zusätzlich / inhaltlich verändert**, relativ zur Nachbedingung.

| Fall | Erwartete Aussage |
| --- | --- |
| Identischer Inhalt | Match, 0 / 0 / 0 |
| Identische Bytes erneut geschrieben | Match, 0 / 0 / 0 |
| Vorzustand gezielt in den richtigen Nachzustand transformiert | Match, 0 / 0 / 0 |
| Textinhalt bei gleicher Dateigröße verändert | Mismatch, 0 / 0 / 1 |
| Leere Datei erhält falschen Inhalt | Mismatch, 0 / 0 / 1 |
| Erwarteter Inhalt wird durch leere Datei ersetzt | Mismatch, 0 / 0 / 1 |
| Binärinhalt bei gleicher Dateigröße verändert | Mismatch, 0 / 0 / 1 |
| Datei fehlt im gesamten Workspace-Vergleich | Mismatch, 1 / 0 / 0 |
| Zusätzliche Debugdatei | Mismatch, 0 / 1 / 0 |
| Je eine fehlende, zusätzliche und veränderte Datei plus unveränderte Kontroll-Datei | Mismatch, 1 / 1 / 1 |
| Veränderung in einem verschachtelten gemappten Verzeichnis | Mismatch, 0 / 0 / 1; vollständiger Workspace-Pfad |
| Zwei veränderte `settings.json` in getrennten Mappings | Mismatch, 0 / 0 / 2; beide Pfade unterscheidbar |
| Gleicher Inhalt unter neuem Dateinamen | Mismatch, 1 / 1 / 0 |
| Explizit gemappte Einzeldatei verändert | Mismatch, 0 / 0 / 1 |
| Zusätzliche Datei außerhalb des Einzeldatei-Mappings | Match, 0 / 0 / 0 |
| Dieselbe Veränderung über `.` und `out` erfasst | Mismatch, 0 / 0 / 1; einmal zählen und auflisten |
| Sechs Abweichungen, Pfadliste auf zwei Einträge begrenzt | Mismatch, 2 / 2 / 2; zwei Pfade und vier ausgelassene Einträge |

Diese 17 Szenarien werden jeweils auf drei Ebenen geprüft:

1. EBT-Entscheidung und strukturierte Diff-Kategorien samt betroffenen Pfaden.
2. Zahlen der menschenlesbaren Zusammenfassung.
3. Aufgelistete Dateipfade und gegebenenfalls korrekte Kürzung.

Vier ergänzende Fälle prüfen:

- Eine Einzeldatei wird mit einer anders benannten Host-Referenz verglichen.
  Die Meldung muss `out/report.csv` nennen, nicht `golden-result.dat`.
- Nur die Rückgabe ist falsch. Der Bericht muss trotzdem `FS: Match` anzeigen
  und darf keine FS-Abweichungen erfinden.
- Eine einzeln gemappte Zieldatei fehlt: Fehlergrund und Zielpfad müssen sichtbar sein.
- Anstelle der erwarteten Datei liegt ein Verzeichnis: Auch dieser Vergleichsfehler
  muss erklärt werden.

Das ergibt **55 zusätzliche Tests**.

## Unabhängige Beobachtung

Das kleine Target schreibt die vorgegebenen Dateien und importiert Cubie nicht.
Für jedes der 17 Szenarien wird es zuerst unmittelbar in einem temporären
Verzeichnis ausgeführt. pytest prüft die tatsächlich geschriebenen Dateibytes
und die Rückgabe. Anschließend läuft dasselbe Target in `TempFS` gegen eine
separat angelegte Referenz.

Die erwarteten Kategorien und Pfade stehen als Literale in der Szenariotabelle.
Die Kontrolle der öffentlichen `RunTrace` dekodiert lediglich die nach
Vergleichspfad gegliederten Diff-Einträge; sie ruft keine privaten Cubie-Vergleiche
auf. Reporterzahlen und Pfadlisten werden in getrennten Tests geprüft, damit
eine falsche Zahl nicht eine weitere falsche Pfadliste verdeckt.

Ein anfänglicher Fehler im Testaufbau behandelte `trace.diffs=None` bei einem
korrekten Match nicht. Dieser wurde korrigiert; die abschließenden Ergebnisse
enthalten diese anfänglichen Testfehler nicht.

## Ergebnisse vor der Produktionskorrektur

Der gezielte Lauf ergibt **26 bestanden, 29 fehlgeschlagen**:

| Prüfung | Bestanden | Fehlgeschlagen |
| --- | ---: | ---: |
| Entscheidung und strukturierte Diffs für die 17 Szenarien | 17 | 0 |
| Zusammenfassungszahlen | 4 | 13 |
| Pfadlisten und Kürzung | 4 | 13 |
| Workspace-Pfad statt anders benannter Referenzdatei | 0 | 1 |
| FS-Match bei falscher Rückgabe | 1 | 0 |
| Sichtbare Erklärung für nicht vergleichbare Pfade | 0 | 2 |
| **Summe** | **26** | **29** |

Dieser Lauf dauerte **13,16 Sekunden**. Das gesamte Nutzer-Package ergibt danach
**85 bestanden, 29 fehlgeschlagen** in **19,22 Sekunden**. Damit bestehen alle
bisherigen 59 Tests weiterhin; die 29 Fehlschläge stammen ausschließlich aus den
neuen Reporteranforderungen. Die erzeugten JUnit-Dateien bestätigen diese
Zuordnung und enthalten weder Ausführungsfehler noch übersprungene Tests.
Ruff meldet **All checks passed!**

Der Befund ist damit genauer eingegrenzt: **Die beobachteten EBT-Entscheidungen
und strukturierten Dateidiffs sind korrekt. Die menschenlesbare FS-Diagnose ist
fehlerhaft.** Bei allen 13 Szenarien mit regulären Abweichungen meldet sie
`0 Missing | 0 Unexpected | 0 Modified` und liefert keine Dateiliste. Auch die
beiden strukturiert vorhandenen Vergleichsfehler werden nicht erklärt.

Die Nullzahlen sind also kein besonderer Randfall einer einzelnen CSV-Datei.
Sie treten ebenso bei rekursiven Verzeichnisvergleichen, mehreren Mappings,
Binärdateien und gemischten Abweichungen auf. Die Prüfungen für überlappende
Mappings und gekürzte Listen waren ebenfalls rot. Solange der Reporter
überhaupt keine Einträge ausgibt, ist damit noch nicht nachgewiesen, wie er nach
einer Korrektur mit Duplikaten oder Kürzung umgehen wird; die Sollanforderungen
sind dafür jetzt als Regressionen vorhanden.

## Nachweise und Wiederholung

Vom Repository-Wurzelverzeichnis:

```bash
.venv/bin/python -m pytest -q tests/tests_user_workflows/test_fs_reporting.py --tb=short
.venv/bin/python -m pytest -q tests/tests_user_workflows --tb=line
.venv/bin/python -m ruff check tests/tests_user_workflows
```

Die ersten beiden Befehle lieferten vor der Korrektur Exitcode `1`, weil die
neuen Anforderungen noch nicht erfüllt waren. Die Tests verlangten die Korrektur
der fehlerhaften Aussagen und schlugen bis dahin fehl.

Die Ausführungsprotokolle liegen unter:

- [Neue FS-Fälle, einschließlich einzelner Fehlerberichte](results/fs-reporting-pytest.txt)
- [Gesamtes Nutzer-Package nach der Ergänzung](results/fs-reporting-package-pytest.txt)
- [Ruff für das Nutzer-Package](results/fs-reporting-ruff.txt)
- [Unabhängige Prüfung der JUnit-Zahlen und Fehlerzuordnung](results/fs-reporting-junit-check.txt)

Der vollständige Projektlauf wurde bei der ursprünglichen Testergänzung nicht wiederholt.
Die im ersten Bericht genannten Gesamtsuite-Zahlen beziehen sich auf den Stand
vor diesen zusätzlichen roten Regressionen. Dabei wurden weder Produktivcode noch
die bisherigen Akzeptanzverträge geändert.

## Produktionskorrektur

Der [Pytest-Reporter](../../src/cubie/reporter.py) verarbeitet jetzt die tatsächlich
gelieferten, nach Vergleichspfad gegliederten FS-Diffs. Er ergänzt die jeweiligen
Mapping-Pfade, normalisiert sie lexikalisch und führt sie je Kategorie in einer
sortierten Menge zusammen. Damit stimmen Zähler und Dateiliste überein;
überlappende Mappings erzeugen keine doppelten Einträge. Die Kürzung erfolgt erst
nach der Aggregation, sodass Gesamtzahlen und Restanzahl vollständig bleiben.
Strukturierte Vergleichsfehler erscheinen separat mit Zielpfad und Grund, auch
bei Verbosity `0` und einer auf null Einträge begrenzten Dateiliste. Liegen nur
Vergleichsfehler vor, wird keine Null-Zusammenfassung erzeugt.

Bei Einzeldateien bezeichnet der strukturierte Diff jetzt `"."` relativ zum
Mapping, statt den Namen der Host-Referenz zu verwenden. Diese kleine Anpassung
in [EBT](../../src/cubie/ebt.py) macht die Ausgabe eindeutig: Eine Einzeldatei und
ein Verzeichnis mit einer gleichnamigen enthaltenen Datei bleiben unterscheidbar.
Der Reporter benötigt keine erneuten Dateisystemzugriffe und funktioniert auch
dann, wenn Workspace und Referenz beim späteren Berichten bereits entfernt sind.
Die Änderung der Einzeldatei-Diffs ist in der
[Vertragssemantik](../../docs/GUIDE_Contract-Semantics.md#dateisystem-und-arenen)
dokumentiert; Verbraucher der strukturierten Diffs müssen den früheren
Host-Basename durch die relative Selbstreferenz `"."` ersetzen.

Die bisherigen 55 FS-Regressionen bleiben in ihren Anforderungen unverändert.
Hinzu kommen neun Fälle für verzögerte Berichte nach gelöschter Referenz,
gemischte Vergleichsfehler und Inhaltsabweichungen bei verschiedenen Ausgabegrenzen
sowie Mapping-Namen `error`, `missing` und `modified`. Diese Namen dürfen nicht
mit den Feldern des Diff-Datensatzes verwechselt werden.

Im ursprünglichen CSV-Beispiel lautet die Ausgabe jetzt:

```text
    - FS: Mismatch
      Details: -0 Missing | +0 Unexpected | ~1 Modified
        ~ paid.csv
```

Der direkte Nutzerbeispiel-Lauf bleibt wie vorgesehen bei vier fehlerhaften und
einem korrekten Target rot; seine FS-Diagnose nennt nun die richtige Anzahl und
Datei ([korrigierte Fehlerberichte](results/production-acceptance-pytest.txt)).

Das gesamte Nutzer-Package besteht mit **123 Tests** in **21,52 Sekunden**,
einschließlich aller **64 FS-Fälle** und des unabhängigen pytest-Kindprozesses
([Einzelfälle](results/production-package-pytest.txt)). Die vorherigen 29 roten
Reporterregressionen sind damit behoben.

Ruff findet in den beiden berührten Produktionsdateien dieselben 46 bereits
vorhandenen Befunde wie im Git-Ausgangsstand (31 in EBT, 15 im Reporter). Der
Vergleich nach Regel und Meldung zeigt keine zusätzlichen Befunde; bestehende
Stil- und Typannotierungsbefunde wurden in dieser fachlichen Korrektur nicht
umgeschrieben.

Der abschließende vollständige Projektlauf besteht mit **810 Tests**,
**11 übersprungenen Tests** und **6 bestehenden Warnungen** in **191,66 Sekunden**,
Exitcode `0` ([Gesamtprotokoll](results/production-full-pytest.txt)). Das Nutzer-Package
ist bei Ruff vollständig grün ([Protokoll](results/production-ruff-tests.txt)); der
[Produktionsvergleich](results/production-ruff-baseline.txt) dokumentiert die
unveränderten Bestandsbefunde. Eine unabhängige Auswertung der erzeugten
JUnit-Dateien bestätigt alle Zahlen sowie den Erfolg sämtlicher 64 FS-Fälle
([JUnit-Prüfung](results/production-junit-check.txt)).
