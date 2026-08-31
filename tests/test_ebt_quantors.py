from ebt import EBT
from protocols import WorldState
import pytest

# ========== TARGETS (Dummy-Functions for formal logic) ================================================================

def target_normalize(text: str) -> str:
    """Standardizes a string (lowercase, no spaces)."""
    return text.strip().lower()

def target_echo(value: int) -> int:
    """Returns the exact value (simulates, for example, a discretized value range)."""
    return value

def target_math(a: int, b: int) -> int:
    """Performs a simple multiplication."""
    return a * b

# ========== ALLQUANTOR (N:1 Mapping) ==================================================================================

def test_forall_green():
    """Verifies: All pre-states result in exactly the same post-state (logical AND)."""
    EBT(
        target=target_normalize,
        pre=[
            WorldState(args=("TEXT",)),
            WorldState(args=(" text ",)),
            WorldState(args=("TeXt",))
        ],
        post=WorldState(returns="text"),
    ).run()

def test_forall_red():
    """Verifies: If even a single pre-state fails, the entire test fails."""
    EBT(
        target=target_normalize,
        pre=[
            WorldState(args=("TEXT",)),
            WorldState(args=(" text ",)),
            WorldState(args=("FEHLER",)) # This run breaks the logical AND (results in "error")
        ],
        post=WorldState(returns="text"),
        expect=False
    ).run()

# ========== EXISTENZQUANTOR (1:N Mapping) =============================================================================

def test_exists_green():
    """Verifies: The test passes if the result lies within the set of permitted post-states (logical OR)."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(3,)),
        post=[
            WorldState(returns=1),
            WorldState(returns=2),
            WorldState(returns=3), # Hit!
            WorldState(returns=4)
        ]
    ).run()

def test_exists_red():
    """Verifies: The test fails if the result is not found in any of the declared post-states."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(99,)),
        post=[
            WorldState(returns=1),
            WorldState(returns=2),
            WorldState(returns=3)
        ],
        expect=False
    ).run()

# ========== MIXED (N:M Mapping) =======================================================================================

def test_forall_exists_green():
    """Verifies: For EVERY pre-state, AT LEAST ONE post-state must apply."""
    EBT(
        target=target_math,
        pre=[ # We are testing 1x2, 2x2, 3x2. The functional results are: 2, 4, 6.
            WorldState(args=(1, 2)),
            WorldState(args=(2, 2)),
            WorldState(args=(3, 2))
        ],
        post=[ # The functional results should be: 2, 4, 6 or 8.
            WorldState(returns=2),
            WorldState(returns=4),
            WorldState(returns=6),
            WorldState(returns=8)
        ]
    ).run()

def test_forall_exists_red():
    """Verifies: If even a single pre-state does not lead to any of the permitted post-states, the test fails."""
    EBT(
        target=target_math,
        pre=[
            WorldState(args=(1, 2)),  # Returns 2 (Hit)
            WorldState(args=(5, 5)),  # Returns 25 (Failure: Not defined in any post set!)
        ],
        post=[
            WorldState(returns=2),
            WorldState(returns=4)
        ],
        expect=False
    ).run()


# ========== MIXED QUANTOR INVERTIONS  =================================================================================

def test_mixed_expect_exists_green():
    """Verifies: Output = 3 (allowed). It yields a positive match and does not violate any negative filter."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(3,)),
        post=[
            WorldState(returns=0, expect=False),
            WorldState(returns=1),
            WorldState(returns=2),
            WorldState(returns=3),
            WorldState(returns=4),
            WorldState(returns=5),
            WorldState(returns=6, expect=False)
        ]
    ).run()

def test_mixed_expect_exists_red_lower_bound():
    """Verifies: Output = 0. Although it matches a declaration, it violates the strict negative filter."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(0,)),
        post=[
            WorldState(returns=0, expect=False),
            WorldState(returns=1),
            WorldState(returns=2),
            WorldState(returns=3),
            WorldState(returns=4),
            WorldState(returns=5),
            WorldState(returns=6, expect=False)
        ],
        expect=False
    ).run()

def test_mixed_expect_exists_red_upper_bound():
    """Verifies: Output = 6. Violates the upper negative filter."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(6,)),
        post=[
            WorldState(returns=0, expect=False),
            WorldState(returns=1),
            WorldState(returns=5),
            WorldState(returns=6, expect=False)
        ],
        expect=False
    ).run()

# ========== LOCAL EXPECT (1:1 Mapping) ================================================================================

def test_single_local_expect_false_green():
    """Verifies: Local expect=False works seamlessly without lists."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(1,)),
        post=WorldState(returns=99, expect=False)
    ).run()

def test_single_local_expect_false_red():
    """Verifies: If the forbidden state occurs during the 1:1 mapping, the test fails locally."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(99,)),
        post=WorldState(returns=99, expect=False),
        expect=False # Expects failure at the EBT level
    ).run()


# ========== EXCLUSIVE NEGATIV-FILTER ==================================================================================

def test_exclusive_negative_filters_green():
    """Verifies: If only negative filters are defined, everything else is implicitly allowed (positive = empty)."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(200,)),
        post=[
            WorldState(returns=404, expect=False),
            WorldState(returns=500, expect=False)
        ]
    ).run()

def test_exclusive_negative_filters_red():
    """Verifies: If the target matches one of the purely negative filters in a list, the test fails outright."""
    EBT(
        target=target_echo,
        pre=WorldState(args=(404,)),
        post=[
            WorldState(returns=404, expect=False),
            WorldState(returns=500, expect=False)
        ],
        expect=False
    ).run()


# ========== ENUMERATION & TRACING =====================================================================================

def test_step_id_enumeration():
    """Verfiies: The step_ids for quantifier lists are neatly enumerated by index (_0, _1, _2)."""
    ebt_instance = EBT( # We instantiate the object explicitly so that we can access the internal traces after the run.
        target=target_normalize,
        pre=[
            WorldState(args=("TEXT",)),
            WorldState(args=(" text ",)),
            WorldState(args=("TeXt",))
        ],
        post=WorldState(returns="text")
    )
    ebt_instance.run()
    traces = ebt_instance._traces
    base_id = ebt_instance._run_id

    # 1. Do we have exactly 3 traces?
    assert len(traces) == 3, "Traces were not generated for all pre-states."
    # 2. Do the IDs end cleanly with the incrementing indices?
    assert traces[0].step_id.endswith("_0"), f"Expected suffix '_0', got: {traces[0].step_id}"
    assert traces[1].step_id.endswith("_1"), f"Expected suffix '_1', got: {traces[1].step_id}"
    assert traces[2].step_id.endswith("_2"), f"Expected suffix '_2', got: {traces[2].step_id}"
    # 3. Does the concatenation of run_id and index match exactly?
    assert traces[0].step_id == f"{base_id}_0"
    assert traces[1].step_id == f"{base_id}_1"
    assert traces[2].step_id == f"{base_id}_2"

# ========== REPORT FORMATTING & ID ROUTING ============================================================================

def test_report_string_formatting():
    """Verifies: the report correctly formats step_id (physical run) and Q-states (evaluations)."""
    ebt_instance = EBT(
        target=target_echo,
        pre=WorldState(args=(6,)),
        post=[WorldState(returns=0),WorldState(returns=1)]
    )
    with pytest.raises(AssertionError) as excinfo: ebt_instance.run()
    error_msg = str(excinfo.value)
    base_id = ebt_instance._run_id
    # 1. Check whether the physical execution is correctly declared as index 0.
    assert f"for step '{base_id}_0':" in error_msg
    # 2. Check whether the list of postconditions increments cleanly as Q-states.
    assert "[Q-State 0]" in error_msg
    assert "[Q-State 1]" in error_msg


def test_step_id_failure_in_forall():
    """Verifies: If a universal quantifier terminates prematurely, the cirrect step_id is reported."""
    ebt_instance = EBT(
        target=target_normalize,
        pre=[
            WorldState(args=("TEXT",)), # Index 0: Results in "text" (Match -> Passed)
            WorldState(args=(" text ",)), # Index 1: Results in "text" (Match -> Passed)
            WorldState(args=("FEHLER",)) # Index 2: Results in "fehler" (Mismatch -> Triggers the crash!)
        ],
        post=WorldState(returns="text")
    )
    with pytest.raises(AssertionError) as excinfo: ebt_instance.run()
    error_msg = str(excinfo.value)
    base_id = ebt_instance._run_id
    # The error must explicitly occur at index 2 (the third pre-state), since the first two completed successfully.
    assert f"for step '{base_id}_2':" in error_msg