# Review: source-preservation

report.publish(source, output) copies source bytes to output/report.txt, creates output if absent, returns None and preserves source bytes. Source and output are distinct paths. Empty and non-UTF-8 contents are valid.

Review the current source without modifying it. Evaluate criterion `preserve_source`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
