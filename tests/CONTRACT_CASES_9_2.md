# EBT-Cases zu Gutachten 9.2: Umgebungsausführung und Abnahme

Diese Cases konkretisieren den Sollzustand aus Abschnitt 9.2 des
[Gutachtens](../GUTACHTEN.md). Sie wurden zunächst gegen den unkorrigierten
Produktivcode entwickelt und anschließend zur Prüfung der Korrekturen verwendet.
Die Repository-Cases werden regulär eingesammelt und enthalten kein `xfail`.
Die roten Ausgangsergebnisse bleiben unten als historische Gegenprobe erhalten;
die aktuelle Implementierung und Abnahme stehen im letzten Abschnitt.

## Zuordnung der sechs Kritikpunkte

| Punkt | Cases / Nachweis | Sollvertrag |
| --- | --- | --- |
| 9.2.1 / B6 | [test_core_without_tk.py](test_core_without_tk.py), gemeinsames [Prozessszenario](wheel/tk_contract.py) | Paketimport, EBT, TempFS und Headless-RBT funktionieren ohne Tk. Erst ein grafischer Review benötigt Tk und meldet bei Fehlen einen verständlichen Installationshinweis. |
| 9.2.2 / B7 | [test_ebt_console_environment.py](tests_arena/test_ebt_console_environment.py) | Ein kopiertes Konsolenskript verwendet Interpreter und Abhängigkeiten des Klons; alternativ wird eine nicht unterstützte Basis vor dem Target-Aufruf ausdrücklich abgelehnt. |
| 9.2.3 | [test_ebt_fresh_file_comparison.py](tests_ebt/test_ebt_fresh_file_comparison.py) | Erneute Datei-, Verzeichnis- und Arena-Vergleiche lesen aktuelle Inhalte, auch bei gleicher Größe und wiederhergestellter mtime. |
| 9.2.4 | [test_default_collection_contract.py](test_default_collection_contract.py) | Alle 14 historischen Fälle gehören zur Standardsammlung. Ihre explizite Ausführung und Ergebnisse stehen unten. |
| 9.2.5 | Ergänzungen in [smoke_installed.py](wheel/smoke_installed.py); bestehende [MyPy-Cases](tests_linter/test_mypy_analysis_integrity.py) und [GUI-Cases](test_human_reviewer_fresh_decision.py) | Die Wheel-Matrix prüft echte absolute Dateipfade sowie fehlendes Tk. Fensterabbruch verwirft alte Freigaben und unbestätigte Berichte. |
| 9.2.6 | Dokumentationsabgleich unten mit ausführbaren Vertragsnachweisen | Historische Fehlerbehauptungen werden vom gegenwärtigen Verhalten getrennt; offene B6-/B7-/Cache-Befunde werden nicht vorzeitig als behoben bezeichnet. |

## Konkretisierte Verträge

**B6 – 12 Cases:** Jeder Fall startet einen neuen Interpreter mit `-I` außerhalb
des Projektverzeichnisses. Ein Importfinder verweigert wahlweise `tkinter` oder
die native Erweiterung `_tkinter`. Zwei positive Kontrollfälle beweisen, dass
dieser Schutz tatsächlich greift. Die weiteren Fälle verlangen Kernimport,
positive EBT- und TempFS-Ausführung, explizite positive und negative
Headless-Reviews sowie einen `RuntimeError` mit Tk- und Installationshinweis
beim grafischen Review. Der Import und die Konstruktion des grafischen
Reviewers selbst müssen möglich bleiben. Kernfunktionen dürfen Tk gar nicht
laden. Ein Displayserver oder eine Betriebssystemänderung ist nicht nötig.
Die Wheel-Tests verwenden dasselbe Prozessszenario ohne eingeschobenen
Repository-Quellpfad; das vorhandene Wheel-Skript kopiert die Hilfsdatei mit.

**B7 – ursprünglich 6, jetzt 14 Cases:** Eine lokale Standardbibliotheks-Venv enthält eine kleine
Abhängigkeit und ein Konsolenskript. Ohne Leerzeichen im Interpreterpfad nutzt
es eine absolute Shebang; mit Leerzeichen einen Shell-Launcher mit absolutem
Interpreterpfad. Eine unabhängige Ausführung bestätigt zunächst die Basis.
Das Target verändert ausschließlich die kopierte Abhängigkeit auf den Wert
`clone` und startet das Skript über PATH oder seinen absoluten kopierten Pfad.
`sys.prefix`, die tatsächlich importierte Abhängigkeit, der ausgewählte
Skriptpfad und `VIRTUAL_ENV` müssen zum Klon gehören. Ein korrektes
`VIRTUAL_ENV` allein reicht ausdrücklich nicht.

Alternativ darf die Implementierung solche Basen mit einem ausdrücklichen
Hinweis auf nicht unterstützte Launcher ablehnen. Diese Ablehnung muss vor
Target-Seiteneffekten erfolgen, ohne abgeschlossenen Trace oder Reporter-Aufruf.
Die Workspace-Bereinigung und unveränderte Basis werden auch bei Fehlern
kontrolliert. Je Launcher-Variante bleibt ein positiver `python -m`-Fall mit
einer Basis ohne das problematische Konsolenskript erhalten. Die Cases
installieren keine Pakete und benötigen kein Netzwerk. Die Launcher-Proben
sind POSIX-spezifisch und werden unter Windows ausdrücklich übersprungen;
eine native Windows-Launcher-Abnahme bleibt offen.

Die gewählte Implementierung unterstützt die beiden Standard-POSIX-Launcher.
Die sechs ursprünglichen Fälle verlangen deshalb inzwischen deren erfolgreiche
Ausführung und erlauben keine pauschale Ablehnung mehr. Vier ergänzende Fälle
prüfen die frühe Ablehnung zusätzlicher `.exe`-Launcher und eigener
basisgebundener Shell-Skripte. Vier weitere Fälle prüfen interne und externe
Skriptlinks: Interne Links samt Python-Einstiegsskript laufen im Klon, externe
Links werden vor dem Target-Aufruf abgelehnt. Jede dieser Ergänzungen läuft mit
und ohne Leerzeichen im Basispfad.

**Dateivergleich – 12 Cases:** Eine kleine injizierte Arena hält ihre Pfade
über zwei EBT-Läufe stabil. Damit wird die im Gutachten genannte Lücke real
über `run()` geprüft, ohne einem eingebauten TempFS-Lauf wiederverwendete
Pfade zu unterstellen. Der erste Lauf wärmt den Vergleich mit `good` auf.
Danach wird entweder die Ergebnis- oder Referenzdatei durch `evil` ersetzt,
mit identischer Länge und exakt wiederhergestellter mtime. Unabhängige
Byte-Lesezugriffe belegen die Abweichung. Der zweite Trace muss ablehnen
und den geänderten relativen Pfad melden; der erste Trace bleibt positiv.
Sechs Gegenproben mit weiterhin gleichen Bytes müssen bestehen. Die drei
Vergleichswege sind gemappte Einzeldatei, gemapptes Verzeichnis und Arena.
Der `filecmp`-Cache wird nur vor und nach dem jeweiligen Test geleert,
ausdrücklich nicht zwischen dessen beiden Läufen.

**Standardsammlung – 3 Cases:** Zwei getrennte `pytest --collect-only`-Läufe
ermitteln die Standardsammlung und die explizite Sammlung der historischen
Dateien. EBT erwartet je Datei keine fehlenden Node-IDs; zusätzlich müssen
weiterhin 7, 3 und 4 Fälle existieren. Weder ein Sammlungsfehler noch das
Entfernen von Tests kann so als Erfolg erscheinen. Der Abgleich akzeptiert
sowohl eine spätere Konfigurationsänderung als auch die üblichen Umbenennungen
zu `test_mp_hypothesis.py`, `test_mypy.py` und `test_linter.py`.
Die Prüfung sammelt Tests, sie behauptet keinen erfolgreichen Lauf dieser Fälle.

**Plattformabnahme:** Die Wheel-Suite enthält zusätzlich 12 Tk-Prozessfälle
und zwei MyPy-Dateifälle. MyPy erhält einen echten absoluten `Path` mit
Leerzeichen, einmal mit Typfehler und einmal mit sauberem Inhalt. Im
Linterprofil müssen Fehlercode, Schweregrad, Zeile und vollständiger Pfad
erhalten bleiben; im Kernprofil wird stattdessen der bekannte Hinweis auf das
fehlende Linter-Extra verlangt. Diese Fälle werden durch die vorhandene
Wheel-Matrix auch unter Windows ausgeführt, sobald die CI läuft. Die 23
vorhandenen MyPy-Parserfälle mit kontrollierter Werkzeugausgabe und die acht
GUI-Abbruch-/Entscheidungsfälle werden ergänzend wiederverwendet. Die GUI-Cases
verwenden Fensterdoubles und benötigen keine manuelle Eingabe.

## Ausgangsergebnis am 10. November 2026

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/test_core_without_tk.py \
  tests/tests_arena/test_ebt_console_environment.py \
  tests/tests_ebt/test_ebt_fresh_file_comparison.py \
  tests/test_default_collection_contract.py \
  tests/test_human_reviewer_fresh_decision.py \
  tests/tests_linter/test_mypy_analysis_integrity.py
```

| Gruppe | Fehlgeschlagen | Bestanden | Gesamt |
| --- | ---: | ---: | ---: |
| B6: fehlendes Tk einschließlich Schutzkontrollen | 10 | 2 | 12 |
| B7: Konsolenskripte und Modulaufrufe | 4 | 2 | 6 |
| Frische Dateivergleiche | 6 | 6 | 12 |
| Standardsammlung | 3 | 0 | 3 |
| Vorhandene GUI-Entscheidungen | 0 | 8 | 8 |
| Vorhandene MyPy-Analyseintegrität | 0 | 23 | 23 |
| **Gesamt** | **23** | **41** | **64** |

Die **33 neuen Repository-Cases** ergeben damit **23 failed, 10 passed**.
Die Fehler reproduzieren die beschriebenen offenen Verhaltenslücken; es gab
keine Setup- oder Sammlungsfehler. B6 verhindert derzeit bereits den Import
im Kindprozess, sodass dessen spätere EBT-/GUI-Schritte noch nicht erreicht
werden. Ruff akzeptiert alle sechs neuen beziehungsweise geänderten Python-Dateien.

Die zwei neuen MyPy-Dateifälle wurden separat im lokalen Quellbaum ausgeführt:

```bash
QB_CUBIE_WHEEL_PROFILE=linters .venv/bin/python -m pytest -q \
  tests/wheel/smoke_installed.py -k mypy_with_native_absolute_file_path
```

Ergebnis: **2 passed**. Das ist ein Linux-Test der neuen Fälle mit vorhandenen
Linter-Abhängigkeiten. Eine neue Distribution wurde für diesen Testschritt
nicht gebaut oder installiert. Ein nativer Windows-Lauf und eine erfolgreiche
Wheel-Abnahme werden hier nicht behauptet.

## Explizite Auswertung der 14 historischen Tests vor Korrekturen

Der folgende historische Befehl verwendet die damaligen Dateinamen.
Die aktuellen Namen stehen im Abnahmebefehl am Ende dieses Dokuments.

```bash
.venv/bin/python -m pytest -q --tb=short \
  tests/tests_multiprocessors/mp_hypothesis.py \
  tests/tests_linter/tests_mypy.py \
  tests/tests_linter/tests_linter.py
```

Ergebnis unter lokalem Linux: **3 failed, 11 passed in 85.53s**.
Explizit eingesammelt wurden tatsächlich 14 Fälle. Alle sieben Linterfälle
und die ersten vier Inspector-Fälle bestehen. Die drei Parameter von
`test_state_inspector_scalable_matrix` (`2-5`, `10-20`, `50-100`) scheitern
mit `hypothesis.errors.DeadlineExceeded`: Die beobachteten Beispiele benötigen
etwa 331–351 ms bei einer Frist von 200 ms. Das ist ein Testzeitbudgetbefund
bei echter Multiprocessing-Ausführung, kein Nachweis eines falschen
fachlichen Ergebnisses. Ein angepasstes Budget beziehungsweise ein gezielt
konfigurierter Prozess-Test muss separat bewertet werden. In diesem Schritt
werden weder die Frist erhöht noch die Fälle als erfolgreich verbucht.

Das Einbinden allein genügt für die Abnahme nicht: Auch die dann regulär
laufenden generativen Fälle müssen mit einem begründeten Zeitbudget bestehen.

## Abgleich historischer Dokumentationsaussagen vor Korrekturen

| Fundstelle | Abweichung / aktueller Stand | Ausführbarer Nachweis und nächster Dokumentationsschritt |
| --- | --- | --- |
| [EBT-Entwicklerübersicht](../docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) | Der Absatz „Bekannte Fehler“ behauptet weiterhin ungeprüfte `None`-Rückgaben, akzeptierte leere Zustandslisten und veränderliche alte Traces. Diese Behauptungen sind überholt. | [Explizite None-Rückgaben](tests_ebt/test_ebt_returns.py), [Rückgabeverträge](tests_ebt/test_ebt_contract_returns.py), [Zustandsvalidierung](tests_ebt/test_ebt_state_validation.py), [Laufisolation](tests_ebt/test_ebt_run_isolation.py); Absatz an die zentrale Semantikreferenz anpassen. |
| [Linter-Entwicklerhandbuch](../docs/dev/DEV-GUIDE_2-5_Linter.md) | Der Schlussabsatz behauptet weiterhin, MyPy könne Prozessabbrüche als leere Liste behandeln. | [MyPy-Prozessstatus](tests_linter/test_mypy_process_status.py) und [Analyseintegrität](tests_linter/test_mypy_analysis_integrity.py); historischen Befund von der korrigierten Status-/Parserprüfung trennen. |
| [README: bekannte Einschränkungen](../README.md#bekannte-einschränkungen) | Tk-Paketimport, kopierte Skripte, Cache und 14 fehlende Standardfälle sind weiterhin zutreffend als offen beschrieben. | Neue Cases dieses Dokuments; Aussagen erst nach Produktivkorrektur beziehungsweise Sammlung und Auswertung aktualisieren. |
| [RBT-Nutzungsmuster](../docs/GUIDE_RBT-Usage-Pattern.md) | Schließen ohne Entscheidung ergibt eine neue Ablehnung mit leerem Bericht. Die Aussage entspricht der Korrektur aus 9.1. | Acht [GUI-Cases](test_human_reviewer_fresh_decision.py) bestehen; als aktuelle Semantik beibehalten. |

Dieser historische Abgleich dokumentiert die konkreten Korrekturstellen für
9.2.6; er ersetzt keine umfassende Prüfung sämtlicher Dokumente. Die beiden
überholten Handbuchabsätze wurden inzwischen berichtigt. README, Arena- und
RBT-Handbuch sowie die Semantikreferenz beschreiben die aktuelle Implementierung.
Das Gutachten erhält einen Nachtrag; seine Untersuchungsbefunde bleiben erhalten.

Die fünf verlinkten Dateien für None-Rückgaben, weitere Rückgabeverträge,
Zustandsvalidierung, Laufisolation und MyPy-Prozessstatus wurden zusätzlich
ausgeführt: **185 passed**. Die vollständige Repository-Suite wurde in diesem
vorbereitenden Testschritt nicht erneut ausgeführt.

## Implementierung und Abnahme

- Tk wird durch `_load_tk()` erst bei GUI-Nutzung importiert. GUI-Doubles
  ersetzen diese Ladefunktion; auch die vorhandenen GUI-Tests benötigen daher
  keine installierte Tk-Bibliothek. Der Installationsfehler bleibt von einem
  tatsächlich fehlenden Display bei vorhandenem Tk unterscheidbar.
- Der gemeinsame Dateivergleich liest bei jedem Aufruf neue Byteblöcke von
  maximal 128 KiB je Datei. Er speichert keine Stat-Signaturen oder Ergebnisse.
- PyVenv passt auf die Basis verweisende Python-Shebangs und übliche
  Shell-Trampoline im Klon an. Nicht unterstützte basisgebundene Launcher,
  zusätzliche `.exe`-Dateien und externe Skriptlinks werden abgelehnt. Die
  Unterstützung umfasst keine beliebigen eingebetteten Paketpfade und keine
  interaktiven Aktivierungsskripte; siehe [Arena-Handbuch](../docs/GUIDE_Arena-Management.md#pyvenv-kopierte-virtuelle-umgebung).
- Die drei historischen Dateien heißen jetzt `test_mp_hypothesis.py`,
  `test_mypy.py` und `test_linter.py`. Die sieben Inspector-/Multiprocessing-
  und sieben Linterfälle werden regulär eingesammelt. Das lokale
  `@settings(max_examples=100, deadline=None)` gilt ausschließlich für die drei
  Parameter der echten Prozessmatrix: Diese prüfen Korrektheit einschließlich
  Prozessstart, keinen 200-ms-Leistungsvertrag. Andere Hypothesis-Tests behalten
  ihre Einstellungen; globale Profilregistrierungen beim Modulimport entfallen.
  Die Prozessmatrix begrenzt pro Beispiel zusätzlich die Zahl der Zustände auf
  fünf sowie FS-/Kwargs-Felder je Zustand auf drei. Die rekursiven Breiten
  2/10/50 und Blattbudgets 5/20/100 bleiben erhalten; so werden unabhängige
  Dimensionen nicht unkontrolliert miteinander multipliziert. Der CI-Job
  besitzt weiterhin sein äußeres Zeitlimit.
- Die Wheel-Matrix enthält Tk-Ausfallfälle und echte absolute Dateipfade.
  Die gemeinsame Tk-Hilfsdatei wird auch in die Quelldistribution aufgenommen.

Der gezielte Abnahmebefehl lautet:

```bash
.venv/bin/python -m pytest -q \
  tests/test_core_without_tk.py \
  tests/tests_arena/test_ebt_console_environment.py \
  tests/tests_ebt/test_ebt_fresh_file_comparison.py \
  tests/test_default_collection_contract.py \
  tests/test_human_reviewer_fresh_decision.py \
  tests/tests_linter/test_mypy_analysis_integrity.py \
  tests/tests_multiprocessors/test_mp_hypothesis.py \
  tests/tests_linter/test_mypy.py \
  tests/tests_linter/test_linter.py
```

Die sieben Inspector-/Multiprocessing-Fälle bestehen separat mit
**7 passed in 66.11s**. Die drei Prozessmatrix-Parameter benötigen dabei
11.11 s, 23.27 s und 27.61 s für jeweils bis zu 100 generierte Beispiele.
Dieser Lauf hat keine Hypothesis-Warnungen und keine übersprungenen Fälle.
Die ergänzten Launcher-Prüfungen zusammen mit Styleguide und Lint ergeben
**35 passed, 1 skipped**; der Skip betrifft die bereits zuvor ausgesetzte
Modulgrößenregel.

Die Distribution wurde mit `uv build --python .venv/bin/python` als
Quelldistribution und daraus als Wheel gebaut. Die Tk-Hilfsdatei ist in der
Quelldistribution enthalten. `scripts/check_wheel.py` installiert das Wheel
außerhalb des Checkouts und ergibt unter Linux mit Python 3.13:

- Kernprofil: **22 passed**, einschließlich der Tk-Ausfallfälle.
- Linterprofil: **22 passed**, einschließlich echter absoluter MyPy-Dateipfade.
- Kernimport und EBT vor Installation von pytest sowie `pip check` sind erfolgreich.

Eine native Windows- oder macOS-Abnahme sowie manuelle GUI-Interaktion sind
damit nicht behauptet; dafür bleiben die CI-Matrix beziehungsweise ein eigener
manueller Lauf zuständig.

Die vollständige lokale Linux-Suite mit `.venv/bin/python -m pytest -q`
ergibt nach allen Korrekturen:

```text
1324 passed, 12 skipped, 6 warnings in 337.62s (0:05:37)
```

Darin bestehen die 41 neuen Repository-Cases, alle 14 nun regulär
eingesammelten historischen Fälle und die vorhandenen Regressionen.
Die zwölf bestehenden Skips werden nicht als bestanden gezählt. Die sechs
Warnungen betreffen die bereits vorhandenen Hinweise zur TempFS-Nutzung für
Umgebungsisolation und zur experimentellen Instanzrehydrierung.
Funktionsgröße, Docstrings, Ruff, Pylint und MyPy gehören zu diesem Gesamtlauf.
Ruff akzeptiert zusätzlich alle neuen beziehungsweise angepassten Python-Tests.
