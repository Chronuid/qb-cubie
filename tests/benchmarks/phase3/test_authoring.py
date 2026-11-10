"""Public authoring and discovery must work without importing runner internals."""

import json
import tomllib
from pathlib import Path

import pytest

from ..contracts import accepted, rejected
from .conftest import cli, configure_agent, read_json, traffic, write_suite


def test_agent_template_is_editable_and_does_not_start_an_agent(external, public_api):
    path = external / "new agents" / "current.toml"
    accepted(public_api("init_agent"), path, expected=lambda value: value["agent"] == str(path.resolve()))
    config = tomllib.loads(path.read_text(encoding="utf-8"))
    assert config["schema_version"] == 1 and config["transport"] == "jsonl-v1"
    assert config["command"] and config["command"] != ["builtin:fake"]
    assert isinstance(config["capabilities"], list)
    assert not traffic(external)


def test_agent_template_never_overwrites_local_configuration(external, public_api):
    path = external / "agents/current.toml"
    previous = path.read_bytes()
    rejected(public_api("init_agent"), path, match="exist|overwrite")
    assert path.read_bytes() == previous and not traffic(external)


def test_validate_agent_exercises_real_handshake_but_no_scenario(external, public_api):
    accepted(public_api("validate_agent"), external / "agents/current.toml", expected=lambda value: (
        value["schema_version"] == 1 and value["valid"] is True and value["agent_id"] == "own-agent"
        and "phased_submission" in value["capabilities"] and value["agent_version"] == "fixture-1"))
    entries = traffic(external)
    assert entries and all(e["request"]["type"] == "capabilities" for e in entries)
    assert not (external / "results").exists()


@pytest.mark.parametrize("mode,match", [("wrong_version", "version"), ("missing_capabilities", "capabilit")])
def test_validate_agent_rejects_actual_protocol_mismatch(external, public_api, mode, match):
    path = configure_agent(external, mode)
    rejected(public_api("validate_agent"), path, match=match)
    assert traffic(external) and not (external / "results").exists()


@pytest.mark.parametrize("benchmark", ["review_agent", "developer_agent"])
def test_scenario_template_is_a_complete_external_package(tmp_path, public_api, benchmark):
    destination = tmp_path / "my new case"
    accepted(public_api("init_scenario"), destination, benchmark, expected=lambda result: (
        result["package"] == str(destination.resolve())))
    package = accepted(public_api("load_package"), destination, expected=lambda value: len(value["scenarios"]) == 1)
    case, = package["scenarios"]
    assert case["benchmark"] == benchmark
    assert case["evaluator"]["kind"] == ("builtin.review_reference_v1" if benchmark == "review_agent"
                                        else "builtin.pytest_project_v1")
    reference = read_json((destination / case["manifest"]).parent / case["evaluator"]["reference"])
    assert reference["validation_status"] == "author_checked" and reference["human_reviews"] == []


def test_scenario_template_does_not_overwrite_authored_material(external, public_api):
    previous = {p.relative_to(external): p.read_bytes() for p in external.rglob("*") if p.is_file()}
    rejected(public_api("init_scenario"), external, "review_agent", match="exist|overwrite")
    assert previous == {p.relative_to(external): p.read_bytes() for p in external.rglob("*") if p.is_file()}


def test_structure_only_validation_is_explicitly_not_reference_validation(external, public_api):
    accepted(public_api("validate_package"), external, expected=lambda result: (
        result["schema_version"] == 1 and result["valid"] is True and result["references_checked"] is False))
    assert not traffic(external)


def test_reference_validation_checks_solution_and_mutant_without_agent(external, public_api):
    validator = public_api("validate_package")
    result = accepted(lambda: validator(external, check_references=True), expected=lambda value: (
        value["valid"] is True and value["references_checked"] is True))
    case, = [s for s in result["scenarios"] if s["scenario_id"] == "shop/fee-initial"]
    assert case["validation_status"] == "author_checked" and case["reference_passed"] is True
    assert case["mutants"] == [{"id": "wrong-return", "detected": True, "criterion_results": {"fee": "fail"}}]
    assert not traffic(external)


@pytest.mark.parametrize("material", ["solution.py.txt", "wrong.py.txt"])
def test_broken_solution_or_ineffective_mutant_fails_reference_validation(external, public_api, material):
    validator = public_api("validate_package")
    base = external / "scenarios/fee-initial/evaluator"
    replacement = "wrong.py.txt" if material == "solution.py.txt" else "solution.py.txt"
    (base / material).write_bytes((base / replacement).read_bytes())
    rejected(lambda: validator(external, check_references=True), match="fee-initial|reference|mutant")
    assert not traffic(external)


def test_cli_discovers_custom_taxonomy_without_executing_code(external):
    result = accepted(lambda: cli("list", "--package", external, "--format", "json", cwd=external.parent),
                      expected=lambda p: p.returncode == 0)
    listing = json.loads(result.stdout)
    assert listing["namespace"] == "shop" and len(listing["scenarios"]) == 3
    assert {s["qualified_id"] for s in listing["scenarios"]} == {"shop/review-correct", "shop/review-boundary", "shop/fee-initial"}
    assert "shop/shipping" in listing["types"] and "boundary" in listing["tags"]
    assert not traffic(external)


def test_cli_and_python_use_the_same_external_plan(external, public_api):
    suite = write_suite(external, 'types_any = ["shop/shipping"]\nbenchmarks = ["review_agent"]')
    plan = accepted(public_api("plan_suite"), suite, expected=lambda p: len(p["runs"]) == 1)
    output = accepted(lambda: cli("plan", "--suite", suite, "--format", "json", cwd=external.parent),
                      expected=lambda p: p.returncode == 0)
    assert json.loads(output.stdout) == plan and not traffic(external)


def test_cli_help_points_to_custom_agent_workflow(external):
    accepted(lambda: cli("--help", cwd=external.parent), expected=lambda p: (
        p.returncode == 0 and all(word in p.stdout for word in
                                 ["init-agent", "validate-agent", "init-scenario", "validate", "list", "compare",
                                  "GUIDE_Benchmark-Custom"])))


def test_cli_can_create_a_suite_with_one_explicit_external_agent(external):
    destination = external / "own sets" / "smoke.toml"
    accepted(lambda: cli("init-suite", destination, "--preset", "smoke", "--agent",
                         external / "agents/current.toml", "--package", external,
                         "--format", "json", cwd=external.parent), expected=lambda p: p.returncode == 0)
    config = tomllib.loads(destination.read_text(encoding="utf-8"))
    assert config["profile"] == "agent-evaluation" and config["repetitions"] == 1
    assert len(config["agents"]) == 1
    assert (destination.parent / config["agents"][0]).resolve() == external / "agents/current.toml"
    assert len(config["sources"]) == 1 and Path(destination.parent / config["sources"][0]["path"]).resolve() == external
    assert not traffic(external)
