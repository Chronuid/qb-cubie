"""Bounded corrections, classified interruptions, usage and separate evidence."""

import json
import urllib.error

import pytest

from .checks import completed, interrupted, records
from .support import report, response, setup_session, submit


def malformed():
    return response(submit(report()), message={"role": "assistant", "content": "not-json"})


def test_one_correction_keeps_failed_evidence_and_sums_model_usage(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    adapter, transport, writer = setup_session(api, reviewer_api, root, tmp_path, [malformed(), response(submit(report()))])
    event = completed(adapter, root, report())
    assert event["usage"] == {"input_tokens": 26, "output_tokens": 14, "cost": None}
    assert len(transport.requests) == 2
    correction = json.loads(transport.requests[1][0].data)
    assert "json" in json.dumps(correction["messages"]).lower()
    steps = records(writer, tmp_path)
    assert any(step["status"] == "invalid_output" and step["raw_response"] == malformed() for step in steps)
    assert any(step["status"] == "completed" and step["action"] == submit(report()) for step in steps)


def test_criterion_validation_errors_are_given_to_the_single_correction(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    invalid = report()
    del invalid["criterion_results"]["unicode_preserved"]
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(submit(invalid)), response(submit(report()))])
    completed(adapter, root, report())
    messages = json.loads(transport.requests[1][0].data)["messages"]
    assert "unicode_preserved" in messages[-1]["content"] or "criteri" in messages[-1]["content"].lower()


def test_second_invalid_response_ends_without_third_model_call(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [malformed(), malformed()])
    interrupted(adapter, root, "invalid_output")
    assert len(transport.requests) == 2


@pytest.mark.parametrize("error,status", [(TimeoutError("replay timeout"), "agent_timeout"),
                                        (urllib.error.URLError("offline provider failure"), "infrastructure_error")])
def test_transport_failures_are_not_abstention_or_completed_review(api, reviewer_api, review_workspace, tmp_path, error, status):
    root = review_workspace()
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [error])
    interrupted(adapter, root, status)
    assert len(transport.requests) == 1


def test_length_abort_is_not_accepted_even_if_json_is_complete(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    reply = response(submit(report()), done_reason="length")
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [reply, reply])
    interrupted(adapter, root, "invalid_output")
    assert len(transport.requests) <= 2


def test_repair_is_charged_to_the_same_model_budget(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [malformed()], max_model_calls=1)
    interrupted(adapter, root, "budget_exceeded")
    assert len(transport.requests) == 1


def test_tool_loop_exhaustion_is_not_completed_abstention(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    action = {"action": "read_file", "path": "escaping.py"}
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(action)] * 6)
    interrupted(adapter, root, "budget_exceeded")
    assert len(transport.requests) == 6


def test_internal_tool_budget_is_independent_of_model_budget(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    action = {"action": "read_file", "path": "escaping.py"}
    adapter, transport, _ = setup_session(api, reviewer_api, root, tmp_path, [response(action)] * 2, max_tool_calls=1)
    interrupted(adapter, root, "budget_exceeded")
    assert len(transport.requests) <= 2


def test_unknown_token_measurement_remains_null_in_completed_event(api, reviewer_api, review_workspace, tmp_path):
    root = review_workspace()
    reply = response(submit(report()))
    del reply["prompt_eval_count"]
    adapter, _, _ = setup_session(api, reviewer_api, root, tmp_path, [malformed(), reply])
    event = completed(adapter, root, report())
    assert event["usage"] == {"input_tokens": None, "output_tokens": 14, "cost": None}


def test_review_method_keeps_stdout_free_for_jsonl(api, reviewer_api, review_workspace, tmp_path, capsys):
    root = review_workspace()
    adapter, _, writer = setup_session(api, reviewer_api, root, tmp_path, [response(submit(report()))])
    completed(adapter, root, report())
    records(writer, tmp_path)
    output = capsys.readouterr()
    assert output.out == "" and len(output.err.encode()) < 65536
