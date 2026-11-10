"""Copy trusted host inputs without writing outside the workspace."""

# Sources and targets must be trusted; these checks do not guard concurrent changes.

import shutil
from collections import deque
from collections.abc import Mapping
from os import PathLike
from pathlib import Path


def hydrate_workspace(workspace: Path, mappings: Mapping) -> None:
    """Hydrate destination-to-source mappings; raise ValueError for path escapes."""
    _Hydrator(workspace.resolve()).run(mappings)


class _Hydrator:
    def __init__(self, root: Path):
        self.root = root
        self.links: list[tuple[Path, object]] = []

    def run(self, mappings: Mapping) -> None:
        for destination, host_source in mappings.items():
            self._mapping(destination, host_source)
        # Later mappings can change an earlier link's meaning.
        for link, destination in self.links:
            self._checked(link, destination)

    def _mapping(self, destination: object, host_source) -> None:
        relative = self._relative(destination)
        target = self._checked(self.root / relative, destination)
        source = Path(host_source)
        if not source.exists():
            raise FileNotFoundError(f"Host path for FS mapping not found: {source}")
        if source.is_dir():
            self._directory(source, target, destination)
        else:
            self._file(source, target, destination)

    def _directory(self, source: Path, target: Path, destination: object) -> None:
        target = self._checked(target, destination)
        target.mkdir(parents=True, exist_ok=True)
        for child in source.iterdir():
            output = target / child.name
            if child.is_symlink():
                self._symlink(child, output, destination)
            elif child.is_dir():
                self._directory(child, output, destination)
            else:
                self._file(child, output, destination)
        shutil.copystat(source, target)

    def _symlink(self, source: Path, target: Path, destination: object) -> None:
        # symlink_to deliberately rejects an occupied destination.
        target.symlink_to(source.readlink(), target_is_directory=source.is_dir())
        self.links.append((target, destination))
        self._checked(target, destination)
        shutil.copystat(source, target, follow_symlinks=False)

    def _file(self, source: Path, target: Path, destination: object) -> None:
        target = self._checked(target, destination)
        # Check the implicit basename explicitly before copying a file into a directory.
        if target.is_dir():
            target = self._checked(target / source.name, destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        shutil.copystat(source, target)

    def _checked(self, path: Path, destination: object) -> Path:
        # Resolve symlinks before '..' and check every intermediate location.
        pending = deque(path.relative_to(self.root).parts)
        current = self.root
        followed = 0
        while pending:
            part = pending.popleft()
            candidate = current.parent if part == ".." else current / part
            self._confined(candidate, destination, f"path escapes workspace: {path}")
            if candidate.is_symlink():
                current, followed = self._follow(candidate, current, pending, followed, destination, path)
            else:
                current = self._junction(candidate, destination)
        return current

    def _follow(
        self, candidate: Path, current: Path, pending: deque[str],
        followed: int, destination: object, path: Path,
    ) -> tuple[Path, int]:
        followed += 1
        if followed > 40:
            raise self._invalid(destination, f"symlink loop or excessive link depth: {path}")
        link = candidate.readlink()
        if link.anchor:
            current = self.root
            parts = self._absolute_link(link, candidate, destination)
        else:
            parts = link.parts
        pending.extendleft(reversed(parts))
        return current, followed

    def _absolute_link(self, link: Path, candidate: Path, destination: object) -> tuple[str, ...]:
        if not link.is_absolute() or not link.is_relative_to(self.root):
            raise self._invalid(destination, f"symlink escapes workspace: {candidate} -> {link}")
        return link.relative_to(self.root).parts

    def _junction(self, candidate: Path, destination: object) -> Path:
        current = candidate.resolve() if candidate.is_junction() else candidate
        self._confined(current, destination, f"junction escapes workspace: {candidate}")
        return current

    def _confined(self, path: Path, destination: object, detail: str) -> None:
        if not path.is_relative_to(self.root):
            raise self._invalid(destination, detail)

    @classmethod
    def _relative(cls, destination: object) -> Path:
        if not isinstance(destination, (str, PathLike)):
            raise cls._invalid(destination, "expected a relative filesystem path")
        relative = Path(destination)
        if relative.anchor:
            raise cls._invalid(destination, "expected a relative filesystem path")
        return relative

    @staticmethod
    def _invalid(destination: object, detail: str) -> ValueError:
        return ValueError(f"Invalid pre.fs destination {destination!r}: {detail}")
