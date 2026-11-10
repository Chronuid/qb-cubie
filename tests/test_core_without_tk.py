"""GUTACHTEN 9.2 / B6: EBT and terminal reviews work without either Tk module."""

import subprocess
import sys
from pathlib import Path

import pytest

from qb_cubie import EBT, WorldState

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("missing", ["tkinter", "_tkinter"])
@pytest.mark.parametrize("feature", [
    "guard", "imports", "ebt", "tempfs", "headless", "gui-unavailable",
])
def test_core_contract_with_missing_tk(tmp_path, feature, missing):
    result = EBT(target=subprocess.run, pre=WorldState(
        args=([sys.executable, "-I", str(ROOT / "tests/wheel/tk_contract.py"),
               feature, missing, str(ROOT / "src")],),
        kwargs={"cwd": tmp_path, "capture_output": True, "text": True, "timeout": 20, "check": False},
    ), post=WorldState(returns=lambda process: process.returncode == 0), reporter=None).run()
    process = result.traces[0].outcome.returns
    assert result.evaluation is True, process.stdout + process.stderr
