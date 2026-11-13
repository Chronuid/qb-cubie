"""Executable v8 QA template calibration, independent of a v8 controller.

Each paired input/oracle is a separate test. A swapped implementation must fail,
which an uncorrelated set of EBT postconditions would incorrectly accept.
"""

import os
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from v8_support import BROKEN, FIXED, contract


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
@pytest.mark.parametrize("production", ["correct", "off-by-one", "swapped"])
def test_v8_37_qa_template_distinguishes_correct_wrong_and_swapped_results(tmp_path, mode, production):
    def observe():
        source = {"correct": FIXED, "off-by-one": BROKEN,
                  "swapped": "def double(value):\n    return 6 - value * 2\n"}[production]
        (tmp_path / "app.py").write_text(source)
        test = (
            "import pytest\nfrom app import double\n"
            "from qb_cubie import EBT, WorldState\n\n"
            "# REQ-1: the issue specifies both concrete input/output pairs.\n"
            '@pytest.mark.parametrize("value, expected", [(1, 2), (2, 4)])\n'
            "def test_double(value, expected):\n"
        )
        test += (
            "    result = EBT(target=double, pre=WorldState(args=(value,)),\n"
            "                 post=WorldState(returns=expected), reporter=None).run()\n"
            "    assert result.evaluation is True\n"
        ) if mode == "cubie" else "    assert double(value) == expected\n"
        (tmp_path / "test_case.py").write_text(test)
        repo = Path(__file__).resolve().parents[3]
        env = os.environ | {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
            "PYTHONPATH": os.pathsep.join([str(tmp_path), str(repo / "src")]),
        }
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--noconftest", "-o", "addopts=",
             "--junitxml=result.xml", "test_case.py"],
            cwd=tmp_path, env=env, capture_output=True, text=True, check=False, timeout=30,
        )
        assert process.returncode in {0, 1}, process.stdout + process.stderr
        cases = ET.parse(tmp_path / "result.xml").findall(".//testcase")
        return (process.returncode, len(cases), sum(c.find("failure") is not None for c in cases),
                sum(c.find("error") is not None for c in cases), sum(c.find("skipped") is not None for c in cases))
    contract(observe, (0, 2, 0, 0, 0) if production == "correct" else (1, 2, 2, 0, 0))
