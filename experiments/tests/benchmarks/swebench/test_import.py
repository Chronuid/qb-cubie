"""Require relocatable packages, hidden references and transactional imports."""

import shutil

import pytest

from ..contracts import accepted, rejected
from .conftest import exported_cases, git, read_json, rewrite_snapshot, tree


def export(importer, config, destination):
    return accepted(importer, config, destination, expected=lambda value: (
        value["package"] == str(destination.resolve()) and value["status"] == "complete"
        and value["imported"] == config["instance_ids"] and value["skipped"] == []))


def test_import_exports_the_base_commit_without_solution_or_future_history(config, snapshot, importer, public_api, tmp_path):
    root = tmp_path / "package"
    before = git(snapshot["repo"], "rev-parse", "HEAD")
    export(importer, config, root)
    _, cases = exported_cases(public_api, root)
    assert len(cases) == 2
    for case, directory in cases:
        visible = directory / case["visible"]
        assert (visible / "calc.py").read_text() == "def total(values):\n    return 0\n"
        assert (visible / "setup.py").is_file()  # Included as data, never imported.
        assert not list(visible.rglob(".git")) and not (visible / "test_total.py").exists()
        payload = b"\n".join(tree(visible).values()) + (directory / case["task"]).read_bytes()
        assert all(token not in payload for token in (
            b"GOLD_SOLUTION_SENTINEL", b"PRIVATE_TEST_SENTINEL", b"OPTIONAL_HINT_SENTINEL"))
    assert git(snapshot["repo"], "rev-parse", "HEAD") == before


def test_manifest_preserves_provenance_publication_and_repository_groups(config, importer, public_api, tmp_path):
    root = tmp_path / "package"
    export(importer, config, root)
    package, cases = exported_cases(public_api, root)
    catalog = read_json(root / package["dataset"])
    assert catalog["publication_status"] == "public"
    assert len({case["group_id"] for case, _ in cases}) == 1
    assert len({catalog["cases"][case["id"]]["design_id"] for case, _ in cases}) == 1
    for case, _ in cases:
        record = catalog["cases"][case["id"]]
        assert case["split"] == "development" and record["potentially_known"] is True
        assert record["source"]["split"] == "test" and record["source"]["revision"] == config["revision"]
        assert record["source"]["instance_id"] == case["id"]
        assert record["source"]["dataset_name"] == config["dataset_name"]
        assert record["source"]["repository_license"] == "MIT" and record["source"]["dataset_license"] == "MIT"
        assert record["origin"] and record["license"] and record["domain"]


def test_issue_repair_never_claims_tdd_or_review_findings(config, importer, public_api, tmp_path):
    root = tmp_path / "package"
    export(importer, config, root)
    _, cases = exported_cases(public_api, root)
    for case, directory in cases:
        assert case["benchmark"] == "developer_agent" and case["requires"] == []
        assert case["process_profile"] == "issue_resolution"
        assert case["evaluator"]["kind"] == "external.swebench_v1"
        reference = read_json(directory / case["evaluator"]["reference"])
        assert reference["validation_status"] == "unvalidated" and reference["human_reviews"] == []
        assert "findings" not in reference and "mutants" not in reference
        assert reference["FAIL_TO_PASS"] == ["test_total.py::test_total"]
        assert reference["PASS_TO_PASS"] == ["test_existing.py::test_empty"]
        assert "GOLD_SOLUTION_SENTINEL" in (directory / reference["gold_patch"]).read_text()
        assert "PRIVATE_TEST_SENTINEL" in (directory / reference["test_patch"]).read_text()
        task = (directory / case["task"]).read_text()
        assert "Größe" in task and "OPTIONAL_HINT_SENTINEL" not in task


def test_optional_hints_are_an_explicit_versioned_condition(config, importer, public_api, tmp_path):
    plain = export(importer, config, tmp_path / "plain")
    config["include_hints"] = True
    hinted = export(importer, config, tmp_path / "hinted")
    assert plain["plan_sha256"] != hinted["plan_sha256"]
    _, cases = exported_cases(public_api, tmp_path / "hinted")
    assert all("OPTIONAL_HINT_SENTINEL" in (directory / case["task"]).read_text() for case, directory in cases)


def test_export_is_relocatable_and_contains_no_host_paths(config, importer, public_api, tmp_path):
    root = tmp_path / "original"
    export(importer, config, root)
    assert all(str(tmp_path).encode() not in content for content in tree(root).values())
    moved = tmp_path / "different parent" / "moved package"
    moved.parent.mkdir()
    shutil.move(root, moved)
    accepted(public_api("load_package"), moved, expected=lambda value: len(value["scenarios"]) == 2)


def test_same_inputs_produce_identical_package_bytes(config, importer, tmp_path):
    export(importer, config, tmp_path / "first")
    export(importer, config, tmp_path / "second")
    assert tree(tmp_path / "first") == tree(tmp_path / "second")


def test_existing_destination_is_never_overwritten(config, importer, tmp_path):
    root = tmp_path / "authored"
    root.mkdir()
    (root / "notes.txt").write_text("keep authored data", encoding="utf-8")
    before = tree(root)
    rejected(importer, config, root, match="exist|overwrite|destination")
    assert tree(root) == before


def test_unavailable_base_commit_leaves_no_partial_package(config, snapshot, importer, tmp_path):
    snapshot["records"][1]["base_commit"] = "f" * 40
    rewrite_snapshot(snapshot)
    destination = tmp_path / "failed package"
    rejected(importer, config, destination, match="demo__calc-2.*(commit|checkout)|commit.*demo__calc-2")
    assert not destination.exists()


def test_explicit_skip_policy_reports_all_exclusions_without_fabricating_success(config, snapshot, importer, tmp_path):
    snapshot["records"][1]["base_commit"] = "f" * 40
    rewrite_snapshot(snapshot)
    config["on_error"] = "skip"
    result = accepted(importer, config, tmp_path / "partial", expected=lambda value: value["status"] == "partial")
    assert result["imported"] == ["demo__calc-1"]
    assert len(result["skipped"]) == 1 and result["skipped"][0]["instance_id"] == "demo__calc-2"
    assert result["skipped"][0]["stage"] == "checkout" and result["skipped"][0]["reason"]


def test_skip_policy_still_rejects_an_empty_package(config, snapshot, importer, tmp_path):
    for row in snapshot["records"]:
        row["base_commit"] = "f" * 40
    rewrite_snapshot(snapshot)
    config["on_error"] = "skip"
    destination = tmp_path / "empty"
    rejected(importer, config, destination, match="empty|no.*scenario|all.*failed")
    assert not destination.exists()


@pytest.mark.parametrize("attack", ["repository-path", "symlink", "submodule"])
def test_source_cannot_escape_the_cache_or_visible_tree(config, snapshot, importer, tmp_path, attack):
    if attack == "repository-path":
        snapshot["source"]["repositories"]["demo/calc"] = "../../outside"
    else:
        repo = snapshot["repo"]
        git(repo, "checkout", "--detach", snapshot["base"])
        if attack == "symlink":
            (repo / "escape").symlink_to("../../outside-secret")
            git(repo, "add", "escape")
        else:
            git(repo, "update-index", "--add", "--cacheinfo", "160000," + snapshot["base"] + ",dependency")
        git(repo, "commit", "-m", "Synthetic unsafe tree")
        for row in snapshot["records"]:
            row["base_commit"] = git(repo, "rev-parse", "HEAD")
    rewrite_snapshot(snapshot)
    rejected(importer, config, tmp_path / "unsafe", match="path|escape|symlink|submodule|gitlink")
    assert not (tmp_path / "unsafe").exists()


def test_modified_reference_invalidates_package_integrity(config, importer, public_api, tmp_path):
    root = tmp_path / "package"
    export(importer, config, root)
    _, cases = exported_cases(public_api, root)
    case, directory = cases[0]
    reference = read_json(directory / case["evaluator"]["reference"])
    with (directory / reference["gold_patch"]).open("a", encoding="utf-8") as stream:
        stream.write("\nchanged after import\n")
    rejected(public_api("load_package"), root, match="hash|integrity|sha256")


def test_source_evaluation_scripts_and_unknown_fields_stay_private(config, snapshot, importer, public_api, tmp_path):
    snapshot["records"][0].update(eval_script="PRIVATE_EVAL_SCRIPT_SENTINEL",
                                   future_metadata="PRIVATE_UNKNOWN_FIELD_SENTINEL")
    rewrite_snapshot(snapshot)
    root = tmp_path / "package"
    export(importer, config, root)
    _, cases = exported_cases(public_api, root)
    for case, directory in cases:
        payload = b"\n".join(tree(directory / case["visible"]).values()) + (directory / case["task"]).read_bytes()
        assert b"PRIVATE_EVAL_SCRIPT_SENTINEL" not in payload and b"PRIVATE_UNKNOWN_FIELD_SENTINEL" not in payload
