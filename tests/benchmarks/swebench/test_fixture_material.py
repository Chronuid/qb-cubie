"""Confirm that the synthetic patches provide a real failing and passing test."""

import shutil
import subprocess
import sys

import pytest

from ..contracts import accepted
from .conftest import GOLD, TEST_PATCH, git


@pytest.mark.parametrize("stage,code,summary", [("base", 1, "1 failed, 1 passed"), ("gold", 0, "2 passed")])
def test_synthetic_reference_material_really_distinguishes_base_and_gold(snapshot, tmp_path, stage, code, summary):
    root = tmp_path / "reference control"
    shutil.copytree(snapshot["repo"], root)
    git(root, "checkout", "--detach", snapshot["base"])
    patches = [TEST_PATCH] + ([GOLD] if stage == "gold" else [])
    for patch in patches:
        subprocess.run(["git", "-C", str(root), "apply", "-"], input=patch, text=True,
                       capture_output=True, check=True)
    accepted(lambda: subprocess.run(
        [sys.executable, "-m", "pytest", "test_total.py", "test_existing.py", "-q", "--tb=no"],
        cwd=root, capture_output=True, text=True, check=False),
        expected=lambda value: value.returncode == code and summary in value.stdout)
