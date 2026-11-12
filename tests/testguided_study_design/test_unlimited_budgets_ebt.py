# ruff: noqa: F811
"""Unlimited call counts remain bounded by the explicit per-agent clock."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from test_session_integration import action, check, session  # noqa: F401
from testguided_study import agent
from testguided_study.artifacts import load_config
from testguided_study.cli import call_limit
from testguided_study.design import default_design
from testguided_study.launch import options

ROOT = Path(__file__).resolve().parents[2] / 'experiments/testguided-study'


@pytest.mark.parametrize('path', ['study.toml', 'v6.toml', 'v7.toml', 'profiles/pilot.toml', 'profiles/three-hours.toml', 'profiles/six-hours.toml'])
def test_standard_profiles_reserve_30_minutes_and_expanded_context(path):
    def observe():
        config = load_config(ROOT / path)
        return (config['budgets']['wall_seconds'], config['budgets']['model_calls'], config['budgets']['tool_calls'],
                config['ollama']['num_predict'], config['ollama']['num_ctx'], config['budgets']['context_bytes'])
    check(observe, (1800, 0, 0, 8192, 32768, 80000))


@pytest.mark.parametrize('field,value,valid', [
    ('model_calls', 0, True), ('tool_calls', 0, True), ('model_calls', 1, True),
    ('model_calls', -1, False), ('tool_calls', -1, False),
    ('wall_seconds', 0, False), ('command_seconds', 0, False), ('context_bytes', 0, False),
])
def test_zero_is_unlimited_only_for_call_budgets(tmp_path, field, value, valid):
    source = (ROOT / 'study.toml').read_text()
    lines = [f'{field} = {value}' if line.startswith(field + ' =') else line for line in source.splitlines()]
    path = tmp_path / 'study.toml'
    path.write_text('\n'.join(lines))

    def observe():
        try:
            load_config(path)
        except ValueError:
            return False
        return True
    check(observe, valid)


@pytest.mark.parametrize('limit,expected', [(0, ('submitted', 49, 48)), (5, ('submitted', 49, 48))])
def test_unlimited_steps_reach_submission_beyond_previous_limits(session, monkeypatch, limit, expected):
    run, config, guides = session
    config['budgets'].update(model_calls=limit, tool_calls=0)
    monkeypatch.setattr(agent, 'execute', lambda manager, sandbox, selected, timeout, output_limit: {
        'status': 'completed', 'text': selected['path'], 'path': selected['path'], 'start': 1})

    def observe():
        actions = [action('read_file', path=f'module_{i}.py', start=1) for i in range(48)]
        result, _, _ = run([*actions, action('submit', reason='verified')], design=default_design('pytest', guides, version=4))
        return result['status'], result['model_calls'], result['tool_calls']
    check(observe, expected)


def test_time_deadline_still_applies_when_both_call_budgets_are_unlimited(session):
    run, config, guides = session
    config['budgets'].update(model_calls=0, tool_calls=0, wall_seconds=900)
    ticks = iter([0, 0, 0, 901, 901])

    def observe():
        result, _, _ = run([action('read_file', path='module.py', start=1)],
                            design=default_design('pytest', guides, version=4), clock=lambda: next(ticks))
        return result['status'], result['model_calls'], result['tool_calls']
    check(observe, ('wall_budget', 1, 0))


def test_smoke_and_explicit_cli_zero_preserve_unlimited_defaults():
    def observe():
        config = options(SimpleNamespace(config=None, mode='smoke', tasks=None, seeds=None, task_type=None,
                                         agent_seconds=None, model_calls=call_limit('0'), tasks_manifest=None))
        return config['budgets']['wall_seconds'], config['budgets']['model_calls'], config['budgets']['tool_calls']
    check(observe, (1800, 0, 0))


@pytest.mark.parametrize('version', [6, 7])
def test_team_ignores_legacy_call_phase_and_repair_limits_until_deadline(tmp_path, version):
    from v6_support import Harness as V6Harness
    from v7_support import Harness as V7Harness

    h = (V6Harness if version == 6 else V7Harness)(
        tmp_path, wall_seconds=1800, model_calls=1, tool_calls=1,
        information_requests=1, revision_rounds=1, repair_calls=0)
    for _ in range(110):
        assert h.team.request() is not None
        if version == 6:
            h.ok('analysis', 'read_file', path='src/calc.py', start=1, end=2)
        else:
            h.ok('analysis', 'read_file', path='src/calc.py', line_start=1, line_end=2)
    for _ in range(5):
        h.team.reject_output(raw={'invalid': True}, usage={})
        assert h.team.request() is not None
    h.clock.now = 1799
    assert h.team.request() is not None
    assert h.snapshot()['status'] == 'running'
    assert h.snapshot()['role'] == 'analysis'
    assert h.snapshot()['budget']['reserve_active'] is False
    assert h.snapshot()['metrics']['output_repairs'] == 5
    h.clock.now = 1800
    assert h.team.request() is None
    assert h.snapshot()['reason'] == ('wall_budget' if version == 6 else 'budget_exhausted')
    assert (tmp_path / 'archive/full.patch').exists()


@pytest.mark.parametrize('version', [6, 7])
def test_model_cannot_abandon_an_incomplete_task_while_time_remains(tmp_path, version):
    from v6_support import Harness as V6Harness
    from v7_support import Harness as V7Harness

    h = (V6Harness if version == 6 else V7Harness)(tmp_path)
    result = h.send('analysis', 'finish_incomplete', reason='Still investigating')
    assert result['status'] == 'rejected'
    assert h.team.request() is not None
    assert h.snapshot()['completion']['allowed'] is False


@pytest.mark.parametrize('version', [6, 7])
def test_runner_extends_legacy_design_and_gives_tools_the_remaining_task_time(tmp_path, monkeypatch, version):
    from ollama_agents.errors import AdapterError
    from testguided_study import team_agent
    from v6_support import GUIDES, ISSUE
    from v6_support import Harness as V6Harness
    from v7_support import Harness as V7Harness

    h = (V6Harness if version == 6 else V7Harness)(tmp_path / 'setup')
    design = default_design('pytest', GUIDES, version=version)
    design['core']['policy'].update(wall_seconds=900, model_calls=1, tool_calls=1)
    requests, tool_timeouts = [], []

    class Client:
        def chat(self, **request):
            requests.append(request)
            if len(requests) > 1:
                raise AdapterError('infrastructure_error', 'End deterministic replay')
            h.clock.now = 125
            region = {'start': 1, 'end': 2} if version == 6 else {'line_start': 1, 'line_end': 2}
            return {'action': {'action': 'read_file', 'path': 'src/calc.py', **region}, 'usage': {}}

    def execute(manager, sandbox, action, timeout, output_limit):
        tool_timeouts.append(timeout)
        return {'status': 'completed'}

    monkeypatch.setattr(team_agent, 'execute', execute)
    config = {'budgets': {'wall_seconds': 1800, 'model_calls': 1, 'tool_calls': 1,
                          'command_seconds': 30, 'context_bytes': 80000, 'output_chars': 12000},
              'ollama': {'think': False, 'temperature': 0.2, 'num_ctx': 32768, 'num_predict': 8192}}
    result = team_agent.develop(None, None, SimpleNamespace(problem_statement=ISSUE),
        {'mode': 'pytest', 'seed': 42, 'run_id': '0001'}, config, GUIDES, tmp_path / 'run',
        design=design, client=Client(), clock=h.clock, store=h.team.store)
    assert [r['timeout'] for r in requests] == [1800, 1675]
    assert tool_timeouts == [1675]
    assert result['team']['policy']['wall_seconds'] == 1800
    assert result['model_calls'] == 2
