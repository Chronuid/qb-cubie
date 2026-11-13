# Document index: maintenance

Implement `indexer.build_index(source, output)`, returning None. Copy files byte-for-byte and produce `output/index.txt` listing relative POSIX paths in ascending lexicographic order, one per line. Preserve the source tree. Output contains exactly the copies and index.txt. Empty selection produces an empty index. The source does not contain index.txt.

Process subdirectories recursively. Include only files with the case-sensitive suffix `.txt`; preserve their relative paths.

Submit executable acceptance tests before implementation and observe a failure for the missing behavior. Preserve existing tests. A syntax/import error is not a valid red phase.
