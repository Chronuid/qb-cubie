import os
import sys
from pathlib import Path

import pytest

# conftest.py is located in /tests, so the parent directory is your project root
PROJECT_ROOT = Path(__file__).parent.parent
# 1. Override the IDE's right-click behavior: force the CWD to the project root
os.chdir(PROJECT_ROOT)
# 2. Fix the pytest runner: make src/ and experimental benchmark sources importable
sys.path.insert(0, str(PROJECT_ROOT / "experiments/benchmarks"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

pytest_plugins = ["cubie_benchmarks.pytest_plugin"]


@pytest.fixture(scope="session")
def src_files():
    """Discover project sources while pruning caches and generated virtualenvs."""
    files = []
    for directory, children, names in (PROJECT_ROOT / "src").walk():
        children[:] = [
            name for name in children
            if name != "__pycache__" and not (directory / name / "pyvenv.cfg").is_file()
        ]
        files.extend(directory / name for name in names if name.endswith(".py"))
    assert files, "No Python sources found under src/."
    return tuple(sorted(files))
