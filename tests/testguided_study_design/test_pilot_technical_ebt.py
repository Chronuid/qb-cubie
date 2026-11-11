"""Executable requirements from TECHNIKANALYSE-20261111-171515.md.

Introduced as red requirements and now expected to pass, without xfails. Real session, controller,
workspace, context and EBT code; deterministic model/test-run ports. No historical
archives, Docker, Ollama, or new runtime APIs are needed to collect this suite.
"""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pytest
from ollama_agents.errors import AdapterError
from test_session_integration import Replay, action
from test_workspace_iteration import execute as local_execute
from testguided_study import admission, agent, workspace
from testguided_study.artifacts import read, write
from testguided_study.controller import Controller, compact_observation
from testguided_study.design import default_design, design_schema
from testguided_study.iteration import context
from testguided_study.monitor import run_view
from testguided_study.telemetry import Observer

from qb_cubie import EBT, WorldState

ROOT = Path(__file__).resolve().parents[2]
SUBMIT = action("submit", reason="State verification and remaining limitations")


def contract(target, expected):
    result = EBT(target=target, post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True


def failing_suite(errors=8):
    """Many real JUnit failures sharing one long environmental root cause."""
    xml = ET.Element("testsuite")
    for index in range(errors):
        case = ET.SubElement(xml, "testcase", classname="tests.test_render", name=f"test_case_{index}")
        failure = ET.SubElement(case, "failure", message="TypeError: " + "root cause " * 45)
        failure.text = "intermediate stack frame\n" * 70 + "render.py:42: TypeError: incompatible argument"
    text = ET.tostring(xml, encoding="unicode")
    return {"status": "completed", "observation": "test_failure", "exit_code": 1,
            "timed_out": False, "stdout": "long traceback\n" * 2000, "stderr": "",
            "junit_xml": text, "diagnostics": workspace.test_diagnostics(text),
            "framework_usage": {"available": True, "collected": errors,
                                "test_ids": [f"tests/test_render.py::test_case_{i}" for i in range(errors)]},
            "baseline": False, "collection_only": False}


@pytest.fixture
def pilot_session(tmp_path, monkeypatch):
    tree = tmp_path / "workspace"
    tree.mkdir()
    (tree / "module.py").write_text("UNIQUE_IMPLEMENTATION = 1\n")
    (tree / "large.py").write_text(("# " + "unrelated source context " * 2 + "\n") * 160)
    (tree / "tests").mkdir()
    (tree / "tests/test_module.py").write_text("def test_value(): assert True\n")
    initial = {p.relative_to(tree).as_posix(): p.read_text() for p in tree.rglob("*.py")}
    guides = {mode: (ROOT / f"experiments/testguided-study/guides/{mode}.md").read_text()
              for mode in ("pytest", "cubie")}
    config = {"budgets": {"wall_seconds": 600, "model_calls": 24, "tool_calls": 24,
                           "command_seconds": 10, "context_bytes": 40000, "output_chars": 12000},
              "ollama": {"endpoint": "http://unused.invalid", "model": "replay", "think": False,
                         "temperature": 0.2, "num_ctx": 16384, "num_predict": 4096}}

    def patch(*_):
        current = {p.relative_to(tree).as_posix(): p.read_text() for p in tree.rglob("*.py")}
        return "" if current == initial else json.dumps(current, sort_keys=True)

    monkeypatch.setattr(agent, "patch", patch)

    def run(actions, *, mode="pytest", test_result=None, observer=None, design_version=3):
        def execute(manager, sandbox, selected, timeout, limit):
            if selected["action"] in {"run_tests", "collect_tests", "check_baseline"}:
                return copy.deepcopy(test_result or {
                    "status": "completed", "observation": "collected", "collection_only": True})
            response = local_execute(tree, selected)
            return workspace.bounded(json.loads(response.stdout), limit)

        monkeypatch.setattr(agent, "execute", execute)
        directory = tmp_path / "session"
        directory.mkdir()
        client = Replay(actions)
        result = agent.develop(object(), object(), SimpleNamespace(problem_statement="Fix module behavior"),
                               {"mode": mode, "run_id": "0001", "seed": 42}, config, guides,
                               directory, client=client, design=default_design(mode, guides, version=design_version), observer=observer)
        return result, client, directory

    return run, tree, config


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_p01_large_test_result_allows_next_model_request_with_counts_and_full_evidence(pilot_session, mode):
    run, _, _ = pilot_session
    suite = failing_suite()

    def observe():
        result, client, directory = run([action("run_tests", targets=["."]), SUBMIT],
                                        mode=mode, test_result=suite)
        reached_next_request = len(client.requests) == 2
        latest = json.loads(client.requests[-1]["messages"][-1]["content"]) if reached_next_request else {}
        return {"status": result["status"], "next_request": reached_next_request,
                "within_capacity": all(len(json.dumps(r["messages"], ensure_ascii=False).encode())
                                       <= result["context_policy"]["capacity_bytes"] for r in client.requests),
                "failed_count": latest.get("diagnostics", {}).get("counts", {}).get("failed"),
                "full_evidence": read(directory / "steps/0000-tool.json")["result"]["junit_xml"] == suite["junit_xml"]}

    contract(observe, {"status": "submitted", "next_request": True, "within_capacity": True,
                       "failed_count": 8, "full_evidence": True})


def test_p02_compaction_does_not_mutate_archived_evidence():
    def observe():
        suite = failing_suite()
        before = copy.deepcopy(suite)
        visible = compact_observation(suite)
        return suite == before, "junit_xml" not in visible, visible["diagnostics"]["counts"]["failed"]
    contract(observe, (True, True, 8))


def test_p03_evicted_file_content_can_be_read_again(pilot_session):
    run, _, _ = pilot_session

    def observe():
        result, client, directory = run([
            action("read_file", path="module.py", start=1),
            action("read_file", path="module.py", start=1),
            action("read_file", path="large.py", start=1),
            action("read_file", path="large.py", start=1),
            action("read_file", path="module.py", start=1), SUBMIT])
        # The need to reread is part of the setup, not an assumed property.
        before_reread = client.requests[4]["messages"]
        evicted = not any("UNIQUE_IMPLEMENTATION" in m["content"] for m in before_reread)
        reread = read(directory / "steps/0004-tool.json")["result"]
        return (evicted, result["status"], reread.get("status"),
                "UNIQUE_IMPLEMENTATION" in reread.get("text", ""))
    contract(observe, (True, "submitted", "completed", True))


def test_p04_repeated_missing_paths_still_stop_without_mutations(pilot_session):
    run, tree, _ = pilot_session

    def observe():
        result, _, directory = run([action("read_file", path="missing.py", start=1)] * 20)
        return result["status"], result["model_calls"] < 20, (directory / "full.patch").read_text(), (tree / "module.py").exists()
    contract(observe, ("stalled", True, "", True))


@pytest.mark.parametrize("mutate", [False, True])
def test_p05_test_selection_cannot_invent_a_production_change(pilot_session, mutate):
    run, _, _ = pilot_session

    def observe():
        actions = [action("collect_tests", targets=["module.py"])]
        if mutate:
            actions.append(action("write_file", path="module.py", content="UNIQUE_IMPLEMENTATION = 2\n", reason="fix behavior"))
        result, _, directory = run([*actions, SUBMIT])
        initial = read(directory / "initial-evidence.json")["versions"]
        return {"changed": result["process_metrics"]["first_production_change_call"],
                "production_equal": initial["production"] == result["final_versions"]["production"],
                "patch_empty": (directory / "full.patch").read_text() == ""}
    contract(observe, {"changed": 2 if mutate else None, "production_equal": not mutate, "patch_empty": not mutate})


@pytest.mark.parametrize("classname,name,expected", [
    ("tests.test_card", "test_render", "tests/test_card.py::test_render"),
    ("tests.test_requests.TestTimeout", "test_connect[timeout0]",
     "tests/test_requests.py::TestTimeout::test_connect[timeout0]"),
    ("tests.test_ansi", "test_private[;]", "tests/test_ansi.py::test_private[;]"),
])
def test_p06_failure_diagnostics_identify_the_actual_test_target(classname, name, expected):
    def observe():
        xml = ET.Element("testsuite")
        case = ET.SubElement(xml, "testcase", classname=classname, name=name)
        ET.SubElement(case, "failure", message="wrong output").text = "example.py:1: AssertionError"
        return workspace.test_diagnostics(ET.tostring(xml, encoding="unicode"))["errors"][0]["id"]
    contract(observe, expected)


@pytest.mark.parametrize("op,field,terms", [
    ("read_file", "start", ("line", "1")),
    ("search_content", "start", ("offset", "0")),
    ("find_paths", "pattern", ("glob", "*")),
])
def test_p07_tool_schema_explains_line_numbers_offsets_and_globs(op, field, terms):
    def observe():
        schema = design_schema(default_design("pytest", {"pytest": "guide"}))
        entry = next(e for e in schema["oneOf"] if e["properties"]["action"]["const"] == op)
        description = entry["properties"][field].get("description", "").lower()
        return all(term in description for term in terms)
    contract(observe, True)


def test_p08_literal_search_finds_first_definition_and_pages_without_loss(tmp_path):
    (tmp_path / "utils.py").write_text("def target(): pass\n" * 83)

    def observe():
        first = json.loads(local_execute(tmp_path, action("search_content", path="utils.py", query="def target", start=0)).stdout)
        second = json.loads(local_execute(tmp_path, action("search_content", path="utils.py", query="def target", start=first["next_start"])).stdout)
        return [h["line"] for h in first["hits"] + second["hits"]], second["next_start"]
    contract(observe, (list(range(1, 84)), None))


@pytest.mark.parametrize("condition", ["healthy", "snapshot_defect", "network_unavailable"])
def test_p09_admission_records_visible_baseline_separately_from_private_issue_tests(tmp_path, monkeypatch, condition):
    """New artifact contract: visible-baseline.json describes original visible tests.

    The evaluator port models a healthy private gold check despite an unrelated
    visible failure. The test requires admission to request and expose both scopes.
    """
    item = {"id": "example", "record": "record.json"}
    write(tmp_path / "record.json", {"instance_id": "example"})
    task = SimpleNamespace(test_patch="+def test_issue():\n+    assert False\n", patch="private gold patch",
                           test_files=["tests/test_issue.py"])
    monkeypatch.setattr(admission.backend, "task_for", lambda *_: task)
    managers = []

    def manager(*_):
        directory = tmp_path / f"container-{len(managers)}"
        directory.mkdir()
        local = LocalSandbox(directory, False)
        (local.tree / "test_value.py").unlink()
        tests = local.tree / "tests"
        tests.mkdir()
        (tests / "test_issue.py").write_text("def test_existing(): assert True\n")
        behavior = {"healthy": "assert True", "snapshot_defect": "raise TypeError('inconsistent Column')",
                    "network_unavailable": "raise OSError(101, 'Network is unreachable')"}[condition]
        (tests / "test_environment.py").write_text(f"def test_visible_environment():\n    {behavior}\n")
        local.start = lambda: local
        local.cleanup_all = lambda: None
        managers.append(local)
        return local

    def apply(manager, sandbox, content, directory, name):
        if content == task.test_patch:
            path = manager.tree / "tests/test_issue.py"
            path.write_text(path.read_text() + "\ndef test_issue(): assert True\n")

    monkeypatch.setattr(admission.backend, "manager", manager)
    monkeypatch.setattr(admission.backend, "prepare", lambda *_: None)
    monkeypatch.setattr(admission, "apply", apply)
    requests = []

    def evaluate(root, selected, config, image, directory, submitted, *, targets=None):
        visible = targets == ["."]
        requests.append((visible, submitted))
        directory.mkdir(parents=True, exist_ok=True)
        xml = ET.Element("testsuite")
        nodes = ["test_visible"] if visible else ["test_issue", "test_existing"]
        for name in nodes:
            case = ET.SubElement(xml, "testcase", classname="tests.test_issue", name=name)
            failed = condition != "healthy" if visible else name == "test_issue" and not submitted
            if failed:
                ET.SubElement(case, "failure", message=condition if visible else "missing behavior").text = "test_issue.py:1: AssertionError"
        (directory / "junit.xml").write_text(ET.tostring(xml, encoding="unicode"))
        return {"available": True, "observation": "assertion_failure" if (visible and condition != "healthy") or not submitted else "pass"}

    monkeypatch.setattr(admission.backend, "evaluate", evaluate)

    def observe():
        output = tmp_path / "admission"
        admission.admit(tmp_path, item, {"budgets": {"verification_seconds": 20}}, "fake-image", output)
        receipt = output / "visible-baseline.json"
        # Receipt format stays open; counts and original visible scope are mandatory.
        data = read(receipt) if receipt.exists() else {}
        return {"private_gold_checked": (False, task.patch) in requests,
                "receipt_saved": receipt.exists(),
                # Only the two original visible cases, never the added private case.
                "collected": data.get("diagnostics", {}).get("collected"),
                "failed": data.get("diagnostics", {}).get("counts", {}).get("failed")}
    contract(observe, {"private_gold_checked": True, "receipt_saved": True,
                       "collected": 2, "failed": int(condition != "healthy")})


def truncated_output():
    return AdapterError("invalid_output", "Response is incomplete or has invalid stop reason: length",
                        raw={"done": True, "done_reason": "length", "eval_count": 4096,
                             "message": {"role": "assistant", "content": '{"action":"write_file","content":"# repeated'}},
                        usage={"input_tokens": 3000, "output_tokens": 4096})


def test_p10_length_repair_asks_for_a_small_action_instead_of_repeating_full_file(pilot_session):
    run, _, _ = pilot_session

    def observe():
        result, client, directory = run([truncated_output(), SUBMIT])
        prompt = json.dumps(client.requests[1]["messages"]).lower()
        return (result["status"], result["repairs"],
                any(term in prompt for term in ("small edit", "small change", "short read", "replace_text"))
                and any(term in prompt for term in ("truncat", "length limit", "token limit")),
                read(directory / "steps/0000-response.json")["raw"]["eval_count"])
    contract(observe, ("submitted", 1, True, 4096))


def test_p11_two_truncated_answers_stop_without_executing_partial_write(pilot_session):
    run, _, _ = pilot_session

    def observe():
        result, client, directory = run([truncated_output(), truncated_output(), SUBMIT])
        return (result["status"], len(client.requests), result["tool_calls"],
                len(list((directory / "steps").glob("*-response.json"))), (directory / "full.patch").read_text())
    contract(observe, ("invalid_output", 2, 0, 2, ""))


def test_p12_live_monitor_keeps_rejected_raw_answer_visible(pilot_session, tmp_path):
    run, _, _ = pilot_session
    observer = Observer(tmp_path / "monitor-root")

    def observe():
        run([truncated_output(), truncated_output()], observer=observer)
        state = read(observer.directory / "state.json")
        response = state["agent"].get("response", {})
        return response.get("status"), response.get("raw", {}).get("done_reason"), response.get("usage", {}).get("output_tokens")
    contract(observe, ("invalid_output", "length", 4096))


def test_p13_archived_monitor_exposes_failed_answer_without_claiming_valid_action(pilot_session, tmp_path):
    run, _, _ = pilot_session

    def observe():
        _, _, directory = run([truncated_output(), truncated_output()])
        archive = tmp_path / "public-archive"
        archive.mkdir()
        (archive / "runs").mkdir()
        directory.rename(archive / "runs/0001")
        write(archive / "schedule.json", [{"run_id": "0001", "mode": "pytest"}])
        view = run_view(archive, "0001")
        return view["steps"], view["agent"]["action"], view["agent"]["response"]["raw"]["done_reason"]
    contract(observe, ([0, 1], None, "length"))


class LocalSandbox:
    """Run real pytest/probe commands in a temp tree; isolate /tmp artifacts too."""

    def __init__(self, root, foreign_plugin):
        self.tree = root / "workspace"
        self.scratch = root / "scratch"
        self.tree.mkdir()
        self.scratch.mkdir()
        (self.tree / "test_value.py").write_text("def test_value(): assert 2 + 2 == 4\n")
        (self.scratch / "unrelated_plugin.py").write_text("raise RuntimeError('UNRELATED_PLUGIN_IMPORTED')\n")
        self.env = dict(os.environ, PYTEST_PLUGINS="unrelated_plugin" if foreign_plugin else "")

    def exec(self, sandbox, cmd, *, timeout):
        cmd = cmd.replace("/tmp/", str(self.scratch) + "/").replace("PYTHONPATH=/tmp ", f"PYTHONPATH={self.scratch} ")
        cmd = cmd.replace("/workspace", str(self.tree)).replace("python3 ", f"{sys.executable} ")
        result = subprocess.run(cmd, shell=True, cwd=self.tree, env=self.env,
                                capture_output=True, text=True, timeout=timeout, check=False)
        return SimpleNamespace(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr, timed_out=False)


@pytest.mark.parametrize("foreign_plugin", [False, True])
def test_p14_unrelated_global_plugin_cannot_break_a_focused_test(tmp_path, foreign_plugin):
    manager = LocalSandbox(tmp_path, foreign_plugin)

    def observe():
        result = workspace.run_tests(manager, object(), ["test_value.py"], 20, 12000)
        return (result["observation"], result["diagnostics"].get("counts", {}).get("passed", 0),
                "UNRELATED_PLUGIN_IMPORTED" in result["stderr"])
    contract(observe, ("pass", 1, False))


def test_p15_mutation_conflicts_still_require_a_fresh_read():
    def observe():
        controller = Controller(3)
        edit = action("replace_text", path="module.py", old="1", new="2", expected_sha256="a" * 64, reason="fix")
        controller.observe(edit, {"status": "tool_error", "code": "edit_conflict"}, {}, 1)
        blocked = controller.guard(edit)["code"]
        controller.observe(action("read_file", path="module.py", start=1),
                           {"status": "completed", "sha256": "b" * 64}, {}, 2)
        return blocked, controller.guard(edit)
    contract(observe, ("read_required", None))


def test_p16_oversize_issue_is_explicit_instead_of_silently_truncated():
    def observe():
        try:
            context("guide", "mandatory issue " * 1000, [], {}, 200)
        except ValueError as error:
            return "context" in str(error).lower()
        return False
    contract(observe, True)


@pytest.mark.parametrize("target,category", [
    ("super_len", "target_not_found"), ("production.py", "no_tests_collected"),
])
def test_p19_invalid_collection_distinguishes_missing_target_from_empty_module(tmp_path, target, category):
    manager = LocalSandbox(tmp_path, False)
    (manager.tree / "production.py").write_text("def transform(value): return value\n")

    def observe():
        result = workspace.run_tests(manager, object(), [target], 20, 12000, collect=True)
        diagnostics = result["diagnostics"]
        return (result.get("code", diagnostics.get("category")),
                result["observation"] not in {"collected", "pass", "assertion_failure"},
                diagnostics.get("counts", {}).get("passed", 0))
    contract(observe, (category, True, 0))


def test_p20_collection_counts_collected_cases_without_claiming_execution(tmp_path):
    manager = LocalSandbox(tmp_path, False)

    def observe():
        result = workspace.run_tests(manager, object(), ["test_value.py"], 20, 12000, collect=True)
        return (result["observation"], result["diagnostics"]["collected"],
                result["framework_usage"]["collected"], result["diagnostics"]["counts"]["passed"])
    contract(observe, ("collected", 1, 1, 0))


def test_p21_repair_request_preserves_previous_rejected_answer_for_monitor_polling(pilot_session, tmp_path):
    run, _, _ = pilot_session

    class RecordingObserver(Observer):
        def __init__(self, root):
            super().__init__(root)
            self.requests = []

        def emit(self, kind, message, **changes):
            super().emit(kind, message, **changes)
            if kind == "model_request":
                self.requests.append(copy.deepcopy(self.state["agent"]))

    def contains_rejected_answer(value):
        if not isinstance(value, dict):
            return False
        if value.get("status") == "invalid_output" and value.get("raw", {}).get("done_reason") == "length":
            return True
        return any(contains_rejected_answer(child) for child in value.values())

    observer = RecordingObserver(tmp_path / "retained-error-monitor")

    def observe():
        result, _, _ = run([truncated_output(), SUBMIT], observer=observer)
        return result["status"], len(observer.requests), contains_rejected_answer(observer.requests[1])
    contract(observe, ("submitted", 2, True))
