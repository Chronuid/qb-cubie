"""Expose bounded file tools and real pytest observations inside a sandbox."""

import base64
import json
import re
import shlex
import uuid
import xml.etree.ElementTree as ET

SCRIPT = r'''
import hashlib, json, pathlib, sys
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
if op == 'list_files':
    names = [str(p.relative_to(root)) for p in files()]
    result = {'files': names[:1500], 'omitted': max(0, len(names)-1500)}
elif op == 'read_file':
    p = target(arg['path'])
    if p.stat().st_size > 2_000_000:
        raise ValueError('File exceeds the readable size limit')
    lines = p.read_text().splitlines()
    start = arg['start'] - 1
    result = {'path': arg['path'], 'start': start+1, 'total_lines': len(lines),
              'text': '\n'.join(lines[start:start+160])}
elif op in ('search_text', 'search_files'):
    scope = target(arg['path']) if op == 'search_files' else root
    if not scope.exists():
        raise ValueError('Search path does not exist')
    offset = arg['start'] if op == 'search_files' else 0
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
elif op == 'replace_text':
    p = target(arg['path'])
    if p.stat().st_size > 2_000_000:
        raise ValueError('File exceeds the editable size limit')
    original = p.read_bytes().decode('utf-8')
    if not arg['old'] or original.count(arg['old']) != 1:
        raise ValueError('Old text must match exactly once; file unchanged')
    data = original.replace(arg['old'], arg['new'], 1).encode('utf-8')
    if len(data) > 2_000_000:
        raise ValueError('Replacement exceeds the editable size limit')
    p.write_bytes(data)
    result = {'written': arg['path'], 'sha256': hashlib.sha256(data).hexdigest()}
elif op in ('write_file', 'delete_file'):
    p = target(arg['path'])
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
'''


def command(script, *arguments):
    encoded = base64.b64encode(script.encode()).decode("ascii")
    loader = "import base64; exec(base64.b64decode(" + repr(encoded) + "))"
    return "python3 -S -c " + shlex.quote(loader) + " " + " ".join(shlex.quote(arg) for arg in arguments)


def execute(manager, sandbox, action, timeout, limit):
    if action["action"] == "run_tests":
        return run_tests(manager, sandbox, action["targets"], timeout, limit)
    result = manager.exec(sandbox, command(SCRIPT, json.dumps(action)), timeout=timeout)
    if result.exit_code:
        return {"status": "tool_error", "stderr": result.stderr[:limit], "timed_out": result.timed_out}
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


def run_tests(manager, sandbox, targets, timeout, limit):
    for target in targets:
        path = target.split("::", 1)[0]
        if not path or path.startswith(("/", "-")) or any(p in {"..", ".git"} for p in path.split("/")):
            return {"status": "tool_error", "error": "Use relative test paths or pytest node IDs"}
    report = f"/tmp/study-{uuid.uuid4().hex}.xml"
    cmd = ("cd /workspace && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1 "
           "python3 -m pytest --rootdir=/workspace " + " ".join(shlex.quote(path) for path in targets)
           + f" --junitxml={report} -q")
    result = manager.exec(sandbox, cmd, timeout=timeout)
    xml = manager.exec(sandbox, "cat " + report, timeout=10)
    observed = classify(result.exit_code, xml.stdout, result.timed_out)
    return {"status": "completed", "observation": observed, "exit_code": result.exit_code,
            "timed_out": result.timed_out, "stdout": result.stdout[:limit], "stderr": result.stderr[:limit],
            "output_truncated": len(result.stdout) > limit or len(result.stderr) > limit,
            "junit_xml": xml.stdout}


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
