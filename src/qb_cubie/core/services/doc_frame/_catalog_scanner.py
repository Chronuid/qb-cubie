"""Fence-aware qb:frame comment parser and Pass 1 DocumentCatalog metadata extractor."""

from __future__ import annotations

from pathlib import Path

from ...service_core.guards import parse_bool_attr, parse_int_attr
from ...service_core.markdown import (
    HTML_WRAP_RE,
    DirectiveSpan,
    DirectiveSpanScanner,
    is_horizontal_rule,
    parse_kv_attrs,
)
from ...service_core.workspace import InMemoryWorkspaceView, WorkspaceView
from .protocols import DocMeta, DocumentCatalog, FrameSpan, sort_doc_metas, validate_zone


def _validate_frame_attrs(attrs: dict[str, str]) -> None:
    """Validate mandatory id and optional zone attributes on a qb:frame directive."""
    if not attrs.get("id", "").strip():
        raise ValueError("STATE-GUARD: qb:frame comment requires a non-empty 'id' attribute.")
    validate_zone(attrs.get("zone", "head"))


_FRAME_SCANNER = DirectiveSpanScanner("frame", validate_attrs=_validate_frame_attrs)


def parse_frame_spans(content: str) -> tuple[list[FrameSpan], list[int]]:
    """Extracts all fenced-safe qb:frame spans and line numbers of any unclosed opening tags."""
    raw_spans, unclosed = _FRAME_SCANNER.scan(content)
    return [_to_frame_span(span) for span in raw_spans], unclosed


def _to_frame_span(span: DirectiveSpan) -> FrameSpan:
    """Convert a generic DirectiveSpan into a typed DocFrame FrameSpan record."""
    return FrameSpan(
        frame_id=span.attrs["id"].strip(),
        zone=span.attrs.get("zone", "head"),
        attrs=span.attrs,
        open_tag=span.open_tag,
        inner_content=span.inner_content,
        close_tag=span.close_tag,
        start_line=span.start_line,
        end_line=span.end_line,
        start_idx=span.start_idx,
        end_idx=span.end_idx,
    )


def extract_doc_meta(rel_path: str, content: str) -> DocMeta:
    """Extracts Pass 1 routing metadata (title, label, summary, order, routable) from a document."""
    norm_path = Path(rel_path).as_posix().strip("/")
    spans, _ = parse_frame_spans(content)
    head = next((s for s in spans if s.zone == "head"), None)
    attrs = dict(head.attrs) if head is not None else {}
    title = _extract_h1_title(head.inner_content if head is not None else content, norm_path)
    label = attrs.get("label", "").strip() or title
    summary = _extract_header_summary(head.inner_content) if head is not None else ""
    order = _parse_optional_order(attrs.get("order"))
    routable = bool(content.strip()) and _parse_routable(attrs.get("routable"))
    category = Path(norm_path).parent.as_posix()
    return DocMeta(norm_path, head.frame_id if head else None, title, label, summary, order, routable, category, attrs)


def build_catalog_from_sources(
    root: Path,
    sources: list[tuple[str, str]],
    workspace: WorkspaceView | None = None,
) -> DocumentCatalog:
    """Builds a sorted DocumentCatalog from resolved (file_path, content) pairs."""
    resolved_root = root.resolve()
    entries = [
        extract_doc_meta(Path(fp).resolve().relative_to(resolved_root).as_posix(), text)
        for fp, text in sources
    ]
    ordered = tuple(sort_doc_metas(entries))
    ws = workspace if workspace is not None else InMemoryWorkspaceView(resolved_root, paths=tuple(e.path for e in ordered))
    return DocumentCatalog(root=resolved_root, entries=ordered, workspace=ws)


def _extract_h1_title(text: str, fallback_path: str) -> str:
    """Finds the first H1 Markdown heading or falls back to the file stem."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return Path(fallback_path).stem


def _extract_header_summary(inner_head: str) -> str:
    """Extracts the first narrative paragraph below the banner and before the first divider."""
    pre_divider = _slice_before_divider(inner_head.splitlines())
    para_lines: list[str] = []
    for line in pre_divider:
        stripped = line.strip()
        if _is_ignorable_header_line(stripped):
            if para_lines:
                break
            continue
        para_lines.append(stripped)
    return " ".join(para_lines)


def _slice_before_divider(lines: list[str]) -> list[str]:
    """Returns all lines inside a head frame preceding the first horizontal rule."""
    result: list[str] = []
    for line in lines:
        if is_horizontal_rule(line):
            break
        result.append(line)
    return result


def _is_ignorable_header_line(stripped: str) -> bool:
    """Checks whether a header line is blank, an HTML wrapper, a heading, or an image."""
    if not stripped or HTML_WRAP_RE.match(stripped):
        return True
    return stripped.startswith(("#", "!["))


def _parse_optional_order(raw_order: str | None) -> int | None:
    """Parses an optional integer order attribute or raises a ValueError STATE-GUARD."""
    return parse_int_attr(raw_order, "order", allow_none=True)


def _parse_routable(raw_routable: str | None) -> bool:
    """Parses an optional boolean routable attribute from a head marker tag."""
    return parse_bool_attr(raw_routable, "routable", default=True)


def parse_tag_attrs(attr_str: str) -> dict[str, str]:
    """Extracts strictly quoted key-value attribute pairs from a qb:frame HTML comment."""
    return parse_kv_attrs(attr_str, mode="quoted")
