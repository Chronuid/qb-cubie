<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="60" -->
<div align="center">

# Knoten: LIVING_DOCS (Dokumentations-Synchronisation & Hygiene)

![Cubie](../.assets/cubie-logo-written.png)

Dritter Kernknoten und durchgehende Dokumentations-Ebene von TGD: Synchronisiert produktive Handbücher, ausführbare Beispiele und Übersichten streng nach dem Prinzip *Arbeitsergebnis als Wahrheitsquelle* (*Code as Source of Truth*), verifiziert alle Doku-Gates und schließt den Zyklus sauber ab.

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
| **Rolle** | TGD-Kernknoten 3 & Abschluss der Dokumentations-Schiene — Synchronisation der produktiven Handbücher, Beispiel-Verifikation & Zyklus-Abschluss |
| **Eintrittsbedingungen ($P$)** | Grüner Stand aus `PHASE_GREEN` oder `GREEN_AUDIT (RESOLVED)` (bzw. ein eigenständiger Dokumentations-Auftrag im `RUN`-Dokument), direkter Lesezugriff auf das reale Arbeitsergebnis (z. B. Quellcode), ggf. Doku-Handoff-Liste aus Phase Green, saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich Dokumentationsdateien (Handbücher, Übersichten/Indizes, bekannte Einschränkungen, Änderungsprotokolle) |
| **Eingefrorene Bereiche (Tabu)** | **Ausnahmefrei** `0` Änderungen an Umsetzung/Arbeitsergebnis (z. B. Quellcode) und am gesamten Prüfsystem/Test-Verzeichnis (inkl. abgeschlossener Audit-Protokolle!) |
| **Abnahme ($Q$)** | Alle betroffenen und angrenzenden Handbücher gegen das reale Arbeitsergebnis abgeglichen, automatische Rahmen/Indizes idempotent synchronisiert (`0` Änderungen im 2. Lauf), Living-Docs-Prüfungen & relevante Gates grün, `0` Änderungen an Umsetzung und Prüfsystem |
| **Einsatz & Folge-Knoten im Baukasten** | **Zyklus abgeschlossen** *(plus ggf. nachgelagerte 1-Schritt-Abschluss-Hygiene für Audit-/Run-Artefakte durch die Orchestrierung)*; bei größeren Doku-Umbauten können vorab situativ [`NODE_ANALYSIS`](./NODE_ANALYSIS.md) oder [`NODE_HYPOTHESIS`](./NODE_HYPOTHESIS.md) zugeschaltet werden |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Schon während der gesamten Bauzeit lief das Berichts- und Planwesen im Hintergrund mit: Vorhandene Pläne wurden als Nachschlagewerk genutzt, und die einzelnen Schritte haben bei Bedarf kurze Vermessungs-, Entwurfs- oder Mängelprotokolle hinterlassen. Jetzt, wo das fertige Haus steht und die versiegelte Checkliste komplett abgehakt ist, werden in der Rolle **`NODE_LIVING_DOCS`** die offiziellen Baupläne, Bedienungsanleitungen und Inhaltsverzeichnisse auf den *tatsächlichen* Endstand gebracht — und zwar durch direkten Blick auf das fertige Werk, nicht durch blindes Abschreiben alter Entwurfsskizzen. Erst wenn alle Handbücher wieder exakt stimmen, können Einsteiger, Experten und künftige Projekte verlässlich darauf aufbauen.
* **Für Experten & KI-Agenten (Doppelrolle der Dokumentations-Schiene & vierte Verifikationsschicht):** Im symmetrischen TGD-Baukasten ([`GUIDE_TGD.md`](../GUIDE_TGD.md)) erfüllt die Dokumentations-Ebene eine klar getrennte Doppelrolle:
  1. **Querschnittliche Dokumentations- & Berichts-Schiene (während aller Knoten):** Jeder Knoten liest bestehende Handbücher als Vertrags-Referenz und kann begleitende Berichte (`ANALYSIS*`, `HYPOTHESIS*`, `GREEN_AUDIT`, Run-Notizen) erzeugen — während die **produktiven Handbücher** in allen anderen Knoten streng bei `0` Diff eingefroren bleiben.
  2. **Dedizierter Abschluss-Knoten (`NODE_LIVING_DOCS`):** Hier werden die produktiven Handbücher, ausführbaren Beispiele und Navigationsrahmen als **orthogonale Verifikationsschicht** aktualisiert und maschinell geprüft. Die strikte Bindung an das **reale Arbeitsergebnis als Wahrheitsquelle** (*Code as Source of Truth*) eliminiert Plan-vs.-Umsetzungs-Drift (etwa wenn Qualitäts-Gates während `PHASE_GREEN` eine geplante Signatur verändert haben). Gleichzeitig garantiert die **ausnahmefreie Schreibgrenze** (`Umsetzung = 0`, `Prüfsystem = 0`), dass kein Dokumentations-Stand unbemerkt Änderungen an Produkt oder Tests einschleust.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage & Kontext-Reset:** Status des Arbeitsverzeichnisses gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) in einem frischen Kontext prüfen; fremde Altlasten (Klasse 3) stoppen den Start sofort.
2. **Auftrags-Konsistenz & grüne Baseline prüfen:** Am `RUN`-Dokument gemäß [Rollen-, Kontext- & Run-Disziplin](./README.md#42-rollen--kontext---run-disziplin) prüfen, ob Knoten-Rolle (`LIVING_DOCS`) und Zielbeschreibung übereinstimmen und ob der Vorgänger-Knoten (`PHASE_GREEN` bzw. `GREEN_AUDIT` mit `Status: RESOLVED` oder ein eigenständiger Doku-Auftrag) sauber vorliegt.
3. **Wahrheitsquelle & Handoff-Liste sammeln:** Das reale Arbeitsergebnis (z. B. die geänderten Quellcode-Dateien), eine eventuelle Living-Docs-Diagnoseliste aus `PHASE_GREEN` (*Diagnose-statt-Edit-Regel*) sowie alle betroffenen und angrenzenden Handbücher als Lese-Basis bereitstellen. Bei umfangreichen Doku-Umbauten kann vorab eine systematische Drift-Bestandsaufnahme per [`NODE_ANALYSIS`](./NODE_ANALYSIS.md) genutzt werden.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Reales Arbeitsergebnis als Wahrheitsquelle (`Code-as-Source-of-Truth` / Anti-Drift-Regel):**
   * Sämtliche Fachbegriffe, Schnittstellen, Signaturen, Parameter, Rückgabewerte, Fehlermeldungen, Kommandos und Optionen werden **direkt am realen Arbeitsergebnis (z. B. am Quellcode)** verifiziert.
   * Vorläufige Entwurfsnamen aus früheren Analyse- oder Hypothesenberichten dürfen **niemals ungeprüft** in produktive Handbücher kopiert werden.
2. **Nachbarschafts- & Index-Scan:**
   * Neben dem primären bzw. neu erstellten Handbuch systematisch alle angrenzenden Einstiegs-, Fach- und Entwickler-Handbücher, Ordner-Übersichten und bekannte Einschränkungen auf veraltete Angaben, tote Querverweise oder geänderte Konzepte prüfen.
3. **Zugänglichkeit für Einsteiger & Präzision für Experten (Werkzeugneutralität):**
   * Komplexe Konzepte beidseitig zugänglich formulieren: anschauliche Alltags- oder Baustellen-Analogien für Einsteiger kombinieren mit präzisen Verträgen, Invarianten und Abnahmekriterien für Experten und KI-Agenten.
   * Durchgängig plattform- und werkzeugneutrale Sprache sowie Standard-Markdown-Links verwenden (keine proprietären CLI-/IDE-Sonderbefehle oder `@`-Referenzen in produktiven Handbüchern und Rahmen-Zonen).
4. **Ausführbarkeits- & Fence-Hygiene:**
   * Fachliche Code- und Anwendungsbeispiele so verfassen, dass die automatische Living-Docs-Prüfung sie real ausführen und gegen die tatsächliche Ausgabe verifizieren kann.
   * Nicht-ausführbare Skizzen, Vorlagen, Diagramme oder Pseudocode strikt in nicht-ausführbare Blöcke (z. B. `text`, `markdown` mit passenden verschachtelten Fences oder `mermaid`) setzen — niemals als ausführbare Sprachblöcke tarnen.
5. **Idempotente Rahmen- & Navigations-Synchronisation:**
   * Automatische Dokumentrahmen und Index-/Router-Tabellen aktualisieren und zwingend durch einen **zweiten Synchronisationslauf** belegen, dass der Zustand stabil und idempotent ist (`0` weitere geänderte Dateien).
6. **Artefakt-Hygiene & ehrliche Abschluss-Meldung:**
   * Temporäre Lauf- und Berichts-Artefakte gemäß dem [3-Zustands-Lebenszyklus](./README.md#43-allgemeiner-3-zustands-lebenszyklus-temporärer-artefakte) einordnen.
   * Liegt noch ein abgeschlossenes Audit-Protokoll (`Status: RESOLVED`) im Prüf-/Test-Verzeichnis, wird dieses **nicht** in `NODE_LIVING_DOCS` selbst gelöscht oder verschoben, sondern im Abschlussbericht ausdrücklich als fällige 1-Schritt-Abschluss-Hygiene für die Orchestrierung ausgewiesen.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Ein reales Beispiel in der Doku deckt einen echten Defekt im Arbeitsergebnis (z. B. im Quellcode) auf** | Arbeitsergebnis **nicht** still in `LIVING_DOCS` patchen! Stoppen, reproduzierbaren Befund sauber dokumentieren und einen regulären Korrektur-Durchlauf (`PHASE_RED` $\to$ `PHASE_GREEN`) anstoßen. | Wahrung der Schreibgrenze & ehrliche Fehlerkultur |
| **Entwurf aus `HYPOTHESIS` weicht vom realen Arbeitsergebnis ab** | Das reale Arbeitsergebnis gewinnt immer. Das Handbuch beschreibt ausschließlich das tatsächlich umgesetzte Verhalten (bei Bedarf kurzer Hinweis auf die bewusste Abweichung im Zyklus-Bericht). | Null Plan-vs.-Umsetzungs-Drift |
| **Neues oder umbenanntes Handbuch erzeugt breiten Navigations-/Footer-Diff über viele bestehende Dokumente** | Erwartetes Verhalten automatischer Navigations-Rahmen — unveränderte Fremd-Inhalte nicht manuell berühren und den automatischen Sync-Anteil im Abschlussbericht transparent benennen. | Nachvollziehbarer, sauberer Doku-Stand |
| **Abgeschlossenes Audit-Protokoll liegt noch im Prüf-/Test-Verzeichnis** | Strikte Schreibgrenze einhalten (`Prüfsystem/Test-Verzeichnis = 0`); die fällige Archivierung oder Entfernung klar als nachgelagerte Abschluss-Hygiene für die Orchestrierung protokollieren. | Ausnahmefreie Schreibgrenze |
| **Fehlende Konvention für Berichts-, Anker- oder Rahmen-Syntax** | Vor dem Editieren die jeweiligen Projekt-Konventionen prüfen und nach jeder Änderung mit den automatischen Doku-Prüfern verifizieren. | `0` Rahmen- oder Doku-Diagnosen |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `LIVING_DOCS` (und damit der aktuelle TGD-Zyklus) gilt genau dann als abgeschlossen, wenn alle fünf objektiven Kriterien erfüllt sind:

1. **Treue zum Arbeitsergebnis belegt:** Alle neuen und aktualisierten Handbücher, Beispiele und Indizes spiegeln nachweislich den realen Stand des Arbeitsergebnisses wider (keine ungeprüften Entwurfs-Namen).
2. **Idempotente Synchronisation nachgewiesen:** Der zweite Lauf der automatischen Rahmen-/Index-Synchronisation meldet `0` weitere Änderungen.
3. **Alle Doku-Gates & relevante Prüfungen grün:** Rahmen-Prüfung, ausführbare Living-Docs-Prüfung und die dazugehörigen Doku-Test-Gates laufen mit Exit-Code `0` und `0` Diagnosen durch.
4. **Schreibgrenzen-Nachweis erbracht:** Der Status des Arbeitsverzeichnisses weist ausschließlich Dokumentationsdateien aus — **`0` Änderungen an Umsetzung/Quellcode und am Prüfsystem/Test-Verzeichnis**.
5. **Abschluss-Hygiene klar dokumentiert:** Offene nachgelagerte Aufräum- oder Archivierungsschritte (z. B. ein abgeschlossenes Audit-Protokoll im Test-Verzeichnis oder temporäre `RUN`-Dokumente) sind im Abschlussbericht explizit benannt.

> [!TIP]
> **Konkretes Projekt-Profil für `qb-cubie`:** Die exakten `docframe`-, `docensurance`- und `pytest`-Kommandos sowie der konkrete 3-Zustands-Lebenszyklus für `qb-cubie` stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md) und den [Dokumentrahmen-Konventionen](../dev/DEV-GUIDE_DocFrame-Conventions.md).

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
