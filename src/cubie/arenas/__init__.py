"""
Provides execution environments (sandboxing) for the temporary execution of targets.
===========

`PyVenv`:
    Executes targets as arena runners within virtual environments utilizing IPC codecs and phantom import hooks.

`TempFS`:
    Executes targets within the host process while encapsulating file system operations in an ephemeral workspace.

`ArenaBuilder`:
    Programmatically provisions base environments.

IPC Codecs (`MSGspecCodec`, `PickleCodec`, `CloudpickleCodec`):
    Handles inter-process  communication serialization, payload extraction, and runner script generation.

Phantom Middleware / Hooks:
    Intercepts module imports during execution to silently absorb or block specified decontamination.
"""

from . import arena_envs, codecs, phantom_hook, pyvenv, tempfs
from .codecs import MSGspecCodec, CloudpickleCodec, PickleCodec
__all__ = [
    "arena_envs",
    "codecs",
    "phantom_hook",
    "pyvenv",
    "tempfs",
    "MSGspecCodec",
    "PickleCodec",
    "CloudpickleCodec",
]