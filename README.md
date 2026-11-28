<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-banner.png" -->
<div align="center">

# qb-cubie: Quality-Bench

![Cubie](./docs/.assets/cubie-banner.png)

**qb-cubie bietet einfache Teststrukturen und Datei-Workflows auf Basis von pytest.**  
Eingaben, Rückgabemuster und erwartete Dateien werden gemeinsam beschrieben.  
Reviewer können zusätzliche, ausdrücklich formulierte Kriterien beurteilen.

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

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

Der [Benchmark-Guide](docs/feature-drafts/GUIDE_Benchmarks.md) bündelt Schnellstart, eigene
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

Typen, Unions, reguläre Ausdrücke und Prädikate können anstelle fester Rückgabewerte verwendet werden. Die genaue Bedeutung aller Felder und Vergleiche steht in der [verbindlichen Semantikreferenz](./docs/core/GUIDE_Contract-Semantics.md).

## Datei-Workflows und Arenen

`TempFS` führt Targets mit dem Host-Interpreter in einem Kindprozess mit temporärem Arbeitsverzeichnis aus. `PyVenv` verwendet eine kopierte virtuelle Umgebung. Beide Prozesse besitzen weiterhin die Rechte des aufrufenden Benutzers und bieten **keine OS-Sicherheitsgrenze**. Sie eignen sich für vertrauenswürdigen Code. `DockerArena` und `VmArena` sind [Entwürfe](./docs/feature-drafts/virtualization/README.md) und gehören nicht zur öffentlichen API.

Die Hydrierung von `pre.fs` begrenzt Schreibziele auf den Workspace und weist
absolute Ziele, Pfadausbrüche und nach außen führende Links mit `ValueError` ab.
Hostquellen, Konfigurationen, Targets und Rückgaben müssen dennoch vertrauenswürdig
sein. Die [Pfadprüfung](./docs/core/GUIDE_Arena-Management.md#pfadgrenzen-der-hydrierung)
ersetzt keine Sicherheitsgrenze für nicht vertrauenswürdigen Code.

Ein vollständiges Beispiel für eine Dateitransformation steht im [EBT-Nutzungshandbuch](./docs/core/GUIDE_EBT-Usage-Pattern.md). Für `fs`-Prüfungen muss eine Arena explizit angegeben werden.

## Review-Based Testing (RBT)

RBT übergibt eine Zielbezeichnung und eine Prüfregel an einen Reviewer. Es führt das Target nicht aus und liest eine als String übergebene Quelldatei nicht automatisch ein. Standardmäßig wartet `HeadlessReviewer` am Terminal auf eine Entscheidung; interaktive pytest-Läufe benötigen `-s`.

```python
from qb_cubie.core.rbt import HeadlessReviewer, RBT


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

Die Python-Beispiele und Dokumentrahmen dieser README und der Dokumentation werden durch `DocFrame` und `DocEnsurance` nach dem `CUBIE_DOC_STYLE` direkt ausgeführt und gegen ihre erwarteten `<details>`-Ergebnisse geprüft:

```bash
.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py
```

## Bekannte Fehler und Einschränkungen

Offene Bugs, dokumentierte Einschränkungen sowie plattformspezifische Hinweise (einschließlich des aktuellen Windows-CI-Status) werden zentral in [`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md) gepflegt. Hinweise zum Erfassen neuer Bugs stehen im [DEV-GUIDE: Bugs dokumentieren](./docs/dev/DEV-GUIDE_Write-down-the-bugs.md).

Für den historischen Prüfstand siehe außerdem das [Gutachten](./GUTACHTEN.md) sowie [CI_PLATFORM_STATUS.md](CI_PLATFORM_STATUS.md).

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./docs/GUIDE_TGD.md)  

[↦ | Service-Core | ↤](./docs/services/GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./docs/README.md)  
[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./docs/dev/README.md)  
[↦ | Core-Internals | ↤](./docs/dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
