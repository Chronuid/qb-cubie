"""Persist deterministic benchmark data and content identities."""

import hashlib
import importlib.metadata
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse


def now():
    """Return the current UTC timestamp."""
    return datetime.now(UTC).isoformat()


def write_json(path, value):
    """Persist a deterministic finite JSON document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return path


def digest(path):
    """Return the SHA-256 digest of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    """Map archived file paths to their content digests."""
    return {path.relative_to(root).as_posix(): digest(path)
            for path in sorted(root.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}


def tree_hash(root):
    """Identify a logical file tree including paths and permission modes."""
    value = [(name, (root / name).stat().st_mode & 0o777, checksum)
             for name, checksum in inventory(root).items()]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def copy_tree(source, destination):
    """Copy material without generated Python and pytest caches."""
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    return destination


def wheel_hash():
    """Identify the installed wheel from recorded installation provenance."""
    try:
        data = importlib.metadata.distribution("qb-cubie").read_text("direct_url.json")
        origin = json.loads(data or "{}")
        url = urlparse(origin.get("url", ""))
        if url.scheme == "file" and url.path.endswith(".whl"):
            return _wheel_digest(origin, Path(unquote(url.path)))
    except (importlib.metadata.PackageNotFoundError, OSError, ValueError):
        return None
    return None


def _wheel_digest(origin, path):
    """Resolve a wheel digest from its archive or installation metadata."""
    if path.is_file():
        return digest(path)
    return origin.get("archive_info", {}).get("hashes", {}).get("sha256")
