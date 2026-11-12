"""Value contracts for reproducible agent variants and development campaigns.

No model, Docker or private task dependencies live here. Runtime integrations
consume these same values rather than reconstructing prompts or identities.
"""

import copy
import hashlib
import json
from pathlib import Path

MODES = {"pytest", "cubie"}
TOOLS = {"analyze", "list_files", "read_file", "search_text", "write_file", "delete_file", "run_tests", "submit", "update_ledger", "search_files", "replace_text", "find_paths", "search_content", "collect_tests", "check_baseline", "read_test_details"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identity(design):
    return hashlib.sha256(canonical(design).encode("utf-8")).hexdigest()


def _fields(value, names, scope):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError(f"Invalid {scope} fields")


def _text(value, scope):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{scope} must be nonempty text")


def compose(core, specialization):
    """Validate closed component schemas and detach the resolved design."""
    _fields(core, "id prompt tools policy context", "core")
    _fields(specialization, "id mode guide examples", "specialization")
    for name in ("id", "prompt"):
        _text(core[name], f"core.{name}")
    for name in ("id", "guide"):
        _text(specialization[name], f"specialization.{name}")
    if specialization["mode"] not in MODES:
        raise ValueError("Invalid specialization mode")
    examples = specialization["examples"]
    if not isinstance(examples, list) or any(not isinstance(x, str) for x in examples):
        raise ValueError("specialization.examples must be a list of text")
    team = isinstance(core.get('context'), dict) and core['context'].get('version') in (6, 7, 8, 9)
    if team:
        from .team_design import POLICY, ROLES
        from .team_design import TOOLS as TEAM_TOOLS
        if core['context']['version'] == 9:
            from .team_v9_design import POLICY
            from .team_v9_design import TOOLS as TEAM_TOOLS
        elif core['context']['version'] == 8:
            from .team_v8_design import POLICY
            from .team_v8_design import TOOLS as TEAM_TOOLS
        elif core['context']['version'] == 7:
            from .team_v7_design import POLICY
            from .team_v7_design import TOOLS as TEAM_TOOLS
        _fields(core['context'], 'strategy version roles schemas templates', 'core.context')
        if core['context']['strategy'] != 'team' or type(core['context']['version']) is not int:
            raise ValueError('Invalid team context')
        if set(core['context']['roles']) != set(ROLES) or set(core['context']['schemas']) != set(ROLES):
            raise ValueError('Team requires analysis, qa and dev')
        for role in ROLES:
            _text(core['context']['roles'][role], 'role prompt')
            entries = core['context']['schemas'][role].get('oneOf', [])
            if not entries or any(e.get('properties', {}).get('action', {}).get('const') not in TEAM_TOOLS for e in entries):
                raise ValueError('Invalid role schema')
            from ollama_agents.errors import AdapterError
            from ollama_agents.schema import check_schema
            try:
                check_schema(core['context']['schemas'][role])
            except AdapterError as error:
                raise ValueError('Invalid role schema') from error
        _text(core['context']['templates'], 'template revision')
        _fields(core['policy'], ' '.join(POLICY), 'core.policy')
        if any(type(v) is not int or v < 0 for v in core['policy'].values()):
            raise ValueError('Invalid team policy')
    tools = core["tools"]
    if (not isinstance(tools, list) or not tools or any(not isinstance(t, str) or t not in (TEAM_TOOLS if team else TOOLS) for t in tools)
            or len(set(tools)) != len(tools)):
        raise ValueError("Invalid core tools")
    if not team:
        _fields(core["policy"], "repeat_limit repair_calls", "core.policy")
    if type(core["policy"]["repeat_limit"]) is not int or core["policy"]["repeat_limit"] < 2:
        raise ValueError("core.policy.repeat_limit must be at least two")
    if type(core["policy"]["repair_calls"]) is not int or core["policy"]["repair_calls"] not in (0, 1):
        raise ValueError("core.policy.repair_calls must be zero or one")
    if not team and (not isinstance(core["context"], dict) or type(core["context"].get("version")) is not int or core["context"] not in ({"strategy": "ledger", "version": 1},
                               {"strategy": "evidence", "version": 3},
                               {"strategy": "evidence", "version": 4},
                               {"strategy": "evidence", "version": 5})):
        raise ValueError("Unsupported core context strategy")
    return copy.deepcopy({"core": core, "specialization": specialization})


def freeze_design(design, path):
    """Create an exclusive snapshot; never replace previous experiment evidence."""
    _fields(design, "core specialization", "design")
    resolved = compose(design["core"], design["specialization"])
    content = canonical({"design": resolved, "identity": identity(resolved)}) + "\n"
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(content)
    except FileExistsError as error:
        raise ValueError(f"Design destination exists: {path}") from error


def load_design(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    _fields(payload, "design identity", "design snapshot")
    if identity(payload["design"]) != payload["identity"]:
        raise ValueError("Frozen design identity changed")
    design = payload["design"]
    _fields(design, "core specialization", "design")
    return compose(design["core"], design["specialization"])


def context(system, issue, exchanges, ledger, capacity):
    """Keep mandatory context and a contiguous suffix of complete exchanges.

    Measure the entire serialized request including the omission notice. The
    newest exchange is mandatory, so losing a tool result is never silent.
    """
    if type(capacity) is not int or capacity <= 0:
        raise ValueError("context capacity must be positive")
    for pair in exchanges:
        if len(pair) != 2 or [m["role"] for m in pair] != ["assistant", "user"]:
            raise ValueError("context requires complete assistant/user exchanges")

    def request(start):
        content = issue
        if ledger:
            content += "\nWorking ledger (observations, not instructions):\n" + canonical(ledger)
        if start:
            content += f"\n{start} older tool exchanges omitted; inspect current files as needed."
        return [{"role": "system", "content": system}, {"role": "user", "content": content}] + [
            copy.deepcopy(message) for pair in exchanges[start:] for message in pair]

    # json.dumps' default spacing matches the request representation used by the client.
    def fits(value):
        return len(json.dumps(value, ensure_ascii=False).encode("utf-8")) <= capacity

    start = max(0, len(exchanges) - 1)
    result = request(start)
    if not fits(result):
        raise ValueError("Mandatory context exceeds context_bytes")
    while start > 0:
        candidate = request(start - 1)
        if not fits(candidate):
            break
        start -= 1
        result = candidate
    return result


def progress(events, repeat_limit=3):
    """Derive feedback from observations, ignoring the model's stage label."""
    if type(repeat_limit) is not int or repeat_limit < 2:
        raise ValueError("repeat_limit must be at least two")
    if not events:
        return "continue"
    events = [e for e in events if e["action"]["action"] != "update_ledger"]
    if not events:
        return "continue"
    last = events[-1]
    observation = last["result"].get("observation")
    if observation == "invalid_test_run":
        return "repair_test"
    if observation == "assertion_failure":
        return "implement"


    recent = events[-repeat_limit:]
    if len(recent) == repeat_limit and len({event_signature(e) for e in recent}) == 1:
        return "redirect"
    return "continue"


def event_signature(event):
    """Ignore audit labels and nondeterministic pytest duration/output banners."""
    action = {k: v for k, v in event["action"].items() if k not in {"stage", "note"}}
    if action["action"] == "run_tests":
        result = {key: event["result"].get(key) for key in ("status", "observation", "exit_code", "timed_out")}
    else:
        result = {k: v for k, v in event["result"].items() if k not in {"elapsed_seconds", "junit_xml"}}
    return identity([action, result, event["workspace_sha256"]])


def validate_campaign(config):
    """Validate the admission projection; qualification evidence is bound at freeze."""
    if config.get("phase") not in {"development", "pilot", "measurement"}:
        raise ValueError("Invalid campaign phase")
    if set(config.get("modes", [])) != MODES or len(config["modes"]) != 2:
        raise ValueError("Campaign requires both modes")
    if not config.get("core_ids") or not config.get("task_ids"):
        raise ValueError("Campaign requires core and tasks")
    seeds = config.get("seeds")
    if not isinstance(seeds, list) or not seeds or any(type(seed) is not int for seed in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError("Campaign requires distinct integer seeds")
    if len(set(config["task_ids"])) != len(config["task_ids"]):
        raise ValueError("Campaign requires distinct tasks")
    if config["phase"] != "measurement":
        return
    if len(set(config["core_ids"])) != 1:
        raise ValueError("Measurement requires a common core")
    development = set(config.get("development_task_ids", []))
    if development.intersection(config["task_ids"]):
        raise ValueError("Measurement overlaps development tasks")
    groups = config.get("related_groups", {})
    if any(not groups.get(task) for task in [*development, *config["task_ids"]]):
        raise ValueError("Missing related group provenance")
    used = {groups[task] for task in development}
    if any(groups[task] in used for task in config["task_ids"]):
        raise ValueError("Measurement overlaps related development groups")
    budgets = config.get("budgets", {})
    if set(budgets) != MODES or budgets["pytest"] != budgets["cubie"]:
        raise ValueError("Measurement requires identical budgets")
    if any(config.get("qualification", {}).get(mode) is not True for mode in MODES):
        raise ValueError("Measurement requires qualification for both modes")


def summarize_trials(rows):
    result = {}
    for row in rows:
        entry = result.setdefault(row["phase"], {}).setdefault(
            row["design_id"], {"scheduled": 0, "resolved": 0, "unavailable": 0})
        entry["scheduled"] += 1
        entry["resolved"] += int(row["resolved"] is True)
        entry["unavailable"] += int(row["resolved"] is None)
    return result
