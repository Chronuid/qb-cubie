"""Orchestrator for synchronizing and verifying Markdown document frames via service_core."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final

from ...protocols import Reporter
from ...reporter import PytestReporter
from ...service_core.markdown import apply_span_replacements
from ...service_core.reporting import ServiceReport
from ...service_core.rules import FileCheckRunner
from ...service_core.workspace import atomic_write_text, load_sources, normalize_excludes
from ._catalog_scanner import parse_frame_spans
from .adapters import build_workspace_catalog, normalize_frame_patterns, resolve_target_path
from .doc_frame_rules import CUBIE_DOCFRAME_RULES
from .presets import (
    AUTO_INDEX_ROUTER,
    CONTEXT_ROUTER,
    CUBIE_DOC_FRAME_1,
    CUBIE_DOC_FRAME_2,
    CUBIE_DOC_FRAME_3,
    DEFAULT_FRAME_PATTERNS,
    EPISTEMIC_NOTICE,
    EPISTEMIC_NOTICE_TEXT,
    GUIDE_ROUTER,
    HEADER_QUICK_NAV,
    SERVICE_ROUTER,
    STD_FOOTER_BLOCKS,
    STD_HEAD_BLOCKS,
    FramePattern,
)
from .protocols import (
    DocFrameReport,
    DocumentCatalog,
    FrameRenderContext,
    FrameSpan,
)

__all__ = [
    "AUTO_INDEX_ROUTER",
    "CONTEXT_ROUTER",
    "CUBIE_DOC_FRAME_1",
    "CUBIE_DOC_FRAME_2",
    "CUBIE_DOC_FRAME_3",
    "DEFAULT_FRAME_PATTERNS",
    "EPISTEMIC_NOTICE",
    "EPISTEMIC_NOTICE_TEXT",
    "GUIDE_ROUTER",
    "HEADER_QUICK_NAV",
    "SERVICE_ROUTER",
    "STD_FOOTER_BLOCKS",
    "STD_HEAD_BLOCKS",
    "DocFrame",
    "FramePattern",
]

_DEFAULT_CHECK_REPORTER: Final[PytestReporter] = PytestReporter()


# ========== DOC-FRAME SERVICE =========================================================================================
class DocFrame:
    """Orchestrator for synchronizing and verifying Markdown frames via service_core."""

    def __init__(
        self,
        target: str | Path | None = None,
        pattern: FramePattern | Sequence[FramePattern] | None = None,
        excludes: Sequence[str] | None = None,
        reporter: Reporter[DocFrameReport] | None = None,
    ) -> None:
        """Initializes the DocFrame service and validates target, pattern, excludes, and reporter."""
        self.target_path = resolve_target_path(target)
        self.patterns = normalize_frame_patterns(pattern)
        self.excludes = normalize_excludes(excludes)
        self.reporter = reporter

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
        reporter: Reporter[DocFrameReport] | None = None,
    ) -> DocFrameReport:
        """Executes Pass 1 (Catalog) and Pass 2 (Frame Rendering) and writes updated files atomically."""
        return cls(target=target, pattern=pattern, excludes=excludes, reporter=reporter).run()

    @classmethod
    def check(
        cls,
        target: str | Path | None = None,
        pattern: FramePattern | Sequence[FramePattern] | None = None,
        rules: Sequence[Any] | None = None,
        excludes: Sequence[str] | None = None,
        reporter: Reporter[ServiceReport] | None = _DEFAULT_CHECK_REPORTER,
    ) -> ServiceReport:
        """Verifies Markdown document frames natively via FileCheckRunner without DocEnsurance."""
        __tracebackhide__ = True
        target_path = resolve_target_path(target)
        patterns = normalize_frame_patterns(pattern)
        norm_excludes = normalize_excludes(excludes)
        catalog = build_workspace_catalog(target_path, norm_excludes)
        check_rules = CUBIE_DOCFRAME_RULES if rules is None else rules
        options = {
            "catalog": catalog,
            "patterns": patterns,
            "target": target_path,
            "excludes": tuple(norm_excludes),
        }
        return FileCheckRunner(
            rules=check_rules,
            target=target_path,
            glob="*.md",
            excludes=tuple(norm_excludes),
            options=options,
            service="doc_frame",
            reporter=reporter,
        ).run()

    def build_catalog(self) -> DocumentCatalog:
        """Scans all non-excluded Markdown files under the catalog root into a DocumentCatalog."""
        return build_workspace_catalog(self.target_path, self.excludes)

    def run(self) -> DocFrameReport:
        """Synchronizes all qb:frame blocks in the target scope and returns a DocFrameReport."""
        target_sources = load_sources(
            self.target_path, pattern="*.md", excludes=self.excludes, allow_in_memory=False
        )
        catalog = self.build_catalog()
        updated: list[str] = []
        for source in target_sources:
            file_path = Path(source.path)
            new_content = self._render_file_frames(file_path, source.content, catalog)
            if new_content != source.content:
                atomic_write_text(file_path, new_content, encoding="utf-8", newline="\n")
                updated.append(file_path.resolve().relative_to(catalog.root).as_posix())
        report = DocFrameReport(str(self.target_path), True, tuple(updated), catalog, ())
        if self.reporter is not None:
            self.reporter.report(report)
        return report

    def _render_file_frames(self, file_path: Path, content: str, catalog: DocumentCatalog) -> str:
        """Re-renders all closed qb:frame spans in a single document while protecting outside text."""
        spans, _ = parse_frame_spans(content)
        if not spans:
            return content
        rel_path = file_path.resolve().relative_to(catalog.root).as_posix()
        replacements = [
            (span.start_idx, span.end_idx, self._render_single_span(file_path, rel_path, span, catalog, content))
            for span in spans
        ]
        return apply_span_replacements(content, replacements)

    def _render_single_span(
        self, file_path: Path, rel_path: str, span: FrameSpan, catalog: DocumentCatalog, full_text: str
    ) -> str:
        """Renders one FrameSpan using its matching FramePattern or raises a STATE-GUARD error."""
        if span.frame_id not in self.patterns:
            raise ValueError(f"STATE-GUARD: Unknown FramePattern id {span.frame_id!r} in {file_path}.")
        pattern = self.patterns[span.frame_id]
        ctx = FrameRenderContext(file_path.resolve(), rel_path, catalog, span)
        inner = pattern.render_zone(span.zone, ctx)
        lead_nl = "\n\n" if span.zone == "foot" else "\n"
        trail_nl = "\n" if full_text[span.start_idx : span.end_idx].endswith("\n") else ""
        return f"{span.open_tag}{lead_nl}{inner}\n{span.close_tag}{trail_nl}"
