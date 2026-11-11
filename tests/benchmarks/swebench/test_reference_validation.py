"""Check baseline/gold grading through an explicit synthetic executor boundary."""

import hashlib
import json
from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from .conftest import read_json, tree
from .test_import import export


def executor_fixture(damage=None):
    calls = []

    def execute(request):
        calls.append(request)
        tests = {name: "pass" for name in request["FAIL_TO_PASS"] + request["PASS_TO_PASS"]}
        if request["stage"] == "base":
            tests.update({name: "fail" for name in request["FAIL_TO_PASS"]})
        status = "completed"
        if damage == "base-already-green" and request["stage"] == "base":
            tests.update({name: "pass" for name in request["FAIL_TO_PASS"]})
        if damage == "gold-fails" and request["stage"] == "gold":
            tests[request["FAIL_TO_PASS"][0]] = "fail"
        if damage == "regression":
            tests[request["PASS_TO_PASS"][0]] = "fail"
        if damage == "missing-test":
            del tests[request["FAIL_TO_PASS"][0]]
        if damage == "skipped-test":
            tests[request["FAIL_TO_PASS"][0]] = "skip"
        if damage in {"timeout", "setup_error", "patch_error", "collection_error"}:
            status = damage
        output = Path(request["output_dir"])
        output.mkdir(parents=True, exist_ok=True)
        log = output / "tests.json"
        log.write_text(json.dumps({"status": status, "tests": tests}), encoding="utf-8")
        result = {"instance_id": request["instance_id"], "run_id": request["run_id"],
                  "request_sha256": request["request_sha256"], "status": status, "tests": tests,
                  "image_digest": "sha256:" + "d" * 64,
                  "artifacts": [{"path": "tests.json", "sha256": hashlib.sha256(log.read_bytes()).hexdigest()}]}
        if damage == "wrong-instance":
            result["instance_id"] = "other__case-999"
        if damage == "stale-result":
            result["request_sha256"] = "0" * 64
        if damage == "missing-artifact":
            log.unlink()
        if damage == "tampered-artifact":
            log.write_text("changed after execution", encoding="utf-8")
        if damage == "artifact-escape":
            result["artifacts"][0]["path"] = "../../outside.json"
        if damage == "unpinned-image":
            result["image_digest"] = "image:latest"
        return result

    return execute, calls


def validate(public_api, root, executor):
    return public_api("validate_swebench_references")(root, executor=executor)


def test_baseline_and_gold_are_checked_separately_with_bound_evidence(config, importer, public_api, tmp_path):
    root = tmp_path / "package"
    export(importer, config, root)
    execute, calls = executor_fixture()
    result = accepted(lambda: validate(public_api, root, execute), expected=lambda value: value["valid"] is True)
    assert len(calls) == 4 and len(result["scenarios"]) == 2
    assert {(call["instance_id"], call["stage"]) for call in calls} == {
        (instance, stage) for instance in config["instance_ids"] for stage in ("base", "gold")}
    assert len({call["run_id"] for call in calls}) == 4
    assert all(call["harness_revision"] == config["harness_revision"] and call["network"] is False for call in calls)
    assert all(("GOLD_SOLUTION_SENTINEL" in call["patch"]) is (call["stage"] == "gold") for call in calls)
    assert all("PRIVATE_TEST_SENTINEL" in call["test_patch"] for call in calls)
    assert all(row["reference_passed"] is True and row["validation_status"] == "author_checked"
               and row["human_reviews"] == [] and row["evidence"] for row in result["scenarios"])


@pytest.mark.parametrize("damage", [
    "base-already-green", "gold-fails", "regression", "missing-test", "skipped-test",
    "timeout", "setup_error", "patch_error", "collection_error", "wrong-instance",
    "stale-result", "missing-artifact", "tampered-artifact", "artifact-escape", "unpinned-image",
])
def test_invalid_references_or_infrastructure_never_receive_quality_credit(
        config, importer, public_api, tmp_path, damage):
    root = tmp_path / "package"
    export(importer, config, root)
    execute, _ = executor_fixture(damage)
    result = accepted(lambda: validate(public_api, root, execute), expected=lambda value: value["valid"] is False)
    assert result["scenarios"]
    for row in result["scenarios"]:
        assert row["reference_passed"] is False and row["reason"]
        assert row["validation_status"] == "unvalidated"


def test_revalidation_uses_new_attempt_ids_and_preserves_original_package(config, importer, public_api, tmp_path):
    root = tmp_path / "package"
    export(importer, config, root)
    before = tree(root)
    execute, calls = executor_fixture()
    accepted(lambda: validate(public_api, root, execute), expected=lambda value: value["valid"] is True)
    accepted(lambda: validate(public_api, root, execute), expected=lambda value: value["valid"] is True)
    assert len(calls) == len({call["run_id"] for call in calls}) == 8
    assert tree(root) == before


def test_structural_validation_does_not_execute_references_or_promote_them(config, importer, public_api, tmp_path):
    root = tmp_path / "package"
    export(importer, config, root)
    before = tree(root)
    accepted(lambda: public_api("validate_package")(root, check_references=False),
             expected=lambda value: value["valid"] is True and value["references_checked"] is False)
    assert tree(root) == before
    assert all(read_json(path)["validation_status"] == "unvalidated" for path in root.rglob("reference.json"))


def test_missing_isolation_is_an_error_before_any_repository_code_runs(config, importer, public_api, tmp_path, monkeypatch):
    root = tmp_path / "package"
    export(importer, config, root)
    monkeypatch.setenv("PATH", "")
    rejected(lambda: public_api("validate_swebench_references")(root), match="container|isolation|executor|runtime")
