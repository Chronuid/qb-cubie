import libcst as cst
import libcst.matchers as m
from cubie.linter import CstLinter, CstRule
from cubie.protocols import WorldState
from cubie.ebt import EBT


# --- 1. Definition der Custom Rules ---

class ForbidEvalRule(CstRule):
    """
    Prüft auf die unsichere Verwendung von eval().
    """
    def visit_Call(self, node: cst.Call) -> None:
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(
                node=node,
                rule_id="CST001",
                message="Die Nutzung von 'eval()' ist ein Sicherheitsrisiko und verboten."
            )


class RequireReturnTypeRule(CstRule):
    """
    Erzwingt Type-Hints für Rückgabewerte (außer bei __init__).
    """
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        # Deklaratives Pattern Matching: Wir suchen exakt die Struktur m.Annotation()
        has_return_type = m.matches(node, m.FunctionDef(returns=m.Annotation()))
        if not has_return_type and node.name.value != "__init__":
            self.add_diagnostic(
                node=node,
                rule_id="CST002",
                message=f"Der Funktion '{node.name.value}' fehlt die Return-Type-Annotation."
            )


# --- 2. EBT Test-Suiten ---

def test_cstlinter_clean_code():
    """Der glückliche Pfad: Sauberer Code wirft keine Fehler."""
    clean_code = """
def berechne_summe(a: int, b: int) -> int:
    return a + b
"""
    EBT(
        target=CstLinter(rules=[ForbidEvalRule(), RequireReturnTypeRule()]).check,
        pre=WorldState(kwargs={"target": clean_code}),
        post=WorldState(returns=[])  # Erwartung: Leere Fehlerliste
    ).run()


def test_cstlinter_finds_eval():
    """Prüft, ob die eval-Regel korrekt anschlägt und die Koordinaten stimmen."""
    bad_code = "x = 5\nresult = eval('x + 1')\n"
    def validate_eval_diagnostic(diagnostics: list) -> bool:
        if len(diagnostics) != 1: return False
        d = diagnostics[0]
        # eval steht in der zweiten Zeile (Zeile 2), ab Zeichen 10 (Spalte 9, nullbasiert)
        return d.rule_id == "CST001" and d.line == 2

    EBT(
        target=CstLinter(rules=[ForbidEvalRule()]).check,
        pre=WorldState(kwargs={"target": bad_code}),
        post=WorldState(returns=validate_eval_diagnostic)
    ).run()


def test_cstlinter_missing_return_type():
    """Prüft die Matcher-basierte Regel für Type-Hints."""
    bad_code = """
def helfer_funktion(x):
    pass
"""

    def validate_type_diagnostic(diagnostics: list) -> bool:
        return len(diagnostics) == 1 and diagnostics[0].rule_id == "CST002"

    EBT(
        target=CstLinter(rules=[RequireReturnTypeRule()]).check,
        pre=WorldState(kwargs={"target": bad_code}),
        post=WorldState(returns=validate_type_diagnostic)
    ).run()


def test_cstlinter_aggregation():
    """Prüft, ob der Linter mehrere Regeln nahtlos bündelt."""
    very_bad_code = """
def unsichere_funktion(x):
    return eval(x)
"""

    def validate_aggregation(diagnostics: list) -> bool:
        rule_ids = {d.rule_id for d in diagnostics}
        # Es müssen zwingend BEIDE Fehler gefunden werden
        return {"CST001", "CST002"}.issubset(rule_ids)
    EBT(
        target=CstLinter(rules=[ForbidEvalRule(), RequireReturnTypeRule()]).check,
        pre=WorldState(kwargs={"target": very_bad_code}),
        post=WorldState(returns=validate_aggregation)
    ).run()