"""Meta-Gate 2: Enforce explicit justification for EBT cross-product contracts."""

import ast
from pathlib import Path

import libcst as cst
import pytest

from qb_cubie import EBT, CstLinter, CstRule, LinterDiagnostic, WorldState

RULE_ID = "META-EBT-CROSS-PRODUCT"
REASON_TAG_KEY = "meta:cross-product-reason"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCAN_EXCLUDES = [".arenas", ".venv", "__pycache__", ".git", ".pytest_cache"]


def _is_ebt_call(node: cst.Call) -> bool:
    """Return True if the call invokes EBT directly or as an attribute."""
    if isinstance(node.func, cst.Name):
        return node.func.value == "EBT"
    if isinstance(node.func, cst.Attribute):
        return node.func.attr.value == "EBT"
    return False


def _is_worldstate_call(node: cst.BaseExpression) -> bool:
    """Return True if the expression is a direct or attribute WorldState call."""
    if not isinstance(node, cst.Call):
        return False
    if isinstance(node.func, cst.Name):
        return node.func.value == "WorldState"
    if isinstance(node.func, cst.Attribute):
        return node.func.attr.value == "WorldState"
    return False


def _literal_string(module: cst.Module, node: cst.BaseExpression) -> str | None:
    """Safely evaluate a static string literal CST node."""
    if not isinstance(node, (cst.SimpleString, cst.ConcatenatedString)):
        return None
    try:
        value = ast.literal_eval(module.code_for_node(node))
    except (SyntaxError, ValueError):
        return None
    return value if isinstance(value, str) else None


def _extract_call_params(module: cst.Module, node: cst.Call) -> dict[str, cst.BaseExpression]:
    """Extract relevant EBT parameters from positional, keyword, and literal **kwargs args."""
    positional_map = {2: "pre", 3: "post", 9: "tags"}
    params: dict[str, cst.BaseExpression] = {}
    pos_idx = 0
    for arg in node.args:
        if arg.keyword is not None:
            params[arg.keyword.value] = arg.value
        elif arg.star == "":
            if pos_idx in positional_map:
                params[positional_map[pos_idx]] = arg.value
            pos_idx += 1
        elif arg.star == "*":
            pos_idx = 10_000
        elif arg.star == "**" and isinstance(arg.value, cst.Dict):
            for elem in arg.value.elements:
                if isinstance(elem, cst.DictElement):
                    key = _literal_string(module, elem.key)
                    if key in {"pre", "post", "tags"}:
                        params[key] = elem.value
    return params


def _is_positive_worldstate(expr: cst.BaseExpression) -> bool:
    """Return True unless expr is a WorldState call with expect=False or expect=None."""
    if not _is_worldstate_call(expr):
        return True
    assert isinstance(expr, cst.Call)
    expect_expr: cst.BaseExpression | None = None
    pos_idx = 0
    for arg in expr.args:
        if arg.keyword is not None:
            if arg.keyword.value == "expect":
                expect_expr = arg.value
        elif arg.star == "":
            if pos_idx == 5:
                expect_expr = arg.value
            pos_idx += 1
        elif arg.star == "*":
            pos_idx = 10_000
    return not (isinstance(expect_expr, cst.Name) and expect_expr.value in {"False", "None"})


def _extract_wrapper_field(
    module: cst.Module,
    expr: cst.BaseExpression,
    field_name: str,
) -> cst.BaseExpression | None:
    """Extract a static string-keyed value from a quantifier wrapper dict."""
    if not isinstance(expr, cst.Dict):
        return None
    for elem in expr.elements:
        if not isinstance(elem, cst.DictElement):
            continue
        if _literal_string(module, elem.key) == field_name:
            return elem.value
    return None


def _count_pre_states(module: cst.Module, pre_expr: cst.BaseExpression | None) -> int:
    """Count statically declared pre-states in an EBT call (including dict wrappers)."""
    if isinstance(pre_expr, cst.Dict):
        pre_expr = _extract_wrapper_field(module, pre_expr, "states")
    if isinstance(pre_expr, (cst.List, cst.Tuple)):
        return len(pre_expr.elements)
    return 1


def _count_positive_post_states(module: cst.Module, post_expr: cst.BaseExpression | None) -> int:
    """Count statically declared disjunctive positive post-states (expect != False/None)."""
    if isinstance(post_expr, cst.Dict):
        quantor_expr = _extract_wrapper_field(module, post_expr, "quantor")
        quantor = _literal_string(module, quantor_expr) if quantor_expr is not None else None
        if quantor == "all":
            return 1
        post_expr = _extract_wrapper_field(module, post_expr, "states")
    if isinstance(post_expr, (cst.List, cst.Tuple)):
        return sum(1 for el in post_expr.elements if _is_positive_worldstate(el.value))
    if post_expr is not None and not _is_positive_worldstate(post_expr):
        return 0
    return 1


def _extract_cross_product_reason(module: cst.Module, tags_expr: cst.BaseExpression | None) -> str | None:
    """Extract a non-empty justification string from EBT's tags dictionary."""
    if not isinstance(tags_expr, cst.Dict):
        return None
    for elem in tags_expr.elements:
        if not isinstance(elem, cst.DictElement):
            continue
        if _literal_string(module, elem.key) != REASON_TAG_KEY:
            continue
        reason = _literal_string(module, elem.value)
        if reason is not None and reason.strip():
            return reason.strip()
    return None


class EbtCrossProductRule(CstRule):
    """Detect EBT calls with >1 pre-state and >1 positive post-state without justification."""

    def visit_Call(self, node: cst.Call) -> None:
        """Inspect EBT(...) calls for unjustified NxM cross-product contracts."""
        if not self._module or not _is_ebt_call(node):
            return
        params = _extract_call_params(self._module, node)
        pre_n = _count_pre_states(self._module, params.get("pre"))
        positive_post_n = _count_positive_post_states(self._module, params.get("post"))
        if pre_n <= 1 or positive_post_n <= 1:
            return
        if _extract_cross_product_reason(self._module, params.get("tags")) is not None:
            return
        self.add_diagnostic(
            node=node,
            rule_id=RULE_ID,
            message=(
                f"{pre_n}x{positive_post_n} EBT-Kreuzprodukt ohne Begründung: "
                f"Füge tags={{'{REASON_TAG_KEY}': '...'}} hinzu oder trenne in Einzelverträge."
            ),
            node_name=f"{pre_n}x{positive_post_n}",
        )


def build_cross_product_linter() -> CstLinter:
    """Create the configured CstLinter instance for Meta-Gate 2."""
    return CstLinter(rules=[EbtCrossProductRule()], excludes=SCAN_EXCLUDES)


def _format_diagnostics(diagnostics: list[LinterDiagnostic]) -> str:
    """Format linter diagnostics with file, line, rule ID, and message."""
    return "\n".join(
        f"{d.file_path}:{d.line}:{d.column} [{d.rule_id}] {d.message}"
        for d in diagnostics
    )


@pytest.mark.parametrize(
    "clean_source",
    [
        "EBT(target=f, pre=WorldState(), post=WorldState())\n",
        "EBT(target=f, pre=[p1, p2], post=WorldState(returns='ok'))\n",
        "EBT(target=f, pre=[p1, p2], post=[WorldState(returns='ok')])\n",
        "EBT(target=f, pre=WorldState(args=(1,)), post=[WorldState(returns=1), WorldState(returns=2)])\n",
        (
            "EBT(target=f, pre=[p1, p2], "
            "post={'quantor': 'all', 'states': [WorldState(returns=3), WorldState(returns=99, expect=False)]})\n"
        ),
        (
            "EBT(target=f, pre=[p1, p2], "
            "post={'quantor': 'all', 'states': [WorldState(returns=1, expect=False), WorldState(returns=2, expect=False)]})\n"
        ),
        (
            "EBT(target=f, pre=[p1, p2], "
            "post={'quantor': 'all', 'states': [WorldState(returns=int), WorldState(returns=3)]})\n"
        ),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)], "
            "tags={'meta:cross-product-reason': 'Tests N:M quantifier matrix'})\n"
        ),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)], "
            "tags={'meta:cross-product-reason': 'Line 1 ' 'Line 2'})\n"
        ),
        (
            "qb_cubie.EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)], "
            "tags={'meta:cross-product-reason': 'Qualified call justified'})\n"
        ),
        "other_func(pre=[p1, p2], post=[q1, q2])\n",
        'example = "EBT(target=f, pre=[p1, p2], post=[q1, q2])"\n',
    ],
    ids=[
        "single-1x1",
        "many-pre-single-post-object",
        "many-pre-single-post-list",
        "single-pre-many-post",
        "many-pre-one-positive-one-negative",
        "many-pre-only-negative-posts",
        "many-pre-conjunctive-post-all",
        "justified-cross-product",
        "justified-concatenated-reason",
        "justified-attribute-ebt",
        "non-ebt-call",
        "string-literal",
    ],
)
def test_cross_product_rule_accepts_clean_probes(clean_source: str) -> None:
    """Clean probe: 1xN, Nx1, 1-positive-post, and justified NxM calls yield zero diagnostics."""
    linter = build_cross_product_linter()
    EBT(
        target=linter.check,
        pre=WorldState(args=(clean_source,)),
        post=WorldState(returns=[]),
        reporter=None,
    ).run()


@pytest.mark.parametrize(
    "bad_source, expected_line, expected_matrix",
    [
        ("EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)])\n", 1, "2x2"),
        ("EBT(target=f, pre=(p1, p2), post=(WorldState(returns=1), WorldState(returns=2)))\n", 1, "2x2"),
        ("EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1, expect=True), WorldState(returns=2)])\n", 1, "2x2"),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2), WorldState(returns=99, expect=False)])\n",
            1,
            "2x2",
        ),
        ("EBT(f, None, [p1, p2], [WorldState(returns=1), WorldState(returns=2)])\n", 1, "2x2"),
        ("qb_cubie.EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)])\n", 1, "2x2"),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)], "
            + "tags={'meta:cross-product-reason': ''})\n",
            1,
            "2x2",
        ),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)], "
            + "tags={'meta:cross-product-reason': '   '})\n",
            1,
            "2x2",
        ),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)], "
            + "tags={'meta:cross-product-reason': True})\n",
            1,
            "2x2",
        ),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=1), WorldState(returns=2)], "
            + "tags={'meta:other': 'not the cross-product key'})\n",
            1,
            "2x2",
        ),
        ("# Kommentar\nEBT(target=f, pre=[p1, p2, p3], post=[q1, q2, q3, q4])\n", 2, "3x4"),
        (
            "EBT(target=f, pre={'quantor': 'all', 'states': [p1, p2]}, "
            + "post=[WorldState(returns=1), WorldState(returns=2)])\n",
            1,
            "2x2",
        ),
        (
            "EBT(target=f, pre=[p1, p2], "
            + "post={'quantor': 'exists', 'states': [WorldState(returns=1), WorldState(returns=2)]})\n",
            1,
            "2x2",
        ),
        (
            "EBT(target=f, pre={'quantor': 'exists', 'states': [p1, p2]}, "
            + "post={'quantor': 'exists', 'states': [WorldState(returns=1), WorldState(returns=2)]})\n",
            1,
            "2x2",
        ),
    ],
    ids=[
        "list-2x2",
        "tuple-2x2",
        "explicit-expect-true-2x2",
        "two-positive-one-negative",
        "positional-args-2x2",
        "attribute-ebt-2x2",
        "empty-reason-string",
        "whitespace-reason-string",
        "non-string-reason",
        "unrelated-tag-key",
        "line-number-offset-3x4",
        "dict-pre-list-post-2x2",
        "list-pre-dict-post-exists-2x2",
        "dict-pre-dict-post-exists-2x2",
    ],
)
def test_cross_product_rule_detects_fault_probes(
    bad_source: str,
    expected_line: int,
    expected_matrix: str,
) -> None:
    """Fault probe: unjustified NxM cross-products trigger META-EBT-CROSS-PRODUCT with exact line."""
    linter = build_cross_product_linter()

    def has_expected_diagnostic(diagnostics: list[LinterDiagnostic]) -> bool:
        if len(diagnostics) != 1:
            return False
        diag = diagnostics[0]
        return (
            diag.rule_id == RULE_ID
            and diag.line == expected_line
            and diag.node_name == expected_matrix
            and REASON_TAG_KEY in diag.message
        )

    EBT(
        target=linter.check,
        pre=WorldState(args=(bad_source,)),
        post=WorldState(returns=has_expected_diagnostic),
        reporter=None,
    ).run()


def test_cross_product_rule_reports_file_path_on_disk(tmp_path: Path) -> None:
    """File probe: diagnostics report the concrete file path and line on disk."""
    bad_file = tmp_path / "broken_cross_product_sample.py"
    bad_file.write_text(
        "from qb_cubie import EBT, WorldState\n"
        "EBT(target=sum, pre=[WorldState(args=([1],)), WorldState(args=([2],))], "
        "post=[WorldState(returns=1), WorldState(returns=2)])\n",
        encoding="utf-8",
    )
    diagnostics = build_cross_product_linter().check(bad_file)
    assert len(diagnostics) == 1, _format_diagnostics(diagnostics)
    assert diagnostics[0].file_path == str(bad_file)
    assert diagnostics[0].rule_id == RULE_ID
    assert diagnostics[0].line == 2
    assert diagnostics[0].node_name == "2x2"


def test_repository_has_no_unjustified_ebt_cross_products() -> None:
    """Repository gate: no Python file under tests/ has an unjustified EBT cross-product."""
    diagnostics = build_cross_product_linter().check(PROJECT_ROOT / "tests")
    assert diagnostics == [], (
        "Unjustified EBT cross-products found in tests/ :\n"
        f"{_format_diagnostics(diagnostics)}"
    )
