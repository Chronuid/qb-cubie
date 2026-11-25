"""Domain-neutral service report model and uniform text/JSON formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from ..protocols import DiagnosticProtocol, ServiceReportProtocol
from .guards import validate_non_empty_str

SERVICE_REPORT_SCHEMA_VERSION: Final[int] = 1


@dataclass(frozen=True)
class ServiceReport:
    """Immutable, hashable report fulfilling ServiceReportProtocol for any qb-cubie service."""

    service: str
    target: str
    passed: bool
    diagnostics: tuple[DiagnosticProtocol, ...] = ()
    changed_files: tuple[str, ...] = ()
    files_checked: int = 0
    metadata: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        validate_non_empty_str(self.service, "service")
        if type(self.passed) is not bool:
            raise TypeError(f"STATE-GUARD: passed must be a bool; received {type(self.passed).__name__}.")
        if isinstance(self.files_checked, bool) or not isinstance(self.files_checked, int):
            raise TypeError(
                f"STATE-GUARD: files_checked must be a non-negative int; received {type(self.files_checked).__name__}."
            )
        if self.files_checked < 0:
            raise ValueError(f"STATE-GUARD: files_checked must be >= 0; received {self.files_checked!r}.")


def diagnostic_context(diag: DiagnosticProtocol) -> str | None:
    """Extract an optional diagnostic context string, falling back to session_id."""
    ctx = getattr(diag, "context", None)
    if ctx is not None:
        return str(ctx)
    session_id = getattr(diag, "session_id", None)
    return str(session_id) if session_id is not None else None


def diagnostic_to_dict(diag: DiagnosticProtocol) -> dict[str, Any]:
    """Serialize any DiagnosticProtocol record into a JSON-compatible dictionary."""
    return {
        "file_path": str(diag.file_path),
        "rule_id": str(diag.rule_id),
        "line": int(diag.line),
        "message": str(diag.message),
        "severity": str(getattr(diag, "severity", "error")),
        "context": diagnostic_context(diag),
    }


def format_diagnostic_line(diag: DiagnosticProtocol) -> str:
    """Format a diagnostic with standard prefix and optional trailing context label."""
    base = f"[{diag.rule_id}] {diag.file_path}:{diag.line}: {diag.message}"
    ctx = diagnostic_context(diag)
    return f"{base} ({ctx})" if ctx else base


def report_to_dict(report: ServiceReportProtocol) -> dict[str, Any]:
    """Serialize any ServiceReportProtocol object into a schema_version=1 JSON dict."""
    changed = getattr(report, "changed_files", getattr(report, "updated_files", ()))
    raw_meta = getattr(report, "metadata", ())
    return {
        "schema_version": SERVICE_REPORT_SCHEMA_VERSION,
        "service": str(getattr(report, "service", type(report).__name__)),
        "target": str(report.target),
        "passed": bool(report.passed),
        "files_checked": int(getattr(report, "files_checked", 0)),
        "changed_files": [str(item) for item in changed],
        "diagnostics": [diagnostic_to_dict(diag) for diag in report.diagnostics],
        "metadata": dict(raw_meta) if raw_meta else {},
    }


def format_service_report_text(report: ServiceReportProtocol) -> str:
    """Render a concise human-readable text summary for a service report."""
    if not report.diagnostics:
        return f"OK ({report.target})"
    return "\n".join(format_diagnostic_line(diag) for diag in report.diagnostics)
