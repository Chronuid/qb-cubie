# configuration-package: initial

Merge UTF-8 JSON objects from source/<layer>/*.json into destination/<basename>.json. Traverse relative input paths lexicographically; later values override earlier values for the same key of the same basename. Distinct basenames remain distinct outputs. Merging is shallow. Write canonical JSON (sorted keys, compact separators, terminal LF, non-ASCII characters escaped using JSON Unicode escapes) and exactly these output files. Empty source produces an empty output directory. Return None. Do not overwrite or remove inputs.

Public API: `config_bundle.merge_packages(source, destination, priority=None, schema=None)`. Preserve the input material. Deliver production code, executable tests and a short README. Submit tests before implementation; demonstrate business red, then green, then refactor without weakening the frozen tests. Return types and the complete specified output tree are part of acceptance.
