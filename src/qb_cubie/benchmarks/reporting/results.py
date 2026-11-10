"""Archive resolved plans, observations and linked human-readable results."""

import platform

from qb_cubie.benchmarks.reporting._files import (
    digest,
    inventory,
    wheel_hash,
    write_json,
)


def save(root, plan, inputs, runs):
    """Persist results, linked evidence and the resolved run manifest."""
    result = {"schema_version": 1, "run_id": root.name, "output": str(root), "runs": runs}
    write_json(root / "results.json", result)
    _report(root / "report.md", result)
    manifest = {"schema_version": 1, "run_id": root.name, "plan": plan, "inputs": inputs,
                "started_at": min(run["started_at"] for run in runs), "finished_at": max(run["finished_at"] for run in runs),
                "suite_sha256": digest(root / inputs["suite"][0]),
                "resolved_plan_sha256": digest(root / inputs["plan"][0]),
                "python_version": platform.python_version(), "wheel_sha256": wheel_hash(),
                "artifact_hashes": inventory(root)}
    write_json(root / "manifest.json", manifest)
    return result


def _report(path, result):
    """Write the human-readable run report."""
    description = "Infrastructure check; no model performance was measured." if all(r["agent_kind"] == "fake" for r in result["runs"]) else "External process benchmark; inspect each agent configuration and its evidence."
    lines = ["# Benchmark results", "", description, "",
             "[Manifest](manifest.json) · [JSON results](results.json)", ""]
    for run in result["runs"]:
        lines.extend(_section(run))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _section(run):
    """Describe one attempt and link its evaluation evidence."""
    lines = [f"## {run['scenario_id']} ({run['run_id']})", "",
             f"Status: {run['status']}; quality_passed: {str(run['quality_passed']).lower()}", ""]
    lines.extend(f"- {key}: {value}" for key, value in run["criterion_results"].items())
    lines.extend(_phases(run))
    if run.get("process_reason") or run.get("reason"):
        lines.extend(["", str(run.get("process_reason") or run["reason"])])
    lines.extend(["", *[f"- [Evidence]({path})" for path in run["evidence"]], ""])
    return lines


def _phases(run):
    """Render developer phase outcomes and evidence links."""
    return [f"- {phase['phase']}: {phase['test_outcome']} " +
            " ".join(f"[Evidence]({path})" for path in phase["evidence"])
            for phase in run.get("phases", [])]
