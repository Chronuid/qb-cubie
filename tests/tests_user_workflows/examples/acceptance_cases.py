"""Intentionally red user examples, run explicitly by test_pytest_process.py.

This filename deliberately does not match pytest's default test_*.py pattern.
Run manually with PYTHONPATH=src:tests from the repository root:
python -m pytest tests/tests_user_workflows/examples/acceptance_cases.py
Expected: one pass, four failures (exit code 1).
"""

from functools import partial

from tests_user_workflows.targets import Stock, availability, export_orders

from cubie import EBT, TempFS, WorldState


def export_case(tmp_path, fault=None):
    source = tmp_path / "orders.csv"
    source.write_text("id,status,quantity,unit_cents\nB,unpaid,1,999\n", encoding="utf-8")
    expected = tmp_path / "expected.csv"
    expected.write_text("id,total_cents\n", encoding="utf-8")
    return EBT(
        target=partial(export_orders, fault), arena=TempFS(),
        pre=WorldState(fs={"orders.csv": str(source)}),
        post=WorldState(returns=None, fs={"paid.csv": str(expected)}),
    )


def test_correct_export(tmp_path):
    export_case(tmp_path).run()


def test_unexpected_count(tmp_path):
    export_case(tmp_path, "return-count").run()


def test_unpaid_order_exported(tmp_path):
    export_case(tmp_path, "include-unpaid").run()


def test_wrong_empty_stock_count():
    EBT(target=partial(availability, "count", True), post=WorldState(returns=0)).run()


def test_stale_stock_success():
    case = EBT(target=Stock().reserve, post=WorldState(returns={"remaining": [1]}))
    case.run()
    case.run()
