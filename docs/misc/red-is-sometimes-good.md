The v0.0.7 Release is from DocFrame. I've mutated the README.md by hand. CI on Github said: 
```text

10m 25s
Run uv run --no-sync python -m pytest -m "" -q
........................................................................ [  4%]
.................s......................F............................... [  9%]
........................................................................ [ 14%]
........................................................................ [ 19%]
........................................................................ [ 24%]
........................................................................ [ 29%]
........................................................................ [ 34%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 49%]
........................................................................ [ 54%]
........................................................................ [ 59%]
........................................................................ [ 64%]
........................................................................ [ 69%]
.............................................................s..s..s..s. [ 74%]
.s..s................................................................... [ 79%]
.....................................s..s..s..s......................... [ 84%]
........................................................................ [ 89%]
........................................................................ [ 94%]
........................................................................ [ 99%]
....                                                                     [100%]
=================================== FAILURES ===================================
___________________________ test_docs_code_examples ____________________________

    def test_docs_code_examples() -> None:
        """Verifies that all documentation code examples and frames follow Cubie conventions."""
        DocEnsurance(
            pattern=(CUBIE_DOC_STYLE, CUBIE_DOC_FRAME_1, CUBIE_DOC_FRAME_2, CUBIE_DOC_FRAME_3),
            rules=(CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES),
            excludes=(
                ".pytest_cache",
                "tests",
                "experiments",  # Reason: I need to clean up the artifacts of the sprint in the core first.
                "GUTACHTEN.md",  # Reason: No Cubie-Rules apply to Inspectors.
                "CHANGELOG.md",
            ),
>       ).run()
          ^^^^^
E       AssertionError: 
E       --- Service Report (/home/runner/work/qb-cubie/qb-cubie) ---
E       - [DOCFRAME-OUTDATED] /home/runner/work/qb-cubie/qb-cubie/README.md:1: Frame zone 'head' (CUBIE_DOC_FRAME_1) is out of sync; run DocFrame.update().

tests/test_styleguide.py:120: AssertionError
=============================== warnings summary ===============================
tests/tests_ebt/test_ebt_ignores.py::test_standard_fs_critical_red
tests/tests_ebt/test_ebt_ignores.py::test_custom_fs_ignores_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignore_deep_directory_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignores_with_forall_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignores_with_expect_false_red
  /home/runner/work/qb-cubie/qb-cubie/src/qb_cubie/arenas/tempfs.py:66: UserWarning: TempFS is not intended for venv or side-package isolation; use PyVenv instead.
    warnings.warn("TempFS is not intended for venv or side-package isolation; use PyVenv instead.")

tests/tests_ebt/test_ebt_imports.py::test_import_rehydration_instance[PyVenv]
  /home/runner/work/qb-cubie/qb-cubie/src/qb_cubie/arenas/codecs.py:102: UserWarning: It is strongly recommended to use stateless static methods or classmethods. Instance rehydration via IPC is experimental and may fail for complex objects.
    return cls._extract_instance(target)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_styleguide.py::test_docs_code_examples - AssertionError: 
--- Service Report (/home/runner/work/qb-cubie/qb-cubie) ---
- [DOCFRAME-OUTDATED] /home/runner/work/qb-cubie/qb-cubie/README.md:1: Frame zone 'head' (CUBIE_DOC_FRAME_1) is out of sync; run DocFrame.update().
1 failed, 1432 passed, 11 skipped, 6 warnings in 622.12s (0:10:22)
Error: Process completed with exit code 1.
```
Red is sometimes good.
