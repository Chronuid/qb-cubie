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


@pytest.mark.parametrize('path', ['study.toml', 'profiles/pilot.toml', 'profiles/three-hours.toml', 'profiles/six-hours.toml'])
def test_standard_profiles_reserve_15_minutes_and_expanded_context(path):
    def observe():
        config = load_config(ROOT / path)
        return (config['budgets']['wall_seconds'], config['budgets']['model_calls'], config['budgets']['tool_calls'],
                config['ollama']['num_predict'], config['ollama']['num_ctx'], config['budgets']['context_bytes'])
    check(observe, (900, 0, 0, 8192, 32768, 80000))


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


@pytest.mark.parametrize('limit,expected', [(0, ('submitted', 49, 48)), (5, ('model_budget', 5, 5))])
def test_unlimited_steps_reach_submission_beyond_previous_limits(session, monkeypatch, limit, expected):
    run, config, guides = session
    config['budgets'].update(model_calls=limit, tool_calls=0)
    monkeypatch.setattr(agent, 'execute', lambda manager, sandbox, selected, timeout, output_limit: {
        'status': 'completed', 'text': selected['path'], 'path': selected['path'], 'start': 1})

    def observe():
        # Different located pages provide new evidence; stagnation is unrelated
        # to removing numerical model/tool allowances.
        actions = [action('read_file', path=f'module_{i}.py', start=1) for i in range(48)]
        result, _, _ = run([*actions, action('submit', reason='verified')], design=default_design('pytest', guides))
        return result['status'], result['model_calls'], result['tool_calls']
    check(observe, expected)


def test_time_deadline_still_applies_when_both_call_budgets_are_unlimited(session):
    run, config, guides = session
    config['budgets'].update(model_calls=0, tool_calls=0, wall_seconds=900)
    ticks = iter([0, 0, 0, 901, 901])

    def observe():
        result, _, _ = run([action('read_file', path='module.py', start=1)],
                            design=default_design('pytest', guides), clock=lambda: next(ticks))
        return result['status'], result['model_calls'], result['tool_calls']
    check(observe, ('wall_budget', 1, 0))


def test_smoke_and_explicit_cli_zero_preserve_unlimited_defaults():
    def observe():
        config = options(SimpleNamespace(config=None, mode='smoke', tasks=None, seeds=None, task_type=None,
                                         agent_seconds=None, model_calls=call_limit('0'), tasks_manifest=None))
        return config['budgets']['wall_seconds'], config['budgets']['model_calls'], config['budgets']['tool_calls']
    check(observe, (900, 0, 0))
