import os
import sys
from pathlib import Path

# conftest.py is located in /tests, so the parent directory is your project root
PROJECT_ROOT = Path(__file__).parent.parent
# 1. Override the IDE's right-click behavior: force the CWD to the project root
os.chdir(PROJECT_ROOT)
# 2. Fix the pytest runner: make the src/ directory known for Cubie's framework modules
sys.path.insert(0, str(PROJECT_ROOT / "src"))