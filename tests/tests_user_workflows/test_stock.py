"""A warehouse reruns acceptance checks and retains historical ledgers."""

from copy import deepcopy
from functools import partial

import pytest

from cubie import EBT, WorldState

from .targets import Stock, availability


def test_reservation_success_cannot_hide_later_shortage(check_case):
    stock = Stock()
    expected = {"remaining": [1]}
    case = EBT(target=stock.reserve, post=WorldState(returns=expected))
    first, _ = check_case(case, accepted=True)
    saved = deepcopy(first)
    second, _ = check_case(case, accepted=False)
    third, _ = check_case(case, accepted=False)

    # Domain state and recorded observations have explicit independent oracles.
    assert stock.ledger == {"remaining": [-1]}
    for result, remaining in [(first, 1), (second, 0), (third, -1)]:
        assert len(result.traces) == 1
        assert result.traces[0].outcome.returns == {"remaining": [remaining]}
    assert len({first.run_id, second.run_id, third.run_id}) == 3
    assert first == saved

    # Caller edits and a subsequent recovery must not rewrite old evidence.
    expected["remaining"].append(99)
    stock.ledger["remaining"][:] = [2]
    case.post = WorldState(returns={"remaining": [1]})
    recovered, _ = check_case(case, accepted=True)
    assert recovered.traces[0].outcome.returns == {"remaining": [1]}
    assert first == saved
    assert second.traces[0].outcome.returns == {"remaining": [0]}


@pytest.mark.parametrize("field, expected, wrong", [
    ("count", 0, 1), ("can_ship", False, True),
    ("pending", [], ["SKU-1"]), ("next_sku", "", "SKU-1"),
])
@pytest.mark.parametrize("faulty", [False, True], ids=["correct", "wrong-value"])
def test_empty_warehouse_values_are_checked_and_reported(check_case, field, expected, wrong, faulty):
    actual = availability(field, faulty)
    assert actual == (wrong if faulty else expected)
    assert type(actual) is type(expected)
    case = EBT(target=partial(availability, field, faulty), post=WorldState(returns=expected))
    result, message = check_case(case, accepted=not faulty)
    assert len(result.traces) == 1
    assert result.traces[0].outcome.returns == actual
    if faulty and message:
        assert f"Expected {expected} | Actual {wrong}" in message
