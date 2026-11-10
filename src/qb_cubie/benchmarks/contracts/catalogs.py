"""Validate optional provenance catalogs for public scenario datasets."""

from qb_cubie.benchmarks.contracts import _validation as v


def validate_catalog(root, package, scenarios):
    """Require complete provenance coverage without importing scenario code."""
    if "dataset" not in package:
        return
    catalog = v.read_data(v.contained(root, package["dataset"], "dataset"))
    v.choice(catalog.get("publication_status"), {"public"}, "publication_status")
    cases = v.mapping(catalog.get("cases"), "dataset.cases")
    v.require(set(cases) == {case["id"] for case in scenarios}, "dataset.cases", "scenario coverage differs")
    groups: dict[str, str] = {}
    for scenario in scenarios:
        _case(scenario, cases[scenario["id"]], groups)


def _case(scenario, record, groups):
    """Keep public provenance and independent design groups consistent."""
    v.mapping(record, "dataset.cases")
    for field in ("origin", "license", "design_id", "domain"):
        v.text(record.get(field), "dataset." + field)
    assessment = "manual" if "maintainability" in scenario["types"] else "executable"
    v.require(record.get("assessment") == assessment, "dataset.assessment", "inconsistent assessment kind")
    v.require(record.get("potentially_known") is True and scenario["split"] == "development",
              "dataset", "public cases must be potentially known development material")
    group, design = scenario["group_id"], record["design_id"]
    v.require(group not in groups or groups[group] == design, "design_id", "project variants must share one design")
    v.require(design not in groups.values() or groups.get(group) == design, "design_id", "one design cannot inflate project groups")
    groups[group] = design
