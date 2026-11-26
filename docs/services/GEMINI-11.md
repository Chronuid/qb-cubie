<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Gemini-App" model="Gemini 4 Neon" effort="High" -->
# GEMINI-11: Hypothesen-Auftrag für knotenspezifische TGD-Handbücher (`docs/tgd/`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** High
- **Erstellungsdatum:** 26. November 2026, ~16:15 (CET)
- **Synthesebasis:** `docs/services/ANALYSIS-POST.md`, `docs/GUIDE_TGD.md`, `docs/services/HYPOTHESIS.md`, `tests/GREEN_AUDIT.md`, unsere gemeinsame Konversation in der Gemini-App sowie für Antigravity-CLI nicht im Detail einsehbare Informationen aus dem Memory-System der Gemini-App. In dieser Konversation durfte die Gemini-App (`Gemini 4 Neon`, Effort `High`) bereits den überarbeiteten Ablauf-Abschnitt von `GEMINI-8.md` sowie die Erstentwürfe für `GEMINI-9.md`, `GEMINI-10.md` und dieses Dokument (`GEMINI-11.md`) formulieren; der Nutzer hat diese Entwürfe vor der Übergabe an Antigravity-CLI jeweils noch um einige für die Gemini-App unbekannte kleine Details mutiert.
- **Stand:** qb-cubie (`v0.1.1`, Branch `main`, Commit `1a19dc09` gemäß `docs/services/ANALYSIS-POST.md`; direkter Zugriff auf Working Tree / Git in der Gemini-App nicht vorhanden)
- **Git-Log:** `2d512e14` ("... Analyzed the current series of TGD experiments ...")

---

```text
commit 2d512e14a77f833958c848fd1b17272db384e805 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 26 16:07:17 2026 +0100

    ... Analyzed the current series of TGD experiments ...

Auftrag (docs/services/GEMINI-11.md — erstellt in Gemini-App):
- Stützrad 2 (HYPOTHESIS): Konzeption, Architektur-Hypothesen, Gegenmodelle,
  Meta-QA-Prüfung und offene Entscheidungsmatrix für knotenspezifische
  TGD-Handbücher unter docs/tgd/ auf Basis von docs/services/ANALYSIS-POST.md.
- Scope: Rein konzeptionelle Hypothesenbildung (kein Produktivcode unter src/,
  kein Testcode unter tests/, keine Änderungen an bestehenden Handbüchern).

```

# Ziel

Hypothetisierung eines tragfähigen, modularen Konzepts für knotenspezifische TGD-Handbücher unter **`docs/tgd/`** sowie eines standardisierten Minimal-Orchestrierungs- und Artefakt-Lebenszyklus auf empirischer Basis von `docs/services/ANALYSIS-POST.md`.

## Kontext

Die empirische Git- und Artefakt-Vermessung in `docs/services/ANALYSIS-POST.md` (Läufe `L0`–`L9`, Schwerpunkt Service-Core-Doppelzyklus `L9`) hat gezeigt, dass die zustandslose Knoten-Orchestrierung mit Kontext-Reset (`/clear`) pro Schritt und kurzen Auftragsdokumenten (`GEMINI-*.md`) hochwirksam ist — jedoch sofort wieder lange Inline-Leitplanken benötigt, sobald knotenspezifische Regeln (wie der Mikro-TGD-Rücksprung nach einem `GREEN_AUDIT`-Event, die `Code-as-Source-of-Truth`-Pflicht in `PHASE_LIVING_DOCS` oder Pre-Flight- und Schreibgrenzen-Regeln) nicht in dedizierten Handbüchern kodifiziert sind.

Ziel der neuen Handbuch-Reihe unter **`docs/tgd/`** ist es, künftig in jedem Knoten der TGD-Zustandsmaschine genau das passende Knoten-Handbuch referenzieren zu können, sodass Auftragsdokumente (`GEMINI*.md`) schlank und fehlerresistent bleiben, Copy-Paste-Drift vermieden wird und jeder frische Agenten-Kontext eindeutige Eintrittsbedingungen ($P$), Schreibgrenzen, Meta-QA-Heuristiken, Eskalationspfade und Austrittsbedingungen ($Q$) vorfindet.

## Weiteres

@docs/services/ANALYSIS-POST.md

@docs/GUIDE_TGD.md

@docs/dev/DEV-GUIDE_Agent-Reports.md

@docs/dev/DEV-GUIDE_DocFrame-Conventions.md

@docs/dev/DEV-GUIDE_Services.md

@docs/services/HYPOTHESIS.md

@tests/GREEN_AUDIT.md

## Hypothesen-Schwerpunkte

Arbeite auf Grundlage der empirischen Befunde und der fünf Leitfragen aus `docs/services/ANALYSIS-POST.md` (§3–§5) ein falsifizierbares Hypothesensystem aus:

1. **Makro-Konzeptvergleich (Konzept A vs. B vs. C) & SSOT-Rolle von `docs/GUIDE_TGD.md`:**
* Vergleiche drei strukturell unterschiedliche Design-Konzepte für `docs/tgd/` in einer Entscheidungsmatrix (z. B. minimalistische Checklisten-Karten vs. schichtsaubere Zustandsautomaten-Handbücher mit `GUIDE_TGD.md` als schlankem Übersichts-Hub vs. stark formalisierte Template-/Meta-Gate-Spezifikation).
* Kläre die klare Rollenverteilung und Redundanzfreiheit (Single Source of Truth) zwischen `docs/GUIDE_TGD.md` (Einstieg, Epistemologie, Überblick) und `docs/tgd/*.md` (operative Knoten-Verträge) sowie die Einbindung in die `DocFrame`-Navigation (`docs/tgd/README.md`, Router, Presets).


2. **Knoten-Topologie, Automaten-Übergänge & `GREEN_AUDIT`-Semantik (Leitfrage 1):**
* Formuliere die Ziel-Topologie und Benennungskonvention unter `docs/tgd/` für alle sechs erhobenen Knoten (`ANALYSIS`, `HYPOTHESIS` inkl. Sonderfall Post-Red-Kritik aus `L3`, `PHASE_RED`, `PHASE_GREEN`, `GREEN_AUDIT`-Rücksprung, `PHASE_LIVING_DOCS`) inklusive eines eindeutigen Zustandsübergangs-Graphen.
* Löse die in `GEMINI-8.md` / `b7f1c87c` beobachtete Begriffsambiguität zwischen Makro-`PHASE_RED` und Mikro-TGD (`MICRO-GREEN` / direktes `PASSED` nach Fixture-Fix) sauber auf und modelliere beide Ausgänge explizit: **`RESOLVED` $\to$ `PHASE_LIVING_DOCS**` sowie den bisher noch nicht empirisch eingetretenen Pfad **`REFUTED` $\to$ `PHASE_GREEN**`.


3. **Verbindliche Knoten-Invarianten & Abwehr realer Fehlerbilder (Leitfragen 2, 3 & 4):**
* Definiere ein einheitliches Vertragsschema pro Knoten-Handbuch: Pre-Flight & Eintrittsbedingungen ($P$), harte Schreibgrenzen, Arbeits- & Meta-QA-Heuristiken, Kantenfälle/Eskalation und Austrittsbedingungen ($Q$).
* Nimm begründet Stellung zu den drei empirischen Konfliktstellen aus `ANALYSIS-POST.md`:
1. **Rote Living-Docs-Tests in `PHASE_GREEN`:** L4-Muster (`docs/` strikt unberührt, Übergabe an `PHASE_LIVING_DOCS`) vs. L9-Z1-Muster (`277a188d`: 46 `.md`-Dateien mitgepflegt).
2. **Pre-Flight-Gate (`git status --short`):** Wie verhindern die Handbücher unbemerkte Working-Tree-Altlasten (`4c949c34`: `presets.py`) und das Vermischen vorab angelegter Folge-Prompts (`GEMINI-(n+1).md`)?
3. **Pausierte Gates & Fixture-Hygiene:** Unterscheidung zwischen harten Gates und pausierten Stil-Checks (`test_function_size` / `BUG-006`) sowie verbindliche `PHASE_RED`-Regeln gegen unterdeckte synthetische Fixtures (`_seed_docframe_workspace`) und duplizierte Prosa-Fixtures (`BUG-007`).




4. **Minimal-Ticket (`GEMINI*.md`) & Artefakt-Lebenszyklus (Leitfrage 5):**
* Entwirf das standardisierte Minimal-Format für künftige Auftragsdokumente (`GEMINI*.md`) inklusive verbindlicher Bestätigungstabelle für offene Entscheidungen (`E1..En` statt losem `"Ok."`) und Schutz gegen Copy-Paste-Ziel-Drift (`GEMINI-4.md:27`).
* Entwirf eine konsistente Ablage-, `DocFrame`-Entkopplungs- (`DOC_EXCLUDES` vs. Arbeitsordner) und Bereinigungs- bzw. Archivierungsregel (`docs/misc/lake/` vs. Cleanup in `PHASE_LIVING_DOCS`) für `GEMINI*.md`, `ANALYSIS*.md`, `HYPOTHESIS*.md`, `AGENT_REPORT*.md` und `tests/GREEN_AUDIT.md`.


5. **Meta-QA & Prozess-Mutanten-Matrix vor Umsetzung:**
* Übertrage die Meta-QA-Prüfung aus `docs/GUIDE_TGD.md` auf die neue Handbuch-Reihe selbst: Wie werden Widersprüche zwischen `GUIDE_TGD.md` und `docs/tgd/*`, leere Floskeln, `DocEnsurance`-Fallen (````python` vs. ````text`) und tote `DocFrame`-Routen ausgeschlossen?
* Erstelle eine **Prozess-Mutanten-Matrix (`PM1`–`PM8`)** konkreter historischer oder denkbarer Agenten-Fehlverhalten (z. B. stilles Test-Hacking, blindes Abnicken eines `GREEN_AUDIT`, `docs/`-Schreibbruch in Green, Übernahme veralteter `HYPOTHESIS`-Signaturen in Living-Docs) mit dem jeweiligen Handbuch-Vertrag bzw. Prüf-Gate, das den Mutanten deterministisch abfängt.
* Schließe mit einer strukturierten Tabelle **offener Design-Entscheidungen (`E1..En`)** und einer konkreten, inkrementellen Umsetzungs-Roadmap ab.



## Leitplanken

* **Strikter `HYPOTHESIS`-Scope:** Rein konzeptionelle Phase. Produktivcode unter `src/`, Testcode unter `tests/` sowie bestehende Handbücher (`docs/GUIDE_*.md`, `docs/dev/*.md`, `docs/services/GUIDE_*.md`) bleiben vollständig unverändert.
* **Ausgabe-Artefakt:** Erstelle genau ein konsolidiertes Hypothesen-Dokument unter **`docs/services/HYPOTHESIS-POST.md`** im `CUBIE_DOC_FRAME_2`-Format gemäß `docs/dev/DEV-GUIDE_Agent-Reports.md` (orientiert am Qualitätsniveau von `docs/services/HYPOTHESIS.md`).
* **Wissenschaftliche Sprache (Fallibilismus nach Popper):** Trenne strikt zwischen belegten `Ist`-Befunden (mit Referenz auf `ANALYSIS-POST.md` bzw. reale Repo-Dateien), `Hypothese`, `Gegenhypothese / Risiko` und objektivem `Falsifikationskriterium`. Verwende für nicht ausführbare Skizzen/Beispiele strikt ````text` oder ````markdown` (niemals nicht-ausführbare ````python`-Blöcke), damit `DocEnsurance` fehlerfrei bleibt.
* **Verifikation:** Synchronisiere `docs/services/HYPOTHESIS-POST.md` idempotent mit `qb-cubie docframe update`, prüfe das Dokument gezielt mit `qb-cubie docframe check` und `qb-cubie docensurance check` und belege die eingehaltene Schreibgrenze über `git status -s`.

---

## Auftrag

* Stützrad 2 (`HYPOTHESIS`): Konzeption & Architektur-Hypothesen für die modulare TGD-Knoten-Handbuchreihe unter `docs/tgd/` auf Basis von `docs/services/ANALYSIS-POST.md`.

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
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->