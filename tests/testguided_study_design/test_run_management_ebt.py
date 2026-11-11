"""One-command run management contracts, including automatic fresh freezes.

Real CLI, selection, preparation, admission, freeze, preflight, runner and report;
synthetic task pool and deterministic build/container/model/evaluator ports.
"""

import itertools
import json
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pytest
from ollama_agents.schema import validate
from test_pilot_technical_ebt import contract
from testguided_study import agent, artifacts, backend, cli, execution, launch
from testguided_study.artifacts import ROOT, digest, read, verify, write
from testguided_study.smoke import generate
from testguided_study.telemetry import snapshot


def tree_identity(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def managed_study(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    shutil.copytree(ROOT / "profiles", project / "profiles")
    shutil.copytree(ROOT / "guides", project / "guides")
    monkeypatch.setattr(launch, "ROOT", project)
    monkeypatch.delenv("KAGGLE_SANDBOX_DIR", raising=False)
    generate(tmp_path / "sample")
    sample = read(tmp_path / "sample/record.json")
    template = read(tmp_path / "sample/tasks.json")[0]
    snapshots = project / "snapshots"
    snapshots.mkdir()
    records, candidates = [], []
    for index in range(3):
        task_id = f"synthetic-pilot-{index}"
        records.append({**sample, "instance_id": task_id})
        candidates.append({**template, "id": task_id, "related_group": task_id, "eligible": True})
        shutil.copyfile(tmp_path / "sample/snapshot.tar.gz", snapshots / f"{task_id}.tgz")
    source = project / "records.jsonl"

    def save_pool():
        source.write_text("".join(json.dumps(row) + "\n" for row in records))
        write(project / "candidate-catalog.json", {"source": str(source), "source_sha256": digest(source),
                                                   "tasks": candidates})

    save_pool()
    state = SimpleNamespace(failure=None, code="code-v1", model="model-v1", image="image-v1", fixed_clock=False)
    ticks, managers, archives, servers, calls = itertools.count(), [], [], [], []
    monkeypatch.setattr(launch, "time", SimpleNamespace(
        strftime=lambda _: "20261111-190000" if state.fixed_clock else f"20261111-1900{next(ticks):02d}"))
    actual_sources = artifacts.sources
    monkeypatch.setattr(artifacts, "sources", lambda: {**actual_sources(), "fixture/runtime": state.code})
    actual_observer = launch.Observer

    class Observer(actual_observer):
        def __init__(self, root, **kwargs):
            super().__init__(root, **kwargs)
            archives.append(Path(root))

    monkeypatch.setattr(launch, "Observer", Observer)

    def ensure(config, directory, observer, *, build):
        calls.append("images")
        if state.failure == "images":
            raise RuntimeError("Synthetic image build failed")
        write(directory / "images.json", {"revision": state.image, "automatic_build": build})

    monkeypatch.setattr(launch.images, "ensure", ensure)
    monkeypatch.setattr(backend, "runtime", lambda: {"version": "synthetic-swegemma"})

    def provider(config):
        if state.failure == "preflight":
            raise RuntimeError("Synthetic model preflight failed")
        return {"model": {"digest": state.model}}

    monkeypatch.setattr(execution, "provider", provider)
    monkeypatch.setattr(backend, "image_identity", lambda image, mode: {
        "image_id": f"{image}:{state.image}", "python": [3, 13], "pytest": "9", "packages": {}})
    monkeypatch.setattr(backend, "task_for", lambda root, item: SimpleNamespace(**read(root / item["record"])))
    monkeypatch.setattr(backend, "prepare", lambda *_: None)

    class Manager:
        def __init__(self):
            self.cleaned = False
            managers.append(self)

        def start(self):
            return self

        def cleanup_all(self):
            self.cleaned = True

    monkeypatch.setattr(backend, "manager", lambda *_: Manager())
    monkeypatch.setattr(agent, "execute", lambda *_: {"status": "completed"})
    monkeypatch.setattr(agent, "patch", lambda *_: "")

    class Client:
        def chat(self, **kwargs):
            calls.append("model")
            if state.failure == "interrupt":
                raise KeyboardInterrupt
            action = {"action": "submit", "stage": "finish", "reason": "Deterministic run-management replay"}
            names = {e['properties']['action']['const'] for e in kwargs['schema']['oneOf']}
            if 'submit' not in names:
                if 'analyze' in names:
                    entry = next(e for e in kwargs['schema']['oneOf'] if e['properties']['action']['const'] == 'analyze')
                    phase = entry['properties']['phase']['enum'][0]
                    action = {"action": 'analyze', "stage": 'inspect', "phase": phase,
                                  "requirement": 'Synthetic issue', "example": 'boundary', "observation": 'No verification',
                                  "decision": 'unclear', "next": 'Finish replay'}
                else:
                    action = {"action": 'read_file', "stage": 'inspect', "path": 'bounds.py', "start": 1}
            validate(action, kwargs["schema"])
            return {"action": action, "usage": {"input_tokens": 7, "output_tokens": 3}, "raw": {"replay": True}}

    monkeypatch.setattr(agent, "OllamaClient", lambda **_: Client())

    def baseline(root, item, config, image, directory):
        calls.append("visible_baseline")
        result = {"status": "completed", "observation": "pass", "diagnostics": {
            "collected": 1, "counts": {"passed": 1, "failed": 0, "errors": 0, "skipped": 0}, "errors": []}}
        write(directory / "visible-baseline.json", result)
        return result

    monkeypatch.setattr(execution.admission, "visible_baseline", baseline)
    monkeypatch.setattr(execution.admission, "collect", lambda *_: [
        {"nodeid": "tests/test_bounds.py::test_inside", "fixtures": [], "skip": False},
        {"nodeid": "tests/test_bounds.py::test_outside", "fixtures": [], "skip": False}])

    def evaluate(root, item, config, image, directory, submitted, **kwargs):
        calls.append("evaluation")
        task = backend.task_for(root, item)
        gold = submitted == task.patch
        suite = ET.Element("testsuite")
        states = {}
        for node in [*task.FAIL_TO_PASS, *task.PASS_TO_PASS]:
            path, name = node.split("::")
            case = ET.SubElement(suite, "testcase", classname=path.removesuffix(".py").replace("/", "."), name=name)
            failed = node in task.FAIL_TO_PASS and not gold
            if failed:
                ET.SubElement(case, "failure", message="AssertionError: synthetic regression")
            states[node] = "fail" if failed else "pass"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "junit.xml").write_text(ET.tostring(suite, encoding="unicode"))
        result = {"available": True, "resolved": gold, "observation": "pass" if gold else "assertion_failure",
                  "tests": states}
        if state.failure == "admission" and gold:
            result["resolved"] = False
        write(directory / "result.json", result)
        return result

    monkeypatch.setattr(backend, "evaluate", evaluate)

    class Monitor:
        def __init__(self, root, port):
            self.root, self.closed = root, False
            servers.append(self)

        def start(self):
            if state.failure == "monitor":
                raise RuntimeError("Synthetic monitor bind failed")
            return "http://127.0.0.1:12345"

        def close(self):
            self.closed = True

    monkeypatch.setattr(launch, "MonitorServer", Monitor)

    def arguments(**overrides):
        return SimpleNamespace(**({"command": "start", "mode": "pilot", "config": None, "tasks": None,
            "seeds": None, "task_type": None, "agent_seconds": None, "model_calls": None, "output": None,
            "monitor": "none", "port": 0, "keep_monitor": False, "prepare_only": False,
            "no_build_images": False, "catalog": project / "candidate-catalog.json",
            "source": None, "snapshots": snapshots, "tasks_manifest": None, "regression_tests": 8} | overrides))

    return SimpleNamespace(start=lambda **kw: launch.start(arguments(**kw)), arguments=arguments, state=state,
                           project=project, managers=managers, archives=archives, calls=calls, servers=servers,
                           records=records, save_pool=save_pool)


def test_m01_default_cli_prepares_freezes_checks_runs_and_reports_without_manual_steps(managed_study, monkeypatch):
    env = managed_study
    monkeypatch.setattr(sys, "argv", ["study"])
    # The real parser's default catalog was resolved from artifacts.ROOT at
    # import; point that default at the isolated synthetic project as well.
    monkeypatch.setattr(cli, "ROOT", env.project)

    def observe():
        code = cli.main()
        root = env.archives[0]
        report = read(root / "report.json")
        execution.ready(root / "frozen")
        return (code, verify(root / "frozen")["phase"], report["scheduled_runs"], report["complete_pairs"],
                snapshot(root)["state"], read(root / "launch.json")["output"],
                read(root / "setup/images.json")["automatic_build"], env.calls.count("model"),
                all(manager.cleaned for manager in env.managers))

    contract(observe, (0, "pilot", 6, 3, "finished", None, True, 24, True))


@pytest.mark.parametrize("mode", ["smoke", "pilot"])
def test_m02_sequential_starts_in_one_second_allocate_distinct_complete_archives(managed_study, mode):
    env = managed_study
    env.state.fixed_clock = True

    def observe():
        first = env.start(mode=mode)
        root = Path(first["archive"])
        before = tree_identity(root)
        try:
            second = env.start(mode=mode)
        except FileExistsError:
            second = {}
        return (bool(second), second.get("archive") != first["archive"], tree_identity(root) == before,
                len(list((env.project / "runs").glob("*/report.json"))))

    contract(observe, (True, True, True, 2))


def test_m03_concurrent_automatic_starts_cannot_claim_the_same_archive(managed_study):
    env = managed_study
    env.state.fixed_clock = True
    barrier = threading.Barrier(2)

    def start():
        barrier.wait(timeout=5)
        try:
            return env.start(mode="smoke", prepare_only=True)
        except FileExistsError:
            return None

    def observe():
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(start) for _ in range(2)]
            results = [future.result(timeout=15) for future in futures]
        paths = [Path(result["archive"]) for result in results if result]
        return (len(paths), len(set(paths)), all((path / "frozen/ready.json").exists() for path in paths),
                env.calls.count("model"))

    contract(observe, (2, 2, True, 0))


@pytest.mark.parametrize("change", ["guide", "code", "model", "image", "budget", "tasks"])
def test_m04_new_start_automatically_freezes_current_inputs_and_runtime(managed_study, change):
    env = managed_study

    def observe():
        first = Path(env.start()["archive"])
        before = tree_identity(first)
        overrides = {}
        if change == "guide":
            guide = env.project / "guides/cubie.md"
            guide.write_text(guide.read_text() + "\nCURRENT_GUIDE_REVISION\n")
        elif change == "budget":
            overrides["agent_seconds"] = 123
        elif change == "tasks":
            for record in env.records:
                record["problem_statement"] += "\nCURRENT_TASK_REVISION"
            env.save_pool()
        else:
            setattr(env.state, change, f"{change}-v2")
        second = Path(env.start(**overrides)["archive"])
        frozen = second / "frozen"
        config, runtime = execution.ready(frozen)
        changed = {
            "guide": lambda: "CURRENT_GUIDE_REVISION" in read(frozen / "guides.json")["cubie"],
            "code": lambda: read(frozen / "manifest.json")["implementation"]["fixture/runtime"] == "code-v2",
            "model": lambda: runtime["ollama"]["model"]["digest"] == "model-v2",
            "image": lambda: runtime["images"]["cubie"]["image_id"].endswith(":image-v2"),
            "budget": lambda: config["budgets"]["wall_seconds"] == 123,
            "tasks": lambda: all("CURRENT_TASK_REVISION" in read(frozen / item["record"])["problem_statement"]
                                 for item in read(frozen / "tasks.json")),
        }[change]()
        return first != second, changed, tree_identity(first) == before, snapshot(second)["state"]

    contract(observe, (True, True, True, "finished"))


@pytest.mark.parametrize("failure", ["images", "admission", "preflight"])
def test_m05_failed_preparation_is_archived_and_next_start_succeeds_without_repair_commands(managed_study, failure):
    env = managed_study

    def observe():
        env.state.failure = failure
        with pytest.raises((ValueError, RuntimeError)):
            env.start()
        failed = env.archives[0]
        before = tree_identity(failed)
        no_inference = env.calls.count("model") == 0
        env.state.failure = None
        current = Path(env.start()["archive"])
        return (snapshot(failed)["state"], (failed / "failure.json").exists(), no_inference,
                current != failed, snapshot(current)["state"], tree_identity(failed) == before)

    contract(observe, ("failed", True, True, True, "finished", True))


def test_m06_interrupted_attempt_is_preserved_and_next_start_is_independent(managed_study):
    env = managed_study

    def observe():
        env.state.failure = "interrupt"
        with pytest.raises(KeyboardInterrupt):
            env.start(mode="smoke")
        prior = env.archives[0]
        before = tree_identity(prior)
        env.state.failure = None
        current = Path(env.start(mode="smoke")["archive"])
        return (snapshot(prior)["state"], any((prior / "frozen/runs").glob("*/result.json")),
                tree_identity(prior) == before, current != prior, snapshot(current)["state"],
                all(manager.cleaned for manager in env.managers))

    contract(observe, ("interrupted", True, True, True, "finished", True))


def test_m07_prepare_only_never_infers_and_does_not_need_to_be_resumed_for_next_start(managed_study):
    env = managed_study

    def observe():
        prepared = Path(env.start(prepare_only=True)["archive"])
        before = tree_identity(prepared)
        calls = env.calls.count("model")
        current = Path(env.start()["archive"])
        return (snapshot(prepared)["state"], calls, current != prepared, tree_identity(prepared) == before,
                snapshot(current)["completed_runs"])

    contract(observe, ("prepared", 0, True, True, 6))


@pytest.mark.parametrize("populated", [False, True])
def test_m08_explicit_existing_output_is_never_replaced_or_silently_redirected(managed_study, populated):
    env = managed_study
    output = env.project / "explicit-output"
    output.mkdir()
    if populated:
        (output / "evidence.txt").write_text("Preserve this earlier evidence")
    before = tree_identity(output)

    def observe():
        with pytest.raises(FileExistsError):
            env.start(output=output)
        return tree_identity(output) == before, env.calls.count("model"), len(env.archives)

    contract(observe, (True, 0, 0))


def test_m09_completed_frozen_attempt_cannot_be_silently_resumed(managed_study):
    env = managed_study

    def observe():
        prior = Path(env.start(mode="smoke")["archive"])
        before = tree_identity(prior)
        with pytest.raises(ValueError, match="never silently resumes"):
            execution.run(prior / "frozen")
        return tree_identity(prior) == before, snapshot(prior)["completed_runs"]

    contract(observe, (True, 2))


@pytest.mark.parametrize("failure", [None, "monitor", "images", "preflight", "interrupt"])
def test_m10_automatically_started_monitor_is_closed_on_every_exit(managed_study, failure):
    env = managed_study

    def observe():
        env.state.failure = failure
        caught = None
        try:
            env.start(mode="smoke", monitor="web")
        except (RuntimeError, KeyboardInterrupt) as error:
            caught = type(error).__name__
            if failure is None:
                raise
        return (len(env.servers), all(server.closed for server in env.servers),
                env.servers[0].root == env.archives[0], caught, snapshot(env.archives[0])["state"])

    expected_error = "KeyboardInterrupt" if failure == "interrupt" else "RuntimeError" if failure else None
    expected_state = "interrupted" if failure == "interrupt" else "failed" if failure else "finished"
    contract(observe, (1, True, True, expected_error, expected_state))
