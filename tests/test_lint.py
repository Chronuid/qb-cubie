"""Check src/ with the development linters, including unreachable code."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {
    "ruff": [
        "--isolated", "--no-cache", "--select=E4,E7,E9,F", "--output-format=concise",
    ],
    "pylint": [
        "--disable=all", "--enable=unreachable", "--reports=n", "--score=n",
        "--persistent=n", "--jobs=1",
    ],
    "mypy": [
        "--warn-unreachable", "--check-untyped-defs", "--show-error-codes",
        "--show-column-numbers", "--no-error-summary", "--no-pretty",
    ],
}


@pytest.mark.parametrize("tool", COMMANDS)
def test_src_lint(tool, src_files, tmp_path):
    result = run_linter(tool, src_files, tmp_path)
    assert result.returncode == 0, (
        f"{tool} failed (exit {result.returncode}).\n"
        f"{result.stdout}\n{result.stderr}"
    )


@pytest.mark.parametrize("tool, code, diagnostic", [
    ("ruff", "print(undefined_name)\n", "F821"),
    ("pylint", "def sample():\n    return 1\n    print('dead')\n", "W0101"),
    ("mypy", "def sample():\n    return 1\n    print('dead')\n", "[unreachable]"),
])
def test_linter_detects_regressions(tool, code, diagnostic, tmp_path):
    path = tmp_path / "probe.py"
    path.write_text(code, encoding="utf-8")
    result = run_linter(tool, [path], tmp_path)
    assert result.returncode != 0, result.stdout
    assert diagnostic in result.stdout, result.stdout + result.stderr


@pytest.mark.parametrize("tool", COMMANDS)
def test_linter_accepts_clean_source(tool, tmp_path):
    path = tmp_path / "probe.py"
    path.write_text("def sample():\n    return 1\n", encoding="utf-8")
    result = run_linter(tool, [path], tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def run_linter(tool, paths, tmp_path):
    """Run an installed linter with an isolated configuration and cache."""
    config = tmp_path / "empty.ini"
    config.write_text("[mypy]\n" if tool == "mypy" else "", encoding="utf-8")
    arguments = ["check"] if tool == "ruff" else [
        f"--{'config-file' if tool == 'mypy' else 'rcfile'}={config}",
    ]
    command = [sys.executable, "-m", tool, *arguments, *COMMANDS[tool]]
    command.extend(str(path) for path in paths)
    return subprocess.run(
        command, cwd=PROJECT_ROOT, text=True, capture_output=True, timeout=120,
        env={**os.environ, "MYPY_CACHE_DIR": str(tmp_path / "mypy-cache"),
             "PYLINTHOME": str(tmp_path / "pylint-cache")},
        check=False,
    )
