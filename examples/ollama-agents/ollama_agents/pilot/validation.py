"""Compare selected trial cells and task material independently of calibration success."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.execution import _inputs
from qb_cubie.benchmarks.reporting._files import inventory
from qb_cubie.benchmarks.reporting.archives import read_archive


def calibration(roots):
    """Verify every declared archive and retain all its started observations."""
    v.require(type(roots) is list and bool(roots), "calibration", "expected nonempty archive paths")
    entries: list[tuple[Path, dict]] = []
    seen = set()
    for root in roots:
        v.require(root.is_dir() and not any(p.is_symlink() for p in root.rglob("*")),
                  "calibration.archive", "expected a regular archive without symlinks")
        result = read_archive(root)
        for run in result["runs"]:
            v.choice(run.get("status"), v.STATUSES, "calibration.status")
        v.require(result["run_id"] not in seen, "calibration", "duplicate archive")
        seen.add(result["run_id"])
        entries.extend((root, run) for run in result["runs"])
    cells([run for _, run in entries], 2, "calibration")
    return entries


def cells(runs, repetitions, label):
    """Require exactly one started observation per required repeat in each cell."""
    grouped = defaultdict(list)
    for run in runs:
        grouped[cell(run)].append(run["repetition"])
        v.require(run.get("status") != "not_started", label, "calibration trial was not started")
    v.require(bool(grouped), label, "empty selection")
    v.require(all(sorted(values) == list(range(1, repetitions + 1)) for values in grouped.values()),
              label, f"expected exactly {repetitions} repetitions per selected cell")
    return set(grouped)


def cell(run):
    """Identify one task, benchmark, agent identity and comparison condition."""
    return tuple(run[key] for key in ("scenario_id", "benchmark", "agent_id", "condition"))


def validate_pilot(bundle, manifest, entries, exploratory):
    """Validate the captured pilot rather than mutable pre-freeze source files."""
    planned = manifest["plan"]["runs"]
    v.require(cells(planned, 5, "pilot") == {cell(run) for _, run in entries},
              "calibration.selection", "pilot scenario, agent or condition cells differ")
    materials = _materials(bundle)
    for run in planned:
        material = materials[run["scenario_id"]]
        if not exploratory:
            v.require(material["reference"]["validation_status"] == "independently_checked",
                      "reference_admission", "independently_checked references required for official pilot")
    _compare(entries, materials, planned)


def _materials(bundle):
    """Resolve the immutable archived packages using the existing contract validator."""
    return _inputs._scenarios(list((bundle / "inputs/packages").iterdir()))


def _compare(entries, materials, planned):
    """Allow new admission receipts and tuning while binding task and evaluator contents."""
    by_cell = {cell(run): run for run in planned}
    cached = {}
    for root, run in entries:
        if root not in cached:
            cached[root] = _materials(root)
        expected = by_cell[cell(run)]
        identity = lambda item: {key: item["package"][key] for key in ("namespace", "version")}
        v.require(identity(run) == identity(expected), "calibration.version", "package identity changed")
        name = run["scenario_id"]
        v.require(_signature(cached[root][name]) == _signature(materials[name]),
                  "calibration.material", f"task, source or evaluator material changed: {name}")


def _signature(material):
    """Exclude only admission metadata, its declared receipts and tunable scenario budgets."""
    scenario, reference, base = (material[key] for key in ("scenario", "reference", "base"))
    omitted = {scenario["evaluator"]["reference"], Path(scenario["manifest"]).name}
    omitted.update(review["evidence"] for review in reference.get("human_reviews", []))
    files = {name: (checksum, (base / name).stat().st_mode & 0o777)
             for name, checksum in inventory(base).items() if name not in omitted}
    return {"scenario": {key: value for key, value in scenario.items() if key != "budgets"},
            "reference": {key: value for key, value in reference.items()
                          if key not in {"validation_status", "human_reviews"}}, "files": files}


def chronological(entries, frozen_at):
    """Reject future or malformed calibration timestamps before publishing the pilot."""
    cutoff = datetime.fromisoformat(frozen_at)
    for _, run in entries:
        try:
            start, finish = (datetime.fromisoformat(run[key]) for key in ("started_at", "finished_at"))
            v.require(start.tzinfo is not None and finish.tzinfo is not None and start <= finish <= cutoff,
                      "calibration.time", "started calibration must finish before pilot freeze")
        except (TypeError, KeyError) as error:
            raise ValueError(f"calibration.time: malformed timestamps: {error}") from error
