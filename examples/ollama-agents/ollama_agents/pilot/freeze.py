"""Publish a portable calibrated pilot atomically, with an explicit exploratory mode."""

import shutil
import tempfile
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.measurement import _bundle
from qb_cubie.benchmarks.measurement.frozen import freeze_suite
from qb_cubie.benchmarks.reporting._files import digest, now, write_json

from .validation import calibration, chronological, validate_pilot


def freeze_pilot(*, calibration_archives, suite_path, destination, exploratory=False):
    """Require two calibration repeats and freeze five measurement repeats per selected cell."""
    destination = Path(destination).resolve()
    v.require(type(exploratory) is bool, "exploratory", "expected an explicit boolean")
    v.require(not destination.exists(), "destination", "already exists; refusing overwrite")
    v.require(type(calibration_archives) is list, "calibration", "expected archive paths")
    roots = [Path(path).resolve() for path in calibration_archives]
    calibration(roots)
    v.require(not any(destination.is_relative_to(root) for root in roots), "destination", "inside calibration archive")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pilot-", dir=destination.parent) as temporary:
        bundle = _stage(Path(temporary), suite_path, roots, exploratory)
        bundle.rename(destination)
    return {"schema_version": 1, "path": str(destination), "measurement_sha256": digest(destination / "measurement.json")}


def _stage(temporary, suite, roots, exploratory):
    """Verify copied calibration and task snapshots before publishing any destination."""
    bundle = temporary / "bundle"
    freeze_suite(suite, bundle)
    manifest = _bundle.verify(bundle)
    receipts = [_copy(root, bundle, index) for index, root in enumerate(roots)]
    entries = calibration([bundle / receipt["path"] for receipt in receipts])
    validate_pilot(bundle, manifest, entries, exploratory)
    frozen_at = now()
    chronological(entries, frozen_at)
    manifest["pilot"] = _receipt(receipts, frozen_at, exploratory)
    manifest.update(files=_bundle.files(bundle), modes=_bundle.modes(bundle))
    write_json(bundle / "measurement.json", manifest)
    _bundle.verify(bundle)
    return bundle


def _copy(source, bundle, index):
    """Bind each complete calibration archive to its verified pre-copy manifest."""
    checksum = digest(source / "manifest.json")
    relative = f"inputs/calibration/{index}"
    shutil.copytree(source, bundle / relative)
    v.require(digest(bundle / relative / "manifest.json") == checksum == digest(source / "manifest.json"),
              "calibration.hash", "archive changed during copy")
    return {"path": relative, "manifest_sha256": checksum}


def _receipt(receipts, frozen_at, exploratory):
    """Distinguish a structurally admitted official pilot from exploratory measurements."""
    return {"calibration_repetitions": 2, "measurement_repetitions": 5,
            "reference_admission": "author_checked" if exploratory else "independently_checked",
            "study_kind": "exploratory" if exploratory else "official",
            "frozen_at": frozen_at, "calibration_archives": receipts}
