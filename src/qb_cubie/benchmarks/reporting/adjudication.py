"""Publish versioned semantic review decisions as a derived, verifiable archive."""

import copy
import json
import shutil
import tempfile
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.execution.evaluators import _metric
from qb_cubie.benchmarks.reporting._files import digest, inventory, write_json
from qb_cubie.benchmarks.reporting.archives import read_archive
from qb_cubie.benchmarks.reporting.gates import assess
from qb_cubie.benchmarks.reporting.results import _report


def apply_adjudication(archive_path: str | Path, decisions_path: str | Path, destination: str | Path) -> dict:
    """Bind complete finding mappings to immutable original evaluation bytes."""
    root, destination = Path(archive_path).resolve(), Path(destination).resolve()
    v.require(not destination.exists() and not destination.is_relative_to(root),
              "destination", "must be new and outside the original archive")
    result = copy.deepcopy(read_archive(root))
    parent_manifest = v.read_data(root / "manifest.json")
    decisions = _decisions(root, decisions_path, parent_manifest)
    _adjudicate_runs(root, result, decisions)
    manifest = v.read_data(root / "manifest.json")
    result["gate_evaluation"] = assess(manifest["plan"], result["runs"])
    # All validation precedes publication. The original archive remains byte-identical.
    return _publish(root, destination, result, manifest, decisions)


def _apply(run, original, decision):
    """Count canonical matched defects once and keep unmatched findings as false positives."""
    actual, expected, mappings = _finding_map(original, decision)
    # A match cannot cross criterion, source path or symbol; mechanism and impact are adjudicated.
    _finding_identity(actual, expected, mappings)
    hits = len({index for index in mappings if index is not None})
    unmatched = len({repr(sorted(finding.items())) for finding, index in zip(actual, mappings) if index is None})
    run["metrics"] = [_metric("precision", hits / (hits + unmatched) if hits + unmatched else None),
                      _metric("recall", hits / len(expected) if expected else None)]
    run["quality_passed"] = (original["response"]["criterion_results"] == original["reference"]["criterion_results"]
                             and hits == len(expected) and unmatched == 0)
    run["evaluation_status"] = "complete"


def _decisions(root, decisions_path, parent_manifest):
    """Validate adjudication provenance against the original archive."""
    v.require("adjudication_parent_sha256" not in parent_manifest, "adjudication",
              "publish each revised decision from the original archive")
    decisions = v.read_data(Path(decisions_path))
    v.require(decisions.get("schema_version") == 1, "adjudication", "unsupported schema")
    v.require(decisions.get("manifest_sha256") == digest(root / "manifest.json"),
              "adjudication", "original manifest differs")
    v.text(decisions.get("evaluator_id"), "adjudication.evaluator_id")
    v.text(decisions.get("version"), "adjudication.version")
    return decisions


def _adjudicate_runs(root, result, decisions):
    """Apply complete decisions to the selected original review runs."""
    entries = v.mapping(decisions.get("runs"), "adjudication.runs")
    runs = {run["run_id"]: run for run in result["runs"]}
    v.require(bool(entries) and set(entries) <= runs.keys(), "adjudication.runs", "unknown or empty selection")
    for identifier, decision in entries.items():
        _decision(root, runs, identifier, decision)


def _decision(root, runs, identifier, decision):
    """Bind one review decision to the exact original evaluation bytes."""
    v.mapping(decision, "adjudication.decision")
    run = runs[identifier]
    v.require(run["benchmark"] == "review_agent" and run["status"] == "completed",
              "adjudication.runs", "only completed reviews can be adjudicated")
    path, = [name for name in run["evidence"] if name.endswith("review-evaluation.json")]
    v.require(decision.get("evaluation_sha256") == digest(root / path),
              "adjudication.evaluation", "reference or response changed; reassess all affected answers")
    original = json.loads((root / path).read_text(encoding="utf-8"))
    _apply(run, original, decision)
    run["evidence"] = [*run["evidence"], "adjudication.json"]


def _derived_files(staged, root, destination, result, manifest, decisions):
    """Write a derived archive with its immutable adjudication parent."""
    write_json(staged / "adjudication.json", decisions)
    write_json(staged / "adjudication-parent.json", {"manifest": manifest, "results": read_archive(root)})
    result["output"] = str(destination)
    write_json(staged / "results.json", result)
    _report(staged / "report.md", result)
    manifest["adjudication_parent_sha256"] = decisions["manifest_sha256"]
    manifest["artifact_hashes"] = {k: val for k, val in inventory(staged).items() if k != "manifest.json"}
    write_json(staged / "manifest.json", manifest)


def _publish(root, destination, result, manifest, decisions):
    """Validate and atomically publish a complete derived review archive."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".adjudication-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "archive"
        shutil.copytree(root, staged)
        _derived_files(staged, root, destination, result, manifest, decisions)
        read_archive(staged)
        staged.rename(destination)
    return read_archive(destination)


def _finding_map(original, decision):
    """Require one valid canonical mapping per submitted finding."""
    v.text(decision.get("reason"), "adjudication.reason")
    mappings = decision.get("matches")
    actual, expected = original["response"].get("findings", []), original["reference"]["findings"]
    v.require(type(mappings) is list and len(mappings) == len(actual),
              "adjudication.matches", "one reference index or null per response finding required")
    v.require(all(index is None or type(index) is int and 0 <= index < len(expected) for index in mappings),
              "adjudication.matches", "invalid reference index")
    return (actual, expected, mappings)


def _finding_identity(actual, expected, mappings):
    """Keep adjudicated matches within the same source and criterion."""
    for finding, index in zip(actual, mappings):
        if index is not None:
            v.require(all(finding[key] == expected[index][key] for key in ("criterion_id", "path", "symbol")),
                      "adjudication.matches", "matched finding identifies different code or criterion")
