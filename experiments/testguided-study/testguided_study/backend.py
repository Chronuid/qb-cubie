"""Adapt swegemma's fresh Docker workspaces and independent verifier."""

import asyncio
import importlib.metadata
import json
import re
import shlex
import time
from pathlib import Path
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
    timed_out = False

    def capture(sandbox, cmd, *, timeout=None):
        nonlocal count, timed_out
        if "python3 -s -m pytest " in cmd:
            cmd = cmd.replace("python3 -s -m pytest ", "python3 -s -m pytest --rootdir=/workspace ", 1)
        result = original(sandbox, cmd, timeout=timeout)
        timed_out = timed_out or result.timed_out
        report = re.search(r"--junitxml=(/tmp/_swegemma_junit_[0-9a-f]+\.xml)", cmd)
        if report:
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
        # Agent-caused syntax/import failures count as failed solutions after task admission.
        data["available"] = data["test_exit_code"] in (0, 1, 2) and not timed_out
        xml = test_observations[-1] if test_observations else ""
        data["observation"] = classify(data["test_exit_code"], xml, timed_out)
        data["tests"] = outcomes(xml, [*task.FAIL_TO_PASS, *task.PASS_TO_PASS])
        data["resolved"] = data["resolved"] and all(state == "pass" for state in data["tests"].values())
        write(directory / "result.json", data)
        return data
    finally:
        mgr.cleanup_all()


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
