<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DEV-GUIDE: Service-Architektur & strikte Service-Isolation

![Cubie](../.assets/cubie-logo-written.png)

Verbindliche Architektur-Spezifikation für Pakete unter `src/qb_cubie/core/services/` und den gemeinsamen Service-Core (`src/qb_cubie/core/service_core/`): Clean-Architecture-Abhängigkeitsregel, Bounded Contexts, Functional Core / Imperative Shell sowie Komposition an der Aufrufstelle.

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

## 1. Makro-Architektur: Dependency Rule & Service-Isolation

Services unter `src/qb_cubie/core/services/` sind **Bounded Contexts** (jeweils genau eine fachliche Domäne) und folgen einer strikten, unidirektionalen **Dependency Rule** von außen nach innen:

```text
┌─────────────────────────────────────────────────────────────┐
│  Composition Root (CLI-Router, Tests, User-Pipelines)       │
│  • Verdrahtet Services über Core-Protocols & dünne Adapter  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────┐┌──────────────────────────────┐
│ services.doc_ensurance      ││ services.doc_frame / <neu>   │
│ (Bounded Context A)         ││ (Bounded Context B)          │
└──────────────┬──────────────┘└──────────────┬───────────────┘
               │      ✗ KEINE Querkopplung     │
               │   (auch kein TYPE_CHECKING)  │
               └──────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  qb_cubie.core.service_core  (Domänenneutraler Service-Core)│
│  guards • workspace (WorkspaceView, atomic_write) •         │
│  rules (RuleRegistry, FileCheckRunner) • reporting          │
│  ✗ KEINE Rückwärts-Importe in core.services.*               │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  qb_cubie Core (Kernel)                                     │
│  protocols • reporter • linter • arenas • ebt • rbt         │
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Python 3.13 Stdlib & zugelassene Drittpakete (z. B. libcst)│
└─────────────────────────────────────────────────────────────┘

```

### Verbindliche Makro-Invarianten

1. **Strikte Einbahnstraße (`services.<name>` $\to$ `core.service_core` $\to$ Core-Kernel):** Erlaubt sind ausschließlich die Python-Standardbibliothek, zugelassene Drittpakete (z. B. `libcst`), `qb_cubie.core.service_core` sowie die übrigen `qb_cubie`-Core-Module (`protocols`, `reporter`, `linter`, `arenas`, `ebt`, `rbt`). Umgekehrt darf `core.service_core` **niemals** in `core.services.*` importieren oder Service-Domänensymbole referenzieren (`META-SERVICE-CORE-NEUTRALITY`); zudem löst `qb_cubie.core.__init__` das Subpaket `services` strikt lazy via PEP-562 (`__getattr__`) auf.
2. **Null Querkopplung (Acyclic Dependencies):** Ein Service importiert **niemals** ein Geschwister-Paket unter `qb_cubie.core.services.*` — auch **nicht** innerhalb von `if TYPE_CHECKING:`. Jede Querkante zerstört eigenständige Importierbarkeit, isolierte Testbarkeit und Entfernbarkeit.
3. **Kohäsion nach Änderungsursache (SRP / CCP):** Ein Service kapselt genau eine fachliche Aufgabe (`doc_ensurance` = Regel- & Snippet-Prüfung, `doc_frame` = Dokument-Rahmen & Link-Graph, `coverage` = Nachweis- & Abdeckungsanalyse).
4. **Komposition nur an der Aufrufstelle:** Services kennen und orchestrieren einander nicht. Verknüpfungen erfolgen ausschließlich im **Composition Root** (CLI-Einstiegspunkt, Test-Suite, Aufrufer-Skript) über Core-Verträge (`WorkspaceCheckRuleProtocol`, `FileCheckProtocol`, `Reporter`) oder dünne Adapter.

---

## 2. Mikro-Architektur: Innerer Aufbau eines Clean Service

Jeder Service trennt **reine Domänenlogik (Functional Core)** strikt von **Seiteneffekten (Imperative Shell)** nach Ports & Adapters:

### Azyklischer Schichten- und Modulfluss

```text
models.py ──▶ protocols.py ──▶ engine.py / rules.py ──▶ adapters.py / cli.py ──▶ __init__.py
 (DTOs)         (Ports)        (Pure Core & Guards)       (I/O & CLI-Shell)       (Public API)

```

* **`models.py` (Domänen-DTOs):** Unveränderliche Datenstrukturen (`dataclass(frozen=True)` oder `msgspec.Struct`), frei von I/O und Geschäftslogik.
* **`protocols.py` (Ports / Dependency Inversion):** `typing.Protocol`-Verträge für benötigte Datenquellen, Sensoren und Prüfer. Der Service definiert, was er braucht — nicht, wer es liefert.
* **`engine.py` / `rules.py` (und alle Nicht-Shell-Module — Functional Core):** Deterministische Transformationen, Prüfregeln und explizite Zustandsautomaten (`STATE-GUARD` via `service_core.guards`). **Verboten:** Dateisystem-Zugriffe und Probes (`open`, `print`, `read_text`/`write_text`, `exists`, `is_file`, `is_dir`, `rglob`, `glob`, `iterdir`, `mkdir`, `unlink`, `stat`, `cwd`), Subprozesse und `sys.argv`. Pfad-Existenzprüfungen erfolgen ausschließlich über den reinen Lese-Port `WorkspaceView.has_path(...)` aus `qb_cubie.core.service_core.workspace`.
* **`adapters.py` / `cli.py` (Imperative Shell):** Kapselt Dateisystem (`find_project_root`, `crawl_files`, `FileSystemWorkspaceView`, `atomic_write_text`), AST/CST-Parsing, `sys.monitoring`, Profil-Laden und den eigenen CLI-Subcommand (`qb-cubie <service> ...`). Delegiert sofort an den reinen Kern.
* **`__init__.py` (Fassade):** Exportiert ausschließlich die öffentliche Service-API via `__all__` — **ohne** Import-Seiteneffekte (keine I/O, keine Registrierungen, keine globalen Singletons).

### Code-, Zustands- und Ressourcen-Hygiene (*Simplex Veri Sigillum*)

* **Größen- und Lesbarkeitsbudget:** Funktionen **7–12 Zeilen** (exakt eine Aufgabe), Module **300–500 Zeilen** (danach fachlich teilen), Top-Down-Aufbau (*Narrative Programming*: Public API $\to$ Use-Case-Orchestrierung $\to$ interne Pipes $\to$ pure Helfer).
* **Explizite Konfiguration statt globalem Zustand:** Service-Presets (z. B. `CUBIE_COVERAGE_PROFILE`) leben im eigenen Namensraum und werden als unveränderliche Wert-Objekte injiziert.
* **Deterministische Befunde & Sandbox-Souveränität:** Ergebnisse fließen strukturiert über Core-`Diagnostic` / `Reporter[T]`. Dateisystem- oder Prozess-Isolierung läuft über Core-Arenen (`TempFS`, `PyVenv`); Nutzer-Dateien werden nur durch explizit mutierende CLI-Befehle (z. B. `docframe update`) verändert.

---

## 3. Core-Promotion-Regel (Kern schlank halten)

Ein Baustein wandert erst dann aus einem Service in den `qb_cubie`-Core (`core/service_core/`, `core/protocols.py` oder `core/reporter.py`), wenn **beide** Bedingungen erfüllt sind:

1. **Regel der Zwei:** Mindestens zwei Services benötigen dieselbe Abstraktion.
2. **Domänenneutralität:** Der Baustein enthält null Service-Spezifika (z. B. `guards`, `workspace` mit `WorkspaceView` & `atomic_write_text`, `RuleRegistry`, `FileCheckRunner`, `FileContextCache`, `ServiceReport`, `Diagnostic`, `validate_severity`, `Reporter[T]`).

Domänenspezifische Typen (z. B. `FramePattern`, `DocumentCatalog`, `ExamplePattern`, `EvidenceRecord`) verbleiben **immer** in ihrem Heimat-Service. Alle Bausteine von Zyklus 1 beschreibt das [Service-Core-Handbuch](../services/GUIDE_Service-Core.md).

---

## 4. Referenz-Blueprint & Entkopplungs-Matrix

| Dimension | Historisches Anti-Pattern (bereinigt) | Realisierte Ziel-Architektur (`service_core`, `doc_ensurance`, `doc_frame` & künftig `coverage`) |
| --- | --- | --- |
| **Geteilte Typen & Guards** | `doc_frame_rules` importierte aus `doc_ensurance`; Root-Suche, Crawler und Guards waren dupliziert. | `Diagnostic` (inkl. `context`), `ServiceReportProtocol`, `validate_severity` liegen in `core/protocols.py`; Guards, `workspace` (`WorkspaceView`, `crawl_files`, `atomic_write_text`), `rules` (`RuleRegistry`, `FileCheckRunner`, `FileContextCache`) und `reporting` (`ServiceReport`, `report_to_dict`) liegen in **`qb_cubie.core.service_core`**. |
| **Prüf-Orchestrierung & Domänen-Grenze** | `DocFrame` hatte keinen eigenen Prüf-Runner und lief huckepack über `DocEnsurance` samt Dummy-`scan()`/`check()`-Methoden. | `DocFrame.check()` prüft nativ über `service_core.FileCheckRunner` und `WorkspaceCheckRuleProtocol` (`FileContextCache` parst jede Datei 1× statt 4×, `depends_on=("DOCFRAME-MISSING",)`). `FramePattern` und `CUBIE_DOCFRAME_RULES` sind frei von Dummy-Methoden und Filesystem-I/O (`adapters.py` + `WorkspaceView`). |
| **Reporting & Atomares Schreiben** | `JsonReporter` lehnte `ServiceReportProtocol` ab; `DocFrame` nutzte nicht-atomares `write_text`. | `JsonReporter` unterstützt `RunTrace` **und** `ServiceReportProtocol` (`schema_version: 1`) über `atomic_write_text`; `PytestReporter` formatiert optionalen `context`/`session_id`; `DocFrame` unterstützt `reporter=...` und `atomic_write_text`. |
| **Service-Fassade** | `qb_cubie.core.__init__` und `core/services/__init__.py` luden Geschwister-Services eager. | PEP-562-Lazy-Fassade (`__getattr__`) in `qb_cubie.core/__init__.py` (`services`) und `qb_cubie.core.services/__init__.py` löst Submodule bedarfsgerecht auf, ohne Geschwister-Services zu laden. |
| **Neuer Service (`coverage`, `styleguide`)** | — | Komponiert direkt `service_core.{guards, workspace, rules, reporting}` ohne Vererbungszwang und ohne Markdown-Overhead. |
| **Service-Verknüpfung** | Direkter Cross-Import oder Huckepack-Runner. | Komposition erfolgt im Composition Root (`tests/test_doc_ensurance.py`, `tests/test_doc_frame.py`, CLI) über Core-Protokolle (`WorkspaceCheckRuleProtocol`, `Reporter`). |

### Migrationsstatus

1. **Core-Umhängung & Isolation (umgesetzt):** Domänenneutrale Primitiven nach `qb_cubie.core.protocols` promoviert, Cross-Imports zwischen `doc_frame` und `doc_ensurance` entfernt, Lazy-Fassade eingeführt.
2. **Service-Core Zyklus 1 (umgesetzt):** `src/qb_cubie/core/service_core/` (`guards.py`, `workspace.py`, `rules.py`, `reporting.py`) eingeführt; `DocFrame.check()` (`FileCheckRunner`), `doc_frame/adapters.py` + `WorkspaceView`, `DocEnsurance` (`RuleRegistry`, `normalize_excludes`, `execute_file_checks`), `CstLinter` (`crawl_files`), `JsonReporter` (`ServiceReportProtocol`) und geschärftes Meta-Gate 4 (`META-SERVICE-CORE-NEUTRALITY` + Filesystem-Probe-Verbot) abgeschlossen.
3. **Service-Core Zyklus 2 & neue Services (geplant, siehe [`HYPOTHESIS.md`](../services/HYPOTHESIS.md)):** Optionale Markdown-Lexer-Subschicht (`service_core/markdown.py`), lazy CLI-Command-Registry (`service_core/cli_spec.py` inkl. `qb-cubie docensurance`) sowie Neubau künftiger Services (`coverage`, `styleguide`) ab Tag 1 unter Meta-Gate 4.

---

## 5. Operations-Checkliste & Meta-Gate für Agenten

Ein Service unter `src/qb_cubie/core/services/<name>/` (sowie jede Änderung an `src/qb_cubie/core/service_core/`) gilt erst dann als **abgeschlossen**, wenn alle vier Prüfungen bestehen (automatisch durchgesetzt von `tests/tests_core/tests_services/test_service_architecture_gate.py`):

1. **Meta-Gate Import-, I/O- & Neutralitäts-Grenze (`test_service_architecture_gate.py`):**
   * `META-SERVICE-ISOLATION`: Null Imports von `qb_cubie.core.services.*` in Geschwister-Services (inkl. `TYPE_CHECKING`).
   * `META-SERVICE-PURE-DOMAIN-IO`: Null verbotene I/O-Operationen **oder Filesystem-Probes** (`open`, `print`, `read_text`, `write_text`, `exists`, `is_file`, `is_dir`, `rglob`, `glob`, `iterdir`, `mkdir`, `unlink`, `stat`, `cwd`, `subprocess`, `sys.argv`) in sämtlichen Nicht-Shell-Modulen eines Services (Shell-Ausnahmen: `__init__.py`, `__main__.py`, `adapters.py`, `cli.py`, `_source_loader.py`, `<service_name>.py`).
   * `META-SERVICE-DOMAIN-COUPLING`: Null `DocFrame`-Domänensymbole in `doc_ensurance`.
   * `META-SERVICE-CORE-NEUTRALITY`: Null Rückwärts-Importe oder Domänensymbole aus `core/services/*` innerhalb von `src/qb_cubie/core/service_core/`.
2. **Isolations-Probe:** `python -c "import qb_cubie.core.services.<name>"` läuft grün bei blockierten Geschwister-Services (`sys.meta_path`), und `import qb_cubie.core.service_core` läuft grün bei vollständig blockiertem `qb_cubie.core.services`.
3. **Schicht- & Budget-Audit:** Azyklischer interner Import-Graph in jedem Service **und** in `core/service_core/`, Funktionen $\le 12$ Zeilen, Module $\le 500$ Zeilen, `__init__.py` ohne Seiteneffekte.
4. **Statische & Dynamische Verifikation:** `MyPy`, `Pylint`, `AstLinter`/`CstLinter`, `DocFrame.check()`, `DocEnsurance` und `pytest` laufen fehlerfrei; alle Vorbedingungen sind durch explizite `STATE-GUARD`s (`service_core.guards`) abgesichert.


<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

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
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
