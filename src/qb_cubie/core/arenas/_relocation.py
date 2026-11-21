"""Relocate supported Python entry points and reject unsupported base-bound launchers."""

import os
import re
import shlex
from pathlib import Path

from ._relocation_win32 import relocate_windows_launcher


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
    if re.fullmatch(r"(?:python|[π𝜋]thon)w?(?:\d+(?:\.\d+)*t?)?(?:_d)?(?:\.exe)?", script.name, re.IGNORECASE):
        return
    if script.is_symlink():
        _relocate_link(script, base, clone)
    elif script.is_file() and script.suffix.lower() == ".exe":
        if not relocate_windows_launcher(script, base, clone):
            raise _unsupported(script)
    elif script.is_file():
        _relocate_text(script, base, clone)


def _relative_to_base(target: Path, base: Path) -> Path | None:
    """Return target's relative path inside base while tolerating symlinked root prefixes."""
    if target.is_relative_to(base):
        return target.relative_to(base)
    resolved_target, resolved_base = target.resolve(), base.resolve()
    if resolved_target.is_relative_to(resolved_base):
        return resolved_target.relative_to(resolved_base)
    return None


def _relocate_link(script: Path, base: Path, clone: Path) -> None:
    target = Path(os.readlink(script))
    if not target.is_absolute():
        target = script.parent / target
    if (rel := _relative_to_base(target, base)) is not None:
        script.unlink()
        target = clone / rel
        script.symlink_to(target)
    if not target.resolve().is_relative_to(clone.resolve()):
        raise _unsupported(script)
    if target.is_file():
        _relocate(target.resolve(), base, clone)


def _relocate_text(script: Path, base: Path, clone: Path) -> None:
    content = script.read_bytes()
    prefixes = tuple(
        os.fsencode(root) + sep
        for root in dict.fromkeys((base, base.resolve()))
        for sep in (b"/", b"\\")
    )
    if not any(prefix in content for prefix in prefixes):
        return
    relocated = _rewrite_script(script, content, prefixes, clone)
    if relocated is not None:
        script.write_bytes(relocated)


def _rewrite_script(script: Path, content: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes | None:
    header, _, body = content.partition(b"\n")
    header = header.rstrip(b"\r")
    if header.startswith(b"#!") and any(header[2:].startswith(prefix) for prefix in prefixes):
        return _python_header(header[2:], prefixes, clone) + body
    if content.startswith((b"#!/bin/sh\n'''exec' ", b"#!/bin/sh\r\n'''exec' ")):
        return _shell_header(content, prefixes, clone)
    if header.startswith(b"#!") or script.stat().st_mode & 0o111 or script.suffix.lower() in {".py", ".bat", ".cmd", ".ps1"}:
        raise _unsupported(script)
    return None  # Activation helpers are not part of the subprocess activation API.


def _is_python_interpreter(executable: str) -> bool:
    name = Path(executable.replace("\\", "/")).name
    return bool(re.fullmatch(r"python(?:w|\d+(?:\.\d+)*)?(?:\.exe)?", name, re.IGNORECASE))


def _python_header(command: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes:
    prefix = next(prefix for prefix in prefixes if command.startswith(prefix))
    relative, *arguments = os.fsdecode(command[len(prefix):]).split()
    executable = str(clone / relative.replace("\\", "/"))
    if not _is_python_interpreter(executable):
        raise RuntimeError("Unsupported console shebang: only Python entry points can be relocated.")
    # A shell trampoline also supports spaces and paths beyond shebang length limits.
    command_line = shlex.join([executable, *arguments])
    return os.fsencode(f"#!/bin/sh\n'''exec' {command_line} \"$0\" \"$@\"\n' '''\n")


def _shell_header(content: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes:
    lines = content.split(b"\n", 3)
    if len(lines) != 4 or lines[2].rstrip(b"\r") != b"' '''":
        raise RuntimeError("Unsupported console shell trampoline cannot be relocated.")
    line_end = b"\r" if lines[1].endswith(b"\r") else b""
    command = shlex.split(os.fsdecode(lines[1].rstrip(b"\r")[len(b"'''exec' "):]))
    if command[-2:] != ["$0", "$@"] or len(command) != 3:
        raise RuntimeError("Unsupported console shell trampoline arguments cannot be relocated.")
    executable = os.fsdecode(_replace_prefixes(os.fsencode(command[0]), prefixes, clone))
    if not _is_python_interpreter(executable):
        raise RuntimeError("Unsupported console shell interpreter cannot be relocated.")
    lines[1] = os.fsencode(f"'''exec' {shlex.quote(executable)} \"$0\" \"$@\"") + line_end
    return b"\n".join(lines)


def _replace_prefixes(value: bytes, prefixes: tuple[bytes, ...], clone: Path) -> bytes:
    for prefix in prefixes:
        value = value.replace(prefix, os.fsencode(clone) + b"/")
    return value
