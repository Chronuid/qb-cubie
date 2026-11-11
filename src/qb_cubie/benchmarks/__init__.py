"""Experimental benchmark APIs, separate from the qb-cubie Core."""

from qb_cubie.benchmarks.adapters.process import validate_agent
from qb_cubie.benchmarks.contracts.packages import load_package
from qb_cubie.benchmarks.contracts.protocols import (
    validate_agent_event,
    validate_agent_request,
    validate_evaluation,
    validate_evaluator_request,
)
from qb_cubie.benchmarks.contracts.validation import list_package, validate_package
from qb_cubie.benchmarks.measurement.frozen import freeze_suite, run_frozen_suite
from qb_cubie.benchmarks.planning.planner import plan_suite
from qb_cubie.benchmarks.reporting.adjudication import apply_adjudication
from qb_cubie.benchmarks.reporting.comparison import compare_runs
from qb_cubie.benchmarks.reporting.gates import evaluate_gates
from qb_cubie.benchmarks.reporting.pilot import summarize_pilot
from qb_cubie.benchmarks.runner import run_suite
from qb_cubie.benchmarks.scaffolding.base import init_base_package
from qb_cubie.benchmarks.scaffolding.custom import (
    init_agent,
    init_example,
    init_scenario,
    init_suite,
)
from qb_cubie.benchmarks.scaffolding.ollama import init_ollama
from qb_cubie.benchmarks.scaffolding.templates import init_smoke_suite
from qb_cubie.benchmarks.swebench.importer import import_swebench, plan_swebench_import
from qb_cubie.benchmarks.swebench.validation import validate_swebench_references

__all__ = [
    "apply_adjudication",
    "compare_runs",
    "evaluate_gates",
    "freeze_suite",
    "import_swebench",
    "init_agent",
    "init_base_package",
    "init_example",
    "init_ollama",
    "init_scenario",
    "init_smoke_suite",
    "init_suite",
    "list_package",
    "load_package",
    "plan_suite",
    "plan_swebench_import",
    "run_frozen_suite",
    "run_suite",
    "summarize_pilot",
    "validate_agent",
    "validate_agent_event",
    "validate_agent_request",
    "validate_evaluation",
    "validate_evaluator_request",
    "validate_package",
    "validate_swebench_references",
]
