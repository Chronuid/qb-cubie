"""V8 provider replay through the real workspace scripts and EBT probe."""

import json
import subprocess
from types import SimpleNamespace

import pytest
from ollama_agents.errors import AdapterError
from ollama_agents.schema import validate
from test_v6_runtime import HostContainer, a
from testguided_study import agent
from testguided_study.artifacts import load_config, read
from testguided_study.design import default_design
from testguided_study.iteration import freeze_design, load_design
from testguided_study.monitor import run_view
from v8_support import CASE, GUIDES, ISSUE, NODE, REGRESSION


class V8Replay:
    def __init__(self, directory, mode, *, check_evaluation=True):
        self.directory, self.mode = directory, mode
        self.check_evaluation = check_evaluation
        self.requests = []
        self.actions = self.sequence()

    def last(self):
        return read(self.directory / f'steps/{len(self.requests) - 2:04d}-tool.json')['result']

    def sequence(self):
        yield a('read_file', path='src/calc.py', line_start=1, line_end=2)
        source = self.last()['evidence_id']
        yield a('finish', delivery={
            'requirements': [{'id': 'REQ-1', 'text': ISSUE, 'refs': ['issue:REQ-1']}],
            'facts': [{'text': 'double is in src/calc.py', 'refs': [source]}],
            'source_refs': [source], 'test_paths': ['tests'], 'test_command': 'python -m pytest',
            'baseline': [], 'hypotheses': [], 'open_questions': [],
        })
        if self.mode == 'cubie':
            body = ('    result = EBT(target=double, pre=WorldState(args=(value,)), '
                    'post=WorldState(returns=expected), reporter=None).run()\n')
            if self.check_evaluation:
                body += '    assert result.evaluation is True\n'
            imports = 'from qb_cubie import EBT, WorldState\n'
        else:
            body, imports = '    assert double(value) == expected\n', ''
        test = ('import pytest\nfrom src.calc import double\n' + imports
                + '\n@pytest.mark.parametrize("value,expected", [(1, 2), (2, 4)])\n'
                + 'def test_double(value, expected):\n' + body)
        for path, text in [('tests/test_calc.py', test), ('tests/test_old.py',
                'from src.calc import double\n\ndef test_old():\n    assert double(1) == 2\n')]:
            yield a('read_file', path=path, line_start=1, line_end=1)
            yield a('edit_tests', handle=self.last()['handle'], new_text=text, reason=ISSUE)
        yield a('collect_tests', targets=[NODE, REGRESSION])
        yield a('finish', delivery={'cases': [CASE], 'targets': [NODE], 'regressions': [REGRESSION]})
        yield a('run_tests', targets=[NODE])
        evidence = [self.last()['evidence_id']]
        yield a('read_file', path='src/calc.py', line_start=2, line_end=2)
        yield a('edit_source', handle=self.last()['handle'], new_text='    return value * 2\n', reason=ISSUE)
        # Exercises the actual remote baseline port, with final tests on original production.
        yield a('run_tests', targets=[NODE], baseline=True)
        evidence.append(self.last()['evidence_id'])
        yield a('run_tests', targets=[NODE])
        evidence.append(self.last()['evidence_id'])
        yield a('run_tests', targets=[REGRESSION])
        evidence.append(self.last()['evidence_id'])
        yield a('finish', delivery={'summary': 'Correct multiplication for both issue inputs.',
                                   'evidence_refs': evidence, 'open_points': []})
        diff = self.last()['diff_ref']
        for ref in [*evidence, diff]:
            yield a('read_evidence', ref=ref)
        yield a('read_file', path='src/calc.py', line_start=1, line_end=2)
        yield a('finish', delivery={'verdict': 'verified', 'requirement_ids': ['REQ-1'],
            'reason': 'Both specified inputs, final patch and current focused/regression results inspected.',
            'evidence_refs': evidence, 'open_points': []})

    def chat(self, **request):
        self.requests.append(request)
        try:
            action = next(self.actions)
        except StopIteration:
            raise AdapterError('infrastructure_error', 'End of deterministic replay') from None
        validate(action, request['schema'])
        return {'action': action, 'raw': {'replay': True},
                'usage': {'input_tokens': 20, 'output_tokens': 10}}


@pytest.mark.parametrize('mode,checked,submitted', [('pytest', True, True), ('cubie', True, True),
                                                  ('cubie', False, False)])
def test_v8_provider_workspace_probe_and_archive(tmp_path, mode, checked, submitted):
    root = tmp_path / 'workspace'
    (root / 'src').mkdir(parents=True)
    (root / 'src/calc.py').write_text('def double(value):\n    return value * 2 - 1\n')
    for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Tests',
            '-c', 'user.email=tests@example.invalid', 'commit', '-qm', 'baseline'],
            ['tag', '_swegemma_baseline']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True, timeout=30)
    directory = tmp_path / 'archive'
    directory.mkdir()
    design = default_design(mode, GUIDES, version=8)
    freeze_design(design, tmp_path / 'design.json')
    assert load_design(tmp_path / 'design.json') == design
    client = V8Replay(directory, mode, check_evaluation=checked)
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
        assert all(e['case_results']['C-1']['ebt_executed'] == 2 for e in observations[:3])
        assert all(e['case_results']['C-1']['ebt_evaluation_checked'] == int(checked) * 2
                   for e in observations[:3])
    for request in client.requests:
        assert (GUIDES[mode] in json.dumps(request['messages'])) == (
            'edit_tests' in {e['properties']['action']['const'] for e in request['schema']['oneOf']})
    assert result['patch'] == (directory / 'production.patch').read_text()
    assert 'tests/test_calc.py' not in result['patch']
    assert 'tests/test_calc.py' in (directory / 'full.patch').read_text()
    assert read(directory / 'team.json')['private_evaluation_required']
    assert all(stats['input_tokens'] > 0 for stats in result['process_metrics']['roles'].values())
    # Monitor consumes the same archived role/context/evidence as other generations.
    monitor_root = tmp_path / 'monitor'
    (monitor_root / 'runs').mkdir(parents=True)
    (monitor_root / 'runs/0001').symlink_to(directory, target_is_directory=True)
    (monitor_root / 'schedule.json').write_text(json.dumps([{'run_id': '0001', 'mode': mode}]))
    view = run_view(monitor_root, '0001')
    assert view['agent']['team']['status'] == result['status']


def test_v8_profile_loads_without_changing_default_profile():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3] / 'experiments/testguided-study'
    config = load_config(root / 'v8.toml')
    assert config['agent_version'] == 8
    assert config['budgets']['wall_seconds'] == 1800
    assert config['ollama']['think'] is False
