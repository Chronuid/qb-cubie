"""Verifies pluggable rules, linter adapters, and severity contracts in DocEnsurance."""

import re
import warnings
from typing import Any, Sequence

import libcst as cst

from qb_cubie import CstLinter, CstRule, EBT, ExceptionExpectation, PytestReporter, TempFS, WorldState
from qb_cubie.services import (
    CUBIE_DOC_STYLE,
    CodeRule,
    CodeSnippet,
    CollapsibleResult,
    DocDiagnostic,
    DocEnsurance,
    DocLinterRule,
    ExamplePattern,
    Explanation,
    ExplanationRule,
    IsolatedScope,
    MissingOutputRule,
    OutputMatchRule,
    OutputRule,
    TaggedScope,
)

# ---------- Test-Fixtures & Markdown-Korpus ---------------------------------------------------------------------------

_CLEAN_DOC = (
    "Diese Erklärung beschreibt ein sauberes Beispiel ohne Regelverstöße.\n\n"
    "```python\n"
    "value = 21 * 2\n"
    "print(value)\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
)

_RULE_VIOLATION_DOC = (
    "TODO: Diese Erklärung enthält noch einen offenen Marker.\n\n"
    "```python session=alpha\n"
    "x = 40 + 2\n"
    "print(eval('x'))\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
)

_EMPTY_RESULT_BLOCK_DOC = (
    "Dieses Beispiel gibt Text aus, hat aber noch einen leeren Ergebnis-Block.\n\n"
    "```python\n"
    "print('computed_42')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n```\n</details>"
)

_MISSING_BLOCKS_DOC = (
    "Zu kurz.\n\n"
    "```python\n"
    "print(21 * 2)\n"
    "```\n\n"
    "Normaler Absatz statt eines einklappbaren Ergebnis-Blocks."
)


class _ForbidEvalCstRule(CstRule):
    """Flags calls to eval() inside documentation code snippets."""

    def visit_Call(self, node: cst.Call) -> None:
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(node, "CST-NO-EVAL", "Use of eval() is forbidden in docs.")


def _run_rules_scenario(
    doc: str,
    rules: Sequence[Any] | None = None,
    pattern: ExamplePattern = CUBIE_DOC_STYLE,
    scope: Any = None,
    extra_registered: Sequence[Any] = (),
) -> dict[str, Any]:
    """Runs DocEnsurance with configured rules and projects the report for EBT."""
    service = DocEnsurance(
        target=doc,
        pattern=pattern,
        scope=scope or TaggedScope(),
        arena=TempFS(),
        reporter=None,
        rules=rules,
    )
    if extra_registered:
        service.register_rule(*extra_registered)
    report = service.run()
    return {
        "passed": report.passed,
        "session_count": len(report.sessions),
        "session_passed": [s.passed for s in report.sessions],
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "diagnostics": [
            (d.rule_id, d.severity, d.line, d.session_id, d.message)
            for d in report.diagnostics
        ],
    }


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: PLUGGABLE CHECKS FÜR ERKLÄRUNG, CODE & AUSGABE (INKL. SEVERITY)
# ======================================================================================================================
def test_ebt_custom_explanation_code_and_output_rules() -> None:
    """
    Gesetz:
    1. Benutzerdefinierte Regeln für Erklärung (ExplanationRule), Code (CodeRule) und
       Ausgabe (OutputRule) lassen sich via `rules=[...]` oder `.register_rule(...)` einhängen.
    2. Haben alle ausgelösten Regeln `severity='warning'`, bleibt `passed` auf `True`.
    3. Sobald mindestens eine ausgelöste Regel `severity='error'` besitzt, wird `passed` `False`.
    """
    no_todo_warn = ExplanationRule(
        rule_id="DOC-EXP-TODO",
        message="Explanation contains TODO.",
        check_fn=lambda text: "TODO" not in text,
        severity="warning",
    )
    no_eval_warn = CodeRule(
        rule_id="DOC-CODE-EVAL",
        message="Code contains eval().",
        check_fn=lambda code: "eval(" not in code,
        severity="warning",
    )
    output_not_42_err = OutputRule(
        rule_id="DOC-OUT-FORBIDDEN",
        message="Output '42' is reserved.",
        check_fn=lambda exp, act: act != "42",
        severity="error",
    )

    # 1a. Sauberes Dokument besteht alle drei Regeln ohne Diagnose
    EBT(
        target=_run_rules_scenario,
        pre=WorldState(args=(_CLEAN_DOC, [no_todo_warn, no_eval_warn])),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "session_passed": [True],
                "outputs": [["42"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_rules_clean_pass",
    ).run()

    # 1b. Nur Warnungen (Explanation + Code) -> Lauf und Session bestehen (passed=True)
    EBT(
        target=_run_rules_scenario,
        pre=WorldState(
            args=(_RULE_VIOLATION_DOC, [no_todo_warn]),
            kwargs={"extra_registered": [no_eval_warn]},
        ),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "session_passed": [True],
                "outputs": [["42"]],
                "diagnostics": [
                    ("DOC-EXP-TODO", "warning", 3, "IN_MEMORY::session:alpha", "Explanation contains TODO."),
                    ("DOC-CODE-EVAL", "warning", 3, "IN_MEMORY::session:alpha", "Code contains eval()."),
                ],
            }
        ),
        custom_id="doc_rules_warnings_keep_passed_true",
    ).run()

    # 1c. Kombination aus Warnungen + einer Error-Regel -> Lauf schlägt fehl (passed=False)
    EBT(
        target=_run_rules_scenario,
        pre=WorldState(
            args=(_RULE_VIOLATION_DOC, [no_todo_warn, no_eval_warn, output_not_42_err])
        ),
        post=WorldState(
            returns={
                "passed": False,
                "session_count": 1,
                "session_passed": [False],
                "outputs": [["42"]],
                "diagnostics": [
                    ("DOC-EXP-TODO", "warning", 3, "IN_MEMORY::session:alpha", str),
                    ("DOC-CODE-EVAL", "warning", 3, "IN_MEMORY::session:alpha", str),
                    ("DOC-OUT-FORBIDDEN", "error", 3, "IN_MEMORY::session:alpha", str),
                ],
            }
        ),
        custom_id="doc_rules_error_flips_passed_false",
    ).run()


# ======================================================================================================================
# 2. ÄQUIVALENZKLASSE: FEHLENDE ERGEBNIS-AUSGABEN (WARNING VS. ERROR) & REGEL-DEDUPLIZIERUNG
# ======================================================================================================================
def test_ebt_missing_output_rule_severity_and_override() -> None:
    """
    Gesetz:
    1. Mit `MissingOutputRule(severity='warning')` erzeugt ein leerer <details>-Block
       lediglich eine Warnung (`DOC-OUT-MISSING`), ohne dass `DOC-OUT` als harter Fehler feuert.
    2. Wird `MissingOutputRule(severity='error')` übergeben oder per `.register_rule()`
       nachregistriert, überschreibt sie die gleichnamige Regel (`rule_id='DOC-OUT-MISSING'`)
       und erzwingt einen harten Fehlschlag (`passed=False`).
    """
    # 2a. Default der MissingOutputRule ist 'warning' -> passed=True trotz Ausgabe 'computed_42'
    EBT(
        target=_run_rules_scenario,
        pre=WorldState(args=(_EMPTY_RESULT_BLOCK_DOC, [MissingOutputRule()])),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "session_passed": [True],
                "outputs": [["computed_42"]],
                "diagnostics": [
                    ("DOC-OUT-MISSING", "warning", 3, str, re.compile(r"Missing expected output")),
                ],
            }
        ),
        custom_id="doc_rules_missing_output_warning_default",
    ).run()

    # 2b. Überschreiben derselben rule_id auf 'error' -> keine Duplikate, harter Fail
    EBT(
        target=_run_rules_scenario,
        pre=[
            WorldState(args=(_EMPTY_RESULT_BLOCK_DOC, [MissingOutputRule(severity="error")])),
            WorldState(
                args=(_EMPTY_RESULT_BLOCK_DOC, [MissingOutputRule(severity="warning")]),
                kwargs={"extra_registered": [MissingOutputRule(severity="error")]},
            ),
        ],
        post=WorldState(
            returns={
                "passed": False,
                "session_count": 1,
                "session_passed": [False],
                "outputs": [["computed_42"]],
                "diagnostics": [
                    ("DOC-OUT-MISSING", "error", 3, str, re.compile(r"Missing expected output")),
                ],
            }
        ),
        custom_id="doc_rules_missing_output_error_override",
    ).run()


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: BLOCK-LEVEL REGELN & STRUKTURELLE SEVERITIES (DOC-PRE / DOC-POST)
# ======================================================================================================================
def test_ebt_block_level_rules_and_structural_severities() -> None:
    """
    Gesetz:
    1. Werden `Explanation(severity='warning')` und `CollapsibleResult(severity='warning')`
       im Pattern deklariert, erzeugen fehlende/ungültige Nachbarblöcke `DOC-PRE`/`DOC-POST`
       mit `severity='warning'`, und das Anker-Snippet wird trotzdem ausgeführt.
    2. Direkt an Pattern-Blöcken befestigte `rules=(...)` werden automatisch übernommen.
    """
    soft_pattern = ExamplePattern(
        name="soft-structure-pattern",
        pre=(Explanation(min_chars=20, severity="warning"),),
        anchor=CodeSnippet(
            lang="python",
            rules=(
                CodeRule(
                    rule_id="BLOCK-ATTACHED-RULE",
                    message="Triggered from anchor block.",
                    check_fn=lambda code: "21" not in code,
                    severity="warning",
                ),
            ),
        ),
        post=(CollapsibleResult(severity="warning"),),
    )

    EBT(
        target=_run_rules_scenario,
        pre=WorldState(args=(_MISSING_BLOCKS_DOC, None, soft_pattern)),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "session_passed": [True],
                "outputs": [["42"]],
                "diagnostics": [
                    ("DOC-PRE", "warning", 3, None, re.compile(r".*explanation")),
                    ("DOC-POST", "warning", 3, None, re.compile(r".*result")),
                    ("BLOCK-ATTACHED-RULE", "warning", 3, str, "Triggered from anchor block."),
                ],
            }
        ),
        custom_id="doc_rules_soft_structural_blocks_and_attached_rules",
    ).run()


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: LINTER-ADAPTION (`CstLinter` & `DocLinterRule`) INKL. ZEILEN-OFFSET
# ======================================================================================================================
def test_ebt_cst_linter_integration_and_line_mapping() -> None:
    """
    Gesetz:
    1. Ein `Linter` (z. B. `CstLinter`) kann direkt in `rules=[...]` oder via `DocLinterRule`
       registriert werden.
    2. Die Zeilennummer eines Linter-Treffers im Snippet wird exakt auf die Startzeile des
       Code-Blocks im Markdown-Dokument aufaddiert (Fence in Zeile 3, `eval` in Snippet-Zeile 2 -> Zeile 5).
    3. `DocLinterRule(linter=..., severity='warning')` stuft Linter-Fehler auf Warnungen herab.
    """
    cst_linter = CstLinter(rules=[_ForbidEvalCstRule()])

    # 4a. Direkte Übergabe von CstLinter -> übernimmt 'error'-Severity -> passed=False, Zeile 5
    EBT(
        target=_run_rules_scenario,
        pre=WorldState(args=(_RULE_VIOLATION_DOC, [cst_linter])),
        post=WorldState(
            returns={
                "passed": False,
                "session_count": 1,
                "session_passed": [False],
                "outputs": [["42"]],
                "diagnostics": [
                    ("CST-NO-EVAL", "error", 5, "IN_MEMORY::session:alpha", "Use of eval() is forbidden in docs."),
                ],
            }
        ),
        custom_id="doc_rules_cst_linter_error_and_line_offset",
    ).run()

    # 4b. Gekapselt in DocLinterRule mit severity='warning' -> passed=True, Zeile 5
    EBT(
        target=_run_rules_scenario,
        pre=WorldState(
            args=(_RULE_VIOLATION_DOC, [DocLinterRule(linter=cst_linter, severity="warning")])
        ),
        post=WorldState(
            returns={
                "passed": True,
                "session_count": 1,
                "session_passed": [True],
                "outputs": [["42"]],
                "diagnostics": [
                    ("CST-NO-EVAL", "warning", 5, "IN_MEMORY::session:alpha", "Use of eval() is forbidden in docs."),
                ],
            }
        ),
        custom_id="doc_rules_cst_linter_warning_override",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: INTERAKTION MIT ISOLATED-SCOPE BEI WARNING VS. ERROR
# ======================================================================================================================
def test_ebt_isolated_scope_executes_warnings_but_drops_errors() -> None:
    """
    Gesetz: Im `IsolatedScope` werden Snippets mit strukturellen Warnungen (`severity='warning'`)
    weiterhin ausgeführt, während strukturelle Fehler (`severity='error'`) vor dem Arena-Lauf
    herausgefiltert werden.
    """
    warn_pre_pattern = ExamplePattern(
        pre=(Explanation(min_chars=20, severity="warning"),),
        anchor=CodeSnippet(lang="python"),
        post=(CollapsibleResult(severity="warning"),),
    )
    err_pre_pattern = ExamplePattern(
        pre=(Explanation(min_chars=20, severity="error"),),
        anchor=CodeSnippet(lang="python"),
        post=(CollapsibleResult(severity="warning"),),
    )

    EBT(
        target=_run_rules_scenario,
        pre=[
            WorldState(args=(_MISSING_BLOCKS_DOC, None, warn_pre_pattern, IsolatedScope())),
            WorldState(args=(_MISSING_BLOCKS_DOC, None, err_pre_pattern, IsolatedScope())),
        ],
        post=[
            WorldState(
                returns={
                    "passed": True,
                    "session_count": 1,
                    "session_passed": [True],
                    "outputs": [["42"]],
                    "diagnostics": [
                        ("DOC-PRE", "warning", 3, None, str),
                        ("DOC-POST", "warning", 3, None, str),
                    ],
                }
            ),
            WorldState(
                returns={
                    "passed": False,
                    "session_count": 0,
                    "session_passed": [],
                    "outputs": [],
                    "diagnostics": [
                        ("DOC-PRE", "error", 3, None, str),
                        ("DOC-POST", "warning", 3, None, str),
                    ],
                }
            ),
        ],
        custom_id="doc_rules_isolated_scope_severity_filtering",
    ).run()


# ======================================================================================================================
# 6. ÄQUIVALENZKLASSE: PYTEST-REPORTER VERTRAG (USER-WARNING VS. ASSERTION-ERROR)
# ======================================================================================================================
def _run_with_pytest_reporter(doc: str, rules: Sequence[Any]) -> dict[str, Any]:
    """Executes DocEnsurance with PytestReporter while capturing emitted UserWarnings."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        try:
            DocEnsurance(
                target=doc,
                rules=rules,
                arena=TempFS(),
                reporter=PytestReporter(),
            ).run()
            assertion_msg = None
        except AssertionError as error:
            assertion_msg = str(error)
    return {
        " asserted": assertion_msg is not None,
        "assertion_msg": assertion_msg,
        "warnings": [str(w.message) for w in caught if issubclass(w.category, UserWarning)],
    }


def test_ebt_pytest_reporter_emits_user_warnings_and_asserts_only_on_errors() -> None:
    """
    Gesetz:
    1. Enthält ein `DocReport` ausschließlich Diagnosen mit `severity='warning'`, gibt
       `PytestReporter` für jede Warnung eine `UserWarning` aus und wirft KEINEN `AssertionError`.
    2. Enthält der Report zusätzlich mindestens eine `'error'`-Diagnose, wird sowohl die
       `UserWarning` emittiert als auch `AssertionError` ausgelöst.
    """
    warn_rule = MissingOutputRule(severity="warning")
    err_rule = CodeRule(
        rule_id="DOC-CODE-STRICT",
        message="print is forbidden in strict mode.",
        check_fn=lambda code: "print(" not in code,
        severity="error",
    )

    EBT(
        target=_run_with_pytest_reporter,
        pre=[
            WorldState(args=(_EMPTY_RESULT_BLOCK_DOC, [warn_rule])),
            WorldState(args=(_EMPTY_RESULT_BLOCK_DOC, [warn_rule, err_rule])),
        ],
        post=[
            WorldState(
                returns={
                    " asserted": False,
                    "assertion_msg": None,
                    "warnings": [re.compile(r"^\[DOC-OUT-MISSING\] IN_MEMORY:3: Missing expected output")],
                }
            ),
            WorldState(
                returns={
                    " asserted": True,
                    "assertion_msg": re.compile(r"DOC-CODE-STRICT"),
                    "warnings": [re.compile(r"^\[DOC-OUT-MISSING\] IN_MEMORY:3: Missing expected output")],
                }
            ),
        ],
        custom_id="doc_rules_pytest_reporter_warnings_and_assertions",
    ).run()


# ======================================================================================================================
# 7. ÄQUIVALENZKLASSE: STATE-GUARDS FÜR UNGÜLTIGE SEVERITIES & UNGÜLTIGE REGEL-OBJEKTE
# ======================================================================================================================
def _construct_with_severity(kind: str, severity: Any) -> Any:
    """Helper to test severity validation across all dataclasses and rules."""
    factories = {
        "diagnostic": lambda s: DocDiagnostic("f.md", "R1", 1, "msg", severity=s),
        "explanation_block": lambda s: Explanation(severity=s),
        "code_block": lambda s: CodeSnippet(severity=s),
        "result_block": lambda s: CollapsibleResult(severity=s),
        "exp_rule": lambda s: ExplanationRule("R1", "msg", lambda _: True, severity=s),
        "code_rule": lambda s: CodeRule("R1", "msg", lambda _: True, severity=s),
        "out_rule": lambda s: OutputRule("R1", "msg", lambda _e, _a: True, severity=s),
        "missing_rule": lambda s: MissingOutputRule(severity=s),
        "match_rule": lambda s: OutputMatchRule(severity=s),
        "linter_rule": lambda s: DocLinterRule(CstLinter(rules=[]), severity=s),
    }
    return factories[kind](severity)


def test_ebt_severity_and_rule_type_state_guards() -> None:
    """
    Gesetz:
    1. Jede Severity außerhalb von `('error', 'warning')` wird sofort beim Instanziieren
       durch einen `ValueError('STATE-GUARD: severity ...')` abgewiesen.
    2. Ungültige Regel-Objekte in `DocEnsurance(rules=[...])` oder `.register_rule(...)`
       lösen sofort einen `TypeError('STATE-GUARD: Rule ...')` aus.
    """
    kinds = (
        "diagnostic", "explanation_block", "code_block", "result_block",
        "exp_rule", "code_rule", "out_rule", "missing_rule", "match_rule", "linter_rule",
    )
    EBT(
        target=_construct_with_severity,
        pre=[
            WorldState(args=(kind, bad_sev))
            for kind in kinds
            for bad_sev in ("info", "fatal", "", 123)
        ],
        post=WorldState(
            raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD: severity")
        ),
        custom_id="doc_rules_invalid_severity_state_guards",
    ).run()

    EBT(
        target=_run_rules_scenario,
        pre=[
            WorldState(args=(_CLEAN_DOC, ["not_a_rule"])),
            WorldState(args=(_CLEAN_DOC, [12345])),
            WorldState(args=(_CLEAN_DOC, None), kwargs={"extra_registered": [object()]}),
        ],
        post=WorldState(
            raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD: Rule")
        ),
        custom_id="doc_rules_invalid_rule_object_state_guards",
    ).run()