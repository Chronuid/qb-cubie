<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-banner.png" -->
<div align="center">

# qb-cubie: Quality-Bench

![Cubie](./docs/.assets/cubie-banner.png)

**qb-cubie bietet einfache Teststrukturen und Datei-Workflows auf Basis von pytest.**  
Eingaben, Rückgabemuster und erwartete Dateien werden gemeinsam beschrieben.  
Reviewer können zusätzliche, ausdrücklich formulierte Kriterien beurteilen.

---

> [!Note]  
> **Dieses Projekt ist experimentell und in einer frühen Entwicklungs-Phase.**  
> Erfolgreiche Tests dokumentieren beobachtete Konformität in den geprüften Fällen.  
> Sie belegen weder allgemeine Korrektheit noch eine vollständige Testabdeckung.
>
> ---
>
> **Cubie befindet sich derzeit unter aktiver Mutation und Überarbeitung und könnte daher Fehler, Unvollständigkeiten oder veraltete Angaben enthalten.**

---

[README](./README.md) • [QA-Handbuch](./docs/GUIDE_Quality-Assurance.md) • [DocEnsurance](./docs/services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Installation

```bash
uv pip install qb-cubie
```

## Einstieg

Voraussetzung ist Python ≥ 3.13. Der öffentliche Distributionsname lautet `qb-cubie`, der Python-Importname `qb_cubie`. In den internen Handbüchern wird weiterhin „cubie“ verwendet. Frühere Importe aus `cubie` müssen auf `qb_cubie` umgestellt werden.

```python
from qb_cubie import EBT, WorldState


def your_function(input_a, input_b):
    result = input_a * (100 + input_b) // 100
    return result


def test_your_function():
    result = EBT(
        target=your_function,
        pre=WorldState(args=(100, 19)),
        post=WorldState(returns=119),
    ).run()
    return result.evaluation

if __name__ == "__main__":
    print(test_your_function())
```

<details>
<summary>Ergebnis</summary>

```text
True
```
</details>

## Lizenz und Abhängigkeiten

qb-cubie steht unter der [MIT-Lizenz](./LICENSE), Copyright © 2026 Dominick Wirzba. Lizenztext, SPDX-Kennung `MIT` und Autor werden in Quelldistribution und Wheel mitgeliefert.

Der Laufzeitkern benötigt `cloudpickle` für TempFS und Serialisierung, `msgspec` für den Standardcodec von PyVenv, `loky` für parallele Auswertungen mit dynamischen Prädikaten und `packaging` für Anforderungsprüfungen. Die ungenutzten Pakete `fsspec` und `path` gehören nicht zu den Abhängigkeiten. pytest wird vom aufrufenden Testprojekt bereitgestellt; der Paketimport und direkte `.run()`-Aufrufe benötigen es nicht.

Die Analysewerkzeuge LibCST, MyPy und Pylint sind über das Extra `linters` erhältlich. Für eine lokale Installation mit diesen Werkzeugen:

```bash
.venv/bin/python -m pip install -e '.[linters]' pytest
```

## Experimentelle Benchmarks außerhalb des Core

Der [Benchmark-Guide](docs/GUIDE_Benchmarks.md) bündelt Schnellstart, eigene
JSONL-Agenten und Szenarien, Ergebnisvergleich, SWE-bench und CI-Messbetrieb.
Er beschreibt auch gespiegelte Developer-Aufgaben mit getrennten
Cubie-/Pytest-Agenten und einem Cubie-freien Vergleichscontainer.
`cubie-bench guide` zeigt denselben Guide aus dem installierten Paket.
Der gesamte Bereich einschließlich Adapter, Datensätzen und Messfunktionen
gehört nicht zum qb-cubie Core.

## Testguided-Vergleichsstudie (`experiments/testguided-study`)

Im Verzeichnis [`experiments/testguided-study`](./experiments/testguided-study/README.md) befindet sich eine unabhängige empirische A/B-Vergleichsstudie (eingereicht im *Google Gemma 4 Developer Agent Competition – Paper Track*). Die Studie untersucht, ob der Zugang zu **qb-cubie** und dessen deklarativen EBT-Verträgen (Example-Based Testing) die Lösungsquote eines lokalen, testgeführten Programmieragenten gegenüber regulärem **pytest** auf realen Software-Engineering-Aufgaben steigert.

### Forschungsfrage und Versuchsaufbau

- **Zentrale Fragestellung:** Verbessert das Angebot von `qb-cubie` (Version 0.0.3) samt strukturierter Anleitung die unabhängig evaluierte Lösungsquote eines mit `gemma4:12b` (Ollama, Consumer-Hardware) betriebenen Coding-Agenten unter identischen Ressourcen- und Zeitbudgets gegenüber der Standard-Kontrollbedingung mit `pytest`?
- **Zero-Leakage-Evaluationsharness:** Beide Agentenarme starten mit identischen Repository-Snapshots und dürfen während der Bearbeitung sichtbare Testdateien im Workspace frei erstellen und modifizieren. Nach Abschluss extrahiert ein separater, Cubie-freier Evaluator-Container ausschließlich den veränderten Produktionscode (`production.patch`), verwirft alle Teständerungen des Agenten und bewertet die Reparatur gegen private, dem Modell verborgene `FAIL_TO_PASS`- und `PASS_TO_PASS`-Testsuiten.
- **Aufgabenbasis:** 129 SWE-bench-kompatible Aufgaben aus 4 realen Python-Repositories (FastAPI, Requests, Rich, HTTPX). Ein Katalog von 39 manuell auditierten Aufgaben ([KANDIDATEN.md](./experiments/testguided-study/KANDIDATEN.md)) bildet die Basis; die iterativen Piloten verwenden standardmäßig 3 fest gefrorene Referenzaufgaben (FastAPI `#9425`, Requests `#6589`, Rich `#3278`, Seed 42).

### Wichtige Dokumente und Artefakte

| Dokument | Inhalt |
| :--- | :--- |
| [experiments/testguided-study/README.md](./experiments/testguided-study/README.md) | Vollständige Dokumentation zu Studienaufbau, Starter-CLI, Profilen und Container-Images |
| [G4DA Paper Submission](./experiments/testguided-study/g4da_paper_submission_qb_cubie_and_floor_effect_analysis.md) | Wettbewerbs-Paper: *qb-cubie and Floor-Effect Analysis* (v1–v9 A/B-Evaluation) |
| [PAPER.md](./experiments/testguided-study/PAPER.md) | Ursprünglicher Studienbericht und Methodik der Single-Agent-Reihen (v1–v5) |
| [PROTOKOLL.md](./experiments/testguided-study/PROTOKOLL.md) | Verbindliches Studienprotokoll, Messgrößen und Hypothesendefinitionen |
| [ANALYSE-GENERATIONEN-V6-V9.md](./experiments/testguided-study/ANALYSE-GENERATIONEN-V6-V9.md) | Detaillierte Telemetrie- und Ursachenanalyse der Multi-Agenten-Generationen v6 bis v9 |
| [DATEN.md](./experiments/testguided-study/DATEN.md) / [KANDIDATEN.md](./experiments/testguided-study/KANDIDATEN.md) | SWE-bench-Aufgabenpool, Audit-Befunde und reproduzierbare Aufgabenselektion |
| [AGENTENDESIGN-V9.md](./experiments/testguided-study/AGENTENDESIGN-V9.md) | Architektur und Spezifikation der Multi-Agenten-Generation v9 |
| [HYPOTHESEN-URSACHENANALYSE.md](./experiments/testguided-study/HYPOTHESEN-URSACHENANALYSE-20261111.md) | Ursachenanalyse zu Inferenzengpässen und Floor-Effekten (Antigravity & Codex) |

---

---

## Example-Based Testing (EBT)

Ein `WorldState` ist ein veränderlicher Datensatz für konkrete Eingaben oder ein erwartetes Ergebnismuster. EBT ruft das Target für jeden angegebenen Eingang einmal auf und vergleicht die beobachteten Ergebnisse.

Standardmäßig wirkt `pre` als reiner Allquantor (`"all"`, jeder Eingang muss bestehen) und `post` als reiner Existenzquantor (`"exists"`, mindestens ein Zielmuster muss passen); über `{"quantor": "all" | "exists", "states": ...}` lassen sich beide Quantoren explizit steuern, wobei Verbote (`WorldState(..., expect=False)`) ausschließlich unter `post={"quantor": "all", ...}` zulässig sind. Bei mehreren Eingängen gilt dieselbe Zielmenge für jeden Eingang; es gibt keine automatische paarweise Zuordnung zwischen `pre[i]` und `post[i]`. Zusammengehörige Ein-/Ausgabepaare benötigen getrennte EBT-Verträge. Eine Liste erlaubter Würfelergebnisse prüft nur die beobachtete Ausgabe; auch ein konstanter Generator kann bestehen. Zufälligkeit und Verteilung werden damit nicht geprüft.

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
from qb_cubie.rbt import HeadlessReviewer, RBT


def test_logging_review():
    RBT(
        target="auth_module.py",
        check="Prüfe die Datei: Werden Passwörter im Klartext geloggt?",
    ).run()


demo = RBT(
    target="auth_module.py",
    check="Prüfe die Datei: Werden Passwörter im Klartext geloggt?",
    reviewer=HeadlessReviewer(answer=True),
)
demo.run()
print(f"Target: {demo.target} | Reviewer: {type(demo.reviewer).__name__}")
```

<details>
<summary>Ergebnis</summary>

```text
Target: auth_module.py | Reviewer: HeadlessReviewer
```
</details>

Die Datei muss vom Reviewer selbst geöffnet und beurteilt werden. Ein positives Review bleibt eine Beurteilung unter den jeweiligen Bedingungen. Eigene automatisierte Reviewer lassen sich injizieren; ein fertiger LLM-Adapter wird nicht mitgeliefert.

Speichere das Beispiel als `test_logging_review.py` und starte es mit freigegebener Terminaleingabe:

```bash
.venv/bin/python -m pytest -q -s test_logging_review.py
```

Antworte nach der Prüfung mit `y` oder `n` und gib optional einen Bericht ein. Eine Ablehnung lässt den Test fehlschlagen.

Die Python-Beispiele dieser README und der Dokumentation werden durch `DocEnsurance` nach dem `CUBIE_DOC_STYLE` direkt ausgeführt und gegen ihre erwarteten `<details>`-Ergebnisse geprüft:

```bash
.venv/bin/python -m pytest -q tests/test_styleguide.py
```

## Bekannte Einschränkungen

Das [Gutachten vom 10. November 2026](./GUTACHTEN.md) dokumentiert den damaligen Stand. Die Punkte B1–B5 aus Abschnitt 9.1 sind inzwischen durch Produktivkorrekturen und Regressionstests abgesichert: EBT bewertet den kopierten Vertragsstand, Phantom-Aufrufe scheitern ausdrücklich, die Linter prüfen Status und Ausgabe, und jeder grafische Review beginnt ohne Entscheidung. Abschnitt 9.2 ergänzt den Kernbetrieb ohne Tk, aktuelle Dateivergleiche und einen geprüften Unterstützungsumfang für kopierte Konsolenskripte. Weiterhin gelten:

- **Prädikate und externe Daten:** Erwartungsobjekte müssen tief kopierbar sein. Funktionen behalten ihre Referenzen auf Closures, globale Variablen und externe Ressourcen; deren Zustand wird nicht eingefroren. Referenzdateien werden ebenfalls nicht archiviert.
- **PyVenv-Importhilfen:** `decontams` ersetzt nur ausdrücklich gewählte Module. Ohne installiertes pytest unterstützt eine begrenzte Importhilfe dessen Testdeklarationen; relevante Laufzeitaufrufe benötigen die echte Bibliothek. Die Importbedingungen bleiben Teil des Testvertrags.
- **Grafischer Reviewer:** Nur der Start der GUI benötigt `tkinter` und eine grafische Umgebung. Ohne Tk bleiben Paketimport, EBT und Headless-RBT verfügbar; der GUI-Aufruf gibt einen Installationshinweis.
- **Kopierte Umgebungen:** Übliche POSIX-Python-Einstiegsskripte werden auf den Klon angepasst. Nicht unterstützte Launcher werden vor Target-Ausführung abgelehnt; insbesondere sind zusätzliche native Windows-`.exe`-Launcher ausgeschlossen. Beliebige absolute Paket- oder Anwendungspfade werden nicht umgeschrieben. Den unterstützten Umfang beschreibt das [Arena-Handbuch](./docs/GUIDE_Arena-Management.md#pyvenv-kopierte-virtuelle-umgebung).
- **Dateivergleich:** Inhalte werden bei jedem Vergleich ohne persistenten Vergleichscache neu gelesen. Gleichzeitig laufende Schreibzugriffe ergeben weiterhin keine atomare Momentaufnahme.

Leere Zustandslisten werden inzwischen abgelehnt; aufeinanderfolgende `.run()`-Aufrufe setzen die EBT-Laufdaten zurück. Das setzt weder Target-Seiteneffekte noch bereits veränderte Argumente zurück. `WorldState(returns=None)` erwartet ausdrücklich `None`; ohne `returns` oder mit `returns=qb_cubie.UNSPECIFIED` bleibt die Rückgabe ungeprüft. Mehrere Eingänge teilen dieselbe Zielmenge; korrelierte Ein-/Ausgabepaare benötigen getrennte Verträge. Ein `JsonReporter` persistiert Ergebnisse, erhebt aber selbst keine fachliche Assertion. Die genaue Vertragsbedeutung steht in der [Semantikreferenz](./docs/GUIDE_Contract-Semantics.md).

Die vollständige Repository-Testsuite ist in der CI für Linux vorgesehen; macOS erhält die begrenzte Wheel-Prüfung, einschließlich fehlendem Tk und echten absoluten MyPy-Dateipfaden. Die Windows-Checks sind bis zur Bereitstellung nativer Windows-Launcher-Anpassungen vorübergehend eingefroren (siehe [CI_PLATFORM_STATUS.md](./docs/CI_PLATFORM_STATUS.md)). Die zuvor nicht regulär eingesammelten 14 Fälle gehören jetzt zur Standardsammlung. Umsetzung, Ausgangsbefunde und Abnahme von Abschnitt 9.2 sind in den zugehörigen Vertrags- und Plattformtests abgesichert.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Arena-Management | ↤](./docs/GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./docs/GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](./docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](./docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](./docs/GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](./docs/GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](./docs/GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Entwicklerübersicht & Internals | ↤](./docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
