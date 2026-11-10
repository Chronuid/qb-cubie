"""Track episode deadlines, independent internal call limits and per-phase token usage."""

import math
import time

from .errors import AdapterError, infrastructure
from .jsonio import token_count


class BudgetLedger:
    """Keep one conservative episode clock across all phases and repair attempts."""

    _input: int | None
    _output: int | None

    def __init__(self, *, wall_time_seconds, max_model_calls, max_tool_calls,
                 reserve_seconds, clock=time.monotonic):
        _duration(wall_time_seconds, "wall time", positive=True)
        _duration(reserve_seconds, "runner reserve")
        self._limits = {"model": _limit(max_model_calls), "tool": _limit(max_tool_calls)}
        self._calls = {"model": 0, "tool": 0}
        self._clock = clock
        self._started = _duration(clock(), "clock origin", signed=True)
        self._last = self._started
        self._duration, self._reserve = wall_time_seconds, reserve_seconds
        self.begin_phase()

    def claim_model(self):
        """Reserve one model invocation and return its remaining time allowance."""
        return self._claim("model")

    def claim_tool(self):
        """Reserve one local tool invocation and return its remaining time allowance."""
        return self._claim("tool")

    def record_usage(self, *, input_tokens, output_tokens):
        """Accumulate observed tokens without converting unknown measurements to zero."""
        incoming = token_count(input_tokens)
        outgoing = token_count(output_tokens)
        self._input = _sum(self._input, incoming)
        self._output = _sum(self._output, outgoing)

    def usage(self):
        """Return an independent snapshot of measured phase usage and unknown cost."""
        return {"input_tokens": self._input, "output_tokens": self._output, "cost": None}

    def begin_phase(self):
        """Reset only phase usage while preserving episode counters and deadline."""
        self._input, self._output = 0, 0

    def _claim(self, kind):
        """Check both remaining episode time and the selected internal call limit."""
        now = _duration(self._clock(), "episode clock", signed=True)
        if now < self._last:
            raise infrastructure("Episode clock must be monotonic")
        self._last = now
        remaining = self._duration - (now - self._started) - self._reserve
        if remaining <= 0:
            raise AdapterError("budget_exceeded", "Episode time budget exhausted; runner reserve reached")
        if self._calls[kind] >= self._limits[kind]:
            raise AdapterError("budget_exceeded", f"Internal {kind} call budget limit reached")
        self._calls[kind] += 1
        return remaining


def _duration(value, name, *, positive=False, signed=False):
    """Validate finite duration and clock configuration without boolean coercion."""
    if type(value) not in (int, float) or not math.isfinite(value):
        raise infrastructure(f"Invalid {name}: a finite number is required")
    if not signed and (value < 0 or (positive and value == 0)):
        raise infrastructure(f"Invalid {name}: {'positive' if positive else 'nonnegative'} value required")
    return value


def _limit(value):
    """Validate a nonnegative integer internal call limit."""
    if type(value) is not int or value < 0:
        raise infrastructure("Internal call limit must be a nonnegative integer")
    return value


def _sum(previous, current):
    """Keep an aggregate unknown after any unknown component observation."""
    return None if previous is None or current is None else previous + current
