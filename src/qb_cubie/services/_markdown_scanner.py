"""Lightweight line-based Markdown scanner producing structural MdBlock records."""

from __future__ import annotations

import re
import textwrap

from .protocols import MdBlock

_SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)
_NON_PARA_RE = re.compile(r"^(?:[-*+]\s|\d+[.)]\s|>+|(?:\|.*\|))")


class _MarkdownScanner:
    """Lightweight line-based state machine converting Markdown text into MdBlocks."""

    def __init__(self, source: str) -> None:
        """Initializes scanner buffers for the given Markdown source text."""
        self.lines = source.splitlines()
        self.blocks: list[MdBlock] = []
        self.para_lines: list[str] = []
        self.para_start: int = 1
        self.in_list: bool = False

    def parse(self) -> list[MdBlock]:
        """Parses all lines into a flat sequence of structural MdBlocks."""
        idx = 0
        while idx < len(self.lines):
            idx = self._consume_line(idx)
        self._flush_paragraph()
        return self.blocks

    def _consume_line(self, idx: int) -> int:
        """Routes the current line to the matching block consumer and returns the next index."""
        line = self.lines[idx]
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            self.in_list = False
            fence = stripped[: len(stripped) - len(stripped.lstrip(stripped[0]))]
            return self._consume_code_fence(idx, stripped[len(fence) :].strip(), fence)
        if stripped.startswith("<details"):
            self.in_list = False
            return self._consume_details(idx)
        return self._consume_text_line(idx, line, stripped)

    def _consume_text_line(self, idx: int, line: str, stripped: str) -> int:
        """Classifies headings, lists, blockquotes, tables, blank lines, and paragraphs."""
        self._flush_if_boundary(stripped)
        if not stripped:
            self.in_list = False
        elif stripped.startswith("#"):
            self.in_list = False
            self.blocks.append(MdBlock(kind="heading", content=stripped, line=idx + 1))
        elif self.in_list or _NON_PARA_RE.match(stripped):
            self.in_list = True
            self.blocks.append(MdBlock(kind="list", content=stripped, line=idx + 1))
        else:
            self._append_paragraph(line, idx + 1)
        return idx + 1

    def _flush_if_boundary(self, stripped: str) -> None:
        """Flushes active paragraphs when encountering blank lines or non-paragraph blocks."""
        if not stripped or stripped.startswith("#") or self.in_list or _NON_PARA_RE.match(stripped):
            self._flush_paragraph()

    def _append_paragraph(self, line: str, line_no: int) -> None:
        """Appends a text line to the active paragraph buffer."""
        if not self.para_lines:
            self.para_start = line_no
        self.para_lines.append(line)

    def _flush_paragraph(self) -> None:
        """Emits the accumulated paragraph lines as a single paragraph MdBlock."""
        if self.para_lines:
            content = "\n".join(self.para_lines).strip()
            self.blocks.append(MdBlock(kind="paragraph", content=content, line=self.para_start))
            self.para_lines = []

    def _consume_code_fence(self, start_idx: int, meta: str, fence: str) -> int:
        """Consumes a fenced code block up to its matching closing backtick or tilde fence."""
        self._flush_paragraph()
        indent = len(self.lines[start_idx]) - len(self.lines[start_idx].lstrip(" "))
        body: list[str] = []
        idx = start_idx + 1
        while idx < len(self.lines) and not self._is_closing_fence(self.lines[idx].strip(), fence):
            body.append(self._strip_fence_indent(self.lines[idx], indent))
            idx += 1
        code = "\n".join(body) if indent > 0 else textwrap.dedent("\n".join(body))
        self.blocks.append(MdBlock(kind="code", content=code, line=start_idx + 1, meta=meta))
        return idx + 1

    @staticmethod
    def _strip_fence_indent(line: str, indent: int) -> str:
        """Strips up to the opening fence's leading space count from a code line."""
        lead = min(indent, len(line) - len(line.lstrip(" ")))
        return line[lead:]

    @staticmethod
    def _is_closing_fence(stripped: str, fence: str) -> bool:
        """Checks whether a stripped line closes the active backtick or tilde fence."""
        return (
            len(stripped) >= len(fence)
            and stripped.startswith(fence[0])
            and not stripped.lstrip(fence[0])
        )

    def _consume_details(self, start_idx: int) -> int:
        """Consumes a collapsible HTML details block if a closing tag precedes the next details."""
        self._flush_paragraph()
        for idx in range(start_idx, len(self.lines)):
            if idx > start_idx and self.lines[idx].strip().startswith("<details"):
                break
            if "</details>" in self.lines[idx]:
                raw = "\n".join(self.lines[start_idx : idx + 1])
                self.blocks.append(self._build_details_block(raw, start_idx + 1))
                return idx + 1
        self._append_paragraph(self.lines[start_idx], start_idx + 1)
        return start_idx + 1

    @staticmethod
    def _build_details_block(raw: str, line_no: int) -> MdBlock:
        """Extracts the summary metadata and inner body from a raw details HTML block."""
        closed_raw = raw[: raw.find("</details>")]
        summary_match = _SUMMARY_RE.search(closed_raw)
        meta = summary_match.group(1).strip() if summary_match else ""
        body = _SUMMARY_RE.sub("", closed_raw)
        body = re.sub(r"<details[^>]*>", "", body).strip()
        return MdBlock(kind="details", content=body, line=line_no, meta=meta)
