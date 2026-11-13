"""Use a deterministic episode clock to test limits, phase accounting and fresh sessions."""

import pytest

from ..benchmarks.contracts import accepted
from .contracts import failed


def ledger(api, clock, **changes):
    return api("BudgetLedger")(
        **{"wall_time_seconds": 30, "max_model_calls": 2, "max_tool_calls": 3,
           "reserve_seconds": 5, "clock": lambda: clock[0], **changes},
    )


def test_no_op_usage_is_zero_with_unknown_cost(api):
    budget = ledger(api, [100.0])
    accepted(budget.usage, expected={"input_tokens": 0, "output_tokens": 0, "cost": None})


def test_timeouts_use_remaining_episode_time_and_preserve_runner_reserve(api):
    clock = [100.0]
    budget = ledger(api, clock)
    accepted(budget.claim_model, expected=25.0)
    clock[0] = 109.0
    accepted(budget.claim_tool, expected=16.0)
    clock[0] = 124.5
    accepted(budget.claim_model, expected=0.5)


@pytest.mark.parametrize("claim,limit", [("claim_model", 2), ("claim_tool", 3)])
def test_internal_call_limits_include_repair_attempts_and_do_not_reset_each_call(api, claim, limit):
    budget = ledger(api, [100.0])
    for _ in range(limit):
        accepted(getattr(budget, claim), expected=25.0)
    failed(getattr(budget, claim), status="budget_exceeded", match="budget|call|limit")


def test_model_and_local_tool_counters_are_independent(api):
    budget = ledger(api, [100.0])
    for _ in range(2):
        accepted(budget.claim_model, expected=25.0)
    for _ in range(3):
        accepted(budget.claim_tool, expected=25.0)
    failed(budget.claim_model, status="budget_exceeded", match="budget|call|limit")
    failed(budget.claim_tool, status="budget_exceeded", match="budget|call|limit")


@pytest.mark.parametrize("elapsed", [25, 30, 31], ids=["reserve-boundary", "deadline", "past-deadline"])
def test_no_work_starts_at_or_after_reserved_episode_deadline(api, elapsed):
    clock = [100.0]
    budget = ledger(api, clock)
    clock[0] += elapsed
    failed(budget.claim_model, status="budget_exceeded", match="time|deadline|budget|reserve")
    failed(budget.claim_tool, status="budget_exceeded", match="time|deadline|budget|reserve")


def test_usage_sums_all_initial_and_repair_calls(api):
    budget = ledger(api, [100.0])
    budget.claim_model()
    budget.record_usage(input_tokens=13, output_tokens=7)
    budget.claim_model()
    budget.record_usage(input_tokens=5, output_tokens=3)
    accepted(budget.usage, expected={"input_tokens": 18, "output_tokens": 10, "cost": None})


@pytest.mark.parametrize("missing,expected", [
    ({"input_tokens": None, "output_tokens": 3}, {"input_tokens": None, "output_tokens": 10, "cost": None}),
    ({"input_tokens": 5, "output_tokens": None}, {"input_tokens": 18, "output_tokens": None, "cost": None}),
    ({"input_tokens": None, "output_tokens": None}, {"input_tokens": None, "output_tokens": None, "cost": None}),
], ids=["unknown-input", "unknown-output", "both-unknown"])
def test_partial_measurements_keep_each_unknown_total_null(api, missing, expected):
    budget = ledger(api, [100.0])
    budget.claim_model()
    budget.record_usage(input_tokens=13, output_tokens=7)
    budget.claim_model()
    budget.record_usage(**missing)
    accepted(budget.usage, expected=expected)


def test_phase_usage_resets_but_episode_limits_and_clock_remain(api):
    clock = [100.0]
    budget = ledger(api, clock)
    budget.claim_model()
    budget.record_usage(input_tokens=13, output_tokens=7)
    budget.begin_phase()
    accepted(budget.usage, expected={"input_tokens": 0, "output_tokens": 0, "cost": None})
    clock[0] = 110.0
    accepted(budget.claim_model, expected=15.0)
    failed(budget.claim_model, status="budget_exceeded", match="budget|call|limit")


def test_fresh_sessions_have_separate_counters_usage_and_episode_origins(api):
    clock = [100.0]
    first = ledger(api, clock)
    first.claim_model()
    first.record_usage(input_tokens=13, output_tokens=7)
    first.claim_model()
    clock[0] = 140.0
    second = ledger(api, clock)
    accepted(second.claim_model, expected=25.0)
    accepted(second.usage, expected={"input_tokens": 0, "output_tokens": 0, "cost": None})
    accepted(first.usage, expected={"input_tokens": 13, "output_tokens": 7, "cost": None})
    failed(first.claim_model, status="budget_exceeded", match="budget|time|call|limit")
