"""Build offline measurement inputs and genuine runner archives before testing new APIs."""

import json
import shutil
from pathlib import Path

import pytest

from cubie_benchmarks import init_smoke_suite, run_suite

from ..contracts import edit_json
from ..phase2.conftest import configure_fake
from ..phase3.conftest import FIXTURES, configure_agent, write_suite


def append_gate(suite, **changes):
    gate = {"id": "acceptance", "metric": "quality_pass_rate", "operator": "gte", "threshold": 1.0, **changes}
    lines = ["", "[[gates]]"]
    for key, value in gate.items():
        if key == "select":
            lines.extend(f"select.{name} = {json.dumps(items)}" for name, items in value.items())
        else:
            lines.append(f"{key} = {json.dumps(value)}")
    with suite.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return gate


def create_suite(root, behavior="reference"):
    suite = root / "sets/measurement.toml"
    init_smoke_suite(suite)
    configure_fake(suite, behavior, "review_agent")
    for name in ("review-paid-correct", "review-paid-faulty"):
        edit_json(root / f"scenarios/smoke/scenarios/{name}/scenario.json",
                  lambda case: case.update(types=["correctness", "team/payment"]))
    return suite


@pytest.fixture
def measurement_suite(tmp_path):
    return create_suite(tmp_path / "measurement inputs")


@pytest.fixture(scope="module")
def gate_recording(tmp_path_factory):
    suite = create_suite(tmp_path_factory.mktemp("measurement-recording"))
    append_gate(suite)
    result = run_suite(suite)
    assert len(result["runs"]) == 2 and all(run["quality_passed"] for run in result["runs"])
    return Path(result["output"])


@pytest.fixture
def gate_archive(tmp_path, gate_recording):
    target = tmp_path / "relocated results"
    shutil.copytree(gate_recording, target)
    return target


@pytest.fixture
def process_suite(tmp_path):
    root = tmp_path / "external process inputs"
    shutil.copytree(FIXTURES, root)
    source = root / "agents/jsonl_agent.py.txt"
    source.rename(source.with_suffix(""))
    configure_agent(root)
    suite = write_suite(root, 'benchmarks = ["review_agent"]', repetitions=2)
    text = suite.read_text(encoding="utf-8").replace("repetitions = 2", "repetitions = 2\nseed = 41")
    suite.write_text(text, encoding="utf-8")
    append_gate(suite)
    return suite
