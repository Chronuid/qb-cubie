"""Tries to verify scanner, matcher, path-heuristic, and runtime edge cases in DocEnsurance."""

import re
from typing import Any
from pathlib import Path

from qb_cubie import CloudpickleCodec, EBT, ExceptionExpectation, TempFS, WorldState
from qb_cubie.arenas.pyvenv import ArenaBuilder
from qb_cubie.services import (
    CUBIE_DOC_STYLE,
    CodeSnippet,
    CollapsibleResult,
    DocEnsurance,
    ExamplePattern,
    Explanation,
    IsolatedScope,
    MdBlock,
)
from qb_cubie.services.doc_ensurance import _MarkdownScanner

_FOUR_BACKTICK_AND_EMPTY_FENCE_DOC = (
    "````markdown\n"
    "Dieses innere Snippet ist nur ein Doku-Beispiel und darf nicht als Anker matchen:\n\n"
    "```python\n"
    "raise RuntimeError('inner fence inside 4-backtick block must not execute')\n"
    "```\n"
    "````\n\n"
    "Ausreichend lange Erklärung für einen eingerückten Block ohne Konsolenausgabe.\n\n"
    "    ```python\n"
    "    value = 21 * 2\n"
    "    ```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)

_TILDE_AND_MULTILINE_STRING_INDENT_DOC = (
    "Ausreichend lange Erklärung vor einem Tilde-Codeblock und Multiline-String.\n\n"
    "    ~~~python\n"
    "    msg = '''zeile1\n"
    "zeile2'''\n"
    "    print(len(msg.splitlines()))\n"
    "    ~~~\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n~~~text\n2\n~~~\n</details>Nachsatz"
)

_NON_PARAGRAPH_PRE_DOCS = (
    (
        "1. Eine nummerierte Liste direkt vor dem Code ist kein Fließtext-Absatz.\n\n"
        "```python\nprint(1)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n1\n```\n</details>"
    ),
    (
        "1) Eine Klammerliste direkt vor dem Code ist ebenfalls kein Fließtext-Absatz.\n\n"
        "```python\nprint(1)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n1\n```\n</details>"
    ),
    (
        "- Kurzer Punkt\n  Mehrzeilige Listenfortsetzung direkt vor dem Codeblock.\n\n"
        "```python\nprint(1)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n1\n```\n</details>"
    ),
    (
        ">> Verschachteltes Blockquote direkt vor dem Code ist kein Fließtext-Absatz.\n\n"
        "```python\nprint(1)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n1\n```\n</details>"
    ),
    (
        "| Spalte A | Spalte B mit viel Text |\n| --- | --- |\n\n"
        "```python\nprint(1)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n1\n```\n</details>"
    ),
    (
        "Ausreichend lange Erklärung vor einem Code-Block mit ungeschlossenem Details-Tag.\n\n"
        "```python\nprint(1)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\n1\n```"
    ),
)

_UNCLOSED_DETAILS_BEFORE_VALID_DOC = (
    "Erstes Beispiel mit versehentlich nicht geschlossenem Details-Block.\n\n"
    "```python\nprint('erster')\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nerster\n```\n\n"
    "Zweites Beispiel ist vollständig und darf nicht vom ersten Details verschluckt werden.\n\n"
    "```python\nprint('zweiter')\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nzweiter\n```\n</details>"
)

_MULTI_PRE_DOC = (
    "## Kapitelüberschrift\n\n"
    "Die eigentliche Erklärung direkt vor dem Code-Snippet.\n\n"
    "```python\nprint('ok')\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nok\n```\n</details>"
)

_TAG_BOUNDARY_AND_TWO_INNER_FENCES_DOC = (
    "Prüft Wortgrenzen bei my_session/no_raises sowie zwei Fences in einem Details-Block.\n\n"
    "```python my_session=alpha no_raises=ValueError\n"
    "print('```text\\nfirst\\n```\\n\\nText\\n\\n```text\\nsecond\\n```')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    "```text\nfirst\n```\n\nText\n\n```text\nsecond\n```\n</details>"
)

_BROKEN_SESSION_IN_ISOLATED_SCOPE_DOC = (
    "Kurz.\n\n"
    "```python session=alpha\n"
    "raise RuntimeError('must not execute in IsolatedScope when DOC-PRE fails')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)

_SYS_EXIT_UNDECLARED_DOC = (
    "Dieses Snippet ruft sys.exit(0) ohne deklariertes raises=SystemExit auf.\n\n"
    "```python\nimport sys\nsys.exit(0)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)

_SYS_EXIT_DECLARED_DOCS = (
    (
        "Dieses Snippet fängt sys.exit(0) über raises=SystemExit regulär ab.\n\n"
        "```python raises=SystemExit\nimport sys\nsys.exit(0)\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nSystemExit: 0\n```\n</details>"
    ),
    (
        "Dieses Snippet fängt ein argumentloses sys.exit() ohne Leerzeichen-Mismatch ab.\n\n"
        "```python raises=SystemExit\nimport sys\nsys.exit()\n```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nSystemExit:\n```\n</details>"
    ),
)


class _HeadingRule:
    """Matches a Markdown heading block as an outer structural precondition."""

    @property
    def role(self) -> str:
        """Returns the structural role identifier for headings."""
        return "heading"

    def matches(self, block: MdBlock) -> bool:
        """Checks whether the inspected block is a heading."""
        return block.kind == "heading"

    def extract(self, block: MdBlock) -> str:
        """Extracts the heading text without leading hash symbols."""
        return block.content.lstrip("#").strip()


def _run_edge_doc(doc: str, arena: Any = None, scope: Any = None) -> dict[str, Any]:
    """Runs DocEnsurance on an in-memory document and returns a normalized summary dict."""
    report = DocEnsurance(
        target=doc,
        pattern=CUBIE_DOC_STYLE,
        scope=scope,
        arena=arena or TempFS(),
        reporter=None,
    ).run()
    return {
        "target": report.target,
        "passed": report.passed,
        "session_count": len(report.sessions),
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "diagnostics": [(d.rule_id, d.line, d.message) for d in report.diagnostics],
    }


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: 4-BACKTICK-, TILDE- & EINGERÜCKTE FENCES INKL. MULTILINE-STRINGS
# ======================================================================================================================
def test_ebt_four_backtick_tilde_and_indented_fences() -> None:
    """Verifies 4-backtick isolation, tilde fences, multiline-string dedenting, and empty inner fences."""
    EBT(
        target=_run_edge_doc,
        pre=[
            WorldState(args=(_FOUR_BACKTICK_AND_EMPTY_FENCE_DOC,)),
            WorldState(args=(_TILDE_AND_MULTILINE_STRING_INDENT_DOC,)),
        ],
        post=[
            WorldState(
                returns={
                    "target": "IN_MEMORY",
                    "passed": True,
                    "session_count": 1,
                    "outputs": [[""]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "target": "IN_MEMORY",
                    "passed": True,
                    "session_count": 1,
                    "outputs": [["2"]],
                    "diagnostics": [],
                }
            ),
        ],
        custom_id="doc_edge_fences_and_indentation",
    ).run()


# ======================================================================================================================
# 2. ÄQUIVALENZKLASSE: LISTEN, TABELLEN, BLOCKQUOTES & UNGESCHLOSSENE <DETAILS>
# ======================================================================================================================
def test_ebt_lists_tables_blockquotes_and_unclosed_details() -> None:
    """Verifies that lists, tables, and blockquotes fail Explanation and unclosed details fail DOC-POST."""
    EBT(
        target=_run_edge_doc,
        pre=[WorldState(args=(doc,)) for doc in _NON_PARAGRAPH_PRE_DOCS],
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": False,
                "session_count": 0,
                "outputs": [],
                "diagnostics": [(re.compile(r"^DOC-(PRE|POST)$"), int, re.compile(r".+"))],
            }
        ),
        custom_id="doc_edge_lists_quotes_unclosed_details",
    ).run()


def test_ebt_unclosed_details_does_not_swallow_subsequent_examples() -> None:
    """Verifies that an unclosed details tag stops at the next details block without swallowing code."""
    EBT(
        target=_run_edge_doc,
        pre=WorldState(args=(_UNCLOSED_DETAILS_BEFORE_VALID_DOC,)),
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": False,
                "session_count": 1,
                "outputs": [["zweiter"]],
                "diagnostics": [("DOC-POST", 3, re.compile(r".*result"))],
            }
        ),
        custom_id="doc_edge_unclosed_details_isolation",
    ).run()


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: MEHRERE PRE-REGELN, TAG-WORTGRENZEN & ISOLATED-SCOPE
# ======================================================================================================================
def _scan_multi_pre_explanation(doc: str) -> str | None:
    """Scans a document with two pre-rules and returns the extracted explanation string."""
    pattern = ExamplePattern(
        pre=(_HeadingRule(), Explanation(min_chars=15)),
        anchor=CodeSnippet(lang="python"),
        post=(CollapsibleResult(),),
    )
    examples, _ = pattern.scan(_MarkdownScanner(doc).parse(), "IN_MEMORY")
    return examples[0].explanation if examples else None


def test_ebt_multiple_pre_rules_and_tag_word_boundaries() -> None:
    """Verifies multi-pre explanation preservation, tag word boundaries, and IsolatedScope filtering."""
    EBT(
        target=_scan_multi_pre_explanation,
        pre=WorldState(args=(_MULTI_PRE_DOC,)),
        post=WorldState(returns="Die eigentliche Erklärung direkt vor dem Code-Snippet."),
        custom_id="doc_edge_multi_pre_explanation",
    ).run()
    EBT(
        target=_run_edge_doc,
        pre=WorldState(args=(_TAG_BOUNDARY_AND_TWO_INNER_FENCES_DOC,)),
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": True,
                "session_count": 1,
                "outputs": [["```text\nfirst\n```\n\nText\n\n```text\nsecond\n```"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_edge_tag_boundaries_and_double_fences",
    ).run()
    EBT(
        target=_run_edge_doc,
        pre=WorldState(args=(_BROKEN_SESSION_IN_ISOLATED_SCOPE_DOC, None, IsolatedScope())),
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": False,
                "session_count": 0,
                "outputs": [],
                "diagnostics": [("DOC-PRE", 3, re.compile(r".*explanation"))],
            }
        ),
        custom_id="doc_edge_isolated_scope_drops_broken_session_step",
    ).run()


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: EINZEILIGE IN-MEMORY-MARKDOWN-STRINGS VS. PFAD-HEURISTIK
# ======================================================================================================================
def test_ebt_single_line_in_memory_markdown() -> None:
    """Verifies that single-line Markdown constructs and prose mentioning .md are treated as IN_MEMORY."""
    EBT(
        target=_run_edge_doc,
        pre=[
            WorldState(args=("#NurEineUeberschriftOhneLeerzeichen",)),
            WorldState(args=("Siehe docs/guide fuer weitere Informationen.",)),
            WorldState(args=("Siehe README.md",)),
            WorldState(args=("+ListenpunktOhneLeerzeichen",)),
            WorldState(args=("![Bild](logo.png)",)),
            WorldState(args=("[Link](https://example.org)",)),
            WorldState(args=("> Einzeiliges Blockquote ohne Code",)),
        ],
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": True,
                "session_count": 0,
                "outputs": [],
                "diagnostics": [],
            }
        ),
        custom_id="doc_edge_single_line_in_memory",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: SYSTEMEXIT (SYS.EXIT(0) & SYS.EXIT()) IN TEMPFS & PYVENV
# ======================================================================================================================
def _run_sys_exit_in_pyvenv(doc: str) -> dict[str, Any]:
    """Executes a snippet containing sys.exit(0) inside a provisioned PyVenv arena."""
    arena = ArenaBuilder(".venv_edge_sysexit").with_packages(["cloudpickle", "msgspec"]).build()
    return _run_edge_doc(doc, arena=arena)


def test_ebt_system_exit_interception_and_raises() -> None:
    """Verifies that sys.exit(0) and sys.exit() are caught as DOC-EXEC or satisfied via raises=SystemExit."""
    EBT(
        target=_run_sys_exit_in_pyvenv,
        arena=TempFS(),
        pre=WorldState(args=(_SYS_EXIT_UNDECLARED_DOC,)),
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": False,
                "session_count": 1,
                "outputs": [[""]],
                "diagnostics": [("DOC-EXEC", int, re.compile(r"^Unhandled SystemExit: 0"))],
            }
        ),
    ).run()
    EBT(
        target=_run_edge_doc,
        pre=[WorldState(args=(doc,)) for doc in _SYS_EXIT_DECLARED_DOCS],
        post=[
            WorldState(
                returns={
                    "target": "IN_MEMORY",
                    "passed": True,
                    "session_count": 1,
                    "outputs": [["SystemExit: 0"]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "target": "IN_MEMORY",
                    "passed": True,
                    "session_count": 1,
                    "outputs": [["SystemExit:"]],
                    "diagnostics": [],
                }
            ),
        ],
        custom_id="doc_edge_sys_exit_with_and_without_arg",
    ).run()


# ======================================================================================================================
# 6. ÄQUIVALENZKLASSE: INSTANZ-WIEDERVERWENDUNG & REPORT-RESET BEI FEHLERHAFTEM ZWEITLAUF
# ======================================================================================================================
def _reuse_instance_after_failure() -> Any:
    """Runs a DocEnsurance instance once successfully, then triggers an arrange error on reuse."""
    service = DocEnsurance(target=_TILDE_AND_MULTILINE_STRING_INDENT_DOC, reporter=None)
    service.run()
    service.target = "   "
    try:
        service.run()
    except ValueError:
        return service.report_result
    return "DID_NOT_RAISE"


def test_ebt_instance_reuse_resets_report_result() -> None:
    """Verifies that a failing second run() clears the stale report_result from the first run."""
    EBT(
        target=_reuse_instance_after_failure,
        pre=WorldState(),
        post=WorldState(returns=None),
        custom_id="doc_edge_instance_reuse_reset",
    ).run()


# ======================================================================================================================
# 7. ÄQUIVALENZKLASSE: SESSION-WEITERLAUF TROTZ DOC-POST, DOC-OUT & DOC-RAISE (BEFUND C)
# ======================================================================================================================
_SESSION_SURVIVES_ALL_NON_FATAL_VIOLATIONS_DOC = (
    "Schritt 1 initialisiert x regulär in der Session s1.\n\n"
    "```python session=s1\nx = 10\nprint(x)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n10\n```\n</details>\n\n"
    "Schritt 2 hat keinen <details>-Block (DOC-POST), mutiert aber trotzdem y.\n\n"
    "```python session=s1\ny = x + 5\nprint(y)\n```\n\n"
    "Normaler Absatz statt <details>.\n\n"
    "Schritt 3 hat einen falschen Output im <details>-Block (DOC-OUT), setzt aber z.\n\n"
    "```python session=s1\nz = y * 2\nprint(z)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n999\n```\n</details>\n\n"
    "Schritt 4 wirft die angekündigte Exception nicht (DOC-RAISE), setzt aber final.\n\n"
    "```python session=s1 raises=ValueError\nfinal = z + 12\nprint(final)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>\n\n"
    "Schritt 5 greift auf final zu und beweist, dass die Session durchlief.\n\n"
    "```python session=s1\nprint(final)\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
)


def test_ebt_session_continues_across_post_out_and_raise_violations() -> None:
    """Verifies that TaggedScope sessions preserve state across DOC-POST, DOC-OUT, and DOC-RAISE."""
    EBT(
        target=_run_edge_doc,
        pre=WorldState(args=(_SESSION_SURVIVES_ALL_NON_FATAL_VIOLATIONS_DOC,)),
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": False,
                "session_count": 1,
                "outputs": [["10", "15", "30", "42", "42"]],
                "diagnostics": [
                    ("DOC-POST", int, re.compile(r".*result")),
                    ("DOC-OUT", int, re.compile(r".*expected '999', got '30'")),
                    ("DOC-RAISE", int, re.compile(r"^Expected exception 'ValueError'")),
                ],
            }
        ),
        custom_id="doc_edge_session_survives_non_fatal_violations",
    ).run()


# ======================================================================================================================
# 8. ÄQUIVALENZKLASSE: 19/20-ZEICHEN-GRENZE, <DETAILS>-VARIANTEN, STDERR & FREMDFENCES (BEFUND D)
# ======================================================================================================================
_EXPLANATION_19_CHARS_DOC = (
    "   1234567890123456789   \n\n"
    "```python\nprint('fail')\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nfail\n```\n</details>"
)

_EXPLANATION_20_CHARS_AND_DETAILS_VARIANTS_DOC = (
    "12345678901234567890\n\n"
    "```python\nimport sys\nsys.stderr.write('ignored_err\\n')\nprint('ok_open')\n```\n\n"
    "<details open>\nok_open\n</details>\n\n"
    "Zweiter Block prüft einzeiliges <details> und ignoriert fremde Sprach-Tags.\n\n"
    "```python\nprint('ok_inline')\n```\n\n"
    "<details><summary>Ergebnis</summary>ok_inline</details>\n\n"
    "```python3\nraise RuntimeError('python3 tag must be ignored')\n```\n\n"
    "```py\nraise RuntimeError('py tag must be ignored')\n```"
)


def test_ebt_explanation_boundary_details_variants_and_stderr_isolation() -> None:
    """Verifies the 19/20 char boundary, <details open>/inline variants, stderr, and foreign lang tags."""
    EBT(
        target=_run_edge_doc,
        pre=[
            WorldState(args=(_EXPLANATION_19_CHARS_DOC,)),
            WorldState(args=(_EXPLANATION_20_CHARS_AND_DETAILS_VARIANTS_DOC,)),
        ],
        post=[
            WorldState(
                returns={
                    "target": "IN_MEMORY",
                    "passed": False,
                    "session_count": 0,
                    "outputs": [],
                    "diagnostics": [("DOC-PRE", int, re.compile(r".*explanation"))],
                }
            ),
            WorldState(
                returns={
                    "target": "IN_MEMORY",
                    "passed": True,
                    "session_count": 2,
                    "outputs": [["ok_open"], ["ok_inline"]],
                    "diagnostics": [],
                }
            ),
        ],
        custom_id="doc_edge_char_boundary_details_and_stderr",
    ).run()


# ======================================================================================================================
# 9. ÄQUIVALENZKLASSE: RAISES-VERERBUNG, TAG-REIHENFOLGE, LEERE EXCEPTION & SYNTAXERROR (BEFUND E)
# ======================================================================================================================
_RAISES_INHERITANCE_AND_SYNTAX_DOC = (
    "Schritt 1 prüft umgekehrte Tag-Reihenfolge, Bindestrich-ID und MRO-Vererbung.\n\n"
    "```python raises=LookupError session=step-1\n_ = {}['missing']\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nKeyError: 'missing'\n```\n</details>\n\n"
    "Schritt 2 prüft eine leere Exception-Message ohne nachgestelltes Leerzeichen.\n\n"
    "```python session=step-1 raises=ValueError\nraise ValueError()\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nValueError:\n```\n</details>\n\n"
    "Schritt 3 prüft das gezielte Abfangen eines SyntaxError im Snippet.\n\n"
    "```python session=step-1 raises=SyntaxError\ncompile('def broken(:', '<str>', 'exec')\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    "```text\nSyntaxError: invalid syntax (<str>, line 1)\n```\n</details>"
)


def test_ebt_raises_mro_reversed_tags_empty_msg_and_syntax_error() -> None:
    """Verifies MRO exception matching, reversed tags with hyphens, empty messages, and SyntaxError."""
    EBT(
        target=_run_edge_doc,
        pre=WorldState(args=(_RAISES_INHERITANCE_AND_SYNTAX_DOC,)),
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": True,
                "session_count": 1,
                "outputs": [
                    [
                        "KeyError: 'missing'",
                        "ValueError:",
                        "SyntaxError: invalid syntax (<str>, line 1)",
                    ]
                ],
                "diagnostics": [],
            }
        ),
        custom_id="doc_edge_raises_mro_and_syntax_error",
    ).run()


# ======================================================================================================================
# 10. ÄQUIVALENZKLASSE: PYVENV MIT CLOUDPICKLE, TRAILING-SLASH-EXCLUDES & TIMEOUT-VORRANG (BEFUNDE A & F)
# ======================================================================================================================
_PYVENV_CLOUDPICKLE_SESSION_DOC = (
    "Schritt 1 prüft das gesperrte Modul statistics in PyVenv mit CloudpickleCodec.\n\n"
    "```python session=venv_demo raises=TypeError\n"
    "import statistics\n"
    "statistics.mean([1, 2])\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    "```text\nTypeError: PhantomObject 'statistics.mean' cannot be called; install the real dependency.\n```\n</details>\n\n"
    "Schritt 2 läuft in derselben PyVenv-Session normal weiter.\n\n"
    "```python session=venv_demo\nprint('venv_alive')\n```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nvenv_alive\n```\n</details>"
)


def _run_pyvenv_cloudpickle_doc(doc: str) -> dict[str, Any]:
    """Executes DocEnsurance inside a PyVenv configured with CloudpickleCodec and decontams."""
    arena = ArenaBuilder(".venv_edge_cpkl").build(codec=CloudpickleCodec())
    arena._decontams = ["statistics"]
    return _run_edge_doc(doc, arena=arena)


def _check_arena_timeout_precedence(
    arena_timeout: float | None, service_timeout: float | None
) -> float | None:
    """Returns the effective arena timeout after initializing DocEnsurance."""
    arena = TempFS(timeout=arena_timeout)
    service = DocEnsurance(target="# Title", arena=arena, timeout=service_timeout, reporter=None)
    return getattr(service.arena, "timeout", None)


def _run_all_excluded_dir() -> Any:
    """Creates a directory whose Markdown files are all excluded via trailing slash."""
    sub = Path("docs_empty_check") / "sub"
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    return DocEnsurance(target=Path("docs_empty_check"), excludes=("sub/",), reporter=None).run()


def test_ebt_pyvenv_cloudpickle_timeout_precedence_and_empty_excludes() -> None:
    """Verifies PyVenv with CloudpickleCodec, arena timeout precedence, and trailing-slash excludes."""
    EBT(
        target=_run_pyvenv_cloudpickle_doc,
        arena=TempFS(),
        pre=WorldState(args=(_PYVENV_CLOUDPICKLE_SESSION_DOC,)),
        post=WorldState(
            returns={
                "target": "IN_MEMORY",
                "passed": True,
                "session_count": 1,
                "outputs": [[re.compile(r"^TypeError: PhantomObject"), "venv_alive"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_edge_pyvenv_cloudpickle_codec",
    ).run()
    EBT(
        target=_check_arena_timeout_precedence,
        pre=[
            WorldState(args=(0.2, 10.0)),
            WorldState(args=(None, 4.5)),
        ],
        post=[
            WorldState(returns=0.2),
            WorldState(returns=4.5),
        ],
        custom_id="doc_edge_arena_timeout_precedence",
    ).run()
    EBT(
        target=_run_all_excluded_dir,
        arena=TempFS(),
        pre=WorldState(),
        post=WorldState(
            raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD: No Markdown files found")
        ),
        custom_id="doc_edge_all_excluded_dir_guard",
    ).run()