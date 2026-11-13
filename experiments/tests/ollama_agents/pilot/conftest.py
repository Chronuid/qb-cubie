"""Resolve only the missing pilot gate lazily; keep runner and EBT real."""

import importlib.util
import sys
from pathlib import Path

import pytest

from .support import pilot_inputs

ENTRY = Path(__file__).resolve().parents[4] / "experiments/ollama-agents/pilot.py"


@pytest.fixture
def pilot_api(monkeypatch):
    def resolve():
        assert ENTRY.is_file(), "Agenten §5.5: experiments/ollama-agents/pilot.py is not implemented yet"
        monkeypatch.syspath_prepend(str(ENTRY.parent))
        spec = importlib.util.spec_from_file_location("cubie_ollama_pilot", ENTRY)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, module)
        spec.loader.exec_module(module)
        target = getattr(module, "freeze_pilot", None)
        assert callable(target), "Agenten §5.5: missing freeze_pilot entry point"
        return target
    return resolve


@pytest.fixture
def prepared(tmp_path):
    return pilot_inputs(tmp_path / "study inputs")
