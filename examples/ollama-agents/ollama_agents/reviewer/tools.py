"""Read-only reviewer tools and bounded pytest execution on copied originals."""

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

from ..errors import AdapterError, infrastructure

MAX_OUTPUT = 32768


def execute(action, sources, timeout):
    """Execute only the validated fixed reviewer action set."""
    name = action['action']
    if name == 'list_files':
        return sorted(sources.hashes)
    if name == 'read_file':
        return sources.policy.read_file(action['path']).decode('utf-8')
    if name == 'search_text':
        return search(sources, action['query'])
    return run_tests(sources, timeout)


def search(sources, query):
    """Return literal text matches with source names and one-based line numbers."""
    return [{'path': name, 'line': index, 'text': line}
            for name in sorted(sources.contents)
            for index, line in enumerate(sources.contents[name].splitlines(), 1) if query in line]


def bounded(text):
    """Explicitly mark omitted tool output without concealing truncation."""
    return text if len(text) <= MAX_OUTPUT else text[:MAX_OUTPUT] + '\n[output truncated]'


def run_tests(sources, timeout):
    """Populate a fresh project copy without importing or caching in the originals."""
    with tempfile.TemporaryDirectory(prefix='cubie-review-tests-') as temporary:
        root = Path(temporary)
        for name in sources.hashes:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(sources.policy.read_file(name))
        return _pytest(root, timeout)


def _pytest(root, timeout):
    """Use a fixed interpreter command and spool output outside the reviewed tree."""
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
    for key in ('PYTHONPATH', 'PYTHONHOME', 'PYTEST_ADDOPTS', 'PYTEST_PLUGINS'):
        environment.pop(key, None)
    command = [sys.executable, '-m', 'pytest', '-q', '-s', '-p', 'no:cacheprovider', 'tests']
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        return _process(command, root, environment, timeout, out, err)


def _process(command, root, environment, timeout, out, err):
    """Terminate and reap the test process group if its deadline is reached."""
    try:
        process = subprocess.Popen(command, cwd=root, env=environment, stdout=out, stderr=err,
                                   start_new_session=True)
        code = _wait(process, timeout)
    except OSError as error:
        raise infrastructure(f'Cannot execute visible tests: {error}') from error
    out.seek(0)
    err.seek(0)
    return {'exit_code': code, 'stdout': _output(out), 'stderr': _output(err)}


def _wait(process, timeout):
    """Apply the remaining episode time to the entire subprocess group."""
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        raise AdapterError('agent_timeout', 'Visible test execution timeout') from error


def _output(stream):
    """Read a bounded diagnostic prefix from a spooled process stream."""
    body = stream.read(MAX_OUTPUT + 1)
    text = body[:MAX_OUTPUT].decode('utf-8', errors='replace')
    return text + ('\n[output truncated]' if len(body) > MAX_OUTPUT else '')
