import pytest
from retention import expired

def test_boundary():
    assert expired(30,30) is True
    assert expired(29,30) is False
    assert expired(0,0) is True

def test_invalid():
    with pytest.raises(ValueError): expired(-1,30)
    with pytest.raises(ValueError): expired(2,-1)
