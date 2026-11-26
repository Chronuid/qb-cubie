<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DEV-GUIDE: `CUBIE_DOC_FRAME_*`-Konventionen für Agenten

![Cubie](../.assets/cubie-logo-written.png)

Kompakte Kurzreferenz aller aktuellen `CUBIE_DOC_FRAME_*`-Rahmenkonventionen (`CUBIE_DOC_FRAME_1` bis `CUBIE_DOC_FRAME_3`), Zonen, Attribute, Prüfregeln und Sync-Kommandos für Agenten.

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

## 1. Welches Preset wofür?

| Preset | Einsatzbereich | Pflicht-Zonen | Besonderheit |
| :--- | :--- | :--- | :--- |
| **`CUBIE_DOC_FRAME_1`** | Handbücher (`GUIDE_*.md`), Dev-Guides (`DEV-GUIDE_*.md`), Essays, `README.md` ohne Auto-Index | `head`, `foot` | Zentrierter Kopf mit Titel, Banner, Intro, optionalem Disclaimer und Quick-Nav |
| **`CUBIE_DOC_FRAME_2`** | Agenten-Berichte, Analysen (`ANALYSIS*.md`), Audits, Hypothesen, TGD-Protokolle | `head`, `foot` | Provenance-Header (`env`, `model`, `effort`) + optionaler `PromptSlot` |
| **`CUBIE_DOC_FRAME_3`** | Ordner-Indizes und Routing-`README.md`s (z. B. `docs/README.md`, `docs/dev/README.md`) | `head`, `router`, `foot` | Wie `FRAME_1`, plus automatisch generierte Index-Tabelle/Linkliste in `zone="router"` |

---

## 2. Tag-Syntax & gemeinsame `head`-Attribute

Rahmen werden als einzeilige HTML-Kommentar-Paare außerhalb von Code-Fences notiert (`service_core.markdown.DirectiveSpanScanner("frame")`):
* **Strikte Anführungszeichen (`mode="quoted"`):** Alle Attributwerte müssen in doppelten oder einfachen Anführungszeichen stehen (`key="val"` / `key='val'`). Ungequotete Werte (wie `order=10`) oder fehlerhafte Tokens werden **nicht** ignoriert, sondern sofort per `ValueError("STATE-GUARD: ...")` abgewiesen.
* **Geschlossene & einzeilige Tags:** Unabgeschlossene Rahmen (`<!-- /qb:frame -->` fehlt) sowie unvollständige Öffnungs-Tags ohne `-->` auf derselben Zeile lösen `DOCFRAME-MISSING` aus.

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
...
<!-- /qb:frame -->
```

**Gemeinsame Attribute im `zone="head"`-Tag:**

| Attribut | Typ / Werte | Wirkung |
| :--- | :--- | :--- |
| `id` *(Pflicht)* | `CUBIE_DOC_FRAME_1\|2\|3` | Wählt das `FramePattern` (unbekannte ID $\to$ `STATE-GUARD`-Fehler) |
| `zone` | `head` (Default), `router`, `foot` | Kennzeichnet die Rahmen-Zone |
| `banner` | Dateiname oder Relativpfad | Banner-Bild für `FRAME_1`/`3` (Default: `cubie-logo-written.png` aus `docs/.assets/`) |
| `label` | String | Überschreibt den `# H1`-Titel als Anzeigetext in Routern und Tabellen |
| `order` | Integer (z. B. `10`, `20`) | Sortier-Priorität im Ordner (`README.md` ohne `order` $\to$ `order` aufsteigend $\to$ alphabetisch) |
| `routable` | `true\|false` (`1\|0`, `yes\|no`) | Blendet das Dokument bei `false` aus dynamischen Routern aus (0-Byte-Dateien immer `false`) |

---

## 3. Zonen- & Slot-Regeln je Preset

### `CUBIE_DOC_FRAME_1` (Standard-Dokumente)
* **`head`:** H1-Titel (`# ...`), Banner und Kurzbeschreibung stehen **vor dem ersten `---`**. Der erste Textabsatz unter dem Banner wird automatisch als `summary` für `CatalogRouter`-Tabellen extrahiert.
* **Optionaler Disclaimer:** Dokument-spezifischer Text zwischen dem 1. und 2. `---` bleibt bei Updates über `DisclaimerSlot` erhalten.
* **Verpflichtender erkenntnistheoretischer Hinweis (`EPISTEMIC_NOTICE_TEXT`):** Wird als fester `StaticBlock` (`EPISTEMIC_NOTICE`) aus `src/qb_cubie/core/services/doc_frame/presets.py` direkt vor der Quick-Nav eingeblendet. Um den Hinweistext zentral für das gesamte Repository zu ändern, genügt die Anpassung von `EPISTEMIC_NOTICE_TEXT` in `presets.py` (der Erkennungsmarker `"erkenntnistheoretischen Grenzen"` muss erhalten bleiben, damit `DisclaimerSlot` Altbestände sauber dedupliziert) gefolgt von `DocFrame.update(excludes=DOC_EXCLUDES)`.
* **`foot`:** Wird vollständig von `DocFrame` gerendert (`<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->` … `<!-- /qb:frame -->`).

### `CUBIE_DOC_FRAME_2` (Agenten-Berichte & Audits)
* **Pflicht-Attribute im `head`-Tag:** `env="..."` (`Plattform / Umgebung`), `model="..."` (`Modell`), `effort="..."` (`Reasoning-Effort`). Tag-Attribute überschreiben beim Update die jeweiligen Bullet-Werte.
* **Vor dem ersten `---`:** Nur optionale `# H1`-Überschrift und Bullet-Zeilen im Format `- **Schlüssel:** Wert` (alle Zusatzfelder wie `Analysedatum`, `Synthesebasis`, `Stand` bleiben erhalten; sonstige Zeilen werden beim Update entfernt).
* **Nach dem ersten `---` (`PromptSlot`):** Freier Platz für Aufgabenstellung, Leitfragen oder mehrzeilige Codeblöcke (z. B. `git log -n 1`).
* Details & Kopiervorlage: [Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`)](./DEV-GUIDE_Agent-Reports.md).

### `CUBIE_DOC_FRAME_3` (Index- & Routing-Dokumente)
* Besitzt `head` und `foot` wie `FRAME_1` sowie mindestens eine **`zone="router"`**.
* **Router-Attribute:**
  * `mode="table"` (Default, 2-spaltige Tabelle `Dokument | Inhalt und Geltung`) oder `mode="links"` (`[↦ | ... | ↤]`-Liste).
  * `dir="."` (aktueller Ordner) oder Repo-/ordnerrelativer Pfad (z. B. `dir="docs/dev/services"`).
  * `recursive="false"` (Default) oder `"true"`; optional `glob="*.md"`.
  * Das eigene Index-Dokument sowie `README.md` werden automatisch ausgeschlossen.

---

## 4. Prüfregeln (`CUBIE_DOCFRAME_RULES` via `DocFrame.check()`)

Die vier `WorkspaceCheckRuleProtocol`-Regeln werden nativ über `DocFrame.check()` (`qb_cubie.core.service_core.FileCheckRunner` mit `FileContextCache` und `depends_on=("DOCFRAME-MISSING",)` auf `DocFrameOutdated`) ohne `DocEnsurance`-Kopplung ausgewertet:

| Regel-ID | Auslöser |
| :--- | :--- |
| `DOCFRAME-MISSING` | Ungeschlossener `qb:frame`-Tag, fehlende `head`-/`foot`-Zone oder fehlende `router`-Zone bei `FRAME_3` |
| `DOCFRAME-PROVENANCE-INCOMPLETE` | Pflichtfeld (`Plattform / Umgebung`, `Modell`, `Reasoning-Effort`) in `FRAME_2` fehlt oder ist leer |
| `DOCFRAME-BROKEN-ROUTE` | Banner-Asset oder relativer Markdown-Link innerhalb eines Rahmens fehlt im `WorkspaceView` |
| `DOCFRAME-OUTDATED` | Gespeicherter Rahmen-Inhalt weicht vom aktuellen `DocumentCatalog`/Renderer ab |

---

## 5. Synchronisieren & Verifizieren

Nach dem Anlegen oder Ändern gerahmter Dokumente immer synchronisieren und gegen Rahmen- sowie Doku-Regeln prüfen (Details: [Service-Core](../services/GUIDE_Service-Core.md), [DocFrame-Handbuch](../services/GUIDE_DocFrame.md), [DocFrame-Internals](./services/DEV-GUIDE_DocFrame.md); CLI-Exit-Codes: `0` = bestanden, `1` = Prüffehlschlag, `2` = `STATE-GUARD`/I/O-Fehler):

```bash
qb-cubie docframe update <pfad/zur/datei.md>
```

```bash
qb-cubie docframe update docs/dev/README.md
```

```bash
qb-cubie docframe check <pfad/zur/datei.md> --format text
```

```bash
qb-cubie docensurance check <pfad/zur/datei.md> --format text
```

```bash
.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py
```

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
[↦ | Core-Internals | ↤](./core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

[↦ | DEV-GUIDE: Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`) | ↤](./DEV-GUIDE_Agent-Reports.md)  
[↦ | DEV-GUIDE: `CUBIE_DOC_FRAME_*`-Konventionen für Agenten | ↤](./DEV-GUIDE_DocFrame-Conventions.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Service-Architektur & strikte Service-Isolation | ↤](./DEV-GUIDE_Services.md)  
[↦ | DEV-GUIDE: TGD-Workflow-Profil für `qb-cubie` | ↤](./DEV-GUIDE_TGD-Workflow.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
