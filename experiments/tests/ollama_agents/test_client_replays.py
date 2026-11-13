"""Reject malformed or incomplete Ollama output without model calls or silent repairs."""

import json

import pytest

from ..benchmarks.contracts import accepted
from .conftest import (
    ACTION,
    MESSAGES,
    OPTIONS,
    WRITE_SCHEMA,
    ReplayTransport,
    chat,
    client,
)
from .contracts import failed


def test_completed_schema_response_preserves_action_usage_and_raw_evidence(api, response, capsys):
    transport = ReplayTransport(response)
    adapter = client(api, transport)
    accepted(lambda: chat(adapter), expected={
        "action": ACTION, "usage": {"input_tokens": 13, "output_tokens": 7, "cost": None},
        "raw": response,
    })
    assert len(transport.requests) == 1
    request, timeout = transport.requests[0]
    payload = json.loads(request.data)
    assert request.full_url == "http://localhost:11434/api/chat"
    assert request.get_method() == "POST" and timeout == 4.5
    assert request.get_header("Content-type") == "application/json"
    assert payload == {"model": "gemma4:12b", "messages": MESSAGES, "format": WRITE_SCHEMA,
                       "stream": False, "think": False, "options": OPTIONS}
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("body", [b"not json", b"{} trailing", b"[]", b"null", b"\xff"],
                         ids=["non-json", "trailing-garbage", "array", "null", "invalid-utf8"])
def test_malformed_envelopes_are_invalid_output_without_implicit_retry(api, body):
    transport = ReplayTransport(body)
    failed(lambda: chat(client(api, transport)), status="invalid_output", match="json|response|encoding|utf")
    assert len(transport.requests) == 1


@pytest.mark.parametrize("change", [
    {"done": False}, {"done_reason": "length"}, {"done_reason": "unexpected"},
    {"message": {}}, {"message": {"role": "assistant", "content": {"files": {}}}},
    {"message": {"role": "user", "content": "{}"}}, {"model": "another-model"},
], ids=["unfinished", "length-even-with-valid-json", "unknown-stop-reason", "missing-content",
        "content-not-string", "wrong-role", "silent-model-switch"])
def test_incomplete_or_foreign_response_cannot_be_submitted(api, response, change):
    response.update(change)
    transport = ReplayTransport(response)
    failed(lambda: chat(client(api, transport)), status="invalid_output",
           match="done|complet|length|stop|message|content|role|model")
    assert len(transport.requests) == 1


@pytest.mark.parametrize("content", [
    '{"files":', '```json\n{"files":{"src/fee.py":"pass"}}\n```',
    '{}', '{"files":{}}', '{"files":[]}', '{"files":{"src/fee.py":12}}',
    '{"files":{"src/fee.py":"pass"},"shell":"rm -rf ."}',
    '{"files":{"src/fee.py":"first"},"files":{"src/fee.py":"second"}}',
    '{"files":{"src/fee.py":NaN}}',
], ids=["truncated-json", "markdown-wrapper", "required-field", "empty-write", "wrong-container",
        "wrong-file-type", "unknown-action", "duplicate-key", "nonfinite-json"])
def test_schema_failures_are_not_repaired_by_stripping_or_coercion(api, response, content):
    response["message"]["content"] = content
    transport = ReplayTransport(response)
    failed(lambda: chat(client(api, transport)), status="invalid_output",
           match="json|schema|files|field|duplicate|propert|finite")
    assert len(transport.requests) == 1


@pytest.mark.parametrize("error,status", [
    (TimeoutError("read deadline exceeded"), "agent_timeout"),
    (OSError("provider unavailable"), "infrastructure_error"),
])
def test_transport_failures_remain_distinct_from_model_format_failures(api, error, status):
    transport = ReplayTransport(error)
    failed(lambda: chat(client(api, transport)), status=status, match="deadline|timeout|provider|unavailable")
    assert len(transport.requests) == 1


def test_missing_token_measurements_are_null_and_not_zero(api, response):
    response.pop("prompt_eval_count")
    response.pop("eval_count")
    accepted(lambda: chat(client(api, ReplayTransport(response))), expected={
        "action": ACTION, "usage": {"input_tokens": None, "output_tokens": None, "cost": None},
        "raw": response,
    })


@pytest.mark.parametrize("count", [-1, True, "13", 1.5])
def test_invalid_token_counts_are_not_coerced_into_measurements(api, response, count):
    response["prompt_eval_count"] = count
    failed(lambda: chat(client(api, ReplayTransport(response))), status="invalid_output", match="token|count|usage")


@pytest.mark.parametrize("timeout", [0, -1])
def test_expired_timeout_prevents_transport_start(api, response, timeout):
    transport = ReplayTransport(response)
    adapter = client(api, transport)
    failed(lambda: adapter.chat(messages=MESSAGES, schema=WRITE_SCHEMA, timeout=timeout),
           status="agent_timeout", match="time|deadline")
    assert transport.requests == []
