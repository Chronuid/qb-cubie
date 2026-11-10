"""Resolve declarative filters and explicit episode prerequisites."""

from qb_cubie.benchmarks.contracts import _validation as v

FIELDS = {"ids", "exclude_ids", "benchmarks", "splits", "types_any", "types_all",
          "types_none", "tags_any", "tags_all", "tags_none"}


def select_scenarios(scenarios, filters):
    """Return the selected scenarios once each in dependency order."""
    v.mapping(filters, "select")
    v.require(set(filters) <= FIELDS, "select", f"unknown filters: {sorted(set(filters) - FIELDS)}")
    for field, values in filters.items():
        v.strings(values, field, nonempty=True)
        _known(scenarios, field, values)
    chosen = {s["qualified_id"]: s for s in scenarios if _matches(s, filters)}
    v.require(bool(chosen), "selection", "empty selection")
    return _order(chosen)


def _known(scenarios, field, values):
    """Validate explicit selection identifiers against available scenarios."""
    if field in {"ids", "exclude_ids"}:
        available = {s["qualified_id"] for s in scenarios}
        v.require(set(values) <= available, field, f"unknown IDs: {sorted(set(values) - available)}; available: {sorted(available)}")
    elif field.endswith(("_any", "_all")):
        available = {item for scenario in scenarios for item in scenario[field.split("_")[0]]}
        v.require(bool(set(values) & available), field, f"no matches for {values}; available: {sorted(available)}")
    elif field in {"benchmarks", "splits"}:
        available = set(v.PHASES) if field == "benchmarks" else {"development", "held_out"}
        v.require(set(values) <= available, field, f"unknown values; available: {sorted(available)}")


def _matches(scenario, filters):
    """Determine whether a scenario satisfies all selection fields."""
    tests = {"ids": scenario["qualified_id"] in filters.get("ids", [scenario["qualified_id"]]),
             "exclude_ids": scenario["qualified_id"] not in filters.get("exclude_ids", []),
             "benchmarks": scenario["benchmark"] in filters.get("benchmarks", [scenario["benchmark"]]),
             "splits": scenario["split"] in filters.get("splits", [scenario["split"]])}
    return all(tests.values()) and all(_taxonomy(set(scenario[field]), filters, field) for field in ("types", "tags"))


def _taxonomy(values, filters, field):
    """Validate positive type and tag filters against available values."""
    any_values = filters.get(field + "_any")
    return ((any_values is None or bool(values & set(any_values)))
            and set(filters.get(field + "_all", [])) <= values
            and not (set(filters.get(field + "_none", [])) & values))


def _order(chosen):
    """Order selected scenarios by their declared prerequisites."""
    ordered, pending = [], dict(chosen)
    for scenario in chosen.values():
        missing = set(scenario["requires"]) - chosen.keys()
        v.require(not missing, "requires", f"{scenario['qualified_id']} missing prerequisites: {sorted(missing)}")
    while pending:
        ready = sorted(key for key, scenario in pending.items() if not (set(scenario["requires"]) & pending.keys()))
        v.require(bool(ready), "requires", f"cyclic prerequisites: {sorted(pending)}")
        for key in ready:
            ordered.append(pending.pop(key))
    return ordered
