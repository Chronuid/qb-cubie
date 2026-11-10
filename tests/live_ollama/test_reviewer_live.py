"""Two concrete EBT contracts using actual Ollama inference, never a replay."""

import json
import os
import urllib.request

import pytest

from qb_cubie import EBT, JsonReporter, PytestReporter, WorldState
from qb_cubie.benchmarks.contracts.protocols import validate_agent_event

from ..ollama_agents.reviewer.support import SOURCES, hashes, request

pytestmark = pytest.mark.skipif(os.environ.get('CUBIE_RUN_OLLAMA_SMOKE') != '1',
                                reason='Enable real inference with CUBIE_RUN_OLLAMA_SMOKE=1')
OPTIONS = {'temperature': 0, 'seed': 42, 'num_ctx': 16384, 'num_predict': 2048}
MODEL = 'gemma4:12b'


def metadata(endpoint):
    result = {}
    for name in ('version', 'tags', 'ps'):
        with urllib.request.urlopen(endpoint + '/api/' + name, timeout=10) as response:
            result[name] = json.load(response)
    assert any(model['name'] == MODEL for model in result['tags']['models']), f'{MODEL} must be installed'
    return result


def save(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def observe(adapter, incoming, root, before):
    event = adapter.review(incoming)
    validate_agent_event(event, incoming)
    save(root.parent / 'event.json', event)
    payload = json.loads((root / 'review.json').read_bytes()) if (root / 'review.json').exists() else {}
    return {'status': event['status'], 'criterion_results': payload.get('criterion_results'),
            'sources': sorted(payload.get('sources', [])),
            'originals_unchanged': {key: hashes(root).get(key) for key in before} == before,
            'artifact_bound': event['artifact_hashes'] == {'review.json': hashes(root).get('review.json')},
            'locations': sorted((f['criterion_id'], f['path'], f['symbol']) for f in payload.get('findings', [])),
            'reproducible_impact': all('&amp;' in f['impact'] and '&' in f['impact'].replace('&amp;', '')
                                       for f in payload.get('findings', [])),
            'measured_tokens': all(type(event['usage'][key]) is int and event['usage'][key] > 0
                                   for key in ('input_tokens', 'output_tokens'))}


def execute_contract(adapter, incoming, root, before, expected):
    result = EBT(target=observe, pre=WorldState(args=(adapter, incoming, root, before)),
                 post=WorldState(returns=expected), reporter=JsonReporter(root.parent / 'ebt.json')).run()
    PytestReporter().report(result)
    assert result.evaluation is True and result.traces[0].evaluation is True


@pytest.mark.parametrize('variant,decision', [('conform', 'pass'), ('faulty', 'fail')])
def test_real_reviewer_ebt(api, reviewer_api, review_workspace, tmp_path, variant, decision):
    root = review_workspace(variant)
    endpoint = os.environ.get('CUBIE_OLLAMA_ENDPOINT', 'http://localhost:11434').rstrip('/')
    save(tmp_path / 'provider.json', {**metadata(endpoint), 'options': OPTIONS, 'think': False})
    writer = api('EvidenceWriter')(archive_root=tmp_path / 'archives', workspace=root)
    adapter = real_adapter(api, reviewer_api, endpoint, writer)
    expected = expectation(decision)
    try:
        execute_contract(adapter, request(root), root, hashes(root), expected)
    finally:
        save(tmp_path / 'archive.json', writer.finalize())
        save(tmp_path / 'provider-after.json', metadata(endpoint))


def real_adapter(api, reviewer_api, endpoint, writer):
    client = api('OllamaClient')(endpoint=endpoint, model=MODEL, options=OPTIONS, think=False)
    budget = api('BudgetLedger')(wall_time_seconds=300, max_model_calls=6,
                               max_tool_calls=12, reserve_seconds=5)
    return reviewer_api(client=client, budget=budget, evidence=writer, context_max_bytes=65536)


def expectation(decision):
    return {'status': 'completed',
            'criterion_results': {'markup_escaping': decision, 'unicode_preserved': 'pass'},
            'sources': SOURCES, 'originals_unchanged': True, 'artifact_bound': True,
            'locations': [('markup_escaping', 'escaping.py', 'escape_text')] if decision == 'fail' else [],
            'measured_tokens': True, 'reproducible_impact': True}
