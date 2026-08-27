from ebt import *
from tempfs import *

# ======================================================================================================================
# ARENEN:  PyVenv("tests/.arenas/empty_venv")  |  TempFS()

test_arena=PyVenv("tests/.arenas/empty_venv")

# ========== FS-TARGETS (Dummy-Funktionen für die Arena) ===============================================================

def target_read_file(filename: str) -> str:
    """Liest eine Datei aus dem aktuellen Workspace und gibt den Inhalt zurück."""
    from pathlib import Path
    return Path(filename).read_text(encoding="utf-8").strip()

def target_write_file(filename: str, content: str) -> bool:
    """Schreibt Inhalt in eine Datei im aktuellen Workspace."""
    from pathlib import Path
    Path(filename).write_text(content, encoding="utf-8")
    return True

def target_modify_deep_file(folder: str, filename: str) -> bool:
    """Geht in einen Ordner und verändert dort eine Datei."""
    from pathlib import Path
    target_path = Path(folder) / filename
    target_path.write_text("MODIFIZIERT", encoding="utf-8")
    return True

# ----------------------------------------------------------------------------------------------------------------------

def test_fs_hydration_and_cwd():
    """Beweist: pre.fs kopiert Dateien in den Workspace und die Arena setzt das CWD korrekt."""
    EBT(
        arena=test_arena,
        target=target_read_file,
        pre=WorldState(
            args=("test_read.txt",),
            fs={"test_read.txt": "tests/fixtures/pre.txt"}
        ),
        post=WorldState(returns="Original")
    ).run()

def test_fs_set_convention():
    """Beweist: Ein Set wird implizit korrekt aufgelöst (Basename wird zum Zielpfad)."""
    EBT(
        arena=test_arena,
        target=target_read_file,
        pre=WorldState(
            args=("pre.txt",),
            fs={"tests/fixtures/pre.txt"}
        ),
        post=WorldState(returns="Original")
    ).run()

def test_fs_post_assertion_green():
    """Beweist: Das Byte-Diffing meldet Erfolg, wenn das Target den erwarteten FS-Zustand generiert."""
    EBT(
        arena=test_arena,
        target=target_write_file,
        pre=WorldState(args=("output.txt", "Generiert")),
        post=WorldState(
            returns=True,
            fs={"output.txt": "tests/fixtures/post.txt"}
        )
    ).run()

def test_fs_post_assertion_red():
    """Beweist: Das Framework erkennt Abweichungen auf Byte-Ebene gnadenlos."""
    EBT(
        arena=test_arena,
        target=target_write_file,
        pre=WorldState(args=("output.txt", "FALSCHER INHALT!")),
        post=WorldState(fs={"output.txt": "tests/fixtures/post.txt"}),
        expect=False
    ).run()

def test_fs_deep_directory_diffing():
    """Beweist: Ganze Ordnerstrukturen werden sauber hydriert und rekursiv auf Diffs geprüft."""
    EBT(
        arena=test_arena,
        target=target_modify_deep_file,
        pre=WorldState(
            args=("workspace_tree", "sub/file.txt"),
            fs={"workspace_tree": "tests/fixtures/tree_pre"}
        ),
        post=WorldState(
            returns=True,
            fs={"workspace_tree": "tests/fixtures/tree_post"}
        )
    ).run()