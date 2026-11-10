"""Build explicit, source-bound visible contexts without silent truncation."""

from .errors import AdapterError, infrastructure, invalid
from .jsonio import digest, encode
from .paths import names


class ContextBuilder:
    """Read only policy-granted files and enforce a deterministic context byte budget."""

    def __init__(self, *, policy):
        self._policy = policy

    def inventory(self):
        """Return the sorted visible file inventory with freshly observed hashes."""
        return [{"path": name, "sha256": digest(self._policy.read_file(name))}
                for name in sorted(self._policy.readable)]

    def build(self, *, paths, max_bytes, prompt_bytes, output_reserve_bytes):
        """Return a complete selected context or report explicit budget exhaustion."""
        _capacity(max_bytes, prompt_bytes, output_reserve_bytes)
        if prompt_bytes + output_reserve_bytes > max_bytes:
            raise AdapterError("budget_exceeded", "Prompt and output reserve exceed context capacity")
        files: list[dict] = []
        result = {"files": files, "truncated": False}
        for name in sorted(names(paths)):
            files.append(self._block(name))
            _fits(result, max_bytes - prompt_bytes - output_reserve_bytes)
        _fits(result, max_bytes - prompt_bytes - output_reserve_bytes)
        return result

    def _block(self, name):
        """Bind the hash and decoded text to the same freshly read source bytes."""
        body = self._policy.read_file(name)
        try:
            text = body.decode("utf-8")
        except UnicodeError as error:
            raise invalid(f"Invalid UTF-8 source encoding for {name}: {error}") from error
        return {"path": name, "sha256": digest(body), "content": text}


def _capacity(*values):
    """Require explicit nonnegative integer byte limits and reserves."""
    if any(type(value) is not int or value < 0 for value in values):
        raise infrastructure("Context capacity and reserves must be nonnegative integer byte counts")


def _fits(result, capacity):
    """Reject overflow including context metadata without changing selected content."""
    if len(encode(result)) > capacity:
        raise AdapterError("budget_exceeded", "Context capacity exceeded; no silent truncation allowed")
