"""Real pytest/JUnit observations independently establish red and the false oracle."""

import runpy
import time

import pytest

from cubie_benchmarks.execution import _pytest

from ...benchmarks.contracts import accepted
from .support import (
    BASE,
    BOUNDARY_BUG,
    CODE_PATH,
    EXCEPTION_TEST,
    FALSE_ORACLE,
    GOOD,
    TEST_PATH,
    TESTS,
)


def observe(root, tmp_path, code, tests):
    (root / CODE_PATH).write_text(code)
    (root / TEST_PATH).write_text(tests)
    context = {"deadline": time.monotonic() + 30, "tool_calls": 0,
               "run": {"budgets": {"tool_calls": 1}}}
    return _pytest.observe(context, root, root / "tests", tmp_path / "observation.json")


@pytest.mark.parametrize("code,tests,outcome", [
    (BASE, TESTS, "assertion_failure"), (BASE, EXCEPTION_TEST, "assertion_failure"),
    (GOOD, TESTS, "passed"), (BOUNDARY_BUG, TESTS, "assertion_failure"),
    (GOOD, FALSE_ORACLE, "assertion_failure"), (BOUNDARY_BUG, FALSE_ORACLE, "passed"),
    ("def fee(amount):\n    raise NotImplementedError\n", EXCEPTION_TEST, "test_error"),
    (BASE, "def test_broken(:\n    pass\n", "import_error"),
    (BASE, "from absent_module import fee\n", "import_error"),
])
def test_real_runner_classifies_business_red_and_execution_errors(developer_workspace, tmp_path, code, tests, outcome):
    accepted(lambda: observe(developer_workspace, tmp_path, code, tests),
             expected=lambda value: value["test_outcome"] == outcome)


@pytest.mark.parametrize("amount,expected", [(0, 7), (99, 7), (100, 0), (101, 0)])
def test_reference_implementation_against_independent_pairs(tmp_path, amount, expected):
    source = tmp_path / "reference.py"
    source.write_text(GOOD)
    accepted(runpy.run_path(str(source))["fee"], amount, expected=expected)
