"""Produce real offline archives with a deterministic process peer, never a model."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from qb_cubie.benchmarks import init_smoke_suite, run_suite

from ..contracts import edit_json
from ..phase2.conftest import configure_fake
from ..phase3.conftest import FIXTURES, configure_agent, write_suite


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@pytest.fixture(scope="module")
def pilot_recording(tmp_path_factory):
    root = tmp_path_factory.mktemp("pilot-peer") / "external"
    shutil.copytree(FIXTURES, root)
    peer = root / "agents/jsonl_agent.py.txt"
    source = peer.read_text(encoding="utf-8").replace("def review(workspace):", "def review(workspace, request):")
    source = source.replace("review(workspace) if", "review(workspace, request) if")
    source = source.replace('faulty = "> 5000" in source and MODE != "approve_all"',
                            'faulty = request["scenario_id"].endswith("error-family")')
    source = source.replace('"cost": None', '"cost": (None if request["scenario_id"].endswith("review-correct") '
                            'else 3 if request["scenario_id"].endswith("error-family") else 1)')
    peer.with_suffix("").write_text(source, encoding="utf-8")
    peer.unlink()
    for name in ("review-correct", "review-boundary"):
        edit_json(root / f"scenarios/{name}/scenario.json", lambda case: case.update(types=["correctness"]))
    for name in ("boundary-two", "boundary-three", "error-family"):
        shutil.copytree(root / "scenarios/review-boundary", root / "scenarios" / name)
        edit_json(root / f"scenarios/{name}/scenario.json", lambda case, name=name: case.update(
            id=name, group_id="other-project" if name == "error-family" else "shipping-review",
            types=["error_handling"] if name == "error-family" else ["correctness"]))
        edit_json(root / "package.json", lambda package, name=name: package["scenarios"].append(
            f"scenarios/{name}/scenario.json"))
    configure_agent(root)
    suite = write_suite(root, 'benchmarks = ["review_agent"]', repetitions=2)
    result = run_suite(suite)
    assert len(result["runs"]) == 10 and all(run["status"] == "completed" for run in result["runs"])
    return Path(result["output"])


@pytest.fixture
def pilot_archive(tmp_path, pilot_recording):
    destination = tmp_path / "archived pilot"
    shutil.copytree(pilot_recording, destination)
    return destination


def replace_observation(root, index, **changes):
    """Create explicitly simulated evaluation states and reseal fixture hashes."""
    result = read_json(root / "results.json")
    run = result["runs"][index]
    run.update(changes)
    write_json(root / "results.json", result)
    # The per-episode copy predates the addition of its own evidence link.
    record = root / next(path for path in run["evidence"] if path.endswith("/result.json"))
    saved = read_json(record)
    saved.update(changes)
    write_json(record, saved)
    manifest = read_json(root / "manifest.json")
    for name in manifest["artifact_hashes"]:
        manifest["artifact_hashes"][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    write_json(root / "manifest.json", manifest)


@pytest.fixture(scope="module")
def developer_recording(tmp_path_factory):
    root = tmp_path_factory.mktemp("pilot-developer")
    suite = root / "sets/pilot.toml"
    init_smoke_suite(suite)
    configure_fake(suite, "missing_red", "developer_agent")
    candidate = root / "agents/candidate.toml"
    text = (root / "agents/fake.toml").read_text(encoding="utf-8")
    candidate.write_text(text.replace('id = "fake"', 'id = "candidate"').replace('"missing_red"', '"reference"'),
                         encoding="utf-8")
    text = suite.read_text(encoding="utf-8").replace('profile = "agent-evaluation"', 'profile = "cubie-vs-pytest"')
    text = text.replace('agents = ["../agents/fake.toml"]', 'agents = ["../agents/fake.toml", "../agents/candidate.toml"]')
    text = text.replace("repetitions = 1", "repetitions = 2").replace("max_runs = 3", "max_runs = 8")
    text = text.replace("max_total_wall_time_seconds = 60", "max_total_wall_time_seconds = 160")
    suite.write_text(text, encoding="utf-8")
    result = run_suite(suite)
    assert len(result["runs"]) == 8 and all(run["quality_passed"] for run in result["runs"])
    return Path(result["output"])
