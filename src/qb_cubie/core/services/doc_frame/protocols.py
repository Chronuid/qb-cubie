"""Protocols and immutable data records for the qb_cubie.services.doc_frame package."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
import fnmatch
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from ...protocols import Diagnostic

VALID_ZONES: Final[tuple[str, ...]] = ("head", "router", "foot")
VALID_WRAP_TAGS: Final[tuple[str, ...]] = ("div", "center")
VALID_CATALOG_MODES: Final[tuple[str, ...]] = ("table", "links")


def validate_zone(zone: str) -> str:
    """Validates that a parsed frame zone identifier is supported."""
    if not isinstance(zone, str) or zone not in VALID_ZONES:
        raise ValueError(
            f"STATE-GUARD: zone must be one of {VALID_ZONES}; received {zone!r}."
        )
    return zone


def validate_wrap_tag(tag: str) -> str:
    """Validates that a CenterWrap HTML tag is supported."""
    if not isinstance(tag, str) or tag not in VALID_WRAP_TAGS:
        raise ValueError(
            f"STATE-GUARD: tag must be one of {VALID_WRAP_TAGS}; received {tag!r}."
        )
    return tag


def validate_catalog_mode(mode: str) -> str:
    """Validates that a CatalogRouter rendering mode is supported."""
    if not isinstance(mode, str) or mode not in VALID_CATALOG_MODES:
        raise ValueError(
            f"STATE-GUARD: mode must be one of {VALID_CATALOG_MODES}; received {mode!r}."
        )
    return mode


def sort_doc_metas(entries: Iterable[DocMeta]) -> list[DocMeta]:
    """Sorts DocMeta records with un-ordered README.md first, then explicit order, then filename."""
    return sorted(entries, key=_doc_meta_sort_key)


def _doc_meta_sort_key(entry: DocMeta) -> tuple[int, int, str, str]:
    """Computes the deterministic sort key for a single DocMeta record."""
    name = Path(entry.path).name
    if name == "README.md" and entry.order is None:
        return (0, 0, name, entry.path)
    if entry.order is not None:
        return (1, entry.order, name, entry.path)
    return (2, 0, name, entry.path)


# ========== DOC-FRAME DATA RECORDS ====================================================================================
@dataclass(frozen=True)
class DocMeta:
    """Stores Pass 1 routing metadata extracted from a Markdown document's head frame."""

    path: str
    frame_id: str | None
    title: str
    label: str
    summary: str
    order: int | None = None
    routable: bool = True
    category: str = "."
    attrs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class FrameSpan:
    """Represents a single parsed qb:frame comment block and its line/character coordinates."""

    frame_id: str
    zone: str
    attrs: dict[str, str]
    open_tag: str
    inner_content: str
    close_tag: str
    start_line: int
    end_line: int
    start_idx: int
    end_idx: int


@dataclass(frozen=True)
class DocumentCatalog:
    """Immutable Pass 1 catalog of discovered Markdown documents and their routing metadata."""

    root: Path
    entries: tuple[DocMeta, ...] = field(default_factory=tuple)

    def get(self, rel_path: str) -> DocMeta | None:
        """Returns the DocMeta for a repository-relative POSIX path or None if absent."""
        norm = Path(rel_path).as_posix().strip("/")
        return next((e for e in self.entries if e.path == norm), None)

    def by_path(self, rel_path: str) -> DocMeta:
        """Returns the DocMeta for a repository-relative POSIX path or raises KeyError."""
        found = self.get(rel_path)
        if found is None:
            raise KeyError(f"STATE-GUARD: Document not found in catalog: {rel_path!r}")
        return found

    def select(
        self,
        directory: str = ".",
        glob: str = "*.md",
        exclude: Sequence[str] = (),
        *,
        recursive: bool = False,
        include_unroutable: bool = False,
    ) -> list[DocMeta]:
        """Filters and deterministically sorts catalog entries for a target directory and glob."""
        norm_dir = Path(directory).as_posix().strip("/") or "."
        excl_set = {e.strip("/") for e in exclude if e.strip("/")}
        matched = [
            e for e in self.entries
            if (include_unroutable or e.routable)
            and _matches_dir(e.category, norm_dir, recursive)
            and fnmatch.fnmatch(Path(e.path).name, glob)
            and Path(e.path).name not in excl_set
            and e.path not in excl_set
        ]
        return sort_doc_metas(matched)


def _matches_dir(category: str, target_dir: str, recursive: bool) -> bool:
    """Checks whether an entry's parent category matches the requested directory scope."""
    if not recursive:
        return category == target_dir
    if target_dir == ".":
        return True
    return category == target_dir or category.startswith(f"{target_dir}/")


@dataclass(frozen=True)
class FrameRenderContext:
    """Provides file coordinates, catalog access, and current span metadata during Pass 2 rendering."""

    file_path: Path
    rel_path: str
    catalog: DocumentCatalog
    span: FrameSpan


@dataclass(frozen=True)
class DocFrameReport:
    """Aggregates updated file paths, catalog state, and diagnostics of a DocFrame run."""

    target: str
    passed: bool
    updated_files: tuple[str, ...] = field(default_factory=tuple)
    catalog: DocumentCatalog | None = None
    diagnostics: tuple[Diagnostic, ...] = field(default_factory=tuple)


@runtime_checkable
class FrameBlockProtocol(Protocol):
    """Contract for stateless building blocks rendered inside a document frame zone."""

    def render(self, ctx: FrameRenderContext) -> str: ...
