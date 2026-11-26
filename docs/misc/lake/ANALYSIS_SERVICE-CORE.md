<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Neon" effort="High" -->
# Analyse: Service-Core-Vermessung (`DocEnsurance` & `DocFrame`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** High
- **Analysedatum:** 25. November 2026, ~13:45 (CET)
- **Synthesebasis:** `GEMINI-1.md`, `docs/services/GUIDE_DocEnsurance.md`, `docs/services/GUIDE_DocFrame.md`, `docs/dev/DEV-GUIDE_Services.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md`, `docs/dev/DEV-GUIDE_DocFrame-Conventions.md`, `src/qb_cubie/core/services/__init__.py`, `src/qb_cubie/core/services/docframe.py`, `src/qb_cubie/core/services/doc_ensurance/*.py` (7 Module), `src/qb_cubie/core/services/doc_frame/*.py` (8 Module), `src/qb_cubie/core/protocols.py`, `src/qb_cubie/core/reporter.py`, `src/qb_cubie/core/linter.py`, `src/qb_cubie/cli.py`, `tests/test_doc_ensurance.py`, `tests/test_doc_frame.py`, `tests/tests_core/tests_services/test_service_architecture_gate.py`
- **Stand:** qb-cubie (`v0.1.1`, Branch `main`, Commit `ab65797a`)
- **Git-Log:** `ab65797a` ("Neues GPT-Gutachten")

---

```text
commit ab65797af3bdaa26e04e473574a0d8cb2807c7ed (HEAD -> main, origin/main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Wed Nov 25 11:50:59 2026 +0100

    Neues GPT-Gutachten

Auftrag (docs/services/GEMINI.md):
- Vermessung und Analyse der sich überschneidenden Muster, Grammatiken/Syntaxen und
  gemeinsamen Features von DocEnsurance und DocFrame zur Vorbereitung eines Service-Cores.
- Scope: Rein lesende Code- und Dokumentationsanalyse (kein Produktivcode unter src/ geändert;
  ausschließlich Erstellung und Rahmen-Synchronisation von docs/services/ANALYSIS.md).
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

**Scope:** Rein lesende Bestandsaufnahme von `DocEnsurance` (7 Module, 1.529 LOC) und `DocFrame` (8 Module + Alias, 1.653 LOC) inklusive ihrer Kern-Schnittstellen (`core/protocols.py`, `core/reporter.py`, `core/linter.py`, `cli.py`) und Architektur-Gates (`test_service_architecture_gate.py`). Produktivcode unter `src/` wurde nicht verändert.

**Kernbefunde (Ist):**

1. **`[BLOCKER]` Fehlende generische Service-Execution-Schicht erzwingt Huckepack-Kopplung:** `DocFrame` besitzt keinen eigenen Prüf-Runner und keinen `Reporter`, sodass `tests/test_doc_frame.py` `DocEnsurance` als fremden Host-Runner zweckentfremden muss. Dafür implementieren `FramePattern` (`presets.py:47-57`) und alle 4 `DocFrame`-Regeln (`doc_frame_rules.py:137-252`) leere Dummy-Methoden (`scan`, `check`), und `DocEnsurance` parst bei reinen Frame-Läufen dennoch jede Datei vollständig mit `_MarkdownScanner` und erzeugt eine ungenutzte `TempFS`-Arena.
2. **`[BLOCKER]` Hartcodierte CLI- und Fassaden-Verdrahtung skaliert nicht für weitere Services:** `src/qb_cubie/cli.py:11` importiert `doc_frame` starr am Modul-Kopf (während `DocEnsurance` gar kein CLI besitzt), und `src/qb_cubie/core/services/__init__.py` (213 LOC, 90 flache Re-Exports) erfordert für jeden neuen Service manuelle Dreifach-Pflege (`TYPE_CHECKING`, `_<SVC>_EXPORTS`, `_EXPORT_TO_SUBMODULE`).
3. **`[RISIKO]` Substantielle 1:1-Code-Duplikate mit bereits einsetzendem Verhalten-Drift:** Projekt-Root-Suche, Directory-Crawling, Exclude-Matching (~95 LOC), Code-Fence-State-Machines (3× unabhängig), Enum-/Bool-`STATE-GUARD`s (6× nach identischem Muster) und HTML-Wrapper-Regexes (2× identisch) sind über beide Services dupliziert — mit nachweisbaren Abweichungen (z. B. fehlender `TypeError`-Guard für `excludes="tests"` in `DocEnsurance`, inkonsistente Exclude-Semantik in `CstLinter`, nicht-atomares `write_text` in `DocFrame` trotz „atomar“-Dokumentation).
4. **`[ABWEICHUNG]` Zwei inkompatible Inline-Attribut-Grammatiken & blinde Flecken zwischen Markdown-Scannern:** `DocEnsurance` nutzt ungequotete Whitelist-Tags (`session=x`, `raises=Y`), `DocFrame` zwingend gequotete Direktiven (`<!-- qb:frame k="v" -->`). `_MarkdownScanner` schluckt HTML-Kommentare spurlos und klassifiziert `---` als `paragraph`, während `doc_frame_rules.py` jede Datei 4× redundant parst.
5. **`[HINWEIS]` Saubere Platzierung des künftigen Service-Cores:** Wegen Meta-Gate 4 (`META-SERVICE-ISOLATION` in `test_service_architecture_gate.py`) darf der Service-Core **nicht** als Geschwister-Service unter `core/services/<name>` liegen, sondern muss im `qb_cubie`-Core (z. B. `src/qb_cubie/core/service_core/`) verankert werden, damit die Einbahnstraße `services.* -> core.*` erhalten bleibt.

---

## 1. Quantitative Bestandsaufnahme (Ist-Vermessung)

Die direkte AST- und Zeilenvermessung aller Module unter `src/qb_cubie/core/services/` zeigt zwei nahezu gleich große, strukturell gespiegelte Pakete mit insgesamt **3.393 LOC**:

| Bereich / Modul | LOC | Klassen (`dc` / `Proto`) | `def`s | `re.compile` | `STATE-GUARD`s | Rolle im Service |
| :--- | ---: | :---: | ---: | ---: | ---: | :--- |
| **`doc_ensurance/__init__.py`** | 89 | 0 (0 / 0) | 0 | 0 | 0 | Öffentliche Fassade (40 `__all__`-Exporte) |
| **`doc_ensurance/protocols.py`** | 122 | 10 (6 / 4) | 12 | 0 | 0 | 6 DTOs + 4 Protocols (`DocRule/Block/Pattern/Scope`) |
| **`doc_ensurance/_source_loader.py`** | 71 | 0 (0 / 0) | 5 | 0 | 4 | Target-Auflösung (File, Dir, In-Memory) & Excludes |
| **`doc_ensurance/_markdown_scanner.py`** | 213 | 1 (0 / 0) | 21 | 3 | 0 | Line-basierter Markdown-Block-Scanner (`MdBlock`) |
| **`doc_ensurance/doc_patterns.py`** | 386 | 11 (10 / 0) | 32 | 1 | 0 | 6 Basis-Regeln, 3 Blöcke, `ExamplePattern`, `TaggedScope` |
| **`doc_ensurance/doc_rules.py`** | 180 | 4 (4 / 0) | 13 | 0 | 1 | 4 didaktische Standardregeln (`CUBIE_DOC_RULES`) |
| **`doc_ensurance/doc_ensurance.py`** | 468 | 1 (0 / 0) | 38 | 0 | 5 | Orchestrator, Rule-Registry, Arena-Worker, Reporting |
| **Summe `doc_ensurance` (7 Dateien)** | **1.529** | **27 (20 / 4)** | **121** | **4** | **10** | — |
| **`doc_frame/__init__.py`** | 132 | 0 (0 / 0) | 0 | 0 | 0 | Öffentliche Fassade (63 `__all__`-Exporte) |
| **`doc_frame/__main__.py`** | 8 | 0 (0 / 0) | 0 | 0 | 0 | CLI-Delegation an `qb_cubie.cli.main` |
| **`doc_frame/protocols.py`** | 168 | 6 (5 / 1) | 10 | 0 | 4 | 5 DTOs + `FrameBlockProtocol` + 3 Enum-Guards + Sort |
| **`doc_frame/_catalog_scanner.py`** | 178 | 1 (0 / 0) | 16 | 4 | 3 | Fence-sicherer Span-Scanner + Pass-1-Meta-Extraktor |
| **`doc_frame/frame_blocks.py`** | 444 | 14 (14 / 0) | 34 | 3 | 5 | 14 Bausteine (Static, 3 Router, 5 geschützte Slots) |
| **`doc_frame/presets.py`** | 179 | 1 (1 / 0) | 5 | 0 | 3 | `FramePattern`, `EPISTEMIC_NOTICE_TEXT`, `FRAME_1..3` |
| **`doc_frame/doc_frame_rules.py`** | 300 | 5 (4 / 0) | 22 | 1 | 1 | `_DocFrameRuleBase` + 4 `FileCheckProtocol`-Regeln |
| **`doc_frame/doc_frame.py`** | 233 | 1 (0 / 0) | 16 | 0 | 10 | 2-Pass-Orchestrator + eigenes Source-Loading/Crawling |
| **Summe `doc_frame` (8 Dateien)** | **1.642** | **28 (24 / 1)** | **103** | **8** | **26** | *(zzgl. `docframe.py` Alias: 11 LOC)* |
| **`services/__init__.py` + `docframe.py`** | **224** | — | 1 | 0 | 0 | PEP-562-Lazy-Fassade (90 `__all__`-Exporte) + Alias |
| **Bereits im Core (`core/protocols.py:260-337`)** | **78** | 4 (1 / 3) | 5 | 0 | 1 | `Diagnostic`, `DiagnosticProtocol`, `ServiceReportProtocol`, `FileCheckProtocol`, `validate_severity` |

**Beobachtung (Ist):** Beide Services schöpfen das 500-LOC-Modulbudget aus `DEV-GUIDE_Services.md` bereits nahezu aus (`doc_ensurance.py`: 468 LOC, `frame_blocks.py`: 444 LOC). Fast alle Domänen-Bausteine sind konsistent als `@dataclass(frozen=True)` modelliert (44 von 55 Klassen = 80 %).

---

## 2. Topologische Projektion & Architektur-Muster

### 2.1 Die 5-Schichten-Isomorphie beider Services (Ist)

Die historische Projektion von `DocEnsurance` auf `DocFrame` erzeugt fünf unmittelbar korrespondierende Strukturebenen:

| Schicht | `DocEnsurance` | `DocFrame` | Gemeinsamer Muster-Kern |
| :--- | :--- | :--- | :--- |
| **0. Workspace & Source-Auflösung** | `_source_loader.py` + `DocEnsurance._default_project_dir` | `DocFrame._resolve_target_path` … `_load_path_sources` | Projekt-Root ab `pyproject.toml`, `DEFAULT_EXCLUDES`-Merge, rekursives `*.md`-Crawling, Pfad-`STATE-GUARD`s |
| **1. Dokument-Frontend (Scanner)** | `_MarkdownScanner` (Line-FSM $\to$ `list[MdBlock]`) | `_FrameSpanScanner` (Line-FSM $\to$ `list[FrameSpan]`) | Zeilenbasierte State-Machine mit Backtick-/Tilde-Fence-Tracking und Zeilennummern |
| **2. Atomare Bausteine (Level 1)** | `DocBlockProtocol`: `Explanation`, `CodeSnippet`, `CollapsibleResult` | `FrameBlockProtocol`: 14 Bausteine (Static, Router, Content-Slots) | Unveränderliche (`frozen=True`) Protokoll-Implementierungen mit `__post_init__`-Validierung |
| **3. Kompositions-Pattern & Presets (Level 2)** | `ExamplePattern(anchor, pre, post)` + `CUBIE_DOC_STYLE` | `FramePattern(id, head, router, foot)` + `CUBIE_DOC_FRAME_1..3` | Deklarative Komposition von Level-1-Bausteinen in benannte Slots/Zonen + `Final`-Presets |
| **4. Pluggable Rules & Regel-Sets** | `DocRuleProtocol` (10 Klassen) + `DEFAULT_DOC_RULES`, `CUBIE_DOC_RULES` | `FileCheckProtocol` (4 Klassen via `_DocFrameRuleBase`) + `CUBIE_DOCFRAME_RULES` | `rule_id` + `severity` (`"error"` / `"warning"`), `validate_severity`, Doppel-Namenskonvention (`Foo` + Alias `FooRule`) |
| **5. Service-Orchestrator, Report & Ausführung** | `DocEnsurance.run()` $\to$ `DocReport` $\to$ `PytestReporter` | `DocFrame.run()` / `.update()` / `.scan_catalog()` $\to$ `DocFrameReport` | Service-Instanz mit `run() -> ServiceReportProtocol`; bei `DocFrame` zusätzlich Convenience-Classmethods & CLI |

### 2.2 Abweichung vom Ziel-Layout in `DEV-GUIDE_Services.md` (`[ABWEICHUNG]`)

`DEV-GUIDE_Services.md` (§2) definiert das kanonische Modul-Layout `models.py -> protocols.py -> engine.py / rules.py -> adapters.py / cli.py -> __init__.py`, und Meta-Gate 4 (`test_service_architecture_gate.py:26, 434-438`) erzwingt I/O-Freiheit auf genau diesen Dateinamen (`PURE_DOMAIN_FILENAMES` + `*_rules.py`).

**Ist-Befund:**
- Keiner der beiden Services nutzt bislang `models.py`, `engine.py`, `adapters.py` oder ein eigenes `cli.py`. DTOs und Protocols liegen gemeinsam in `protocols.py`.
- In `doc_frame` entgehen `_catalog_scanner.py`, `frame_blocks.py` und `presets.py` dem `PureDomainIoRule`-Gate. Tatsächlich enthält `frame_blocks.py` direkte Filesystem-Abfragen (`(root / ".assets" / clean).exists()` L45, `(catalog.root / norm).exists()` L237, `(ctx.catalog.root / raw).exists()` L275), und `doc_frame_rules.py` prüft Dateipfade auf Platte (`.exists()` L66, L72) sowie ruft `DocFrame(...).build_catalog()` (L84) aus dem angeblich reinen `*_rules.py`-Modul auf — das Gate schlägt nur deshalb nicht an, weil `PureDomainIoRule` lediglich `open`/`print`/`read_text`/`write_text`/`subprocess`/`sys.argv` prüft, nicht `.exists()` oder Adapter-Instanziierung.
- **Konsequenz (Hypothese):** Ohne klare Schnittstelle zwischen reinem Kern und Workspace-Port (z. B. `WorkspaceView` / `FileIndex` im Service-Core) werden auch künftige Services `Path.exists()`-Aufrufe in vermeintlich reine Regel- und Blockmodule einschleppen.

---

## 3. Vermessung der Grammatiken und Syntaxen

Beide Services erweitern reguläres Markdown um deklarative Mikro-Grammatiken. Ein direkter Vergleich deckt gemeinsame lexikalische Grundelemente, aber auch **inkompatible Syntaxkonventionen** auf:

### 3.1 Lexikalische & strukturelle Vergleichsmatrix (Ist)

| Grammatik-Element | `DocEnsurance` (`_markdown_scanner.py`, `doc_patterns.py`) | `DocFrame` (`_catalog_scanner.py`, `frame_blocks.py`, `doc_frame_rules.py`) | Überlappung / Konflikt |
| :--- | :--- | :--- | :--- |
| **Code-Fences** | ```` ``` ```` und `~~~` beliebiger Länge $\ge 3$; Ende wenn gleiche Char-Art, Länge $\ge$ Startlänge, sonst leer (`_markdown_scanner.py:38-41, 128-134, 148-150`, `doc_patterns.py:269-275`) | Identische Regel (`_catalog_scanner.py:146-155`) | **100 % identische Grammatik**, 3× getrennt implementiert |
| **HTML-Kommentare / Direktiven** | `_consume_html_comment` (`_markdown_scanner.py:55-61`): ein-/mehrzeilige `<!-- ... -->` werden komplett verworfen | `_OPEN_TAG_RE`: `^<!--\s*qb:frame\b([^>]*)-->$` und `_CLOSE_TAG_RE`: `^<!--\s*/qb:frame\s*-->$` (`_catalog_scanner.py:10-11`), zwingend einzeilig | **Asymmetrische Blindheit:** `_MarkdownScanner` kennt keine `qb:*`-Direktiven; `_FrameSpanScanner` unterstützt keine mehrzeiligen Öffnungs-Tags |
| **Key-Value-Attribute** | `_TAG_RE`: `\b(?P<key>session\|raises)=(?P<val>[^\s,]+)` (`doc_patterns.py:20`) — **ungequotet**, geschlossene 2-Key-Whitelist, kein Whitespace um `=` | `_ATTR_RE`: `([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*(?:"([^"]*)"\|'([^']*)')` (`_catalog_scanner.py:12`) — **zwingend gequotet**, offene Key-Menge, Whitespace um `=` erlaubt | **`[ABWEICHUNG]` Zwei inkompatible Attribut-Dialekte:** `session="a b"` zerbricht in `DocEnsurance`, `order=10` wird in `DocFrame` stumm verworfen |
| **HTML-Container** | `<details>...<summary>...</summary>...</details>` mit innerem Fence-Tracking (`_markdown_scanner.py:136-213`) | `<div align="center">...</div>` und `<center>...</center>` (`_HTML_WRAP_RE` in `_catalog_scanner.py:13` **und** `frame_blocks.py:21`) | Duplizierte Regex `_HTML_WRAP_RE`; unterschiedliche Strategien für verschachtelte HTML-Wrapper |
| **Trenner & Blöcke** | `#` (`heading`), `[-*+]\s \| \d+[.)]\s \| >+ \| \|.*\|` (`list`), `> [!NOTE\|...]` (`paragraph`), sonst `paragraph`. **Achtung:** `---` hat kein Leerzeichen nach `-`, wird also als `paragraph` gewertet! | `---` dient als harter Zonen-Segment-Delimiter (`_slice_before_divider`, `_split_by_dividers`); `# ` (H1), `![...](...)` (Banner), `!?\[...\]\((...)\)` (Links), `- **Key:** Value` (Provenance) | **`[ABWEICHUNG]` `---`-Konflikt:** In `DocFrame` struktureller Trenner, in `DocEnsurance` fälschlicherweise `paragraph` (könnte als `Explanation` matchen, wenn Länge $\ge$ `min_chars`) |
| **Dokument-Repräsentation (IR)** | Flacher Block-Stream `list[MdBlock(kind, content, line, meta)]` — **nur Zeilennummern**, keine Char-Offsets, verlustbehaftet (Leerzeilen/Kommentare fehlen) | Offset-Spans `list[FrameSpan(..., start_line, end_line, start_idx, end_idx)]` — **verlustfreies In-Place-Rewriting** durch Rückwärts-Slicing (`doc_frame.py:114-116`), aber keine Kenntnis des restlichen Dokuments | Komplementäre IRs: Read-Only-Struktur-Stream vs. Offset-treue Schreib-Spans |
| **Inline-Typ-Konvertierungen** | String-Werte direkt (`session_id`, `expected_raises`) | `int` (`order`: `_parse_optional_order`), `bool` (`routable`: `_parse_routable`; `recursive`: `_resolve_recursive`), `Enum` (`zone`, `mode`, `tag`) | Zwei getrennte Kopien des exakt gleichen Bool-Parsers (`true/1/yes` vs. `false/0/no`) |

### 3.2 Bewertung des `<!-- qb:<directive> ... -->`-Musters (Hypothese & Soll)

`DocFrame` hat mit `<!-- qb:frame id="..." zone="..." --> ... <!-- /qb:frame -->` bereits eine saubere, Markdown-konforme **Direktiven-Grammatik** etabliert, die von Standard-Renderern (GitHub, PyPI, IDEs) unsichtbar toleriert wird. Für künftige Dokument- oder Nachweis-Services (z. B. `qb:toc`, `qb:include`, `qb:coverage`, `qb:contract`) lässt sich dieses Muster direkt zu einer generischen `qb:<namespace>`-Direktiven-Schicht im Markdown-Core verallgemeinern, während Fence-Attribute (`key=value` / `key="value"`) über denselben vereinheitlichten Attribut-Parser unterstützt werden können.

---

## 4. Vermessung konkreter Code-Duplikate, Asymmetrien & Bruchstellen

### 4.1 Nachgewiesene 1:1-Duplikate (Ist)

| Nr. | Duplizierte Logik | Vorkommen A | Vorkommen B (und ggf. C) | Befund / Drift |
| :-: | :--- | :--- | :--- | :--- |
| **D1** | Projekt-Root-Auflösung (`pyproject.toml` aufwärts) | `doc_ensurance.py:273-279` (`_default_project_dir`) | `doc_frame.py:183-189` (`_default_project_dir`) + `doc_frame.py:192-201` (`_resolve_catalog_root`) | 100 % identischer 7-Zeilen-Code; `_resolve_catalog_root` ergänzt lediglich `docs/.assets`-Marker und `cwd`-Stopp |
| **D2** | Rekursives `.md`-Crawling & Exclude-Matching | `_source_loader.py:39-71` (`crawl_directory`, `is_excluded`, `load_path_sources`) | `doc_frame.py:204-233` (`_crawl_directory`, `_is_excluded`, `_load_path_sources`); 3. Variante: `core/linter.py:242-248` (`CstLinter._crawl_directory`) | **`[RISIKO]`** Services kopieren ~60 LOC 1:1; `CstLinter` nutzt eine schwächere 3. Variante ohne Teilpfad-Excludes (`"docs/drafts"` funktioniert dort nicht) |
| **D3** | Backtick-/Tilde-Fence-Tracking | `_markdown_scanner.py:128-134, 148-150, 152-165, 196-202` | `doc_patterns.py:269-275` (`CollapsibleResult._is_wrapped_fence`) & `_catalog_scanner.py:146-155` (`_FrameSpanScanner._update_fence`) | 3 unabhängige Implementierungen derselben CommonMark-Fence-Regel |
| **D4** | Enum-`STATE-GUARD`-Validierung | `core/protocols.py:265-271` (`validate_severity`) | `doc_frame/protocols.py:18-42` (`validate_zone`, `validate_wrap_tag`, `validate_catalog_mode`) | 4× identischer 6-Zeilen-Validator (nur Tuple-Konstante & Feldname variieren) |
| **D5** | Bool-Attribut-Parsing (`true/1/yes` vs. `false/0/no`) | `_catalog_scanner.py:97-106` (`_parse_routable`) | `frame_blocks.py:279-288` (`CatalogRouter._resolve_recursive`) | 2× identischer 10-Zeilen-Parser innerhalb desselben Services |
| **D6** | HTML-Wrapper-Regex | `_catalog_scanner.py:13` (`_HTML_WRAP_RE`) | `frame_blocks.py:21` (`_HTML_WRAP_RE`) | Zeichenidentisch dupliziert |
| **D7** | Rule-Klassen-Alias-Konvention | `doc_rules.py:170-173` (`NoOutputRule = NoOutput`, …) | `doc_frame_rules.py:290-293` (`DocFrameMissingRule = DocFrameMissing`, …) | Einheitliches Ergonomie-Muster, aber ohne verbindliche Core-Konvention |

### 4.2 Strukturelle Asymmetrien & versteckte Mängel (Ist)

1. **`[BLOCKER]` Huckepack-Verifikation (`DocFrame` $\leftrightarrow$ `DocEnsurance`):**
   - `tests/test_doc_frame.py:16-24` startet `DocEnsurance(pattern=(CUBIE_DOC_FRAME_1, ...), rules=CUBIE_DOCFRAME_RULES, excludes=DOC_EXCLUDES).run()`.
   - Konsequenz im Laufzeitpfad (`doc_ensurance.py:126-132, 178, 301-309`):
     - `self.pattern` wird auf `CUBIE_DOC_FRAME_1` gesetzt; `FramePattern` muss dafür Dummy-Methoden `name` und `scan() -> ([], [])` vorhalten (`presets.py:47-57`).
     - Alle 4 Regeln in `doc_frame_rules.py` schleppen Dummy-Methoden `check(example, actual_output=None) -> []` mit (L137, L171, L209, L247), obwohl `_coerce_rule` bereits `FileCheckProtocol` direkt akzeptiert (`doc_ensurance.py:244`).
     - `DocEnsurance` baut dennoch `DEFAULT_DOC_RULES` und eine `TempFS`-Arena auf und jagt jede Markdown-Datei durch `_MarkdownScanner(content).parse()`, nur um die geparsten `MdBlock`s sofort wegzuwerfen.
   - **Ursache:** Es existiert kein generischer **Verification-Runner / Rule-Engine-Host** im Core — `DocEnsurance` erfüllt heimlich *beide* Rollen (Fach-Service für Code-Snippets + generischer Multi-File-Checker).

2. **`[RISIKO]` Redundantes 4×-Parsing & ad-hoc Kaskaden-Unterdrückung in `doc_frame_rules.py`:**
   - Jede der 4 `CUBIE_DOCFRAME_RULES` ruft pro Datei erneut `parse_frame_spans(content)` und `_validate_known_patterns(...)` auf (`doc_frame_rules.py:153, 187, 224, 262`) — also 4× pro Datei.
   - `DocFrameOutdated._check_spans_sync` (`doc_frame_rules.py:280`) ruft zusätzlich `_find_incomplete_provenance` und `_find_broken_route_in_span` noch einmal auf, um Kaskadendiagnosen zu unterdrücken.
   - Ursache: `FileCheckProtocol.check_file(file_path, content, context)` (`core/protocols.py:332-337`) kennt weder einen pro Datei gecachten Parse-Kontext noch Regel-Prioritäten/Vorbedingungen.

3. **`[RISIKO]` Drift bei `excludes`- und `target`-Guards:**
   - `DocFrame._normalize_excludes` (`doc_frame.py:172-180`) weist `excludes="tests"` mit `TypeError("STATE-GUARD: ...")` ab.
   - `DocEnsurance.__init__` (`doc_ensurance.py:131`) macht `set(DEFAULT_EXCLUDES) | set(excludes or ())` ohne Typ-Guard: `excludes="tests"` wird still zu `{'t', 'e', 's'}`!
   - `DocEnsurance` unterstützt In-Memory-Targets (`looks_like_path`), `DocFrame` nicht.

4. **`[ABWEICHUNG]` Nicht-atomares Schreiben in `DocFrame` trotz „atomar“-Zusage:**
   - `doc_frame.py:84` und `GUIDE_DocFrame.md:116` dokumentieren: *„writes updated files atomically“*.
   - Tatsächlich ruft `doc_frame.py:103` direkt `file_path.write_text(new_content, encoding="utf-8", newline="\n")` auf (nicht atomar bei Prozessabbruch/I/O-Fehler). Dabei besitzt der Core in `core/reporter.py:289-301` (`JsonReporter._write`) bereits das korrekte atomare Pattern (`NamedTemporaryFile` im Zielordner + `os.replace`).

5. **`[ABWEICHUNG]` Unvollständige Reporter- und Diagnostic-Vereinheitlichung:**
   - `DocEnsurance` akzeptiert `reporter: Reporter[DocReport] | None = PytestReporter()`; `DocFrame` besitzt gar keinen `reporter`-Parameter, obwohl `DocFrameReport` (`doc_frame/protocols.py:154-161`) bereits `ServiceReportProtocol` erfüllt.
   - `DocDiagnostic` (`doc_ensurance/protocols.py:48-59`) ergänzt Core-`Diagnostic` um `session_id: str | None = None`, aber `PytestReporter._generate_service_report` (`core/reporter.py:86-94`) wertet `session_id` überhaupt nicht aus.
   - `JsonReporter` (`core/reporter.py:264-278`) lehnt `ServiceReportProtocol` mit `TypeError("JsonReporter requires a RunTrace.")` ab, weshalb `cli.py:66-73` eine parallele Ad-hoc-JSON-Serialisierung pflegt.

6. **`[BLOCKER]` Nicht-erweiterbare CLI- & Fassaden-Architektur:**
   - `src/qb_cubie/cli.py:11` importiert `DocFrame` direkt auf Top-Level. Jeder neue Service (`docensurance`, `coverage`, `styleguide`, …) müsste `cli.py` direkt verändern und `--exclude` / `--format` / Exit-Code-Handling (`0` vs. `2`) kopieren.
   - `src/qb_cubie/core/services/__init__.py` verwaltet aktuell 90 flache Re-Exports über manuelle Listen (213 LOC). Bei 3–4 weiteren Services überschreitet die Fassade das 500-LOC-Limit und riskiert Symbolkollisionen (z. B. `DEFAULT_*`, `Report`, `Rule`).

---

## 5. Architekturentwurf: Zielbild für den `qb-cubie` Service-Core (Soll)

### 5.1 Ablageort & Vereinbarkeit mit Meta-Gate 4 (`DEV-GUIDE_Services.md`)

Die Abwägung der Ablageorte unter Berücksichtigung von `DEV-GUIDE_Services.md` (§1 & §3) und `test_service_architecture_gate.py`:

| Option | Pfad | Vorteile | Nachteile / Risiken | Bewertung |
| :--- | :--- | :--- | :--- | :--- |
| **Option A (Empfohlen)** | **`src/qb_cubie/core/service_core/`** *(re-exportiert selektiv über `core/protocols.py` bzw. direkte Core-Imports)* | 100 % konform mit der Einbahnstraße `services.<name> -> core.*`; Meta-Gate 4 (`ServiceIsolationImportRule`) bleibt unverändert und ausnahmefrei scharf; klare Trennung zwischen Framework-Core (`ebt`, `rbt`, `arenas`, `linter`) und Service-Infrastruktur (`service_core`). | Fügt ein weiteres Subpaket unter `core/` hinzu. | **Bevorzugt** |
| **Option B** | `src/qb_cubie/core/services/_core/` | Optische Nähe zu den Services. | Erfordert Sonderausnahme in `ServiceIsolationImportRule` (`test_service_architecture_gate.py:64-150`) und weicht Regel 2 aus `DEV-GUIDE_Services.md` („Null Importe aus `core.services.*`“) auf. | Nicht empfohlen |

### 5.2 Strenge 3-Zonen-Schichtung nach der Core-Promotion-Regel

Gemäß `DEV-GUIDE_Services.md` §3 wandert ein Baustein nur dann in den Service-Core, wenn **Regel der Zwei** *und* **Domänenneutralität** erfüllt sind:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  Composition Root (cli.py, pytest-Suites, User-Skripte)                      │
│  • Lazy CLI-Dispatch via ServiceCommandProtocol                              │
└──────────────┬─────────────────────────┬─────────────────────────┬───────────┘
               ▼                         ▼                         ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌──────────────────────┐
│ services.doc_ensurance  │ │ services.doc_frame      │ │ services.<future>    │
│ • ExamplePattern, Arena │ │ • FramePattern, Catalog │ │ (z. B. coverage,     │
│ • TaggedScope, Linter   │ │ • 14 FrameBlocks/Router │ │  styleguide, ...)    │
│ • CUBIE_DOC_STYLE/RULES │ │ • CUBIE_DOC_FRAME_1..3  │ │                      │
└────────────┬────────────┘ └────────────┬────────────┘ └──────────┬───────────┘
             │                           │                         │
             │   (optional für Markdown-Services)                  │
             ├──────────────┐            │                         │
             ▼              ▼            ▼                         │
┌─────────────────────────────────────────────────────┐            │
│  core.service_core.markdown  (Dokument-Spezialschicht)           │
│  • FenceTracker • DirectiveSpanScanner (qb:<kind>)  │            │
│  • parse_kv_attrs • apply_span_replacements         │            │
│  • compute_rel_link                                 │            │
└───────────────────────────┬─────────────────────────┘            │
                            ▼                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  core.service_core  (Domänenneutraler Service-Core für ALLE Services)        │
│  1. guards.py     : validate_choice, validate_positive_int, parse_bool_attr  │
│  2. workspace.py  : find_project_root, normalize_excludes, crawl_files,      │
│                     load_sources, atomic_write_text, WorkspaceIndex          │
│  3. rules.py      : RuleRegistry, FileCheckRunner, FileCheckContext (Cache), │
│                     Rule-Suppression/Dependencies                            │
│  4. reporting.py  : ServiceReport, Diagnostic (+ context/metadata),          │
│                     PytestReporter & JsonReporter für ServiceReportProtocol  │
│  5. cli_spec.py   : ServiceCommandProtocol, Standard-Flags (--exclude/--fmt) │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  qb_cubie Core Kernel (protocols, reporter, linter, arenas, state)           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Konkrete Bausteine des Service-Cores & ihre Nutznießer

| Modul im Service-Core | Konkrete Primitiven (Soll) | Löst direkt welchen Befund? | Nutzen für künftige Services (z. B. `coverage`, `styleguide`) |
| :--- | :--- | :--- | :--- |
| **`service_core/guards.py`** | `validate_choice(val, valid, name)`, `validate_non_empty_str`, `validate_positive_int`, `validate_positive_float`, `parse_bool_attr`, `parse_int_attr` | Eliminiert D4, D5 und vereinheitlicht alle 36 `STATE-GUARD`s | Sofortige, konsistente Eingabe-Guards ohne Copy-Paste |
| **`service_core/workspace.py`** | `find_project_root`, `resolve_workspace_root`, `normalize_excludes`, `is_excluded`, `crawl_files(root, glob, excludes)`, `load_sources(..., allow_in_memory)`, `atomic_write_text` | Eliminiert D1, D2, behebt `excludes="str"`-Lücke in `DocEnsurance`, behebt nicht-atomares Schreiben in `DocFrame` und harmonisiert `CstLinter` | Einheitliche Datei-Discovery & sichere Schreib-Operationen für jeden File-Service (`.py`, `.md`, `.toml`) |
| **`service_core/rules.py`** | `RuleRegistry` (Flattening, Autoinstantiierung, `rule_id`-Override, Kollisions-Slots), `FileCheckRunner` (führt `FileCheckProtocol` + per-File-Parse-Cache ohne `DocEnsurance`-Huckepack aus) | Behebt Blocker 1 (`DocFrame` braucht keine Dummy-`scan`/`check`-Methoden und keinen `DocEnsurance`-Host mehr) & eliminiert 4×-Parsing in `doc_frame_rules.py` | Jeder neue Check-Service (`coverage`, `styleguide`) bekommt gratis eine getestete Rule-Engine mit Severity-Overrides |
| **`service_core/reporting.py`** | Generisches `ServiceReport` (erfüllt `ServiceReportProtocol`, inkl. optionaler `changed_files` / `metadata`), `Diagnostic` (mit optionalem `context: str | None = None`), einheitliches `reporter`-Injecting in jedem Service + `JsonReporter`-Support für `ServiceReportProtocol` | Vereinheitlicht `DocReport`, `DocFrameReport`, `PytestReporter`, `JsonReporter` und `cli.py`-JSON-Ausgabe | Einheitliche `pytest`-Integration, CI-JSON-Artefakte und konsistente Warn-/Fehler-Semantik ab Tag 1 |
| **`service_core/cli_spec.py`** | `ServiceCommandProtocol` + Lazy-Subcommand-Registry in `qb_cubie/cli.py`, gemeinsame Argument-Builder (`target`, `--exclude`, `--format text\|json`, `--check`/`--dry-run`) | Behebt Blocker 2 (`cli.py` koppelt nicht mehr hart an `doc_frame`; `qb-cubie docensurance` wird trivial ergänzbar) | Neue Services klinken sich über ein eigenes `cli.py`-Adaptermodul ein, ohne `qb_cubie/cli.py` aufzublähen |
| **`service_core/markdown.py`** *(Sub-Schicht)* | `FenceTracker`, `DirectiveSpanScanner` (`<!-- qb:<name> ... -->`), `parse_kv_attrs` (definierter Modus für Direktiven & Fence-Tags), `apply_span_replacements`, `compute_rel_link` | Eliminiert D3, D6, behebt Attribut-Dialekt-Drift und `---`-Mehrdeutigkeit | Baukasten für alle künftigen Dokumentations-Services (`doc_toc`, `doc_links`, `doc_glossary`) |

### 5.4 Was ausdrücklich NICHT in den Service-Core gehört (Schutz vor Kern-Aufblähung)

- **Kein Code-Execution-/Arena-Code** (`_execute_session_payload`, `TaggedScope`, `ExamplePattern`, `DocLinterRule`) — bleibt exklusiv in `doc_ensurance`.
- **Keine Katalog-Router, Content-Slots oder Cubie-Presets** (`DocMeta`, `DocumentCatalog`, `FolderRouter`, `SiblingRouter`, `CatalogRouter`, `ProvenanceBlock`, `EPISTEMIC_NOTICE_TEXT`, `CUBIE_DOC_FRAME_1..3`) — bleiben exklusiv in `doc_frame`.
- **Keine automatische Flachexport-Pflicht in `services/__init__.py`:** Für neue Services empfiehlt sich, primär den Service-Namespace (`from qb_cubie.core.services.coverage import ...`) und allenfalls die Haupt-Service-Klasse in `services/__init__.py` zu exportieren, statt 30–50 interne Bausteine flach zu spiegeln.

---

## 6. Empfohlene Migrations-Roadmap (Soll)

1. **Schritt 1 – Fundament (`service_core/guards.py` & `service_core/workspace.py`):**
   Duplikate D1/D2/D4/D5 zentralisieren, `atomic_write_text` einführen, `DocEnsurance._source_loader` und `DocFrame`-Dateizugriffe darauf umstellen (inkl. `excludes`-Guard-Härtung für `DocEnsurance`).
2. **Schritt 2 – Generische Rule- & Report-Schicht (`service_core/rules.py` & `service_core/reporting.py`):**
   `RuleRegistry` und `FileCheckRunner` (mit per-File-Parse-Cache) aus `DocEnsurance` extrahieren; `DocFrame.check()` (oder `FileCheckRunner` direkt) ermöglichen; Dummy-`scan()`/`check()`-Methoden aus `FramePattern` und `doc_frame_rules.py` entfernen; `reporter`-Parameter in `DocFrame` und `ServiceReportProtocol`-Support in `JsonReporter` ergänzen.
3. **Schritt 3 – Markdown-Frontend (`service_core/markdown.py`):**
   `FenceTracker`, `parse_kv_attrs`, `DirectiveSpanScanner` und `apply_span_replacements` extrahieren; `_MarkdownScanner` (inkl. explizitem `hr`-Handling für `---`) und `_FrameSpanScanner` darauf umstellen.
4. **Schritt 4 – Erweiterbare CLI & Gate-Nachschärfung (`service_core/cli_spec.py` & Meta-Gate 4):**
   `cli.py` auf Lazy-Command-Registry umstellen (mit `qb-cubie docframe` und `qb-cubie docensurance`), das Modul-Layout beider Alt-Services schrittweise an `DEV-GUIDE_Services.md` angleichen und Meta-Gate 4 (`PureDomainIoRule`) um Filesystem-Probes wie `.exists()` schärfen.

---

## 7. Verifikation & Besonderheiten

> [!NOTE]
> **Beobachtete Arbeitskopie-Besonderheit:** Vor Beginn dieser Analyse enthielt der Checkout bereits eine lokale Änderung in `src/qb_cubie/core/services/doc_frame/presets.py:80` (`> [!Note]` $\to$ `> [!NOTE]`) sowie uncommittete Dateien `GEMINI-1.md` und `docs/services/ANALYSIS.md`. Diese bestehenden Änderungen wurden nicht verändert.

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| **Quantitative Code-Vermessung** | `.venv/bin/python - <<'PY' ... PY` (AST-/LOC-/Regex-/Guard-Zählung über `src/qb_cubie/core/services/`) | `doc_ensurance`: 7 Dateien, 1.529 LOC, 10 Guards; `doc_frame`: 8 Dateien, 1.642 LOC, 26 Guards; `services.__all__`: 90 Exporte |
| **Rahmen-Synchronisation (`ANALYSIS.md`)** | `.venv/bin/python -m qb_cubie docframe update docs/services/ANALYSIS.md --exclude ...` | 1. Lauf: `Updated 1 file(s): docs/services/ANALYSIS.md`; 2. Lauf idempotent: `Updated 0 file(s); all frames up to date.` |
| **Gezielte DocFrame- & DocEnsurance-Prüfung auf `ANALYSIS.md`** | `.venv/bin/python -c "... DocEnsurance(target='docs/services/ANALYSIS.md', pattern=(CUBIE_DOC_STYLE, CUBIE_DOC_FRAME_1..3), rules=(CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES), excludes=DOC_EXCLUDES, reporter=None).run()"` | `ANALYSIS_CHECK: True ()` (`passed=True`, 0 Diagnosen) |
| **Service-Architektur-Gate & Service-Unit-Tests** | `.venv/bin/python -m pytest -q tests/tests_core/tests_services/test_service_architecture_gate.py tests/tests_core/tests_services/tests_doc_frame/ tests/tests_core/tests_services/tests_doc_ensurance/` | `140 passed in 49.71s` (Exit-Code `0`, inkl. Meta-Gate 4) |

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | Service-Core | ↤](./GUIDE_Service-Core.md)  
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
