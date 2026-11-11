"""Bind measurement admission to archived development evidence, never to a flag."""


from .iteration import identity, load_design, validate_campaign


def behavior_cycle(observations, require_versions=False, final_tests=None):
    for index, red in enumerate(observations):
        if red["observation"] != "assertion_failure" or not red.get("targets") or (not require_versions and not red.get("workspace_sha256")):
            continue
        for green in observations[index + 1:]:
            if (green["observation"] != "pass" or green.get("targets") != red["targets"]
                    or green.get("baseline") or green.get("collection_only")):
                continue
            if require_versions:
                if final_tests is not None and green.get("tests") != final_tests:
                    continue
                if (red.get("tests") and red.get("tests") == green.get("tests") and
                        red.get("production") and green.get("production") and
                        (red.get("baseline") or red["production"] != green["production"])):
                    return True
            elif green.get("workspace_sha256") and green["workspace_sha256"] != red["workspace_sha256"]:
                return True
    return False


def admit(config, tasks, designs, source, destination):
    from .artifacts import MODES, digest, read, verify, write
    from .report import summarize

    projection = {"phase": config["phase"], "modes": list(MODES), "seeds": config["seeds"],
                  "core_ids": [identity(designs[mode]["core"]) for mode in MODES],
                  "task_ids": [task["id"] for task in tasks],
                  "budgets": {mode: config["budgets"] for mode in MODES},
                  "development_task_ids": [],
                  "related_groups": {task["id"]: task.get("related_group") for task in tasks},
                  "qualification": {mode: False for mode in MODES}}
    provenance = []
    if config.get("campaign"):
        campaign_path = source.parent / config["campaign"]
        specification = read(campaign_path)
        archives = specification.get("development_archives", [])
        if not isinstance(archives, list):
            raise ValueError("campaign.development_archives must be a list")
        # Keep revision hypothesis/parent/acceptance metadata as part of the freeze.
        write(destination / "campaign-specification.json", specification)
        qualifying = {mode: set() for mode in MODES}
        for archive in archives:
            root = (campaign_path.parent / archive).resolve()
            previous = verify(root)
            if previous["phase"] == "measurement":
                raise ValueError("Qualification requires development archives")
            # summarize checks every completed run's evidence manifest.
            summarize(root)
            previous_tasks = {task["id"]: task for task in read(root / "tasks.json")}
            for task in previous_tasks.values():
                projection["development_task_ids"].append(task["id"])
                group = task.get("related_group")
                if task["id"] in projection["related_groups"] and projection["related_groups"][task["id"]] != group:
                    raise ValueError("Conflicting related group provenance")
                projection["related_groups"][task["id"]] = group
            same_environment = all(previous[key] == config[key] for key in ("budgets", "ollama", "images"))
            all_available = True
            results = []
            for row in read(root / "schedule.json"):
                path = root / "runs" / row["run_id"] / "result.json"
                result = read(path) if path.exists() and (path.parent / "manifest.json").exists() else {"resolved": None}
                results.append((row, result))
                all_available &= result["resolved"] is not None
            contributes = False
            for mode in MODES:
                frozen_design = root / "designs" / f"{mode}.json"
                same_design = frozen_design.exists() and identity(load_design(frozen_design)) == identity(designs[mode])
                if not (same_environment and same_design and all_available):
                    continue
                for row, result in results:
                    task = previous_tasks[row["task_id"]]
                    if (row["mode"] != mode or result["resolved"] is not True
                            or not task.get("task_type") or task["task_type"] == "infrastructure_smoke"
                            or not task.get("related_group")):
                        continue
                    if behavior_cycle(result.get("agent", {}).get("test_observations", []),
                                      require_versions=designs[mode]["core"]["context"]["version"] >= 3,
                                      final_tests=result.get("agent", {}).get("final_versions", {}).get("tests", "")
                                      if designs[mode]["core"]["context"]["version"] >= 3 else None):
                        qualifying[mode].add(task["related_group"])
                        contributes = True
            admission = read(root / "ready.json")
            if admission["manifest_sha256"] != digest(root / "manifest.json"):
                raise ValueError("Qualification manifest changed after admission")
            for name, expected in admission["preflight_files"].items():
                if digest(root / name) != expected:
                    raise ValueError("Qualification preflight evidence changed")
            provenance.append({"archive": str(root), "contributes": contributes,
                               "runtime": read(root / "preflight/identity.json"),
                               "tasks": list(previous_tasks.values()), "admission": admission,
                               "runs": [{"schedule": row, "result": result,
                                         "manifest": read(root / "runs" / row["run_id"] / "manifest.json")
                                         if (root / "runs" / row["run_id"] / "manifest.json").exists() else None}
                                        for row, result in results], "manifest": read(root / "manifest.json"),
                               "qualified_groups": {mode: sorted(ids) for mode, ids in qualifying.items()}})
        projection["qualification"] = {mode: len(ids) >= 2 for mode, ids in qualifying.items()}
    elif config["phase"] == "measurement":
        raise ValueError("Measurement requires campaign development_archives and qualification evidence")
    validate_campaign(projection)
    write(destination / "campaign.json", {"admission": projection, "provenance": provenance})
