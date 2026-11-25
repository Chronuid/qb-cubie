"""Diagnostic rules for Markdown frames powered by core.service_core.rules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Final

from ...protocols import Diagnostic, validate_severity
from ...service_core.rules import FileContextCache, WorkspaceCheckRuleProtocol
from ...service_core.workspace import FileSource
from ._catalog_scanner import parse_frame_spans
from .adapters import prepare_docframe_workspace
from .frame_blocks import ProvenanceBlock, resolve_banner_rel_path
from .presets import FramePattern
from .protocols import DocumentCatalog, FrameRenderContext, FrameSpan

_LINK_TARGET_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_DocFrameContext = tuple[DocumentCatalog, dict[str, FramePattern]]
_ParsedSpans = tuple[list[FrameSpan], list[int]]


def _parse_and_validate_spans(
    file_path: str,
    content: str,
    patterns: dict[str, FramePattern],
) -> _ParsedSpans:
    """Parse qb:frame spans once per file and validate that every frame_id is known."""
    spans, unclosed = parse_frame_spans(content)
    _validate_known_patterns(spans, patterns, file_path)
    return spans, unclosed


def _has_missing_zones(
    spans: list[FrameSpan], unclosed: list[int], patterns: dict[str, FramePattern]
) -> tuple[bool, int, str]:
    """Check whether a document has unclosed tags or is missing required head, foot, or router zones."""
    if unclosed:
        return True, unclosed[0], "Unclosed qb:frame comment block in document."
    zones = {s.zone for s in spans}
    if "head" not in zones or "foot" not in zones:
        return True, 1, "Document is missing required 'head' or 'foot' qb:frame block."
    for span in spans:
        pat = patterns[span.frame_id]
        if pat.router and "router" not in zones:
            return True, span.start_line, f"Document using {span.frame_id} is missing required zone='router' block."
    return False, 1, ""


def _validate_known_patterns(
    spans: Sequence[FrameSpan], patterns: dict[str, FramePattern], file_path: str
) -> None:
    """Raise a STATE-GUARD ValueError if any frame span references an unknown FramePattern id."""
    for span in spans:
        if span.frame_id not in patterns:
            raise ValueError(f"STATE-GUARD: Unknown FramePattern id {span.frame_id!r} in {file_path}.")


def _find_incomplete_provenance(span: FrameSpan, pattern: FramePattern) -> str | None:
    """Return the first missing or empty required provenance key in a head span, or None."""
    prov = next((b for b in pattern.head if span.zone == "head" and isinstance(b, ProvenanceBlock)), None)
    if prov is None:
        return None
    existing = prov._parse_existing_bullets(span.inner_content)
    overrides = prov._extract_attr_overrides(span.attrs)
    return next((k for k in prov.required_keys if not overrides.get(k, existing.get(k, "")).strip()), None)


def _find_broken_route_in_span(file_path: Path, span: FrameSpan, catalog: DocumentCatalog) -> str | None:
    """Return the first missing asset or link target referenced by a frame span via WorkspaceView."""
    workspace = catalog.workspace
    banner = span.attrs.get("banner", "").strip()
    if banner:
        banner_rel = resolve_banner_rel_path(banner, catalog.root, workspace)
        if workspace is not None and not workspace.has_path(banner_rel):
            return banner_rel
    for raw_target in _LINK_TARGET_RE.findall(span.inner_content):
        clean = raw_target.split("#", 1)[0].split("?", 1)[0].strip()
        if not clean or clean.startswith(("http://", "https://", "mailto:")):
            continue
        target_path = (file_path.resolve().parent / clean).resolve()
        if workspace is not None and not workspace.has_path(target_path):
            return clean
    return None


def _cached_incomplete_provenance(
    span: FrameSpan, pattern: FramePattern, cache: FileContextCache
) -> str | None:
    """Return cached incomplete provenance result for one span within the current file."""
    key = f"doc_frame:prov:{span.start_idx}:{span.end_idx}"
    return cache.get_or_compute(key, lambda: _find_incomplete_provenance(span, pattern))


def _cached_broken_route(
    path_obj: Path, span: FrameSpan, catalog: DocumentCatalog, cache: FileContextCache
) -> str | None:
    """Return cached broken route result for one span within the current file."""
    key = f"doc_frame:route:{span.start_idx}:{span.end_idx}"
    return cache.get_or_compute(key, lambda: _find_broken_route_in_span(path_obj, span, catalog))


class _DocFrameRuleBase:
    """Shared WorkspaceCheckRuleProtocol base for DocFrame diagnostic rules."""

    rule_id: str
    severity: str

    @property
    def context_key(self) -> str:
        """Return the shared cache key so all DocFrame rules reuse one catalog build."""
        return "doc_frame"

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Return prerequisite rule IDs that suppress this rule on the same file when failing."""
        return ()

    def prepare_workspace(self, sources: Sequence[FileSource], options: Mapping[str, Any]) -> _DocFrameContext:
        """Build or reuse the shared DocumentCatalog and FramePattern map via adapters."""
        return prepare_docframe_workspace(sources, options)

    def check_file(
        self,
        source: FileSource,
        workspace_ctx: _DocFrameContext,
        file_cache: FileContextCache,
    ) -> list[Diagnostic]:
        """Parse spans once per file via file_cache and dispatch to the concrete rule."""
        catalog, patterns = workspace_ctx
        parsed = file_cache.get_or_compute(
            "doc_frame:parsed_spans",
            lambda: _parse_and_validate_spans(source.path, source.content, patterns),
        )
        return self._check_parsed(source.path, parsed, catalog, patterns, file_cache)

    def _check_parsed(
        self,
        file_path: str,
        parsed: _ParsedSpans,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
        file_cache: FileContextCache,
    ) -> list[Diagnostic]:
        """Evaluate a pre-parsed Markdown document against this frame rule."""
        raise NotImplementedError


# ========== DOC-FRAME DIAGNOSTIC RULES ================================================================================
@dataclass(frozen=True)
class DocFrameMissing(_DocFrameRuleBase):
    """Flag Markdown files missing required head, foot, or router qb:frame blocks."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-MISSING"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def _check_parsed(
        self,
        file_path: str,
        parsed: _ParsedSpans,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
        file_cache: FileContextCache,
    ) -> list[Diagnostic]:
        """Emit DOCFRAME-MISSING when a document lacks valid head, foot, or router blocks."""
        _ = (catalog, file_cache)
        spans, unclosed = parsed
        missing, line, msg = _has_missing_zones(spans, unclosed, patterns)
        if missing:
            return [Diagnostic(file_path, self.rule_id, line, msg, severity=self.severity)]
        return []


@dataclass(frozen=True)
class DocFrameProvenanceIncomplete(_DocFrameRuleBase):
    """Flag CUBIE_DOC_FRAME_2 documents with missing or empty required provenance fields."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-PROVENANCE-INCOMPLETE"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def _check_parsed(
        self,
        file_path: str,
        parsed: _ParsedSpans,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
        file_cache: FileContextCache,
    ) -> list[Diagnostic]:
        """Emit DOCFRAME-PROVENANCE-INCOMPLETE when a required provenance key is blank or absent."""
        _ = catalog
        spans, unclosed = parsed
        if unclosed:
            return []
        for span in spans:
            missing_key = _cached_incomplete_provenance(span, patterns[span.frame_id], file_cache)
            if missing_key is not None:
                msg = f"Required provenance field '{missing_key}' is missing or empty."
                return [Diagnostic(file_path, self.rule_id, span.start_line, msg, severity=self.severity)]
        return []


@dataclass(frozen=True)
class DocFrameBrokenRoute(_DocFrameRuleBase):
    """Flag qb:frame blocks that reference non-existent Markdown routes or banner assets."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-BROKEN-ROUTE"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def _check_parsed(
        self,
        file_path: str,
        parsed: _ParsedSpans,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
        file_cache: FileContextCache,
    ) -> list[Diagnostic]:
        """Emit DOCFRAME-BROKEN-ROUTE when a linked document or banner asset is missing."""
        _ = patterns
        spans, unclosed = parsed
        if unclosed:
            return []
        path_obj = Path(file_path)
        for span in spans:
            broken = _cached_broken_route(path_obj, span, catalog, file_cache)
            if broken is not None:
                msg = f"Broken route or asset reference in frame ({span.zone}): {broken!r} not found."
                return [Diagnostic(file_path, self.rule_id, span.start_line, msg, severity=self.severity)]
        return []


@dataclass(frozen=True)
class DocFrameOutdated(_DocFrameRuleBase):
    """Flag qb:frame blocks whose stored content diverges from the current DocumentCatalog."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-OUTDATED"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Skip outdated checks on files that already failed DOCFRAME-MISSING."""
        return ("DOCFRAME-MISSING",)

    def _check_parsed(
        self,
        file_path: str,
        parsed: _ParsedSpans,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
        file_cache: FileContextCache,
    ) -> list[Diagnostic]:
        """Emit DOCFRAME-OUTDATED when a well-formed frame zone differs from freshly rendered output."""
        spans, unclosed = parsed
        missing, _, _ = _has_missing_zones(spans, unclosed, patterns)
        if missing:
            return []
        return self._check_spans_sync(Path(file_path), spans, catalog, patterns, file_cache)

    def _check_spans_sync(
        self,
        path_obj: Path,
        spans: list[FrameSpan],
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
        file_cache: FileContextCache,
    ) -> list[Diagnostic]:
        """Compare each valid frame span against freshly rendered output with span-level cascade guards."""
        rel_path = path_obj.resolve().relative_to(catalog.root).as_posix()
        for span in spans:
            pat = patterns[span.frame_id]
            if _cached_incomplete_provenance(span, pat, file_cache) or _cached_broken_route(
                path_obj, span, catalog, file_cache
            ):
                continue
            ctx = FrameRenderContext(path_obj.resolve(), rel_path, catalog, span)
            expected = pat.render_zone(span.zone, ctx)
            if span.inner_content.strip() != expected.strip():
                msg = f"Frame zone '{span.zone}' ({span.frame_id}) is out of sync; run DocFrame.update()."
                return [Diagnostic(str(path_obj), self.rule_id, span.start_line, msg, severity=self.severity)]
        return []


DocFrameMissingRule = DocFrameMissing
DocFrameOutdatedRule = DocFrameOutdated
DocFrameBrokenRouteRule = DocFrameBrokenRoute
DocFrameProvenanceRule = DocFrameProvenanceIncomplete

CUBIE_DOCFRAME_RULES: Final[tuple[WorkspaceCheckRuleProtocol, ...]] = (
    DocFrameMissing(severity="error"),
    DocFrameOutdated(severity="error"),
    DocFrameBrokenRoute(severity="error"),
    DocFrameProvenanceIncomplete(severity="error"),
)
