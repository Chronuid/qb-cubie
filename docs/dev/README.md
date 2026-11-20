<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Entwicklerdokumentation

![Cubie](../.assets/cubie-logo-written.png)

Zentraler Einstiegspunkt für die interne Entwicklerdokumentation von `qb-cubie`: Architektur- und Klassenübersichten für Kernmodule und Services sowie verbindliche Leitfäden zu Styleguide, Bug-Dokumentation und Releases.

---

> [!NOTE]
> **Abgrenzung zu Anwender-Handbüchern & Verträgen:**  
> Die Dokumente unter `docs/dev/` beschreiben interne Architektur, Implementierungsdetails und Entwicklungsprozesse für die Arbeit am Code. Für die verbindliche öffentliche Vertragssemantik und Nutzungsbeispiele gelten die Handbücher unter [`docs/`](../README.md) – insbesondere die [Vertragssemantik](../GUIDE_Contract-Semantics.md) und das [QA-Handbuch](../GUIDE_Quality-Assurance.md).

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Einstieg nach Aufgabe

| Ziel / Aufgabe | Empfohlener Einstieg |
| :--- | :--- |
| **Code schreiben, strukturieren & prüfen** | [Styleguide](./Style-Guide.md) und [Testsuite-Leitfaden](../../tests/README.md) |
| **Review-Based Testing (`qb_cubie.rbt`) verstehen** | [Review-Based Testing](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) $\to$ [RBT-Klassen](./DEV-GUIDE_1-1_RBT-Classes.md) |
| **Example-Based Testing (`qb_cubie.ebt`) & Kernmodule verstehen** | [EBT: Entwicklerübersicht](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) $\to$ [Die EBT-Klasse](./DEV-GUIDE_2-1_EBT-Class.md), [WorldState](./DEV-GUIDE_2-2_WorldState-Class.md), [Arenen & IPC-Codecs](./DEV-GUIDE_2-3_Arenas.md), [`Multiprocessors`](./DEV-GUIDE_2-4_Multiprocessors.md), [`Linter`](./DEV-GUIDE_2-5_Linter.md) |
| **Services (`qb_cubie.services`) entwickeln & erweitern** | [`DocEnsurance`](./services/DEV-GUIDE_DocEnsurance.md) und [`DocFrame` (Prototyp)](./services/DEV-GUIDE_DocFrame.md) |
| **Bugs reproduzierbar erfassen & prüfen** | [Bugs dokumentieren](./DEV-GUIDE_Write-down-the-bugs.md) und [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) |
| **Releases vorbereiten & CI-Kompatibilität prüfen** | [Release-Vorbereitung](./DEV-GUIDE_Release-Preparation.md) und [CI Plattformstatus](../CI_PLATFORM_STATUS.md) |
| **Nächste Entwicklungsschritte & Aufräum-Roadmap einsehen** | [Next Steps](./DEV-GUIDE_Next-Steps.md) |

---

## Kern-Architektur, Konventionen & Prozesse (`docs/dev/`)

Die folgende Übersicht umfasst sämtliche direkt in `docs/dev/` abgelegten Entwickler-Dokumente (RBT `1.x`, EBT & Kern-Subsysteme `2.x`, Prozess-Leitfäden und Styleguide) und wird automatisch durch `DocFrame` (`CUBIE_DOC_FRAME_3`) synchronisiert:

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Review-Based Testing](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) | RBT orchestriert Beurteilungen anhand einer Prüfregel. Es ist für manuelle Abnahmen oder eigene automatisierte Reviewer nutzbar. Es führt das Target nicht aus und liefert keinen formalen Korrektheits- oder Sicherheitsnachweis. Die [Semantikreferenz](../GUIDE_Contract-Semantics.md) definiert die Grenzen; vollständige Beispiele stehen im [RBT-Nutzungshandbuch](../GUIDE_RBT-Usage-Pattern.md). |
| [RBT-Klassen](./DEV-GUIDE_1-1_RBT-Classes.md) | Die [RBT-Übersicht](DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) beschreibt Ablauf und Aussagegrenzen. Die folgenden Klassen gehören zu `qb_cubie.rbt`, die Daten- und Schnittstellenverträge zu `qb_cubie.protocols`. |
| [EBT: Entwicklerübersicht](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) | EBT orchestriert konkrete Ausführungen und Ergebnisvergleiche. Die Anordnung von Ausgangsdaten, Operation und Zielmustern erinnert an Hoare-Tripel, implementiert aber keine formale Programmverifikation. Maßgeblich ist die [Vertragssemantik](../GUIDE_Contract-Semantics.md). |
| [Die EBT-Klasse](./DEV-GUIDE_2-1_EBT-Class.md) | `EBT` orchestriert endliche Beispielausführungen. Die [Vertragssemantik](../GUIDE_Contract-Semantics.md) definiert Felder, Match-Regeln und bekannte Fehler zentral. Die Struktur „Ausgangszustand – Operation – Zielmuster“ ist eine Analogie zu Hoare-Tripeln, keine implementierte Beweisführung. |
| [WorldState](./DEV-GUIDE_2-2_WorldState-Class.md) | `WorldState` ist eine veränderliche Dataclass, die konkrete Aufrufdaten oder erwartete Ergebnismuster beschreibt. Sie besitzt keine eigene Ausführungs- oder Beweislogik. Die Bedeutung der Felder hängt von ihrer Verwendung in `pre`, `post` oder einem erfassten Ergebnis ab. Die verbindlichen Regeln stehen in der [Semantikreferenz](../GUIDE_Contract-Semantics.md). |
| [Arenen und IPC-Codecs](./DEV-GUIDE_2-3_Arenas.md) | Arenen implementieren die Ausführungsschicht für konkrete EBT-Fälle. Die beiden vorhandenen Arenen sind Prozess- und Workspace-Abstraktionen ohne OS-Sicherheitsgrenze. Die [Vertragssemantik](../GUIDE_Contract-Semantics.md) und das [Arena-Nutzungshandbuch](../GUIDE_Arena-Management.md) beschreiben die verbindlichen Grenzen. |
| [`Multiprocessors`](./DEV-GUIDE_2-4_Multiprocessors.md) | Diese Entwicklerreferenz beschreibt Multiprozess-Ausführung und die zugehörigen Schnittstellen. |
| [`Linter`](./DEV-GUIDE_2-5_Linter.md) | Diese Entwicklerreferenz beschreibt Aufbau und Schnittstellen der Linter-Integration. |
| [DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes](./DEV-GUIDE_Next-Steps.md) |  |
| [DEV-GUIDE: Release-Vorbereitung und sauberer Release](./DEV-GUIDE_Release-Preparation.md) | Dieser Leitfaden beschreibt den verbindlichen Ablauf vom Branch-Abgleich bis zum automatisierten GitHub- und PyPI-Release von `qb-cubie`. |
| [DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`)](./DEV-GUIDE_Write-down-the-bugs.md) | Kurzanleitung zum einheitlichen, reproduzierbaren Erfassen und Pflegen von Bugs in [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md). |
| [Styleguide](./Style-Guide.md) | Dieser Styleguide beschreibt Konventionen für die Entwicklung und Strukturierung des Cubie-Codes. |
<!-- /qb:frame -->

---

## Services-Internals (`docs/dev/services/`)

Technische Entwicklerreferenzen zu den wiederverwendbaren Verifikations- und Dokumentations-Services in `qb_cubie.services` (automatisch synchronisiert durch `DocFrame`):

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="docs/dev/services" recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [`DocEnsurance`](./services/DEV-GUIDE_DocEnsurance.md) | Das `doc_ensurance`-Paket bildet die Verifikations-Engine für ausführbare Dokumentation innerhalb von `qb_cubie.services`. Es überträgt das formallogische Hoare-Tripel $\{P\}\ S\ \{Q\}$ aus der `EBT`-Architektur auf Markdown-Dokumente und sichert Code-Beispiele dreistufig ab: **strukturell** (Nachbarschafts-Muster rund um Code-Anker), **statisch-didaktisch** (Pluggable Check-Regeln & Linter-Adapter) und **funktional** (isolierte oder zustandsgeteilte Ausführung in einer `Arena`). |
| [`DocFrame` (Prototyp)](./services/DEV-GUIDE_DocFrame.md) | Das `doc_frame`-Paket bildet den **Prototyp** einer zweistufigen Synchronisations-, Routing- und Verifikations-Engine für Markdown-Dokumentrahmen innerhalb von `qb_cubie.services` (noch zu evaluieren und zu härten). Es kombiniert eine **Zero-Config-Katalogisierung** (Pass 1: Fence-sicherer Span-Scanner & Metadaten-Extraktion in einen unveränderlichen `DocumentCatalog`) mit **tiefen- und kontextsensitivem Rendering** (Pass 2: zustandslose `FrameBlockProtocol`-Bausteine, geschützte Content-Slots und dynamische Router) sowie **orthogonalen Dokument-Prüfregeln** (`CUBIE_DOCFRAME_RULES`) für `DocEnsurance`. |
<!-- /qb:frame -->

---

## QA-Handbücher

Für die Qualitätssicherung, das Test-Guided Development (TGD) sowie den sauberen Aufbau deklarativer Verträge gelten diese vier QA-Handbücher aus `docs/`:

| Handbuch | Fokus & Inhalt |
| :--- | :--- |
| [Qualitätssicherung mit Cubie](../GUIDE_Quality-Assurance.md) | Leitfaden zu deklarativen Verträgen, orthogonalen Prüfschichten, Test-Guided Development (TGD) und $Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$. |
| [Vertragsaufbau: Eindeutigkeit & Kopplung](../GUIDE_Contract-Design.md) | Paarweise Verträge, `@pytest.mark.parametrize` und Vermeidung von Unterspezifikation durch gemischte `pre`/`post`-Listen. |
| [Erwartungssteuerung & Safety (`expect`-Flags)](../GUIDE_Expect-Flags.md) | Einsatz von `expect=True`/`expect=False` auf `WorldState`- und `EBT`-Ebene, Red-Phase-Gegenproben und Schutz vor *Vacuous Passes*. |
| [Fortgeschrittene Quantoren (`all` vs. `exists`)](../GUIDE_Quantifiers.md) | Umschalten der Standard-Quantoren (`pre="all"`, `post="exists"`) für UND-Checklisten in `post` und ODER-Routen in `pre`. |

---

## Angrenzende Entwicklungs-Ressourcen

| Bereich | Dokument |
| :--- | :--- |
| Gesamte Dokumentations-Übersicht (Anwender-Guides, Services, Hintergrund, Drafts) | [Dokumentations-Index](../README.md) |
| Testsuite, `pytest`-Marker, `Makefile`-Profile und Arena-Provisionierung | [Testsuite-Leitfaden](../../tests/README.md) |
| Zentrale Übersicht offener Bugs und bekannter Einschränkungen | [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) |
| CI-Matrix und Plattform-Kompatibilitätsstatus (Linux, macOS, Windows) | [CI Plattformstatus](../CI_PLATFORM_STATUS.md) |
| Versionshistorie und Release-Notes | [`CHANGELOG.md`](../../CHANGELOG.md) |
| Pflege & Funktionsweise der automatischen Rahmen und Index-Tabellen | [DocFrame-Handbuch (Prototyp)](../services/GUIDE_DocFrame.md) |

---

## Pflege dieses Routing-Dokuments

Neue Entwickler-Dokumente unter `docs/dev/` oder `docs/dev/services/` werden automatisch in die obigen Tabellen aufgenommen, sobald sie über einen gültigen `CUBIE_DOC_FRAME_1`-Kopfrahmen mit kurzem Einführungstext vor dem ersten `---` verfügen. Anschließend lassen sich alle Rahmen und Index-Tabellen synchronisieren und verifizieren:

```bash
qb-cubie docframe update docs/dev/README.md
.venv/bin/python -m pytest -q tests/test_styleguide.py
```

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](../GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
