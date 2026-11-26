"""CLI command adapter for the DocEnsurance service implementing ServiceCommandProtocol."""

from __future__ import annotations

import argparse
from typing import Final

from ...service_core.cli_spec import (
    EXIT_CHECK_FAILED,
    EXIT_OK,
    CommandResult,
    add_standard_service_args,
)
from .adapters import resolve_cli_target_path
from .doc_ensurance import DocEnsurance

__all__ = ["COMMAND", "DocEnsuranceCommand"]


class DocEnsuranceCommand:
    """Lazy ServiceCommandProtocol adapter exposing 'docensurance check'."""

    name: str = "docensurance"
    help: str = "Verify documentation code examples."

    def register(self, subparser: argparse.ArgumentParser) -> None:
        """Register the 'check' subcommand on the docensurance parser."""
        de_sub = subparser.add_subparsers(dest="docensurance_command", required=True)
        check_parser = de_sub.add_parser("check", help="Verify Markdown documentation code examples.")
        add_standard_service_args(check_parser)

    def execute(self, args: argparse.Namespace) -> CommandResult:
        """Dispatch parsed docensurance CLI arguments and return an immutable CommandResult."""
        if args.docensurance_command != "check":
            raise ValueError(f"STATE-GUARD: Unsupported docensurance subcommand: {args.docensurance_command!r}.")
        target_path = resolve_cli_target_path(args.target)
        excludes = tuple(args.excludes) if args.excludes else None
        report = DocEnsurance(target=target_path, excludes=excludes, reporter=None).run()
        return CommandResult(
            exit_code=EXIT_OK if report.passed else EXIT_CHECK_FAILED,
            report=report,
        )


COMMAND: Final[DocEnsuranceCommand] = DocEnsuranceCommand()
