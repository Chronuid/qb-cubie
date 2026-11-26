<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Gemini-App" model="Gemini 4 Neon" effort="High" -->
# GEMINI-13: Umsetzung (Stufe 2) — Living-Docs, Ticket-Entkopplung, L9-Artefakt-Hygiene & Feinschliff

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** High
- **Erstellungsdatum:** 26. November 2026, ~18:05 (CET)
- **Synthesebasis:** `docs/tgd/README.md`, `docs/tgd/NODE_*.md`, `docs/services/HYPOTHESIS-POST.md`, `docs/services/ANALYSIS-POST.md`, `docs/services/GEMINI-12.md`, unsere gemeinsame Konversation in der Gemini-App sowie für Antigravity-CLI nicht im Detail einsehbare Informationen aus dem Memory-System der Gemini-App. In dieser Konversation durfte die Gemini-App (`Gemini 4 Neon`, Effort `High`) bereits den überarbeiteten Ablauf-Abschnitt von `GEMINI-8.md` sowie die Erstentwürfe für `GEMINI-9.md`, `GEMINI-10.md`, `GEMINI-11.md`, `GEMINI-12.md` und dieses Dokument (`GEMINI-13.md`) formulieren; der Nutzer hat diese Entwürfe vor der Übergabe an Antigravity-CLI jeweils noch um einige für die Gemini-App unbekannte kleine Details mutiert.
- **Stand:** qb-cubie (`v0.1.1`, Branch `main`, Commit `60236168`; direkter Zugriff auf Working Tree / Git in der Gemini-App nicht vorhanden)
- **Git-Log:** `60236168` ("... gave birth to a series of TGD guides ...")

---

```text
commit 60236168 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 26 2026

    ... gave birth to a series of TGD guides ...

Auftrag (docs/services/GEMINI-13.md — erstellt in Gemini-App):
- Umsetzung Stufe 2 (Living-Docs & Abschluss-Hygiene): Ticket-Entkopplung über
  DOC_EXCLUDES (E4), Anwendung des 3-Zustands-Lebenszyklus auf die L9-Artefakte
  und tests/GREEN_AUDIT.md (E5a), Universalitäts-Feinschliff in docs/tgd/ sowie
  Aktualisierung von DEV-GUIDE_TGD-Workflow.md und betroffenen Querverweisen.
- Scope: Dokumentations- & Hygiene-Schnitt unter docs/ mit zwei explizit
  freigegebenen Minimal-Eingriffen unter tests/ (src/ bleibt zu 100 % unverändert).
```
<!-- /qb:frame -->

# Ziel

Abschluss der TGD-Handbuch-Einführung (Stufe 2): Entkopplung künftiger Arbeits-Tickets über `DOC_EXCLUDES`, Bereinigung und Archivierung der abgeschlossenen L9-Arbeitsartefakte (einschließlich `tests/GREEN_AUDIT.md`), Universalitäts-Feinschliff an `docs/tgd/` sowie vollständige Synchronisation und Verifikation aller betroffenen Dokumentationen.

## Kontext

In Stufe 1 (`60236168`) wurden die sechs universellen Knoten-Handbücher plus Automaten-Hub unter `docs/tgd/` sowie das technische Projekt-Profil `docs/dev/DEV-GUIDE_TGD-Workflow.md` erfolgreich aufgebaut. Nun bereinigt Stufe 2 das Repository gemäß dem neuen 3-Zustands-Lebenszyklus, setzt die zurückgestellte Ticket-Entkopplung (`E4`) um, glättet kleine sprachliche Restspuren in `docs/tgd/` und bereitet eine saubere Ausgangsbasis für künftige TGD-Läufe (kontinuierliche Bewährung im Alltag).

## Weiteres

@docs/tgd/README.md  
@docs/tgd/NODE_LIVING_DOCS.md  
@docs/dev/DEV-GUIDE_TGD-Workflow.md  
@docs/services/HYPOTHESIS-POST.md  
@tests/test_doc_ensurance.py  
@tests/test_doc_frame.py  
@tests/GREEN_AUDIT.md

## Verbindliche Beschlüsse & explizite Schreibgrenzen-Ausnahmen

| ID | Entscheidung / Vorgabe | Status |
| :-: | :--- | :---: |
| **E2** | **Kein `presets.py`-Edit:** `src/qb_cubie/core/services/doc_frame/presets.py` bleibt unverändert (`src = 0`). | `BESTÄTIGT` |
| **E4** | **Ticket-Entkopplung umsetzen:** `docs/misc/runs` wird in `tests/test_doc_ensurance.py::DOC_EXCLUDES` aufgenommen (inkl. Prüfung, ob `tests/test_doc_frame.py` dieselbe Konstante nutzt). | `BESTÄTIGT` |
| **E5a** | **Abschluss-Hygiene für `tests/GREEN_AUDIT.md`:** Das abgeschlossene Audit-Protokoll (`Status: RESOLVED`) wird als historischer Beleg des ersten autonomen Audit-Laufs nach `docs/misc/lake/GREEN_AUDIT_SERVICE-CORE-Z2.md` verschoben (stellt die Single-Active-Signal-Invariante in `tests/` wieder her). | `BESTÄTIGT` |

* **Explizite Ausnahme zur Schreibgrenze von `NODE_LIVING_DOCS.md`:** Abweichend von der regulären `tests = 0`-Regel sind in diesem kombinierten Living-Docs- und Hygiene-Schnitt exakt **zwei** Operationen unter `tests/` freigegeben:
  1. Aufnahme von `"docs/misc/runs"` in `DOC_EXCLUDES` in `tests/test_doc_ensurance.py` (falls `tests/test_doc_frame.py` eine eigene Ausschlussliste pflegt, dort analog angleichen).
  2. Verschieben/Archivieren von `tests/GREEN_AUDIT.md` nach `docs/misc/lake/GREEN_AUDIT_SERVICE-CORE-Z2.md`.
* **Strikt eingefroren (Tabu):** Das gesamte Verzeichnis `src/` (`0` Änderungen) sowie alle übrigen Testdateien unter `tests/**/*.py`.

## Arbeits-Schwerpunkte

### 1. Ticket-Entkopplung (`E4`)
* Ergänze `"docs/misc/runs"` in `tests/test_doc_ensurance.py::DOC_EXCLUDES` (und prüfe, dass `tests/test_doc_frame.py` denselben Ausschluss übernimmt).
* Optional: Lege eine kurze, knappe `docs/misc/runs/README.md` (ohne `DocFrame`, da ausgeschlossen) an, die den Zweck des Arbeitsordners für aktive Minimal-Tickets in 3–5 Zeilen festhält.

### 2. L9-Artefakt-Hygiene (3-Zustands-Lebenszyklus anwenden)
* **Archivwürdige Grundsatzberichte nach `docs/misc/lake/` verschieben** (mit sprechenden Namen, konsistent zu den dort bestehenden Dateien wie `ANALYSIS_COVERAGE_OPTIONS.md`):
  * `docs/services/ANALYSIS.md` $\to$ `docs/misc/lake/ANALYSIS_SERVICE-CORE.md`
  * `docs/services/HYPOTHESIS.md` $\to$ `docs/misc/lake/HYPOTHESIS_SERVICE-CORE.md`
  * `docs/services/ANALYSIS-POST.md` $\to$ `docs/misc/lake/ANALYSIS_TGD-EXPERIMENTS.md`
  * `docs/services/HYPOTHESIS-POST.md` $\to$ `docs/misc/lake/HYPOTHESIS_TGD-NODES.md`
  * `tests/GREEN_AUDIT.md` $\to$ `docs/misc/lake/GREEN_AUDIT_SERVICE-CORE-Z2.md`
* **Abgeschlossene Auftrags-Tickets bereinigen:** Entferne die erledigten Durchlauf-Tickets `docs/services/GEMINI-1.md` bis `docs/services/GEMINI-12.md` (die Git-Historie bewahrt den vollständigen Verlauf). Lasse dieses laufende Übergangs-Ticket `docs/services/GEMINI-13.md` als Klasse-1-Ticket zunächst unverändert (es kann nach Abschluss vom Nutzer entfernt werden).
* **Keine toten Links hinterlassen:** Prüfe alle verbleibenden Dokumente unter `docs/` (insb. `docs/services/GUIDE_Service-Core.md`, `docs/dev/DEV-GUIDE_TGD-Workflow.md`, `docs/README.md`, `docs/misc/README.md`) auf Verweise, die noch auf die verschobenen Pfade unter `docs/services/` oder `tests/GREEN_AUDIT.md` zeigen, und aktualisiere oder bereinige sie sauber.

### 3. Dokumentations-Aktualisierung & Universalitäts-Feinschliff
* **Projekt-Jargon in `docs/tgd/` glätten:** Ersetze den noch verbliebenen historischen Lauf-Begriff **„L4-Muster“** in `docs/tgd/NODE_PHASE_GREEN.md` und `docs/tgd/NODE_LIVING_DOCS.md` durch eine selbsterklärende, projektneutrale Bezeichnung (z. B. *Diagnose-statt-Edit-Regel* bzw. *Handoff-Prinzip*).
* **Kurz-Review aller `docs/tgd/*.md`:** Prüfe alle sieben Dateien unter `docs/tgd/` auf eventuelle weitere unbeabsichtigte interne Kürzel, unklare Querverweise oder kleine sprachliche Unebenheiten und schleife sie behutsam nach (ohne die bewährte Struktur oder den einsteiger- und agentenfreundlichen Stil aufzubrechen).
* **`docs/dev/DEV-GUIDE_TGD-Workflow.md` auf den realen Stand heben:** Entferne den Stufe-1-Vorbehalt, dass `docs/misc/runs` noch nicht in `DOC_EXCLUDES` eingetragen sei, und spiegele den nun aktiven Zustand (inkl. der realen `docs/misc/lake/`-Konvention und der `Single-Active-Signal`-Regel für `tests/GREEN_AUDIT.md`) exakt nach dem Prinzip *Code als Wahrheitsquelle*.
* **Prüfung angrenzender Indizes:** Prüfe `docs/README.md`, `docs/dev/README.md`, `docs/misc/README.md` und `docs/GUIDE_TGD.md` auf konsistente Verlinkungen und aktuelle Kurzbeschreibungen.

## Leitplanken & Abnahme-Gates ($Q$)

1. **Pre-Flight:** `git status --short` prüfen — nur `docs/services/GEMINI-13.md` darf lokal als Klasse-1-Ticket vorliegen; bei fremden Änderungen sofort stoppen.
2. **Statische Hygiene auf geänderter Testdatei:** `.venv/bin/ruff check tests/test_doc_ensurance.py` und `MYPYPATH=src .venv/bin/mypy tests/test_doc_ensurance.py` melden `0` Fehler (analog für `tests/test_doc_frame.py`, falls berührt).
3. **Idempotente Rahmen-Synchronisation:** `.venv/bin/python -m qb_cubie docframe update` über die geänderten/betroffenen Dokumente (2. Lauf zwingend idempotent: `Updated 0 file(s); all frames up to date.`).
4. **Vollständige Doku-Gates:** `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` läuft mit Exit-Code `0` und `0` Diagnosen durch.
5. **Schreibgrenzen-Nachweis:** `git status -s` bestätigt `0` Änderungen unter `src/`, unter `tests/` ausschließlich den `DOC_EXCLUDES`-Edit sowie das entfernte `tests/GREEN_AUDIT.md`, und ein sauber aufgeräumtes `docs/services/` (nur dauerhafte `GUIDE_*.md`-Handbücher zzgl. laufendem `GEMINI-13.md`).

---

## Auftrag

* Umsetzung Stufe 2 (`LIVING_DOCS` + explizit freigegebene Abschluss-Hygiene): Ticket-Entkopplung (`E4`), L9-Artefakt-Hygiene & `GREEN_AUDIT`-Archivierung (`E5a`), Universalitäts-Feinschliff in `docs/tgd/` sowie Synchronisation von `DEV-GUIDE_TGD-Workflow.md` und allen betroffenen Dokumentationen.

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