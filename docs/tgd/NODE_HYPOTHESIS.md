<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="20" -->
<div align="center">

# Knoten: HYPOTHESIS (Falsifizierbares Design & Meta-QA)

![Cubie](../.assets/cubie-logo-written.png)

Falsifizierbarer Entwurf und Meta-QA-Prüfung (optionales Stützrad 2, in jedem Knoten zuschaltbar): Entwickelt konkurrierende Lösungsmodelle, Fehler-/Mutanten-Matrizen und entscheidungsreife Beschlüsse mit Standard-Empfehlungen (Consent-by-Exception) — vor dem Prüfaufbau, zur Prüfkritik oder bei komplexen Weichenstellungen.

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

## 1. Knoten-Steckbrief

| Eigenschaft | Verbindliche Festlegung |
| :--- | :--- |
| **Rolle** | Optionales Stützrad 2 (frei positionierbar im Baukasten) — falsifizierbarer Lösungsentwurf, Vier-Säulen-Meta-QA & Entscheidungs-Vorbereitung |
| **Eintrittsbedingungen ($P$)** | *Modus A (Pre-Red-Entwurf):* Vorliegende Ist-Grundlage (z. B. aus `ANALYSIS` oder direkt aus dem Bestand) und relevante Handbücher. *Modus B (Post-Red-Kritik):* Erster Entwurf der Prüfkriterien/Tests aus `PHASE_RED` zur kritischen Härtung. *Situativ:* Komplexe Abwägung aus einem anderen Knoten. Plus saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell). |
| **Erlaubte Schreibziele** | Ausschließlich der designierte Hypothesenbericht (auf der Dokumentations- & Berichts-Schiene) |
| **Eingefrorene Bereiche (Tabu)** | Umsetzung/Arbeitsergebnis (z. B. Quellcode), Prüfsystem (z. B. Test-Suite) und bestehende produktive Handbücher (`0` Änderungen) |
| **Abnahme ($Q$)** | Konkurrierende Alternativen, falsifizierbare Hypothesen (mit Gegenhypothese & Falsifikationskriterium), Vier-Säulen-Meta-QA inkl. Fehler-/Mutanten-Matrix, Beschlusstabelle (`E1..En`) mit eindeutig markierten **Standard-Empfehlungen** für *Consent-by-Exception*; Berichts-Checks grün; `0` Änderungen an Umsetzung, Prüfsystem und produktiven Handbüchern |
| **Einsatz & Folge-Knoten im Baukasten** | Vor [`NODE_PHASE_RED`](./NODE_PHASE_RED.md) *(Modus A: Freigabe im Folge-`RUN` via `EMPFEHLUNGEN: ALLE` + optionale Abweichungen)*, als Härtungs-Schleife zurück an [`NODE_PHASE_RED`](./NODE_PHASE_RED.md) *(Modus B: Post-Red-Kritik)* oder situativ für [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) bzw. [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Bevor auf einer Baustelle Material bestellt oder eine verbindliche Abnahme-Checkliste geschrieben wird, zeichnet die Architektin nicht einfach den erstbesten Einfall auf. Sie stellt zwei bis drei echte Plan-Varianten nebeneinander, prüft auf dem Papier, wo jeder Plan scheitern könnte, und legt für jede offene Entscheidungsfrage (`E1..En`) eine klar markierte **Standard-Empfehlung** fest. Dadurch bleibt die Abstimmung kinderleicht (*Consent-by-Exception*): Statt jede Antwort mühsam einzeln abzutippen, genügt im nächsten Schritt ein kurzes *„Ich übernehme alle Empfehlungen (`EMPFEHLUNGEN: ALLE`), außer bei Punkt E2“*. Und weil `HYPOTHESIS` ein flexibles Stützrad ist, kann die Architektin genauso gut gerufen werden, um eine frisch entworfene Checkliste noch vor ihrer Versiegelung auf blinde Flecken abzuklopfen (*Post-Red-Kritik*) oder während eines Audits Reparatur-Alternativen gegeneinander abzuwägen.
* **Für Experten & KI-Agenten (Fallibilismus, Einsatzmodi & Consent-by-Exception):** `HYPOTHESIS` operationalisiert Karl Poppers kritischen Rationalismus als methodische Entwurfs- und Prüfdisziplin. Statt voreiliger Gewissheit (*„Beweis: …“*) formuliert jeder Vorschlag **widerlegbare Arbeitshypothesen** (*„Hypothese: …“*) samt Risiko und objektivem **Falsifikationskriterium**. Im modularen TGD-Baukasten wird dieses Stützrad vor allem in zwei Modi (sowie situativ an jedem anderen Knoten) eingesetzt:
  * **Modus A — Pre-Red-Entwurf (vor dem Prüfaufbau):** Entwickelt die Ziel-Struktur ($Q_{\text{Soll}}$), die Fehler-/Mutanten-Matrix und die Entscheidungsmatrix (`E1..En`) mit eindeutigen Standard-Empfehlungen gemäß [Rollen-, Kontext- & Run-Disziplin](./README.md#42-rollen--kontext---run-disziplin).
  * **Modus B — Post-Red-Kritik (zur Härtung neuer Prüfkriterien):** Durchleuchtet einen ersten Prüf- bzw. Test-Entwurf aus `PHASE_RED` noch vor dem endgültigen Freeze im frischen Kontext auf die vier Meta-QA-Schwachstellen (Subsumtion, Tautologien, *Vacuous Passes*, überlebende Kernfehler/Mutanten) und liefert eine präzise Härtungsliste zurück an `NODE_PHASE_RED`.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage:** Status des Arbeitsverzeichnisses gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; bei fremden Altlasten (Klasse 3) sofort vor der ersten Änderung stoppen.
2. **Betriebsmodus & Ziel-Konsistenz im `RUN`-Dokument klären:** Am `RUN`-Dokument eindeutig feststellen, welcher Modus (**Modus A: Pre-Red-Entwurf**, **Modus B: Post-Red-Kritik** oder situative Abwägung) beauftragt ist und unter welchem Zielpfad der Hypothesenbericht abgelegt wird. Widersprüche zwischen Knoten-Rolle und Zielbeschreibung führen zum sofortigen Stopp.
3. **Evidenzbasis verifizieren:** Alle referenzierten Vorgänger-Artefakte (z. B. Analysebericht, zu prüfende Prüf-/Testdateien sowie geltende Fach-, Architektur- und Stil-Handbücher) vollständig lesen.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Konkurrierende Makro-Konzepte (mindestens A vs. B vs. C):** Kein Entwurf ohne echte Gegenmodelle (z. B. *Minimal-Eingriff* vs. *ausgewogene System-Lösung* vs. *streng formalisierter Ausbau*). Bewertung über eine transparente Entscheidungsmatrix mit klar benannten Bruchstellen (`[RISIKO]`).
2. **Falsifizierbare Hypothesen-Struktur:** Jede Kernhypothese trennt verbindlich vier Bausteine:
   * **Beobachteter Ist-Befund** (verankert an der Analyse bzw. am realen Bestand),
   * **Hypothese & Ziel-Skizze (`Soll`)**,
   * **Gegenhypothese / Risiko** (unter welchen Bedingungen bricht das Modell?),
   * **Objektives Falsifikationskriterium** (woran wäre die Hypothese im Prüflauf eindeutig widerlegt?).
3. **Vier-Säulen-Meta-QA (vor dem Einfrieren des Prüfsystems):** Sowohl geplante Prüfkriterien (*Modus A*) als auch bestehende Prüf- bzw. Test-Entwürfe (*Modus B*) werden systematisch auf vier formale Schwachstellen abgeklopft:
   * **Säule 1 — Logische Subsumtion ($Q_{\text{pos}} \implies \neg Q_{\text{neg}}$):** Schließt eine positive Soll-Bedingung das Verbot bereits implizit ein, sodass das Verbot selbst nie eigenständig geprüft wird?
   * **Säule 2 — Prädikatenlogische Tautologien:** Ist eine zusammengesetzte Prüfregel (insbesondere bei ODER-Verknüpfungen wie $(y \in \mathbb{Z}) \lor (y \neq 99) \equiv \top$) logisch immer wahr und damit blind gegen Fehler?
   * **Säule 3 — *Vacuous Passes* (`0pos/Kneg`):** Kann eine Prüfung oder ein Qualitäts-Wächter grün durchlaufen, obwohl gar kein relevanter Prüfgegenstand getroffen wurde (leere Prüfmenge, reine Verbote ohne positives Soll-Ziel, unkalibrierter Regel-Scan)?
   * **Säule 4 — Fehler- & Mutanten-Überlebens-Matrix:** Für jeden plausiblen Kernfehler im Arbeitsergebnis (Mutanten `M1..Mn`) wird genau das Pflicht-Prüfkriterium (bzw. der Test) benannt, das deterministisch fehlschlagen muss, solange dieser Defekt existiert.
4. **Gate-Kollisions- & Generalisierungsprobe:** Geplante Schnittstellen, Zuschnitte und Prüfmuster frühzeitig gegen bestehende Struktur-, Isolations- und Stil-Gates prüfen (um Selbst-Sabotage in späteren Knoten zu vermeiden) und bei wiederverwendbaren Konzepten gegen mindestens einen zweiten Anwendungsfall spiegeln.
5. **Entscheidungsmatrix (`E1..En`) mit Standard-Empfehlungen (*Consent-by-Exception*):** Jede offene Gestaltungsfrage erhält eine eindeutige ID (`E1`, `E2`, …), eine **eindeutig markierte Standard-Empfehlung** sowie die Auswirkung bei Abweichung. Dadurch genügt im Folge-`RUN` das kompakte Freigabe-Signal **`EMPFEHLUNGEN: ALLE`** plus eventuelle explizite Ausnahmen ([Rollen-, Kontext- & Run-Disziplin](./README.md#42-rollen--kontext---run-disziplin)).

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Geplanter Entwurf oder Prüfaufbau kollidiert mit einem bestehenden Qualitäts-/Struktur-Gate** | Konflikt bereits im Hypothesenbericht auflösen (z. B. kollisionsfreie Benennung oder sauberer Zuschnitt), statt ihn erst in `PHASE_RED` oder `PHASE_GREEN` aufprallen zu lassen. | Gate-kompatibler Entwurf |
| **Bestands- oder Analyse-Basis weist eine relevante Faktenlücke auf** | Keine spekulativen Annahmen als Fakten tarnen; fehlende Fakten direkt lesend am Bestand nachmessen (`ANALYSIS`-Disziplin) oder als offene Evidenzlücke samt Entscheidungspunkt (`E*`) ausweisen. | Belastbare Hypothesengrundlage |
| **Unklare Trennung zwischen Modus A (Pre-Red) und Modus B (Post-Red-Kritik)** | Aktiven Modus im Berichtskopf explizit benennen; im Modus *Post-Red-Kritik* ausschließlich das entworfene Prüfsystem kritisieren und eine konkrete Härtungsliste für `NODE_PHASE_RED` liefern. | Eindeutige Rollen- und Übergabegrenze |
| **Versuchung, schon „vorab“ Skizzen direkt in Umsetzungs- oder Prüfdateien anzulegen** | Strikt verboten! Alle Entwürfe bleiben rein dokumentarisch in nicht-ausführbaren Blöcken innerhalb des Hypothesenberichts. | `0` Änderungen an Umsetzung und Prüfsystem |
| **Offene Fragen (`E1..En`) ohne klar hervorgehobene Standard-Empfehlung** | Unzulässig für *Consent-by-Exception*: Jede Entscheidungsfrage muss eine eindeutig markierte Standard-Empfehlung tragen, damit der Folge-Knoten mit `EMPFEHLUNGEN: ALLE` arbeitsfähig ist. | Bürokratiefreie, eindeutige Übergabe |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `HYPOTHESIS` gilt genau dann als abgeschlossen, wenn alle fünf objektiven Kriterien erfüllt sind:

1. **Konkurrierende Optionen & falsifizierbare Hypothesen:** Alternativen sind nachvollziehbar verglichen; jede Kernhypothese besitzt Ist-Befund, Soll-Skizze, Gegenhypothese/Risiko und ein objektiv prüfbares Falsifikationskriterium.
2. **Vier-Säulen-Meta-QA vollständig:** Subsumtion, Tautologien, *Vacuous Passes* und eine konkrete Fehler-/Mutanten-Überlebens-Matrix (`M1..Mn`) sind substanziell ausgearbeitet.
3. **Entscheidungsreife Beschlusstabelle (`E1..En`):** Alle offenen Entscheidungen tragen eine **eindeutig markierte Standard-Empfehlung** und Folgeabschätzung für *Consent-by-Exception* *(bzw. in Modus B eine priorisierte Härtungsliste für `NODE_PHASE_RED`)*.
4. **Berichts-Checks grün:** Alle Format-, Rahmen- und Doku-Prüfungen auf dem Hypothesenbericht bestehen idempotent mit `0` Diagnosen.
5. **Schreibgrenzen-Nachweis erbracht:** Der Status des Arbeitsverzeichnisses zeigt ausschließlich den Hypothesenbericht (plus ggf. das unveränderte Klasse-1-`RUN`-Dokument) und **`0` Änderungen** an Umsetzung/Quellcode, Prüfsystem/Test-Suite und bestehenden produktiven Handbüchern. Die spätere Archivierung oder Bereinigung folgt dem [3-Zustands-Lebenszyklus](./README.md#43-allgemeiner-3-zustands-lebenszyklus-temporärer-artefakte).

> [!TIP]
> **Konkretes Projekt-Profil für `qb-cubie`:** Die projektspezifischen Prüfkommandos, das Minimal-Run-Format (`RUN-*.md`) mit `EMPFEHLUNGEN: ALLE` und das Berichtsformat stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md) sowie im [Leitfaden für Agenten-Berichte](../dev/DEV-GUIDE_Agent-Reports.md).

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

[↦ | Knoten: ANALYSIS (Bestandsaufnahme & Ist-Vermessung) | ↤](./NODE_ANALYSIS.md)  
[↦ | Knoten: HYPOTHESIS (Falsifizierbares Design & Meta-QA) | ↤](./NODE_HYPOTHESIS.md)  
[↦ | Knoten: PHASE_RED (Testaufbau, Gate-Kalibrierung & Test-Freeze) | ↤](./NODE_PHASE_RED.md)  
[↦ | Knoten: PHASE_GREEN (Implementierung unter Test-Freeze) | ↤](./NODE_PHASE_GREEN.md)  
[↦ | Knoten: GREEN_AUDIT (Kontrollierter Rücksprung aus Phase Green) | ↤](./NODE_GREEN_AUDIT.md)  
[↦ | Knoten: LIVING_DOCS (Dokumentations-Synchronisation & Hygiene) | ↤](./NODE_LIVING_DOCS.md)  

</div>
<!-- /qb:frame -->
