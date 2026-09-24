import pytest, hashlib
from src.cubie.ebt import *
from typing import List, Any, Callable, Iterable
from src.cubie.protocols import WorldState, Mapper
from src.cubie.arenas.tempfs import TempFS
from src.cubie.arenas.pyvenv import PyVenv
from src.cubie.multiprocessors import PickleProcessor, LokyProcessor
class MockTriggeredSignal(BaseException): pass

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

def target_mutate_fs_adapter(dummy_arg: str) -> str:
    """
    Adapter for matrix testing. Converts the single-parameter matrix call into a valid two-parameter call.
    """
    return target_mutate_fs(filename="matrix_testfile.txt", content=dummy_arg)

def target_execute_in_venv(code: str) -> int:
    """Simulates a subprocess call (Python in a venv)."""
    return os.system(f'python3 -c "{code}"')

_global_memory_state = []
def target_mutate_in_memory(val: str) -> str:
    """Mutates the RAM state. In multiprocessing scenarios, the host state must remain unchanged."""
    _global_memory_state.append(val)
    return val

def target_mutate_venv(dummy_arg: str) -> int:
    """Simulates a real venv mutation (side effect in the arena) within the virtual arena."""
    return os.system(f"echo '{dummy_arg}' > venv_mutation_marker.txt")


# ---------- FORALL-TARGETS --------------------------------------------------------------------------------------------

def target_process_batch_item(item_id: int) -> str:
    """A simple target that simulates a deterministic transformation."""
    return f"PROCESSED_ITEM_{item_id}"

def pre_state_forall_factory(scale: int) -> List[WorldState]:
    """Generates N initial states to place the universal quantifier under load."""
    return [WorldState(args=(i,)) for i in range(scale)]

def target_heavy_computation_and_io(item_id: int) -> str:
    """Combines CPU, crypto, and I/O loads to fully saturate the worker processes."""
    total = 0
    for i in range(250_000): total += (i ** 2) % 99991 # 1. CPU-Bound: Harte Mathematik-Schleife
    filename = f"heavy_mutation_{item_id}.txt" # 2. I/O-Bound: Physische Dateisystem-Mutation
    with open(filename, "w") as f: # Wir schreiben absichtlich ein paar Kilobyte Daten
        f.write(f"Resultat von Item {item_id} ist {total}\n" * 500)
    return hashlib.sha256(f"{item_id}_{total}".encode()).hexdigest() # 3. Krypto/Hashing-Last

def pre_state_heavy_factory(scale: int) -> list:
    """Generates N tasks for the heavy workload."""
    from src.cubie.ebt import WorldState
    return [WorldState(args=(i,)) for i in range(scale)]


# =========== MOCKS ====================================================================================================

class DummyMapper:
    def __enter__(self) -> 'DummyMapper': return self
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: pass
    def map(self, fn: Callable, *iterables: Iterable, chunksize: int = 1) -> Iterable[Any]:
        raise MockTriggeredSignal("DummyMapper was successfully triggered!")

class MockProcessor:
    priority = 999
    @staticmethod
    def check_condition(pre_states: list, post_states: list) -> bool: return True
    @staticmethod
    def create_handler(n_tasks: int) -> Mapper: return DummyMapper()


class ConfigurableMockProcessor:
    """
    A spy processor for black-box testing of the MultiprocessResolver.
    """
    def __init__(self, mock_id: str, priority: int, triggers: bool):
        self.mock_id = mock_id
        self.priority = priority
        self.triggers = triggers

    def check_condition(self, pre_states: list, post_states: list) -> bool:
        return self.triggers

    def create_handler(self, n_tasks: int) -> Mapper:
        class SpyMapper:
            def __init__(self, spy_id: str): self.spy_id = spy_id
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
            def map(self, fn: Callable, *iterables: Iterable, chunksize: int = 1) -> Iterable[Any]:
                raise MockTriggeredSignal(f"WINNER:{self.spy_id}")
        return SpyMapper(self.mock_id)

# ========== FACTORY-LISTS ============================================================================================

TARGETS = [
    target_state_mutator,
    target_execute_in_venv,
    target_mutate_fs_adapter,
    target_mutate_venv,
    target_mutate_in_memory,
]

ARENAS = [
    lambda: None,
    lambda: TempFS(),
    lambda: PyVenv()
]

PROCESSORS = [
    lambda: None,
    lambda: PickleProcessor(),
    lambda: LokyProcessor(),
    lambda: MockProcessor(),
]

BASE_PROCESSORS = [lambda: PickleProcessor()]

RESOLUTION_SCENARIOS = [
    (
        # Scenario A: Priority Trumps Sequence
        [
            ConfigurableMockProcessor("LOSER", priority=1, triggers=True),
            ConfigurableMockProcessor("CHAMPION", priority=99, triggers=True)
        ],
        "WINNER:CHAMPION"
    ),
    (
        # Scenario B: Highest priority is ignored if check_condition is False
        [
            ConfigurableMockProcessor("LAZY_GIANT", priority=100, triggers=False),
            ConfigurableMockProcessor("HARD_WORKER", priority=10, triggers=True)
        ],
        "WINNER:HARD_WORKER"
    ),
    (
        # Scenario C: The State Guard triggers when all priorities are set to 0 (deactivated)
        [
            ConfigurableMockProcessor("DISABLED", priority=0, triggers=True)
        ],
        "STATE-GUARD" # Erwartet den RuntimeError aus unserem Resolver
    ),
    (
        # Scenario D: The state guard triggers if no hook catches
        [
            ConfigurableMockProcessor("NO_MATCH", priority=50, triggers=False)
        ],
        "STATE-GUARD"
    )
]


########################################################################################################################
# ========== TESTS =====================================================================================================

@pytest.mark.parametrize("arena_factory", ARENAS)
@pytest.mark.parametrize("processor_factory", PROCESSORS[:3])
@pytest.mark.parametrize("target", TARGETS)
def test_multiprocess_with_types(
        arena_factory,
        processor_factory,
        target
    ):
    """
    Demonstrates the ability to handle pure type comparisons within the WorldStates.
    """
    active_arena = arena_factory()
    active_processor = processor_factory()
    if active_arena is None and target in [target_mutate_fs_adapter, target_mutate_venv]:
        pytest.skip("Skipped: Preventing host filesystem mutation during unisolated matrix tests.")
    kwargs = {"multiprocessors": [active_processor]} if active_processor else {}
    engine = EBT(
        target=target,
        arena=active_arena,
        pre=[WorldState(args=("TEST",))],
        post=[WorldState(returns=Any)],
        multiprocessing=True,
        **kwargs
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True


@pytest.mark.parametrize("scale", [10, 50, 150])
@pytest.mark.parametrize("arena_factory", ARENAS)
@pytest.mark.parametrize("processor_factory", PROCESSORS[:3])  # Standard, Pickle, Loky
def test_forall_multiprocessing_scaling(
        scale,
        arena_factory,
        processor_factory
    ):
    """
    Demonstrates formal-logical universal quantifier satisfaction (∀) under multiprocessing load.
    """
    active_arena = arena_factory()
    active_processor = processor_factory()
    kwargs = {"multiprocessors": [active_processor]} if active_processor else {}
    engine = EBT(
        target=target_process_batch_item,
        arena=active_arena,
        pre=pre_state_forall_factory(scale),
        post=[WorldState(returns=re.compile(r"^PROCESSED_ITEM_\d+$"))],
        multiprocessing=True,
        **kwargs
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True
    assert len(run_trace.traces) == scale



# Scaling: 10 (warm-up), 50 (load), 150 (stress for the chunking heuristic)
@pytest.mark.parametrize("scale", [10, 50, 150])
@pytest.mark.parametrize("arena_factory", ARENAS[1:])  # Important: Only safe arenas due to I/O!
@pytest.mark.parametrize("processor_factory", PROCESSORS[:3]) # Standard, Pickle, Loky
def test_heavy_workload_scaling(
        scale,
        arena_factory,
        processor_factory
    ):
    """
    Stress test for the CPU cores, the arena's I/O pipes, and the chunk size heuristic.
    """
    active_arena = arena_factory()
    active_processor = processor_factory()
    kwargs = {"multiprocessors": [active_processor]} if active_processor else {}
    engine = EBT(
        target=target_heavy_computation_and_io,
        arena=active_arena,
        pre=pre_state_heavy_factory(scale),
        post=[WorldState(returns=re.compile(r"^[a-f0-9]{64}$"))],
        multiprocessing=True,
        **kwargs
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True
    assert len(run_trace.traces) == scale


MUTATION_TARGETS = TARGETS[2:] # We filter our targets: FS adapter, venv mutation, in-memory mutation
@pytest.mark.parametrize("scale", [10, 50])  # Scaling for parallel mutation conflicts
@pytest.mark.parametrize("arena_factory", ARENAS[1:]) # IMPORTANT: TempFS and PyVenv only!
@pytest.mark.parametrize("processor_factory", PROCESSORS[:3])  # Standard, Pickle, Loky
@pytest.mark.parametrize("target", MUTATION_TARGETS)
def test_multiprocessing_mutations_scaling(
        scale,
        arena_factory,
        processor_factory,
        target
    ):
    """
    Demonstrates that side effects are isolated and correctly evaluated during parallel execution within the arenas.
    """
    active_arena = arena_factory()
    active_processor = processor_factory()
    kwargs = {"multiprocessors": [active_processor]} if active_processor else {}
    pre_states = [WorldState(args=(f"MUTATION_{i}",)) for i in range(scale)]
    engine = EBT(
        target=target,
        arena=active_arena,
        pre=pre_states,
        post=[WorldState(returns=Any)],
        multiprocessing=True,
        **kwargs
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True
    assert len(run_trace.traces) == scale
    if target == target_mutate_in_memory: assert len(_global_memory_state) == 0


@pytest.mark.parametrize("arena_factory", ARENAS)
@pytest.mark.parametrize("processor_factory", PROCESSORS[2:])
@pytest.mark.parametrize("target", TARGETS)
def test_custom_processor_injections(
        arena_factory,
        processor_factory,
        target
    ):
    """
    Demonstrates the functionality of the DI injection.
    """
    active_arena = arena_factory()
    active_processor = processor_factory()
    if active_arena is None and target in [target_mutate_fs_adapter, target_mutate_venv]:
        pytest.skip("Skipped: Preventing host filesystem mutation during unisolated matrix tests.")
    post_state = WorldState(returns=lambda x: True)
    engine = EBT(
        target=target,
        arena=arena_factory(),
        pre=[WorldState(args=("TEST",))],
        post=[post_state],
        multiprocessing=True
    )
    engine.MULTIPROCESSORS = [factory() for factory in BASE_PROCESSORS]
    engine.MULTIPROCESSORS.append(active_processor)
    if isinstance(active_processor, MockProcessor):
        with pytest.raises(MockTriggeredSignal, match="DummyMapper was successfully triggered!"):
            engine.run()
    else:
        run_trace = engine.run()
        assert run_trace.evaluation is True


@pytest.mark.parametrize("arena_factory", ARENAS)
@pytest.mark.parametrize("processor_factory", [PROCESSORS[0], PROCESSORS[2]])
def test_multiprocess_with_lambda_predicates(
        arena_factory,
        processor_factory
    ):
    """
    Demonstrates that dynamic predicates from loky are correctly serialized across all arenas.
    """
    active_processor = processor_factory()
    kwargs = {"multiprocessors": [active_processor]} if active_processor else {}
    engine = EBT(
        target=target_state_mutator,
        arena=arena_factory(),
        pre=[WorldState(args=("CUBIE",))],
        post=[WorldState(returns=lambda x: isinstance(x, str))],
        multiprocessing=True,
        **kwargs
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True


@pytest.mark.parametrize("arena_factory", ARENAS)
@pytest.mark.parametrize("processor_factory", [PROCESSORS[0], PROCESSORS[2]])
def test_multiprocess_with_local_closures(
        arena_factory,
        processor_factory
    ):
    """
    Demonstrates that closures are cleanly transferred to the workers across all arenas using Loky.
    """
    active_processor = processor_factory()
    kwargs = {"multiprocessors": [active_processor]} if active_processor else {}
    secret_value = "CUBIE_CLOSURE"
    def my_local_closure(actual: str) -> bool: return actual == secret_value
    engine = EBT(
        target=target_state_mutator, # Passes the input through 1:1
        arena=arena_factory(),
        pre=[WorldState(args=("CUBIE_CLOSURE",))],
        post=[WorldState(returns=my_local_closure)], # We pass our local closure as a validator
        multiprocessing=True,
        **kwargs
    )
    run_trace = engine.run()
    assert run_trace.evaluation is True


@pytest.mark.parametrize("processor_setup, expected_error_match", RESOLUTION_SCENARIOS)
def test_multiprocess_resolutions(
        processor_setup,
        expected_error_match
    ):
    """
    Demonstrates that the MultiprocessResolver correctly sorts injected processors by priority,
    skips inactive or unsuitable ones, and triggers the state guard in an emergency.
    """
    engine = EBT(
        target=target_state_mutator,
        arena=None,
        pre=[WorldState(args=("TEST",))],
        post=[WorldState(returns=Any)],
        multiprocessing=True
    )
    engine.MULTIPROCESSORS = processor_setup
    expected_exception = MockTriggeredSignal if "WINNER" in expected_error_match else RuntimeError
    with pytest.raises(expected_exception, match=expected_error_match):
        engine.run()