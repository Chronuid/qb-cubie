"""Run installed pytest/Cubie in a temporary copy using the runner classifier."""

import tempfile
import time
from pathlib import Path

from qb_cubie.benchmarks.execution import _pytest  # type: ignore[import-untyped]
from qb_cubie.benchmarks.execution._process import ExecutionError  # type: ignore[import-untyped]

from ..errors import AdapterError
from ..reviewer.tools import bounded


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
    context = {'deadline': time.monotonic() + timeout, 'tool_calls': 0,
               'run': {'budgets': {'tool_calls': 1}}}
    try:
        result = _pytest.observe(context, root, root / 'tests', archive / 'pytest.json')
    except ExecutionError as error:
        raise AdapterError(error.status, str(error)) from error
    return {'exit_code': result['returncode'], 'stdout': bounded(result['stdout']),
            'stderr': bounded(result['stderr']), 'test_outcome': result['test_outcome'],
            'cases': result['cases']}
