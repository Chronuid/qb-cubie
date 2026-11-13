"""Lazy contract resolution keeps independent oracle cases runnable before implementation."""

import importlib.util
import sys
from pathlib import Path

import pytest

from .support import BASE, CODE_PATH, TASK

ENTRY = Path(__file__).resolve().parents[4] / "experiments/ollama-agents/developer.py"


@pytest.fixture
def developer_api(monkeypatch):
    def resolve(**kwargs):
        assert ENTRY.is_file(), "Agenten §5.3: experiments/ollama-agents/developer.py is not implemented yet"
        monkeypatch.syspath_prepend(str(ENTRY.parent))
        spec = importlib.util.spec_from_file_location("cubie_ollama_developer", ENTRY)
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, module)
        spec.loader.exec_module(module)
        factory = getattr(module, "DeveloperAdapter", None)
        assert callable(factory), "Agenten §5.3: missing DeveloperAdapter entry point"
        return factory(**kwargs)
    return resolve


@pytest.fixture
def developer_workspace(tmp_path):
    root = tmp_path / "visible"
    (root / "pricing").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pricing/__init__.py").write_text("")
    (root / CODE_PATH).write_text(BASE)
    (root / "task.md").write_text(TASK)
    (root / "README.md").write_text("Existing project documentation.\n")
    return root
