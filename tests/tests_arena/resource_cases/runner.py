"""Watchdog-owned process exercising the real EBT/arena lifecycle."""

import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

from qb_cubie import EBT, CloudpickleCodec, PyVenv, TempFS, WorldState


def record_process(directory, name):
    # Include kernel start time so emergency cleanup cannot kill a reused PID.
    pid = os.getpid()
    stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    pending = directory / f"{name}.pending"
    pending.write_text(json.dumps([pid, stat[19]]))
    pending.replace(directory / f"{name}.json")


def main(config):
    directory = Path(config["directory"])
    scratch = directory / "scratch"
    scratch.mkdir()
    tempfile.tempdir = str(scratch)
    observations = {}
    arena = None
    started = time.monotonic()
    try:
        if config["arena"] == "tempfs":
            arena = TempFS(**config["limits"])
        else:
            arena = PyVenv(
                env_path=config["base"], codec=CloudpickleCodec(), **config["limits"],
            )

        def target():
            import subprocess

            record_process(directory, "target")
            (directory / "workspace").write_text(str(Path.cwd()))
            mode = config["mode"]
            if mode.startswith("tree"):
                # Child and grandchild keep inherited output pipes open. Neither
                # creates another session: these are ordinary target descendants.
                script = '''
import json, os, signal, subprocess, sys, time
from pathlib import Path
directory, role, stubborn = sys.argv[1:]
if stubborn == "yes":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
pid = os.getpid()
stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
pending = Path(directory) / f"{role}.pending"
pending.write_text(json.dumps([pid, stat[19]]))
pending.replace(Path(directory) / f"{role}.json")
if role == "child":
    subprocess.Popen([sys.executable, "-c", SCRIPT, directory, "grandchild", stubborn])
while True:
    time.sleep(1)
'''
                script = "SCRIPT = " + repr(script) + "\n" + script
                subprocess.Popen([
                    sys.executable, "-c", script, str(directory), "child",
                    "yes" if config.get("stubborn") else "no",
                ])
                deadline = time.monotonic() + 5
                while not (directory / "grandchild.json").exists():
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Probe descendants did not start")
                    time.sleep(0.01)
                (directory / "tree_ready").touch()
            if mode in ("sleep", "tree_timeout"):
                while True:
                    time.sleep(1)
            if mode in ("output", "tree_output"):
                streams = config.get("streams", [1])
                count = config.get("bytes", 65536)
                # os.write also covers native output bypassing Python's print.
                payload = ("ü".encode() * ((count + 1) // 2))[:count]
                for stream in streams:
                    remaining = payload
                    while remaining:
                        remaining = remaining[os.write(stream, remaining):]
                if config.get("hang_after_output"):
                    while True:
                        time.sleep(1)
            return "completed"

        case = EBT(
            target=target, arena=arena, post=WorldState(returns="completed"),
            reporter=None, expect=config.get("expect", True),
        )
        try:
            if config.get("entrypoint") == "run":
                observations["returns"] = arena.run(target, (), {})
            else:
                trace = case.run()
                observations["evaluation"] = trace.evaluation
                observations["trace_count"] = len(trace.traces)
        finally:
            observations["run_trace_present"] = case.run_trace is not None
    except BaseException as error:  # noqa: BLE001 - report every remote failure to the independent oracle
        observations.update(
            error_type=type(error).__name__, message=str(error),
            is_timeout=isinstance(error, TimeoutError),
            is_runtime_error=isinstance(error, RuntimeError),
            traceback=traceback.format_exc(),
        )
    observations["elapsed"] = time.monotonic() - started
    observations["workspace_reset"] = arena is not None and arena.workspace_path is None
    observations["scratch_entries"] = [path.name for path in scratch.iterdir()]
    (directory / "result.json").write_text(json.dumps(observations))


if __name__ == "__main__":
    main(json.loads(Path(sys.argv[1]).read_text()))
