"""Install one wheel in a fresh venv and test it outside the checkout.

Usage: python scripts/check_wheel.py dist
Only the standard library is needed to run this script. Installation may use
the network. Core, optional linter and benchmark profiles are checked separately;
pytest is installed explicitly as a test harness after checking the core alone.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
import venv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel_dir", type=Path, help="Directory containing exactly one qb-cubie wheel")
    args = parser.parse_args()
    wheels = list(args.wheel_dir.resolve().glob("qb_cubie-*.whl"))
    if len(wheels) != 1:
        parser.error(f"Expected exactly one qb-cubie wheel, found {len(wheels)} in {args.wheel_dir}")

    # Do not inherit source paths, Python startup hooks or pytest configuration.
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("PYTHON", "PYTEST", "QB_CUBIE_", "CUBIE_"))
    }
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory(prefix="qb-cubie-wheel-") as temporary:
        root = Path(temporary)
        if root.is_relative_to(PROJECT_ROOT):
            raise RuntimeError("The temporary test directory must be outside the checkout (check TMPDIR/TEMP)")
        virtualenv = root / "venv"
        venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt").create(virtualenv)
        python = virtualenv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        environment["VIRTUAL_ENV"] = str(virtualenv)
        # Only the test venv may supply optional linter executables.
        if os.name == "nt":
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            system_paths = [
                str(python.parent),
                os.path.join(system_root, "System32"),
                system_root,
                os.path.join(system_root, "System32", "Wbem"),
            ]
            orig_path = os.environ.get("PATH", "")
            if orig_path:
                system_paths.append(orig_path)
            environment["PATH"] = os.pathsep.join(system_paths)
            for var in ("SystemRoot", "COMSPEC", "PATHEXT", "TEMP", "TMP"):
                if var in os.environ:
                    environment[var] = os.environ[var]
        else:
            environment["PATH"] = str(python.parent)
        tests = root / "tests"
        shutil.copytree(PROJECT_ROOT / "tests/wheel", tests)
        shutil.copytree(PROJECT_ROOT / "tests/benchmarks/fixtures/phase3", tests / "phase3-example")
        config = root / "pytest.ini"
        config.write_text("[pytest]\n", encoding="utf-8")

        def run(*arguments, timeout=300):
            subprocess.run(
                [str(python), "-I", *arguments], cwd=root, env=environment,
                check=True, timeout=timeout,
            )

        run("-m", "pip", "install", "--disable-pip-version-check", str(wheels[0]))
        run("-m", "pip", "check")
        run("-c", "import importlib.util; import qb_cubie; "
            "assert all(importlib.util.find_spec(name) is None for name in "
            "('cubie', 'pytest', 'hypothesis', 'xdist', 'ruff', 'libcst', 'mypy', 'pylint', 'fsspec', 'path')); "
            "assert qb_cubie.EBT(target=sum, pre=qb_cubie.WorldState(args=([1, 2],)), "
            "post=qb_cubie.WorldState(returns=3)).run().evaluation is True")
        run("-m", "pip", "install", "--disable-pip-version-check", "pytest==9.2.0")
        for profile in ("core", "linters", "benchmarks"):
            if profile == "linters":
                run("-m", "pip", "install", "--disable-pip-version-check", f"{wheels[0]}[linters]")
            if profile == "benchmarks":
                run("-m", "pip", "install", "--disable-pip-version-check", f"{wheels[0]}[benchmarks]")
                environment["QB_CUBIE_TEST_WHEEL_SHA256"] = hashlib.sha256(wheels[0].read_bytes()).hexdigest()
            environment["QB_CUBIE_WHEEL_PROFILE"] = profile
            run("-m", "pip", "check")
            filename = "benchmark_installed.py" if profile == "benchmarks" else "smoke_installed.py"
            run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config), str(tests / filename))
            if profile == "benchmarks":
                run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config),
                    str(tests / "benchmark_custom_installed.py"))
                run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config),
                    str(tests / "benchmark_base_installed.py"))
                run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config),
                    str(tests / "benchmark_measurement_installed.py"))
                run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config),
                    str(tests / "ollama_agents_installed.py"))


if __name__ == "__main__":
    main()
