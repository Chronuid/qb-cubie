"""Select reproducible task prefixes balanced by task type and repository."""

import random
from collections import Counter, defaultdict

METADATA = ("task_type", "change_kind", "test_scope", "related_group", "repo", "review_status")


def select(tasks, *, count=None, seed=20261111, task_types=()):
    if count is not None and (type(count) is not int or count < 1):
        raise ValueError("selection.task_count must be a positive integer")
    if type(seed) is not int:
        raise ValueError("selection.seed must be an integer")
    if len({task["id"] for task in tasks}) != len(tasks):
        raise ValueError("Task IDs must be distinct")
    rng = random.Random(seed)
    buckets = defaultdict(lambda: defaultdict(list))
    for task in sorted(tasks, key=lambda item: item["id"]):
        kind = task.get("task_type", "unspecified")
        if not task_types or kind in task_types:
            buckets[kind][task.get("repo", "unspecified")].append(task)
    kinds = sorted(buckets)
    rng.shuffle(kinds)
    repositories = {}
    for kind in kinds:
        repositories[kind] = sorted(buckets[kind])
        rng.shuffle(repositories[kind])
        for repo in repositories[kind]:
            rng.shuffle(buckets[kind][repo])
    ordered, groups = [], set()
    while kinds:
        remaining = []
        for kind in kinds:
            task = take(buckets[kind], repositories[kind], groups)
            if task is not None:
                ordered.append(task)
                groups.add(task.get("related_group") or task["id"])
                remaining.append(kind)
        kinds = remaining
    if count is not None and count > len(ordered):
        raise ValueError(f"Requested {count} tasks, but only {len(ordered)} independent eligible tasks match")
    if not ordered:
        raise ValueError("No tasks match the selection")
    return ordered if count is None else ordered[:count]


def take(buckets, repositories, groups):
    for _ in range(len(repositories)):
        repo = repositories.pop(0)
        repositories.append(repo)
        while buckets[repo]:
            task = buckets[repo].pop()
            if (task.get("related_group") or task["id"]) not in groups:
                return task
    return None


def configured(tasks, config):
    options = config.get("selection", {})
    if not options:
        return tasks
    return select(tasks, count=options.get("task_count"), seed=options.get("seed", config["order_seed"]),
                  task_types=options.get("task_types", []))


def distribution(tasks):
    return {key: dict(sorted(Counter(task.get(key, "unspecified") for task in tasks).items()))
            for key in ("task_type", "change_kind", "test_scope", "repo")}


def metadata(task):
    result = {key: task[key] for key in METADATA if key in task}
    if any(not isinstance(value, str) or not value.strip() for value in result.values()):
        raise ValueError("Task metadata must contain nonempty strings")
    return result
