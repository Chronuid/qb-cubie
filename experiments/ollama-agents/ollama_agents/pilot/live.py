"""Run an explicitly exploratory two-plus-five study on the public Ollama smoke set."""

import argparse
import json
import sys
import tomllib
from pathlib import Path

from cubie_benchmarks import run_frozen_suite, summarize_pilot
from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.measurement._toml import write_toml
from cubie_benchmarks.measurement.frozen import freeze_suite
from cubie_benchmarks.reporting._files import inventory, now, write_json
from cubie_benchmarks.scaffolding.ollama import init_ollama

from .freeze import freeze_pilot
from .observations import environment, verify_evidence, warmup


def measure_smoke(destination, *, endpoint="http://localhost:11434", model="gemma4:12b", exploratory=False):
    """Preserve all public-set attempts and keep official human admission explicitly open."""
    v.require(exploratory is True, "exploratory", "public smoke study requires explicit exploratory=True")
    root = Path(destination).resolve()
    v.require(not root.exists(), "destination", "already exists; refusing overwrite")
    init_ollama(root / "example", endpoint=endpoint, model=model)
    _configure(root)
    study = {"schema_version": 1, "study_kind": "exploratory", "human_admission": False,
             "public_development_material": True, "started_at": now(), "stages": []}
    write_json(root / "study.json", study)
    try:
        _measure(root, study, endpoint)
    except (ValueError, OSError, KeyboardInterrupt) as error:
        write_json(root / "interrupted.json", {"at": now(), "reason": str(error), "type": type(error).__name__})
        raise
    study["finished_at"] = now()
    write_json(root / "study.json", study)
    write_json(root / "evidence-manifest.json", {"schema_version": 1, "artifact_hashes": inventory(root)})
    return study


def _configure(root):
    """Keep adapter evidence outside disposable frozen execution copies."""
    for role in ("reviewer", "developer"):
        path = root / f"example/adapter/{role}.json"
        config = json.loads(path.read_bytes())
        config["archive_root"] = str(root / f"adapter-evidence/{role}")
        write_json(path, config)
        for stage, repetitions in (("calibration", 2), ("pilot", 5)):
            _suite(root, role, stage, repetitions)


def _suite(root, role, stage, repetitions):
    """Select the same public task cells, with declared seeds and complete run budgets."""
    original = root / f"example/sets/{role}.toml"
    data = tomllib.loads(original.read_text(encoding="utf-8"))
    data.update(name=f"{role}-{stage}", repetitions=repetitions, seed=42)
    data["limits"] = {key: value * repetitions for key, value in data["limits"].items()}
    write_toml(original.with_name(f"{role}-{stage}.toml"), data)


def _measure(root, study, endpoint):
    """Finish all calibrations before freezing either pilot; run measurements serially."""
    calibrations = {}
    models = {role: json.loads((root / f"example/adapter/{role}.json").read_bytes())["model"]
              for role in ("reviewer", "developer")}
    write_json(root / "environment-initial.json", environment(endpoint, models["reviewer"]["model_id"], models["reviewer"]))
    for role, model in models.items():
        warmup(root / f"preflight/{role}.json", endpoint, model)
        bundle = root / f"frozen/{role}-calibration"
        freeze_suite(root / f"example/sets/{role}-calibration.toml", bundle)
        calibrations[role] = _run(root, study, endpoint, model, role, "calibration", bundle)
    for role in models:
        freeze_pilot(calibration_archives=[calibrations[role]],
                     suite_path=root / f"example/sets/{role}-pilot.toml",
                     destination=root / f"frozen/{role}-pilot", exploratory=True)
    for role, model in models.items():
        _run(root, study, endpoint, model, role, "pilot", root / f"frozen/{role}-pilot")


def _run(root, study, endpoint, model, role, stage, bundle):
    """Journal the started batch before execution and retain failed individual attempts."""
    label = f"{role}-{stage}"
    record = {"role": role, "stage": stage, "status": "started", "started_at": now(),
              "bundle": str(bundle.relative_to(root)), "output_parent": f"results/{label}"}
    study["stages"].append(record)
    write_json(root / "study.json", study)
    write_json(root / f"environment/{label}-before.json", environment(endpoint, model["model_id"], model))
    print(f"Starting {label}", file=sys.stderr, flush=True)
    result = run_frozen_suite(bundle, root / record["output_parent"])
    archive = Path(result["output"])
    evidence = verify_evidence(archive)
    write_json(root / f"summaries/{label}.json", summarize_pilot([archive]))
    write_json(root / f"environment/{label}-after.json", environment(endpoint, model["model_id"], model))
    record.update(status="archived", finished_at=now(), archive=str(archive.relative_to(root)), evidence=evidence,
                  evidence_complete=len(evidence) == len(result["runs"]))
    write_json(root / "study.json", study)
    print(f"Archived {label}: {len(result['runs'])} attempts", file=sys.stderr, flush=True)
    return archive


def main(argv=None):
    """Require explicit opt-in before creating a study or calling a provider."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    parser.add_argument("--endpoint", default="http://localhost:11434")
    parser.add_argument("--model", default="gemma4:12b")
    parser.add_argument("--exploratory", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        result = measure_smoke(args.destination, endpoint=args.endpoint, model=args.model, exploratory=args.exploratory)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(f"Study error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
