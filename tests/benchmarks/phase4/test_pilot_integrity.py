"""Exercise incompatible evaluator pools and incomplete hash inventories."""

import json

from ..contracts import rejected
from .conftest import read_json, replace_observation


def test_same_task_with_different_evaluator_versions_is_not_pooled(pilot_archive, public_api):
    runs = read_json(pilot_archive / "results.json")["runs"]
    index = next(index for index, run in enumerate(runs) if run["repetition"] == 2)
    replace_observation(pilot_archive, index, evaluator_version="simulated-new-evaluator")
    rejected(public_api("summarize_pilot"), [pilot_archive], match="incompatible|evaluator|identity")


def test_cited_evidence_cannot_be_removed_from_the_hash_inventory(pilot_archive, public_api):
    run = read_json(pilot_archive / "results.json")["runs"][0]
    manifest = read_json(pilot_archive / "manifest.json")
    del manifest["artifact_hashes"][run["evidence"][0]]
    (pilot_archive / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    rejected(public_api("summarize_pilot"), [pilot_archive], match="hash|evidence")


def test_declared_source_identity_must_match_actual_archived_content(pilot_archive, public_api):
    replace_observation(pilot_archive, 0, source_tree_sha256="f" * 64, context_sha256="f" * 64)
    rejected(public_api("summarize_pilot"), [pilot_archive], match="source|context|hash")
