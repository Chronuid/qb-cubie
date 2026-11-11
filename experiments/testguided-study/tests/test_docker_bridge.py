"""Exercise the actual swegemma bridge while replaying only model responses."""

import json
import os

import pytest
from testguided_study.artifacts import freeze, read
from testguided_study.smoke import FIX, VISIBLE, generate

pytestmark = pytest.mark.skipif(os.environ.get("CUBIE_STUDY_DOCKER") != "1",
                                reason="Explicit local Docker integration opt-in")


class ReplayClient:
    def __init__(self, mode):
        test = (VISIBLE + "\ndef test_regression():\n"
                "    assert bounded(-2, 0, 5) == 0\n")
        if mode == "cubie":
            test = (VISIBLE + "\nfrom qb_cubie import EBT, WorldState\n\n"
                    "def test_regression():\n"
                    "    assert EBT(target=bounded, pre=WorldState(args=(-2, 0, 5)), "
                    "post=WorldState(returns=0), reporter=None).run().evaluation\n")
        self.actions = iter([
            {"action": "run_tests", "stage": "inspect", "targets": ["tests/test_bounds.py"]},
            {"action": "write_file", "stage": "test", "path": "tests/test_bounds.py", "content": test,
             "reason": "Add the missing lower-bound regression to the existing suite"},
            {"action": "run_tests", "stage": "test", "targets": ["tests/test_bounds.py"]},
            {"action": "write_file", "stage": "implement", "path": "bounds.py", "content": FIX,
             "reason": "Clamp values to the required interval"},
            {"action": "run_tests", "stage": "implement", "targets": ["tests/test_bounds.py"]},
            {"action": "write_file", "stage": "refactor", "path": "tests/test_bounds.py",
             "content": test + "\ndef test_upper():\n    assert bounded(9, 0, 5) == 5\n",
             "reason": "Extend the existing suite after green to cover the other boundary"},
            {"action": "run_tests", "stage": "refactor", "targets": ["tests/test_bounds.py"]},
            {"action": "check_baseline", "stage": "test", "targets": ["tests/test_bounds.py"]},
            {"action": "run_tests", "stage": "finish", "targets": ["tests/test_bounds.py"]},
            {"action": "submit", "stage": "finish", "reason": "Both boundaries verified"},
        ])

    def chat(self, **kwargs):
        from ollama_agents.schema import validate
        action = next(self.actions)
        validate(action, kwargs["schema"])
        assert "test_outside" not in json.dumps(kwargs["messages"])
        return {"action": action, "raw": {"replay": True},
                "usage": {"input_tokens": 10, "output_tokens": 10, "cost": None}}


def test_real_containers_allow_revising_original_tests_after_green(tmp_path, monkeypatch):
    from testguided_study import agent, execution
    from testguided_study.report import summarize
    generate(tmp_path / "input")
    frozen = tmp_path / "frozen"
    freeze(tmp_path / "input/study.toml", frozen)
    monkeypatch.setattr(execution, "provider", lambda config: {"model": {"digest": "offline-replay"}})
    assert execution.preflight(frozen)["status"] == "ready"
    actual = agent.OllamaClient
    monkeypatch.setattr(agent, "OllamaClient", lambda **kwargs: ReplayClient(current_mode[0]))
    original = execution.develop
    current_mode = [None]

    def develop(*args, **kwargs):
        current_mode[0] = args[3]["mode"]
        return original(*args, **kwargs)

    monkeypatch.setattr(execution, "develop", develop)
    assert execution.run(frozen)["status"] == "finished"
    report = summarize(frozen)
    assert report["complete_pairs"] == 1
    assert report["arms"]["pytest"]["resolved"] == report["arms"]["cubie"]["resolved"] == 1
    group = report["by_task_type"]["infrastructure_smoke"]
    for mode in ("pytest", "cubie"):
        assert group["arms"][mode]["measured_model_calls"] == 10
        assert group["arms"][mode]["measured_tool_calls"] == 9
        assert group["arms"][mode]["visible_test_observations"] == {"pass": 4, "assertion_failure": 2}
    for row in read(frozen / "schedule.json"):
        directory = frozen / "runs" / row["run_id"]
        assert "test_upper" in (directory / "full.patch").read_text()
        assert "test_regression" not in (directory / "evaluation/evaluated.patch").read_text()
        agent_result = read(directory / "agent.json")
        if row["mode"] == "cubie":
            assert agent_result["process_metrics"]["ebt_executed"] >= 1
        from testguided_study.campaign import behavior_cycle
        observations = agent_result["test_observations"]
        assert observations[-2]["baseline"] is True
        assert behavior_cycle(observations, require_versions=True)
        assert [v["observation"] for v in observations] == ["pass", "assertion_failure", "pass", "pass", "assertion_failure", "pass"]
    monkeypatch.setattr(agent, "OllamaClient", actual)
    with pytest.raises(ValueError, match="already exist"):
        execution.run(frozen)


def test_modified_visible_tests_cannot_make_a_wrong_fix_pass(tmp_path):
    from testguided_study import backend
    generate(tmp_path / "input")
    frozen = tmp_path / "frozen"
    freeze(tmp_path / "input/study.toml", frozen)
    from testguided_study.artifacts import verify
    config = verify(frozen)
    item = read(frozen / "tasks.json")[0]
    patch = """diff --git a/tests/test_bounds.py b/tests/test_bounds.py
--- a/tests/test_bounds.py
+++ b/tests/test_bounds.py
@@ -1,4 +1,2 @@
-from bounds import bounded
-
-def test_inside():
-    assert bounded(3, 0, 5) == 3
+def test_fake():
+    assert True
"""
    result = backend.evaluate(frozen, item, config, config["images"]["evaluator"], tmp_path / "evaluation", patch)
    assert result["available"] is True
    assert result["resolved"] is False
    assert result["observation"] == "assertion_failure"


def test_automatic_admission_derives_actual_node_ids_without_inference(tmp_path):
    from testguided_study import admission
    from testguided_study.artifacts import load_config, write
    from testguided_study.telemetry import Observer
    source = tmp_path / "input"
    generate(source)
    config = load_config(source / "study.toml")
    item = read(source / "tasks.json")[0]
    record_path = source / item["record"]
    record = read(record_path)
    record.pop("FAIL_TO_PASS")
    record.pop("PASS_TO_PASS")
    record["patch"] = record["patch"].rstrip("\n")
    record["test_patch"] = record["test_patch"].rstrip("\n")
    write(record_path, record)
    observer = Observer(tmp_path)
    admission.admit(source, item, config, config["images"]["evaluator"], tmp_path / "admission", observer=observer)
    admitted = read(record_path)
    assert admitted["FAIL_TO_PASS"] == ["tests/test_bounds.py::test_outside"]
    assert admitted["PASS_TO_PASS"] == ["tests/test_bounds.py::test_inside"]
    receipt = read(tmp_path / "admission/admission.json")
    assert receipt["before"]["tests/test_bounds.py::test_outside"] == "fail"
    assert receipt["after"]["tests/test_bounds.py::test_outside"] == "pass"
