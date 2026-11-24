<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DocFrame (Prototyp)

![Cubie](../.assets/cubie-logo-written.png)

Wenn ein Projekt wächst, veralten manuell gepflegte Kopf- und Fußzeilen, relative Navigationspfade über verschiedene Verzeichnistiefen, Provenance-Kopfblöcke und Bereichs-Indizes (`README.md`) innerhalb kürzester Zeit. **`DocFrame`** *(Prototyp – noch zu evaluieren und zu härten)* aus `qb_cubie.core.services` (bzw. dem Kurz-Alias `qb_cubie.core.services.docframe`) adressiert dieses Problem durch eine zweistufige Synchronisations- und Routing-Engine, während **`DocEnsurance`** über **`CUBIE_DOCFRAME_RULES`** prüft, ob nicht-exkludierte Markdown-Dokumente gültige, vollständige und aktuelle Rahmen besitzen.

---

> [!WARNING]
>
> **Status: Prototyp – noch nicht evaluiert und gehärtet:**  
> `DocFrame` (`qb_cubie.core.services.doc_frame` / `qb_cubie.core.services.docframe`, einschließlich `CUBIE_DOC_FRAME_1..3` und `CUBIE_DOCFRAME_RULES`) ist derzeit ein **experimenteller Prototyp**, der vor einer produktiven Stabilitätszusage noch systematisch evaluiert und gehärtet werden muss:
> * **Unstabile Schnittstellen & Heuristiken:** Öffentliche Signaturen, Preset-Strukturen, Scanner-Heuristiken (`_catalog_scanner`) und Regelverhalten können sich in kommenden Releases noch ändern.
> * **Vorläufige Absicherung:** Die bisherigen Unit- und Integrationstests belegen nur die geprüften Szenarien im eigenen Checkout; vor dem Einsatz auf fremden oder größeren Repositories sollten Backups angelegt und eigene Verifikationsläufe durchgeführt werden.

> [!NOTE]
>
> **Wichtiger Hinweis zu Rahmen-Synchronisation & Geltungsbereich:**  
> Jedes Dokument im Repository fungiert über seinen `zone="head"`-Block als eigene *Single Source of Truth* für Titel, Kurzbeschreibung, Sortier-Priorität und Sichtbarkeit:
> * **Strikter Schutz des Dokumentkörpers:** `DocFrame.update()` modifiziert ausschließlich den Bereich innerhalb geschlossener `<!-- qb:frame ... --> ... <!-- /qb:frame -->`-Kommentarblöcke (außerhalb von Markdown-Code-Fences) und tastet den eigentlichen Fließtext sowie geschützte Header-Inhalte niemals an.
> * **Orthogonale Verifikation in der Test-Suite:** Während `DocFrame.update()` die Rahmen idempotent synchronisiert, prüft `DocEnsurance` mit `CUBIE_DOCFRAME_RULES` im CI-Lauf zerstörungsfrei auf fehlende Zonen, veraltete Stände, tote Links und unvollständige Provenance-Metadaten.

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](./GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Schnelleinstieg (Minimal-Setup für Synchronisation & Test-Suite)

Im Alltag greifen zwei komplementäre Aufrufe ineinander: Während der Entwicklung bringt `DocFrame.update()` sämtliche Kopf-, Index- und Fußrahmen im Repository in einem einzigen Durchlauf auf den aktuellen Stand; in der Test-Suite (getrennt in `tests/test_doc_ensurance.py` und `tests/test_doc_frame.py`) überwacht `DocEnsurance` gemeinsam mit `CUBIE_DOCFRAME_RULES`, dass kein Dokument ohne gültigen oder aktuellen Rahmen eingecheckt wird:

```python
from qb_cubie.core.services import (
    CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3,
    CUBIE_DOC_RULES, CUBIE_DOC_STYLE, CUBIE_DOCFRAME_RULES,
    DocEnsurance, DocFrame,
)

FRAME_PATTERNS = (CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3)
EXCLUDES = (".pytest_cache", "tests", "experiments", "GUTACHTEN.md", "CHANGELOG.md")
doc_ensurance = DocEnsurance(
    pattern=(CUBIE_DOC_STYLE, *FRAME_PATTERNS),
    rules=(CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES),
    excludes=EXCLUDES,
)


def sync_repository_frames() -> None:
    """Synchronizes all head, router, and foot zones across the repository."""
    DocFrame.update(pattern=FRAME_PATTERNS, excludes=EXCLUDES)


def test_docs_and_frames() -> None:
    """Verifies code examples (CUBIE_DOC_RULES) and document frames (CUBIE_DOCFRAME_RULES)."""
    doc_ensurance.run()


print(f"Presets: {len(FRAME_PATTERNS)} | Frame-Regeln: {[r.rule_id for r in CUBIE_DOCFRAME_RULES]}")
```

<details>
<summary>Ergebnis</summary>

```text
Presets: 3 | Frame-Regeln: ['DOCFRAME-MISSING', 'DOCFRAME-OUTDATED', 'DOCFRAME-BROKEN-ROUTE', 'DOCFRAME-PROVENANCE-INCOMPLETE']
```
</details>

---

## 2. API-Quick-Lookup (`DocFrame` & Einstiegspunkte)

Die Klasse `DocFrame` kann sowohl direkt als zustandsbehafteter Service (`DocFrame(...).run()`) als auch über zwei ergonomische Klassenmethoden (`DocFrame.update(...)` und `DocFrame.scan_catalog(...)`) genutzt werden:

```text
DocFrame(
    target: str | Path | None = None,
    pattern: FramePattern | Sequence[FramePattern] | None = None,
    excludes: Sequence[str] | None = None,
)
```
```text
DocFrame.update(
    target: str | Path | None = None,
    pattern: FramePattern | Sequence[FramePattern] | None = None,
    excludes: Sequence[str] | None = None,
) -> DocFrameReport
```
```text
DocFrame.scan_catalog(
    target: str | Path | None = None,
    excludes: Sequence[str] | None = None,
) -> DocumentCatalog
```

| Parameter / Methode | Standardwert | Funktion & Verhalten |
| :--- | :--- | :--- |
| **`target`** | `None` (Projekt-Root) | Bestimmt den zu aktualisierenden Ziel-Scope: `None` löst automatisch das Projekt-Root ab der nächstgelegenen `pyproject.toml` (Fallback: `Path.cwd()`) auf; akzeptiert zudem existierende Ordnerpfade (`"docs"`) oder Einzeldateien (`"docs/services/GUIDE_DocFrame.md"`). |
| **`pattern`** | `DEFAULT_FRAME_PATTERNS` | Ein einzelnes `FramePattern` oder eine Sequenz von `FramePattern`-Objekten. `None` registriert automatisch `CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3`. |
| **`excludes`** | `DEFAULT_EXCLUDES` | Ergänzt die Standard-Ausschlüsse (`.venv`, `.git`, `__pycache__`, `.pytest_cache` etc.) um zusätzliche Ordnernamen (`"experiments"`), Dateinamen (`"CHANGELOG.md"`) oder relative Teilpfade (`"docs/drafts"`). |
| **`DocFrame.update(...)`** | Klassenmethode | Führt Pass 1 (`build_catalog`) und Pass 2 (Zonen-Rendering) aus, schreibt nur tatsächlich veränderte Dateien atomar zurück und liefert einen `DocFrameReport(target, passed, updated_files, catalog, diagnostics)`. |
| **`DocFrame.scan_catalog(...)`** | Klassenmethode | Führt ausschließlich Pass 1 ohne Dateisystem-Schreibzugriffe aus und gibt den unveränderlichen `DocumentCatalog(root, entries)` zurück. |

### Aufruf über die Core-CLI (`qb-cubie`)

Für die direkte Synchronisation aus der Kommandozeile steht `DocFrame.update()` über die Core-CLI `qb-cubie` (sowie `python -m qb_cubie`, `python -m qb_cubie.core.services.docframe` und `python -m qb_cubie.core.services.doc_frame`) bereit:

```bash
qb-cubie docframe update
```

```bash
qb-cubie docframe update docs/ --exclude experiments --exclude CHANGELOG.md --format json
```

```bash
python -m qb_cubie.core.services.docframe update docs/services/GUIDE_DocFrame.md
```

### Wichtige Konfigurations-Details für die Praxis

* **Trennung von Schreib-Scope (`target`) und Katalog-Root:**
  Wird `DocFrame.update(target="docs/services/GUIDE_DocFrame.md")` gezielt auf eine einzelne Datei oder einen Unterordner angesetzt, lädt Pass 2 zum Schreiben nur die im `target` angeforderten Dateien. Für Pass 1 ermittelt `build_catalog()` hingegen automatisch das übergeordnete Repository-Root (anhand von `pyproject.toml` oder `docs/.assets`), sodass alle dynamischen Router (`FolderRouter`, `SiblingRouter`, `CatalogRouter`) auch bei Einzeldatei-Updates den vollständigen Projekt-Katalog kennen.
* **Strikte Idempotenz & `DocFrameReport.updated_files`:**
  `DocFrame.update()` überschreibt eine Datei nur dann auf der Festplatte (`new_content != content`), wenn sich mindestens eine Rahmen-Zone geändert hat. Ein zweiter Lauf über ein bereits synchronisiertes Verzeichnis liefert `report.updated_files == ()` und führt keinen einzigen Schreibzugriff aus.
* **Kurz-Alias für Imports (`docframe` vs. `doc_frame`):**
  Alle Bausteine, Presets und Regeln sind direkt unter `qb_cubie.core.services`, `qb_cubie.core.services.doc_frame` sowie über das Kurz-Alias-Modul `qb_cubie.core.services.docframe` importierbar.
* **Explizite `STATE-GUARD`s vor dem Lauf:**
  Nicht existierende Zielpfade (`FileNotFoundError`), leere Pfad-Strings oder Verzeichnisse ohne `.md`-Dateien (`ValueError`), falsche Parametertypen (`TypeError`) sowie unbekannte `frame_id`-Referenzen in Dokumenten (`ValueError`) werden sofort mit einer sprechenden `STATE-GUARD`-Meldung abgewiesen.

Das folgende Beispiel legt ein kleines Projektverzeichnis an, synchronisiert dessen Rahmen über `DocFrame.update()` und zeigt anschließend, dass ein zweiter Lauf idempotent `updated_files == ()` liefert:

```python
from pathlib import Path
from qb_cubie.core.services import DocFrame

root = Path("mini_repo")
(root / "docs/.assets").mkdir(parents=True, exist_ok=True)
(root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
(root / "docs/.assets/cubie-logo-written.png").write_text("img", encoding="utf-8")
(root / "docs/.assets/cubie-small.png").write_text("img", encoding="utf-8")
(root / "README.md").write_text("# Root\n", encoding="utf-8")
(root / "docs/GUIDE_Alpha.md").write_text(
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Alpha Guide\n\nKurze Einleitung.\n<!-- /qb:frame -->\n\nText.\n\n'
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n',
    encoding="utf-8",
)

first_run = DocFrame.update(target=root)
second_run = DocFrame.update(target=root)
print(f"1. Lauf: {first_run.updated_files} | 2. Lauf: {second_run.updated_files} | Katalog: {len(first_run.catalog.entries)}")
```

<details>
<summary>Ergebnis</summary>

```text
1. Lauf: ('docs/GUIDE_Alpha.md',) | 2. Lauf: () | Katalog: 2
```
</details>

---

## 3. Grundprinzip: Das 2-Pass-Modell & Zero-Config-Katalogisierung

Damit neue Guides, verschobene Dateien oder geänderte Dokumenttitel sofort in allen Fußzeilen und Index-Tabellen erscheinen, ohne dass statische Pfadlisten im Python-Code nachgepflegt werden müssen, arbeitet `DocFrame` in zwei streng getrennten Phasen:

1. **Pass 1 – Fence-sicherer Span-Scanner & `DocumentCatalog`:**
   Der zeilenbasierte Zustandsautomat (`parse_frame_spans`) liest alle nicht-exkludierten Markdown-Dateien ein und ignoriert dabei sämtliche `<!-- qb:frame ... -->`-Tags, die innerhalb von Markdown-Code-Fences (`` ``` ``, ```` ```` ```` oder `~~~`) als Dokumentations-Beispiele stehen. Aus jedem echten `zone="head"`-Block extrahiert `extract_doc_meta(rel_path, content)` ein unveränderliches `DocMeta`-Objekt:
   * **`title` & `label`:** Die erste `# H1-Überschrift` (Fallback: Dateiname ohne Endung) sowie das Anzeige-Label für Router (`label="..."`-Attribut oder `title`).
   * **`summary`:** Der erste erklärende Textabsatz unterhalb des Banners und vor der ersten horizontalen Linie (`---`), bereinigt um HTML-Wrapper (`<div...>`, `<center>`), Überschriften und Bilder. Nachfolgende Absätze oder Disclaimer bluten niemals in die Kurzbeschreibung.
   * **`order`, `routable` & `category`:** Optionale Sortier-Priorität (`int | None`), Sichtbarkeits-Flag (`bool`, leere 0-Byte-Dateien sind automatisch `routable=False`) und der relative Elternordner (`category`).
2. **Pass 2 – Tiefen- & kontextsensitives Rendering:**
   Für jede Datei im Ziel-Scope werden alle geschlossenen Rahmen-Spans **rückwärts vom Dateiende zum Dateianfang** (`foot` $\to$ `router` $\to$ `head`) über ihre exakten Zeichen-Offsets (`start_idx`, `end_idx`) ersetzt, sodass sich vorangehende Indizes niemals verschieben. Alle Links und Asset-Pfade werden dabei automatisch relativ zur Verzeichnistiefe der jeweiligen Datei (`./` oder `../`) berechnet.

### Dreistufige Sortier-Invariante (`sort_doc_metas`)

Alle Katalog-Abfragen über `catalog.select(...)`, `FolderRouter`, `SiblingRouter` und `CatalogRouter` sortieren Dokumente betriebssystemunabhängig in drei Stufen:

1. **Stufe 0 (`README.md` ohne `order`):** Eine `README.md` ohne explizites `order`-Attribut steht in ihrem Ordner immer an erster Stelle.
2. **Stufe 1 (Explizite Priorität via `order="<int>"`):** Dokumente mit gesetztem `order`-Attribut im `head`-Tag folgen aufsteigend nach ihrem Zahlenwert (bei Gleichstand alphabetisch).
3. **Stufe 2 (Alphabetischer Standard):** Alle übrigen Dokumente ohne `order`-Attribut folgen alphabetisch nach Dateiname und relativem Pfad.

Das folgende Beispiel zeigt, wie `parse_frame_spans` einen `qb:frame`-Kommentar innerhalb eines Code-Fences ignoriert und wie `extract_doc_meta` Titel, Label, Kurzbeschreibung und Sortier-Rang extrahiert:

```python
from qb_cubie.core.services.docframe import extract_doc_meta, parse_frame_spans

fence = "```"
raw_md = (
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" label="Kurz-Label" order="15" -->\n'
    '<div align="center">\n\n# Vollständiger Handbuch-Titel\n\n'
    "![Cubie](.assets/cubie-logo-written.png)\n\n"
    "Erster Satz der Zusammenfassung\nüber zwei Zeilen.\n\n---\n\n"
    "> Optionaler Disclaimer bleibt aus der Summary ausgeschlossen.\n\n---\n\n</div>\n"
    "<!-- /qb:frame -->\n\n"
    f'{fence}markdown\n<!-- qb:frame id="IGNORED" zone="head" -->\n<!-- /qb:frame -->\n{fence}\n'
)

spans, unclosed = parse_frame_spans(raw_md)
meta = extract_doc_meta("docs/services/GUIDE_Demo.md", raw_md)
print(f"Spans: {len(spans)} | Unclosed: {unclosed} | Label: {meta.label!r} | Order: {meta.order}")
print(f"Summary: {meta.summary!r} | Category: {meta.category!r}")
```

<details>
<summary>Ergebnis</summary>

```text
Spans: 1 | Unclosed: [] | Label: 'Kurz-Label' | Order: 15
Summary: 'Erster Satz der Zusammenfassung über zwei Zeilen.' | Category: 'docs/services'
```
</details>

---

## 4. Die drei Rahmen-Standards (`CUBIE_DOC_FRAME_1`, `FRAME_2`, `FRAME_3`)

In `qb-cubie` decken drei vordefinierte `FramePattern`-Presets (`DEFAULT_FRAME_PATTERNS`) sämtliche Dokumenttypen des Projekts ab:

| Preset | Ziel-Dokumente | Pflicht-Zonen (`zone=...`) | Geschützte Autoren-Slots & Auto-Routing |
| :--- | :--- | :--- | :--- |
| **`CUBIE_DOC_FRAME_1`** | Handbücher & Dev-Guides (`GUIDE_*.md`, `DEV-GUIDE_*.md`, Root-`README.md`) | `head`, `foot` | Schützt `# Titel`, Einleitung (`HeaderContentSlot`) und optionalen Disclaimer (`DisclaimerSlot`); generiert Schnellnavigation + dynamischen Footer. |
| **`CUBIE_DOC_FRAME_2`** | Gutachten, Hypothesen, Audits & Feldberichte | `head`, `foot` | Synchronisiert Provenance-Pflichtfelder (`Plattform / Umgebung`, `Modell`, `Reasoning-Effort`), bewahrt freie Zusatzfelder und optionalen Prompt-Text (`PromptSlot`). |
| **`CUBIE_DOC_FRAME_3`** | Dedizierte Bereichs-Indizes (`README.md` in Unterordnern) | `head`, `router`, `foot` | Wie `FRAME_1`, ergänzt um eine `zone="router"` im Dokumentkörper, die automatisch Index-Tabellen (`mode="table"`) oder Link-Listen (`mode="links"`) rendert. |

### 4.1 Handbuch-Rahmen (`CUBIE_DOC_FRAME_1`)

In regulären Guides steuert das optionale Attribut `banner="..."` das Kopfbild aus `docs/.assets/` (Standard: `"cubie-logo-written.png"`). Der `# H1-Titel`, der Einführungstext vor dem ersten `---` sowie ein optionaler Hinweisblock zwischen dem ersten und zweiten `---` bleiben bei jedem `DocFrame.update()`-Lauf vollständig geschützt, während Banner-Pfad, Schnellnavigation und Footer-Routen tiefenkorrekt aktualisiert werden:

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# RBT-Nutzungsmuster

![Cubie](.assets/cubie-logo-written.png)

RBT delegiert eine sprachlich formulierte Prüfregel an einen Reviewer...

---

> Optionaler dokument-spezifischer Hinweis oder Disclaimer (wird bei Fehlen nahtlos ausgeblendet).

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->
```

Im zugehörigen `zone="foot"`-Block sorgt der `SiblingRouter` (`CONTEXT_ROUTER`) für kontextsensitive Navigation:
* In **Top-Level- und Service-Guides** (`README.md`, `docs/*.md`, `docs/services/*.md`) zeigt der Footer unterhalb der Haupt- und Service-Guides kompakt die konfigurierten Bereichs-Hubs (`Entwicklerübersicht & Internals`, `Hintergrund & Essays`, `Feature-Drafts`).
* Innerhalb tieferer **Unterordner** (wie `docs/dev/` oder `docs/dev/services/`) blendet der `SiblingRouter` den Sammel-Hub des eigenen Ordners aus und klappt stattdessen automatisch alle routbaren Geschwister-Dokumente des aktuellen Unterordners im Footer auf.

### 4.2 Provenance-Rahmen für Berichte und Analysen (`CUBIE_DOC_FRAME_2`)

Für Hypothesen, Pilot-Analysen und Gutachten hält `CUBIE_DOC_FRAME_2` den Herkunftsnachweis (`**Dokument-Informationen & Herkunft:**`) konsistent. Die drei Pflichtfelder lassen sich direkt über Kurz-Attribute im Kommentar-Tag setzen (`env` $\to$ `Plattform / Umgebung`, `model` $\to$ `Modell`, `effort` $\to$ `Reasoning-Effort`). Bestehende benutzerdefinierte Aufzählungspunkte (wie `Analysedatum` oder `Synthesebasis`) sowie ein optionaler Fragetext (`PromptSlot`) unterhalb von `---` bleiben beim Update verlustfrei erhalten:

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

Optionaler Prompt- oder Aufgaben-Kontext unterhalb der Trennlinie.
<!-- /qb:frame -->
```

### 4.3 Selbstaktualisierende Index-Tabellen (`CUBIE_DOC_FRAME_3`)

In Bereichs-Indizes (wie `docs/misc/README.md`) ergänzt `CUBIE_DOC_FRAME_3` den Kopf- und Fußrahmen um eine `zone="router"` mitten im Dokument. Der darin eingebaute `CatalogRouter` liest alle routbaren Dokumente des Zielordners (unter automatischem Ausschluss der aufrufenden `README.md` selbst) aus dem `DocumentCatalog` und generiert eine zweispaltige Übersichtstabelle (`mode="table"`) oder eine kompakte Routen-Liste (`mode="links"`):

```markdown
<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Clean-Code Pragmatismus](./Clean-Code-Pragmatism.md) | Dieser Essay diskutiert kontextabhängige Entwurfsentscheidungen und pragmatische Clean-Code-Prinzipien. |
<!-- /qb:frame -->
```

Im folgenden zweistufigen Praxis-Beispiel (`session=frame_standards`) legen wir im ersten Schritt einen `CUBIE_DOC_FRAME_2`-Analysebericht mit Kurz-Attributen sowie einen `CUBIE_DOC_FRAME_3`-Bereichsindex an:

```python session=frame_standards
from pathlib import Path
from qb_cubie.core.services import DocFrame

ws = Path("standards_demo")
(ws / "docs/.assets").mkdir(parents=True, exist_ok=True)
(ws / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
for asset in ("cubie-logo-written.png", "cubie-small.png"):
    (ws / "docs/.assets" / asset).write_text("img", encoding="utf-8")

(ws / "docs/Report.md").write_text(
    '<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="CLI" model="Argon" effort="High" -->\n'
    "# Audit-Bericht\n\n- **Analysedatum:** 16. November 2026\n\n---\nPrüffrage A\n<!-- /qb:frame -->\n\n"
    '<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->\n<!-- /qb:frame -->\n',
    encoding="utf-8",
)
(ws / "docs/README.md").write_text(
    '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" -->\n# Doku-Index\n\nÜbersicht aller Berichte.\n<!-- /qb:frame -->\n\n'
    '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." -->\n<!-- /qb:frame -->\n\n'
    '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->\n<!-- /qb:frame -->\n',
    encoding="utf-8",
)
report = DocFrame.update(target=ws)
print(f"Aktualisiert: {report.updated_files}")
```

<details>
<summary>Ergebnis</summary>

```text
Aktualisiert: ('docs/README.md', 'docs/Report.md')
```
</details>

Im zweiten Schritt derselben Session prüfen wir den synchronisierten Provenance-Kopf in `docs/Report.md` sowie die automatisch generierte Index-Tabelle in `docs/README.md`:

```python session=frame_standards
from qb_cubie.core.services.docframe import parse_frame_spans

report_head = parse_frame_spans((ws / "docs/Report.md").read_text(encoding="utf-8"))[0][0]
readme_router = parse_frame_spans((ws / "docs/README.md").read_text(encoding="utf-8"))[0][1]
print(report_head.inner_content.strip())
print("===")
print(readme_router.inner_content.strip())
```

<details>
<summary>Ergebnis</summary>

```text
# Audit-Bericht

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** CLI
- **Modell:** Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 16. November 2026

---

Prüffrage A
===
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Audit-Bericht](./Report.md) | - **Analysedatum:** 16. November 2026 |
```
</details>

---

## 5. Steuerung über Marker-Attribute & `STATE-GUARD`-Validierung

Über Schlüssel-Wert-Attribute direkt im öffnenden HTML-Kommentar (`<!-- qb:frame ... -->`) lässt sich das Verhalten von `DocFrame` pro Dokument und Zone feinsteuern, ohne eigenen Python-Code anzufassen.

### 5.1 Attribute für `zone="head"` und `zone="router"`

| Attribut | Zone | Gültige Werte / Beispiel | Wirkung |
| :--- | :--- | :--- | :--- |
| **`id`** | alle | `"CUBIE_DOC_FRAME_1"` | **Pflichtattribut:** Wählt das zuständige `FramePattern` aus. |
| **`zone`** | alle | `"head"`, `"router"`, `"foot"` | Bestimmt die zu rendernde Rahmen-Zone (Default: `"head"`). |
| **`banner`** | `head` | `"cubie-banner.png"` | Wählt ein Banner-Bild aus `docs/.assets/` (oder einen relativen Pfad) für `HeaderContentSlot`. |
| **`label`** | `head` | `"QA-Handbuch"` | Überschreibt den `# H1-Titel` durch einen kompakten Anzeigenamen in allen Routern und Tabellen. |
| **`order`** | `head` | `"10"`, `"-5"` | Ganzzahlige Sortier-Priorität in `sort_doc_metas` (Stufe 1 vor alphabetischen Dokumenten). |
| **`routable`** | `head` | `"true"`, `"false"` | Bei `"false"` (`"0"`, `"no"`) wird das Dokument aus allen automatischen Routern und Tabellen ausgeblendet. |
| **`env`, `model`, `effort`** | `head` (`FRAME_2`) | `env="CLI" model="Argon"` | Setzt oder überschreibt die drei Pflichtfelder im `ProvenanceBlock`; `title="..."` ergänzt optional den H1-Titel. |
| **`mode`** | `router` (`FRAME_3`) | `"table"`, `"links"` | Steuert im `CatalogRouter`, ob eine Markdown-Tabelle oder eine `[↦ \| ... \| ↤]`-Linkliste erzeugt wird. |
| **`dir`** | `router` (`FRAME_3`) | `"."`, `"docs/misc"` | Zielordner für die Katalog-Abfrage (relativ zur aktuellen Datei oder ab Repository-Root). |
| **`recursive`** | `router` (`FRAME_3`) | `"true"`, `"false"` | Bezieht bei `"true"` auch alle Unterordner von `dir` in die Katalog-Auswahl ein. |
| **`glob`** | `router` (`FRAME_3`) | `"*.md"`, `"GUIDE_*.md"` | Filtert die im `CatalogRouter` gelisteten Dateinamen nach einem `fnmatch`-Muster. |

### 5.2 Schutz gegen Tippfehler durch `STATE-GUARD`-Exceptions

Genau wie im `qb-cubie`-Kern validiert `DocFrame` sämtliche Marker-Attribute und Konfigurationsparameter sofort über explizite `STATE-GUARD`s. Ungültige Zonen-Namen, fehlende `id`-Attribute, nicht-ganzzahlige `order`-Werte oder unzulässige `routable`-/ `recursive`-/ `mode`-Angaben lösen unmittelbar einen `ValueError` aus:

```python raises=ValueError
from qb_cubie.core.services.docframe import extract_doc_meta

invalid_md = '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" order="high" -->\n# Titel\n<!-- /qb:frame -->'
extract_doc_meta("docs/GUIDE_Broken.md", invalid_md)
```

<details>
<summary>Ergebnis</summary>

```text
ValueError: STATE-GUARD: order attribute must be an integer; received 'high'.
```
</details>

---

## 6. Pluggable Rahmen-Prüfregeln (`CUBIE_DOCFRAME_RULES`) & `DocEnsurance`-Kopplung

Damit Rahmen-Drifts und tote Routen genauso zuverlässig abgefangen werden wie kaputte Python-Beispiele, stellt `qb_cubie.core.services` das Regel-Tupel **`CUBIE_DOCFRAME_RULES`** bereit. Es lässt sich zusammen mit den `FramePattern`-Objekten direkt in `DocEnsurance` einhängen:

* **Orthogonale Ausführung in einem Durchlauf (`FileCheckProtocol`):** Übergibt man `pattern=(CUBIE_DOC_STYLE, CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3)` und `rules=(CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES)`, delegiert `DocEnsurance` dateiweite Prüfungen domänenneutral über das Core-`FileCheckProtocol` (`prepare_context` / `check_file`). Dabei bauen `CUBIE_DOCFRAME_RULES` unter dem gemeinsamen `context_key="doc_frame"` einmalig den `DocumentCatalog` auf und prüfen alle Dokumentrahmen orthogonal zu den Code-Snippets.
* **Kaskadenfreie Abschirmung (`DocFrameOutdated`):** Damit ein einzelner Ursachenfehler niemals doppelt gemeldet wird, arbeitet `DocFrameOutdated` kaskadenfrei: Fehlt in einer Datei bereits eine Pflicht-Zone (`DOCFRAME-MISSING`) oder weist ein Span unvollständige Provenance-Daten (`DOCFRAME-PROVENANCE-INCOMPLETE`) bzw. einen toten Link (`DOCFRAME-BROKEN-ROUTE`) auf, wird für diesen Span keine zusätzliche `DOCFRAME-OUTDATED`-Diagnose emittiert.
* **Feingranulare Severity-Steuerung (`"error"` vs. `"warning"`):** Jede der vier Regel-Klassen (`DocFrameMissing`, `DocFrameOutdated`, `DocFrameBrokenRoute`, `DocFrameProvenanceIncomplete`) akzeptiert `severity="warning"` oder `severity="error"` und überschreibt über ihre `rule_id` deterministisch den Standardeintrag aus `CUBIE_DOCFRAME_RULES`.

Im ersten Schritt der Session `frame_verification` legen wir ein Dokument an, dessen `zone="foot"` noch leer (und damit gegenüber dem Katalog veraltet) ist, und prüfen es mit `DocEnsurance`:

```python session=frame_verification
from pathlib import Path
from qb_cubie.core.services import (
    CUBIE_DOC_FRAME_1, CUBIE_DOC_STYLE, CUBIE_DOCFRAME_RULES, DocEnsurance, DocFrame,
)

check_dir = Path("verify_demo")
(check_dir / "docs/.assets").mkdir(parents=True, exist_ok=True)
(check_dir / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
for asset in ("cubie-logo-written.png", "cubie-small.png"):
    (check_dir / "docs/.assets" / asset).write_text("img", encoding="utf-8")
for nav_doc in ("README.md", "docs/GUIDE_Quality-Assurance.md", "docs/services/GUIDE_DocEnsurance.md"):
    p = check_dir / nav_doc
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" -->\n# Nav\n<!-- /qb:frame -->\n<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->\n<!-- /qb:frame -->\n', encoding="utf-8")

DocFrame.update(target=check_dir)
target_doc = check_dir / "docs/GUIDE_Quality-Assurance.md"
target_doc.write_text(target_doc.read_text(encoding="utf-8").replace("![Cubie]", "VERALTET"), encoding="utf-8")

verifier = DocEnsurance(
    target=target_doc, pattern=(CUBIE_DOC_STYLE, CUBIE_DOC_FRAME_1), rules=CUBIE_DOCFRAME_RULES, reporter=None,
)
bad_report = verifier.run()
print(f"Vor Update: passed={bad_report.passed} | rules={[d.rule_id for d in bad_report.diagnostics]}")
```

<details>
<summary>Ergebnis</summary>

```text
Vor Update: passed=False | rules=['DOCFRAME-OUTDATED']
```
</details>

Im zweiten Schritt derselben Session synchronisieren wir die Datei über `DocFrame.update(target=target_doc)` (oder stufen `DocFrameOutdated(severity="warning")` ab) und prüfen mit derselben `verifier`-Instanz, dass `DocEnsurance` nun mit `passed=True` besteht:

```python session=frame_verification
DocFrame.update(target=target_doc)
good_report = verifier.run()
print(f"Nach Update: passed={good_report.passed} | diagnostics={len(good_report.diagnostics)}")
```

<details>
<summary>Ergebnis</summary>

```text
Nach Update: passed=True | diagnostics=0
```
</details>

---

## 7. Diagnose-Codes (`CUBIE_DOCFRAME_RULES`)

Jeder Rahmen-Befund wird als unveränderliches Core-`Diagnostic(file_path, rule_id, line, message, severity="error")` (`qb_cubie.core.protocols`) im `DocReport.diagnostics` abgelegt. `CUBIE_DOCFRAME_RULES` umfasst vier spezialisierte Dokument-Regeln:

* **`DOCFRAME-MISSING` (`DocFrameMissing` / Alias `DocFrameMissingRule`):**
  Meldet strukturell unvollständige Rahmen:
  1. Ein öffnender `<!-- qb:frame ... -->`-Kommentar wurde nicht durch `<!-- /qb:frame -->` geschlossen (Diagnose exakt auf der Startzeile des ungeschlossenen Tags).
  2. In der Datei fehlt entweder die `zone="head"` oder die `zone="foot"` (Diagnose auf Zeile `1`; gilt auch für leere 0-Byte-Dateien).
  3. Die Datei nutzt ein `FramePattern` mit konfigurierter `router`-Zone (wie `CUBIE_DOC_FRAME_3`), besitzt aber keinen `zone="router"`-Block (Diagnose auf der Startzeile des Referenz-Spans).
* **`DOCFRAME-PROVENANCE-INCOMPLETE` (`DocFrameProvenanceIncomplete` / Alias `DocFrameProvenanceRule`):**
  Feuert auf der Startzeile eines `zone="head"`-Spans mit `ProvenanceBlock` (`CUBIE_DOC_FRAME_2`), wenn nach dem Zusammenführen der bestehenden `- **Key:** Value`-Aufzählungspunkte und der Tag-Attribute (`env`, `model`, `effort`) mindestens eines der Pflichtfelder (`"Plattform / Umgebung"`, `"Modell"`, `"Reasoning-Effort"`) fehlt oder leer ist.
* **`DOCFRAME-BROKEN-ROUTE` (`DocFrameBrokenRoute` / Alias `DocFrameBrokenRouteRule`):**
  Prüft jeden Rahmen-Span darauf, ob ein referenziertes `banner="..."`-Asset oder ein relativer Markdown-Link bzw. Bild-Verweis `[...](...)` innerhalb des Rahmen-Inhalts physisch im Dateisystem fehlt. URL-Anker (`#...`) und Query-Strings (`?...`) werden vor der Pfadprüfung abgetrennt; externe Links (`http://`, `https://`, `mailto:`) werden ignoriert.
* **`DOCFRAME-OUTDATED` (`DocFrameOutdated` / Alias `DocFrameOutdatedRule`):**
  Vergleicht jede strukturell gültige und fehlerfreie Rahmen-Zone im Dry-Run mit dem frisch gerenderten Soll-Zustand (`pat.render_zone(span.zone, ctx)`). Weicht der gespeicherte Inhalt ab (z. B. weil ein neues Handbuch hinzugekommen ist oder sich ein Titel geändert hat), weist die Diagnose mit Zeilennummer und Zonenname auf `DocFrame.update()` hin.

---

## 8. Deep-Dive: „Lego-Bausteine“, eigene `FramePattern`s und Dokument-Regeln entwickeln

Wie `DocEnsurance` folgt auch `DocFrame` dem Open-Closed-Prinzip über klar getrennte Schichten in `qb_cubie.core.services.doc_frame`:

1. **Ebene 0 (`_catalog_scanner`):** Fence-sicherer Span-Scanner (`parse_frame_spans`), Metadaten-Extraktor (`extract_doc_meta`) und Katalog-Builder (`DocumentCatalog`).
2. **Ebene 1 (`FrameBlockProtocol` in `frame_blocks`):** Zustandslose Struktur-Bausteine (`Divider`, `StaticBlock`, `AssetImage`, `CenterWrap`, `CompactNav`, `RouteGroup`), dynamische Katalog-Router (`FolderRouter`, `SiblingRouter`, `CatalogRouter`) und geschützte Content-Slots (`HeaderContentSlot`, `DisclaimerSlot`, `TitleSlot`, `ProvenanceBlock`, `PromptSlot`).
3. **Ebene 2 (`doc_frame_rules`):** Dokument-weite Prüfregeln über Core-`FileCheckProtocol` (`_DocFrameRuleBase` $\to$ `check_document`) für `DocEnsurance`.
4. **Ebene 3 (`FramePattern`, Presets & `DocFrame` in `presets` & `doc_frame`):** Zentrale Kopf-/Fuß-Templates (`STD_HEAD_BLOCKS`, `STD_FOOTER_BLOCKS`), verpflichtender erkenntnistheoretischer Hinweis-Anker (`EPISTEMIC_NOTICE` / `EPISTEMIC_NOTICE_TEXT`) und 2-Pass-Orchestrator.

### 8.1 Die mitgelieferten „Lego-Bausteine“ zu eigenen `FramePattern`s zusammensetzen

Alle drei Cubie-Presets werden deklarativ aus den Bausteinen in `qb_cubie.core.services.docframe` zusammengesteckt. Im ersten Schritt der Session `docframe_presets` definieren wir die Kopf-Schnellnavigation (`CompactNav`) sowie die dynamischen `FolderRouter`- und `SiblingRouter`-Instanzen:

```python session=docframe_presets
from qb_cubie.core.services.docframe import (
    CatalogRouter, CompactNav, FolderRouter, SiblingRouter,
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
        ("Entwicklerdokumentation", "docs/dev/README.md"),
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

Im zweiten Schritt bündeln wir die Router in einem zentrierten `<div align="center">`-Container (`CenterWrap`) für den gemeinsamen Footer (`STD_FOOTER_BLOCKS`) und konfigurieren den `CatalogRouter`:

```python session=docframe_presets
from qb_cubie.core.services.docframe import AssetImage, CenterWrap, Divider

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

Im dritten Schritt kombinieren wir die geschützten Content-Slots (`HeaderContentSlot`, `DisclaimerSlot`, `TitleSlot`, `ProvenanceBlock`, `PromptSlot`) sowie den festen erkenntnistheoretischen Hinweis-Anker (`EPISTEMIC_NOTICE`) mit den Navigations-Blöcken zu `FramePattern`-Definitionen:

```python session=docframe_presets
from qb_cubie.core.services.docframe import (
    EPISTEMIC_NOTICE, DisclaimerSlot, FramePattern, HeaderContentSlot, PromptSlot, ProvenanceBlock, TitleSlot,
)

STD_HEAD_BLOCKS = (
    CenterWrap(
        tag="div",
        blocks=(
            HeaderContentSlot(), Divider(), DisclaimerSlot(), Divider(),
            EPISTEMIC_NOTICE, Divider(), HEADER_QUICK_NAV,
        ),
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

### 8.2 Eigene Rahmen-Bausteine (`FrameBlockProtocol`) schreiben

Um einen völlig eigenen Baustein zu ergänzen – etwa eine Breadcrumb-Zeile, die den Katalog-Ordner (`meta.category`), das Anzeige-Label (`meta.label`) und einen tiefenkorrekten Rücklink zum Hauptverzeichnis (`compute_rel_link`) rendert –, implementiert man das `FrameBlockProtocol` über eine einzige Methode `render(self, ctx: FrameRenderContext) -> str`:

```python
from dataclasses import dataclass
from pathlib import Path
from qb_cubie.core.services.docframe import (
    DocumentCatalog, FramePattern, FrameRenderContext, FrameSpan, compute_rel_link, extract_doc_meta,
)


@dataclass(frozen=True)
class BreadcrumbBar:
    prefix: str = "Navigation:"

    def render(self, ctx: FrameRenderContext) -> str:
        meta = ctx.catalog.by_path(ctx.rel_path)
        root_link = compute_rel_link(ctx.file_path, "README.md", ctx.catalog.root)
        return f"{self.prefix} [Root]({root_link}) / `{meta.category}` / **{meta.label}**"


raw = '<!-- qb:frame id="CUSTOM_FRAME" zone="head" -->\n# Mein Service-Guide\n<!-- /qb:frame -->\n'
cat = DocumentCatalog(root=Path("/repo"), entries=(extract_doc_meta("docs/services/guide.md", raw),))
span = FrameSpan("CUSTOM_FRAME", "head", {}, "<!-- qb:frame -->", "# Mein Service-Guide\n", "<!-- /qb:frame -->", 1, 3, 0, len(raw))
ctx = FrameRenderContext(Path("/repo/docs/services/guide.md"), "docs/services/guide.md", cat, span)
pattern = FramePattern(id="CUSTOM_FRAME", head=(BreadcrumbBar(),))
print(pattern.render_zone("head", ctx))
```

<details>
<summary>Ergebnis</summary>

```text
Navigation: [Root](../../README.md) / `docs/services` / **Mein Service-Guide**
```
</details>

### 8.3 Eigene Datei-Prüfregeln (`FileCheckProtocol`) für `DocEnsurance` entwickeln

Möchte ein Team neben `CUBIE_DOCFRAME_RULES` eigene Rahmen-Konventionen in `DocEnsurance` prüfen (z. B. dass jeder `CUBIE_DOC_FRAME_1`-Header zwingend ein explizites `banner="..."`-Attribut im öffnenden Kommentar-Tag deklarieren muss), implementiert man eine `@dataclass(frozen=True)` nach dem domänenneutralen Core-`FileCheckProtocol` (`context_key`, `prepare_context`, `check_file`) mit `validate_severity` und Core-`Diagnostic`:

```python
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from qb_cubie.core.protocols import Diagnostic, FileCheckProtocol, validate_severity
from qb_cubie.core.services import DocEnsurance
from qb_cubie.core.services.docframe import parse_frame_spans

@dataclass(frozen=True)
class RequireExplicitBannerRule:
    rule_id: str = "DOCFRAME-EXPLICIT-BANNER"
    severity: str = "warning"
    context_key: str = "explicit-banner"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def prepare_context(self, target: str | Path, excludes: Sequence[str], patterns: Sequence[Any]) -> None:
        return None

    def check_file(self, file_path: str, content: str, context: None) -> list[Diagnostic]:
        spans, _ = parse_frame_spans(content)
        return [
            Diagnostic(file_path, self.rule_id, s.start_line, "Missing explicit banner attribute.", self.severity)
            for s in spans if s.zone == "head" and s.frame_id == "CUBIE_DOC_FRAME_1" and not s.attrs.get("banner")
        ]

service = DocEnsurance(rules=[RequireExplicitBannerRule], reporter=None)
print(f"FileCheck={isinstance(RequireExplicitBannerRule(), FileCheckProtocol)} | {[r.rule_id for r in service.rules]}")
```

<details>
<summary>Ergebnis</summary>

```text
FileCheck=True | ['DOC-OUT-MISSING', 'DOC-OUT', 'DOCFRAME-EXPLICIT-BANNER']
```
</details>

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

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
