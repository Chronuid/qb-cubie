"""Offline developer acceptance: frozen tests, local repair and honest final submissions."""

import json

import pytest

from ..conftest import tree_bytes
from ..reviewer.checks import records
from .checks import phase
from .support import (
    BOUNDARY_BUG,
    CODE_PATH,
    DOC,
    EXCEPTION_TEST,
    FALSE_ORACLE,
    GOOD,
    SUBMIT,
    TEST_PATH,
    TESTS,
    design,
    session,
    write,
)


@pytest.mark.parametrize("tests", [TESTS, EXCEPTION_TEST], ids=["ebt-threshold", "pytest-raises"])
def test_design_preserves_originals_and_red_is_immutable_noop(api, developer_api, developer_workspace, tmp_path, tests):
    root = developer_workspace
    before = tree_bytes(root)
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [write({TEST_PATH: tests}), SUBMIT])
    event = design(adapter, root, tests)
    assert tree_bytes(root) == {**before, TEST_PATH: tests.encode()}
    assert event["usage"] == {"input_tokens": 26, "output_tokens": 14, "cost": None}
    assert len(transport.requests) == 2


def test_green_repairs_locally_without_changing_frozen_tests(api, developer_api, developer_workspace, tmp_path, capsys):
    root = developer_workspace
    actions = [write({TEST_PATH: TESTS}), SUBMIT, write({CODE_PATH: BOUNDARY_BUG, "USAGE.md": DOC}),
               write({CODE_PATH: GOOD, "USAGE.md": DOC}), SUBMIT, SUBMIT]
    adapter, transport, evidence = session(api, developer_api, root, tmp_path, actions)
    design(adapter, root)
    green = phase(adapter, root, "green")
    frozen = tree_bytes(root)
    refactor = phase(adapter, root, "refactor")
    assert tree_bytes(root) == frozen and frozen[TEST_PATH] == TESTS.encode()
    assert frozen[CODE_PATH] == GOOD.encode() and frozen["USAGE.md"] == DOC.encode()
    assert green["usage"] == {"input_tokens": 39, "output_tokens": 21, "cost": None}
    assert refactor["usage"] == {"input_tokens": 13, "output_tokens": 7, "cost": None}
    assert len(transport.requests) == 6
    # Actual failed test detail reaches the next model call; runner sends no feedback.
    assert b"test_threshold" in transport.requests[3][0].data
    archive = records(evidence, tmp_path)
    assert any(step["phase"] == "green" and "test_threshold" in json.dumps(step["tool_result"]) for step in archive)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("bad", ["def test_broken(:\n    pass\n", "from absent_module import fee\n",
                                TESTS.replace("(100, 0)", "(100, 7)").replace("(101, 0)", "(101, 7)").replace(
                                    "with pytest.raises(ValueError):", "if False:")],
                         ids=["syntax", "import", "all-green"])
def test_test_design_repairs_non_business_red_before_submission(api, developer_api, developer_workspace, tmp_path, bad):
    root = developer_workspace
    actions = [write({TEST_PATH: bad}), write({TEST_PATH: TESTS}), SUBMIT]
    adapter, transport, _ = session(api, developer_api, root, tmp_path, actions)
    design(adapter, root)
    assert len(transport.requests) == 3
    assert b"test" in transport.requests[1][0].data


def test_false_oracle_remains_visible_and_frozen_on_correct_implementation(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    actions = [write({TEST_PATH: FALSE_ORACLE}), SUBMIT] + [write({CODE_PATH: GOOD, "USAGE.md": DOC})] * 3
    adapter, transport, evidence = session(api, developer_api, root, tmp_path, actions)
    design(adapter, root, FALSE_ORACLE)
    # Three valid proposals may still be submitted red: completed is no process approval.
    phase(adapter, root, "green")
    assert (root / TEST_PATH).read_text() == FALSE_ORACLE
    assert (root / CODE_PATH).read_text() == GOOD
    assert len(transport.requests) == 5
    steps = records(evidence, tmp_path)
    assert any(step["phase"] == "green" and "test_threshold" in json.dumps(step["tool_result"]) for step in steps)


@pytest.mark.parametrize("phase_name", ["green", "refactor"])
def test_forbidden_test_rewrite_rejected_atomically(api, developer_api, developer_workspace, tmp_path, phase_name):
    root = developer_workspace
    illegal = write({TEST_PATH: "def test_nothing():\n    pass\n", CODE_PATH: BOUNDARY_BUG})
    actions = [write({TEST_PATH: TESTS}), SUBMIT]
    if phase_name == "refactor":
        actions += [write({CODE_PATH: GOOD, "USAGE.md": DOC}), SUBMIT]
    adapter, _, _ = session(api, developer_api, root, tmp_path, actions + [illegal, illegal])
    design(adapter, root)
    if phase_name == "refactor":
        phase(adapter, root, "green")
    before = tree_bytes(root)
    phase(adapter, root, phase_name, "invalid_output")
    assert tree_bytes(root) == before


@pytest.mark.parametrize("target", [CODE_PATH, "README.md", "task.md", "../private.py", "/tmp/agent.py"])
def test_design_cannot_modify_originals_or_escape_workspace(api, developer_api, developer_workspace, tmp_path, target):
    root = developer_workspace
    action = write({TEST_PATH: TESTS, target: "unauthorized"})
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [action, action])
    before = tree_bytes(root)
    phase(adapter, root, "test_design", "invalid_output")
    assert tree_bytes(root) == before
    assert len(transport.requests) == 2


def test_model_budget_is_shared_across_phases(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path,
                                    [write({TEST_PATH: TESTS}), SUBMIT], models=2)
    design(adapter, root)
    before = tree_bytes(root)
    phase(adapter, root, "green", "budget_exceeded")
    assert tree_bytes(root) == before and len(transport.requests) == 2


def test_red_uses_zero_tokens_and_no_model_request(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [write({TEST_PATH: TESTS}), SUBMIT])
    phase(adapter, root, "test_design")
    event = phase(adapter, root, "red")
    assert event["usage"] == {"input_tokens": 0, "output_tokens": 0, "cost": None}
    assert len(transport.requests) == 2


def test_visible_tests_execute_in_copy_with_real_evidence(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    tests = "from pathlib import Path\nPath('test-marker.txt').write_text('executed')\n" + TESTS
    adapter, _, evidence = session(api, developer_api, root, tmp_path, [write({TEST_PATH: tests}), SUBMIT])
    design(adapter, root, tests)
    assert not (root / "test-marker.txt").exists()
    assert not list(root.rglob("__pycache__")) and not (root / ".pytest_cache").exists()
    steps = records(evidence, tmp_path)
    observations = [step["tool_result"] for step in steps if step["tool_result"]]
    assert any("test_threshold" in json.dumps(result) and "test_negative" in json.dumps(result)
               for result in observations)
    assert any(step["artifact_hashes"].get(TEST_PATH) for step in steps)


@pytest.mark.parametrize("error,status", [(TimeoutError("provider stalled"), "agent_timeout"),
                                          (ConnectionError("provider offline"), "infrastructure_error")])
def test_provider_errors_are_never_business_red(api, developer_api, developer_workspace, tmp_path, error, status):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [error])
    before = tree_bytes(root)
    phase(adapter, root, "test_design", status)
    assert tree_bytes(root) == before and len(transport.requests) == 1


def test_external_change_of_frozen_test_blocks_green(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [write({TEST_PATH: TESTS}), SUBMIT])
    design(adapter, root)
    (root / TEST_PATH).write_text("def test_replaced():\n    pass\n")
    before = tree_bytes(root)
    phase(adapter, root, "green", "invalid_output")
    assert tree_bytes(root) == before and len(transport.requests) == 2


@pytest.mark.parametrize("name", ["red", "green", "refactor"])
def test_phase_cannot_skip_test_design(api, developer_api, developer_workspace, tmp_path, name):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [])
    before = tree_bytes(root)
    phase(adapter, root, name, "invalid_output")
    assert tree_bytes(root) == before and not transport.requests
