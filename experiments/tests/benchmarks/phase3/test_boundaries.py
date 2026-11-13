"""Exercise packaged examples and runtime boundaries beyond the initial cases."""

from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from .conftest import cli, configure_agent, traffic, write_suite


def test_packaged_example_runs_without_repository_fixtures(tmp_path, public_api):
    root = tmp_path / "exported shipping"
    example = accepted(public_api("init_example"), root, expected=lambda p: p["package"] == str(root))
    result = accepted(public_api("run_suite"), example["suite"], expected=lambda r: len(r["runs"]) == 3)
    assert all(r["status"] == "completed" and r["quality_passed"] for r in result["runs"])
    assert next(r for r in result["runs"] if r["benchmark"] == "developer_agent")["process_passed"] is True
    original = (root / "package.json").read_bytes()
    rejected(public_api("init_example"), root, match="exist|overwrite")
    assert (root / "package.json").read_bytes() == original


def test_developer_template_validates_mutants_with_missing_output(tmp_path, public_api):
    root = tmp_path / "new development"
    accepted(public_api("init_scenario"), root, "developer_agent", expected=lambda p: p["package"] == str(root))
    validate = public_api("validate_package")
    result = accepted(lambda: validate(root, check_references=True), expected=lambda r: r["valid"] is True)
    scenario, = result["scenarios"]
    assert scenario["reference_passed"] is True
    missing, = [m for m in scenario["mutants"] if m["id"] == "missing-copy"]
    assert missing["detected"] is True and missing["criterion_results"]["copies"] == "fail"


def test_installed_guide_has_a_complete_offline_workflow(external):
    result = accepted(lambda: cli("guide", cwd=external.parent), expected=lambda p: p.returncode == 0)
    for word in ["init-example", "validate-agent", "--check-references", "plan", "run", "compare", "init-scenario"]:
        assert word in result.stdout


def test_unsupported_hard_budget_is_rejected_before_handshake(external, public_api):
    suite = write_suite(external)
    text = suite.read_text(encoding="utf-8").replace('"tool_calls"]', '"tool_calls", "cost"]')
    # Advertise cost support to get past data-only capability selection.
    agent = external / "agents/current.toml"
    agent.write_text(agent.read_text(encoding="utf-8").replace('"tool_calls"]', '"tool_calls", "cost"]'), encoding="utf-8")
    suite.write_text(text.replace("tool_calls = 20", "tool_calls = 20\ncost = 1"), encoding="utf-8")
    rejected(public_api("run_suite"), suite, match="budgets|cost")
    assert not traffic(external) and not (external / "results").exists()


def test_nonzero_exit_after_valid_submission_is_still_infrastructure_failure(external, public_api):
    script = external / "agents/jsonl_agent.py"
    original = script.read_text(encoding="utf-8")
    assert original.count("emit(event(incoming))") == 1
    script.write_text(original.replace("emit(event(incoming))", "emit(event(incoming))\n    sys.exit(7)"), encoding="utf-8")
    suite = write_suite(external, 'ids = ["shop/review-correct"]')
    result = accepted(public_api("run_suite"), suite, expected=lambda r: len(r["runs"]) == 1)
    run, = result["runs"]
    assert run["status"] == "infrastructure_error" and run["quality_passed"] is False
    assert run["evaluation_status"] == "not_evaluated"


def test_generated_caches_do_not_change_package_identity_or_exports(external, public_api):
    suite = write_suite(external, 'ids = ["shop/review-correct"]')
    plan = accepted(public_api("plan_suite"), suite, expected=lambda p: len(p["runs"]) == 1)
    for name in ("__pycache__", ".pytest_cache"):
        cache = external / "scenarios/review-correct/visible" / name
        cache.mkdir()
        (cache / "generated").write_bytes(b"generated cache data")
    accepted(public_api("plan_suite"), suite, expected=plan)
    result = accepted(public_api("run_suite"), suite, expected=lambda r: r["runs"][0]["quality_passed"] is True)
    workspace = Path(result["runs"][0]["workspace"])
    assert not (workspace / "__pycache__").exists() and not (workspace / ".pytest_cache").exists()


def test_process_commands_preserve_repeated_arguments(external, public_api):
    agent = external / "agents/current.toml"
    original = agent.read_text(encoding="utf-8")
    agent.write_text(original.replace('"own-agent"]', '"own-agent", "own-agent"]'), encoding="utf-8")
    suite = write_suite(external, 'ids = ["shop/review-correct"]')
    accepted(public_api("run_suite"), suite, expected=lambda r: r["runs"][0]["quality_passed"] is True)


@pytest.mark.parametrize("mode", ["reference", "approve_all"])
def test_process_configuration_and_working_directory_survive_relocation(external, tmp_path, public_api, mode):
    import shutil

    configure_agent(external, mode)
    suite = write_suite(external, 'ids = ["shop/review-correct"]')
    target = tmp_path / "relocated example"
    shutil.move(external, target)
    result = accepted(public_api("run_suite"), target / "sets" / suite.name,
                      expected=lambda r: len(r["runs"]) == 1 and r["runs"][0]["quality_passed"] is True)
    assert Path(result["runs"][0]["workspace"]).is_relative_to(target)
