# ruff: noqa: F811
"""Integration boundaries introduced by the technical pilot repairs."""

import json
from types import SimpleNamespace

import pytest
from test_pilot_technical_ebt import (
    SUBMIT,
    LocalSandbox,
    contract,
    failing_suite,
    pilot_session,  # noqa: F401 -- shared integration fixture
)
from test_session_integration import action
from testguided_study import agent, backend, execution, workspace
from testguided_study.artifacts import read
from testguided_study.design import default_design
from testguided_study.smoke import generate


def test_large_file_fallback_keeps_valid_pages_and_allows_rereading(pilot_session):
    run, _, config = pilot_session
    config['budgets']['context_bytes'] = 10500

    def observe():
        result, client, _ = run([action('read_file', path='large.py', start=1), SUBMIT])
        page = json.loads(client.requests[1]['messages'][-1]['content'])
        return (result['status'], page['truncated'], bool(page['text']), page['next_start'] > page['start'],
                all(len(json.dumps(r['messages'], ensure_ascii=False).encode()) <= 10500 for r in client.requests))
    contract(observe, ('submitted', True, True, True, True))


def test_full_error_details_remain_accessible_after_compaction(pilot_session):
    run, _, _ = pilot_session
    suite = failing_suite()

    def observe():
        result, client, directory = run([
            action('run_tests', targets=['.']), action('read_test_details', step=1, start=0), SUBMIT,
        ], test_result=suite)
        details = json.loads(client.requests[2]['messages'][-1]['content'])
        full = read(directory / 'steps/0000-tool.json')['result']['diagnostics']['errors'][0]
        return result['status'], details['hits'][0] == full, details['next_start']
    contract(observe, ('submitted', True, 1))


@pytest.mark.parametrize('step', [0, 1, 9999])
def test_error_details_cannot_read_current_future_or_private_steps(tmp_path, step):
    (tmp_path / 'evaluation').mkdir()
    (tmp_path / 'evaluation/result.json').write_text('{"patch":"PRIVATE_GOLD"}')

    def observe():
        result = agent.test_details(tmp_path, {'step': step, 'start': 0}, current_step=0, limit=4000)
        return result['status'], 'PRIVATE_GOLD' in json.dumps(result)
    contract(observe, ('tool_error', False))


def test_probe_preserves_real_node_ids_for_lowercase_test_classes(tmp_path):
    manager = LocalSandbox(tmp_path, False)
    (manager.tree / 'test_value.py').write_text(
        'class lowercase:\n    def test_value(self): assert False\n')
    (manager.tree / 'pytest.ini').write_text('[pytest]\npython_classes = lowercase\n')

    def observe():
        result = workspace.run_tests(manager, object(), ['test_value.py'], 20, 12000)
        return result['observation'], result['diagnostics']['errors'][0]['id']
    contract(observe, ('assertion_failure', 'test_value.py::lowercase::test_value'))


def test_original_visible_baseline_reaches_agent_without_private_tests(tmp_path, monkeypatch):
    generate(tmp_path / 'input')
    config = read_config(tmp_path)
    guides = {'pytest': 'short guide', 'cubie': 'short guide'}
    baseline = failing_suite(1)
    monkeypatch.setattr(agent, 'patch', lambda *_: '')
    captured = []

    class Client:
        def chat(self, **kwargs):
            captured.append(kwargs['messages'])
            return {'action': SUBMIT, 'usage': {}, 'raw': {}}

    def observe():
        directory = tmp_path / 'run'
        result = agent.develop(None, None, SimpleNamespace(problem_statement='Visible issue', test_patch='PRIVATE_GOLD'),
                               {'mode': 'pytest', 'run_id': '0001', 'seed': 42}, config, guides, directory,
                               client=Client(), design=default_design('pytest', guides), visible_baseline=baseline)
        sent = json.dumps(captured[0])
        return (result['status'], 'visible_baseline' in sent, 'existing failures' in sent,
                'PRIVATE_GOLD' in sent, read(directory / 'visible-baseline.json') == baseline)
    contract(observe, ('submitted', True, True, False, True))


def read_config(tmp_path):
    from testguided_study.artifacts import load_config
    return load_config(tmp_path / 'input/study.toml')


def test_preflight_profiles_visible_suite_before_private_reference_checks(tmp_path, monkeypatch):
    from testguided_study.artifacts import freeze, write

    generate(tmp_path / 'input')
    frozen = tmp_path / 'frozen'
    freeze(tmp_path / 'input/study.toml', frozen)
    calls = []
    monkeypatch.setattr(backend, 'runtime', dict)
    monkeypatch.setattr(execution, 'provider', lambda _: {'model': {'digest': 'model'}})
    monkeypatch.setattr(backend, 'image_identity', lambda *args: {'image_id': args[0], 'python': '3.13', 'pytest': '9', 'packages': {}})
    monkeypatch.setattr(backend, 'task_for', lambda *_: SimpleNamespace(patch='GOLD', FAIL_TO_PASS=['issue'], PASS_TO_PASS=['control']))

    def visible(root, item, config, image, directory):
        calls.append('visible')
        write(directory / 'visible-baseline.json', {'diagnostics': {'counts': {'failed': 0}}})

    def evaluate(*args):
        gold = args[-1] == 'GOLD'
        calls.append('gold' if gold else 'private_base')
        return {'available': True, 'resolved': gold, 'observation': 'pass' if gold else 'assertion_failure',
                'tests': {'issue': 'pass' if gold else 'fail', 'control': 'pass'}}

    monkeypatch.setattr(execution.admission, 'visible_baseline', visible)
    monkeypatch.setattr(backend, 'evaluate', evaluate)

    def observe():
        result = execution.preflight(frozen)
        ready = read(frozen / 'ready.json')
        return result['status'], calls, 'preflight/visible/0000/visible-baseline.json' in ready['preflight_files']
    contract(observe, ('ready', ['visible', 'private_base', 'gold'], True))
