"""Exercise real pytest stubs without accepting undeclared exceptions or setup failures."""

import time

import pytest

from cubie_benchmarks.execution._pytest import observe


@pytest.mark.parametrize("phase,exception,message,declared,setup,outcome", [
    ("red", "NotImplementedError", "pending", True, False, "assertion_failure"),
    ("green", "NotImplementedError", "pending", True, False, "test_error"),
    ("red", "NotImplementedError", "pending", False, False, "test_error"),
    ("red", "NotImplementedError", "other", True, False, "test_error"),
    ("red", "RuntimeError", "pending", True, False, "test_error"),
    ("red", "NotImplementedError", "pending", True, True, "test_error"),
])
def test_expected_stub_is_only_business_red_in_declared_production_call(
        tmp_path, phase, exception, message, declared, setup, outcome):
    workspace = tmp_path / phase / "snapshot"
    workspace.mkdir(parents=True)
    (workspace / "app.py").write_text(f'def run():\n    raise {exception}({message!r})\n')
    test = workspace / "test_app.py"
    test.write_text("import pytest\nfrom app import run\n" + (
        "@pytest.fixture\ndef broken():\n    run()\ndef test_run(broken):\n    pass\n" if setup else
        "def test_run():\n    assert run() == 1\n"))
    reference = {"expected_red_exception": {"module": "app.py", "message": "pending"}} if declared else {}
    context = {"reference": reference, "deadline": time.monotonic() + 30, "tool_calls": 0,
               "run": {"budgets": {"tool_calls": 1}}}
    result = observe(context, workspace, test, tmp_path / phase / "observation.json")
    assert result["test_outcome"] == outcome
