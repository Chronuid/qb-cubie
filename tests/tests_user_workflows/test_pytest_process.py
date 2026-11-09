"""Verify real pytest outcomes independently via its process status and XML."""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def test_faulty_user_examples_really_fail_pytest(tmp_path):
    package = Path(__file__).resolve().parent
    root = package.parent.parent
    config = tmp_path / "pytest.ini"
    config.write_text("[pytest]\n", encoding="utf-8")
    report = tmp_path / "results.xml"
    environment = dict(os.environ)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment["PYTEST_ADDOPTS"] = ""
    environment["PYTHONPATH"] = os.pathsep.join([str(root / "src"), str(root / "tests")])
    process = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", "-c", str(config),
         "-p", "no:cacheprovider", f"--junitxml={report}",
         str(package / "examples" / "acceptance_cases.py")],
        cwd=tmp_path, env=environment, capture_output=True, text=True, check=False, timeout=30,
    )
    assert process.returncode == 1, process.stdout + process.stderr
    cases = {case.attrib["name"]: case for case in ET.parse(report).iter("testcase")}
    expected_failures = {
        "test_unexpected_count", "test_unpaid_order_exported",
        "test_wrong_empty_stock_count", "test_stale_stock_success",
    }
    assert set(cases) == expected_failures | {"test_correct_export"}, process.stdout
    control = cases["test_correct_export"]
    assert control.find("failure") is None and control.find("error") is None
    assert control.find("skipped") is None
    for name in expected_failures:
        failure = cases[name].find("failure")
        assert failure is not None, process.stdout
        assert cases[name].find("error") is None
        assert cases[name].find("skipped") is None
        assert "EBT-Assert failed" in failure.attrib["message"]
    assert "Expected None | Actual 0" in cases["test_unexpected_count"].find("failure").text
    assert "Expected 0 | Actual 1" in cases["test_wrong_empty_stock_count"].find("failure").text
