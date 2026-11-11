"""Run the same testguided action loop for both framework treatments."""

import json
import time

from ollama_agents.client import OllamaClient
from ollama_agents.errors import AdapterError

from .artifacts import write
from .design import SCHEMA, instruction
from .telemetry import emit
from .workspace import execute, patch


def messages(system, task, history, capacity):
    initial = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    size = len(json.dumps(initial, ensure_ascii=False).encode())
    kept = []
    for pair in reversed(history):
        addition = len(json.dumps(pair, ensure_ascii=False).encode())
        if size + addition > capacity:
            break
        kept[:0] = pair
        size += addition
    if (history and not kept) or size > capacity:
        raise ValueError("A complete task/tool exchange exceeds context_bytes")
    omitted = len(history) - len(kept) // 2
    if omitted:
        initial[1]["content"] += f"\n{omitted} older tool exchanges omitted; inspect current files as needed."
    return initial + kept


def develop(manager, sandbox, task, row, config, guides, directory, client=None, observer=None):
    limits, model = config["budgets"], config["ollama"]
    client = client or OllamaClient(endpoint=model["endpoint"], model=model["model"],
                                    think=model["think"], options={
                                        key: model[key] for key in ("temperature", "num_ctx", "num_predict")
                                    } | {"seed": row["seed"]})
    started = time.monotonic()
    emit(observer, "agent_started", "Agentenschleife gestartet", active={"agent_started_at": time.time()})
    history, usage, observations = [], [], []
    status, calls, tools = "model_budget", 0, 0
    system = instruction(row["mode"], guides)
    public_task = task.problem_statement
    for step in range(limits["model_calls"]):
        remaining = limits["wall_seconds"] - (time.monotonic() - started)
        if remaining <= 0:
            status = "wall_budget"
            break
        try:
            request = messages(system, public_task, history, limits["context_bytes"])
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
        before = time.monotonic()
        try:
            response = client.chat(messages=request, schema=SCHEMA, timeout=remaining)
        except AdapterError as error:
            usage.append(error.usage or {})
            write(directory / f"steps/{step:04d}-response.json", {"error": str(error), "status": error.status,
                                                               "raw": error.raw, "usage": error.usage})
            status = error.status
            emit(observer, "model_error", f"Modellaufruf: {error.status}", state="model_error",
                 agent={"response": {"error": str(error), "status": error.status}})
            break
        usage.append(response["usage"])
        write(directory / f"steps/{step:04d}-response.json", response)
        action = response["action"]
        emit(observer, "model_response", f"{row['run_id']} · {action['stage']}: {action['action']}",
             state="action", active={"stage": action["stage"], "operation": action["action"]},
             agent={"response": response, "action": action})
        if time.monotonic() - started >= limits["wall_seconds"]:
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
        timeout = max(1, min(limits["command_seconds"], int(limits["wall_seconds"] - (time.monotonic() - started))))
        result = execute(manager, sandbox, action, timeout, limits["output_chars"])
        write(directory / f"steps/{step:04d}-tool.json", {"action": action, "result": result,
                                                         "elapsed_seconds": time.monotonic() - before})
        visible = dict(result)
        visible.pop("junit_xml", None)
        emit(observer, "tool_result", f"{action['action']}: {result.get('observation', result['status'])}",
             state="tool_result", agent={"result": visible})
        if action["action"] in {"write_file", "delete_file", "run_tests"}:
            (directory / f"steps/{step:04d}.patch").write_text(patch(manager, sandbox), encoding="utf-8")
        if "observation" in result:
            observations.append({"step": step, "stage": action["stage"], "observation": result["observation"]})
        history.append([{"role": "assistant", "content": json.dumps(action)},
                        {"role": "user", "content": json.dumps(visible)}])
    final = patch(manager, sandbox)
    (directory / "full.patch").write_text(final, encoding="utf-8")
    emit(observer, "agent_finished", f"Agentenschleife beendet: {status}",
         active={"agent_finished_at": time.time(), "operation": "evaluation"})
    return {"status": status, "model_calls": calls, "tool_calls": tools,
            "duration_seconds": time.monotonic() - started, "usage": usage,
            "test_observations": observations, "patch": final}
