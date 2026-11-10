"""Execute and preserve developer phases before independent project acceptance."""

from qb_cubie.benchmarks.adapters import fake
from qb_cubie.benchmarks.execution._messages import exchange
from qb_cubie.benchmarks.execution._pytest import observe
from qb_cubie.benchmarks.reporting._files import copy_tree, tree_hash, write_json


def develop(context):
    """Execute developer phases and assess their observed process evidence."""
    fake.tests(context)
    design = _design(context)
    path, original = fake.alter_red(context)
    red = _red(context)
    path.write_bytes(original)
    fake.alter_green(context)
    green = _phase(context, "green")
    refactor = _phase(context, "refactor")
    phases = [design, red, green, refactor]
    valid, reason = _process(phases)
    return {"phases": phases, "process_passed": valid, "process_reason": reason}


def _design(context):
    """Freeze and archive the submitted test design."""
    directory = context["directory"] / "test_design"
    directory.mkdir()
    snapshot = copy_tree(context["workspace"], directory / "snapshot")
    record = write_json(directory / "observation.json", {"phase": "test_design", "tests_frozen": True})
    return _entry(context, "test_design", "not_executed", snapshot, [record])


def _red(context):
    """Observe the red phase or record its deliberate omission."""
    if context["behavior"] != "missing_red":
        return _phase(context, "red")
    record = write_json(context["directory"] / "red.json", {"phase": "red", "observed": False})
    return _entry(context, "red", "not_observed", context["workspace"], [record])


def _phase(context, phase):
    """Execute tests against an archived phase snapshot."""
    directory = context["directory"] / phase
    directory.mkdir()
    snapshot = copy_tree(context["workspace"], directory / "snapshot")
    record = directory / "observation.json"
    observed = observe(context, snapshot, snapshot / "tests", record)
    write_json(record, observed)
    return _entry(context, phase, observed["test_outcome"], snapshot, [record, record.with_suffix(".xml")])


def _entry(context, phase, outcome, snapshot, evidence):
    """Bind a phase observation to its test-tree identity and evidence."""
    exchange(context, phase, ["tests/test_project.py", context["reference"]["submission_module"]])
    return {"phase": phase, "test_outcome": outcome, "test_tree_sha256": tree_hash(snapshot / "tests"),
            "snapshot": snapshot.relative_to(context["root"]).as_posix(),
            "evidence": [p.relative_to(context["root"]).as_posix() for p in evidence]}


def _process(phases):
    """Assess frozen tests and the observed red-to-green transition."""
    if len({p["test_tree_sha256"] for p in phases}) != 1:
        return False, "Frozen tests changed after test_design"
    if phases[1]["test_outcome"] != "assertion_failure":
        return False, "No observed assertion failure in red phase"
    if any(p["test_outcome"] != "passed" for p in phases[2:]):
        return False, "Green or refactor verification did not pass"
    return True, None
