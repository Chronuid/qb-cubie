"""Call Ollama once with an explicit schema and retain invalid-response evidence."""

import copy
import http.client
import math
import urllib.error
import urllib.parse
import urllib.request

from .errors import AdapterError, infrastructure, invalid
from .jsonio import decode, encode, token_count
from .schema import check_schema, validate

MAX_RESPONSE_BYTES = 32 * 1024 * 1024


class OllamaClient:
    """Perform bounded nonstreaming inference against one configured model."""

    def __init__(self, *, endpoint, model, options, think=False, transport=None):
        self._url = _endpoint(endpoint)
        if not isinstance(model, str) or not model or not isinstance(options, dict):
            raise infrastructure("Explicit model and options are required")
        if think is not None and type(think) is not bool:
            raise infrastructure("think must be a boolean or None when unsupported")
        self._model = model
        self._options = copy.deepcopy(options)
        self._think = think
        self._transport = transport if transport is not None else http_transport

    def chat(self, *, messages, schema, timeout):
        """Return a locally validated action, provider usage and raw response."""
        _timeout(timeout)
        check_schema(schema)
        request = self._request(messages, schema)
        body = _exchange(self._transport, request, timeout)
        return self._response(body, schema)

    def _request(self, messages, schema):
        """Construct a nonstreaming JSON-schema request without altering caller data."""
        payload = {"model": self._model, "options": self._options, "messages": messages,
                   "format": schema, "stream": False}
        if self._think is not None:
            payload["think"] = self._think
        try:
            body = encode(payload)
        except (TypeError, ValueError, RecursionError) as error:
            raise infrastructure(f"Invalid chat request configuration: {error}") from error
        return urllib.request.Request(self._url, body, {"Content-Type": "application/json"}, method="POST")

    def _response(self, body, schema):
        """Preserve usable raw evidence and measurements when validation fails."""
        raw, usage = body, {"input_tokens": None, "output_tokens": None, "cost": None}
        try:
            raw = decode(body)
            usage = _usage(raw)
            action = self._action(raw, schema)
        except AdapterError as error:
            error.raw, error.usage = raw, usage
            raise
        return {"action": action, "usage": usage, "raw": raw}

    def _action(self, raw, schema):
        """Require a complete answer from the configured model before decoding its action."""
        if raw.get("model") != self._model:
            raise invalid("Response model does not match configured model")
        if raw.get("done") is not True or raw.get("done_reason") != "stop":
            raise invalid(f"Response is incomplete or has invalid stop reason: {raw.get('done_reason')}")
        message = raw.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            raise invalid("Response message must have assistant role")
        if not isinstance(message.get("content"), str):
            raise invalid("Response message content must be a JSON string")
        action = decode(message["content"])
        validate(action, schema, checked=True)
        return action


def http_transport(request, *, timeout):
    """Read one bounded HTTP response using the standard library."""
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise invalid("Provider response exceeds the byte limit")
    return body


def _exchange(transport, request, timeout):
    """Classify transport failures without retrying or switching providers."""
    try:
        return transport(request, timeout=timeout)
    except TimeoutError as error:
        raise AdapterError("agent_timeout", f"Provider timeout: {error}") from error
    except urllib.error.URLError as error:
        status = "agent_timeout" if isinstance(error.reason, TimeoutError) else "infrastructure_error"
        raise AdapterError(status, f"Provider transport failure: {error}") from error
    except OSError as error:
        raise infrastructure(f"Provider unavailable: {error}") from error
    except http.client.HTTPException as error:
        raise AdapterError("infrastructure_error", f"Incomplete provider HTTP response: {error}",
                           raw=getattr(error, "partial", None)) from error


def _endpoint(endpoint):
    """Require an explicit HTTP endpoint without embedded credentials or URL modifiers."""
    if not isinstance(endpoint, str):
        raise infrastructure("Ollama endpoint must be an HTTP URL")
    parsed = urllib.parse.urlsplit(endpoint)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise infrastructure("Ollama endpoint must be an HTTP URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise infrastructure("Ollama endpoint cannot contain credentials, query or fragment")
    return endpoint.rstrip("/") + "/api/chat"


def _timeout(value):
    """Reject expired or unbounded request deadlines before transport starts."""
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise AdapterError("agent_timeout", "HTTP timeout must be finite and positive")


def _usage(raw):
    """Extract measured provider token counts without supplying inferred values."""
    if not isinstance(raw, dict):
        raise invalid("JSON response must be an object")
    if "error" in raw:
        raise infrastructure(f"Provider error response: {raw['error']}")
    return {"input_tokens": token_count(raw.get("prompt_eval_count")),
            "output_tokens": token_count(raw.get("eval_count")), "cost": None}
