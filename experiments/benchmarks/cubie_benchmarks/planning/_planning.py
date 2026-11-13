"""Resolve local plan inputs, resource limits and adapter capabilities."""

import hashlib

from cubie_benchmarks.contracts import _validation as v
from cubie_benchmarks.contracts.packages import load_package
from cubie_benchmarks.planning.order import trials
from cubie_benchmarks.planning.pairs import groups

DEFAULTS = {"review_agent": {"wall_time_seconds": 300, "tool_calls": 20},
            "developer_agent": {"wall_time_seconds": 1800, "tool_calls": 100}}
CAPABILITIES = {"wall_time_seconds": "wall_time", "tool_calls": "tool_calls",
                "input_tokens": "token_usage", "output_tokens": "token_usage", "cost": "cost"}


def sources(root, values):
    """Resolve scenario sources and reject conflicting package identities."""
    v.require(type(values) is list and bool(values), "sources", "expected a nonempty list")
    scenarios: list[dict] = []
    packages: dict[str, dict] = {}
    admissions: dict[str, str | None] = {}
    for source in values:
        _source_cases(root, source, packages, admissions, scenarios)
    return scenarios, list(packages.values())


def _source(root, source):
    """Resolve a supported local scenario source."""
    v.mapping(source, "sources")
    v.require(set(source) <= {"path", "reference_report"} and "path" in source, "sources", "expected local path and optional reference_report")
    return (root / v.text(source.get("path"), "sources.path")).resolve()


def _identity(root, package):
    """Identify all declared package material with a deterministic digest."""
    paths = _package_paths(root, package)
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        _hash_file(digest, root, path)
    return {"namespace": package["namespace"], "version": package["version"], "sha256": digest.hexdigest()}


def _scenarios(package, identity):
    """Attach package identity to every loaded scenario."""
    return [{**scenario, "package": identity} for scenario in package["scenarios"]]


def agents(root, values):
    """Load uniquely identified agent configurations."""
    paths = v.strings(values, "agents", nonempty=True)
    result, ids = [], set()
    for path in paths:
        agent = v.read_data(root / path, toml=True)
        identifier = v.identifier(agent.get("id"), "agent.id")
        v.require(identifier not in ids, "agent.id", f"duplicate agent: {identifier}")
        v.command(agent.get("command"))
        v.strings(agent.get("capabilities"), "agent.capabilities")
        result.append(agent)
        ids.add(identifier)
    return result


def expand(scenarios, configured_agents, suite):
    """Expand selected scenarios into bounded trial combinations."""
    conditions = ["cubie", "pytest"] if suite["profile"] == "cubie-vs-pytest" else ["cubie"]
    paired = groups(suite, configured_agents)
    _preflight(scenarios, paired, conditions, suite)
    runs = []
    for pair_id, arms in paired:
        for repetition in range(1, suite["repetitions"] + 1):
            for scenario, condition in trials(scenarios, conditions, suite, repetition):
                run = _run(scenario, arms[condition], repetition, condition, suite)
                if pair_id is not None:
                    run["agent_pair_id"] = pair_id
                runs.append(run)
    return runs


def _run(scenario, agent, repetition, condition, suite):
    """Resolve one trial with its budgets and required capabilities."""
    budget = _budget(scenario, suite)
    required = _capabilities(scenario["benchmark"], budget)
    if scenario.get("process_profile") == "issue_resolution":
        required = (required - {"phased_submission"}) | {"project_patch"}
    missing = required - set(agent["capabilities"])
    v.require(not missing, "capabilities", f"{agent['id']} is missing {sorted(missing)}")
    extra = {key: scenario[key] for key in ("process_profile", "source", "regression_coverage", "reference_report_sha256", "reference_image_digest", "import_summary") if key in scenario}
    return {**extra, "scenario_id": scenario["qualified_id"], "agent_id": agent["id"],
            "repetition": repetition, "condition": condition, "budgets": budget,
            "benchmark": scenario["benchmark"], "types": scenario["types"], "tags": scenario["tags"],
            "split": scenario["split"], "group_id": scenario["group_id"], "package": scenario["package"],
            "evaluator": scenario["evaluator"], "required_capabilities": sorted(required)}


def _capabilities(benchmark, budget):
    """Determine capabilities required by the benchmark and budgets."""
    required = {"review_output"} if benchmark == "review_agent" else {"workspace_changes", "phased_submission"}
    return required | {CAPABILITIES[key] for key in budget} | {"cancel"}


def limits(value, count, total):
    """Validate global limits against the complete run plan."""
    v.mapping(value, "limits")
    v.require(set(value) <= {"max_runs", "max_total_wall_time_seconds"}, "limits", "unknown global limit")
    maximum = v.number(value.get("max_runs", 1000), "max_runs", positive=True, integer=True)
    seconds = v.number(value.get("max_total_wall_time_seconds", 36000), "max_total_wall_time_seconds", positive=True)
    v.require(count <= maximum, "max_runs", f"plan requires {count} runs; limit is {maximum}")
    v.require(total <= seconds, "max_total_wall_time_seconds", f"plan requires {total} seconds; limit is {seconds}")
    return {"max_runs": maximum, "max_total_wall_time_seconds": seconds, "total_wall_time_seconds": total}


def _preflight(scenarios, configured_agents, conditions, suite):
    """Check trial counts and total budgets before expansion."""
    factor = len(configured_agents) * len(conditions) * suite["repetitions"]
    count = len(scenarios) * factor
    total = sum(_budget(scenario, suite)["wall_time_seconds"] for scenario in scenarios) * factor
    limits(suite.get("limits", {}), count, total)


def _budget(scenario, suite):
    """Resolve default, suite and scenario budget overrides."""
    return {**DEFAULTS[scenario["benchmark"]], **suite.get("budgets", {}), **scenario.get("budgets", {})}


def _hash_file(digest, root, path):
    """Add framed path, mode, symlink and content data to a package digest."""
    if {"__pycache__", ".pytest_cache"} & set(path.relative_to(root).parts):
        return
    v.require(path.resolve().is_relative_to(root), "sources", f"material escapes package: {path}")
    v.require(not (path.is_symlink() and path.is_dir()), "sources", "directory symlinks are unsupported")
    name = path.relative_to(root).as_posix().encode()
    content = path.read_bytes() if path.is_file() else b""
    target = str(path.readlink()).encode() if path.is_symlink() else b""
    mode = (path.stat().st_mode & 0o777).to_bytes(2, "big")
    for value in (name, mode, target, content):
        digest.update(len(value).to_bytes(8, "big") + value)


def _admission(root, source, path, package):
    """Resolve a bound reference report and the executed image identities."""
    report = source.get("reference_report")
    if report is not None:
        v.text(report, "sources.reference_report")
        from cubie_benchmarks.swebench.admission import check_report
        report_hash = check_report((root / report).resolve(), path, package)
        report_data = v.read_data((root / report).resolve())
        images = {row["instance_id"]: row["evidence"][0]["image_digest"] for row in report_data["scenarios"]}
    else:
        report_hash, images = None, {}
    return (report_hash, images)


def _source_cases(root, source, packages, admissions, scenarios):
    """Collect one source while rejecting conflicting package admissions."""
    path = _source(root, source)
    package = load_package(path)
    namespace, identity = package["namespace"], _identity(path, package)
    report_hash, images = _admission(root, source, path, package)
    v.require(namespace not in packages or packages[namespace] == identity, "namespace", f"conflicting package {namespace}")
    v.require(namespace not in admissions or admissions[namespace] == report_hash, "reference_report", "conflicting reference admission for one package")
    admissions[namespace] = report_hash
    if namespace not in packages:
        scenarios.extend({**scenario, **({"reference_report_sha256": report_hash, "reference_image_digest": images[scenario["id"]]} if report_hash else {})}
                         for scenario in _scenarios(package, identity))
    packages[namespace] = identity


def _package_paths(root, package):
    """Enumerate every declared package material path."""
    manifests = [root / "package.json"]
    paths = set(manifests)
    if "dataset" in package:
        paths.add(v.contained(root, package["dataset"], "dataset"))
    if "swebench_import" in package:
        paths.add(v.contained(root, package["swebench_import"], "swebench_import"))
    for scenario in package["scenarios"]:
        directory = root / scenario["manifest"]
        paths.update(directory.parent.rglob("*"))
    return paths
