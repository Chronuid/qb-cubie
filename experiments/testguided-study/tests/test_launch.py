"""Check the one-command lifecycle and flag overrides without inference."""

from types import SimpleNamespace

import pytest
from testguided_study import launch
from testguided_study.artifacts import ROOT, read, verify
from testguided_study.telemetry import snapshot


def arguments(tmp_path, **overrides):
    return SimpleNamespace(**({"mode": "smoke", "config": None, "tasks": None, "seeds": [17],
                                "task_type": None, "agent_seconds": 45, "model_calls": 2,
                                "output": tmp_path / "study", "monitor": "none", "port": 0,
                                "keep_monitor": False, "prepare_only": True, "no_build_images": True,
                                "catalog": ROOT / "candidate-catalog.json", "source": None, "snapshots": None,
                                "tasks_manifest": None, "regression_tests": 8} | overrides))


def test_single_command_prepares_frozen_inputs_and_preserves_updated_guides(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(launch.images, "ensure", lambda *args, **kwargs: called.append("images"))

    def preflight(root, observer):
        assert verify(root)["budgets"]["wall_seconds"] == 45
        called.append("preflight")

    monkeypatch.setattr(launch.execution, "preflight", preflight)
    monkeypatch.setattr(launch.execution, "run", lambda *args: pytest.fail("prepare-only must never start inference"))
    args = arguments(tmp_path)
    result = launch.start(args)
    assert result["status"] == "prepared"
    assert called == ["images", "preflight"]
    config = verify(args.output / "frozen")
    assert config["study_id"] == "plumbing-smoke-not-evidence-v3"
    assert config["seeds"] == [17]
    assert config["budgets"]["model_calls"] == 2
    guides = read(args.output / "frozen/guides.json")
    assert guides["pytest"] == (ROOT / "guides/pytest.md").read_text()
    assert guides["cubie"] == (ROOT / "guides/cubie.md").read_text()
    assert snapshot(args.output)["state"] == "prepared"
    assert snapshot(args.output)["total_runs"] == 2


def test_preparation_failure_is_visible_and_never_starts_agents(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("Docker unavailable")

    monkeypatch.setattr(launch.images, "ensure", unavailable)
    monkeypatch.setattr(launch.execution, "run", lambda *args: pytest.fail("No inference after admission failure"))
    args = arguments(tmp_path)
    with pytest.raises(RuntimeError, match="Docker unavailable"):
        launch.start(args)
    assert snapshot(args.output)["state"] == "failed"
    assert read(args.output / "failure.json")["type"] == "RuntimeError"
    with pytest.raises(FileExistsError):
        launch.start(args)


def test_real_modes_use_task_and_budget_overrides(tmp_path):
    args = arguments(tmp_path, mode="short", tasks=7, seeds=[42, 137],
                     task_type=["parsing_encoding"], agent_seconds=600, model_calls=20)
    config = launch.options(args)
    assert config["phase"] == "measurement"
    assert config["selection"]["task_count"] == 7
    assert config["selection"]["task_types"] == ["parsing_encoding"]
    assert config["seeds"] == [42, 137]
    assert config["budgets"]["wall_seconds"] == 600
    assert config["budgets"]["model_calls"] == 20
    with pytest.raises(ValueError, match="exactly one"):
        launch.options(arguments(tmp_path, tasks=2))
