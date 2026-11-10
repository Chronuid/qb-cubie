"""Keep complete adapter evidence in separate, sealed per-session archives."""

import math
import os
import sys
import tempfile
from pathlib import Path

from .errors import infrastructure, invalid
from .jsonio import digest, encode
from .paths import absolute, directory, guard


class EvidenceWriter:
    """Archive internal steps without polluting the visible workspace or JSONL stdout."""

    def __init__(self, *, archive_root, workspace):
        try:
            self._root = _archive(archive_root, workspace)
            self._steps: list[str] = []
            self._hashes: dict[str, str] = {}
            self._summary: dict[str, str] | None = None
        except OSError as error:
            raise infrastructure(f"Cannot create evidence archive: {error}") from error

    def record_step(self, *, phase, request, raw_response, action, tool_result,
                    artifact_hashes, duration_seconds, usage, status):
        """Persist one complete internal step before adding it to the manifest."""
        if self._summary is not None:
            raise infrastructure("Evidence archive is already finalized")
        _duration(duration_seconds)
        record = {"phase": phase, "request": request, "raw_response": raw_response, "action": action,
                  "tool_result": tool_result, "artifact_hashes": artifact_hashes,
                  "duration_seconds": duration_seconds, "usage": usage, "status": status}
        body = _serialize(record)
        name = f"step-{len(self._steps) + 1:06d}.json"
        self._write(name, body)
        self._steps.append(name)
        self._hashes[name] = digest(body)

    def finalize(self):
        """Seal the archive and emit only its small hash-bound diagnostic summary."""
        try:
            self._verify()
            if self._summary is None:
                self._summary = self._seal()
            result = dict(self._summary)
            print(encode(result).decode("utf-8"), file=sys.stderr, flush=True)
            return result
        except OSError as error:
            raise infrastructure(f"Cannot finalize evidence archive: {error}") from error

    def _seal(self):
        """Publish a manifest bound to the exact recorded evidence files."""
        manifest = {"schema_version": 1, "archive_id": self._root.name,
                    "steps": self._steps, "artifact_hashes": self._hashes}
        body = _serialize(manifest)
        self._write("manifest.json", body)
        return {"archive_id": self._root.name, "manifest_path": str(self._root / "manifest.json"),
                "manifest_sha256": digest(body)}

    def _write(self, name, body):
        """Atomically store one private evidence file under the checked archive root."""
        try:
            directory(self._root)
            target = guard(self._root / name)
            if target.exists():
                raise infrastructure(f"Evidence target already exists: {name}")
            _atomic(target, body)
        except OSError as error:
            raise infrastructure(f"Cannot write evidence file {name}: {error}") from error

    def _verify(self):
        """Detect missing, added, symlinked or modified evidence before sealing."""
        directory(self._root)
        expected = dict(self._hashes)
        if self._summary is not None:
            expected["manifest.json"] = self._summary["manifest_sha256"]
        if {p.name for p in self._root.iterdir()} != set(expected):
            raise infrastructure("Evidence archive contains missing or unexpected files")
        for name, identity in expected.items():
            path = guard(self._root / name)
            if not path.is_file() or digest(path.read_bytes()) != identity:
                raise infrastructure(f"Evidence hash mismatch: {name}")


def _archive(archive_root, workspace):
    """Allocate a fresh private archive outside the resolved visible workspace."""
    visible, parent = absolute(workspace).resolve(), absolute(archive_root)
    if parent.resolve().is_relative_to(visible):
        raise invalid("Evidence archive must be outside the visible workspace")
    guard(parent)
    parent.mkdir(parents=True, exist_ok=True)
    directory(parent)
    return Path(tempfile.mkdtemp(prefix="episode-", dir=parent))


def _atomic(target, body):
    """Publish evidence bytes only after flushing the complete temporary file."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".pending-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _serialize(record):
    """Reject unrepresentable evidence before modifying archive contents."""
    try:
        return encode(record)
    except (TypeError, ValueError, RecursionError) as error:
        raise infrastructure(f"Cannot serialize evidence JSON: {error}") from error


def _duration(value):
    """Require a measured finite nonnegative step duration."""
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise infrastructure("Evidence duration must be finite and nonnegative")
