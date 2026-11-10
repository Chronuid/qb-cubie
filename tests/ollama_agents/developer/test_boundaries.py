"""Additional implementation counterexamples beyond the original acceptance cases."""

import json

import pytest

from ..conftest import tree_bytes
from ..reviewer.checks import records
from .checks import phase
from .support import (
    BOUNDARY_BUG,
    CODE_PATH,
    DOC,
    GOOD,
    SUBMIT,
    TEST_PATH,
    TESTS,
    design,
    session,
    write,
)


@pytest.mark.parametrize('mode', ['cubie', 'pytest'])
def test_explicit_mode_receives_framework_documentation(api, developer_api, developer_workspace, tmp_path, mode):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [write({TEST_PATH: TESTS}), SUBMIT])
    adapter.mode = mode
    design(adapter, root)
    payload = json.loads(transport.requests[0][0].data)
    context = json.loads(payload['messages'][1]['content'])
    assert context['mode'] == mode
    assert ('WorldState' if mode == 'cubie' else 'tmp_path') in context['framework_docs']


def test_zero_tool_budget_preserves_original_bytes(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [write({TEST_PATH: TESTS})], tools=0)
    before = tree_bytes(root)
    phase(adapter, root, 'test_design', 'budget_exceeded')
    assert tree_bytes(root) == before and len(transport.requests) == 1


@pytest.mark.parametrize('action', [{'action': 'shell', 'command': 'touch bad'},
                                  {'action': 'write_files', 'files': {TEST_PATH: TESTS}, 'command': 'bad'}])
def test_arbitrary_shell_fields_are_never_executed(api, developer_api, developer_workspace, tmp_path, action):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [action, action])
    before = tree_bytes(root)
    phase(adapter, root, 'test_design', 'invalid_output')
    assert tree_bytes(root) == before and len(transport.requests) == 2


def test_symlink_source_is_rejected_before_model_call(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    outside = tmp_path / 'private.txt'
    outside.write_text('private evidence')
    (root / 'leak.txt').symlink_to(outside)
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [])
    phase(adapter, root, 'test_design', 'invalid_output')
    assert not transport.requests and outside.read_text() == 'private evidence'


def test_unknown_token_measurement_survives_later_measured_call(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    adapter, transport, _ = session(api, developer_api, root, tmp_path, [write({TEST_PATH: TESTS}), SUBMIT])
    del transport.responses[0]['prompt_eval_count']
    event = design(adapter, root)
    assert event['usage'] == {'input_tokens': None, 'output_tokens': 14, 'cost': None}


def test_refactor_failure_is_repaired_against_unchanged_tests(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    actions = [write({TEST_PATH: TESTS}), SUBMIT, write({CODE_PATH: GOOD, 'USAGE.md': DOC}), SUBMIT,
               write({CODE_PATH: BOUNDARY_BUG}), SUBMIT, write({CODE_PATH: GOOD}), SUBMIT]
    adapter, transport, evidence = session(api, developer_api, root, tmp_path, actions)
    design(adapter, root)
    phase(adapter, root, 'green')
    phase(adapter, root, 'refactor')
    assert (root / CODE_PATH).read_text() == GOOD and (root / TEST_PATH).read_text() == TESTS
    assert len(transport.requests) == 8
    steps = records(evidence, tmp_path)
    assert any(step['phase'] == 'refactor' and step['status'] == 'invalid_output' for step in steps)


def test_three_green_proposals_without_docs_cannot_publish_completion(api, developer_api, developer_workspace, tmp_path):
    root = developer_workspace
    actions = [write({TEST_PATH: TESTS}), SUBMIT] + [write({CODE_PATH: GOOD})] * 4
    adapter, transport, _ = session(api, developer_api, root, tmp_path, actions)
    design(adapter, root)
    phase(adapter, root, 'green', 'invalid_output')
    assert len(transport.requests) == 6
    assert (root / TEST_PATH).read_text() == TESTS and not (root / 'USAGE.md').exists()
