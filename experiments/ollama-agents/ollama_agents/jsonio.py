"""Serialize deterministic JSON and reject ambiguous provider data."""

import base64
import hashlib
import json
import math

from .errors import invalid


def encode(value):
    """Encode deterministic UTF-8 JSON without nonfinite numbers."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, default=_binary).encode("utf-8")


def decode(body):
    """Decode strict UTF-8 JSON with unique object keys and finite numbers."""
    try:
        text = body.decode("utf-8") if isinstance(body, bytes) else body
        result = json.loads(text, object_pairs_hook=_unique, parse_constant=_constant,
                            parse_float=_float)
        encode(result)  # Reject lone Unicode surrogates before discarding the original wire bytes.
        return result
    except (ValueError, TypeError, RecursionError) as error:
        raise invalid(f"Invalid JSON response or UTF-8 encoding: {error}") from error


def digest(body):
    """Return the SHA-256 identity of exact bytes."""
    return hashlib.sha256(body).hexdigest()


def token_count(value):
    """Validate an optional nonnegative integer token measurement."""
    if value is not None and (type(value) is not int or value < 0):
        raise invalid("Invalid token count in usage; expected a nonnegative integer or null")
    return value


def _unique(pairs):
    """Reject repeated keys before a JSON object loses information."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value):
    """Reject the nonfinite constants accepted by the default JSON decoder."""
    raise ValueError(f"Nonfinite JSON constant: {value}")


def _float(value):
    """Reject finite JSON literals whose decoded value would overflow."""
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Nonfinite JSON number: {value}")
    return result


def _binary(value):
    """Preserve malformed raw response bytes losslessly in evidence JSON."""
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}
    raise TypeError(f"Unsupported JSON evidence value: {type(value).__name__}")
