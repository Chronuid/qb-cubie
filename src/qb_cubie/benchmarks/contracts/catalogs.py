"""Validate optional provenance catalogs for public scenario datasets."""

from qb_cubie.benchmarks.contracts import _validation as v


def validate_catalog(root, package, scenarios):
    """Require complete provenance coverage without importing scenario code."""
    if "dataset" not in package:
        return
    catalog = v.read_data(v.contained(root, package["dataset"], "dataset"))
    status = v.choice(catalog.get("publication_status"), {"public", "held_out"}, "publication_status")
    cases = v.mapping(catalog.get("cases"), "dataset.cases")
    v.require(set(cases) == {case["id"] for case in scenarios}, "dataset.cases", "scenario coverage differs")
    groups: dict[str, str] = {}
    for scenario in scenarios:
        _case(scenario, cases[scenario["id"]], groups, status)


def _case(scenario, record, groups, status):
    """Keep public provenance and independent design groups consistent."""
    v.mapping(record, "dataset.cases")
    for field in ("origin", "license", "design_id", "domain"):
        v.text(record.get(field), "dataset." + field)
    assessment = "manual" if "maintainability" in scenario["types"] else "executable"
    v.require(record.get("assessment") == assessment, "dataset.assessment", "inconsistent assessment kind")
    _publication(scenario, record, status)
    group, design = scenario["group_id"], record["design_id"]
    v.require(group not in groups or groups[group] == design, "design_id", "project variants must share one design")
    v.require(design not in groups.values() or groups.get(group) == design, "design_id", "one design cannot inflate project groups")
    groups[group] = design


def _publication(scenario, record, status):
    """Keep publicly known material distinct from declaratively held-out material."""
    v.require(type(record.get("potentially_known")) is bool, "dataset.potentially_known", "expected boolean")
    if status == "public":
        v.require(record["potentially_known"] and scenario["split"] == "development",
                  "dataset", "public cases must be potentially known development material")
    else:
        v.require(scenario["split"] == "held_out", "dataset.split", "held_out catalog requires held_out scenarios")
