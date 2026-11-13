"""Read-only dependency checks for arena provisioning and runtime validation."""

import json
import os
import subprocess
from pathlib import Path

# Only stdlib imports: the target environment need not contain packaging or pip.
_INSPECT_ENVIRONMENT = """
import importlib.metadata
import json
import os
import platform
import sys

version = sys.implementation.version
implementation_version = f"{version.major}.{version.minor}.{version.micro}"
if version.releaselevel != "final":
    implementation_version += version.releaselevel[0] + str(version.serial)
environment = {
    "implementation_name": sys.implementation.name,
    "implementation_version": implementation_version,
    "os_name": os.name,
    "platform_machine": platform.machine(),
    "platform_python_implementation": platform.python_implementation(),
    "platform_release": platform.release(),
    "platform_system": platform.system(),
    "platform_version": platform.version(),
    "python_full_version": platform.python_version(),
    "python_version": ".".join(platform.python_version_tuple()[:2]),
    "sys_platform": sys.platform,
}
distributions = [
    {
        "name": dist.metadata["Name"],
        "version": dist.version,
        "requires": dist.requires or [],
        "extras": dist.metadata.get_all("Provides-Extra") or [],
        "requires_python": dist.metadata.get("Requires-Python", ""),
    }
    for dist in importlib.metadata.distributions()
    if dist.metadata["Name"]
]
print(json.dumps({
    "environment": environment,
    "distributions": distributions,
    "is_venv": sys.prefix != sys.base_prefix,
}))
"""


def _environment_python(env_path: Path) -> Path:
    """Keep the venv symlink intact so Python recognizes its pyvenv.cfg."""
    base = env_path.absolute()
    if (base / "bin").is_dir():
        return base / "bin" / "python"
    return base / "Scripts" / "python.exe"


def _requirements_satisfied(python_exe: Path, requirements: list[str]) -> bool:
    """Check installed metadata, versions, extras and transitive requirements."""
    if not requirements:
        return True
    parsed = _parse_requirements(requirements)
    if parsed is None:
        return False
    return _Requirements(_inspect_environment(python_exe)).check(parsed)


def _parse_requirements(requirements: list[str]):
    # Import lazily: minimal arenas can import Cubie without packaging installed.
    from packaging.requirements import InvalidRequirement, Requirement

    try:
        return [Requirement(value) for value in requirements]
    except InvalidRequirement:
        return None


def _inspection_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    # Preserve application hooks without exposing host site-packages.
    env["PYTHONPATH"] = os.pathsep.join(
        str(Path(path).absolute())
        for path in env.get("PYTHONPATH", "").split(os.pathsep)
        if path and "site-packages" not in path and "dist-packages" not in path
    )
    return env


def _inspect_environment(python_exe: Path) -> dict:
    try:
        process = subprocess.run(
            [str(python_exe.absolute()), "-B", "-c", _INSPECT_ENVIRONMENT],
            cwd=python_exe.parent.parent, env=_inspection_env(),
            check=True, capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", None) or str(error)
        raise RuntimeError(f"Could not inspect arena requirements using {python_exe}: {detail}") from error
    return _read_snapshot(python_exe, process.stdout)


def _read_snapshot(python_exe: Path, stdout: str) -> dict:
    try:
        snapshot = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid package metadata response from {python_exe}: {stdout}") from error
    if not snapshot.get("is_venv", True):
        raise RuntimeError(
            f"Could not inspect arena requirements using {python_exe}: "
            "target is not an isolated virtual environment (missing pyvenv.cfg)."
        )
    return snapshot


class _Requirements:
    def __init__(self, snapshot: dict):
        from packaging.utils import canonicalize_name

        self.environment = snapshot["environment"]
        self.installed: dict[str, dict] = {}
        for distribution in snapshot["distributions"]:
            self.installed.setdefault(canonicalize_name(distribution["name"]), distribution)
        self.checked: set[tuple[str, frozenset[str]]] = set()

    def check(self, requirements) -> bool:
        from packaging.requirements import InvalidRequirement
        from packaging.specifiers import InvalidSpecifier
        from packaging.version import InvalidVersion

        try:
            return all(self.satisfied(requirement) for requirement in requirements)
        except (InvalidRequirement, InvalidSpecifier, InvalidVersion):
            # Delegate unsupported metadata to the explicit provisioning step.
            return False

    def satisfied(self, requirement, parent_extras=("",)) -> bool:
        from packaging.utils import canonicalize_name

        if not self._active(requirement, parent_extras):
            return True
        if requirement.url:
            return False
        distribution = self.installed.get(canonicalize_name(requirement.name))
        if distribution is None or not self._matches(requirement, distribution):
            return False
        return self._dependencies(requirement, distribution)

    def _active(self, requirement, parent_extras) -> bool:
        return not requirement.marker or any(
            requirement.marker.evaluate({**self.environment, "extra": extra})
            for extra in parent_extras
        )

    def _matches(self, requirement, distribution: dict) -> bool:
        from packaging.specifiers import SpecifierSet
        from packaging.utils import canonicalize_name

        if not requirement.specifier.contains(distribution["version"], prereleases=True):
            return False
        if not SpecifierSet(distribution["requires_python"]).contains(
            self.environment["python_full_version"], prereleases=True,
        ):
            return False
        extras = {canonicalize_name(extra) for extra in requirement.extras}
        return extras <= {canonicalize_name(extra) for extra in distribution["extras"]}

    def _dependencies(self, requirement, distribution: dict) -> bool:
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name

        extras = frozenset(canonicalize_name(extra) for extra in requirement.extras)
        key = (canonicalize_name(requirement.name), extras)
        if key in self.checked:
            return True
        self.checked.add(key)
        return all(
            self.satisfied(Requirement(value), ("", *extras))
            for value in distribution["requires"]
        )
