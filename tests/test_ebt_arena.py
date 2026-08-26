from pyvenv import *
from ebt import *


# ======================================================================================================================
# Diese Tests überprüfen, ob die Arenen vom Host (cubie) isoliert sind.
# Da Cubie das Pytest-Package installiert hat, sollten die leeren Arenen keinen Zugriff darauf haben.

def check_host_isolation():
    """Versucht ein Paket zu importieren, das nur auf dem Host existiert."""
    try:
        import pytest
        return True
    except ImportError: return False

# ----------------------------------------------------------------------------------------------------------------------

def test_arena_isolation_green():
    EBT(
        arena=PyVenv("tests/.arenas/empty_venv"),
        target=check_host_isolation,
        post=WorldState(returns=False)
    ).run()

def test_arena_isolation_red():
    EBT(
        arena=PyVenv("tests/.arenas/empty_venv"),
        target=check_host_isolation,
        post=WorldState(returns=True),
        expect=False
    ).run()

# ======================================================================================================================
# Diese Tests überprüfen, ob die Arenen voneinander isoliert sind.
# Das cowsay-Package ist nicht auf dem Host (Cubie), sondern nur in der cowsay_env-Arena installiert,
# weswegen der import in der cowsay_env-Arena funktionieren und in der empty_qa_venv_1-Arena fehlschlagen sollte.

def check_arena_isolation():
    """Versucht ein Paket zu laden, das exklusiv in der Arena lebt."""
    try:
        import cowsay
        return True
    except ImportError: return False

# ----------------------------------------------------------------------------------------------------------------------

def test_arena_import_success():
    # Der import von cowsay sollte funktionieren.
    EBT(
        arena=PyVenv("tests/.arenas/cowsay_env"),
        target=check_arena_isolation,
        post=WorldState(returns=True)
    ).run()

def test_arena_import_fail():
    # Der import von cowsay sollte fehlschlagen.
    EBT(
        arena=PyVenv("tests/.arenas/empty_venv"),
        target=check_arena_isolation,
        post=WorldState(returns=False)
    ).run()


# ======================================================================================================================

def get_virtual_env_path():
    """Gibt den Pfad der aktiven virtuellen Umgebung zurück."""
    return os.environ.get("VIRTUAL_ENV")


def verify_cloned_env_vars(original_path_str: str):
    """Prüft, ob die Umgebungsvariablen in der Sandbox korrekt auf den Klon zeigen."""
    import os
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path: return False
    if venv_path == original_path_str: return False
    if "cubie_arena_" not in venv_path: return False
    return True

# ----------------------------------------------------------------------------------------------------------------------

def test_arena_env_vars():
    arena_path = "tests/.arenas/empty_venv"
    abs_original = str(Path(arena_path).absolute())
    EBT( # 1. Pipeline führt Target im isolierten Klon aus
        arena=PyVenv(arena_path),
        target=verify_cloned_env_vars,
        pre=WorldState(args=(abs_original,)),
        post=WorldState(returns=True)
    ).run()
    # 2. Assert nach dem Test: Auf dem Host (außerhalb der Arena) darf VIRTUAL_ENV nicht modifiziert worden sein.
    assert os.environ.get("VIRTUAL_ENV") != abs_original


# ======================================================================================================================

def mutate_active_venv():
    """Erstellt eine Dummy-Datei im aktuell aktiven Environment."""
    import os
    from pathlib import Path
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path: return False
    dummy_file = Path(venv_path) / "böse_mutation.txt"
    dummy_file.write_text("Diese Datei sollte nie im Original landen!")
    return True


def check_path_isolation(original_path: str):
    """Gibt True zurück, wenn der aktive Pfad vom Original abweicht."""
    import os
    venv_path = os.environ.get("VIRTUAL_ENV")
    return venv_path != original_path and venv_path is not None

def _cleanup_mutation_file(arena_path: str) -> None:
    """Entfernt die Dummy-Datei aus dem übergebenen Arena-Pfad restlos."""
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
        assert not mutation_file.exists(), "STATE-GUARD: Der Original-Ordner wurde mutiert!"
    finally: _cleanup_mutation_file(base_arena)

def test_arena_uses_clone_path():
    base_arena = "tests/.arenas/empty_venv"
    original_abs = str(Path(base_arena).absolute())
    EBT(
        arena=PyVenv(base_arena),
        target=check_path_isolation,
        pre=WorldState(args=(original_abs,)),
        post=WorldState(returns=True) # Wir erwarten 'True', also dass die Pfade abweichen
    ).run()

def test_arena_teardown_destroys_clone():
    base_arena = "tests/.arenas/empty_venv"
    arena_instance = PyVenv(base_arena)
    EBT(
        arena=arena_instance,
        target=check_path_isolation,
        pre=WorldState(args=(str(Path(base_arena).absolute()),)),
        post=WorldState(returns=True)
    ).run()
    # Nach dem Test: Wenn die Instanz einen Klon angelegt hat, muss dieser vernichtet sein
    if hasattr(arena_instance, '_clone_path') and arena_instance._clone_path:
        assert not os.path.exists(arena_instance._clone_path), "STATE-GUARD: Klon-Ordner wurde vom Teardown nicht gelöscht!"