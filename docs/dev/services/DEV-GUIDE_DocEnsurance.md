<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# `DocEnsurance`

![Cubie](../../.assets/cubie-logo-written.png)

Das `doc_ensurance`-Paket bildet die Verifikations-Engine für ausführbare Dokumentation innerhalb von `qb_cubie.services`. Es überträgt das formallogische Hoare-Tripel $\{P\}\ S\ \{Q\}$ aus der `EBT`-Architektur auf Markdown-Dokumente und sichert Code-Beispiele dreistufig ab: **strukturell** (Nachbarschafts-Muster rund um Code-Anker), **statisch-didaktisch** (Pluggable Check-Regeln & Linter-Adapter) und **funktional** (isolierte oder zustandsgeteilte Ausführung in einer `Arena`).

---

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

---

---

## Paket-Topologie & Architektur-Überblick

Um das Modul-Limit des Cubie-Styleguides ($\le 500$ Zeilen pro Datei, $\le 12$ Codezeilen pro Funktionskörper) strikt einzuhalten und gleichzeitig eine offene Erweiterbarkeit nach dem **Open-Closed-Prinzip** zu gewährleisten, ist `src/qb_cubie/services/doc_ensurance/` in fünf spezialisierte Module unterteilt:

| Modul | Architektonische Rolle | Kern-Komponenten |
| :--- | :--- | :--- |
| **`protocols.py`** | Unveränderliche Daten-Container (DTOs), Severity-Guards und Protokoll-Verträge | `MdBlock`, `ExtractedExample`, `ExampleSession`, `DocDiagnostic`, `SessionTrace`, `DocReport`, `DocBlockProtocol`, `DocRuleProtocol`, `DocPatternProtocol`, `DocScopeProtocol`, `ServiceReportProtocol` |
| **`_markdown_scanner.py`** | Zustandslose Tokenisierungs-Engine (Ebene 0) | `_MarkdownScanner` (zeilenbasierter Zustandsautomat: Markdown-Text $\to$ `list[MdBlock]`) |
| **`doc_patterns.py`** | Atomare Struktur-Matcher (Ebene 1), Basis-Regeln (Ebene 2), Anker-Scanner (Ebene 3) & Session-Scoping (Ebene 4) | `Explanation`, `CodeSnippet`, `CollapsibleResult`, `ExplanationRule`, `CodeRule`, `OutputRule`, `DocLinterRule`, `MissingOutputRule`, `OutputMatchRule`, `ExamplePattern`, `TaggedScope`, `CUBIE_DOC_STYLE`, `DEFAULT_DOC_RULES` |
| **`doc_rules.py`** | Didaktische Standard-Prüfregeln (Ebene 2) | `NoOutput`, `HighComplexity`, `LargeOutput`, `RawTraceback`, `CUBIE_DOC_RULES` |
| **`doc_ensurance.py`** | Stateful Orchestrator (Ebene 5) & IPC-sicherer Arena-Worker | `DocEnsurance`, `_execute_session_payload`, `_execute_single_step`, `_classify_step_exception` |

---

## Konstruktor-API & Konfiguration (Quick-Lookup)

Die Klasse `DocEnsurance` fungiert als zentraler **Stateful Orchestrator**. Ihr Konstruktor validiert alle Konfigurationsparameter sofort über explizite `STATE-GUARD`s, bevor die Pipeline überhaupt gestartet wird:

* **`target`** (`str | Path | None`, Default: `None`): Bestimmt den Scan-Raum. `None` löst automatisch das Projekt-Root ab `pyproject.toml` (Fallback: `Path.cwd()`) auf. Akzeptiert außerdem Verzeichnis- oder Dateipfade sowie mehrzeilige (oder einzeilige) In-Memory-Markdown-Strings.
* **`pattern`** (`DocPatternProtocol | None`, Default: `CUBIE_DOC_STYLE`): Das strukturelle Sequenz-Muster, das Markdown-Blöcke in ausführbare `ExtractedExample`-Objekte und strukturelle `DocDiagnostic`s (`DOC-PRE`, `DOC-POST`) überführt.
* **`scope`** (`DocScopeProtocol | None`, Default: `TaggedScope()`): Die Gruppierungs-Strategie, die extrahierte Beispiele in isolierte oder geteilte `ExampleSession`-Einheiten bündelt.
* **`arena`** (`Arena | None`, Default: `TempFS(timeout=10.0)`): Die physische Ausführungsumgebung (`TempFS` oder `PyVenv`). Jede `ExampleSession` durchläuft einen eigenen `setup(pre_state)` $\to$ `execute(...)` $\to$ `teardown()`-Zyklus.
* **`reporter`** (`Reporter[DocReport] | None`, Default: `PytestReporter()`): Konsument des finalen `DocReport`. `None` aktiviert den geräuschlosen Headless-Modus für programmatische Analysen und Meta-Tests.
* **`pre_state`** (`WorldState | None`, Default: `WorldState()`): Ausgangszustand (insb. `WorldState(fs={...})`), der vor jeder Session frisch in den Arena-Workspace hydratisiert wird.
* **`excludes`** (`Sequence[str] | None`, Default: `None`): Zusätzliche Datei-, Ordner- oder Teilpfad-Ausschlüsse, die mit `DEFAULT_EXCLUDES` (`.venv`, `.git`, `__pycache__` etc.) vereinigt werden.
* **`rules`** (`Sequence[DocRuleProtocol | Linter | type] | None`, Default: `None`): Optionale Liste zusätzlicher oder überschreibender Prüfregeln und Linter-Backends.
* **`timeout`** (`float | None`, Keyword-only, Default: `10.0`): Maximale Laufzeit (TTL in Sekunden) pro Arena-Session auf POSIX-Systemen.

### Konfigurations-Invariante für Arena-Timeouts (`_configure_arena`)

Übergibt der Aufrufer keine eigene Arena (`arena=None`), instanziiert `DocEnsurance` automatisch `TempFS(timeout=self.timeout)`. Wird hingegen eine bereits instanziierte Arena übergeben, gilt eine strikte **Spezifitäts-Rangfolge**:
* Besitzt die übergebene Arena noch kein eigenes Limit (`getattr(arena, "timeout", None) is None`), injiziert `DocEnsurance` sein `self.timeout` auf die Arena-Instanz.
* Wurde die Arena bereits explizit mit einem Timeout konfiguriert (z. B. `TempFS(timeout=0.5)`), bleibt dieses spezifische Arena-Limit unangetastet und hat Vorrang vor dem Service-Default.

---

## 1. Kern-Datenstrukturen (DTOs) & Protokoll-Verträge (`protocols.py`)

Sämtliche Datenstrukturen in `protocols.py` sind als unveränderliche `@dataclass(frozen=True)`-Records entworfen. Dadurch können Zwischenstände gefahrlos zwischen Scanner, Regel-Engine, Arena-Boundary und Reporter weitergereicht werden, ohne dass nachgelagerte Stufen historische Diagnosen oder Extrakte mutieren.

### 1.1 Die Daten-Pipeline (Vom Roh-Block zum Report)

1. **`MdBlock(kind, content, line, meta="")`**
   Das atomare Ausgabe-Token des `_MarkdownScanner`.
   * `kind`: Einer der fünf kanonischen Block-Typen `"heading"`, `"paragraph"`, `"list"`, `"code"` oder `"details"`.
   * `content`: Der normalisierte Text- oder Code-Inhalt des Blocks.
   * `line`: 1-basierte Startzeile des Blocks im ursprünglichen Markdown-Dokument.
   * `meta`: Kontextabhängige Metadaten – bei `"code"` der Info-String hinter dem öffnenden Fence (z. B. `"python session=alpha raises=ValueError"`), bei `"details"` der bereinigte Text des `<summary>`-Tags.

2. **`ExtractedExample(file_path, line, code, expected_output, explanation, session_id, expected_raises)`**
   Repräsentiert einen durch das `DocPatternProtocol` erkannten Anker-Block samt seinen aufgelösten Nachbarn ($P$ und $Q$) sowie den geparsten Fence-Tags:
   * `explanation`: Extrahierter Text des Pre-Blocks (oder `None`, falls kein Pre-Block vorhanden war).
   * `expected_output`: Extrahierter Soll-Output des Post-Blocks (oder `None`, falls der Post-Block fehlte).
   * `session_id`: Wert eines `session=<id>`-Tags oder `None` für isolierte Einzel-Snippets.
   * `expected_raises`: Wert eines `raises=<Exception>`-Tags oder `None` für reguläre Ausführung.

3. **`ExampleSession(session_id, steps)`**
   Bündelt ein Tupel zusammengehöriger `ExtractedExample`-Schritte (`steps: tuple[ExtractedExample, ...]`) unter einer eindeutigen `session_id` (z. B. `"docs/guide.md::session:alpha"` oder `"docs/guide.md::isolated:0"`). Eine `ExampleSession` entspricht exakt einem physischen Arena-Lauf.

4. **`DocDiagnostic(file_path, rule_id, line, message, session_id=None, severity="error")`**
   Das universelle Diagnose-DTO für Strukturbrüche, Regelverstöße, Linter-Befunde und Laufzeitfehler. Ein `__post_init__`-Hook erzwingt über `validate_severity(self.severity)`, dass ausschließlich `"error"` oder `"warning"` (`VALID_SEVERITIES`) instanziiert werden können.

5. **`SessionTrace(session_id, actual_outputs, passed)` & `DocReport(target, passed, sessions, diagnostics)`**
   `SessionTrace` protokolliert die real beobachteten Ausgaben (`actual_outputs: tuple[str, ...]`) pro Schritt sowie den Booleschen Gesamtstatus einer Session. `DocReport` bündelt alle `SessionTrace`s und `DocDiagnostic`s des Laufs und implementiert das `@runtime_checkable` `ServiceReportProtocol`, über das `PytestReporter` beliebige Cubie-Services einheitlich auswertet.

---

## 2. Ebene 0: Der Markdown-Zustandsautomat (`_MarkdownScanner`)

Anstatt schwere externe Markdown-AST-Bibliotheken einzubinden (die HTML-Blöcke, GitHub-Alerts oder verschachtelte Code-Fences oft unterschiedlich interpretieren), nutzt `DocEnsurance` in `_markdown_scanner.py` eine deterministische, zeilenbasierte State-Machine (`_MarkdownScanner`).

### 2.1 Absatz-Klassifikation & Nachbarschafts-Schutz (`_consume_text_line`)

Für die strukturelle Prüfung (`DOC-PRE`) ist entscheidend, dass nur echter erklärender Fließtext als `MdBlock(kind="paragraph")` emittiert wird, während Aufzählungen, Tabellen oder Zitate niemals versehentlich als gültige `Explanation` durchgehen:

* **Nicht-Absatz-Erkennung (`_NON_PARA_RE`):** Zeilen, die mit Aufzählungszeichen (`- `, `* `, `+ `), Nummerierungen (`1. `, `1) `), Blockquotes (`>`) oder Tabellen-Pipes (`|...|`) beginnen, werden als Nicht-Absatz markiert, flushen einen eventuell offenen Absatz-Puffer und werden als `MdBlock(kind="list", ...)` abgelegt.
* **Mehrzeilige Listen-Fortsetzungen (`self.in_list`):** Befindet sich der Scanner in einer Liste (`in_list = True`) und ist die Folgezeile eingerückt (`line != line.lstrip(" \t")`), gilt sie weiterhin als Teil des Listenpunkts und nicht als neuer Paragraph. Erst eine Leerzeile, eine Überschrift (`#`), ein Code-Fence oder ein Spezialblock setzt `in_list` zurück.
* **GitHub-Alerts als valide Erklärungen (`_consume_alert`):** Während klassische Zitate (`> Text`) keine `Explanation` darstellen, werden GitHub-spezifische Hinweisblöcke (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!WARNING]`, `> [!CAUTION]`) über `_ALERT_RE` abgefangen. Ihr Textkörper wird von führenden `>`-Zeichen befreit und bewusst als `MdBlock(kind="paragraph")` emittiert, damit ein Warn- oder Hinweisblock unmittelbar vor einem Code-Beispiel als Erklärung dienen kann.
* **Transparenz von HTML-Kommentaren (`_consume_html_comment`):** Ein- und mehrzeilige Kommentare (`<!-- ... -->`) flushen zwar den aktuellen Absatz, emittieren selbst aber **keinen** `MdBlock`. Ein unsichtbarer Kommentar zwischen Erklärung und Code-Block unterbricht somit nicht die direkte Block-Nachbarschaft.

### 2.2 Code-Fence-Isolation & Selektives Dedenting (`_consume_code_fence`)

Beim Einlesen eines Code-Blocks (` ``` ` oder `~~~`) löst der Scanner zwei klassische Dokumentations-Fallstricke:

1. **Dynamische Fence-Länge (`_fence_prefix` & `_is_closing_fence`):**
   Ein öffnender Fence wird erst durch eine Zeile geschlossen, die mindestens genauso viele identische Fence-Zeichen (` ``` ` vs. ```` ```` ```` bzw. `~~~`) enthält und danach keine weiteren Zeichen besitzt. Dadurch können Entwickler in Dokumentationen 4-Backtick-Blöcke (```` ````markdown ````) verwenden, um 3-Backtick-Python-Beispiele darzustellen, ohne dass diese inneren Blöcke jemals als ausführbare Anker geparst werden.
2. **Schutz von Multiline-Strings bei eingerückten Fences (`_strip_fence_indent`):**
   Ist ein Code-Block im Markdown eingerückt (z. B. um 4 Leerzeichen unter einem Listenpunkt), würde ein pauschales `textwrap.dedent()` auf dem gesamten Code scheitern, sobald das Python-Snippet einen un-eingerückten Multiline-String (`'''zeile1\nzeile2'''`) enthält. Deshalb zieht `_strip_fence_indent` bei eingerückten Fences (`indent > 0`) zeilenweise maximal `indent` führende Leerzeichen ab und nutzt `textwrap.dedent` nur dann, wenn der öffnende Fence selbst auf Spalte 0 stand (`indent == 0`).

### 2.3 Fence-sicheres `<details>`-Parsing (`_consume_details`)

Ein `<details>`-Ergebnisblock kann im erwarteten Konsolen-Output selbst HTML-Fragmente wie `<summary>Inner</summary>` oder `</details>` enthalten (etwa wenn ein Beispiel HTML-Text auf `stdout` ausgibt).

* **Fence-Tracking in `_find_details_end` und `_partition_details_lines`:**
  Der Scanner verfolgt den Code-Fence-Zustand *innerhalb* des `<details>`-Blocks (`_step_details_fence`). Solange ein innerer Code-Fence aktiv ist (`is_fenced = True`), werden `<summary>`- und `</details>`-Tags komplett ignoriert.
* **Schutz gegen ungeschlossene `<details>`-Blöcke:**
  Vergisst ein Autor das schließende `</details>`-Tag, sucht `_find_details_end` nur bis zum nächsten öffnenden `<details` (auf äußerer Ebene). Trifft es vorher auf kein `</details>`, gibt es `None` zurück, und `_consume_details` stuft die `<details>`-Zeile als normalen Absatz zurück. Dadurch schlägt zwar das fehlerhafte erste Beispiel sauber mit `DOC-POST` fehl, verschluckt aber niemals nachfolgende Code-Beispiele im selben Dokument.

Das folgende ausführbare Beispiel demonstriert, wie `_MarkdownScanner` einen Markdown-String mit HTML-Kommentar, 4-Backtick-Block und `<details>`-Container in flache `MdBlock`-Objekte zerlegt:

```python
from qb_cubie.services.doc_ensurance import _MarkdownScanner

fence = "```"
raw_md = (
    "Einleitender Absatz vor einem unsichtbaren HTML-Kommentar.\n\n"
    "<!-- interner Kommentar -->\n\n"
    f"{fence}python session=s1\n"
    "print('hello')\n"
    f"{fence}\n\n"
    f"<details>\n<summary>Ergebnis</summary>\n\n{fence}text\nhello\n{fence}\n</details>"
)

blocks = _MarkdownScanner(raw_md).parse()
print([(b.kind, b.line, b.meta) for b in blocks])
```

<details>
<summary>Ergebnis</summary>

```text
[('paragraph', 1, ''), ('code', 5, 'python session=s1'), ('details', 9, 'Ergebnis')]
```
</details>

---

## 3. Ebene 1, 3 & 4: Die „Lego-Blöcke“ (`doc_patterns.py`)

Die strukturelle Erkennung folgt dem Baukasten-Prinzip: Atomare Block-Matcher (`DocBlockProtocol`) werden in einem Sequenz-Muster (`DocPatternProtocol`) um einen Anker gruppiert und anschließend über eine Scope-Strategie (`DocScopeProtocol`) in Arena-Sessions überführt.

### 3.1 Atomare Block-Protokolle (`DocBlockProtocol` – Ebene 1)

Jeder Baustein implementiert das `DocBlockProtocol`:

```text
class DocBlockProtocol(Protocol):
    @property
    def role(self) -> str: ...
    @property
    def severity(self) -> str: ...
    @property
    def rules(self) -> Sequence[DocRuleProtocol]: ...
    def matches(self, block: MdBlock) -> bool: ...
    def extract(self, block: MdBlock) -> str: ...
```

Die drei mitgelieferten Standard-Bausteine in `doc_patterns.py` decken den `CUBIE_DOC_STYLE` ab:

1. **`Explanation(min_chars=20, role="explanation", severity="error", rules=())`**
   Prüft `block.kind == "paragraph" and len(block.content.strip()) >= self.min_chars` und gibt den bereinigten Absatztext zurück.
2. **`CodeSnippet(lang="python", role="target", severity="error", rules=())`**
   Zerlegt `block.meta` über `re.split(r"[\s,]+", block.meta.strip())` und prüft, ob das erste Token exakt `self.lang` entspricht (sodass fremde Blöcke wie `python3`, `py` oder `bash` ignoriert werden). Über `CodeSnippet.parse_tags(meta)` werden die Schlüssel-Wert-Paare `session=<id>` und `raises=<Exc>` mittels `_TAG_RE = re.compile(r"\b(?P<key>session|raises)=(?P<val>[^\s,]+)")` extrahiert. Durch die Wortgrenze `\b` lösen Attribute wie `my_session=alpha` oder `no_raises=ValueError` keine Fehl-Extraktion aus.
3. **`CollapsibleResult(summary=None, role="result", severity="error", rules=())`**
   Prüft `block.kind == "details"` sowie optional `self.summary in block.meta`. Beim Extrahieren (`extract`) entfernt `_is_wrapped_fence` genau dann die erste und letzte Zeile, wenn der gesamte Inhalt von einem einzigen passenden Code-Fence umschlossen ist (ohne dass derselbe Fence zwischendurch geschlossen und neu geöffnet wird). Dabei wird nur `strip("\r\n")` statt `.strip()` verwendet, damit signifikante führende Leerzeichen in mehrzeiligen Konsolenausgaben erhalten bleiben.

### 3.2 Der Anker-Scanner (`ExamplePattern` – Ebene 3)

`ExamplePattern(anchor, pre=(), post=(), name="example-pattern")` iteriert über den `MdBlock`-Strom. Immer wenn `self.anchor.matches(block)` an Index `idx` zutrifft, prüft `_inspect_anchor` die unmittelbare Nachbarschaft:

* **Rückwärts-Prüfung (`_check_pre`):**
  Iteriert mit `enumerate(reversed(self.pre), start=1)` rückwärts vom Anker (`target_idx = idx - offset`). Liegt `target_idx < 0` oder schlägt `rule.matches(blocks[target_idx])` fehl, wird eine Diagnose `DOC-PRE` mit der `severity` des jeweiligen Pre-Bausteins auf der Zeile des Anker-Blocks emittiert.
* **Der `_fallback_explanation`-Mechanismus:**
  Schlägt ein `Explanation`-Baustein lediglich wegen unterschrittener `min_chars` fehl (z. B. `"kurz."` bei `Explanation(min_chars=20, severity="warning")`), ist an `target_idx` dennoch ein realer `MdBlock(kind="paragraph")` vorhanden. `_fallback_explanation` extrahiert diesen Text trotzdem in `ExtractedExample.explanation`, damit nachgelagerte inhaltliche `ExplanationRule`s (wie Großschreibungs- oder TODO-Prüfungen) nicht blind übersprungen werden.
* **Vorwärts-Prüfung (`_check_post`):**
  Iteriert mit `enumerate(self.post, start=1)` vorwärts (`target_idx = idx + offset`). Fehlt ein geforderter Post-Block, entsteht eine Diagnose `DOC-POST` mit `rule.severity` und `expected_output` bleibt `None`.

### 3.3 Session-Topologie (`TaggedScope` – Ebene 4)

`TaggedScope.group(examples)` gruppiert die Liste aller `ExtractedExample`-Objekte unter Beibehaltung ihrer Deklarationsreihenfolge in ein geordnetes Dictionary:
* Besitzt ein Beispiel eine `session_id` (aus `session=<id>`), lautet der Bucket-Schlüssel `f"{ex.file_path}::session:{ex.session_id}"`.
* Besitzt es keine `session_id`, erhält es den eindeutigen Schlüssel `f"{ex.file_path}::isolated:{idx}"`.

Durch den Datei-Präfix `{ex.file_path}::` sind gleichnamige Sessions (z. B. `session=demo`) über verschiedene Markdown-Dateien hinweg physisch voneinander getrennt.

---

## 4. Ebene 2: Regel-System, Coercion & Linter-Merging (`doc_patterns.py` & `doc_rules.py`)

Inhaltliche und statische Prüfungen sind vollständig über das `@runtime_checkable` `DocRuleProtocol` entkoppelt:

```text
@runtime_checkable
class DocRuleProtocol(Protocol):
    @property
    def rule_id(self) -> str: ...
    @property
    def severity(self) -> str | None: ...
    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> Sequence[DocDiagnostic]: ...
```

### 4.1 Die Regel-Bausteine (`DEFAULT_DOC_RULES` & `CUBIE_DOC_RULES`)

* **Generische Prädikat-Adapter (`doc_patterns.py`):**
  * `ExplanationRule(rule_id, message, check_fn: Callable[[str], bool], severity="error")`: Prüft `example.explanation` (sofern nicht `None`).
  * `CodeRule(rule_id, message, check_fn: Callable[[str], bool], severity="error")`: Prüft `example.code`.
  * `OutputRule(rule_id, message, check_fn: Callable[[str | None, str | None], bool], severity="error")`: Prüft `(example.expected_output, actual_output)`, sobald das Snippet tatsächlich in der Arena gelaufen ist (`actual_output is not None`).
* **Basis-Ausgaberegeln (`DEFAULT_DOC_RULES` in `doc_patterns.py`):**
  * `MissingOutputRule` (`DOC-OUT-MISSING`, Default: `"warning"`): Feuert, wenn `actual_output is not None`, `expected_output is not None`, aber `expected_output.strip() == ""`.
  * `OutputMatchRule` (`DOC-OUT`, Default: `"error"`): Feuert, wenn ein nicht-leerer `expected_output` vom beobachteten `actual_output` abweicht.
* **Didaktische Standardregeln (`CUBIE_DOC_RULES` in `doc_rules.py`):**
  * `NoOutput` (`DOC-NO-OUTPUT`, Default: `"warning"`): Ersetzt `DOC-OUT-MISSING` durch eine kontextsensitive Diagnose. Hat das Snippet `stdout` produziert, der Ergebnisblock ist aber leer, zeigt die Meldung den beobachteten Output an; blieb das Snippet stumm (`actual_output == ""`), empfiehlt die Meldung `print(result)` oder die Verkettung über `session=<id>`.
  * `HighComplexity` (`DOC-HIGH-COMPLEXITY`, Default: `max_lines=30`, `"error"`): Begrenzt die Zeilenzahl einzelner Snippets und verweist auf `session=<id>` sowie `pre_state=WorldState(fs=...)`.
  * `LargeOutput` (`DOC-LARGE-OUTPUT`, Default: `max_lines=25`, `"warning"`): Warnt vor unleserlichen Konsolen-Dumps.
  * `RawTraceback` (`DOC-RAW-TRACEBACK`, Default: `"warning"`): Erkennt `"Traceback (most recent call last):"` im Ergebnisblock und empfiehlt `raises=<Exception>`.

### 4.2 Regel-Normalisierung (`_coerce_rule`) und Registry-Logik (`_build_rules`)

`DocEnsurance` führt Regeln aus drei Quellen in einer geordneten Registry (`dict[str, DocRuleProtocol]`) zusammen:
1. **`DEFAULT_DOC_RULES`** (`DOC-OUT-MISSING` + `DOC-OUT`). Übergibt der Nutzer explizit eine leere Sequenz `rules=()`, wird `DOC-OUT-MISSING` abgewählt und nur `OutputMatchRule` (`DOC-OUT`) als Minimal-Default behalten.
2. **Block-gebundene Regeln (`_extract_pattern_rules`):** Alle in `pattern.pre`, `pattern.anchor` und `pattern.post` hinterlegten `.rules`.
3. **Explizite Service-Regeln:** Über `DocEnsurance(rules=...)` oder `service.register_rule(*rules)` übergebene Einträge.

Dabei gelten drei zentrale Invarianten:
* **0-Arg-Klassen- & Linter-Coercion (`_coerce_rule`):** Wird eine Klasse übergeben (`isinstance(item, type)`), instanziiert `_coerce_rule` diese parameterlos (`item()`). Erfüllt das Objekt danach `DocRuleProtocol`, wird es direkt genutzt; besitzt es `.check` und `.name` (das `Linter`-Protokoll), wird es automatisch in `DocLinterRule(linter=instance)` gewrappt. Alles andere löst sofort einen `TypeError("STATE-GUARD: Rule must implement DocRuleProtocol or Linter...")` aus.
* **Deterministischer Override & `DOC-NO-OUTPUT`-Vorrang:** Regeln mit identischer `rule_id` überschreiben bestehende Einträge in der Registry. Sobald `DOC-NO-OUTPUT` (`NoOutput`) in der Registry aktiv ist, wird `DOC-OUT-MISSING` (`MissingOutputRule`) automatisch per `registry.pop("DOC-OUT-MISSING", None)` entfernt, damit leere Ergebnisblöcke niemals doppelt gemeldet werden.
* **Verlustfreies Linter-Merging (`_register_into` & `_merge_linter_rules`):** Da `DocLinterRule` seine `rule_id` als `f"DOC-LINT:{self.linter.name}"` bildet, hätten zwei `CstLinter`-Instanzen beide die ID `"DOC-LINT:CST-Linter"`. Damit der zweite `CstLinter` den ersten nicht stillschweigend überschreibt, prüft `_register_into`:
  * Handelt es sich bei beiden um `CstLinter` mit identischer `severity`, werden ihre `.rules` und `_excludes` über `_merge_linter_rules` zu einem einzigen kombinierten `CstLinter` verschmolzen.
  * Können zwei Linter mit derselben `rule_id` nicht verschmolzen werden (z. B. unterschiedliche `severity`), vergibt `_unique_rule_key` einen eindeutigen Slot-Schlüssel `f"{rule_id}#{idx}"`, sodass beide Linter aktiv bleiben.

Das folgende Beispiel zeigt, wie `DocEnsurance` zwei separate `CstLinter`-Instanzen sowie `NoOutput` in der internen Regel-Registry zusammenführt und `DOC-OUT-MISSING` automatisch ablöst:

```python
import libcst as cst
from qb_cubie import CstLinter, CstRule
from qb_cubie.services import DocEnsurance, NoOutput


class RuleA(CstRule):
    pass


class RuleB(CstRule):
    pass


service = DocEnsurance(
    rules=[CstLinter(rules=[RuleA()]), CstLinter(rules=[RuleB()]), NoOutput],
    reporter=None,
)
cst_rule = next(r for r in service.rules if r.rule_id == "DOC-LINT:CST-Linter")
print(f"Rules: {[r.rule_id for r in service.rules]} | Merged CST rules: {len(cst_rule.linter.rules)}")
```

<details>
<summary>Ergebnis</summary>

```text
Rules: ['DOC-OUT', 'DOC-LINT:CST-Linter', 'DOC-NO-OUTPUT'] | Merged CST rules: 2
```
</details>

---

## 5. Ebene 5: Der Orchestrator & die Ausführungs-Pipeline (`doc_ensurance.py`)

Der Aufruf `service.run()` durchläuft analog zu `EBT` drei strikt getrennte Makro-Phasen: `_arrange()`, `_validate()` und `_report()`.

### 5.1 Phase 1: `_arrange()` – Ziel-Auflösung, Ausschlüsse & asymmetrische Vorfilterung

1. **Pfad-Heuristik (`_resolve_sources` & `_looks_like_path`):**
   Wird `target` als `str` übergeben, entscheidet `_looks_like_path(target)`, ob es sich um einen Dateisystempfad oder einen In-Memory-Markdown-String handelt:
   * Enthält der String Zeilenumbrüche (`\n`), beginnt er mit typischen Markdown-Präfixen (`#`, `` ` ``, `~`, `<`, `>`, `-`, `*`, `+`, `!`, `[`, `|`) oder enthält er Markdown-Links (`](`, `://`), wird er sofort als `("IN_MEMORY", target)` behandelt.
   * Existiert der Pfad im Dateisystem oder endet er auf `.md` / `.markdown`, gilt er als Dateipfad (sodass ein Tippfehler wie `"docs/missing_guide.md"` garantiert einen `FileNotFoundError`-`STATE-GUARD` wirft).
   * Einzeilige Strings ohne Leerzeichen gelten als Pfad, sobald sie Pfad- oder Dateizeichen (`/`, `\`, `.`, `_`, `-`) enthalten (z. B. `"docs_typo"` $\to$ `FileNotFoundError`, aber `"Hello"` $\to$ `IN_MEMORY`). Enthält der String Leerzeichen, gilt er nur dann als Pfad, wenn das erste Wort einen Pfadtrenner (`/` oder `\`) besitzt und der String nicht mit Satzzeichen (`.`, `!`, `?`) endet (sodass Fließtext wie `"Read/write operations in Python."` als `IN_MEMORY` erkannt wird).

2. **Elternpfad- und Basename-sichere Excludes (`_crawl_directory` & `_is_excluded`):**
   Beim rekursiven Scannen eines Verzeichnisses (`resolved.rglob("*.md")`) wird jeder Pfad zunächst via `path.relative_to(resolved)` relativ zum Scan-Root normalisiert:
   * Dadurch können Ordnernamen *oberhalb* des Scan-Roots (etwa wenn das Projekt selbst in einem Ordner `/tmp/experiments/subproject` liegt und `excludes=("experiments",)` aktiv ist) niemals zu Fehl-Ausschlüssen führen.
   * In `_is_excluded` wird ein führendes `{root_name}/` über `stripped.removeprefix(f"{root_name}/")` abgetrennt, damit `DocEnsurance(target="docs", excludes=("docs/drafts",))` und `excludes=("drafts",)` identisch funktionieren.
   * Enthält das Exclude-Muster einen Schrägstrich (`/`), prüft `_is_excluded` exakt auf `rel_posix == norm` oder `rel_posix.startswith(f"{norm}/")`; nur reine Segmentnamen ohne `/` werden gegen `rel_path.parts` geprüft. So schließt `excludes=("docs/guide.md",)` zwar `docs/guide.md` aus, lässt aber `docs/tutorials/guide.md` unangetastet.

3. **Asymmetrische Vorfilterung bei Strukturfehlern (`_partition_executable` vs. `_has_structural_errors`):**
   Nachdem `self.pattern.scan(...)` alle Beispiele und Strukturdiagnosen (`DOC-PRE`, `DOC-POST`) einer Datei geliefert hat, unterscheidet `_partition_executable` zwischen isolierten Snippets und getaggten Session-Schritten:
   * **Ungetaggte Snippets (`session_id is None`)** mit einem strukturellen `"error"` (`DOC-PRE` oder `DOC-POST`) werden **nicht** in die Arena geschickt (spart Prozess-Overhead), durchlaufen aber sofort alle statischen Regeln via `self._run_step_rules(ex, None, None)`. Haben die Strukturdiagnosen hingegen nur `severity="warning"`, wird das Snippet regulär ausgeführt.
   * **Getaggte Session-Schritte (`session_id is not None`)** werden **trotz** eines `DOC-PRE`- oder `DOC-POST`-Fehlers in die `executable`-Liste übernommen und in der Arena ausgeführt. *Architektonischer Grund:* Würde Schritt 1 einer `session=alpha` wegen einer zu kurzen Erklärung vor der Arena-Ausführung verworfen, fehlten allen nachfolgenden Schritten derselben Session die dort definierten Variablen und Dateien, was eine Kaskade künstlicher `NameError`-Diagnosen (`DOC-EXEC`) auslösen würde. Damit die Session trotz Ausführung nicht als bestanden gilt, prüft `_evaluate_outcomes` am Ende über `_has_structural_errors(session)`, ob für einen der Schritte bereits ein struktureller `"error"` vorlag, und setzt `SessionTrace.passed = False`.

### 5.2 Phase 2: `_validate()` – IPC-Worker & Cross-Step Session-Linting

#### Der IPC-sichere Arena-Worker (`_execute_session_payload`)

Damit jede `ExampleSession` sowohl im Host-basierten `TempFS` als auch über Subprozess-Codecs (`MSGspecCodec`, `PickleCodec`, `CloudpickleCodec`) in `PyVenv` ohne Serialisierungsprobleme läuft, ist der Arena-Worker als reine Top-Level-Funktion implementiert, die ausschließlich primitive Dictionaries (`list[dict[str, Any]]`) konsumiert und zurückgibt:

* **Geteilter Session-Namensraum:** `_execute_session_payload` legt einmalig `shared_globals = {"__name__": "__main__"}` an und reicht dieses Dictionary schrittweise durch `_execute_single_step` weiter. Alle Schritte derselben Session teilen sich somit Variablen, Funktionen, Klassen, Imports und das Arbeitsverzeichnis (`CWD`) der Arena.
* **Zeileninvariante Kompilierung & `stdout`-Isolation:** Jeder Schritt wird via `compile(step["code"], "<doc>", "exec")` kompiliert und unter `contextlib.redirect_stdout(buffer)` ausgeführt. Der feste Dateiname `"<doc>"` garantiert, dass `SyntaxError`-Meldungen (`SyntaxError: invalid syntax (<doc>, line 1)`) unabhängig von der Markdown-Zeilenposition reproduzierbar bleiben. Ausgaben auf `sys.stderr` werden nicht in den Ergebnis-Buffer umgeleitet.
* **`BaseException`-Abfang & MRO-Abgleich (`_classify_step_exception`):**
  Der Worker fängt `BaseException` ab (sodass selbst `sys.exit()` / `SystemExit` oder `KeyboardInterrupt` den Test-Runner nicht abbrechen). Für den abgefangenen Fehler wird die Menge aller einfachen und vollqualifizierten Klassennamen entlang der Method Resolution Order (`type(error).__mro__`) gebildet:
  * Stimmt `expected_raises` mit einem Namen in `mro_names` überein (z. B. `raises=LookupError` bei geworfenem `KeyError` oder `raises=builtins.ValueError`), liefert der Schritt `{"status": "OK", "output": f"{type(error).__name__}: {error}".strip()}`. Etwaiger `stdout`, der vor der Exception im selben Schritt ausgegeben wurde, wird verworfen, und die Session läuft im nächsten Schritt normal weiter.
  * Wurde eine andere Exception geworfen oder blieb eine deklarierte `expected_raises`-Exception aus (`_finalize_normal_step`), liefert der Worker den Status `"DOC-RAISE"`.
  * Trat ohne `expected_raises` eine Exception auf, liefert der Worker `"DOC-EXEC"` mit leerem `output`.

#### Cross-Step Session-Linting (`_run_session_linters` & `_lint_joined_steps`)

Wird ein statischer Linter (wie `MyPy` oder `CstLinter`) über `DocLinterRule` eingebunden, entsteht bei mehrstufigen Sessions (`len(session.steps) > 1`) eine besondere Herausforderung: Schritt 1 definiert `x: int = 41`, und Schritt 2 führt `print(x + 1)` aus. Würde `MyPy` jeden Schritt isoliert prüfen, würde Schritt 2 mit `Name "x" is not defined` fehlschlagen.

`DocEnsurance` löst dieses Problem in `_evaluate_outcomes` zweistufig:
1. Besitzt eine Session mehr als einen Schritt (`include_linters = len(session.steps) <= 1`), werden während der Einzel-Schritt-Prüfung (`_check_step_outcome`) nur die regulären `DocRuleProtocol`-Regeln ausgeführt, während alle `DocLinterRule`-Instanzen zunächst zurückgestellt werden.
2. Anschließend ruft `_evaluate_outcomes` einmalig `_run_session_linters(session)` auf:
   * Schritte mit `expected_raises == "SyntaxError"` werden abgetrennt und einzeln gelintet, damit absichtlich fehlerhafte Syntax-Beispiele nicht den gemeinsamen Syntaxbaum der gesamten Session unparsbar machen.
   * Alle übrigen validen Schritte der Session werden in `_lint_joined_steps` mit `"\n"` zu einem einzigen zusammenhängenden Quellcode-Dokument verbunden und gemeinsam an `r.linter.check(joined)` übergeben.
   * Über `_step_line_ranges` (1-basierte inklusive Zeilen-Intervalle `(start, end, step)`) ermittelt `_map_session_diag` für jeden Linter-Befund den zugehörigen `ExtractedExample`-Schritt, rechnet die Zeilennummer relativ zum Schritt-Anfang um (`diag.line - start + 1`) und addiert sie über `rule._map_diagnostic` exakt auf die Markdown-Startzeile dieses Schritts auf.

### 5.3 Phase 3: `_report()` – Konsolidierung & Reporter-Vertrag

`_report()` bündelt alle `SessionTrace`s und `DocDiagnostic`s in einem unveränderlichen `DocReport`. Dabei gilt:
* `report.passed` ist genau dann `True`, wenn keine einzige Diagnose `severity == "error"` besitzt (`not self._has_errors(self._diagnostics)`).
* Ist ein Reporter konfiguriert (Standard: `PytestReporter()`), wird `self.reporter.report(report)` aufgerufen. `PytestReporter` gibt zunächst für jede Diagnose mit `severity == "warning"` eine standardisierte `UserWarning` (`[rule_id] file:line: message`) aus und löst anschließend nur dann einen `AssertionError` aus, wenn `report.passed is False`.

---

## 6. Entwickler-Rezepte: Eigene Erweiterungen bauen (DI-Guide)

Dank der strikten Protokoll-Trennung lassen sich neue Struktur-Bausteine, Prüfregeln, Sequenz-Muster und Scoping-Strategien ohne Änderung am `DocEnsurance`-Kern implementieren und per Dependency Injection übergeben.

### 6.1 Eigenen Struktur-Baustein (`DocBlockProtocol`) implementieren

Um einen neuen Markdown-Blocktyp strukturell zu verlangen (z. B. eine Pflicht-Überschrift `### Beispiel:` unmittelbar vor der Erklärung), genügt eine Klasse mit den Attributen `role`, `severity`, `rules` sowie den Methoden `matches(block)` und `extract(block)`:

```python
from dataclasses import dataclass
from qb_cubie.services import (
    CodeSnippet, CollapsibleResult, DocRuleProtocol, ExamplePattern, Explanation, MdBlock,
)


@dataclass(frozen=True)
class ExampleHeading:
    prefix: str = "### Beispiel:"
    role: str = "example-heading"
    severity: str = "error"
    rules: tuple[DocRuleProtocol, ...] = ()

    def matches(self, block: MdBlock) -> bool:
        return block.kind == "heading" and block.content.startswith(self.prefix)

    def extract(self, block: MdBlock) -> str:
        return block.content.removeprefix(self.prefix).strip()


pattern = ExamplePattern(
    name="headed-cubie-style",
    pre=(ExampleHeading(), Explanation(min_chars=15)),
    anchor=CodeSnippet(lang="python"),
    post=(CollapsibleResult(),),
)
print(f"Pattern: {pattern.name} | Pre-Roles: {[b.role for b in pattern.pre]}")
```

<details>
<summary>Ergebnis</summary>

```text
Pattern: headed-cubie-style | Pre-Roles: ['example-heading', 'explanation']
```
</details>

### 6.2 Eigene Prüfregel (`DocRuleProtocol`) mit State-Guard implementieren

Reichen die generischen Prädikat-Wrapper (`ExplanationRule`, `CodeRule`, `OutputRule`) nicht aus – etwa weil eine Regel gleichzeitig den Quellcode, die Erklärung und den Laufzeit-Output korrelieren soll –, implementiert man das `DocRuleProtocol` direkt als `@dataclass(frozen=True)` und sichert die Severity im `__post_init__` über `validate_severity` ab:

```python
from dataclasses import dataclass
from qb_cubie.services import DocDiagnostic, DocEnsurance, ExtractedExample, validate_severity


@dataclass(frozen=True)
class RequirePrintMatchRule:
    rule_id: str = "DOC-CUSTOM-PRINT"
    severity: str = "warning"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: ExtractedExample, actual_output: str | None = None
    ) -> list[DocDiagnostic]:
        if actual_output and "print(" not in example.code:
            msg = "Output without explicit print() call."
            return [DocDiagnostic(example.file_path, self.rule_id, example.line, msg, example.session_id, self.severity)]
        return []


service = DocEnsurance(rules=[RequirePrintMatchRule], reporter=None)
print([r.rule_id for r in service.rules])
```

<details>
<summary>Ergebnis</summary>

```text
['DOC-OUT-MISSING', 'DOC-OUT', 'DOC-CUSTOM-PRINT']
```
</details>

### 6.3 Eigene Session-Topologie (`DocScopeProtocol`) injizieren

Möchte ein Projekt beispielsweise, dass *alle* Code-Blöcke einer Markdown-Datei automatisch (auch ohne explizites `session=<id>`-Tag) von oben nach unten in einer einzigen gemeinsamen Datei-Session ablaufen, lässt sich ein eigener `FileGlobalScope` in fünf Zeilen definieren und über `scope=...` injizieren:

```python
from collections.abc import Sequence
from qb_cubie.services import DocEnsurance, ExampleSession, ExtractedExample


class FileGlobalScope:
    """Groups all extracted examples of a file into a single shared session."""

    def group(self, examples: Sequence[ExtractedExample]) -> list[ExampleSession]:
        buckets: dict[str, list[ExtractedExample]] = {}
        for ex in examples:
            buckets.setdefault(f"{ex.file_path}::file_global", []).append(ex)
        return [ExampleSession(session_id=k, steps=tuple(v)) for k, v in buckets.items()]


fence = "```"
doc = (
    "Erster Block definiert x ohne explizites Session-Tag.\n\n"
    f"{fence}python\nx = 21\nprint(x)\n{fence}\n\n"
    f"<details><summary>Ergebnis</summary>\n\n{fence}text\n21\n{fence}\n</details>\n\n"
    "Zweiter Block greift dank FileGlobalScope direkt auf x zu.\n\n"
    f"{fence}python\nprint(x * 2)\n{fence}\n\n"
    f"<details><summary>Ergebnis</summary>\n\n{fence}text\n42\n{fence}\n</details>"
)
report = DocEnsurance(target=doc, scope=FileGlobalScope(), reporter=None).run()
print(f"passed={report.passed} | sessions={len(report.sessions)} | outputs={report.sessions[0].actual_outputs}")
```

<details>
<summary>Ergebnis</summary>

```text
passed=True | sessions=1 | outputs=('21', '42')
```
</details>

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerübersicht & Internals | ↤](../DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](../../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  
[↦ | `DocEnsurance` | ↤](./DEV-GUIDE_DocEnsurance.md)  
[↦ | `DocFrame` (Prototyp) | ↤](./DEV-GUIDE_DocFrame.md)  

</div>
<!-- /qb:frame -->
