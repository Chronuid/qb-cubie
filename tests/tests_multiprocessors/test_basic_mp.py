import pytest, os
from src.cubie.ebt import *
from src.cubie.arenas.tempfs import *
from typing import Iterable
from src.cubie.protocols import Mapper
from src.cubie.arenas.tempfs import TempFS
from src.cubie.arenas.pyvenv import PyVenv

########################################################################################################################
# ==========  ARENAS:  PyVenv("tests/arenas/empty_venv")  |  TempFS()  =================================================

test_arena=PyVenv("tests/arenas/test_venv")


# ========== TARGETS ===================================================================================================

def target_normalize(text: str) -> str:
    return text.strip().lower()

def target_state_mutator(val: int) -> int:
    global_mutator_state.append(val)
    return val

global_mutator_state = []

def target_mutate_fs(filename: str, content: str) -> str:
    """A target that performs physical I/O operations."""
    with open(filename, "w") as f: f.write(content)
    return filename

def target_execute_in_venv(code: str) -> int:
    """Simulates a subprocess call (Python in a venv)."""
    return os.system(f'python3 -c "{code}"')

# =========== MOCKS ====================================================================================================

class DummyMapper:
    def __enter__(self) -> 'DummyMapper':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def map(self, fn: Callable, *iterables: Iterable, chunksize: int = 1) -> Iterable[Any]:
        raise NotImplementedError("DummyMapper was successfully triggered!")

class MockProcessor:
    priority = 999

    @staticmethod
    def check_condition(pre_states: list, post_states: list) -> bool:
        return True

    def create_handler(self, n_tasks: int) -> Mapper:
        return DummyMapper()  # We return our dummy mapper directly


########################################################################################################################
# =========== TESTS ====================================================================================================


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


# =========== SÄULE 1: DI & INTERFACE ==================================================================================


def test_ebt_standard_multiprocessing_works_implicitly():
    """Tests the implicit functionality of the native pickler (fallback)."""
    engine = EBT(
        target=target_normalize,
        pre=[WorldState(args=(" A ",)), WorldState(args=(" B ",))],
        post=[WorldState(returns=str)],  # Typprüfung ist standardmäßig pickelbar
        multiprocessing=True
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True
    assert len(run_trace.traces) == 2


# =========== SÄULE 2: CLOUDPICKLE / LOKY SUPPORT ======================================================================

def test_ebt_multiprocessing_with_lambda_predicate():
    """Demonstrates that lambdas are serialized and executed thanks to Loky-Switch."""
    engine = EBT(
        target=target_normalize,
        pre=[WorldState(args=(" CUBIE ",))],
        # Ein Lambda führt bei nativem multiprocessing.Pool sofort zum AttributeError
        post=[WorldState(returns=lambda x: x == "cubie")],
        multiprocessing=True
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True


def test_ebt_multiprocessing_with_local_closure():
    """Demonstrates that local functions with closure state (scope) are serialized."""
    expected_value = "dynamic_value"

    def local_predicate(actual: str) -> bool:
        """A local function (closure) that accesses 'expected_value'."""
        return actual == expected_value

    engine = EBT(
        target=target_normalize,
        pre=[WorldState(args=(" DYNAMIC_VALUE ",))],
        post=[WorldState(returns=local_predicate)],
        multiprocessing=True
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True



# =========== SÄULE 3: EDGE CASES & ARENA ISOLATION ====================================================================

def test_ebt_multiprocessing_with_tempfs():
    engine = EBT(
        target=target_mutate_fs,
        arena=TempFS(),
        pre=[
            WorldState(args=("file_1.txt", "content_a")),
            WorldState(args=("file_2.txt", "content_b"))
        ],
        post=[
            WorldState(fs={"file_1.txt": lambda p: p.exists()}),
            WorldState(fs={"file_2.txt": lambda p: p.exists()})
        ],
        multiprocessing=True
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True


def test_ebt_multiprocessing_with_pyvenv():
    """Checks whether subprocesses (fork/spawn conflicts) survive within the workers."""
    engine = EBT(
        target=target_execute_in_venv,
        arena=PyVenv(),
        pre=[
            WorldState(args=("print('Worker 1')",)),
            WorldState(args=("print('Worker 2')",))
        ],
        post=WorldState(returns=0),  # os.system success code
        multiprocessing=True
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True