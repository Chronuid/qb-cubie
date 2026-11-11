"""Plan paired runs and explicit runtime allowances without model inference."""

import math
from pathlib import Path

from .artifacts import digest, load_config, read
from .selection import configured, distribution, metadata


def allowance(config, count):
    budget, planning = config["budgets"], config.get("planning", {})
    seeds = len(config["seeds"])
    setup = planning.get("setup_seconds_per_run", 60)
    agent = 2 * seeds * budget["wall_seconds"]
    evaluation = 2 * seeds * budget["verification_seconds"]
    execution_setup = 2 * seeds * setup
    references = 2 * (budget["verification_seconds"] + setup)
    per_task = agent + evaluation + execution_setup + references
    hours = planning.get("hours")
    return {"tasks": count, "seeds_per_task": seeds, "agent_runs": 2 * seeds * count,
            "agent_budget_hours": count * agent / 3600,
            "evaluation_budget_hours": count * evaluation / 3600,
            "reference_and_setup_allowance_hours": count * (execution_setup + references) / 3600,
            "total_allowance_hours": count * per_task / 3600, "target_hours": hours,
            "fits_allowance": count * per_task <= hours * 3600 if hours is not None else None,
            "task_capacity_for_target": math.floor(hours * 3600 / per_task) if hours is not None else None,
            "setup_seconds_per_run_assumed": setup,
            "interpretation": "Planning allowance, not measured runtime or a hard study deadline. "
                              "Includes baseline/reference checks and one setup allowance per container. "
                              "Image builds, image probes and manual data admission are additional."}


def plan(config_path, catalog=None):
    config_path = Path(config_path).resolve()
    config = load_config(config_path)
    source = Path(catalog).resolve() if catalog else config_path.parent / config["tasks"]
    data = read(source)
    if catalog:
        tasks = [task for task in data["tasks"] if task["split"] == config["phase"] and task["eligible"]]
        stage = "candidates_not_admitted"
    else:
        tasks = data
        if any(task["split"] != config["phase"] for task in tasks):
            raise ValueError("Task splits must match study phase")
        stage = "input_manifest_not_preflighted"
    selected = configured(tasks, config)
    return {"study_id": config["study_id"], "phase": config["phase"], "status": stage,
            "source_sha256": digest(source), "available_before_selection": len(tasks),
            "selection": config.get("selection", {}),
            "tasks": [{"id": task["id"], "split": task["split"], **metadata(task)} for task in selected],
            "distribution": distribution(selected), "runtime": allowance(config, len(selected))}
