"""Optional Markdown lexer primitives for document-oriented qb-cubie services."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any, Final

from .guards import validate_choice, validate_str_sequence

VALID_KV_MODES: Final[tuple[str, ...]] = ("quoted", "unquoted_whitelist")
HTML_WRAP_RE: Final[re.Pattern[str]] = re.compile(r"^</?(?:div|center)\b[^>]*>$", re.IGNORECASE)

_DIRECTIVE_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")
_QUOTED_ATTR_RE: Final[re.Pattern[str]] = re.compile(
    r'([a-zA-Z_][a-zA-Z0-9_-]*)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')'
)
_HR_RE: Final[re.Pattern[str]] = re.compile(r"^[ \t]*([-*_])(?:[ \t]*\1){2,}[ \t]*$")

__all__ = [
    "HTML_WRAP_RE",
    "VALID_KV_MODES",
    "DirectiveSpan",
    "DirectiveSpanScanner",
    "FenceTracker",
    "apply_span_replacements",
    "compute_rel_link",
    "extract_fence_prefix",
    "is_closing_fence",
    "is_horizontal_rule",
    "parse_kv_attrs",
]


def extract_fence_prefix(line: str) -> str | None:
    """Return the leading backtick or tilde fence marker (>= 3 chars), or None."""
    stripped = line.strip()
    if not stripped.startswith(("```", "~~~")):
        return None
    char = stripped[0]
    length = len(stripped) - len(stripped.lstrip(char))
    return char * length


def is_closing_fence(line: str, active_fence: str) -> bool:
    """Check whether line closes active_fence under CommonMark length and char rules."""
    if not active_fence:
        return False
    stripped = line.strip()
    char = active_fence[0]
    return len(stripped) >= len(active_fence) and stripped.startswith(char) and not stripped.lstrip(char)


class FenceTracker:
    """Stateful CommonMark backtick/tilde code-fence tracker."""

    def __init__(self) -> None:
        """Initialize an inactive code-fence tracker."""
        self.fence: str | None = None

    @property
    def in_fence(self) -> bool:
        """Return True while currently inside an open fenced code block."""
        return self.fence is not None

    def feed(self, line: str) -> bool:
        """Advance fence state with one line and return True if the line belongs to a fence."""
        if self.fence is not None:
            if is_closing_fence(line, self.fence):
                self.fence = None
            return True
        opening = extract_fence_prefix(line)
        if opening is not None:
            self.fence = opening
            return True
        return False


def parse_kv_attrs(
    raw: Any,
    *,
    mode: Any = "quoted",
    allowed_keys: Any = None,
) -> dict[str, str]:
    """Parse inline key-value attributes in strict quoted or unquoted-whitelist mode."""
    if not isinstance(raw, str):
        raise TypeError(f"STATE-GUARD: raw must be a str; received {type(raw).__name__}.")
    norm_mode = validate_choice(mode, VALID_KV_MODES, "mode")
    allowed = validate_str_sequence(allowed_keys, "allowed_keys", allow_none=False) if allowed_keys is not None else None
    if norm_mode == "quoted":
        return _parse_quoted_attrs(raw, frozenset(allowed) if allowed is not None else None)
    return _parse_unquoted_whitelist_attrs(raw, allowed)


def _skip_ws(text: str, pos: int) -> int:
    """Advance pos past ASCII/Unicode whitespace characters in text."""
    while pos < len(text) and text[pos].isspace():
        pos += 1
    return pos


def _parse_quoted_attrs(raw: str, allowed_set: frozenset[str] | None) -> dict[str, str]:
    """Strictly parse whitespace-separated key='val' / key=\"val\" pairs without silent drops."""
    attrs: dict[str, str] = {}
    pos = _skip_ws(raw, 0)
    while pos < len(raw):
        match = _QUOTED_ATTR_RE.match(raw, pos)
        if match is None or (match.end() < len(raw) and not raw[match.end()].isspace()):
            raise ValueError(f"STATE-GUARD: Malformed or unquoted attribute near {raw[pos:]!r}.")
        key = match.group(1)
        if allowed_set is not None and key not in allowed_set:
            raise ValueError(f"STATE-GUARD: Unknown attribute key {key!r}.")
        attrs[key] = match.group(2) if match.group(2) is not None else match.group(3)
        pos = _skip_ws(raw, match.end())
    return attrs


def _parse_unquoted_whitelist_attrs(raw: str, allowed: tuple[str, ...] | None) -> dict[str, str]:
    """Extract whitelisted unquoted key=value tokens from fence metadata."""
    if not allowed or any(not key.strip() for key in allowed):
        raise ValueError("STATE-GUARD: allowed_keys must be a non-empty sequence of non-empty strings.")
    keys_pat = "|".join(re.escape(key) for key in allowed)
    pattern = re.compile(rf"\b(?P<key>{keys_pat})=(?P<val>[^\s,]+)")
    return {match.group("key"): match.group("val") for match in pattern.finditer(raw)}


@dataclass(frozen=True)
class DirectiveSpan:
    """Immutable coordinate-accurate record for a closed <!-- qb:<directive> ... --> span."""

    directive: str
    attrs: dict[str, str]
    open_tag: str
    inner_content: str
    close_tag: str
    start_line: int
    end_line: int
    start_idx: int
    end_idx: int


class DirectiveSpanScanner:
    """Fence-aware scanner for generic <!-- qb:<directive> ... --> ... <!-- /qb:<directive> --> blocks."""

    def __init__(
        self,
        directive: Any,
        *,
        validate_attrs: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        """Validate directive name and compile open, incomplete-open, and close tag patterns."""
        if not isinstance(directive, str):
            raise TypeError(f"STATE-GUARD: directive must be a str; received {type(directive).__name__}.")
        if not _DIRECTIVE_NAME_RE.match(directive):
            raise ValueError(f"STATE-GUARD: directive must be a valid identifier; received {directive!r}.")
        self.directive = directive
        self._validate_attrs = validate_attrs
        escaped = re.escape(directive)
        self._open_re = re.compile(rf"^<!--\s*qb:{escaped}(?=\s|-->)([^>]*)-->$")
        self._incomplete_re = re.compile(rf"^<!--\s*qb:{escaped}(?=\s|$)")
        self._close_re = re.compile(rf"^<!--\s*/qb:{escaped}\s*-->$")

    def scan(self, content: str) -> tuple[list[DirectiveSpan], list[int]]:
        """Scan Markdown text and return (closed_spans, unclosed_open_line_numbers)."""
        if not isinstance(content, str):
            raise TypeError(f"STATE-GUARD: content must be a str; received {type(content).__name__}.")
        state = _ScanState(content)
        offset = 0
        for line_no, raw_line in enumerate(content.splitlines(keepends=True), start=1):
            self._consume_line(state, line_no, raw_line, offset)
            offset += len(raw_line)
        if state.active_open is not None:
            state.unclosed.append(state.active_open[0])
        return state.spans, state.unclosed

    def _consume_line(self, state: _ScanState, line_no: int, raw_line: str, offset: int) -> None:
        """Process one source line while respecting active code fences."""
        if state.fences.feed(raw_line):
            return
        stripped = raw_line.strip()
        open_match = self._open_re.match(stripped)
        if open_match is not None:
            self._open_span(state, line_no, stripped, open_match.group(1), offset, offset + len(raw_line))
        elif self._incomplete_re.match(stripped):
            state.unclosed.append(line_no)
        elif self._close_re.match(stripped) and state.active_open is not None:
            self._close_span(state, line_no, stripped, offset, offset + len(raw_line))

    def _open_span(
        self,
        state: _ScanState,
        line_no: int,
        open_tag: str,
        raw_attrs: str,
        start_idx: int,
        inner_start: int,
    ) -> None:
        """Record an opening directive tag and flag any unclosed predecessor."""
        if state.active_open is not None:
            state.unclosed.append(state.active_open[0])
        attrs = parse_kv_attrs(raw_attrs, mode="quoted")
        if self._validate_attrs is not None:
            self._validate_attrs(attrs)
        state.active_open = (line_no, start_idx, open_tag, attrs, inner_start)

    def _close_span(
        self, state: _ScanState, line_no: int, close_tag: str, close_start: int, end_idx: int
    ) -> None:
        """Complete the currently open DirectiveSpan at its matching closing tag."""
        if state.active_open is None:
            return
        s_line, s_idx, open_tag, attrs, inner_start = state.active_open
        inner = state.content[inner_start:close_start]
        span = DirectiveSpan(self.directive, attrs, open_tag, inner, close_tag, s_line, line_no, s_idx, end_idx)
        state.spans.append(span)
        state.active_open = None


class _ScanState:
    """Mutable per-scan cursor state kept private to DirectiveSpanScanner.scan()."""

    def __init__(self, content: str) -> None:
        """Initialize buffers for one DirectiveSpanScanner.scan() pass."""
        self.content = content
        self.fences = FenceTracker()
        self.active_open: tuple[int, int, str, dict[str, str], int] | None = None
        self.spans: list[DirectiveSpan] = []
        self.unclosed: list[int] = []


def apply_span_replacements(content: str, replacements: Sequence[tuple[int, int, str]]) -> str:
    """Apply non-overlapping (start_idx, end_idx, replacement) slices deterministically."""
    if not isinstance(content, str):
        raise TypeError(f"STATE-GUARD: content must be a str; received {type(content).__name__}.")
    raw_items: Any = replacements
    if isinstance(raw_items, (str, bytes)) or not isinstance(raw_items, Sequence):
        raise TypeError(f"STATE-GUARD: replacements must be a sequence; received {type(raw_items).__name__}.")
    ordered = sorted(_validate_replacement(item, len(content)) for item in raw_items)
    _ensure_non_overlapping(ordered)
    result = content
    for start, end, text in reversed(ordered):
        result = result[:start] + text + result[end:]
    return result


def _validate_replacement(item: Any, length: int) -> tuple[int, int, str]:
    """Validate one (start, end, text) replacement entry for types and bounds."""
    if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or len(item) != 3:
        raise TypeError("STATE-GUARD: Each replacement must be a (start, end, text) 3-tuple.")
    start, end, text = item[0], item[1], item[2]
    if isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool) or not isinstance(end, int):
        raise TypeError("STATE-GUARD: Replacement start and end indices must be ints (not bool).")
    if not isinstance(text, str):
        raise TypeError(f"STATE-GUARD: Replacement text must be a str; received {type(text).__name__}.")
    if start < 0 or end < start or end > length:
        raise ValueError(f"STATE-GUARD: Replacement range ({start}, {end}) is out of bounds for length {length}.")
    return start, end, text


def _ensure_non_overlapping(ordered: list[tuple[int, int, str]]) -> None:
    """Reject any pair of overlapping replacement spans with a ValueError STATE-GUARD."""
    for prev, curr in zip(ordered, ordered[1:]):
        if curr[0] < prev[1]:
            raise ValueError(f"STATE-GUARD: Overlapping replacement spans ({prev[0]}, {prev[1]}) and ({curr[0]}, {curr[1]}).")


def is_horizontal_rule(line: str) -> bool:
    """Return True if line is a CommonMark thematic break (---, ***, ___ with optional spaces)."""
    if not isinstance(line, str):
        raise TypeError(f"STATE-GUARD: line must be a str; received {type(line).__name__}.")
    return bool(_HR_RE.match(line))


def compute_rel_link(from_file: Path, target_rel: str, root: Path) -> str:
    """Compute a POSIX relative Markdown link prefixed with ./ or ../ from a file to a repo path."""
    target_abs = (root.resolve() / target_rel.lstrip("/")).resolve()
    from_dir = from_file.resolve().parent
    rel = os.path.relpath(target_abs, start=from_dir).replace("\\", "/")
    return rel if rel.startswith(".") else f"./{rel}"
