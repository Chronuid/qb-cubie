"""Keep one developer episode alive across the four JSONL phase requests."""

import hashlib
import sys
from pathlib import Path

from ..budget import BudgetLedger
from ..client import OllamaClient
from ..errors import invalid
from ..evidence import EvidenceWriter
from ..jsonio import decode, encode
from ..reviewer.process import incoming
from .adapter import DeveloperAdapter
from .schema import FRAMEWORK_DOCS, PHASES, PROMPT, PROMPT_VERSION, SCHEMA

CAPABILITIES = ['workspace_changes', 'phased_submission', 'cancel', 'wall_time', 'tool_calls']
VERSION = 'ollama-developer-v4-jsonl-1'


def prompt_hash(mode='cubie'):
    """Bind role, mode, framework documentation, schema and local tools."""
    if mode == 'repair':
        from . import repair
        return hashlib.sha256(encode({'prompt': repair.PROMPT, 'schema': repair.SCHEMA, 'version': repair.PROMPT_VERSION,
                                      'implementation_sha256': hashlib.sha256(Path(repair.__file__).read_bytes()).hexdigest()})).hexdigest()
    if mode not in FRAMEWORK_DOCS:
        raise invalid('Developer mode must be cubie or pytest')
    package = {'prompt': PROMPT, 'schema': SCHEMA, 'version': PROMPT_VERSION,
               'mode': mode, 'framework_docs': FRAMEWORK_DOCS[mode],
               'tools_sha256': hashlib.sha256(Path(__file__).with_name('tools.py').read_bytes()).hexdigest()}
    return hashlib.sha256(encode(package)).hexdigest()


def load_config(path):
    """Validate the frozen role identity before any inference or workspace access."""
    config = decode(Path(path).read_bytes())
    model = config['model']
    if model['prompt_sha256'] != prompt_hash(config['mode']) or model['adapter_version'] != VERSION:
        raise invalid('Configured prompt hash or adapter version differs from this implementation')
    if model['provider'] != 'ollama':
        raise invalid('Developer process requires the ollama provider')
    return config


def handshake(config):
    """Confirm configuration without loading a model or constructing an episode."""
    capabilities = ['workspace_changes', 'project_patch', 'cancel', 'wall_time', 'tool_calls'] if config['mode'] == 'repair' else CAPABILITIES
    return {'schema_version': 1, 'type': 'capabilities', 'agent_id': config['agent_id'],
            'agent_version': VERSION, 'capabilities': capabilities, 'model': config['model']}


def serve(config, reader, writer):
    """Share budgets, frozen tests and evidence until final phase, error or EOF."""
    evidence = None
    adapter = None
    finished = False
    try:
        for line in iter(lambda: reader.readline(1024 * 1024 + 1), b''):
            request = incoming(line)
            if request.get('type') == 'capabilities' and request.get('schema_version') == 1:
                event = handshake(config)
            elif request.get('type') == 'request' and not finished:
                if adapter is None:
                    # Reject an invalid first phase before creating external state.
                    if config['mode'] == 'repair':
                        from .repair import validate_request
                    else:
                        from .schema import validate_request
                    validate_request(request)
                    if request['phase'] != ('repair' if config['mode'] == 'repair' else PHASES[0]):
                        raise invalid('Developer episode must begin with test_design')
                    evidence = EvidenceWriter(archive_root=config['archive_root'], workspace=request['workspace'])
                    options = dict(config['model']['parameters'])
                    client = OllamaClient(endpoint=config['endpoint'], model=config['model']['model_id'],
                                          think=options.pop('think'), options=options)
                    budget = BudgetLedger(wall_time_seconds=request['budgets']['wall_time_seconds'],
                                          reserve_seconds=5, max_model_calls=12, max_tool_calls=40)
                    if config['mode'] == 'repair':
                        from .repair import RepairAdapter
                        adapter = RepairAdapter(client=client, budget=budget, evidence=evidence)
                    else:
                        adapter = DeveloperAdapter(client=client, budget=budget, evidence=evidence, mode=config['mode'])
                event = adapter.develop(request)
                finished = event['status'] != 'completed' or request['phase'] in ('repair', PHASES[-1])
                if finished:
                    assert evidence is not None
                    evidence.finalize()
                    evidence = None
            else:
                raise invalid('Expected v1 capabilities or a single developer episode')
            writer.write(encode(event) + b'\n')
            writer.flush()
    finally:
        if evidence is not None:
            evidence.finalize()


def main(path):
    """Run the configured peer with diagnostics confined to stderr."""
    try:
        serve(load_config(path), sys.stdin.buffer, sys.stdout.buffer)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'Developer process: {error}', file=sys.stderr)
        return 1
    return 0
