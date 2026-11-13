"""Evaluate complete agent patches in the external evaluator workspace."""

import subprocess
import time
from pathlib import Path

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.reporting._files import write_json

from ._common import sha
from .validation import bind_request, check_response, request_for


def patch_paths(content):
    """Ask Git to parse its own patch format without applying or executing it."""
    result = _patch_stats(content)
    chunks = iter(result.stdout.split(b'\0'))
    paths = []
    for chunk in chunks:
        if not chunk:
            continue
        paths.extend(_chunk_paths(chunk, chunks))
    return paths


def protect_tests(patch, test_patch):
    """Reject changes to private tests and collection configuration."""
    protected = set(patch_paths(test_patch))
    for name in patch_paths(patch):
        path = Path(name)
        v.require(name not in protected and not any(part in {'tests', 'test', '.git'} for part in path.parts)
                  and not path.name.startswith('test_') and not path.name.endswith('_test.py')
                  and path.name not in {'conftest.py', 'pytest.ini', 'tox.ini', 'setup.cfg', 'pyproject.toml'},
                  'submission.patch', 'test and collection configuration changes are not permitted')


def evaluate_patch(context, artifact, *, executor=None):
    """Keep functional judgments distinct from execution/infrastructure failures."""
    from .runtime import ContainerExecutor
    reference = context['reference']
    patch = artifact.read_text(encoding='utf-8')
    protect_tests(patch, (context['base'] / reference['test_patch']).read_text(encoding='utf-8'))
    output = context['directory'] / 'evaluation'
    output.mkdir(parents=True)
    executor = executor or ContainerExecutor(reference['harness_revision'])
    request = _submission_request(context, reference, output, patch, executor)
    response = _execute(output, request, executor)
    return _evaluation(context, output, patch, request, response)


def _patch_stats(content):
    """Parse a Git patch without applying it."""
    try:
        result = subprocess.run(['git', 'apply', '--numstat', '-z'], input=content.encode('utf-8'),
                                capture_output=True, check=False, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError('submission.patch: cannot parse Git patch') from error
    v.require(result.returncode == 0, 'submission.patch', 'invalid unified patch')
    return result


def _chunk_paths(chunk, chunks):
    """Validate each path declared by one Git patch statistic."""
    paths = []
    fields = chunk.split(b'\t', 2)
    v.require(len(fields) == 3, 'submission.patch', 'invalid Git path record')
    names = [fields[2]] if fields[2] else [next(chunks), next(chunks)]
    for name in names:
        path = name.decode('utf-8')
        v.relative(path, 'submission.patch.path')
        paths.append(path)
    return paths


def _submission_request(context, reference, output, patch, executor):
    """Bind the submitted patch to the admitted execution environment."""
    request = request_for(context['base'], reference, 'submission', output, patch=patch)
    request['limits']['wall_time_seconds'] = max(1, min(request['limits']['wall_time_seconds'], int(context['deadline'] - time.monotonic())))
    request = bind_request(request, executor)
    if 'execution_environment' in request:
        v.require(request['execution_environment']['image_digest'] == context['run']['reference_image_digest'],
                  'reference_report', 'evaluation image differs from admitted reference')
    return request


def _execute(output, request, executor):
    """Archive and verify the external patch evaluation."""
    write_json(output / 'request.json', request)
    response = executor(v.snapshot(request))
    write_json(output / 'response.json', response)
    check_response(response, request, check_tests=False)
    return response


def _judgments(response, request):
    """Judge repair and regression coverage separately."""
    tests = response['tests']
    judgments = {'repair': 'pass' if all(tests[name] == 'pass' for name in request['FAIL_TO_PASS']) else 'fail',
                 'regression': 'pass' if all(tests[name] == 'pass' for name in request['PASS_TO_PASS']) else 'fail'}
    return judgments


def _evaluation(context, output, patch, request, response):
    """Describe the functional outcome without TDD process credit."""
    judgments = _judgments(response, request)
    result = {'status': 'completed', 'evaluation_status': 'complete', 'criterion_results': judgments,
              'metrics': [], 'evidence': [(output / name).relative_to(context['root']).as_posix()
                                         for name in ('request.json', 'response.json')],
              'quality_passed': all(value == 'pass' for value in judgments.values()),
              'process_profile': 'issue_resolution', 'process_passed': None,
              'submission_sha256': sha(patch.encode('utf-8')), 'image_digest': response['image_digest']}
    write_json(output / 'evaluation.json', result)
    return result
