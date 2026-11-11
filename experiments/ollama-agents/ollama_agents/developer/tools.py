"""Observe pytest in a temporary copy without depending on the Cubie package."""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from ..errors import AdapterError
from ..reviewer.tools import _process


def run_tests(sources, timeout):
    """Keep caches, JUnit and test side effects outside the submitted tree."""
    with tempfile.TemporaryDirectory(prefix='cubie-developer-tests-') as temporary:
        root = Path(temporary) / 'project'
        root.mkdir()
        policy = sources.policy()
        for name in sorted(policy.readable):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(policy.read_file(name))
        return observe(root, Path(temporary), timeout)


def observe(root, archive, timeout):
    """Use isolated Python, a fixed pytest command and real JUnit failure causes."""
    config, junit = root / 'pytest.ini', archive / 'pytest.xml'
    config.write_text('[pytest]\npythonpath = .\n', encoding='utf-8')
    environment = {key: value for key, value in os.environ.items()
                   if key not in {'PYTHONPATH', 'PYTHONHOME', 'PYTEST_ADDOPTS', 'PYTEST_PLUGINS'}}
    environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-I', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               '--import-mode=importlib', '--confcutdir=' + str(root), '-c', str(config),
               '--junitxml=' + str(junit), str(root / 'tests')]
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        result = _process(command, root, environment, timeout, out, err)
    try:
        cases = [{'name': case.attrib['name'], 'failures': [
            {'kind': child.tag, 'message': child.get('message', ''), 'text': child.text or ''}
            for child in case if child.tag in {'failure', 'error', 'skipped'}]}
                 for case in ET.parse(junit).iter('testcase')]
    except (OSError, ET.ParseError, KeyError) as error:
        raise AdapterError('infrastructure_error', f'Missing or invalid pytest JUnit report: {error}') from error
    failures = [failure for case in cases for failure in case['failures']]
    outcome = ('passed' if result['exit_code'] == 0 and cases else
               'import_error' if result['exit_code'] == 2 else
               'assertion_failure' if result['exit_code'] == 1 and failures and all(_business(f) for f in failures)
               else 'test_error')
    return {**result, 'test_outcome': outcome, 'cases': cases}


def _business(failure):
    """Credit assertions and missing expected exceptions, never setup errors."""
    terminal = failure['text'].rstrip().rsplit('\n', 1)[-1]
    return failure['kind'] == 'failure' and (terminal.endswith(': AssertionError') or (
        terminal.endswith(': Failed') and failure['message'].startswith('Failed: DID NOT RAISE ')))
