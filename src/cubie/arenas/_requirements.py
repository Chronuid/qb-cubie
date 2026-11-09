"""Read-only checks before provisioning an arena's Python dependencies."""

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
print(json.dumps({"environment": environment, "distributions": distributions}))
"""


def _environment_python(env_path: Path) -> Path:
    """Keep the venv symlink intact so Python recognizes its pyvenv.cfg."""
    base = env_path.absolute()
    if (base / "bin").is_dir():
        return base / "bin" / "python"
    return base / "Scripts" / "python.exe"


def _requirements_satisfied(python_exe: Path, requirements: list[str]) -> bool:
    """Check installed metadata, versions, extras and transitive requirements.

    Installer arguments and direct references are delegated to uv because their
    satisfaction cannot be established from version metadata alone. No success
    is cached across calls, so changes to an existing arena are observed.
    """
    if not requirements:
        return True
    # Provisioning runs on the host. Import lazily so importing Cubie inside a
    # minimal arena does not require packaging in that arena as well.
    from packaging.requirements import InvalidRequirement, Requirement
    from packaging.specifiers import InvalidSpecifier, SpecifierSet
    from packaging.utils import canonicalize_name
    from packaging.version import InvalidVersion

    try:
        parsed = [Requirement(value) for value in requirements]
    except InvalidRequirement:
        return False

    env = os.environ.copy()
    env.pop("PYTHONHOME", None)
    env["PYTHONNOUSERSITE"] = "1"
    # Preserve application hooks, but never use host site-packages via PYTHONPATH.
    env["PYTHONPATH"] = os.pathsep.join(
        str(Path(path).absolute())
        for path in env.get("PYTHONPATH", "").split(os.pathsep)
        if path and "site-packages" not in path and "dist-packages" not in path
    )
    try:
        process = subprocess.run(
            [str(python_exe.absolute()), "-B", "-c", _INSPECT_ENVIRONMENT],
            cwd=python_exe.parent.parent, env=env,
            check=True, capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", None) or str(error)
        raise RuntimeError(
            f"Could not inspect arena requirements using {python_exe}: {detail}"
        ) from error
    try:
        snapshot = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid package metadata response from {python_exe}: {process.stdout}"
        ) from error

    environment = snapshot["environment"]
    installed = {}
    for distribution in snapshot["distributions"]:
        installed.setdefault(canonicalize_name(distribution["name"]), distribution)
    checked = set()

    def satisfied(requirement, parent_extras=("",)):
        if requirement.marker and not any(
            requirement.marker.evaluate({**environment, "extra": extra})
            for extra in parent_extras
        ):
            return True
        if requirement.url:
            return False
        distribution = installed.get(canonicalize_name(requirement.name))
        if distribution is None:
            return False
        if not requirement.specifier.contains(distribution["version"], prereleases=True):
            return False
        if not SpecifierSet(distribution["requires_python"]).contains(
            environment["python_full_version"], prereleases=True,
        ):
            return False
        extras = {canonicalize_name(extra) for extra in requirement.extras}
        if not extras <= {canonicalize_name(extra) for extra in distribution["extras"]}:
            return False
        key = (canonicalize_name(requirement.name), frozenset(extras))
        if key in checked:
            return True
        checked.add(key)
        return all(
            satisfied(Requirement(value), ("", *extras))
            for value in distribution["requires"]
        )

    try:
        return all(satisfied(requirement) for requirement in parsed)
    except (InvalidRequirement, InvalidSpecifier, InvalidVersion):
        # Let the existing installer handle unsupported or malformed metadata.
        return False
