"""Explicitly provision the local bases required by the repository's tests.

Run with the project interpreter after `uv sync --locked --group dev`:
    .venv/bin/python scripts/provision_test_arenas.py
This is an installation step and may access the network. Pytest never calls it.
"""

import os
import shutil
import stat
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from qb_cubie.core.arenas.pyvenv import ArenaBuilder, default_arena_path

# Keep codec versions aligned with uv.lock. All bases support both codecs
# without needing another provisioning step when a test switches codecs.
CODEC_PACKAGES = ["msgspec==0.22.0", "cloudpickle==3.1.2"]
PROFILES = {
    default_arena_path(): CODEC_PACKAGES,
    PROJECT_ROOT / "tests/.arenas/empty_venv": CODEC_PACKAGES,
    PROJECT_ROOT / "tests/.arenas/cowsay_env": [*CODEC_PACKAGES, "cowsay==6.1"],
    PROJECT_ROOT / "tests/.arenas/linter_env": [*CODEC_PACKAGES, "pylint==4.1.3"],
}


def _is_valid_venv(path: Path) -> bool:
    has_python = (path / "bin" / "python").exists() or (path / "Scripts" / "python.exe").exists()
    return (path / "pyvenv.cfg").is_file() and has_python


def _remove_readonly(func, path: str, exc: BaseException) -> None:
    if not isinstance(exc, PermissionError):
        raise exc
    os.chmod(path, stat.S_IMODE(os.lstat(path).st_mode) | stat.S_IWUSR)
    parent = os.path.dirname(path)
    if func in (os.unlink, os.rmdir) and parent:
        os.chmod(parent, stat.S_IMODE(os.lstat(parent).st_mode) | stat.S_IWUSR | stat.S_IXUSR)
    func(path)


def _remove_incomplete_venv(path: Path) -> None:
    if path.exists() and not _is_valid_venv(path):
        print(f"Removing incomplete arena base {path}", flush=True)
        shutil.rmtree(path, onexc=_remove_readonly)


def main():
    for path, packages in PROFILES.items():
        _remove_incomplete_venv(path)
        print(f"Provisioning {path}", flush=True)
        ArenaBuilder(str(path)).with_packages(packages).build()


if __name__ == "__main__":
    main()
