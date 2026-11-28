"""Domain-neutral workspace discovery, exclude matching, atomic writes, and WorkspaceView ports."""

from __future__ import annotations

from collections.abc import Iterable, Sequence, Set as AbstractSet
from dataclasses import dataclass
import os
from pathlib import Path
import posixpath
import tempfile
from typing import Any, Final, Protocol, runtime_checkable

from .guards import validate_str_sequence

DEFAULT_EXCLUDES: Final[tuple[str, ...]] = (".venv", "__pycache__", ".git")
_MD_PREFIXES: Final[tuple[str, ...]] = ("#", "`", "~", "<", ">", "-", "*", "+", "!", "[", "|")


@dataclass(frozen=True)
class FileSource:
    """Immutable source record holding canonical path, POSIX rel_path, and UTF-8 content."""

    path: str
    rel_path: str
    content: str


@runtime_checkable
class WorkspaceView(Protocol):
    """Pure read-only workspace membership port decoupling domain logic from filesystem I/O."""

    @property
    def root(self) -> Path: ...

    def has_path(self, rel_or_abs: str | Path) -> bool: ...


class InMemoryWorkspaceView:
    """In-memory WorkspaceView implementation supporting files, directories, and relative paths."""

    def __init__(self, root: Path, paths: Iterable[str] = ()) -> None:
        """Initialize an in-memory path index rooted at root."""
        self._root = Path(root)
        self._known = self._expand_paths(paths)

    @property
    def root(self) -> Path:
        """Return the virtual root directory for this workspace view."""
        return self._root

    def has_path(self, rel_or_abs: str | Path) -> bool:
        """Check whether rel_or_abs exists in the indexed file or parent directory set."""
        rel = self._normalize_query(rel_or_abs)
        return rel is not None and (rel == "." or rel in self._known)

    @staticmethod
    def _expand_paths(paths: Iterable[str]) -> frozenset[str]:
        """Collect all normalized file paths and their ancestor directories."""
        known: set[str] = set()
        for raw in paths:
            norm = posixpath.normpath(str(raw).replace("\\", "/")).lstrip("/")
            if not norm or norm in (".", "..") or norm.startswith("../"):
                continue
            known.add(norm)
            parent = posixpath.dirname(norm)
            while parent and parent not in (".", "/"):
                known.add(parent)
                parent = posixpath.dirname(parent)
        return frozenset(known)

    def _normalize_query(self, rel_or_abs: str | Path) -> str | None:
        """Normalize a relative or absolute path query relative to self._root."""
        candidate = Path(rel_or_abs)
        if candidate.is_absolute():
            rel = self._strip_root(candidate)
            if rel is None:
                return None
            raw = rel
        else:
            raw = str(rel_or_abs).replace("\\", "/")
        norm = posixpath.normpath(raw).lstrip("/")
        return None if norm == ".." or norm.startswith("../") else (norm or ".")

    def _strip_root(self, candidate: Path) -> str | None:
        """Relativize an absolute path against self._root without touching the filesystem."""
        try:
            return candidate.relative_to(self._root).as_posix()
        except ValueError:
            return None


class FileSystemWorkspaceView:
    """Filesystem-backed WorkspaceView adapter for imperative shells."""

    def __init__(self, root: Path) -> None:
        """Initialize a filesystem-backed workspace view rooted at root."""
        self._root = Path(root).resolve()

    @property
    def root(self) -> Path:
        """Return the resolved root directory on disk."""
        return self._root

    def has_path(self, rel_or_abs: str | Path) -> bool:
        """Check whether the resolved relative or absolute path exists on disk."""
        candidate = Path(rel_or_abs)
        target = candidate if candidate.is_absolute() else (self._root / candidate)
        return target.exists()


def find_project_root(
    start: Path | None = None,
    *,
    markers: Sequence[str] = ("pyproject.toml",),
    stop_at_cwd: bool = False,
) -> Path:
    """Search upward from start (or CWD) for the nearest directory containing any marker."""
    origin = (start if start is not None else Path.cwd()).resolve()
    if origin.is_file():
        origin = origin.parent
    cwd = Path.cwd().resolve()
    for directory in (origin, *origin.parents):
        if any((directory / marker).exists() for marker in markers):
            return directory
        if stop_at_cwd and directory == cwd:
            break
    return origin


def normalize_excludes(excludes: Any, *, base: Iterable[str] = DEFAULT_EXCLUDES) -> frozenset[str]:
    """Validate user excludes as a sequence of strings and merge them with base excludes."""
    validated = validate_str_sequence(excludes, "excludes", allow_none=True)
    return frozenset(base) | frozenset(validated)


def is_excluded(rel_path: Path, root_name: str, excludes: AbstractSet[str]) -> bool:
    """Check whether rel_path matches any segment, subpath, or root-prefixed exclude."""
    rel_posix = rel_path.as_posix()
    for excl in excludes:
        stripped = excl.replace("\\", "/").strip("/")
        if not stripped:
            continue
        norm = stripped.removeprefix(f"{root_name}/")
        if rel_posix == norm or rel_posix.startswith(f"{norm}/"):
            return True
        if "/" not in stripped and norm in rel_path.parts:
            return True
    return False


def crawl_files(
    root: Path,
    *,
    pattern: str = "*.md",
    excludes: AbstractSet[str] = frozenset(),
) -> list[Path]:
    """Recursively collect deterministically sorted files matching pattern while honoring excludes."""
    resolved = _validate_crawl_dir(root)
    matched = [
        path
        for path in resolved.rglob(pattern)
        if path.is_file() and not is_excluded(path.relative_to(resolved), resolved.name, excludes)
    ]
    return sorted(matched, key=lambda path: path.relative_to(resolved).as_posix())


def _validate_crawl_dir(root: Path) -> Path:
    """Ensure root is an existing directory Path and return its resolved path."""
    if not isinstance(root, Path):
        raise TypeError(f"STATE-GUARD: root must be a Path; received {type(root).__name__}.")
    if not root.exists():
        raise FileNotFoundError(f"STATE-GUARD: Directory does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"STATE-GUARD: Expected directory for crawl_files; received file: {root}")
    return root.resolve()


def looks_like_path(target: str) -> bool:
    """Distinguish single-line filesystem path strings from inline in-memory text."""
    stripped = target.strip()
    if "\n" in stripped or stripped.startswith(_MD_PREFIXES) or "](" in stripped or "://" in stripped:
        return False
    if Path(stripped).exists() or stripped.lower().endswith((".md", ".markdown")):
        return True
    if " " not in stripped:
        return any(ch in stripped for ch in ("/", "\\", ".", "_", "-"))
    first = stripped.split()[0]
    return ("/" in first or "\\" in first) and not stripped.endswith((".", "!", "?"))


def load_sources(
    target: Any,
    *,
    pattern: str = "*.md",
    excludes: AbstractSet[str] = frozenset(),
    allow_in_memory: bool = False,
) -> list[FileSource]:
    """Resolve target to one or more FileSource records with strict path and non-empty guards."""
    if isinstance(target, Path):
        return _load_path_sources(target, pattern, excludes)
    if isinstance(target, str):
        if not target.strip():
            raise ValueError("STATE-GUARD: Target string must not be empty.")
        if allow_in_memory and not looks_like_path(target):
            return [FileSource(path="IN_MEMORY", rel_path="IN_MEMORY", content=target)]
        return _load_path_sources(Path(target.strip()), pattern, excludes)
    raise TypeError(f"STATE-GUARD: target must be a str or Path; received {type(target).__name__}.")


def _load_path_sources(target: Path, pattern: str, excludes: AbstractSet[str]) -> list[FileSource]:
    """Load a single file or crawl a directory into FileSource records."""
    if not target.exists():
        raise FileNotFoundError(f"STATE-GUARD: Target path not found: {target}")
    if target.is_file():
        return [FileSource(path=str(target), rel_path=target.name, content=target.read_text(encoding="utf-8"))]
    resolved = target.resolve()
    files = crawl_files(resolved, pattern=pattern, excludes=excludes)
    if not files:
        raise ValueError(f"STATE-GUARD: No files matching {pattern!r} found in directory: {target}")
    return [
        FileSource(path=str(path), rel_path=path.relative_to(resolved).as_posix(), content=path.read_text(encoding="utf-8"))
        for path in files
    ]


def atomic_write_text(
    path: Path,
    content: str,
    *,
    encoding: str = "utf-8",
    newline: str = "\n",
) -> None:
    """Atomically write text to path via a sibling temp file and os.replace, cleaning up on error."""
    temporary: Path | None = None
    try:
        temporary = _create_sibling_temp(path)
        temporary.write_text(content, encoding=encoding, newline=newline)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _create_sibling_temp(path: Path) -> Path:
    """Allocate an unlinked-safe sibling temporary file in the target parent directory."""
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
        return Path(stream.name)
