"""Prototype orchestrator for synchronizing Markdown document frames (pending evaluation and hardening)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from ...linter import DEFAULT_EXCLUDES
from ..doc_ensurance.protocols import DocDiagnostic, ExtractedExample, MdBlock
from ._catalog_scanner import build_catalog_from_sources, parse_frame_spans
from .frame_blocks import (
    AssetImage,
    CatalogRouter,
    CenterWrap,
    CompactNav,
    DisclaimerSlot,
    Divider,
    FolderRouter,
    HeaderContentSlot,
    PromptSlot,
    ProvenanceBlock,
    SiblingRouter,
    TitleSlot,
)
from .protocols import (
    DocFrameReport,
    DocumentCatalog,
    FrameBlockProtocol,
    FrameRenderContext,
    FrameSpan,
    validate_zone,
)


@dataclass(frozen=True)
class FramePattern:
    """Defines the structural block composition for head, router, and foot zones."""

    id: str
    head: Sequence[FrameBlockProtocol] = ()
    foot: Sequence[FrameBlockProtocol] = ()
    router: Sequence[FrameBlockProtocol] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("STATE-GUARD: FramePattern id must be a non-empty string.")
        for zone_name, seq in (("head", self.head), ("foot", self.foot), ("router", self.router)):
            _validate_block_sequence(zone_name, seq)

    @property
    def name(self) -> str:
        """Returns the pattern identifier for compatibility with DocPatternProtocol."""
        return self.id

    def scan(
        self, blocks: Sequence[MdBlock], file_path: str
    ) -> tuple[list[ExtractedExample], list[DocDiagnostic]]:
        """Satisfies DocPatternProtocol when FramePattern is passed in DocEnsurance(pattern=...)."""
        _ = (blocks, file_path)
        return [], []

    def render_zone(self, zone: str, ctx: FrameRenderContext) -> str:
        """Renders all configured blocks for the requested zone ('head', 'router', or 'foot')."""
        validate_zone(zone)
        blocks = {"head": self.head, "router": self.router, "foot": self.foot}[zone]
        rendered = [out for block in blocks if (out := block.render(ctx))]
        return "\n\n".join(rendered)


def _validate_block_sequence(zone_name: str, seq: Any) -> None:
    """Validates that a zone block collection is a sequence of FrameBlockProtocol objects."""
    if isinstance(seq, (str, bytes)) or not isinstance(seq, Sequence):
        raise TypeError(f"STATE-GUARD: FramePattern.{zone_name} must be a sequence of frame blocks.")
    for item in seq:
        if not isinstance(item, FrameBlockProtocol):
            raise TypeError(
                f"STATE-GUARD: Block in {zone_name} must implement FrameBlockProtocol; got {type(item).__name__}."
            )


# ========== STANDARD CUBIE DOC-FRAME PRESETS ==========================================================================
HEADER_QUICK_NAV: Final[CompactNav] = CompactNav(
    routes=(
        ("README", "README.md"),
        ("QA-Handbuch", "docs/GUIDE_Quality-Assurance.md"),
        ("DocEnsurance", "docs/services/GUIDE_DocEnsurance.md"),
    )
)

GUIDE_ROUTER: Final[FolderRouter] = FolderRouter(dir="docs", glob="GUIDE_*.md")
SERVICE_ROUTER: Final[FolderRouter] = FolderRouter(dir="docs/services", glob="GUIDE_*.md")
CONTEXT_ROUTER: Final[SiblingRouter] = SiblingRouter(
    hubs=(
        ("Entwicklerübersicht & Internals", "docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md"),
        ("Hintergrund & Essays", "docs/misc/README.md"),
        ("Feature-Drafts: Virtualisierung", "docs/feature-drafts/virtualization/README.md"),
    )
)

STD_FOOTER_BLOCKS: Final[tuple[FrameBlockProtocol, ...]] = (
    Divider(),
    Divider(),
    CenterWrap(
        tag="div",
        blocks=(
            AssetImage(path="docs/.assets/cubie-small.png", alt="Cubie"),
            GUIDE_ROUTER,
            SERVICE_ROUTER,
            CONTEXT_ROUTER,
        ),
    ),
)

AUTO_INDEX_ROUTER: Final[CatalogRouter] = CatalogRouter(
    default_mode="table",
    exclude=("README.md",),
    extract_summary=True,
)

STD_HEAD_BLOCKS: Final[tuple[FrameBlockProtocol, ...]] = (
    CenterWrap(
        tag="div",
        blocks=(HeaderContentSlot(), Divider(), DisclaimerSlot(), Divider(), HEADER_QUICK_NAV),
    ),
)

CUBIE_DOC_FRAME_1: Final[FramePattern] = FramePattern(
    id="CUBIE_DOC_FRAME_1",
    head=STD_HEAD_BLOCKS,
    foot=STD_FOOTER_BLOCKS,
)

CUBIE_DOC_FRAME_2: Final[FramePattern] = FramePattern(
    id="CUBIE_DOC_FRAME_2",
    head=(
        TitleSlot(optional=True),
        ProvenanceBlock(required_keys=("Plattform / Umgebung", "Modell", "Reasoning-Effort")),
        Divider(),
        PromptSlot(optional=True),
    ),
    foot=STD_FOOTER_BLOCKS,
)

CUBIE_DOC_FRAME_3: Final[FramePattern] = FramePattern(
    id="CUBIE_DOC_FRAME_3",
    head=STD_HEAD_BLOCKS,
    router=(AUTO_INDEX_ROUTER,),
    foot=STD_FOOTER_BLOCKS,
)

DEFAULT_FRAME_PATTERNS: Final[tuple[FramePattern, ...]] = (
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
)


# ========== DOC-FRAME SERVICE =========================================================================================
class DocFrame:
    """Prototype orchestrator for synchronizing Markdown frames (pending evaluation and hardening)."""

    def __init__(
        self,
        target: str | Path | None = None,
        pattern: FramePattern | Sequence[FramePattern] | None = None,
        excludes: Sequence[str] | None = None,
    ) -> None:
        """Initializes the DocFrame service and validates target, pattern, and exclude parameters."""
        self.target_path = self._resolve_target_path(target)
        self.patterns = self._normalize_patterns(pattern)
        self.excludes = self._normalize_excludes(excludes)

    @classmethod
    def scan_catalog(
        cls,
        target: str | Path | None = None,
        excludes: Sequence[str] | None = None,
    ) -> DocumentCatalog:
        """Executes Pass 1 and returns the immutable DocumentCatalog for the target workspace."""
        return cls(target=target, excludes=excludes).build_catalog()

    @classmethod
    def update(
        cls,
        target: str | Path | None = None,
        pattern: FramePattern | Sequence[FramePattern] | None = None,
        excludes: Sequence[str] | None = None,
    ) -> DocFrameReport:
        """Executes Pass 1 (Catalog) and Pass 2 (Frame Rendering) and writes updated files atomically."""
        return cls(target=target, pattern=pattern, excludes=excludes).run()

    def build_catalog(self) -> DocumentCatalog:
        """Scans all non-excluded Markdown files under the catalog root into a DocumentCatalog."""
        catalog_root = self._resolve_catalog_root(self.target_path)
        files = self._crawl_directory(catalog_root, self.excludes)
        sources = [(str(p), p.read_text(encoding="utf-8")) for p in files]
        return build_catalog_from_sources(catalog_root, sources)

    def run(self) -> DocFrameReport:
        """Synchronizes all qb:frame blocks in the target scope and returns a DocFrameReport."""
        target_sources = self._load_path_sources(self.target_path, self.excludes)
        catalog = self.build_catalog()
        updated: list[str] = []
        for file_path_str, content in target_sources:
            file_path = Path(file_path_str)
            new_content = self._render_file_frames(file_path, content, catalog)
            if new_content != content:
                file_path.write_text(new_content, encoding="utf-8")
                updated.append(file_path.resolve().relative_to(catalog.root).as_posix())
        return DocFrameReport(str(self.target_path), True, tuple(updated), catalog, ())

    def _render_file_frames(self, file_path: Path, content: str, catalog: DocumentCatalog) -> str:
        """Re-renders all closed qb:frame spans in a single document while protecting outside text."""
        spans, _ = parse_frame_spans(content)
        if not spans:
            return content
        rel_path = file_path.resolve().relative_to(catalog.root).as_posix()
        result = content
        for span in reversed(spans):
            replacement = self._render_single_span(file_path, rel_path, span, catalog, content)
            result = result[: span.start_idx] + replacement + result[span.end_idx :]
        return result

    def _render_single_span(
        self, file_path: Path, rel_path: str, span: FrameSpan, catalog: DocumentCatalog, full_text: str
    ) -> str:
        """Renders one FrameSpan using its matching FramePattern or raises a STATE-GUARD error."""
        if span.frame_id not in self.patterns:
            raise ValueError(
                f"STATE-GUARD: Unknown FramePattern id {span.frame_id!r} in {file_path}."
            )
        pattern = self.patterns[span.frame_id]
        ctx = FrameRenderContext(file_path.resolve(), rel_path, catalog, span)
        inner = pattern.render_zone(span.zone, ctx)
        lead_nl = "\n\n" if span.zone == "foot" else "\n"
        trail_nl = "\n" if full_text[span.start_idx : span.end_idx].endswith("\n") else ""
        return f"{span.open_tag}{lead_nl}{inner}\n{span.close_tag}{trail_nl}"

    @classmethod
    def _resolve_target_path(cls, target: Any) -> Path:
        """Validates the target parameter and resolves it to an existing filesystem Path."""
        if target is None:
            return cls._default_project_dir()
        path = cls._coerce_path_arg(target)
        if not path.exists():
            raise FileNotFoundError(f"STATE-GUARD: Documentation path not found: {path}")
        return path.resolve()

    @staticmethod
    def _coerce_path_arg(target: Any) -> Path:
        """Converts a string or Path target into a Path or raises a STATE-GUARD error."""
        if isinstance(target, Path):
            return target
        if isinstance(target, str):
            if not target.strip():
                raise ValueError("STATE-GUARD: target path string must not be empty.")
            return Path(target.strip())
        raise TypeError(f"STATE-GUARD: target must be a Path, str, or None; received {type(target).__name__}.")

    @staticmethod
    def _normalize_patterns(
        pattern: Any,
    ) -> dict[str, FramePattern]:
        """Normalizes a single FramePattern or sequence of FramePatterns into an ID-keyed dict."""
        if pattern is None:
            return {p.id: p for p in DEFAULT_FRAME_PATTERNS}
        items = (pattern,) if isinstance(pattern, FramePattern) else pattern
        if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
            raise TypeError("STATE-GUARD: pattern must be a FramePattern or sequence of FramePatterns.")
        if not items:
            raise ValueError("STATE-GUARD: pattern sequence must not be empty.")
        if not all(isinstance(item, FramePattern) for item in items):
            raise TypeError("STATE-GUARD: All pattern items must be FramePattern instances.")
        return {item.id: item for item in items}

    @staticmethod
    def _normalize_excludes(excludes: Any) -> set[str]:
        """Validates user excludes and merges them with DEFAULT_EXCLUDES."""
        if excludes is None:
            return set(DEFAULT_EXCLUDES)
        if isinstance(excludes, (str, bytes)) or not isinstance(excludes, Sequence):
            raise TypeError("STATE-GUARD: excludes must be a sequence of strings or None.")
        if not all(isinstance(e, str) for e in excludes):
            raise TypeError("STATE-GUARD: All exclude entries must be strings.")
        return set(DEFAULT_EXCLUDES) | set(excludes)

    @staticmethod
    def _default_project_dir() -> Path:
        """Finds the nearest ancestor containing pyproject.toml or falls back to CWD."""
        cwd = Path.cwd().resolve()
        for directory in (cwd, *cwd.parents):
            if (directory / "pyproject.toml").exists():
                return directory
        return cwd

    @staticmethod
    def _resolve_catalog_root(target: Path) -> Path:
        """Determines the project root directory for catalog scanning given a file or directory target."""
        start = target if target.is_dir() else target.parent
        cwd = Path.cwd().resolve()
        for directory in (start, *start.parents):
            if (directory / "pyproject.toml").exists() or (directory / "docs" / ".assets").exists():
                return directory
            if directory == cwd:
                break
        return start

    @classmethod
    def _crawl_directory(cls, root: Path, excludes: set[str]) -> list[Path]:
        """Recursively collects non-excluded Markdown files under root."""
        resolved = root.resolve()
        return [
            p for p in sorted(resolved.rglob("*.md"))
            if p.is_file() and not cls._is_excluded(p.relative_to(resolved), resolved.name, excludes)
        ]

    @staticmethod
    def _is_excluded(rel_path: Path, root_name: str, excludes: set[str]) -> bool:
        """Checks whether a path relative to root matches any configured exclusion."""
        rel_posix = rel_path.as_posix()
        for excl in excludes:
            stripped = excl.strip("/")
            if not stripped:
                continue
            norm = stripped.removeprefix(f"{root_name}/")
            if rel_posix == norm or rel_posix.startswith(f"{norm}/") or ("/" not in stripped and norm in rel_path.parts):
                return True
        return False

    @classmethod
    def _load_path_sources(cls, target: Path, excludes: set[str]) -> list[tuple[str, str]]:
        """Loads Markdown file contents for a single file or non-empty directory."""
        if target.is_file():
            return [(str(target), target.read_text(encoding="utf-8"))]
        files = cls._crawl_directory(target, excludes)
        if not files:
            raise ValueError(f"STATE-GUARD: No Markdown files found in directory: {target}")
        return [(str(p), p.read_text(encoding="utf-8")) for p in files]
