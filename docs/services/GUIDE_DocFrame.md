<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DocFrame

![Cubie](../.assets/cubie-logo-written.png)

`DocFrame` synchronisiert die zentrierten Dokument-Rahmen und Index-Router über alle Verzeichnistiefen hinweg,  
während `DocEnsurance` über `CUBIE_DOCFRAME_RULES` prüft,  
ob alle nicht-exkludierten Markdown-Dateien gültige und aktuelle Rahmen besitzen.

---

> **Hinweis zur Rahmen-Synchronisation:**  
> Jedes Dokument liefert seine Routing-Metadaten (Titel, Kurzbeschreibung, Sortierung) direkt über seinen `zone="head"`-Block,  
> sodass neue Guides und Bereichs-Indizes durch `DocFrame.update()` ohne Pflege statischer Routen-Listen aktualisiert werden.

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](./GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Drei Rahmen-Standards: Handbücher (`FRAME_1`), Feldberichte (`FRAME_2`) & Index-Hubs (`FRAME_3`)

In `qb-cubie` decken drei komplementäre Rahmen-Presets alle Dokumenttypen im Repository ab:

1. **`CUBIE_DOC_FRAME_1` (Handbücher & Dev-Guides):** Zentrierter `<div align="center">`-Kopf mit Titel, Banner aus `.assets/`, Erklärung, optionaler Disclaimer-Zone zwischen `---` und kompakter `•`-Navigation sowie ein selbstaktualisierender Fuß mit Logo, `FolderRouter`-Gruppen und kontextsensitivem `SiblingRouter`.
2. **`CUBIE_DOC_FRAME_2` (Provenance-Rahmen für Gutachten, Hypothesen & Berichte):** Schlanker Herkunftsnachweis (`**Dokument-Informationen & Herkunft:**`) für Analysen, Audits und Feldberichte, die während der Entwicklung oder in Benchmark-Läufen entstehen.
3. **`CUBIE_DOC_FRAME_3` (Index- & Routing-Dokumente wie `README.md`):** Ergänzt `head` und `foot` um eine dedizierte **`zone="router"`** im Dokumentkörper, die Katalog-Tabellen (`mode="table"`) oder Link-Listen (`mode="links"`) automatisch aus dem `DocumentCatalog` aufbaut.

| Preset | Ziel-Dokumente | Zonen (`zone=...`) | Besonderheit beim Auto-Routing |
| :--- | :--- | :--- | :--- |
| **`CUBIE_DOC_FRAME_1`** | Reguläre Guides & Dev-Guides (`GUIDE_*.md`, `DEV-GUIDE_*.md`) | `head`, `foot` | Dynamischer Fuß aus globalen `FolderRouter`-Gruppen + kontextuellem `SiblingRouter` für Unterordner. |
| **`CUBIE_DOC_FRAME_2`** | Gutachten, Hypothesen, Audits & Feldberichte | `head`, `foot` | Schlanker Provenance-Kopf (`env`, `model`, `effort` + Zusatzfelder) + Standard-Fuß. |
| **`CUBIE_DOC_FRAME_3`** | Dedizierte Routing- & Index-Dokumente (`README.md`) | `head`, `router`, `foot` | Generiert Index-Tabellen (`\| Dokument \| Inhalt und Geltung \|`) oder Routen-Listen aus dem `DocumentCatalog`. |

---

## 2. Lego-Bausteine in Python zusammenstecken

Alle drei Standards werden in Python schrittweise aus kleinen, zustandslosen Bausteinen zusammengesetzt. Im ersten Schritt definieren wir die Kompakt-Navigation für den Kopf sowie die dynamischen `FolderRouter`- und `SiblingRouter`-Bausteine:

```python session=docframe_presets
from qb_cubie.services.docframe import (
    CatalogRouter, CompactNav, FolderRouter, RouteGroup, SiblingRouter
)

HEADER_QUICK_NAV = CompactNav(
    routes=(
        ("README", "README.md"),
        ("QA-Handbuch", "docs/GUIDE_Quality-Assurance.md"),
        ("DocEnsurance", "docs/services/GUIDE_DocEnsurance.md"),
    )
)

GUIDE_ROUTER = FolderRouter(dir="docs", glob="GUIDE_*.md")
SERVICE_ROUTER = FolderRouter(dir="docs/services", glob="GUIDE_*.md")
CONTEXT_ROUTER = SiblingRouter(
    hubs=(
        ("Entwicklerübersicht & Internals", "docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md"),
        ("Hintergrund & Essays", "docs/misc/README.md"),
        ("Feature-Drafts: Virtualisierung", "docs/feature-drafts/virtualization/README.md"),
    )
)
print(f"Quick-Nav: {len(HEADER_QUICK_NAV.routes)} | Hubs: {len(CONTEXT_ROUTER.hubs)}")
```

<details>
<summary>Ergebnis</summary>

```text
Quick-Nav: 3 | Hubs: 3
```
</details>

Im zweiten Schritt bündeln wir die dynamischen Router in einem gemeinsamen `<div align="center">`-Fußbaustein (`STD_FOOTER_BLOCKS`) und konfigurieren den `CatalogRouter` (`AUTO_INDEX_ROUTER`) für Index-Tabellen:

```python session=docframe_presets
from qb_cubie.services.docframe import AssetImage, CenterWrap, Divider

STD_FOOTER_BLOCKS = (
    Divider(),
    Divider(),
    CenterWrap(
        tag="div",
        blocks=(
            AssetImage(path="docs/.assets/cubie-small.png", alt="Cubie"),
            GUIDE_ROUTER,
            SERVICE_ROUTER,
            CONTEXT_ROUTER,
        ),
    ),
)

AUTO_INDEX_ROUTER = CatalogRouter(
    default_mode="table",
    exclude=("README.md",),
    extract_summary=True,
)
print(f"Footer-Blöcke: {len(STD_FOOTER_BLOCKS)} | Index-Mode: {AUTO_INDEX_ROUTER.default_mode}")
```

<details>
<summary>Ergebnis</summary>

```text
Footer-Blöcke: 3 | Index-Mode: table
```
</details>

Im dritten Schritt setzen wir daraus die drei importierbaren Standards `CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` zusammen:

```python session=docframe_presets
from qb_cubie.services.docframe import (
    DisclaimerSlot, FramePattern, HeaderContentSlot, PromptSlot, ProvenanceBlock, TitleSlot
)

STD_HEAD_BLOCKS = (
    CenterWrap(
        tag="div",
        blocks=(HeaderContentSlot(), Divider(), DisclaimerSlot(), Divider(), HEADER_QUICK_NAV),
    ),
)
PROVENANCE_KEYS = ("Plattform / Umgebung", "Modell", "Reasoning-Effort")

CUBIE_DOC_FRAME_1 = FramePattern(id="CUBIE_DOC_FRAME_1", head=STD_HEAD_BLOCKS, foot=STD_FOOTER_BLOCKS)
CUBIE_DOC_FRAME_2 = FramePattern(
    id="CUBIE_DOC_FRAME_2",
    head=(TitleSlot(optional=True), ProvenanceBlock(required_keys=PROVENANCE_KEYS), Divider(), PromptSlot(optional=True)),
    foot=STD_FOOTER_BLOCKS,
)
CUBIE_DOC_FRAME_3 = FramePattern(
    id="CUBIE_DOC_FRAME_3", head=STD_HEAD_BLOCKS, router=(AUTO_INDEX_ROUTER,), foot=STD_FOOTER_BLOCKS,
)
print(f"Presets: {CUBIE_DOC_FRAME_1.id}, {CUBIE_DOC_FRAME_2.id}, {CUBIE_DOC_FRAME_3.id}")
```

<details>
<summary>Ergebnis</summary>

```text
Presets: CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3
```
</details>

---

## 3. Referenzierung in den Dokumenten

### A. Handbuch-Rahmen (`CUBIE_DOC_FRAME_1`)
In Guides wählt das optionale Attribut `banner="..."` ein Bild aus `.assets/`, während optionale Attribute wie `label="..."`, `order="10"` oder `routable="false"` die Darstellung und Sortierung in den Routern steuern. Der `# Titel`, die Erklärung sowie der optionale Disclaimer zwischen den beiden `---` bleiben geschützt:

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# RBT-Nutzungsmuster

![Cubie](.assets/cubie-logo-written.png)

RBT delegiert eine sprachlich formulierte Prüfregel an einen Reviewer...

---

> Optionaler dokument-spezifischer Hinweis oder Disclaimer.

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->
```

### B. Provenance-Rahmen im Eifer des Gefechts (`CUBIE_DOC_FRAME_2`)
Für Hypothesen, Pilot-Analysen und Meta-Fragen hält `CUBIE_DOC_FRAME_2` die Herkunfts-Metadaten konsistent. Standardfelder lassen sich direkt im Marker-Tag setzen (`env`, `model`, `effort`), während zusätzliche freie Aufzählungspunkte (wie `Analysedatum` oder `Synthesebasis`) sowie ein optionaler Fragetext nach `---` beim Update erhalten bleiben:

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Gemini-App" model="Gemini-4-Argon" effort="High" -->
# Hypothesen und Quick-Fixes zum v6-Pilotlauf

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Gemini-App
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 12. November 2026
- **Synthesebasis:** `PILOTANALYSE-20261112.md` (Antigravity & Codex)

---
<!-- /qb:frame -->
```

### C. Selbstaktualisierende Index-Tabellen (`CUBIE_DOC_FRAME_3`)
In Bereichs-Indizes (`README.md`) erzeugt ein `zone="router"`-Block aus den Titeln und Kurzbeschreibungen der Nachbardokumente vollautomatisch eine Übersichtstabelle (`mode="table"`) oder Routen-Liste (`mode="links"`):

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Clean-Code Pragmatismus](./Clean-Code-Pragmatism.md) | Dieser Essay diskutiert kontextabhängige Entwurfsentscheidungen und pragmatische Clean-Code-Prinzipien. |
<!-- /qb:frame -->
```

---

## 4. Synchronisation (`DocFrame.update`) und Prüfung (`DocEnsurance`)

Die Aktualisierung der Dateien und die Verifikation in der Test-Suite greifen über dieselben Pattern-Objekte und das Regel-Tupel `CUBIE_DOCFRAME_RULES` ineinander:

```python
from qb_cubie.services import (
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
    CUBIE_DOC_RULES,
    CUBIE_DOC_STYLE,
    CUBIE_DOCFRAME_RULES,
    DocEnsurance,
    DocFrame,
)


def sync_all_frames() -> None:
    DocFrame.update(
        pattern=[CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3],
        excludes=("experiments", "GUTACHTEN.md"),
    )


def verify_all_docs() -> None:
    DocEnsurance(
        pattern=[CUBIE_DOC_STYLE, CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3],
        rules=(CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES),
        excludes=("experiments", "GUTACHTEN.md"),
    ).run()


print(f"Sync: {sync_all_frames.__name__} | Rules: {len(CUBIE_DOCFRAME_RULES)}")
```

<details>
<summary>Ergebnis</summary>

```text
Sync: sync_all_frames | Rules: 4
```
</details>

Für alle geprüften Dokumente stellt `CUBIE_DOCFRAME_RULES` über vier Diagnose-Regeln (`DOCFRAME-MISSING`, `DOCFRAME-OUTDATED`, `DOCFRAME-BROKEN-ROUTE` und `DOCFRAME-PROVENANCE-INCOMPLETE`) sicher, dass Rahmen vollständig, aktuell und frei von toten Links sind.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Error while trying to load the image](../.assets/cubie-small.png)

[↦ | Qualitätssicherung: Handbuch & Methodik | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](../GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  

[↦ | DocEnsurance: Lebende Dokumentation | ↤](./GUIDE_DocEnsurance.md)  
[↦ | DocFrame: Dokument-Rahmen & Router | ↤](./GUIDE_DocFrame.md)  
[↦ | Entwicklerübersicht EBT | ↤](../dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</div>
<!-- /qb:frame -->
