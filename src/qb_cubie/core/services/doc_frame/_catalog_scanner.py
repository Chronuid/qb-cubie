"""Fence-aware qb:frame comment parser and Pass 1 DocumentCatalog metadata extractor."""

from __future__ import annotations

from pathlib import Path
import re

from .protocols import DocMeta, DocumentCatalog, FrameSpan, sort_doc_metas, validate_zone

_OPEN_TAG_RE = re.compile(r"^<!--\s*qb:frame\b([^>]*)-->$")
_CLOSE_TAG_RE = re.compile(r"^<!--\s*/qb:frame\s*-->$")
_ATTR_RE = re.compile(r'([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')')
_HTML_WRAP_RE = re.compile(r"^</?(?:div|center)\b[^>]*>$", re.IGNORECASE)


def parse_frame_spans(content: str) -> tuple[list[FrameSpan], list[int]]:
    """Extracts all fenced-safe qb:frame spans and line numbers of any unclosed opening tags."""
    scanner = _FrameSpanScanner(content)
    return scanner.parse()


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


def build_catalog_from_sources(root: Path, sources: list[tuple[str, str]]) -> DocumentCatalog:
    """Builds a sorted DocumentCatalog from resolved (file_path, content) pairs."""
    resolved_root = root.resolve()
    entries = [
        extract_doc_meta(Path(fp).resolve().relative_to(resolved_root).as_posix(), text)
        for fp, text in sources
    ]
    return DocumentCatalog(root=resolved_root, entries=tuple(sort_doc_metas(entries)))


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
        if line.strip() == "---":
            break
        result.append(line)
    return result


def _is_ignorable_header_line(stripped: str) -> bool:
    """Checks whether a header line is blank, an HTML wrapper, a heading, or an image."""
    if not stripped or _HTML_WRAP_RE.match(stripped):
        return True
    return stripped.startswith(("#", "!["))


def _parse_optional_order(raw_order: str | None) -> int | None:
    """Parses an optional integer order attribute or raises a ValueError STATE-GUARD."""
    if raw_order is None or not raw_order.strip():
        return None
    try:
        return int(raw_order.strip())
    except ValueError as exc:
        raise ValueError(f"STATE-GUARD: order attribute must be an integer; received {raw_order!r}.") from exc


def _parse_routable(raw_routable: str | None) -> bool:
    """Parses an optional boolean routable attribute from a head marker tag."""
    if raw_routable is None or not raw_routable.strip():
        return True
    low = raw_routable.strip().lower()
    if low in ("true", "1", "yes"):
        return True
    if low in ("false", "0", "no"):
        return False
    raise ValueError(f"STATE-GUARD: routable must be 'true' or 'false'; received {raw_routable!r}.")


def parse_tag_attrs(attr_str: str) -> dict[str, str]:
    """Extracts key-value attribute pairs from a qb:frame HTML comment."""
    return {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3)) for m in _ATTR_RE.finditer(attr_str)}


class _FrameSpanScanner:
    """Line-based state machine that extracts qb:frame spans while ignoring fenced code blocks."""

    def __init__(self, content: str) -> None:
        """Initializes scanner state with line offsets for the given Markdown text."""
        self.content = content
        self.lines = content.splitlines(keepends=True)
        self.fence: str | None = None
        self.active_open: tuple[int, int, str, dict[str, str], int] | None = None
        self.spans: list[FrameSpan] = []
        self.unclosed: list[int] = []

    def parse(self) -> tuple[list[FrameSpan], list[int]]:
        """Iterates over all lines and returns completed FrameSpans and unclosed tag lines."""
        offset = 0
        for idx, raw_line in enumerate(self.lines):
            self._consume_line(idx + 1, raw_line, offset)
            offset += len(raw_line)
        if self.active_open is not None:
            self.unclosed.append(self.active_open[0])
        return self.spans, self.unclosed

    def _consume_line(self, line_no: int, raw_line: str, offset: int) -> None:
        """Processes a single line for code fences or qb:frame open/close markers."""
        stripped = raw_line.strip()
        if self._update_fence(stripped):
            return
        if _OPEN_TAG_RE.match(stripped):
            self._open_span(line_no, stripped, offset, offset + len(raw_line))
        elif _CLOSE_TAG_RE.match(stripped) and self.active_open is not None:
            self._close_span(line_no, stripped, offset, offset + len(raw_line))

    def _update_fence(self, stripped: str) -> bool:
        """Tracks backtick or tilde code fences and returns True while inside a fence."""
        if self.fence is not None:
            if len(stripped) >= len(self.fence) and stripped.startswith(self.fence[0]) and not stripped.lstrip(self.fence[0]):
                self.fence = None
            return True
        if stripped.startswith(("```", "~~~")):
            self.fence = stripped[: len(stripped) - len(stripped.lstrip(stripped[0]))]
            return True
        return False

    def _open_span(self, line_no: int, stripped: str, start_idx: int, inner_start: int) -> None:
        """Records a new opening qb:frame tag and validates its zone and id attributes."""
        if self.active_open is not None:
            self.unclosed.append(self.active_open[0])
        match = _OPEN_TAG_RE.match(stripped)
        attrs = parse_tag_attrs(match.group(1) if match else "")
        frame_id = attrs.get("id", "").strip()
        if not frame_id:
            raise ValueError("STATE-GUARD: qb:frame comment requires a non-empty 'id' attribute.")
        validate_zone(attrs.get("zone", "head"))
        self.active_open = (line_no, start_idx, stripped, attrs, inner_start)

    def _close_span(self, line_no: int, stripped: str, close_start: int, end_idx: int) -> None:
        """Completes the active FrameSpan upon encountering a closing /qb:frame comment."""
        if self.active_open is None:
            return
        s_line, s_idx, open_tag, attrs, inner_start = self.active_open
        inner = self.content[inner_start:close_start]
        zone = attrs.get("zone", "head")
        span = FrameSpan(attrs["id"].strip(), zone, attrs, open_tag, inner, stripped, s_line, line_no, s_idx, end_idx)
        self.spans.append(span)
        self.active_open = None
