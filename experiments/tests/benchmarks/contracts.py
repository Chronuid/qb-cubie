"""Shared EBT assertions and fixture editing, with no benchmark implementation."""

import json

from qb_cubie import EBT, ExceptionExpectation, WorldState


def accepted(target, *args, expected):
    result = EBT(target=target, pre=WorldState(args=args),
                 post=WorldState(returns=expected), reporter=None).run()
    assert result.evaluation is True
    assert len(result.traces) == 1
    assert result.traces[0].evaluation is True
    return result.traces[0].outcome.returns


def rejected(target, *args, match):
    result = EBT(target=target, pre=WorldState(args=args), post=WorldState(
        raises=ExceptionExpectation(ValueError, match=match)), reporter=None).run()
    assert result.evaluation is True
    assert len(result.traces) == 1
    assert result.traces[0].evaluation is True


def edit_json(path, change):
    payload = json.loads(path.read_text(encoding="utf-8"))
    change(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")


def scenario(package, name="review-paid-correct"):
    return package / "scenarios" / name / "scenario.json"
