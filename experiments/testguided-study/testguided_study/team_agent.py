"""Run one serial v6 team within one frozen study attempt and budget."""

import time

from ollama_agents.client import OllamaClient
from ollama_agents.errors import AdapterError

from .artifacts import write
from .controller import compact_observation, context_capacity
from .design import design_schema
from .iteration import identity
from .team import TeamController
from .team_workspace import RemoteWorkspace
from .telemetry import emit
from .workspace import execute


def develop(manager, sandbox, task, row, config, guides, directory, *, design,
            client=None, observer=None, clock=None, visible_baseline=None, store=None, io=None):
    clock = clock or time.monotonic
    limits, model = config['budgets'], config['ollama']
    if model['think'] is not False:
        raise ValueError('V6 requires explicit think=false; freeze another variant to change it')
    if design['specialization']['mode'] != row['mode'] or row.get('design_id', identity(design)) != identity(design):
        raise ValueError('Team design does not match the frozen run')
    client = client or OllamaClient(endpoint=model['endpoint'], model=model['model'], think=False,
                                    options={key: model[key] for key in ('temperature', 'num_ctx', 'num_predict')}
                                    | {'seed': row['seed']})
    started = clock()
    store = store or RemoteWorkspace(manager, sandbox)
    policy = dict(design['core']['policy'])
    # Configuration may tighten a frozen design budget, never extend it.
    for key in ('wall_seconds', 'model_calls', 'tool_calls', 'context_bytes'):
        configured, frozen = limits[key], policy[key]
        if configured:
            policy[key] = min(configured, frozen) if frozen else configured
    policy['context_bytes'] = min(policy['context_bytes'], context_capacity(limits, model, design_schema(design)))

    def port(action):
        timeout = max(1, min(limits['command_seconds'], policy['wall_seconds'] - (clock() - started)))
        return execute(manager, sandbox, {**action, 'team': True}, timeout, limits['output_chars'])

    team = TeamController(workspace='/workspace', artifact_dir=directory, mode=row['mode'],
                          issue=task.problem_statement, guides={**guides, row['mode']: design['specialization']['guide']},
                          manifest=store.manifest, policy=policy, execute=io or port, clock=clock,
                          store=store, design=design)
    # Setup time belongs to this same attempt, not a fresh role budget.
    team.started = started
    write(directory / 'team-design.json', design)
    if visible_baseline is not None:
        record = team._record(visible_baseline, baseline=True, scope='original visible suite before agent edits')
        team.context['visible_baseline'] = compact_observation(record, 3000)
    emit(observer, 'agent_started', 'V6-Team gestartet', active={'agent_started_at': time.time(),
         'role': team.role, 'wall_seconds': policy['wall_seconds'],
         'max_model_calls': policy['model_calls'], 'max_tool_calls': policy['tool_calls']})
    usage, observations = [], []
    while team.status == 'running':
        request = team.request()
        if request is None:
            break
        role = request['role']
        emit(observer, 'model_request', f"{row['run_id']} · {role}: Modell antwortet …", state='model_wait',
             active={'step': team.metrics['model_calls'] - 1, 'role': role, 'stage': team.state,
                     'operation': 'model', 'model_calls': team.metrics['model_calls'],
                     'tool_calls': team.metrics['tool_calls'], 'job_id': team.active_job['id'],
                     'context_revision': team.context_revision},
             agent={'context': request['messages'], 'schema': request['schema'], 'team': team.snapshot(),
                    'action': None, 'result': None, 'response': None})
        before = clock()
        remaining = policy['wall_seconds'] - (before - started)
        if remaining <= 0:
            team.finish('wall_budget')
            break
        try:
            response = client.chat(messages=request['messages'], schema=request['schema'], timeout=remaining)
        except AdapterError as error:
            usage.append(error.usage or {})
            if error.status == 'invalid_output':
                team.reject_output(raw=error.raw, usage=error.usage or {}, seconds=clock() - before)
            else:
                team.record_response({'status': error.status, 'error': str(error), 'raw': error.raw,
                                      'usage': error.usage or {}}, clock() - before)
                team.finish(error.status)
            emit(observer, 'model_error', f'{role}: {error.status}', state='model_error',
                 agent={'last_error': {'error': str(error), 'status': error.status, 'step': team.metrics['model_calls']}})
            continue
        usage.append(response.get('usage', {}))
        team.record_response(response, clock() - before)
        action = response['action']
        emit(observer, 'tool_started', f"{role}: {action['action']}", state='tool_wait',
             active={'operation': action['action'], 'role': role}, agent={'response': response, 'action': action})
        result = team.dispatch(role, action)
        write(directory / f'steps/{team.metrics["model_calls"] - 1:04d}-tool.json',
              {'role': role, 'action': action, 'result': result})
        if action['action'] in {'run_tests', 'check_baseline'}:
            observations.append({'targets': action['targets'], 'observation': result.get('observation'),
                                 'baseline': action['action'] == 'check_baseline',
                                 **result.get('versions', {}), 'role': role, 'evidence_id': result.get('evidence_id')})
        emit(observer, 'tool_finished', f"{role}: {action['action']} · {result['status']}", state=team.state,
             active={'role': team.role, 'stage': team.state, 'job_id': team.active_job['id'],
                     'tool_calls': team.metrics['tool_calls'], 'context_revision': team.context_revision,
                     'reserve_active': team.reserve},
             agent={'result': compact_observation(result), 'team': team.snapshot()})
    team._archive()
    final = store.patch()
    (directory / 'full.patch').write_text(final, encoding='utf-8')
    submitted = store.production_patch() if hasattr(store, 'production_patch') else final
    (directory / 'production.patch').write_text(submitted, encoding='utf-8')
    state = team.snapshot()
    emit(observer, 'agent_finished', f"V6-Team beendet: {state['status']} · {state['completion']['status']}",
         state='agent_finished', active={'agent_finished_at': time.time(), 'operation': 'evaluation'},
         agent={'stop_reason': state['reason'] or state['status'], 'team': state})
    return {'design_id': identity(design), 'status': state['status'], 'reason': state['reason'],
            'completion': state['completion'], 'private_evaluation_required': True,
            'model_calls': team.metrics['model_calls'], 'tool_calls': team.metrics['tool_calls'],
            'duration_seconds': clock() - started, 'usage': usage, 'test_observations': observations,
            'repairs': team.metrics['output_repairs'], 'process_metrics': team.metrics,
            'final_versions': state['versions'], 'team': state, 'patch': submitted,
            'context_policy': {'capacity_bytes': policy['context_bytes'], 'token_measurement': 'provider_usage',
                               'estimate': 'two_utf8_bytes_per_token'}}
