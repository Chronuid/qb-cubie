"""Explicitly provision the local bases required by the repository's tests.

Run with the project interpreter after `uv sync --locked --group dev`:
    .venv/bin/python scripts/provision_test_arenas.py
This is an installation step and may access the network. Pytest never calls it.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from qb_cubie.arenas.pyvenv import CURRENT_DIR, ArenaBuilder

# Keep codec versions aligned with uv.lock. All bases support both codecs
# without needing another provisioning step when a test switches codecs.
CODEC_PACKAGES = ["msgspec==0.22.0", "cloudpickle==3.1.2"]
PROFILES = {
    CURRENT_DIR / "arena_envs" / "empty_test_env": CODEC_PACKAGES,
    PROJECT_ROOT / "tests/.arenas/empty_venv": CODEC_PACKAGES,
    PROJECT_ROOT / "tests/.arenas/cowsay_env": [*CODEC_PACKAGES, "cowsay==6.1"],
    PROJECT_ROOT / "tests/.arenas/linter_env": [*CODEC_PACKAGES, "pylint==4.1.3"],
}


def main():
    for path, packages in PROFILES.items():
        print(f"Provisioning {path}", flush=True)
        ArenaBuilder(str(path)).with_packages(packages).build()


if __name__ == "__main__":
    main()
