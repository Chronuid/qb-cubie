"""**Tries to** verify CUBIE_DOC_RULES and standard didactic rules (NoOutput, HighComplexity, LargeOutput, RawTraceback)."""

import re
import warnings
from collections.abc import Sequence
from typing import Any

from qb_cubie import EBT, ExceptionExpectation, PytestReporter, TempFS, WorldState
from qb_cubie.core.services import (
    CUBIE_DOC_RULES,
    CUBIE_DOC_STYLE,
    DocEnsurance,
    HighComplexity,
    LargeOutput,
    NoOutput,
    RawTraceback,
)


def _build_doc(code: str, expected_out: str = "42") -> str:
    """Builds a CUBIE_DOC_STYLE Markdown string from a code snippet and expected output."""
    body = f"{expected_out}\n" if expected_out else ""
    return (
        "Ausreichend lange Erklärung für das nachfolgende Code-Beispiel.\n\n"
        f"```python\n{code}\n```\n\n"
        f"<details>\n<summary>Ergebnis</summary>\n\n```text\n{body}```\n</details>"
    )


def _run_std_rules(
    doc: str,
    rules: Sequence[Any] = CUBIE_DOC_RULES,
    extra_registered: Sequence[Any] = (),
) -> dict[str, Any]:
    """Executes DocEnsurance with standard rules and returns a normalized EBT summary."""
    service = DocEnsurance(
        target=doc,
        pattern=CUBIE_DOC_STYLE,
        rules=rules,
        arena=TempFS(),
        reporter=None,
    )
    if extra_registered:
        service.register_rule(*extra_registered)
    report = service.run()
    return {
        "passed": report.passed,
        "outputs": [list(s.actual_outputs) for s in report.sessions],
        "diagnostics": [(d.rule_id, d.severity, d.message) for d in report.diagnostics],
    }


# ======================================================================================================================
# 1. ÄQUIVALENZKLASSE: CUBIE_DOC_RULES PRESET (CLEAN PASS VS. DIDAKTISCHE USER-WARNINGS)
# ======================================================================================================================
def _run_preset_with_pytest_reporter(doc: str) -> dict[str, Any]:
    """Runs DocEnsurance with CUBIE_DOC_RULES and PytestReporter while recording warnings."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        report = DocEnsurance(
            target=doc,
            pattern=CUBIE_DOC_STYLE,
            rules=CUBIE_DOC_RULES,
            arena=TempFS(),
            reporter=PytestReporter(),
        ).run()
    return {
        "passed": report.passed,
        "warning_count": len([w for w in caught if issubclass(w.category, UserWarning)]),
        "rule_ids": [d.rule_id for d in report.diagnostics],
    }


def test_ebt_cubie_doc_rules_preset_clean_and_multi_warning_execution() -> None:
    """
    Gesetz:
    1. Ein kompaktes Code-Beispiel (<= 30 Zeilen) mit dokumentierter Ausgabe (<= 25 Zeilen)
       besteht `CUBIE_DOC_RULES` komplett ohne Warnungen.
    2. Triggern `NoOutput` und `LargeOutput` im Standard-Preset `CUBIE_DOC_RULES`,
       emittiert `PytestReporter` entsprechende `UserWarning`s, ohne den Lauf abzubrechen (`passed=True`).
    """
    clean_doc = _build_doc("value = 21 * 2\nprint(value)", "42")
    noisy_doc = _build_doc("for i in range(26):\n    print(i)", "")

    EBT(
        target=_run_preset_with_pytest_reporter,
        pre=WorldState(args=(clean_doc,)),
        post=WorldState(
            returns={"passed": True, "warning_count": 0, "rule_ids": []}
        ),
        custom_id="doc_std_rules_preset_clean_execution",
    ).run()
    EBT(
        target=_run_preset_with_pytest_reporter,
        pre=WorldState(args=(noisy_doc,)),
        post=WorldState(
            returns={
                "passed": True,
                "warning_count": 2,
                "rule_ids": ["DOC-NO-OUTPUT", "DOC-LARGE-OUTPUT"],
            }
        ),
        custom_id="doc_std_rules_preset_noisy_execution",
    ).run()


# ======================================================================================================================
# 2. ÄQUIVALENZKLASSE: NO-OUTPUT REGEL (STUMMER CODE VS. UNDOKUMENTIERTER STDOUT & ERROR-OVERRIDE)
# ======================================================================================================================
def test_ebt_no_output_rule_context_messages_and_severity_override() -> None:
    """
    Gesetz:
    1. Erzeugt das Snippet keinen `stdout` und das Ergebnis ist leer, erklärt `NoOutput`,
       warum der Output fehlt, und verweist auf `print(...)` sowie `session=<id>`.
    2. Erzeugt das Snippet `stdout`, während der Ergebnis-Block leer gelassen wurde, nennt
       `NoOutput` den beobachteten Output in der Diagnose und unterdrückt einen harten `DOC-OUT`-Fail.
    3. Mit `NoOutput(severity='error')` wird ein leerer Ergebnis-Block zum harten Test-Fail (`passed=False`).
    """
    silent_code_doc = _build_doc("x = 21 * 2", "")
    undocumented_stdout_doc = _build_doc("print('computed_42')", "")

    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(silent_code_doc,)),
        post=WorldState(
            returns={
                "passed": True,
                "outputs": [[""]],
                "diagnostics": [
                    (
                        "DOC-NO-OUTPUT",
                        "warning",
                        re.compile(
                            r"^Result block is empty[\s\S]*produced no stdout[\s\S]*print\(result\)[\s\S]*session=<id>"
                        ),
                    )
                ],
            }
        ),
        custom_id="doc_std_rules_no_output_silent_code",
    ).run()
    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(undocumented_stdout_doc,)),
        post=WorldState(
            returns={
                "passed": True,
                "outputs": [["computed_42"]],
                "diagnostics": [
                    (
                        "DOC-NO-OUTPUT",
                        "warning",
                        re.compile(
                            r"^Result block is empty[\s\S]*produced stdout \('computed_42'\)[\s\S]*Document the expected output"
                        ),
                    )
                ],
            }
        ),
        custom_id="doc_std_rules_no_output_undocumented_stdout",
    ).run()

    # 2b. Überschreiben von NoOutput auf severity='error' erzwingt passed=False
    EBT(
        target=_run_std_rules,
        pre=WorldState(
            args=(silent_code_doc, CUBIE_DOC_RULES),
            kwargs={"extra_registered": [NoOutput(severity="error")]},
        ),
        post=WorldState(
            returns={
                "passed": False,
                "outputs": [[""]],
                "diagnostics": [
                    ("DOC-NO-OUTPUT", "error", re.compile(r"^Result block is empty[\s\S]*produced no stdout")),
                ],
            }
        ),
        custom_id="doc_std_rules_no_output_error_override",
    ).run()


# ======================================================================================================================
# 3. ÄQUIVALENZKLASSE: HIGH-COMPLEXITY REGEL (30/31-ZEILEN-GRENZE & KONFIGURIERBARES LIMIT)
# ======================================================================================================================
def test_ebt_high_complexity_boundary_and_custom_limits() -> None:
    """
    Gesetz:
    1. Ein Code-Block mit exakt 30 Zeilen besteht `HighComplexity(max_lines=30)` ohne Diagnose.
    2. Ab 31 Zeilen feuert `DOC-HIGH-COMPLEXITY` im Preset `CUBIE_DOC_RULES` als harter Fehler (`severity='error'`)
       mit Angabe der Zeilenzahl sowie den Empfehlungen zu `session=<id>` und `pre_state=WorldState(fs=...)`.
    3. Eigene Limits und Severities (z. B. `HighComplexity(max_lines=5, severity='warning')`)
       lassen sich frei konfigurieren.
    """
    code_30_lines = "\n".join([*(f"v_{i} = {i}" for i in range(29)), "print(v_28)"])
    code_31_lines = "\n".join([*(f"v_{i} = {i}" for i in range(30)), "print(v_29)"])
    code_6_lines = "\n".join([*(f"v_{i} = {i}" for i in range(5)), "print(v_4)"])

    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(_build_doc(code_30_lines, "28"),)),
        post=WorldState(
            returns={"passed": True, "outputs": [["28"]], "diagnostics": []}
        ),
        custom_id="doc_std_rules_high_complexity_30_lines_pass",
    ).run()
    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(_build_doc(code_31_lines, "29"),)),
        post=WorldState(
            returns={
                "passed": False,
                "outputs": [["29"]],
                "diagnostics": [
                    (
                        "DOC-HIGH-COMPLEXITY",
                        "error",
                        re.compile(
                            r"^Code example has 31 lines \(limit: 30\)[\s\S]*session=<id>[\s\S]*pre_state"
                        ),
                    )
                ],
            }
        ),
        custom_id="doc_std_rules_high_complexity_31_lines_error",
    ).run()
    EBT(
        target=_run_std_rules,
        pre=WorldState(
            args=(_build_doc(code_6_lines, "4"), [HighComplexity(max_lines=5, severity="warning")])
        ),
        post=WorldState(
            returns={
                "passed": True,
                "outputs": [["4"]],
                "diagnostics": [
                    (
                        "DOC-HIGH-COMPLEXITY",
                        "warning",
                        re.compile(r"^Code example has 6 lines \(limit: 5\)"),
                    )
                ],
            }
        ),
        custom_id="doc_std_rules_high_complexity_custom_limit_warning",
    ).run()


_QA_GUIDE_SECTION_1_EXAMPLE_DOC = (
    "Das folgende Einstiegsbeispiel zeigt das Grundmuster eines deklarativen `EBT`-Vertrags "
    "anhand der Standardfunktion `divmod` für zwei Eingabepaare:\n\n"
    "```python\n"
    "from qb_cubie import EBT, WorldState\n\n"
    "trace = EBT(\n"
    "    target=divmod,\n"
    "    pre=[WorldState(args=(17, 5)), WorldState(args=(20, 4))],\n"
    "    post=[\n"
    "        WorldState(returns=(3, 2)),\n"
    "        WorldState(returns=(5, 0)),\n"
    "    ],\n"
    "    reporter=None,\n"
    ").run()\n"
    'print(f"Vertrag erfüllt: {trace.evaluation} | Geprüfte Paare: {len(trace.traces)}")\n\n'
    '"""\n'
    "buuut...\n\n"
    "you know ...\n\n"
    "what if ...\n\n\n"
    + "\n\n".join("..." for _ in range(66))
    + '\n"""\n'
    "```\n\n"
    "<details>\n"
    "<summary>Ergebnis</summary>\n\n"
    "```text\n"
    "Vertrag erfüllt: True | Geprüfte Paare: 4\n"
    "```\n"
    "</details>"
)


def _run_cubie_doc_service(doc: str) -> None:
    """Runs DocEnsurance blackbox with CUBIE_DOC_STYLE, CUBIE_DOC_RULES, and PytestReporter."""
    DocEnsurance(
        target=doc,
        pattern=CUBIE_DOC_STYLE,
        rules=CUBIE_DOC_RULES,
        arena=TempFS(),
        reporter=PytestReporter(),
    ).run()


def test_ebt_high_complexity_fails_on_oversized_qa_guide_example() -> None:
    """
    Soll-Gesetz (TGD Red-Phase):
    Das 153-zeilige Einstiegsbeispiel aus `docs/GUIDE_Quality-Assurance.md` (Abschnitt 1)
    überschreitet das 30-Zeilen-Limit und muss den `DocEnsurance`-Service mit
    `CUBIE_DOC_RULES` hart fehlschlagen lassen (`AssertionError` mit `DOC-HIGH-COMPLEXITY`),
    statt stillschweigend grün durchzulaufen.
    """
    EBT(
        target=_run_cubie_doc_service,
        pre=WorldState(args=(_QA_GUIDE_SECTION_1_EXAMPLE_DOC,)),
        post=WorldState(
            raises=ExceptionExpectation(AssertionError, match=r"DOC-HIGH-COMPLEXITY")
        ),
        custom_id="doc_std_rules_qa_guide_section_1_complexity_failure",
    ).run()


# ======================================================================================================================
# 4. ÄQUIVALENZKLASSE: LARGE-OUTPUT & RAW-TRACEBACK REGELN
# ======================================================================================================================
def test_ebt_large_output_and_raw_traceback_rules() -> None:
    """
    Gesetz:
    1. `LargeOutput` akzeptiert bis zu 25 Ausgabezeilen und warnt ab 26 Zeilen (`DOC-LARGE-OUTPUT`).
    2. `RawTraceback` erkennt rohe Python-Stacktraces im Ergebnis-Block (`DOC-RAW-TRACEBACK`)
       und verweist auf `raises=<Exception>`.
    """
    out_25 = "\n".join(str(i) for i in range(25))
    out_26 = "\n".join(str(i) for i in range(26))
    doc_25_out = _build_doc("for i in range(25): print(i)", out_25)
    doc_26_out = _build_doc("for i in range(26): print(i)", out_26)

    raw_tb_text = "Traceback (most recent call last):\n  File 'x.py', line 1\nValueError: boom"
    doc_raw_tb = _build_doc("print(" + repr(raw_tb_text) + ")", raw_tb_text)

    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(doc_25_out,)),
        post=WorldState(
            returns={"passed": True, "outputs": [[out_25]], "diagnostics": []}
        ),
        custom_id="doc_std_rules_large_output_25_lines_pass",
    ).run()
    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(doc_26_out,)),
        post=WorldState(
            returns={
                "passed": True,
                "outputs": [[out_26]],
                "diagnostics": [
                    ("DOC-LARGE-OUTPUT", "warning", re.compile(r"^Output spans 26 lines \(limit: 25\)")),
                ],
            }
        ),
        custom_id="doc_std_rules_large_output_26_lines_warning",
    ).run()
    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(doc_raw_tb,)),
        post=WorldState(
            returns={
                "passed": True,
                "outputs": [[raw_tb_text]],
                "diagnostics": [
                    (
                        "DOC-RAW-TRACEBACK",
                        "warning",
                        re.compile(r"^Result block contains a raw Python traceback[\s\S]*raises=<Exception>"),
                    ),
                ],
            }
        ),
        custom_id="doc_std_rules_raw_traceback_warning",
    ).run()


# ======================================================================================================================
# 5. ÄQUIVALENZKLASSE: STATE-GUARDS FÜR FEHLKONFIGURIERTE STANDARD-REGELN
# ======================================================================================================================
def _instantiate_std_rule(rule_cls: Any, kwargs: dict[str, Any]) -> Any:
    """Instantiates a standard rule class with the provided keyword arguments."""
    return rule_cls(**kwargs)


def test_ebt_standard_rules_state_guards() -> None:
    """
    Gesetz: Ungültige `max_lines`-Schwellenwerte (< 1, bool, nicht-int) oder ungültige
    `severity`-Werte werden sofort beim Instanziieren durch `ValueError('STATE-GUARD: ...')` abgewiesen.
    """
    EBT(
        target=_instantiate_std_rule,
        pre=[
            WorldState(args=(HighComplexity, {"max_lines": 0})),
            WorldState(args=(HighComplexity, {"max_lines": -10})),
            WorldState(args=(HighComplexity, {"max_lines": True})),
            WorldState(args=(HighComplexity, {"max_lines": "30"})),
            WorldState(args=(LargeOutput, {"max_lines": 0})),
            WorldState(args=(LargeOutput, {"max_lines": False})),
            WorldState(args=(NoOutput, {"severity": "info"})),
            WorldState(args=(HighComplexity, {"severity": "fatal"})),
            WorldState(args=(LargeOutput, {"severity": "invalid"})),
            WorldState(args=(RawTraceback, {"severity": ""})),
        ],
        post=WorldState(
            raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")
        ),
        custom_id="doc_std_rules_state_guards",
    ).run()


# ======================================================================================================================
# 6. ÄQUIVALENZKLASSE: REGEL-KLASSEN-COERCION & INTERAKTION MIT RAISES=<EXCEPTION>
# ======================================================================================================================
_RAISES_WITH_STD_RULES_DOC = (
    "Ausreichend lange Erklärung für ein erwartetes Negativ-Beispiel.\n\n"
    "```python raises=ValueError\n"
    "raise ValueError('invalid threshold')\n"
    "```\n\n"
    "<details>\n<summary>Ergebnis</summary>\n\n```text\nValueError: invalid threshold\n```\n</details>"
)


def test_ebt_standard_rule_classes_and_raises_compatibility() -> None:
    """Verifies that standard rule classes coerce via type and do not false-alarm on raises= snippets."""
    rule_classes = (NoOutput, HighComplexity, LargeOutput, RawTraceback)
    EBT(
        target=_run_std_rules,
        pre=WorldState(args=(_RAISES_WITH_STD_RULES_DOC, rule_classes)),
        post=WorldState(
            returns={
                "passed": True,
                "outputs": [["ValueError: invalid threshold"]],
                "diagnostics": [],
            }
        ),
        custom_id="doc_std_rules_class_coercion_and_raises",
    ).run()
