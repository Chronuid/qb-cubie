"""Adapt swegemma's fresh Docker workspaces and independent verifier."""

import ast
import asyncio
import importlib.metadata
import json
import re
import shlex
import time
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

from .artifacts import digest, read, write
from .workspace import classify, command, outcomes


def runtime():
    import swegemma
    if swegemma.__version__ != "0.2.11":
        raise ValueError("This bridge was validated with swegemma 0.2.11; validate changes before upgrading")
    root = Path(swegemma.__file__).parent
    return {"version": swegemma.__version__, "files": {
        path.relative_to(root).as_posix(): digest(path) for path in sorted(root.rglob("*.py"))},
        "dependencies": {name: importlib.metadata.version(name) for name in
                         ("adk-eval-core", "adk-submission", "docker", "pydantic")}}


def manager(image, seconds):
    from swegemma.sandbox import ContainerConfig, ContainerManager
    return ContainerManager(ContainerConfig(image=image, network_mode="none", reuse_containers=False,
                                            timeout_seconds=seconds,
                                            environment={"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                                                         "PYTHONDONTWRITEBYTECODE": "1"}))


def harness_config(root, directory, config):
    from swegemma.harness.container_setup import resolve_sandbox_setup_script
    # Disable implicit wheel discovery: every dependency must already be in the image.
    empty = directory / "empty-wheels"
    empty.mkdir(parents=True, exist_ok=True)
    cfg = SimpleNamespace(tasks_path=root / "inputs/tasks.json", snapshots_dir=root / "inputs/snapshots",
                           submission_dir=None, wheels_dir=empty, results_dir=directory, sandbox="docker",
                           harness=SimpleNamespace(command_timeout_seconds=config["budgets"]["command_seconds"],
                                                   verification_timeout_seconds=config["budgets"]["verification_seconds"]))
    if resolve_sandbox_setup_script(cfg) is not None:
        raise ValueError("Ambient host setup script found; study setup must come exclusively from pinned images")
    return cfg


def task_for(root, item):
    from swegemma.models import Task
    return Task(**read(root / item["record"]))


def prepare(mgr, sandbox, root, item, task, config, directory):
    from swegemma.harness.container_setup import (
        extract_snapshot,
        install_editable_package,
        install_test_dependencies,
        setup_baseline_commit,
        setup_git_exclude,
        setup_workspace_test_config,
    )
    mgr.study_plugins = task_plugins(task.repo)
    cfg = harness_config(root, directory, config)
    extract_snapshot(mgr, sandbox, root / item["snapshot"])
    setup_git_exclude(mgr, sandbox)
    install_editable_package(mgr, sandbox)
    install_test_dependencies(mgr, sandbox, task.repo, config=cfg)
    setup_workspace_test_config(mgr, sandbox, repo=task.repo)
    setup_baseline_commit(mgr, sandbox, "study-baseline")
    result = mgr.exec(sandbox, "git rev-parse _swegemma_baseline", timeout=10)
    if result.exit_code:
        raise RuntimeError("swegemma did not establish a baseline: " + result.stderr)


def evaluate(root, item, config, image, directory, submitted, *, targets=None):
    from swegemma.harness.verification import (
        strip_protected_files_from_patch,
        verify_task,
    )
    task = task_for(root, item)
    evaluation_task = TargetedTask(task, targets or [*task.FAIL_TO_PASS, *task.PASS_TO_PASS])
    directory.mkdir(parents=True, exist_ok=True)
    effective = strip_protected_files_from_patch(submitted, extra_protected_paths=task.test_files)
    (directory / "evaluated.patch").write_text(effective, encoding="utf-8")
    mgr = manager(image, config["budgets"]["verification_seconds"])
    original = mgr.exec
    count = 0
    test_observations = []
    test_commands = []
    timed_out = False

    def capture(sandbox, cmd, *, timeout=None):
        nonlocal count, timed_out
        if "python3 -s -m pytest " in cmd:
            plugin_env = 'PYTEST_PLUGINS=' + shlex.quote(','.join(task_plugins(task.repo))) + ' '
            cmd = cmd.replace("python3 -s -m pytest ", plugin_env + "python3 -s -m pytest --rootdir=/workspace ", 1)
        result = original(sandbox, cmd, timeout=timeout)
        timed_out = timed_out or result.timed_out
        report = re.search(r"--junitxml=(/tmp/_swegemma_junit_[0-9a-f]+\.xml)", cmd)
        if report:
            test_commands.append((result.exit_code, result.stderr))
            xml = original(sandbox, "cat " + report[1], timeout=10)
            test_observations.append(xml.stdout)
            (directory / "junit.xml").write_text(xml.stdout, encoding="utf-8")
        write(directory / f"commands/{count:04d}.json", {"command": cmd, "exit_code": result.exit_code,
                                                       "stdout": result.stdout, "stderr": result.stderr,
                                                       "timed_out": result.timed_out})
        count += 1
        return result

    mgr.exec = capture
    try:
        result = asyncio.run(verify_task(mgr, harness_config(root, directory, config), evaluation_task,
                                         root / item["snapshot"], agent_patch=effective,
                                         start_time=time.perf_counter()))
        data = {key: getattr(result, key) for key in
                ("resolved", "test_exit_code", "test_output", "error", "duration_seconds")}
        # pytest also uses exit 4 for conftest import failures, without JUnit.
        # Attribute those only when the captured traceback reaches a file in
        # the effective production patch. CLI errors and timeouts stay unavailable.
        patch_failure = (data['test_exit_code'] == 4 and test_commands
                         and test_commands[-1][0] == 4
                         and patch_import_failure(effective, test_commands[-1][1]))
        data["available"] = bool((data["test_exit_code"] in (0, 1, 2) or patch_failure)
                                 and not timed_out and not data['error'])
        xml = test_observations[-1] if test_observations else ""
        data["observation"] = classify(data["test_exit_code"], xml, timed_out)
        data["tests"] = outcomes(xml, [*task.FAIL_TO_PASS, *task.PASS_TO_PASS])
        data["resolved"] = data["resolved"] and all(state == "pass" for state in data["tests"].values())
        write(directory / "result.json", data)
        return data
    finally:
        mgr.cleanup_all()


def patch_import_failure(patch, stderr):
    """Recognize a conftest import failure in an actually changed workspace file."""
    conftest = re.search(r"ImportError while loading conftest ['\"]([^'\"]+)['\"]", stderr)
    if not conftest or not re.search(
            r'^\s*(?:E\s+)?(?:SyntaxError|IndentationError|TabError|ImportError|ModuleNotFoundError):',
            stderr, re.MULTILINE):
        return False
    changed = set()
    for line in patch.splitlines():
        if line.startswith('+++ '):
            name = line[4:].split('\t', 1)[0]
            if name.startswith('"'):
                try:
                    name = ast.literal_eval(name)
                except (ValueError, SyntaxError):
                    continue
            if name.startswith('b/'):
                changed.add(name[2:])
    roots = (PurePosixPath('/workspace'), PurePosixPath(conftest[1]).parent)
    frames = re.findall(r'^\s*(?:E\s+)?File ["\']([^"\']+)["\'], line \d+', stderr, re.MULTILINE)
    frames += re.findall(r'^\s*([^\n]+\.py):\d+: in ', stderr, re.MULTILINE)
    for frame in frames:
        path = PurePosixPath(frame)
        if not path.is_absolute() and path.as_posix() in changed:
            return True
        for root in roots:
            if path.is_relative_to(root) and path.relative_to(root).as_posix() in changed:
                return True
    return False


def task_plugins(repo):
    """Explicit task dependencies; never inherit plugins from an ambient image."""
    return ('pytest_httpbin.plugin',) if repo.lower() == 'psf/requests' else ()


class TargetedTask:
    def __init__(self, task, targets):
        self.task = task
        self.test_files = targets or task.test_files

    def __getattr__(self, name):
        return getattr(self.task, name)


def image_identity(image, mode):
    mgr = manager(image, 30)
    # Resolve explicitly before ContainerManager can substitute an unrelated fallback image.
    metadata = mgr.client.images.get(image)
    image_id = metadata.id
    mgr.config.image = image_id
    sandbox = mgr.start()
    script = """import site; site.main()
import importlib.metadata as m, importlib.util as u, json, sys
print(json.dumps({'python':list(sys.version_info[:3]), 'pytest':m.version('pytest'),
 'cubie':u.find_spec('qb_cubie') is not None,
 'packages':dict(sorted((d.metadata['Name'].lower(), d.version) for d in m.distributions()))}))
"""
    try:
        result = mgr.exec(sandbox, command(script), timeout=30)
        if result.exit_code:
            raise RuntimeError(f"Image probe failed: {result.stderr}")
        identity = json.loads(result.stdout)
        if identity["python"][:2] < [3, 13] or identity["cubie"] != (mode == "cubie"):
            raise ValueError(f"Invalid Python/Cubie isolation for {mode}: {identity}")
        if mode == "cubie":
            probe = mgr.exec(sandbox, "python3 -c " + shlex.quote(
                "from qb_cubie import EBT, WorldState; "
                "assert EBT(target=lambda: 2, post=WorldState(returns=2), reporter=None).run().evaluation"), timeout=30)
            if probe.exit_code:
                raise ValueError("Cubie runtime check failed: " + probe.stderr)
        return {"image_id": image_id, **identity}
    finally:
        mgr.cleanup_all()
