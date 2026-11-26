<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GEMINI

![Cubie](../.assets/cubie-logo-written.png)

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

# Ziel

Empirische Git- und Artefakt-Analyse der bisherigen TGD-Versuchsreihe (ab dem Sprint zu `v0.0.3` bis zum aktuellen `HEAD`) mit Fokus auf dem jüngsten Service-Core-Lauf, um eine belastbare Datengrundlage für knotenspezifische TGD-Handbücher zu gewinnen.

## Kontext

Bislang stützt sich die agentengestützte Entwicklung in `qb-cubie` auf das allgemeine Handbuch `docs/GUIDE_TGD.md` sowie auf zustandslos orchestrierte Einzelschritte (`GEMINI*.md`-Aufträge mit Kontext-Reset via `/clear` pro Knoten). Diese Versuchsreihe läuft bereits seit dem Release-Sprint zu `v0.0.3`; ein Großteil der zugehörigen `GEMINI*.md`-, `ANALYSIS*.md`-, `HYPOTHESIS*.md`- und `GREEN_AUDIT*.md` sowie `AGENT_REPORT*.md`-Artefakte liegt heute über die Git-Historie verteilt (teilweise verschoben oder in späteren Commits wieder bereinigt).

Im aktuellsten Durchlauf (Aufbau des neuen Service-Cores im Doppelzyklus) kam es zudem erstmals zu einem vollständig autonom ausgelösten `GREEN_AUDIT`-Event inklusive anschließendem Mikro-TGD-Rücksprung in die Phase Red. Um künftig für jeden einzelnen Knoten des TGD-Prozesses ein präzises, direkt referenzierbares Handbuch zu formulieren, sollen zunächst alle empirischen Befunde dieser Versuchsreihe systematisch ans Licht geholt und strukturiert ausgewertet werden.

## Weiteres

@docs/GUIDE_TGD.md  
@docs/dev/DEV-GUIDE_Agent-Reports.md  
@docs/services/ANALYSIS.md  
@docs/services/HYPOTHESIS.md  
@tests/GREEN_AUDIT.md

## Analyse-Schwerpunkte

1. **Git-Archäologie der Versuchsreihe (`v0.0.3`-Sprint bis `HEAD`):**
   * Durchsuche die gesamte Git-Historie (einschließlich umbenannter, verschobener und zwischenzeitlich gelöschter Dateien über `git log --all` / `--full-history` und `git show <commit>:<pfad>`) nach allen `GEMINI*.md`-, `ANALYSIS*.md`-, `HYPOTHESIS*.md`- und `GREEN_AUDIT*.md`-Artefakten sowie zugehörigen Commits.
   * Rekonstruiere eine chronologische Übersicht der identifizierten TGD-Läufe (Zeitraum/Commits, Zielsetzung, durchlaufene Knoten-Sequenz, Grad der Autonomie vs. manuelle Eingriffe, beobachtete Evolution der Prompt- und Prozessmuster).
2. **Tiefenvermessung des aktuellsten Laufs (Service-Core-Doppelzyklus):**
   * Rekonstruiere den vollständigen Zustandsverlauf des Service-Core-Experiments von `ANALYSIS` über `HYPOTHESIS`, Zyklus 1 (`Red → Green → Living-Docs`), Zyklus 2 (`Red → Green`), das autonome `GREEN_AUDIT`-Event, den Mikro-TGD-Rücksprung in `PHASE_RED` bis zum abschließenden `Living-Docs`-Stand.
   * Analysiere konkret: Welche Leitplanken und Referenzen in den `GEMINI-*.md`-Dokumenten haben sauber getragen? Wo entstanden Reibungen, Begriffsambiguitäten (z. B. Makro- vs. Mikro-TGD), Plan-vs.-Code-Drift oder unerwartete Rückkopplungen? Welche Qualitätsmuster haben sich implizit übertragen (auch dort, wo einzelne Gates wie das 12-Zeilen-Limit geskippt waren)?
3. **Empirische Rohdaten je TGD-Knoten (Anforderungsprofil für künftige Knoten-Handbücher):**
   * Verdichte die historischen und aktuellen Befunde systematisch für jeden Knoten des TGD-Automaten:
     * `ANALYSIS` *(Stützrad 1)*
     * `HYPOTHESIS` *(Stützrad 2)*
     * `PHASE_RED` *(Regulärer Testaufbau & Freeze)*
     * `PHASE_GREEN` *(Implementierung, Freeze-Disziplin & Audit-Auslösung)*
     * `GREEN_AUDIT` & Rücksprung (`GREEN_AUDIT → PHASE_RED` als Mikro-TGD-Zyklus)
     * `PHASE_LIVING_DOCS` *(Dokumentations-Synchronisation & Code-as-Source-of-Truth)*
   * Erhebe pro Knoten anhand konkreter Belege aus der Historie:
     1. **Eintrittsbedingungen & Pflicht-Artefakte ($P$):** Was muss vorliegen, damit ein frischer `/clear`-Kontext den Knoten sicher ausführen kann?
     2. **Schreibgrenzen & Verbote:** Welche Verzeichnisse/Artefakte sind beschreibbar, welche strikt eingefroren?
     3. **Bewährte Arbeits- & Meta-QA-Heuristiken:** Welche Prüfmethoden haben nachweislich Fehler abgefangen (z. B. Mutanten-Matrix, Subprozess-Blocker, Falsifikation von Audit-Berichten)?
     4. **Typische Fehlerbilder, Kantenfälle & Eskalationspfade:** Was ist real schiefgegangen oder beinahe schiefgegangen (z. B. synthetische Fixtures, Doku-Drift, übersehene Scope-Grenzen)?
     5. **Austrittsbedingungen & Abnahme-Gates ($Q$):** Woran ist eindeutig erkennbar, dass der Knoten abgeschlossen ist?
4. **Orchestrierung & Artefakt-Lebenszyklus:**
   * Bewerte auf Basis der Historie, welche Minimalstruktur ein knotenspezifisches Auftragsdokument (`GEMINI*.md`) benötigt, wenn die Knoten-Regeln künftig in eigene Handbücher ausgelagert werden, und dokumentiere beobachtete Muster im Umgang mit temporären TGD-Artefakten (Verbleib, Archivierung, Bereinigung).

## Leitplanken

* **Strikter Analyse-Scope (`ANALYSIS`):** Rein lesende Bestandsaufnahme. Produktivcode unter `src/`, Testcode unter `tests/` sowie bestehende Handbücher bleiben vollständig unverändert.
* **Ausgabe-Artefakt:** Erstelle genau einen konsolidierten Analysebericht (`ANALYSIS-POST.md` im Zielordner dieses Auftrags) im `CUBIE_DOC_FRAME_2`-Format gemäß `docs/dev/DEV-GUIDE_Agent-Reports.md`.
* **Evidenzpflicht & Fallibilismus:** Belege jeden historischen Befund mit konkretem Commit-Hash und Dateipfad. Trenne strikt zwischen beobachteten Fakten (*Ist*) und ersten abgeleiteten Gestaltungshinweisen (*Hypothese*). Markiere Lücken in der Git-Historie (z. B. nicht committete Zwischenschritte oder manuelle `/clear`-Eingriffe ohne Commit-Spur) explizit statt sie zu extrapolieren.
* **Verifikation:** Synchronisiere den Dokumentrahmen des neu erstellten `ANALYSIS.md` mit `DocFrame` und prüfe das Dokument gezielt mit `DocFrame` und `DocEnsurance`.

---

## Auftrag

* Stützrad 1 (`ANALYSIS`): Historische & empirische Vermessung der TGD-Versuchsreihe (`v0.0.3` bis `HEAD`) als Datengrundlage für knotenspezifische TGD-Handbücher.

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