"""Load the future example lazily and replay only the external transport boundary."""

import copy
import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "experiments/ollama-agents/common.py"
WRITE_SCHEMA = {
    "type": "object",
    "properties": {"files": {"type": "object", "additionalProperties": {"type": "string"},
                              "minProperties": 1}},
    "required": ["files"],
    "additionalProperties": False,
}
ACTION = {"files": {"src/fee.py": "def fee():\n    return 2\n"}}
MESSAGES = [{"role": "system", "content": "Return the requested JSON object."},
            {"role": "user", "content": "Implement the visible requirement."}]
OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 16384, "num_predict": 4096}


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline acceptance cases must never contact a model or the network")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)


@pytest.fixture
def api(monkeypatch):
    loaded = None

    def resolve(name):
        nonlocal loaded
        if loaded is None:
            assert COMMON.is_file(), (
                "Agenten §5.1: experiments/ollama-agents/common.py is not implemented yet"
            )
            monkeypatch.syspath_prepend(str(COMMON.parent))
            spec = importlib.util.spec_from_file_location("cubie_ollama_agents_common", COMMON)
            loaded = importlib.util.module_from_spec(spec)
            monkeypatch.setitem(sys.modules, spec.name, loaded)
            spec.loader.exec_module(loaded)
        target = getattr(loaded, name, None)
        assert callable(target), f"Missing shared adapter entry point: {name}"
        return target
    return resolve


@pytest.fixture
def response():
    return {"model": "gemma4:12b", "done": True, "done_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(ACTION)},
            "prompt_eval_count": 13, "eval_count": 7,
            "total_duration": 1000000, "load_duration": 1000}


class ReplayTransport:
    """A recording byte transport, with no parsing, retries or adapter decisions."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, *, timeout):
        self.requests.append((request, timeout))
        assert self.responses, "Unexpected extra HTTP request"
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response if isinstance(response, bytes) else json.dumps(response).encode("utf-8")


def client(api, transport):
    return api("OllamaClient")(
        endpoint="http://localhost:11434", model="gemma4:12b",
        options=copy.deepcopy(OPTIONS), think=False, transport=transport,
    )


def chat(client):
    return client.chat(messages=copy.deepcopy(MESSAGES), schema=copy.deepcopy(WRITE_SCHEMA), timeout=4.5)


def tree_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*")) if path.is_file()}


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "visible"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src/fee.py").write_bytes(b"def fee():\n    return 0\n")
    (root / "tests/test_fee.py").write_bytes(b"def test_fee():\n    assert False\n")
    (root / "task.md").write_text("Gebühr: einschließlich der Grenze.\n", encoding="utf-8")
    return root
