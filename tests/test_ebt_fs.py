from src.cubie.ebt import *
from src.cubie.arenas.tempfs import *

# ======================================================================================================================

test_arena=TempFS()  # ARENEN:  PyVenv("tests/arenas/empty_venv")  |  TempFS()

# ========== FS-TARGETS ================================================================================================

def target_read_file(filename: str) -> str:
    """Reads a file from the current workspace and returns the content."""
    from pathlib import Path
    return Path(filename).read_text(encoding="utf-8").strip()

def target_write_file(filename: str, content: str) -> bool:
    """Writes content to a file in the current workspace."""
    from pathlib import Path
    Path(filename).write_text(content, encoding="utf-8")
    return True

def target_modify_deep_file(folder: str, filename: str) -> bool:
    """Go into a folder and modify a file there."""
    from pathlib import Path
    target_path = Path(folder) / filename
    target_path.write_text("MODIFIZIERT", encoding="utf-8")
    return True

# ----------------------------------------------------------------------------------------------------------------------

def test_fs_hydration_and_cwd():
    """Verifies: pre.fs copies files into the workspace and the arena sets the CWD correctly."""
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
    """Verifies: A set is resolved correctly implicitly (basename becomes the target path)."""
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
    """Verifies: Byte-diffing reports success when the target generates the expected file system state."""
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
    """Verifies: The framework ruthlessly detects discrepancies at the byte level."""
    EBT(
        arena=test_arena,
        target=target_write_file,
        pre=WorldState(args=("output.txt", "FALSCHER INHALT!")),
        post=WorldState(fs={"output.txt": "tests/fixtures/post.txt"}),
        expect=False
    ).run()

def test_fs_deep_directory_diffing():
    """Verifies: Entire folder structures are cleanly hydrated and recursively checked for diffs."""
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