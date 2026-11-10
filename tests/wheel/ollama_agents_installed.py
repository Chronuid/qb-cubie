"""§5.4: real installed processes/runner/tools with only Ollama HTTP replayed."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import tomllib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

MODEL = 'gemma4:12b'
REVISION = 'offline-replay-digest'
TESTS = '''import pytest
from qb_cubie import EBT, WorldState
from shipping import fee

@pytest.mark.parametrize("subtotal,expected", [(0, 499), (4999, 499), (5000, 0), (9000, 0)])
def test_fee(subtotal, expected):
    trace = EBT(target=fee, pre=WorldState(args=(subtotal,)),
                post=WorldState(returns=expected), reporter=None).run()
    assert trace.evaluation is True
'''


def cli(*args, cwd, code=0):
    command = Path(sys.executable).parent / ('cubie-bench.exe' if os.name == 'nt' else 'cubie-bench')
    result = subprocess.run([str(command), *map(str, args), '--format', 'json'], cwd=cwd,
                            capture_output=True, text=True, timeout=120, check=False)
    assert result.returncode == code, result.stdout + result.stderr
    return json.loads(result.stdout) if code == 0 else result


@pytest.fixture
def provider():
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            calls.append((self.path, None))
            payload = {'/api/version': {'version': 'offline-replay'},
                       '/api/tags': {'models': [{'name': MODEL, 'digest': REVISION,
                                                'details': {'quantization_level': 'REPLAY'}}]},
                       '/api/ps': {'models': []}}[self.path]
            self.send(payload)

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            calls.append((self.path, payload))
            if self.path == '/api/show':
                self.send({'details': {'quantization_level': 'REPLAY'}, 'capabilities': ['completion']})
                return
            assert self.path == '/api/chat'
            action = replay(payload)
            self.send({'model': MODEL, 'done': True, 'done_reason': 'stop',
                       'message': {'role': 'assistant', 'content': json.dumps(action)},
                       'prompt_eval_count': 13, 'eval_count': 7})

        def send(self, payload):
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def replay(payload):
    """Fixed independent actions; no implementation or protocol behavior is mocked."""
    content = json.loads(payload['messages'][1]['content'])
    if 'phase' not in content:
        faulty = '> 5000' in json.dumps(content['context'])
        findings = [{'criterion_id': 'free_threshold', 'path': 'shipping.py', 'symbol': 'is_free',
                     'mechanism': 'Strict comparison excludes the free-shipping boundary.',
                     'impact': 'An order of 5000 cents is charged shipping.'}] if faulty else []
        return {'action': 'submit_review', 'review': {'schema_version': 1, 'findings': findings,
                'criterion_results': {'free_threshold': 'fail' if faulty else 'pass'},
                'sources': ['shipping.py', 'task.md']}}
    if len(payload['messages']) > 2 or content['phase'] == 'refactor':
        return {'action': 'submit_phase'}
    if content['phase'] == 'test_design':
        return {'action': 'write_files', 'files': {'tests/test_fee.py': TESTS}}
    assert content['phase'] == 'green'
    return {'action': 'write_files', 'files': {
        'shipping.py': 'def fee(subtotal):\n    return 0 if subtotal >= 5000 else 499\n',
        'USAGE.md': 'from shipping import fee\nfee(5000)  # 0\n'}}


def exported(tmp_path, endpoint):
    import ollama_agents
    assert Path(ollama_agents.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    root = tmp_path / 'export with spaces'
    cli('init-ollama', root, '--endpoint', endpoint, cwd=tmp_path)
    # Relocation proves config, launcher and archive paths do not bind the export location.
    moved = tmp_path / 'relocated example'
    shutil.move(root, moved)
    return moved


def test_installed_export_handshakes_and_plans_do_not_infer(tmp_path, provider):
    endpoint, calls = provider
    root = exported(tmp_path, endpoint)
    cli('validate', root / 'package', '--check-references', cwd=tmp_path)
    for role, count in [('reviewer', 2), ('developer', 1)]:
        answer = cli('validate-agent', root / f'agents/{role}.toml', cwd=tmp_path)
        declared = tomllib.loads((root / f'agents/{role}.toml').read_text())
        runtime = json.loads((root / f'adapter/{role}.json').read_bytes())
        assert answer['model_provenance'] == {**declared['model'], 'source': 'matched_agent_handshake'}
        assert declared['model'] == runtime['model']
        assert declared['model']['revision'] == REVISION
        plan = cli('plan', '--suite', root / f'sets/{role}.toml', cwd=tmp_path)
        assert len(plan['runs']) == count
    assert not (root / 'adapter-evidence').exists()
    assert [route for route, _ in calls] == ['/api/version', '/api/tags', '/api/ps', '/api/show']
    identity = json.loads((root / 'installation.json').read_bytes())
    assert identity['wheel_sha256'] == os.environ['QB_CUBIE_TEST_WHEEL_SHA256']
    assert identity['provider_sha256'] == hashlib.sha256((root / 'provider.json').read_bytes()).hexdigest()
    cli('init-ollama', root, '--endpoint', endpoint, cwd=tmp_path, code=2)
    assert len(calls) == 4


def test_both_installed_smoke_sets_keep_model_calls_usage_and_hash_bound_evidence(tmp_path, provider):
    endpoint, calls = provider
    root = exported(tmp_path, endpoint)
    results = [cli('run', '--suite', root / f'sets/{role}.toml', cwd=tmp_path)
               for role in ('reviewer', 'developer')]
    runs = [run for result in results for run in result['runs']]
    assert len(runs) == 3
    assert all(run['status'] == 'completed' and run['quality_passed'] for run in runs)
    developer, = [run for run in runs if run['benchmark'] == 'developer_agent']
    assert developer['process_passed'] is True
    assert all(run['model_id'] == MODEL and run['usage']['input_tokens'] > 0 for run in runs)
    manifests = list((root / 'adapter-evidence').glob('*/manifest.json'))
    assert len(manifests) == 3
    records = []
    for path in manifests:
        manifest = json.loads(path.read_bytes())
        for name, digest in manifest['artifact_hashes'].items():
            assert hashlib.sha256((path.parent / name).read_bytes()).hexdigest() == digest
        records += [json.loads((path.parent / name).read_bytes()) for name in manifest['steps']]
    chat = [payload for route, payload in calls if route == '/api/chat']
    assert len(chat) == len(records) == 7
    assert sum(run['usage']['input_tokens'] for run in runs) == len(chat) * 13
    assert sum(run['usage']['output_tokens'] for run in runs) == len(chat) * 7
    outcomes = {record['tool_result']['test_outcome'] for record in records
                if isinstance(record['tool_result'], dict) and 'test_outcome' in record['tool_result']}
    assert outcomes == {'assertion_failure', 'passed'}
    assert all(payload['model'] == MODEL and payload['think'] is False for payload in chat)
    bound_manifests = []
    for result in results:
        output = Path(result['output'])
        manifest = json.loads((output / 'manifest.json').read_bytes())
        assert all(hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
                   for name, digest in manifest['artifact_hashes'].items())
        for stderr in output.glob('episodes/*/transport/stderr.log'):
            summary, = [json.loads(line) for line in stderr.read_text().splitlines()]
            evidence_path = Path(summary['manifest_path'])
            assert hashlib.sha256(evidence_path.read_bytes()).hexdigest() == summary['manifest_sha256']
            bound_manifests.append(evidence_path)
    assert set(bound_manifests) == set(manifests)


def test_unavailable_model_fails_without_creating_an_example_or_inference(tmp_path, provider):
    endpoint, calls = provider
    destination = tmp_path / 'missing-model'
    result = cli('init-ollama', destination, '--endpoint', endpoint, '--model', 'missing:explicit', cwd=tmp_path, code=2)
    assert 'no automatic pull or fallback' in result.stderr
    assert not destination.exists()
    assert not any(route == '/api/chat' for route, _ in calls)
