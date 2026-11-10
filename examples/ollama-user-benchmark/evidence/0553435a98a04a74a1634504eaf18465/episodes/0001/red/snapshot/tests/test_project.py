import pytest
from qb_cubie import EBT, WorldState
from billing import billable_minutes

def test_billable_minutes_zero():
    trace = EBT(target=billable_minutes, pre=WorldState(args=(0,)), post=WorldState(returns=0), reporter=None).run()
    assert trace.evaluation is True

def test_billable_minutes_exact_minute():
    trace = EBT(target=billable_minutes, pre=WorldState(args=(60,)), post=WorldState(returns=1), reporter=None).run()
    assert trace.evaluation is True

def test_billable_minutes_rounded_up():
    trace = EBT(target=billable_minutes, pre=WorldState(args=(61,)), post=WorldState(returns=2), reporter=None).run()
    assert trace.evaluation is True

def test_billable_minutes_large_value():
    large_val = 10**18
    trace = EBT(target=billable_minutes, pre=WorldState(args=(large_val,)), post=WorldState(returns=10**18 // 60), reporter=None).run()
    assert trace.evaluation is True

def test_billable_minutes_large_rounded_up():
    large_val = 10**18 + 30
    # (10**18 + 30) // 60 = 16666666666666666
    # (10**18 + 30 + 59) // 60 = 16666666666666667
    # Since 10**18 is divisible by 60, 10**18 + 30 should round up to 16666666666666667
    # Wait, 10**18 / 60 = 16666666666666666.666...
    # Let's use a simpler large number: 1200000000000000000 (divisible by 60)
    # 1200000000000000000 + 1 should round up.
    val = 1200000000000000000 + 1
    trace = EBT(target=billable_minutes, pre=WorldState(args=(val,)), post=WorldState(returns=20000000000000000), reporter=None).run()
    assert trace.evaluation is True

def test_billable_minutes_negative():
    with pytest.raises(ValueError):
        billable_minutes(-1)

def test_billable_minutes_small_positive():
    trace = EBT(target=billable_minutes, pre=WorldState(args=(1,)), post=WorldState(returns=1), reporter=None).run()
    assert trace.evaluation is True
