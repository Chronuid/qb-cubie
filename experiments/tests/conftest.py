import os
import sys
from pathlib import Path

# conftest.py is located in /experiments/tests, so parents[2] is the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# 1. Override the IDE's right-click behavior: force the CWD to the project root
os.chdir(PROJECT_ROOT)
# 2. Fix the pytest runner: make src/ and experimental packages importable
sys.path.insert(0, str(PROJECT_ROOT / "experiments/ollama-agents"))
sys.path.insert(0, str(PROJECT_ROOT / "experiments/benchmarks"))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

pytest_plugins = ["cubie_benchmarks.pytest_plugin"]
