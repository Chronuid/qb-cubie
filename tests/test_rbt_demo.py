from src.qb_cubie.rbt import RBT
import pytest

@pytest.mark.skip
def test_humanreviewer(): RBT(check="Cuty Kitty :3", target="Hello There").run()