"""Imperative filesystem and catalog adapters for DocFrame (keeps rules and blocks I/O-free)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set as AbstractSet
from pathlib import Path
from typing import Any

from ...service_core.workspace import (
    FileSource,
    FileSystemWorkspaceView,
    crawl_files,
    find_project_root,
    normalize_excludes,
)
from ._catalog_scanner import build_catalog_from_sources
from .presets import DEFAULT_FRAME_PATTERNS, FramePattern
from .protocols import DocumentCatalog


def resolve_target_path(target: Any) -> Path:
    """Validate a target argument and resolve it to an existing filesystem Path."""
    if target is None:
        return find_project_root()
    path = _coerce_path_arg(target)
    if not path.exists():
        raise FileNotFoundError(f"STATE-GUARD: Documentation path not found: {path}")
    return path.resolve()


def _coerce_path_arg(target: Any) -> Path:
    """Convert a Path or non-empty string target into a Path or raise STATE-GUARD."""
    if isinstance(target, Path):
        return target
    if isinstance(target, str):
        if not target.strip():
            raise ValueError("STATE-GUARD: target path string must not be empty.")
        return Path(target.strip())
    raise TypeError(f"STATE-GUARD: target must be a Path, str, or None; received {type(target).__name__}.")


def normalize_frame_patterns(pattern: Any) -> dict[str, FramePattern]:
    """Normalize a FramePattern, sequence, or mapping into an ID-keyed dict."""
    if pattern is None:
        return {p.id: p for p in DEFAULT_FRAME_PATTERNS}
    if isinstance(pattern, Mapping) and all(isinstance(v, FramePattern) for v in pattern.values()):
        return {v.id: v for v in pattern.values()}
    items = (pattern,) if isinstance(pattern, FramePattern) else pattern
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise TypeError("STATE-GUARD: pattern must be a FramePattern or sequence of FramePatterns.")
    if not items:
        raise ValueError("STATE-GUARD: pattern sequence must not be empty.")
    if not all(isinstance(item, FramePattern) for item in items):
        raise TypeError("STATE-GUARD: All pattern items must be FramePattern instances.")
    return {item.id: item for item in items}


def resolve_catalog_root(target: Path) -> Path:
    """Determine the catalog root directory for a file or directory target."""
    return find_project_root(start=target, markers=("pyproject.toml", "docs/.assets"), stop_at_cwd=True)


def build_workspace_catalog(target_path: Path, excludes: AbstractSet[str]) -> DocumentCatalog:
    """Crawl non-excluded Markdown files under the catalog root into a DocumentCatalog."""
    catalog_root = resolve_catalog_root(target_path)
    files = crawl_files(catalog_root, pattern="*.md", excludes=excludes)
    sources = [(str(path), path.read_text(encoding="utf-8")) for path in files]
    return build_catalog_from_sources(catalog_root, sources, workspace=FileSystemWorkspaceView(catalog_root))


def prepare_docframe_workspace(
    sources: Sequence[FileSource],
    options: Mapping[str, Any],
) -> tuple[DocumentCatalog, dict[str, FramePattern]]:
    """Return a prebuilt or freshly constructed (DocumentCatalog, FramePattern map) context."""
    raw_patterns = options.get("patterns")
    patterns = _coerce_option_patterns(raw_patterns)
    cached_catalog = options.get("catalog")
    if isinstance(cached_catalog, DocumentCatalog):
        return cached_catalog, patterns
    raw_target = options.get("target")
    if raw_target is None and sources:
        raw_target = Path(sources[0].path)
    target_path = resolve_target_path(raw_target)
    excludes = normalize_excludes(options.get("excludes"))
    return build_workspace_catalog(target_path, excludes), patterns


def _coerce_option_patterns(raw_patterns: Any) -> dict[str, FramePattern]:
    """Filter optional mixed pattern collections down to FramePattern instances."""
    if raw_patterns is None:
        return normalize_frame_patterns(None)
    if isinstance(raw_patterns, Mapping):
        return normalize_frame_patterns(raw_patterns)
    if isinstance(raw_patterns, FramePattern):
        return normalize_frame_patterns(raw_patterns)
    if isinstance(raw_patterns, Sequence) and not isinstance(raw_patterns, (str, bytes)):
        frame_pats = tuple(p for p in raw_patterns if isinstance(p, FramePattern))
        return normalize_frame_patterns(frame_pats or None)
    return normalize_frame_patterns(raw_patterns)
