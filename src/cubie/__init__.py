"""
Framework for structured quality assurance via formal program verification and static code analysis.
===========

`EBT` (Example-Based Testing):
    Orchestrates tests based on Hoare triples ({P}S{Q}), supporting quantifier mappings and sandboxed execution.

`RBT` (Review-Based Testing):
    Orchestrates review pipelines bridging automated targets with human or machine reviewers.

`arenas` (`PyVenv`, `TempFS`, `DockerArena`, `VmArena`):
    Provides sandboxing and isolated execution environments for temporary target runs.

`linters` (`AstLinter`, `CstLinter`, `Pylint`, `MyPy`):
    Provides static code analysis, linting, and concrete syntax tree validation tools.

`protocols` & `WorldState`:
    Defines foundational protocols, execution states, and IPC serialization codecs.
"""
from . import ebt, multiprocessors, protocols, rbt, reporter
from .arenas.tempfs import TempFS
from .arenas.pyvenv import PyVenv
from .arenas.vmarena import VmArena
from .arenas.codecs import CloudpickleCodec, MSGspecCodec, PickleCodec
from .arenas.dockerarena import DockerArena
from .protocols import WorldState, DeviceResources
from .linter import Linter, LinterDiagnostic, AstLinter, CstRule, CstLinter
from .ebt import EBT
from .linters.mypy import MyPy
from .linters.pylint import Pylint

__all__ = [
    "WorldState",
    "PickleCodec",
    "CloudpickleCodec",
    "MSGspecCodec",
    "TempFS",
    "PyVenv",
    "DeviceResources",
    "VmArena",
    "DockerArena",
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
    "MyPy"
]