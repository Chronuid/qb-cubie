"""Capture repository and installed environment identities without claiming lock compliance."""

import hashlib
import importlib.metadata
import subprocess
from pathlib import Path

from qb_cubie.benchmarks.reporting._files import digest


def capture(source):
    """Keep commit, dirty state, declared lock and actual distributions distinct."""
    root = next((path for path in Path(source).resolve().parents if (path / ".git").exists()), None)
    value = {"repository_commit": None, "repository_dirty": None,
             "repository_diff_sha256": None, "dependency_lock_sha256": None,
             "dependency_lock_path": None, "dependency_lock_verified": False,
             "container_image_digest": None}
    _distributions(value)
    if root is None:
        return value
    _repository(root, value)
    _lock(root, value)
    return value


def _git(root, *arguments):
    """Read repository state with bounded execution and no optional git writes."""
    return subprocess.run(["git", "--no-optional-locks", "-C", str(root), *arguments],
                          check=True, capture_output=True, timeout=10).stdout


def _distributions(value):
    """Record the identity of the actual installed distributions."""
    packages = sorted((item.metadata["Name"].lower(), item.version)
                      for item in importlib.metadata.distributions() if item.metadata["Name"])
    value["installed_distributions_sha256"] = hashlib.sha256(repr(packages).encode()).hexdigest()


def _repository(root, value):
    """Record available repository state independently of declared dependencies."""
    try:
        commit = _git(root, "rev-parse", "HEAD").decode().strip()
        status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
        diff = _git(root, "diff", "HEAD", "--binary", "--no-ext-diff")
        value.update(repository_commit=commit, repository_dirty=bool(status),
                     repository_diff_sha256=hashlib.sha256(status + b"\0" + diff).hexdigest())
    except (OSError, subprocess.SubprocessError):
        pass


def _lock(root, value):
    """Record the first declared dependency lock without claiming compliance."""
    for name in ("uv.lock", "poetry.lock", "requirements.lock"):
        lock = root / name
        if lock.is_file():
            value.update(dependency_lock_path=name, dependency_lock_sha256=digest(lock))
            break
