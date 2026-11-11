"""Capture explicitly referenced local adapter files without copying unrelated secrets."""

import shutil
import sys
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.measurement._toml import write_toml


def archive_adapters(prepared, root):
    """Rewrite frozen configurations to point at bundled local adapter inputs."""
    for identifier, entry in prepared["agents"].items():
        agent = dict(entry["config"])
        if agent["command"] != ["builtin:fake"] and "container_image" not in agent:
            target = root / "inputs/adapters" / identifier
            target.mkdir(parents=True)
            agent["command"] = _command(agent["command"], entry["cwd"], target)
            _declared(agent, entry["cwd"], target)
            agent["cwd"] = "../adapters/" + identifier
        write_toml(root / "inputs/agents" / (identifier + ".toml"), agent)


def _command(command, cwd, target):
    """Bundle local command arguments and retain environment-provided executables."""
    return [Path(sys.executable).name if index == 0 and argument == sys.executable
            else _argument(argument, index, cwd, target) for index, argument in enumerate(command)]


def _argument(argument, index, cwd, target):
    """Relativize local script arguments while refusing external file dependencies."""
    path = cwd / argument
    if not path.is_file():
        return argument
    resolved = path.resolve()
    if index == 0 and not resolved.is_relative_to(cwd):
        return argument
    v.require(resolved.is_relative_to(cwd), "adapter.files", "local arguments must remain inside agent cwd")
    name = resolved.relative_to(cwd).as_posix()
    _copy(path, target / name)
    return "./" + name if index == 0 else name


def _declared(agent, cwd, target):
    """Include explicitly listed helper modules and resource directories."""
    for name in v.strings(agent.get("adapter_files", []), "adapter_files"):
        v.relative(name, "adapter_files")
        source = cwd / name
        v.require(source.resolve().is_relative_to(cwd), "adapter_files", "path escapes agent cwd")
        if source.is_dir():
            _directory(source, target / name)
        else:
            _copy(source, target / name)


def _directory(source, destination):
    """Preserve explicit resource directories and reject symlinks even when empty."""
    v.require(not source.is_symlink() and not any(path.is_symlink() for path in source.rglob("*")),
              "adapter_files", "symlinks unsupported")
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))


def _copy(source, destination):
    """Copy regular adapter inputs while rejecting symlink-dependent layouts."""
    v.require(source.is_file() and not source.is_symlink(), "adapter_files", f"expected regular file: {source}")
    v.require(not any(parent.is_symlink() for parent in source.parents), "adapter_files", "symlink directories unsupported")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
