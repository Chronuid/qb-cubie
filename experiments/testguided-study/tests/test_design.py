"""Check paired scheduling, leakage boundaries and outcome interpretation."""

import json
import tarfile

import pytest
from testguided_study.agent import messages
from testguided_study.artifacts import check_snapshot, freeze, read, schedule, verify
from testguided_study.design import SCHEMA
from testguided_study.report import interval, summarize
from testguided_study.smoke import generate
from testguided_study.workspace import classify, outcomes


def test_schedule_pairs_same_seeds_and_counterbalances_order():
    tasks = [{"id": f"task-{i}"} for i in range(7)]
    rows = schedule(tasks, [42, 137], 123)
    assert rows == schedule(tasks, [42, 137], 123)
    pairs = [rows[i:i+2] for i in range(0, len(rows), 2)]
    assert len(pairs) == 14
    assert sum(pair[0]["mode"] == "pytest" for pair in pairs) == 7
    for left, right in pairs:
        assert {left["mode"], right["mode"]} == {"pytest", "cubie"}
        assert (left["task_id"], left["seed"], left["pair_id"]) == (right["task_id"], right["seed"], right["pair_id"])


def test_freeze_copies_inputs_and_detects_changed_guide(tmp_path):
    inputs, frozen = tmp_path / "input", tmp_path / "frozen"
    generate(inputs)
    freeze(inputs / "study.toml", frozen)
    (inputs / "record.json").unlink()
    assert verify(frozen)["phase"] == "pilot"
    assert len(read(frozen / "schedule.json")) == 2
    (frozen / "guides.json").write_text("{}")
    with pytest.raises(ValueError, match="Frozen input changed"):
        verify(frozen)


def test_pilot_cannot_be_relabelled_measurement(tmp_path):
    generate(tmp_path / "input")
    config = tmp_path / "input/study.toml"
    config.write_text(config.read_text().replace('phase = "pilot"', 'phase = "measurement"'))
    with pytest.raises(ValueError, match="splits"):
        freeze(config, tmp_path / "frozen")


@pytest.mark.parametrize("name,content", [("../escape.py", b"pass"), ("evaluator/gold.py", b"pass"),
                                         ("README.md", b"use qb_cubie")])
def test_snapshot_rejects_unsafe_or_leaking_inputs(tmp_path, name, content):
    import io
    path = tmp_path / "snapshot.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        entry = tarfile.TarInfo(name)
        entry.size = len(content)
        archive.addfile(entry, io.BytesIO(content))
    with pytest.raises(ValueError):
        check_snapshot(path)


@pytest.mark.parametrize("xml,code,expected", [
    ('<testsuite><testcase><failure type="AssertionError"/></testcase></testsuite>', 1, "assertion_failure"),
    ('<testsuite><testcase><failure message="assert -2 == 0">tests/test_bounds.py:7: AssertionError</failure></testcase></testsuite>', 1, "assertion_failure"),
    ('<testsuite><testcase><failure type="ImportError"/></testcase></testsuite>', 1, "test_failure"),
    ('<testsuite><testcase><error/></testcase></testsuite>', 1, "invalid_test_run"),
    ('<testsuite><testcase><skipped/></testcase></testsuite>', 0, "invalid_test_run"),
    ('<testsuite/>', 0, "invalid_test_run"),
    ('<testsuite><testcase/></testsuite>', 0, "pass"),
    ('broken', 0, "invalid_test_run"),
])
def test_business_red_requires_observed_assertions(xml, code, expected):
    assert classify(code, xml) == expected


def test_context_preserves_task_and_whole_recent_exchanges():
    history = [[{"role": "assistant", "content": "old" * 500}, {"role": "user", "content": "x"}],
               [{"role": "assistant", "content": "new"}, {"role": "user", "content": "result"}]]
    request = messages("system", "original task", history, 500)
    assert request[1]["content"].startswith("original task")
    assert "1 older" in request[1]["content"]
    assert request[-2:] == history[-1]
    with pytest.raises(ValueError, match="context_bytes"):
        messages("system", "too big" * 1000, [], 100)


def test_actions_offer_test_edits_without_phase_freeze():
    from ollama_agents.schema import validate
    for stage in ("test", "implement", "refactor"):
        validate({"action": "write_file", "stage": stage, "path": "tests/test_existing.py",
                  "content": "def test_behavior():\n    assert True\n", "reason": "Correct the oracle"}, SCHEMA)


def test_no_runs_are_unknown_and_do_not_create_successes(tmp_path):
    generate(tmp_path / "input")
    freeze(tmp_path / "input/study.toml", tmp_path / "frozen")
    report = summarize(tmp_path / "frozen")
    assert report["complete_pairs"] == 0
    assert report["paired_task_mean_difference"] is None
    assert report["arms"]["cubie"]["unavailable"] == 1
    assert report["arms"]["cubie"]["resolved_per_scheduled"] == 0
    assert interval([1]) is None


def test_duplicate_seeds_are_rejected(tmp_path):
    generate(tmp_path / "input")
    config = tmp_path / "input/study.toml"
    config.write_text(config.read_text().replace("seeds = [42]", "seeds = [42, 42]"))
    with pytest.raises(ValueError, match="distinct"):
        freeze(config, tmp_path / "frozen")


def test_reference_data_is_only_in_private_record(tmp_path):
    generate(tmp_path / "input")
    record = json.loads((tmp_path / "input/record.json").read_text())
    assert "test_outside" not in record["problem_statement"]
    with tarfile.open(tmp_path / "input/snapshot.tar.gz") as archive:
        assert set(archive.getnames()) == {"bounds.py", "tests/test_bounds.py"}
        assert b"test_outside" not in archive.extractfile("tests/test_bounds.py").read()


def test_private_node_matching_does_not_confuse_identical_function_names():
    xml = ('<testsuite><testcase classname="tests.test_a" name="test_same"/>'
           '<testcase classname="tests.test_b" name="test_same"><failure/></testcase>'
           '<testcase classname="tests.test_c.TestBoundary" name="test_limit[1]"/>'
           '<testcase classname="tests.test_c.TestBoundary" name="test_limit[2]"><skipped/></testcase></testsuite>')
    nodes = ["tests/test_a.py::test_same", "tests/test_b.py::test_same", "tests/test_missing.py::test_same",
             "tests/test_c.py::TestBoundary::test_limit[1]", "tests/test_c.py::TestBoundary::test_limit"]
    assert list(outcomes(xml, nodes).values()) == ["pass", "fail", "missing", "pass", "skip"]
