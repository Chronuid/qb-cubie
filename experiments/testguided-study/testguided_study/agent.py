"""Run the same testguided action loop for both framework treatments."""

import json
import time

from ollama_agents.client import OllamaClient
from ollama_agents.errors import AdapterError

from .artifacts import write
from .design import default_design, design_instruction, design_schema
from .iteration import compose, context, event_signature, identity, progress
from .telemetry import emit
from .workspace import execute, patch


def messages(system, task, history, capacity):
    return context(system, task, history, {}, capacity)


def develop(manager, sandbox, task, row, config, guides, directory, client=None, observer=None, design=None, clock=None):
    clock = clock or time.monotonic
    design = design or default_design(row["mode"], guides)
    design = compose(design["core"], design["specialization"])
    if design["specialization"]["mode"] != row["mode"]:
        raise ValueError("Design specialization does not match run mode")
    if row.get("design_id", identity(design)) != identity(design):
        raise ValueError("Design identity does not match frozen run")
    schema = design_schema(design)
    policy = design["core"]["policy"]
    limits, model = config["budgets"], config["ollama"]
    client = client or OllamaClient(endpoint=model["endpoint"], model=model["model"],
                                    think=model["think"], options={
                                        key: model[key] for key in ("temperature", "num_ctx", "num_predict")
                                    } | {"seed": row["seed"]})
    started = clock()
    emit(observer, "agent_started", "Agentenschleife gestartet", active={"agent_started_at": time.time()})
    history, usage, observations = [], [], []
    status, calls, tools = "model_budget", 0, 0
    system = design_instruction(design)
    ledger, events, repairs = {}, [], 0
    workspace_patch = patch(manager, sandbox)
    repeat_signature, repeats = None, 0
    public_task = task.problem_statement
    for step in range(limits["model_calls"]):
        remaining = limits["wall_seconds"] - (clock() - started)
        if remaining <= 0:
            status = "wall_budget"
            break
        try:
            request = context(system, public_task, history, ledger, limits["context_bytes"])
        except ValueError as error:
            write(directory / f"steps/{step:04d}-context.json", {"error": str(error)})
            status = "context_budget"
            break
        write(directory / f"steps/{step:04d}-request.json", request)
        calls += 1
        emit(observer, "model_request", f"{row['run_id']} · Schritt {step + 1}: Modell antwortet …",
             state="model_wait", active={"step": step, "operation": "model", "model_calls": calls,
                                         "tool_calls": tools},
             agent={"context": request, "action": None, "result": None, "response": None})
        before = clock()
        try:
            response = client.chat(messages=request, schema=schema, timeout=remaining)
        except AdapterError as error:
            usage.append(error.usage or {})
            write(directory / f"steps/{step:04d}-response.json", {"error": str(error), "status": error.status,
                                                               "raw": error.raw, "usage": error.usage})
            status = error.status
            emit(observer, "model_error", f"Modellaufruf: {error.status}", state="model_error",
                 agent={"response": {"error": str(error), "status": error.status}})
            if error.status == "invalid_output" and repairs < policy["repair_calls"]:
                repairs += 1
                ledger["action_error"] = str(error)[:1000]
                ledger["next"] = "Return one valid JSON action matching the schema. Keep it short."
                continue
            break
        status = "model_budget"
        ledger.pop("action_error", None)
        usage.append(response["usage"])
        write(directory / f"steps/{step:04d}-response.json", response)
        action = response["action"]
        emit(observer, "model_response", f"{row['run_id']} · {action['stage']}: {action['action']}",
             state="action", active={"stage": action["stage"], "operation": action["action"]},
             agent={"response": response, "action": action})
        if clock() - started >= limits["wall_seconds"]:
            status = "wall_budget"
            break
        if action["action"] == "submit":
            status = "submitted"
            break
        if tools >= limits["tool_calls"]:
            status = "tool_budget"
            break
        tools += 1
        emit(observer, "tool_started", f"Werkzeug läuft: {action['action']}", state="tool_wait",
             active={"tool_calls": tools})
        timeout = max(1, min(limits["command_seconds"], int(limits["wall_seconds"] - (clock() - started))))
        if action["action"] == "update_ledger":
            ledger.update({key: action[key] for key in ("hypothesis", "next", "files")})
            result = {"status": "completed", "updated": True}
        else:
            result = execute(manager, sandbox, action, timeout, limits["output_chars"])
        write(directory / f"steps/{step:04d}-tool.json", {"action": action, "result": result,
                                                         "elapsed_seconds": clock() - before})
        visible = dict(result)
        visible.pop("junit_xml", None)
        emit(observer, "tool_result", f"{action['action']}: {result.get('observation', result['status'])}",
             state="tool_result", agent={"result": visible})
        if action["action"] in {"write_file", "delete_file", "replace_text", "run_tests"}:
            workspace_patch = patch(manager, sandbox)
            (directory / f"steps/{step:04d}.patch").write_text(workspace_patch, encoding="utf-8")
        if "observation" in result:
            observations.append({"step": step, "stage": action["stage"], "observation": result["observation"],
                                 "targets": action["targets"], "workspace_sha256": identity(workspace_patch)})
        history.append([{"role": "assistant", "content": json.dumps(action)},
                        {"role": "user", "content": json.dumps(visible)}])
        event = {"action": action, "result": visible, "workspace_sha256": identity(workspace_patch)}
        events.append(event)
        signature = event_signature(event)
        repeats = repeats + 1 if signature == repeat_signature else 1
        repeat_signature = signature
        directive = progress(events, policy["repeat_limit"])
        hints = {
            "redirect": "No new evidence: narrow the search, read a located file, or change the implementation.",
            "repair_test": "Repair collection/import/syntax errors before treating this as behavioral red.",
            "implement": "Observed assertion red: implement the required behavior, then rerun this test.",
        }
        if directive in hints:
            ledger["feedback"] = hints[directive]
        else:
            ledger.pop("feedback", None)
        if action.get("path"):
            ledger["last_file"] = action["path"]
        if action.get("reason"):
            ledger["last_reason"] = action["reason"][:1000]
        if "observation" in result:
            ledger["last_test"] = {"targets": action.get("targets"), "observation": result["observation"]}
        write(directory / f"steps/{step:04d}-progress.json", {"directive": directive, "ledger": ledger})
        if repeats >= 2 * policy["repeat_limit"]:
            status = "stalled"
            break
    final = patch(manager, sandbox)
    (directory / "full.patch").write_text(final, encoding="utf-8")
    emit(observer, "agent_finished", f"Agentenschleife beendet: {status}",
         active={"agent_finished_at": time.time(), "operation": "evaluation"})
    return {"design_id": identity(design), "status": status, "model_calls": calls, "tool_calls": tools,
            "duration_seconds": clock() - started, "usage": usage,
            "test_observations": observations, "repairs": repairs, "ledger": ledger, "patch": final}
