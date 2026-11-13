import os
import sys
from pathlib import Path

import pytest

# conftest.py is located in /tests, so the parent directory is your project root
PROJECT_ROOT = Path(__file__).parent.parent
TESTS_ROOT = Path(__file__).resolve().parent
# 1. Override the IDE's right-click behavior: force the CWD to the project root
os.chdir(PROJECT_ROOT)
# 2. Fix the pytest runner: make the src/ directory known for Cubie's framework modules
sys.path.insert(0, str(PROJECT_ROOT / "src"))

DIR_MARKERS: dict[str, tuple[str, ...]] = {
    "tests_ebt": ("ebt",),
    "tests_arena": ("arena",),
    "tests_multiprocessors": ("multiprocess",),
    "tests_linter": ("linter",),
    "tests_services": ("services",),
    "tests_user_workflows": ("workflows",),
}

FILE_MARKERS: dict[str, tuple[str, ...]] = {
    "test_lint.py": ("meta", "linter", "lint", "slow"),
    "test_styleguide.py": ("meta", "lint"),
    "test_default_collection_contract.py": ("meta",),
    "test_offline_core.py": ("meta",),
    "test_core_without_tk.py": ("meta",),
    "test_headless_reviewer.py": ("reviewer",),
    "test_human_reviewer_fresh_decision.py": ("reviewer",),
    "test_rbt_reporter.py": ("reviewer",),
    "test_rbt_demo.py": ("reviewer",),
    "tests_arena/test_ebt_resource_limits.py": ("slow",),
    "tests_multiprocessors/test_mp_xdist.py": ("slow",),
    "tests_multiprocessors/test_mp_hypothesis.py": ("hypothesis",),
    "tests_linter/test_mypy.py": ("slow",),
    "tests_linter/test_linter.py": ("slow",),
    "tests_linter/test_linter_ast.py": ("slow",),
    "tests_user_workflows/test_pytest_process.py": ("slow",),
    "tests_user_workflows/test_quality_gate.py": ("slow",),
}


def _configure_hypothesis_profiles() -> None:
    """Register lightweight local dev and thorough CI Hypothesis profiles."""
    try:
        from hypothesis import settings
    except ImportError:
        return
    settings.register_profile("dev", max_examples=15, deadline=None)
    settings.register_profile("ci", max_examples=100, deadline=None)
    default_profile = "ci" if os.environ.get("CI") else "dev"
    settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", default_profile))


_configure_hypothesis_profiles()


def _markers_for_item(item: pytest.Item) -> set[str]:
    """Derive default category and speed markers from a test item's relative path."""
    try:
        rel = Path(item.path).resolve().relative_to(TESTS_ROOT).as_posix()
    except ValueError:
        return set()
    markers = set(DIR_MARKERS.get(rel.split("/", 1)[0], ()))
    markers.update(FILE_MARKERS.get(rel, ()))
    return markers


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-tag tests by subsystem and speed while honoring explicit fast/slow overrides."""
    for item in items:
        existing = {marker.name for marker in item.iter_markers()}
        derived = _markers_for_item(item)
        if "fast" in existing:
            derived.discard("slow")
        for name in sorted(derived - existing):
            item.add_marker(getattr(pytest.mark, name))
            existing.add(name)
        if "slow" not in existing and "fast" not in existing:
            item.add_marker(pytest.mark.fast)


def _is_venv_dir(path: Path) -> bool:
    return (
        (path / "pyvenv.cfg").is_file()
        or (path / "bin" / "activate").is_file()
        or (path / "Scripts" / "activate").is_file()
    )


@pytest.fixture(scope="session")
def src_files():
    """Discover project sources while pruning caches and generated virtualenvs."""
    arena_envs_dir = PROJECT_ROOT / "src" / "qb_cubie" / "arenas" / "arena_envs"
    files = []
    for directory, children, names in (PROJECT_ROOT / "src").walk():
        if directory == arena_envs_dir:
            children[:] = []
        else:
            children[:] = [
                name for name in children
                if name != "__pycache__" and not _is_venv_dir(directory / name)
            ]
        files.extend(directory / name for name in names if name.endswith(".py"))
    assert files, "No Python sources found under src/."
    return tuple(sorted(files))
