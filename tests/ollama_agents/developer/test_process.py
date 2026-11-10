"""Stateful JSONL process boundaries, including EOF and failed phase cleanup."""

import importlib
import io
import json

import pytest

from ..conftest import ReplayTransport, client
from .support import (
    CODE_PATH,
    DOC,
    GOOD,
    SUBMIT,
    TEST_PATH,
    TESTS,
    request,
    response,
    write,
)


@pytest.fixture
def process(api):
    api('BudgetLedger')
    return importlib.import_module('ollama_agents.developer.process')


def configuration(process, tmp_path):
    return {'agent_id': 'ollama-gemma4-developer', 'mode': 'cubie',
            'endpoint': 'http://no-network.invalid', 'archive_root': str(tmp_path / 'archives'),
            'model': {'provider': 'ollama', 'model_id': 'gemma4:12b',
                      'parameters': {'think': False}, 'adapter_version': process.VERSION,
                      'prompt_sha256': process.prompt_hash()}}


def serve(process, config, messages):
    reader = io.BytesIO(b''.join(json.dumps(message).encode() + b'\n' for message in messages))
    writer = io.BytesIO()
    process.serve(config, reader, writer)
    return [json.loads(line) for line in writer.getvalue().splitlines()]


def test_handshake_has_no_inference_or_archive(process, tmp_path):
    config = configuration(process, tmp_path)
    assert serve(process, config, [{'schema_version': 1, 'type': 'capabilities'}]) == [process.handshake(config)]
    assert list(tmp_path.iterdir()) == []
    assert process.prompt_hash('cubie') != process.prompt_hash('pytest')


@pytest.mark.parametrize('field,value', [('prompt_sha256', '0' * 64), ('adapter_version', 'stale')])
def test_stale_identity_rejected_before_handshake(process, tmp_path, field, value):
    config = configuration(process, tmp_path)
    config['model'][field] = value
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='hash|version'):
        process.load_config(path)
    assert not (tmp_path / 'archives').exists()


def test_wrong_first_phase_creates_no_archive(process, tmp_path, developer_workspace):
    with pytest.raises(ValueError, match='test_design'):
        serve(process, configuration(process, tmp_path), [request(developer_workspace, 'green')])
    assert not (tmp_path / 'archives').exists()


def test_model_sees_test_directory_grant_and_actionable_path_correction(
        process, api, developer_api, developer_workspace, tmp_path):
    from .support import session
    adapter, transport, _ = session(api, developer_api, developer_workspace, tmp_path,
                                   [write({'test_design.py': TESTS}), write({TEST_PATH: TESTS}), SUBMIT])
    event = adapter.develop(request(developer_workspace, 'test_design'))
    assert event['status'] == 'completed'
    first = json.loads(transport.requests[0][0].data)
    correction = json.loads(transport.requests[1][0].data)
    assert 'tests/test_shipping.py' in first['messages'][0]['content']
    assert 'After observing this business red, your next action must be submit_phase.' in first['messages'][0]['content']
    assert any('below tests/' in message['content'] for message in correction['messages'][2:])
    assert not (developer_workspace / 'test_design.py').exists()


def test_documented_ebt_example_produces_business_red_inside_a_test_function(
        process, api, developer_api, developer_workspace, tmp_path):
    from ollama_agents.developer.schema import FRAMEWORK_DOCS

    from .support import session

    # Instantiate the public template for the visible task, preserving its test structure.
    example = 'import pytest\n' + FRAMEWORK_DOCS['cubie'].split('import pytest\n', 1)[1].split('\nNever execute', 1)[0]
    example = example.replace('from module_under_test import function', 'from pricing.policy import fee as function')
    example = example.replace('input_a, result_a', '0, 7').replace('input_b, result_b', '100, 0')
    adapter, _, _ = session(api, developer_api, developer_workspace, tmp_path,
                            [write({TEST_PATH: example}), SUBMIT])
    event = adapter.develop(request(developer_workspace, 'test_design'))
    assert event['status'] == 'completed'
    assert adapter.observation['test_outcome'] == 'assertion_failure'
    assert len(adapter.observation['cases']) == 2


@pytest.mark.parametrize('ending', ['eof', 'wrong-phase', 'complete'])
def test_episode_shares_state_and_seals_on_completion_failure_or_eof(
        process, api, tmp_path, developer_workspace, monkeypatch, ending):
    actions = [write({TEST_PATH: TESTS}), SUBMIT]
    if ending == 'complete':
        actions += [write({CODE_PATH: GOOD, 'USAGE.md': DOC}), SUBMIT, SUBMIT]
    transport = ReplayTransport(*(response(action) for action in actions))
    monkeypatch.setattr(process, 'OllamaClient', lambda **kwargs: client(api, transport))
    phases = ['test_design']
    if ending == 'complete':
        phases += ['red', 'green', 'refactor']
    elif ending == 'wrong-phase':
        phases += ['green']
    events = serve(process, configuration(process, tmp_path), [request(developer_workspace, phase) for phase in phases])
    assert len(events) == len(phases)
    assert events[-1]['status'] == ('invalid_output' if ending == 'wrong-phase' else 'completed')
    assert (developer_workspace / TEST_PATH).read_text() == TESTS
    if ending == 'complete':
        assert events[1]['usage'] == {'input_tokens': 0, 'output_tokens': 0, 'cost': None}
        assert (developer_workspace / CODE_PATH).read_text() == GOOD
    manifest, = (tmp_path / 'archives').glob('*/manifest.json')
    assert len(json.loads(manifest.read_bytes())['steps']) == len(actions)
    assert not transport.responses
