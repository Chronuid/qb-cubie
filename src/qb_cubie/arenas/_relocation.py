"""Relocate supported Python entry points and reject unsupported base-bound launchers."""

import os
import re
import shlex
from pathlib import Path


def relocate_scripts(base: Path, clone: Path) -> None:
    """Adapt copied entry points without modifying the source environment."""
    base = base.absolute()
    for directory in (clone / "bin", clone / "Scripts"):
        if directory.is_dir():
            for script in directory.iterdir():
                _relocate(script, base, clone.absolute())


def _unsupported(script: Path) -> RuntimeError:
    return RuntimeError(
        f"Unsupported console entry point cannot be relocated safely: {script.name}. "
        "Use a base without this launcher and invoke its module with the clone's Python."
    )


def _relocate(script: Path, base: Path, clone: Path) -> None:
    if re.fullmatch(r"python(?:w|\d+(?:\.\d+)*)?(?:\.exe)?", script.name, re.IGNORECASE):
        return
    if script.is_symlink():
        _relocate_link(script, base, clone)
    elif script.is_file() and script.suffix.lower() == ".exe":
        raise _unsupported(script)
    elif script.is_file():
        _relocate_text(script, base, clone)


def _relocate_link(script: Path, base: Path, clone: Path) -> None:
    target = Path(os.readlink(script))
    if not target.is_absolute():
        target = script.parent / target
    if target.is_relative_to(base):
        script.unlink()
        target = clone / target.relative_to(base)
        script.symlink_to(target)
    if not target.resolve().is_relative_to(clone.resolve()):
        raise _unsupported(script)
    if target.is_file():
        _relocate(target.resolve(), base, clone)


def _relocate_text(script: Path, base: Path, clone: Path) -> None:
    content = script.read_bytes()
    prefixes = (os.fsencode(base) + b"/", os.fsencode(base.resolve()) + b"/")
    if not any(prefix in content for prefix in prefixes):
        return
    relocated = _rewrite_script(script, content, prefixes, clone)
    if relocated is not None:
        script.write_bytes(relocated)


def _rewrite_script(script: Path, content: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes | None:
    header, _, body = content.partition(b"\n")
    if header.startswith(b"#!") and any(header[2:].startswith(prefix) for prefix in prefixes):
        return _python_header(header[2:], prefixes, clone) + body
    if content.startswith(b"#!/bin/sh\n'''exec' "):
        return _shell_header(content, prefixes, clone)
    if script.stat().st_mode & 0o111 or script.suffix.lower() in {".py", ".bat", ".cmd", ".ps1"}:
        raise _unsupported(script)
    return None  # Activation helpers are not part of the subprocess activation API.


def _python_header(command: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes:
    prefix = next(prefix for prefix in prefixes if command.startswith(prefix))
    relative, *arguments = os.fsdecode(command[len(prefix):]).split()
    executable = str(clone / relative)
    if not re.fullmatch(r"python(?:w|\d+(?:\.\d+)*)?", Path(executable).name):
        raise RuntimeError("Unsupported console shebang: only Python entry points can be relocated.")
    # A shell trampoline also supports spaces and paths beyond shebang length limits.
    command_line = shlex.join([executable, *arguments])
    return os.fsencode(f"#!/bin/sh\n'''exec' {command_line} \"$0\" \"$@\"\n' '''\n")


def _shell_header(content: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes:
    lines = content.split(b"\n", 3)
    if len(lines) != 4 or lines[2] != b"' '''":
        raise RuntimeError("Unsupported console shell trampoline cannot be relocated.")
    command = shlex.split(os.fsdecode(lines[1][len(b"'''exec' "):]))
    if command[-2:] != ["$0", "$@"] or len(command) != 3:
        raise RuntimeError("Unsupported console shell trampoline arguments cannot be relocated.")
    executable = os.fsdecode(_replace_prefixes(os.fsencode(command[0]), prefixes, clone))
    if not re.fullmatch(r"python(?:w|\d+(?:\.\d+)*)?", Path(executable).name):
        raise RuntimeError("Unsupported console shell interpreter cannot be relocated.")
    lines[1] = os.fsencode(f"'''exec' {shlex.quote(executable)} \"$0\" \"$@\"")
    return b"\n".join(lines)


def _replace_prefixes(value: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes:
    for prefix in prefixes:
        value = value.replace(prefix, os.fsencode(clone) + b"/")
    return value
