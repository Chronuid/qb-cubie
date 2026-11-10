# Review: scanner-failure

scanner.scan(callback) returns the callback result on success. OSError raised by the diagnostic tool must propagate. An empty successful result is allowed; missing observations must never become a successful empty diagnostics list.

Review the current source without modifying it. Evaluate criterion `tool_failure_visible`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
