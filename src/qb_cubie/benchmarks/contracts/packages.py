"""Load scenario packages without importing or executing their code."""

from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.contracts.catalogs import validate_catalog
from qb_cubie.benchmarks.contracts.references import validate_reference


def load_package(path: str | Path) -> dict:
    """Validate and normalize a local version-one scenario package."""
    root = Path(path).resolve()
    package = v.read_data(root / "package.json")
    _identity(package)
    paths = v.strings(package.get("scenarios"), "scenarios", nonempty=True)
    scenarios = [_scenario(root, name, package["namespace"]) for name in paths]
    _groups(scenarios)
    validate_catalog(root, package, scenarios)
    return {**package, "scenarios": scenarios}


def _identity(package):
    """Validate package identity, licensing and provenance."""
    v.identifier(package.get("namespace"), "namespace")
    for field in ("version", "license", "provenance"):
        v.text(package.get(field), field)


def _scenario(root, name, namespace):
    """Load and normalize one declared scenario manifest."""
    path = v.contained(root, name, "scenarios")
    scenario = v.read_data(path)
    _fields(scenario)
    scenario["qualified_id"] = f"{namespace}/{scenario['id']}"
    scenario["manifest"] = name
    scenario["types"] = v.strings(scenario.get("types", []), "types")
    scenario["tags"] = v.strings(scenario.get("tags", []), "tags")
    scenario["requires"] = v.strings(scenario.get("requires", []), "requires")
    _materials(path.parent, scenario)
    return scenario


def _fields(scenario):
    """Validate scenario identity, benchmark, criteria and budgets."""
    for field in ("id", "group_id"):
        v.identifier(scenario.get(field), field)
    v.text(scenario.get("title"), "title")
    v.choice(scenario.get("benchmark"), v.PHASES, "benchmark")
    v.choice(scenario.get("split"), {"development", "held_out"}, "split")
    v.strings(scenario.get("criteria"), "criteria", nonempty=True)
    v.budgets(scenario.get("budgets", {}))


def _materials(root, scenario):
    """Validate scenario materials and independent reference declarations."""
    v.contained(root, scenario.get("task"), "task")
    visible = v.contained(root, scenario.get("visible"), "visible", directory=True)
    _visible(visible)
    for dependency in scenario["requires"]:
        v.identifier(dependency, "requires", qualified=True)
    evaluator = v.mapping(scenario.get("evaluator"), "evaluator")
    kind = "builtin.review_reference_v1" if scenario["benchmark"] == "review_agent" else "builtin.pytest_project_v1"
    v.choice(evaluator.get("kind"), {kind}, "evaluator.kind")
    reference = v.contained(root, evaluator.get("reference"), "evaluator.reference")
    v.require(not reference.is_relative_to(visible), "evaluator.reference", "must stay outside visible material")
    validate_reference(root, scenario, v.read_data(reference))


def _visible(root):
    """Reject visible symlinks that escape their declared source tree."""
    for path in root.rglob("*"):
        v.require(path.resolve().is_relative_to(root), "visible", f"symlink escapes visible tree: {path}")


def _groups(scenarios):
    """Reject duplicate scenario IDs and groups that cross dataset splits."""
    ids = set()
    splits: dict[str, str] = {}
    for scenario in scenarios:
        identifier, group = scenario["id"], scenario["group_id"]
        v.require(identifier not in ids, "id", f"duplicate scenario ID: {identifier}")
        v.require(group not in splits or splits[group] == scenario["split"], "split", f"group {group} crosses splits")
        ids.add(identifier)
        splits[group] = scenario["split"]
