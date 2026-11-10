"""Verify base resources and pilot aggregation in a wheel outside the checkout."""

import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from qb_cubie import EBT, WorldState


def contract(target, *args, expected):
    trace = EBT(target=target, pre=WorldState(args=args), post=WorldState(returns=expected), reporter=None).run()
    assert trace.evaluation is True and trace.traces[0].evaluation is True
    return trace.traces[0].outcome.returns


def cli(*args, cwd):
    command = Path(sys.executable).parent / ("cubie-bench.exe" if os.name == "nt" else "cubie-bench")
    return subprocess.run([str(command), *map(str, args)], cwd=cwd, capture_output=True, text=True,
                          timeout=60, check=False)


def test_installed_base_is_complete_relocatable_and_discoverable(tmp_path):
    module = importlib.import_module("qb_cubie.benchmarks")
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    original = tmp_path / "base"
    contract(lambda: cli("init-base", original, "--format", "json", cwd=tmp_path), expected=lambda value: value.returncode == 0)
    moved = tmp_path / "moved base with spaces"
    shutil.move(original, moved)
    package = contract(module.load_package, moved, expected=lambda value: len(value["scenarios"]) == 36)
    assert package["namespace"] == "base-v1" and (moved / "dataset.json").is_file()
    assert sum(case["benchmark"] == "review_agent" for case in package["scenarios"]) == 24
    contract(lambda: cli("list", "--package", moved, cwd=tmp_path), expected=lambda value: value.returncode == 0)


def test_installed_base_executes_paired_repeats_and_archives_its_catalog(tmp_path):
    module = importlib.import_module("qb_cubie.benchmarks")
    module.init_base_package(tmp_path / "base")
    module.init_smoke_suite(tmp_path / "sets/smoke.toml")
    suite = tmp_path / "sets/pilot.toml"
    module.init_suite(suite, tmp_path / "agents/fake.toml", tmp_path / "base")
    text = suite.read_text(encoding="utf-8").replace('profile = "agent-evaluation"', 'profile = "cubie-vs-pytest"')
    text = text.replace("repetitions = 1", "repetitions = 2\nseed = 17")
    suite.write_text(text + '\n[select]\nids = ["base-v1/pure-calculation-initial"]\n', encoding="utf-8")
    run = contract(module.run_suite, suite, expected=lambda value: len(value["runs"]) == 4)
    assert all(item["quality_passed"] and item["process_passed"] for item in run["runs"])
    root = Path(run["output"])
    summary = contract(module.summarize_pilot, [root], expected=lambda value: len(value["groups"]) == 2)
    assert summary["measurement_kind"] == "infrastructure_only"
    output = contract(lambda: cli("summarize-pilot", root, "--format", "json", cwd=tmp_path),
                      expected=lambda value: value.returncode == 0)
    assert json.loads(output.stdout) == summary
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert "inputs/packages/base-v1/dataset.json" in manifest["artifact_hashes"]
    assert manifest["wheel_sha256"] == os.environ["QB_CUBIE_TEST_WHEEL_SHA256"]


def test_installed_objective_and_manual_references_keep_distinct_validation_statuses(tmp_path):
    module = importlib.import_module("qb_cubie.benchmarks")
    root = tmp_path / "selected base"
    module.init_base_package(root)
    names = {"review-correctness-warehouse-correct", "review-correctness-warehouse-faulty",
             "review-maintainability-service-policy-faulty", "pure-calculation-initial"}
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    package["scenarios"] = [path for path in package["scenarios"] if Path(path).parent.name in names]
    (root / "package.json").write_text(json.dumps(package), encoding="utf-8")
    catalog = json.loads((root / "dataset.json").read_text(encoding="utf-8"))
    catalog["cases"] = {name: record for name, record in catalog["cases"].items() if name in names}
    (root / "dataset.json").write_text(json.dumps(catalog), encoding="utf-8")
    checked = contract(lambda: module.validate_package(root, check_references=True),
                       expected=lambda value: value["valid"] and value["references_checked"])
    for scenario in checked["scenarios"]:
        assert scenario["validation_status"] == "author_checked"
        manual = "maintainability" in scenario["scenario_id"]
        assert scenario["reference_check"] == ("manual_required" if manual else "executed")
        assert scenario["reference_passed"] is (None if manual else True)
