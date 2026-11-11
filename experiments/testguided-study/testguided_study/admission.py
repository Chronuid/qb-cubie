"""Derive explicit repair and regression nodes before any agent inference."""

import json
import re
import shlex
from pathlib import Path, PurePosixPath

from . import backend
from .artifacts import read, write
from .telemetry import emit
from .workspace import outcomes, run_tests

COLLECT = '''import json, pytest
class Capture:
    def pytest_collection_finish(self, session):
        print("STUDY_NODES=" + json.dumps([{"nodeid": i.path.relative_to('/workspace').as_posix() + '::' + i.nodeid.split('::', 1)[1], "fixtures": i.fixturenames, "skip": any(m.name == 'skip' or (m.name == 'skipif' and True in m.args) for m in i.iter_markers())} for i in session.items]))
raise SystemExit(pytest.main(TARGETS + ["--rootdir=/workspace", "--collect-only", "-q", "-o", "addopts="], plugins=[Capture()]))
'''


def changed_tests(patch):
    names = set(re.findall(r"^\+\s*(?:async\s+)?def\s+(test_\w+)\s*\(", patch, re.MULTILINE))
    names.update(re.findall(r"^@@[^\n]*@@.*?def\s+(test_\w+)\s*\(", patch, re.MULTILINE))
    names.update(re.findall(r"^ \s*def\s+(test_\w+)\s*\(", patch, re.MULTILINE))
    return names


def apply(mgr, sandbox, content, directory, name):
    if not content.strip():
        return
    from swegemma.harness.container_setup import apply_patch_in_container
    path = directory / name
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
    target = f"/tmp/{name}"
    mgr.copy_to(sandbox, path, target)
    code, stdout, stderr = apply_patch_in_container(mgr, sandbox, target)
    if code:
        raise ValueError("Reference patch cannot be applied: " + (stderr or stdout)[-2000:])


def control_file(paths, targets):
    words = {word for target in targets for word in PurePosixPath(target).stem.split("_") if word != "test"}
    choices = [path for path in paths if path not in targets]
    return min(choices, key=lambda path: (-len(words & set(PurePosixPath(path).stem.split("_"))),
                                        len(PurePosixPath(path).parts), path)) if choices else None


def collection(mgr, sandbox, targets, config, receipt):
    script = "TARGETS = " + repr(targets) + "\n" + COLLECT
    plugins = shlex.quote(','.join(getattr(mgr, 'study_plugins', ())))
    result = mgr.exec(sandbox, "cd /workspace && PYTEST_PLUGINS=" + plugins + " python3 -c " + shlex.quote(script),
                      timeout=config["budgets"]["verification_seconds"])
    write(receipt, {"stdout": result.stdout, "stderr": result.stderr,
                    "exit_code": result.exit_code, "timed_out": result.timed_out})
    match = re.search(r"^STUDY_NODES=(.*)$", result.stdout, re.MULTILINE)
    if result.exit_code or not match:
        raise ValueError(f"Cannot collect independent tests; see {receipt}")
    return json.loads(match[1])


def visible_baseline(root, item, config, image, directory):
    """Profile original visible tests in a fresh sandbox, before any private patch."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    task = backend.task_for(root, item)
    mgr = backend.manager(image, config['budgets']['verification_seconds'])
    try:
        sandbox = mgr.start()
        backend.prepare(mgr, sandbox, root, item, task, config, directory)
        result = run_tests(mgr, sandbox, ['.'], config['budgets']['verification_seconds'], 12000)
        (directory / 'visible-baseline.xml').write_text(result.get('junit_xml', ''), encoding='utf-8')
        write(directory / 'visible-baseline.json', result)
        return result
    finally:
        mgr.cleanup_all()


def collect(root, item, config, image, directory):
    task = backend.task_for(root, item)
    mgr = backend.manager(image, config["budgets"]["verification_seconds"])
    try:
        sandbox = mgr.start()
        backend.prepare(mgr, sandbox, root, item, task, config, directory)
        apply(mgr, sandbox, task.patch, directory, "gold.patch")
        apply(mgr, sandbox, task.test_patch, directory, "tests.patch")
        targets = [path for path in task.test_files if path.endswith(".py") and not path.endswith("conftest.py")]
        nodes = collection(mgr, sandbox, targets, config, directory / "collection.json")
        changed = changed_tests(task.test_patch)
        if nodes and all(node["nodeid"].split("::")[-1].split("[")[0] in changed for node in nodes):
            script = "import json,pathlib; print(json.dumps(sorted(p.relative_to('/workspace').as_posix() for p in pathlib.Path('/workspace/tests').rglob('test_*.py'))))"
            inventory = mgr.exec(sandbox, "python3 -S -c " + shlex.quote(script), timeout=30)
            extra = control_file(json.loads(inventory.stdout), targets)
            if extra:
                write(directory / "control-file.json", {"path": extra, "reason": "no unchanged nodes in modified test files"})
                nodes = collection(mgr, sandbox, targets + [extra], config, directory / "collection-controls.json")
        return nodes
    finally:
        mgr.cleanup_all()


def admit(root, item, config, image, directory, *, regressions=8, observer=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    task = backend.task_for(root, item)
    emit(observer, "admission_started", f"Unabhängige Testzuordnung ermitteln: {item['id']}", state="admission")
    visible_baseline(root, item, config, image, directory)
    nodes = collect(root, item, config, image, directory)
    names = changed_tests(task.test_patch)
    changed = sorted({node["nodeid"] for node in nodes if node["nodeid"].split("::")[-1].split("[")[0] in names})
    if not changed:
        raise ValueError(f"No changed test functions found for {item['id']}; explicit node mapping required")
    control_nodes = [node for node in nodes if node["nodeid"] not in changed and not node.get("skip")]
    control_nodes.sort(key=lambda node: (any("httpbin" in f for f in node["fixtures"]), node["nodeid"]))
    controls = [node["nodeid"] for node in control_nodes[:regressions]]
    targets = changed + controls
    write(directory / "probe-targets.json", {"changed": changed, "controls": controls,
                                             "collected_nodes": len(nodes), "regression_limit": regressions})
    base = backend.evaluate(root, item, config, image, directory / "base", "", targets=targets)
    gold = backend.evaluate(root, item, config, image, directory / "gold", task.patch, targets=targets)
    before = outcomes((directory / "base/junit.xml").read_text(), targets)
    after = outcomes((directory / "gold/junit.xml").read_text(), targets)
    repairs = [node for node in changed if before[node] == "fail" and after[node] == "pass"]
    regressions_passed = [node for node in targets if before[node] == after[node] == "pass"]
    if (not base["available"] or base["observation"] != "assertion_failure" or not gold["available"]
            or any(state != "pass" for state in after.values()) or not repairs or not regressions_passed):
        write(directory / "rejected.json", {"before": before, "after": after, "base": base, "gold": gold})
        raise ValueError(f"Task {item['id']} failed automatic admission; inspect {directory}")
    record_path = root / item["record"]
    record = read(record_path)
    record.update(FAIL_TO_PASS=repairs, PASS_TO_PASS=regressions_passed)
    write(record_path, record)
    write(directory / "admission.json", {"task_id": item["id"], "FAIL_TO_PASS": repairs,
                                         "PASS_TO_PASS": regressions_passed, "before": before, "after": after,
                                         "scope": "changed tests and capped controls in private test files"})
    emit(observer, "admission_finished", f"{item['id']}: {len(repairs)} Reparatur- und {len(regressions_passed)} Regressionstests zugeordnet")
