"""Lightweight line-based Markdown scanner producing structural MdBlock records."""

from __future__ import annotations

import re
import textwrap

from .protocols import MdBlock

_SUMMARY_RE = re.compile(r"<summary(?:\s[^>]*)?>(.*?)</summary>", re.DOTALL)
_NON_PARA_RE = re.compile(r"^(?:[-*+]\s|\d+[.)]\s|>+|(?:\|.*\|))")
_ALERT_RE = re.compile(r"^>\s*\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$", re.IGNORECASE)


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
            fence = self._fence_prefix(stripped)
            return self._consume_code_fence(idx, stripped[len(fence) :].strip(), fence)
        if stripped.startswith(("<!--", "<details")) or _ALERT_RE.match(stripped):
            self.in_list = False
            return self._consume_special(idx, stripped)
        return self._consume_text_line(idx, line, stripped)

    def _consume_special(self, idx: int, stripped: str) -> int:
        """Dispatches HTML comments, details blocks, and GitHub alert blockquotes."""
        if stripped.startswith("<!--"):
            return self._consume_html_comment(idx)
        if stripped.startswith("<details"):
            return self._consume_details(idx)
        return self._consume_alert(idx)

    def _consume_html_comment(self, start_idx: int) -> int:
        """Skips single-line or multi-line HTML comments without emitting blocks."""
        self._flush_paragraph()
        for idx in range(start_idx, len(self.lines)):
            if "-->" in self.lines[idx]:
                return idx + 1
        return len(self.lines)

    def _consume_alert(self, start_idx: int) -> int:
        """Consumes a GitHub alert blockquote and emits its body text as a paragraph."""
        self._flush_paragraph()
        body: list[str] = []
        idx = start_idx + 1
        while idx < len(self.lines) and self.lines[idx].strip().startswith(">"):
            text = re.sub(r"^>\s?", "", self.lines[idx].strip())
            if text:
                body.append(text)
            idx += 1
        if body:
            self.blocks.append(MdBlock(kind="paragraph", content="\n".join(body), line=start_idx + 1))
        return idx

    def _consume_text_line(self, idx: int, line: str, stripped: str) -> int:
        """Classifies headings, lists, blockquotes, tables, blank lines, and paragraphs."""
        is_non_para = bool(_NON_PARA_RE.match(stripped)) or (self.in_list and line != line.lstrip(" \t"))
        self._flush_if_boundary(stripped, is_non_para)
        self.in_list = is_non_para and bool(stripped) and not stripped.startswith("#")
        if stripped.startswith("#"):
            self.blocks.append(MdBlock(kind="heading", content=stripped, line=idx + 1))
        elif self.in_list:
            self.blocks.append(MdBlock(kind="list", content=stripped, line=idx + 1))
        elif stripped:
            self._append_paragraph(line, idx + 1)
        return idx + 1

    def _flush_if_boundary(self, stripped: str, is_non_para: bool) -> None:
        """Flushes active paragraphs when encountering blank lines or non-paragraph blocks."""
        if not stripped or stripped.startswith("#") or is_non_para:
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
        end_idx = self._find_details_end(start_idx)
        if end_idx is not None:
            raw = "\n".join(self.lines[start_idx : end_idx + 1])
            self.blocks.append(self._build_details_block(raw, start_idx + 1))
            return end_idx + 1
        self._append_paragraph(self.lines[start_idx], start_idx + 1)
        return start_idx + 1

    @staticmethod
    def _fence_prefix(stripped: str) -> str:
        """Extracts the leading backtick or tilde fence marker from a stripped line."""
        return stripped[: len(stripped) - len(stripped.lstrip(stripped[0]))]

    def _find_details_end(self, start_idx: int) -> int | None:
        """Finds the matching outer </details> line while ignoring fenced code blocks."""
        fence: str | None = None
        for idx in range(start_idx, len(self.lines)):
            s = self.lines[idx].strip()
            if fence is not None:
                fence = None if self._is_closing_fence(s, fence) else fence
            elif idx > start_idx and s.startswith("<details"):
                return None
            elif s.startswith(("```", "~~~")):
                fence = self._fence_prefix(s)
            elif "</details>" in self.lines[idx]:
                return idx
        return None

    @classmethod
    def _build_details_block(cls, raw: str, line_no: int) -> MdBlock:
        """Extracts the summary metadata and inner body from a raw details HTML block."""
        outer_lines, tagged = cls._partition_details_lines(raw.splitlines())
        outer_text = "\n".join(outer_lines)
        match = _SUMMARY_RE.search(outer_text)
        meta = match.group(1).strip() if match else ""
        cleaned_outer = _SUMMARY_RE.sub("", outer_text, count=1)
        cleaned_lines = re.sub(r"<details[^>]*>", "", cleaned_outer, count=1).split("\n")
        body = "\n".join(cls._merge_details_lines(tagged, cleaned_lines)).strip()
        return MdBlock(kind="details", content=body, line=line_no, meta=meta)

    @classmethod
    def _partition_details_lines(cls, lines: list[str]) -> tuple[list[str], list[tuple[bool, str]]]:
        """Splits details lines into outer HTML lines and tagged (is_fenced, text) pairs."""
        outer: list[str] = []
        tagged: list[tuple[bool, str]] = []
        fence: str | None = None
        for line in lines:
            fence, is_fenced = cls._step_details_fence(line.strip(), fence)
            chunk = line if is_fenced else cls._trim_details_close(line)
            tagged.append((is_fenced, chunk))
            if not is_fenced:
                outer.append(chunk)
                if "</details>" in line:
                    break
        return outer, tagged

    @classmethod
    def _step_details_fence(cls, stripped: str, fence: str | None) -> tuple[str | None, bool]:
        """Advances the inner code-fence state inside a details block."""
        if fence is not None:
            return (None if cls._is_closing_fence(stripped, fence) else fence), True
        if stripped.startswith(("```", "~~~")):
            return cls._fence_prefix(stripped), True
        return None, False

    @staticmethod
    def _trim_details_close(line: str) -> str:
        """Truncates a non-fenced details line before its closing </details> tag."""
        return line[: line.find("</details>")] if "</details>" in line else line

    @staticmethod
    def _merge_details_lines(tagged: list[tuple[bool, str]], cleaned_outer: list[str]) -> list[str]:
        """Recombines cleaned outer HTML lines with unmodified fenced code lines."""
        outer_iter = iter(cleaned_outer)
        return [line if is_fenced else next(outer_iter, "") for is_fenced, line in tagged]
