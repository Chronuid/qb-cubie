import qb_cubie.rbt
from src.qb_cubie.rbt import RBT
import pytest

@pytest.mark.skip(reason="You need a human to test the human reviewer! :3")
def test_humanreviewer(): RBT(reviewer=qb_cubie.rbt.HumanReviewer, check="Cuty Kitty :3", target="Hello There").run()