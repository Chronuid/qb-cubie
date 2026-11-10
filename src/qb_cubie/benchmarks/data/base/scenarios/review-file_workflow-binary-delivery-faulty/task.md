# Review: binary-delivery

delivery.emit(destination, payloads) accepts a fresh output directory and a mapping of simple stem names to bytes. Create exactly one <stem>.bin per payload, preserve binary bytes exactly and return None. Empty input creates an empty directory. Filenames are defined by layout.filename.

Review the current source without modifying it. Evaluate criterion `exact_binary_tree`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
