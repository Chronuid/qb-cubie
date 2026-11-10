"""Create real suites and archives with explicitly synthetic admission receipts."""

import hashlib
import json
from pathlib import Path

from qb_cubie.benchmarks import init_smoke_suite, run_suite

from ...benchmarks.contracts import accepted, edit_json


def read_json(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def suite_at(root, *, repetitions=2, profile="agent-evaluation", behavior="reference",
             benchmark="review_agent"):
    suite = root / "sets/study.toml"
    init_smoke_suite(suite)
    text = suite.read_text(encoding="utf-8")
    text = text.replace("repetitions = 1", f"repetitions = {repetitions}\nseed = 42")
    text = text.replace('profile = "agent-evaluation"', f'profile = "{profile}"')
    text = text.replace("max_runs = 3", "max_runs = 100")
    text = text.replace("max_total_wall_time_seconds = 60", "max_total_wall_time_seconds = 2000")
    suite.write_text(text + f'\n[select]\nbenchmarks = ["{benchmark}"]\n', encoding="utf-8")
    agent = root / "agents/fake.toml"
    agent.write_text(agent.read_text(encoding="utf-8").replace('behavior = "reference"',
                                                           f'behavior = "{behavior}"'), encoding="utf-8")
    return suite


def reference_paths(suite):
    return sorted((suite.parent.parent / "scenarios/smoke/scenarios").glob("*/evaluator/reference.json"))


def admit_references(suite):
    for reference in reference_paths(suite):
        directory = reference.parent / "reviews"
        directory.mkdir(exist_ok=True)
        receipts = []
        for identity in ("human-a", "human-b"):
            (directory / f"{identity}.md").write_text(
                "SYNTHETIC TEST RECEIPT: no human admission has taken place.\n", encoding="utf-8")
            receipts.append({"reviewer_id": identity, "decision": "approve",
                             "evidence": f"evaluator/reviews/{identity}.md"})
        edit_json(reference, lambda value, receipts=receipts: value.update(
            validation_status="independently_checked", human_reviews=receipts))


def calibrate(suite):
    result = accepted(run_suite, suite, expected=lambda value: bool(value["runs"]))
    return Path(result["output"])


def set_repetitions(suite, value):
    text = suite.read_text(encoding="utf-8")
    current = next(line for line in text.splitlines() if line.startswith("repetitions ="))
    suite.write_text(text.replace(current, f"repetitions = {value}"), encoding="utf-8")


def pilot_inputs(root, **options):
    suite = suite_at(root, **options)
    archive = calibrate(suite)
    set_repetitions(suite, 5)
    admit_references(suite)
    return suite, archive


def freeze(freeze_pilot, suite, archives, destination):
    return accepted(lambda: freeze_pilot(calibration_archives=archives, suite_path=suite,
                                        destination=destination), expected=lambda value: (
        value["schema_version"] == 1 and value["path"] == str(destination.resolve())
        and value["measurement_sha256"] == digest(destination / "measurement.json")))
