<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="40" -->
<div align="center">

# Knoten: PHASE_GREEN (Implementierung unter Test-Freeze)

![Cubie](../.assets/cubie-logo-written.png)

Zweiter Kernknoten von TGD: Setzt die Lösung im Arbeitsergebnis (z. B. Quellcode) unter striktem Freeze des Prüfsystems um und nutzt nur im Ausnahmefall eines unbehebbaren Prüf-Widerspruchs die optionale Rückwärtstür (`NODE_GREEN_AUDIT`).

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
| **Rolle** | TGD-Kernknoten 2 — Umsetzung des Arbeitsergebnisses (z. B. Quellcode-Implementierung) unter strikter Freeze-Disziplin |
| **Eintrittsbedingungen ($P$)** | Eingefrorener `PHASE_RED`-Stand mit reproduzierbar roten Prüfkriterien/Tests (oder Rückkehr nach `NODE_GREEN_AUDIT` mit `Status: REFUTED` samt Audit-Protokoll), saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich das umzusetzende Arbeitsergebnis (z. B. Quellcode) — sowie im begründeten Ausnahmefall **genau ein** strukturiertes Audit-Protokoll im Prüf-Bereich (auf der Berichts-Schiene) |
| **Eingefrorene Bereiche (Tabu)** | **Das gesamte Prüfsystem** (keine Edits an Prüfdateien/Test-Code, kein Überspringen/`skip`, kein Aufweichen von Kriterien) sowie die **produktive Dokumentation** (`0` Änderungen!) |
| **Abnahme ($Q$)** | *Regulär (Idealfall):* Alle funktionalen Prüfkriterien/Tests, Struktur-Wächter, Qualitäts-Prüfer (z. B. Linter, Typprüfer) & aktiven Stil-Gates grün + Advisory-Check für pausierte Stil-Gates + beobachtender Doku-Check + `0` Edits an Prüfsystem und produktiver Doku. *Eskalation (Ausnahmefall):* Unstrittige Prüfungen/Gates grün + belegtes Audit-Protokoll |
| **Einsatz & Folge-Knoten im Baukasten** | Direkt zu [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) *(regulärer Idealfall `GREEN`)*; bei Bedarf situatives Zuschalten von [`NODE_ANALYSIS`](./NODE_ANALYSIS.md) (z. B. zur Ursachen-Isolierung); nur bei echtem Prüf-Widerspruch über die optionale Rückwärtstür zu [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Jetzt setzt der Handwerker das Vorhaben genau nach der versiegelten Checkliste der Bauprüferin um — egal ob es sich um ein Bauwerk, ein technisches Konzept oder Software-Quellcode handelt. **Im Idealfall** läuft die Umsetzung glatt durch, alle Punkte der Checkliste springen auf Grün und es geht direkt weiter zur Aktualisierung der Handbücher (`NODE_LIVING_DOCS`). Zwei goldene Regeln schützen dabei die Qualität: Erstens darf der Handwerker die Checkliste niemals heimlich selbst umschreiben. Nur wenn sich unterwegs zeigt, dass in der Checkliste selbst ein echter Fehler steckt, darf er die **optionale Rückwärtstür** nutzen und einen nachvollziehbaren Mängelbericht (**`GREEN_AUDIT`**) einreichen. Zweitens ändert er während der Bauarbeit noch nicht die offiziellen Baupläne und Handbücher: Die bleiben eingefroren und werden erst im nächsten Schritt sauber nachgezogen (*Diagnose-statt-Edit-Regel*).
* **Für Experten & KI-Agenten (Freeze-Disziplin, Diagnose-statt-Edit-Regel, Zwei-Stufen-Gate & Stützräder):** `PHASE_GREEN` trennt die fachliche Umsetzung strikt von Änderungen am Prüfsystem und an der produktiven Dokumentation. Dadurch beweist der resultierende Diff eindeutig, dass allein das neue Arbeitsergebnis alle eingefrorenen Verträge erfüllt. Vier Prinzipien halten diesen Knoten stabil:
  1. **Unantastbarkeit des Prüfsystems** (Verhinderung von stillem *Test-Hacking* und Bestätigungsfehlern),
  2. **Diagnose-statt-Edit-Regel auf der Dokumentations-Schiene** (`0` Edits an produktiven Handbüchern in `PHASE_GREEN`; Doku-Prüfungen laufen rein beobachtend und liefern das Übergabe-Backlog für `NODE_LIVING_DOCS`),
  3. **Zwei-Stufen-Gate-Modell** (harte automatische Qualitäts-Gates plus verbindlicher Advisory-Check auf geänderten Dateien für vorübergehend pausierte Stil- oder Größenregeln),
  4. **Situative Stützräder statt Blindflug:** Treten unerwartete Fehlschläge auf, wird nicht blind am Arbeitsergebnis herumprobiert, sondern situativ die [`NODE_ANALYSIS`](./NODE_ANALYSIS.md)- bzw. [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md)-Disziplin zugeschaltet, um die Ursache systematisch zu isolieren.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage:** Status des Arbeitsverzeichnisses gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; fremde Altlasten (Klasse 3) stoppen den Start sofort.
2. **Auftrags-Konsistenz & Eingaben prüfen:** Am `RUN`-Dokument prüfen, ob Knoten-Rolle (`PHASE_GREEN`) und Zielbeschreibung konsistent sind ([Rollen-, Kontext- & Run-Disziplin](./README.md#42-rollen--kontext---run-disziplin)). Reproduzierbarkeit der eingefrorenen roten Prüfkriterien/Tests verifizieren.
3. **Rückkehr nach `REFUTED`-Audit:** Kehrt der Ablauf aus [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) mit `Status: REFUTED` zurück, ist das bestehende Audit-Protokoll **Pflicht-Eingabe**: Den dort belegten Mangel im Arbeitsergebnis zuerst lesen und gezielt beheben.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Inkrementelles Grün-Schalten von innen nach außen (mit situativem Stützrad-Einsatz):**
   * Erst die neuen Einzel- und Vertrags-Prüfungen grün schalten,
   * danach das betroffene Bestands-Prüfsystem verifizieren,
   * anschließend Struktur-, Architektur- und Meta-Wächter ausführen,
   * zum Schluss formale Qualitäts-Prüfer (in der Software-Entwicklung z. B. Linter, Typprüfer und Stil-Gates) abnehmen.
   * *Bei überraschenden Fehlschlägen:* Erst über eine gezielte `ANALYSIS`-Bestandsaufnahme Ursache und Nebeneffekte isolieren, statt auf Verdacht Änderungen zu stapeln.
2. **Zwei-Stufen-Gate-Modell (für aktive und vorübergehend pausierte Qualitäts-/Stil-Gates):**
   * **Stufe 1 — Harte automatische Gates (blockierend):** Alle aktiven funktionalen Prüfsysteme, Struktur-Wächter, Linter, Typprüfer und aktiven Stilregeln müssen **`0` Fehler** melden.
   * **Stufe 2 — Verbindlicher Advisory-Check für pausierte Stil-Gates:** Ist ein Stil- oder Struktur-Gate (z. B. ein Größen- oder Komplexitätslimit) im Projekt vorübergehend global pausiert, prüft dieser Knoten **alle neu angelegten und geänderten Dateien des Arbeitsergebnisses** dennoch eigenständig gegen die pausierte Regel. Ziel sind **`0` neue Verstöße**; jede bewusst in Kauf genommene Überschreitung muss im Abschlussbericht knapp fachlich begründet werden. Sobald das Gate wieder global aktiv ist, entfällt der manuelle Advisory-Schritt automatisch.
3. **Beobachtender Living-Docs-Check (Diagnose-statt-Edit-Regel):** Erst *nach* bestandener funktionaler und formaler Abnahme werden vorhandene Living-Docs- und Dokumentrahmen-Prüfungen **rein diagnostisch** ausgeführt (Details siehe Abschnitt 5).
4. **Optionale Rückwärtstür (`GREEN_AUDIT`) statt Aufweichung des Arbeitsergebnisses:** Stößt die Umsetzung auf ein rotes Prüfkriterium, das nur durch fachwidriges Aufweichen des Arbeitsergebnisses oder durch Eingriff in das eingefrorene Prüfsystem lösbar wäre, wird **nicht gepfuscht, sondern sauber über die Berichts-Schiene eskaliert**:
   * Keine Änderungen am Prüf-/Test-Code, keine faule Notlösung im Arbeitsergebnis.
   * Stattdessen wird genau ein strukturiertes Audit-Protokoll angelegt mit: betroffener Prüfdatei und Fundstelle, reproduzierbarem Fehlerbeleg, sachlicher Gegenüberstellung mit den geltenden Verträgen/Handbüchern und mindestens zwei konkreten Lösungsoptionen ohne Aufweichung des Arbeitsergebnisses.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Living-Docs- oder Rahmen-Prüfung schlägt wegen neuer/geänderter Schnittstellen fehl (Diagnose-statt-Edit-Regel)** | Ursache scharf trennen! Liegt der Fehler an *bestehenden Dokumentationsdateien* (veraltete Beispiele, Signaturen oder Rahmen) $\to$ **Dokumentation NICHT anfassen!** Diagnosen als geplantes Übergabe-Backlog für `NODE_LIVING_DOCS` protokollieren. Liegt der Fehler hingegen an einem *Defekt im neuen Arbeitsergebnis* (z. B. defekter Parser) $\to$ im Arbeitsergebnis beheben. | Reiner Umsetzungs-Diff (`Doku = 0`) |
| **Unlösbarer Widerspruch in einem eingefrorenen Prüfkriterium oder einer Prüfumgebung/Fixture** | Prüf-/Test-Code nicht anfassen, Arbeitsergebnis nicht aufweichen; alle unstrittigen Prüfungen/Gates grün bringen, strukturiertes Audit-Protokoll verfassen und über die optionale Rückwärtstür übergeben. | Kontrollierter Rücksprung zu [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) |
| **Pausiertes Stil-Gate wird von einem neuen Baustein (z. B. einer Funktion) überschritten** | Baustein bevorzugt sauber in kleinere, klar geschnittene Einheiten zerlegen; nur bei zwingendem sachlichem Grund ausnahmsweise im Abschlussbericht begründen. | Verhinderung stiller Stil-Drift |
| **Rückkehr nach `REFUTED` — und später tritt ein weiterer Prüf-Widerspruch auf** | Das bestehende Audit-Protokoll mit der früheren Widerlegung **nicht überschreiben**, sondern einen neuen datierten Abschnitt anhängen. | Lückenlose Audit-Historie |
| **Prüf-/Test-Datei enthält einen offensichtlichen Tipp- oder Formalfehler** | Auch „offensichtliche“ Kleinigkeiten im Prüfsystem bleiben in `PHASE_GREEN` tabu! Entweder sauber per Audit-Protokoll eskalieren oder geordnet in die Prüf-Rolle zurückgeben. | Ausnahmefreie Freeze-Disziplin |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Je nach Verlauf endet `PHASE_GREEN` über genau einen von zwei objektiv prüfbaren Ausgängen (wobei **Ausgang A** der reguläre Idealfall ist):

### Ausgang A — Regulärer Abschluss (`GREEN` $\to$ [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md))
1. **Harte Gates 100 % grün:** Alle funktionalen Prüfkriterien/Tests, Struktur-/Architektur-Wächter, Qualitäts-Prüfer (z. B. Linter, Typprüfer) und aktiven Stil-Gates laufen mit `0` Fehlern durch.
2. **Advisory-Check dokumentiert:** Alle vorübergehend pausierten Stil-Gates wurden auf sämtlichen neuen/geänderten Dateien des Arbeitsergebnisses geprüft (`0` Verstöße oder knapp begründete Ausnahme).
3. **Beobachtender Living-Docs-Check ausgewertet:** Etwaige veraltete Doku-Diagnosen sind als Handoff-Liste für `NODE_LIVING_DOCS` protokolliert — ohne selbst eine Dokumentationsdatei zu verändern.
4. **Schreibgrenzen-Nachweis erbracht:** Der Diff im Arbeitsverzeichnis weist **`0` Änderungen am Prüfsystem/Test-Code** und **`0` Änderungen an der produktiven Dokumentation** aus.

### Ausgang B — Kontrollierte Eskalation über die optionale Rückwärtstür (`GREEN_AUDIT` $\to$ [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md))
1. **Unstrittiger Bestand grün:** Sämtliche nicht vom Widerspruch betroffenen Prüfungen, Struktur-Wächter und Qualitäts-Prüfer sind grün.
2. **Audit-Protokoll vollständig:** Genau ein strukturiertes Audit-Protokoll mit Fundstellen, Reproduktionsbeleg, Vertragsvergleich und Lösungsoptionen wurde gemäß der [Single-Active-Signal-Invariante](./README.md#43-allgemeiner-3-zustands-lebenszyklus-temporärer-artefakte) angelegt.
3. **Schreibgrenzen-Nachweis erbracht:** **`0` Änderungen am Prüfsystem/Test-Code** und **`0` Änderungen an der produktiven Dokumentation**.

> [!TIP]
> **Konkretes Projekt-Profil für `qb-cubie`:** Die exakten `pytest`-, `ruff`-, `pylint`- und `mypy`-Kommandos sowie der Pfad der Audit-Datei (`tests/GREEN_AUDIT.md`) stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md).

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
