"""Execute the actual README snippets, including controls against false passes."""

import ast
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def readme_examples():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    blocks = re.findall(r"^```python\s*\n(.*?)^```\s*$", readme, re.MULTILINE | re.DOTALL)
    assert blocks, "README must contain executable Python examples"
    examples = {}
    for code in blocks:
        tests = [
            node.name for node in ast.parse(code).body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
        assert len(tests) == 1, "Each README Python block must define one pytest test"
        name = tests[0]
        assert name not in examples, f"Duplicate README example: {name}"
        examples[name] = code
    return examples


def run_examples(tmp_path, examples, terminal_input=""):
    """Use a fresh pytest process without the repository conftest or plugins."""
    paths = []
    for name, code in examples.items():
        path = tmp_path / f"{name}.py"
        path.write_text(code, encoding="utf-8")
        paths.append(str(path))
    config = tmp_path / "pytest.ini"
    config.write_text("[pytest]\n", encoding="utf-8")
    report = tmp_path / "results.xml"
    environment = os.environ.copy()
    environment.update({
        "PYTHONPATH": str(PROJECT_ROOT / "src"),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTEST_ADDOPTS": "",
    })
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-s", "--tb=short",
         "-c", str(config), "-p", "no:cacheprovider", f"--junitxml={report}",
         *paths],
        cwd=tmp_path, env=environment, input=terminal_input,
        capture_output=True, text=True, timeout=30, check=False,
    )
    output = process.stdout + process.stderr
    assert report.exists(), output
    cases = {case.attrib["name"]: case for case in ET.parse(report).iter("testcase")}
    assert set(cases) == set(examples), output
    for case in cases.values():
        assert case.find("error") is None, output
        assert case.find("skipped") is None, output
    return process.returncode, cases, output


def test_all_readme_python_examples_pass(readme_examples, tmp_path):
    status, cases, output = run_examples(tmp_path, readme_examples, "y\n\n")

    assert status == 0, output
    assert all(case.find("failure") is None for case in cases.values()), output


def test_readme_tax_example_rejects_faulty_target(readme_examples, tmp_path):
    """Dropping .run() must fail this control even if the positive test passes."""
    tree = ast.parse(readme_examples["test_tax"])
    target = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "calculate_tax"
    )
    target.body = [ast.Return(value=ast.Constant(value=0))]
    faulty_example = ast.unparse(ast.fix_missing_locations(tree))
    status, cases, output = run_examples(tmp_path, {"test_tax": faulty_example})

    assert status == 1, output
    failure = cases["test_tax"].find("failure")
    assert failure is not None, output
    assert "EBT-Assert failed" in failure.attrib["message"], output
    assert "Expected 119 | Actual 0" in failure.text, output


def test_readme_review_example_rejects_negative_decision(readme_examples, tmp_path):
    status, cases, output = run_examples(
        tmp_path, {"test_logging_review": readme_examples["test_logging_review"]},
        "n\nREADME review rejected\n",
    )

    assert status == 1, output
    failure = cases["test_logging_review"].find("failure")
    assert failure is not None, output
    assert "README review rejected" in failure.attrib["message"], output
