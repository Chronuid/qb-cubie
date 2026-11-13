"""Runnable oracle and I/O calibration; does not require a v9 implementation."""

import os
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from v9_support import BROKEN, FIXED, IO, NODE, Clock, contract, source_for_arm


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
@pytest.mark.parametrize("production", ["correct", "off-by-one", "swapped"])
def test_v9_40_paired_oracles_kill_both_mutations_in_both_arms(tmp_path, mode, production):
    def observe():
        source = {"correct": FIXED, "off-by-one": BROKEN,
                  "swapped": "def double(value):\n    return 6 - value * 2\n"}[production]
        (tmp_path / "app.py").write_text(source)
        test = (
            "import pytest\nfrom app import double\n"
            "from qb_cubie import EBT, WorldState\n\n"
            "# REQ-1 explicitly pairs input 1 with 2 and input 2 with 4.\n"
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
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--noconftest", "-o", "addopts=",
             "--junitxml=result.xml", "test_case.py"],
            cwd=tmp_path, env=os.environ | {
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
                "PYTHONPATH": os.pathsep.join([str(tmp_path), str(repo / "src")]),
            }, capture_output=True, text=True, check=False, timeout=30,
        )
        assert process.returncode in {0, 1}, process.stdout + process.stderr
        cases = ET.parse(tmp_path / "result.xml").findall(".//testcase")
        return (process.returncode, len(cases), sum(c.find("failure") is not None for c in cases),
                sum(c.find("error") is not None for c in cases), sum(c.find("skipped") is not None for c in cases))
    contract(observe, (0, 2, 0, 0, 0) if production == "correct" else (1, 2, 2, 0, 0))


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_v9_41_real_runner_port_recognizes_red_and_green_without_controller(tmp_path, mode):
    def observe():
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests/test_calc.py").write_text(source_for_arm(mode))
        (tmp_path / "conftest.py").write_text("# fixture\n")
        (tmp_path / "pytest.ini").write_text("[pytest]\n")
        io = IO(tmp_path, Clock(), real_tests=True)
        results = []
        for source in (BROKEN, FIXED):
            (tmp_path / "src/calc.py").write_text(source)
            # Remove import bytecode between rapid runs of similarly sized files.
            for cached in tmp_path.rglob("*.pyc"):
                cached.unlink()
            results.append(io({"action": "run_tests", "targets": [NODE], "baseline": False}))
        return ([r["observation"] for r in results],
                [r["diagnostics"]["executed"] for r in results],
                set(results[0]["case_results"]) == {NODE}, len(io.runs))
    contract(observe, (["assertion_failure", "pass"], [1, 1], True, 2))
