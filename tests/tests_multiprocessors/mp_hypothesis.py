import pytest
from hypothesis import given, strategies as st
from ebt import EBT
from protocols import WorldState
from multiprocessors import StateInspector


########################################################################################################################
####### =======================  HYPOTHESIS-EXPLORATION  ======================================================= #######
########## -------------------------------------------------------------------------------------------------- ##########

def safe_global_func(): pass

@st.composite
def unpicklable_callable(draw):
    def local_closure(): pass
    return draw(st.sampled_from([lambda x: x, local_closure]))

# ========== 1. Die hashbaren Blätter ==================================================================================

leaf_strategy = st.one_of(
    st.integers(),
    st.text(),
    st.none(),
    st.just(safe_global_func),
    unpicklable_callable()
)

# ========== 2. Der korrigierte Baum ===================================================================================

recursive_data = st.recursive(
    leaf_strategy,
    lambda children: st.one_of(
        st.lists(children),
        st.tuples(children),
        st.dictionaries(st.text(), children)
        # st.sets(children) wurde entfernt, um TypeError zu vermeiden!
    ),
    max_leaves=20
)

# ========== 3. Wenn wir Sets testen wollen, injizieren wir sie sicher =================================================

safe_sets = st.sets(leaf_strategy, max_size=5) # (Sets bestehen hier garantiert nur aus hashbaren leaves)
final_strategy = st.one_of(recursive_data, safe_sets) # Wir mischen die Sets mit in die finale Datenstruktur
@given(
    returns_data=final_strategy,
    fs_data=st.dictionaries(st.text(), final_strategy),
    args_data=st.tuples(final_strategy)
)
def test_state_inspector_traversal_stability(returns_data, fs_data, args_data):
    state = WorldState( # ARRANGE: Wir bauen den WorldState mit den hochkomplexen PBT-Daten
        returns=returns_data,
        fs=fs_data,
        args=args_data
    )
    try: # ACT | Dieser Aufruf darf NIEMALS crashen (kein RecursionError, kein TypeError)
        result = StateInspector.has_unpicklable_callables([state], [])
        # ASSERT (Das Prädikat / Gesetz)
        assert isinstance(result, bool) # Wenn die Daten generiert wurden, muss das Ergebnis ein Boolean sein.
    except Exception as e: # PBT-Gesetz: Die Traversierung ist exception-sicher.
        pytest.fail(f"Der Inspector ist gecrasht! Exception: {e}")


########################################################################################################################



########################################################################################################################
####### =======================  CUBIE-VALIDATION  ============================================================= #######
########## -------------------------------------------------------------------------------------------------- ##########


# ========== SCENARIOS =================================================================================================

scenario_kwargs = WorldState(kwargs={"on_success": lambda: "done"})
scenario_nested = WorldState(args=([lambda x: x],))
scenario_safe_primitives = WorldState(kwargs={"a": 1, "b": "test", "c": None}, fs={"file.txt": 123})
scenario_safe_builtins = WorldState(args=([len, str, int],))

# ========== TEST-RUNS =================================================================================================

def test_stateinspector_has_upickable_callables():
    test_ebt = EBT( # 2. Das Hoare-Tripel Setup {P}S{Q}
        target=StateInspector.has_unpicklable_callables,
        pre=[
            WorldState(args=([scenario_kwargs], [])), # P1: Teste den kwargs-Blindflug
            WorldState(args=([scenario_nested], [])) # P2: Teste das Oberflächen-Syndrom (Nested Lambda in Liste)
        ],
        post=WorldState(returns=True), # Q: Wir erwarten in BEIDEN Fällen, dass 'True' gemeldet wird.
    )
    test_ebt.run() # 3. Feuer!

def test_stateinspector_safe_callables_allow_fast_path():
    """
    Testet die Gegenprobe: Sichere Callables (Built-ins, globale Funktionen)
    und primitive Daten dürfen keinen False-Positive auslösen.
    """
    test_ebt = EBT(
        target=StateInspector.has_unpicklable_callables,
        pre=[
            WorldState(args=([scenario_safe_primitives], [])), # P3: Keine Callables, nur primitive Typen
            WorldState(args=([scenario_safe_builtins], [])), # P4: Built-in Callables sind sicher und pickelbar
        ],
        post=WorldState(returns=False) # Q: Unsere Erwartung ist, dass der Inspector meldet: "Alles sauber, Fast-Path erlaubt!"
    )
    test_ebt.run()



########################################################################################################################
####### =======================  HYPOTHESIS-GENERATED CUBIE-ORCHESTRATION  ===================================== #######
########## -------------------------------------------------------------------------------------------------- ##########


# ========== HYPOTHESIS-EXPLORATION ====================================================================================

def safe_global_func(): pass

@st.composite
def unpicklable_callable(draw):
    def local_closure(): pass
    return draw(st.sampled_from([lambda x: x, local_closure]))


@st.composite
def generated_state_with_expectation(draw):
    safe_leaves = st.one_of(st.integers(), st.text(), st.none(), st.just(safe_global_func))
    recursive_tree = st.recursive(
        safe_leaves,
        lambda children: st.one_of(
            st.lists(children),
            st.tuples(children),
            st.dictionaries(st.text(), children)
        ),
        max_leaves=20
    )
    state = WorldState(
        returns=draw(recursive_tree),
        fs=draw(st.dictionaries(st.text(), recursive_tree)),
        args=draw(st.tuples(recursive_tree)),
        kwargs=draw(st.dictionaries(st.text(), recursive_tree))
    )
    is_poisoned = draw(st.booleans())
    if is_poisoned:
        poison = draw(unpicklable_callable())
        target_field = draw(st.sampled_from(["returns", "args", "fs", "kwargs"]))
        if target_field == "returns": state.returns = poison
        elif target_field == "args": state.args = (poison,)  # Tuple
        elif target_field == "fs": state.fs = {"vergiftete_datei.py": poison}
        elif target_field == "kwargs": state.kwargs = {"vergiftetes_kwarg": poison}
    return state, is_poisoned


# ========== CUBIE-VALIDATION ==========================================================================================

@given(data_and_oracle=generated_state_with_expectation())
def test_state_inspector_metamorphic_ebt(data_and_oracle):
    state, expected_result = data_and_oracle
    test_ebt = EBT(
        target=StateInspector.has_unpicklable_callables,
        pre=WorldState(args=([state], [])),
        post=WorldState(returns=expected_result),
    )
    test_ebt.run()


########################################################################################################################
####### ===================  HYPOTHESIS-GEN | PYTEST-PARAM  | CUBIE-VALID  ==================================== ########
########## -------------------------------------------------------------------------------------------------- ##########

# ==========  HYPOTHESIS-GENERATION  |  DYNAMISCHE EXPLORATION  ========================================================

from hypothesis import given, settings, strategies as st
from protocols import WorldState


@st.composite
def scalable_fuzzing_batch(draw, max_width: int, max_depth: int):
    """
    Ein dynamischer Generator, der Breite und Tiefe als Parameter annimmt.
    Er generiert direkt eine ganze LISTE von WorldStates für die EBT-Pipe.
    """
    safe_leaves = st.one_of(st.integers(), st.text(), st.none(), st.just(safe_global_func))
    # 1. TIEFE & BREITE (Die Datenstruktur)
    recursive_tree = st.recursive(
        safe_leaves,
        lambda children: st.one_of(
            st.lists(children, max_size=max_width),  # <-- Skalierbare Breite
            st.dictionaries(st.text(), children, max_size=max_width)  # <-- Skalierbare Breite
        ),
        max_leaves=max_depth  # <-- Skalierbare Tiefe
    )
    # 2. BREITE DER TESTLISTEN (Menge der States)
    num_states = draw(st.integers(min_value=1, max_value=max_width))
    pre_states = []

    # Das globale Orakel für den gesamten Batch
    is_batch_poisoned = False
    for _ in range(num_states):
        state = WorldState(
            returns=draw(recursive_tree),
            fs=draw(st.dictionaries(st.text(), recursive_tree, max_size=max_width)),
            args=draw(st.tuples(recursive_tree)),
            kwargs=draw(st.dictionaries(st.text(), recursive_tree, max_size=max_width))
        )
        # 3. ZWANGS-INJEKTION (Das Gift)
        if draw(st.booleans()):
            is_batch_poisoned = True
            poison = draw(unpicklable_callable())
            target_field = draw(st.sampled_from(["returns", "args", "fs", "kwargs"]))
            if target_field == "returns": state.returns = poison
            elif target_field == "args": state.args = (poison,)
            elif target_field == "fs": state.fs = {"vergiftet.py": poison}
            elif target_field == "kwargs": state.kwargs = {"vergiftetes_kwarg": poison}
        pre_states.append(state)
    return pre_states, is_batch_poisoned


# ==========  PYTEST-PARAMETRISIERUNG  |   KARTESISCHE-PRODUKTE  =======================================================

settings.register_profile("smoke", max_examples=100)
settings.register_profile("deep", max_examples=1000)
settings.register_profile("stress", max_examples=5000, deadline=None)
settings.load_profile("smoke")
@pytest.mark.parametrize("width, depth", [
        (2, 5),      # Stufe 1: Flacher Baum
        (10, 20),    # Stufe 2: Tiefer Wald
        (50, 100),   # Stufe 3: Schwarzwald
    ]
)
@given(data=st.data())
def test_state_inspector_scalable_matrix(width, depth, data):
    pre_states_list, expected_result = data.draw(scalable_fuzzing_batch(max_width=width, max_depth=depth))


# ==========  CUBIE-VALIDIERUNG  |  DYNAMISCH-EXPLORATIVE KARTESISCHE-PRODUKT VERFIIKATIONEN  ===========================

    test_ebt = EBT(
        target=StateInspector.has_unpicklable_callables,
        pre=WorldState(args=(pre_states_list, [])),
        post=WorldState(returns=expected_result),
        multiprocessing=True
    )
    test_ebt.run()