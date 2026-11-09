<center>

# Cubie: Quality-Bench

![Cubie](./docs/.assets/cubie-banner.png)

**Cubie bietet deklarative Akzeptanztests für Python-Funktionen und Datei-Workflows auf Basis von pytest.**  
Eingaben, Rückgabemuster und erwartete Dateien werden gemeinsam beschrieben.  
Reviewer können zusätzliche, ausdrücklich formulierte Kriterien beurteilen.  

---

Cubie ist experimentell. Erfolgreiche Tests dokumentieren beobachtete Konformität in den geprüften Fällen.  
Sie belegen weder allgemeine Korrektheit noch eine vollständige Testabdeckung.

---

</center>

## Einstieg

Voraussetzung ist Python ≥ 3.13. Im Projektverzeichnis:

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -e .
```

Virtuelle Umgebungen, lokale IDE-Einstellungen, Caches und erzeugte Paketmetadaten werden durch die Root-`.gitignore` ausgeschlossen und lokal erzeugt. Für die Entwicklung mit den in `uv.lock` festgehaltenen Abhängigkeiten kann stattdessen `uv sync --locked --extra dev` verwendet werden. `pyproject.toml` und `uv.lock` bleiben versioniert.

Die Repository-Tests benötigen zusätzlich lokal provisionierte Arena-Basen und `uv` im `PATH`:

```bash
uv sync --locked --extra dev
.venv/bin/python scripts/provision_test_arenas.py
.venv/bin/python -m pytest -q
```

Die Provisionierung ist ein eigener Installationsschritt und kann Netzwerkzugriff benötigen. `PyVenv.setup()` prüft die Codec-Abhängigkeiten und kopiert die Basis, ohne Pakete zu installieren. Die erzeugten Pfade, Paketversionen und Wiederholung des Schritts beschreibt das [Arena-Handbuch](./docs/GUIDE_Arena-Management.md#provisionierung-der-testbasen).

Speichere dieses vollständige Beispiel als `test_tax.py`:

```python
from cubie import EBT, WorldState


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

## Wheel-Prüfung und CI

Die [CI](./.github/workflows/ci.yml) läuft bei Pushes und Pull Requests und kann manuell gestartet werden. Die Prüfmatrix ist bewusst begrenzt:

| Prüfung | Python | Betriebssystem / GitHub-Runner |
| --- | --- | --- |
| Wheel bauen, installieren und prüfen | 3.13, 3.14 | Linux (`ubuntu-24.04`), macOS (`macos-15`), Windows (`windows-2022`) |
| Vollständige Repository-Testsuite mit provisionierten Arena-Basen | 3.13, 3.14 | Linux (`ubuntu-24.04`) |

Die Wheel-Jobs bauen zunächst eine Quelldistribution und daraus das Wheel. Lokale Arena-Basen werden aus beiden Distributionen ausgeschlossen. [check_wheel.py](./scripts/check_wheel.py) erzeugt eine neue virtuelle Umgebung ohne Zugriff auf die Hostpakete und installiert ausschließlich das Wheel mit seinen deklarierten Pflichtabhängigkeiten. `pip check` prüft die Abhängigkeiten. Die [Installationstests](./tests/wheel/smoke_installed.py) laufen anschließend außerhalb des Checkouts mit isoliertem Python, ohne die Repository-`conftest.py`, zusätzliche pytest-Plugins oder `PYTHONPATH=src`.

Geprüft werden die Herkunft des installierten Pakets, alle Paketimporte, positive und negative EBT-/RBT-Auswertungen, ein TempFS-Dateiworkflow, PyVenv mit PickleCodec und der MyPy-Aufruf. Diese Installationsprüfungen ersetzen keine vollständige Plattformabnahme; insbesondere laufen die übrigen Repository-Tests bislang nur unter Linux. Weitere Python-Versionen sind durch diese Matrix nicht abgesichert.

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

Ein vollständiges Beispiel für eine Dateitransformation steht im [EBT-Nutzungshandbuch](./docs/GUIDE_EBT-Usage-Pattern.md). Für `fs`-Prüfungen muss eine Arena explizit angegeben werden.

## Review-Based Testing (RBT)

RBT übergibt eine Zielbezeichnung und eine Prüfregel an einen Reviewer. Es führt das Target nicht aus und liest eine als String übergebene Quelldatei nicht automatisch ein. Standardmäßig wartet `HeadlessReviewer` am Terminal auf eine Entscheidung; interaktive pytest-Läufe benötigen `-s`.

```python
from cubie.rbt import RBT


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

Der aktuelle Prüfkern kann falsche Erfolge melden: Leere Zustandslisten können ungeprüft bestehen, und wiederholtes `.run()` auf derselben EBT-Instanz vermischt Ergebnisse. Verwende pro Lauf eine neue Instanz und nichtleere, explizite Verträge. `WorldState(returns=None)` erwartet explizit `None`; ohne `returns` oder mit `returns=cubie.UNSPECIFIED` bleibt die Rückgabe ungeprüft. Weitere Grenzen und deren genaue Bedeutung stehen in der [Semantikreferenz](./docs/GUIDE_Contract-Semantics.md); die Befunde erläutert das [Gutachten](./GUTACHTEN.md).

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
