"""Enforce docstring completeness on the experimental cubie_benchmarks package."""

import ast
from pathlib import Path

FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def test_benchmark_functions_have_docstrings():
    benchmark_root = Path(__file__).resolve().parents[3] / "experiments/benchmarks/cubie_benchmarks"
    missing = []
    for path in sorted(benchmark_root.rglob("*.py")):
        if "__pycache__" in path.parts or "data" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        missing.extend(f"{path}:{node.lineno}: {node.name}" for node in ast.walk(tree)
                       if isinstance(node, FUNCTIONS) and not ast.get_docstring(node))
    assert not missing, "Missing benchmark function docstrings:\n" + "\n".join(missing)
