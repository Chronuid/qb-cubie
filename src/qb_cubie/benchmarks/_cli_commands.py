"""Dispatch the public custom-agent authoring and comparison commands."""

from qb_cubie.benchmarks.adapters.process import validate_agent
from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.contracts.validation import list_package, validate_package
from qb_cubie.benchmarks.reporting._pilot_text import render
from qb_cubie.benchmarks.reporting.comparison import compare_runs
from qb_cubie.benchmarks.reporting.pilot import summarize_pilot
from qb_cubie.benchmarks.scaffolding.base import init_base_package
from qb_cubie.benchmarks.scaffolding.custom import (
    init_agent,
    init_example,
    init_scenario,
    init_suite,
)
from qb_cubie.benchmarks.scaffolding.ollama import init_ollama
from qb_cubie.benchmarks.scaffolding.templates import init_smoke_suite


def dispatch(args):
    """Execute a command using the same public API as Python clients."""
    return _actions(args)[args.command](), 0


def _actions(args):
    """Bind authoring and reporting arguments without executing a selected action."""
    return {"init-agent": lambda: init_agent(args.path),
               "init-ollama": lambda: init_ollama(args.path, endpoint=args.endpoint, model=args.model),
               "validate-agent": lambda: validate_agent(args.path),
               "init-scenario": lambda: init_scenario(args.path, args.benchmark),
               "init-example": lambda: init_example(args.path),
               "init-base": lambda: init_base_package(args.path),
               "guide": guide,
               "init-suite": lambda: _suite(args),
               "validate": lambda: validate_package(args.path, args.check_references),
               "list": lambda: list_package(args.package),
               "summarize-pilot": lambda: summarize_pilot(args.archives),
               "compare": lambda: compare_runs(args.before, args.after, before_agent=args.before_agent, after_agent=args.after_agent)}


def guide():
    """Return the tutorial bundled in the installed distribution."""
    from importlib.resources import files
    return {"guide": files("qb_cubie.benchmarks").joinpath("data/GUIDE_Benchmark-Custom.md").read_text(encoding="utf-8")}


def _suite(args):
    """Require an explicit fake choice or a complete external configuration."""
    if args.fake:
        v.require(args.agent is None and args.package is None, "init-suite", "--fake cannot combine with --agent/--package")
        return init_smoke_suite(args.path)
    v.require(args.agent is not None and args.package is not None, "init-suite", "provide --agent and --package or --fake")
    return init_suite(args.path, args.agent, args.package)


def text(result):
    """Render comparison scope, discovery and validation in plain language."""
    if "guide" in result:
        return result["guide"]
    if "groups" in result:
        return render(result)
    if "scope" in result:
        return "\n".join([f"Comparison: {result['scope']}", *result["warnings"],
                          *[_comparison_pair(p) for p in result["pairs"]]])
    if "scenarios" in result:
        return "\n".join([f"Package: {result['namespace']}",
                          *[s.get("qualified_id", s.get("scenario_id", "")) for s in result["scenarios"]]])
    return "\n".join(f"{key}: {value}" for key, value in result.items())


def _comparison_pair(pair):
    """Show both attempt outcomes alongside numeric differences."""
    return (f"{pair['scenario_id']} ({pair['condition']}, repetition {pair['repetition']}):\n"
            f"  before: {_attempt(pair['before'])}\n"
            f"  after: {_attempt(pair['after'])}\n"
            f"  metric_deltas: {pair['metric_deltas']}")


def _attempt(run):
    """Keep infrastructure, evaluation, quality and process outcomes distinct."""
    return (f"agent={run['agent_id']}; status={run['status']}; "
            f"evaluation_status={run['evaluation_status']}; quality_passed={run['quality_passed']}; "
            f"process_passed={run.get('process_passed')}")
