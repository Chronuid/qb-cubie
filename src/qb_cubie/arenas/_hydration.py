"""Copy trusted host inputs without writing outside the workspace.

This guards configuration mistakes, including symlinks in copied trees and
existing destinations. It is not a sandbox or protection against concurrent
filesystem changes by an adversary. Sources and executing targets must be trusted.
"""

import shutil
from collections import deque
from collections.abc import Mapping
from os import PathLike
from pathlib import Path


def hydrate_workspace(workspace: Path, mappings: Mapping) -> None:
    """Hydrate destination-to-source mappings; raise ValueError for path escapes.

    Host sources resolve from the caller's CWD. Root source symlinks are followed;
    symlinks inside directories are preserved and checked in their new location.
    Partial workspace contents are left to the arena's lifecycle cleanup on error.
    """
    root = workspace.resolve()
    links: list[tuple[Path, object]] = []

    def invalid(destination: object, detail: str) -> ValueError:
        return ValueError(f"Invalid pre.fs destination {destination!r}: {detail}")

    def checked(path: Path, destination: object) -> Path:
        # Resolve components explicitly: normalizing '..' before following a
        # symlink can hide an escape. Check every intermediate location, too.
        pending = deque(path.relative_to(root).parts)
        current = root
        followed = 0
        while pending:
            part = pending.popleft()
            candidate = current.parent if part == ".." else current / part
            if not candidate.is_relative_to(root):
                raise invalid(destination, f"path escapes workspace: {path}")
            if candidate.is_symlink():
                followed += 1
                if followed > 40:
                    raise invalid(destination, f"symlink loop or excessive link depth: {path}")
                link = candidate.readlink()
                if link.anchor:
                    if not link.is_absolute() or not link.is_relative_to(root):
                        raise invalid(destination, f"symlink escapes workspace: {candidate} -> {link}")
                    current = root
                    pending.extendleft(reversed(link.relative_to(root).parts))
                else:
                    pending.extendleft(reversed(link.parts))
            else:
                # Windows directory junctions also redirect writes.
                current = candidate.resolve() if candidate.is_junction() else candidate
                if not current.is_relative_to(root):
                    raise invalid(destination, f"junction escapes workspace: {candidate}")
        return current

    def copy_directory(source: Path, target: Path, destination: object) -> None:
        target = checked(target, destination)
        target.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            output = target / child.name
            if child.is_symlink():
                # Create the link itself, without following an existing output
                # link. symlink_to deliberately rejects an occupied destination.
                output.symlink_to(child.readlink(), target_is_directory=child.is_dir())
                links.append((output, destination))
                checked(output, destination)
                shutil.copystat(child, output, follow_symlinks=False)
            elif child.is_dir():
                copy_directory(child, output, destination)
            else:
                copy_file(child, output, destination)
        shutil.copystat(source, target)

    def copy_file(source: Path, target: Path, destination: object) -> None:
        target = checked(target, destination)
        # copy2 accepts directories and implicitly appends the source basename.
        # Make that extra destination explicit so it is checked as well.
        if target.is_dir():
            target = checked(target / source.name, destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        # copyfile never appends another basename if that path is a directory.
        shutil.copyfile(source, target)
        shutil.copystat(source, target)

    for destination, host_source in mappings.items():
        if not isinstance(destination, (str, PathLike)):
            raise invalid(destination, "expected a relative filesystem path")
        relative = Path(destination)
        if relative.anchor:
            raise invalid(destination, "expected a relative filesystem path")
        target = checked(root / relative, destination)
        source = Path(host_source)
        if not source.exists():
            raise FileNotFoundError(f"Host path for FS mapping not found: {source}")
        if source.is_dir():
            copy_directory(source, target, destination)
        else:
            copy_file(source, target, destination)

    # Forward references and later mappings can change an earlier link's
    # meaning. Validate the completed topology before target execution.
    for link, destination in links:
        checked(link, destination)
