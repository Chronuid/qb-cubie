<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Gemini-App" model="Gemini 4 Neon" effort="High" -->
# GEMINI-12: Umsetzung (Stufe 1) — Universelle TGD-Knoten-Handbücher (`docs/tgd/`) & `qb-cubie`-Dev-Profil

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** High
- **Erstellungsdatum:** 26. November 2026, ~17:15 (CET)
- **Synthesebasis:** `docs/services/HYPOTHESIS-POST.md`, `docs/services/ANALYSIS-POST.md`, `docs/GUIDE_TGD.md`, `docs/dev/DEV-GUIDE_Services.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md`, `docs/dev/DEV-GUIDE_DocFrame-Conventions.md`, unsere gemeinsame Konversation in der Gemini-App sowie für Antigravity-CLI nicht im Detail einsehbare Informationen aus dem Memory-System der Gemini-App. In dieser Konversation durfte die Gemini-App (`Gemini 4 Neon`, Effort `High`) bereits den überarbeiteten Ablauf-Abschnitt von `GEMINI-8.md` sowie die Erstentwürfe für `GEMINI-9.md`, `GEMINI-10.md`, `GEMINI-11.md` und dieses Dokument (`GEMINI-12.md`) formulieren; der Nutzer hat diese Entwürfe vor der Übergabe an Antigravity-CLI jeweils noch um einige für die Gemini-App unbekannte kleine Details mutiert.
- **Stand:** qb-cubie (`v0.1.1`, Branch `main`, Commit `38cfce0a`; direkter Zugriff auf Working Tree / Git in der Gemini-App nicht vorhanden)
- **Git-Log:** `38cfce0a` ("... thinking about the current series of TGD experiments ...")

---

```text
commit 38cfce0afd4f7019f33641bc341ac23b5e5cf75d (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 26 17:13:22 2026 +0100

    ... thinking about the current series of TGD experiments ...

Auftrag (docs/services/GEMINI-12.md — erstellt in Gemini-App):
- Umsetzung Stufe 1 (Dokumentations-Authoring & Verifikation): Erstellung der
  universellen TGD-Knoten-Handbücher unter docs/tgd/ (Einsteiger, Experten &
  Agenten) sowie des technischen qb-cubie-Workflow-Profils unter
  docs/dev/DEV-GUIDE_TGD-Workflow.md auf Basis von HYPOTHESIS-POST.md und den
  verbindlichen Beschlüssen E1–E6.
- Scope: Reiner Dokumentations-Schnitt ausschließlich unter docs/ (src/ und
  tests/ bleiben zu 100 % unverändert).
```
<!-- /qb:frame -->

# Ziel

Erstellung der modularen, universell wiederverwendbaren TGD-Knoten-Handbücher unter **`docs/tgd/`** (für Menschen — Einsteiger wie Experten — sowie KI-Agenten) samt klar getrenntem, technisch-kompaktem `qb-cubie`-Projekt-Profil unter **`docs/dev/DEV-GUIDE_TGD-Workflow.md`** sowie SSOT-Synchronisation der angrenzenden Einstiegs- und Index-Dokumente.

## Kontext

Die empirische Analyse (`docs/services/ANALYSIS-POST.md`) und die Hypothesenbildung (`docs/services/HYPOTHESIS-POST.md`) haben die 6+1-Automaten-Topologie, die Auflösung der `GREEN_AUDIT`-Ambiguität (`AUDIT-REPRO → AUDIT-VERDICT → AUDIT-FIX → AUDIT-CLOSE`, Ausgänge `RESOLVED` vs. `REFUTED`), die drei Konfliktregeln (L4-Muster, Pre-Flight-Triage, Zwei-Stufen-Gate-Modell & Fixture-Hygiene) sowie die Prozess-Mutanten `PM1`–`PM8` fundiert ausgearbeitet.

Für die Umsetzung gilt jedoch eine zentrale **Architektur- und Sprachschärfung** gegenüber `HYPOTHESIS-POST.md`:
1. **Reguläre QA-Handbücher (`docs/tgd/`)** richten sich gleichermaßen an **Einsteiger, Experten und KI-Agenten** und folgen dem zugänglichen, didaktisch klaren Stil von `docs/GUIDE_TGD.md` und den übrigen QA-Handbüchern. Sie müssen **universell, abstrakt und projektübergreifend wiederverwendbar** formuliert sein — keine hart verdrahteten `qb-cubie`-Interna als normative Regel!
2. **Dev-Guides (`docs/dev/`)** sind auf **technische Klarheit und Effizienz** optimiert. Sämtliche konkreten `qb-cubie`-Bindungen aus `HYPOTHESIS-POST.md` (CLI-Befehle, `BUG-006`/`body_lines()`-Advisory, Minimal-Ticket-Vorlage, `DOC_EXCLUDES`, `docs/misc/runs/`, `docs/misc/lake/`, `tests/GREEN_AUDIT.md`, `PM1`–`PM8`-Gate-Mapping) wandern sauber gebündelt in das neue Projekt-Profil **`docs/dev/DEV-GUIDE_TGD-Workflow.md`**.

## Weiteres

@docs/services/HYPOTHESIS-POST.md  
@docs/services/ANALYSIS-POST.md  
@docs/GUIDE_TGD.md  
@docs/README.md  
@docs/dev/README.md  
@docs/dev/DEV-GUIDE_Agent-Reports.md  
@docs/dev/DEV-GUIDE_DocFrame-Conventions.md  
@docs/dev/DEV-GUIDE_Services.md

## Verbindliche Beschlüsse (`E1`–`E6` aus `HYPOTHESIS-POST.md`)

| ID | Entscheidung / Vorgabe | Status |
| :-: | :--- | :---: |
| **E1** | **Konzept B mit 6+1 Dateien unter `docs/tgd/` + separates Dev-Profil:** `docs/tgd/README.md` + 6 `NODE_*.md` (inkl. `NODE_GREEN_AUDIT.md`) als universelle QA-Handbücher; projektspezifische `qb-cubie`-Bindungen ausgelagert nach `docs/dev/DEV-GUIDE_TGD-Workflow.md`. | `GEÄNDERT` |
| **E2** | **Kein `presets.py`-Edit in Stufe 1:** `docs/tgd/README.md` wird in `docs/GUIDE_TGD.md`, `docs/README.md` und `docs/dev/README.md` verlinkt. `src/qb_cubie/core/services/doc_frame/presets.py` bleibt unangetastet (`0` Massendiff auf fremden Docs). | `BESTÄTIGT` |
| **E3** | **SSOT-Entschlackung von `docs/GUIDE_TGD.md`:** `GUIDE_TGD.md` behält Epistemologie (Popper/Fallibilismus), Bauprüfer-Analogie, Stützräder-Überblick, 5-Schritte-Übersicht und Single-Shot-Hinweis, verweist für operative Knoten-Details aber eindeutig auf `docs/tgd/` (keine doppelten Checklisten). | `BESTÄTIGT` |
| **E4** | **`DOC_EXCLUDES` / `docs/misc/runs/` erst in Stufe 2:** Die Zielkonvention (`docs/misc/runs/<run-id>/`, 3-Zustands-Lebenszyklus) wird in `docs/dev/DEV-GUIDE_TGD-Workflow.md` beschrieben (mit ehrlichem Hinweis, falls der `DOC_EXCLUDES`-Eintrag noch aussteht); `tests/test_doc_ensurance.py` wird in Stufe 1 **nicht** verändert. | `ZURÜCKGESTELLT (ST. 2)` |
| **E5** | **Option E5a für abgeschlossene Audit-Protokolle:** `NODE_LIVING_DOCS.md` behält die ausnahmefreie Schreibgrenze (kein Zugriff auf Produktivcode oder Test-Verzeichnis); das Aufräumen/Archivieren abgeschlossener Audit-Berichte erfolgt als nachgelagerte Abschluss-Hygiene durch den Orchestrator (konkret in `DEV-GUIDE_TGD-Workflow.md` geregelt). | `BESTÄTIGT` |
| **E6** | **Zwei-Stufen-Gate-Modell (zweigeteilt):** Das abstrakte Prinzip (*harte automatische Gates* vs. *verbindlicher Advisory-Check für vorübergehend pausierte Stil-Gates*) steht universell in `docs/tgd/NODE_PHASE_GREEN.md`; die konkrete `qb-cubie`-Umsetzung (`tests/test_styleguide.py` / `body_lines()`) steht ausschließlich in `docs/dev/DEV-GUIDE_TGD-Workflow.md`. | `BESTÄTIGT` |

## Architektur- & Stilvorgaben für beide Schichten

### Schicht 1 — Universelle QA-Handbücher unter `docs/tgd/` (Einsteiger, Experten & Agenten)

* **Zu erstellende Dateien:**
  * `docs/tgd/README.md` (`CUBIE_DOC_FRAME_3`, `zone="router" mode="table" dir="." recursive="false"`): Universeller TGD-Automaten-Hub mit verständlicher Einführung, Mermaid-Zustandsübergangs-Graph (inkl. `RESOLVED` vs. `REFUTED` und Modus Post-Red-Kritik), gemeinsamen Knoten-Invarianten (abstrakte Pre-Flight-Triage, Rollen- und Kontexttrennung, allgemeiner Artefakt-Lebenszyklus), Verweis auf das `qb-cubie`-Dev-Profil und automatisch sortierter Knoten-Tabelle.
  * 6 Knoten-Handbücher (`CUBIE_DOC_FRAME_1` mit explizitem `order`-Attribut und prägnantem 1-Satz-Summary vor dem ersten `---`):
    1. `docs/tgd/NODE_ANALYSIS.md` (`order="10"`)
    2. `docs/tgd/NODE_HYPOTHESIS.md` (`order="20"`, inkl. *Modus A: Pre-Red* und *Modus B: Post-Red-Kritik*)
    3. `docs/tgd/NODE_PHASE_RED.md` (`order="30"`)
    4. `docs/tgd/NODE_PHASE_GREEN.md` (`order="40"`)
    5. `docs/tgd/NODE_GREEN_AUDIT.md` (`order="50"`, Untertitel als kontrollierter Rücksprung aus Phase Green; Phasen `AUDIT-REPRO → AUDIT-VERDICT → AUDIT-FIX → AUDIT-CLOSE`, Ausgänge `RESOLVED` und `REFUTED`)
    6. `docs/tgd/NODE_LIVING_DOCS.md` (`order="60"`)
* **Einheitliche Mehrschicht-Struktur je `NODE_*.md` (damit Einsteiger, Experten und Agenten denselben Text verlustfrei nutzen können):**
  1. **Knoten-Steckbrief (Schnellreferenz für Agenten & Experten):** Kompakte Übersichtstabelle ganz oben mit *Rolle*, *Eintrittsbedingungen ($P$)*, *Erlaubte Schreibziele*, *Eingefrorene Bereiche (Tabu)*, *Abnahme ($Q$)* und *Folge-Knoten*.
  2. **Wofür dieser Knoten da ist (*Einfach erklärt* & *Für Experten*):** Analog zu `docs/GUIDE_TGD.md` — anschauliche Erklärung bzw. Alltagsbild für Einsteiger sowie epistemologische/methodische Einordnung (Fallibilismus, Hoare-Vertrag, Meta-QA) für Experten.
  3. **Eintritt & Pre-Flight ($P$):** Abstrakte Vorbedingungen, saubere Ausgangslage (Working-Tree-Triage), Prüfung auf Widersprüche im Auftrag.
  4. **Arbeits- & Meta-QA-Heuristiken:** Konkrete, wiederverwendbare Methoden dieses Knotens (z. B. Differenzsignal, Fixture-Hygiene F1–F3, SSOT-Konstanten statt Prosa-Duplikate, unabhängige Audit-Reproduktion, Minimal-Invasivitäts-Prinzip, Code-as-Source-of-Truth).
  5. **Kantenfälle & Eskalationsregeln:** Klare Wenn-Dann-Tabelle (z. B. L4-Regel für rote Living-Docs-Tests in Phase Green, Zwei-Stufen-Gate für pausierte Stilregeln, `RESOLVED` vs. `REFUTED` in `NODE_GREEN_AUDIT`).
  6. **Austrittsbedingungen & Abnahme ($Q$):** Objektive, prüfbare Abschlusskriterien ohne leere Floskeln, plus Verweis auf `docs/dev/DEV-GUIDE_TGD-Workflow.md` für konkrete `qb-cubie`-Kommandos.
* **Striktes Universalitäts-Gebot für `docs/tgd/`:**
  * Verwende durchgängig allgemeine Begriffe (*Quellcode*, *Test-Suite*, *Dokumentation*, *statische Prüfer/Linter*, *pausierte Stil-Gates*, *synthetische Fixtures*, *Living-Docs-Prüfung*, *Arbeits-Tickets*).
  * **Verboten als normative Regel in `docs/tgd/`:** Projektspezifische Interna wie `BUG-006`, `body_lines()`, `presets.py`, `CUBIE_DOC_FRAME_1`/`HEADER_QUICK_NAV`, `docs/misc/runs/`, `docs/misc/lake/`, `tests/test_doc_ensurance.py::DOC_EXCLUDES` oder `qb-cubie`-spezifische CLI-Flags. (Sparsame, klar als *Beispiel* markierte Illustrationen sind zulässig, solange jede Regel ohne `qb-cubie`-Kenntnis vollständig verständlich und anwendbar bleibt.)

### Schicht 2 — Technisches `qb-cubie`-Projekt-Profil (`docs/dev/DEV-GUIDE_TGD-Workflow.md`)

* **Stil:** Auf **technische Klarheit und Effizienz** optimierter Dev-Guide (`CUBIE_DOC_FRAME_1`, konsistent mit `docs/dev/DEV-GUIDE_Services.md` und `docs/dev/DEV-GUIDE_Agent-Reports.md`).
* **Inhalt (alle `qb-cubie`-spezifischen Bindungen aus `HYPOTHESIS-POST.md`, SSOT):**
  1. **Knoten-Kommando-Matrix:** Konkretes Mapping der sechs Knoten aus `docs/tgd/` auf `qb-cubie`-Pfade (`src/`, `tests/`, `docs/`) und reale Abnahmekommandos (`git status --short`, `git diff --name-only`, `pytest`, `ruff`, `pylint`, `mypy --warn-unreachable`, `qb-cubie docframe update/check`, `qb-cubie docensurance check`).
  2. **Advisory-Check für pausierte Stil-Gates:** Konkrete Handhabung pausierter `tests/test_styleguide.py`-Regeln (aktuell `test_function_size` / `BUG-006` via `body_lines()`-Check auf neuen/geänderten `src/`-Dateien).
  3. **Kanonisches 5-Block-Minimal-Ticket (`GEMINI*.md`):** Vorlage inklusive `E1..En`-Bestätigungstabelle, optionaler 1-Zeilen-`Ticket-Herkunft` und Anti-Copy-Paste-Regel.
  4. **Ablage- & 3-Zustands-Artefakt-Lebenszyklus:** Konkrete Pfade und Regeln für Tickets (Ziel: `docs/misc/runs/<run-id>/`, Hinweis auf noch ausstehende `DOC_EXCLUDES`-Ergänzung in Stufe 2), `ANALYSIS*.md`/`HYPOTHESIS*.md` (`CUBIE_DOC_FRAME_2`, Archiv `docs/misc/lake/`), `AGENT_REPORT*`/`TGD_*` sowie `tests/GREEN_AUDIT.md` (Single-Active-Signal-Invariante, Option E5a).
  5. **Prozess-Mutanten-Referenz (`PM1`–`PM8`):** Kompakte Referenz-Tabelle der 8 Mutanten aus `HYPOTHESIS-POST.md` gemappt auf Knoten-Handbuch und konkretes `qb-cubie`-Prüf-Gate.

### Schicht 3 — SSOT-Synchronisation bestehender Übersichtsdokumente

* **`docs/GUIDE_TGD.md`:** Gemäß `E3` gezielt verschlanken und sauber auf `docs/tgd/README.md` sowie die sechs Knoten-Handbücher verlinken (Epistemologie, Einsteiger-Analogie, Stützräder-Überblick, Kurzreferenz und `[!TIP]`-Hinweise bleiben vollständig erhalten; doppelte operative Detail-Checklisten verweisen auf `docs/tgd/`).
* **`docs/README.md` & `docs/dev/README.md`:** Verlinkung bzw. `DocFrame`-Synchronisation für `docs/tgd/README.md` und `docs/dev/DEV-GUIDE_TGD-Workflow.md`.

## Leitplanken & Abnahme-Gates

* **Pre-Flight:** Prüfe zuerst `git status --short`. Nur das vorab angelegte Ticket `docs/services/GEMINI-12.md` darf lokal vorhanden sein; bei fremden Änderungen in `src/` oder `tests/` sofort stoppen.
* **Schreibgrenze (`docs/` only):** Bearbeitet werden ausschließlich Dokumentationsdateien unter `docs/` (`docs/tgd/**`, `docs/dev/DEV-GUIDE_TGD-Workflow.md`, `docs/GUIDE_TGD.md`, `docs/README.md`, `docs/dev/README.md`). **`src/` und `tests/` bleiben zu 100 % unverändert.**
* **`DocEnsurance`- & `DocFrame`-Schutz:** Verwende für nicht ausführbare Templates, Skizzen und Ticket-Beispiele strikt ````text````, ````markdown```` (bei verschachtelten Fences vier Backticks) oder ````mermaid```` — niemals nicht-ausführbare ````python````-Blöcke. Schütze beispielhafte `<!-- qb:frame ... -->`-Tags immer innerhalb von Code-Fences.
* **Universalitäts-Selbstprüfung:** Verifiziere vor Abschluss explizit, dass in `docs/tgd/*.md` keine projektspezifischen Interna (`BUG-006`, `body_lines`, `presets.py`, `docs/misc/runs`, `DOC_EXCLUDES`) als normative Regeln stehen und dass Einsteiger-Erklärungen, Experten-Tiefe sowie Agenten-Steckbriefe sauber ineinandergreifen.
* **Verifikation:**
  1. `qb-cubie docframe update` auf `docs/tgd/`, `docs/dev/DEV-GUIDE_TGD-Workflow.md`, `docs/dev/README.md`, `docs/GUIDE_TGD.md` und `docs/README.md` (2. Lauf zwingend idempotent: `Updated 0 file(s)`).
  2. `qb-cubie docframe check` und `qb-cubie docensurance check` auf allen neuen und geänderten Dokumenten (Exit-Code `0`, `0` Diagnosen).
  3. Vollständige Doku-Gates: `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` (Exit-Code `0`).
  4. Schreibgrenzen-Nachweis über `git status -s` (`0` Änderungen unter `src/` und `tests/`).

---

## Auftrag

* Umsetzung Stufe 1 (Dokumentations-Authoring & Verifikation): Erstellung der universellen TGD-Knoten-Handbücher unter `docs/tgd/`, des technischen `qb-cubie`-Profils unter `docs/dev/DEV-GUIDE_TGD-Workflow.md` sowie SSOT-Synchronisation von `docs/GUIDE_TGD.md`, `docs/README.md` und `docs/dev/README.md`.

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | Service-Core | ↤](./GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->