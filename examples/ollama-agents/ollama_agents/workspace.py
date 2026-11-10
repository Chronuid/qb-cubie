"""Apply explicit file grants to workspace reads, proposals and artifact hashes."""

from .errors import infrastructure, invalid
from .jsonio import digest
from .paths import directory, file_path, names, relative
from .transaction import WriteTransaction


class WorkspacePolicy:
    """Constrain file access to an explicit visible workspace and phase grant."""

    def __init__(self, *, root, readable, writable):
        try:
            self._root = directory(root)
            self._readable = names(readable)
            self._writable = names(writable)
        except OSError as error:
            raise infrastructure(f"Cannot inspect workspace paths: {error}") from error

    @property
    def readable(self):
        """Expose the immutable read grant for source inventory."""
        return self._readable

    def read_file(self, name):
        """Return exact bytes from a permitted regular source file."""
        try:
            return self._target(name, self._readable).read_bytes()
        except OSError as error:
            raise infrastructure(f"Cannot read workspace file: {error}") from error

    def write_files(self, files):
        """Validate and publish a whole proposal with rollback on handled failures."""
        try:
            prepared = self._proposal(files)
            return WriteTransaction(self._root, prepared, self._writable).run()
        except OSError as error:
            raise infrastructure(f"Workspace write or commit failed: {error}") from error

    def artifact_hashes(self, paths):
        """Hash the bytes currently stored at permitted artifact paths."""
        try:
            grant = self._readable | self._writable
            return {name: digest(self._target(name, grant).read_bytes()) for name in sorted(names(paths))}
        except OSError as error:
            raise infrastructure(f"Cannot hash workspace artifact: {error}") from error

    def _target(self, name, grant):
        """Recheck root, permission and path components for every access."""
        relative(name)
        if name not in grant:
            raise invalid(f"File path is not allowed by this phase's permissions: {name}")
        directory(self._root)
        return file_path(self._root, name)

    def _proposal(self, files):
        """Prepare every destination and byte string before any directory changes."""
        if not isinstance(files, dict) or not files:
            raise invalid("write_files requires a nonempty files object")
        prepared = {}
        for name, content in files.items():
            self._target(name, self._writable)
            if not isinstance(content, str):
                raise invalid(f"File content must be a string: {name}")
            prepared[name] = _utf8(content, name)
        _conflicts(prepared)
        return prepared


def _utf8(content, name):
    """Reject file text that cannot be encoded losslessly as UTF-8."""
    try:
        return content.encode("utf-8")
    except UnicodeError as error:
        raise invalid(f"Invalid file content encoding for {name}: {error}") from error


def _conflicts(files):
    """Reject proposals that use the same path as a file and a parent directory."""
    for name in files:
        parts = name.split("/")
        if any("/".join(parts[:index]) in files for index in range(1, len(parts))):
            raise invalid(f"Conflicting file and parent paths in write proposal: {name}")
