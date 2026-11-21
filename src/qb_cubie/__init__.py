"""Experimental framework for declarative acceptance tests, reviews, and static code analysis."""

# `EBT` (Example-Based Testing):
#     Runs finite examples against result patterns; successful runs are not general correctness proofs.
#
# `RBT` (Review-Based Testing):
#     Orchestrates review pipelines bridging automated targets with human or machine reviewers.
#
# `arenas` (`PyVenv`, `TempFS`):
#     Provides temporary workspaces and child processes without an OS security boundary.
#
# `linters` (`AstLinter`, `CstLinter`, `Pylint`, `MyPy`):
#     Provides static code analysis, linting, and concrete syntax tree validation tools.
#
# `protocols` & `WorldState`:
#     Defines foundational protocols, execution states, and IPC serialization codecs.

from .core import ebt, multiprocessors, protocols, rbt, reporter
from .core.arenas.tempfs import TempFS
from .core.arenas.pyvenv import PyVenv
from .core.arenas.codecs import CloudpickleCodec, MSGspecCodec, PickleCodec
from .core.protocols import WorldState, DeviceResources, UNSPECIFIED, ExceptionExpectation
from .core.reporter import JsonReporter, PytestReporter
from .core._execution import RemoteException
from .core.linter import Linter, LinterDiagnostic, AstLinter, CstRule, CstLinter
from .core.ebt import EBT
from .core.linters.mypy import MyPy
from .core.linters.pylint import Pylint

__all__ = [
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
    "ebt",
    "EBT",
    "multiprocessors",
    "protocols",
    "rbt",
    "reporter",
    "Linter",
    "LinterDiagnostic",
    "AstLinter",
    "CstRule",
    "CstLinter",
    "Pylint",
    "MyPy",
]
