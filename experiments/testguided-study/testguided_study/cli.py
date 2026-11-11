"""Provide explicit offline preparation and opt-in local inference commands."""

import argparse
import json
import sys
from pathlib import Path

from .artifacts import ROOT, freeze


def positive(value):
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    launch = commands.add_parser("start", help="Prepare and start a complete local study with live monitoring")
    launch.add_argument("--mode", choices=("smoke", "pilot", "short", "long"), default="pilot")
    launch.add_argument("--config", type=Path)
    launch.add_argument("--tasks", type=positive)
    launch.add_argument("--seeds", type=int, nargs="+")
    launch.add_argument("--task-type", action="append")
    launch.add_argument("--agent-seconds", type=positive)
    launch.add_argument("--model-calls", type=positive)
    launch.add_argument("--regression-tests", type=positive, default=8)
    launch.add_argument("--catalog", type=Path, default=ROOT / "candidate-catalog.json")
    launch.add_argument("--source", type=Path)
    launch.add_argument("--snapshots", type=Path)
    launch.add_argument("--tasks-manifest", type=Path)
    launch.add_argument("--output", type=Path)
    launch.add_argument("--monitor", choices=("web", "terminal", "none"), default="web")
    launch.add_argument("--port", type=int, default=0)
    launch.add_argument("--keep-monitor", action="store_true")
    launch.add_argument("--prepare-only", action="store_true")
    launch.add_argument("--no-build-images", action="store_true")
    status = commands.add_parser("status", help="Read current study state in a separate terminal")
    status.add_argument("study", type=Path)
    status.add_argument("--watch", action="store_true")
    status.add_argument("--json", action="store_true")
    status.add_argument("--view", choices=("context", "action", "result", "response"))
    monitor = commands.add_parser("monitor", help="Open a read-only web monitor for an existing study")
    monitor.add_argument("study", type=Path)
    monitor.add_argument("--port", type=int, default=0)
    plan = commands.add_parser("freeze", help="Freeze selected tasks, prompts and paired schedule without network")
    plan.add_argument("config", type=Path)
    plan.add_argument("destination", type=Path)
    smoke = commands.add_parser("make-smoke", help="Generate a synthetic infrastructure task, not study evidence")
    smoke.add_argument("destination", type=Path)
    planning = commands.add_parser("plan", help="Select tasks and estimate paired runtime without inference")
    planning.add_argument("config", type=Path)
    planning.add_argument("--catalog", type=Path, help="Plan reviewed candidates before preparing task snapshots")
    planning.add_argument("--output", type=Path)
    for name in ("preflight", "run", "report"):
        sub = commands.add_parser(name)
        sub.add_argument("study", type=Path)
    argv = sys.argv[1:]
    if not argv or (argv[0].startswith("-") and argv[0] not in {"-h", "--help"}):
        argv = ["start", *argv]
    args = parser.parse_args(argv)
    try:
        if hasattr(args, "port") and not 0 <= args.port <= 65535:
            raise ValueError("port must be in [0, 65535]")
        if args.command == "start":
            from .launch import start
            result = start(args)
        elif args.command == "status":
            from .status import display
            display(args)
            return 0
        elif args.command == "monitor":
            from .status import serve
            result = serve(args)
        elif args.command == "freeze":
            result = freeze(args.config, args.destination)
        elif args.command == "plan":
            from .artifacts import write
            from .planning import plan
            result = plan(args.config, args.catalog)
            if args.output:
                if args.output.exists():
                    raise ValueError("Plan output already exists; refusing to overwrite")
                write(args.output, result)
        elif args.command == "make-smoke":
            from .smoke import generate
            result = generate(args.destination)
        elif args.command == "report":
            from .report import summarize
            result = summarize(args.study)
        else:
            from .execution import preflight, run
            result = preflight(args.study) if args.command == "preflight" else run(args.study)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, ImportError, RuntimeError) as error:
        print(f"study: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("study: interrupted; evidence was retained", file=sys.stderr)
        return 130
