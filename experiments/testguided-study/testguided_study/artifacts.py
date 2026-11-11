"""Freeze inputs, paired schedules and implementation identities."""

import base64
import hashlib
import ipaddress
import json
import random
import shutil
import tarfile
import tempfile
import tomllib
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from .selection import configured, distribution, metadata

ROOT = Path(__file__).resolve().parents[1]
MODES = ("pytest", "cubie")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=encoded) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def encoded(value):
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}
    raise TypeError(f"Unsupported evidence value: {type(value).__name__}")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sources():
    import ollama_agents
    result = {}
    for label, root in (("study", ROOT / "testguided_study"), ("ollama", Path(ollama_agents.__file__).parent)):
        for path in sorted(root.rglob("*.py")):
            result[f"{label}/{path.relative_to(root)}"] = digest(path)
    result["study/study.py"] = digest(ROOT / "study.py")
    return result


def schedule(tasks, seeds, order_seed):
    rng = random.Random(order_seed)
    pairs = [(task["id"], seed) for task in tasks for seed in seeds]
    rng.shuffle(pairs)
    first = rng.randrange(2)
    rows = []
    for index, (task_id, seed) in enumerate(pairs):
        modes = MODES if (index + first) % 2 == 0 else tuple(reversed(MODES))
        for mode in modes:
            rows.append({"run_id": f"{len(rows) + 1:04d}", "pair_id": f"{index + 1:04d}",
                         "task_id": task_id, "seed": seed, "mode": mode,
                         **metadata(next(task for task in tasks if task["id"] == task_id))})
    return rows


def load_config(path):
    with Path(path).open("rb") as stream:
        config = tomllib.load(stream)
    fields(config, "schema_version study_id phase tasks seeds order_seed ollama budgets images guides", "study",
           optional="selection planning designs campaign")
    fields(config["ollama"], "endpoint model think temperature num_ctx num_predict", "ollama")
    fields(config["budgets"], "wall_seconds model_calls tool_calls command_seconds verification_seconds context_bytes output_chars", "budgets")
    fields(config["images"], "pytest cubie evaluator", "images")
    fields(config["guides"], "pytest cubie", "guides")
    if "designs" in config:
        fields(config["designs"], "pytest cubie", "designs")
        if any(not isinstance(path, str) or not path for path in config["designs"].values()):
            raise ValueError("designs requires JSON paths")
    if "campaign" in config and (not isinstance(config["campaign"], str) or not config["campaign"]):
        raise ValueError("campaign must be a JSON path")
    if config["schema_version"] != 1 or config["phase"] not in {"pilot", "development", "measurement"}:
        raise ValueError("Unsupported schema_version or study phase")
    seeds = config["seeds"]
    if not seeds or len(set(seeds)) != len(seeds) or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be distinct integers")
    if type(config["order_seed"]) is not int:
        raise ValueError("order_seed must be an integer")
    for name, value in config["budgets"].items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"budgets.{name} must be a positive integer")
    model = config["ollama"]
    url = urlsplit(model["endpoint"])
    host = url.hostname
    local = is_local(host)
    if url.scheme != "http" or not local or url.username or url.password or url.query or url.fragment or url.path not in ("", "/"):
        raise ValueError("ollama.endpoint must be a local HTTP origin without credentials")
    if type(model["think"]) is not bool or not 0 <= model["temperature"] <= 2:
        raise ValueError("Explicit think boolean and temperature in [0, 2] required")
    if not 0 < model["num_predict"] < model["num_ctx"]:
        raise ValueError("Output reserve must be smaller than the model context")
    selection = config.get("selection", {})
    if selection:
        fields(selection, "task_count seed task_types", "selection")
        if type(selection["task_count"]) is not int or selection["task_count"] < 1 or type(selection["seed"]) is not int:
            raise ValueError("selection requires positive task_count and an integer seed")
        if not isinstance(selection["task_types"], list) or any(not isinstance(t, str) for t in selection["task_types"]):
            raise ValueError("selection.task_types must be a list of type names")
    planning = config.get("planning", {})
    if planning:
        fields(planning, "hours setup_seconds_per_run", "planning")
        if type(planning["hours"]) not in (int, float) or not 0 < planning["hours"] < float("inf"):
            raise ValueError("planning.hours must be finite and positive")
        if type(planning["setup_seconds_per_run"]) is not int or planning["setup_seconds_per_run"] < 0:
            raise ValueError("planning.setup_seconds_per_run must be a nonnegative integer")
    return config


def fields(data, expected, scope, optional=""):
    required = set(expected.split())
    if not isinstance(data, dict) or not required <= set(data) or set(data) - required - set(optional.split()):
        raise ValueError(f"{scope} requires exactly these fields: {', '.join(sorted(required))}")


def is_local(host):
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def check_snapshot(path):
    with tarfile.open(path, "r:*") as archive:
        for entry in archive:
            name = PurePosixPath(entry.name)
            if name.is_absolute() or ".." in name.parts or ".git" in name.parts:
                raise ValueError(f"Unsafe snapshot entry: {entry.name}")
            if not entry.isdir() and not entry.isfile():
                raise ValueError(f"Snapshot links/special files must be materialized: {entry.name}")
            if any(part in {"evaluator", "secret", "evidence"} for part in name.parts):
                raise ValueError(f"Private inputs in visible snapshot: {entry.name}")
            if entry.isfile() and entry.size < 2_000_000:
                content = archive.extractfile(entry).read()
                if b"qb_cubie" in content or b"qb-cubie" in content:
                    raise ValueError(f"Common snapshot already exposes Cubie: {entry.name}")


def freeze(config_path, destination):
    config_path, destination = Path(config_path).resolve(), Path(destination).resolve()
    config = load_config(config_path)
    task_path = config_path.parent / config["tasks"]
    tasks = read(task_path)
    if not tasks or len({task["id"] for task in tasks}) != len(tasks):
        raise ValueError("Select a nonempty list of distinct task IDs before freezing")
    allowed_splits = {"pilot", "development"} if config["phase"] == "development" else {config["phase"]}
    if any(task["split"] not in allowed_splits for task in tasks):
        raise ValueError("Task splits must match study phase; pilot and measurement cannot mix")
    tasks = configured(tasks, config)
    if config["phase"] == "measurement" and any(
            not {"task_type", "change_kind", "test_scope", "repo", "related_group"} <= task.keys() for task in tasks):
        raise ValueError("Measurement tasks require task_type, change_kind, test_scope, repo and related_group metadata")
    destination.mkdir(parents=True, exist_ok=False)
    try:
        shutil.copyfile(config_path, destination / "study.toml")
        frozen = []
        for index, task in enumerate(tasks):
            snapshot, record = task_path.parent / task["snapshot"], task_path.parent / task["record"]
            data = read(record)
            if data["instance_id"] != task["id"] or not data["test_patch"] or not data["patch"]:
                raise ValueError("Every task needs matching identity, private tests and a reference fix")
            if task.get("repo", data["repo"]) != data["repo"]:
                raise ValueError("Task metadata repository does not match the private record")
            if not data.get("FAIL_TO_PASS") or not data.get("PASS_TO_PASS"):
                raise ValueError("Explicit repair and regression test IDs are required")
            check_snapshot(snapshot)
            directory = destination / "inputs" / f"{index:04d}"
            directory.mkdir(parents=True)
            shutil.copyfile(snapshot, directory / "snapshot.tar.gz")
            shutil.copyfile(record, directory / "record.json")
            frozen.append({"id": task["id"], "split": task["split"],
                           **metadata(task),
                           "snapshot": (directory / "snapshot.tar.gz").relative_to(destination).as_posix(),
                           "record": (directory / "record.json").relative_to(destination).as_posix()})
        guides = {mode: (config_path.parent / config["guides"][mode]).read_text(encoding="utf-8") for mode in MODES}
        write(destination / "guides.json", guides)
        write(destination / "tasks.json", frozen)
        write(destination / "task-distribution.json", distribution(frozen))
        from . import campaign
        from .design import default_design
        from .iteration import compose, freeze_design, identity
        designs = {}
        if "designs" in config:
            fields(config["designs"], "pytest cubie", "designs")
        for mode in MODES:
            if "designs" in config:
                data = read(config_path.parent / config["designs"][mode])
                fields(data, "core specialization", "design")
                designs[mode] = compose(data["core"], data["specialization"])
                if designs[mode]["specialization"]["mode"] != mode:
                    raise ValueError("Design specialization mode does not match configuration")
            else:
                designs[mode] = default_design(mode, guides)
            freeze_design(designs[mode], destination / "designs" / f"{mode}.json")
        campaign.admit(config, frozen, designs, config_path, destination)
        rows = schedule(frozen, config["seeds"], config["order_seed"])
        for row in rows:
            row.update(design_id=identity(designs[row["mode"]]),
                       core_id=identity(designs[row["mode"]]["core"]), phase=config["phase"])
        write(destination / "schedule.json", rows)
        manifest = {p.relative_to(destination).as_posix(): digest(p) for p in destination.rglob("*") if p.is_file()}
        write(destination / "manifest.json", {"schema_version": 1, "files": manifest, "implementation": sources()})
    except BaseException:
        shutil.rmtree(destination)
        raise
    return {"directory": str(destination), "tasks": len(tasks), "runs": len(tasks) * len(config["seeds"]) * 2,
            "manifest_sha256": digest(destination / "manifest.json")}


def verify(root):
    root = Path(root).resolve()
    manifest = read(root / "manifest.json")
    for name, expected in manifest["files"].items():
        if digest(root / name) != expected:
            raise ValueError(f"Frozen input changed: {name}")
    if sources() != manifest["implementation"]:
        raise ValueError("Agent/study implementation changed since freeze; create a new study")
    return load_config(root / "study.toml")
