<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Core-Internals & Architektur

![Cubie](../../.assets/cubie-logo-written.png)

Technische Entwicklerreferenzen für die Kernmodule von `qb-cubie`: Review-Based Testing (`1.x` – `qb_cubie.core.rbt`) sowie Example-Based Testing und Ausführungsinfrastruktur (`2.x` – `qb_cubie.core.ebt`, `WorldState`, Arenen, `Multiprocessors`, `Linter`).

---

> [!NOTE]
> **Einordnung im Dokumentationsbaum:**  
> Dieses Verzeichnis (`docs/dev/core/`) bündelt ausschließlich die internen Architektur- und Klassenreferenzen des `qb-cubie`-Kerns. Übergreifende Entwicklungsprozesse, Styleguide und Services-Internals liegen im übergeordneten [`docs/dev/`](../README.md); die verbindlichen öffentlichen Handbücher und Vertragssemantiken stehen unter [`docs/core/`](../../core/README.md).

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Empfohlene Lesepfade

| Thema / Subsystem | Lesereihenfolge |
| :--- | :--- |
| **1.x – Review-Based Testing (`qb_cubie.core.rbt`)** | [1.0 Review-Based Testing](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) $\to$ [1.1 RBT-Klassen](./DEV-GUIDE_1-1_RBT-Classes.md) |
| **2.x – Example-Based Testing (`qb_cubie.core.ebt`)** | [2.0 EBT: Entwicklerübersicht](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) $\to$ [2.1 Die EBT-Klasse](./DEV-GUIDE_2-1_EBT-Class.md) $\to$ [2.2 WorldState](./DEV-GUIDE_2-2_WorldState-Class.md) |
| **2.x – Ausführung, Parallelisierung & Analyse** | [2.3 Arenen und IPC-Codecs](./DEV-GUIDE_2-3_Arenas.md) $\to$ [2.4 `Multiprocessors`](./DEV-GUIDE_2-4_Multiprocessors.md) $\to$ [2.5 `Linter`](./DEV-GUIDE_2-5_Linter.md) |

---

## Core-Entwicklerreferenzen (`docs/dev/core/`)

Die folgende Übersicht umfasst sämtliche direkt in `docs/dev/core/` abgelegten Architektur- und Klassenreferenzen und wird automatisch durch `DocFrame` (`CUBIE_DOC_FRAME_3`) synchronisiert:

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Review-Based Testing](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) | RBT orchestriert Beurteilungen anhand einer Prüfregel. Es ist für manuelle Abnahmen oder eigene automatisierte Reviewer nutzbar. Es führt das Target nicht aus und liefert keinen formalen Korrektheits- oder Sicherheitsnachweis. Die [Semantikreferenz](../../core/GUIDE_Contract-Semantics.md) definiert die Grenzen; vollständige Beispiele stehen im [RBT-Nutzungshandbuch](../../core/GUIDE_RBT-Usage-Pattern.md). |
| [RBT-Klassen](./DEV-GUIDE_1-1_RBT-Classes.md) | Die [RBT-Übersicht](DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) beschreibt Ablauf und Aussagegrenzen. Die folgenden Klassen gehören zu `qb_cubie.core.rbt`, die Daten- und Schnittstellenverträge zu `qb_cubie.core.protocols`. |
| [EBT: Entwicklerübersicht](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) | EBT orchestriert konkrete Ausführungen und Ergebnisvergleiche. Die Anordnung von Ausgangsdaten, Operation und Zielmustern erinnert an Hoare-Tripel, implementiert aber keine formale Programmverifikation. Maßgeblich ist die [Vertragssemantik](../../core/GUIDE_Contract-Semantics.md). |
| [Die EBT-Klasse](./DEV-GUIDE_2-1_EBT-Class.md) | `EBT` orchestriert endliche Beispielausführungen. Die [Vertragssemantik](../../core/GUIDE_Contract-Semantics.md) definiert Felder, Match-Regeln und bekannte Fehler zentral. Die Struktur „Ausgangszustand – Operation – Zielmuster“ ist eine Analogie zu Hoare-Tripeln, keine implementierte Beweisführung. |
| [WorldState](./DEV-GUIDE_2-2_WorldState-Class.md) | `WorldState` ist eine veränderliche Dataclass, die konkrete Aufrufdaten oder erwartete Ergebnismuster beschreibt. Sie besitzt keine eigene Ausführungs- oder Beweislogik. Die Bedeutung der Felder hängt von ihrer Verwendung in `pre`, `post` oder einem erfassten Ergebnis ab. Die verbindlichen Regeln stehen in der [Semantikreferenz](../../core/GUIDE_Contract-Semantics.md). |
| [Arenen und IPC-Codecs](./DEV-GUIDE_2-3_Arenas.md) | Arenen implementieren die Ausführungsschicht für konkrete EBT-Fälle. Die beiden vorhandenen Arenen sind Prozess- und Workspace-Abstraktionen ohne OS-Sicherheitsgrenze. Die [Vertragssemantik](../../core/GUIDE_Contract-Semantics.md) und das [Arena-Nutzungshandbuch](../../core/GUIDE_Arena-Management.md) beschreiben die verbindlichen Grenzen. |
| [`Multiprocessors`](./DEV-GUIDE_2-4_Multiprocessors.md) | Diese Entwicklerreferenz beschreibt Multiprozess-Ausführung und die zugehörigen Schnittstellen. |
| [`Linter`](./DEV-GUIDE_2-5_Linter.md) | Diese Entwicklerreferenz beschreibt Aufbau und Schnittstellen der Linter-Integration. |
<!-- /qb:frame -->

---

## Angrenzende Bereiche

| Bereich | Einstieg |
| :--- | :--- |
| Entwicklerdokumentation (Prozesse, Styleguide, Services) | [`docs/dev/README.md`](../README.md) |
| Öffentliche Core-Handbücher & Vertragssemantik | [`docs/core/README.md`](../../core/README.md) |
| Services-Internals (`DocEnsurance`, `DocFrame`) | [`DocEnsurance`](../services/DEV-GUIDE_DocEnsurance.md) • [`DocFrame`](../services/DEV-GUIDE_DocFrame.md) |

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../README.md)  
[↦ | Hintergrund & Essays | ↤](../../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  

</div>
<!-- /qb:frame -->
