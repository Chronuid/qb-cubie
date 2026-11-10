"""Offline boundaries of the real JSONL reviewer entry point."""

import importlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ...benchmarks.contracts import accepted
from ..contracts import failed


@pytest.fixture
def process(api):
    api('BudgetLedger')
    return importlib.import_module('ollama_agents.reviewer.process')


def config(process):
    return {'agent_id': 'offline-reviewer', 'model': {'provider': 'ollama',
            'adapter_version': process.VERSION, 'prompt_sha256': process.prompt_hash()}}


def test_handshake_has_no_inference_or_workspace_side_effects(process, tmp_path):
    path = tmp_path / 'runtime.json'
    path.write_text(json.dumps(config(process)), encoding='utf-8')
    script = Path(__file__).resolve().parents[3] / 'examples/ollama-agents/reviewer_process.py'
    result = accepted(lambda: subprocess.run([sys.executable, '-S', str(script), '--config', str(path)],
                      input='{"schema_version":1,"type":"capabilities"}\n', cwd=tmp_path,
                      capture_output=True, text=True, timeout=5, check=False), expected=lambda value: value.returncode == 0)
    answer, = [json.loads(line) for line in result.stdout.splitlines()]
    assert answer == process.handshake(config(process)) and result.stderr == ''
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('field,value', [('prompt_sha256', '0' * 64), ('adapter_version', 'different')])
def test_stale_configuration_is_rejected_before_handshake(process, tmp_path, field, value):
    payload = config(process)
    payload['model'][field] = value
    path = tmp_path / 'runtime.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    failed(lambda: process.load_config(path), status='invalid_output', match='hash|version')


@pytest.mark.parametrize('body', [b'{}', b'x' * (1024 * 1024 + 1)])
def test_unterminated_or_oversized_jsonl_is_rejected_without_output(process, body):
    output = io.BytesIO()
    failed(lambda: process.serve(config(process), io.BytesIO(body), output),
           status='invalid_output', match='limit|newline')
    assert output.getvalue() == b''
