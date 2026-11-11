# ruff: noqa: F811
"""Exercise both v4 treatments against real workspace edits."""

import pytest
from test_pilot_technical_ebt import pilot_session  # noqa: F401
from test_session_integration import action
from testguided_study.artifacts import read


@pytest.mark.parametrize('mode', ['pytest', 'cubie'])
def test_v4_small_edits_use_read_hash_and_require_refresh(pilot_session, mode):
    run, tree, _ = pilot_session
    edit = action('replace_text', path='module.py', old='= 1', new='= 2', reason='fix boundary')
    result, _, directory = run([
        action('read_file', path='module.py', start=1), edit,
        action('replace_text', path='module.py', old='= 2', new='= 3', reason='extend fix'),
        action('read_file', path='module.py', start=1),
        action('replace_text', path='module.py', old='= 2', new='= 3', reason='extend fix'),
        action('submit', reason='workspace edit probe'),
    ], mode=mode, design_version=4)
    assert result['status'] == 'submitted'
    assert (tree / 'module.py').read_text() == 'UNIQUE_IMPLEMENTATION = 3\n'
    assert read(directory / 'steps/0002-tool.json')['result']['code'] == 'read_required'
    first = read(directory / 'steps/0001-tool.json')
    last = read(directory / 'steps/0004-tool.json')
    assert first['executed_action']['expected_sha256'] != last['executed_action']['expected_sha256']
    assert first['result']['status'] == last['result']['status'] == 'completed'
