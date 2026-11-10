# Review: service-policy

The required maintenance contract is a single pricing policy: adding one service or changing its rate must require editing exactly one policy table, shared by quote and invoice APIs. Evaluate the number of policy edits for a new service; no behavior or style change beyond this requirement is requested.

Review the current source without modifying it. Evaluate criterion `single_pricing_policy`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
