"""Execute each base project in both conditions through the public runner."""

import json
from pathlib import Path

import pytest

from ..contracts import accepted, edit_json, rejected
from ..phase3.conftest import CAPABILITIES

PROJECTS = ["billing-export", "configuration-package", "document-index", "pure-calculation"]


def base_suite(root, public_api, project):
    package = root / "base"
    accepted(public_api("init_base_package"), package, expected=lambda value: Path(value["package"]) == package)
    agent = root / "fake.toml"
    agent.write_text('schema_version = 1\nid = "reference"\ncommand = ["builtin:fake"]\n'
                     f'capabilities = {json.dumps(CAPABILITIES)}\n[fake]\nbehavior = "reference"\n', encoding="utf-8")
    suite = root / "set.toml"
    accepted(public_api("init_suite"), suite, agent, package, expected=lambda value: Path(value["suite"]) == suite)
    text = suite.read_text(encoding="utf-8").replace('profile = "agent-evaluation"', 'profile = "cubie-vs-pytest"')
    ids = [f"base-v1/{project}-{episode}" for episode in ("initial", "maintenance", "diagnosis")]
    suite.write_text(text + f'\n[select]\nids = {json.dumps(ids)}\n', encoding="utf-8")
    return suite


@pytest.mark.parametrize("project", PROJECTS)
def test_reference_completes_all_primary_episodes_in_both_conditions(tmp_path, public_api, project):
    suite = base_suite(tmp_path, public_api, project)
    result = accepted(public_api("run_suite"), suite, expected=lambda value: len(value["runs"]) == 6)
    for run in result["runs"]:
        assert run["status"] == "completed" and run["quality_passed"] is True
        assert run["process_passed"] is True, run.get("process_reason")
        assert [phase["test_outcome"] for phase in run["phases"]] == [
            "not_executed", "assertion_failure", "passed", "passed"]
    summary = accepted(public_api("summarize_pilot"), [result["output"]],
                       expected=lambda value: len(value["groups"]) == 2)
    assert all(group["independent_groups"] == 1 for group in summary["groups"])
    assert all(len(group["episodes"]) == 3 for group in summary["groups"])
    catalog = Path(result["output"]) / "inputs/packages/base-v1/dataset.json"
    assert catalog.is_file()
    manifest = json.loads((Path(result["output"]) / "manifest.json").read_text(encoding="utf-8"))
    assert "inputs/packages/base-v1/dataset.json" in manifest["artifact_hashes"]


@pytest.mark.parametrize("fault", ["runtime-error", "false-counterexample"])
def test_review_execution_errors_and_false_references_cannot_validate(tmp_path, public_api, fault):
    root = tmp_path / "base"
    accepted(public_api("init_base_package"), root, expected=lambda value: Path(value["package"]) == root)
    name = "review-correctness-warehouse-faulty"
    edit_json(root / "package.json", lambda value: value.update(scenarios=[f"scenarios/{name}/scenario.json"]))
    edit_json(root / "dataset.json", lambda value: value.update(cases={name: value["cases"][name]}))
    base = root / "scenarios" / name
    if fault == "runtime-error":
        (base / "visible/stock_policy.py").write_text('def included(row):\n    raise RuntimeError("broken tool")\n', encoding="utf-8")
    else:
        (base / "visible/stock_policy.py").write_text('def included(row):\n    return row["active"] is True\n', encoding="utf-8")
    rejected(lambda: public_api("validate_package")(root, check_references=True), match="reference|business|execution")


def test_catalog_changes_are_part_of_the_resolved_package_identity(tmp_path, public_api):
    suite = base_suite(tmp_path, public_api, "pure-calculation")
    before = accepted(public_api("plan_suite"), suite, expected=lambda value: len(value["runs"]) == 6)
    edit_json(tmp_path / "base/dataset.json", lambda value: value["cases"]["pure-calculation-initial"].update(
        origin="Revised documented provenance"))
    after = accepted(public_api("plan_suite"), suite, expected=lambda value: len(value["runs"]) == 6)
    assert before["packages"][0]["sha256"] != after["packages"][0]["sha256"]
