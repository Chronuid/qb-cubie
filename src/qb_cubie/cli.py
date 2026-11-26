"""Lazy composition-root command-line interface for qb-cubie."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys
from typing import Final

from .core.service_core.cli_spec import (
    EXIT_ERROR,
    CommandSpec,
    ServiceCommandProtocol,
    load_command,
    render_command_result,
)

_COMMAND_SPECS: Final[tuple[CommandSpec, ...]] = (
    CommandSpec("docframe", "Document frame synchronization and checks.", "qb_cubie.core.services.doc_frame.cli:COMMAND"),
    CommandSpec("docensurance", "Verify documentation code examples.", "qb_cubie.core.services.doc_ensurance.cli:COMMAND"),
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the lazy qb-cubie core CLI and return its process exit code."""
    raw_argv = list(sys.argv[1:]) if argv is None else list(argv)
    selected = _select_command_spec(raw_argv)
    command = load_command(selected) if selected is not None else None
    parser = _build_parser(command)
    args = parser.parse_args(raw_argv)
    return _run_command(command, args)


def _select_command_spec(argv: Sequence[str]) -> CommandSpec | None:
    """Return the matching CommandSpec for the first positional token before any help flag."""
    spec_map = {spec.name: spec for spec in _COMMAND_SPECS}
    for token in argv:
        if token in ("-h", "--help"):
            return None
        if not token.startswith("-"):
            return spec_map.get(token)
    return None


def _build_parser(active_command: ServiceCommandProtocol | None) -> argparse.ArgumentParser:
    """Build the top-level parser and register full arguments only for the selected command."""
    parser = argparse.ArgumentParser(prog="qb-cubie", description="qb-cubie command-line interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for spec in _COMMAND_SPECS:
        sub = subparsers.add_parser(spec.name, help=spec.help)
        if active_command is not None and spec.name == active_command.name:
            active_command.register(sub)
    return parser


def _run_command(command: ServiceCommandProtocol | None, args: argparse.Namespace) -> int:
    """Execute the lazily loaded service command and format its output or error."""
    if command is None:
        print(f"Error: Unsupported command: {args.command}", file=sys.stderr)
        return EXIT_ERROR
    try:
        result = command.execute(args)
        fmt = str(getattr(args, "format", "text"))
        print(render_command_result(result, fmt))
        return result.exit_code
    except (ValueError, TypeError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
