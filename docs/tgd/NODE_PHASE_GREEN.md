<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" order="40" -->
<div align="center">

# Knoten: PHASE_GREEN (Implementierung unter Test-Freeze)

![Cubie](../.assets/cubie-logo-written.png)

Zweiter verbindlicher Kernknoten von TGD: Implementiert die Lösung ausschließlich im Quellcode unter striktem Test-Freeze und nutzt bei unbehebbaren Test-Widersprüchen die kontrollierte Rückwärtstür (`NODE_GREEN_AUDIT`).

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
| **Rolle** | Verbindlicher Kernknoten 2 — Quellcode-Implementierung unter strikter Freeze-Disziplin |
| **Eintrittsbedingungen ($P$)** | Eingefrorener `PHASE_RED`-Stand mit reproduzierbar roten Vertrags-Tests (oder Rückkehr nach `NODE_GREEN_AUDIT` mit Status `REFUTED` samt Audit-Protokoll), saubere [Pre-Flight-Triage](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) |
| **Erlaubte Schreibziele** | Ausschließlich Quellcode — sowie im begründeten Eskalationsfall **genau ein** strukturiertes Audit-Protokoll im Test-Bereich |
| **Eingefrorene Bereiche (Tabu)** | **Sämtlicher Test-Code** (keine Edits, kein `skip`, kein Abschwächen von Assertions) sowie die **Produkt-Dokumentation** (`0` Änderungen!) |
| **Abnahme ($Q$)** | *Regulär:* Alle funktionalen Tests, Architektur-Wächter, Linter, Typprüfer & aktiven Stil-Gates grün + Advisory-Check für pausierte Stil-Gates + `0` Edits an Test-Code und Doku. *Eskalation:* Unstrittige Tests/Gates grün + belegtes Audit-Protokoll |
| **Folge-Knoten** | [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md) *(regulärer Ausgang `GREEN`)* oder [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) *(Eskalations-Ausgang)* |

---

## 2. Wofür dieser Knoten da ist

* **Einfach erklärt (für Einsteiger):** Jetzt baut der Handwerker das Haus genau nach der versiegelten Checkliste des Bauprüfers. Zwei goldene Regeln schützen dabei die Qualität: Erstens darf der Handwerker die Checkliste niemals heimlich selbst umschreiben — entdeckt er aber einen echten Widerspruch in der Checkliste, darf er ehrlich die offizielle Rückwärtstür nutzen und einen Mängelbericht (**`GREEN_AUDIT`**) schreiben. Zweitens überarbeitet er während des Bauens noch nicht den Bauplan (die Dokumentation): Der kommt sauber im nächsten Schritt dran, damit Bau-Änderungen und Doku-Änderungen nicht durcheinanderpurzeln.
* **Für Experten (Freeze-Disziplin, L4-Muster & Zwei-Stufen-Gate):** `PHASE_GREEN` trennt Implementierung strikt von Test-Modifikation und Dokumentations-Pflege. Dadurch beweist der resultierende Diff eindeutig, dass allein der neue Produktivcode alle eingefrorenen Verträge erfüllt. Drei strukturelle Konfliktregeln halten diesen Knoten sauber:
  1. **Unantastbarkeit des Test-Codes** (Verhinderung von *Test-Hacking* und Bestätigungsfehlern),
  2. **L4-Muster für Living-Docs-Tests** (keine stillen Dokumentations-Edits in `PHASE_GREEN`; veraltete Handbuch-Diagnosen sind geplantes Übergabe-Signal an `NODE_LIVING_DOCS`),
  3. **Zwei-Stufen-Gate-Modell** (harte automatische Gates plus verbindlicher Advisory-Check auf geänderten Quellcode-Dateien für vorübergehend pausierte Stilregeln).

---

## 3. Eintritt & Pre-Flight ($P$)

1. **Pre-Flight-Triage:** Status des Versionierungssystems gemäß dem [3-Klassen-Modell](./README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell) prüfen; fremde Altlasten (Klasse 3) stoppen den Start sofort.
2. **Auftrags-Konsistenz & Eingaben prüfen:** Prüfen, ob Knoten-Rolle (`PHASE_GREEN`) und Zielbeschreibung konsistent sind. Reproduzierbarkeit der eingefrorenen roten Tests verifizieren.
3. **Rückkehr nach `REFUTED`-Audit:** Kehrt der Automat aus [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) mit `Status: REFUTED` zurück, ist das bestehende Audit-Protokoll **Pflicht-Eingabe**: Den dort belegten Quellcode-Defekt zuerst lesen und gezielt beheben.

---

## 4. Arbeits- & Meta-QA-Heuristiken

1. **Inkrementelles Grün-Schalten von innen nach außen:**
   * Erst neue Unit- und Vertrags-Tests grün schalten,
   * danach die betroffene Bestands-Test-Suite prüfen,
   * anschließend statische Architektur- und Meta-Wächter ausführen,
   * zum Schluss Linter, Typprüfer und Stil-Gates abnehmen.
2. **Zwei-Stufen-Gate-Modell (für aktive und vorübergehend pausierte Stil-Gates):**
   * **Stufe 1 — Harte automatische Gates (blockierend):** Alle aktiven funktionalen Test-Suiten, Architektur-Wächter, Linter, Typprüfer und aktiven Stilregeln müssen **`0` Fehler** melden.
   * **Stufe 2 — Verbindlicher Advisory-Check für pausierte Stil-Gates:** Ist ein Stil-Gate (z. B. ein Größen- oder Komplexitätslimit) im Projekt vorübergehend global pausiert, prüft dieser Knoten **alle neu angelegten und geänderten Quellcode-Dateien** dennoch eigenständig gegen die pausierte Regel. Ziel sind **`0` neue Verstöße**; jede bewusst in Kauf genommene Überschreitung muss im Abschlussbericht knapp fachlich begründet werden. Sobald das Gate wieder global aktiv ist, entfällt der manuelle Advisory-Schritt automatisch.
3. **Beobachtender Living-Docs-Check (L4-Muster):** Erst *nach* bestandener funktionaler und statischer Abnahme werden eventuell vorhandene Repo-weite Living-Docs- und Dokumentrahmen-Tests **rein diagnostisch** ausgeführt (Details siehe Abschnitt 5).
4. **Strukturierte `GREEN_AUDIT`-Eskalation statt Produktivcode-Aufweichung:** Stößt die Implementierung auf einen roten Test, der nur durch fachwidriges Aufweichen des Quellcodes oder durch Änderung der Test-Suite lösbar wäre, wird **sofort eskaliert**:
   * Keine Änderungen am Test-Code, keine Notlösung im Quellcode.
   * Stattdessen wird genau ein strukturiertes Audit-Protokoll angelegt mit: betroffenem Testpfad und Zeilennummer, reproduzierbarem Fehlerbeleg, sachlicher Gegenüberstellung mit den geltenden Verträgen/Konventionen und mindestens zwei konkreten Lösungsoptionen ohne Aufweichung des Quellcodes.

---

## 5. Kantenfälle & Eskalationsregeln

| Situation / Konflikt | Verbindliche Reaktion | Ziel / Ausgang |
| :--- | :--- | :--- |
| **Living-Docs- oder Rahmen-Prüfung schlägt wegen neuer/geänderter API fehl (L4-Muster)** | Ursache scharf trennen! Liegt der Fehler an *bestehenden Dokumentationsdateien* (veraltete Beispiele, Signaturen oder Rahmen) $\to$ **Dokumentation NICHT anfassen!** Diagnosen als geplantes Übergabe-Backlog für `NODE_LIVING_DOCS` protokollieren. Liegt der Fehler hingegen an einem *Defekt im neuen Quellcode* (z. B. defekter Scanner/Parser) $\to$ im Quellcode beheben. | Reiner Quellcode-Diff (`Doku = 0`) |
| **Unlösbarer Widerspruch in einem eingefrorenen Test oder einer Test-Fixture** | Test-Code nicht anfassen, Quellcode nicht aufweichen; alle unstrittigen Tests/Gates grün bringen, strukturiertes Audit-Protokoll verfassen und sauber übergeben. | Kontrollierter Rücksprung zu [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md) |
| **Pausiertes Stil-Gate wird von neuer Funktion im Quellcode überschritten** | Funktion bevorzugt sauber in kleinere Einheiten zerlegen; nur bei zwingendem technischem Grund ausnahmsweise im Abschlussbericht dokumentieren. | Verhinderung stiller Stil-Drift |
| **Rückkehr nach `REFUTED` — und später tritt ein weiterer Test-Widerspruch auf** | Das bestehende Audit-Protokoll mit der früheren Widerlegung **nicht überschreiben**, sondern einen neuen datierten Abschnitt anhängen. | Lückenlose Audit-Historie |
| **Test-Datei enthält einen offensichtlichen Tippfehler oder Lint-Fehler** | Auch „offensichtliche“ Kleinigkeiten im Test-Code bleiben in `PHASE_GREEN` tabu! Entweder sauber per Audit-Protokoll eskalieren oder regulär zurück in die Test-Rolle übergeben. | Ausnahmefreie Freeze-Disziplin |

---

## 6. Austrittsbedingungen & Abnahme ($Q$)

Je nach Verlauf endet `PHASE_GREEN` über genau einen von zwei objektiv prüfbaren Ausgängen:

### Ausgang A — Regulärer Abschluss (`GREEN` $\to$ [`NODE_LIVING_DOCS`](./NODE_LIVING_DOCS.md))
1. **Harte Gates 100 % grün:** Alle funktionalen Tests, Architektur-/Meta-Wächter, Linter, Typprüfer und aktiven Stil-Gates laufen mit `0` Fehlern durch.
2. **Advisory-Check dokumentiert:** Alle vorübergehend pausierten Stil-Gates wurden auf sämtlichen neuen/geänderten Quellcode-Dateien geprüft (`0` Verstöße oder knapp begründete Ausnahme).
3. **Beobachtender Living-Docs-Check ausgewertet:** Etwaige veraltete Doku-Diagnosen sind als Handoff-Liste für `NODE_LIVING_DOCS` protokolliert — ohne selbst eine Doku-Datei zu verändern.
4. **Schreibgrenzen-Nachweis erbracht:** Der Diff im Versionierungssystem weist **`0` Änderungen an Test-Code** und **`0` Änderungen an der Produkt-Dokumentation** aus.

### Ausgang B — Kontrollierte Eskalation (`GREEN_AUDIT` $\to$ [`NODE_GREEN_AUDIT`](./NODE_GREEN_AUDIT.md))
1. **Unstrittiger Bestand grün:** Sämtliche nicht vom Widerspruch betroffenen Tests, Architektur-Wächter, Linter und Typprüfer sind grün.
2. **Audit-Protokoll vollständig:** Genau ein strukturiertes Audit-Protokoll mit Pfaden, Zeilennummern, Reproduktionsbeleg, Vertragsvergleich und Lösungsoptionen wurde angelegt.
3. **Schreibgrenzen-Nachweis erbracht:** **`0` Änderungen an Test-Code** und **`0` Änderungen an der Produkt-Dokumentation**.

> [!TIP]
> **Konkrete `qb-cubie`-Kommandos & Advisory-Einzeiler:** Die exakten `pytest`-, `ruff`-, `pylint`-, `mypy`- und Advisory-Kommandos sowie der Pfad der Audit-Datei stehen in [`DEV-GUIDE: TGD-Workflow-Profil für qb-cubie`](../dev/DEV-GUIDE_TGD-Workflow.md).

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
