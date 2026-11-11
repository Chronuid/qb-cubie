"""Summarize verified pilot archives without rerunning or modifying experiments."""

from collections import Counter, defaultdict
from pathlib import Path

from qb_cubie.benchmarks.contracts import _validation as v
from qb_cubie.benchmarks.reporting import _pilot_stats as stats
from qb_cubie.benchmarks.reporting._pilot_integrity import compatible
from qb_cubie.benchmarks.reporting.archives import read_archive


def summarize_pilot(archives: list[str | Path]) -> dict:
    """Aggregate archived attempts by benchmark, agent and comparison condition."""
    v.require(type(archives) is list and bool(archives), "archives", "expected nonempty archive paths")
    try:
        entries = _entries(archives)
        compatible(entries)
        grouped = defaultdict(list)
        for _, run in entries:
            grouped[run["benchmark"], run["agent_id"], run["condition"], run.get("process_profile", "builtin")].append(run)
        return {"schema_version": 1, **_provenance(entries), "pending_adjudications": _pending(entries),
                "groups": [_group(key, grouped[key]) for key in sorted(grouped)]}
    except (KeyError, TypeError, IndexError, OSError) as error:
        raise ValueError(f"archive: malformed or missing pilot material: {error}") from error


def _entries(archives):
    """Validate each archive and prevent duplicate attempts across copied inputs."""
    entries, seen = [], set()
    for path in archives:
        root = Path(path).resolve()
        result = read_archive(root)
        for run in result["runs"]:
            _validate(run)
            v.require(run["run_id"] not in seen, "run_id", "duplicate trial in pilot archives")
            seen.add(run["run_id"])
            entries.append((root, run))
    v.require(bool(entries), "archives", "no trials")
    return entries


def _validate(run):
    """Require supported statuses and preserve optional quality observations."""
    v.choice(run["status"], v.STATUSES, "status")
    v.choice(run["evaluation_status"], {"complete", "not_evaluated", "pending_adjudication"}, "evaluation_status")
    v.choice(run["benchmark"], v.PHASES, "benchmark")
    v.require(run["quality_passed"] is None or type(run["quality_passed"]) is bool, "quality_passed", "expected boolean or null")
    v.require(type(run["metrics"]) is list, "metrics", "expected a list")
    v.require(type(run["repetition"]) is int and run["repetition"] > 0, "repetition", "expected positive integer")
    v.strings(run["types"], "types")
    v.mapping(run["usage"], "usage")


def _group(key, runs):
    """Report quality, process, effort and project counts independently."""
    counts = stats.counts(runs)
    result = dict(zip(("benchmark", "agent_id", "condition"), key[:3], strict=True))
    result.update(counts=counts, scenario_count=len({run["scenario_id"] for run in runs}),
                  independent_groups=len({(run["package"]["namespace"], run["group_id"]) for run in runs}),
                  repetitions=sorted({run["repetition"] for run in runs}), statuses=dict(sorted(Counter(run["status"] for run in runs).items())),
                  quality_pass_rate=counts["quality_passed"] / counts["started"] if counts["started"] else None,
                  usage=stats.usage(runs))
    if key[3] == "issue_resolution":
        return _repair_group(result, runs)
    return {**result, **_details(key[0], runs)}


def _details(benchmark, runs):
    """Attach the metrics appropriate to one benchmark kind."""
    if benchmark == "review_agent":
        families = stats.family_stats(runs)
        return {"families": families, "macro_metrics": stats.macro(families)}
    return {"episodes": _episodes(runs)}


def _episodes(runs):
    """Keep primary episode kinds distinct from repeated project observations."""
    return {episode: {"counts": stats.counts([run for run in runs if episode in run["types"]])}
            for episode in sorted(stats.EPISODES) if any(episode in run["types"] for run in runs)}


def _provenance(entries):
    """Never infer actual model use from a successful process handshake."""
    modeled = [run["agent_kind"] == "process" and bool(run.get("model_id")) and bool(run.get("model_provenance"))
               for _, run in entries]
    kind = "agent_evaluation" if all(modeled) else "mixed" if any(modeled) else "infrastructure_only"
    warnings = (["Model provenance is adapter-declared and matched to configuration; this does not independently verify provider execution."]
                if all(modeled) else ["Some or all attempts have no archived model provenance; process and fake trials are infrastructure observations."])
    return {"measurement_kind": kind, "warnings": warnings}


def _pending(entries):
    """Retain source archive identities and evidence for unresolved findings."""
    return [{"archive": str(root), "run_id": run["run_id"], "scenario_id": run["scenario_id"],
             "evidence": list(run["evidence"]), "reason": run.get("reason")}
            for root, run in entries if run["evaluation_status"] == "pending_adjudication"]


def _repair_group(result, runs):
    """Report repair quality by repository without TDD process credit."""
    result["counts"]["process_passed"] = None
    return {**result, "process_profile": "issue_resolution",
            "independent_groups": len({run["source"]["repo"] for run in runs}),
            "repositories": sorted({run["source"]["repo"] for run in runs}),
            "regression_coverage_missing": sorted({run["scenario_id"] for run in runs if not run["regression_coverage"]}),
            "provenance": [{"scenario_id": run["scenario_id"], "source": run["source"], "import_summary": run["import_summary"]} for run in runs]}
