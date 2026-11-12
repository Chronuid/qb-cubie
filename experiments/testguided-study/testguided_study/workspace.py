"""Expose bounded file tools and real pytest observations inside a sandbox."""

import base64
import json
import re
import shlex
import uuid
import xml.etree.ElementTree as ET

SCRIPT = r'''
import difflib, fnmatch, hashlib, json, pathlib, sys
root = pathlib.Path('/workspace')
arg = json.loads(sys.argv[1])
op = arg['action']
def target(name):
    p = pathlib.PurePosixPath(name)
    if not name or p.is_absolute() or any(x in p.parts for x in ('..', '.git')):
        raise ValueError('Only workspace paths outside .git are accessible')
    path = root / p
    if not path.resolve().is_relative_to(root) or any(x.is_symlink() for x in (path, *path.parents)):
        raise ValueError('Symlinks and paths outside workspace are inaccessible')
    return path
def files():
    import os
    result = []
    for folder, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in ('.git', '__pycache__', '.pytest_cache')
                         and not (pathlib.Path(folder) / d).is_symlink())
        result.extend(pathlib.Path(folder) / n for n in sorted(names)
                      if not (pathlib.Path(folder) / n).is_symlink())
    return result
try:
    if op == 'overview':
        names = [str(p.relative_to(root)) for p in files()]
        result = {'roots': sorted({p.split('/')[0] for p in names})[:60],
                  'configuration': [p for p in names if '/' not in p and p.endswith(('.toml', '.ini', '.cfg'))][:20]}
    elif op == 'snapshot':
        groups = {'tests': {}, 'production': {}}
        for p in files():
            name = str(p.relative_to(root))
            explicit_test = any(p == root / t or p.is_relative_to(root / t) for t in arg.get('test_paths', []))
            is_test = (bool({'tests', 'test'} & set(p.relative_to(root).parts)) or
                       p.name.startswith('test_') or p.name == 'conftest.py' or explicit_test)
            if p.suffix != '.py' and not is_test:
                continue
            group = 'tests' if is_test else 'production'
            groups[group][name] = hashlib.sha256(p.read_bytes()).hexdigest()
        result = {k: hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest() for k, v in groups.items()}
    elif op == 'find_paths':
        names = [str(p.relative_to(root)) for p in files()
                 if fnmatch.fnmatch(str(p.relative_to(root)), arg['pattern'])]
        offset = arg['start']
        result = {'files': names[offset:offset+80], 'start': offset,
                  'next_start': offset+80 if len(names) > offset+80 else None}
    elif op == 'list_files':
        names = [str(p.relative_to(root)) for p in files()]
        result = {'files': names[:1500], 'omitted': max(0, len(names)-1500)}
    elif op == 'read_file':
        p = target(arg['path'])
        if p.stat().st_size > 2_000_000:
            raise ValueError('File exceeds the readable size limit')
        lines = p.read_text().splitlines()
        start = arg['start'] - 1
        result = {'path': arg['path'], 'start': start+1, 'total_lines': len(lines),
                  'text': '\n'.join(lines[start:start+160]),
                  'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    elif op in ('search_text', 'search_files', 'search_content'):
        scope = target(arg['path']) if op != 'search_text' else root
        if not scope.exists():
            raise ValueError('Search path does not exist')
        offset = arg['start'] if op != 'search_text' else 0
        hits, seen = [], 0
        for p in files():
            if p != scope and not p.is_relative_to(scope):
                continue
            if p.stat().st_size > 500_000:
                continue
            try:
                for i, line in enumerate(p.read_text().splitlines(), 1):
                    if arg['query'] in line:
                        seen += 1
                        if seen <= offset:
                            continue
                        hits.append({'path': str(p.relative_to(root)), 'line': i, 'text': line[:500]})
                        if len(hits) > 80:
                            break
            except UnicodeError:
                continue
            if len(hits) > 80:
                break
        result = {'hits': hits[:80], 'start': offset, 'limit': 80,
                  'next_start': offset + 80 if len(hits) > 80 else None}
    elif op in ('replace_text', 'replace_region'):
        p = target(arg['path'])
        if p.stat().st_size > 2_000_000:
            raise ValueError('File exceeds the editable size limit')
        original = p.read_bytes().decode('utf-8')
        current_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        if op == 'replace_region':
            if arg.get('expected_sha256') != current_hash:
                raise ValueError('Stale region: reread before editing')
            lines = original.splitlines(keepends=True)
            lines[arg['start']-1:arg['end']] = [arg['new_text']]
            data = ''.join(lines).encode('utf-8')
            if p.suffix == '.py':
                compile(data.decode('utf-8'), arg['path'], 'exec')
            import os, tempfile
            with tempfile.NamedTemporaryFile(dir=p.parent, delete=False) as stream:
                pending = pathlib.Path(stream.name)
                stream.write(data)
            try:
                pending.chmod(p.stat().st_mode)
                pending.replace(p)
            finally:
                pending.unlink(missing_ok=True)
            print(json.dumps({'status': 'completed', 'written': arg['path'], 'sha256': hashlib.sha256(data).hexdigest()}))
            sys.exit(0)
        matches = original.count(arg['old']) if arg['old'] else 0
        conflict = ('hash_mismatch' if arg.get('expected_sha256', current_hash) != current_hash else
                    'anchor_missing' if matches == 0 else 'anchor_ambiguous' if matches != 1 else None)
        if conflict:
            repairs = {
                'hash_mismatch': 'Read the current file and copy its exact sha256 into expected_sha256.',
                'anchor_missing': 'Read the relevant lines and use a small old anchor copied exactly from current source.',
                'anchor_ambiguous': 'Read current source and extend old with enough surrounding text to match exactly once.',
            }
            print(json.dumps({'status': 'tool_error', 'code': 'edit_conflict',
                              'conflict_reason': conflict, 'sha256': current_hash, 'match_count': matches,
                              'excerpt': original[:1500], 'repair': repairs[conflict]}))
            sys.exit(1)
        data = original.replace(arg['old'], arg['new'], 1).encode('utf-8')
        if len(data) > 2_000_000:
            raise ValueError('Replacement exceeds the editable size limit')
        if p.suffix == '.py':
            compile(data.decode('utf-8'), arg['path'], 'exec')
        p.write_bytes(data)
        result = {'written': arg['path'], 'sha256': hashlib.sha256(data).hexdigest()}
    elif op in ('write_file', 'delete_file', 'create_source_file', 'create_test_file', 'delete_source_file', 'delete_test_file'):
        p = target(arg['path'])
        if op.startswith('create_'):
            if p.exists():
                raise ValueError('Creation cannot overwrite a file')
            op = 'write_file'
        elif op.startswith('delete_'):
            op = 'delete_file'
        if op == 'write_file' and not p.exists() and (not p.name.strip() or not any(c.isalnum() for c in p.name)):
            raise ValueError('New filename must contain a letter or digit')
        if op == 'write_file' and p.suffix == '.py':
            compile(arg['content'], arg['path'], 'exec')
        if op == 'delete_file':
            p.unlink()
            result = {'deleted': arg['path']}
        else:
            data = arg['content'].encode('utf-8')
            if len(data) > 128_000:
                raise ValueError('Write exceeds 128000 bytes; use smaller modules')
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            result = {'written': arg['path'], 'sha256': hashlib.sha256(data).hexdigest()}
    else:
        raise ValueError('Unknown file action')
    print(json.dumps(result))
except (OSError, ValueError, SyntaxError, UnicodeError) as error:
    name = arg.get('path', '')
    suggestions = []
    if isinstance(error, FileNotFoundError):
        names = [str(p.relative_to(root)) for p in files()]
        suggestions = [n for n in names if pathlib.PurePosixPath(n).name == pathlib.PurePosixPath(name).name][:5]
        code = 'not_found'
    elif isinstance(error, SyntaxError):
        code = 'invalid_python'
    else:
        code = 'invalid_action'
    print(json.dumps({'status': 'tool_error', 'code': code, 'error': str(error)[:500],
                      'suggestions': suggestions, 'repair':
                      'Python syntax rejected before writing; fix the candidate syntax and retry a small edit.'
                      if isinstance(error, SyntaxError) else 'Inspect existing paths and current source before retrying.'}))
    sys.exit(1)

'''


def command(script, *arguments):
    encoded = base64.b64encode(script.encode()).decode("ascii")
    loader = "import base64; exec(base64.b64decode(" + repr(encoded) + "))"
    return "python3 -S -c " + shlex.quote(loader) + " " + " ".join(shlex.quote(arg) for arg in arguments)


def execute(manager, sandbox, action, timeout, limit):
    if action["action"] in {"run_tests", "collect_tests", "check_baseline"}:
        return run_tests(manager, sandbox, action["targets"], timeout, limit,
                         collect=action["action"] == "collect_tests", baseline=action["action"] == "check_baseline",
                         workspace=action.get('workspace'), team=action.get('team', False))
    result = manager.exec(sandbox, command(SCRIPT, json.dumps(action)), timeout=timeout)
    if result.exit_code:
        try:
            return bounded(json.loads(result.stdout), limit)
        except (ValueError, TypeError):
            return {"status": "tool_error", "code": "execution_error", "stderr": result.stderr[-min(limit, 1000):],
                    "timed_out": result.timed_out}
    return bounded(json.loads(result.stdout), limit)


def bounded(result, limit):
    """Keep search/file results structured, with continuation at entry boundaries."""
    result = {"status": "completed", **result}
    if len(json.dumps(result)) <= limit:
        return result
    result["truncated"] = True
    for key in ("hits", "files"):
        if key in result:
            original_count = len(result[key])
            while result[key] and len(json.dumps(result)) > limit:
                result[key].pop()
                result["next_start"] = result.get("start", 0) + len(result[key])
            if original_count and not result[key]:
                return {"status": "tool_error", "error": "output_chars cannot fit one entry; narrow the query"}
            return result
    if "text" in result:
        lines = result["text"].splitlines()
        while lines and len(json.dumps(result)) > limit:
            lines.pop()
            result["text"] = "\n".join(lines)
            result["next_start"] = result["start"] + len(lines)
        if not lines:
            return {"status": "tool_error", "error": "output_chars cannot fit one line"}
        return result
    return {"status": "tool_error", "error": "Result exceeds output_chars"}


def run_tests(manager, sandbox, targets, timeout, limit, *, collect=False, baseline=False, workspace=None, team=False):
    for target in targets:
        path = target.split("::", 1)[0]
        if not path or path.startswith(("/", "-")) or any(p in {"..", ".git"} for p in path.split("/")):
            return {"status": "tool_error", "error": "Use relative test paths or pytest node IDs"}
    report = f"/tmp/study-{uuid.uuid4().hex}.xml"
    prepared = workspace is not None
    if prepared and not re.fullmatch(r'/tmp/v6-baseline-[a-zA-Z0-9_-]+', workspace):
        return {'status': 'tool_error', 'error': 'Invalid prepared baseline workspace'}
    workspace = workspace or "/workspace"
    cleanup = None
    if baseline and not prepared:
        workspace = f"/tmp/study-baseline-{uuid.uuid4().hex}"
        setup = manager.exec(sandbox, command(BASELINE, workspace, json.dumps(targets)), timeout=timeout)
        if setup.exit_code:
            return {"status": "tool_error", "code": "baseline_setup", "error": setup.stderr[-1000:]}
        cleanup = workspace
    plugin_name = "study_probe_" + uuid.uuid4().hex
    plugin_path = f"/tmp/{plugin_name}.py"
    evidence = f"/tmp/{plugin_name}.json"
    install_script = INSTALL_PROBE
    if team:
        from .team_probe import PROBE as team_probe
        install_script = 'import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(' + repr(team_probe) + ".replace('EVIDENCE', repr(sys.argv[2])))"
    install = manager.exec(sandbox, command(install_script, plugin_path, evidence), timeout=10)
    if install.exit_code:
        return {"status": "tool_error", "code": "probe_setup", "error": install.stderr[-1000:]}
    plugins = ','.join(getattr(manager, 'study_plugins', ()))
    cmd = ("cd " + shlex.quote(workspace) + " && PYTHONPATH=/tmp PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1 "
           + 'PYTEST_PLUGINS=' + shlex.quote(plugins) + ' '
           "python3 -m pytest -p " + plugin_name + " --rootdir=" + shlex.quote(workspace) + " " + " ".join(shlex.quote(path) for path in targets)
           + f" --junitxml={report} -q" + (" --collect-only" if collect else ""))
    result = manager.exec(sandbox, cmd, timeout=timeout)
    xml = manager.exec(sandbox, "cat " + report, timeout=10)
    observed = classify(result.exit_code, xml.stdout, result.timed_out)
    probe = manager.exec(sandbox, "cat " + evidence, timeout=10)
    try:
        usage = json.loads(probe.stdout)
    except ValueError:
        usage = {"available": False}
    if cleanup:
        manager.exec(sandbox, command(REMOVE_TREE, cleanup), timeout=10)
    diagnostics = test_diagnostics(xml.stdout, usage.get('test_ids', []), usage.get('collection_error_ids', []))
    diagnostics['executed'] = sum(diagnostics['counts'].get(k, 0) for k in ('passed', 'failed'))
    if collect and result.exit_code == 0 and usage.get("collected", 0):
        observed = "collected"
        diagnostics['collected'] = usage['collected']
    if not result.timed_out:
        if result.exit_code == 4 and re.search(r'(file or directory not found|not found:)', result.stderr):
            diagnostics['category'] = 'target_not_found'
        elif result.exit_code == 5:
            diagnostics['category'] = 'no_tests_collected'
        if 'category' in diagnostics:
            diagnostics['targets'] = targets
            diagnostics['repair'] = ('Locate a relative test file or collected pytest node ID with find_paths; '
                                     'production modules and function names alone are not test targets.')
    return {"status": "completed", "observation": observed, "exit_code": result.exit_code,
            "timed_out": result.timed_out, "stdout": result.stdout[:limit], "stderr": result.stderr[:limit],
            "output_truncated": len(result.stdout) > limit or len(result.stderr) > limit,
            "junit_xml": xml.stdout, "diagnostics": diagnostics, "framework_usage": usage,
            "baseline": baseline, "collection_only": collect, 'case_results': usage.get('case_results', {})}


def classify(exit_code, xml, timed_out=False):
    if timed_out:
        return "timeout"
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return "invalid_test_run"
    cases = list(root.iter("testcase"))
    if not cases or list(root.iter("error")):
        return "invalid_test_run"
    failures = list(root.iter("failure"))
    if exit_code == 1 and failures:
        assertions = all(is_assertion(f) for f in failures)
        return "assertion_failure" if assertions else "test_failure"
    if exit_code == 0 and not failures and any(c.find("skipped") is None for c in cases):
        return "pass"
    return "invalid_test_run"


def is_assertion(failure):
    if failure.attrib.get("type", "").endswith("AssertionError"):
        return True
    # pytest's xunit2 reports omit type; the final traceback line carries it.
    lines = (failure.text or "").rstrip().splitlines()
    return bool(lines and re.search(r":\d+: AssertionError(?::.*)?$", lines[-1]))


def outcomes(xml, required):
    try:
        cases = list(ET.fromstring(xml).iter("testcase"))
    except ET.ParseError:
        cases = []
    result = {}
    for node in required:
        matches = [case for case in cases if node in identifiers(case) or
                   ("[" not in node and any(name.startswith(node + "[") for name in identifiers(case)))]
        states = ["error" if case.find("error") is not None else
                  "fail" if case.find("failure") is not None else
                  "skip" if case.find("skipped") is not None else "pass" for case in matches]
        result[node] = ("missing" if not states else "error" if "error" in states else
                        "fail" if "fail" in states else "skip" if "skip" in states else "pass")
    return result


def identifiers(case):
    parts = case.attrib.get("classname", "").split(".")
    name = case.attrib.get("name", "")
    # Try module/class boundaries without collapsing distinct files to the same function name.
    return {"/".join(parts[:index]) + ".py::" + "::".join([*parts[index:], name])
            for index in range(1, len(parts) + 1)}


def patch(manager, sandbox):
    result = manager.exec(sandbox, "cd /workspace && git add -N . && git diff --binary _swegemma_baseline", timeout=30)
    if result.exit_code:
        raise RuntimeError("Cannot capture workspace patch: " + result.stderr)
    return result.stdout


BASELINE = r'''
import json, pathlib, shutil, subprocess, sys
root = pathlib.Path(sys.argv[1])
targets = [t.split("::", 1)[0] for t in json.loads(sys.argv[2]) if t != "."]
root.mkdir()
archive = subprocess.Popen(['git', '-C', '/workspace', 'archive', '_swegemma_baseline'], stdout=subprocess.PIPE)
extract = subprocess.run(['tar', '-x', '-C', str(root)], stdin=archive.stdout, check=True)
archive.stdout.close()
if archive.wait():
    raise RuntimeError('Cannot archive baseline')
# Replace baseline test trees with the current visible test trees, including deletions.
for folder in list(root.rglob('*')):
    if folder.is_dir() and folder.name in {'tests', 'test'}:
        shutil.rmtree(folder)
for source in list(root.rglob('test_*.py')) + list(root.rglob('conftest.py')):
    if source.exists():
        source.unlink()
# Copy only visible test Python files and fixtures under test directories.
for source in pathlib.Path('/workspace').rglob('*'):
    relative = source.relative_to('/workspace')
    if '.git' in relative.parts or source.is_symlink() or not source.is_file():
        continue
    if (any(source == pathlib.Path('/workspace') / t or source.is_relative_to(pathlib.Path('/workspace') / t) for t in targets)
            or 'tests' in relative.parts or 'test' in relative.parts or source.name.startswith('test_')
            or source.name == 'conftest.py') and not any(p in {'__pycache__', '.pytest_cache'} for p in relative.parts):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
'''

REMOVE_TREE = "import shutil, sys; shutil.rmtree(sys.argv[1])"

PROBE = r'''
import json
import pytest
from pathlib import Path
usage = {'available': True, 'collected': 0, 'ebt_executed': 0, 'ebt_evaluated': 0, 'ebt_passed': 0}
def pytest_configure(config):
    try:
        from qb_cubie import EBT
    except ImportError:
        return
    original = EBT.run
    def run(self, *args, **kwargs):
        usage['ebt_executed'] += 1
        try:
            return original(self, *args, **kwargs)
        finally:
            trace = self.run_trace
            if trace is not None and trace.evaluation is not None:
                usage['ebt_evaluated'] += 1
                usage['ebt_passed'] += int(trace.evaluation is True)
    EBT.run = run
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

INSTALL_PROBE = "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(" + repr(PROBE) + ".replace('EVIDENCE', repr(sys.argv[2])))"


def diagnostic_id(case, node_ids=(), collection_ids=()):
    """Prefer collected pytest IDs; use JUnit module/class conventions offline."""
    recorded = case.findall("./properties/property[@name='study_nodeid']")
    if recorded:
        return recorded[-1].get('value')
    actual = identifiers(case) & set(node_ids)
    if len(actual) == 1:
        return actual.pop()
    if not case.get('classname') and case.find('error') is not None:
        # JUnit flattens collector paths into dotted names. Only reverse this
        # using actual collected IDs, since dots may also occur in filenames.
        matches = []
        for node in collection_ids:
            path, *names = node.split('::')
            label = '.'.join([path.removesuffix('.py').replace('/', '.'), *names])
            if label == case.get('name'):
                matches.append(node)
        return matches[0] if len(matches) == 1 else case.get('file') or None
    parts = case.get('classname', '').split('.')
    boundary = next((i for i, part in enumerate(parts) if part[:1].isupper()), len(parts))
    path = case.get('file') or '/'.join(parts[:boundary]) + '.py'
    return '::'.join([path, *parts[boundary:], case.get('name', '')])


def test_diagnostics(xml, node_ids=(), collection_ids=()):
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    try:
        cases = list(ET.fromstring(xml).iter("testcase"))
    except ET.ParseError:
        return {"collected": 0, "counts": counts, "errors": [], "invalid_xml": True}
    errors = []
    for case in cases:
        failure = case.find("failure")
        error = case.find("error")
        counts["errors" if error is not None else "failed" if failure is not None else
               "skipped" if case.find("skipped") is not None else "passed"] += 1
        node = error if error is not None else failure
        if node is not None:
            errors.append({"id": diagnostic_id(case, node_ids, collection_ids), "phase": "setup_or_collection" if error is not None else "call",
                           "type": node.get("type"), "message": node.get("message", "")[:500],
                           "traceback_tail": (node.text or "")[-1000:]})
    return {"collected": len(cases), "counts": counts, "errors": errors}
