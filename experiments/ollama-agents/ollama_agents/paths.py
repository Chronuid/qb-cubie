"""Validate canonical relative names and reject symlinks at every path component."""

import os
from pathlib import Path, PurePosixPath, PureWindowsPath

from .errors import infrastructure, invalid


def relative(name):
    """Require one unambiguous relative POSIX file path."""
    if not isinstance(name, str) or not name or "\0" in name or "\\" in name:
        raise invalid("Invalid relative file path")
    path = PurePosixPath(name)
    if path.is_absolute() or PureWindowsPath(name).drive or ".." in path.parts:
        raise invalid(f"Forbidden absolute or traversal path: {name}")
    if not path.parts or path.as_posix() != name:
        raise invalid(f"Noncanonical file path: {name}")
    return name


def absolute(path):
    """Anchor a configured root without hiding its symlink components."""
    return Path(os.path.abspath(path))


def guard(path):
    """Reject symlinks and nondirectory parents before a filesystem operation."""
    for parent in reversed(path.parents):
        if parent.is_symlink():
            raise invalid(f"Symlink parent path is forbidden: {parent}")
        if parent.exists() and not parent.is_dir():
            raise invalid(f"Parent path is not a directory: {parent}")
    if path.is_symlink():
        raise invalid(f"Symlink path is forbidden: {path}")
    return path


def file_path(root, name):
    """Resolve a canonical workspace target without following symlinks."""
    target = guard(root / relative(name))
    if not target.is_relative_to(root):
        raise invalid(f"File path is outside workspace: {name}")
    if target.exists() and not target.is_file():
        raise invalid(f"File path is not a regular file: {name}")
    return target


def names(values):
    """Freeze explicit file grants without interpreting strings as collections."""
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise infrastructure("File permissions must be explicit collections of relative paths")
    return frozenset(relative(name) for name in values)


def directory(path):
    """Require an existing symlink-free root directory."""
    path = guard(absolute(path))
    if not path.is_dir():
        raise infrastructure(f"Root directory does not exist: {path}")
    return path
