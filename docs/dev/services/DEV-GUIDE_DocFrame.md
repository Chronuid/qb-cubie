<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# `DocFrame`

![Cubie](../../.assets/cubie-logo-written.png)

Die Analyse des aktuellen Dokumentationsbestands (26 Markdown-Dateien) zeigt deutlich, warum statische Tupel bei wachsendem Projekt zum Flaschenhals werden und wie `DocFrame` dies über einen zweistufigen Zero-Config-Katalog (`DocumentCatalog`) und dynamische Router (`FolderRouter`, `SiblingRouter`, `CatalogRouter`) löst.

---

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

---

## 1. Befundanalyse: Aktueller Bestand vs. `DocFrame`-Skizze

### A. Versteckte und ungeroutete Dokumente im Footer (`zone="foot"`)

Ursprünglich besaßen alle befüllten Markdown-Dateien im Repository exakt denselben statischen Footer (`CUBIE_DOC_FRAME_1`) mit 10 fest verdrahteten Links. Sobald ein neues Dokument entsteht, bleibt es unsichtbar, solange es nicht manuell in alle Footer oder einen Zwischen-Router eingetragen wird:

* **Wurzel (`docs/`):** 7 Guides sind im Footer verlinkt, während `CI_PLATFORM_STATUS.md` und `GUIDE_Benchmarks.md` im Footer komplett fehlen.
* **Entwickler-Dokumentation (`docs/dev/`):** Der Footer verlinkt ausschließlich auf `DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`. Dieser verweist am Ende zwar manuell auf `2-1` bis `2-4`, aber `DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md`, `DEV-GUIDE_1-1_RBT-Classes.md`, `DEV-GUIDE_2-5_Linter.md`, `DEV-GUIDE_Release-Preparation.md`, `DEV-GUIDE_Next-Steps.md`, `Style-Guide.md` sowie `dev/services/DEV-GUIDE_DocEnsurance.md` tauchen weder im globalen Footer noch in einem gemeinsamen `dev/`-Index auf.
* **Hintergrundtexte (`docs/misc/`):** `misc/README.md` erwähnt *Clean-Code-Pragmatism*, *Die Suchmaschine von Babel*, *Erweitertes PBT* und *FP-OOP-Isomorphismus* lediglich kursiv im Fließtext, besitzt aber **keinen einzigen anklickbaren Link** auf diese vier Dateien. Da sie auch im Footer fehlen, sind diese Dokumente echte „Waisen“ (Orphan Pages).
* **Feature-Drafts (`docs/feature-drafts/virtualization/`):** `feature-drafts/virtualization/README.md` pflegt die Links auf `arena-requirements.md`, `vm-requirements.md`, `Libvirt-Handbuch.md`, `Wizards-Handbuch.md` und die `.py.txt`-Artefakte manuell als Aufzählungsliste im Rumpf.

### B. Inkonsistenzen zwischen früherer `services/GUIDE_DocFrame.md`-Skizze und den echten Dateien

* **HTML-Wrapper & Alt-Text:** Die ursprüngliche Skizze nutzte für den Footer `CenterWrap(tag="center")` und `AssetImage(..., alt="Cubie")`. Alle realen Dateien nutzen im Footer jedoch `<div align="center">` und trugen noch den fehlerhaften Alt-Text `![Error while trying to load the image](.assets/cubie-small.png)`.
* **Abweichende Routen-Definition:** `CORE_ROUTES` enthielt nur 4 statt 7 Routen, `SERVICE_ROUTES` nur 2 statt 3 Routen, und der skizzierte `FolderRouter(dir="docs/qa_evolution", ...)` verwies auf ein Verzeichnis, das im aktuellen `docs/`-Baum gar nicht existiert.

---

## 2. Kern-Idee: Zero-Config-Metadaten aus `zone="head"` + 2-Pass-Katalog

Wenn ein neues Dokument hinzukommt und sich über `DocFrame.update()` vollautomatisch in die Fuß-Router und die dedizierten Routing-Dokumente (`README.md`) einspielen soll, darf die Information über das Dokument **nicht** in einer zentralen Python-Liste (`CORE_ROUTES = (...)`) gepflegt werden müssen.

Stattdessen liefert jedes Dokument seine Routing-Metadaten **selbst** über seinen `zone="head"`-Rahmen (Single Source of Truth):

1. **Automatische Extraktion aus dem bestehenden Header (Zero-Config):**
   Fast jedes Dokument in `docs/` folgt im `HeaderContentSlot` bereits exakt demselben Muster: `# H1-Titel` $\to$ `![Cubie](Banner)` $\to$ `Kurzbeschreibung (1–2 Sätze)`.
   * **Router-Label:** Wird automatisch aus dem `# H1-Titel` gelesen (oder optional über ein Marker-Attribut `label="Linter"` bzw. `order="70"` im `<!-- qb:frame ... -->`-Tag überschrieben).
   * **Kurzbeschreibung (für Index-Tabellen):** Wird automatisch aus dem ersten Absatz (`MdBlock(kind="paragraph")`) unterhalb des Banners im `HeaderContentSlot` extrahiert.

2. **Zweistufige Ausführung (`Pass 1: Scan` $\to$ `Pass 2: Render/Verify`):**
   * **Pass 1 (`DocumentCatalog`):** `DocFrame` scannt einmalig alle nicht-exkludierten `.md`-Dateien ab Projekt-Root, liest deren `qb:frame`-Header aus und baut im Speicher einen unveränderlichen `DocumentCatalog` mit `DocMeta(path, frame_id, title, label, summary, order, routable, category, attrs)` auf.
   * **Pass 2 (Relatives Pfad-Routing):** Jeder Router-Baustein (`FolderRouter`, `SiblingRouter`, `CatalogRouter`) fragt diesen Katalog ab und berechnet für jede Zieldatei den exakten relativen Pfad (`./`, `../`, `../../`) über `os.path.relpath`.

---

## 3. Drei-Säulen-Architektur mit `CUBIE_DOC_FRAME_3`

Damit sowohl die Fußzeilen aller Dokumente als auch die verteilten Routing-Hubs (`docs/README.md`, `docs/misc/README.md`, `docs/feature-drafts/virtualization/README.md` und ein künftiges `docs/dev/README.md`) vollautomatisch synchron bleiben, gliedert sich `DocFrame` in drei Presets:

| Preset | Ziel-Dokumente | Zonen (`zone=...`) | Besonderheit beim Auto-Routing |
| --- | --- | --- | --- |
| **`CUBIE_DOC_FRAME_1`** | Reguläre Guides & Dev-Guides (`GUIDE_*.md`, `DEV-GUIDE_*.md`) | `head`, `foot` | Dynamischer Fuß aus globalen `FolderRouter`-Gruppen + kontextuellem **`SiblingRouter`** (zeigt automatisch alle Nachbardokumente des eigenen Unterordners). |
| **`CUBIE_DOC_FRAME_2`** | Gutachten, Hypothesen, Audits & Feldberichte | `head`, `foot` | Schlanker Provenance-Kopf (`env`, `model`, `effort`) + Standard-Fuß. |
| **`CUBIE_DOC_FRAME_3`** | Dedizierte Routing- & Index-Dokumente (`README.md`, Bereichs-Hubs) | `head`, **`router`**, `foot` | Führt die neue **`zone="router"`** im Dokumentkörper ein: Generiert Index-Tabellen (`\| Dokument \| Inhalt und Geltung \|`) oder Katalog-Listen vollautomatisch aus dem `DocumentCatalog`. |

---

## 4. Wie das automatische Routing im Detail funktioniert

### A. Der selbstaktualisierende Fuß (`STD_FOOTER_BLOCKS`)

Anstatt Routen als statische Strings in `RouteGroup` einzutragen, kombinieren wir im Footer drei dynamische Router-Bausteine:

1. **`FolderRouter(dir="docs", glob="GUIDE_*.md")`:** Findet automatisch alle Haupt-Guides in `docs/`. Kommt morgen `docs/GUIDE_Property-Based-Testing.md` hinzu, landet es beim nächsten `DocFrame.update()` sofort in allen Footern.
2. **`FolderRouter(dir="docs/services", glob="GUIDE_*.md")`:** Findet automatisch alle Service-Guides (`GUIDE_DocEnsurance.md`, `GUIDE_DocFrame.md` usw.).
3. **`SiblingRouter(include_hubs=True)` (Der Kontext-Booster für Unterordner):**
   * Damit der globale Footer nicht irgendwann 35 Links lang wird, zeigt die unterste Gruppe im Footer die **Bereichs-Hubs** (`docs/dev/`, `docs/misc/`, `docs/feature-drafts/`).
   * Befindet sich der Leser jedoch *innerhalb* eines Unterordners (z. B. in `docs/dev/DEV-GUIDE_2-1_EBT-Class.md` oder `docs/misc/FP-OOP-Isomorphismus.md`), klappt `SiblingRouter` automatisch alle Geschwister-Dokumente dieses Ordners im Footer auf! So sind alle `DEV-GUIDE_*` und alle `misc/`-Essays untereinander sofort erreichbar, ohne den Footer der Haupt-Guides aufzublähen.

### B. `CUBIE_DOC_FRAME_3` und die neue `zone="router"` für Index-Dokumente

In Routing-Dokumenten wie `docs/README.md`, `docs/misc/README.md` oder `docs/feature-drafts/virtualization/README.md` liegt das eigentliche Routing mitten im Dokument (als Tabelle oder Liste), während davor oder danach noch manueller Fließtext steht (wie der Hinweis zum experimentellen Benchmark-Bereich in `docs/README.md`).

Mit `CUBIE_DOC_FRAME_3` bekommt das Dokument neben `head` und `foot` einen expliziten **`<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" ... -->`**-Block im Rumpf:

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Clean-Code Pragmatismus](./Clean-Code-Pragmatism.md) | Dieser Essay diskutiert kontextabhängige Entwurfsentscheidungen und pragmatische Clean-Code-Prinzipien. |
| [Die Suchmaschine von Babel: eine Metapher](./Die-Suchmaschine-von-Babel.md) | Status: konzeptioneller Essay. Cubie enthält weder eine Suchmaschine für Programme noch einen Codegenerator. |
| [Erweitertes Property-Based Testing](./Erweitertes-PBT.md) | Status: konzeptioneller Vorschlag, keine implementierte Cubie-API. |
| [FP-OOP-Isomorphismus](./FP-OOP-Isomorphismus.md) | Dieser Essay untersucht Beziehungen zwischen funktionaler und objektorientierter Programmierung. |
<!-- /qb:frame -->
```

**Was passiert hier beim Aufruf von `DocFrame.update()`?**

1. `CatalogRouter` scannt das im Attribut `dir="."` (oder `dir="docs/dev"`) angegebene Verzeichnis (exklusive der `README.md` selbst).
2. Für jede gefundene Markdown-Datei holt er sich aus dem `DocumentCatalog` den `# Titel` (bzw. das `label`) und den ersten Satz/Absatz aus dem `HeaderContentSlot` des jeweiligen Dokuments.
3. Er generiert die Markdown-Tabelle (`mode="table"`) oder `[↦ | ... | ↤]`-Liste (`mode="links"`) komplett neu. Manueller Text *außerhalb* von `<!-- qb:frame ... -->` (wie die Tabelle zu den `experiments/`-Links in `misc/README.md`) bleibt zu 100 % geschützt.

---

## 5. Umsetzung der Presets in `qb_cubie.services.docframe`

So fügt sich das Konzept mit `CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` nahtlos in die Lego-Architektur und die `DocEnsurance`-Konventionen (`session=docframe_presets`, $\le 30$ Zeilen pro Code-Block) ein.

### Schritt 1: Dynamische Router-Bausteine statt starrer Listen

Im ersten Schritt definieren wir die Schnellnavigation für den Dokumentkopf sowie die dynamischen `FolderRouter`- und `SiblingRouter`-Bausteine für den Fußbereich:

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

### Schritt 2: Gemeinsamer Fuß (`div align="center"`) & Index-Katalog

Im zweiten Schritt setzen wir den gemeinsamen Fuß-Block (`STD_FOOTER_BLOCKS`) mit `<div align="center">` sowie den `CatalogRouter` (`AUTO_INDEX_ROUTER`) für Index-Dokumente zusammen:

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

### Schritt 3: Die drei Presets (`FRAME_1`, `FRAME_2`, `FRAME_3`)

Im dritten Schritt bündeln wir die Kopf-, Router- und Fuß-Bausteine zu den drei Rahmen-Presets `CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3`:

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

## 6. Zusammenspiel mit `DocEnsurance` & Diagnose-Regeln

Damit `DocEnsurance` und `DocFrame` ohne Code-Duplizierung über dieselbe Engine laufen, nutzt `DocFrame` intern eine `Dry-Run`-Diff-Berechnung:

1. **`DocFrame.update(target=None, pattern=(...), excludes=(...))`:**
   * Führt **Pass 1** (`build_catalog`) über das Repository aus.
   * Rendert in **Pass 2** für jede Datei die gefundenen `<!-- qb:frame id="..." zone="head|router|foot" ... -->`-Blöcke neu (unter Bewahrung der geschützten Slots wie `HeaderContentSlot`, `DisclaimerSlot`, `TitleSlot` und `PromptSlot`) und schreibt geänderte Dateien atomar zurück.
2. **Prüfregeln in `CUBIE_DOCFRAME_RULES` (für `DocEnsurance`):**
   * **`DOCFRAME-MISSING` (`error`):** Eine nicht-exkludierte `.md`-Datei besitzt keinen gültigen `head`- oder `foot`-Rahmen (oder eine `CUBIE_DOC_FRAME_3`-Datei hat keinen `zone="router"`-Block).
   * **`DOCFRAME-OUTDATED` (`error`):** Der in der Datei gespeicherte Rahmen oder Router weicht vom frisch berechneten Katalog-Zustand ab (z. B. weil eine neue `.md`-Datei im Ordner angelegt wurde, `DocFrame.update()` aber noch nicht lief, oder weil ein Link im Footer noch den alten `![Error while trying to load the image]`-Tag trägt).
   * **`DOCFRAME-BROKEN-ROUTE` (`error`):** Ein im Rahmen oder Router referenziertes Ziel oder Banner-Asset existiert physisch nicht im Workspace.
   * **`DOCFRAME-PROVENANCE-INCOMPLETE` (`error`):** Ein Dokument mit `CUBIE_DOC_FRAME_2` lässt Pflichtfelder im `ProvenanceBlock` leer.

### Optionales feingranulares Steuern im Dokument-Header

Damit die Sortierung und Benennung im Fuß-Router (`[↦ | Label | ↤]`) trotz Vollautomatisierung genauso prägnant bleibt wie in handgeschriebenen Footern, kann jedes Dokument im öffnenden `head`-Kommentar optionale Routing-Hints mitgeben:

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-banner.png" label="Qualitätssicherung: Handbuch & Methodik" order="10" -->
```

* Fehlt `label="..."`, fällt `DocFrame` automatisch auf den `# H1-Titel` des Dokuments zurück.
* Fehlt `order="..."`, sortiert `FolderRouter` deterministisch alphabetisch nach Dateiname (mit `README.md` immer auf Platz 1).
* Will man ein spezielles Dokument (wie ein temporäres Scratchpad) zwar mit einem Rahmen versehen, aber *nicht* automatisch in fremde Footer einspielen lassen, setzt man `routable="false"` im Header.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../../GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../../GUIDE_Benchmarks.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../../GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../../GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../../GUIDE_Example-Based-Testing.md)  
[↦ | Linter | ↤](../../GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | RBT-Nutzungsmuster | ↤](../../GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Entwicklerübersicht & Internals | ↤](../DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](../../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  
[↦ | `DocEnsurance` | ↤](./DEV-GUIDE_DocEnsurance.md)  
[↦ | `DocFrame` | ↤](./DEV-GUIDE_DocFrame.md)  

</div>
<!-- /qb:frame -->
