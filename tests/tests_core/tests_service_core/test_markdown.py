"""**Tries to** specify Cycle 2 Markdown lexer primitives in core.service_core.markdown and service integrations."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

from qb_cubie import EBT, ExceptionExpectation, WorldState
from qb_cubie.core.services.doc_ensurance import (
    CUBIE_DOC_STYLE,
    CodeSnippet,
    DocEnsurance,
    _MarkdownScanner,
)
from qb_cubie.core.services.doc_frame import parse_frame_spans

pytestmark = pytest.mark.services


def _markdown_module() -> Any:
    """Lazily imports qb_cubie.core.service_core.markdown so Phase-Red collection stays clean."""
    return importlib.import_module("qb_cubie.core.service_core.markdown")


# ---------- Stateless Test Adapters -----------------------------------------------------------------------------------


def _trace_fence_lines(lines: list[str]) -> list[tuple[bool, bool, str | None]]:
    """Feeds lines into FenceTracker and records (is_fenced_line, in_fence_after, active_fence)."""
    tracker = _markdown_module().FenceTracker()
    trace: list[tuple[bool, bool, str | None]] = []
    for line in lines:
        in_block = tracker.feed(line)
        trace.append((in_block, tracker.in_fence, tracker.fence))
    return trace


def _call_parse_kv_attrs(
    raw: Any,
    mode: Any = "quoted",
    allowed_keys: Any = None,
) -> dict[str, str]:
    """Invokes service_core.markdown.parse_kv_attrs with explicit mode and optional whitelist."""
    return _markdown_module().parse_kv_attrs(raw, mode=mode, allowed_keys=allowed_keys)


def _scan_directive_summary(directive: str, content: str) -> dict[str, Any]:
    """Scans a Markdown document with DirectiveSpanScanner and projects spans to a flat dict."""
    scanner = _markdown_module().DirectiveSpanScanner(directive)
    spans, unclosed = scanner.scan(content)
    return {
        "spans": [
            {
                "directive": span.directive,
                "attrs": dict(span.attrs),
                "inner": span.inner_content,
                "lines": (span.start_line, span.end_line),
                "slice_matches": content[span.start_idx : span.end_idx]
                == f"{span.open_tag}\n{span.inner_content}{span.close_tag}"
                or content[span.start_idx : span.end_idx].startswith(span.open_tag),
            }
            for span in spans
        ],
        "unclosed": list(unclosed),
    }


def _call_directive_scanner(directive: Any, content: str = "") -> Any:
    """Constructs DirectiveSpanScanner and runs scan() for STATE-GUARD validation."""
    scanner = _markdown_module().DirectiveSpanScanner(directive)
    return scanner.scan(content)


def _call_apply_replacements(content: str, replacements: Any) -> str:
    """Invokes service_core.markdown.apply_span_replacements."""
    return _markdown_module().apply_span_replacements(content, replacements)


def _call_is_horizontal_rule(line: str) -> bool:
    """Invokes service_core.markdown.is_horizontal_rule."""
    return _markdown_module().is_horizontal_rule(line)


def _call_compute_rel_link(from_file: Path, target_rel: str, root: Path) -> str:
    """Invokes service_core.markdown.compute_rel_link."""
    return _markdown_module().compute_rel_link(from_file, target_rel, root)


def _scan_doc_ensurance_block_kinds(markdown: str) -> list[tuple[str, str]]:
    """Parses Markdown with DocEnsurance's _MarkdownScanner and returns (kind, content) pairs."""
    blocks = _MarkdownScanner(markdown).parse()
    return [(block.kind, block.content) for block in blocks]


def _run_doc_ensurance_on_hr_preceded_snippet() -> dict[str, Any]:
    """Runs DocEnsurance on a snippet preceded only by a 25-char horizontal rule."""
    markdown = (
        "# Heading\n\n"
        "-------------------------\n\n"
        "```python\n"
        "print('hello')\n"
        "```\n\n"
        "<details>\n<summary>Ergebnis</summary>\n\n```text\nhello\n```\n</details>\n"
    )
    report = DocEnsurance(target=markdown, pattern=CUBIE_DOC_STYLE, reporter=None).run()
    return {
        "passed": report.passed,
        "rule_ids": [diag.rule_id for diag in report.diagnostics],
    }


# ======================================================================================================================
# 1. FenceTracker (CommonMark Backtick & Tilde Fences — Mutant M5)
# ======================================================================================================================


def test_ebt_fence_tracker_handles_backticks_and_tildes() -> None:
    """Basic backtick and tilde fences toggle state cleanly and ignore non-fenced text."""
    lines = [
        "Intro text",
        "```python",
        "x = 1",
        "```",
        "Between fences",
        "~~~text",
        "raw",
        "~~~",
        "After fences",
    ]
    expected = [
        (False, False, None),
        (True, True, "```"),
        (True, True, "```"),
        (True, False, None),
        (False, False, None),
        (True, True, "~~~"),
        (True, True, "~~~"),
        (True, False, None),
        (False, False, None),
    ]
    EBT(
        target=_trace_fence_lines,
        pre=WorldState(args=(lines,)),
        post=WorldState(returns=expected),
        custom_id="service_core_markdown_fence_basic",
    ).run()


def test_ebt_fence_tracker_keeps_four_backtick_fence_open_on_three_backticks() -> None:
    """Mutant M5: a 4-backtick fence stays open on inner 3-backtick lines and closes on >= 4 backticks."""
    lines = [
        "````markdown",
        "```python",
        "print(1)",
        "```",
        "`````",
        "Outside",
    ]
    expected = [
        (True, True, "````"),
        (True, True, "````"),
        (True, True, "````"),
        (True, True, "````"),
        (True, False, None),
        (False, False, None),
    ]
    EBT(
        target=_trace_fence_lines,
        pre=WorldState(args=(lines,)),
        post=WorldState(returns=expected),
        custom_id="service_core_markdown_fence_mutant_m5",
    ).run()


def test_ebt_fence_tracker_rejects_mismatched_chars_and_trailing_info_as_closers() -> None:
    """Tildes and backtick lines with trailing info text never close an active backtick fence."""
    lines = [
        "  ```python",
        "~~~",
        "```python",
        "  ```  ",
        "plain",
    ]
    expected = [
        (True, True, "```"),
        (True, True, "```"),
        (True, True, "```"),
        (True, False, None),
        (False, False, None),
    ]
    EBT(
        target=_trace_fence_lines,
        pre=WorldState(args=(lines,)),
        post=WorldState(returns=expected),
        custom_id="service_core_markdown_fence_strict_close",
    ).run()


def test_ebt_fence_helper_functions_contract() -> None:
    """extract_fence_prefix and is_closing_fence enforce CommonMark length and character matching."""

    def _probe() -> dict[str, Any]:
        md = _markdown_module()
        return {
            "open_bt3": md.extract_fence_prefix("```python"),
            "open_bt4": md.extract_fence_prefix("  ````markdown"),
            "open_tilde": md.extract_fence_prefix("~~~"),
            "open_none": md.extract_fence_prefix("``not-a-fence"),
            "close_ok": md.is_closing_fence("````", "````"),
            "close_longer_ok": md.is_closing_fence("`````", "````"),
            "close_short_fail": md.is_closing_fence("```", "````"),
            "close_mismatch_fail": md.is_closing_fence("~~~", "```"),
            "close_info_fail": md.is_closing_fence("```text", "```"),
        }

    expected = {
        "open_bt3": "```",
        "open_bt4": "````",
        "open_tilde": "~~~",
        "open_none": None,
        "close_ok": True,
        "close_longer_ok": True,
        "close_short_fail": False,
        "close_mismatch_fail": False,
        "close_info_fail": False,
    }
    EBT(
        target=_probe,
        pre=WorldState(),
        post=WorldState(returns=expected),
        custom_id="service_core_markdown_fence_helpers",
    ).run()


# ======================================================================================================================
# 2. parse_kv_attrs (Quoted Directive Mode & Unquoted Whitelist Mode — Mutant M6 / E3)
# ======================================================================================================================


def test_ebt_parse_kv_attrs_quoted_mode_parses_valid_attributes() -> None:
    """Quoted mode parses double/single-quoted values, whitespace around '=', and empty values."""
    raw = ' id="CUBIE_DOC_FRAME_1" zone = \'head\' banner="cubie-logo.png" label="Service Core" empty="" '
    expected = {
        "id": "CUBIE_DOC_FRAME_1",
        "zone": "head",
        "banner": "cubie-logo.png",
        "label": "Service Core",
        "empty": "",
    }
    EBT(
        target=_call_parse_kv_attrs,
        pre=WorldState(args=(raw, "quoted")),
        post=WorldState(returns=expected),
        custom_id="service_core_markdown_kv_quoted_valid",
    ).run()


def test_ebt_parse_kv_attrs_quoted_mode_empty_input_returns_empty_dict() -> None:
    """Empty or whitespace-only attribute strings return an empty dict in quoted mode."""
    EBT(
        target=_call_parse_kv_attrs,
        pre=[WorldState(args=("", "quoted")), WorldState(args=("   \t  ", "quoted"))],
        post=WorldState(returns={}),
        custom_id="service_core_markdown_kv_quoted_empty",
    ).run()


def test_ebt_parse_kv_attrs_quoted_rejects_unquoted_and_malformed_tokens() -> None:
    """Mutant M6 / E3: quoted mode raises ValueError STATE-GUARD on unquoted values or stray tokens."""
    EBT(
        target=_call_parse_kv_attrs,
        pre=[
            WorldState(args=('id="CUBIE_DOC_FRAME_1" order=10', "quoted")),
            WorldState(args=("zone=head", "quoted")),
            WorldState(args=('id="CUBIE_DOC_FRAME_1" stray_token', "quoted")),
            WorldState(args=('id="unclosed', "quoted")),
            WorldState(args=('id="ok" = "missing_key"', "quoted")),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_kv_quoted_mutant_m6",
    ).run()


def test_ebt_parse_kv_attrs_quoted_respects_optional_allowed_keys() -> None:
    """When allowed_keys is supplied in quoted mode, unknown keys raise ValueError STATE-GUARD."""
    EBT(
        target=_call_parse_kv_attrs,
        pre=WorldState(args=('id="A" zone="head"', "quoted", ("id", "zone"))),
        post=WorldState(returns={"id": "A", "zone": "head"}),
        custom_id="service_core_markdown_kv_quoted_whitelist_ok",
    ).run()
    EBT(
        target=_call_parse_kv_attrs,
        pre=WorldState(args=('id="A" unknown="x"', "quoted", ("id", "zone"))),
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_kv_quoted_whitelist_reject",
    ).run()


def test_ebt_parse_kv_attrs_unquoted_whitelist_extracts_fence_tags() -> None:
    """Unquoted whitelist mode extracts whitelisted key=val fence tags and ignores unrelated tokens."""
    EBT(
        target=_call_parse_kv_attrs,
        pre=WorldState(args=("python session=demo_1, raises=ValueError extra=ignored flag", "unquoted_whitelist", ("session", "raises"))),
        post=WorldState(returns={"session": "demo_1", "raises": "ValueError"}),
        custom_id="service_core_markdown_kv_unquoted_whitelist_ok",
    ).run()


def test_ebt_parse_kv_attrs_state_guards_on_invalid_arguments() -> None:
    """Invalid raw type, unknown mode, or missing/invalid allowed_keys trigger STATE-GUARD errors."""
    EBT(
        target=_call_parse_kv_attrs,
        pre=[
            WorldState(args=(None, "quoted")),
            WorldState(args=(123, "quoted")),
            WorldState(args=("python session=x", "unquoted_whitelist", "session")),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_kv_type_guards",
    ).run()
    EBT(
        target=_call_parse_kv_attrs,
        pre=[
            WorldState(args=('id="X"', "loose")),
            WorldState(args=("python session=x", "unquoted_whitelist", None)),
            WorldState(args=("python session=x", "unquoted_whitelist", ())),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_kv_value_guards",
    ).run()


# ======================================================================================================================
# 3. DirectiveSpanScanner (Generic <!-- qb:<directive> ... --> Extraction)
# ======================================================================================================================


def test_ebt_directive_span_scanner_extracts_generic_directives_and_ignores_fences_and_siblings() -> None:
    """DirectiveSpanScanner extracts only the requested directive while ignoring code fences and sibling directives."""
    doc = (
        "# Title\n"
        '<!-- qb:other id="IGNORE" -->\n'
        "other body\n"
        "<!-- /qb:other -->\n"
        "````markdown\n"
        "```text\n"
        '<!-- qb:toc id="FENCED" -->\n'
        "<!-- /qb:toc -->\n"
        "```\n"
        "````\n"
        '<!-- qb:toc depth="2" mode="links" -->\n'
        "- Section A\n"
        "<!-- /qb:toc -->\n"
    )
    expected = {
        "spans": [
            {
                "directive": "toc",
                "attrs": {"depth": "2", "mode": "links"},
                "inner": "- Section A\n",
                "lines": (11, 13),
                "slice_matches": True,
            }
        ],
        "unclosed": [],
    }
    EBT(
        target=_scan_directive_summary,
        pre=WorldState(args=("toc", doc)),
        post=WorldState(returns=expected),
        custom_id="service_core_markdown_directive_scanner_generic",
    ).run()


def test_ebt_directive_span_scanner_reports_eof_nested_and_incomplete_open_tags() -> None:
    """Unclosed EOF tags, nested re-opens, and incomplete multi-line open tags are all reported in unclosed."""
    doc_eof = '<!-- qb:toc id="A" -->\ncontent without close\n'
    doc_nested = '<!-- qb:toc id="A" -->\n<!-- qb:toc id="B" -->\nok\n<!-- /qb:toc -->\n'
    doc_multiline_open = '<!-- qb:toc id="A"\n depth="2" -->\ncontent\n<!-- /qb:toc -->\n'

    EBT(
        target=_scan_directive_summary,
        pre=WorldState(args=("toc", doc_eof)),
        post=WorldState(returns={"spans": [], "unclosed": [1]}),
        custom_id="service_core_markdown_directive_unclosed_eof",
    ).run()
    EBT(
        target=_scan_directive_summary,
        pre=WorldState(args=("toc", doc_nested)),
        post=WorldState(
            returns={
                "spans": [
                    {
                        "directive": "toc",
                        "attrs": {"id": "B"},
                        "inner": "ok\n",
                        "lines": (2, 4),
                        "slice_matches": True,
                    }
                ],
                "unclosed": [1],
            }
        ),
        custom_id="service_core_markdown_directive_unclosed_nested",
    ).run()
    EBT(
        target=_scan_directive_summary,
        pre=WorldState(args=("toc", doc_multiline_open)),
        post=WorldState(returns={"spans": [], "unclosed": [1]}),
        custom_id="service_core_markdown_directive_incomplete_multiline_open",
    ).run()


def test_ebt_directive_span_scanner_rejects_unquoted_attrs_and_invalid_directive_names() -> None:
    """Unquoted attributes inside a directive and invalid directive identifiers raise STATE-GUARD errors."""
    EBT(
        target=_call_directive_scanner,
        pre=[
            WorldState(args=("toc", '<!-- qb:toc depth=2 -->\n<!-- /qb:toc -->\n')),
            WorldState(args=("", "text")),
            WorldState(args=("bad name", "text")),
            WorldState(args=("123bad", "text")),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_directive_value_guards",
    ).run()
    EBT(
        target=_call_directive_scanner,
        pre=[WorldState(args=(None, "text")), WorldState(args=(42, "text"))],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_directive_type_guards",
    ).run()


# ======================================================================================================================
# 4. apply_span_replacements, is_horizontal_rule & compute_rel_link
# ======================================================================================================================


def test_ebt_apply_span_replacements_handles_unsorted_and_adjacent_spans() -> None:
    """Replacements are applied deterministically regardless of order and preserve untouched text."""
    content = "0123456789"
    EBT(
        target=_call_apply_replacements,
        pre=WorldState(args=(content, [(5, 10, "BB"), (0, 5, "AA")])),
        post=WorldState(returns="AABB"),
        custom_id="service_core_markdown_apply_unsorted_adjacent",
    ).run()
    EBT(
        target=_call_apply_replacements,
        pre=WorldState(args=(content, [])),
        post=WorldState(returns=content),
        custom_id="service_core_markdown_apply_empty",
    ).run()


def test_ebt_apply_span_replacements_rejects_overlapping_and_invalid_ranges() -> None:
    """H4(c): overlapping spans, out-of-bounds indices, and bool/non-int indices raise STATE-GUARD."""
    content = "0123456789"
    EBT(
        target=_call_apply_replacements,
        pre=[
            WorldState(args=(content, [(2, 6, "X"), (5, 8, "Y")])),
            WorldState(args=(content, [(0, 10, "X"), (3, 4, "Y")])),
            WorldState(args=(content, [(-1, 3, "X")])),
            WorldState(args=(content, [(0, 11, "X")])),
            WorldState(args=(content, [(6, 4, "X")])),
        ],
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_apply_overlap_and_bounds_guard",
    ).run()
    EBT(
        target=_call_apply_replacements,
        pre=[
            WorldState(args=(content, [(True, 3, "X")])),
            WorldState(args=(content, [(0, "3", "X")])),
        ],
        post=WorldState(raises=ExceptionExpectation(TypeError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_apply_index_type_guard",
    ).run()


@pytest.mark.parametrize("line", ["---", "***", "___", "-----", "- - -", "  * * *  "])
def test_ebt_is_horizontal_rule_accepts_commonmark_thematic_breaks(line: str) -> None:
    """CommonMark thematic breaks (---, ***, ___, spaced variants) are recognized as horizontal rules."""
    EBT(
        target=_call_is_horizontal_rule,
        pre=WorldState(args=(line,)),
        post=WorldState(returns=True),
        custom_id="service_core_markdown_hr_valid",
    ).run()


@pytest.mark.parametrize("line", ["", "--", "--- text", "- item", "*bold*", "___x", "a---"])
def test_ebt_is_horizontal_rule_rejects_non_rules(line: str) -> None:
    """Short dashes, list items, emphasis, and mixed lines are not horizontal rules."""
    EBT(
        target=_call_is_horizontal_rule,
        pre=WorldState(args=(line,)),
        post=WorldState(returns=False),
        custom_id="service_core_markdown_hr_invalid",
    ).run()


def test_ebt_compute_rel_link_produces_posix_relative_links(tmp_path: Path) -> None:
    """compute_rel_link returns POSIX ./ and ../ paths across repository depths."""
    root = tmp_path / "repo"
    EBT(
        target=_call_compute_rel_link,
        pre=WorldState(args=(root / "README.md", "docs/GUIDE.md", root)),
        post=WorldState(returns="./docs/GUIDE.md"),
        custom_id="service_core_markdown_rel_link_down",
    ).run()
    EBT(
        target=_call_compute_rel_link,
        pre=WorldState(args=(root / "docs" / "services" / "GUIDE.md", "README.md", root)),
        post=WorldState(returns="../../README.md"),
        custom_id="service_core_markdown_rel_link_up",
    ).run()


# ======================================================================================================================
# 5. Cycle 2 Integrations: _MarkdownScanner 'hr' Fix & DocFrame Strict Quoted Attributes
# ======================================================================================================================


def test_ebt_markdown_scanner_classifies_horizontal_rules_as_hr_not_paragraph() -> None:
    """H4(a): DocEnsurance's _MarkdownScanner parses --- / *** / ___ as kind='hr', never 'paragraph'."""
    md = "# Title\n\n---\n\n***\n\n___\n\nReal paragraph text.\n"
    expected = [
        ("heading", "# Title"),
        ("hr", "---"),
        ("hr", "***"),
        ("hr", "___"),
        ("paragraph", "Real paragraph text."),
    ]
    EBT(
        target=_scan_doc_ensurance_block_kinds,
        pre=WorldState(args=(md,)),
        post=WorldState(returns=expected),
        custom_id="service_core_markdown_doc_ensurance_hr_kind",
    ).run()


def test_ebt_doc_ensurance_does_not_accept_long_hr_as_explanation_paragraph() -> None:
    """H4(a) integration: a 25-char '---...' rule before a snippet triggers DOC-PRE instead of passing Explanation."""
    EBT(
        target=_run_doc_ensurance_on_hr_preceded_snippet,
        pre=WorldState(),
        post=WorldState(returns={"passed": False, "rule_ids": ["DOC-PRE"]}),
        custom_id="service_core_markdown_doc_ensurance_hr_not_explanation",
    ).run()


def test_ebt_docframe_parse_frame_spans_rejects_unquoted_attribute() -> None:
    """H4(b) / E3 / Mutant M6: DocFrame rejects unquoted attributes like order=10 with ValueError STATE-GUARD."""
    bad_doc = '<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" order=10 -->\n# Title\n<!-- /qb:frame -->\n'
    EBT(
        target=parse_frame_spans,
        pre=WorldState(args=(bad_doc,)),
        post=WorldState(raises=ExceptionExpectation(ValueError, match=r"STATE-GUARD:")),
        custom_id="service_core_markdown_docframe_rejects_unquoted_attr",
    ).run()


def test_ebt_doc_ensurance_code_snippet_parse_tags_matches_service_core_markdown() -> None:
    """DocEnsurance CodeSnippet.parse_tags produces identical output to service_core.markdown.parse_kv_attrs."""

    def _probe(meta: str) -> dict[str, Any]:
        via_snippet = CodeSnippet.parse_tags(meta)
        via_core = _markdown_module().parse_kv_attrs(
            meta, mode="unquoted_whitelist", allowed_keys=("session", "raises")
        )
        return {"snippet": via_snippet, "core": via_core, "equal": via_snippet == via_core}

    EBT(
        target=_probe,
        pre=WorldState(args=("python session=s_1, raises=TypeError ignored=abc",)),
        post=WorldState(
            returns={
                "snippet": {"session": "s_1", "raises": "TypeError"},
                "core": {"session": "s_1", "raises": "TypeError"},
                "equal": True,
            }
        ),
        custom_id="service_core_markdown_code_snippet_parse_tags",
    ).run()
