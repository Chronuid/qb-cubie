"""EBT contracts for paired execution, failure evidence and monitor shutdown.

Only Docker and inference are replaced; freeze, schedule, execution, telemetry,
HTTP delivery, evidence manifests and reporting use the production code.
"""

import json
import threading
import urllib.request
from types import SimpleNamespace

import pytest
from test_launch import arguments
from testguided_study import agent, execution, launch
from testguided_study.artifacts import read, verify
from testguided_study.monitor import MonitorServer
from testguided_study.telemetry import Observer, snapshot

from qb_cubie import EBT, WorldState


@pytest.mark.parametrize("failure", [None, "setup", "model", "evaluation"])
def test_six_runs_reach_report_even_with_unavailable_attempt(tmp_path, monkeypatch, failure):
    managers = []
    monkeypatch.setattr(launch.images, "ensure", lambda *a, **kw: None)

    def preflight(root, observer):
        config = verify(root)
        identity = {"images": {mode: {"image_id": mode} for mode in ("pytest", "cubie", "evaluator")}}
        monkeypatch.setattr(execution, "ready", lambda root: (config, identity))

    monkeypatch.setattr(execution, "preflight", preflight)

    class Manager:
        def __init__(self):
            self.index = len(managers)
            self.cleaned = False
            managers.append(self)

        def start(self):
            if failure == "setup" and self.index == 2:
                raise ConnectionError("container unavailable")
            return self

        def cleanup_all(self):
            self.cleaned = True

    monkeypatch.setattr(execution.backend, "manager", lambda *a: Manager())
    monkeypatch.setattr(execution.backend, "task_for", lambda *a: SimpleNamespace(problem_statement="Visible issue"))
    monkeypatch.setattr(execution.backend, "prepare", lambda *a: None)
    monkeypatch.setattr(agent, "patch", lambda *a: "")
    monkeypatch.setattr(agent, "execute", lambda *a: {"status": "completed"})

    class Client:
        def chat(self, **kwargs):
            if failure == "model" and len(managers) == 3:
                from ollama_agents.errors import infrastructure
                raise infrastructure("Ollama connection lost")
            return {"action": {"action": "submit", "stage": "finish", "reason": "done"}, "usage": {}}

    monkeypatch.setattr(agent, "OllamaClient", lambda **kw: Client())

    def evaluate(*args):
        if failure == "evaluation" and len(managers) == 3:
            raise ConnectionError("evaluator unavailable")
        return {"available": True, "resolved": True}

    monkeypatch.setattr(execution.backend, "evaluate", evaluate)
    args = arguments(tmp_path, prepare_only=False, seeds=[17, 18, 19])

    def lifecycle():
        result = launch.start(args)
        result.pop("archive")
        state = snapshot(args.output)
        frozen = args.output / "frozen"
        rows = read(frozen / "schedule.json")
        results = [read(frozen / "runs" / row["run_id"] / "result.json") for row in rows]
        before = (frozen / "runs/0001/result.json").read_bytes()
        with pytest.raises(ValueError, match="never silently resumes"):
            execution.run(frozen)
        return {"state": state["state"], "completed": state["completed_runs"],
                "unavailable": state["unavailable_runs"], "managers_cleaned": all(m.cleaned for m in managers),
                "results": len(results), "report_saved": read(args.output / "report.json") == result,
                "pairs": result["complete_pairs"], "evidence_preserved": before == (frozen / "runs/0001/result.json").read_bytes()}

    EBT(target=lifecycle, post=WorldState(returns={
        "state": "finished", "completed": 6, "unavailable": int(failure is not None),
        "managers_cleaned": True, "results": 6, "report_saved": True,
        "pairs": 3 if failure is None else 2, "evidence_preserved": True,
    })).run()


@pytest.mark.parametrize("state", ["finished", "failed", "interrupted", "prepared"])
def test_attached_monitor_receives_final_state_before_socket_closes(tmp_path, state):
    def shutdown():
        observer = Observer(tmp_path)
        observer.emit("starting", "Running", state="running")
        server = MonitorServer(tmp_path)
        url = server.start()
        with urllib.request.urlopen(url + "/api/state", timeout=2) as response:
            assert not json.load(response)["monitor_closing"]
        observer.emit(state, "Final state", state=state, phase=state)
        closing = threading.Thread(target=server.close)
        closing.start()
        try:
            assert server.closing.wait(1)
            with urllib.request.urlopen(url + "/api/state", timeout=2) as response:
                final = json.load(response)
            closing.join(3)
            return final["state"], final["monitor_closing"], server.final_delivered.is_set(), closing.is_alive()
        finally:
            closing.join(4)

    EBT(target=shutdown, post=WorldState(returns=(state, True, True, False))).run()
