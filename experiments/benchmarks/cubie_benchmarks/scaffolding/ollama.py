"""Export installed role adapters, frozen model settings and separate smoke sets."""

import json
import shutil
import sys
from importlib import import_module
from importlib.resources import as_file, files
from pathlib import Path
from urllib.request import Request, urlopen

from cubie_benchmarks.adapters.provenance import validate_model
from cubie_benchmarks.measurement._toml import write_toml
from cubie_benchmarks.reporting._files import (
    copy_tree,
    digest,
    now,
    wheel_hash,
    write_json,
)
from cubie_benchmarks.scaffolding.custom import _available
from cubie_benchmarks.scaffolding.templates import _review_sources, _write

LAUNCHER = '''"""Run the explicitly exported adapter under isolated Python."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--role', choices=['reviewer', 'developer'], required=True)
parser.add_argument('--config', required=True)
args = parser.parse_args()
if args.role == 'reviewer':
    from ollama_agents.reviewer.process import main
else:
    from ollama_agents.developer.process import main
raise SystemExit(main(args.config))
'''


def _observe(endpoint, model):
    """Read provider identity and load state; never pull, load or chat here."""
    def fetch(route, payload=None):
        """Read a bounded provider metadata response without inference."""
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        request = Request(endpoint + '/api/' + route, data=data, headers={'Content-Type': 'application/json'})
        with urlopen(request, timeout=10) as response:
            return json.load(response)
    return {'version': fetch('version'), 'tags': fetch('tags'), 'ps': fetch('ps'),
            'show': fetch('show', {'model': model}), 'observed_at': now()}


def init_ollama(path: str | Path, *, endpoint='http://localhost:11434', model='gemma4:12b') -> dict:
    """Freeze the explicitly selected local model and export a standalone example."""
    path = Path(path).resolve()
    _available(path)
    endpoint = endpoint.rstrip('/')
    observed = _observe(endpoint, model)
    models = _models(observed, model)
    _export(path)
    _provider(path, observed)
    for role, metadata in models.items():
        _role(path, role, metadata, endpoint)
    return {'example': str(path), 'reviewer_suite': str(path / 'sets/reviewer.toml'),
            'developer_suite': str(path / 'sets/developer.toml'), 'revision': models['reviewer']['revision']}


def _models(observed, model):
    """Validate the selected identity before publishing any exported files."""
    matches = [entry for entry in observed['tags']['models'] if entry['name'] == model]
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one installed model named {model}; no automatic pull or fallback')
    base = {'model_id': model, 'revision': matches[0]['digest'], 'provider': 'ollama',
            'provider_version': observed['version']['version']}
    models = {}
    for role in ('reviewer', 'developer'):
        process = import_module(f'ollama_agents.{role}.process')
        models[role] = _model(base, process, 2048 if role == 'reviewer' else 4096)
        validate_model(models[role])
    return models


def _model(base, process, predict):
    """Bind role prompts and explicit calibration parameters to the provider identity."""
    return {**base, 'adapter_version': process.VERSION, 'prompt_sha256': process.prompt_hash(),
            'parameters': {'temperature': 0, 'seed': 42, 'num_ctx': 16384,
                           'num_predict': predict, 'think': False}}


def _export(path):
    """Export installed adapter helpers and scenario materials without a fake peer."""
    with as_file(files('ollama_agents')) as source:
        copy_tree(source, path / 'adapter/ollama_agents')
    with as_file(files('cubie_benchmarks').joinpath('data/shipping')) as source:
        copy_tree(source, path / 'package')
    _review_sources(path / 'package')
    shutil.rmtree(path / 'package/agents')
    _write(path / 'adapter/process.py', LAUNCHER)
    guide = files('cubie_benchmarks').joinpath('data/GUIDE_Ollama-Agents.md').read_text(encoding='utf-8')
    _write(path / 'README.md', guide)


def _provider(path, observed):
    """Persist raw provider metadata and installed wheel provenance together."""
    write_json(path / 'provider.json', observed)
    write_json(path / 'installation.json', {'schema_version': 1, 'wheel_sha256': wheel_hash(),
               'provider_sha256': digest(path / 'provider.json'), 'python': sys.version})


def _role(path, role, model, endpoint):
    """Export one role's configuration and conservative smoke selection."""
    process = import_module(f'ollama_agents.{role}.process')
    _agent(path, role, process.CAPABILITIES, model, endpoint)
    _suite(path, role)


def _agent(path, role, capabilities, model, endpoint):
    """Use relative example paths; bind the selected interpreter explicitly."""
    agent_id = f'ollama-gemma4-{role}'
    runtime = {'agent_id': agent_id, 'model': model, 'endpoint': endpoint,
               'archive_root': '../adapter-evidence', 'mode': 'cubie'}
    write_json(path / f'adapter/{role}.json', runtime)
    command = [sys.executable, '-I', 'process.py', '--role', role, '--config', f'{role}.json']
    header = {'schema_version': 1, 'id': agent_id, 'transport': 'jsonl-v1', 'cwd': '../adapter',
              'command': command, 'capabilities': capabilities, 'adapter_files': ['ollama_agents']}
    (path / 'agents').mkdir(exist_ok=True)
    write_toml(path / f'agents/{role}.toml', {**header, 'model': model})


def _suite(path, role):
    """Keep role selection and conservative episode limits explicit."""
    count, seconds, tools = (2, 300, 20) if role == 'reviewer' else (1, 1800, 100)
    benchmark = 'review_agent' if role == 'reviewer' else 'developer_agent'
    suite = {'schema_version': 1, 'name': f'ollama-{role}-smoke', 'profile': 'agent-evaluation', 'repetitions': 1,
             'agents': [f'../agents/{role}.toml'], 'output': f'../results/{role}', 'sources': [{'path': '../package'}],
             'select': {'benchmarks': [benchmark]}, 'budgets': {'wall_time_seconds': seconds, 'tool_calls': tools},
             'limits': {'max_runs': count, 'max_total_wall_time_seconds': count * seconds}}
    (path / 'sets').mkdir(exist_ok=True)
    write_toml(path / f'sets/{role}.toml', suite)
