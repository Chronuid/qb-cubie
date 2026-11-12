"""Qualify the concrete v6 reference templates with actual pytest/EBT execution.

These are template calibration tests, independent of the missing team runner.
Each form must reject a known defect and accept the corrected public fixture.
"""

import os
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from v6_support import contract
from v6_templates import FORMS, render

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = Path(__file__).parent / "fixtures/v6/app.py"


@pytest.mark.parametrize("form", FORMS, ids=lambda form: form.id)
@pytest.mark.parametrize("mode", ["pytest", "cubie"])
@pytest.mark.parametrize("broken", [True, False], ids=["defective", "corrected"])
def test_a11_reference_form_distinguishes_real_production_behavior(tmp_path, form, mode, broken):
    def observe():
        source = PRODUCTION.read_text(encoding="utf-8")
        assert source.count(form.broken_from) == 1, form.id
        if broken:
            source = source.replace(form.broken_from, form.broken_to, 1)
        (tmp_path / "app.py").write_text(source, encoding="utf-8")
        (tmp_path / "test_case.py").write_text(render(form, mode), encoding="utf-8")
        env = os.environ | {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
            "PYTHONPATH": os.pathsep.join([str(tmp_path), str(ROOT / "src")]),
        }
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--noconftest", "-o", "addopts=",
             "--junitxml=result.xml", "test_case.py"],
            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30, check=False,
        )
        assert result.returncode in {0, 1}, result.stdout + result.stderr
        cases = ET.parse(tmp_path / "result.xml").findall(".//testcase")
        errors = sum(len(case.findall("error")) for case in cases)
        skipped = sum(len(case.findall("skipped")) for case in cases)
        failures = sum(len(case.findall("failure")) for case in cases)
        return result.returncode, len(cases), errors, skipped, failures

    contract(observe, (1 if broken else 0, 2 if form.id == "F01" else 1, 0, 0,
                       (2 if form.id == "F01" else 1) if broken else 0))
