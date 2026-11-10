"""Visible task and deterministic proposals, never adapter decisions."""

from ..conftest import ReplayTransport, client
from ..reviewer.support import hashes, response

TASK = """Implement pricing.policy.fee(amount) for integer amounts:
negative amounts raise ValueError; 0 through 99 cost 7; 100 and above cost 0.
Use EBT for input/output acceptance, pytest.raises for exceptions.
Add USAGE.md with a concrete usage example. Preserve existing files in test_design.
"""
BASE = "def fee(amount):\n    return 7\n"
GOOD = ("def fee(amount):\n    if amount < 0:\n        raise ValueError('negative amount')\n"
        "    return 0 if amount >= 100 else 7\n")
BOUNDARY_BUG = GOOD.replace(">= 100", "> 100")
TEST_PATH = "tests/test_policy.py"
CODE_PATH = "pricing/policy.py"
TESTS = '''import pytest
from qb_cubie import EBT, WorldState
from pricing.policy import fee

@pytest.mark.parametrize("amount,expected", [(0, 7), (99, 7), (100, 0), (101, 0)])
def test_threshold(amount, expected):
    trace = EBT(target=fee, pre=WorldState(args=(amount,)),
                post=WorldState(returns=expected), reporter=None).run()
    assert trace.evaluation is True

@pytest.mark.parametrize("amount", [-1, -100])
def test_negative(amount):
    with pytest.raises(ValueError):
        fee(amount)
'''
EXCEPTION_TEST = '''import pytest
from pricing.policy import fee

def test_negative():
    with pytest.raises(ValueError):
        fee(-1)
'''
FALSE_ORACLE = TESTS.replace("(100, 0)", "(100, 7)")
SUBMIT = {"action": "submit_phase"}
DOC = "from pricing.policy import fee\nfee(100)  # 0\nNegative amounts raise ValueError.\n"


def write(files):
    return {"action": "write_files", "files": files}


def request(root, phase):
    return {"schema_version": 1, "type": "request", "run_id": "developer-5-3",
            "scenario_id": "pricing/threshold", "benchmark": "developer_agent", "phase": phase,
            "task": TASK, "workspace": str(root), "criteria": ["threshold", "negative"],
            "output_format": "project_v1", "budgets": {"wall_time_seconds": 1800, "tool_calls": 100}}


def session(api, developer_api, root, tmp_path, actions, **limits):
    transport = ReplayTransport(*(response(action) if isinstance(action, dict) else action for action in actions))
    budget = api("BudgetLedger")(wall_time_seconds=1800, max_model_calls=limits.get("models", 12),
                               max_tool_calls=limits.get("tools", 40), reserve_seconds=5, clock=lambda: 100.)
    evidence = api("EvidenceWriter")(archive_root=tmp_path / "archives", workspace=root)
    adapter = developer_api(client=client(api, transport), budget=budget, evidence=evidence,
                            context_max_bytes=65536, mode="cubie")
    return adapter, transport, evidence


def design(adapter, root, tests=TESTS):
    from .checks import phase
    event = phase(adapter, root, "test_design")
    assert (root / TEST_PATH).read_text() == tests
    phase(adapter, root, "red")
    return event


__all__ = ["hashes", "response"]
