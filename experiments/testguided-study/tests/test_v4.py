"""Regression coverage for edit binding and recovery after pilot failures."""

from types import SimpleNamespace

from ollama_agents.errors import AdapterError
from ollama_agents.schema import validate
from testguided_study import agent
from testguided_study.artifacts import ROOT, load_config, read
from testguided_study.controller import Controller
from testguided_study.design import default_design, design_schema


def test_runner_binds_read_version_and_invalidates_it_after_changes():
    controller = Controller(3, local_edits=True)
    edit = {'action': 'replace_text', 'path': 'module.py', 'old': '1', 'new': '2'}
    assert controller.guard(edit)['code'] == 'read_required'
    controller.observe({'action': 'read_file', 'path': 'module.py', 'start': 1},
                       {'status': 'completed', 'sha256': 'a' * 64}, {}, 1)
    assert controller.guard(edit) is None
    assert controller.bind_edit(edit)['expected_sha256'] == 'a' * 64
    controller.observe(edit, {'status': 'completed'}, {}, 2)
    assert controller.guard(edit)['code'] == 'read_required'
    controller.observe({'action': 'read_file', 'path': 'module.py', 'start': 1},
                       {'status': 'completed', 'sha256': 'b' * 64}, {}, 3)
    assert controller.bind_edit(edit)['expected_sha256'] == 'b' * 64
    controller.observe(edit, {'status': 'tool_error', 'code': 'edit_conflict'}, {}, 4)
    assert controller.guard(edit)['code'] == 'read_required'


def test_unchanged_green_prompts_reproduction():
    controller = Controller(3, local_edits=True)
    controller.observe({'action': 'run_tests', 'targets': ['tests/test_module.py']},
                       {'status': 'completed', 'observation': 'pass'}, {}, 1)
    assert 'baseline evidence only' in controller.facts['next_action']
    controller.metrics['first_production_change_call'] = 2
    controller.observe({'action': 'run_tests', 'targets': ['tests/test_module.py']},
                       {'status': 'completed', 'observation': 'pass'}, {}, 3)
    assert 'then submit' in controller.facts['next_action']


def test_recovery_restricts_next_action_then_restores_full_schema(tmp_path, monkeypatch):
    config = load_config(ROOT / 'study.toml')
    config['budgets']['model_calls'] = 5
    requests = []
    executed = []
    monkeypatch.setattr(agent, 'patch', lambda *args: '')

    def execute(manager, sandbox, action, *args):
        executed.append(action)
        return {'status': 'completed', 'sha256': 'c' * 64, 'text': 'value = 1'}

    monkeypatch.setattr(agent, 'execute', execute)

    class Client:
        def chat(self, **kwargs):
            requests.append(kwargs)
            if len(requests) == 1:
                raise AdapterError('invalid_output', 'truncated', raw={'done_reason': 'length'})
            actions = [
                {'action': 'read_file', 'stage': 'inspect', 'path': 'module.py', 'start': 1},
                {'action': 'replace_text', 'stage': 'implement', 'path': 'module.py',
                 'old': '1', 'new': '2', 'reason': 'required boundary'},
                {'action': 'submit', 'stage': 'finish', 'reason': 'done'},
            ]
            action = actions[len(requests) - 2]
            validate(action, kwargs['schema'])
            return {'action': action, 'usage': {}}

    result = agent.develop(None, None, SimpleNamespace(problem_statement='Fix boundary'),
                           {'mode': 'pytest', 'run_id': '0001', 'seed': 42}, config,
                           {'pytest': 'guide'}, tmp_path, client=Client())
    assert result['status'] == 'submitted'
    assert result['repairs'] == 1
    assert [e['properties']['action']['const'] for e in requests[1]['schema']['oneOf']] == ['read_file']
    assert len(requests[2]['schema']['oneOf']) > 1
    assert executed[1]['expected_sha256'] == 'c' * 64
    archived = read(tmp_path / 'steps/0002-tool.json')
    assert 'expected_sha256' not in archived['action']
    assert archived['executed_action']['expected_sha256'] == 'c' * 64
    schema = design_schema(default_design('pytest', {'pytest': 'guide'}))
    assert requests[2]['schema'] == schema
