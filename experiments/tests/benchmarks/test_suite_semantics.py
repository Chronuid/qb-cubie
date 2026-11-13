"""Phase 10.1: declarative selection has one meaning before any agent starts."""

import shutil

import pytest

from .contracts import accepted, edit_json, rejected, scenario


def suite(package, select="", extra=""):
    path = package / "sets" / "smoke.toml"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(extra)
        if select:
            stream.write("\n[select]\n" + select + "\n")
    return path


def expect_ids(result, ids):
    runs = result["runs"]
    return (sorted(run["scenario_id"] for run in runs) == sorted(f"phase1/{id_}" for id_ in ids)
            and len(runs) == len(ids)
            and all(run["agent_id"] == "fake" and run["repetition"] == 1 for run in runs))


@pytest.mark.parametrize("selection,ids", [
    ('benchmarks = ["review_agent"]', ["review-paid-correct", "review-paid-faulty"]),
    ('types_any = ["maintenance", "diagnosis"]\nids = ["phase1/index-initial", "phase1/index-maintenance", "phase1/index-diagnosis"]', []),
    ('types_none = ["file_workflow"]', ["review-paid-correct", "review-paid-faulty"]),
    ('ids = ["phase1/review-paid-correct", "phase1/review-paid-faulty"]\nexclude_ids = ["phase1/review-paid-faulty"]', ["review-paid-correct"]),
])
def test_selection_and_exclusions(package, public_api, selection, ids):
    if not ids:
        rejected(public_api("plan_suite"), suite(package, selection), match="requires|prerequisite")
    else:
        accepted(public_api("plan_suite"), suite(package, selection), expected=lambda plan: expect_ids(plan, ids))


def test_custom_multiple_types_and_tags_do_not_duplicate_runs(package, public_api):
    edit_json(scenario(package), lambda data: data.update(
        types=["correctness", "myteam/payment_rules"], tags=["billing", "fast"]))
    path = suite(package, 'types_any = ["correctness", "myteam/payment_rules"]\ntypes_all = ["correctness", "myteam/payment_rules"]\ntags_all = ["billing", "fast"]\nsplits = ["development"]\ntags_any = ["billing", "other"]\ntags_none = ["slow"]\nbenchmarks = ["review_agent"]')
    accepted(public_api("plan_suite"), path,
             expected=lambda plan: expect_ids(plan, ["review-paid-correct"]))


@pytest.mark.parametrize("selection,match", [
    ('ids = ["phase1/missing"]', "phase1/missing"),
    ('types_any = ["missing"]', "missing"),
    ('tags_any = ["missing"]', "missing"),
    ('benchmarks = ["review_agent"]\nexclude_ids = ["phase1/review-paid-correct", "phase1/review-paid-faulty"]', "empty|selection"),
    ('ids = ["phase1/index-diagnosis"]', "requires|prerequisite"),
])
def test_invalid_selection_is_rejected_before_agent_start(package, public_api, selection, match):
    rejected(public_api("plan_suite"), suite(package, selection), match=match)


@pytest.mark.parametrize("field", ["ids", "exclude_ids", "types_any", "types_all", "types_none",
                                    "tags_any", "tags_all", "tags_none", "benchmarks", "splits"])
def test_explicitly_empty_filter_is_invalid(package, public_api, field):
    rejected(public_api("plan_suite"), suite(package, field + " = []"), match=field)


def test_all_episodes_are_planned_in_dependency_order(package, public_api):
    accepted(public_api("plan_suite"), suite(package, 'benchmarks = ["developer_agent"]'),
             expected=lambda plan: [r["scenario_id"] for r in plan["runs"]]
             == ["phase1/index-initial", "phase1/index-maintenance", "phase1/index-diagnosis"])


def test_paths_resolve_from_suite_and_planning_starts_no_process(package, public_api, tmp_path, monkeypatch):
    planner = public_api("plan_suite")
    monkeypatch.chdir(tmp_path)
    # The agent command deliberately does not exist; a planner must not start it.
    accepted(planner, package / "sets" / "smoke.toml", expected=lambda plan: (
        len(plan["runs"]) == 5 and plan["output"] == str((package / "results").resolve())
        and plan["max_total_wall_time_seconds"] == 300
        and all(run["budgets"] == {"wall_time_seconds": 60, "tool_calls": 5} for run in plan["runs"])
    ))


@pytest.mark.parametrize("old,new,match", [
    ("max_runs = 5", "max_runs = 4", "max_runs"),
    ("max_total_wall_time_seconds = 300", "max_total_wall_time_seconds = 299", "max_total_wall_time_seconds"),
    ("repetitions = 1", "repetitions = 0", "repetitions"),
])
def test_hard_limits_reject_instead_of_truncating(package, public_api, old, new, match):
    path = suite(package)
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    rejected(public_api("plan_suite"), path, match=match)


def test_same_namespace_with_different_content_is_rejected(package, public_api):
    other = package.parent / "other"
    shutil.copytree(package, other)
    edit_json(other / "package.json", lambda data: data.update(version="2.0.0"))
    path = suite(package, extra='\n[[sources]]\npath = "../../other"\n')
    rejected(public_api("plan_suite"), path, match="namespace.*phase1|phase1.*namespace")


def test_repetitions_expand_trials_without_losing_identity(package, public_api):
    path = suite(package, 'ids = ["phase1/review-paid-correct"]')
    path.write_text(path.read_text(encoding="utf-8").replace("repetitions = 1", "repetitions = 2"), encoding="utf-8")
    accepted(public_api("plan_suite"), path, expected=lambda plan: (
        len(plan["runs"]) == 2
        and all(run["scenario_id"] == "phase1/review-paid-correct" for run in plan["runs"])
        and {run["repetition"] for run in plan["runs"]} == {1, 2}
    ))
