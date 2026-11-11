# ruff: noqa: F811
"""Regression contracts for the observed pilot failures, including actual EBT execution."""

import json
import os
import subprocess
import sys

import pytest
from ollama_agents.schema import validate
from test_session_integration import action, session  # noqa: F401
from test_workspace_iteration import execute
from testguided_study import agent
from testguided_study.campaign import behavior_cycle
from testguided_study.controller import Controller, context_capacity
from testguided_study.design import default_design, design_schema
from testguided_study.workspace import PROBE
from testguided_study.workspace import test_diagnostics as diagnostics


def test_notes_do_not_consume_a_turn_or_overwrite_runner_facts(session):
    run, _, guides = session
    result, client, _ = run([
        action('read_file', path='bounds.py', start=1, note={
            'hypothesis': 'missing boundary', 'requirement': 'Fix bounds', 'next': 'add test'}),
        action('submit', reason='No reproduction yet')], design=default_design('pytest', guides))
    assert result['tool_calls'] == 1
    assert result['model_calls'] == 2
    assert 'missing boundary' in json.dumps(client.requests[1]['messages'])
    assert result['process_metrics']['first_read_call'] == 1


def test_alternating_notes_and_failed_path_are_bounded(session, monkeypatch):
    run, _, guides = session
    executed = []

    def fail(*args):
        executed.append(args[2])
        return {'status': 'tool_error', 'code': 'not_found', 'suggestions': ['src/requests/utils.py']}
    monkeypatch.setattr(agent, 'execute', fail)
    result, _, _ = run([action('read_file', path='requests/utils.py', start=1,
                              note={'next': f'retry {i}'}) for i in range(20)],
                       design=default_design('cubie', guides), mode='cubie')
    assert result['status'] == 'stalled'
    assert len(executed) == 2
    assert result['process_metrics']['rejected_retries'] >= 1


def test_conflict_requires_read_and_guard_does_not_execute_mutations():
    c = Controller(3)
    edit = action('replace_text', path='x.py', old='x', new='y', reason='fix', expected_sha256='a'*64)
    c.observe(edit, {'status': 'tool_error', 'code': 'edit_conflict'}, {}, 1)
    assert c.guard(edit)['code'] == 'read_required'
    c.observe(action('read_file', path='x.py', start=1), {'status': 'completed', 'sha256': 'b'*64}, {}, 2)
    assert c.guard(edit) is None


def test_navigation_and_hash_conflict_use_real_workspace(tmp_path):
    (tmp_path/'src').mkdir()
    source = tmp_path/'src/utils.py'
    source.write_text('value = 1\n')
    missing = execute(tmp_path, action('read_file', path='utils.py', start=1))
    assert json.loads(missing.stdout)['suggestions'] == ['src/utils.py']
    found = execute(tmp_path, action('find_paths', pattern='*utils.py', start=0))
    assert json.loads(found.stdout)['files'] == ['src/utils.py']
    response = execute(tmp_path, action('replace_text', path='src/utils.py', old='1', new='2',
                                       reason='fix', expected_sha256='0'*64))
    assert json.loads(response.stdout)['code'] == 'edit_conflict'
    assert source.read_text() == 'value = 1\n'


def test_schema_separates_navigation_and_prevents_standalone_notes():
    schema = design_schema(default_design('pytest', {'pytest': 'guide'}))
    names = {e['properties']['action']['const'] for e in schema['oneOf']}
    assert {'find_paths', 'search_content', 'collect_tests', 'check_baseline'} <= names
    assert not {'search_text', 'update_ledger'} & names
    validate(action('find_paths', pattern='*.py', start=0, note={'example': 'x'}), schema)


def test_final_test_version_required_for_qualification():
    red = {'observation': 'assertion_failure', 'targets': ['test.py'], 'tests': 'old', 'production': 'base'}
    green = {'observation': 'pass', 'targets': ['test.py'], 'tests': 'final', 'production': 'fix'}
    assert not behavior_cycle([red, green], require_versions=True)
    assert behavior_cycle([red | {'tests': 'final'}, green], require_versions=True)
    assert behavior_cycle([red | {'tests': 'final', 'baseline': True}, green], require_versions=True)
    assert not behavior_cycle([red | {'tests': 'final'}, green | {'production': 'base'}], require_versions=True)


def test_context_reserves_schema_and_output():
    limits = {'context_bytes': 40000}
    model = {'num_ctx': 16384, 'num_predict': 4096}
    assert 0 < context_capacity(limits, model, {'type': 'object'}) < 24576


@pytest.mark.parametrize('valid', [True, False])
def test_cubie_probe_records_real_contract_execution_and_failure(tmp_path, valid):
    evidence = tmp_path/'usage.json'
    plugin = tmp_path/'study_probe_test.py'
    plugin.write_text(PROBE.replace('EVIDENCE', repr(str(evidence))))
    test = tmp_path/'test_contract.py'
    test.write_text('from qb_cubie import EBT, WorldState\n'
                    'def test_contract():\n'
                    f'    result = EBT(target=lambda: 2, post=WorldState(returns={2 if valid else 3}), reporter=None).run()\n'
                    '    assert result.evaluation is True\n')
    env = dict(os.environ, PYTHONPATH=str(tmp_path), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    result = subprocess.run([sys.executable, '-m', 'pytest', '-p', 'study_probe_test', str(test),
                             '--rootdir', str(tmp_path), '-q'], check=False, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == (0 if valid else 1), result.stdout + result.stderr
    usage = json.loads(evidence.read_text())
    assert usage['ebt_executed'] == usage['ebt_evaluated'] == 1
    assert usage['ebt_passed'] == int(valid)


def test_mixed_failures_preserve_individual_diagnostics():
    xml = '<testsuite><testcase classname="tests.test_a" name="test_x"><failure message="wrong">tail</failure></testcase><testcase classname="tests.test_a" name="test_y"><error message="import"/></testcase></testsuite>'
    result = diagnostics(xml)
    assert result['counts']['failed'] == result['counts']['errors'] == 1
    assert [e['phase'] for e in result['errors']] == ['call', 'setup_or_collection']


def test_production_change_allows_rerunning_previously_cached_tests():
    c = Controller(3)
    test = action('run_tests', targets=['tests/test_x.py'])
    for call in (1, 2):
        c.observe(test, {'status': 'completed', 'observation': 'pass'}, {'tests': 't', 'production': 'p'}, call)
    c.observe(action('write_file', path='src/x.py', content='fix', reason='bug'),
              {'status': 'completed', 'written': 'src/x.py'}, {'tests': 't', 'production': 'fixed'}, 3)
    assert c.guard(test) is None


@pytest.mark.parametrize('mode', ['pytest', 'cubie'])
@pytest.mark.parametrize('correct', [True, False])
def test_shipped_guide_examples_are_executable_and_reject_wrong_behavior(tmp_path, mode, correct):
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    guide = (root/'experiments/testguided-study/guides'/f'{mode}.md').read_text()
    blocks = re.findall(r'```python\n(.*?)```', guide, re.DOTALL)
    assert len(blocks) == 3
    for index, block in enumerate(blocks):
        (tmp_path/f'test_example_{index}.py').write_text(block)
    (tmp_path/'module_under_test.py').write_text(
        f'def transform(x): return x * {2 if correct else 3}\n'
        f'def reject_order(x): raise {"ValueError" if correct else "TypeError"}("invalid order")\n'
        f'def create_report(source, output): output.write_text(source.read_text().{"upper" if correct else "lower"}())\n')
    result = subprocess.run([sys.executable, '-m', 'pytest', str(tmp_path), '--rootdir', str(tmp_path), '-q'],
                            check=False, capture_output=True, text=True, timeout=30,
                            env=dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=str(tmp_path)))
    assert result.returncode == (0 if correct else 1), result.stdout + result.stderr
    assert ('4 passed' if correct else '4 failed') in result.stdout


def test_later_test_change_invalidates_an_earlier_qualified_cycle():
    red = {'observation': 'assertion_failure', 'targets': ['test.py'], 'tests': 'old', 'production': 'base'}
    green = {'observation': 'pass', 'targets': ['test.py'], 'tests': 'old', 'production': 'fix'}
    assert not behavior_cycle([red, green], require_versions=True, final_tests='final')


def test_test_fixtures_and_explicit_targets_are_versioned_separately(tmp_path):
    (tmp_path/'tests').mkdir()
    fixture = tmp_path/'tests/expected.txt'
    fixture.write_text('strong expectation')
    (tmp_path/'regression.py').write_text('def test_custom(): assert True\n')
    (tmp_path/'app.py').write_text('value = 1\n')
    def snapshot():
        return json.loads(execute(tmp_path, {'action': 'snapshot', 'test_paths': ['regression.py']}).stdout)
    before = snapshot()
    fixture.write_text('weakened')
    after = snapshot()
    assert before['tests'] != after['tests']
    assert before['production'] == after['production']
    (tmp_path/'regression.py').write_text('def test_custom(): pass\n')
    final = snapshot()
    assert after['tests'] != final['tests']
    assert after['production'] == final['production']
