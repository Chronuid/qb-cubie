"""Deterministically balance conditions while preserving scenario prerequisites."""

import hashlib


def trials(scenarios, conditions, suite, repetition):
    """Yield a legacy order or a seeded, balanced sequence of paired tasks."""
    seed = suite.get("seed")
    if seed is None:
        return [(scenario, condition) for condition in conditions for scenario in scenarios]
    ordered = _scenarios(scenarios, seed, repetition)
    return [(scenario, condition) for scenario in ordered
            for condition in _conditions(conditions, seed, repetition, scenario)]


def _conditions(conditions, seed, repetition, scenario):
    """Alternate the first condition for each scenario across repetitions."""
    offset = int(_rank(seed, 0, scenario), 16) % 2
    return conditions if (repetition + offset) % 2 else list(reversed(conditions))


def _rank(seed, repetition, scenario):
    """Assign a stable random rank to an entire project group."""
    identity = f"{seed}:{repetition}:{scenario['package']['namespace']}:{scenario['group_id']}"
    return hashlib.sha256(identity.encode()).hexdigest()


def _scenarios(scenarios, seed, repetition):
    """Shuffle ready projects without executing a dependent episode too early."""
    pending = {scenario["qualified_id"]: scenario for scenario in scenarios}
    indices = {scenario["qualified_id"]: index for index, scenario in enumerate(scenarios)}
    ordered = []
    while pending:
        ready = [case for case in pending.values() if not (set(case["requires"]) & pending.keys())]
        chosen = min(ready, key=lambda case: (_rank(seed, repetition, case), indices[case["qualified_id"]]))
        ordered.append(pending.pop(chosen["qualified_id"]))
    return ordered
