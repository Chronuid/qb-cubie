"""Public pytest instrumentation for case execution and explicit EBT checks."""

PROBE = r'''
import ast
import inspect
import json
from pathlib import Path
import pytest
usage = {'available': True, 'collected': 0, 'ebt_executed': 0, 'ebt_evaluated': 0,
         'ebt_passed': 0, 'ebt_evaluation_checked': 0, 'case_results': {}}
active = None
results = {}
checked = set()
source_checks = {}
keys = ('ebt_executed', 'ebt_evaluated', 'ebt_passed', 'ebt_evaluation_checked')
def increment(key):
    usage[key] += 1
    if active is not None:
        usage['case_results'][active][key] += 1
def check_line(filename, line):
    if filename not in source_checks:
        lines = set()
        try:
            tree = ast.parse(Path(filename).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assert):
                    continue
                test = node.test
                if (isinstance(test, ast.Compare) and len(test.ops) == 1
                        and isinstance(test.ops[0], ast.Is)
                        and isinstance(test.left, ast.Attribute) and test.left.attr == 'evaluation'
                        and isinstance(test.comparators[0], ast.Constant) and test.comparators[0].value is True):
                    lines.update(range(node.lineno, node.end_lineno + 1))
        except (OSError, ValueError, SyntaxError):
            pass
        source_checks[filename] = lines
    return line in source_checks[filename]
def pytest_configure(config):
    try:
        from qb_cubie import EBT
        from qb_cubie.protocols import RunTrace
    except ImportError:
        return
    original_run = EBT.run
    original_get = RunTrace.__getattribute__
    def get(self, name):
        if name == 'evaluation' and id(self) in results and active is not None:
            caller = inspect.currentframe().f_back
            marker = (active, id(self))
            if marker not in checked and check_line(caller.f_code.co_filename, caller.f_lineno):
                checked.add(marker)
                increment('ebt_evaluation_checked')
        return original_get(self, name)
    RunTrace.__getattribute__ = get
    def run(self, *args, **kwargs):
        increment('ebt_executed')
        try:
            trace = original_run(self, *args, **kwargs)
        finally:
            trace = self.run_trace
            if trace is not None and trace.evaluation is not None:
                increment('ebt_evaluated')
                if trace.evaluation is True:
                    increment('ebt_passed')
        if trace is not None:
            results[id(trace)] = trace
        return trace
    EBT.run = run
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    global active
    active = item.nodeid
    usage['case_results'][active] = {'executed': False, 'outcome': 'missing', **dict.fromkeys(keys, 0)}
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    report = (yield).get_result()
    record = usage['case_results'].setdefault(item.nodeid, {'executed': False, 'outcome': 'missing', **dict.fromkeys(keys, 0)})
    if report.when == 'call':
        record['executed'] = True
        record['outcome'] = ('skip' if report.skipped else 'assertion_failure'
                             if report.failed and 'AssertionError' in report.longreprtext else
                             'test_failure' if report.failed else 'pass')
        if hasattr(report, 'wasxfail'):
            record['outcome'] = 'xfail' if report.skipped else 'xpass'
    elif report.failed:
        record['outcome'] = 'invalid_test_run'
def pytest_collection_finish(session):
    usage['collected'] = len(session.items)
    usage['test_ids'] = [item.nodeid for item in session.items]
def pytest_collectreport(report):
    if report.failed:
        usage.setdefault('collection_error_ids', []).append(report.nodeid)
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    report.user_properties.append(('study_nodeid', report.nodeid))
def pytest_sessionfinish(session, exitstatus):
    Path(EVIDENCE).write_text(json.dumps(usage))
'''
