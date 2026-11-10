# Review: format-registry

The extension contract requires one shared formatter registry for both preview and export. Adding a formatter must require one registry insertion, without separate edits to both call paths. Existing formatters may use compact lambdas; this is permitted.

Review the current source without modifying it. Evaluate criterion `shared_extension_point`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
