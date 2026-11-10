"""Use actual EBT traces for both accepted operations and classified failures."""

import re

from ..benchmarks.contracts import accepted


def failed(target, *, status, match):
    def observe():
        try:
            target()
        except ValueError as error:
            return {"status": getattr(error, "status", None), "reason": str(error)}
        return {"status": "unexpected_success", "reason": "operation was accepted"}
    return accepted(observe, expected={
        "status": status, "reason": re.compile(rf".*(?:{match}).*", re.IGNORECASE | re.DOTALL),
    })
