# ruff: noqa: F811
"""Exercise actual v6 provider requests, container scripts and final evidence."""

import ast
import base64
import copy
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from ollama_agents.schema import validate
from test_run_management_ebt import managed_study  # noqa: F401
from testguided_study import agent
from testguided_study.artifacts import freeze, load_config, read, verify
from testguided_study.caseforms import render
from testguided_study.design import default_design
from testguided_study.iteration import identity
from testguided_study.launch import save_config
from testguided_study.monitor import run_view
from testguided_study.smoke import generate
from testguided_study.team_probe import PROBE
from v6_support import CASE, GUIDES, ISSUE, NODE, Harness, outcome


class HostContainer:
    """Execute the real public container scripts in a temporary local repository.

    Only the root path and interpreter are adapted; controller, I/O scripts,
    git baselines, pytest, probe and archive code all run unchanged.
    """
    def __init__(self, root):
        self.root = root
        self.calls = []

    def exec(self, sandbox, command, *, timeout):
        self.calls.append(command)
        words = shlex.split(command)
        if words[:3] == ['python3', '-S', '-c']:
            tree = ast.parse(words[3])
            call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                        and isinstance(n.func, ast.Attribute) and n.func.attr == 'b64decode')
            script = base64.b64decode(ast.literal_eval(call.args[0])).decode()
            script = script.replace("'/workspace'", repr(str(self.root))).replace('"/workspace"', repr(str(self.root)))
            args = [sys.executable, '-S', '-c', script, *words[4:]]
            result = subprocess.run(args, cwd=self.root, capture_output=True, text=True,
                                    timeout=timeout, check=False)
        else:
            command = command.replace('/workspace', str(self.root)).replace('python3 -m pytest',
                                                                                  shlex.quote(sys.executable) + ' -m pytest')
            result = subprocess.run(command, shell=True, cwd=self.root, capture_output=True,
                                    text=True, timeout=timeout, check=False)
        return SimpleNamespace(exit_code=result.returncode, stdout=result.stdout,
                               stderr=result.stderr, timed_out=False)


def a(name, **fields):
    return {'action': name, **fields}


class Replay:
    def __init__(self, directory, *, incomplete=False):
        self.directory, self.incomplete = directory, incomplete
        self.requests = []
        self.actions = iter([
            a('read_file', path='src/calc.py', start=1),
            lambda result: a('publish_context', requirements=[{'id': 'REQ-1', 'text': ISSUE, 'refs': ['issue:REQ-1']}],
                             sources=[result['evidence_id']], baseline=[], open_questions=[]),
            a('handoff', to='qa', job_id='J-QA', inputs=['REQ-1'], delivery='Regression case', acceptance=ISSUE),
            a('create_case', case=copy.deepcopy(CASE) | {'target': 'src.calc.double'}),
            a('collect_tests', targets=[NODE]),
            a('publish_suite', case_ids=['C-1'], targets=[NODE], expected_red={'C-1': '3 instead of 4'}),
            a('run_tests', targets=[NODE], purpose='focused'),
            a('read_file', path='src/calc.py', start=2, end=2),
            lambda result: a('replace_region', handle=result['handle'], new_text='    return value * 2\n', reason='REQ-1'),
            *([a('finish_incomplete', reason='no remaining verification')] if incomplete else [
                a('run_tests', targets=[NODE], purpose='focused'),
                a('run_tests', targets=[NODE], purpose='regression'),
                a('publish_implementation', requirement_ids=['REQ-1'], open_points=[]),
                a('verify_completion'),
                a('submit', reason='Current focused and regression evidence satisfy REQ-1'),
            ]),
        ])

    def chat(self, **request):
        previous = self.directory / f'steps/{len(self.requests) - 1:04d}-tool.json'
        self.requests.append(request)
        action = next(self.actions)
        if callable(action):
            action = action(read(previous)['result'])
        validate(action, request['schema'])
        return {'action': action, 'usage': {'input_tokens': 20, 'output_tokens': 10}, 'raw': {'replay': True}}


@pytest.mark.parametrize('mode', ['pytest', 'cubie'])
def test_complete_team_uses_real_edits_pytest_and_role_requests(tmp_path, mode):
    root = tmp_path / 'workspace'
    (root / 'src').mkdir(parents=True)
    (root / 'tests').mkdir()
    (root / 'src/calc.py').write_text('def double(value):\n    return value * 2 - 1\n')
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Tests', '-c', 'user.email=tests@example.invalid',
                                             'commit', '-qm', 'baseline'], ['tag', '_swegemma_baseline']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    directory = tmp_path / 'archive'
    directory.mkdir()
    design = default_design(mode, GUIDES, version=6)
    client = Replay(directory)
    config = {'budgets': {'wall_seconds': 900, 'model_calls': 48, 'tool_calls': 96, 'context_bytes': 80000,
                          'command_seconds': 30, 'output_chars': 12000},
              'ollama': {'think': False, 'temperature': 0.2, 'num_ctx': 32768, 'num_predict': 8192}}
    manager = HostContainer(root)
    result = agent.develop(manager, None, SimpleNamespace(problem_statement=ISSUE),
                           {'mode': mode, 'seed': 42, 'run_id': '0001'}, config, GUIDES,
                           directory, client=client, design=design)
    assert result['status'] == 'submitted', result
    assert result['completion'] == {'allowed': True, 'status': 'verified_green'}
    assert result['model_calls'] == len(client.requests) == 14
    assert result['team']['roles'] == ['analysis', 'qa', 'dev']
    assert result['team']['qualifications'] == {'reproduced': True, 'verified': True}
    assert len(result['test_observations']) == 3
    assert result['test_observations'][0]['observation'] == 'assertion_failure'
    assert (root / 'src/calc.py').read_text().endswith('return value * 2\n')
    test_source = (root / 'tests/test_calc.py').read_text()
    assert ('result.evaluation is True' in test_source) == (mode == 'cubie')
    assert (directory / 'team-design.json').exists()
    assert read(directory / 'team.json')['status'] == 'submitted'
    assert all(ISSUE in json.dumps(req['messages']) and GUIDES[mode] in json.dumps(req['messages'])
               for req in client.requests)
    metrics = result['process_metrics']['roles']
    assert sum(m['model_calls'] for m in metrics.values()) == 14
    assert all(m['input_tokens'] > 0 for m in metrics.values())
    if mode == 'cubie':
        assert result['process_metrics']['ebt_evaluation_checked'] == 3


@pytest.mark.parametrize('source,executed,evaluated,checked', [
    ('EBT(target=lambda: 2, post=WorldState(returns=2), reporter=None)', 0, 0, 0),
    ('result = EBT(target=lambda: 2, post=WorldState(returns=2), reporter=None).run()', 1, 1, 0),
    ('result = EBT(target=lambda: 2, post=WorldState(returns=2), reporter=None).run()\n    assert result.evaluation is True', 1, 1, 1),
    ('result = EBT(target=lambda: 2, post=WorldState(returns=2), reporter=None).run()\n    if False:\n        assert result.evaluation is True', 1, 1, 0),
])
def test_probe_distinguishes_executed_explicit_check_from_dead_source(tmp_path, source, executed, evaluated, checked):
    evidence = tmp_path / 'usage.json'
    (tmp_path / 'v6_probe.py').write_text(PROBE.replace('EVIDENCE', repr(str(evidence))))
    (tmp_path / 'test_case.py').write_text('from qb_cubie import EBT, WorldState\n\ndef test_case():\n    ' + source + '\n')
    env = os.environ | {'PYTHONPATH': str(tmp_path), 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTEST_ADDOPTS': ''}
    result = subprocess.run([sys.executable, '-m', 'pytest', '-p', 'v6_probe', '--rootdir', str(tmp_path), '-q', str(tmp_path)],
                            env=env, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    usage = read(evidence)
    assert (usage['ebt_executed'], usage['ebt_evaluated'], usage['ebt_evaluation_checked']) == (executed, evaluated, checked)
    assert usage['case_results']['test_case.py::test_case']['executed'] is True


def test_case_revision_without_file_change_invalidates_old_reproduction(tmp_path):
    h = Harness(tmp_path)
    h.red()
    request = h.ok('dev', 'request_test_change', case_ids=['C-1'], requirement_id='REQ-1',
                   evidence_ids=[next(reversed(h.team.evidence))], reason='Revisit documented expectation')
    before = h.snapshot()['versions']['tests']
    h.ok('qa', 'revise_case', case=CASE | {'expected': {'returns': 5}, 'reason': 'Different public requirement interpretation'})
    assert h.snapshot()['versions']['tests'] != before
    assert not h.snapshot()['qualifications']['reproduced']
    h.ok('qa', 'respond_test_change', reply_to=request['message_id'], accepted=True, reason='Needs rerun', refs=['issue:REQ-1'], unresolved=False)


@pytest.mark.parametrize('kind,limit', [('information', 6), ('revision', 3)])
def test_legacy_round_limits_allow_extra_handoffs(tmp_path, kind, limit):
    h = Harness(tmp_path, repeat_limit=100)
    red = h.red()
    for _ in range(limit):
        if kind == 'information':
            request = h.ok('dev', 'ask_analysis', question='Confirm issue requirement', refs=['issue:REQ-1'])
            h.ok('analysis', 'answer_question', reply_to=request['message_id'], answer=ISSUE, refs=['issue:REQ-1'], unknown=False)
        else:
            request = h.ok('dev', 'request_test_change', case_ids=['C-1'], requirement_id='REQ-1',
                           evidence_ids=[red['evidence_id']], reason='Review oracle')
            h.ok('qa', 'respond_test_change', reply_to=request['message_id'], accepted=False,
                 reason='Oracle matches issue', refs=['issue:REQ-1'], unresolved=False)
    action = ('ask_analysis', {'question': 'one too many', 'refs': []}) if kind == 'information' else (
        'request_test_change', {'case_ids': ['C-1'], 'requirement_id': 'REQ-1', 'evidence_ids': [red['evidence_id']], 'reason': 'one too many'})
    response = h.send('dev', action[0], **action[1])
    assert response['status'] == 'completed'
    assert h.snapshot()['status'] == 'running'


def test_nested_analysis_probe_resumes_both_interrupted_jobs(tmp_path):
    h = Harness(tmp_path)
    h.suite()
    original = h.snapshot()['active_job']['id']
    first = h.ok('dev', 'ask_analysis', question='Need API evidence', refs=['issue:REQ-1'])
    # Analysis can inspect while answering. No fresh run or model call is created.
    h.ok('analysis', 'read_file', path='tests/test_calc.py', start=1)
    h.ok('analysis', 'answer_question', reply_to=first['message_id'], answer='Use double', refs=['issue:REQ-1'], unknown=False)
    assert h.snapshot()['active_job']['id'] == original
    assert h.snapshot()['role'] == 'dev'
    assert h.snapshot()['metrics']['model_calls'] == 0


def test_v6_freeze_uses_explicit_version_and_role_schema_identity(tmp_path):
    generate(tmp_path / 'input')
    config_path = tmp_path / 'input/study.toml'
    config = load_config(config_path)
    config.update(agent_version=6)
    config['ollama']['think'] = False
    save_config(config_path, config)
    freeze(config_path, tmp_path / 'frozen')
    assert verify(tmp_path / 'frozen')['agent_version'] == 6
    payload = read(tmp_path / 'frozen/designs/cubie.json')
    assert payload['design']['core']['context']['version'] == 6
    assert set(payload['design']['core']['context']['roles']) == {'analysis', 'qa', 'dev'}
    changed = copy.deepcopy(payload['design'])
    changed['core']['context']['roles']['qa'] += '\nA distinct frozen hypothesis.'
    assert identity(changed) != payload['identity']


def test_v6_monitor_reads_team_requests_and_separate_completion(tmp_path):
    directory = tmp_path / 'runs/0001'
    (directory / 'steps').mkdir(parents=True)
    for path, data in {
        tmp_path / 'schedule.json': [{'run_id': '0001', 'mode': 'cubie'}],
        directory / 'team.json': {'role': 'dev', 'completion': {'status': 'incomplete'}},
        directory / 'steps/0001-request.json': {'role': 'dev', 'messages': [{'role': 'user', 'content': ISSUE}], 'schema': {}},
    }.items():
        path.write_text(json.dumps(data))
    view = run_view(tmp_path, '0001')
    assert view['agent']['context'] == [{'role': 'user', 'content': ISSUE}]
    assert view['agent']['role'] == 'dev'
    assert view['agent']['team']['completion']['status'] == 'incomplete'


@pytest.mark.parametrize('mode', ['pytest', 'cubie'])
@pytest.mark.parametrize('broken', [False, True])
def test_generated_fixture_adapter_observes_real_production(tmp_path, mode, broken):
    production = Path(__file__).parent / 'fixtures/v6/app.py'
    source = production.read_text()
    if broken:
        source = source.replace('self.total += amount', 'self.total = amount')
    (tmp_path / 'app.py').write_text(source)
    case = CASE | {
        'target': 'observe', 'args': [3], 'expected': {'returns': (5, 5)},
        'setup': {
            'fixtures': ['counter'],
            'code': 'import app\n@pytest.fixture\ndef counter():\n    return app.Counter(2)\n',
            'body': 'def observe(amount):\n    returned = counter.add(amount)\n    return returned, counter.total\n',
        },
    }
    (tmp_path / 'test_case.py').write_text(render(case, mode))
    env = os.environ | {'PYTHONPATH': str(tmp_path), 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTEST_ADDOPTS': ''}
    result = subprocess.run([sys.executable, '-m', 'pytest', '--rootdir', str(tmp_path), '-q', str(tmp_path)],
                            env=env, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == int(broken), result.stdout + result.stderr


@pytest.mark.parametrize('mode', ['pytest', 'cubie'])
def test_test_change_question_resumes_nested_qa_job(tmp_path, mode):
    h = Harness(tmp_path, mode=mode)
    red = h.red()
    change = h.ok('dev', 'request_test_change', case_ids=['C-1'], requirement_id='REQ-1',
                  evidence_ids=[red['evidence_id']], reason='Check public API')
    qa_job = h.snapshot()['active_job']['id']
    question = h.ok('qa', 'ask_analysis', question='Which oracle applies?', refs=['issue:REQ-1'])
    h.ok('analysis', 'answer_question', reply_to=question['message_id'], answer=ISSUE, refs=['issue:REQ-1'], unknown=False)
    assert h.snapshot()['role'] == 'qa'
    assert h.snapshot()['state'] == 'revise_tests'
    assert h.snapshot()['active_job']['id'] == qa_job
    h.ok('qa', 'respond_test_change', reply_to=change['message_id'], accepted=False,
         reason='The case matches the requirement', refs=['issue:REQ-1'], unresolved=False)
    assert h.snapshot()['role'] == 'dev'
    assert h.snapshot()['pending_requests'] == []


def test_analysis_can_delegate_a_probe_while_answering_an_information_request(tmp_path):
    h = Harness(tmp_path)
    h.suite()
    original_job = h.snapshot()['active_job']['id']
    question = h.ok('dev', 'ask_analysis', question='Need current runtime evidence', refs=['issue:REQ-1'])
    h.ok('analysis', 'handoff', to='dev', job_id='probe', inputs=['REQ-1'], delivery='Run focused case', acceptance='Observed output')
    h.run(outcome('assertion_failure', failed=[(NODE, 'AssertionError', 'assert 3 == 4')]))
    h.ok('dev', 'publish_implementation', requirement_ids=['REQ-1'], open_points=[])
    assert h.snapshot()['state'] == 'answer_information'
    h.ok('analysis', 'answer_question', reply_to=question['message_id'], answer=ISSUE, refs=['issue:REQ-1'], unknown=False)
    assert h.snapshot()['active_job']['id'] == original_job
    assert h.snapshot()['state'] == 'reproduce'


@pytest.mark.parametrize('version', [6, 7])
def test_real_incomplete_teams_reach_independent_evaluation_in_both_arms(tmp_path, managed_study, monkeypatch, version):
    import tarfile

    from ollama_agents.errors import AdapterError
    from testguided_study import backend, team_agent

    env = managed_study
    config = load_config(env.project / 'profiles/pilot.toml')
    config['agent_version'] = version
    config['ollama']['think'] = False
    config['guides'] = {mode: str(env.project / 'guides' / f'{mode}.md') for mode in ('pytest', 'cubie')}
    config_path = env.project / f'v{version}.toml'
    save_config(config_path, config)

    class Manager(HostContainer):
        def __init__(self):
            root = tmp_path / f'container-{len(env.managers)}'
            root.mkdir()
            super().__init__(root)
            self.cleaned = False
            env.managers.append(self)

        def start(self):
            return self

        def cleanup_all(self):
            self.cleaned = True

    def prepare(manager, sandbox, root, item, task, config, directory):
        with tarfile.open(root / item['snapshot']) as archive:
            archive.extractall(manager.root, filter='data')
        for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Tests', '-c', 'user.email=tests@example.invalid',
                                                 'commit', '-qm', 'baseline'], ['tag', '_swegemma_baseline']):
            subprocess.run(['git', *args], cwd=manager.root, check=True, capture_output=True)

    class Client:
        def __init__(self):
            case = CASE | {'target': 'bounds.bounded', 'args': [-2, 0, 5], 'expected': {'returns': 0}}
            actions = [
                a('read_file', path='bounds.py', start=1),
                lambda result: a('publish_context', requirements=[{'id': 'REQ-1', 'text': 'Clamp to lower boundary', 'refs': ['issue:REQ-1']}],
                                 sources=[result['evidence_id']], baseline=[], open_questions=[]),
                a('handoff', to='qa', job_id='qa', inputs=['REQ-1'], delivery='Lower-bound case', acceptance='Below lower returns lower'),
                a('create_case', case=case), a('collect_tests', targets=[NODE]),
                a('publish_suite', case_ids=['C-1'], targets=[NODE], expected_red={'C-1': '-2 instead of 0'}),
                a('run_tests', targets=[NODE], purpose='focused'),
                a('read_file', path='bounds.py', start=2, end=2),
                lambda result: a('replace_region', handle=result['handle'], new_text='    return max(lower, min(value, upper))\n', reason='Clamp to specified bounds'),
                AdapterError('invalid_output', 'truncated', raw={'content': 'invalid-1'}, usage={'output_tokens': 8192}),
                AdapterError('invalid_output', 'truncated again', raw={'content': 'invalid-2'}, usage={'output_tokens': 8192}),
                AdapterError('infrastructure_error', 'Provider unavailable after repairs'),
            ]
            if version == 7:
                actions[1:3] = [lambda result: a('finish_orientation', requirements=[{
                    'id': 'REQ-1', 'text': 'Clamp to lower boundary', 'refs': ['issue:REQ-1'], 'status': 'confirmed'}],
                    source_refs=[result['evidence_id']], test_entry_refs=[], hypotheses=[], unknowns=[])]
                for action in actions:
                    if isinstance(action, dict) and action['action'] == 'read_file':
                        action['line_start'] = action.pop('start')
                        action['line_end'] = action.pop('end', 2)
            self.actions = iter(actions)

        def chat(self, **request):
            action = next(self.actions)
            if isinstance(action, Exception):
                raise action
            if callable(action):
                action = action(json.loads(request['messages'][-1]['content']))
            validate(action, request['schema'])
            return {'action': action, 'raw': {'replay': True}, 'usage': {'input_tokens': 10, 'output_tokens': 10}}

    monkeypatch.setattr(backend, 'manager', lambda *_: Manager())
    monkeypatch.setattr(backend, 'prepare', prepare)
    monkeypatch.setattr(team_agent, 'OllamaClient', lambda **_: Client())
    archive = Path(env.start(mode='smoke', config=config_path)['archive']) / 'frozen'
    rows = read(archive / 'schedule.json')
    results = [read(archive / 'runs' / row['run_id'] / 'result.json') for row in rows]
    assert len(results) == 2
    assert {row['mode'] for row in rows} == {'pytest', 'cubie'}
    assert all(result['agent']['reason'] == 'infrastructure_error' for result in results)
    assert all(result['agent']['status'] == 'incomplete' for result in results)
    assert all(result['resolved'] is True for result in results)
    assert all(result['agent']['repairs'] == 2 for result in results)
    assert all(manager.cleaned for manager in env.managers)
    for row in rows:
        directory = archive / 'runs' / row['run_id']
        assert 'tests/test_calc.py' in (directory / 'full.patch').read_text()
        assert 'tests/test_calc.py' not in (directory / 'production.patch').read_text()
        raw = (directory / f'steps/{10 if version == 6 else 9:04d}-response.json').read_text()
        assert 'invalid-2' in raw


@pytest.mark.parametrize('disposition', ['existing_coverage', 'not_reproducible'])
def test_classified_green_original_does_not_itself_claim_completion(tmp_path, disposition):
    h = Harness(tmp_path)
    h.suite()
    original = h.run()
    question = h.ok('dev', 'ask_analysis', question='Original case is green; classify coverage', refs=[])
    h.ok('analysis', 'classify_reproduction', classification=disposition, requirement_ids=['REQ-1'],
         evidence_ids=[original['evidence_id']], reason='Current case is already covered on original production')
    h.ok('analysis', 'answer_question', reply_to=question['message_id'], answer='Original green is not a repair', refs=['issue:REQ-1'], unknown=False)
    h.run(purpose='regression')
    h.ok('dev', 'publish_implementation', requirement_ids=['REQ-1'], open_points=[])
    h.send('analysis', 'verify_completion')
    assert h.snapshot()['qualifications']['reproduced'] is False
    assert h.snapshot()['completion']['allowed'] is False
    assert h.snapshot()['metrics']['first_production_change_call'] is None


def test_context_republication_cannot_erase_an_unresolved_runner_question(tmp_path):
    h = Harness(tmp_path)
    h.suite()
    question = h.ok('dev', 'ask_analysis', question='Unspecified behavior?', refs=[])
    source = h.ok('analysis', 'read_file', path='src/calc.py', start=1)
    h.ok('analysis', 'answer_question', reply_to=question['message_id'], answer='Unknown', refs=[], unknown=True)
    another = h.ok('dev', 'ask_analysis', question='Refresh context', refs=[])
    h.ok('analysis', 'publish_context', requirements=[{'id': 'REQ-1', 'text': ISSUE, 'refs': ['issue:REQ-1']}],
         sources=[source['evidence_id']], baseline=[], open_questions=[])
    assert any(q['id'] == question['message_id'] for q in h.snapshot()['open_questions'])
    assert another['message_id'] in h.snapshot()['pending_requests']


def test_rephrased_context_receives_guidance_without_stopping(tmp_path):
    h = Harness(tmp_path)
    source = h.ok('analysis', 'read_file', path='src/calc.py', start=1)
    for index in range(8):
        h.send('analysis', 'publish_context', requirements=[{'id': 'REQ-1', 'text': f'Rephrasing {index}', 'refs': ['issue:REQ-1']}],
               sources=[source['evidence_id']], baseline=[], open_questions=[])
    assert h.snapshot()['status'] == 'running'
    assert h.snapshot()['metrics']['recoveries'] >= 1


def test_remote_baseline_preserves_original_production_and_rejects_git_tag_tampering(tmp_path):
    from testguided_study.team_workspace import RemoteWorkspace

    root = tmp_path / 'workspace'
    (root / 'src').mkdir(parents=True)
    (root / 'tests').mkdir()
    original = 'def double(value):\n    return value * 2 - 1\n'
    (root / 'src/calc.py').write_text(original)
    (root / 'tests/test_calc.py').write_text('# original tests\n')
    (root / 'pytest.ini').write_text('[pytest]\n')
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Tests', '-c', 'user.email=tests@example.invalid',
                                             'commit', '-qm', 'baseline'], ['tag', '_swegemma_baseline']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    store = RemoteWorkspace(HostContainer(root), None)
    (root / 'src/calc.py').write_text('def double(value):\n    return value * 2\n')
    (root / 'tests/test_calc.py').write_text('# final tests\n')
    (root / 'pytest.ini').write_text('[pytest]\naddopts = -q\n')
    baseline = store.baseline()
    try:
        assert (Path(baseline) / 'src/calc.py').read_text() == original
        assert (Path(baseline) / 'tests/test_calc.py').read_text() == '# final tests\n'
        assert (Path(baseline) / 'pytest.ini').read_text() == '[pytest]\naddopts = -q\n'
    finally:
        store.remove_baseline(baseline)
    for args in (['add', '.'], ['-c', 'user.name=Tests', '-c', 'user.email=tests@example.invalid',
                               'commit', '-qm', 'tampered'], ['tag', '-f', '_swegemma_baseline']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    with pytest.raises(OSError, match='differs from the original'):
        store.baseline()
