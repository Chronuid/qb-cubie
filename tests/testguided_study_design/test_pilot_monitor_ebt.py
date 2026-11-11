"""Monitor requirements for latest versus explicitly selected archived steps."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from qb_cubie import EBT, WorldState

ROOT = Path(__file__).resolve().parents[2]


def monitor_example(selection):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required to execute the actual monitor JavaScript")
    result = subprocess.run([
        node, str(Path(__file__).parent / "fixtures/pilot_monitor.cjs"),
        str(ROOT / "experiments/testguided-study/testguided_study/monitor.html"), selection,
    ], check=True, capture_output=True, text=True, timeout=10)
    return json.loads(result.stdout)


@pytest.mark.parametrize("selection", ["latest", "pinned"])
def test_p17_selected_running_archive_refreshes_latest_but_keeps_pinned_step(selection):

    def observe():
        data = monitor_example(selection)
        return {"status_updated": data["stateCalls"] == 2,
                "correct_context": ("CONTEXT_ONE" if selection == "latest" else "CONTEXT_ZERO") in data["payload"],
                "new_step_listed": "1" in data["steps"] if selection == "latest" else True}

    result = EBT(target=observe, post=WorldState(returns={
        "status_updated": True, "correct_context": True, "new_step_listed": True}), reporter=None).run()
    assert result.evaluation is True


def test_p18_visible_step_number_matches_the_model_request_number():
    result = EBT(target=lambda: monitor_example("latest")["stepLabel"].split(" / ")[0],
                 post=WorldState(returns="2"), reporter=None).run()
    assert result.evaluation is True
