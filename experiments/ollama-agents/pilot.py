"""Freeze a calibrated pilot using the installed example implementation."""

from ollama_agents.pilot import freeze_pilot
from ollama_agents.pilot.__main__ import main

__all__ = ["freeze_pilot"]

if __name__ == "__main__":
    raise SystemExit(main())
