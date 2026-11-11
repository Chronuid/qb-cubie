"""Import the standalone experiment and its local inference adapter."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments/testguided-study"))
sys.path.insert(0, str(ROOT / "experiments/ollama-agents"))
