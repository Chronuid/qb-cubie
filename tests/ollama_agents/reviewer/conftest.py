"""Resolve the future reviewer lazily, under the inherited offline network guard."""

import importlib.util
import sys
from pathlib import Path

import pytest

from .support import SOURCES

FIXTURES = Path(__file__).parent / "fixtures"
ENTRY = Path(__file__).resolve().parents[3] / "examples/ollama-agents/reviewer.py"


@pytest.fixture
def reviewer_api(monkeypatch):
    def resolve(**kwargs):
        assert ENTRY.is_file(), "Agenten §5.2: examples/ollama-agents/reviewer.py is not implemented yet"
        monkeypatch.syspath_prepend(str(ENTRY.parent))
        spec = importlib.util.spec_from_file_location("cubie_ollama_reviewer", ENTRY)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, module)
        spec.loader.exec_module(module)
        factory = getattr(module, "ReviewerAdapter", None)
        assert callable(factory), "Agenten §5.2: missing ReviewerAdapter entry point"
        return factory(**kwargs)
    return resolve


@pytest.fixture
def review_workspace(tmp_path):
    def build(variant="conform"):
        root = tmp_path / variant / "visible"
        for name in SOURCES:
            source = FIXTURES / "visible" / (name + ".txt")
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        if variant == "faulty":
            (root / "escaping.py").write_bytes((FIXTURES / "faulty_escaping.py.txt").read_bytes())
        return root
    return build
