import os
from pathlib import Path

import libcst as cst
import libcst.matchers as m
import pytest
from qb_cubie import EBT, CstLinter, CstRule, ExceptionExpectation, WorldState


# --- 1. Definition of Custom Rules ---

class ForbidEvalRule(CstRule):
    """
    Checks for the unsafe use of eval().
    """
    def visit_Call(self, node: cst.Call) -> None:
        if isinstance(node.func, cst.Name) and node.func.value == "eval":
            self.add_diagnostic(
                node=node,
                rule_id="CST001",
                message="The use of 'eval()' is a security risk and is prohibited."
            )


class RequireReturnTypeRule(CstRule):
    """
    Enforces type hints for return values (except for __init__).
    """
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        has_return_type = m.matches(node, m.FunctionDef(returns=m.Annotation()))
        if not has_return_type and node.name.value != "__init__":
            self.add_diagnostic(
                node=node,
                rule_id="CST002",
                message=f"The function '{node.name.value}' is missing the return type annotation."
            )


# --- 2. EBT Tests ---

clean_code = """
def calculate_summ(a: int, b: int) -> int:
    return a + b
"""
def test_cstlinter_clean_code():
    """The happy path: Clean code does not throw errors."""
    target_code = clean_code
    EBT(
        target=CstLinter(rules=[ForbidEvalRule(), RequireReturnTypeRule()]).check,
        pre=WorldState(kwargs={"target": target_code}),
        post=WorldState(returns=[])
    ).run()


def test_cstlinter_finds_eval():
    """Check whether the eval rule triggers correctly and the coordinates are correct."""
    bad_target_code = "x = 5\nresult = eval('x + 1')\n"
    def validate_eval_diagnostic(diagnostics: list) -> bool:
        if len(diagnostics) != 1: return False
        d = diagnostics[0]
        return d.rule_id == "CST001" and d.line == 2
    EBT(
        target=CstLinter(rules=[ForbidEvalRule()]).check,
        pre=WorldState(kwargs={"target": bad_target_code}),
        post=WorldState(returns=validate_eval_diagnostic)
    ).run()


bad_code = """
def helfer_funktion(x):
    pass
"""
def test_cstlinter_missing_return_type():
    """Checks the matcher-based rule for type hints."""
    def validate_type_diagnostic(diagnostics: list) -> bool:
        return len(diagnostics) == 1 and diagnostics[0].rule_id == "CST002"
    EBT(
        target=CstLinter(rules=[RequireReturnTypeRule()]).check,
        pre=WorldState(kwargs={"target": bad_code}),
        post=WorldState(returns=validate_type_diagnostic)
    ).run()


very_bad_code = """
def unsichere_funktion(x):
    return eval(x)
"""
def test_cstlinter_aggregation():
    """Checks whether the linter seamlessly bundles multiple rules."""
    def validate_aggregation(diagnostics: list) -> bool:
        rule_ids = {d.rule_id for d in diagnostics}
        return {"CST001", "CST002"}.issubset(rule_ids)
    EBT(
        target=CstLinter(rules=[ForbidEvalRule(), RequireReturnTypeRule()]).check,
        pre=WorldState(kwargs={"target": very_bad_code}),
        post=WorldState(returns=validate_aggregation)
    ).run()


# --- 3. Path Target Validation & Filesystem Equivalence Classes (BUG-003) ---


@pytest.mark.parametrize("case", ["missing_file", "missing_dir", "broken_symlink"])
def test_cstlinter_rejects_nonexistent_path(tmp_path: Path, case: str) -> None:
    """Missing files, missing directories, and broken symlinks must raise FileNotFoundError."""
    if case == "missing_file":
        target = tmp_path / "nicht_vorhanden.py"
    elif case == "missing_dir":
        target = tmp_path / "nicht_vorhanden_dir"
    else:
        target = tmp_path / "broken_link.py"
        target.symlink_to(tmp_path / "dangling_target.py")
    EBT(
        target=CstLinter(rules=[ForbidEvalRule()]).check,
        pre=WorldState(kwargs={"target": target}),
        post=WorldState(raises=ExceptionExpectation(FileNotFoundError, match=r"STATE-GUARD:")),
    ).run()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX mkfifo required")
def test_cstlinter_rejects_unsuitable_path(tmp_path: Path) -> None:
    """Existing Path targets that are neither file nor directory must raise ValueError."""
    fifo_path = tmp_path / "named_pipe"
    os.mkfifo(fifo_path)
    EBT(
        target=CstLinter(rules=[ForbidEvalRule()]).check,
        pre=WorldState(kwargs={"target": fifo_path}),
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
    ).run()


def test_cstlinter_valid_path_targets(tmp_path: Path) -> None:
    """Positive control: valid file, empty directory, and directory with excludes."""
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x: int = 1\n", encoding="utf-8")
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "bad.py").write_text("eval('1')\n", encoding="utf-8")
    excluded = pkg_dir / ".venv"
    excluded.mkdir()
    (excluded / "ignored.py").write_text("eval('2')\n", encoding="utf-8")

    linter = CstLinter(rules=[ForbidEvalRule()], excludes=[".venv"])
    EBT(
        target=linter.check,
        pre=WorldState(kwargs={"target": clean_file}),
        post=WorldState(returns=[]),
    ).run()
    EBT(
        target=linter.check,
        pre=WorldState(kwargs={"target": empty_dir}),
        post=WorldState(returns=[]),
    ).run()
    EBT(
        target=linter.check,
        pre=WorldState(kwargs={"target": pkg_dir}),
        post=WorldState(returns=lambda diags: len(diags) == 1 and diags[0].rule_id == "CST001"),
    ).run()
