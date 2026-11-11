"""One actual benchmark episode from JSONL/Ollama through independent evaluation to RBT."""

import hashlib
import importlib
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from qb_cubie import EBT, JsonReporter, PytestReporter, WorldState
from qb_cubie.benchmarks import run_suite

from ..benchmarks.phase3.conftest import write_suite
from ..ollama_agents.reviewer.support import CRITERIA
from .test_reviewer_live import MODEL, OPTIONS, metadata, save

pytestmark = pytest.mark.skipif(os.environ.get('CUBIE_RUN_OLLAMA_SMOKE') != '1',
                                reason='Enable real inference with CUBIE_RUN_OLLAMA_SMOKE=1')
ROOT = Path(__file__).resolve().parents[2]


def scenario(external, visible):
    base = external / 'scenarios/review-correct'
    shutil.rmtree(base / 'visible')
    shutil.copytree(visible, base / 'visible')
    shutil.move(base / 'visible/task.md', base / 'task.md')
    path = base / 'scenario.json'
    payload = json.loads(path.read_bytes())
    payload.update(title='Live markup review through RBT', criteria=CRITERIA)
    save(path, payload)
    save(base / 'evaluator/reference.json', {'schema_version': 1, 'validation_status': 'author_checked',
         'human_reviews': [], 'criterion_results': dict.fromkeys(CRITERIA, 'pass'), 'findings': []})


def configure(external, endpoint, observed, process):
    installed = next(model for model in observed['tags']['models'] if model['name'] == MODEL)
    model = {'model_id': MODEL, 'revision': installed['digest'], 'provider': 'ollama',
             'provider_version': observed['version']['version'], 'adapter_version': process.VERSION,
             'prompt_sha256': process.prompt_hash(), 'parameters': {**OPTIONS, 'think': False}}
    runtime = external / 'agents/runtime.json'
    save(runtime, {'agent_id': 'ollama-gemma4-reviewer', 'model': model, 'endpoint': endpoint,
                   'archive_root': str(external.parent / 'adapter-evidence')})
    write_agent(external, runtime, model, process.CAPABILITIES)


def write_agent(external, runtime, model, capabilities):
    example = ROOT / 'experiments/ollama-agents'
    command = [sys.executable, str(example / 'reviewer_process.py'), '--config', str(runtime)]
    lines = ['schema_version = 1', 'transport = "jsonl-v1"', 'id = "ollama-gemma4-reviewer"',
             f'cwd = {json.dumps(str(example))}', f'command = {json.dumps(command)}',
             f'capabilities = {json.dumps(capabilities)}', '[model]']
    lines += [f'{key} = {json.dumps(value)}' for key, value in model.items() if key != 'parameters']
    lines += ['[model.parameters]']
    lines += [f'{key} = {json.dumps(value)}' for key, value in model['parameters'].items()]
    (external / 'agents/current.toml').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def observe_pipeline(suite):
    result = run_suite(suite)
    output = Path(result['output'])
    run, = result['runs']
    rbt, = output.rglob('rbt.json')
    evaluation, = output.rglob('review-evaluation.json')
    archived = json.loads(evaluation.read_bytes())
    return {'status': run['status'], 'evaluated': run['evaluation_status'],
            'quality_passed': run['quality_passed'], 'condition': run['condition'],
            'model_id': run['model_id'], 'criteria': run['criterion_results'],
            'rbt': json.loads(rbt.read_bytes()), 'independent_quality': archived['quality_passed'],
            'rbt_report_bound': json.loads(rbt.read_bytes())['report'] == archived['response'],
            'manifest_valid': manifest_valid(output), 'real_evidence': real_evidence(suite.parent.parent, run)}


def manifest_valid(output):
    manifest = json.loads((output / 'manifest.json').read_bytes())
    return bool(manifest['artifact_hashes']) and all(
        hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
        for name, digest in manifest['artifact_hashes'].items())


def real_evidence(external, run):
    manifests = list((external.parent / 'adapter-evidence').glob('*/manifest.json'))
    records = [json.loads((path.parent / name).read_bytes()) for path in manifests
               for name in json.loads(path.read_bytes())['steps']]
    return bool(records) and any(record['raw_response'].get('model') == MODEL for record in records
                                if isinstance(record['raw_response'], dict)) and all(
        type(run['usage'][key]) is int and run['usage'][key] > 0 for key in ('input_tokens', 'output_tokens'))


def test_benchmark_ollama_evaluator_and_rbt_form_one_pipeline(external, review_workspace, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'experiments/ollama-agents'))
    process = importlib.import_module('ollama_agents.reviewer.process')
    endpoint = os.environ.get('CUBIE_OLLAMA_ENDPOINT', 'http://localhost:11434').rstrip('/')
    observed = metadata(endpoint)
    save(tmp_path / 'provider.json', observed)
    scenario(external, review_workspace())
    configure(external, endpoint, observed, process)
    suite = write_suite(external, 'ids = ["shop/review-correct"]', seconds=180)
    execute_contract(suite, tmp_path)


def execute_contract(suite, tmp_path):
    expected = {'status': 'completed', 'evaluated': 'complete', 'quality_passed': True,
                'condition': 'cubie', 'model_id': MODEL, 'criteria': dict.fromkeys(CRITERIA, 'pass'),
                'rbt': lambda value: value['passed'] is True and value['report']['findings'] == [],
                'independent_quality': True, 'rbt_report_bound': True, 'manifest_valid': True, 'real_evidence': True}
    result = EBT(target=observe_pipeline, pre=WorldState(args=(suite,)), post=WorldState(returns=expected),
                 reporter=JsonReporter(tmp_path / 'pipeline-ebt.json')).run()
    PytestReporter().report(result)
    assert result.evaluation is True and result.traces[0].evaluation is True
