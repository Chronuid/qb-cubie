<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# `DocFrame` (Prototyp)

![Cubie](../../.assets/cubie-logo-written.png)

Das `doc_frame`-Paket bildet den **Prototyp** einer zweistufigen Synchronisations-, Routing- und Verifikations-Engine für Markdown-Dokumentrahmen innerhalb von `qb_cubie.core.services` (noch zu evaluieren und zu härten). Es setzt auf dem gemeinsamen `qb_cubie.core.service_core` auf und kombiniert **Zero-Config-Katalogisierung** (Pass 1: Fence-sicherer Span-Scanner & Metadaten-Extraktion in einen unveränderlichen `DocumentCatalog` mit reinem `WorkspaceView`-Port), **tiefen- und kontextsensitives Rendering** (Pass 2: I/O-freie `FrameBlockProtocol`-Bausteine, geschützte Content-Slots, dynamische Router und atomares `atomic_write_text`) sowie **eigenständige Rahmen-Verifikation** über `DocFrame.check()` (`FileCheckRunner` + `CUBIE_DOCFRAME_RULES`).

---

> [!WARNING]
>
> **Entwicklungsstatus: Prototyp – Evaluation und Härtung ausstehend:**  
> `qb_cubie.core.services.doc_frame` ist als **Prototyp** markiert und muss vor einer Stabilitätsfreigabe noch systematisch evaluiert (z. B. gegen heterogene Markdown-Dialekte, Edge-Cases im Scanner und größere Dokumentationsbäume) sowie gehärtet werden. Änderungen an DTOs, Presets und Regel-Semantik bleiben ausdrücklich vorbehalten.

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

---

---

## Paket-Topologie & Architektur-Überblick

Um die Schranken des Cubie-Styleguides ($\le 500$ Zeilen pro Service-Modul, $\le 12$ Codezeilen pro Funktionskörper, einzeilige Docstrings) und Meta-Gate 4 (`META-SERVICE-PURE-DOMAIN-IO`, kanonisches `adapters.py`/`cli.py`-Layout) strikt einzuhalten und gleichzeitig eine offene Erweiterbarkeit nach dem **Open-Closed-Prinzip** zu gewährleisten, ist `src/qb_cubie/core/services/doc_frame/` in spezialisierte Module unterteilt (ergänzt durch das Kurz-Alias-Modul `src/qb_cubie/core/services/docframe.py`) und delegiert domänenneutrale Infrastruktur (Guards, Workspace, `FileCheckRunner`, Reporting, `cli_spec`) sowie Markdown-Lexer-Primitiven (`service_core.markdown`) vollständig an [`qb_cubie.core.service_core`](../../services/GUIDE_Service-Core.md):

| Modul | Architektonische Rolle | Kern-Komponenten |
| :--- | :--- | :--- |
| **`protocols.py`** | Unveränderliche Daten-Container (DTOs), Sortier-Invariante, Guard-Validatoren (via `service_core.guards.validate_choice`) und Protokoll-Vertrag | `DocMeta`, `FrameSpan`, `DocumentCatalog` (mit `workspace: WorkspaceView \| None`), `FrameRenderContext`, `DocFrameReport` (mit `.service == "doc_frame"`), `FrameBlockProtocol`, `sort_doc_metas`, `validate_zone`, `validate_wrap_tag`, `validate_catalog_mode`, `VALID_ZONES`, `VALID_WRAP_TAGS`, `VALID_CATALOG_MODES` |
| **`_catalog_scanner.py`** | Fence-sicherer Kommentar-Scanner (via `service_core.markdown.DirectiveSpanScanner("frame")`, `parse_kv_attrs`, `HTML_WRAP_RE`, `is_horizontal_rule`) & Pass-1-Metadaten-Extraktor (Ebene 0, I/O-frei) | `_FRAME_SCANNER`, `parse_frame_spans`, `parse_tag_attrs`, `extract_doc_meta`, `build_catalog_from_sources` |
| **`frame_blocks.py`** | 100 % I/O-freie Struktur-Bausteine (re-exportiert `compute_rel_link` und nutzt `HTML_WRAP_RE` aus `service_core.markdown`), dynamische Router (via `WorkspaceView.has_path`) & geschützte Content-Slots (Ebene 1) | `Divider`, `StaticBlock`, `AssetImage`, `CenterWrap`, `CompactNav`, `RouteGroup`, `FolderRouter`, `SiblingRouter`, `CatalogRouter` (`CatalogTable`), `HeaderContentSlot`, `DisclaimerSlot`, `TitleSlot`, `ProvenanceBlock`, `PromptSlot`, `compute_rel_link`, `resolve_banner_rel_path` |
| **`presets.py`** | Zentrale Single Source of Truth für Kopf-/Fuß-Templates, Standard-Presets & den verpflichtenden erkenntnistheoretischen Anker (Ebene 2, I/O-frei) | `FramePattern`, `EPISTEMIC_NOTICE_TEXT`, `EPISTEMIC_NOTICE`, `CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2`, `CUBIE_DOC_FRAME_3`, `DEFAULT_FRAME_PATTERNS`, `STD_HEAD_BLOCKS`, `STD_FOOTER_BLOCKS`, `HEADER_QUICK_NAV`, `GUIDE_ROUTER`, `SERVICE_ROUTER`, `CONTEXT_ROUTER`, `AUTO_INDEX_ROUTER` |
| **`doc_frame_rules.py`** | I/O-freie Dokument-Diagnose-Regeln nach `WorkspaceCheckRuleProtocol` mit `FileContextCache` & `depends_on` (Ebene 2) | `_DocFrameRuleBase`, `DocFrameMissing` (`DocFrameMissingRule`), `DocFrameOutdated` (`DocFrameOutdatedRule`, inkl. `allow_empty_foot`), `DocFrameBrokenRoute` (`DocFrameBrokenRouteRule`), `DocFrameProvenanceIncomplete` (`DocFrameProvenanceRule`), `DocFrameFootLinks` (`DocFrameFootLinksRule`), `CUBIE_DOCFRAME_RULES` |
| **`rule_profiles.py`** | Preset-spezifische Profilbindungen & Regelsets nach SRP (Ebene 2) | `FrameRuleProfile`, `DocFrameRuleSet`, `CUBIE_DOCFRAME_PROFILE_1..3`, `CUBIE_DOCFRAME_RULE_SET` |
| **`adapters.py`** | Imperative Shell für Dateisystem-Auflösung, Katalog-Crawling & `FileSystemWorkspaceView`-Injektion | `resolve_target_path`, `normalize_frame_patterns`, `resolve_catalog_root`, `build_workspace_catalog`, `prepare_docframe_workspace` |
| **`cli.py` & `__main__.py`** | Lazy CLI-Adapter nach `service_core.cli_spec.ServiceCommandProtocol` (`qb-cubie docframe update\|check`) | `DocFrameCommand`, `COMMAND`, Module-Entrypoint `python -m qb_cubie.core.services.doc_frame` |
| **`doc_frame.py`** | 2-Pass-Orchestrator (`update`, `check`, `scan_catalog`) via `service_core` (`FileCheckRunner`, `atomic_write_text`, `apply_span_replacements`) & Preset-Re-Export (Ebene 3) | `DocFrame` (sowie Re-Export von `FramePattern` und allen Presets aus `presets.py`) |

---

## Konstruktor-API, Klassenmethoden & Konfiguration (Quick-Lookup)

Die Klasse `DocFrame` fungiert sowohl als zustandsbehafteter Service-Orchestrator (`DocFrame(...).run()`) als auch über drei ergonomische Klassenmethoden (`DocFrame.update(...)`, `DocFrame.check(...)` und `DocFrame.scan_catalog(...)`). Der Konstruktor delegiert Validierungen direkt an `adapters.py` und `service_core`:

* **`target`** (`str | Path | None`, Default: `None`): Bestimmt den zu synchronisierenden oder zu prüfenden Ziel-Scope (`adapters.resolve_target_path`). `None` löst über `service_core.workspace.find_project_root()` automatisch das Projekt-Root anhand der nächstgelegenen `pyproject.toml` (Fallback: `Path.cwd()`) auf. Akzeptiert existierende Datei- oder Verzeichnispfade; leere Strings (`ValueError`), falsche Typen (`TypeError`) oder nicht existierende Pfade (`FileNotFoundError`) werden sofort abgewiesen.
* **`pattern`** (`FramePattern | Sequence[FramePattern] | None`, Default: `None`): Ein einzelnes `FramePattern` oder eine nicht-leere Sequenz/Mapping von `FramePattern`-Objekten, die in `adapters.normalize_frame_patterns` zu einem ID-indizierten Dictionary `dict[str, FramePattern]` normalisiert werden. `None` registriert automatisch `DEFAULT_FRAME_PATTERNS` (`CUBIE_DOC_FRAME_1`, `CUBIE_DOC_FRAME_2`, `CUBIE_DOC_FRAME_3`).
* **`excludes`** (`Sequence[str] | None`, Default: `None`): Optionale Sequenz zusätzlicher Datei-, Ordner- oder Teilpfad-Ausschlüsse, die über `service_core.workspace.normalize_excludes` strikt validiert (`excludes="str"` $\to$ `TypeError("STATE-GUARD")`) und mit `DEFAULT_EXCLUDES` vereinigt werden.
* **`reporter`** (`Reporter[DocFrameReport] | None` bei `DocFrame`/`update`, Default: `None`; `Reporter[ServiceReport] | None` bei `check`, Default: `PytestReporter()`): Pluggable Reporter (`PytestReporter`, `JsonReporter` oder `None`).

### Einstiegspunkte für Synchronisation, Prüfung und Analyse

1. **`DocFrame.update(target=None, pattern=None, excludes=None, reporter=None) -> DocFrameReport`:**
   Führt Pass 1 (`build_catalog`) und Pass 2 (`_render_file_frames`) aus, schreibt nur real geänderte Dateien (`new_content != content`) atomar über `service_core.workspace.atomic_write_text` zurück, benachrichtigt optional `reporter` und gibt den `DocFrameReport` inklusive `updated_files` und `catalog` zurück.
2. **`DocFrame.check(target=None, pattern=None, rules=None, excludes=None, reporter=PytestReporter()) -> ServiceReport`:**
   Baut den `DocumentCatalog` einmalig auf und delegiert die vollständige Multi-File-Verifikation nativ an `service_core.rules.FileCheckRunner` (Standardregeln: `CUBIE_DOCFRAME_RULES`, `service="doc_frame"`). Läuft 100 % isoliert ohne Import von `doc_ensurance`.
3. **`DocFrame.scan_catalog(target=None, excludes=None) -> DocumentCatalog`:**
   Führt ausschließlich Pass 1 (`build_catalog`) aus und liefert den unveränderlichen `DocumentCatalog` (inkl. `FileSystemWorkspaceView`) ohne Dateisystem-Schreibzugriffe zurück.
4. **Lazy CLI-Einstiegspunkt (`src/qb_cubie/cli.py` + `doc_frame/cli.py`, `[project.scripts].qb-cubie`):**
   `qb-cubie docframe update|check [target] [--exclude ...] [--format text|json]` (sowie `python -m qb_cubie docframe ...`, `python -m qb_cubie.core.services.docframe ...` und `python -m qb_cubie.core.services.doc_frame ...`) wird lazy über `CommandSpec` geladen (ohne `doc_ensurance` zu importieren), delegiert über `DocFrameCommand` an `DocFrame.update(...)` bzw. `DocFrame.check(..., reporter=None)`, rendert Text oder `schema_version: 1`-JSON (`"service": "doc_frame"`, bei `update` zusätzlich mit abwärtskompatiblen Feldern `updated_files` und `catalog_entries`) und nutzt die einheitlichen Exit-Codes `0` (`EXIT_OK`), `1` (`EXIT_CHECK_FAILED` bei `passed=False`) und `2` (`EXIT_ERROR` bei `ValueError`, `TypeError`, `OSError`).

### Architektur-Invariante: Katalog-Root vs. Ziel-Scope (`adapters.resolve_catalog_root`)

Wird `DocFrame` gezielt auf eine einzelne Datei oder einen Unterordner angesetzt (z. B. `DocFrame.update(target="docs/services/GUIDE_DocFrame.md")`), trennt der Orchestrator strikt zwischen **Schreib-Scope** und **Katalog-Scope**:
* `service_core.workspace.load_sources(self.target_path, pattern="*.md", excludes=self.excludes, allow_in_memory=False)` lädt für Pass 2 ausschließlich die im `target` angeforderten Markdown-Dateien.
* `build_catalog()` ermittelt hingegen über `adapters.resolve_catalog_root(self.target_path)` (`find_project_root(..., markers=("pyproject.toml", "docs/.assets"), stop_at_cwd=True)`) das übergeordnete Repository-Root und injiziert `FileSystemWorkspaceView(catalog_root)` in den `DocumentCatalog`. Dadurch steht den dynamischen Routern (`FolderRouter`, `SiblingRouter`, `CatalogRouter`) selbst bei Einzeldatei-Updates immer der vollständige Projekt-Katalog zur Verfügung.

---

## 1. Kern-Datenstrukturen (DTOs), Sortier-Invariante & Protokoll-Verträge (`protocols.py`)

Sämtliche Datenstrukturen in `protocols.py` sind als unveränderliche `@dataclass(frozen=True)`-Records modelliert. Dadurch kann der in Pass 1 erzeugte `DocumentCatalog` gefahrlos über alle Datei-Kontexte in Pass 2 und alle Prüfregeln in `CUBIE_DOCFRAME_RULES` geteilt werden.

### 1.1 Die Daten-Pipeline (Vom Dokument-Header zum `DocFrameReport`)

1. **`DocMeta(path, frame_id, title, label, summary, order=None, routable=True, category=".", attrs={})`**
   Speichert die in Pass 1 aus einer Markdown-Datei extrahierten Routing-Metadaten:
   * `path`: Repository-relativer POSIX-Pfad ohne führenden Schrägstrich (z. B. `"docs/GUIDE_Linter.md"`).
   * `frame_id`: Die ID des öffnenden `zone="head"`-Rahmens (z. B. `"CUBIE_DOC_FRAME_1"`) oder `None`, falls die Datei keinen `head`-Rahmen besitzt.
   * `title` & `label`: Der extrahierte `# H1-Titel` (Fallback: Dateistamm) sowie das effektive Anzeige-Label für Router (`attrs.get("label") or title`).
   * `summary`: Der erste erklärende Textabsatz unterhalb des Banners im `head`-Rahmen (für Index-Tabellen in `CatalogRouter`).
   * `order` & `routable`: Optionale Sortier-Priorität (`int | None`) und Sichtbarkeits-Flag (`bool`) für dynamische Router.
   * `category`: Der POSIX-Elternpfad relativ zum Katalog-Root (z. B. `"."`, `"docs"`, `"docs/dev/services"`).

2. **`FrameSpan(frame_id, zone, attrs, open_tag, inner_content, close_tag, start_line, end_line, start_idx, end_idx)`**
   Repräsentiert einen einzelnen geparsten `<!-- qb:frame ... --> ... <!-- /qb:frame -->`-Block mit dualen Koordinaten:
   * `start_line` & `end_line`: 1-basierte Zeilennummern für präzise `Diagnostic`-Positionsangaben (`qb_cubie.core.protocols.Diagnostic`).
   * `start_idx` & `end_idx`: 0-basierte Zeichen-Offsets im Original-String für exaktes In-Place-Slicing während Pass 2.
   * `open_tag`, `inner_content`, `close_tag`: Der exakte öffnende Kommentar-Tag, der unmodifizierte Innenbereich zwischen den Tags sowie der schließende Kommentar-Tag.

3. **`DocumentCatalog(root, entries=(), workspace=None)`**
   Der unveränderliche Pass-1-Katalog aller gefundenen Markdown-Dokumente unterhalb von `root: Path` samt optionalem, I/O-freiem **`workspace: WorkspaceView | None`**-Read-Port (`FileSystemWorkspaceView` aus `adapters.py` oder `InMemoryWorkspaceView` in Tests):
   * `get(rel_path) -> DocMeta | None`: Sucht einen Eintrag anhand seines normalisierten POSIX-Pfads.
   * `by_path(rel_path) -> DocMeta`: Wie `get()`, wirft jedoch bei fehlendem Dokument einen expliziten `KeyError("STATE-GUARD: Document not found in catalog: ...")`.
   * `select(directory=".", glob="*.md", exclude=(), *, recursive=False, include_unroutable=False) -> list[DocMeta]`: Filtert Einträge nach Zielordner (`_matches_dir`), Dateinamen-Glob (`fnmatch.fnmatch`), Dateinamen- oder Pfad-Excludes sowie `routable`-Status und gibt sie deterministisch sortiert über `sort_doc_metas` zurück.

4. **`FrameRenderContext(file_path, rel_path, catalog, span)` & `DocFrameReport(target, passed, updated_files=(), catalog=None, diagnostics=())`**
   `FrameRenderContext` bündelt während Pass 2 den absoluten Dateipfad (`file_path`), den Katalog-relativen POSIX-Pfad (`rel_path`), den `DocumentCatalog` und den aktuell zu rendernden `FrameSpan`. `DocFrameReport` erfüllt `ServiceReportProtocol`, lässt sich direkt an `PytestReporter` oder `JsonReporter` übergeben und fasst die Pfade aller real aktualisierten Dateien (`updated_files`), den Katalog und etwaige Diagnosen zusammen.

### 1.2 Dreistufige Sortier-Invariante (`sort_doc_metas`) & Guard-Validatoren

Damit automatisch generierte Fußzeilen und Index-Tabellen über alle Betriebssysteme und Dateisysteme hinweg eine reproduzierbare Reihenfolge aufweisen, bildet `_doc_meta_sort_key(entry)` ein vierstelliges Sortier-Tupel `(tier, order_val, name, path)`:
* **Stufe 0 (`(0, 0, name, path)`):** Eine `README.md` ohne explizites `order`-Attribut (`entry.order is None`) steht im jeweiligen Ordner immer auf Platz 1.
* **Stufe 1 (`(1, entry.order, name, path)`):** Dokumente mit explizitem `order="<int>"`-Attribut im `head`-Tag folgen aufsteigend nach ihrem Zahlenwert (bei Gleichstand alphabetisch nach Dateiname und Pfad).
* **Stufe 2 (`(2, 0, name, path)`):** Alle übrigen Dokumente ohne `order`-Attribut folgen deterministisch alphabetisch nach Dateiname (`Path(entry.path).name`) und relativem Gesamtpfad.

Flankiert wird `protocols.py` durch drei strikte `STATE-GUARD`-Validatoren:
* `validate_zone(zone)`: Erlaubt ausschließlich `VALID_ZONES = ("head", "router", "foot")`.
* `validate_wrap_tag(tag)`: Erlaubt für `CenterWrap` ausschließlich `VALID_WRAP_TAGS = ("div", "center")`.
* `validate_catalog_mode(mode)`: Erlaubt für `CatalogRouter` ausschließlich `VALID_CATALOG_MODES = ("table", "links")`.

---

## 2. Pass 1: Fence-sicherer Span-Scanner & Zero-Config-Katalogisierung (`_catalog_scanner.py`)

In Pass 1 analysiert `_catalog_scanner.py` alle Markdown-Dateien des Projekts ohne externe Parser-Abhängigkeiten.

### 2.1 Zeilenbasierte Span-Erkennung & Fence-Isolation (`service_core.markdown.DirectiveSpanScanner`)

Ein Dokumentations-Handbuch (wie `GUIDE_DocFrame.md` oder dieser Dev-Guide) enthält in seinen Markdown-Codeblöcken häufig selbst Beispiel-Kommentare der Form `<!-- qb:frame id="..." -->`. Ein naiver Regex-Lauf über den gesamten Datei-String würde diese Code-Beispiele fälschlicherweise als echte Rahmen-Zonen des Dokuments interpretieren.

`_catalog_scanner.py` delegiert das gesamte Scanning über `_FRAME_SCANNER = DirectiveSpanScanner("frame", validate_attrs=_validate_frame_attrs)` an `qb_cubie.core.service_core.markdown` und übersetzt die zurückgegebenen `DirectiveSpan`-Records in typisierte `FrameSpan`-DTOs (`parse_frame_spans(content) -> tuple[list[FrameSpan], list[int]]`):

1. **Dynamisches Code-Fence-Tracking (`FenceTracker`):**
   Beginnt eine getrimmte Zeile außerhalb eines Fences mit mindestens drei Backticks (`` ``` ``) oder Tilden (`~~~`), merkt sich `FenceTracker` den exakten Fence-Präfix (z. B. ```` ```` ```` bei einem 4-Backtick-Block). Solange der Fence aktiv ist, ignoriert der Scanner sämtliche `qb:frame`-Tags im Inneren. Erst eine Zeile aus mindestens genauso vielen identischen Fence-Zeichen ohne Folgezeichen schließt den Fence.
2. **Strikte Attribut-Extraktion & Sofort-Guards (`parse_kv_attrs(..., mode="quoted")` & `_validate_frame_attrs`):**
   Trifft `DirectiveSpanScanner` außerhalb eines Fences auf einen einzeiligen Öffnungs-Tag (`^<!--\s*qb:frame(?=\s|-->)([^>]*)-->$`), parst `parse_kv_attrs(..., mode="quoted")` (auch re-exportiert als `parse_tag_attrs`) strikt Leerzeichen-getrennte `key="val"`- oder `key='val'`-Paare. Ungequotete Werte (z. B. `order=10`) oder syntaktisch defekte Tokens werfen sofort `ValueError("STATE-GUARD: Malformed or unquoted attribute ...")` statt still ignoriert zu werden. Anschließend prüft `_validate_frame_attrs`, dass `id` nicht leer ist und `zone` (Default: `"head"`) in `VALID_ZONES` liegt.
3. **Erkennung unvollständiger & ungeschlossener Rahmen (`unclosed`):**
   Ein unvollständiger Öffnungs-Tag (`<!-- qb:frame ...` ohne `-->` auf derselben Zeile), ein neu geöffneter `qb:frame`-Tag vor einem schließenden `<!-- /qb:frame -->` oder ein offener Tag am Dateiende tragen die 1-basierte Startzeile direkt in `unclosed: list[int]` ein.

### 2.2 Zero-Config-Metadaten-Extraktion (`extract_doc_meta`)

Jedes Dokument im Repository fungiert über seinen `zone="head"`-Rahmen als eigene Single Source of Truth für alle Router. `extract_doc_meta(rel_path, content)` extrahiert daraus vollautomatisch das `DocMeta`-Objekt:

* **H1-Titel (`_extract_h1_title`):** Sucht im `head.inner_content` (bzw. im gesamten Dokument, falls kein `head`-Span existiert) die erste Zeile, die getrimmt mit `"# "` beginnt. Besitzt das Dokument keine H1-Überschrift, fällt der Titel auf `Path(fallback_path).stem` zurück.
* **Router-Label:** Nutzt `attrs.get("label", "").strip()` falls angegeben, andernfalls direkt den extrahierten `title`.
* **Kurzbeschreibung vor dem ersten Divider (`_extract_header_summary`):**
  `_slice_before_divider` schneidet alle Zeilen des `head.inner_content` vor der ersten horizontalen Linie (`---`) aus. Anschließend überspringt `_is_ignorable_header_line` führende Leerzeilen, HTML-Wrapper (`<div...>`, `</div>`, `<center>`, `</center>` via `_HTML_WRAP_RE`), Überschriften (`#`) und Banner-Bilder (`![...](...)`). Die Zeilen des ersten echten Textabsatzes werden mit `" ".join(para_lines)` verbunden; die nächste Leer- oder Wrapper-Zeile beendet die Extraktion sofort, sodass zweite Absätze oder Disclaimer niemals in die Kurzbeschreibung der Index-Tabellen bluten.
* **Typ-sichere `order`- und `routable`-Parser (`service_core.guards`):**
  Delegiert an `parse_int_attr(raw, "order")` (wirft `ValueError("STATE-GUARD: order must be an integer...")`) und `parse_bool_attr(raw, "routable", default=True)` (`("true", "1", "yes")` vs. `("false", "0", "no")`). Zusätzlich erzwingt `bool(content.strip())`, dass leere 0-Byte-Dateien immer als `routable=False` eingestuft werden.

Das folgende ausführbare Beispiel demonstriert, wie `parse_frame_spans` einen `qb:frame`-Tag innerhalb eines Code-Fences ignoriert und wie `extract_doc_meta` Titel, Label, Kurzbeschreibung und Sortier-Attribute extrahiert:

```python
from qb_cubie.core.services.doc_frame import extract_doc_meta, parse_frame_spans

fence = "```"
raw_md = (
    '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" label="Kurz-Label" order="15" -->\n'
    '<div align="center">\n\n# Vollständiger Handbuch-Titel\n\n'
    "![Cubie](.assets/cubie-logo-written.png)\n\n"
    "Erster Satz der Zusammenfassung\nüber zwei Zeilen.\n\n---\n\n</div>\n"
    "<!-- /qb:frame -->\n\n"
    f"{fence}markdown\n<!-- qb:frame id=\"IGNORED\" zone=\"head\" -->\n<!-- /qb:frame -->\n{fence}\n"
)

spans, unclosed = parse_frame_spans(raw_md)
meta = extract_doc_meta("docs/services/GUIDE_Demo.md", raw_md)
print(f"spans={len(spans)} | unclosed={unclosed} | label={meta.label!r} | order={meta.order}")
print(f"summary={meta.summary!r} | category={meta.category!r}")
```

<details>
<summary>Ergebnis</summary>

```text
spans=1 | unclosed=[] | label='Kurz-Label' | order=15
summary='Erster Satz der Zusammenfassung über zwei Zeilen.' | category='docs/services'
```
</details>

---

## 3. Pass 2: Die „Lego-Blöcke“, Dynamische Router & Geschützte Content-Slots (`frame_blocks.py`)

Alle Bausteine innerhalb einer Rahmen-Zone implementieren das `@runtime_checkable` `FrameBlockProtocol`:

```text
@runtime_checkable
class FrameBlockProtocol(Protocol):
    def render(self, ctx: FrameRenderContext) -> str: ...
```

### 3.1 Tiefen-Auflösung & Statische Struktur-Bausteine

Damit ein einziges `FramePattern` für Dokumente auf beliebiger Verzeichnistiefe (`README.md`, `docs/GUIDE_Linter.md`, `docs/dev/services/DEV-GUIDE_DocFrame.md`) gültige Links erzeugt, berechnen zwei Hilfsfunktionen alle Pfade zur Render-Laufzeit relativ zu `ctx.file_path`:

* **`compute_rel_link(from_file, target_rel, root) -> str`:**
  Löst `target_rel` gegen `root.resolve()` auf, berechnet `os.path.relpath(target_abs, start=from_file.resolve().parent)` mit POSIX-Schrägstrichen und stellt sicher, dass der Pfad immer explizit mit `./` oder `../` beginnt.
* **`resolve_banner_rel_path(banner, root, workspace=None) -> str`:**
  Enthält `banner` bereits einen Pfadtrenner (`/`), bleibt der relative Pfad erhalten. Wird nur ein Dateiname wie `"cubie-logo-written.png"` übergeben, prüft die Funktion I/O-frei über den injizierten `WorkspaceView`-Port (`workspace.has_path(f".assets/{clean}")` ohne `docs/.assets/<clean>`) und liefert standardmäßig `"docs/.assets/<clean>"`.

Darauf bauen fünf statische Struktur- und Navigations-Bausteine auf:
1. **`Divider()`:** Rendert `"---"`.
2. **`AssetImage(path="docs/.assets/cubie-small.png", alt="Cubie")`:** Validiert im `__post_init__`, dass `path` und `alt` nicht-leere Strings sind (`STATE-GUARD`), und rendert `![{self.alt}]({compute_rel_link(...)})`.
3. **`CenterWrap(tag="div", blocks=())`:** Prüft `tag` über `validate_wrap_tag` (`"div"` erzeugt `<div align="center">`, `"center"` erzeugt `<center>`). Rendert alle Kind-Blöcke, **filtert leere Rückgabestrings aus** (`[out for block in self.blocks if (out := block.render(ctx))]`) und verbindet die nicht-leeren Ausgaben durch Leerzeilen (`"\n\n"`).
4. **`CompactNav(routes=(), separator=" • ")`:** Rendert eine einzeilige Schnellnavigation (`[Label](rel_link) • ...  `) inklusive zweier abschließender Leerzeichen für den Markdown-Zeilenumbruch.
5. **`RouteGroup(routes=())`:** Formatiert statische `(label, repo_rel_path)`-Tupel über `_format_route_lines` als `[↦ | {label} | ↤]({rel_link})  `.

### 3.2 Dynamische Katalog-Router (`FolderRouter`, `SiblingRouter`, `CatalogRouter`)

Anstatt Routen manuell in Python-Tupeln zu pflegen, fragen die drei Router-Bausteine während Pass 2 den `ctx.catalog` ab:

1. **`FolderRouter(dir="docs", glob="*.md", exclude=())`:**
   Ruft `ctx.catalog.select(self.dir, glob=self.glob, exclude=self.exclude)` auf und formatiert jedes gefundene `DocMeta` als `[↦ | {e.label} | ↤]({rel_link})  `.
2. **`SiblingRouter(hubs=(), include_hubs=True, exclude=("README.md",))`:**
   Verhindert, dass der globale Footer bei wachsender Zahl von Unterordner-Dokumenten überläuft, und bietet gleichzeitig volle Tiefen-Navigation innerhalb von Unterordnern:
   * Ermittelt den Elternordner des aktuellen Dokuments (`parent_dir = Path(ctx.rel_path).parent.as_posix()`) und prüft `expand_sub = parent_dir not in (".", "docs", "docs/services")`.
   * **In Haupt- und Service-Guides (`expand_sub is False`):** Rendert nur die konfigurierten Bereichs-Hubs (`self.hubs`). Dabei löst `_resolve_hub_target(catalog, target)` jeden Hub I/O-frei auf: Existiert die Zieldatei im Katalog oder über `catalog.workspace.has_path(norm)`, wird sie direkt verlinkt; andernfalls fällt der Hub automatisch auf das erste routbare Markdown-Dokument im selben Ordner zurück.
   * **Innerhalb eines Unterordners (`expand_sub is True`, z. B. `docs/dev` oder `docs/dev/services`):** Übergibt `skip_dir=parent_dir` an `_append_hubs` (sodass der Sammel-Hub des eigenen Ordners ausgeblendet wird) und klappt stattdessen alle routbaren Geschwister-Dokumente aus `parent_dir` (exklusive `README.md`) direkt im Footer auf. Ein `seen: set[str]` verhindert doppelte Pfad-Einträge.
3. **`CatalogRouter(default_mode="table", exclude=("README.md",), extract_summary=True, dir=".", recursive=False)` (Alias `CatalogTable`):**
   Wird in `CUBIE_DOC_FRAME_3`-Index-Dokumenten innerhalb von `zone="router"` eingesetzt und wertet die Attribute des `<!-- qb:frame ... -->`-Tags dynamisch aus:
   * `mode`: Überschreibt `self.default_mode` per Tag-Attribut (`mode="table"` oder `mode="links"`, abgesichert durch `validate_catalog_mode`).
   * `dir`: `_resolve_dir(ctx)` löst `""` oder `"."` auf den Elternordner der aktuellen Datei auf; ist `raw` im `catalog.workspace` vorhanden (`workspace.has_path(raw)`), wird der Pfad ab Repository-Root interpretiert, andernfalls relativ zum Elternordner der aktuellen Datei.
   * `recursive` & `glob`: `_resolve_recursive` delegiert an `service_core.guards.parse_bool_attr` (mit `STATE-GUARD` bei ungültigen Werten); `glob` steuert das Dateimuster (Default: `"*.md"`).
   * **Selbst-Ausschluss:** Das aufrufende Index-Dokument selbst wird über `if e.path != ctx.rel_path` immer ausgefiltert. Im Modus `"table"` erzeugt `_render_table` eine zweispaltige Markdown-Tabelle (`| Dokument | Inhalt und Geltung |`), im Modus `"links"` eine `[↦ | ... | ↤]`-Routenliste.

### 3.3 Geschützte Content-Slots (`HeaderContentSlot`, `DisclaimerSlot`, `TitleSlot`, `ProvenanceBlock`, `PromptSlot`)

Damit `DocFrame.update()` Banner-Pfade, Alt-Texte, Provenance-Felder und Navigationsleisten aktualisieren kann, ohne den vom Autor verfassten Titel, Einführungstext, Disclaimer oder Prompt anzutasten, zerlegen die Content-Slots den bestehenden `ctx.span.inner_content` über `_strip_outer_html_wrappers` und `_split_by_dividers` an den horizontalen Linien (`---`):

* **`HeaderContentSlot(default_banner="cubie-logo-written.png", alt="Cubie")`:**
  Analysiert das Segment vor dem ersten `---` (`first_seg = _split_by_dividers(inner_lines)[0]`) über `_scan_header_lines`:
  * Isoliert die erste `# `-Überschrift (`title`), die erste Bildzeile `_IMG_BANNER_RE` (`existing_banner = Path(m.group(1)).name`) und alle übrigen Textzeilen (`body_lines`).
  * Bestimmt den Banner-Dateinamen nach der Prioritätskette `ctx.span.attrs.get("banner") or existing_banner or self.default_banner` und berechnet über `resolve_banner_rel_path` und `compute_rel_link` den tiefenkorrekten Pfad mit normiertem Alt-Text `![Cubie](...)`.
  * Setzt `# {title}`, `![{self.alt}]({banner_rel})` und den unveränderten Einführungstext (`intro`) wieder zusammen.
* **`DisclaimerSlot(optional=True)`:**
  Extrahiert in `CUBIE_DOC_FRAME_1` und `CUBIE_DOC_FRAME_3` alle dokument-spezifischen Zwischensegmente `segments[1:-1]` (sofern `len(segments) >= 3`) und filtert dabei automatisch jedes Segment heraus, das den Anker-Marker `_EPISTEMIC_MARKER = "erkenntnistheoretischen Grenzen"` enthält. So bleibt ein optionaler Dokument-Disclaimer verlustfrei erhalten, während der zentrale erkenntnistheoretische Hinweis (`EPISTEMIC_NOTICE` aus `presets.py`) weder überschrieben noch dupliziert wird. Besitzt ein Dokument keinen eigenen Disclaimer, gibt `DisclaimerSlot.render` einen leeren String `""` zurück und `CenterWrap` dedupliziert aufeinanderfolgende `---`-Trenner über `_dedupe_dividers`.
  * **Zentrale Pflege:** Änderungen am Wortlaut des erkenntnistheoretischen Hinweises erfolgen ausschließlich in `src/qb_cubie/core/services/doc_frame/presets.py` (`EPISTEMIC_NOTICE_TEXT`, unter Erhalt von `_EPISTEMIC_MARKER`) mit anschließendem `DocFrame.update(...)`.
* **`TitleSlot(optional=True)`, `ProvenanceBlock(required_keys=...)` & `PromptSlot(optional=True)` (`CUBIE_DOC_FRAME_2`):**
  * `TitleSlot` bewahrt eine vorhandene `# `-Überschrift vor dem ersten `---` oder generiert sie aus einem optionalen `title="..."`-Marker-Attribut.
  * `ProvenanceBlock` parst alle bestehenden Aufzählungspunkte der Form `- **Key:** Value` (`_PROV_BULLET_RE`) vor dem ersten `---` und überlagert sie mit den Attribut-Overrides aus dem öffnenden Kommentar-Tag (`_ATTR_TO_PROV_KEY`: `env` $\to$ `"Plattform / Umgebung"`, `model` $\to$ `"Modell"`, `effort` $\to$ `"Reasoning-Effort"` sowie direkte Schlüsselnamen). Dabei werden zuerst alle `required_keys` in kanonischer Reihenfolge ausgegeben und danach sämtliche benutzerdefinierten Zusatzfelder (z. B. `- **Analysedatum:** ...` oder `- **Synthesebasis:** ...`) verlustfrei angehängt.
  * `PromptSlot` konserviert den gesamten Text unterhalb des ersten `---` (`"\n---\n".join(...)` über `segments[1:]`), selbst wenn der Prompt-Text eigene horizontale Linien enthält.

---

## 4. Rahmen-Muster (`FramePattern`), Standard-Presets & Orchestrierung (`doc_frame.py`)

### 4.1 `FramePattern` als reiner Zonen-Renderer & die drei Standard-Presets

`FramePattern(id, head=(), foot=(), router=())` definiert die Block-Komposition für die drei Zonen `"head"`, `"router"` und `"foot"` ohne jegliche Fremd-Protokoll-Adapter oder Dummy-Methoden:
* Im `__post_init__` prüft `_validate_block_sequence`, dass `id` nicht leer ist und jede Zone ausschließlich `FrameBlockProtocol`-Instanzen enthält (`STATE-GUARD`).
* `render_zone(zone, ctx)` validiert den Zonennamen über `validate_zone`, rendert alle Blöcke der Zone und verbindet nicht-leere Ergebnisse mit `"\n\n"`.
* Die früheren Dummy-Methoden `name` und `scan()` für `DocPatternProtocol` wurden im Zuge des Service-Core-Umbaus ersatzlos entfernt, da `DocFrame.check()` nun nativ über `FileCheckRunner` läuft.

In `presets.py` (und re-exportiert über `doc_frame.py`) sind daraus drei Standard-Presets (`DEFAULT_FRAME_PATTERNS`) vordefiniert:

| Preset | `head`-Komposition | `router`-Komposition | `foot`-Komposition |
| :--- | :--- | :--- | :--- |
| **`CUBIE_DOC_FRAME_1`** | `STD_HEAD_BLOCKS`: `CenterWrap(tag="div", blocks=(HeaderContentSlot(), Divider(), DisclaimerSlot(), Divider(), EPISTEMIC_NOTICE, Divider(), HEADER_QUICK_NAV))` | `()` | `STD_FOOTER_BLOCKS`: `Divider(), Divider(), CenterWrap(tag="div", blocks=(AssetImage(...), GUIDE_ROUTER, SERVICE_ROUTER, CONTEXT_ROUTER))` |
| **`CUBIE_DOC_FRAME_2`** | `(TitleSlot(optional=True), ProvenanceBlock(required_keys=("Plattform / Umgebung", "Modell", "Reasoning-Effort")), Divider(), PromptSlot(optional=True))` | `()` | `STD_FOOTER_BLOCKS` |
| **`CUBIE_DOC_FRAME_3`** | `STD_HEAD_BLOCKS` | `(AUTO_INDEX_ROUTER,)` (`CatalogRouter(default_mode="table", exclude=("README.md",), extract_summary=True)`) | `STD_FOOTER_BLOCKS` |

### 4.2 Rückwärts-Slicing, Zeilenumbruch-Invariante & Idempotenz (`_render_file_frames`)

Wenn `DocFrame.run()` in Pass 2 eine Datei aktualisiert, müssen `head`-, `router`- und `foot`-Spans ersetzt werden, ohne den dazwischenliegenden Dokumentkörper zu verändern:

* **In-Place-Ersetzung in umgekehrter Reihenfolge (`service_core.markdown.apply_span_replacements`):**
  Da eine neu gerenderte `head`- oder `router`-Zone länger oder kürzer sein kann als der bisherige `inner_content`, würden sich bei einer Ersetzung von oben nach unten die Zeichen-Offsets (`start_idx`, `end_idx`) aller nachfolgenden Spans verschieben. `_render_file_frames` sammelt alle `(span.start_idx, span.end_idx, rendered)`-Tupel und delegiert das Rückwärts-Slicing inklusive Grenzen- und Überlappungs-`STATE-GUARD`s an `service_core.markdown.apply_span_replacements(content, replacements)`.
* **Zeilenumbruch-Invariante & Idempotenz (`_render_single_span`):**
  `_render_single_span` setzt vor den Zonen-Inhalt `lead_nl = "\n\n" if span.zone == "foot" else "\n"`, schließt mit `\n{span.close_tag}` ab und erhält einen etwaigen Zeilenumbruch hinter dem schließenden Tag (`trail_nl`). Da `parse_frame_spans` beim nächsten Lauf exakt diesen `inner_content` wieder ausliest und `inner_content.strip()` identisch gerendert wird, ist `DocFrame.update()` streng **idempotent**: Ein zweiter Lauf über ein bereits synchronisiertes Repository erzeugt `updated_files == ()` und führt keinen einzigen Schreibzugriff aus.

Das folgende Beispiel zeigt in drei zusammengehörigen Schritten (`session=docframe_presets`), wie sich die Router-Bausteine, der gemeinsame Footer und die drei Presets in Python zusammensetzen und abfragen lassen:

```python session=docframe_presets
from qb_cubie.core.services.doc_frame import (
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

Im zweiten Schritt bündeln wir die Router im gemeinsamen `<div align="center">`-Fuß (`STD_FOOTER_BLOCKS`) und konfigurieren den `CatalogRouter` (`AUTO_INDEX_ROUTER`):

```python session=docframe_presets
from qb_cubie.core.services.doc_frame import AssetImage, CenterWrap, Divider

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

Im dritten Schritt fügen wir Kopf-, Router- und Fuß-Blöcke (inklusive `EPISTEMIC_NOTICE`) zu den drei `FramePattern`-Presets zusammen:

```python session=docframe_presets
from qb_cubie.core.services.doc_frame import (
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

---

## 5. Diagnose-Regeln (`CUBIE_DOCFRAME_RULES`) & `WorkspaceCheckRuleProtocol`-Integration (`doc_frame_rules.py`)

Damit veraltete oder unvollständige Rahmen im CI-Lauf zuverlässig und vollständig entkoppelt von `DocEnsurance` auffallen, stellt `doc_frame_rules.py` vier I/O-freie Dokument-Prüfregeln bereit (`CUBIE_DOCFRAME_RULES: Final[tuple[WorkspaceCheckRuleProtocol, ...]]`).

### 5.1 Die vier Rahmen-Prüfregeln, `FileContextCache` & kaskadenfreie Abschirmung

Jede Regel in `CUBIE_DOCFRAME_RULES` erbt von `_DocFrameRuleBase`, implementiert das domänenneutrale **`WorkspaceCheckRuleProtocol`** (`context_key = "doc_frame"`, `depends_on`, `prepare_workspace`, `check_file(source, workspace_ctx, file_cache)`) ohne Dummy-`check()`-Methoden und emittiert ausschließlich Core-`Diagnostic`-Records aus `qb_cubie.core.protocols` (null Cross-Imports zu `doc_ensurance`, null direkte Filesystem-Aufrufe):
* **Einmaliges Parsing pro Datei (`FileContextCache`):** `_DocFrameRuleBase.check_file` speichert `_parse_and_validate_spans(source.path, source.content, patterns)` unter `"doc_frame:parsed_spans"` im per-Datei-`FileContextCache`. Alle vier Regeln teilen sich somit genau **einen** `parse_frame_spans`-Aufruf je Datei (inkl. `_validate_known_patterns`-`STATE-GUARD`).
* **Span-Level-Caching:** `_cached_incomplete_provenance` und `_cached_broken_route` cachen Span-Befunde ebenfalls im `FileContextCache`, damit `DocFrameOutdated` bereits geprüfte Spans ohne Doppelarbeit wiederverwendet.

1. **`DocFrameMissing` (`DOCFRAME-MISSING`, Default: `"error"`, Alias: `DocFrameMissingRule`):**
   Prüft über `_has_missing_zones(spans, unclosed, patterns)` drei strukturelle Grundbedingungen:
   * Enthält `unclosed` Einträge (ungeschlossener `<!-- qb:frame ... -->`-Tag), feuert `DOCFRAME-MISSING` exakt auf der Startzeile `unclosed[0]`.
   * Fehlt in den geschlossenen Spans `"head"` oder `"foot"` (was auch auf komplett leere 0-Byte-Dateien zutrifft), feuert `DOCFRAME-MISSING` auf Zeile `1`.
   * Referenziert ein Span ein `FramePattern` mit nicht-leerer `pat.router`-Sequenz (wie `CUBIE_DOC_FRAME_3`), ohne dass im Dokument ein Span mit `zone="router"` existiert, feuert `DOCFRAME-MISSING` auf `span.start_line`.

2. **`DocFrameProvenanceIncomplete` (`DOCFRAME-PROVENANCE-INCOMPLETE`, Default: `"error"`, Alias: `DocFrameProvenanceRule`):**
   Überspringt Dateien mit ungeschlossenen Tags (`if unclosed: return []`). Prüft über `_cached_incomplete_provenance(span, pattern, file_cache)` jeden `zone="head"`-Span, dessen `FramePattern` einen `ProvenanceBlock` enthält: Bleibt nach dem Zusammenführen der bestehenden `- **Key:** Value`-Zeilen und der Marker-Attribute (`env`, `model`, `effort`) mindestens ein Schlüssel aus `prov.required_keys` leer, emittiert die Regel `DOCFRAME-PROVENANCE-INCOMPLETE` auf `span.start_line`.

3. **`DocFrameBrokenRoute` (`DOCFRAME-BROKEN-ROUTE`, Default: `"error"`, Alias: `DocFrameBrokenRouteRule`):**
   Überspringt Dateien mit ungeschlossenen Tags und prüft für jeden Span I/O-frei über `_cached_broken_route(path_obj, span, catalog, file_cache)` gegen `catalog.workspace.has_path(...)` zwei Arten von Ziel-Referenzen:
   * Besitzt der Span ein `banner="..."`-Attribut, muss `resolve_banner_rel_path(banner, catalog.root, catalog.workspace)` im `WorkspaceView` vorhanden sein.
   * Für jeden im `span.inner_content` gefundenen Markdown-Link oder Bild-Verweis (`_LINK_TARGET_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")`) werden Anker (`#...`) und Query-Parameter (`?...`) abgetrennt; externe URLs (`http://`, `https://`, `mailto:`) werden übersprungen. Fehlt `(file_path.resolve().parent / clean).resolve()` im `WorkspaceView`, meldet die Regel `DOCFRAME-BROKEN-ROUTE` auf `span.start_line`.

4. **`DocFrameOutdated` (`DOCFRAME-OUTDATED`, Default: `"error"`, Alias: `DocFrameOutdatedRule`):**
   Deklariert `depends_on = ("DOCFRAME-MISSING",)` und berechnet im Dry-Run über `pat.render_zone(span.zone, ctx)` den Soll-Zustand jeder Zone (`span.inner_content.strip() != expected.strip()`).
   * **Kaskadenfreie Abschirmung:** Auf Dateiebene überspringt `FileCheckRunner` `DocFrameOutdated` automatisch bei `DOCFRAME-MISSING`-Fehlern (zusätzlich abgesichert durch `_has_missing_zones` bei isoliertem Aufruf); auf Span-Ebene überspringt `_check_spans_sync` jeden Span mit gecachtem Provenance- oder Broken-Route-Befund.

### 5.2 Native Ausführung über `DocFrame.check()` (`FileCheckRunner`) & Kompatibilitätsbrücke

* **Primärer Ausführungspfad (`DocFrame.check()`):** `DocFrame.check()` baut über `adapters.build_workspace_catalog` einmalig den `DocumentCatalog` (inkl. `FileSystemWorkspaceView`) auf und übergibt `rules`, `options={"catalog": catalog, "patterns": patterns, ...}` und `reporter` direkt an `qb_cubie.core.service_core.FileCheckRunner`. Weder `DocEnsurance` noch `_MarkdownScanner` oder `TempFS` werden dabei geladen oder ausgeführt.
* **Kompatibilitätsbrücke in `DocEnsurance`:** Da `DocEnsurance._run_file_rules()` intern `service_core.rules.execute_file_checks()` nutzt, können `WorkspaceCheckRuleProtocol`- und Legacy-`FileCheckProtocol`-Regeln bei Bedarf weiterhin auch über `DocEnsurance` ausgeführt werden — ohne dass `DocEnsurance` irgendwelche `DocFrame`-Typen kennt.

---

## 6. Entwickler-Rezepte: Eigene Erweiterungen bauen (DI-Guide)

Dank der strikten Protokoll-Trennung (`FrameBlockProtocol`, `FramePattern`, `WorkspaceView`, `WorkspaceCheckRuleProtocol`) lassen sich eigene Rahmen-Bausteine, Router-Konfigurationen und Dokument-Prüfregeln ohne Änderung am `doc_frame`-Kern implementieren und per Dependency Injection übergeben.

### 6.1 Eigenen Rahmen-Baustein (`FrameBlockProtocol`) implementieren

Um einen neuen dynamischen Baustein (z. B. eine Breadcrumb-Zeile, die den Katalog-Pfad und die Rahmen-ID des aktuellen Dokuments ausgibt) zu ergänzen, genügt eine `@dataclass(frozen=True)` mit einer `render(self, ctx: FrameRenderContext) -> str`-Methode:

```python
from dataclasses import dataclass
from pathlib import Path
from qb_cubie.core.services.doc_frame import (
    DocumentCatalog, FramePattern, FrameRenderContext, FrameSpan, extract_doc_meta,
)


@dataclass(frozen=True)
class BreadcrumbBar:
    prefix: str = "Pfad:"

    def render(self, ctx: FrameRenderContext) -> str:
        meta = ctx.catalog.by_path(ctx.rel_path)
        return f"{self.prefix} `{meta.category}` / **{meta.label}** (`{ctx.span.frame_id}`)"


raw = '<!-- qb:frame id="CUSTOM_1" zone="head" -->\n# Mein Guide\n<!-- /qb:frame -->\n'
cat = DocumentCatalog(root=Path("/repo"), entries=(extract_doc_meta("docs/dev/guide.md", raw),))
span = FrameSpan("CUSTOM_1", "head", {}, "<!-- qb:frame -->", "# Mein Guide\n", "<!-- /qb:frame -->", 1, 3, 0, len(raw))
ctx = FrameRenderContext(Path("/repo/docs/dev/guide.md"), "docs/dev/guide.md", cat, span)
pattern = FramePattern(id="CUSTOM_1", head=(BreadcrumbBar(),))
print(pattern.render_zone("head", ctx))
```

<details>
<summary>Ergebnis</summary>

```text
Pfad: `docs/dev` / **Mein Guide** (`CUSTOM_1`)
```
</details>

### 6.2 `DocumentCatalog` und `CatalogRouter` programmatisch im Speicher auswerten

Möchte man in Tests oder Analyse-Skripten prüfen, welche Index-Tabelle `CatalogRouter` für eine gegebene Dokumentmenge erzeugt, lässt sich `DocumentCatalog` direkt aus `(rel_path, content)`-Einträgen bestücken und ohne Dateisystem-Schreibzugriff rendern:

```python
from pathlib import Path
from qb_cubie.core.services.doc_frame import (
    CatalogRouter, DocumentCatalog, FrameRenderContext, extract_doc_meta, parse_frame_spans, sort_doc_metas,
)

readme_md = '<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." -->\n<!-- /qb:frame -->'
essay_b = '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" order="20" -->\n# Essay B\n\nZweiter Text.\n\n---\n<!-- /qb:frame -->'
essay_a = '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" order="10" -->\n# Essay A\n\nErster Text.\n\n---\n<!-- /qb:frame -->'

entries = sort_doc_metas([
    extract_doc_meta("docs/misc/README.md", readme_md),
    extract_doc_meta("docs/misc/B.md", essay_b),
    extract_doc_meta("docs/misc/A.md", essay_a),
])
catalog = DocumentCatalog(root=Path("/repo"), entries=tuple(entries))
router_span = parse_frame_spans(readme_md)[0][0]
ctx = FrameRenderContext(Path("/repo/docs/misc/README.md"), "docs/misc/README.md", catalog, router_span)
print(CatalogRouter().render(ctx))
```

<details>
<summary>Ergebnis</summary>

```text
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Essay A](./A.md) | Erster Text. |
| [Essay B](./B.md) | Zweiter Text. |
```
</details>

### 6.3 Eigene Datei-Prüfregel (`WorkspaceCheckRuleProtocol`) mit `FileContextCache` & State-Guard implementieren

Soll `DocFrame.check()` neben `CUBIE_DOCFRAME_RULES` eine projektspezifische Rahmen-Konvention durchsetzen (z. B. dass jeder `CUBIE_DOC_FRAME_1`-Header zwingend ein explizites `banner="..."`-Attribut im Kommentar-Tag deklarieren muss), implementiert man das domänenneutrale **`WorkspaceCheckRuleProtocol`** aus `qb_cubie.core.service_core` und emittiert Core-`Diagnostic`-Records:

```python
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from qb_cubie.core.protocols import Diagnostic, validate_severity
from qb_cubie.core.service_core import FileContextCache, FileSource, RuleRegistry, WorkspaceCheckRuleProtocol
from qb_cubie.core.services.doc_frame import CUBIE_DOCFRAME_RULES, parse_frame_spans

@dataclass(frozen=True)
class RequireExplicitBannerRule:
    rule_id: str = "DOCFRAME-EXPLICIT-BANNER"
    severity: str = "warning"
    context_key: str = "explicit-banner"
    depends_on: tuple[str, ...] = ("DOCFRAME-MISSING",)

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def prepare_workspace(self, sources: Sequence[FileSource], options: Mapping[str, Any]) -> None:
        return None

    def check_file(self, source: FileSource, workspace_ctx: Any, file_cache: FileContextCache) -> list[Diagnostic]:
        spans, _ = file_cache.get_or_compute("banner:spans", lambda: parse_frame_spans(source.content))
        return [
            Diagnostic(source.path, self.rule_id, s.start_line, "Missing explicit banner attribute.", self.severity)
            for s in spans if s.zone == "head" and s.frame_id == "CUBIE_DOC_FRAME_1" and not s.attrs.get("banner")
        ]

reg = RuleRegistry((CUBIE_DOCFRAME_RULES, RequireExplicitBannerRule))
print(f"WorkspaceRule={isinstance(RequireExplicitBannerRule(), WorkspaceCheckRuleProtocol)} | {[r.rule_id for r in reg.rules]}")
```

<details>
<summary>Ergebnis</summary>

```text
WorkspaceRule=True | ['DOCFRAME-MISSING', 'DOCFRAME-OUTDATED', 'DOCFRAME-BROKEN-ROUTE', 'DOCFRAME-PROVENANCE-INCOMPLETE', 'DOCFRAME-EXPLICIT-BANNER']
```
</details>

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../GUIDE_TGD.md)  

[↦ | Service-Core | ↤](../../services/GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../../README.md)  
[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../README.md)  
[↦ | Core-Internals | ↤](../core/README.md)  
[↦ | Hintergrund & Essays | ↤](../../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  

[↦ | `DocEnsurance` | ↤](./DEV-GUIDE_DocEnsurance.md)  
[↦ | `DocFrame` (Prototyp) | ↤](./DEV-GUIDE_DocFrame.md)  

</div>
<!-- /qb:frame -->
