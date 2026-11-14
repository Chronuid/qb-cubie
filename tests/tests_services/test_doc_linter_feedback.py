"""Verifies actionable, unswallowed linter diagnostics and end-to-end reporter UX in DocEnsurance."""

import re
import warnings
from collections.abc import Sequence
from typing import Any

import libcst as cst

from qb_cubie import (
    AstLinter,
    CstLinter,
    CstRule,
    EBT,
    MyPy,
    PytestReporter,
    TempFS,
    WorldState,
)
from qb_cubie.services import (
    CUBIE_DOC_RULES,
    CUBIE_DOC_STYLE,
    DocEnsurance,
    DocLinterRule,
)

# ---------- Test-Fixtures & Markdown-Korpus ---------------------------------------------------------------------------

_STALE_GUIDE_LINTER_DOC = (
    "Dieses Doku-Beispiel nutzt den veralteten Präfix AstLinter(CST-Linter) und verschluckt die Meldung.\n\n"
    "```python\n"
    "import libcst as cst\n"
    "from qb_cubie import AstLinter, CstLinter, CstRule\n\n"
    "class NoEvalArchRule(CstRule):\n"
    "    def visit_Call(self, node: cst.Call) -> None:\n"
    "        if isinstance(node.func, cst.Name) and node.func.value == 'eval':\n"
    "            self.add_diagnostic(node, 'ARCH-NO-EVAL', 'eval() verletzt die Sicherheitsarchitektur.')\n\n"
    "linter = AstLinter(CstLinter(rules=[NoEvalArchRule()]))\n"
    "diags = linter.check(\"x = 21\\nprint(eval('x * 2'))\\n\")\n"
    "print(f'Linter: {linter.name} | Code: {diags[0].rule_id} | Zeile: {diags[0].line}')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    "```text\nLinter: AstLinter(CST-Linter) | Code: ARCH-NO-EVAL | Zeile: 2\n```\n</details>"
)

_ACTIONABLE_GUIDE_LINTER_DOC = (
    "Dieses Doku-Beispiel gibt Linter-Name, Regel-Code, Zeile und die konkrete Linter-Meldung aus.\n\n"
    "```python\n"
    "import libcst as cst\n"
    "from qb_cubie import AstLinter, CstLinter, CstRule\n\n"
    "class NoEvalArchRule(CstRule):\n"
    "    def visit_Call(self, node: cst.Call) -> None:\n"
    "        if isinstance(node.func, cst.Name) and node.func.value == 'eval':\n"
    "            self.add_diagnostic(node, 'ARCH-NO-EVAL', 'eval() verletzt die Sicherheitsarchitektur.')\n\n"
    "linter = AstLinter(CstLinter(rules=[NoEvalArchRule()]))\n"
    "diags = linter.check(\"x = 21\\nprint(eval('x * 2'))\\n\")\n"
    "d = diags[0]\n"
    "print(f'{linter.name} | {d.rule_id} (Zeile {d.line}): {d.message}')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n"
    "```text\n"
    "AST-Linter(CST-Linter) | ARCH-NO-EVAL (Zeile 2): eval() verletzt die Sicherheitsarchitektur.\n"
    "```\n</details>"
)

_EVAL_VIOLATION_DOC = (
    "Diese Erklärung beschreibt das Berechnungsbeispiel mit mindestens zwanzig Zeichen.\n\n"
    "```python\n"
    "x = 21\n"
    "print(eval('x * 2'))\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
)

_EVAL_AND_OUT_MISMATCH_DOC = (
    "Dieses Beispiel hat sowohl einen falschen Ergebnis-Block als auch einen Linter-Verstoß.\n\n"
    "```python\n"
    "x = 21\n"
    "print(eval('x * 2'))\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n99\n```\n</details>"
)

_UNEXPLAINED_EVAL_DOC = (
    "Zu kurz.\n\n"
    "```python\n"
    "x = 21\n"
    "print(eval('x * 2'))\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
)

_SESSION_MULTISTEP_LINT_DOC = (
    "Schritt 1 legt den Basiswert typisiert in der gemeinsamen Session an.\n\n"
    "```python session=lint_ux\n"
    "factor: int = 21\n"
    "print(factor)\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n21\n```\n</details>\n\n"
    "Schritt 2 nutzt factor aus Schritt 1, verletzt aber in Zeile 16 die eval-Architekturregel.\n\n"
    "```python session=lint_ux\n"
    "doubled = factor * 2\n"
    "print(eval('doubled'))\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\n42\n```\n</details>"
)


class _NoEvalArchRule(CstRule):
    """Flags eval() calls with an actionable architectural explanation."""

    def visit_Call(self, node: cst.Call) -> None:
        """Records an ARCH-NO-EVAL diagnostic with a concrete security message."""
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(
                node, "ARCH-NO-EVAL", "eval() verletzt die Sicherheitsarchitektur."
            )


# ---------- Stateless Test-Adapter ------------------------------------------------------------------------------------


def _run_linter_ux_scenario(
    doc: str, rules: Sequence[Any] | None = None
) -> dict[str, Any]:
    """Executes DocEnsurance and returns full diagnostic tuples including concrete messages."""
    report = DocEnsurance(
        target=doc,
        pattern=CUBIE_DOC_STYLE,
        rules=rules,
        arena=TempFS(),
        reporter=None,
    ).run()
    return {
        "passed": report.passed,
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "diagnostics": [
            (d.rule_id, d.severity, d.line, d.message) for d in report.diagnostics
        ],
    }


def _run_pytest_reporter_ux(
    doc: str, rules: Sequence[Any] | None = None
) -> dict[str, Any]:
    """Runs DocEnsurance with PytestReporter and captures both UserWarnings and AssertionError text."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        try:
            DocEnsurance(
                target=doc, pattern=CUBIE_DOC_STYLE, rules=rules, arena=TempFS(), reporter=PytestReporter()
            ).run()
            error_text = ""
        except AssertionError as exc:
            error_text = str(exc)
    warn_list = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
    return {"asserted": bool(error_text), "error_text": error_text, "warnings": warn_list}


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: REPRODUKTION DES GUIDE-SZENARIOS (AST-LINTER-PRÄFIX & KONKRETE LINTER-MELDUNG)
# ======================================================================================================================


def test_ebt_guide_scenario_reproduction_and_actionable_output() -> None:
    """Reproduces the AstLinter vs AST-Linter DOC-OUT trap and enforces concrete message output."""
    # 1a. Szenario von eben: Veraltetes 'AstLinter(CST-Linter)' ohne Message fällt mit DOC-OUT durch
    EBT(
        target=_run_linter_ux_scenario,
        pre=WorldState(args=(_STALE_GUIDE_LINTER_DOC, CUBIE_DOC_RULES)),
        post=[
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["Linter: AST-Linter(CST-Linter) | Code: ARCH-NO-EVAL | Zeile: 2"]],
                    "diagnostics": [
                        (
                            "DOC-OUT",
                            "error",
                            14,
                            re.compile(r"expected 'Linter: AstLinter\(CST-Linter\).*got 'Linter: AST-Linter\(CST-Linter\)"),
                        )
                    ],
                }
            ),
            WorldState(
                returns={"passed": True, "outputs": list, "diagnostics": []},
                expect=False,
            ),
        ],
        custom_id="doc_linter_ux_stale_guide_scenario_reproduction",
    ).run()

    # 1b. Soll-Zustand: Korrekter Präfix + konkrete Linter-Erklärung im Output (verschweigt Message NICHT)
    EBT(
        target=_run_linter_ux_scenario,
        pre=WorldState(args=(_ACTIONABLE_GUIDE_LINTER_DOC, CUBIE_DOC_RULES)),
        post=[
            WorldState(
                returns={
                    "passed": True,
                    "outputs": [
                        ["AST-Linter(CST-Linter) | ARCH-NO-EVAL (Zeile 2): eval() verletzt die Sicherheitsarchitektur."]
                    ],
                    "diagnostics": [],
                }
            ),
            WorldState(
                returns={
                    "passed": True,
                    "outputs": [["Linter: AST-Linter(CST-Linter) | Code: ARCH-NO-EVAL | Zeile: 2"]],
                    "diagnostics": [],
                },
                expect=False,
            ),
        ],
        custom_id="doc_linter_ux_actionable_guide_output",
    ).run()


# ======================================================================================================================
# 2. ÄQUIVALENZKLASSE: UNGEKÜRZTE LINTER-MELDUNGEN IN DOC-ENSURANCE (`AstLinter` & `CstLinter`)
# ======================================================================================================================


def test_ebt_ast_and_cst_linter_preserve_concrete_messages_and_lines() -> None:
    """Verifies that AstLinter and CstLinter preserve the full rule message and exact Markdown line."""
    ast_linter = AstLinter(CstLinter(rules=[_NoEvalArchRule()]))
    EBT(
        target=_run_linter_ux_scenario,
        pre=WorldState(args=(_EVAL_VIOLATION_DOC, [ast_linter])),
        post=[
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["42"]],
                    "diagnostics": [
                        ("ARCH-NO-EVAL", "error", 5, "eval() verletzt die Sicherheitsarchitektur.")
                    ],
                }
            ),
            # Negativ-Abgrenzung (expect=False): Leere, verschluckte oder nur den Code wiederholende Meldung
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["42"]],
                    "diagnostics": [("ARCH-NO-EVAL", "error", 5, "")],
                },
                expect=False,
            ),
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["42"]],
                    "diagnostics": [("ARCH-NO-EVAL", "error", 5, "ARCH-NO-EVAL")],
                },
                expect=False,
            ),
        ],
        custom_id="doc_linter_ux_concrete_message_preservation",
    ).run()


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: KEIN VERSCHLUCKEN DER LINTER-MELDUNG DURCH DOC-OUT ODER DOC-PRE (ORTHOGONALITÄT)
# ======================================================================================================================


def test_ebt_structural_or_output_errors_never_swallow_linter_diagnostics() -> None:
    """Verifies that DOC-OUT and DOC-PRE errors do not mute or swallow concrete linter messages."""
    ast_linter = AstLinter(CstLinter(rules=[_NoEvalArchRule()]))
    EBT(
        target=_run_linter_ux_scenario,
        pre=[
            WorldState(args=(_EVAL_AND_OUT_MISMATCH_DOC, [ast_linter])),
            WorldState(args=(_UNEXPLAINED_EVAL_DOC, [ast_linter])),
        ],
        post=[
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["42"]],
                    "diagnostics": [
                        ("DOC-OUT", "error", 3, re.compile(r"^Output mismatch: expected '99', got '42'")),
                        ("ARCH-NO-EVAL", "error", 5, "eval() verletzt die Sicherheitsarchitektur."),
                    ],
                }
            ),
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [],
                    "diagnostics": [
                        ("DOC-PRE", "error", 3, re.compile(r"Missing or invalid pre-block")),
                        ("ARCH-NO-EVAL", "error", 5, "eval() verletzt die Sicherheitsarchitektur."),
                    ],
                }
            ),
            # Negativ-Abgrenzung (expect=False): DOC-OUT oder DOC-PRE verschluckt die Linter-Meldung
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["42"]],
                    "diagnostics": [
                        ("DOC-OUT", "error", 3, re.compile(r"^Output mismatch")),
                    ],
                },
                expect=False,
            ),
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [],
                    "diagnostics": [
                        ("DOC-PRE", "error", 3, re.compile(r"Missing or invalid pre-block")),
                    ],
                },
                expect=False,
            ),
        ],
        custom_id="doc_linter_ux_no_muting_by_out_or_pre",
    ).run()


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: MULTI-STEP SESSION LINTER-UX (KONTEXT-ERHALT + EXAKTE ZEILEN-RÜCKRECHNUNG)
# ======================================================================================================================


def test_ebt_multistep_session_linter_preserves_context_and_concrete_message() -> None:
    """Verifies that multi-step sessions keep step-1 types in MyPy and report step-2 linter messages."""
    combined_linter = AstLinter(CstLinter(rules=[_NoEvalArchRule()]), MyPy())
    EBT(
        target=_run_linter_ux_scenario,
        pre=WorldState(args=(_SESSION_MULTISTEP_LINT_DOC, [*CUBIE_DOC_RULES, combined_linter])),
        post=[
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["21", "42"]],
                    "diagnostics": [
                        ("ARCH-NO-EVAL", "error", 16, "eval() verletzt die Sicherheitsarchitektur.")
                    ],
                }
            ),
            # Negativ-Abgrenzung (expect=False): Falscher 'name-defined'-Alarm oder falsche Zeilennummer
            WorldState(
                returns={
                    "passed": False,
                    "outputs": [["21", "42"]],
                    "diagnostics": [
                        ("name-defined", "error", int, str),
                        ("ARCH-NO-EVAL", "error", int, str),
                    ],
                },
                expect=False,
            ),
        ],
        custom_id="doc_linter_ux_multistep_session_context_and_line",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: END-TO-END NUTZERERFAHRUNG AM PYTEST-REPORTER (ERROR-ASSERTION & USER-WARNING)
# ======================================================================================================================


def test_ebt_pytest_reporter_surfaces_concrete_linter_messages_end_to_end() -> None:
    """Verifies that PytestReporter includes rule_id, file, line, and concrete linter message."""
    err_linter = AstLinter(CstLinter(rules=[_NoEvalArchRule()]))
    warn_linter = DocLinterRule(linter=err_linter, severity="warning")
    EBT(
        target=_run_pytest_reporter_ux,
        pre=[
            WorldState(args=(_EVAL_VIOLATION_DOC, [err_linter])),
            WorldState(args=(_EVAL_VIOLATION_DOC, [warn_linter])),
        ],
        post=[
            WorldState(
                returns={
                    "asserted": True,
                    "error_text": re.compile(
                        r"--- Service Report \(IN_MEMORY\) ---[\s\S]*"
                        r"- \[ARCH-NO-EVAL\] IN_MEMORY:5: eval\(\) verletzt die Sicherheitsarchitektur\."
                    ),
                    "warnings": [],
                }
            ),
            WorldState(
                returns={
                    "asserted": False,
                    "error_text": "",
                    "warnings": [
                        "[ARCH-NO-EVAL] IN_MEMORY:5: eval() verletzt die Sicherheitsarchitektur."
                    ],
                }
            ),
            # Negativ-Abgrenzung (expect=False): AssertionError ohne die konkrete Linter-Meldung
            WorldState(
                returns={
                    "asserted": True,
                    "error_text": re.compile(r"^((?!eval\(\) verletzt die Sicherheitsarchitektur\.).)*$"),
                    "warnings": [],
                },
                expect=False,
            ),
        ],
        custom_id="doc_linter_ux_pytest_reporter_end_to_end",
    ).run()