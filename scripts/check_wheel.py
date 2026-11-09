"""Install one wheel in a fresh venv and test it outside the checkout.

Usage: python scripts/check_wheel.py dist
Only the standard library is needed to run this script. Installation may use
the network; tests receive only the wheel's declared runtime dependencies.
"""

import argparse
import os
import shutil
import subprocess
import tempfile
import venv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel_dir", type=Path, help="Directory containing exactly one Cubie wheel")
    args = parser.parse_args()
    wheels = list(args.wheel_dir.resolve().glob("cubie-*.whl"))
    if len(wheels) != 1:
        parser.error(f"Expected exactly one Cubie wheel, found {len(wheels)} in {args.wheel_dir}")

    # Do not inherit source paths, Python startup hooks or pytest configuration.
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("PYTHON", "PYTEST", "CUBIE_"))
    }
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory(prefix="cubie-wheel-") as temporary:
        root = Path(temporary)
        if root.is_relative_to(PROJECT_ROOT):
            raise RuntimeError("The temporary test directory must be outside the checkout (check TMPDIR/TEMP)")
        virtualenv = root / "venv"
        venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt").create(virtualenv)
        python = virtualenv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        environment["VIRTUAL_ENV"] = str(virtualenv)
        environment["PATH"] = str(python.parent) + os.pathsep + environment.get("PATH", "")
        tests = root / "tests"
        shutil.copytree(PROJECT_ROOT / "tests/wheel", tests)
        config = root / "pytest.ini"
        config.write_text("[pytest]\n", encoding="utf-8")

        def run(*arguments, timeout=300):
            subprocess.run(
                [str(python), "-I", *arguments], cwd=root, env=environment,
                check=True, timeout=timeout,
            )

        run("-m", "pip", "install", "--disable-pip-version-check", str(wheels[0]))
        run("-m", "pip", "check")
        run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config),
            str(tests / "smoke_installed.py"))


if __name__ == "__main__":
    main()
