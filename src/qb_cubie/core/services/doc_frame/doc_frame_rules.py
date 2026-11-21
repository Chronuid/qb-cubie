"""Prototype DocEnsurance diagnostic rules for Markdown frames (pending evaluation and hardening)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Final

from ...protocols import Diagnostic, FileCheckProtocol, validate_severity
from ._catalog_scanner import parse_frame_spans
from .doc_frame import DocFrame, FramePattern
from .frame_blocks import ProvenanceBlock, resolve_banner_rel_path
from .protocols import DocumentCatalog, FrameRenderContext, FrameSpan

_LINK_TARGET_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _has_missing_zones(
    spans: list[FrameSpan], unclosed: list[int], patterns: dict[str, FramePattern]
) -> tuple[bool, int, str]:
    """Checks whether a document has unclosed tags or is missing required head, foot, or router zones."""
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
    """Raises a STATE-GUARD ValueError if any frame span references an unknown FramePattern id."""
    for span in spans:
        if span.frame_id not in patterns:
            raise ValueError(
                f"STATE-GUARD: Unknown FramePattern id {span.frame_id!r} in {file_path}."
            )


def _find_incomplete_provenance(
    span: FrameSpan, pattern: FramePattern
) -> str | None:
    """Returns the first missing or empty required provenance key in a head span, or None."""
    prov = next((b for b in pattern.head if span.zone == "head" and isinstance(b, ProvenanceBlock)), None)
    if prov is None:
        return None
    existing = prov._parse_existing_bullets(span.inner_content)
    overrides = prov._extract_attr_overrides(span.attrs)
    return next((k for k in prov.required_keys if not overrides.get(k, existing.get(k, "")).strip()), None)


def _find_broken_route_in_span(
    file_path: Path, span: FrameSpan, root: Path
) -> str | None:
    """Returns the first non-existent asset or link target referenced by a frame span, or None."""
    banner = span.attrs.get("banner", "").strip()
    if banner:
        banner_rel = resolve_banner_rel_path(banner, root)
        if not (root / banner_rel).exists():
            return banner_rel
    for raw_target in _LINK_TARGET_RE.findall(span.inner_content):
        clean = raw_target.split("#", 1)[0].split("?", 1)[0].strip()
        if not clean or clean.startswith(("http://", "https://", "mailto:")):
            continue
        if not (file_path.resolve().parent / clean).resolve().exists():
            return clean
    return None


def _prepare_docframe_context(
    target: str | Path,
    excludes: Sequence[str],
    patterns: Sequence[Any],
) -> tuple[DocumentCatalog, dict[str, FramePattern]]:
    """Builds the Pass 1 DocumentCatalog and FramePattern map for document-level checks."""
    frame_pats = tuple(p for p in patterns if isinstance(p, FramePattern)) or None
    frame_svc = DocFrame(target=target, pattern=frame_pats, excludes=excludes)
    return frame_svc.build_catalog(), frame_svc.patterns


class _DocFrameRuleBase:
    """Shared FileCheckProtocol adapter for DocFrame document-level diagnostic rules."""

    @property
    def context_key(self) -> str:
        """Returns the shared cache key so all DocFrame rules reuse one catalog build."""
        return "doc_frame"

    def prepare_context(
        self,
        target: str | Path,
        excludes: Sequence[str],
        patterns: Sequence[Any],
    ) -> tuple[DocumentCatalog, dict[str, FramePattern]]:
        """Builds the shared DocumentCatalog and normalized FramePattern registry."""
        return _prepare_docframe_context(target, excludes, patterns)

    def check_file(
        self,
        file_path: str,
        content: str,
        context: tuple[DocumentCatalog, dict[str, FramePattern]],
    ) -> list[Diagnostic]:
        """Delegates a single-file check to check_document using the prepared frame context."""
        catalog, patterns = context
        return self.check_document(file_path, content, catalog, patterns)

    def check_document(
        self,
        file_path: str,
        content: str,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
    ) -> list[Diagnostic]:
        """Evaluates a single Markdown document against this frame rule."""
        raise NotImplementedError


# ========== DOC-FRAME DIAGNOSTIC RULES ================================================================================
@dataclass(frozen=True)
class DocFrameMissing(_DocFrameRuleBase):
    """Flags Markdown files missing required head, foot, or router qb:frame blocks."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-MISSING"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: Any, actual_output: str | None = None
    ) -> list[Diagnostic]:
        """No-op on code snippets; frame checks run at the document level."""
        _ = (example, actual_output)
        return []

    def check_document(
        self,
        file_path: str,
        content: str,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
    ) -> list[Diagnostic]:
        """Emits DOCFRAME-MISSING when a document lacks valid head, foot, or router blocks."""
        _ = catalog
        spans, unclosed = parse_frame_spans(content)
        _validate_known_patterns(spans, patterns, file_path)
        missing, line, msg = _has_missing_zones(spans, unclosed, patterns)
        if missing:
            return [Diagnostic(file_path, self.rule_id, line, msg, severity=self.severity)]
        return []


@dataclass(frozen=True)
class DocFrameProvenanceIncomplete(_DocFrameRuleBase):
    """Flags CUBIE_DOC_FRAME_2 documents with missing or empty required provenance fields."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-PROVENANCE-INCOMPLETE"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: Any, actual_output: str | None = None
    ) -> list[Diagnostic]:
        """No-op on code snippets; frame checks run at the document level."""
        _ = (example, actual_output)
        return []

    def check_document(
        self,
        file_path: str,
        content: str,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
    ) -> list[Diagnostic]:
        """Emits DOCFRAME-PROVENANCE-INCOMPLETE when a required provenance key is blank or absent."""
        _ = catalog
        spans, unclosed = parse_frame_spans(content)
        _validate_known_patterns(spans, patterns, file_path)
        if unclosed:
            return []
        for span in spans:
            missing_key = _find_incomplete_provenance(span, patterns[span.frame_id])
            if missing_key is not None:
                msg = f"Required provenance field '{missing_key}' is missing or empty."
                return [Diagnostic(file_path, self.rule_id, span.start_line, msg, severity=self.severity)]
        return []


@dataclass(frozen=True)
class DocFrameBrokenRoute(_DocFrameRuleBase):
    """Flags qb:frame blocks that reference non-existent Markdown routes or banner assets."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-BROKEN-ROUTE"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: Any, actual_output: str | None = None
    ) -> list[Diagnostic]:
        """No-op on code snippets; frame checks run at the document level."""
        _ = (example, actual_output)
        return []

    def check_document(
        self,
        file_path: str,
        content: str,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
    ) -> list[Diagnostic]:
        """Emits DOCFRAME-BROKEN-ROUTE when a linked document or banner asset is missing on disk."""
        spans, unclosed = parse_frame_spans(content)
        _validate_known_patterns(spans, patterns, file_path)
        if unclosed:
            return []
        path_obj = Path(file_path)
        for span in spans:
            broken = _find_broken_route_in_span(path_obj, span, catalog.root)
            if broken is not None:
                msg = f"Broken route or asset reference in frame ({span.zone}): {broken!r} not found."
                return [Diagnostic(file_path, self.rule_id, span.start_line, msg, severity=self.severity)]
        return []


@dataclass(frozen=True)
class DocFrameOutdated(_DocFrameRuleBase):
    """Flags qb:frame blocks whose stored content diverges from the current DocumentCatalog."""

    severity: str = "error"
    rule_id: str = "DOCFRAME-OUTDATED"

    def __post_init__(self) -> None:
        validate_severity(self.severity)

    def check(
        self, example: Any, actual_output: str | None = None
    ) -> list[Diagnostic]:
        """No-op on code snippets; frame checks run at the document level."""
        _ = (example, actual_output)
        return []

    def check_document(
        self,
        file_path: str,
        content: str,
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
    ) -> list[Diagnostic]:
        """Emits DOCFRAME-OUTDATED when a well-formed frame zone differs from freshly rendered output."""
        spans, unclosed = parse_frame_spans(content)
        _validate_known_patterns(spans, patterns, file_path)
        missing, _, _ = _has_missing_zones(spans, unclosed, patterns)
        if missing:
            return []
        return self._check_spans_sync(Path(file_path), spans, catalog, patterns)

    def _check_spans_sync(
        self,
        path_obj: Path,
        spans: list[FrameSpan],
        catalog: DocumentCatalog,
        patterns: dict[str, FramePattern],
    ) -> list[Diagnostic]:
        """Compares each valid frame span against the freshly rendered zone output."""
        rel_path = path_obj.resolve().relative_to(catalog.root).as_posix()
        for span in spans:
            pat = patterns[span.frame_id]
            if _find_incomplete_provenance(span, pat) or _find_broken_route_in_span(path_obj, span, catalog.root):
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

CUBIE_DOCFRAME_RULES: Final[tuple[FileCheckProtocol, ...]] = (
    DocFrameMissing(severity="error"),
    DocFrameOutdated(severity="error"),
    DocFrameBrokenRoute(severity="error"),
    DocFrameProvenanceIncomplete(severity="error"),
)
