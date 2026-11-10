# document-index: maintenance

Copy all recursive regular .txt files (case sensitive) from source to destination/files/<relative-path>, preserving bytes. Preserve nested relative paths. Exclude files when fnmatchcase(relative_POSIX_path, pattern) matches any entry of the optional exclude collection. The default collection is empty. Write destination/index.txt containing sorted POSIX relative names with one LF per name. Empty source produces index.txt with empty content. No extra output files are allowed. Return None and preserve the complete input tree.

Public API: `document_catalog.build_catalog(source, destination, exclude=())`. Preserve the input material. Deliver production code, executable tests and a short README. Submit tests before implementation; demonstrate business red, then green, then refactor without weakening the frozen tests. Return types and the complete specified output tree are part of acceptance.
