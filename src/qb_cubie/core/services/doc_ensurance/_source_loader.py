"""Filesystem and in-memory Markdown source resolution for DocEnsurance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_MD_PREFIXES = ("#", "`", "~", "<", ">", "-", "*", "+", "!", "[", "|")


def resolve_sources(target: Any, excludes: set[str]) -> list[tuple[str, str]]:
    """Validates the target and loads Markdown content from file, directory, or memory."""
    if isinstance(target, Path):
        return load_path_sources(target, excludes)
    if isinstance(target, str):
        if not target.strip():
            raise ValueError("STATE-GUARD: Markdown target string must not be empty.")
        if looks_like_path(target):
            return load_path_sources(Path(target.strip()), excludes)
        return [("IN_MEMORY", target)]
    raise TypeError(
        f"STATE-GUARD: target must be a Markdown str or Path; received {type(target).__name__}."
    )


def looks_like_path(target: str) -> bool:
    """Distinguishes single-line filesystem path strings from in-memory Markdown."""
    stripped = target.strip()
    if "\n" in stripped or stripped.startswith(_MD_PREFIXES) or "](" in stripped or "://" in stripped:
        return False
    if Path(stripped).exists() or stripped.lower().endswith((".md", ".markdown")):
        return True
    if " " not in stripped:
        return any(ch in stripped for ch in ("/", "\\", ".", "_", "-"))
    first = stripped.split()[0]
    return ("/" in first or "\\" in first) and not stripped.endswith((".", "!", "?"))


def crawl_directory(root: Path, excludes: set[str]) -> list[Path]:
    """Recursively collects sorted Markdown files while respecting relative exclusions."""
    resolved = root.resolve()
    return [
        path
        for path in sorted(resolved.rglob("*.md"))
        if path.is_file() and not is_excluded(path.relative_to(resolved), resolved.name, excludes)
    ]


def is_excluded(rel_path: Path, root_name: str, excludes: set[str]) -> bool:
    """Checks whether a path relative to root matches any segment or subpath exclusion."""
    rel_posix = rel_path.as_posix()
    for excl in excludes:
        stripped = excl.strip("/")
        if not stripped:
            continue
        norm = stripped.removeprefix(f"{root_name}/")
        if rel_posix == norm or rel_posix.startswith(f"{norm}/") or ("/" not in stripped and norm in rel_path.parts):
            return True
    return False


def load_path_sources(target: Path, excludes: set[str]) -> list[tuple[str, str]]:
    """Loads either a single Markdown file or crawls a directory recursively."""
    if not target.exists():
        raise FileNotFoundError(f"STATE-GUARD: Documentation path not found: {target}")
    if target.is_file():
        return [(str(target), target.read_text(encoding="utf-8"))]
    files = crawl_directory(target, excludes)
    if not files:
        raise ValueError(f"STATE-GUARD: No Markdown files found in directory: {target}")
    return [(str(path), path.read_text(encoding="utf-8")) for path in files]
