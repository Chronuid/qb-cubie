"""Discover packages and explicitly execute independent reference checks."""

import shutil
import tempfile
import time
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.contracts.packages import load_package
from qb_cubie.benchmarks.execution._episode import _export
from qb_cubie.benchmarks.execution._process import ExecutionError
from qb_cubie.benchmarks.execution._pytest import criteria, observe


def list_package(path: str | Path) -> dict:
    """List public scenarios and taxonomy without executing package code."""
    package = load_package(path)
    return {**package, **{field: sorted({value for s in package["scenarios"] for value in s[field]})
                          for field in ("types", "tags")}}


def validate_package(path: str | Path, check_references: bool = False) -> dict:
    """Validate structure and optionally test private project references."""
    root = Path(path).resolve()
    package = load_package(root)
    v.require(type(check_references) is bool, "check_references", "expected boolean")
    scenarios = [_validate(root, s, check_references) for s in package["scenarios"]]
    return {"schema_version": 1, "namespace": package["namespace"], "valid": True,
            "references_checked": check_references, "scenarios": scenarios}


def _validate(root, scenario, execute):
    """Report reference provenance independently of executable validation."""
    base = (root / scenario["manifest"]).parent
    reference = v.read_data(base / scenario["evaluator"]["reference"])
    result = {"scenario_id": scenario["qualified_id"], "validation_status": reference["validation_status"],
              "reference_passed": None, "mutants": [], "reference_check": "structural_only"}
    if execute and scenario["benchmark"] == "developer_agent":
        result.update(_project(base, scenario, reference))
    elif execute:
        result.update(_review(base, scenario, reference))
    return result


def _review(base, scenario, reference):
    """Execute objective review checks without promoting human admission."""
    if "maintainability" in scenario["types"]:
        return {"reference_check": "manual_required"}
    if "acceptance_tests" not in reference:
        return {}
    with tempfile.TemporaryDirectory(prefix="cubie-review-reference-") as directory:
        root = Path(directory)
        workspace = root / "submitted"
        workspace.mkdir()
        _export({"base": base, "scenario": scenario}, workspace)
        actual = _observe(root, workspace, base / reference["acceptance_tests"], scenario, business_only=True)
    v.require(actual == reference["criterion_results"], scenario["id"], "review reference differs from executable evidence")
    return {"reference_passed": True, "reference_check": "executed"}


def _project(base, scenario, reference):
    """Require passing reference output and targeted, detectable mutants."""
    solution = _check(base, scenario, reference, reference["solution"])
    v.require(all(value == "pass" for value in solution.values()), scenario["id"], "reference solution failed")
    mutants = []
    for name, material in reference["mutants"].items():
        judgments = _check(base, scenario, reference, material)
        detected = all(judgments[key] == "fail" for key in reference["mutant_criteria"][name])
        v.require(detected, scenario["id"], f"mutant {name} did not fail its declared criteria")
        mutants.append({"id": name, "detected": True, "criterion_results": judgments})
    return {"reference_passed": True, "mutants": mutants, "reference_check": "executed"}


def _check(base, scenario, reference, module):
    """Run one reference module in a fresh evaluator directory."""
    tests = v.contained(base, reference.get("acceptance_tests"), "acceptance_tests")
    target = v.relative(reference.get("submission_module"), "submission_module")
    with tempfile.TemporaryDirectory(prefix="cubie-reference-") as directory:
        root = Path(directory)
        workspace = root / "submitted"
        workspace.mkdir()
        _export({"base": base, "scenario": scenario}, workspace)
        (workspace / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(v.contained(base, module, "reference"), workspace / target)
        return _observe(root, workspace, tests, scenario)


def _observe(root, workspace, tests, scenario, *, business_only=False):
    """Classify reference execution errors rather than accepting broken tests."""
    acceptance = root / "test_acceptance.py"
    shutil.copyfile(tests, acceptance)
    context = {"deadline": time.monotonic() + 30, "tool_calls": 0, "run": {"budgets": {"tool_calls": 1}}}
    try:
        observed = observe(context, workspace, acceptance, root / "observation.json")
    except (ExecutionError, OSError) as error:
        raise ValueError(f"{scenario['id']}: reference execution: {error}") from error
    _executed(observed, scenario["id"], business_only=business_only)
    return criteria(observed, scenario["criteria"])


def _executed(observed, identifier, *, business_only=False):
    """Accept test-body failures while excluding collection, fixture and skip errors."""
    failures = [failure for case in observed["cases"] for failure in case["failures"]]
    v.require(bool(observed["cases"]) and observed["returncode"] in {0, 1}
              and all(failure["kind"] == "failure" for failure in failures),
              identifier, "reference tests did not execute normally")
    v.require(not business_only or observed["test_outcome"] in {"passed", "assertion_failure"},
              identifier, "review reference requires business failures, not execution errors")
