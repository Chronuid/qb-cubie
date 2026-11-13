"""Check production Docker command policy using a controlled command boundary."""

import json
import subprocess
import sys
import types
from copy import deepcopy

import pytest

from cubie_benchmarks.swebench.runtime import ContainerExecutor
from cubie_benchmarks.swebench.validation import LIMITS, bind_request

IMAGE = 'sha256:' + 'd' * 64


def runtime(tmp_path, monkeypatch, *, fail_start=False):
    commands = []
    instance = ContainerExecutor.__new__(ContainerExecutor)
    instance.revision, instance.environments = 'b' * 40, {}
    instance.spec = lambda request: (types.SimpleNamespace(eval_script='echo actual-test-output\n'), 'mutable:tag')
    grader = types.ModuleType('swebench.harness.grading')
    grader.get_logs_eval = lambda spec, log: ({'test-issue': 'PASSED', 'test-regression': 'PASSED'}, True)
    monkeypatch.setitem(sys.modules, 'swebench.harness.grading', grader)

    def command(arguments, **kwargs):
        commands.append(arguments)
        if arguments[:2] == ['start', '--attach'] and fail_start:
            raise ValueError('container executor: timed out')
        payload = ([{'Id': IMAGE, 'RepoDigests': []}] if arguments[:2] == ['image', 'inspect'] else
                   [{'State': {'OOMKilled': False}}] if arguments[0] == 'inspect' else {})
        return subprocess.CompletedProcess(arguments, 0, json.dumps(payload).encode(), b'')

    instance.command = command
    request = {'instance_id': 'demo__calc-1', 'run_id': 'fresh-run', 'network': False,
               'harness_revision': instance.revision, 'stage': 'gold', 'base_commit': 'a' * 40,
               'patch': 'gold patch bytes', 'test_patch': 'private test patch bytes', 'limits': deepcopy(LIMITS),
               'FAIL_TO_PASS': ['test-issue'], 'PASS_TO_PASS': ['test-regression'], 'output_dir': str(tmp_path)}
    return instance, commands, request


def test_resolved_image_is_bound_and_tests_have_no_host_mounts(tmp_path, monkeypatch):
    executor, commands, request = runtime(tmp_path, monkeypatch)
    bound = bind_request(request, executor)
    assert bound['execution_environment']['image_digest'] == IMAGE and bound['request_sha256']
    result = executor(bound)
    created = next(command for command in commands if command[0] == 'create')
    assert created[created.index('--network') + 1] == 'none'
    assert all(flag in created for flag in ('--memory', '--memory-swap', '--cpus', '--pids-limit', '--cap-drop', '--init'))
    assert not {'--mount', '--volume', '--privileged', '-v'} & set(created)
    assert IMAGE in created and 'mutable:tag' not in created
    assert commands[-1][:2] == ['rm', '--force']
    assert result['image_digest'] == IMAGE and result['tests']['test-issue'] == 'pass'


def test_timeout_always_force_removes_container(tmp_path, monkeypatch):
    executor, commands, request = runtime(tmp_path, monkeypatch, fail_start=True)
    with pytest.raises(ValueError, match='timed out'):
        executor(bind_request(request, executor))
    assert commands[-1][:2] == ['rm', '--force']


def test_runtime_preparation_cannot_substitute_semantic_inputs():
    class ChangedRequest:
        def prepare_request(self, request):
            return {**request, 'patch': 'different patch'}

    with pytest.raises(ValueError, match='semantic inputs'):
        bind_request({'patch': 'original patch', 'limits': deepcopy(LIMITS)}, ChangedRequest())
