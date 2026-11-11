"""Execute fresh baseline/gold attempts and archive content-bound evidence."""

import re
import tempfile
import uuid
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.contracts.packages import load_package

from ._common import encode, sha, write

LIMITS = {'wall_time_seconds': 1800, 'memory_bytes': 8 * 1024**3, 'cpus': 2, 'pids': 256}


def request_for(base, reference, stage, output, *, patch=None):
    """Compose the content-bound request for one fresh evaluation stage."""
    request = _request_data(base, reference, stage)
    if patch is not None:
        request['patch'] = patch
    # The attempt nonce and output location are not semantic execution inputs.
    request['request_sha256'] = sha(encode({k: value for k, value in request.items() if k != 'run_id'}))
    request['output_dir'] = str(output)
    return request


def bind_request(request, executor):
    """Bind actual runtime configuration before handing a request to the executor."""
    if hasattr(executor, 'prepare_request'):
        request = _prepared_request(request, executor)
    request['request_sha256'] = sha(encode({key: value for key, value in request.items()
                                          if key not in {'run_id', 'output_dir', 'request_sha256'}}))
    return request


def check_response(response, request, *, check_tests=True):
    """Verify executor identity, complete judgments and immutable evidence."""
    v.mapping(response, 'executor.response')
    for key in ('instance_id', 'run_id', 'request_sha256'):
        v.require(response.get(key) == request[key], key, 'executor response binding differs')
    v.require(response.get('status') == 'completed', 'executor.status', str(response.get('status')))
    v.require(type(response.get('image_digest')) is str and re.fullmatch(r'sha256:[a-f0-9]{64}', response['image_digest']),
              'image_digest', 'actual immutable image digest required')
    _test_response(response, request, check_tests)
    artifacts = _artifact_response(response, request)
    return {'stage': request['stage'], 'instance_id': request['instance_id'], 'run_id': request['run_id'],
            'request_sha256': request['request_sha256'], 'image_digest': response['image_digest'],
            'artifacts': artifacts}


def validate_swebench_references(package, *, executor=None) -> dict:
    """Archive a separate reference report without modifying the imported package."""
    root = Path(package).resolve()
    loaded = load_package(root)
    manifest = v.read_data(root / 'swebench-import.json')
    if executor is None:
        from .runtime import ContainerExecutor
        executor = ContainerExecutor(manifest['harness_revision'])
    archive = _archive(root)
    results = _scenarios(root, loaded, archive, executor)
    return _report(root, loaded, manifest, results, archive)


def _request_data(base, reference, stage):
    """Describe one semantic baseline or patched execution request."""
    source = reference['source']
    request = {**source, 'stage': stage,
               'patch': (base / reference['gold_patch']).read_text(encoding='utf-8') if stage == 'gold' else '',
               'test_patch': (base / reference['test_patch']).read_text(encoding='utf-8'),
               'FAIL_TO_PASS': reference['FAIL_TO_PASS'], 'PASS_TO_PASS': reference['PASS_TO_PASS'],
               'harness_revision': reference['harness_revision'], 'network': False,
               'limits': dict(LIMITS), 'run_id': uuid.uuid4().hex,
               'record': v.read_data(base / reference['raw_record'])['record']}
    return request


def _prepared_request(request, executor):
    """Accept runtime metadata only when inputs and execution limits remain bound."""
    original = v.snapshot(request)
    request = v.mapping(executor.prepare_request(v.snapshot(request)), 'executor.request')
    v.require(all(request.get(key) == value for key, value in original.items() if key != 'limits'),
              'executor.request', 'runtime preparation changed semantic inputs')
    limits = v.mapping(request.get('limits'), 'executor.limits')
    v.require(set(limits) == set(original['limits']), 'executor.limits', 'resource limits must be complete')
    for key, value in limits.items():
        v.number(value, 'executor.limits.' + key, positive=True, integer=True)
        v.require(value <= original['limits'][key], 'executor.limits.' + key, 'runtime cannot enlarge execution limits')
    return request


def _test_response(response, request, check_tests):
    """Reject incomplete or invalid test outcomes and verify expected judgments."""
    tests = v.mapping(response.get('tests'), 'tests')
    v.require(all(tests.get(name) in {'pass', 'fail'} for name in request['FAIL_TO_PASS'] + request['PASS_TO_PASS']),
              'tests', 'missing, skipped or unknown test outcomes')
    v.require(all(value in {'pass', 'fail'} for value in tests.values()), 'tests', 'test execution error')
    expected = {name: ('fail' if request['stage'] == 'base' and name in request['FAIL_TO_PASS'] else 'pass')
                for name in request['FAIL_TO_PASS'] + request['PASS_TO_PASS']}
    v.require(not check_tests or all(tests.get(name) == outcome for name, outcome in expected.items()), 'tests', 'unexpected test outcomes')


def _artifact_response(response, request):
    """Verify the executed image and every declared artifact."""
    artifacts = response.get('artifacts')
    v.require(type(artifacts) is list and bool(artifacts), 'artifacts', 'execution evidence required')
    if 'execution_environment' in request:
        v.require(response['image_digest'] == request['execution_environment']['image_digest'], 'image_digest', 'runtime image differs from bound request')
    seen = set()
    for item in artifacts:
        v.mapping(item, 'artifact')
        path = v.contained(Path(request['output_dir']), item.get('path'), 'artifact.path')
        v.require(item['path'] not in seen, 'artifacts', 'duplicate artifact')
        seen.add(item['path'])
        v.require(sha(path.read_bytes()) == item.get('sha256'), 'artifact.sha256', 'evidence integrity mismatch')
    return artifacts


def _archive(root):
    """Create a persistent report directory outside the source package."""
    archive_root = root.parent / (root.name + '.reference-reports')
    v.require(not archive_root.resolve().is_relative_to(root), 'reference_report', 'evidence must stay outside the package')
    archive_root.mkdir(parents=True, exist_ok=True)
    archive = Path(tempfile.mkdtemp(prefix='attempt-', dir=archive_root))
    return archive


def _stages(base, reference, archive, scenario, row, executor):
    """Record both reference attempts without granting credit for executor errors."""
    for stage in ('base', 'gold'):
        output = archive / scenario['id'] / stage
        output.mkdir(parents=True)
        request = request_for(base, reference, stage, output)
        write(output / 'request.json', request)
        try:
            _attempt(request, executor, output, archive, row)
        except Exception as error:  # noqa: BLE001 -- archive failures at the external executor boundary
            row.update(reason=str(error), error_class=type(error).__name__)
            write(output / 'error.json', {'reason': str(error), 'error_class': type(error).__name__})


def _attempt(request, executor, output, archive, row):
    """Execute and archive one content-bound reference attempt."""
    request = bind_request(request, executor)
    write(output / 'request.json', request)
    response = executor(v.snapshot(request))
    write(output / 'response.json', response)
    evidence = check_response(response, request)
    evidence['output_dir'] = output.relative_to(archive).as_posix()
    row['evidence'].append(evidence)


def _scenarios(root, loaded, archive, executor):
    """Validate the external references of all imported scenarios."""
    results = []
    for scenario in loaded['scenarios']:
        if scenario['evaluator']['kind'] != 'external.swebench_v1':
            continue
        row = _scenario_reference(root, scenario, archive, executor)
        results.append(row)
    return results


def _scenario_reference(root, scenario, archive, executor):
    """Compose the two-stage validation result for one scenario."""
    base = (root / scenario['manifest']).parent
    reference = v.read_data(base / scenario['evaluator']['reference'])
    row = {'scenario_id': scenario['qualified_id'], 'instance_id': scenario['id'], 'reference_passed': False,
           'validation_status': 'unvalidated', 'human_reviews': [], 'evidence': []}
    _stages(base, reference, archive, scenario, row, executor)
    if len(row['evidence']) == 2 and 'reason' not in row:
        row.update(reference_passed=True, validation_status='author_checked')
    return row


def _report(root, loaded, manifest, results, archive):
    """Archive the complete reference report and its package binding."""
    v.require(bool(results), 'package', 'no SWE-bench scenarios')
    from qb_cubie.benchmarks.planning._planning import _identity
    report = {'schema_version': 1, 'valid': all(row['reference_passed'] for row in results),
              'package': _identity(root, loaded), 'plan_sha256': manifest['plan_sha256'],
              'harness_revision': manifest['harness_revision'], 'scenarios': results}
    write(archive / 'report.json', report)
    return {**report, 'archive': str(archive), 'report': str(archive / 'report.json')}
