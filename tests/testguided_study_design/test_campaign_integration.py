"""Measurement admission consumes actual frozen development/result manifests."""

import copy

import pytest
from testguided_study.artifacts import digest, freeze, load_config, read, verify, write
from testguided_study.smoke import generate


@pytest.fixture
def qualified(tmp_path):
    source = tmp_path / "input"
    generate(source)
    config = source / "study.toml"
    config.write_text(config.read_text().replace('phase = "pilot"', 'phase = "development"'))
    record = read(source / "record.json")
    task = read(source / "tasks.json")[0]
    tasks = []
    for index in range(2):
        record_copy = copy.deepcopy(record)
        record_copy["instance_id"] = f"dev-{index}"
        write(source / f"record-{index}.json", record_copy)
        tasks.append(task | {"id": f"dev-{index}", "record": f"record-{index}.json", "task_type": "api_schema",
                             "related_group": f"dev-group-{index}", "repo": record["repo"]})
    write(source / "tasks.json", tasks)
    archive = tmp_path / "development"
    freeze(config, archive)
    for row in read(archive / "schedule.json"):
        directory = archive / "runs" / row["run_id"]
        result = row | {"resolved": True, "agent": {"status": "submitted", "final_versions": {"tests": "test-version"}, "test_observations": [
            {"observation": "assertion_failure", "targets": ["tests/test_x.py"], "workspace_sha256": "before", "tests": "test-version", "production": "original"},
            {"observation": "pass", "targets": ["tests/test_x.py"], "workspace_sha256": "after", "tests": "test-version", "production": "fixed"}]}}
        write(directory / "result.json", result)
        write(directory / "manifest.json", {"result.json": digest(directory / "result.json")})
    write(archive / "preflight/identity.json", {"ollama": {"model": {"digest": "model"}},
                                               "swegemma": {"version": "pinned"},
                                               "images": {mode: {"image_id": mode} for mode in ("pytest", "cubie", "evaluator")}})
    write(archive / "ready.json", {"manifest_sha256": digest(archive / "manifest.json"),
                                    "preflight_files": {"preflight/identity.json": digest(archive / "preflight/identity.json")}})
    heldout = tasks[0] | {"id": "heldout", "related_group": "heldout-group", "split": "measurement"}
    write(source / "record-0.json", record | {"instance_id": "heldout"})
    write(source / "tasks.json", [heldout])
    config.write_text('campaign = "campaign.json"\n' + config.read_text().replace('phase = "development"', 'phase = "measurement"'))
    write(source / "campaign.json", {"hypothesis": "shared v2 is qualified", "development_archives": [str(archive)]})
    return source, config, archive, tmp_path / "measurement"


def test_qualified_measurement_copies_admission_and_provenance(qualified):
    _, config, _, destination = qualified
    freeze(config, destination)
    assert verify(destination)["phase"] == "measurement"
    campaign = read(destination / "campaign.json")
    assert campaign["admission"]["qualification"] == {"pytest": True, "cubie": True}
    assert campaign["admission"]["development_task_ids"] == ["dev-0", "dev-1"]
    assert campaign["provenance"][0]["runtime"]["ollama"]["model"]["digest"] == "model"


@pytest.mark.parametrize("fault,match", [
    ("related", "related"), ("design", "qualification"),
    ("budget", "qualification"), ("unavailable", "qualification"),
    ("preflight", "preflight evidence"), ("tamper", "Run evidence changed"),
    ("fake_flag", "qualification"), ("missing_manifest", "qualification"),
])
def test_measurement_rejects_unqualified_or_changed_evidence(qualified, fault, match):
    source, config, archive, destination = qualified
    if fault == "related":
        tasks = read(source / "tasks.json")
        tasks[0]["related_group"] = "dev-group-0"
        write(source / "tasks.json", tasks)
    elif fault == "design":
        config.write_text(config.read_text() + '\n[designs]\npytest = "new-pytest.json"\ncubie = "new-cubie.json"\n')
        for mode in ("pytest", "cubie"):
            design = read(archive / "designs" / f"{mode}.json")["design"]
            design["core"]["prompt"] += "revised"
            write(source / f"new-{mode}.json", design)
    elif fault == "budget":
        previous = load_config(config)["budgets"]["wall_seconds"]
        config.write_text(config.read_text().replace(f"wall_seconds = {previous}", f"wall_seconds = {previous + 1}"))
    elif fault in {"unavailable", "tamper"}:
        directory = archive / "runs/0001"
        result = read(directory / "result.json")
        result["resolved"] = None
        write(directory / "result.json", result)
        if fault == "unavailable":
            write(directory / "manifest.json", {"result.json": digest(directory / "result.json")})
    elif fault == "missing_manifest":
        (archive / "runs/0001/manifest.json").unlink()
    elif fault == "preflight":
        write(archive / "preflight/identity.json", {"changed": True})
    else:
        write(source / "campaign.json", {"qualification": {"pytest": True, "cubie": True}})
    with pytest.raises(ValueError, match=match):
        freeze(config, destination)
    assert not destination.exists()


@pytest.mark.parametrize("change,expected", [
    ({}, True),
    ({"targets": ["other_test.py"]}, False),
    ({"workspace_sha256": "before"}, False),
    ({"observation": "invalid_test_run"}, False),
])
def test_qualification_requires_same_test_targets_and_workspace_change(change, expected):
    from testguided_study.campaign import behavior_cycle
    red = {"observation": "assertion_failure", "targets": ["test_x.py"], "workspace_sha256": "before"}
    green = {"observation": "pass", "targets": ["test_x.py"], "workspace_sha256": "after"} | change
    assert behavior_cycle([red, green]) is expected


@pytest.mark.parametrize("changed", ["model", "runtime", "image"])
def test_measurement_preflight_rejects_qualification_identity_drift(qualified, monkeypatch, changed):
    from testguided_study import execution
    _, config, archive, destination = qualified
    freeze(config, destination)
    prior = read(archive / "preflight/identity.json")
    monkeypatch.setattr(execution.backend, "runtime", lambda: {"version": "different"} if changed == "runtime" else prior["swegemma"])
    monkeypatch.setattr(execution, "provider", lambda _: {"model": {"digest": "different"}} if changed == "model" else prior["ollama"])
    monkeypatch.setattr(execution.backend, "image_identity", lambda image, mode: {"image_id": "different"} if changed == "image" else prior["images"][mode])
    with pytest.raises(ValueError, match="identity drift"):
        execution.preflight(destination)
    assert not (destination / "ready.json").exists()
