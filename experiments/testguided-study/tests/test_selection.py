"""Check variable study sizes, runtime planning and task-type provenance."""

import json
from pathlib import Path

import pytest
from testguided_study.artifacts import digest, freeze, read, verify, write
from testguided_study.planning import plan
from testguided_study.report import arm, summarize
from testguided_study.selection import select
from testguided_study.smoke import generate

ROOT = Path(__file__).resolve().parents[1]


def test_size_changes_keep_nested_reproducible_prefixes():
    tasks = [{"id": str(i), "task_type": f"type-{i % 3}", "repo": f"repo-{i % 2}"} for i in range(18)]
    short = select(tasks, count=3, seed=17)
    long = select(list(reversed(tasks)), count=9, seed=17)
    assert short == long[:3]
    assert len({task["task_type"] for task in short}) == 3
    assert len({task["repo"] for task in long}) == 2


def test_related_and_opposite_historical_fixes_are_not_independent_tasks():
    tasks = [{"id": "old", "task_type": "parsing", "related_group": "slash-history"},
             {"id": "new", "task_type": "parsing", "related_group": "slash-history"},
             {"id": "other", "task_type": "rendering"}]
    chosen = select(tasks, count=2)
    assert sum(task.get("related_group") == "slash-history" for task in chosen) == 1
    with pytest.raises(ValueError, match="only 2 independent"):
        select(tasks, count=3)
    with pytest.raises(ValueError, match="No tasks"):
        select(tasks, task_types=["absent"])


def test_catalog_preserves_all_originals_and_records_additional_review():
    catalog = read(ROOT / "candidate-catalog.json")
    old = read(ROOT / "candidate-selection.json")
    by_id = {task["id"]: task for task in catalog["tasks"]}
    assert len(by_id) == 129
    assert catalog["reviewed_count"] == 39
    assert catalog["additional_reviewed_count"] == 24
    assert all(by_id[task["id"]]["review_status"] != "unreviewed" for task in old["candidates"])
    assert by_id["fastapi_15280"]["eligible"] is False
    assert by_id["requests_6757"]["review_status"] == "deferred"
    assert by_id["httpx_3672"]["eligible"] is False
    assert all(by_id[id]["split"] == "pilot" for id in catalog["pilot_reserved_ids"])
    assert all(task["technical_admission"] == "pending" for task in by_id.values())


def test_profiles_plan_both_agents_repeats_references_and_setup():
    catalog = ROOT / "candidate-catalog.json"
    short = plan(ROOT / "profiles/three-hours.toml", catalog)
    long = plan(ROOT / "profiles/six-hours.toml", catalog)
    assert short["tasks"] == long["tasks"][:5]
    assert short["runtime"]["agent_runs"] == 10
    assert long["runtime"]["agent_runs"] == 20
    assert short["runtime"]["total_allowance_hours"] == pytest.approx(360 / 60)
    assert long["runtime"]["total_allowance_hours"] == pytest.approx(720 / 60)
    assert short["runtime"]["fits_allowance"] is False
    assert short["status"] == "candidates_not_admitted"
    assert len({task["related_group"] for task in long["tasks"]}) == 10
    pilot = plan(ROOT / "profiles/pilot.toml", catalog)
    assert not {t["id"] for t in pilot["tasks"]} & {t["id"] for t in long["tasks"]}


def prepared(tmp_path):
    inputs = tmp_path / "inputs"
    generate(inputs)
    template = read(inputs / "record.json")
    tasks = []
    for index, kind in enumerate(("parsing_encoding", "filesystem_configuration", "terminal_rendering")):
        record = f"record-{index}.json"
        write(inputs / record, {**template, "instance_id": f"task-{index}"})
        tasks.append({"id": f"task-{index}", "split": "pilot", "snapshot": "snapshot.tar.gz", "record": record,
                      "task_type": kind, "change_kind": "bugfix", "repo": template["repo"],
                      "test_scope": "unit", "related_group": f"group-{index}"})
    write(inputs / "tasks.json", tasks)
    config = inputs / "study.toml"
    config.write_text(config.read_text() + '\n[selection]\ntask_count = 2\nseed = 17\ntask_types = []\n')
    return config


def test_freeze_and_report_keep_type_and_select_exact_configured_number(tmp_path):
    config = prepared(tmp_path)
    planned = plan(config)
    frozen = tmp_path / "frozen"
    assert freeze(config, frozen)["tasks"] == 2
    assert verify(frozen)["selection"]["task_count"] == 2
    assert {t["id"] for t in read(frozen / "tasks.json")} == {t["id"] for t in planned["tasks"]}
    schedule = read(frozen / "schedule.json")
    for expected in schedule:
        directory = frozen / "runs" / expected["run_id"]
        write(directory / "result.json", {**expected, "resolved": expected["mode"] == "cubie"})
        write(directory / "manifest.json", {"result.json": digest(directory / "result.json")})
    report = summarize(frozen)
    assert report["complete_pairs"] == 2
    assert len(report["by_task_type"]) == 2
    for group in report["by_task_type"].values():
        assert group["tasks"] == 1
        assert group["complete_pairs"] == 1
        assert group["paired_task_mean_difference"] == 1
        assert group["arms"]["pytest"]["resolved"] == 0
        assert group["arms"]["cubie"]["resolved"] == 1
    assert report["by_change_kind"]["bugfix"]["tasks"] == 2
    assert sum(read(frozen / "task-distribution.json")["task_type"].values()) == 2


def test_type_filter_and_count_are_applied_before_copying_inputs(tmp_path):
    config = prepared(tmp_path)
    config.write_text(config.read_text().replace("task_count = 2", "task_count = 1")
                      .replace("task_types = []", 'task_types = ["parsing_encoding"]'))
    frozen = tmp_path / "frozen"
    freeze(config, frozen)
    assert [t["id"] for t in read(frozen / "tasks.json")] == ["task-0"]
    assert len(read(frozen / "schedule.json")) == 2
    schedule = read(frozen / "schedule.json")
    assert all(row["task_type"] == "parsing_encoding" for row in schedule)
    # Manifest binding includes the type labels used in subgroup reports.
    (frozen / "tasks.json").write_text(json.dumps([]))
    with pytest.raises(ValueError, match="Frozen input changed"):
        verify(frozen)


def test_measurements_reject_missing_type_labels_and_mismatched_repository(tmp_path):
    config = prepared(tmp_path)
    tasks_path = config.parent / "tasks.json"
    tasks = read(tasks_path)
    tasks[0]["repo"] = "wrong/repository"
    write(tasks_path, tasks)
    with pytest.raises(ValueError, match="repository"):
        freeze(config, tmp_path / "wrong-repo")
    config.write_text(config.read_text().replace('phase = "pilot"', 'phase = "measurement"'))
    for task in tasks:
        task["split"] = "measurement"
        task.pop("task_type")
    write(tasks_path, tasks)
    with pytest.raises(ValueError, match="require task_type"):
        freeze(config, tmp_path / "untyped")


def test_type_group_telemetry_keeps_missing_runs_and_unknown_tokens_visible():
    rows = [{"resolved": True, "agent": {"duration_seconds": 12, "model_calls": 2, "tool_calls": 1,
             "status": "submitted", "usage": [{"input_tokens": 30, "output_tokens": 4},
                                                {"input_tokens": None, "output_tokens": 6}],
             "test_observations": [{"observation": "assertion_failure"}, {"observation": "pass"}]}},
            {"resolved": None}]
    metrics = arm(rows)
    assert metrics["scheduled"] == 2 and metrics["unavailable"] == 1
    assert metrics["runs_with_agent_metrics"] == 1
    assert metrics["measured_input_tokens"] is None
    assert metrics["measured_total_tokens"] is None
    assert metrics["measured_output_tokens"] == 10
    assert metrics["measured_model_calls"] == 2
    assert metrics["measured_tool_calls"] == 1
    assert metrics["visible_test_observations"] == {"assertion_failure": 1, "pass": 1}
