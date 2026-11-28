<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Entwicklerdokumentation

![Cubie](../.assets/cubie-logo-written.png)

Zentraler Einstiegspunkt für die interne Entwicklerdokumentation von `qb-cubie`: Core-Architektur (`docs/dev/core/`), Services-Internals (`docs/dev/services/`) sowie verbindliche Leitfäden zu Styleguide, Bug-Dokumentation, Agenten-Berichten und Releases (`docs/dev/`).

---

> [!NOTE]
> **Abgrenzung zu Anwender-Handbüchern & Verträgen:**  
> Die Dokumente unter `docs/dev/` beschreiben interne Architektur, Implementierungsdetails und Entwicklungsprozesse für die Arbeit am Code. Für die verbindliche öffentliche Vertragssemantik und Nutzungsbeispiele gelten die Handbücher unter [`docs/`](../README.md) – insbesondere die [Vertragssemantik](../core/GUIDE_Contract-Semantics.md) und das [QA-Handbuch](../GUIDE_Quality-Assurance.md).

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Bereichs-Navigation (`docs/dev/`)

| Bereich | Fokus & Inhalt | Einstieg |
| :--- | :--- | :--- |
| **Core-Internals** (`docs/dev/core/`) | Architektur- und Klassenreferenzen für RBT (`1.x`) und EBT, `WorldState`, Arenen, `Multiprocessors`, `Linter` (`2.x`). | [Core-Internals Index](./core/README.md) |
| **Prozesse & Konventionen** (`docs/dev/`) | Styleguide, `CUBIE_DOC_FRAME_*`-Konventionen, Agenten-Berichte, Bug-Dokumentation, Release-Ablauf und Next Steps. | [Übersicht unten](#prozesse-konventionen--styleguide-docsdev) |
| **Services-Internals** (`docs/dev/services/`) | Technische Referenzen zu den wiederverwendbaren Services in `qb_cubie.core.services` (`DocEnsurance`, `DocFrame`). | [Übersicht unten](#services-internals-docsdevservices) |

---

## Einstieg nach Aufgabe

| Ziel / Aufgabe | Empfohlener Einstieg |
| :--- | :--- |
| **Code schreiben, strukturieren & prüfen** | [Styleguide](./Style-Guide.md) und [Testsuite-Leitfaden](../../tests/README.md) |
| **Review-Based Testing (`qb_cubie.core.rbt`) verstehen** | [Review-Based Testing](./core/DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) $\to$ [RBT-Klassen](./core/DEV-GUIDE_1-1_RBT-Classes.md) |
| **Example-Based Testing (`qb_cubie.core.ebt`) & Kernmodule verstehen** | [EBT: Entwicklerübersicht](./core/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) $\to$ [Die EBT-Klasse](./core/DEV-GUIDE_2-1_EBT-Class.md), [WorldState](./core/DEV-GUIDE_2-2_WorldState-Class.md), [Arenen & IPC-Codecs](./core/DEV-GUIDE_2-3_Arenas.md), [`Multiprocessors`](./core/DEV-GUIDE_2-4_Multiprocessors.md), [`Linter`](./core/DEV-GUIDE_2-5_Linter.md) |
| **Services (`qb_cubie.core.services`) & `service_core` entwickeln & erweitern** | [Service-Architektur & Isolation](./DEV-GUIDE_Services.md) $\to$ [Service-Core-Handbuch](../services/GUIDE_Service-Core.md), [`DocEnsurance`](./services/DEV-GUIDE_DocEnsurance.md) und [`DocFrame` (Prototyp)](./services/DEV-GUIDE_DocFrame.md) |
| **Bugs reproduzierbar erfassen & prüfen** | [Bugs dokumentieren](./DEV-GUIDE_Write-down-the-bugs.md), [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) und [Archiv behobener Bugs](../misc/lake/SOLVED_ISSUES.md) |
| **TGD-Zyklen in `qb-cubie` steuern & abnehmen** | [TGD-Workflow-Profil für `qb-cubie`](./DEV-GUIDE_TGD-Workflow.md) und [TGD-Knoten-Handbücher (`docs/tgd/`)](../tgd/README.md) |
| **Agenten-Berichte, Analysen & Audits verfassen** | [Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`)](./DEV-GUIDE_Agent-Reports.md) |
| **`CUBIE_DOC_FRAME_*`-Konventionen nachschlagen** | [`CUBIE_DOC_FRAME_*`-Konventionen für Agenten](./DEV-GUIDE_DocFrame-Conventions.md) |
| **Releases vorbereiten & CI-Kompatibilität prüfen** | [Release-Vorbereitung](./DEV-GUIDE_Release-Preparation.md) und [CI Plattformstatus](../../CI_PLATFORM_STATUS.md) |
| **Nächste Entwicklungsschritte & Aufräum-Roadmap einsehen** | [Next Steps](./DEV-GUIDE_Next-Steps.md) |

---

## Core-Architektur & Klassenreferenzen (`docs/dev/core/`)

Alle Kernmodul-Referenzen (RBT `1.x`, EBT & Ausführungsschicht `2.x`) – ausführlicher Einstieg über [`docs/dev/core/README.md`](./core/README.md) (automatisch synchronisiert durch `DocFrame`):

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="links" dir="docs/dev/core" recursive="false" -->
[↦ | Review-Based Testing | ↤](./core/DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./core/DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./core/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./core/DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./core/DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./core/DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./core/DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./core/DEV-GUIDE_2-5_Linter.md)  
<!-- /qb:frame -->

---

## Prozesse, Konventionen & Styleguide (`docs/dev/`)

Direkt in `docs/dev/` abgelegte Prozess-Leitfäden, Agenten-Konventionen und der Styleguide (automatisch synchronisiert durch `DocFrame`):

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [DEV-GUIDE: Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`)](./DEV-GUIDE_Agent-Reports.md) | Kurzanleitung für Agenten zum korrekten Ausfüllen des `CUBIE_DOC_FRAME_2`-Provenance-Headers und zum strukturierten Aufbau von Analysen, Hypothesen, Audits und TGD-Protokollen. |
| [DEV-GUIDE: `CUBIE_DOC_FRAME_*`-Konventionen für Agenten](./DEV-GUIDE_DocFrame-Conventions.md) | Kompakte Kurzreferenz aller aktuellen `CUBIE_DOC_FRAME_*`-Rahmenkonventionen (`CUBIE_DOC_FRAME_1` bis `CUBIE_DOC_FRAME_3`), Zonen, Attribute, Prüfregeln und Sync-Kommandos für Agenten. |
| [DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes](./DEV-GUIDE_Next-Steps.md) |  |
| [DEV-GUIDE: Release-Vorbereitung und sauberer Release](./DEV-GUIDE_Release-Preparation.md) | Dieser Leitfaden beschreibt den verbindlichen Ablauf vom Branch-Abgleich bis zum automatisierten GitHub- und PyPI-Release von `qb-cubie`. |
| [DEV-GUIDE: Service-Architektur & strikte Service-Isolation](./DEV-GUIDE_Services.md) | Verbindliche Architektur-Spezifikation für Pakete unter `src/qb_cubie/core/services/` und den gemeinsamen Service-Core (`src/qb_cubie/core/service_core/`): Clean-Architecture-Abhängigkeitsregel, Bounded Contexts, Functional Core / Imperative Shell sowie Komposition an der Aufrufstelle. |
| [DEV-GUIDE: TGD-Workflow-Profil für `qb-cubie`](./DEV-GUIDE_TGD-Workflow.md) | Technisches Projekt-Profil zur Anwendung der flexiblen TGD-Knoten-Handbücher (`docs/tgd/`) im `qb-cubie`-Repository: Knoten-Kommando-Matrix, aktive Stil-Gates, plattformunabhängiges Minimal-Run-Format (`RUN-*.md`), 3-Zustands-Artefakt-Lebenszyklus und Prozess-Mutanten-Mapping (`PM1`–`PM8`). |
| [DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`)](./DEV-GUIDE_Write-down-the-bugs.md) | Kurzanleitung zum einheitlichen, reproduzierbaren Erfassen und Pflegen von Bugs in [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md). |
| [Styleguide](./Style-Guide.md) | Dieser Styleguide beschreibt Konventionen für die Entwicklung und Strukturierung des Cubie-Codes. |
<!-- /qb:frame -->

---

## Services-Internals (`docs/dev/services/`)

Technische Entwicklerreferenzen zu den wiederverwendbaren Verifikations- und Dokumentations-Services in `qb_cubie.core.services` (automatisch synchronisiert durch `DocFrame`):

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="docs/dev/services" recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [`DocEnsurance`](./services/DEV-GUIDE_DocEnsurance.md) | Das `doc_ensurance`-Paket bildet die Verifikations-Engine für ausführbare Dokumentation innerhalb von `qb_cubie.core.services`. Es überträgt das formallogische Hoare-Tripel $\{P\}\ S\ \{Q\}$ aus der `EBT`-Architektur auf Markdown-Dokumente und sichert Code-Beispiele dreistufig ab: **strukturell** (Nachbarschafts-Muster rund um Code-Anker), **statisch-didaktisch** (Pluggable Check-Regeln & Linter-Adapter) und **funktional** (isolierte oder zustandsgeteilte Ausführung in einer `Arena`). |
| [`DocFrame` (Prototyp)](./services/DEV-GUIDE_DocFrame.md) | Das `doc_frame`-Paket bildet den **Prototyp** einer zweistufigen Synchronisations-, Routing- und Verifikations-Engine für Markdown-Dokumentrahmen innerhalb von `qb_cubie.core.services` (noch zu evaluieren und zu härten). Es setzt auf dem gemeinsamen `qb_cubie.core.service_core` auf und kombiniert **Zero-Config-Katalogisierung** (Pass 1: Fence-sicherer Span-Scanner & Metadaten-Extraktion in einen unveränderlichen `DocumentCatalog` mit reinem `WorkspaceView`-Port), **tiefen- und kontextsensitives Rendering** (Pass 2: I/O-freie `FrameBlockProtocol`-Bausteine, geschützte Content-Slots, dynamische Router und atomares `atomic_write_text`) sowie **eigenständige Rahmen-Verifikation** über `DocFrame.check()` (`FileCheckRunner` + `CUBIE_DOCFRAME_RULES`). |
<!-- /qb:frame -->

---

## QA-Handbücher

Für die Qualitätssicherung, das Test-Guided Development (TGD) sowie den sauberen Aufbau deklarativer Verträge gelten diese QA-Handbücher aus `docs/` und `docs/tgd/`:

| Handbuch | Fokus & Inhalt |
| :--- | :--- |
| [Qualitätssicherung mit Cubie](../GUIDE_Quality-Assurance.md) | Leitfaden zu deklarativen Verträgen, orthogonalen Prüfschichten, TGD-Überblick und $Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$. |
| [Test-Guided Development (TGD)](../GUIDE_TGD.md) | TGD für Einsteiger und Experten: TDD mit kontrollierter Rückwärtstür (`GREEN_AUDIT`) nach Karl Poppers Fallibilismus, optionale Stützräder (`ANALYSIS` & `HYPOTHESIS`), Fünf-Schritte-Ablauf und Living Documentation. |
| [TGD-Knoten-Handbücher (Zustandsautomat)](../tgd/README.md) | Universelle, projektübergreifende Knoten-Verträge für alle sechs TGD-Knoten (`ANALYSIS`, `HYPOTHESIS`, `PHASE_RED`, `PHASE_GREEN`, `GREEN_AUDIT`, `LIVING_DOCS`). |
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
| CI-Matrix und Plattform-Kompatibilitätsstatus (Linux, macOS, Windows) | [CI Plattformstatus](../../CI_PLATFORM_STATUS.md) |
| Versionshistorie und Release-Notes | [`CHANGELOG.md`](../../CHANGELOG.md) |
| Pflege & Funktionsweise der automatischen Rahmen und Index-Tabellen | [DocFrame-Handbuch (Prototyp)](../services/GUIDE_DocFrame.md) |

---

## Pflege dieses Routing-Dokuments

Neue Entwickler-Dokumente unter `docs/dev/`, `docs/dev/core/` oder `docs/dev/services/` werden automatisch in die obigen Tabellen aufgenommen, sobald sie über einen gültigen `CUBIE_DOC_FRAME_1`-Kopfrahmen mit kurzem Einführungstext vor dem ersten `---` verfügen. Anschließend lassen sich alle Rahmen und Index-Tabellen synchronisieren und verifizieren:

```bash
qb-cubie docframe update docs/dev/README.md
```

```bash
qb-cubie docframe check docs/dev/
```

```bash
qb-cubie docensurance check docs/dev/
```

```bash
.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py
```

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | Service-Core | ↤](../services/GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Core-Internals | ↤](./core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

[↦ | DEV-GUIDE: Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`) | ↤](./DEV-GUIDE_Agent-Reports.md)  
[↦ | DEV-GUIDE: `CUBIE_DOC_FRAME_*`-Konventionen für Agenten | ↤](./DEV-GUIDE_DocFrame-Conventions.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Service-Architektur & strikte Service-Isolation | ↤](./DEV-GUIDE_Services.md)  
[↦ | DEV-GUIDE: TGD-Workflow-Profil für `qb-cubie` | ↤](./DEV-GUIDE_TGD-Workflow.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
