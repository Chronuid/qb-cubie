"""Separate target observations from failures in execution and result transport.

Only the call itself is caught. Resolution, serialization, arena lifecycle and
BaseException subclasses remain execution failures. This module uses stdlib only
so that pickle-based arenas can import it without loading optional dependencies.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class CapturedResult:
    value: Any = None
    exception: Exception | None = None


@dataclass
class CaptureTarget:
    target: Any

    def __call__(self, *args, **kwargs):
        target = self.target
        if isinstance(target, str):
            import importlib

            if ":" in target:
                module_name, qualname = target.split(":", 1)
            else:
                module_name, _, qualname = target.rpartition(".")
            target = importlib.import_module(module_name)
            for part in qualname.split("."):
                target = getattr(target, part)
        try:
            value = target(*args, **kwargs)
        except Exception as error:  # noqa: BLE001 -- an explicitly requested target observation
            return CapturedResult(exception=error)
        return CapturedResult(value=value)


class RemoteException(Exception):
    """PyVenv observation; preserve identity/MRO without importing remote code.

    This is descriptive evidence, not a reconstructed instance of a remote class.
    """

    def __init__(self, type_name: str, message: str, type_mro: list[str]):
        super().__init__(type_name, message, type_mro)
        self.type_name = type_name
        self.message = message
        self.type_mro = type_mro

    def __str__(self):
        return self.message


def qualified_name(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


def exception_details(error: Exception | None) -> dict | None:
    if error is None:
        return None
    return {"type": error.type_name if isinstance(error, RemoteException) else qualified_name(type(error)),
            "message": str(error)}
