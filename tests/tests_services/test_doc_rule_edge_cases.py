"""Verifies rule coercion, scanner traps, scope asymmetries, and runtime edge cases in DocEnsurance."""

from collections.abc import Sequence
from typing import Any

import libcst as cst

from qb_cubie import EBT, CstLinter, CstRule, ExceptionExpectation, TempFS, WorldState
from qb_cubie.services import (
    CUBIE_DOC_STYLE,
    CodeRule,
    CodeSnippet,
    CollapsibleResult,
    DocEnsurance,
    ExamplePattern,
    Explanation,
    ExplanationRule,
    IsolatedScope,
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
    "```python\n"
    'md = """\n'
    "```\n"
    "hello\n"
    "```\n"
    '"""\n'
    "print(len(md.splitlines()))\n"
    "```\n\n"
    "<details><summary>R</summary>\n\n```text\n3\n```\n</details>"
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
        if isinstance(node.func, cst.Name) and node.func.value == "print":
            self.add_diagnostic(node, "CST-NO-PRINT", "print() flagged.")


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
) -> dict[str, Any]:
    """Executes DocEnsurance and projects session states, outputs, and diagnostics."""
    service = DocEnsurance(
        target=doc, pattern=pattern, scope=scope or TaggedScope(), arena=TempFS(), reporter=None
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


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: REGEL-COERCION & DEFAULT-REDUKTION (CLUSTER A2)
# ======================================================================================================================


def test_ebt_rule_defaults_reduction_and_type_coercion() -> None:
    """Verifies rules=None vs rules=() defaults, 0-arg class coercion, and CstLinter type failure."""
    custom_noop = CodeRule("C1", "noop", lambda _: True)
    EBT(
        target=_inspect_rule_registry,
        pre=[
            WorldState(args=(_SILENT_EMPTY_OUT_DOC, None)),
            WorldState(args=(_SILENT_EMPTY_OUT_DOC, ())),
            WorldState(args=(_SILENT_EMPTY_OUT_DOC, [custom_noop])),
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
            WorldState(returns={"rule_ids": ["DOC-OUT", "C1"], "passed": True, "diag_ids": []}),
            WorldState(
                returns={
                    "rule_ids": ["DOC-OUT", "DOC-NO-OUTPUT"],
                    "passed": True,
                    "diag_ids": [("DOC-NO-OUTPUT", "warning")],
                }
            ),
            WorldState(
                returns={
                    "rule_ids": ["DOC-OUT", "DOC-LINT:CST-Linter"],
                    "passed": False,
                    "diag_ids": [("DOC-OUT", "warning"), ("CST-NO-PRINT", "error")],
                }
            ),
        ],
        custom_id="doc_rule_edge_defaults_and_coercion",
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
    """Verifies that DOC-PRE warning skips ExplanationRule until min_chars is met, and allows override."""
    warn_override = ExplanationRule("EXP-CAP", "Must start uppercase.", lambda s: s[0].isupper(), severity="warning")
    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_SHORT_LOWERCASE_PRE_DOC, _WARN_PRE_WITH_EXP_RULE_PATTERN)),
            WorldState(args=(_LONG_LOWERCASE_PRE_DOC, _WARN_PRE_WITH_EXP_RULE_PATTERN)),
            WorldState(
                args=(_LONG_LOWERCASE_PRE_DOC, _WARN_PRE_WITH_EXP_RULE_PATTERN),
                kwargs={"extra_registered": [warn_override]},
            ),
        ],
        post=[
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["1"]],
                    "diagnostics": [("DOC-PRE", "warning", 3)],
                }
            ),
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
        custom_id="doc_rule_edge_pre_warning_skips_exp_rule_and_override",
    ).run()


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: ASYMMETRIE BEI DOC-PRE IN SESSIONS: TAGGED VS. ISOLATED SCOPE (CLUSTER D3.1)
# ======================================================================================================================


def test_ebt_session_doc_pre_asymmetry_tagged_vs_isolated_scope() -> None:
    """Verifies that TaggedScope executes DOC-PRE session steps while IsolatedScope drops them."""
    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_SESSION_DOC_PRE_ASYMMETRY_DOC, CUBIE_DOC_STYLE, TaggedScope())),
            WorldState(args=(_SESSION_DOC_PRE_ASYMMETRY_DOC, CUBIE_DOC_STYLE, IsolatedScope())),
        ],
        post=[
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [True],
                    "outputs": [["42", "43"]],
                    "diagnostics": [("DOC-PRE", "error", 3)],
                }
            ),
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [[""]],
                    "diagnostics": [("DOC-PRE", "error", 3), ("DOC-EXEC", "error", 17)],
                }
            ),
        ],
        custom_id="doc_rule_edge_session_pre_scope_asymmetry",
    ).run()


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: MARKDOWN-SCANNER NACHBARSCHAFTS-FALLEN (CLUSTER C1 & C2)
# ======================================================================================================================


def test_ebt_lazy_list_continuation_alert_and_html_comment_traps() -> None:
    """Verifies that lazy list paragraphs, GitHub alerts, and HTML comments trigger DOC-PRE."""
    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_LAZY_LIST_CONTINUATION_DOC,)),
            WorldState(args=(_GITHUB_ALERT_PRE_DOC,)),
            WorldState(args=(_HTML_COMMENT_DISPLACES_PRE_DOC,)),
        ],
        post=[
            WorldState(
                returns={"passed": False, "session_passed": [], "outputs": [], "diagnostics": [("DOC-PRE", "error", 4)]}
            ),
            WorldState(
                returns={"passed": False, "session_passed": [], "outputs": [], "diagnostics": [("DOC-PRE", "error", 4)]}
            ),
            WorldState(
                returns={"passed": False, "session_passed": [], "outputs": [], "diagnostics": [("DOC-PRE", "error", 5)]}
            ),
        ],
        custom_id="doc_rule_edge_scanner_pre_traps",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: FENCE-KOLLISIONEN, MEHRFACH-FENCES, KOMMA-TAGS & SUMMARY-LOSE DETAILS (CLUSTER C3)
# ======================================================================================================================


def test_ebt_inner_backticks_double_fences_comma_tags_and_summaryless_details() -> None:
    """Verifies inner fence closing, multiple fences in details, comma tags, and summaryless details."""
    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_FENCE_IN_MULTILINE_STR_DOC,)),
            WorldState(args=(_TWO_FENCES_IN_DETAILS_DOC,)),
            WorldState(args=(_COMMA_TAG_IGNORED_DOC,)),
            WorldState(args=(_SUMMARYLESS_DETAILS_AND_INDENTED_FENCE_DOC,)),
        ],
        post=[
            WorldState(
                returns={"passed": False, "session_passed": [], "outputs": [], "diagnostics": [("DOC-POST", "error", 3)]}
            ),
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [["ok"]],
                    "diagnostics": [("DOC-OUT", "error", 3)],
                }
            ),
            WorldState(returns={"passed": True, "session_passed": [], "outputs": [], "diagnostics": []}),
            WorldState(
                returns={
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["clean_indent"]],
                    "diagnostics": [],
                }
            ),
        ],
        custom_id="doc_rule_edge_fences_comma_tags_and_details",
    ).run()


# ======================================================================================================================
# 6. ÄQUIVALENZKLASSE: BASE-EXCEPTION ESCAPE, DOTTED RAISES, PRINT VOR EXCEPTION & STRIP (CLUSTER D2 & D4)
# ======================================================================================================================


def _capture_base_exception(doc: str) -> tuple[str, str]:
    """Runs DocEnsurance and returns the class name and message of an escaping BaseException."""
    try:
        DocEnsurance(target=doc, arena=TempFS(), reporter=None).run()
    except BaseException as exc:  # noqa: BLE001
        return (type(exc).__name__, str(exc))
    return ("NO_ESCAPE", "")


def test_ebt_base_exception_escape_dotted_raises_and_whitespace_stripping() -> None:
    """Verifies KeyboardInterrupt escape, dotted raises failure, print before raises, and stdout strip."""
    EBT(
        target=_capture_base_exception,
        pre=WorldState(args=(_KEYBOARD_INTERRUPT_DOC,)),
        post=WorldState(returns=("KeyboardInterrupt", "ctrl-c")),
        custom_id="doc_rule_edge_keyboard_interrupt_escapes",
    ).run()

    EBT(
        target=_run_edge_scenario,
        pre=[
            WorldState(args=(_DOTTED_RAISES_DOC,)),
            WorldState(args=(_PRINT_BEFORE_RAISES_DOC,)),
            WorldState(args=(_LEADING_WHITESPACE_STRIP_DOC,)),
        ],
        post=[
            WorldState(
                returns={
                    "passed": False,
                    "session_passed": [False],
                    "outputs": [["ValueError: boom"]],
                    "diagnostics": [("DOC-RAISE", "error", 3)],
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
                    "passed": True,
                    "session_passed": [True],
                    "outputs": [["indented_first\n  indented_second"]],
                    "diagnostics": [],
                }
            ),
        ],
        custom_id="doc_rule_edge_dotted_raises_print_discard_and_strip",
    ).run()
