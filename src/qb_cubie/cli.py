"""Core command-line interface for qb-cubie."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
import sys
from typing import Any

from .services.doc_frame import DocFrame, DocFrameReport


def main(argv: Sequence[str] | None = None) -> int:
    """Runs the qb-cubie core CLI and returns its process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        payload = _dispatch(args)
        print(_render_output(payload, args.format))
        return 0
    except (ValueError, TypeError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    """Constructs the top-level qb-cubie argument parser."""
    parser = argparse.ArgumentParser(prog="qb-cubie", description="qb-cubie command-line interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_docframe_parser(subparsers)
    return parser


def _add_docframe_parser(subparsers: Any) -> None:
    """Registers the 'docframe' command group (prototype) and its subcommands."""
    df_parser = subparsers.add_parser(
        "docframe", help="Document frame tools (prototype; pending evaluation and hardening)."
    )
    df_sub = df_parser.add_subparsers(dest="docframe_command", required=True)
    update_parser = df_sub.add_parser("update", help="Synchronize qb:frame header, router, and footer blocks.")
    update_parser.add_argument(
        "target", nargs="?", default=None, help="Optional file or directory path (default: project root)."
    )
    update_parser.add_argument(
        "--exclude", action="append", default=[], dest="excludes", help="Additional path or name to exclude (repeatable)."
    )
    update_parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")


def _dispatch(args: argparse.Namespace) -> DocFrameReport:
    """Dispatches parsed CLI arguments to the selected core service command."""
    if args.command == "docframe" and args.docframe_command == "update":
        excludes = tuple(args.excludes) if args.excludes else None
        return DocFrame.update(target=args.target, excludes=excludes)
    raise ValueError(f"Unsupported command: {args.command}")


def _render_output(report: DocFrameReport, fmt: str) -> str:
    """Formats a DocFrameReport as either plain text or JSON."""
    if fmt == "json":
        return json.dumps(_report_to_dict(report), indent=2)
    return _format_text_report(report)


def _report_to_dict(report: DocFrameReport) -> dict[str, Any]:
    """Serializes a DocFrameReport into a JSON-compatible dictionary."""
    return {
        "target": report.target,
        "passed": report.passed,
        "updated_files": list(report.updated_files),
        "catalog_entries": len(report.catalog.entries) if report.catalog else 0,
    }


def _format_text_report(report: DocFrameReport) -> str:
    """Renders a concise human-readable summary for a DocFrame.update() run."""
    count = len(report.updated_files)
    if count == 0:
        return "Updated 0 file(s); all frames up to date."
    files = "\n".join(f"  - {path}" for path in report.updated_files)
    return f"Updated {count} file(s):\n{files}"
