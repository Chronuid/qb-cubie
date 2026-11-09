import subprocess, sys
from pathlib import Path
from src.cubie.ebt import EBT
from src.cubie.protocols import WorldState
from src.cubie.arenas.tempfs import TempFS
from src.cubie.arenas.pyvenv import PyVenv

# ======================================================================================================================
# PROVISIONING & FIXTURES
# ======================================================================================================================

BASE_ARENA = "tests/.arenas/empty_venv"
COWSAY_ARENA = "tests/.arenas/cowsay_env"

# ======================================================================================================================
# TARGETS (The Mutators)
# ======================================================================================================================

def create_custom_log(*args, **kwargs) -> bool:
    """Generates a log file that is not ignored by default."""
    Path("custom_log.txt").write_text("log data", encoding="utf-8")
    return True

def create_critical_file(*args, **kwargs) -> bool:
    """Generates a critical functional file."""
    Path("important.txt").write_text("critical data", encoding="utf-8")
    return True

def create_deep_build_artifacts(*args, **kwargs) -> bool:
    """Generates a deep folder structure with arbitrary files."""
    build_dir = Path("build/deep/nested")
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / "artifact.bin").write_text("101010", encoding="utf-8")
    return True

def install_package(package: str) -> bool:
    """Installs a package dynamically at runtime inside the arena."""
    subprocess.run(
        ["uv", "pip", "install", package, "--python", sys.executable],
        check=True, capture_output=True
    )
    return True


# ======================================================================================================================
# 1. BASELINE (Standard Validation)
# ======================================================================================================================

def test_standard_fs_critical_red():
    """Verifies: A newly created, non-ignored file correctly fails the FS byte-diff."""
    EBT(
        target=create_critical_file,
        pre=WorldState(arena=TempFS(), fs={".": BASE_ARENA}),
        post=WorldState(
            returns=True,
            fs={".": BASE_ARENA} # Asserting against the FS explicitly
        ),
        expect=False # Test must fail because 'important.txt' is strictly evaluated
    ).run()


# ======================================================================================================================
# 2. CONFIGURATION OVERRIDES
# ======================================================================================================================

def test_custom_fs_ignores_green():
    """Verifies: Injecting a custom file into FS_IGNORES causes the engine to bypass it during diffing."""
    ebt_run = EBT(
        target=create_custom_log,
        pre=WorldState(arena=TempFS(), fs={".": BASE_ARENA}),
        post=WorldState(
            arena=TempFS(),
            returns=True,
            fs={".": BASE_ARENA} # Expecting clean base FS
        )
    )
    ebt_run.FS_IGNORES = {"custom_log.txt"} # The custom log is explicitly ignored
    ebt_run.run()

def test_empty_arena_ignores_red():
    """Verifies: Wiping ARENA_IGNORES strictly forces PyVenv to evaluate all volatile environment metadata."""
    ebt_run = EBT(
        target=install_package,
        pre=WorldState(args="cowsay==6.1", arena=PyVenv(BASE_ARENA)),
        post=WorldState(
            returns=True,
            arena=PyVenv(COWSAY_ARENA) # Asserting against the Arena explicitly
        ),
        expect=False
    )
    # Wiping convention forces crash due to volatile pip/dist-info metadata mismatches
    ebt_run.ARENA_IGNORES = set()
    ebt_run.run()


# ======================================================================================================================
# 3. TOPOLOGICAL RECURSION
# ======================================================================================================================

def test_fs_ignore_deep_directory_green():
    """Verifies: Adding a top-level directory to FS_IGNORES cascades down to all deeply nested artifacts."""
    ebt_run = EBT(
        target=create_deep_build_artifacts,
        pre=WorldState(arena=TempFS(), fs={".": BASE_ARENA}),
        post=WorldState(
            returns=True,
            fs={".": BASE_ARENA}
        )
    )
    ebt_run.FS_IGNORES = {"build"}
    ebt_run.run()


# ======================================================================================================================
# 4. QUANTIFIER INTERACTION
# ======================================================================================================================

def test_fs_ignores_with_forall_green():
    """Verifies: The logical AND (∀) holds true even if each iteration produces individually ignored side-effects."""
    ebt_run = EBT(
        target=create_custom_log,
        pre=[
            WorldState(args=(1,), arena=TempFS(), fs={".": BASE_ARENA}),
            WorldState(args=(2,), arena=TempFS(), fs={".": BASE_ARENA}),
            WorldState(args=(3,), arena=TempFS(), fs={".": BASE_ARENA})
        ],
        post=WorldState(
            returns=True,
            fs={".": BASE_ARENA}
        )
    )
    ebt_run.FS_IGNORES = {"custom_log.txt"}
    ebt_run.run()


# ======================================================================================================================
# 5. INVERTED EXPECTATION (expect=False)
# ======================================================================================================================

def test_fs_ignores_with_expect_false_red():
    """Verifies: Ignored files do not bypass the assertion engine if a negative expectation is strictly declared."""
    ebt_run = EBT(
        target=create_custom_log,
        pre=WorldState(arena=TempFS()),
        post=WorldState(
            returns=True,
            fs={".": BASE_ARENA}
        ),
        expect=False
    )
    ebt_run.FS_IGNORES = {"custom_log.txt"}
    ebt_run.run()
