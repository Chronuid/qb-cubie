"""Record observational study state independently of agent context and budgets."""

import json
import os
import threading
import time
from pathlib import Path

from .artifacts import read, write


class Observer:
    def __init__(self, root, *, terminal=False):
        self.root = Path(root).resolve()
        self.directory = self.root / "monitor"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.terminal = terminal
        self.lock = threading.RLock()
        self.state = {"schema_version": 1, "state": "initializing", "phase": "initializing",
                      "started_at": time.time(), "updated_at": time.time(), "owner_pid": os.getpid(),
                      "total_runs": 0, "completed_runs": 0, "resolved_runs": 0,
                      "failed_runs": 0, "unavailable_runs": 0, "runs": [], "events": [], "active": {}, "agent": {}}

    def emit(self, kind, message, **changes):
        with self.lock:
            now = time.time()
            for name in ("active", "agent"):
                if name in changes:
                    self.state[name] = {**self.state.get(name, {}), **changes.pop(name)}
            self.state.update(changes, updated_at=now, message=message)
            event = {"sequence": self.state.get("sequence", 0) + 1, "time": now,
                     "kind": kind, "message": message, "run_id": self.state["active"].get("run_id"),
                     "step": self.state["active"].get("step")}
            self.state["sequence"] = event["sequence"]
            self.state["events"] = [*self.state["events"][-79:], event]
            with (self.directory / "events.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
            write(self.directory / "state.json", self.state)
            if self.terminal:
                print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)

    def bind(self, study, config, schedule):
        self.state["study_path"] = Path(study).resolve().relative_to(self.root).as_posix()
        self.state["study_id"] = config["study_id"]
        self.state["runs"] = [{**row, "status": "pending", "resolved": None} for row in schedule]
        self.emit("scheduled", f"{len(schedule)} Agentenläufe geplant", total_runs=len(schedule))

    def begin(self, row, config):
        self.state["agent"] = {}
        self.state["active"] = {**row, "model_calls": 0, "tool_calls": 0, "step": None,
                                "run_started_at": time.time(), "wall_seconds": config["budgets"]["wall_seconds"]}
        for run in self.state["runs"]:
            if run["run_id"] == row["run_id"]:
                run["status"] = "running"
        self.emit("run_started", f"{row['run_id']}: {row['mode']} · {row['task_id']}", phase="running", state="setup")

    def finish(self, result):
        for run in self.state["runs"]:
            if run["run_id"] == result["run_id"]:
                run.update(status=result.get("agent", {}).get("status", "unavailable"),
                           resolved=result["resolved"], total_seconds=result["total_seconds"])
                if 'completion' in result.get('agent', {}):
                    run['completion'] = result['agent']['completion']['status']
        complete = [run for run in self.state["runs"] if run["status"] not in {"pending", "running"}]
        self.emit("run_finished", f"{result['run_id']}: Ergebnis {result['resolved']}",
                  completed_runs=len(complete), resolved_runs=sum(r["resolved"] is True for r in complete),
                  failed_runs=sum(r["resolved"] is False for r in complete),
                  unavailable_runs=sum(r["resolved"] is None for r in complete), state="between_runs")


def snapshot(root):
    path = Path(root) / "monitor/state.json"
    state = read(path) if path.is_file() else {"schema_version": 1, "state": "waiting", "events": [], "runs": []}
    state["observed_at"] = time.time()
    pid = state.get("owner_pid")
    try:
        if pid:
            os.kill(pid, 0)
        state["owner_alive"] = bool(pid)
    except (ProcessLookupError, PermissionError):
        state["owner_alive"] = False
    return state


def emit(observer, kind, message, **changes):
    if observer is not None:
        observer.emit(kind, message, **changes)
