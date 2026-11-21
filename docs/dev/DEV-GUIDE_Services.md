<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DEV-GUIDE: Service-Architektur & strikte Service-Isolation

![Cubie](../.assets/cubie-logo-written.png)

Verbindliche Architektur-Spezifikation für Pakete unter `src/qb_cubie/services/`: Clean-Architecture-Abhängigkeitsregel, Bounded Contexts, Functional Core / Imperative Shell sowie Komposition an der Aufrufstelle.

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Makro-Architektur: Dependency Rule & Service-Isolation

Services unter `src/qb_cubie/services/` sind **Bounded Contexts** (jeweils genau eine fachliche Domäne) und folgen einer strikten, unidirektionalen **Dependency Rule** von außen nach innen:

```text
┌─────────────────────────────────────────────────────────────┐
│  Composition Root (CLI-Router, Tests, User-Pipelines)       │
│  • Verdrahtet Services über Core-Protocols & dünne Adapter  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────┐┌──────────────────────────────┐
│ services.doc_ensurance      ││ services.coverage            │
│ (Bounded Context A)         ││ (Bounded Context B)          │
└──────────────┬──────────────┘└──────────────┬───────────────┘
               │      ✗ KEINE Querkopplung     │
               │   (auch kein TYPE_CHECKING)  │
               └──────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  qb_cubie Core (Kernel)                                     │
│  protocols • reporter • linter • arenas • state • _telemetry│
└─────────────────────────────┬───────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Python 3.13 Stdlib & zugelassene Drittpakete (z. B. libcst)│
└─────────────────────────────────────────────────────────────┘

```

### Verbindliche Makro-Invarianten

1. **Strikte Einbahnstraße (`services.<name>` $\to$ Core):** Erlaubt sind ausschließlich die Python-Standardbibliothek, zugelassene Drittpakete (z. B. `libcst`) und `qb_cubie`-Core-Module (`protocols`, `reporter`, `linter`, `arenas`, `state`, `_telemetry`).
2. **Null Querkopplung (Acyclic Dependencies):** Ein Service importiert **niemals** ein Geschwister-Paket unter `qb_cubie.services.*` — auch **nicht** innerhalb von `if TYPE_CHECKING:`. Jede Querkante zerstört eigenständige Importierbarkeit, isolierte Testbarkeit und Entfernbarkeit.
3. **Kohäsion nach Änderungsursache (SRP / CCP):** Ein Service kapselt genau eine fachliche Aufgabe (`doc_ensurance` = Regel- & Snippet-Prüfung, `doc_frame` = Dokument-Rahmen & Link-Graph, `coverage` = Nachweis- & Abdeckungsanalyse).
4. **Komposition nur an der Aufrufstelle:** Services kennen und orchestrieren einander nicht. Verknüpfungen erfolgen ausschließlich im **Composition Root** (CLI-Einstiegspunkt, Test-Suite, Aufrufer-Skript) über Core-Verträge oder dünne Adapter.

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
* **`engine.py` / `rules.py` (Functional Core):** Deterministische Transformationen, Prüfregeln und explizite Zustandsautomaten (`STATE-GUARD`). **Verboten:** Dateisystem-Zugriffe (`open`, `Path.read_text`/`write_text`), Subprozesse, `sys.argv`, `print()`.
* **`adapters.py` / `cli.py` (Imperative Shell):** Kapselt Dateisystem, AST/CST-Parsing, `sys.monitoring`, Profil-Laden und den eigenen CLI-Subcommand (`qb-cubie <service> ...`). Delegiert sofort an den reinen Kern.
* **`__init__.py` (Fassade):** Exportiert ausschließlich die öffentliche Service-API via `__all__` — **ohne** Import-Seiteneffekte (keine I/O, keine Registrierungen, keine globalen Singletons).

### Code-, Zustands- und Ressourcen-Hygiene (*Simplex Veri Sigillum*)

* **Größen- und Lesbarkeitsbudget:** Funktionen **7–12 Zeilen** (exakt eine Aufgabe), Module **300–500 Zeilen** (danach fachlich teilen), Top-Down-Aufbau (*Narrative Programming*: Public API $\to$ Use-Case-Orchestrierung $\to$ interne Pipes $\to$ pure Helfer).
* **Explizite Konfiguration statt globalem Zustand:** Service-Presets (z. B. `CUBIE_COVERAGE_PROFILE`) leben im eigenen Namensraum und werden als unveränderliche Wert-Objekte injiziert.
* **Deterministische Befunde & Sandbox-Souveränität:** Ergebnisse fließen strukturiert über Core-`Diagnostic` / `Reporter[T]`. Dateisystem- oder Prozess-Isolierung läuft über Core-Arenen (`TempFS`, `PyVenv`); Nutzer-Dateien werden nur durch explizit mutierende CLI-Befehle (z. B. `docframe update`) verändert.

---

## 3. Core-Promotion-Regel (Kern schlank halten)

Ein Baustein wandert erst dann aus einem Service in den `qb_cubie`-Core (`protocols` / `reporter`), wenn **beide** Bedingungen erfüllt sind:

1. **Regel der Zwei:** Mindestens zwei Services benötigen dieselbe Abstraktion.
2. **Domänenneutralität:** Der Baustein enthält null Service-Spezifika (z. B. generisches `Diagnostic`, `Severity`, `validate_severity`, `Reporter[T]`, `FileCheckProtocol`).

Domänenspezifische Typen (z. B. `FramePattern`, `EvidenceRecord`) verbleiben **immer** in ihrem Heimat-Service.

---

## 4. Referenz-Blueprint & Entkopplungs-Matrix

| Dimension | Altlast-Anti-Pattern (`DocEnsurance` $\leftrightarrow$ `DocFrame`) | Ziel-Architektur (`Coverage` & entkoppelte Services) |
| --- | --- | --- |
| **Geteilte Typen** | `doc_frame_rules` importiert `DocDiagnostic`, `DocRuleProtocol`, `validate_severity` direkt aus `doc_ensurance`. | `Diagnostic`, `validate_severity` und `FileCheckProtocol` liegen im **Core**; Services importieren nur den Core. |
| **Domänen-Grenze** | `DocEnsurance` erkennt `FramePattern` und baut `DocumentCatalog` aus `doc_frame`. | `DocFrame` kapselt Rahmen/Kataloge vollständig; `DocEnsurance` prüft nur neutrale Dokument-Regeln/Snippets. |
| **Neuer Service (`coverage`)** | — | `qb_cubie.services.coverage` nutzt nur Stdlib (`sys.monitoring`, `ast`, `json`) + Core (`CatalogExtractorProtocol`, `EvidenceCollectorProtocol`, `CoverageRuleProtocol`, `CoverageProfile`). |
| **Service-Verknüpfung** | Direkter Cross-Import zwischen Services. | `CaseCoverage` akzeptiert beliebige `EvidenceRecord`-Lieferanten per `EvidenceCollectorProtocol`; Aufrufer (z. B. `tests/test_styleguide.py`) stecken einen dünnen `DocEnsurance`-Adapter ein. |
| **CLI & Presets** | Vermischte Zuständigkeiten. | Eigener Einstiegspunkt (`qb-cubie coverage ...`) und gekapseltes Default-Profil (`CUBIE_COVERAGE_PROFILE`). |

### Migrationspfad in 3 Schritten

1. **Neubau ab Tag 1 isoliert:** `qb_cubie.services.coverage` strikt unter diesen Regeln aufsetzen; generische Primitiven (`Diagnostic`, `validate_severity`) direkt als schlanke Core-Verträge schneiden.
2. **Core-Umhängung:** `DocEnsurance` und `DocFrame` auf die neuen Core-Verträge migrieren und den Cross-Import `doc_frame_rules` $\to$ `doc_ensurance` entfernen.
3. **Domänen-Bereinigung:** `FramePattern`-/`DocumentCatalog`-Sonderlogik aus `DocEnsurance` entfernen und bei Bedarf im Composition Root über einen Adapter verbinden.

---

## 5. Operations-Checkliste & Meta-Gate für Agenten

Ein Service unter `src/qb_cubie/services/<name>/` gilt erst dann als **abgeschlossen**, wenn alle vier Prüfungen bestehen:

1. **Meta-Gate Import-Grenze (`CstRule` / `test_gate_*.py`):** Statische AST/CST-Prüfung bestätigt null Imports von `qb_cubie.services.*` (inkl. `TYPE_CHECKING`) und null I/O-Imports in reinen Domain-Modulen.
2. **Isolations-Probe:** `python -c "import qb_cubie.services.<name>"` sowie alle Unit-Tests des Services laufen grün, wenn Geschwister-Services im Testlauf entfernt oder blockiert sind.
3. **Schicht- & Budget-Audit:** Azyklischer interner Import-Graph (`models` $\to$ `protocols` $\to$ `engine/rules` $\to$ `adapters/cli`), Funktionen $\le 12$ Zeilen, Module $\le 500$ Zeilen, `__init__.py` ohne Seiteneffekte.
4. **Statische & Dynamische Verifikation:** `MyPy`, `Pylint`, `AstLinter`/`CstLinter` und `pytest` laufen fehlerfrei; alle Vorbedingungen sind durch explizite `STATE-GUARD`s abgesichert.


<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../core/README.md)  
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
