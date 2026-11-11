"""Exercise mandatory checkpoints through the actual agent loop in both arms."""

from types import SimpleNamespace

import pytest
from ollama_agents.schema import validate
from testguided_study import agent
from testguided_study.analysis import Analysis
from testguided_study.artifacts import ROOT, load_config, read
from testguided_study.design import default_design, design_schema


def assessment(phase):
    return {'action': 'analyze', 'stage': 'inspect', 'phase': phase,
                'requirement': 'Preserve encoded byte length', 'example': 'non-ASCII string',
                'observation': 'See source and test result', 'decision': 'unclear', 'next': 'Inspect or verify'}


@pytest.mark.parametrize('mode', ['pytest', 'cubie'])
def test_checkpoints_survive_edits_failures_and_submission(tmp_path, monkeypatch, mode):
    config = load_config(ROOT / 'study.toml')
    config['budgets']['model_calls'] = 20
    monkeypatch.setattr(agent, 'patch', lambda *_: '')
    outcomes = iter(['assertion_failure', 'pass'])

    def execute(_manager, _sandbox, action, *_):
        if action['action'] == 'run_tests':
            return {'status': 'completed', 'observation': next(outcomes)}
        return {'status': 'completed', 'sha256': 'a' * 64, 'text': 'value = 1'}

    monkeypatch.setattr(agent, 'execute', execute)
    actions = iter([
        {'action': 'read_file', 'stage': 'inspect', 'path': 'module.py', 'start': 1},
        assessment('reproduction'),
        {'action': 'write_file', 'stage': 'test', 'path': 'test_value.py', 'content': 'assert False', 'reason': 'regression'},
        {'action': 'run_tests', 'stage': 'test', 'targets': ['test_value.py']},
        assessment('diagnosis'),
        {'action': 'replace_text', 'stage': 'implement', 'path': 'module.py', 'old': '1', 'new': '2', 'reason': 'fix'},
        {'action': 'run_tests', 'stage': 'test', 'targets': ['test_value.py']},
        assessment('review'),
        {'action': 'submit', 'stage': 'finish', 'reason': 'verification documented'},
    ])
    requests = []

    class Client:
        def chat(self, **kwargs):
            requests.append(kwargs)
            action = next(actions)
            validate(action, kwargs['schema'])
            return {'action': action, 'usage': {}, 'raw': {'message': {'thinking': 'synthetic trace'}}}

    settings = {}

    def client_factory(**kwargs):
        settings.update(kwargs)
        return Client()

    monkeypatch.setattr(agent, 'OllamaClient', client_factory)
    result = agent.develop(None, None, SimpleNamespace(problem_statement='Fix byte length'),
                           {'mode': mode, 'run_id': '0001', 'seed': 42}, config,
                           {mode: 'guide'}, tmp_path)
    assert settings['think'] is True
    assert settings['options']['num_predict'] == 8192
    assert read(tmp_path / 'steps/0001-response.json')['raw']['message']['thinking'] == 'synthetic trace'
    assert all('synthetic trace' not in str(request['messages']) for request in requests)
    assert result['status'] == 'submitted'
    assert result['model_calls'] == 9
    assert set(result['ledger']['analysis']['records']) == {'reproduction', 'diagnosis', 'review'}
    assert read(tmp_path / 'steps/0004-tool.json')['result']['analysis_recorded'] == 'diagnosis'
    assert 'submit' not in names(requests[6]['schema'])
    assert 'submit' in names(requests[8]['schema'])
    assert 'write_file' not in names(requests[4]['schema'])
    assert requests[0]['schema'] != requests[1]['schema']


def names(schema):
    return {e['properties']['action']['const'] for e in schema['oneOf']}


def test_checkpoint_cannot_be_skipped_by_audit_stage_or_stale_review():
    schema = design_schema(default_design('pytest', {'pytest': 'guide'}))
    control = Analysis()
    assert 'analyze' not in names(control.schema(schema))
    assert 'replace_text' not in names(control.schema(schema))
    control.observe({'action': 'read_file'}, {'status': 'completed'})
    control.analyze(assessment('reproduction'))
    control.analyze(assessment('review'))
    assert 'submit' in names(control.schema(schema))
    control.observe({'action': 'write_file', 'stage': 'finish'}, {'status': 'completed'})
    assert 'submit' not in names(control.schema(schema))
    control.observe({'action': 'run_tests'}, {'status': 'completed', 'observation': 'invalid_test_run'})
    entry = next(e for e in control.schema(schema)['oneOf'] if e['properties']['action']['const'] == 'analyze')
    assert entry['properties']['phase']['enum'] == ['diagnosis']


def test_active_profiles_enable_thinking_and_preserve_budgets():
    for path in [ROOT / 'study.toml', *(ROOT / 'profiles').glob('*.toml')]:
        import tomllib
        config = tomllib.loads(path.read_text())
        assert config['ollama']['think'] is True
        assert config['ollama']['num_predict'] == 8192
