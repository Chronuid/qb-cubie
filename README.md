<center>

# qb-cubie: Quality-Bench

![qb-cubie](./docs/.assets/cubie-banner.png)

**qb-cubie bietet deklarative Akzeptanztests für Python-Funktionen und Datei-Workflows auf Basis von pytest.**  
Eingaben, Rückgabemuster und erwartete Dateien werden gemeinsam beschrieben.  
Reviewer können zusätzliche, ausdrücklich formulierte Kriterien beurteilen.  

---

qb-cubie ist experimentell. Erfolgreiche Tests dokumentieren beobachtete Konformität in den geprüften Fällen.  
Sie belegen weder allgemeine Korrektheit noch eine vollständige Testabdeckung.

---

</center>

## Installation

```bash
uv pip install qb-cubie
```

## Einstieg

Voraussetzung ist Python ≥ 3.13. Der öffentliche Distributionsname lautet `qb-cubie`, der Python-Importname `qb_cubie`. In den internen Handbüchern wird weiterhin „cubie“ verwendet. Frühere Importe aus `cubie` müssen auf `qb_cubie` umgestellt werden.

Im Projektverzeichnis:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -e . pytest
```

Virtuelle Umgebungen, lokale IDE-Einstellungen, Caches und erzeugte Paketmetadaten werden durch die Root-`.gitignore` ausgeschlossen und lokal erzeugt. Für die Entwicklung mit den in `uv.lock` festgehaltenen Abhängigkeiten kann stattdessen `uv sync --locked --group dev` verwendet werden. `pyproject.toml` und `uv.lock` bleiben versioniert.

Der gesamte Benchmark-Bereich ist **experimentell und gehört nicht zum
qb-cubie Core**. Ein modellfreier Smoke-Lauf ist mit dem Extra `benchmarks`
auch ohne Checkout verfügbar: `cubie-bench init-suite ./sets/smoke.toml --preset smoke --fake`,
danach `cubie-bench plan --suite ./sets/smoke.toml` und
`cubie-bench run --suite ./sets/smoke.toml`. Installation, Ergebnisdateien und
Gegenproben erklärt der [Benchmark-Guide](docs/GUIDE_Benchmarks.md#schnellstart).

Die Repository-Tests benötigen zusätzlich lokal provisionierte Arena-Basen und `uv` im `PATH`:

```bash
uv sync --locked --group dev
.venv/bin/python scripts/provision_test_arenas.py
.venv/bin/python -m pytest -q
```

Die Provisionierung ist ein eigener Installationsschritt und kann Netzwerkzugriff benötigen. `PyVenv.setup()` prüft die Codec-Abhängigkeiten und kopiert die Basis, ohne Pakete zu installieren. Die erzeugten Pfade, Paketversionen und Wiederholung des Schritts beschreibt das [Arena-Handbuch](./docs/GUIDE_Arena-Management.md#provisionierung-der-testbasen).

Speichere dieses vollständige Beispiel als `test_tax.py`:

```python
from qb_cubie import EBT, WorldState


def calculate_tax(net, rate):
    return net * (100 + rate) // 100


def test_tax():
    EBT(
        target=calculate_tax,
        pre=WorldState(args=(100, 19)),
        post=WorldState(returns=119),
    ).run()
```

```bash
.venv/bin/python -m pytest -q test_tax.py
```

Erst `.run()` führt den Test aus. Der Standardreporter lässt pytest bei einer negativen Auswertung fehlschlagen.

## Lizenz und Abhängigkeiten

qb-cubie steht unter der [MIT-Lizenz](./LICENSE), Copyright © 2026 Dominick Wirzba. Lizenztext, SPDX-Kennung `MIT` und Autor werden in Quelldistribution und Wheel mitgeliefert.

Der Laufzeitkern benötigt `cloudpickle` für TempFS und Serialisierung, `msgspec` für den Standardcodec von PyVenv, `loky` für parallele Auswertungen mit dynamischen Prädikaten und `packaging` für Anforderungsprüfungen. Die ungenutzten Pakete `fsspec` und `path` gehören nicht zu den Abhängigkeiten. pytest wird vom aufrufenden Testprojekt bereitgestellt; der Paketimport und direkte `.run()`-Aufrufe benötigen es nicht.

Die Analysewerkzeuge LibCST, MyPy und Pylint sind über das Extra `linters` erhältlich. Für eine lokale Installation mit diesen Werkzeugen:

```bash
.venv/bin/python -m pip install -e '.[linters]' pytest
```

Für ein gebautes Wheel lautet der entsprechende Installationsaufruf `python -m pip install 'dist/qb_cubie-0.0.3-py3-none-any.whl[linters]'`. Ohne Extra bleiben die Kernfunktionen verfügbar; beim Aufruf fehlender Analysewerkzeuge erscheint ein Installationshinweis. Eigene Linterpfade können über `QB_CUBIE_MYPY_PATH` beziehungsweise `QB_CUBIE_PYLINT_PATH` gesetzt werden.

Veröffentlichte Abhängigkeiten haben Mindestversionen und eine Obergrenze vor der nächsten Hauptversion; bei dem noch mit `0.x` versionierten `msgspec` liegt sie vor der nächsten Nebenversion. Diese Grenzen bilden den vorgesehenen Kompatibilitätsrahmen, keine Zusage, dass jede Kombination geprüft wurde. Die Entwicklungsgruppe `dev` enthält pytest, Hypothesis, pytest-xdist, Ruff und festgelegte Analysewerkzeuge. Sie wird nicht als Paket-Extra veröffentlicht. `uv.lock` hält die genauen direkten und transitiven Versionen für Entwicklung und Repository-CI fest; konsumierende Projekte lösen innerhalb der veröffentlichten Bereiche selbst auf.

Nach Änderungen an Anforderungen wird `uv lock` ausgeführt und die Änderung an `uv.lock` gemeinsam geprüft. `uv sync --locked --group dev` installiert die festgehaltene Entwicklungsumgebung. Releases werden mit isoliertem Setuptools-Build (`setuptools>=77` für SPDX-Lizenzmetadaten) und den folgenden Installationsprüfungen validiert. Die Konfiguration folgt der [Setuptools-Dokumentation](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html) und der [uv-Trennung von Abhängigkeiten, Extras und Entwicklungsgruppen](https://docs.astral.sh/uv/concepts/projects/dependencies/). Für den grafischen Reviewer wird zusätzlich eine Python-Installation mit Tk benötigt.

## Experimentelle Benchmarks außerhalb des Core

Der [Benchmark-Guide](docs/GUIDE_Benchmarks.md) bündelt Schnellstart, eigene
JSONL-Agenten und Szenarien, Ergebnisvergleich, SWE-bench und CI-Messbetrieb.
Er beschreibt auch gespiegelte Developer-Aufgaben mit getrennten
Cubie-/Pytest-Agenten und einem Cubie-freien Vergleichscontainer.
`cubie-bench guide` zeigt denselben Guide aus dem installierten Paket.
Der gesamte Bereich einschließlich Adapter, Datensätzen und Messfunktionen
gehört nicht zum qb-cubie Core.

### Replikation und Download der Experimentdaten (Study-Runs)

Die vollständigen Rohdaten und Telemetrieläufe der empirischen Vergleichsstudie (~1,1 GB entpackt, ~918 MB komprimiert) sind zum Schutz vor Repository-Überlastung aus dem Git-Tracking und PyPI-Paket ausgeschlossen. Sie stehen als GitHub-Release-Asset bereit und können mit dem mitgelieferten Validierungs- und Downloadskript automatisch heruntergeladen, per SHA-256 kryptografisch verifiziert und entpackt werden:

```bash
python scripts/download_study_runs.py
```

Das Skript entpackt die Läufe nach `experiments/testguided-study/runs/`. Alternativ kann ein bereits heruntergeladenes Archiv geprüft und entpackt werden:

```bash
python scripts/download_study_runs.py --from-file dist/testguided-study-runs.tar.gz
```

## Wheel-Prüfung und CI

Die [CI](./.github/workflows/ci.yml) läuft bei Pushes und Pull Requests und kann manuell gestartet werden. Die Prüfmatrix ist bewusst begrenzt:

| Prüfung | Python | Betriebssystem / GitHub-Runner |
| --- | --- | --- |
| Wheel bauen, installieren und prüfen | 3.13, 3.14 | Linux (`ubuntu-24.04`), macOS (`macos-15`) *(Windows vorübergehend eingefroren)* |
| Vollständige Repository-Testsuite mit provisionierten Arena-Basen | 3.13, 3.14 | Linux (`ubuntu-24.04`) |

Details zum Plattformstatus und den vorübergehend eingefrorenen Windows-Checks dokumentiert [CI_PLATFORM_STATUS.md](./docs/CI_PLATFORM_STATUS.md).

Die Wheel-Jobs bauen zunächst eine Quelldistribution und daraus das Wheel. Lokale Arena-Basen werden aus beiden Distributionen ausgeschlossen. [check_wheel.py](./scripts/check_wheel.py) erzeugt eine neue virtuelle Umgebung ohne Zugriff auf die Hostpakete und prüft zunächst Paketimport und EBT nur mit den deklarierten Pflichtabhängigkeiten, ohne pytest oder Analysewerkzeuge. Anschließend wird pytest ausdrücklich als Testtreiber installiert und die Kerninstallation geprüft. Danach wird dasselbe Wheel mit dem Extra `linters` installiert und erneut geprüft. `pip check` prüft die Abhängigkeiten. Die [Installationstests](./tests/wheel/smoke_installed.py) laufen außerhalb des Checkouts mit isoliertem Python, ohne die Repository-`conftest.py`, zusätzliche pytest-Plugins oder `PYTHONPATH=src`.

Geprüft werden Paketname, Lizenzmetadaten und Lizenztext, die Herkunft des installierten Pakets, alle Paketimporte, positive und negative EBT-/RBT-Auswertungen, ein TempFS-Dateiworkflow, PyVenv mit PickleCodec sowie fehlende und installierte Analysewerkzeuge (LibCST, MyPy, Pylint). Diese Installationsprüfungen ersetzen keine vollständige Plattformabnahme; insbesondere laufen die übrigen Repository-Tests bislang nur unter Linux. Weitere Python-Versionen sind durch diese Matrix nicht abgesichert.

Lokal mit Python 3.13 oder 3.14 und `uv` im `PATH`:

```bash
uv build --clear --python python3.13
python3.13 scripts/check_wheel.py dist
```

Unter Windows kann für beide Befehle `python` verwendet werden, wenn der gewünschte Interpreter im `PATH` steht. Der Build verwendet eine isolierte Build-Umgebung; die Wheel-Prüfung benötigt weder eine editierbare Installation noch provisionierte Arena-Basen. Build und Installation können Netzwerkzugriff benötigen. Die vollständige Repository-Testsuite verwendet dagegen die Versionen aus `uv.lock` und das Extra `dev` wie oben beschrieben.

---

## Example-Based Testing (EBT)

Ein `WorldState` ist ein veränderlicher Datensatz für konkrete Eingaben oder ein erwartetes Ergebnismuster. EBT ruft das Target für jeden angegebenen Eingang einmal auf und vergleicht die beobachteten Ergebnisse.

Bei mehreren Eingängen gilt dieselbe Liste erlaubter und verbotener Zielmuster für jeden Eingang. Es gibt keine automatische paarweise Zuordnung zwischen `pre[i]` und `post[i]`. Zusammengehörige Ein-/Ausgabepaare benötigen getrennte EBT-Verträge. Eine Liste erlaubter Würfelergebnisse prüft nur die beobachtete Ausgabe; auch ein konstanter Generator kann bestehen. Zufälligkeit und Verteilung werden damit nicht geprüft.

Typen, Unions, reguläre Ausdrücke und Prädikate können anstelle fester Rückgabewerte verwendet werden. Die genaue Bedeutung aller Felder und Vergleiche steht in der [verbindlichen Semantikreferenz](./docs/GUIDE_Contract-Semantics.md).

## Datei-Workflows und Arenen

`TempFS` führt Targets mit dem Host-Interpreter in einem Kindprozess mit temporärem Arbeitsverzeichnis aus. `PyVenv` verwendet eine kopierte virtuelle Umgebung. Beide Prozesse besitzen weiterhin die Rechte des aufrufenden Benutzers und bieten **keine OS-Sicherheitsgrenze**. Sie eignen sich für vertrauenswürdigen Code. `DockerArena` und `VmArena` sind [Entwürfe](./docs/feature-drafts/virtualization/README.md) und gehören nicht zur öffentlichen API.

Die Hydrierung von `pre.fs` begrenzt Schreibziele auf den Workspace und weist
absolute Ziele, Pfadausbrüche und nach außen führende Links mit `ValueError` ab.
Hostquellen, Konfigurationen, Targets und Rückgaben müssen dennoch vertrauenswürdig
sein. Die [Pfadprüfung](./docs/GUIDE_Arena-Management.md#pfadgrenzen-der-hydrierung)
ersetzt keine Sicherheitsgrenze für nicht vertrauenswürdigen Code.

Ein vollständiges Beispiel für eine Dateitransformation steht im [EBT-Nutzungshandbuch](./docs/GUIDE_EBT-Usage-Pattern.md). Für `fs`-Prüfungen muss eine Arena explizit angegeben werden.

## Review-Based Testing (RBT)

RBT übergibt eine Zielbezeichnung und eine Prüfregel an einen Reviewer. Es führt das Target nicht aus und liest eine als String übergebene Quelldatei nicht automatisch ein. Standardmäßig wartet `HeadlessReviewer` am Terminal auf eine Entscheidung; interaktive pytest-Läufe benötigen `-s`.

```python
from qb_cubie.rbt import RBT


def test_logging_review():
    RBT(
        target="auth_module.py",
        check="Prüfe die Datei: Werden Passwörter im Klartext geloggt?",
    ).run()
```

Die Datei muss vom Reviewer selbst geöffnet und beurteilt werden. Ein positives Review bleibt eine Beurteilung unter den jeweiligen Bedingungen. Eigene automatisierte Reviewer lassen sich injizieren; ein fertiger LLM-Adapter wird nicht mitgeliefert.

Speichere das Beispiel als `test_logging_review.py` und starte es mit freigegebener Terminaleingabe:

```bash
.venv/bin/python -m pytest -q -s test_logging_review.py
```

Antworte nach der Prüfung mit `y` oder `n` und gib optional einen Bericht ein. Eine Ablehnung lässt den Test fehlschlagen.

Die Python-Beispiele dieser README werden direkt aus den Codeblöcken gelesen und mit pytest ausgeführt. Die Prüfung benötigt keine Arena-Basen und lässt sich separat starten:

```bash
.venv/bin/python -m pytest -q tests/test_readme_examples.py
```

Dabei wird die Terminaleingabe für das RBT-Beispiel vorgegeben. Gegenproben mit einer fehlerhaften Steuerberechnung und einem abgelehnten Review müssen fehlschlagen; so wird auch abgesichert, dass die Beispiele tatsächlich `.run()` ausführen und Fehler an pytest melden.

## Bekannte Einschränkungen

Das [Gutachten vom 10. November 2026](./GUTACHTEN.md) dokumentiert den damaligen Stand. Die Punkte B1–B5 aus Abschnitt 9.1 sind inzwischen durch Produktivkorrekturen und [Regressionstests](tests/docs_tmp/CONTRACT_CASES_9_1.md) abgesichert: EBT bewertet den kopierten Vertragsstand, Phantom-Aufrufe scheitern ausdrücklich, die Linter prüfen Status und Ausgabe, und jeder grafische Review beginnt ohne Entscheidung. Abschnitt 9.2 ergänzt den Kernbetrieb ohne Tk, aktuelle Dateivergleiche und einen geprüften Unterstützungsumfang für kopierte Konsolenskripte. Weiterhin gelten:

- **Prädikate und externe Daten:** Erwartungsobjekte müssen tief kopierbar sein. Funktionen behalten ihre Referenzen auf Closures, globale Variablen und externe Ressourcen; deren Zustand wird nicht eingefroren. Referenzdateien werden ebenfalls nicht archiviert.
- **PyVenv-Importhilfen:** `decontams` ersetzt nur ausdrücklich gewählte Module. Ohne installiertes pytest unterstützt eine begrenzte Importhilfe dessen Testdeklarationen; relevante Laufzeitaufrufe benötigen die echte Bibliothek. Die Importbedingungen bleiben Teil des Testvertrags.
- **Grafischer Reviewer:** Nur der Start der GUI benötigt `tkinter` und eine grafische Umgebung. Ohne Tk bleiben Paketimport, EBT und Headless-RBT verfügbar; der GUI-Aufruf gibt einen Installationshinweis.
- **Kopierte Umgebungen:** Übliche POSIX-Python-Einstiegsskripte werden auf den Klon angepasst. Nicht unterstützte Launcher werden vor Target-Ausführung abgelehnt; insbesondere sind zusätzliche native Windows-`.exe`-Launcher ausgeschlossen. Beliebige absolute Paket- oder Anwendungspfade werden nicht umgeschrieben. Den unterstützten Umfang beschreibt das [Arena-Handbuch](./docs/GUIDE_Arena-Management.md#pyvenv-kopierte-virtuelle-umgebung).
- **Dateivergleich:** Inhalte werden bei jedem Vergleich ohne persistenten Vergleichscache neu gelesen. Gleichzeitig laufende Schreibzugriffe ergeben weiterhin keine atomare Momentaufnahme.

Leere Zustandslisten werden inzwischen abgelehnt; aufeinanderfolgende `.run()`-Aufrufe setzen die EBT-Laufdaten zurück. Das setzt weder Target-Seiteneffekte noch bereits veränderte Argumente zurück. `WorldState(returns=None)` erwartet ausdrücklich `None`; ohne `returns` oder mit `returns=qb_cubie.UNSPECIFIED` bleibt die Rückgabe ungeprüft. Mehrere Eingänge teilen dieselbe Zielmenge; korrelierte Ein-/Ausgabepaare benötigen getrennte Verträge. Ein `JsonReporter` persistiert Ergebnisse, erhebt aber selbst keine fachliche Assertion. Die genaue Vertragsbedeutung steht in der [Semantikreferenz](./docs/GUIDE_Contract-Semantics.md).

Die vollständige Repository-Testsuite ist in der CI für Linux vorgesehen; macOS erhält die begrenzte Wheel-Prüfung, einschließlich fehlendem Tk und echten absoluten MyPy-Dateipfaden. Die Windows-Checks sind bis zur Bereitstellung nativer Windows-Launcher-Anpassungen vorübergehend eingefroren (siehe [CI_PLATFORM_STATUS.md](./docs/CI_PLATFORM_STATUS.md)). Die zuvor nicht regulär eingesammelten 14 Fälle gehören jetzt zur Standardsammlung. Umsetzung, Ausgangsbefunde und Abnahme von Abschnitt 9.2 stehen in den [Vertragsfällen](tests/docs_tmp/CONTRACT_CASES_9_2.md).

---

---

<center>

![Error while trying to load the image](./docs/.assets/cubie-small.png)

## Dokumentation

[Dokumentationsübersicht und Einordnung der Ablagen](docs/README.md)

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](./docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](./docs/GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](./docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](./docs/GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](./docs/GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](./docs/GUIDE_Linter.md)  

[↦ | Experimentelle Benchmarks außerhalb des Core | ↤](./docs/GUIDE_Benchmarks.md)  
[↦ | Entwicklerübersicht EBT | ↤](./docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
