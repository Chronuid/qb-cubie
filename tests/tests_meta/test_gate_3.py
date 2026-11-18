"""Meta-Gate 3: Detect EBT contracts whose post-states only negate (expect=False)."""

import ast
from pathlib import Path

import libcst as cst
import pytest

from qb_cubie import EBT, CstLinter, CstRule, LinterDiagnostic, WorldState

RULE_ID = "META-EBT-LONELY-NEGATION"
EXEMPT_TAG = "meta:negative-invariant"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCAN_EXCLUDES = [".arenas", ".venv", "__pycache__", ".git", ".pytest_cache"]


def _is_named_call(node: cst.BaseExpression, target_name: str) -> bool:
    """Return True if expr is a direct or attribute call to target_name."""
    if not isinstance(node, cst.Call):
        return False
    if isinstance(node.func, cst.Name):
        return node.func.value == target_name
    if isinstance(node.func, cst.Attribute):
        return node.func.attr.value == target_name
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


def _extract_call_params(
    module: cst.Module,
    node: cst.Call,
    positional_map: dict[int, str],
    tracked_keys: set[str],
) -> dict[str, cst.BaseExpression]:
    """Extract tracked call parameters from positional, keyword, and literal **kwargs args."""
    params: dict[str, cst.BaseExpression] = {}
    pos_idx = 0
    for arg in node.args:
        if arg.keyword is not None:
            if arg.keyword.value in tracked_keys:
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
                    if key in tracked_keys:
                        params[key] = elem.value
    return params


def _is_explicitly_negative_worldstate(module: cst.Module, expr: cst.BaseExpression) -> bool:
    """Return True when expr is a WorldState(...) call with static expect=False or expect=None."""
    if not _is_named_call(expr, "WorldState"):
        return False
    assert isinstance(expr, cst.Call)
    params = _extract_call_params(module, expr, {5: "expect"}, {"expect"})
    expect_expr = params.get("expect")
    return isinstance(expect_expr, cst.Name) and expect_expr.value in {"False", "None"}


def _extract_post_worldstates(post_expr: cst.BaseExpression | None) -> list[cst.BaseExpression] | None:
    """Return all statically declared WorldState calls in post, or None if unknown/empty."""
    if post_expr is None:
        return None
    if isinstance(post_expr, cst.Name) and post_expr.value == "None":
        return None
    if _is_named_call(post_expr, "WorldState"):
        return [post_expr]
    if isinstance(post_expr, (cst.List, cst.Tuple)):
        if not post_expr.elements:
            return None
        states: list[cst.BaseExpression] = []
        for elem in post_expr.elements:
            if isinstance(elem, cst.StarredElement) or not _is_named_call(elem.value, "WorldState"):
                return None
            states.append(elem.value)
        return states
    return None


def _is_truthy_dict_tag_value(module: cst.Module, value_expr: cst.BaseExpression) -> bool:
    """Return True if a dict tag value is True or a non-empty static string literal."""
    if isinstance(value_expr, cst.Name):
        return value_expr.value == "True"
    text = _literal_string(module, value_expr)
    return text is not None and bool(text.strip())


def _has_negative_invariant_tag(module: cst.Module, tags_expr: cst.BaseExpression | None) -> bool:
    """Return True if EBT tags explicitly opt into a pure negative-invariant contract."""
    if isinstance(tags_expr, (cst.Set, cst.List, cst.Tuple)):
        for elem in tags_expr.elements:
            if isinstance(elem, cst.StarredElement):
                continue
            if _literal_string(module, elem.value) == EXEMPT_TAG:
                return True
        return False
    if isinstance(tags_expr, cst.Dict):
        for dict_elem in tags_expr.elements:
            if not isinstance(dict_elem, cst.DictElement):
                continue
            if _literal_string(module, dict_elem.key) == EXEMPT_TAG:
                return _is_truthy_dict_tag_value(module, dict_elem.value)
    return False


class EbtLonelyNegationRule(CstRule):
    """Detect EBT calls where every WorldState in post has expect=False without opt-in tag."""

    def visit_Call(self, node: cst.Call) -> None:
        """Inspect EBT(...) calls for post-state contracts lacking any positive goal."""
        if not self._module or not _is_named_call(node, "EBT"):
            return
        params = _extract_call_params(
            self._module,
            node,
            {2: "pre", 3: "post", 4: "expect", 9: "tags"},
            {"pre", "post", "expect", "tags"},
        )
        post_states = _extract_post_worldstates(params.get("post"))
        if not post_states:
            return
        if not all(_is_explicitly_negative_worldstate(self._module, state) for state in post_states):
            return
        if _has_negative_invariant_tag(self._module, params.get("tags")):
            return
        count = len(post_states)
        self.add_diagnostic(
            node=node,
            rule_id=RULE_ID,
            message=(
                f"Einsame Negation ({count}x expect=False in post ohne positives Ziel): "
                f"Ergänze ein positives WorldState(...) oder dokumentiere die Ausnahme über "
                f"tags={{'{EXEMPT_TAG}'}}."
            ),
            node_name=f"0pos/{count}neg",
        )


def build_lonely_negation_linter() -> CstLinter:
    """Create the configured CstLinter instance for Meta-Gate 3."""
    return CstLinter(rules=[EbtLonelyNegationRule()], excludes=SCAN_EXCLUDES)


def _format_diagnostics(diagnostics: list[LinterDiagnostic]) -> str:
    """Format linter diagnostics with file, line, rule ID, and message."""
    return "\n".join(
        f"{d.file_path}:{d.line}:{d.column} [{d.rule_id}] {d.message}"
        for d in diagnostics
    )


@pytest.mark.parametrize(
    "clean_source",
    [
        "EBT(target=f)\n",
        "EBT(target=f, post=None)\n",
        "EBT(target=f, post=WorldState(returns=1))\n",
        "EBT(target=f, post=WorldState(returns=1, expect=True))\n",
        "EBT(target=f, post=WorldState(returns=1), expect=False)\n",
        "EBT(target=f, post=[WorldState(returns=1), WorldState(returns=99, expect=False)])\n",
        "EBT(target=f, post=(WorldState(returns=99, expect=False), WorldState(returns=1)))\n",
        "EBT(target=f, post=WorldState(returns=1, expect=flag))\n",
        "EBT(target=f, post=[q1, WorldState(returns=99, expect=False)])\n",
        "EBT(target=f, post=expected_states)\n",
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), "
            "tags={'meta:negative-invariant'})\n"
        ),
        (
            "EBT(target=f, post=[WorldState(returns=404, expect=False), "
            "WorldState(returns=500, expect=False)], tags={'meta:negative-invariant', 'safety'})\n"
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), "
            "tags=['meta:negative-invariant'])\n"
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), "
            "tags=('meta:negative-invariant',))\n"
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), "
            "tags={'meta:negative-invariant': 'Rejects sentinel error code'})\n"
        ),
        (
            "EBT(target=f, pre=[p1, p2], post=[WorldState(returns=404, expect=False), "
            "WorldState(returns=500, expect=False)], "
            "tags={'meta:negative-invariant': True, 'meta:cross-product-reason': 'Status matrix'})\n"
        ),
        (
            "qb_cubie.EBT(target=f, post=qb_cubie.WorldState(returns=99, expect=False), "
            "tags={'meta:negative-invariant'})\n"
        ),
        "other_func(post=WorldState(returns=99, expect=False))\n",
        'example = "EBT(target=f, post=WorldState(returns=99, expect=False))"\n',
    ],
    ids=[
        "omitted-post",
        "none-post",
        "single-positive-default",
        "single-positive-explicit",
        "positive-post-with-ebt-expect-false",
        "mixed-list-pos-and-neg",
        "mixed-tuple-neg-and-pos",
        "dynamic-expect-expression",
        "mixed-opaque-post-list",
        "dynamic-post-variable",
        "exempt-set-single",
        "exempt-set-multi",
        "exempt-list-tag",
        "exempt-tuple-tag",
        "exempt-dict-reason",
        "exempt-dict-bool-with-cross-product",
        "exempt-qualified-call",
        "non-ebt-call",
        "string-literal",
    ],
)
def test_lonely_negation_rule_accepts_clean_probes(clean_source: str) -> None:
    """Clean probe: positive, mixed, dynamic, and tagged negative-invariant contracts pass."""
    linter = build_lonely_negation_linter()
    EBT(
        target=linter.check,
        pre=WorldState(args=(clean_source,)),
        post=WorldState(returns=[]),
        reporter=None,
    ).run()


@pytest.mark.parametrize(
    "bad_source, expected_line, expected_node_name",
    [
        ("EBT(target=f, post=WorldState(returns=99, expect=False))\n", 1, "0pos/1neg"),
        ("EBT(target=f, post=WorldState(expect=False))\n", 1, "0pos/1neg"),
        ("EBT(target=f, post=WorldState(returns=99, expect=None))\n", 1, "0pos/1neg"),
        ("EBT(target=f, post=WorldState(None, None, None, None, 99, False))\n", 1, "0pos/1neg"),
        ("EBT(target=f, post=WorldState(returns=99, **{'expect': False}))\n", 1, "0pos/1neg"),
        (
            "EBT(target=f, post=[WorldState(returns=404, expect=False), "
            + "WorldState(returns=500, expect=False)])\n",
            1,
            "0pos/2neg",
        ),
        (
            "EBT(target=f, post=(WorldState(returns=404, expect=False), "
            + "WorldState(returns=500, expect=False)))\n",
            1,
            "0pos/2neg",
        ),
        ("EBT(f, None, p1, WorldState(returns=99, expect=False))\n", 1, "0pos/1neg"),
        ("EBT(target=f, **{'post': WorldState(returns=99, expect=False)})\n", 1, "0pos/1neg"),
        (
            "qb_cubie.EBT(target=f, post=qb_cubie.WorldState(returns=99, expect=False))\n",
            1,
            "0pos/1neg",
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), tags={'meta:other'})\n",
            1,
            "0pos/1neg",
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), tags=set())\n",
            1,
            "0pos/1neg",
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), "
            + "tags={'meta:negative-invariant': False})\n",
            1,
            "0pos/1neg",
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), "
            + "tags={'meta:negative-invariant': '   '})\n",
            1,
            "0pos/1neg",
        ),
        (
            "EBT(target=f, post=WorldState(returns=99, expect=False), expect=False)\n",
            1,
            "0pos/1neg",
        ),
        (
            "# Kommentar\nEBT(target=f, post=[WorldState(returns=1, expect=False), "
            + "WorldState(returns=2, expect=False), WorldState(returns=3, expect=False)])\n",
            2,
            "0pos/3neg",
        ),
    ],
    ids=[
        "single-expect-false",
        "unrestricted-expect-false",
        "single-expect-none",
        "positional-worldstate-expect-false",
        "kwargs-worldstate-expect-false",
        "list-two-negatives",
        "tuple-two-negatives",
        "positional-ebt-post",
        "kwargs-ebt-post",
        "qualified-ebt-and-worldstate",
        "unrelated-tag",
        "empty-tag-set",
        "dict-tag-false",
        "dict-tag-whitespace",
        "double-negation-without-tag",
        "line-offset-three-negatives",
    ],
)
def test_lonely_negation_rule_detects_fault_probes(
    bad_source: str,
    expected_line: int,
    expected_node_name: str,
) -> None:
    """Fault probe: lonely-negation EBT contracts trigger META-EBT-LONELY-NEGATION."""
    linter = build_lonely_negation_linter()

    def has_expected_diagnostic(diagnostics: list[LinterDiagnostic]) -> bool:
        if len(diagnostics) != 1:
            return False
        diag = diagnostics[0]
        return (
            diag.rule_id == RULE_ID
            and diag.line == expected_line
            and diag.node_name == expected_node_name
            and EXEMPT_TAG in diag.message
        )

    EBT(
        target=linter.check,
        pre=WorldState(args=(bad_source,)),
        post=WorldState(returns=has_expected_diagnostic),
        reporter=None,
    ).run()


def test_lonely_negation_rule_reports_file_path_on_disk(tmp_path: Path) -> None:
    """File probe: diagnostics report the concrete file path and line on disk."""
    bad_file = tmp_path / "broken_lonely_negation_sample.py"
    bad_file.write_text(
        "from qb_cubie import EBT, WorldState\n"
        "EBT(target=lambda: 1, post=WorldState(returns=99, expect=False))\n",
        encoding="utf-8",
    )
    diagnostics = build_lonely_negation_linter().check(bad_file)
    assert len(diagnostics) == 1, _format_diagnostics(diagnostics)
    assert diagnostics[0].file_path == str(bad_file)
    assert diagnostics[0].rule_id == RULE_ID
    assert diagnostics[0].line == 2
    assert diagnostics[0].node_name == "0pos/1neg"


def test_repository_has_no_lonely_ebt_negations() -> None:
    """Repository gate: no Python file under tests/ has an untagged lonely EBT negation."""
    diagnostics = build_lonely_negation_linter().check(PROJECT_ROOT / "tests")
    assert diagnostics == [], (
        "Lonely EBT negations found in tests/ :\n"
        f"{_format_diagnostics(diagnostics)}"
    )
