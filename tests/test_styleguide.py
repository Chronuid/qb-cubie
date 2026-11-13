"""Enforce the measurable limits in docs/dev/Style-Guide.md on src/."""

import ast
import io
import tokenize
from pathlib import Path

import pytest

FUNCTION_LIMIT = 12
MODULE_LIMIT = 500
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
IGNORED = {
    tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
    tokenize.DEDENT, tokenize.ENDMARKER,
}


@pytest.mark.skip(reason="Module size limit temporarily suspended at the user's request.")
def test_module_size(src_files):
    violations = []
    for path in src_files:
        size = len(path.read_text(encoding="utf-8").splitlines())
        if size > MODULE_LIMIT:
            violations.append(f"{path}:1: {size} module lines (maximum {MODULE_LIMIT})")
    assert not violations, "\n" + "\n".join(violations)


def test_function_size(src_files):
    violations = []
    for path in src_files:
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source, filename=str(path))):
            if isinstance(node, FUNCTIONS):
                size = len(body_lines(source, node))
                if size > FUNCTION_LIMIT:
                    violations.append(
                        f"{path}:{node.lineno}: {node.name}: {size} body lines "
                        f"(maximum {FUNCTION_LIMIT})"
                    )
    assert not violations, "\n" + "\n".join(violations)


def test_docstrings(src_files):
    violations = []
    for path in src_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, *FUNCTIONS)):
                doc = ast.get_docstring(node)
                if doc is not None and len(doc.splitlines()) != 1:
                    violations.append(
                        f"{path}:{node.body[0].lineno}: "
                        f"{getattr(node, 'name', '<module>')}: docstring must be one line"
                    )
    assert not violations, "\n" + "\n".join(violations)


def test_benchmark_functions_have_docstrings():
    benchmark_root = Path(__file__).resolve().parents[1] / "experiments/benchmarks/cubie_benchmarks"
    missing = []
    for path in sorted(benchmark_root.rglob("*.py")):
        if "__pycache__" in path.parts or "data" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        missing.extend(f"{path}:{node.lineno}: {node.name}" for node in ast.walk(tree)
                       if isinstance(node, FUNCTIONS) and not ast.get_docstring(node))
    assert not missing, "Missing benchmark function docstrings:\n" + "\n".join(missing)


def body_lines(source, node):
    """Count physical code lines after the signature and optional docstring."""
    body = node.body[1:] if ast.get_docstring(node) is not None else node.body
    if not body:
        return set()
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    return {
        line
        for token in tokens if token.type not in IGNORED
        for line in range(token.start[0], token.end[0] + 1)
        if body[0].lineno <= line <= node.end_lineno
    }


@pytest.mark.parametrize("kind", ["def", "async def"])
@pytest.mark.parametrize("size", [0, 12, 13])
def test_body_counter(kind, size):
    source = (
        f"@decorator\n{kind} sample(\n    argument: int,\n):\n"
        '    """Describe the function.\n\n    Extra documentation.\n    """\n'
        + "    # A comment and blank line do not count.\n\n"
        + "    argument += 1\n" * size
    )
    node = ast.parse(source).body[0]
    assert len(body_lines(source, node)) == size


@pytest.mark.parametrize("body, expected", [
    ("return 1", 1),
    ("value = (\n        1 +\n        2\n    )\n    return value", 5),
    ("if flag:\n        return 1\n    return 2", 3),
    ('value = """first\nsecond\nthird"""\n    return value', 4),
])
def test_body_counter_statements(body, expected):
    source = f"def sample(flag=True):\n    {body}\n"
    assert len(body_lines(source, ast.parse(source).body[0])) == expected
