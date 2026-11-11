"""Stage complete workspace proposals and recover earlier commits after I/O failures."""

import os
import shutil
import tempfile
from pathlib import Path

from .errors import AdapterError, infrastructure
from .jsonio import digest
from .paths import directory, file_path


class WriteTransaction:
    """Publish prepared file contents while retaining backups until successful completion."""

    def __init__(self, root, files, writable):
        self._root, self._files, self._writable = root, files, writable
        self._staging = None
        self._backups = {}
        self._published = []
        self._directories = []

    def run(self):
        """Stage all changes, publish them and restore originals on execution failure."""
        self._staging = Path(tempfile.mkdtemp(prefix=".cubie-stage-", dir=self._root))
        try:
            self._prepare()
            result = self._commit()
        except BaseException as error:
            self._recover(error)
            raise
        self._cleanup()
        return result

    def _prepare(self):
        """Retain original metadata and stage all new bytes before publication."""
        for index, (name, content) in enumerate(self._files.items()):
            target = self._target(name)
            staged = self._stage(index, "new")
            staged.write_bytes(content)
            backup = self._stage(index, "old") if target.exists() else None
            if backup is not None:
                shutil.copy2(target, backup)
                shutil.copymode(target, staged)
            self._backups[name] = backup

    def _commit(self):
        """Replace targets individually and then hash the actual committed bytes."""
        for index, name in enumerate(self._files):
            target = self._target(name)
            self._parents(target.parent)
            os.replace(self._stage(index, "new"), self._target(name))
            self._published.append(name)
        return {name: digest(self._target(name).read_bytes()) for name in self._files}

    def _target(self, name):
        """Recheck the root and file path at the transaction boundary."""
        directory(self._root)
        if name not in self._writable:
            raise infrastructure(f"Write grant changed during commit: {name}")
        return file_path(self._root, name)

    def _stage(self, index, suffix):
        """Locate one private staging file in the current transaction."""
        if self._staging is None:
            raise RuntimeError("Transaction staging is not initialized")
        return self._staging / f"{index}.{suffix}"

    def _parents(self, parent):
        """Create and track missing parent directories for rollback."""
        missing = []
        while parent != self._root and not parent.exists():
            missing.append(parent)
            parent = parent.parent
        for path in reversed(missing):
            path.mkdir()
            self._directories.append(path)

    def _recover(self, original):
        """Attempt every restoration and retain backup files if recovery is incomplete."""
        failures: list[str] = []
        for name in reversed(self._published):
            _attempt(lambda name=name: self._restore(name), failures)
        for path in reversed(self._directories):
            _attempt(path.rmdir, failures)
        if failures:
            raise infrastructure(f"Commit failed ({original}); rollback incomplete ({failures}); "
                                 f"recovery files retained at {self._staging}") from original
        self._cleanup()

    def _restore(self, name):
        """Restore one published target or remove a newly created file."""
        target = self._target(name)
        backup = self._backups[name]
        if backup is None:
            target.unlink()
        else:
            os.replace(backup, target)

    def _cleanup(self):
        """Remove staging data only after publication or complete recovery."""
        if self._staging is not None:
            shutil.rmtree(self._staging)


def _attempt(operation, failures):
    """Collect a recovery failure without preventing the remaining restorations."""
    try:
        operation()
    except (OSError, AdapterError) as error:
        failures.append(str(error))
