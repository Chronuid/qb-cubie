<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="60" -->
<div align="center">

# Knoten: LIVING_DOCS (Dokumentations-Synchronisation & Hygiene)

![Cubie](../.assets/cubie-logo-written.png)

Dritter verbindlicher Kernknoten von TGD: Synchronisiert Handbücher, ausführbare Beispiele und Übersichten streng nach dem Prinzip *Code als Wahrheitsquelle*, verifiziert alle Doku-Gates und schließt den Zyklus sauber ab.

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
| **Rolle** | Verbindlicher Kernknoten 3 — Lebende Dokumentation, Beispiel-Verifikation & Zyklus-Abschluss |
| **Eintrittsbedingungen ($P$)** | Grüner `PHASE_GREEN`- oder `GREEN_AUDIT (RESOLVED)`-Stand, direkter Lesezugriff auf den realen Quellcode, ggf. Doku-Handoff-Liste aus Phase Green, saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich Dokumentationsdateien (Handbücher, Übersichten/Indizes, bekannte Einschränkungen, Änderungsprotokolle) |
| **Eingefrorene Bereiche (Tabu)** | **Ausnahmefrei** `0` Änderungen an Quellcode und am gesamten Test-Verzeichnis (inkl. abgeschlossener Audit-Protokolle!) |
| **Abnahme ($Q$)** | Alle betroffenen und angrenzenden Handbücher gegen realen Quellcode abgeglichen, automatische Rahmen/Indizes idempotent synchronisiert (`0` Änderungen im 2. Lauf), Living-Docs-Prüfungen & relevante Tests grün, `0` Änderungen an Quellcode und Test-Verzeichnis |
| **Folge-Knoten** | **Zyklus abgeschlossen** *(plus ggf. nachgelagerte 1-Schritt-Abschluss-Hygiene für Audit-/Lauf-Artefakte durch die Orchestrierung)* |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Das neue Haus steht und die versiegelte Checkliste ist vollständig abgehakt. Jetzt werden Bauplan, Bedienungsanleitung und Inhaltsverzeichnis auf den *tatsächlichen* Zustand des fertigen Hauses gebracht — und zwar durch direkten Blick auf das gebaute Haus, nicht durch blindes Abschreiben alter Entwurfsskizzen. Erst wenn alle Pläne wieder stimmen, können künftige Projekte verlässlich darauf aufbauen.
* **Für Experten (Lebende Dokumentation als vierte Verifikationsschicht):** In TGD ist Dokumentation kein unverbindlicher Nachtrag, sondern eine **orthogonale Verifikationsschicht**, die ausführbare Beispiele, Links und Dokumentrahmen maschinell prüft. Die strikte Bindung an **Code als Wahrheitsquelle** eliminiert Plan-vs.-Code-Drift (etwa wenn Architektur-Gates während der Implementierung einen geplanten Methodennamen verändert haben). Gleichzeitig garantiert die **ausnahmefreie Schreibgrenze** (`Quellcode = 0`, `Test-Verzeichnis = 0`), dass kein Dokumentations-Commit unbemerkt Code- oder Teständerungen einschleust.

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage:** Status des Versionierungssystems gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; fremde Altlasten (Klasse 3) stoppen den Start sofort.
2. **Auftrags-Konsistenz & grüne Baseline prüfen:** Prüfen, ob Knoten-Rolle (`LIVING_DOCS`) und Zielbeschreibung übereinstimmen und ob der Vorgänger-Knoten (`PHASE_GREEN` oder `GREEN_AUDIT` mit `Status: RESOLVED`) sauber abgeschlossen ist.
3. **Wahrheitsquelle & Handoff-Liste sammeln:** Die real geänderten Quellcode-Dateien sowie eine eventuelle Living-Docs-Diagnoseliste aus `PHASE_GREEN` (*Diagnose-statt-Edit-Regel*) und relevante Nachbar-Handbücher als Arbeitsbasis bereitstellen.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **`Code-as-Source-of-Truth` (Anti-Drift-Regel):**
   * Sämtliche öffentlichen API-Namen, Modulpfade, Funktionssignaturen, Rückgabetypen, Fehlermeldungen, CLI-Optionen und Exit-Codes werden **direkt am realen Quellcode** verifiziert.
   * Entwurfsnamen aus früheren Analyse- oder Hypothesenberichten dürfen **niemals ungeprüft** in produktive Handbücher kopiert werden.
2. **Nachbarschafts- & Index-Scan:**
   * Neben dem primären bzw. neu erstellten Handbuch systematisch alle angrenzenden Anwender-Guides, Entwickler-Referenzen, Ordner-Indizes und bekannte Einschränkungen auf veraltete Signaturen, tote Links oder geänderte Konzepte prüfen.
3. **Ausführbarkeits- & Fence-Hygiene:**
   * Fachliche Code-Beispiele so schreiben, dass die automatische Living-Docs-Prüfung sie real ausführen und gegen die tatsächliche Ausgabe verifizieren kann.
   * Nicht-ausführbare Skizzen, Vorlagen, Diagramme oder Pseudocode strikt in nicht-ausführbare Code-Blöcke (z. B. `text`, `markdown` mit passenden verschachtelten Fences oder `mermaid`) setzen — niemals als ausführbare Sprachblöcke tarnen.
4. **Idempotente Rahmen- & Navigations-Synchronisation:**
   * Automatische Dokumentrahmen und Index-Tabellen aktualisieren und zwingend durch einen **zweiten Synchronisationslauf** belegen, dass der Zustand stabil und idempotent ist (`0` weitere geänderte Dateien).
5. **Artefakt-Hygiene & ehrliche Abschluss-Meldung:**
   * Temporäre Dokumentations-Artefakte gemäß dem [3-Zustands-Lebenszyklus](./README.md#43-allgemeiner-3-zustands-lebenszyklus-temporärer-artefakte) einordnen.
   * Liegt noch ein abgeschlossenes Audit-Protokoll (`Status: RESOLVED`) im Test-Verzeichnis, wird dieses **nicht** in `NODE_LIVING_DOCS` selbst gelöscht oder verschoben, sondern im Abschlussbericht ausdrücklich als fällige 1-Schritt-Abschluss-Hygiene für die Orchestrierung ausgewiesen.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Ein reales Code-Beispiel in der Doku deckt einen echten Defekt im Quellcode auf** | Quellcode **nicht** still in `LIVING_DOCS` patchen! Stoppen, reproduzierbaren Befund sauber dokumentieren und einen neuen Bugfix-/TGD-Durchlauf anstoßen. | Wahrung der Schreibgrenze & ehrliche Fehlerkultur |
| **Entwurf aus `HYPOTHESIS` weicht vom realen Quellcode ab** | Der reale Quellcode gewinnt immer. Das Handbuch beschreibt ausschließlich das tatsächlich implementierte Verhalten (bei Bedarf kurzer Hinweis auf bewusste Abweichung im Zyklus-Bericht). | Null Plan-vs.-Code-Drift |
| **Neues Handbuch erzeugt breiten Navigations-/Footer-Diff über viele bestehende Dokumente** | Erwartetes Verhalten automatischer Navigations-Rahmen — unveränderte Fremd-Inhalte nicht manuell berühren und den automatischen Sync-Anteil im Abschlussbericht transparent benennen. | Nachvollziehbarer, sauberer Doku-Commit |
| **Abgeschlossenes Audit-Protokoll liegt noch im Test-Verzeichnis** | Strikte Schreibgrenze einhalten (`Test-Verzeichnis = 0`); die fällige Archivierung oder Entfernung klar als nachgelagerte Abschluss-Hygiene für die Orchestrierung protokollieren. | Ausnahmefreie Schreibgrenze |
| **Fehlende Konvention für Berichts- oder Rahmen-Syntax** | Vor dem Editieren die jeweiligen Projekt-Konventionen prüfen und nach jeder Änderung mit dem automatischen Prüfer verifizieren. | `0` Rahmen- oder Doku-Diagnosen |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Der Knoten `LIVING_DOCS` (und damit der gesamte TGD-Zyklus) gilt genau dann als abgeschlossen, wenn alle fünf objektiven Kriterien erfüllt sind:

1. **Quellcode-Treue belegt:** Alle neuen und aktualisierten Handbücher, Beispiele und Indizes spiegeln nachweislich den realen Quellcode wider (keine ungeprüften Entwurfs-Namen).
2. **Idempotente Synchronisation nachgewiesen:** Der zweite Lauf der automatischen Rahmen-/Index-Synchronisation meldet `0` weitere Änderungen.
3. **Alle Doku-Gates & relevante Tests grün:** Rahmen-Prüfung, ausführbare Living-Docs-Prüfung und die dazugehörigen Test-Gates laufen mit Exit-Code `0` und `0` Diagnosen durch.
4. **Schreibgrenzen-Nachweis erbracht:** Der Status des Versionierungssystems weist ausschließlich Dokumentationsdateien aus — **`0` Änderungen an Quellcode und am Test-Verzeichnis**.
5. **Abschluss-Hygiene klar dokumentiert:** Offene nachgelagerte Aufräum- oder Archivierungsschritte (z. B. ein abgeschlossenes Audit-Protokoll im Test-Verzeichnis oder temporäre Lauf-Tickets) sind im Abschlussbericht explizit benannt.

> [!TIP]
> **Konkrete `qb-cubie`-Kommandos & Ablagepfade:** Die exakten Sync-, Check- und Pytest-Kommandos sowie der konkrete 3-Zustands-Lebenszyklus für `qb-cubie` stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md) und den [Dokumentrahmen-Konventionen](../dev/DEV-GUIDE_DocFrame-Conventions.md).

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
