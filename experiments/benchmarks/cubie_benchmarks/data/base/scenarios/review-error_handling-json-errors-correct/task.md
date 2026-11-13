# Review: json-errors

parser.parse(text) returns json.loads(text). Invalid JSON must raise ValueError; valid JSON null and {} are legitimate results and must be preserved.

Review the current source without modifying it. Evaluate criterion `invalid_input_visible`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
