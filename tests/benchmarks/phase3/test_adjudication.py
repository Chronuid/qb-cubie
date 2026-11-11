"""Adjudication binds source evidence and produces usable archives without changing originals."""

from pathlib import Path

import pytest

from qb_cubie.benchmarks import apply_adjudication, evaluate_gates, run_suite, summarize_pilot
from qb_cubie.benchmarks.reporting._files import digest, inventory, write_json
from qb_cubie.benchmarks.reporting.archives import read_archive
from .conftest import write_suite


def inputs(external, tmp_path):
    result = run_suite(write_suite(external, 'ids = ["shop/review-boundary"]'))
    root = Path(result["output"])
    run, = result["runs"]
    evidence, = [p for p in run["evidence"] if p.endswith("review-evaluation.json")]
    import json
    original = json.loads((root / evidence).read_text())
    decision = {"schema_version": 1, "manifest_sha256": digest(root / "manifest.json"),
                "evaluator_id": "offline-test", "version": "1", "runs": {run["run_id"]: {
                    "evaluation_sha256": digest(root / evidence), "reason": "Match mechanism and consequence",
                    "matches": list(range(len(original["response"]["findings"])))}}}
    path = tmp_path / "decisions.json"
    write_json(path, decision)
    return root, path, decision


def test_derived_archive_preserves_original_and_recomputes_gates(external, tmp_path):
    root, path, _ = inputs(external, tmp_path)
    before = inventory(root)
    result = apply_adjudication(root, path, tmp_path / "derived")
    assert inventory(root) == before
    assert read_archive(result["output"]) == result
    assert evaluate_gates(result["output"]) == result["gate_evaluation"]
    assert (Path(result["output"]) / "adjudication-parent.json").is_file()
    assert summarize_pilot([result["output"]])["groups"]


@pytest.mark.parametrize("damage", ["binding", "missing", "index"])
def test_invalid_mapping_cannot_publish_or_change_original(external, tmp_path, damage):
    root, path, decision = inputs(external, tmp_path)
    before = inventory(root)
    entry = next(iter(decision["runs"].values()))
    if damage == "binding":
        entry["evaluation_sha256"] = "0" * 64
    elif damage == "missing":
        entry["matches"] = []
    else:
        entry["matches"] = [999] * len(entry["matches"])
    write_json(path, decision)
    with pytest.raises(ValueError):
        apply_adjudication(root, path, tmp_path / "derived")
    assert not (tmp_path / "derived").exists()
    assert inventory(root) == before


def test_rejected_semantic_matches_change_quality_and_metrics(external, tmp_path):
    root, path, decision = inputs(external, tmp_path)
    entry = next(iter(decision["runs"].values()))
    entry["matches"] = [None] * len(entry["matches"])
    write_json(path, decision)
    result = apply_adjudication(root, path, tmp_path / "derived")
    run, = result["runs"]
    assert run["quality_passed"] is False
    assert {metric["name"]: metric["value"] for metric in run["metrics"]} == {"precision": 0, "recall": 0}
