"""V9 runs through the provider boundary, remote scripts and actual EBT probe."""

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_v6_runtime import HostContainer
from test_v8_runtime import V8Replay
from testguided_study import agent
from testguided_study.artifacts import load_config, read
from testguided_study.design import default_design
from testguided_study.iteration import freeze_design, load_design
from testguided_study.monitor import run_view
from v8_support import GUIDES, ISSUE, NODE


class V9Replay(V8Replay):
    def sequence(self):
        for action in super().sequence():
            if action['action'] == 'finish':
                delivery = action['delivery']
                if 'requirements' in delivery:
                    action = {'action': 'finish', 'notes': 'double is in src/calc.py. ' + ISSUE}
                elif 'cases' in delivery:
                    action = {'action': 'finish', 'test_targets': delivery['targets'],
                              'regressions': delivery['regressions'],
                              'notes': 'Input: 1 and 2. Expected: 2 and 4. Reason: ' + ISSUE}
                elif 'summary' in delivery:
                    action = {'action': 'finish', 'notes': delivery['summary']}
                else:
                    action = {'action': 'finish', 'verdict': delivery['verdict'], 'notes': delivery['reason']}
            yield action


@pytest.mark.parametrize('mode,checked,submitted', [
    ('pytest', True, True), ('cubie', True, True), ('cubie', False, False),
])
def test_v9_provider_remote_workspace_and_actual_probe(tmp_path, mode, checked, submitted):
    root = tmp_path / 'workspace'
    (root / 'src').mkdir(parents=True)
    (root / 'src/calc.py').write_text('def double(value):\n    return value * 2 - 1\n')
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Tests',
            '-c', 'user.email=tests@example.invalid', 'commit', '-qm', 'baseline'],
            ['tag', '_swegemma_baseline']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, timeout=30)
    directory = tmp_path / 'archive'
    directory.mkdir()
    design = default_design(mode, GUIDES, version=9)
    freeze_design(design, tmp_path / 'design.json')
    assert load_design(tmp_path / 'design.json') == design
    client = V9Replay(directory, mode, check_evaluation=checked)
    config = {'budgets': {'wall_seconds': 1800, 'context_bytes': 80000, 'output_chars': 12000},
              'ollama': {'think': False, 'temperature': 0.15, 'num_ctx': 32768, 'num_predict': 8192}}
    result = agent.develop(HostContainer(root), None, SimpleNamespace(problem_statement=ISSUE),
        {'mode': mode, 'seed': 42, 'run_id': '0001'}, config, GUIDES,
        directory, client=client, design=design)
    assert result['status'] == ('submitted' if submitted else 'incomplete')
    assert result['completion']['allowed'] is submitted
    observations = result['team']['test_observations']
    assert [e['observation'] for e in observations] == (
        ['assertion_failure', 'assertion_failure', 'pass', 'pass'] if submitted
        else ['pass', 'pass', 'pass', 'pass'])
    if mode == 'cubie':
        assert all(e['case_results'][NODE]['ebt_executed'] == 2 for e in observations[:3])
        assert all(e['case_results'][NODE]['ebt_evaluation_checked'] == int(checked) * 2
                   for e in observations[:3])
    for request in client.requests:
        assert (GUIDES[mode] in json.dumps(request['messages'])) == (
            'edit_tests' in {e['properties']['action']['const'] for e in request['schema']['oneOf']})
    assert result['patch'] == (directory / 'production.patch').read_text()
    assert 'tests/test_calc.py' not in result['patch']
    assert 'tests/test_calc.py' in (directory / 'full.patch').read_text()
    assert read(directory / 'team.json')['private_evaluation_required']
    assert list((directory / 'transactions').glob('*.json'))
    # Actual prompts must contain usable handles, even after hiding raw telemetry.
    assert any('handle: file-' in json.dumps(r['messages']) for r in client.requests)
    monitor_root = tmp_path / 'monitor'
    (monitor_root / 'runs').mkdir(parents=True)
    (monitor_root / 'runs/0001').symlink_to(directory, target_is_directory=True)
    (monitor_root / 'schedule.json').write_text(json.dumps([{'run_id': '0001', 'mode': mode}]))
    assert run_view(monitor_root, '0001')['agent']['team']['status'] == result['status']


def test_v9_profile_preserves_comparison_resources():
    root = Path(__file__).resolve().parents[2] / 'experiments/testguided-study'
    v8, v9 = (load_config(root / name) for name in ('v8.toml', 'v9.toml'))
    assert v9['agent_version'] == 9
    assert v9['phase'] == 'development'
    for field in ('budgets', 'ollama', 'images', 'guides', 'seeds'):
        assert v9[field] == v8[field]


@pytest.mark.parametrize('legacy', ['0', 0, '', 'invalid-token', 'private/hidden.py'])
def test_v9_provider_normalizes_cursor_without_changing_wire_schema(legacy):
    from testguided_study.team_v9 import V9OllamaClient
    from testguided_study.team_v9_design import SCHEMAS

    def transport(request, *, timeout):
        payload = json.loads(request.data)
        assert 'cursor' not in json.dumps(payload['format'])
        return json.dumps({'model': 'replay', 'done': True, 'done_reason': 'stop',
            'message': {'role': 'assistant', 'content': json.dumps({
                'action': 'search_content', 'scope': 'src', 'query': 'double', 'cursor': legacy})}}).encode()

    client = V9OllamaClient(endpoint='http://localhost:11434', model='replay', options={}, transport=transport)
    result = client.chat(messages=[], schema=SCHEMAS['qa'], timeout=1)
    assert result['action'] == {'action': 'search_content', 'scope': 'src', 'query': 'double'}
    assert 'cursor' in result['raw']['message']['content']


def test_v9_measured_token_overflow_blocks_tool_execution(tmp_path):
    from testguided_study.team_agent import develop
    from v9_support import Harness

    h = Harness(tmp_path)

    class OverBudgetClient:
        def chat(self, **request):
            return {'action': {'action': 'read_file', 'path': 'src/calc.py',
                               'line_start': 1, 'line_end': 2},
                    'usage': {'input_tokens': 30000, 'output_tokens': 1}}

    directory = tmp_path / 'runtime'
    directory.mkdir()
    config = {'budgets': {'wall_seconds': 1800, 'context_bytes': 80000, 'output_chars': 12000},
              'ollama': {'think': False, 'num_ctx': 32768, 'num_predict': 8192}}
    result = develop(None, None, SimpleNamespace(problem_statement=ISSUE),
        {'mode': 'cubie', 'seed': 42, 'run_id': '0001'}, config, GUIDES, directory,
        design=default_design('cubie', GUIDES, version=9), client=OverBudgetClient(),
        store=h.team.store, io=h.io, clock=h.clock)
    assert result['reason'] == 'context_error'
    assert result['tool_calls'] == 0
    assert not result['completion']['allowed']
    assert h.io.calls == []


@pytest.mark.parametrize('name', ['.git', 'other/private'])
def test_v9_private_files_are_filtered_from_root_navigation(tmp_path, name):
    from v9_support import Harness

    h = Harness(tmp_path)
    h.write(name, 'PRIVATE_FILE_CONTENT\n')
    found = h.ok('analysis', 'find_paths', pattern='*')
    searched = h.ok('analysis', 'search_content', scope='.', query='PRIVATE_FILE_CONTENT')
    assert name not in found['paths']
    assert searched['hits'] == []
