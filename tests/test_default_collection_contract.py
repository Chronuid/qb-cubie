"""GUTACHTEN 9.2: all fourteen historical cases belong to default collection."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from qb_cubie import EBT, WorldState

ROOT = Path(__file__).resolve().parents[1]
LEGACY_FILES = {
    "tests/tests_multiprocessors/mp_hypothesis.py": 7,
    "tests/tests_linter/tests_mypy.py": 3,
    "tests/tests_linter/tests_linter.py": 4,
}


def standard_filename(filename):
    path = Path(filename)
    name = path.name.replace("tests_", "test_", 1)
    if not name.startswith("test_"):
        name = "test_" + name
    return path.with_name(name).as_posix()


def canonical_node(node):
    filename, test = node.split("::", 1)
    if filename in LEGACY_FILES:
        filename = standard_filename(filename)
    return filename + "::" + test


@pytest.fixture(scope="module")
def collected_cases():
    def collect(*paths):
        process = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-o", "addopts=", *paths],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
            env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": ""},
        )
        assert process.returncode == 0, process.stdout + process.stderr
        return {canonical_node(line.strip()) for line in process.stdout.splitlines()
                if line.startswith("tests/") and "::test_" in line}

    explicit_paths = [name if (ROOT / name).exists() else standard_filename(name)
                      for name in LEGACY_FILES]
    return collect("tests"), collect(*explicit_paths)


@pytest.mark.parametrize("filename, count", LEGACY_FILES.items())
def test_historical_cases_are_part_of_default_collection(collected_cases, filename, count):
    regular, explicit = collected_cases
    expected = {node for node in explicit if node.startswith(standard_filename(filename) + "::")}
    assert len(expected) == count, "Explicit collection must still exercise every historical case"
    missing = sorted(expected - regular)
    result = EBT(target=lambda: missing, post=WorldState(returns=[]), reporter=None).run()
    assert result.evaluation is True, "Missing from default collection:\n" + "\n".join(missing)
