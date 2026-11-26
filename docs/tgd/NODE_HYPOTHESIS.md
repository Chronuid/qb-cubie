<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="20" -->
<div align="center">

# Knoten: HYPOTHESIS (Falsifizierbares Design & Meta-QA)

![Cubie](../.assets/cubie-logo-written.png)

Falsifizierbarer Architekturentwurf und Meta-QA-Prüfung (Stützrad 2): Entwickelt konkurrierende Lösungsmodelle, Mutanten-Matrizen und entscheidungsreife Beschlüsse — im Modus *Pre-Red* vor dem Testbau oder im Modus *Post-Red-Kritik* zur Test-Suite-Härtung.

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
| **Rolle** | Optionales Stützrad 2 — falsifizierbares Design & Meta-QA (*Modus A: Pre-Red* \| *Modus B: Post-Red-Kritik*) |
| **Eintrittsbedingungen ($P$)** | *Modus A (Pre-Red):* Vorliegender Analysebericht (`ANALYSIS`) und relevante Architektur-Handbücher. *Modus B (Post-Red-Kritik):* Erster Test-Suite-Entwurf aus `PHASE_RED` zur kritischen Härtung. Plus saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell). |
| **Erlaubte Schreibziele** | Ausschließlich der designierte Hypothesenbericht |
| **Eingefrorene Bereiche (Tabu)** | Quellcode, Test-Suite und bestehende Produkt-Handbücher (`0` Änderungen) |
| **Abnahme ($Q$)** | Konkurrierende Alternativen, falsifizierbare Hypothesen (mit Gegenhypothese & Falsifikationskriterium), 4-Säulen-Meta-QA inkl. Mutanten-Matrix, strukturierte Beschlusstabelle (`E1..En`); Berichts-Checks grün; `0` Änderungen an Code, Tests und Handbüchern |
| **Folge-Knoten** | [`NODE_PHASE_RED`](./NODE_PHASE_RED.md) *(in Modus A nach expliziter Bestätigung von `E1..En`; in Modus B als gezielte Härtungs-Iteration der Test-Suite)* |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Bevor auf der Baustelle Material bestellt wird, entwirft die Architektin nicht nur *eine* Idee, sondern vergleicht zwei bis drei realistische Baupläne, prüft auf dem Papier, wo jeder Plan brechen könnte, und legt dem Bauherrn die wichtigsten offenen Fragen übersichtlich zur Entscheidung vor. Genauso kann sie im Sonderfall (*Post-Red-Kritik*) noch einmal kritisch über die frisch geschriebene Prüfliste schauen, ob dort versehentlich Lücken oder zu lasche Fragen stehen.
* **Für Experten (Fallibilismus & zwei Betriebsmodi):** `HYPOTHESIS` operationalisiert Karl Poppers kritischen Rationalismus als Design-Disziplin. Statt voreiliger Gewissheit formuliert jeder Entwurf **widerlegbare Arbeitshypothesen** mit explizitem Risiko und objektivem **Falsifikationskriterium**. Der Knoten kennt zwei klar getrennte Betriebsmodi:
  * **Modus A — Pre-Red (Regelfall):** Steht zwischen `ANALYSIS` und `PHASE_RED`. Erarbeitet das Ziel-Design, das Test- und Mutanten-Backlog sowie offene Architekturentscheidungen (`E1..En`).
  * **Modus B — Post-Red-Kritik (Sonderfall zur Test-Suite-Härtung):** Steht optional *nach* einem ersten Entwurf in `PHASE_RED` (noch vor dem endgültigen Test-Freeze). Durchleuchtet die neu geschriebenen Tests im frischen Kontext auf Subsumtion, Tautologien, *Vacuous Passes* und überlebende Mutanten und liefert eine präzise Härtungsliste zurück an `NODE_PHASE_RED`.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage:** Status des Versionierungssystems gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; bei fremden Altlasten (Klasse 3) sofort stoppen.
2. **Betriebsmodus & Ziel-Konsistenz klären:** Am Arbeits-Ticket eindeutig feststellen, ob **Modus A (Pre-Red)** oder **Modus B (Post-Red-Kritik)** beauftragt ist und wo der Hypothesenbericht gespeichert wird. Widersprüche zwischen Knoten-Rolle und Ziel führen zum Stopp.
3. **Evidenzbasis verifizieren:** Alle referenzierten Vorgänger-Artefakte (Analysebericht bzw. zu prüfende Testmodule sowie geltende Architektur- und Stil-Handbücher) vollständig lesen.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Konkurrierende Makro-Konzepte (mindestens A vs. B vs. C):** Keine Architektur-Hypothese ohne echte Gegenentwürfe (z. B. *Minimalansatz* vs. *schichtsaubere Balance* vs. *stark formalisierte Lösung*). Bewertung über eine transparente Entscheidungsmatrix mit klaren Bruchstellen (`[RISIKO]`).
2. **Falsifizierbare Hypothesen-Struktur:** Jede Kernhypothese trennt verbindlich vier Bausteine:
   * **Beobachteter Ist-Befund** (verankert an der Analyse bzw. realem Code),
   * **Hypothese & Design-Skizze (`Soll`)**,
   * **Gegenhypothese / Risiko** (wo könnte das Modell scheitern?),
   * **Objektives Falsifikationskriterium** (woran wäre die Hypothese im Praxislauf eindeutig widerlegt?).
3. **Vier-Säulen-Meta-QA (vor dem Test-Freeze):** Sowohl geplante Verträge (*Modus A*) als auch bestehende Test-Entwürfe (*Modus B*) werden gegen vier formale Schwachstellen geprüft:
   * **Säule 1 — Logische Subsumtion ($Q_{\text{pos}} \implies \neg Q_{\text{neg}}$):** Prüft eine positive Bedingung das Verbot bereits implizit mit, sodass das eigentliche Verbot gar nicht eigenständig getestet wird?
   * **Säule 2 — Prädikatenlogische Tautologien:** Ist eine zusammengesetzte Prüfbedingung (insbesondere bei ODER-Verknüpfungen) logisch immer wahr und damit blind?
   * **Säule 3 — *Vacuous Passes*:** Kann ein Test oder statischer Wächter grün werden, obwohl kein relevanter Prüfgegenstand vorhanden war (leere Dateiliste, reine Verbote ohne positives Soll-Ziel, unkalibrierter Regel-Scan)?
   * **Säule 4 — Mutanten-Überlebens-Matrix:** Für jeden plausiblen Kern-Defekt (Mutanten `M1..Mn`) wird genau der Pflicht-Test benannt, der deterministisch fehlschlagen muss, solange dieser Defekt existiert.
4. **Gate-Kollisions- & Generalisierungsprobe:** Geplante API-Namen, Modul-Zuschnitte und Test-Patterns frühzeitig gegen bestehende Architektur-, I/O- und Stil-Wächter prüfen (um Gate-Selbst-Sabotage zu vermeiden) und bei wiederverwendbaren Abstraktionen gegen mindestens einen weiteren Anwendungsfall gegentesten.
5. **Strukturierte Entscheidungsmatrix (`E1..En`):** Jede offene Gestaltungsfrage erhält eine eindeutige ID (`E1`, `E2`, …), eine begründete Empfehlung sowie die konkrete Auswirkung bei Gegenentscheidung — vorbereitet für eine verbindliche Bestätigung im Folge-Ticket.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Geplante API oder Teststruktur kollidiert mit bestehendem Architektur-/Stil-Gate** | Konflikt bereits in der Hypothesen-Phase auflösen (z. B. kollisionsfreie Methodenbenennung oder saubere Schichtgrenze), statt ihn in `PHASE_RED` aufprallen zu lassen. | Gate-kompatibler Entwurf |
| **Analyse-Basis hat relevante Faktenlücke** | Keine spekulativen Annahmen als Fakten tarnen; fehlende Daten direkt lesend am Code nachmessen oder als offene Evidenzlücke + Entscheidungspunkt ausweisen. | Belastbare Hypothesengrundlage |
| **Unklare Trennung zwischen Modus Pre-Red und Post-Red-Kritik** | Modus im Berichtskopf explizit benennen; im Modus *Post-Red-Kritik* ausschließlich die bestehende Test-Suite kritisieren und konkrete Härtungs-Aufträge für `NODE_PHASE_RED` formulieren. | Eindeutige Rollen- und Übergabegrenze |
| **Versuchung, schon „vorab“ Code-Skizzen in Quell- oder Testdateien anzulegen** | Strikt verboten! Entwürfe bleiben rein dokumentarisch in nicht-ausführbaren Blöcken innerhalb des Hypothesenberichts. | `0` Änderungen an Quellcode und Tests |
| **Zu viele offene Detailfragen ohne klare Empfehlung** | Offene Punkte auf echte Architekturentscheidungen (`E1..En`) verdichten und jede Frage mit einer klaren Standard-Empfehlung versehen. | Entscheidungsreife Übergabe an die Orchestrierung |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `HYPOTHESIS` gilt genau dann als abgeschlossen, wenn alle fünf objektiven Kriterien erfüllt sind:

1. **Konkurrierende Optionen & falsifizierbare Hypothesen:** Alternativen sind tabellarisch verglichen; jede Kernhypothese besitzt Ist-Befund, Soll-Skizze, Gegenhypothese/Risiko und ein prüfbares Falsifikationskriterium.
2. **Vier-Säulen-Meta-QA vollständig:** Subsumtion, Tautologien, *Vacuous Passes* und eine konkrete Mutanten-Überlebens-Matrix sind ausgearbeitet (ohne leere Floskeln).
3. **Entscheidungsreife Beschlusstabelle (`E1..En`):** Alle offenen Entscheidungen liegen mit Empfehlung und Folgeabschätzung vor *(in Modus B: konkrete Härtungsliste für `PHASE_RED`)*.
4. **Berichts-Checks grün:** Alle Format-, Rahmen- und Doku-Prüfungen auf dem Hypothesenbericht bestehen idempotent mit `0` Diagnosen.
5. **Schreibgrenzen-Nachweis erbracht:** Der Status des Versionierungssystems zeigt ausschließlich den Hypothesenbericht (plus ggf. das unveränderte Ticket) und **`0` Änderungen** an Quellcode, Test-Suite und bestehenden Produkt-Handbüchern.

> [!TIP]
> **Konkrete `qb-cubie`-Kommandos & Berichtsformat:** Die projektspezifischen Prüfkommandos und Ticket-Bestätigungsregeln stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md) sowie im [Leitfaden für Agenten-Berichte](../dev/DEV-GUIDE_Agent-Reports.md).

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
