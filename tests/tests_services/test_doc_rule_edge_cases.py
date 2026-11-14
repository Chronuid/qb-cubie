"""Tries to verify rule coercion, scanner traps, scope asymmetries, and runtime edge cases in DocEnsurance."""

from collections.abc import Sequence
from typing import Any

import libcst as cst

from qb_cubie import AstLinter, CstLinter, CstRule, EBT, ExceptionExpectation, MyPy, TempFS, WorldState
from qb_cubie.services import (
    CUBIE_DOC_RULES,
    CUBIE_DOC_STYLE,
    CodeRule,
    CodeSnippet,
    CollapsibleResult,
    DocEnsurance,
    ExamplePattern,
    Explanation,
    ExplanationRule,
    NoOutput,
    OutputMatchRule,
    TaggedScope,
)

# ---------- Test-Fixtures & Markdown-Korpus ---------------------------------------------------------------------------

_SILENT_EMPTY_OUT_DOC = (
    "Ausreichend lange Erklärung für ein stummes Code-Beispiel.\n\n"
    "```python\n"
    "value = 21 * 2\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)

_MISMATCH_OUT_DOC = (
    "Ausreichend lange Erklärung für einen Output-Mismatch.\n\n"
    "```python\n"
    "print('actual_value')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nexpected_value\n```\n</details>"
)

_SHORT_LOWERCASE_PRE_DOC = (
    "lowercase.\n\n"
    "```python\n"
    "print(1)\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\n1\n```\n</details>"
)

_LONG_LOWERCASE_PRE_DOC = (
    "lowercase explanation that easily exceeds fifty characters in total.\n\n"
    "```python\n"
    "print(1)\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\n1\n```\n</details>"
)

_SESSION_DOC_PRE_ASYMMETRY_DOC = (
    "Too short.\n\n"
    "```python session=s1\n"
    "secret = 42\n"
    "print(secret)\n"
    "```\n\n<details><summary>R</summary>\n\n```text\n42\n```\n</details>\n\n"
    "Second explanation is long enough to pass.\n\n"
    "```python session=s1\n"
    "print(secret + 1)\n"
    "```\n\n<details><summary>R</summary>\n\n```text\n43\n```\n</details>"
)

_LAZY_LIST_CONTINUATION_DOC = (
    "- List item one\n"
    "This explanation follows a list item without a blank line.\n\n"
    "```python\nprint(123)\n```\n\n"
    "<details><summary>Ergebnis</summary>\n\n```text\n123\n```\n</details>"
)

_GITHUB_ALERT_PRE_DOC = (
    "> [!NOTE]\n"
    "> This is a GitHub alert explaining the next code snippet thoroughly.\n\n"
    "```python\nprint(1)\n```\n\n"
    "<details><summary>R</summary>\n\n```text\n1\n```\n</details>"
)

_HTML_COMMENT_DISPLACES_PRE_DOC = (
    "This is a long enough explanation paragraph before the comment.\n\n"
    "<!-- comment -->\n\n"
    "```python\nprint(1)\n```\n\n"
    "<details><summary>R</summary>\n\n```text\n1\n```\n</details>"
)

_FENCE_IN_MULTILINE_STR_DOC = (
    "Explanation with twenty characters.\n\n"
    "````python\n"
    'md = """\n'
    "```\n"
    "hello\n"
    "```\n"
    '"""\n'
    "print(len(md.splitlines()))\n"
    "````\n\n"
    "<details><summary>R</summary>\n\n```text\n4\n```\n</details>"
)

_TWO_FENCES_IN_DETAILS_DOC = (
    "Explanation with twenty characters.\n\n"
    "```python\nprint('ok')\n```\n\n"
    "<details><summary>R</summary>\n\n"
    "```text\nok\n```\n\n```text\nextra\n```\n"
    "</details>"
)

_COMMA_TAG_IGNORED_DOC = (
    "Explanation with twenty characters.\n\n"
    "```python,session=s1\nprint(1)\n```\n\n"
    "<details><summary>R</summary>\n\n```text\n1\n```\n</details>"
)

_SUMMARYLESS_DETAILS_AND_INDENTED_FENCE_DOC = (
    "- Aufzählungspunkt vor dem Abschnitt\n\n"
    "Ausreichend lange Erklärung vor einem eingerückten Codeblock.\n\n"
    "    ```python\n"
    "    print('clean_indent')\n"
    "    ```\n\n"
    "<details>\n\n```text\nclean_indent\n```\n</details>"
)

_KEYBOARD_INTERRUPT_DOC = (
    "Explanation with at least twenty chars.\n\n"
    "```python raises=KeyboardInterrupt\n"
    "raise KeyboardInterrupt('ctrl-c')\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\nKeyboardInterrupt: ctrl-c\n```\n</details>"
)

_DOTTED_RAISES_DOC = (
    "Explanation with at least twenty chars.\n\n"
    "```python raises=builtins.ValueError\n"
    "raise ValueError('boom')\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\nValueError: boom\n```\n</details>"
)

_PRINT_BEFORE_RAISES_DOC = (
    "Explanation with at least twenty chars.\n\n"
    "```python raises=ValueError\n"
    "print('stdout before exception is discarded')\n"
    "raise ValueError('boom')\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\nValueError: boom\n```\n</details>"
)

_LEADING_WHITESPACE_STRIP_DOC = (
    "Explanation testing leading whitespace stripping.\n\n"
    "```python\n"
    "print('   indented_first')\n"
    "print('  indented_second')\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n"
    "```text\nindented_first\n  indented_second\n```\n</details>"
)

_SESSION_MYPY_AND_NO_OUTPUT_DOC = (
    "Schritt 1 definiert x als Setup ohne eigene Ausgabe.\n\n"
    "```python session=s1\n"
    "x: int = 41\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\n```\n</details>\n\n"
    "Schritt 2 nutzt x aus Schritt 1 und gibt die Summe aus.\n\n"
    "```python session=s1\n"
    "print(x + 1)\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\n42\n```\n</details>"
)

_EVAL_AND_PRINT_DOC = (
    "Ausreichend lange Erklärung für ein Snippet mit eval und print.\n\n"
    "```python\n"
    "print(eval('42'))\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\n42\n```\n</details>"
)

_HTML_SUMMARY_IN_OUTPUT_DOC = (
    "Erklärung für ein Snippet, das ein summary-Tag auf stdout ausgibt.\n\n"
    "```python\n"
    "print('<summary>Inner</summary>')\n"
    "```\n\n"
    "<details><summary>Ergebnis</summary>\n\n"
    "```text\n<summary>Inner</summary>\n```\n</details>"
)

_HTML_CLOSING_DETAILS_IN_OUTPUT_DOC = (
    "Erklärung für ein Snippet, das ein schließendes details-Tag ausgibt.\n\n"
    "```python\n"
    "print('</details>')\n"
    "```\n\n"
    "<details><summary>Ergebnis</summary>\n\n"
    "```text\n</details>\n```\n</details>"
)

_HTML_SUMMARY_WITH_ATTR_DOC = (
    "Erklärung für ein Snippet mit HTML-Attribut im summary-Tag.\n\n"
    "```python\n"
    "print('ok')\n"
    "```\n\n"
    '<details><summary class="res">Ergebnis</summary>\n\n'
    "```text\nok\n```\n</details>"
)

_RAW_SYNTAX_ERROR_DOC = (
    "Erklärung für einen direkten SyntaxError im Code-Block.\n\n"
    "```python raises=SyntaxError\n"
    "def broken(:\n"
    "```\n\n"
    "<details><summary>Ergebnis</summary>\n\n"
    "```text\nSyntaxError: invalid syntax (<doc>, line 1)\n```\n</details>"
)

_WARN_PRE_WITH_EXP_RULE_PATTERN = ExamplePattern(
    name="warn-pre-exp-rule",
    pre=(
        Explanation(
            min_chars=50,
            severity="warning",
            rules=(ExplanationRule("EXP-CAP", "Must start uppercase.", lambda s: s[0].isupper()),),
        ),
    ),
    anchor=CodeSnippet(lang="python"),
    post=(CollapsibleResult(),),
)


class _NoPrintCstRule(CstRule):
    """Flags print() calls for testing zero-arg CstLinter class coercion."""

    def visit_Call(self, node: cst.Call) -> None:
        """Records a CST-NO-PRINT diagnostic when encountering a print() call."""
        if isinstance(node.func, cst.Name) and node.func.value == "print":
            self.add_diagnostic(node, "CST-NO-PRINT", "print() flagged.")


class _NoEvalCstRule(CstRule):
    """Flags eval() calls for testing CstLinter rule_id collisions."""

    def visit_Call(self, node: cst.Call) -> None:
        """Records a CST-NO-EVAL diagnostic when encountering an eval() call."""
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(node, "CST-NO-EVAL", "eval() flagged.")


class _ZeroArgPrintLinter(CstLinter):
    """Zero-argument Linter subclass that can be coerced directly from its type."""

    def __init__(self) -> None:
        """Initializes CstLinter with the _NoPrintCstRule."""
        super().__init__(rules=[_NoPrintCstRule()])


# ---------- Stateless Test-Adapter ------------------------------------------------------------------------------------


def _inspect_rule_registry(
    doc: str,
    rules: Sequence[Any] | None = None,
    extra_registered: Sequence[Any] = (),
) -> dict[str, Any]:
    """Builds DocEnsurance, runs it, and returns active rule IDs plus diagnostic IDs."""
    service = DocEnsurance(target=doc, rules=rules, arena=TempFS(), reporter=None)
    if extra_registered:
        service.register_rule(*extra_registered)
    report = service.run()
    return {
        "rule_ids": [r.rule_id for r in service.rules],
        "passed": report.passed,
        "diag_ids": [(d.rule_id, d.severity) for d in report.diagnostics],
    }


def _run_edge_scenario(
    doc: str,
    pattern: ExamplePattern = CUBIE_DOC_STYLE,
    scope: Any = None,
    extra_registered: Sequence[Any] = (),
    rules: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Executes DocEnsurance and projects session states, outputs, and diagnostics."""
    service = DocEnsurance(
        target=doc, pattern=pattern, scope=scope or TaggedScope(), rules=rules, arena=TempFS(), reporter=None
    )
    if extra_registered:
        service.register_rule(*extra_registered)
    report = service.run()
    return {
        "passed": report.passed,
        "session_passed": [s.passed for s in report.sessions],
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "diagnostics": [(d.rule_id, d.severity, d.line) for d in report.diagnostics],
    }


def _capture_base_exception(doc: str) -> tuple[str, str]:
    """Runs DocEnsurance and returns the class name and message of an escaping BaseException."""
    try:
        DocEnsurance(target=doc, arena=TempFS(), reporter=None).run()
    except BaseException as exc:  # noqa: BLE001
        return (type(exc).__name__, str(exc))
    return ("NO_ESCAPE", "")


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: REGEL-COERCION & STILLER WEGFALL VON DOC-OUT-MISSING (CLUSTER A2)
# ======================================================================================================================


def test_ebt_rule_defaults_reduction_and_type_coercion() -> None:
    """Verifies 0-arg class coercion and flags silent loss of DOC-OUT-MISSING via expect=False."""
    custom_noop = CodeRule("C1", "noop", lambda _: True)
    EBT(
        target=_inspect_rule_registry,
        pre=[
            WorldState(args=(_SILENT_EMPTY_OUT_DOC, None)),
            WorldState(args=(_SILENT_EMPTY_OUT_DOC, ())),
            WorldState(args=(_SILENT_EMPTY_OUT_DOC, [NoOutput])),
            WorldState(args=(_MISMATCH_OUT_DOC, [_ZeroArgPrintLinter, OutputMatchRule(severity="warning")])),
        ],
        post=[
            WorldState(
                returns={
                    "rule_ids": ["DOC-OUT-MISSING", "DOC-OUT"],
                    "passed": True,
                    "diag_ids": [("DOC-OUT-MISSING", "warning")],
                }
            ),
            WorldState(returns={"rule_ids": ["DOC-OUT"], "passed": True, "diag_ids": []}),
            WorldState(
                returns={
                    "rule_ids": ["DOC-OUT", "DOC-NO-OUTPUT"],
                    "passed": True,
                    "diag_ids": [("DOC-NO-OUTPUT", "warning")],
                }
            ),
            WorldState(
                returns={
                    "rule_ids": ["DOC-OUT-MISSING", "DOC-OUT", "DOC-LINT:CST-Linter"],
                    "passed": False,
                    "diag_ids": [("DOC-OUT", "warning"), ("CST-NO-PRINT", "error")],
                }
            ),
        ],
        custom_id="doc_rule_edge_defaults_and_coercion",
    ).run()

    # Positiv-Vertrag: Einzelne CodeRule lässt DOC-OUT-MISSING nicht mehr verschwinden
    EBT(
        target=_inspect_rule_registry,
        pre=WorldState(args=(_SILENT_EMPTY_OUT_DOC, [custom_noop])),
        post=WorldState(
            returns={
                "rule_ids": ["DOC-OUT-MISSING", "DOC-OUT", "C1"],
                "passed": True,
                "diag_ids": [("DOC-OUT-MISSING", "warning")],
            }
        ),
        custom_id="doc_rule_edge_custom_rule_preserves_missing_output",
    ).run()

    EBT(
        target=_inspect_rule_registry,
        pre=WorldState(args=(_SILENT_EMPTY_OUT_DOC, [CstLinter])),
        post=WorldState(
            raises=ExceptionExpectation(TypeError, match=r"missing 1 required positional argument: 'rules'")
        ),
        custom_id="doc_rule_edge_uninstantiated_cst_linter_type_error",
    ).run()


# ======================================================================================================================
# 2. ÄQUIVALENZKLASSE: EXPLANATION-RULE SKIP BEI DOC-PRE-WARNING & BLOCK-REGEL-OVERRIDE (CLUSTER D3.2)
# ======================================================================================================================


def test_ebt_explanation_rule_skipped_on_pre_warning_and_override() -> None:
    """Verifies block rule override and flags skipped ExplanationRule on DOC-PRE warning via expect=False."""
    warn_override = ExplanationRule("EXP-CAP", "Must start uppercase.", lambda s: s[0].isupper(), severity="warning")
    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_LONG_LOWERCASE_PRE_DOC, _WARN_PRE_WITH_EXP_RULE_PATTERN)),
            WorldState(
                args=(_LONG_LOWERCASE_PRE_DOC, _WARN_PRE_WITH_EXP_RULE_PATTERN),
                kwargs={"extra_registered": [warn_override]},
            ),
        ],
        post=[
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [["1"]],
                    "diagnostics": [("EXP-CAP", "error", 3)],
                }
            ),
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["1"]],
                    "diagnostics": [("EXP-CAP", "warning", 3)],
                }
            ),
        ],
        custom_id="doc_rule_edge_block_rule_override",
    ).run()

    # Positiv-Vertrag: DOC-PRE-Warning liefert trotzdem den Absatz an EXP-CAP weiter
    EBT(
        target=_run_edge_scenario,
        pre=WorldState(args=(_SHORT_LOWERCASE_PRE_DOC, _WARN_PRE_WITH_EXP_RULE_PATTERN)),
        post=WorldState(
            returns={
                "passed": False,
                "session_passed": [False],
                "outputs": [["1"]],
                "diagnostics": [("DOC-PRE", "warning", 3), ("EXP-CAP", "error", 3)],
            }
        ),
        custom_id="doc_rule_edge_pre_warning_preserves_exp_rule",
    ).run()


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: DOC-PRE IN MULTI-STEP-SESSIONS IM TAGGED-SCOPE (CLUSTER D3.1)
# ======================================================================================================================


def test_ebt_session_doc_pre_marks_session_failed_in_tagged_scope() -> None:
    """Verifies session.passed=False when DOC-PRE fails in a multi-step TaggedScope session."""
    EBT(
        target=_run_edge_scenario,
        pre=WorldState(args=(_SESSION_DOC_PRE_ASYMMETRY_DOC, CUBIE_DOC_STYLE, TaggedScope())),
        post=WorldState(
            returns={
                "passed": False,
                "session_passed": [False],
                "outputs": [["42", "43"]],
                "diagnostics": [("DOC-PRE", "error", 3)],
            }
        ),
        custom_id="doc_rule_edge_session_pre_marks_session_failed",
    ).run()


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: MARKDOWN-SCANNER NACHBARSCHAFTS-FALLEN (CLUSTER C1 & C2)
# ======================================================================================================================


def test_ebt_lazy_list_continuation_alert_and_html_comment_traps() -> None:
    """Flags DOC-PRE false alarms caused by sticky in_list, GitHub alerts, and HTML comments."""
    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_LAZY_LIST_CONTINUATION_DOC,)),
            WorldState(args=(_GITHUB_ALERT_PRE_DOC,)),
            WorldState(args=(_HTML_COMMENT_DISPLACES_PRE_DOC,)),
        ],
        post=[
            WorldState(
                returns={"passed": False, "session_passed": [], "outputs": [], "diagnostics": [("DOC-PRE", "error", 4)]},
                expect=False,
            ),
            WorldState(
                returns={"passed": False, "session_passed": [], "outputs": [], "diagnostics": [("DOC-PRE", "error", 5)]},
                expect=False,
            ),
        ],
        custom_id="doc_rule_edge_scanner_pre_traps",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: FENCE-KOLLISIONEN, MEHRFACH-FENCES, KOMMA-TAGS & SUMMARY-LOSE DETAILS (CLUSTER C3)
# ======================================================================================================================


def test_ebt_inner_backticks_double_fences_comma_tags_and_summaryless_details() -> None:
    """Verifies summaryless details and flags inner fence closing, double fences, and ignored comma tags."""
    EBT(
        target=_run_edge_scenario,
        pre=WorldState(args=(_SUMMARYLESS_DETAILS_AND_INDENTED_FENCE_DOC,)),
        post=WorldState(
            returns={
                "passed": True,
                "session_passed": [True],
                "outputs": [["clean_indent"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_rule_edge_summaryless_details_positive",
    ).run()

    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_FENCE_IN_MULTILINE_STR_DOC,)),
            WorldState(args=(_TWO_FENCES_IN_DETAILS_DOC,)),
            WorldState(args=(_COMMA_TAG_IGNORED_DOC,)),
        ],
        post=[
            WorldState(
                returns={"passed": True, "session_passed": [True], "outputs": [["4"]], "diagnostics": []}
            ),
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [["ok"]],
                    "diagnostics": [("DOC-OUT", "error", 3)],
                }
            ),
            WorldState(
                returns={"passed": True, "session_passed": [True], "outputs": [["1"]], "diagnostics": []}
            ),
        ],
        custom_id="doc_rule_edge_fences_and_comma_tags",
    ).run()


# ======================================================================================================================
# 6. ÄQUIVALENZKLASSE: BASE-EXCEPTION CATCH, DOTTED RAISES, PRINT VOR EXCEPTION & STRIP (CLUSTER D2 & D4)
# ======================================================================================================================


def test_ebt_base_exception_catch_dotted_raises_and_whitespace_stripping() -> None:
    """Verifies KeyboardInterrupt capture, dotted raises support, and preserved leading whitespace."""
    EBT(
        target=_capture_base_exception,
        pre=WorldState(args=(_KEYBOARD_INTERRUPT_DOC,)),
        post=WorldState(returns=("NO_ESCAPE", "")),
        custom_id="doc_rule_edge_keyboard_interrupt_captured",
    ).run()

    EBT(
        target=_run_edge_scenario,
        pre=WorldState(args=(_PRINT_BEFORE_RAISES_DOC,)),
        post=WorldState(
            returns={
                "passed": True,
                "session_passed": [True],
                "outputs": [["ValueError: boom"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_rule_edge_print_before_raises_positive",
    ).run()

    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_KEYBOARD_INTERRUPT_DOC,)),
            WorldState(args=(_DOTTED_RAISES_DOC,)),
            WorldState(args=(_LEADING_WHITESPACE_STRIP_DOC,)),
        ],
        post=[
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["KeyboardInterrupt: ctrl-c"]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["ValueError: boom"]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [["   indented_first\n  indented_second"]],
                    "diagnostics": [("DOC-OUT", "error", 3)],
                }
            ),
        ],
        custom_id="doc_rule_edge_dotted_raises_and_strip_preserved",
    ).run()


# ======================================================================================================================
# 7. ÄQUIVALENZKLASSE: MULTI-STEP SESSION MIT MYPY/NO-OUTPUT & CST-LINTER MERGE (BEFUNDE 1 & 2)
# ======================================================================================================================


def test_ebt_session_mypy_integration_no_output_and_cst_linter_merge() -> None:
    """Verifies cross-step MyPy session linting, NoOutput warning on empty setup step, and CstLinter merging."""
    dual_cst = [CstLinter(rules=[_NoEvalCstRule()]), CstLinter(rules=[_NoPrintCstRule()])]
    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_SESSION_MYPY_AND_NO_OUTPUT_DOC,), kwargs={"rules": [*CUBIE_DOC_RULES, MyPy()]}),
            WorldState(args=(_EVAL_AND_PRINT_DOC,), kwargs={"rules": dual_cst}),
        ],
        post=[
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["", "42"]],
                    "diagnostics": [("DOC-NO-OUTPUT", "warning", 3)],
                }
            ),
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [["42"]],
                    "diagnostics": [("CST-NO-EVAL", "error", 4), ("CST-NO-PRINT", "error", 4)],
                }
            ),
        ],
        custom_id="doc_rule_edge_session_mypy_and_cst_merge",
    ).run()

    # AstLinter fulfills Linter protocol and runs orthogonally alongside CUBIE_DOC_RULES and custom rules
    ast_combo = [*CUBIE_DOC_RULES, AstLinter(CstLinter(rules=[_NoEvalCstRule()])), ExplanationRule(
        "EXP-NO-TODO", "Explanation contains TODO.", lambda s: "TODO" not in s
    )]
    EBT(
        target=_run_edge_scenario,
        pre=WorldState(args=(_EVAL_AND_PRINT_DOC,), kwargs={"rules": ast_combo}),
        post=WorldState(
            returns={
                "passed": False,
                "session_passed": [False],
                "outputs": [["42"]],
                "diagnostics": [("CST-NO-EVAL", "error", 4)],
            }
        ),
        custom_id="doc_rule_edge_ast_linter_orthogonal",
    ).run()


# ======================================================================================================================
# 8. ÄQUIVALENZKLASSE: <DETAILS>-HTML-INJEKTION IM OUTPUT & ROHE SYNTAXERROR-SNIPPETS (BEFUNDE 3 & 4)
# ======================================================================================================================


def test_ebt_details_html_injection_and_raw_syntax_error_behavior() -> None:
    """Verifies fence-safe details extraction, line-invariant <doc> SyntaxError, and active CstLinter E999."""
    EBT(
        target=_run_edge_scenario,
        pre=WorldState(args=(_RAW_SYNTAX_ERROR_DOC,)),
        post=WorldState(
            returns={
                "passed": True,
                "session_passed": [True],
                "outputs": [["SyntaxError: invalid syntax (<doc>, line 1)"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_rule_edge_raw_syntax_error_baseline",
    ).run()

    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_HTML_SUMMARY_IN_OUTPUT_DOC,)),
            WorldState(args=(_HTML_CLOSING_DETAILS_IN_OUTPUT_DOC,)),
            WorldState(args=(_HTML_SUMMARY_WITH_ATTR_DOC,)),
            WorldState(args=("\n" + _RAW_SYNTAX_ERROR_DOC,)),
            WorldState(args=(_RAW_SYNTAX_ERROR_DOC,), kwargs={"rules": [CstLinter(rules=[])]}),
        ],
        post=[
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["<summary>Inner</summary>"]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["</details>"]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["ok"]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["SyntaxError: invalid syntax (<doc>, line 1)"]],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [["SyntaxError: invalid syntax (<doc>, line 1)"]],
                    "diagnostics": [("E999", "error", 4)],
                }
            ),
        ],
        custom_id="doc_rule_edge_details_html_and_raw_syntax_error",
    ).run()