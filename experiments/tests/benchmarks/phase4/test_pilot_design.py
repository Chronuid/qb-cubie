"""Plan a single-agent pilot and an optional paired comparison before spending budgets."""

from collections import Counter, defaultdict

import pytest

from ..contracts import accepted, rejected


def design(public_api, tmp_path, profile="agent-evaluation", repetitions=5, seed=17):
    suite = tmp_path / "pilot" / "sets/pilot.toml"
    accepted(public_api("init_smoke_suite"), suite, expected=lambda value: value["suite"] == str(suite.resolve()))
    text = suite.read_text(encoding="utf-8")
    text = text.replace('profile = "agent-evaluation"', f'profile = "{profile}"')
    text = text.replace("repetitions = 1", f"repetitions = {repetitions}\nseed = {seed}")
    text = text.replace("max_runs = 3", "max_runs = 100").replace("max_total_wall_time_seconds = 60",
                                                                              "max_total_wall_time_seconds = 2000")
    suite.write_text(text, encoding="utf-8")
    return suite


@pytest.mark.parametrize("repetitions", [2, 5], ids=["calibration", "pilot"])
@pytest.mark.parametrize("profile,conditions", [("agent-evaluation", {"cubie"}), ("cubie-vs-pytest", {"cubie", "pytest"})])
def test_pilot_supports_one_agent_and_optional_paired_conditions(tmp_path, public_api, repetitions, profile, conditions):
    suite = design(public_api, tmp_path, profile, repetitions)
    plan = accepted(public_api("plan_suite"), suite, expected=lambda value: len(value["runs"]) == 3 * repetitions * len(conditions))
    assert {run["agent_id"] for run in plan["runs"]} == {"fake"}
    assert {run["condition"] for run in plan["runs"]} == conditions
    cells = Counter((run["scenario_id"], run["repetition"], run["condition"]) for run in plan["runs"])
    assert len(cells) == len(plan["runs"]) and set(cells.values()) == {1}
    assert {run["repetition"] for run in plan["runs"]} == set(range(1, repetitions + 1))
    # Planning must not execute this agent or create result artifacts.
    assert not (suite.parent.parent / "results").exists()


def test_seed_and_actual_order_are_reproducible_in_the_resolved_plan(tmp_path, public_api):
    suite = design(public_api, tmp_path)
    first = accepted(public_api("plan_suite"), suite, expected=lambda value: len(value["runs"]) == 15)
    second = accepted(public_api("plan_suite"), suite, expected=lambda value: value == first)
    assert first["seed"] == second["seed"] == 17
    assert first["runs"] == second["runs"]


def test_paired_pilot_balances_which_condition_runs_first(tmp_path, public_api):
    suite = design(public_api, tmp_path, "cubie-vs-pytest", repetitions=5)
    plan = accepted(public_api("plan_suite"), suite, expected=lambda value: len(value["runs"]) == 30)
    orders = defaultdict(list)
    for run in plan["runs"]:
        orders[run["scenario_id"], run["repetition"]].append(run["condition"])
    for identifier in {run["scenario_id"] for run in plan["runs"]}:
        first = Counter(order[0] for (scenario, _), order in orders.items() if scenario == identifier)
        assert set(first) == {"cubie", "pytest"} and abs(first["cubie"] - first["pytest"]) <= 1


def test_repeated_pilot_never_silently_truncates_to_a_smoke_budget(tmp_path, public_api):
    suite = design(public_api, tmp_path)
    suite.write_text(suite.read_text(encoding="utf-8").replace("max_runs = 100", "max_runs = 3"), encoding="utf-8")
    rejected(public_api("plan_suite"), suite, match="max_runs|limit|15")
    assert not (suite.parent.parent / "results").exists()
