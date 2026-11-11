"""Run the separate testguided agent study from a source checkout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ollama-agents"))

from testguided_study.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
