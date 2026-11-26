"""Imperative filesystem and in-memory source adapters for DocEnsurance backed by service_core."""

from __future__ import annotations

from collections.abc import Set as AbstractSet
from pathlib import Path
from typing import Any

from ...service_core.workspace import (
    crawl_files,
    find_project_root,
    is_excluded as _core_is_excluded,
    load_sources,
    looks_like_path as looks_like_path,
)


def resolve_cli_target_path(target: Any) -> Path:
    """Validate a CLI target argument and resolve it to an existing filesystem Path."""
    if target is None:
        return find_project_root()
    path = _coerce_cli_path(target)
    if not path.exists():
        raise FileNotFoundError(f"STATE-GUARD: Documentation path not found: {path}")
    return path.resolve()


def _coerce_cli_path(target: Any) -> Path:
    """Convert a Path or non-empty CLI target string into a Path or raise STATE-GUARD."""
    if isinstance(target, Path):
        return target
    if isinstance(target, str):
        if not target.strip():
            raise ValueError("STATE-GUARD: target path string must not be empty.")
        return Path(target.strip())
    raise TypeError(f"STATE-GUARD: target must be a Path, str, or None; received {type(target).__name__}.")


def resolve_sources(target: Any, excludes: AbstractSet[str]) -> list[tuple[str, str]]:
    """Validate target and load Markdown content from file, directory, or in-memory text."""
    try:
        sources = load_sources(target, pattern="*.md", excludes=excludes, allow_in_memory=True)
    except ValueError as exc:
        if "No files matching" in str(exc):
            raise ValueError(f"STATE-GUARD: No Markdown files found in directory: {target}") from exc
        raise
    return [(src.path, src.content) for src in sources]


def crawl_directory(root: Path, excludes: AbstractSet[str]) -> list[Path]:
    """Recursively collect sorted Markdown files while respecting relative exclusions."""
    return crawl_files(root, pattern="*.md", excludes=excludes)


def is_excluded(rel_path: Path, root_name: str, excludes: AbstractSet[str]) -> bool:
    """Check whether a path relative to root matches any segment or subpath exclusion."""
    return _core_is_excluded(rel_path, root_name, excludes)


def load_path_sources(target: Path, excludes: AbstractSet[str]) -> list[tuple[str, str]]:
    """Load either a single Markdown file or crawl a directory recursively."""
    try:
        sources = load_sources(target, pattern="*.md", excludes=excludes, allow_in_memory=False)
    except ValueError as exc:
        if "No files matching" in str(exc):
            raise ValueError(f"STATE-GUARD: No Markdown files found in directory: {target}") from exc
        raise
    return [(src.path, src.content) for src in sources]
