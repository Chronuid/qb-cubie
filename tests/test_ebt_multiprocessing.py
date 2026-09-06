from ebt import *
from tempfs import *
from pyvenv import PyVenv

# ======================================================================================================================
# ARENAS:  PyVenv("tests/.arenas/empty_venv")  |  TempFS()

test_arena=PyVenv("tests/.arenas/empty_venv")

# ========== TARGETS ===================================================================================================

def target_normalize(text: str) -> str:
    """Standardizes a string (lowercase, no spaces)."""
    return text.strip().lower()

# ----------------------------------------------------------------------------------------------------------------------

def test_forall_multiprocessing():
    """Verifies: All pre-states result in exactly the same post-state (logical AND)."""
    muliprocessor = EBT(
        target=target_normalize,
        pre=[
            WorldState(args=("TEXT",)),
            WorldState(args=(" text ",)),
            WorldState(args=("TeXt",))
        ],
        post=WorldState(returns="text"),
    )
    muliprocessor.MULTIPROCESSING = True
    muliprocessor.run()

def test_forall_singleprocessing():
    """Verifies: All pre-states result in exactly the same post-state (logical AND)."""
    singleprocessor = EBT(
        target=target_normalize,
        pre=[
            WorldState(args=("TEXT",)),
            WorldState(args=(" text ",)),
            WorldState(args=("TeXt",))
        ],
        post=WorldState(returns="text"),
    )
    singleprocessor.run()