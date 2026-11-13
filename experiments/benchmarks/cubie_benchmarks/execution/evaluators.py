"""Evaluate archived submissions independently of adapter status claims."""

import shutil

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.contracts.protocols import (
    validate_evaluation,
    validate_evaluator_request,
)
from cubie_benchmarks.execution._process import ExecutionError
from cubie_benchmarks.execution._pytest import criteria, observe
from cubie_benchmarks.reporting._files import (
    copy_tree,
    digest,
    inventory,
    write_json,
)


def project(context):
    """Evaluate project artifacts with independent acceptance tests."""
    directory = context["directory"] / "evaluation"
    directory.mkdir()
    submitted = copy_tree(context["workspace"], directory / "submitted")
    request = _request(context, submitted, inventory(submitted))
    test = directory / "test_acceptance.py"
    shutil.copy2(context["base"] / context["reference"]["acceptance_tests"], test)
    observed = observe(context, submitted, test, directory / "observation.json")
    write_json(directory / "observation.json", observed)
    judgments = criteria(observed, context["scenario"]["criteria"])
    return _evaluation(context, request, judgments, [], [directory / "observation.json", directory / "observation.xml"])


def review(context, submission):
    """Evaluate review decisions and source-bound findings against the reference."""
    _artifacts(context, submission)
    payload = v.read_data(context["workspace"] / "review.json")
    v.decisions(payload.get("criterion_results"), context["scenario"]["criteria"])
    _sources(context, payload)
    metrics, correct = _review_score(context["reference"], payload)
    record = write_json(context["directory"] / "review-evaluation.json", {"reference": context["reference"],
                        "response": payload, "metrics": metrics, "quality_passed": correct})
    request = _request(context, context["workspace"], submission["artifact_hashes"])
    result = _evaluation(context, request, payload["criterion_results"], metrics, [record])
    return {**result, "quality_passed": correct}


def _artifacts(context, submission):
    """Verify review artifact existence, run binding and content hashes."""
    if submission["run_id"] != context["run"]["run_id"]:
        raise ExecutionError("invalid_output", "Submission belongs to a foreign run_id")
    for name in submission["artifacts"]:
        path = v.contained(context["workspace"], name, "artifacts")
        if digest(path) != submission["artifact_hashes"].get(name):
            raise ExecutionError("invalid_output", "Submitted artifact hash does not match archived bytes")


def _sources(context, payload):
    """Verify complete review source evidence against the original context."""
    sources = v.strings(payload.get("sources"), "sources", nonempty=True)
    v.require(set(sources) == set(context["source_files"]), "sources", "review needs the full visible source context")
    for name in sources:
        path = v.contained(context["workspace"], name, "sources")
        v.require(digest(path) == context["source_files"][name], "sources", "review context changed")


def _request(context, submitted, hashes):
    """Bind evaluator inputs to the submitted and reference workspaces."""
    request = {"schema_version": 1, "run_id": context["run"]["run_id"],
               "scenario_id": context["run"]["scenario_id"], "evaluator_id": context["scenario"]["evaluator"]["kind"],
               "evaluator_version": "1.0.0", "submitted_workspace": str(submitted),
               "reference_workspace": str(context["base"]), "criteria": context["scenario"]["criteria"],
               "artifact_hashes": hashes}
    return validate_evaluator_request(request)


def _evaluation(context, request, judgments, metrics, evidence):
    """Validate and archive independent criterion judgments."""
    value = {"schema_version": 1, "run_id": request["run_id"], "scenario_id": request["scenario_id"],
             "status": "completed", "evaluation_status": "complete", "criterion_results": judgments,
             "metrics": metrics, "evidence": [p.relative_to(context["root"]).as_posix() for p in evidence]}
    validate_evaluation(value, request)
    write_json(context["directory"] / "evaluator-request.json", request)
    return {**value, "quality_passed": all(value == "pass" for value in judgments.values())}


def _review_score(reference, payload):
    """Compare structured findings and decisions with the reference judgment."""
    expected = {_finding(f) for f in reference["findings"]}
    actual = {_finding(f) for f in payload.get("findings", [])}
    hits = len(expected & actual)
    precision = hits / len(actual) if actual else None
    recall = hits / len(expected) if expected else None
    metrics = [_metric("precision", precision), _metric("recall", recall)]
    correct = payload["criterion_results"] == reference["criterion_results"] and expected == actual
    return metrics, correct


def _finding(finding):
    """Normalize the identifying fields of one structured finding."""
    v.mapping(finding, "finding")
    return tuple(v.text(finding.get(key), "finding." + key)
                 for key in ("criterion_id", "path", "symbol", "mechanism", "impact"))


def _metric(name, value):
    """Describe a per-scenario review quality metric."""
    return {"name": name, "value": value, "unit": "ratio", "direction": "higher", "aggregation": "per_scenario"}
