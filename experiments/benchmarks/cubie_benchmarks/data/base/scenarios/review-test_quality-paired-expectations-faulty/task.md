# Review: paired-expectations

routing_checks.accepts(candidate) validates correlated mappings A -> east and B -> west. It must accept the correct function and reject a function returning east for B and west for A. Expectations belong to their input; a result merely appearing anywhere in the expected set is insufficient.

Review the current source without modifying it. Evaluate criterion `correlated_pairs`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
