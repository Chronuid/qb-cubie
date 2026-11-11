"""Orchestrate one-command study preparation, admission, inference and monitoring."""

import copy
import json
import time
from pathlib import Path

from . import admission, corpus, execution, images
from .artifacts import ROOT, freeze, load_config, read, schedule, write
from .monitor import MonitorServer
from .planning import allowance
from .report import summarize
from .selection import configured
from .smoke import generate
from .telemetry import Observer

PROFILES = {"pilot": "pilot.toml", "short": "three-hours.toml", "long": "six-hours.toml", "smoke": "pilot.toml"}


def options(args):
    path = (args.config or ROOT / "profiles" / PROFILES[args.mode]).resolve()
    config = copy.deepcopy(load_config(path))
    config["guides"] = {mode: str(path.parent / guide) for mode, guide in config["guides"].items()}
    config["tasks"] = str(path.parent / config["tasks"])
    if "designs" in config:
        config["designs"] = {mode: str(path.parent / design) for mode, design in config["designs"].items()}
    if "campaign" in config:
        campaign_path = path.parent / config["campaign"]
        # Archive paths in campaign JSON are relative to that JSON, not the generated TOML.
        campaign_config = read(campaign_path)
        campaign_config["development_archives"] = [str((campaign_path.parent / archive).resolve())
                                                   for archive in campaign_config.get("development_archives", [])]
        config["campaign"] = campaign_config
    if args.tasks is not None:
        config.setdefault("selection", {"seed": config["order_seed"], "task_types": []})["task_count"] = args.tasks
    if args.seeds:
        config["seeds"] = args.seeds
    if args.task_type:
        config.setdefault("selection", {"seed": config["order_seed"], "task_count": 1})["task_types"] = args.task_type
    if args.agent_seconds is not None:
        config["budgets"]["wall_seconds"] = args.agent_seconds
    if args.model_calls is not None:
        config["budgets"]["model_calls"] = args.model_calls
    if args.mode == "smoke":
        if args.tasks not in (None, 1) or args.task_type or args.tasks_manifest:
            raise ValueError("The synthetic smoke has exactly one task; task/type overrides require a real-task mode")
        config["phase"] = "pilot"
        config["study_id"] = "plumbing-smoke-not-evidence-v3"
        config["selection"] = {"task_count": 1, "seed": config["order_seed"], "task_types": []}
        config["seeds"] = args.seeds or [42]
        config["budgets"]["wall_seconds"] = args.agent_seconds or 180
        config["budgets"]["model_calls"] = args.model_calls or 12
    return config


def toml_value(value):
    if type(value) is bool:
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def save_config(path, config):
    config = copy.deepcopy(config)
    if isinstance(config.get("campaign"), dict):
        write(Path(path).with_suffix(".campaign.json"), config["campaign"])
        config["campaign"] = str(Path(path).with_suffix(".campaign.json").resolve())
    lines = [f"{key} = {toml_value(value)}" for key, value in config.items() if not isinstance(value, dict)]
    for key, value in config.items():
        if isinstance(value, dict):
            lines.extend(["", f"[{key}]", *(f"{name} = {toml_value(item)}" for name, item in value.items())])
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    load_config(path)


def start(args):
    config = options(args)
    root = (args.output or ROOT / "runs" / time.strftime("%Y%m%d-%H%M%S")).resolve()
    root.mkdir(parents=True, exist_ok=False)
    observer = Observer(root, terminal=args.monitor != "none")
    observer.emit("starting", f"Studie starten · Modus {args.mode}", study_id=config["study_id"], phase="preparation")
    server = None
    print(f"Studienarchiv: {root}", flush=True)
    try:
        if args.monitor == "web":
            server = MonitorServer(root, args.port)
            print(f"Live-Monitor: {server.start()}", flush=True)
        save_config(root / "configured.toml", config)
        write(root / "launch.json", {key: str(value) if isinstance(value, Path) else value
                                      for key, value in vars(args).items()})
        prepared = root / "prepared"
        if args.mode == "smoke":
            generate(prepared)
            observer.bind(root / "frozen", config, schedule(read(prepared / "tasks.json"), config["seeds"], config["order_seed"]))
        elif args.tasks_manifest:
            config["tasks"] = str(args.tasks_manifest.resolve())
            selected = configured(read(args.tasks_manifest), config)
            observer.bind(root / "frozen", config, schedule(selected, config["seeds"], config["order_seed"]))
        else:
            catalog = read(args.catalog)
            eligible = [task for task in catalog["tasks"] if task["split"] in ({"pilot", "development"} if config["phase"] == "development" else {config["phase"]}) and task["eligible"]]
            selected = configured(eligible, config)
            observer.bind(root / "frozen", config, schedule(selected, config["seeds"], config["order_seed"]))
            write(root / "selection.json", {"tasks": selected, "runtime": allowance(config, len(selected))})
            source = args.source or Path(catalog["source"])
            snapshots = args.snapshots or source.parent / "snapshots"
            corpus.prepare(catalog, selected, source, snapshots, prepared, observer)
        images.ensure(config, root / "setup", observer, build=not args.no_build_images)
        if not args.tasks_manifest:
            config["tasks"] = str(prepared / "tasks.json")
            if args.mode != "smoke":
                for index, item in enumerate(read(prepared / "tasks.json")):
                    admission.admit(prepared, item, config, config["images"]["evaluator"], root / "admission" / f"{index:04d}",
                                    regressions=args.regression_tests, observer=observer)
        save_config(root / "configured.toml", config)
        frozen = root / "frozen"
        freeze(root / "configured.toml", frozen)
        observer.bind(frozen, config, read(frozen / "schedule.json"))
        execution.preflight(frozen, observer)
        if args.prepare_only:
            observer.emit("prepared", "Vorbereitet und zugelassen; keine Inferenz gestartet", state="prepared", phase="prepared")
            result = {"status": "prepared", "study": str(frozen)}
        else:
            execution.run(frozen, observer)
            result = summarize(frozen)
            write(root / "report.json", result)
        if args.keep_monitor and server:
            print("Monitor bleibt geöffnet; Strg+C schließt nur den Monitor.", flush=True)
            try:
                while True:
                    server.thread.join(1)
            except KeyboardInterrupt:
                pass
        return {"archive": str(root), **result}
    except KeyboardInterrupt:
        observer.emit("interrupted", "Studie unterbrochen; Belege bleiben erhalten", state="interrupted", phase="interrupted")
        raise
    except Exception as error:
        observer.emit("failed", str(error), state="failed", phase="failed")
        write(root / "failure.json", {"error": str(error), "type": type(error).__name__})
        raise
    finally:
        if server:
            server.close()
