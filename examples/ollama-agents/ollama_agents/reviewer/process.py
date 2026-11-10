"""Bridge the reviewer core to the benchmark's existing JSONL v1 process protocol."""

import hashlib
import sys
from pathlib import Path

from ..budget import BudgetLedger
from ..client import OllamaClient
from ..errors import invalid
from ..evidence import EvidenceWriter
from ..jsonio import decode, encode
from .adapter import ReviewerAdapter
from .schema import PROMPT, PROMPT_VERSION, SCHEMA

CAPABILITIES = ['review_output', 'cancel', 'wall_time', 'tool_calls']
VERSION = 'ollama-reviewer-v2-jsonl-1'


def prompt_hash():
    """Bind the prompt, action schema, version and actual local tool implementation."""
    tools = Path(__file__).with_name('tools.py').read_bytes()
    package = {'prompt': PROMPT, 'schema': SCHEMA, 'version': PROMPT_VERSION,
               'tools_sha256': hashlib.sha256(tools).hexdigest()}
    return hashlib.sha256(encode(package)).hexdigest()


def load_config(path):
    """Read explicit frozen settings without contacting or loading a model."""
    config = decode(Path(path).read_bytes())
    model = config['model']
    if model['prompt_sha256'] != prompt_hash() or model['adapter_version'] != VERSION:
        raise invalid('Configured prompt hash or adapter version differs from this implementation')
    if model['provider'] != 'ollama':
        raise invalid('Reviewer process requires the ollama provider')
    return config


def handshake(config):
    """Confirm declared identity without inference during the bounded handshake."""
    return {'schema_version': 1, 'type': 'capabilities', 'agent_id': config['agent_id'],
            'agent_version': VERSION, 'capabilities': CAPABILITIES, 'model': config['model']}


def review(config, request):
    """Create fresh episode services and seal external evidence before sending completion."""
    writer = EvidenceWriter(archive_root=config['archive_root'], workspace=request['workspace'])
    options = dict(config['model']['parameters'])
    client = OllamaClient(endpoint=config['endpoint'], model=config['model']['model_id'],
                          think=options.pop('think'), options=options)
    budget = BudgetLedger(wall_time_seconds=request['budgets']['wall_time_seconds'],
                          reserve_seconds=5, max_model_calls=6, max_tool_calls=12)
    try:
        return ReviewerAdapter(client=client, budget=budget, evidence=writer).review(request)
    finally:
        writer.finalize()


def serve(config, reader, writer):
    """Emit exactly one JSONL response per handshake or single review request."""
    reviewed = False
    for line in iter(lambda: reader.readline(1024 * 1024 + 1), b''):
        request = incoming(line)
        if request.get('type') == 'capabilities' and request.get('schema_version') == 1:
            event = handshake(config)
        elif request.get('type') == 'request' and not reviewed:
            reviewed = True
            event = review(config, request)
        else:
            raise invalid('Expected v1 capabilities or a single review request')
        writer.write(encode(event) + b'\n')
        writer.flush()


def incoming(line):
    """Reject malformed or oversized JSONL before executing any action."""
    if len(line) > 1024 * 1024 or not line.endswith(b'\n'):
        raise invalid('JSONL input exceeds limit or lacks final newline')
    value = decode(line)
    if not isinstance(value, dict):
        raise invalid('JSONL message must be an object')
    return value


def main(path):
    """Run a configured standalone peer with diagnostics confined to stderr."""
    try:
        serve(load_config(path), sys.stdin.buffer, sys.stdout.buffer)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'Reviewer process: {error}', file=sys.stderr)
        return 1
    return 0
