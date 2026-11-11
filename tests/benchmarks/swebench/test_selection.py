"""Specify pinned sources, deterministic selection and strict row normalization."""

from copy import deepcopy

import pytest

from ..contracts import accepted, rejected
from .conftest import DATASET, REVISION, read_json, rewrite_snapshot, tree, write_json


def plan(public_api, config):
    return accepted(public_api("plan_swebench_import"), config,
                    expected=lambda value: value["schema_version"] == 1 and len(value["plan_sha256"]) == 64)


@pytest.mark.parametrize("dataset", ["SWE-bench/SWE-bench", DATASET, "SWE-bench/SWE-bench_Verified"])
def test_pinned_official_sources_preserve_upstream_split(config, snapshot, public_api, dataset):
    config["dataset_name"] = snapshot["source"]["dataset_name"] = dataset
    rewrite_snapshot(snapshot)
    result = plan(public_api, config)
    assert result["source"]["dataset_name"] == dataset
    assert result["source"]["revision"] == REVISION and result["source"]["split"] == "test"
    assert [row["instance_id"] for row in result["selection"]] == config["instance_ids"]
    assert all(row["base_commit"] == snapshot["base"] for row in result["selection"])


def test_plan_is_read_only_and_does_not_execute_project_code(config, snapshot, public_api):
    previous = tree(snapshot["root"])
    original = deepcopy(config)
    plan(public_api, config)
    assert tree(snapshot["root"]) == previous and config == original
    assert not (snapshot["root"].parent / "cache").exists()


def test_selection_uses_intersection_and_reports_filtered_rows(config, public_api):
    config["repositories"] = ["other/project"]
    rejected(public_api("plan_swebench_import"), config, match="selection|empty|repository")


def test_unknown_explicit_instance_is_an_error_even_with_skip_policy(config, public_api):
    config.update(instance_ids=["demo__calc-999"], on_error="skip")
    rejected(public_api("plan_swebench_import"), config, match="instance|unknown|missing")


def test_seeded_limit_is_stable_after_row_reordering(config, snapshot, public_api):
    config.update(instance_ids=[], limit=2)
    first = plan(public_api, config)
    snapshot["records"].reverse()
    rewrite_snapshot(snapshot)
    second = plan(public_api, config)
    assert [row["instance_id"] for row in first["selection"]] == [row["instance_id"] for row in second["selection"]]
    assert len(first["selection"]) == 2
    assert len(first["excluded"]) == 1 and first["excluded"][0]["reason"] == "limit"


def test_plan_identity_binds_gold_tests_harness_and_hints(config, snapshot, public_api):
    identities = {plan(public_api, config)["plan_sha256"]}
    for field in ("patch", "test_patch"):
        snapshot["records"][0][field] += "\n"
        rewrite_snapshot(snapshot)
        identities.add(plan(public_api, config)["plan_sha256"])
    config["harness_revision"] = "c" * 40
    identities.add(plan(public_api, config)["plan_sha256"])
    config["include_hints"] = True
    identities.add(plan(public_api, config)["plan_sha256"])
    assert len(identities) == 5


@pytest.mark.parametrize("field,value", [
    ("revision", "main"), ("revision", ""), ("harness_revision", "latest"),
    ("dataset_name", "untrusted/arbitrary"), ("split", "missing"),
    ("limit", 0), ("limit", True), ("seed", True), ("offline", "yes"),
    ("on_error", "ignore"), ("process_profile", "tdd"), ("namespace", "../escape"),
])
def test_invalid_configuration_is_rejected(config, public_api, field, value):
    config[field] = value
    rejected(public_api("plan_swebench_import"), config, match=field + "|source|profile")


@pytest.mark.parametrize("field,value", [
    ("instance_id", "../../escape"), ("repo", "../escape"), ("base_commit", "HEAD"),
    ("environment_setup_commit", "latest"), ("problem_statement", ""), ("patch", ""),
    ("test_patch", ""), ("version", ""), ("FAIL_TO_PASS", "not-json"),
    ("FAIL_TO_PASS", "[]"), ("FAIL_TO_PASS", '[1]'),
    ("FAIL_TO_PASS", '["same", "same"]'), ("PASS_TO_PASS", {}),
])
def test_malformed_rows_fail_with_instance_and_field_diagnostics(config, snapshot, public_api, field, value):
    snapshot["records"][0][field] = value
    rewrite_snapshot(snapshot)
    rejected(public_api("plan_swebench_import"), config, match=field + "|instance")


def test_native_test_lists_and_json_strings_have_identical_normalized_records(config, snapshot, public_api):
    first = plan(public_api, config)
    snapshot["records"][0].update(FAIL_TO_PASS=["test_total.py::test_total"],
                                   PASS_TO_PASS=["test_existing.py::test_empty"])
    rewrite_snapshot(snapshot)
    second = plan(public_api, config)
    assert first["selection"] == second["selection"]


def test_fail_to_pass_and_pass_to_pass_cannot_overlap(config, snapshot, public_api):
    snapshot["records"][0]["PASS_TO_PASS"] = snapshot["records"][0]["FAIL_TO_PASS"]
    rewrite_snapshot(snapshot)
    rejected(public_api("plan_swebench_import"), config, match="overlap|FAIL_TO_PASS|PASS_TO_PASS")


def test_duplicate_rows_are_not_silently_deduplicated(config, snapshot, public_api):
    snapshot["records"].append(deepcopy(snapshot["records"][0]))
    rewrite_snapshot(snapshot)
    rejected(public_api("plan_swebench_import"), config, match="duplicate|instance_id")


def test_offline_cache_miss_never_attempts_download(config, tmp_path, public_api):
    config["snapshot"] = str(tmp_path / "missing snapshot")
    rejected(public_api("plan_swebench_import"), config, match="offline|snapshot|cache")


def test_tampered_source_bytes_are_rejected(config, snapshot, public_api):
    with (snapshot["root"] / "records.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("\n")
    rejected(public_api("plan_swebench_import"), config, match="hash|sha256|integrity")


def test_snapshot_cannot_impersonate_another_revision(config, snapshot, public_api):
    path = snapshot["root"] / "source.json"
    source = read_json(path)
    source["revision"] = "f" * 40
    write_json(path, source)
    rejected(public_api("plan_swebench_import"), config, match="revision|source")


@pytest.mark.parametrize("field", ["dataset_license", "repository_licenses"])
def test_missing_licenses_block_import_instead_of_inheriting_cubie_license(config, snapshot, public_api, field):
    del snapshot["source"][field]
    rewrite_snapshot(snapshot)
    rejected(public_api("plan_swebench_import"), config, match="license")
