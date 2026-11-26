"""Declarative lazy CLI command protocol, standard flag builders, and result rendering."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib
import json
from typing import Any, Final, Protocol, runtime_checkable

from ..protocols import ServiceReportProtocol
from .guards import validate_choice, validate_non_empty_str
from .reporting import format_service_report_text, report_to_dict

EXIT_OK: Final[int] = 0
EXIT_CHECK_FAILED: Final[int] = 1
EXIT_ERROR: Final[int] = 2
VALID_OUTPUT_FORMATS: Final[tuple[str, ...]] = ("text", "json")

__all__ = [
    "EXIT_CHECK_FAILED",
    "EXIT_ERROR",
    "EXIT_OK",
    "VALID_OUTPUT_FORMATS",
    "CommandResult",
    "CommandSpec",
    "ServiceCommandProtocol",
    "add_exclude_arg",
    "add_format_arg",
    "add_standard_service_args",
    "add_target_arg",
    "load_command",
    "render_command_result",
]


@dataclass(frozen=True)
class CommandResult:
    """Immutable, hashable result returned by a ServiceCommandProtocol.execute() call."""

    exit_code: int
    report: ServiceReportProtocol | None = None
    text: str = ""
    extra_json: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
            raise TypeError(
                f"STATE-GUARD: exit_code must be a non-negative int; received {type(self.exit_code).__name__}."
            )
        if self.exit_code < 0:
            raise ValueError(f"STATE-GUARD: exit_code must be >= 0; received {self.exit_code!r}.")


@dataclass(frozen=True)
class CommandSpec:
    """Declarative lazy CLI subcommand entry pointing to a 'module:attribute' command loader."""

    name: str
    help: str
    loader: str

    def __post_init__(self) -> None:
        validate_non_empty_str(self.name, "name")
        validate_non_empty_str(self.help, "help")
        validate_non_empty_str(self.loader, "loader")
        mod, sep, attr = self.loader.partition(":")
        if not sep or not mod.strip() or not attr.strip() or ":" in attr:
            raise ValueError(f"STATE-GUARD: loader must use 'module:attribute' syntax; received {self.loader!r}.")


@runtime_checkable
class ServiceCommandProtocol(Protocol):
    """Contract for lazily loaded service CLI command groups."""

    @property
    def name(self) -> str: ...
    @property
    def help(self) -> str: ...
    def register(self, subparser: argparse.ArgumentParser) -> None: ...
    def execute(self, args: argparse.Namespace) -> CommandResult: ...


def load_command(spec: CommandSpec) -> ServiceCommandProtocol:
    """Lazily import and validate the ServiceCommandProtocol referenced by spec."""
    module_path, _, attr_name = spec.loader.partition(":")
    module = importlib.import_module(module_path)
    command = getattr(module, attr_name)
    if not isinstance(command, ServiceCommandProtocol):
        raise TypeError(
            f"STATE-GUARD: Loaded CLI command {spec.loader!r} does not implement ServiceCommandProtocol."
        )
    return command


def add_target_arg(
    parser: argparse.ArgumentParser,
    *,
    help_text: str = "Optional file or directory path (default: project root).",
) -> None:
    """Add the standard optional positional target argument to a subcommand parser."""
    parser.add_argument("target", nargs="?", default=None, help=help_text)


def add_exclude_arg(parser: argparse.ArgumentParser) -> None:
    """Add the standard repeatable --exclude option to a subcommand parser."""
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        dest="excludes",
        help="Additional path or name to exclude (repeatable).",
    )


def add_format_arg(parser: argparse.ArgumentParser) -> None:
    """Add the standard --format (text|json) option to a subcommand parser."""
    parser.add_argument("--format", choices=VALID_OUTPUT_FORMATS, default="text", help="Output format.")


def add_standard_service_args(parser: argparse.ArgumentParser) -> None:
    """Register the standard target, --exclude, and --format arguments on a service parser."""
    add_target_arg(parser)
    add_exclude_arg(parser)
    add_format_arg(parser)


def render_command_result(result: CommandResult, fmt: str) -> str:
    """Render a CommandResult as either plain text or schema_version=1 JSON."""
    norm_fmt = validate_choice(fmt, VALID_OUTPUT_FORMATS, "format")
    if norm_fmt == "json":
        payload: dict[str, Any] = report_to_dict(result.report) if result.report is not None else {}
        if result.extra_json:
            payload.update(dict(result.extra_json))
        return json.dumps(payload, indent=2)
    if result.text:
        return result.text
    if result.report is not None:
        return format_service_report_text(result.report)
    return ""
