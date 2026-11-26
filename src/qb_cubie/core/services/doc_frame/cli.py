"""CLI command adapter for the DocFrame service implementing ServiceCommandProtocol."""

from __future__ import annotations

import argparse
from typing import Final

from ...service_core.cli_spec import (
    EXIT_CHECK_FAILED,
    EXIT_OK,
    CommandResult,
    add_standard_service_args,
)
from .doc_frame import DocFrame
from .protocols import DocFrameReport

__all__ = ["COMMAND", "DocFrameCommand"]


def _format_update_text(report: DocFrameReport) -> str:
    """Render a concise human-readable summary for a DocFrame.update() run."""
    count = len(report.updated_files)
    if count == 0:
        return "Updated 0 file(s); all frames up to date."
    files = "\n".join(f"  - {path}" for path in report.updated_files)
    return f"Updated {count} file(s):\n{files}"


class DocFrameCommand:
    """Lazy ServiceCommandProtocol adapter exposing 'docframe update' and 'docframe check'."""

    name: str = "docframe"
    help: str = "Document frame synchronization and checks."

    def register(self, subparser: argparse.ArgumentParser) -> None:
        """Register 'update' and 'check' subcommands on the docframe parser."""
        df_sub = subparser.add_subparsers(dest="docframe_command", required=True)
        update_parser = df_sub.add_parser("update", help="Synchronize qb:frame header, router, and footer blocks.")
        add_standard_service_args(update_parser)
        check_parser = df_sub.add_parser("check", help="Verify qb:frame blocks and routes without modifying files.")
        add_standard_service_args(check_parser)

    def execute(self, args: argparse.Namespace) -> CommandResult:
        """Dispatch parsed docframe CLI arguments and return an immutable CommandResult."""
        excludes = tuple(args.excludes) if args.excludes else None
        if args.docframe_command == "update":
            return self._execute_update(args.target, excludes)
        if args.docframe_command == "check":
            return self._execute_check(args.target, excludes)
        raise ValueError(f"STATE-GUARD: Unsupported docframe subcommand: {args.docframe_command!r}.")

    @staticmethod
    def _execute_update(target: str | None, excludes: tuple[str, ...] | None) -> CommandResult:
        """Run DocFrame.update() and wrap the report with legacy-compatible JSON fields."""
        report = DocFrame.update(target=target, excludes=excludes, reporter=None)
        extra = (
            ("updated_files", list(report.updated_files)),
            ("catalog_entries", len(report.catalog.entries) if report.catalog else 0),
        )
        return CommandResult(
            exit_code=EXIT_OK if report.passed else EXIT_CHECK_FAILED,
            report=report,
            text=_format_update_text(report),
            extra_json=extra,
        )

    @staticmethod
    def _execute_check(target: str | None, excludes: tuple[str, ...] | None) -> CommandResult:
        """Run DocFrame.check() and map pass/fail to standard CLI exit codes."""
        report = DocFrame.check(target=target, excludes=excludes, reporter=None)
        return CommandResult(
            exit_code=EXIT_OK if report.passed else EXIT_CHECK_FAILED,
            report=report,
        )


COMMAND: Final[DocFrameCommand] = DocFrameCommand()
