"""Gate studies on reference checks and execute their frozen paired schedule."""

import json
import platform
import time
import urllib.request
from pathlib import Path

from . import admission, backend
from .agent import develop
from .artifacts import MODES, digest, read, verify, write
from .iteration import load_design
from .telemetry import Observer, emit


def provider(config):
    model = config["ollama"]
    endpoint = model["endpoint"].rstrip("/")
    with urllib.request.urlopen(endpoint + "/api/version", timeout=10) as response:
        version = json.load(response)
    with urllib.request.urlopen(endpoint + "/api/tags", timeout=10) as response:
        tags = json.load(response)
    matches = [tag for tag in tags["models"] if tag["name"] == model["model"]]
    if len(matches) != 1 or not matches[0].get("digest"):
        raise ValueError("The explicitly configured model must be installed with a digest")
    return {"version": version, "model": matches[0]}


def preflight(root, observer=None):
    root = Path(root).resolve()
    config = verify(root)
    destination = root / "preflight"
    destination.mkdir(exist_ok=False)
    emit(observer, "preflight_started", "Modell- und Containeridentitäten prüfen", phase="preflight", state="preflight")
    # Reject ambient data/setup discovery from unrelated swegemma installations.
    import os
    if os.environ.get("KAGGLE_SANDBOX_DIR"):
        raise ValueError("Unset KAGGLE_SANDBOX_DIR; task setup must come from the pinned images")
    identity = {"swegemma": backend.runtime(), "ollama": provider(config),
                "host": {"platform": platform.platform(), "python": platform.python_version()},
                "images": {mode: backend.image_identity(config["images"][mode], mode)
                           for mode in (*MODES, "evaluator")}}
    if (root / "campaign.json").exists() and config["phase"] == "measurement":
        for evidence in read(root / "campaign.json")["provenance"]:
            if not evidence["contributes"]:
                continue
            prior = evidence["runtime"]
            if prior["ollama"] != identity["ollama"] or prior["swegemma"] != identity["swegemma"]:
                raise ValueError("Qualification model/runtime identity drift")
            if any(prior["images"][mode]["image_id"] != identity["images"][mode]["image_id"]
                   for mode in (*MODES, "evaluator")):
                raise ValueError("Qualification image identity drift")
    images = identity["images"]
    if images["pytest"]["python"] != images["cubie"]["python"] or images["pytest"]["pytest"] != images["cubie"]["pytest"]:
        raise ValueError("Agent images must use identical Python and pytest versions")
    for name, version in images["pytest"]["packages"].items():
        if images["cubie"]["packages"].get(name) != version:
            raise ValueError(f"Shared dependency differs between treatments: {name}")
    write(destination / "identity.json", identity)
    references = {}
    for item in read(root / "tasks.json"):
        emit(observer, "reference_started", f"Private Rot-/Grün-Prüfung: {item['id']}", state="reference_check")
        task = backend.task_for(root, item)
        admission.visible_baseline(root, item, config, images['evaluator']['image_id'],
                                   destination / f'visible/{len(references):04d}')
        base = backend.evaluate(root, item, config, images["evaluator"]["image_id"],
                                destination / f"references/{len(references):04d}/base", "")
        gold = backend.evaluate(root, item, config, images["evaluator"]["image_id"],
                                destination / f"references/{len(references):04d}/gold", task.patch)
        references[item["id"]] = {"base": base, "gold": gold}
        write(destination / "references.json", references)
        if (not base["available"] or base["observation"] != "assertion_failure"
                or base["resolved"] or not gold["available"] or not gold["resolved"]
                or any(base["tests"][node] != "fail" for node in task.FAIL_TO_PASS)
                or any(base["tests"][node] != "pass" for node in task.PASS_TO_PASS)):
            raise ValueError(f"Task {item['id']} failed baseline-red/reference-green admission")
    files = {p.relative_to(root).as_posix(): digest(p) for p in destination.rglob("*") if p.is_file()}
    write(root / "ready.json", {"manifest_sha256": digest(root / "manifest.json"), "preflight_files": files})
    emit(observer, "preflight_finished", "Vorprüfung erfolgreich", state="ready")
    return {"status": "ready", "tasks": len(references), "model_digest": identity["ollama"]["model"]["digest"]}


def ready(root):
    config = verify(root)
    admission = read(root / "ready.json")
    if digest(root / "manifest.json") != admission["manifest_sha256"]:
        raise ValueError("Study manifest changed after admission")
    for path, expected in admission["preflight_files"].items():
        if digest(root / path) != expected:
            raise ValueError(f"Preflight evidence changed: {path}")
    identity = read(root / "preflight/identity.json")
    if backend.runtime() != identity["swegemma"] or provider(config) != identity["ollama"]:
        raise ValueError("swegemma or Ollama/model identity changed after admission")
    return config, identity


def run(root, observer=None):
    root = Path(root).resolve()
    config, identity = ready(root)
    rows = read(root / "schedule.json")
    # Reject reuse before creating an observer or writing any archive state.
    for row in rows:
        if (root / "runs" / row["run_id"]).exists():
            raise ValueError("Runs already exist; this command never silently resumes or overwrites attempts")
    observer = observer or Observer(root)
    observer.bind(root, config, rows)
    tasks = {item["id"]: item for item in read(root / "tasks.json")}
    baselines = {}
    for index, item in enumerate(tasks.values()):
        path = root / f'preflight/visible/{index:04d}/visible-baseline.json'
        if path.is_file():
            baselines[item['id']] = read(path)
    guides = read(root / "guides.json")
    for row in rows:
        # Recheck identity between runs so a restarted/reconfigured provider cannot pass unnoticed.
        ready(root)
        directory = root / "runs" / row["run_id"]
        directory.mkdir(parents=True, exist_ok=False)
        write(directory / "attempt.json", row)
        item = tasks[row["task_id"]]
        observer.begin(row, config)
        print(f"{row['run_id']}: {row['mode']} {row['task_id']} seed={row['seed']}", flush=True)
        mgr = backend.manager(identity["images"][row["mode"]]["image_id"], config["budgets"]["command_seconds"])
        sandbox = None
        started = time.monotonic()
        interrupted = None
        try:
            sandbox = mgr.start()
            task = backend.task_for(root, item)
            backend.prepare(mgr, sandbox, root, item, task, config, directory)
            agent = develop(mgr, sandbox, task, row, config, guides, directory, observer=observer,
                            design=load_design(root / "designs" / f"{row['mode']}.json"),
                            visible_baseline=baselines.get(row['task_id']))
            patch = agent.pop("patch")
            write(directory / "agent.json", agent)
            observer.emit("evaluation_started", "Unabhängige Lösungsauswertung läuft", state="evaluating")
            evaluation = backend.evaluate(root, item, config, identity["images"]["evaluator"]["image_id"],
                                          directory / "evaluation", patch)
            result = {**row, "agent": agent, "evaluation": evaluation,
                      "resolved": evaluation["resolved"] if evaluation["available"]
                      and agent["status"] != "infrastructure_error" else None}
        except KeyboardInterrupt as error:
            interrupted = error
            result = {**row, "resolved": None, "error": "Interrupted by user", "error_type": "KeyboardInterrupt"}
        except Exception as error:  # noqa: BLE001 - Preserve every failed attempt as study evidence.
            result = {**row, "resolved": None, "error": str(error), "error_type": type(error).__name__}
        finally:
            mgr.cleanup_all()
        result["total_seconds"] = time.monotonic() - started
        write(directory / "result.json", result)
        files = {p.relative_to(directory).as_posix(): digest(p) for p in directory.rglob("*") if p.is_file()}
        write(directory / "manifest.json", files)
        observer.finish(result)
        if interrupted is not None:
            observer.emit("interrupted", "Studie unterbrochen; Versuch bleibt erhalten", state="interrupted", phase="interrupted")
            raise interrupted
    observer.emit("finished", "Alle geplanten Läufe abgeschlossen", state="finished", phase="finished")
    return {"status": "finished", "runs": len(read(root / "schedule.json"))}
