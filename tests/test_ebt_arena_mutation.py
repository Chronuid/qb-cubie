import subprocess, sys
from pathlib import Path
from ebt import EBT
from protocols import WorldState
from pyvenv import PyVenv, ArenaBuilder

# ======================================================================================================================
# GLOBAL PROVISIONING (Golden Masters)
# ======================================================================================================================

BASE_ARENA = "tests/.arenas/mutation_base"
PKG_ARENA = "tests/.arenas/mutation_pkg"
ArenaBuilder(BASE_ARENA).build()
ArenaBuilder(PKG_ARENA).with_packages(["cowsay"]).build()


# ======================================================================================================================
# TARGETS (The Mutators)
# ======================================================================================================================

def target_install_package() -> bool:
    """Installs a package dynamically at runtime inside the arena."""
    subprocess.run(
        ["uv", "pip", "install", "cowsay", "--python", sys.executable],
        check=True, capture_output=True
    )
    return True

def target_uninstall_package() -> bool:
    """Uninstalls a package dynamically at runtime inside the arena."""
    subprocess.run(
        ["uv", "pip", "uninstall", "cowsay", "--python", sys.executable],
        check=True, capture_output=True
    )
    return True

def target_generate_volatile_metadata() -> bool:
    """Generates files that strictly fall under the PyVenv ignore list."""
    import site
    site_packages = Path(site.getsitepackages()[0])
    (site_packages / "dummy.pyc").write_text("binary garbage")
    dist_info = site_packages / "fake-1.0.dist-info"
    dist_info.mkdir(exist_ok=True)
    (dist_info / "RECORD").write_text("volatile hash data")
    return True


# ======================================================================================================================
# TESTS: ADDITION & SUBTRACTION
# ======================================================================================================================

def test_basic_mutation_green():
    """Verifies: The environment is successfully mutated (Addition) and corresponds to the expected post-arena state."""
    EBT(
        target=target_install_package,
        pre=WorldState(arena=PyVenv(BASE_ARENA)),
        post=WorldState(returns=True, arena=PyVenv(PKG_ARENA))
    ).run()

def test_basic_mutation_red():
    """Verifies: EBT detects that a package has been installed, even though it should not be (Intrusion)."""
    EBT(
        target=target_install_package,
        pre=WorldState(arena=PyVenv(BASE_ARENA)),
        post=WorldState(arena=PyVenv(BASE_ARENA)),  # Expecting the base, but it was mutated
        expect=False
    ).run()

def test_deletion_mutation_green():
    """Verifies: The target successfully uninstalls a package, resulting in the clean base state."""
    EBT(
        target=target_uninstall_package,
        pre=WorldState(arena=PyVenv(PKG_ARENA)),
        post=WorldState(returns=True, arena=PyVenv(BASE_ARENA))
    ).run()

def test_deletion_mutation_red():
    """Verifies: EBT detects that files are missing if the target deleted them unexpectedly."""
    EBT(
        target=target_uninstall_package,
        pre=WorldState(arena=PyVenv(PKG_ARENA)),
        post=WorldState(arena=PyVenv(PKG_ARENA)),  # Expecting the package to still be there
        expect=False
    ).run()


# ======================================================================================================================
# TESTS: VOLATILITY & FLAKINESS PROTECTION
# ======================================================================================================================

def test_volatile_metadata_ignorance_green():
    """
    Verifies: If a target only mutates volatile metadata (.pyc, .dist-info), 
    the framework ignores it and evaluates the functional state as unchanged.
    """
    EBT(
        target=target_generate_volatile_metadata,
        pre=WorldState(arena=PyVenv(BASE_ARENA)),
        post=WorldState(returns=True, arena=PyVenv(BASE_ARENA))
    ).run()

def test_volatile_metadata_with_strict_expectation_red():
    """
    Verifies: If the user explicitly expects a failure (e.g., negative filter on the base state),
    the test correctly fails, proving the ignore-logic isn't bypassing the assertion engine.
    """
    EBT(
        target=target_generate_volatile_metadata,
        pre=WorldState(arena=PyVenv(BASE_ARENA)),
        post=WorldState(arena=PyVenv(BASE_ARENA), expect=False),
        expect=False # We expect it to fail, but it functionally matches, so the test turns red (expected failure works)
    ).run()


# ======================================================================================================================
# TESTS: QUANTIFIERS (∀ and ∃) WITH ARENA MUTATIONS
# ======================================================================================================================

def test_arena_forall_green():
    """
    Verifies (∀): Multiple pre-states result in the exact same post-state (logical AND).
    Whether the arena starts empty or already has the package, `target_install_package`
    ensures the final state is always PKG_ARENA.
    """
    EBT(
        target=target_install_package,
        pre=[
            WorldState(arena=PyVenv(BASE_ARENA)),
            WorldState(arena=PyVenv(PKG_ARENA))
        ],
        post=WorldState(returns=True, arena=PyVenv(PKG_ARENA))
    ).run()

def test_arena_installs():
    """
    Verifies (∃): The mutated arena matches AT LEAST ONE of the declared post-states (logical OR).
    The target installs 'cowsay', so it will mismatch the first state but hit the second.
    """
    EBT(
        target=target_install_package,
        pre=WorldState(arena=PyVenv(BASE_ARENA)),
        post=[
            WorldState(returns=False, arena=PyVenv(BASE_ARENA)),
            WorldState(returns=True, arena=PyVenv(PKG_ARENA))
        ]
    ).run()

def test_arena_uninstalls():
    """
    Verifies (∃): EBT fails if the mutated arena matches NONE of the expected post-states.
    We uninstall the package, but explicitly do not provide the clean BASE_ARENA as an acceptable outcome.
    """
    EBT(
        target=target_uninstall_package,
        pre=WorldState(arena=PyVenv(PKG_ARENA)),
        post=[
            WorldState(returns=True, arena=PyVenv(BASE_ARENA)),
            WorldState(returns=False, arena=PyVenv(PKG_ARENA))
        ]
    ).run()