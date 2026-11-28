<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="50" -->
<div align="center">

# Knoten: GREEN_AUDIT (Kontrollierter Rücksprung aus Phase Green)

![Cubie](../.assets/cubie-logo-written.png)

Optionale Rückwärtstür aus Phase Green (unabhängige Prüf-Reparatur-Rolle): Prüft ein gemeldetes Audit-Protokoll nach einem Kontext-Reset als widerlegbare Hypothese (`AUDIT-REPRO -> AUDIT-VERDICT -> AUDIT-FIX -> AUDIT-CLOSE`) mit eindeutigem Ausgang `RESOLVED` oder `REFUTED`.

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
| **Rolle** | Optionale Rückwärtstür aus `PHASE_GREEN` *(im Idealfall nicht benötigt)* — unabhängige Audit-Falsifikation & minimal-invasive Reparatur des Prüfsystems |
| **Eintrittsbedingungen ($P$)** | Vorliegendes Audit-Protokoll aus einem eingefrorenen `PHASE_GREEN`-Stand, **zwingend frischer Arbeitskontext (Kontext-Reset)** ohne Voreingenommenheit aus Phase Green, saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich betroffene Dateien des Prüfsystems (z. B. Test-Dateien, *nur bei `CONFIRMED`*) sowie die Abschluss-Sektion des Audit-Protokolls (auf der Berichts-Schiene) |
| **Eingefrorene Bereiche (Tabu)** | **Umsetzung/Arbeitsergebnis** (z. B. Quellcode) und **produktive Dokumentation** (`0` Änderungen); bei Urteil `REFUTED` zusätzlich **100 % des Prüfsystems** |
| **Abnahme ($Q$)** | Eigenständiger Reproduktionsbeleg + eindeutiger Status im Audit-Protokoll: **`Status: RESOLVED`** (Prüfsystem + formale Prüf-Gates 100 % grün) ODER **`Status: REFUTED`** (`0` Edits am Prüfsystem + Gegenbeleg); `0` Änderungen an Umsetzung und produktiver Doku |
| **Einsatz & Folge-Knoten im Baukasten** | [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) *(bei `RESOLVED`)* oder zurück zu [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md) *(bei `REFUTED`)*; intern nutzt dieser Knoten direkt die Stützrad-Disziplin aus [`NODE_ANALYSIS`](./NODE_ANALYSIS.md) und [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Im besten Fall läuft die Arbeit auf der Baustelle ohne diesen Schritt durch. Hat der Handwerker in `PHASE_GREEN` aber einen Mängelbericht für die Abnahme-Checkliste hinterlegt, kommt die Bauprüferin jetzt über die **offizielle Rückwärtstür** mit komplett frischem Kopf (**Kontext-Reset**) zurück auf die Baustelle. Entscheidend ist: Sie glaubt dem Mängelbericht **nicht blind**! Zuerst misst sie selbst nach (`AUDIT-REPRO`). Zeigt sich, dass die Checkliste tatsächlich einen Fehler enthielt (*bestätigt*), repariert sie die Checkliste so behutsam wie möglich, ohne echte Sicherheitsregeln aufzuweichen (**`RESOLVED`**) — und da das Haus bereits fertig gebaut ist, springt die Abnahme damit sofort auf Grün. Zeigt sich aber, dass die Checkliste recht hatte und der Fehler doch am Haus liegt (*widerlegt*), bleibt die Checkliste unangetastet und der Handwerker muss nachbessern (**`REFUTED`**).
* **Für Experten & KI-Agenten (Abgrenzung zu `PHASE_RED`, symmetrischer Fallibilismus & Schienen-Einsatz):** `NODE_GREEN_AUDIT` modelliert die kontrollierte Rückwärtstür aus dem [TGD-Handbuch](../GUIDE_TGD.md) als eigenständigen, optionalen Baukasten-Knoten, weil sich seine operativen Bedingungen grundlegend von regulärem `PHASE_RED` unterscheiden:
  * In regulärem `PHASE_RED` fehlt das neue Arbeitsergebnis noch — Zielsignal ist **`FAILED`**.
  * In `GREEN_AUDIT` liegt das fertige Arbeitsergebnis (z. B. der implementierte Quellcode) bereits vor — Zielsignal nach einer bestätigten, minimal-invasiven Reparatur des Prüfsystems ist das unmittelbare Umspringen auf **`PASSED`** (ohne unnötigen Rücksprung nach `PHASE_GREEN`).
  * Durch die kollisionsfreie vierstufige Mikro-Terminologie **`AUDIT-REPRO` $\to$ `AUDIT-VERDICT` $\to$ `AUDIT-FIX` $\to$ `AUDIT-CLOSE`** entsteht keinerlei Verwechslung mit Makro-`PHASE_GREEN`. Gleichzeitig greifen hier beide Querschnitts-Schienen ineinander: Das auf der **Berichts-Schiene** übergebene Audit-Protokoll wird mit den Werkzeugen der **Stützräder-Schiene** (`ANALYSIS` zur unabhängigen Reproduktion, `HYPOTHESIS` zur Falsifikation und Alternativenabwägung) kritisch geprüft — Poppers Fallibilismus wirkt damit symmetrisch *auch gegen den Audit-Befund selbst*.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Kontext-Reset prüfen:** Gemäß [Rollen-, Kontext- & Run-Disziplin](./README.md#42-rollen--kontext---run-disziplin) sicherstellen, dass dieser Knoten nach einem neutralen **Kontext-Reset** gestartet wurde (kein implizites Rechtfertigen früherer Entscheidungen aus `PHASE_GREEN` durch *Confirmation Bias*).
2. **Pre-Flight-Triage:** Status des Arbeitsverzeichnisses gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; fremde Altlasten (Klasse 3) stoppen den Start sofort.
3. **Auftrags- & Eingabe-Prüfung (`RUN`-Dokument):** Knoten-Rolle (`GREEN_AUDIT`) im `RUN`-Dokument gegen die Zielbeschreibung prüfen und das vollständige Audit-Protokoll samt den referenzierten Prüf-, Umsetzungs- und Spezifikationsdateien lesen.

---

## 4. Arbeits- & Meta-QA-Heuristiken (`AUDIT-REPRO` $\to$ `AUDIT-CLOSE`)

Jeder Durchlauf von `NODE_GREEN_AUDIT` folgt exakt vier aufeinanderfolgenden Schritten:

1. **`AUDIT-REPRO` — Unabhängige Reproduktion (`0` Edits, `ANALYSIS`-Disziplin):**
   * Behandle das Audit-Protokoll strikt als **widerlegbare Hypothese**, nicht als feststehende Wahrheit.
   * Reproduziere jeden gemeldeten Fehlschlag eigenständig gegen den unveränderten Bestand.
   * Bei Isolations-, Schnittstellen- oder Umgebungs-Prüfungen zwingend auch eine unabhängige Isolations-Probe (in der Software-Entwicklung z. B. einen isolierten Subprozess mit Import-Blocker) durchführen, um auszuschließen, dass sich hinter einem vermeintlichen Fehler der Prüfumgebung/Fixture ein echter Defekt im Arbeitsergebnis versteckt.
2. **`AUDIT-VERDICT` — Binäre Falsifikationsentscheidung (`CONFIRMED` vs. `REFUTED`, `HYPOTHESIS`-Disziplin):**
   * **`CONFIRMED` (Prüf- oder Vorlagen-Fehler belegt):** Der Widerspruch liegt nachweislich im Prüfaufbau (z. B. in einer fehlerhaften Test-Fixture) und nicht im Arbeitsergebnis. Jetzt eigenständig alle Reparatur-Optionen abwägen — nach dem **Minimal-Invasivitäts-Prinzip**: Bevorzuge immer die kleinste Reparatur, die **eingefrorene fachliche Kern-Prüfkriterien (Assertions) zu 100 % unverändert lässt** (*Null Assertion-Edits bevorzugen*, selbst wenn das Audit-Protokoll eine breitere Option vorgeschlagen hat!).
   * **`REFUTED` (Audit widerlegt):** Die unabhängige Prüfung zeigt, dass das Prüfkriterium einen realen Mangel im Arbeitsergebnis aufdeckt oder die vorgeschlagene Lockerung den Soll-Vertrag ($Q_{\text{Soll}}$) verletzen würde. Keine einzige Prüfdatei wird verändert.
3. **`AUDIT-FIX` — Minimal-invasive Reparatur *(ausschließlich bei `CONFIRMED`)*:**
   * Die gewählte Minimal-Reparatur ausschließlich in den betroffenen Dateien des Prüfsystems umsetzen.
   * **Explizite Zielsignal-Regel:** Da das Arbeitsergebnis bereits vollständig umgesetzt vorliegt, ist das sofortige Umspringen der betroffenen Prüfungen von `FAILED` auf **`PASSED`** hier das reguläre, erwartete Zielsignal. Anschließend abhängige Prüfbereiche sowie formale Qualitäts-Prüfer (z. B. Linter, Typprüfer) auf den geänderten Prüfdateien vollständig grün laufen lassen.
   * *Bei `REFUTED` entfällt `AUDIT-FIX` vollständig (`0` Edits am Prüfsystem).*
4. **`AUDIT-CLOSE` — Strukturierter Abschluss im Audit-Protokoll (Berichts-Schiene):**
   * Direkt im Audit-Protokoll eine klare Abschluss-Sektion ergänzen mit:
     * eindeutigem Status (**`Status: RESOLVED`** oder **`Status: REFUTED`**),
     * eigenständigem Reproduktionsbeleg (inkl. Isolations-Probe),
     * nachvollziehbarer Begründung der gewählten Option (bzw. klarem Gegenbeleg bei `REFUTED`),
     * kompakter Verifikationstabelle und Schreibgrenzen-Nachweis.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Audit-Protokoll empfiehlt eine Option, die Kern-Prüfkriterien/Assertions ändert, obwohl ein reiner Umgebungs-/Fixture-Fix reicht** | Empfehlung des Audit-Protokolls verwerfen; eigenständig die minimal-invasive Option mit **0 Änderungen an den Kern-Prüfkriterien (0 Assertion-Edits)** wählen und die Abwägung in `AUDIT-CLOSE` begründen. | Maximaler Vertragsschutz (`RESOLVED`) |
| **Unabhängige Probe deckt echten Mangel im Arbeitsergebnis hinter dem vermeintlichen Prüffehler auf** | Keine Änderung am Prüfsystem! Urteil **`REFUTED`** mit reproduzierbarem Gegenbeleg in das Audit-Protokoll schreiben; Audit-Protokoll bleibt als Pflicht-Eingabe bestehen. | Rückübergabe an [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md) |
| **Mischfall (teils echter Vorlagen-/Fixture-Fehler, teils ungelöster Mangel im Arbeitsergebnis)** | Echten Mangel im Arbeitsergebnis niemals durch Abschwächung des Prüfsystems verdecken! Entweder erst auf `REFUTED` stellen, bis das Arbeitsergebnis korrigiert ist, oder den Vorlagen-Fix so ausführen, dass der verbleibende Mangel klar und isoliert sichtbar bleibt. | Ehrliche Trennung von Prüf- und Umsetzungs-Defekt |
| **Impuls, nach `RESOLVED` noch „kurz“ das Arbeitsergebnis oder die Handbücher zu polieren** | Strikt verboten! Arbeitsergebnis (z. B. Quellcode) und produktive Dokumentation bleiben zu 100 % eingefroren. | Saubere Übergabe an [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) |
| **Frage: Darf das abgeschlossene Audit-Protokoll sofort gelöscht werden?** | Nein — während `GREEN_AUDIT` bleibt das Audit-Protokoll als Nachweis erhalten ([3-Zustands-Lebenszyklus](./README.md#43-allgemeiner-3-zustands-lebenszyklus-temporärer-artefakte)). Bei `REFUTED` dient es als Pflicht-Eingabe für `PHASE_GREEN`; nach `RESOLVED` und grünem `LIVING_DOCS` erfolgt die Archivierung/Bereinigung als nachgelagerte Abschluss-Hygiene. | Nachvollziehbare Audit-Spur |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

`NODE_GREEN_AUDIT` endet über genau einen von zwei symmetrischen, objektiv prüfbaren Ausgängen:

### Ausgang A — `Status: RESOLVED` ($\to$ [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md))
1. **Unabhängige Reproduktion & Minimal-Fix belegt:** Das Audit-Protokoll dokumentiert `AUDIT-REPRO`, die Optionsabwägung (`AUDIT-VERDICT`) und trägt explizit **`Status: RESOLVED`**.
2. **Prüfsystem & formale Prüf-Hygiene 100 % grün:** Die reparierte Prüfdatei, abhängige Prüfbereiche sowie Qualitäts-Prüfer (z. B. Linter/Typprüfer) auf den geänderten Prüfdateien laufen mit `0` Fehlern durch (kein erneuter `PHASE_GREEN`-Lauf nötig, da das Arbeitsergebnis unverändert grün ist).
3. **Schreibgrenzen-Nachweis erbracht:** Der Diff im Arbeitsverzeichnis zeigt ausschließlich die betroffenen Dateien des Prüfsystems plus das abgeschlossene Audit-Protokoll — und **`0` Änderungen** an Umsetzung/Quellcode und produktiver Dokumentation.

### Ausgang B — `Status: REFUTED` ($\to$ [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md))
1. **Widerlegung sauber belegt:** Das Audit-Protokoll dokumentiert den reproduzierbaren Gegenbeleg für den Mangel im Arbeitsergebnis und trägt explizit **`Status: REFUTED`**.
2. **Prüfsystem unversehrt:** **`0` Änderungen** an Prüf-/Test-Code, Umsetzung/Quellcode und produktiver Dokumentation (ausschließlich die Abschluss-Sektion im Audit-Protokoll wurde ergänzt).
3. **Übergabe gesichert:** Das Audit-Protokoll verbleibt als Pflicht-Eingabe für die Rückkehr in [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md).

> [!TIP]
> **Konkretes Projekt-Profil für `qb-cubie`:** Die projektspezifischen Prüfkommandos, die Subprozess-Isolations-Probe (`sys.meta_path`) sowie die konkrete Pfad- und Lebenszyklus-Regel für `tests/GREEN_AUDIT.md` (`Single-Active-Signal-Invariante`) stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md).

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
