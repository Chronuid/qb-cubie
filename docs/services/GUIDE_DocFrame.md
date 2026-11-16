<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DocFrame-Nutzungsmuster (Feature-Draft)

![Cubie](../.assets/cubie-logo-written.png)

`DocFrame` synchronisiert die zentrierten Dokument-Rahmen über alle Verzeichnistiefen hinweg,  
während `DocEnsurance` über `CUBIE_DOCFRAME_RULES` prüft,  
ob alle nicht-exkludierten Markdown-Dateien gültige und aktuelle Rahmen besitzen.

---

> **Status: Feature-Draft (Entwurfsphase).**  
> Dieses Dokument spezifiziert das geplante Nutzungsmuster  
> und die Baustein-Architektur von `DocFrame` als Grundlage für die Test-Suite.

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](./GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Zwei Rahmen-Standards: Handbücher (`FRAME_1`) vs. Feldberichte (`FRAME_2`)

In `qb-cubie` existieren zwei Arten von Dokumenten mit unterschiedlichen Anforderungen an ihre Rahmen:

1. **`CUBIE_DOC_FRAME_1` (Handbücher & Guides):** Zentrierter `<div align="center">`-Kopf mit Titel, Banner aus `.assets/`, Erklärung, Disclaimer-Zone zwischen `---` und kompakter `•`-Navigation sowie ein zentrierter Fuß mit Logo und `[↦ | Label | ↤]`-Routen-Gruppen.
2. **`CUBIE_DOC_FRAME_2` (Provenance-Rahmen für Gutachten, Hypothesen & Berichte):** Schlanker Herkunftsnachweis (`**Dokument-Informationen & Herkunft:**`) für Analysen, Audits und `qa_evolution`-Notizen, die während der aktiven Entwicklung oder in Benchmark-Läufen entstehen.

| Dokument-Typ | Preset | Kopf-Struktur (`zone="head"`) | Fuß-Struktur (`zone="foot"`) |
| :--- | :--- | :--- | :--- |
| **Offizielle Guides & README** | `CUBIE_DOC_FRAME_1` | `<div align="center">`, `# Titel`, Asset-Banner, Kurztext, `---`, Disclaimer, `---`, Kompakt-Links (`•`) | `---`, `---`, `<center>`, `cubie-small.png`, thematische `[↦ \| ... \| ↤]`-Blöcke |
| **Gutachten, Hypothesen & Audits** | `CUBIE_DOC_FRAME_2` | Optionaler `# Titel`, `**Dokument-Informationen & Herkunft:**` (Plattform, Modell, Effort + Zusatzfelder), `---`, optionaler Prompt-Slot | Optionaler schlanker Rück-Router oder Standard-Fuß |

---

## 2. Lego-Bausteine in Python zusammenstecken

Beide Standards werden in Python schrittweise aus kleinen, zustandslosen Bausteinen zusammengesetzt. Im ersten Schritt definieren wir die Navigations-Routen relativ zum Projekt-Root:

```python session=docframe_presets
from qb_cubie.services.docframe import CompactNav, RouteGroup

HEADER_QUICK_NAV = CompactNav(
    routes=(
        ("README", "README.md"),
        ("QA-Handbuch", "docs/GUIDE_Quality-Assurance.md"),
        ("DocEnsurance", "docs/services/GUIDE_DocEnsurance.md"),
    )
)

CORE_ROUTES = RouteGroup(
    routes=(
        ("Qualitätssicherung: Handbuch & Methodik", "docs/GUIDE_Quality-Assurance.md"),
        ("Vertragssemantik: zentrale Referenz", "docs/GUIDE_Contract-Semantics.md"),
        ("EBT: ausführbare Nutzungsmuster", "docs/GUIDE_EBT-Usage-Pattern.md"),
        ("RBT: Reviewer und Nutzung", "docs/GUIDE_RBT-Usage-Pattern.md"),
    )
)
print(f"Quick-Nav: {len(HEADER_QUICK_NAV.routes)} | Core-Routes: {len(CORE_ROUTES.routes)}")
```

<details>
<summary>Ergebnis</summary>

```text
Quick-Nav: 3 | Core-Routes: 4
```
</details>

Im zweiten Schritt bündeln wir die weiterführenden Service-Routen und den dynamischen `FolderRouter` zu einem gemeinsamen Fuß-Baustein (`STD_FOOTER_BLOCKS`):

```python session=docframe_presets
from qb_cubie.services.docframe import AssetImage, CenterWrap, Divider, FolderRouter

SERVICE_ROUTES = RouteGroup(
    routes=(
        ("DocEnsurance: Lebende Dokumentation", "docs/services/GUIDE_DocEnsurance.md"),
        ("DocFrame: Dokument-Rahmen & Router", "docs/services/GUIDE_DocFrame.md"),
    )
)

STD_FOOTER_BLOCKS = (
    Divider(),
    Divider(),
    CenterWrap(
        tag="center",
        blocks=(
            AssetImage(path="docs/.assets/cubie-small.png", alt="Cubie"),
            CORE_ROUTES,
            SERVICE_ROUTES,
            FolderRouter(dir="docs/qa_evolution", exclude=("README.md",)),
        ),
    ),
)
print(f"Footer-Bausteine: {len(STD_FOOTER_BLOCKS)}")
```

<details>
<summary>Ergebnis</summary>

```text
Footer-Bausteine: 3
```
</details>

Im dritten Schritt setzen wir daraus die beiden importierbaren Standards `CUBIE_DOC_FRAME_1` (für Handbücher) und `CUBIE_DOC_FRAME_2` (für Provenance-Berichte) zusammen:

```python session=docframe_presets
from qb_cubie.services.docframe import (
    DisclaimerSlot, FramePattern, HeaderContentSlot, PromptSlot, ProvenanceBlock, TitleSlot
)

CUBIE_DOC_FRAME_1 = FramePattern(
    id="CUBIE_DOC_FRAME_1",
    head=(
        CenterWrap(
            tag="div",
            blocks=(HeaderContentSlot(), Divider(), DisclaimerSlot(), Divider(), HEADER_QUICK_NAV),
        ),
    ),
    foot=STD_FOOTER_BLOCKS,
)

CUBIE_DOC_FRAME_2 = FramePattern(
    id="CUBIE_DOC_FRAME_2",
    head=(
        TitleSlot(optional=True),
        ProvenanceBlock(required_keys=("Plattform / Umgebung", "Modell", "Reasoning-Effort")),
        Divider(),
        PromptSlot(optional=True),
    ),
    foot=STD_FOOTER_BLOCKS,
)
print(f"Presets geladen: {CUBIE_DOC_FRAME_1.id}, {CUBIE_DOC_FRAME_2.id}")
```

<details>
<summary>Ergebnis</summary>

```text
Presets geladen: CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2
```
</details>

---

## 3. Referenzierung in den Dokumenten

### A. Handbuch-Rahmen (`CUBIE_DOC_FRAME_1`)
In Guides wählt das optionale Attribut `banner="..."` ein anderes Bild aus `.assets/`. Der `# Titel`, die Erklärung sowie der optionale Disclaimer zwischen den beiden `---` bleiben geschützt, während Banner-Pfad und `•`-Links am Ende des Kopfs automatisch aktualisiert werden:

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
Für Hypothesen, Pilot-Analysen und Meta-Fragen hält `CUBIE_DOC_FRAME_2` die Herkunfts-Metadaten konsistent. Standardfelder lassen sich direkt im Marker-Tag setzen (`env`, `model`, `effort`), während zusätzliche freie Aufzählungspunkte (wie `Analysedatum` oder `Synthesebasis`) sowie ein optionaler Fragetext vor dem doppelten `---` beim Update erhalten bleiben:

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

---

## 4. Synchronisation (`DocFrame.update`) und Prüfung (`DocEnsurance`)

Die Aktualisierung der Dateien und die Verifikation in der Test-Suite greifen über dieselben Pattern-Objekte ineinander:

```python
from qb_cubie.services import (
    DocEnsurance,
    CUBIE_DOC_RULES, CUBIE_DOC_STYLE, 
    DocFrame, 
    CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOCFRAME_RULES
)

def sync_all_frames() -> None:
    DocFrame.update(
        pattern=[CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2],
        excludes=("experiments", "GUTACHTEN.md"),
    )

def verify_all_docs() -> None:
    DocEnsurance(
        pattern=[CUBIE_DOC_STYLE, CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2],
        rules=(CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES),
        excludes=("experiments", "GUTACHTEN.md"),
    ).run()

print(f"Sync: {sync_all_frames.__name__} | Check: {verify_all_docs.__name__}")
```

<details>
<summary>Ergebnis</summary>

```text
Sync: sync_all_frames | Check: verify_all_docs
```
</details>

Für Dokumente mit `CUBIE_DOC_FRAME_2` prüft `CUBIE_DOCFRAME_RULES` zusätzlich, dass die drei Provenance-Pflichtfelder (`Plattform / Umgebung`, `Modell`, `Reasoning-Effort`) ausgefüllt sind (`DOCFRAME-PROVENANCE-INCOMPLETE`).

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<center>

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

</center>
<!-- /qb:frame -->