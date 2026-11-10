"""Expose initialization, planning and offline benchmark execution."""

import argparse
import json
import sys

from qb_cubie.benchmarks import _cli_commands, _cli_parser
from qb_cubie.benchmarks.planning.planner import plan_suite
from qb_cubie.benchmarks.runner import run_suite


def main(argv=None):
    """Run the installed cubie-bench command and return its exit code."""
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        result, code = _dispatch(arguments)
        print(json.dumps(result, indent=2) if arguments.format == "json" else _text(result))
        return code
    except (ValueError, OSError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2


def _parser():
    """Define the supported benchmark commands and arguments."""
    parser = argparse.ArgumentParser(description="Benchmark agents and scenarios: initialize, plan, run, compare; see GUIDE_Benchmark-Custom.md and GUIDE_Benchmark-Contracts.md")
    commands = parser.add_subparsers(dest="command", required=True)
    _cli_parser.authoring(commands)
    _cli_parser.suites(commands)
    _cli_parser.comparison(commands)
    parser.add_argument("--format", choices=["json", "text"], default="text")
    _formats(commands)
    return parser


def _formats(commands):
    """Enable output format selection on each subcommand."""
    for command in commands.choices.values():
        command.add_argument("--format", choices=["json", "text"], default=argparse.SUPPRESS)


def _dispatch(arguments):
    """Execute the selected command and determine its exit code."""
    if arguments.command not in {"plan", "run"}:
        return _cli_commands.dispatch(arguments)
    if arguments.command == "plan":
        return plan_suite(arguments.suite), 0
    result = run_suite(arguments.suite)
    return result, 0 if all(run["status"] == "completed" for run in result["runs"]) else 3


def _text(result):
    """Render a readable plan or run summary."""
    if "output" in result:
        limits = f"Limits: {result['max_runs']} runs; {result['max_total_wall_time_seconds']} seconds\n" if "max_runs" in result else ""
        return f"Output: {result['output']}\nAttempts: {len(result['runs'])}\n" + limits + _summaries(result)
    return _cli_commands.text(result)


def _summaries(result):
    """Render each planned or executed attempt."""
    return "\n".join(_summary(run) for run in result["runs"])


def _summary(run):
    """Describe one attempt and its execution conditions."""
    if "status" in run:
        return f"{run['scenario_id']}: {run['status']}; quality_passed={run['quality_passed']}; process_passed={run.get('process_passed')}"
    return (f"{run['scenario_id']}@{run['package']['version']}: agent={run['agent_id']}, "
            f"condition={run['condition']}, repetition={run['repetition']}, evaluator={run['evaluator']['kind']}, "
            f"types={run['types']}, tags={run['tags']}, budgets={json.dumps(run['budgets'], sort_keys=True)}")
