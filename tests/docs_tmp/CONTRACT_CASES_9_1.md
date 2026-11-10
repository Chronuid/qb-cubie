# EBT-Cases zu Gutachten 9.1: falsche Erfolge verhindern

> Phasenbezogener Entwicklungsnachweis. Zahlen, Rotphasen und offene Folgearbeiten
> beziehen sich auf den jeweils beschriebenen Stand. Einordnung und spätere
> Nachweise: [Übersicht](README.md). Befehle werden aus der Repositorywurzel ausgeführt.

Diese Cases spezifizieren den gewünschten Zustand zu Abschnitt 9.1 des
[Gutachtens](../../GUTACHTEN.md). Sie wurden zunächst gegen den unkorrigierten
Produktivcode entwickelt und danach zur Prüfung der Implementierung verwendet.
Die Tests werden regulär von pytest eingesammelt und haben keine
`xfail`-Markierungen. Das Ausgangsergebnis vor den Korrekturen bleibt unten
als historische Gegenprobe dokumentiert.

| Befund | Cases | Geprüfter Sollvertrag |
| --- | --- | --- |
| B1 | [test_ebt_contract_mutation.py](../tests_ebt/test_ebt_contract_mutation.py) | Vergleich, Diffs und aufgezeichneter Vertrag verwenden denselben vor Ausführung festgelegten Stand. |
| B2 | [test_ebt_phantom_calls.py](../tests_arena/test_ebt_phantom_calls.py) | Importhilfen dürfen relevante Laufzeitprüfungen auch bei ignorierten Rückgaben nicht verschwinden lassen. |
| B2, ergänzend | [test_phantom_import_policy.py](../tests_arena/test_phantom_import_policy.py) | Fehlendes pytest erlaubt nur Testdeklarationen beim Import; Ersatzabhängigkeiten werden ausdrücklich ausgewählt. |
| B3 | [test_pylint_analysis_integrity.py](../tests_linter/test_pylint_analysis_integrity.py) | Abgebrochene oder unvollständige Pylint-Analysen liefern keinen abgeschlossenen EBT-Erfolg. |
| B4 | [test_mypy_analysis_integrity.py](../tests_linter/test_mypy_analysis_integrity.py) | Windows-Diagnosen bleiben erhalten; ein Fehlerstatus ohne erkannte Fehlermeldung wird als Werkzeugfehler behandelt. |
| B5 | [test_human_reviewer_fresh_decision.py](../test_human_reviewer_fresh_decision.py) | Jeder Review braucht eine neue Entscheidung und einen eigenen Bericht. |

## Konkretisierte Verträge

**B1:** Das Target ersetzt eine Rückgabeerwartung, verändert ein mit der Eingabe
geteiltes verschachteltes Objekt, entfernt einen Post-Zustand oder ersetzt den
Ausnahmevertrag. Keine dieser Änderungen darf die bereits festgelegte Erwartung
für diesen Aufruf umschreiben. Positive und negative Zielmuster werden mit
`reporter=None`, `PytestReporter` und `JsonReporter` geprüft. Die fachliche
Entscheidung bleibt gleich; die dokumentierte Assertion-Politik der Reporter
bleibt bestehen. Identitätsprädikate sehen weiterhin das originale Ergebnis;
nicht kopierbare Erwartungen müssen vor Target-Aufruf und Reporting scheitern.
Ein ergänzender Fall prüft denselben Vertragsstand über mehrere Eingänge hinweg.

**B2:** Ein temporäres Modul importiert `pytest` auf Modulebene oder innerhalb
des Targets. `pytest.fail(...)` und ein nicht erfülltes `pytest.raises(...)`
müssen die Ausführung ablehnen, auch wenn danach ein erlaubter Rückgabewert
steht. Der Host-Aufruf beweist unabhängig, dass die Prüfung fehlschlägt.
PyVenv wird mit MSGspecCodec und PickleCodec geprüft. Der Kindprozess erhält
über eine explizite `.pth`-Datei dieselben installierten Abhängigkeiten wie der
Host; ein separater Prozess prüft deren Verfügbarkeit vorab. Ein unbenutzter
Import bleibt als positive Gegenprobe erlaubt. Die Basis wird lokal mit der
Standardbibliothek erzeugt; es werden keine Pakete installiert. Ergänzende Fälle
verwenden eine Basis ohne pytest: Testdeklarationen bleiben möglich, aber
Laufzeitaufrufe scheitern und die Importhilfe bleibt nicht im Modulcache.
Eine echte lokale Abhängigkeit bleibt ohne `decontams` unverändert; bei
ausdrücklicher Ersetzung werden Aufrufe abgelehnt.

**B3:** Signalabbrüche, Usage-Fehler und unbekannte Statusbits sind unabhängig
von stdout/stderr Werkzeugfehler. Das gilt auch mit leerem JSON oder bereits
ausgegebenen Teilbefunden. Zulässige Diagnosebits und Kombinationen erhalten
ihre strukturierten Meldungen. Eine saubere Analyse braucht gültiges JSON `[]`;
fehlende Ausgabe oder ein Diagnosestatus mit leerer Liste reichen nicht.
Ein negierter EBT-Vertrag darf einen Werkzeugabbruch ebenfalls nicht akzeptieren.
Zwei echte Python-Kindprozesse prüfen stillen Usage-Abbruch und SIGKILL; die
SIGKILL-Gegenprobe ist auf POSIX begrenzt. Ergänzende Fälle prüfen beschädigtes
JSON und gültiges JSON mit falscher Struktur, etwa `{}`, `null` oder `[{}]`.

**B4:** Laufwerkspräfixe mit beiden Pfadtrennern, Leerzeichen, UNC-, Unix- und
relative Pfade werden jeweils mit und ohne Spaltennummer geprüft. Ein echtes
Dateiargument vom Typ `Path` erreicht die öffentliche `MyPy.check()`-Methode;
die Werkzeugausgabe ist kontrolliert. Gemischte Unix-/Windows-Ausgabe muss
vollständig erhalten bleiben. Exitcode 1 ohne erkannte Fehlerdiagnose
(einschließlich bloßer Notes oder Zusammenfassungen) ist ein Werkzeugfehler.
Exitcode 0 ohne Diagnosen bleibt zulässig. Ergänzende Fälle verlangen auch bei
Status 0 und bei teilweise erkannten Diagnosen die Ablehnung unbekannter
Ausgabezeilen. Dies ist keine native Windows-Abnahme.

**B5:** Als konkretes Sollverhalten wird Schließen ohne Entscheidung auf
`ReviewData(passed=False, report={})` festgelegt. Alte Freigaben, alte Ablehnungen
und alte Berichte dürfen nicht übernommen werden. Neue ausdrückliche Pass-/Fail-
Entscheidungen ersetzen das vorige Ergebnis. Auch RBT mit Standardreporter und
ohne Reporter muss die neue Ablehnung erkennen. Fenster und Widgets sind
Testdoubles; `review()`, GUI-Lebenszyklus und Entscheidungscallbacks laufen real.
Die Tests benötigen weder Displayserver noch manuelle Eingabe.

## Ausführung und Ausgangsergebnis

```bash
.venv/bin/python -m pytest -q \
  tests/tests_ebt/test_ebt_contract_mutation.py \
  tests/tests_arena/test_ebt_phantom_calls.py \
  tests/tests_arena/test_phantom_import_policy.py \
  tests/tests_linter/test_pylint_analysis_integrity.py \
  tests/tests_linter/test_mypy_analysis_integrity.py \
  tests/test_human_reviewer_fresh_decision.py
```

Der Befehl enthält inzwischen 17 ergänzende Cases, insgesamt 101.
Die ursprünglichen 84 Cases ergaben im lokalen Linux-Lauf am 10. November 2026
vor Implementierungskorrekturen:

| Befund | Fehlgeschlagen | Bestanden | Gesamt |
| --- | ---: | ---: | ---: |
| B1 | 9 | 2 | 11 |
| B2 | 6 | 6 | 12 |
| B3 | 21 | 13 | 34 |
| B4 | 12 | 7 | 19 |
| B5 | 4 | 4 | 8 |
| **Gesamt** | **52** | **32** | **84** |

Die fehlgeschlagenen Tests treffen die spezifizierten Verhaltenslücken;
der Lauf enthält keine Setup- oder Sammlungsfehler. Die bereits bestehenden
Tests aus `test_ebt_run_isolation.py`, `test_mypy_process_status.py`,
`tests/test_headless_reviewer.py` und `test_rbt_reporter.py` bestehen separat:
**94 passed**. Ruff akzeptiert die fünf neuen Python-Testdateien.

## Abnahme nach Produktivkorrekturen

Nach Umsetzung von B1–B5 bestehen alle **101 Cases**, einschließlich der
17 ergänzenden Prüfungen für laufweit feste Erwartungen, Importhilfen und
unvollständige Analyseausgaben. Keine Regression ist als `xfail` markiert.

Der vollständige lokale Linux-Lauf mit `.venv/bin/python -m pytest -q` ergibt:

```text
1269 passed, 12 skipped, 6 warnings in 257.06s (0:04:17)
```

Die regulären Prüfungen von Funktionsgröße, Docstrings, Ruff, Pylint und MyPy
sind darin enthalten. Die sechs neuen Python-Testdateien bestehen zusätzlich
Ruff; Lint-Prüfungen und README-Beispiele ergeben separat **12 passed**.
Übersprungene Tests werden nicht als bestanden gewertet. Windows-Pfade werden
mit kontrollierter Werkzeugausgabe geprüft, GUI-Interaktionen mit Testdoubles;
eine native Windows- oder manuelle GUI-Abnahme ist damit nicht behauptet.
