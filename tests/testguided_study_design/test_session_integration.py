"""Use real session/context/schema/evidence code with deterministic external ports."""

import json
from types import SimpleNamespace

import pytest
from ollama_agents.errors import AdapterError
from ollama_agents.schema import validate
from testguided_study import agent
from testguided_study.artifacts import freeze, load_config, read, verify, write
from testguided_study.design import ITERATION_PROMPT, PROMPT, SCHEMA
from testguided_study.design import default_design as v3_design

from qb_cubie import EBT, WorldState


def default_design(mode, guides):
    """Keep historical session contracts on the explicit v2 schema."""
    design = v3_design(mode, guides)
    design["core"].update(id="testguided-core-v2", prompt=PROMPT + ITERATION_PROMPT,
                          tools=[e["properties"]["action"]["const"] for e in SCHEMA["oneOf"]] + ["update_ledger"],
                          context={"strategy": "ledger", "version": 1})
    return design

from testguided_study.iteration import identity, load_design
from testguided_study.report import summarize
from testguided_study.smoke import generate


class Replay:
    def __init__(self, actions):
        self.actions = iter(actions)
        self.requests = []

    def chat(self, **kwargs):
        self.requests.append(kwargs)
        action = next(self.actions)
        if isinstance(action, Exception):
            raise action
        validate(action, kwargs["schema"])
        return {"action": action, "usage": {"input_tokens": 7, "output_tokens": 3}, "raw": {"replay": True}}


def action(name, **fields):
    return {"action": name, "stage": "inspect", **fields}


SEARCH = action("search_text", query="bounds")
SUBMIT = action("submit", reason="verified")


@pytest.fixture
def session(tmp_path, monkeypatch):
    generate(tmp_path / "input")
    config = load_config(tmp_path / "input/study.toml")
    config["budgets"].update(model_calls=20, tool_calls=20, wall_seconds=100, context_bytes=15000)
    current = {"patch": ""}
    guides = {"pytest": "pytest-specific guide", "cubie": "cubie-specific guide"}
    monkeypatch.setattr(agent, "patch", lambda *args: current["patch"])

    def execute(manager, sandbox, selected, timeout, limit):
        if selected["action"] == "write_file":
            current["patch"] = "implemented boundary"
            return {"status": "completed", "written": selected["path"]}
        if selected["action"] == "run_tests":
            return {"status": "completed", "observation": "pass" if current["patch"] else "assertion_failure",
                    "junit_xml": "PRIVATE_XML_NOT_SENT_TO_MODEL"}
        return {"status": "completed", "hits": [{"path": "bounds.py", "line": 1}]}

    monkeypatch.setattr(agent, "execute", execute)

    def run(actions, mode="pytest", design=None, clock=None):
        directory = tmp_path / "session"
        directory.mkdir()
        client = Replay(actions)
        row = {"mode": mode, "run_id": "0001", "seed": 42}
        result = agent.develop(None, None, SimpleNamespace(problem_statement="Fix bounds"), row,
                               config, guides, directory, client=client, design=design or default_design(mode, guides), clock=clock)
        return result, client, directory

    return run, config, guides


def check(target, expected):
    result = EBT(target=target, post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True


@pytest.mark.parametrize("mode", ["pytest", "cubie"])
def test_repeated_search_receives_feedback_then_reaches_verified_submission(session, mode):
    run, _, guides = session

    def observe():
        result, client, directory = run([
            SEARCH, SEARCH, SEARCH, action("read_file", path="bounds.py", start=1),
            action("run_tests", targets=["tests/test_bounds.py"]),
            action("write_file", path="bounds.py", content="fixed", reason="repair lower bound"),
            action("run_tests", targets=["tests/test_bounds.py"]), SUBMIT,
        ], mode)
        return (result["status"], result["model_calls"], result["tool_calls"],
                "No new evidence" in json.dumps(client.requests[3]["messages"]),
                "Observed assertion red" in json.dumps(client.requests[5]["messages"]),
                result["design_id"] == identity(default_design(mode, guides)),
                "PRIVATE_XML" not in json.dumps(client.requests),
                read(directory / "steps/0002-progress.json")["directive"],
                (directory / "full.patch").read_text())

    check(observe, ("submitted", 8, 7, True, True, True, True, "redirect", "implemented boundary"))


def test_ignored_feedback_continues_and_preserves_evidence(session):
    run, _, _ = session

    def observe():
        result, client, directory = run([SEARCH] * 12 + [SUBMIT])
        return result["status"], result["model_calls"], len(client.requests), (directory / "full.patch").exists()
    check(observe, ("submitted", 13, 13, True))


@pytest.mark.parametrize("errors,expected", [
    ([AdapterError("invalid_output", "missing action")], ("submitted", 2, 1)),
    ([AdapterError("invalid_output", "missing action")] * 2, ("submitted", 3, 2)),
    ([AdapterError("infrastructure_error", "offline")], ("infrastructure_error", 1, 0)),
    ([AdapterError("agent_timeout", "deadline")], ("submitted", 2, 1)),
])
def test_action_repairs_continue_while_transport_failures_remain_explicit(session, errors, expected):
    run, _, _ = session

    def observe():
        result, client, directory = run([*errors, SUBMIT])
        if errors[0].status == "invalid_output" and len(client.requests) > 1:
            assert "missing action" in json.dumps(client.requests[1]["messages"])
        assert read(directory / "steps/0000-response.json")["error"] == str(errors[0])
        return result["status"], result["model_calls"], result["repairs"]
    check(observe, expected)


def test_legacy_model_allowance_does_not_prevent_repair(session):
    run, config, _ = session
    config["budgets"]["model_calls"] = 1

    def observe():
        result, client, _ = run([AdapterError("invalid_output", "bad JSON"), SUBMIT])
        return result["status"], result["model_calls"], len(client.requests)
    check(observe, ("submitted", 2, 2))


def test_custom_design_controls_real_session_schema_and_prompt(session):
    run, _, guides = session
    design = default_design("pytest", guides)
    design["core"]["prompt"] = "custom core prompt"
    design["core"]["tools"] = ["submit"]
    design["specialization"]["examples"] = ["custom framework example"]

    def observe():
        result, client, _ = run([SUBMIT], design=design)
        request = client.requests[0]
        return (result["design_id"] == identity(design), "custom core prompt" in request["messages"][0]["content"],
                "custom framework example" in request["messages"][0]["content"],
                [entry["properties"]["action"]["const"] for entry in request["schema"]["oneOf"]])
    check(observe, (True, True, True, ["submit"]))


def test_ledger_update_is_visible_to_next_request(session):
    run, _, _ = session

    def observe():
        result, client, directory = run([
            action("update_ledger", hypothesis="lower bound missing", next="add regression", files=["bounds.py"]),
            SUBMIT])
        return (result["ledger"]["hypothesis"], "lower bound missing" in json.dumps(client.requests[1]["messages"]),
                read(directory / "steps/0000-tool.json")["result"]["updated"])
    check(observe, ("lower bound missing", True, True))


def test_legacy_tool_allowance_does_not_stop_execution(session):
    run, config, _ = session
    config["budgets"]["tool_calls"] = 1

    def observe():
        result, _, _ = run([SEARCH, SEARCH, SUBMIT])
        return result["status"], result["tool_calls"], result["model_calls"]
    check(observe, ("submitted", 2, 3))


def test_clock_deadline_prevents_tool_execution(session):
    run, _, _ = session
    ticks = iter([0, 0, 0, 101, 101])

    def observe():
        result, _, _ = run([SEARCH], clock=lambda: next(ticks))
        return result["status"], result["model_calls"], result["tool_calls"]
    check(observe, ("wall_budget", 1, 0))


def test_freeze_schedule_and_report_bind_custom_designs(tmp_path):
    source = tmp_path / "input"
    generate(source)
    config_path = source / "study.toml"
    config_path.write_text(config_path.read_text().replace('phase = "pilot"', 'phase = "development"')
                           + '\n[designs]\npytest = "pytest.json"\ncubie = "cubie.json"\n')
    designs = {}
    for mode in ("pytest", "cubie"):
        designs[mode] = default_design(mode, {"pytest": "guide p", "cubie": "guide c"})
        designs[mode]["specialization"]["examples"] = ["explicit example"]
        write(source / f"{mode}.json", designs[mode])

    def observe():
        frozen = tmp_path / "frozen"
        freeze(config_path, frozen)
        (source / "pytest.json").unlink()
        assert verify(frozen)["phase"] == "development"
        rows = read(frozen / "schedule.json")
        report = summarize(frozen)
        return (all(row["design_id"] == identity(designs[row["mode"]]) for row in rows),
                len({row["core_id"] for row in rows}),
                load_design(frozen / "designs/pytest.json") == designs["pytest"],
                report["by_design"]["development"][identity(designs["pytest"])])
    check(observe, (True, 1, True, {"scheduled": 1, "resolved": 0, "unavailable": 1}))


def test_measurement_cannot_bypass_qualification_by_omitting_campaign(tmp_path):
    source = tmp_path / "input"
    generate(source)
    config = source / "study.toml"
    config.write_text(config.read_text().replace('phase = "pilot"', 'phase = "measurement"'))
    tasks = read(source / "tasks.json")
    tasks[0].update(split="measurement", task_type="api_schema", change_kind="bugfix", test_scope="unit",
                    related_group="heldout", repo=read(source / "record.json")["repo"])
    write(source / "tasks.json", tasks)
    with pytest.raises(ValueError, match="qualification"):
        freeze(config, tmp_path / "frozen")
    assert not (tmp_path / "frozen").exists()


def test_test_run_timing_noise_does_not_hide_repeated_green(session, monkeypatch):
    run, _, _ = session
    count = [0]

    def execute(*args):
        count[0] += 1
        return {"status": "completed", "observation": "pass", "exit_code": 0, "timed_out": False,
                "stdout": f"1 passed in {count[0] / 100} seconds"}

    monkeypatch.setattr(agent, "execute", execute)
    check(lambda: run([action("run_tests", targets=["tests/test_bounds.py"])] * 10 + [SUBMIT])[0]["status"], "submitted")
