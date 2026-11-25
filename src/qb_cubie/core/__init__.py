"""Core package for qb-cubie: EBT, RBT, arenas, linters, service_core, services, and protocols."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

from . import arenas, ebt, linter, linters, multiprocessors, protocols, rbt, reporter, service_core
from .arenas.tempfs import TempFS
from .arenas.pyvenv import PyVenv
from .arenas.codecs import CloudpickleCodec, MSGspecCodec, PickleCodec
from .protocols import WorldState, DeviceResources, UNSPECIFIED, ExceptionExpectation
from .reporter import JsonReporter, PytestReporter
from ._execution import RemoteException
from .linter import Linter, LinterDiagnostic, AstLinter, CstRule, CstLinter
from .ebt import EBT
from .linters.mypy import MyPy
from .linters.pylint import Pylint

if TYPE_CHECKING:
    from . import services as services

__all__ = [
    "arenas",
    "ebt",
    "linter",
    "linters",
    "multiprocessors",
    "protocols",
    "rbt",
    "reporter",
    "service_core",
    "services",
    "WorldState",
    "UNSPECIFIED",
    "ExceptionExpectation",
    "JsonReporter",
    "PytestReporter",
    "RemoteException",
    "PickleCodec",
    "CloudpickleCodec",
    "MSGspecCodec",
    "TempFS",
    "PyVenv",
    "DeviceResources",
    "EBT",
    "Linter",
    "LinterDiagnostic",
    "AstLinter",
    "CstRule",
    "CstLinter",
    "Pylint",
    "MyPy",
]


def __getattr__(name: str) -> Any:
    """Lazily resolve optional service submodules without coupling core imports to services."""
    if name == "services":
        return import_module(".services", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
