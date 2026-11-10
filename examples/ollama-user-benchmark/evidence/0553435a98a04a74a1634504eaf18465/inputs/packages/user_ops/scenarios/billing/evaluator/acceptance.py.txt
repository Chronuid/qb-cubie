import pytest
from billing import billable_minutes

def test_rounding():
    assert billable_minutes(0) == 0
    assert billable_minutes(1) == 1
    assert billable_minutes(60) == 1
    assert billable_minutes(61) == 2
    assert billable_minutes(10**30+1) == (10**30+60)//60

def test_invalid():
    with pytest.raises(ValueError): billable_minutes(-1)
