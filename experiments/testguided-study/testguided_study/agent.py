"""Run the same testguided action loop for both framework treatments."""

import json
import time
from itertools import count

from ollama_agents.client import OllamaClient
from ollama_agents.errors import AdapterError

from .analysis import Analysis
from .artifacts import read, write
from .controller import (
    Controller,
    compact_observation,
    context_capacity,
    session_context,
)
from .design import default_design, design_instruction, design_schema
from .iteration import compose, context, identity, progress
from .telemetry import emit
from .workspace import bounded, execute, patch


def test_details(directory, action, current_step, limit):
    """Read only earlier public tool results, never evaluator/private artifacts."""
    step, start = action['step'] - 1, action['start']
    if not 0 <= step < current_step or start < 0:
        return {'status': 'tool_error', 'error': 'Choose an earlier test step and a nonnegative error offset.'}
    path = directory / f'steps/{step:04d}-tool.json'
    if not path.is_file():
        return {'status': 'tool_error', 'error': 'No test evidence at this step.'}
    result = read(path)['result']
    if 'diagnostics' not in result:
        return {'status': 'tool_error', 'error': 'This step did not produce test diagnostics.'}
    errors = result['diagnostics'].get('errors', [])
    # Each diagnostic is bounded at creation. One error per page preserves full
    # messages/trace tails without allowing another large mandatory exchange.
    return bounded({'step': step + 1, 'start': start, 'hits': errors[start:start + 1],
                    'next_start': start + 1 if start + 1 < len(errors) else None,
                    'diagnostic_counts': result['diagnostics'].get('counts', {})}, limit)


def messages(system, task, history, capacity):
    return context(system, task, history, {}, capacity)


def develop(manager, sandbox, task, row, config, guides, directory, client=None, observer=None, design=None, clock=None,
            visible_baseline=None):
    clock = clock or time.monotonic
    design = design or default_design(row["mode"], guides)
    design = compose(design["core"], design["specialization"])
    if design["specialization"]["mode"] != row["mode"]:
        raise ValueError("Design specialization does not match run mode")
    if row.get("design_id", identity(design)) != identity(design):
        raise ValueError("Design identity does not match frozen run")
    if design['core']['context']['version'] in (6, 7, 8, 9):
        from .team_agent import develop as develop_team
        return develop_team(manager, sandbox, task, row, config, guides, directory,
                            client=client, observer=observer, design=design, clock=clock,
                            visible_baseline=visible_baseline)
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
    status, calls, tools = "running", 0, 0
    system = design_instruction(design)
    ledger, events, repairs = {}, [], 0
    if visible_baseline is not None:
        write(directory / 'visible-baseline.json', visible_baseline)
        ledger['visible_baseline'] = compact_observation(visible_baseline, 3000)
        ledger['visible_baseline']['scope'] = 'Original visible suite before any agent or private patch; existing failures are not new regressions.'
    workspace_patch = patch(manager, sandbox)
    v3 = design["core"]["context"]["version"] >= 3
    v4 = design["core"]["context"]["version"] >= 4
    v5 = design["core"]["context"]["version"] == 5
    analysis = Analysis() if v5 else None
    recovering = False
    controller = Controller(policy["repeat_limit"], local_edits=v4)
    capacity = context_capacity(limits, model, schema) if v3 else limits["context_bytes"]
    versions = {}
    if v3 and manager is not None:
        ledger["repository"] = execute(manager, sandbox, {"action": "overview"}, 10, 4000)
        versions = execute(manager, sandbox, {"action": "snapshot"}, 10, 1000)
        write(directory / "initial-evidence.json", {"repository": ledger["repository"], "versions": versions})
    public_task = task.problem_statement
    for step in count():
        remaining = limits["wall_seconds"] - (clock() - started)
        if remaining <= 0:
            status = "wall_budget"
            break
        try:
            if analysis:
                ledger["analysis"] = {"pending": analysis.pending, "reviewed": analysis.reviewed,
                                      "records": analysis.records}
            if v3:
                ledger["evidence"] = controller.facts
            request = (session_context if v3 else context)(system, public_task, history, ledger, capacity)
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
        remaining = limits['wall_seconds'] - (before - started)
        if remaining <= 0:
            status = 'wall_budget'
            break
        try:
            active_schema = analysis.schema(schema) if analysis else schema
            if recovering:
                active_schema = {"oneOf": [entry for entry in schema["oneOf"]
                                          if entry["properties"]["action"]["const"] == "read_file"]}
            response = client.chat(messages=request, schema=active_schema, timeout=remaining)
        except AdapterError as error:
            usage.append(error.usage or {})
            rejected = {"error": str(error), "status": error.status, "raw": error.raw, "usage": error.usage}
            write(directory / f"steps/{step:04d}-response.json", rejected)
            status = error.status
            emit(observer, "model_error", f"Modellaufruf: {error.status}", state="model_error",
                 agent={"response": rejected, "last_error": {**rejected, 'step': step + 1}})
            if error.status in {"invalid_output", "agent_timeout"}:
                repairs += 1
                ledger["action_error"] = str(error)[:1000]
                ledger["next"] = "Return one valid JSON action matching the schema. Keep it short."
                if isinstance(error.raw, dict) and error.raw.get('done_reason') == 'length':
                    ledger['next'] = ('Output was truncated at the token limit. Return a short read action or a small edit '
                                      'with replace_text. Do not repeat a full file or long comments. Return complete JSON.')
                recovering = v4
                if recovering:
                    ledger["next"] = "Recovery schema: return one short read_file action for a relevant source or test file."
                continue
            break
        recovering = False
        status = "running"
        ledger.pop("action_error", None)
        usage.append(response["usage"])
        write(directory / f"steps/{step:04d}-response.json", response)
        action = response["action"]
        if v3 and action.get("note"):
            ledger["note"] = action["note"]
        emit(observer, "model_response", f"{row['run_id']} · {action['stage']}: {action['action']}",
             state="action", active={"stage": action["stage"], "operation": action["action"]},
             agent={"response": response, "action": action})
        if clock() - started >= limits["wall_seconds"]:
            status = "wall_budget"
            break
        if action["action"] == "submit":
            status = "submitted"
            break
        tools += 1
        emit(observer, "tool_started", f"Werkzeug läuft: {action['action']}", state="tool_wait",
             active={"tool_calls": tools})
        timeout = max(0.001, limits["wall_seconds"] - (clock() - started))
        executed_action = controller.bind_edit(action) if v4 else action
        if action["action"] == "analyze" and analysis:
            result = analysis.analyze(action)
        elif action["action"] == "update_ledger":
            ledger.update({key: action[key] for key in ("hypothesis", "next", "files")})
            result = {"status": "completed", "updated": True}
        elif action['action'] == 'read_test_details':
            result = test_details(directory, action, step, limits['output_chars'])
        else:
            result = controller.guard(action) if v3 else None
            if result is None:
                result = execute(manager, sandbox, executed_action,
                                 timeout, limits["output_chars"])
        previous_versions = versions
        if v3 and manager is not None:
            versions = execute(manager, sandbox, {"action": "snapshot"}, min(timeout, 10), 1000)
        if (v3 and previous_versions.get("production") and
                previous_versions.get("production") != versions.get("production") and
                controller.metrics["first_production_change_call"] is None):
            controller.metrics["first_production_change_call"] = calls
        if analysis:
            analysis.observe(action, result)
        if v3:
            controller.observe(action, result, versions, calls)
        write(directory / f"steps/{step:04d}-tool.json", {"action": action, "result": result,
                                                         "executed_action": executed_action,
                                                         "elapsed_seconds": clock() - before})
        visible = compact_observation(result, min(6000, limits['output_chars'])) if v3 else dict(result)
        if v3 and 'diagnostics' in result:
            visible['details'] = {'action': 'read_test_details', 'step': step + 1, 'start': 0}
        visible.pop("junit_xml", None)
        emit(observer, "tool_result", f"{action['action']}: {result.get('observation', result['status'])}",
             state="tool_result", agent={"result": visible})
        if action["action"] in {"write_file", "delete_file", "replace_text", "run_tests"}:
            workspace_patch = patch(manager, sandbox)
            (directory / f"steps/{step:04d}.patch").write_text(workspace_patch, encoding="utf-8")
        if "observation" in result:
            observations.append({"step": step, "stage": action["stage"], "observation": result["observation"],
                                 "targets": action["targets"], "workspace_sha256": identity(workspace_patch),
                                 **versions, "baseline": result.get("baseline", False),
                                 "collection_only": result.get("collection_only", False)})
        history.append([{"role": "assistant", "content": json.dumps(action)},
                        {"role": "user", "content": json.dumps(visible)}])
        event = {"action": action, "result": visible, "workspace_sha256": identity(workspace_patch)}
        events.append(event)
        directive = progress(events, policy["repeat_limit"])
        hints = {
            "redirect": "No new evidence: narrow the search, read a located file, or change the implementation.",
            "repair_test": "Repair collection/import/syntax errors before treating this as behavioral red.",
            "implement": "Observed assertion red: implement the required behavior, then rerun this test.",
        }
        if analysis and analysis.pending:
            hints["implement"] = "Analyze the failing observation before choosing a repair. Assertion red alone does not establish the cause."
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
    final = patch(manager, sandbox)
    (directory / "full.patch").write_text(final, encoding="utf-8")
    emit(observer, "agent_finished", f"Agentenschleife beendet: {status}",
         state='agent_finished', agent={'stop_reason': status},
         active={"agent_finished_at": time.time(), "operation": "evaluation"})
    return {"design_id": identity(design), "status": status, "model_calls": calls, "tool_calls": tools,
            "duration_seconds": clock() - started, "usage": usage,
            "test_observations": observations, "repairs": repairs, "ledger": ledger, "patch": final,
            "process_metrics": controller.metrics if v3 else {}, "final_versions": versions,
            "context_policy": {"capacity_bytes": capacity, "token_measurement": "provider_usage",
                               "estimate": "two_utf8_bytes_per_token" if v3 else "bytes_only"}}
