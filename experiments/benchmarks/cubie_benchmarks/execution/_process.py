"""Run trusted smoke tools with bounded time and isolated environment variables."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from cubie_benchmarks.reporting._files import write_json


class ExecutionError(Exception):
    """Carry a structured execution failure without a fabricated evaluation."""

    def __init__(self, status, reason):
        """Initialize a structured execution failure."""
        super().__init__(reason)
        self.status = status


def invoke(context, command, directory, record):
    """Execute one tool call within episode time and call budgets."""
    remaining = context["deadline"] - time.monotonic()
    if remaining <= 0:
        raise ExecutionError("agent_timeout", "Episode wall time exhausted")
    context["tool_calls"] += 1
    if context["tool_calls"] > context["run"]["budgets"].get("tool_calls", float("inf")):
        raise ExecutionError("budget_exceeded", "tool_calls budget exhausted")
    observed = _execute(command, directory, remaining)
    write_json(record, observed)
    if observed["timed_out"]:
        raise ExecutionError("agent_timeout", "Episode process exceeded wall_time_seconds")
    return observed


def _execute(command, directory, timeout):
    """Capture a bounded subprocess observation in an isolated environment."""
    started = time.time()
    with subprocess.Popen(command, cwd=directory, env=_environment(), text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          start_new_session=os.name != "nt") as process:
        stdout, stderr, timed_out = _communicate(process, timeout)
        return {"command": command, "returncode": process.returncode, "stdout": stdout,
                "stderr": stderr, "timed_out": timed_out, "started_at": started, "finished_at": time.time()}


def _communicate(process, timeout):
    """Collect subprocess output and terminate timed-out process trees."""
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return stdout, stderr, False
    except subprocess.TimeoutExpired:
        _kill(process)
        stdout, stderr = process.communicate()
        return stdout, stderr, True


def _kill(process):
    """Terminate the complete started process group or Windows process tree."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _environment():
    """Build a subprocess environment without inherited provider credentials."""
    names = {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL"}
    return {**{key: value for key, value in os.environ.items() if key in names},
            "PATH": str(Path(sys.executable).parent),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"}
