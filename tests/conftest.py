import os
import sys
from pathlib import Path

import pytest

# conftest.py is located in /tests, so the parent directory is your project root
PROJECT_ROOT = Path(__file__).parent.parent
# 1. Override the IDE's right-click behavior: force the CWD to the project root
os.chdir(PROJECT_ROOT)
# 2. Fix the pytest runner: make the src/ directory known for Cubie's framework modules
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _is_venv_dir(path: Path) -> bool:
    return (
        (path / "pyvenv.cfg").is_file()
        or (path / "bin" / "activate").is_file()
        or (path / "Scripts" / "activate").is_file()
    )


@pytest.fixture(scope="session")
def src_files():
    """Discover project sources while pruning caches and generated virtualenvs."""
    arena_envs_dir = PROJECT_ROOT / "src" / "qb_cubie" / "arenas" / "arena_envs"
    files = []
    for directory, children, names in (PROJECT_ROOT / "src").walk():
        if directory == arena_envs_dir:
            children[:] = []
        else:
            children[:] = [
                name for name in children
                if name != "__pycache__" and not _is_venv_dir(directory / name)
            ]
        files.extend(directory / name for name in names if name.endswith(".py"))
    assert files, "No Python sources found under src/."
    return tuple(sorted(files))
