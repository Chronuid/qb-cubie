import pytest
import qb_cubie.core.rbt
from qb_cubie.core.rbt import RBT


@pytest.mark.skip(reason="You need a human to test the human reviewer! :3")
def test_humanreviewer():
    RBT(reviewer=qb_cubie.core.rbt.HumanReviewer(), check="Cuty Kitty :3", target="Hello There").run()
