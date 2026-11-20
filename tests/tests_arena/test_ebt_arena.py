import os
from pathlib import Path

import pytest

import qb_cubie
from qb_cubie import EBT, PyVenv, WorldState

# ======================================================================================================================
# These tests verify that the arenas are isolated from the host (cubie).
# Since Cubie has the pytest package installed, the empty arenas should not have access to it.

def check_host_isolation():
    """Attempts to import a package that exists only on the host."""
    try:
        import pytest
        return True
    except ImportError: return False

# ----------------------------------------------------------------------------------------------------------------------

def test_arena_isolation_green():
    EBT(
        arena=PyVenv(),
        target=check_host_isolation,
        post=WorldState(returns=False)
    ).run()

def test_arena_isolation_red():
    EBT(
        arena=PyVenv(),
        target=check_host_isolation,
        post=WorldState(returns=True),
        expect=False
    ).run()


def test_mp_arena_isolation_green():
    EBT(
        arena=PyVenv(),
        target=check_host_isolation,
        post=WorldState(returns=False),
        multiprocessing=True
    ).run()

def test_mp_arena_isolation_red():
    EBT(
        arena=PyVenv(),
        target=check_host_isolation,
        post=WorldState(returns=True),
        expect=False,
        multiprocessing=True
    ).run()

# ======================================================================================================================
# These tests verify whether the arenas are isolated from one another.
# The cowsay package is not installed on the host (Cubie), but only in the cowsay_env arena;
# therefore, the import should succeed in the cowsay_env arena and fail in the empty_qa_venv_1 arena.

def check_arena_isolation():
    """Attempts to load a package that resides exclusively in the arena."""
    try:
        import cowsay
        return True
    except ImportError: return False

# ----------------------------------------------------------------------------------------------------------------------

def test_arena_import_success():
    EBT(
        arena=PyVenv("tests/.arenas/cowsay_env"), # Importing cowsay should work.
        target=check_arena_isolation,
        post=WorldState(returns=True)
    ).run()

def test_arena_import_fail():
    EBT(
        arena=PyVenv(),  # The import of cowsay should fail.
        target=check_arena_isolation,
        post=WorldState(returns=False)
    ).run()


# ======================================================================================================================

def get_virtual_env_path():
    """Returns the path of the active virtual environment."""
    return os.environ.get("VIRTUAL_ENV")


def verify_cloned_env_vars(original_path_str: str):
    """Checks whether the environment variables in the sandbox correctly point to the clone."""
    import os
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path: return False
    if venv_path == original_path_str: return False
    if "cubie_arena_" not in venv_path: return False
    return True

# ======================================================================================================================
# Default-Arena

def return_true_in_default():
    return True

def get_default_virtual_env():
    import os
    return os.environ.get("VIRTUAL_ENV")

# ----------------------------------------------------------------------------------------------------------------------

def test_default_pyvenv_execution():
    """Checks whether the PyVenv arena can be successfully invoked without specifying a path."""
    EBT(
        arena=PyVenv(),  # Uses the external default base arena
        target=return_true_in_default,
        post=WorldState(returns=True)
    ).run()


def test_default_pyvenv_resolves_outside_core_package(tmp_path, monkeypatch):
    """Verifies the default PyVenv base lives outside qb_cubie and runs independently of CWD."""
    package_root = Path(qb_cubie.__file__).resolve().parent
    default_arena = PyVenv()
    assert not default_arena.env_path.resolve().is_relative_to(package_root)
    assert not (package_root / "arenas" / "arena_envs").exists()
    monkeypatch.chdir(tmp_path)
    EBT(
        arena=PyVenv(),
        target=return_true_in_default,
        post=WorldState(returns=True),
    ).run()


def test_default_pyvenv_env_override(monkeypatch):
    """Verifies QB_CUBIE_DEFAULT_ARENA redirects PyVenv() to an explicit provisioned base."""
    monkeypatch.setenv("QB_CUBIE_DEFAULT_ARENA", str(Path("tests/.arenas/cowsay_env").resolve()))
    EBT(
        arena=PyVenv(),
        target=check_arena_isolation,
        post=WorldState(returns=True),
    ).run()
    monkeypatch.setenv("QB_CUBIE_DEFAULT_ARENA", str(Path("tests/.arenas/empty_venv").resolve()))
    EBT(
        arena=PyVenv(),
        target=check_arena_isolation,
        post=WorldState(returns=True),
        expect=False,
    ).run()


def test_default_pyvenv_missing_base_fails_without_installing(tmp_path, monkeypatch):
    """Verifies unprovisioned default arenas fail via STATE-GUARD without auto-creating venvs."""
    missing = tmp_path / "unprovisioned_default_arena"
    monkeypatch.setenv("QB_CUBIE_DEFAULT_ARENA", str(missing))
    with pytest.raises(RuntimeError, match="Base arena not found"):
        EBT(
            arena=PyVenv(),
            target=return_true_in_default,
            post=WorldState(returns=True),
        ).run()
    assert not missing.exists()

def test_default_pyvenv_isolation():
    """Verifies that the default arena is correctly loaded as a cloned, isolated 'cubie_arena_' environment."""
    checks_actual_cubie_arena_or_not = lambda actual: actual is not None and "cubie_arena_" in actual
    EBT(
        arena=PyVenv(),
        target=get_default_virtual_env,
        post=WorldState(returns=checks_actual_cubie_arena_or_not)
    ).run()

def test_arena_env_vars():
    arena_path = "tests/.arenas/empty_venv"
    abs_original = str(Path(arena_path).absolute())
    EBT( # 1. Pipeline executes target in an isolated clone
        arena=PyVenv(arena_path),
        target=verify_cloned_env_vars,
        pre=WorldState(args=(abs_original,)),
        post=WorldState(returns=True)
    ).run()
    # 2. Post-test assertion: VIRTUAL_ENV must not have been modified on the host (outside the arena).
    assert os.environ.get("VIRTUAL_ENV") != abs_original


# ======================================================================================================================

def mutate_active_venv():
    """Creates a dummy file in the currently active environment."""
    import os
    from pathlib import Path
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path: return False
    dummy_file = Path(venv_path) / "böse_mutation.txt"
    dummy_file.write_text("Diese Datei sollte nie im Original landen!")
    return True

def check_path_isolation(original_path: str):
    """Returns True if the active path differs from the original."""
    import os
    venv_path = os.environ.get("VIRTUAL_ENV")
    return venv_path != original_path and venv_path is not None

def _cleanup_mutation_file(arena_path: str) -> None:
    """Completely removes the dummy file from the provided arena path."""
    from pathlib import Path
    mutation_file = Path(arena_path) / "böse_mutation.txt"
    if mutation_file.exists(): mutation_file.unlink()

# ----------------------------------------------------------------------------------------------------------------------

def test_arena_immutability():
    base_arena = "tests/.arenas/empty_venv"
    mutation_file = Path(base_arena) / "böse_mutation.txt"
    _cleanup_mutation_file(base_arena)
    try:
        EBT(
            arena=PyVenv(base_arena),
            target=mutate_active_venv,
            post=WorldState(returns=True)
        ).run()
        assert not mutation_file.exists(), "STATE-GUARD: The original folder has been altered!"
    finally: _cleanup_mutation_file(base_arena)

def test_arena_uses_clone_path():
    base_arena = "tests/.arenas/empty_venv"
    original_abs = str(Path(base_arena).absolute())
    EBT(
        arena=PyVenv(base_arena),
        target=check_path_isolation,
        pre=WorldState(args=(original_abs,)),
        post=WorldState(returns=True)
    ).run()

def test_arena_teardown_destroys_clone():
    base_arena = "tests/.arenas/empty_venv"
    arena_instance = PyVenv(base_arena)
    result = EBT(
        arena=arena_instance,
        target=get_virtual_env_path,
        post=WorldState(
            returns=lambda path: (
                path is not None
                and "cubie_arena_" in path
                and path != str(Path(base_arena).absolute())
            )
        ),
    ).run()
    clone_venv = Path(result.traces[0].outcome.returns)
    assert arena_instance.workspace_path is None
    assert arena_instance.virtual_path is None
    assert not clone_venv.exists(), "STATE-GUARD: Clone folder was not deleted by the teardown!"


# ======================================================================================================================
# --- PROOF of WORKSPACE / '.venv' SEPARATION
# ======================================================================================================================

def check_workspace_is_empty():
    """Verifies that the workspace working directory contains no arena or IPC artifacts."""
    return sorted(p.name for p in Path.cwd().iterdir()) == []

def check_no_system_folders_in_root():
    """Verifies that system folders like bin or lib do not exist directly in the workspace root."""
    root = Path.cwd()
    # Checks whether one of the system folders typical of uv is located in the bare root directory
    return any((root / folder).exists() for folder in ["bin", "Scripts", "lib", "Lib"])

def check_system_folders_in_venv():
    """Verifies that the system folders are located in the separated VIRTUAL_ENV outside CWD."""
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path:
        return False
    venv_dir = Path(venv_path)
    if not venv_dir.is_dir() or venv_dir.resolve().is_relative_to(Path.cwd().resolve()):
        return False
    has_bin = (venv_dir / "bin").is_dir() or (venv_dir / "Scripts").is_dir()
    has_lib = (venv_dir / "lib").is_dir() or (venv_dir / "Lib").is_dir()
    return has_bin and has_lib

def check_virtual_env_var_mapping():
    """Verifies that VIRTUAL_ENV points to the sibling .venv directory outside the workspace."""
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path or "cubie_arena_" not in venv_path:
        return False
    venv = Path(venv_path).resolve()
    cwd = Path.cwd().resolve()
    return venv.name == ".venv" and not venv.is_relative_to(cwd) and venv.parent == cwd.parent

# ======================================================================================================================

def test_clean_workspace_excludes_venv_folder():
    """Evidence 1: The default workspace root contains no .venv, phantom, or IPC files."""
    EBT(
        custom_id="proof_clean_venv_excluded",
        arena=PyVenv(),
        target=check_workspace_is_empty,
        post=WorldState(returns=True)
    ).run()

def test_bugreport_workspace_excludes_venv_folder():
    """Evidence 2: The linter workspace root contains no .venv, phantom, or IPC files."""
    EBT(
        custom_id="proof_bugreport_venv_excluded",
        arena=PyVenv("tests/.arenas/linter_env"),
        target=check_workspace_is_empty,
        post=WorldState(returns=True)
    ).run()

def test_workspace_root_is_clean():
    """Evidence 3: The workspace root is clean and contains NO system libraries."""
    EBT(
        custom_id="proof_root_is_clean",
        arena=PyVenv(),
        target=check_no_system_folders_in_root,
        post=WorldState(returns=False) # We expect False, as the root must be clean.
    ).run()

def test_venv_contains_system_folders():
    """Evidence 4: The system folders are physically located in the separated VIRTUAL_ENV."""
    EBT(
        custom_id="proof_venv_is_populated",
        arena=PyVenv(),
        target=check_system_folders_in_venv,
        post=WorldState(returns=True)
    ).run()

def test_virtual_env_var_is_correct():
    """Evidence 5: VIRTUAL_ENV targets the sibling .venv folder outside the workspace."""
    EBT(
        custom_id="proof_env_var_mapping",
        arena=PyVenv(),
        target=check_virtual_env_var_mapping,
        post=WorldState(returns=True)
    ).run()