"""Execute the actual monitor JavaScript against deterministic transport examples."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from testguided_study.artifacts import ROOT

from qb_cubie import EBT, WorldState


@pytest.mark.parametrize("scenario,calls,connection", [
    ("closing", 1, "closed"), ("offline", 10, "offline"),
    ("recover", 3, "closed"), ("finished", 2, "closed"),
    ("failed", 2, "closed"), ("interrupted", 2, "closed"), ("prepared", 2, "closed"), ("disconnect", 11, "offline"), ("malformed", 10, "offline"),
])
def test_monitor_polling_terminates_or_recovers(scenario, calls, connection):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required to execute the monitor JavaScript")

    def observe():
        result = subprocess.run(
            [node, str(Path(__file__).parent / "fixtures/monitor_poll.cjs"),
             str(ROOT / "testguided_study/monitor.html"), scenario],
            capture_output=True, text=True, check=True, timeout=10,
        )
        data = json.loads(result.stdout)
        return {"calls": data["calls"], "pending": data["pending"], "connection": data["connection"],
                "terminal_detail": "Monitor beendet" in data["detail"] if connection == "closed"
                else "Wiederverbindung beendet" in data["detail"],
                "reload_hint": "Seite neu laden" in data["banner"],
                "clock": data["clock"]}

    EBT(target=observe, post=WorldState(returns={
        "calls": calls, "pending": 0, "connection": connection, "terminal_detail": True,
        "reload_hint": connection == "offline", "clock": "Laufzeit 0:50" if connection == "closed" else "Laufzeit 1:40" if scenario == "disconnect" else "",
    })).run()
