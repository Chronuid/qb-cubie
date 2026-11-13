"""Validate independent reference metadata and its declared material."""

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.contracts.admission import validate_admission


def validate_reference(root, scenario, reference):
    """Validate reference coverage without executing reference programs."""
    if scenario["evaluator"]["kind"] == "external.swebench_v1":
        _swebench(root, scenario, reference)
        return
    v.decisions(reference.get("criterion_results"), scenario["criteria"])
    v.choice(reference.get("validation_status"), {"author_checked", "independently_checked"}, "validation_status")
    validate_admission(root, scenario, reference)
    if scenario["benchmark"] == "review_agent":
        _review(root, scenario, reference)
    else:
        _project(root, scenario, reference)


def _swebench(root, scenario, reference):
    """Keep external patch references separate from builtin module references."""
    from cubie_benchmarks.swebench._common import commit, normalize
    v.choice(reference.get("validation_status"), {"unvalidated"}, "validation_status")
    v.require(reference.get("human_reviews") == [], "human_reviews", "imported references are unreviewed")
    for field in ("gold_patch", "test_patch", "raw_record"):
        _private(root, scenario, reference.get(field), field)
    record = normalize(v.read_data(root / reference["raw_record"])["record"])
    v.require(record["instance_id"] == scenario["id"], "instance_id", "reference differs from scenario")
    v.require(reference.get("source") == scenario.get("source"), "source", "reference provenance differs from scenario")
    _patch_record(root, reference, record)
    commit(reference.get("harness_revision"), "harness_revision")


def _review(root, scenario, reference):
    """Validate finding coverage for all failing reference criteria."""
    findings = reference.get("findings")
    v.require(type(findings) is list, "findings", "expected a list")
    failed = {key for key, value in reference["criterion_results"].items() if value == "fail"}
    covered = set()
    for finding in findings:
        v.mapping(finding, "findings")
        v.choice(finding.get("criterion_id"), failed, "criterion_id")
        _finding(root, scenario, finding)
        covered.add(finding["criterion_id"])
    v.require(covered == failed, "findings", f"missing failure references: {sorted(failed - covered)}")
    _review_material(root, scenario, reference)


def _review_material(root, scenario, reference):
    """Check optional executable evidence and required visible context."""
    if "acceptance_tests" in reference:
        _private(root, scenario, reference["acceptance_tests"], "acceptance_tests")
    if "required_context" in reference:
        paths = v.strings(reference["required_context"], "required_context", nonempty=True)
        for path in paths:
            v.contained(root / scenario["visible"], path, "required_context")
        v.text(reference.get("context_reason"), "context_reason")


def _finding(root, scenario, finding):
    """Validate a reference finding and its executable counterexample."""
    visible = (root / scenario["visible"]).resolve()
    v.contained(visible, finding.get("path"), "findings.path")
    for field in ("symbol", "mechanism", "impact"):
        v.text(finding.get(field), f"findings.{field}")
    v.strings(finding.get("allowed_alternatives", []), "allowed_alternatives")
    if "counterexample" in finding:
        example = v.mapping(finding["counterexample"], "counterexample")
        v.require("expected" in example and "actual" in example, "counterexample", "expected and actual required")
        v.require(example["expected"] != example["actual"], "counterexample", "must distinguish the defect")


def _project(root, scenario, reference):
    """Validate project solutions and mutant criterion coverage."""
    _private(root, scenario, reference.get("solution"), "solution")
    _execution_material(root, scenario, reference)
    mutants = v.mapping(reference.get("mutants"), "mutants")
    criteria = v.mapping(reference.get("mutant_criteria"), "mutant_criteria")
    v.require(bool(mutants) and mutants.keys() == criteria.keys(), "mutant_criteria", "each mutant needs criterion coverage")
    for name, material in mutants.items():
        _private(root, scenario, material, f"mutants.{name}")
        keys = v.strings(criteria[name], f"mutant_criteria.{name}", nonempty=True)
        v.require(set(keys) <= set(scenario["criteria"]), "mutant_criteria", f"unknown criteria in {name}")


def _private(root, scenario, material, field):
    """Validate reference material outside the visible source tree."""
    path = v.contained(root, material, field)
    visible = (root / scenario["visible"]).resolve()
    v.require(not path.is_relative_to(visible), field, "reference material must stay outside visible tree")


def _execution_material(root, scenario, reference):
    """Validate private test templates and the submission module path."""
    for field in ("acceptance_tests", "agent_tests", "pytest_agent_tests"):
        if field in reference:
            _private(root, scenario, reference[field], field)
    if "submission_module" in reference:
        v.relative(reference["submission_module"], "submission_module")
    if "expected_red_exception" in reference:
        _red_exception(root, scenario, reference)


def _patch_record(root, reference, record):
    """Check private patch content and test-list provenance."""
    for field, private in (("patch", "gold_patch"), ("test_patch", "test_patch")):
        v.require((root / reference[private]).read_text(encoding="utf-8") == record[field], private, "patch differs from source record")
    for field in ("FAIL_TO_PASS", "PASS_TO_PASS"):
        v.require(reference.get(field) == record[field], field, "reference differs from record")


def _red_exception(root, scenario, reference):
    """Validate a declared production-stub exception."""
    expected = v.mapping(reference["expected_red_exception"], "expected_red_exception")
    v.require(set(expected) == {"module", "message"}, "expected_red_exception", "module and message required")
    v.require(expected["module"] == reference.get("submission_module"),
              "expected_red_exception.module", "must identify the production submission module")
    visible = root / scenario["visible"]
    module = expected["module"] if (visible / expected["module"]).is_file() else expected["module"] + ".txt"
    v.contained(visible, module, "expected_red_exception.module")
    v.text(expected["message"], "expected_red_exception.message")
