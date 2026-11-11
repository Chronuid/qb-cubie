"""Bind frozen files, permission modes, runtime identity and planned trial semantics."""

import hashlib
import platform
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.reporting._files import digest, wheel_hash
from qb_cubie.benchmarks.measurement.provenance import capture


def files(root):
    """Inventory every frozen file except the manifest itself, including unexpected files."""
    return {path.relative_to(root).as_posix(): digest(path) for path in sorted(root.rglob("*"))
            if path.is_file() and path != root / "measurement.json"}


def modes(root):
    """Record file and directory permission modes that participate in package identity."""
    return {path.relative_to(root).as_posix(): path.stat().st_mode & 0o777 for path in sorted(root.rglob("*"))
            if path != root / "measurement.json"}


def runtime():
    """Record runtime provenance without inventing a lockfile or wheel identity."""
    return {"python_version": platform.python_version(), "wheel_sha256": wheel_hash(),
            "source_sha256": _source_hash(), **capture(__file__)}


def _source_hash():
    """Bind the installed Python implementation even when running from an editable checkout."""
    root, checksum = Path(__file__).resolve().parents[2], hashlib.sha256()
    for directory, children, names in root.walk():
        children[:] = sorted(name for name in children if name not in {"__pycache__", "arena_envs"})
        for name in sorted(names):
            path = directory / name
            if path.suffix == ".py":
                for value in (path.relative_to(root).as_posix().encode(), path.read_bytes()):
                    checksum.update(len(value).to_bytes(8, "big") + value)
    return checksum.hexdigest()


def portable(plan):
    """Remove only the per-execution output path from the frozen plan identity."""
    return {**plan, "output": "results"}


def verify(root):
    """Verify complete file coverage and modes before permitting an adapter start."""
    manifest = v.read_data(root / "measurement.json")
    expected = v.mapping(manifest.get("files"), "measurement.files")
    for name in expected:
        v.contained(root, name, "measurement.files")
    v.require(not any(path.is_symlink() for path in root.rglob("*")), "measurement", "symlinks unsupported")
    v.require(files(root) == expected, "measurement.hash", "frozen files changed, missing or additional")
    v.require(modes(root) == manifest.get("modes"), "measurement.modes", "frozen permission modes changed")
    v.contained(root, manifest.get("suite"), "measurement.suite")
    v.mapping(manifest.get("runtime"), "measurement.runtime")
    v.mapping(manifest.get("plan"), "measurement.plan")
    return manifest


def check_runtime(recorded):
    """Require known runtime identities to match rather than silently changing environments."""
    v.text(recorded.get("python_version"), "measurement.runtime.python_version")
    v.text(recorded.get("source_sha256"), "measurement.runtime.source_sha256")
    current = runtime()
    for key in ("python_version", "wheel_sha256", "source_sha256", "installed_distributions_sha256", "dependency_lock_sha256"):
        v.require(recorded.get(key) is None or recorded[key] == current[key], "measurement.runtime", f"different {key}")
