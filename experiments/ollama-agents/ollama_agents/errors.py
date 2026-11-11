"""Distinguish adapter execution failures from domain decisions."""


class AdapterError(ValueError):
    """Carry a protocol status and optional evidence for a failed adapter operation."""

    def __init__(self, status, message, *, raw=None, usage=None):
        super().__init__(message)
        self.status = status
        self.raw = raw
        self.usage = usage


def invalid(message):
    """Create a classified output or permission failure."""
    return AdapterError("invalid_output", message)


def infrastructure(message):
    """Create a classified configuration or I/O failure."""
    return AdapterError("infrastructure_error", message)
