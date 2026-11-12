"""Summarize scheduled outcomes and uncertainty at the task level."""

import random
import statistics
from collections import defaultdict
from pathlib import Path

from .artifacts import MODES, digest, read, verify
from .iteration import summarize_trials
from .planning import allowance
from .selection import distribution


def summarize(root):
    root = Path(root).resolve()
    config = verify(root)
    schedule = read(root / "schedule.json")
    rows = []
    for expected in schedule:
        directory = root / "runs" / expected["run_id"]
        if not (directory / "manifest.json").exists():
            rows.append({**expected, "resolved": None, "missing": True})
            continue
        for name, sha in read(directory / "manifest.json").items():
            if digest(directory / name) != sha:
                raise ValueError(f"Run evidence changed: {directory.name}/{name}")
        row = read(directory / "result.json")
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError("Run result does not match frozen schedule")
        rows.append(row)
    tasks = read(root / "tasks.json")
    return {"study_id": config["study_id"], "phase": config["phase"], "scheduled_runs": len(schedule),
            "by_design": summarize_trials([{**row, "phase": row.get("phase", config["phase"]),
                                             "design_id": row.get("design_id", "legacy-unversioned")} for row in rows]),
            "arms": arms(rows), **paired(rows), "task_distribution": distribution(tasks),
            "by_task_type": grouped(rows, "task_type"), "by_change_kind": grouped(rows, "change_kind"),
            "runtime_plan": allowance(config, len(tasks)),
            "interpretation": "Pilot is exploratory. Seeds are repeated measurements, not independent tasks. "
                              "Missing outcomes remain unavailable; compare both scheduled rates and complete pairs. "
                              "Small task-type subgroups are descriptive, not evidence of a type-specific advantage. "
                              "The contrast is Cubie plus guide on the chosen tasks/model, not universal benefit."}


def paired(rows):
    pairs = defaultdict(dict)
    for row in rows:
        pairs[row["pair_id"]][row["mode"]] = row
    per_task = defaultdict(list)
    discordant = {"cubie_only": 0, "pytest_only": 0}
    complete = 0
    for pair in pairs.values():
        if any(pair[mode]["resolved"] is None for mode in MODES):
            continue
        complete += 1
        pytest, cubie = (int(pair[mode]["resolved"]) for mode in MODES)
        per_task[pair["cubie"]["task_id"]].append(cubie - pytest)
        discordant["cubie_only"] += int(cubie > pytest)
        discordant["pytest_only"] += int(pytest > cubie)
    effects = {task: statistics.mean(values) for task, values in per_task.items()}
    effect = statistics.mean(effects.values()) if effects else None
    return {"complete_pairs": complete,
            "unavailable_pairs": len(pairs) - complete, "discordant_pairs": discordant,
            "per_task_difference": effects, "paired_task_mean_difference": effect,
            "task_bootstrap_95_interval": interval(list(effects.values()))}


def arms(rows):
    return {mode: arm([r for r in rows if r["mode"] == mode]) for mode in MODES}


def grouped(rows, field):
    groups = defaultdict(list)
    for row in rows:
        groups[row.get(field, "unspecified")].append(row)
    return {name: {"tasks": len({row["task_id"] for row in group}),
                   "arms": arms(group), **paired(group)} for name, group in sorted(groups.items())}


def arm(rows):
    resolved = sum(row["resolved"] is True for row in rows)
    available = sum(row["resolved"] is not None for row in rows)
    tokens, times, inputs, outputs, model_calls, tool_calls, observations = [], [], [], [], [], [], []
    for row in rows:
        agent = row.get("agent", {})
        if "duration_seconds" in agent:
            times.append(agent["duration_seconds"])
            model_calls.append(agent.get("model_calls"))
            tool_calls.append(agent.get("tool_calls"))
        observations.extend(item["observation"] for item in agent.get("test_observations", []))
        for usage in agent.get("usage", []):
            inputs.append(usage.get("input_tokens"))
            outputs.append(usage.get("output_tokens"))
            tokens.append(usage.get("input_tokens"))
            tokens.append(usage.get("output_tokens"))
    return {"scheduled": len(rows), "available": available, "unavailable": len(rows) - available,
            "resolved": resolved, "resolved_per_scheduled": resolved / len(rows),
            "resolved_per_available": resolved / available if available else None,
            "median_agent_seconds": statistics.median(times) if times else None,
            "runs_with_agent_metrics": len(times),
            "measured_total_tokens": measured(tokens), "measured_input_tokens": measured(inputs),
            "measured_output_tokens": measured(outputs), "measured_model_calls": measured(model_calls),
            "measured_tool_calls": measured(tool_calls), "visible_test_observations": dict_counts(observations),
            "process_metrics": {key: measured([r.get("agent", {}).get("process_metrics", {}).get(key)
                                               for r in rows])
                                for key in ("rejected_retries", "tool_errors", "ebt_executed", "ebt_evaluated", "ebt_passed")},
            "agent_stops": dict_counts(row.get("agent", {}).get("status", "unavailable") for row in rows),
            'internal_completion': dict_counts(row.get('agent', {}).get('completion', {}).get('status', 'unavailable') for row in rows),
            'team_process_metrics': {key: measured([r.get('agent', {}).get('process_metrics', {}).get(key)
                                                   for r in rows])
                                     for key in ('information_requests', 'revision_rounds', 'edit_conflicts',
                                                 'recoveries', 'ebt_evaluation_checked', 'controller_tool_calls',
                                                 'duplicate_actions', 'cursor_errors', 'scope_not_found')},
            'workflow': workflow(rows) if any('milestones' in r.get('agent', {}).get('process_metrics', {})
                                              for r in rows) else None}


def workflow(rows):
    """Report missing milestones explicitly; durations use reached runs only."""
    milestones = ('qa', 'dev', 'case', 'suite', 'test_run', 'red', 'production_change', 'verification')
    runs = [r.get('agent', {}).get('process_metrics', {}).get('milestones', {}) for r in rows]
    result = {}
    for name in milestones:
        reached = [run[name] for run in runs if name in run]
        result[name] = {'reached': len(reached), 'scheduled': len(rows),
                        'not_reached': len(rows) - len(reached),
                        'per_scheduled': len(reached) / len(rows) if rows else None,
                        'duration_denominator': len(reached),
                        'mean_seconds_when_reached': statistics.mean(r['seconds'] for r in reached) if reached else None,
                        'mean_model_calls_when_reached': statistics.mean(r['model_calls'] for r in reached) if reached else None}
    result['suite_per_started_qa'] = {
        'numerator': result['suite']['reached'], 'denominator': result['qa']['reached'],
        'rate': result['suite']['reached'] / result['qa']['reached'] if result['qa']['reached'] else None}
    return result


def measured(values):
    return sum(values) if values and all(value is not None for value in values) else None


def dict_counts(values):
    result = defaultdict(int)
    for value in values:
        result[value] += 1
    return dict(result)


def interval(values):
    if len(values) < 2:
        return None
    rng = random.Random(20261111)
    samples = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(10000))
    return [samples[249], samples[9749]]
