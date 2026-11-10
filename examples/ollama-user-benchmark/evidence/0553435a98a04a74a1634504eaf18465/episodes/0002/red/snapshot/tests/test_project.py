import pytest
from qb_cubie import EBT, WorldState
from retention import expired

def test_expired_valid_true():
    trace = EBT(target=expired, pre=WorldState(args=(10, 5)), post=WorldState(returns=True), reporter=None).run()
    assert trace.evaluation is True

def test_expired_valid_false():
    trace = EBT(target=expired, pre=WorldState(args=(3, 5)), post=WorldState(returns=False), reporter=None).run()
    assert trace.evaluation is True

def test_expired_equal_true():
    trace = EBT(target=expired, pre=WorldState(args=(5, 5)), post=WorldState(returns=True), reporter=None).run()
    assert trace.evaluation is True

def test_expired_negative_age():
    with pytest.raises(ValueError):
        expired(-1, 5)

def test_expired_negative_retention():
    with pytest.raises(ValueError):
        expired(10, -1)

def test_expired_negative_both():
    with pytest.raises(ValueError):
        expired(-1, -1)