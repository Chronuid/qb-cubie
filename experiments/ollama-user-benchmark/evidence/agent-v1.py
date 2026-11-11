"""Standalone Ollama agent: only public JSONL protocol and Python stdlib."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

CAPABILITIES = ['workspace_changes', 'phased_submission', 'wall_time', 'cancel', 'tool_calls']
SYSTEM = '''You are a Python development agent. Return JSON only: {"files": {"relative/path": "complete file content"}}.
In test_design write tests/test_project.py only. Use executable pytest tests with qb_cubie EBT(target=function, pre=WorldState(args=(...)), post=WorldState(returns=expected), reporter=None).run(); assert trace.evaluation is True. For invalid inputs use pytest.raises(ValueError) directly. Do not implement production code yet.
In green implement the task in the existing production module only; never change tests.
Do not read or invent evaluator files. No markdown fences. Files must contain complete Python source.'''


def reply(request):
    workspace = Path(request['workspace'])
    usage = {'input_tokens': 0, 'output_tokens': 0, 'cost': None}
    # Red observes frozen tests; refactor retains the passing implementation.
    if request['phase'] in ('test_design', 'green'):
        context = {p.relative_to(workspace).as_posix(): p.read_text()
                   for p in sorted(workspace.rglob('*'))
                   if p.is_file() and (p.suffix == '.py' or p.name == 'task.md')}
        prompt = json.dumps({'phase': request['phase'], 'task': request['task'], 'files': context})
        payload = {'model': 'gemma4:12b', 'stream': False, 'think': False, 'format': 'json',
                   'options': {'temperature': 0, 'seed': 42, 'num_predict': 4096},
                   'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt}]}
        req = urllib.request.Request('http://localhost:11434/api/chat',
                                     json.dumps(payload).encode(), {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=240) as response:
            result = json.load(response)
        print(json.dumps({'phase': request['phase'], 'ollama': result}), file=sys.stderr, flush=True)
        if result.get('done_reason') == 'length':
            raise ValueError('Model output truncated')
        files = json.loads(result['message']['content'])['files']
        allowed = {'tests/test_project.py'} if request['phase'] == 'test_design' else {
            name for name in context if '/' not in name and name.endswith('.py')}
        if not files or not set(files) <= allowed:
            raise ValueError(f'Unexpected model paths: {list(files)}; allowed: {allowed}')
        for name, content in files.items():
            dest = workspace / name
            if dest.is_symlink():
                raise ValueError('Symlink output')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
        usage.update(input_tokens=result.get('prompt_eval_count'), output_tokens=result.get('eval_count'))
    names = sorted(p.relative_to(workspace).as_posix() for p in workspace.rglob('*.py')
                   if '__pycache__' not in p.parts)
    return dict(schema_version=1, type='event', run_id=request['run_id'],
                scenario_id=request['scenario_id'], phase=request['phase'], status='completed',
                artifacts=names, artifact_hashes={n: hashlib.sha256((workspace/n).read_bytes()).hexdigest()
                                                  for n in names}, usage=usage)


def main():
    for line in sys.stdin:
        request = json.loads(line)
        if request['type'] == 'capabilities':
            event = dict(schema_version=1, type='capabilities', agent_id='ollama-user',
                         agent_version='1.0.0', capabilities=CAPABILITIES)
        elif request['type'] == 'request':
            event = reply(request)
        else:
            raise ValueError(f'Unsupported message: {request["type"]}')
        print(json.dumps(event), flush=True)


if __name__ == '__main__':
    main()
