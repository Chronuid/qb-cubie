"""An accountant exports paid orders and expects a command returning None."""

from functools import partial
from pathlib import Path

import pytest

from cubie import EBT, TempFS, WorldState

from .targets import export_orders


def test_file_only_contract_leaves_return_unchecked(tmp_path, check_case):
    """An initial file-only user contract deliberately does not promise None."""
    source = tmp_path / "orders.csv"
    source.write_text("id,status,quantity,unit_cents\n", encoding="utf-8")
    expected = tmp_path / "paid.csv"
    expected.write_text("id,total_cents\n", encoding="utf-8")
    case = EBT(
        target=partial(export_orders, "return-count"), arena=TempFS(),
        pre=WorldState(fs={"orders.csv": str(source)}),
        post=WorldState(fs={"paid.csv": str(expected)}),
    )
    result, _ = check_case(case, accepted=True)
    assert result.traces[0].outcome.returns == 0


@pytest.mark.parametrize("empty", [False, True], ids=["paid-order", "no-paid-orders"])
@pytest.mark.parametrize("fault", [None, "return-count", "include-unpaid", "missing-file", "extra-file"],
                         ids=["correct", "wrong-return", "wrong-content", "missing-output", "extra-output"])
def test_paid_order_export(tmp_path, monkeypatch, check_case, empty, fault):
    source = tmp_path / "orders.csv"
    source.write_text(
        "id,status,quantity,unit_cents\n"
        + ("A,unpaid,2,125\n" if empty else "A,paid,2,125\n")
        + "B,unpaid,1,999\n", encoding="utf-8",
    )
    expected_csv = "id,total_cents\n" + ("" if empty else "A,250\n")
    expected = tmp_path / "expected"
    expected.mkdir()
    (expected / "orders.csv").write_bytes(source.read_bytes())
    (expected / "paid.csv").write_text(expected_csv, encoding="utf-8")

    # Independently observe this exact application variant without Cubie.
    direct = tmp_path / "direct"
    direct.mkdir()
    (direct / "orders.csv").write_bytes(source.read_bytes())
    with monkeypatch.context() as context:
        context.chdir(direct)
        actual_return = export_orders(fault)
    actual_files = {p.name: p.read_bytes() for p in direct.iterdir()}
    desired_files = {p.name: p.read_bytes() for p in expected.iterdir()}
    conforms = actual_return is None and actual_files == desired_files
    assert conforms is (fault is None)

    case = EBT(
        target=partial(export_orders, fault), arena=TempFS(),
        pre=WorldState(fs={"orders.csv": str(source)}),
        post=WorldState(returns=None, fs={".": str(expected)}),
    )
    result, message = check_case(case, accepted=conforms)
    assert len(result.traces) == 1
    assert result.traces[0].outcome.returns == actual_return
    if message and fault == "return-count":
        assert f"Expected None | Actual {actual_return}" in message
    if message and fault in {"include-unpaid", "missing-file", "extra-file"}:
        assert "FS: Mismatch" in message
    assert Path.cwd() != direct
    assert source.read_bytes() == (expected / "orders.csv").read_bytes()
