"""Execute bounded Docker tests with a commit-pinned official harness."""

import importlib.metadata
import json
import re
import subprocess
from importlib import import_module
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v

from ._common import docker, encode, sha


def harness_revision():
    """Require installation provenance, rather than trusting a version or tag."""
    try:
        distribution = importlib.metadata.distribution('swebench')
        direct = json.loads(distribution.read_text('direct_url.json') or '{}')
    except (importlib.metadata.PackageNotFoundError, ValueError) as error:
        raise ValueError('executor runtime: install the official swebench harness at the pinned Git commit') from error
    revision = direct.get('vcs_info', {}).get('commit_id')
    v.require(bool(revision), 'executor.runtime', 'harness requires a VCS installation with full commit provenance')
    return revision


class ContainerExecutor:
    """Fresh no-network test containers with finite resource and time limits."""

    def __init__(self, revision):
        """Initialize the bounded container execution configuration."""
        self.docker = docker('container.runtime', 'Docker executor unavailable; no host fallback')
        v.require(harness_revision() == revision, 'harness_revision', 'installed executor harness commit differs')
        self.revision = revision
        self.environments = {}
        info = json.loads(self.command(['info', '--format', '{{json .}}'], timeout=30).stdout)
        v.require(info.get('OSType') == 'linux' and all(info.get(key) is True for key in ('MemoryLimit', 'SwapLimit', 'PidsLimit'))
                  and (info.get('CpuCfsQuota') is True or info.get('CPUCfsQuota') is True),
                  'container.isolation', 'runtime must support Linux memory, swap, PID and CPU limits')

    def command(self, args, *, timeout=60, check=True):
        """Execute one bounded Docker operation with sanitized diagnostics."""
        try:
            result = subprocess.run([self.docker, *args], capture_output=True, timeout=timeout, check=False)
        except (OSError, subprocess.SubprocessError) as error:
            raise ValueError('container executor: command failed or timed out') from error
        v.require(not check or result.returncode == 0, 'container.executor', 'Docker operation failed')
        return result

    def spec(self, request):
        """Resolve a supported harness specification and its image reference."""
        try:
            spec = _spec_factory(request['record'])(request['record'])
            image = v.text(getattr(spec, 'image', None) or getattr(spec, 'instance_image_key', None), 'harness.image')
            v.require(not image.startswith('-'), 'harness.image', 'invalid image reference')
            return spec, image
        except (ImportError, KeyError, TypeError, AttributeError) as error:
            raise ValueError('harness.compatibility: dataset metadata unsupported by pinned harness') from error

    def prepare_request(self, request):
        """Bind the resolved image and harness script before execution."""
        if request['instance_id'] in self.environments:
            request['execution_environment'] = dict(self.environments[request['instance_id']])
            return request
        spec, image = self.spec(request)
        metadata = json.loads(self.command(['image', 'inspect', image]).stdout)[0]
        request['execution_environment'] = {'image_digest': metadata['Id'], 'eval_script_sha256': sha(spec.eval_script.encode('utf-8')),
                                            'runtime': 'docker', 'network': 'none'}
        self.environments[request['instance_id']] = dict(request['execution_environment'])
        return request

    def __call__(self, request):
        """Execute one fresh container and always terminate its process namespace."""
        v.require(request['harness_revision'] == self.revision and request['network'] is False,
                  'executor.request', 'different harness or network policy')
        spec, _image = self.spec(request)
        metadata = _bound_image(self, request, spec)
        files = _runtime_files(request, spec, metadata)
        name = v.identifier('cubie-swebench-' + request['run_id'], 'container.name')
        try:
            return _run_container(self, request, spec, metadata['Id'], name, files)
        finally:
            _remove(self, name)


def _spec_factory(record):
    """Select a harness adapter compatible with the source metadata."""
    if all(record.get(key) for key in ('image', 'eval_script', 'log_parser', 'eval_type')):
        return import_module('swebench.harness.utils').make_test_spec
    else:
        v.require(not any(record.get(key) for key in ('image', 'eval_script', 'log_parser', 'eval_type')),
                  'harness.compatibility', 'partial execution metadata; cannot interpret this dataset revision')
        return import_module('swebench.harness.test_spec.test_spec').make_test_spec


def _container_args(request, digest, name):
    """Declare the bounded no-network test container."""
    limits = request['limits']
    args = ['create', '--name', name, '--network', 'none', '--memory', str(limits['memory_bytes']),
            '--memory-swap', str(limits['memory_bytes']), '--cpus', str(limits['cpus']),
            '--pids-limit', str(limits['pids']), '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--init', '--entrypoint', '/bin/bash', digest, '-c',
            ('cd /testbed && git reset --hard "$1" && '
            'if [ -s /tmp/cubie.patch ]; then git apply --check /tmp/cubie.patch && git apply /tmp/cubie.patch; fi && '
            '/bin/bash /tmp/cubie-eval.sh'), 'cubie', request['base_commit']]
    return args


def _test_results(spec, log):
    """Parse complete harness output while rejecting infrastructure errors."""
    get_logs_eval = import_module('swebench.harness.grading').get_logs_eval
    tests, found = get_logs_eval(spec, str(log))
    v.require(found, 'executor.tests', 'patch/collection failure or missing test output')
    content = log.read_text(encoding='utf-8', errors='replace')
    v.require(not re.search(r'ImportError|ModuleNotFoundError|INTERNALERROR|ERROR collecting|errors during collection', content),
              'executor.tests', 'import or collection failure')
    statuses = {'PASSED': 'pass', 'FAILED': 'fail'}
    tests = {key: statuses.get(value, 'error') for key, value in tests.items()}
    return tests


def _response(request, digest, tests, output, script, patch, log):
    """Bind the actual image and artifact bytes to the completed attempt."""
    artifacts = [{'path': path.name, 'sha256': sha(path.read_bytes())}
                 for path in (script, patch, log, output / 'image.json')]
    return {**{key: request[key] for key in ('instance_id', 'run_id', 'request_sha256')},
            'status': 'completed', 'tests': tests, 'image_digest': digest, 'artifacts': artifacts}


def _observation(executor, output, name, run):
    """Archive container output and reject failed execution."""
    log = output / 'test-output.txt'
    log.write_bytes(run.stdout + b'\n' + run.stderr)
    state = json.loads(executor.command(['inspect', name]).stdout)[0]
    v.require(not state['State'].get('OOMKilled') and run.returncode == 0,
              'executor.status', 'patch, setup, resource or test command failure')
    return log


def _bound_image(executor, request, spec):
    """Verify the immutable image and evaluation script binding."""
    v.require('execution_environment' in request, 'executor.request', 'runtime inputs must be bound before execution')
    inspected = executor.command(['image', 'inspect', request['execution_environment']['image_digest']])
    metadata = json.loads(inspected.stdout)[0]
    digest = metadata['Id']
    v.require(sha(spec.eval_script.encode('utf-8')) == request['execution_environment']['eval_script_sha256'], 'executor.request', 'evaluation script differs')
    v.require(re.fullmatch(r'sha256:[a-f0-9]{64}', digest), 'image_digest', 'invalid actual image identity')
    return metadata


def _runtime_files(request, spec, metadata):
    """Stage only explicit scripts, patches and image provenance."""
    output = Path(request['output_dir'])
    output.mkdir(parents=True, exist_ok=True)
    (output / 'image.json').write_bytes(encode({'Id': metadata['Id'], 'RepoDigests': metadata.get('RepoDigests', [])}))
    script = output / 'eval.sh'
    script.write_text(spec.eval_script, encoding='utf-8')
    patch = output / 'submission.patch'
    patch.write_text(request['patch'], encoding='utf-8')
    return (output, script, patch)


def _run_container(executor, request, spec, digest, name, files):
    """Run staged inputs and return independently parsed test evidence."""
    output, script, patch = files
    executor.command(_container_args(request, digest, name))
    executor.command(['cp', str(script), name + ':/tmp/cubie-eval.sh'])
    executor.command(['cp', str(patch), name + ':/tmp/cubie.patch'])
    run = executor.command(['start', '--attach', name], timeout=request['limits']['wall_time_seconds'], check=False)
    log = _observation(executor, output, name, run)
    tests = _test_results(spec, log)
    return _response(request, digest, tests, output, script, patch, log)


def _remove(executor, name):
    """Confirm forced removal of the complete container process namespace."""
    removed = executor.command(['rm', '--force', name], timeout=30, check=False)
    v.require(removed.returncode == 0 or b'No such container' in removed.stderr, 'container.executor', 'could not confirm termination')
