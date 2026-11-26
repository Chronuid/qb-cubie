<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="50" -->
<div align="center">

# Knoten: GREEN_AUDIT (Kontrollierter Rücksprung aus Phase Green)

![Cubie](../.assets/cubie-logo-written.png)

Eigenständiger Rücksprung-Knoten (Test-Reparatur-Rolle): Prüft ein in Phase Green gemeldetes Audit-Protokoll im frischen Kontext als widerlegbare Hypothese (`AUDIT-REPRO -> AUDIT-VERDICT -> AUDIT-FIX -> AUDIT-CLOSE`) mit eindeutigem Ausgang `RESOLVED` oder `REFUTED`.

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
| **Rolle** | Kontrollierter Rücksprung aus `PHASE_GREEN` — unabhängige Audit-Falsifikation & minimal-invasive Test-Reparatur-Rolle |
| **Eintrittsbedingungen ($P$)** | Vorliegendes Audit-Protokoll aus einem eingefrorenen `PHASE_GREEN`-Stand, **zwingend frischer Kontext** (ohne Gesprächs-Voreingenommenheit aus Phase Green), saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich betroffene Test-Dateien *(nur bei `CONFIRMED`)* sowie die Abschluss-Sektion des Audit-Protokolls |
| **Eingefrorene Bereiche (Tabu)** | **Quellcode** und **Produkt-Dokumentation** (`0` Änderungen); bei Urteil `REFUTED` zusätzlich **100 % des Test-Codes** |
| **Abnahme ($Q$)** | Eigenständiger Reproduktionsbeleg + eindeutiger Status im Audit-Protokoll: **`Status: RESOLVED`** (Test-Suite + Test-Linter 100 % grün) ODER **`Status: REFUTED`** (`0` Test-Code-Edits + Gegenbeleg); `0` Änderungen an Quellcode und Doku |
| **Folge-Knoten** | [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) *(bei `RESOLVED`)* oder [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md) *(bei `REFUTED`)* |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Der Handwerker hat während des Bauens einen Mängelbericht für die Checkliste hinterlegt. Jetzt kommt der Bauprüfer mit frischem Kopf zurück auf die Baustelle — aber er glaubt dem Bericht **nicht blind**! Zuerst misst er selbst nach. Zeigt sich, dass die Checkliste tatsächlich einen Fehler enthielt (*bestätigt*), repariert der Prüfer die Checkliste so behutsam wie möglich, ohne echte Sicherheitsregeln aufzuweichen (**`RESOLVED`**). Zeigt sich aber, dass die Checkliste recht hatte und der Fehler doch am Haus liegt (*widerlegt*), bleibt die Checkliste unverändert und der Handwerker muss nachbessern (**`REFUTED`**).
* **Für Experten (Abgrenzung zu `PHASE_RED` & symmetrischer Fallibilismus):** `NODE_GREEN_AUDIT` bildet die philosophische Rückwärtstür aus dem [TGD-Handbuch](../GUIDE_TGD.md) als eigenständigen Automaten-Knoten ab, weil sich seine operativen Bedingungen grundlegend von regulärem `PHASE_RED` unterscheiden:
  * In regulärem `PHASE_RED` fehlt der neue Quellcode noch — Zielsignal ist **`FAILED`**.
  * In `GREEN_AUDIT` liegt der implementierte Quellcode bereits vor — Zielsignal nach einer bestätigten, minimal-invasiven Test-Reparatur ist das unmittelbare Umspringen auf **`PASSED`** (ohne erneuten `PHASE_GREEN`-Lauf).
  * Durch die kollisionsfreie vierstufige Mikro-Terminologie **`AUDIT-REPRO` $\to$ `AUDIT-VERDICT` $\to$ `AUDIT-FIX` $\to$ `AUDIT-CLOSE`** entsteht keinerlei Verwechslung mit Makro-`PHASE_GREEN`, und Poppers Fallibilismus wirkt symmetrisch *auch gegen den Audit-Befund selbst*.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Kontext-Frische prüfen:** Sicherstellen, dass dieser Knoten in einem frischen Kontext gestartet wurde (kein implizites Rechtfertigen früherer Entscheidungen aus `PHASE_GREEN`).
2. **Pre-Flight-Triage:** Status des Versionierungssystems gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; fremde Altlasten (Klasse 3) stoppen den Start sofort.
3. **Auftrags- & Eingabe-Prüfung:** Knoten-Rolle (`GREEN_AUDIT`) gegen Zielbeschreibung prüfen und das vollständige Audit-Protokoll samt den referenzierten Test-, Quellcode- und Spezifikationsdateien lesen.

---

## 4. Arbeits- & Meta-QA-Heuristiken (`AUDIT-REPRO` $\to$ `AUDIT-CLOSE`)

Jeder Durchlauf von `NODE_GREEN_AUDIT` folgt exakt vier aufeinanderfolgenden Schritten:

1. **`AUDIT-REPRO` — Unabhängige Reproduktion (`0` Edits):**
   * Behandle das Audit-Protokoll strikt als **widerlegbare Hypothese**, nicht als feststehende Wahrheit.
   * Reproduziere jeden gemeldeten Fehlschlag eigenständig gegen den unveränderten Stand.
   * Bei Isolations-, Import- oder Umgebungs-Tests zwingend auch eine unabhängige Isolations-Probe (z. B. isolierter Subprozess) durchführen, um auszuschließen, dass sich hinter einem vermeintlichen Fixture-Problem ein echter Defekt im Quellcode versteckt.
2. **`AUDIT-VERDICT` — Binäre Falsifikationsentscheidung (`CONFIRMED` vs. `REFUTED`):**
   * **`CONFIRMED` (Test- oder Fixture-Fehler belegt):** Der Widerspruch liegt nachweislich im Testaufbau und nicht im Produktivcode. Jetzt eigenständig alle Reparatur-Optionen abwägen — nach dem **Minimal-Invasivitäts-Prinzip**: Bevorzuge immer die kleinste Reparatur, die **eingefrorene fachliche Assertions zu 100 % unverändert lässt** (*Null Assertion-Edits bevorzugen*, selbst wenn das Audit-Protokoll eine breitere Option empfohlen hat!).
   * **`REFUTED` (Audit widerlegt):** Die unabhängige Prüfung zeigt, dass der Test ein reales Problem im Quellcode aufdeckt oder die vorgeschlagene Lockerung den Vertrag verletzen würde. Kein Test-Code wird angefasst.
3. **`AUDIT-FIX` — Minimal-invasive Reparatur *(ausschließlich bei `CONFIRMED`)*:**
   * Die gewählte Minimal-Reparatur ausschließlich in den betroffenen Testdateien umsetzen.
   * **Explizite Zielsignal-Regel:** Da der Quellcode bereits vollständig implementiert vorliegt, ist das sofortige Umspringen der betroffenen Tests von `FAILED` auf **`PASSED`** hier das reguläre, erwartete Zielsignal. Anschließend betroffene Suiten sowie statische Test-Prüfer (Linter, Typprüfer) vollständig grün laufen lassen.
   * *Bei `REFUTED` entfällt `AUDIT-FIX` vollständig (`0` Edits an Test-Code).*
4. **`AUDIT-CLOSE` — Strukturierter Abschluss im Audit-Protokoll:**
   * Direkt im Audit-Protokoll eine klare Abschluss-Sektion ergänzen mit:
     * maschinenlesbarem Status (**`Status: RESOLVED`** oder **`Status: REFUTED`**),
     * eigenständigem Reproduktionsbeleg (inkl. Isolations-Probe),
     * nachvollziehbarer Begründung der gewählten Option (bzw. klarem Gegenbeleg bei `REFUTED`),
     * kompakter Verifikationstabelle und Schreibgrenzen-Nachweis.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Audit-Protokoll empfiehlt eine Option, die Assertions ändert, obwohl ein reiner Fixture-Fix reicht** | Empfehlung des Audit-Protokolls verwerfen; eigenständig die minimal-invasive Option mit **0 Assertion-Edits** wählen und die Abwägung in `AUDIT-CLOSE` begründen. | Maximaler Vertragsschutz (`RESOLVED`) |
| **Unabhängige Probe deckt echten Quellcode-Bug hinter dem vermeintlichen Testfehler auf** | Keine Test-Änderung! Urteil **`REFUTED`** mit reproduzierbarem Gegenbeleg in das Audit-Protokoll schreiben; Audit-Protokoll bleibt als Pflicht-Eingabe im Repository liegen. | Rückübergabe an [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md) |
| **Mischfall (teils echter Fixture-Fehler, teils ungelöster Quellcode-Bug)** | Echten Quellcode-Bug niemals durch Test-Abschwächung verdecken! Entweder erst auf `REFUTED` stellen, bis der Quellcode-Bug behoben ist, oder strikt belegen, dass der verbleibende Fehler ausschließlich im Quellcode liegt. | Ehrliche Trennung von Test- und Code-Defekt |
| **Impuls, nach `RESOLVED` noch „kurz“ den Quellcode oder die Doku zu polieren** | Strikt verboten! Quellcode und Produkt-Dokumentation bleiben zu 100 % eingefroren. | Saubere Übergabe an [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) |
| **Frage: Darf das abgeschlossene Audit-Protokoll sofort gelöscht werden?** | Nein — während `GREEN_AUDIT` bleibt das Audit-Protokoll als Nachweis erhalten. Bei `REFUTED` dient es als Pflicht-Eingabe für `PHASE_GREEN`; nach `RESOLVED` und grünem `LIVING_DOCS` erfolgt die Archivierung/Bereinigung als nachgelagerte Abschluss-Hygiene. | Nachvollziehbare Audit-Spur |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

`NODE_GREEN_AUDIT` endet über genau einen von zwei symmetrischen, objektiv prüfbaren Ausgängen:

### Ausgang A — `Status: RESOLVED` ($\to$ [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md))
1. **Unabhängige Reproduktion & Minimal-Fix belegt:** Das Audit-Protokoll dokumentiert `AUDIT-REPRO`, die Optionsabwägung (`AUDIT-VERDICT`) und trägt explizit **`Status: RESOLVED`**.
2. **Test-Suite & Test-Hygiene 100 % grün:** Die reparierte Testdatei, abhängige Test-Suiten sowie Linter/Typprüfer auf den geänderten Testdateien laufen mit `0` Fehlern durch (kein erneuter `PHASE_GREEN`-Lauf nötig, da der Quellcode unverändert grün ist).
3. **Schreibgrenzen-Nachweis erbracht:** Der Diff im Versionierungssystem zeigt ausschließlich die betroffenen Testdateien plus das abgeschlossene Audit-Protokoll — und **`0` Änderungen** an Quellcode und Produkt-Dokumentation.

### Ausgang B — `Status: REFUTED` ($\to$ [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md))
1. **Widerlegung sauber belegt:** Das Audit-Protokoll dokumentiert den reproduzierbaren Gegenbeleg für den Quellcode-Defekt und trägt explizit **`Status: REFUTED`**.
2. **Test-Suite unversehrt:** **`0` Änderungen** an Test-Code, Quellcode und Produkt-Dokumentation (ausschließlich die Abschluss-Sektion im Audit-Protokoll wurde ergänzt).
3. **Übergabe gesichert:** Das Audit-Protokoll verbleibt als Pflicht-Eingabe für die Rückkehr in [`NODE_PHASE_GREEN`](./NODE_PHASE_GREEN.md).

> [!TIP]
> **Konkrete `qb-cubie`-Kommandos & Ablageregeln:** Die projektspezifischen Prüfkommandos sowie die konkrete Pfad- und Lebenszyklus-Regel für das Audit-Protokoll stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md).

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
