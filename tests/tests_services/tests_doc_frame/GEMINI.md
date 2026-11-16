(qb-cubie) symphonie@symphonie:~/PycharmProjects/cubie$ make test-all
.venv/bin/python -m pytest -m "" --hypothesis-profile=ci -q
.........................................................................................s........................................................................................................................................... [ 15%]
..................................................................................................................................................................................................................................... [ 31%]
..................................................................................................................................................................................................................................... [ 47%]
..................................................................................................................................................................................................................................... [ 63%]
.........................................................................................................................................................s..s..s..s..s..s............................................................ [ 79%]
............................................s..s..s..s............................................................................................................................................................................... [ 95%]
......................................................................                                                                                                                                                                [100%]
============================================================================================================= warnings summary ==============================================================================================================
tests/tests_ebt/test_ebt_ignores.py::test_standard_fs_critical_red
tests/tests_ebt/test_ebt_ignores.py::test_custom_fs_ignores_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignore_deep_directory_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignores_with_forall_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignores_with_expect_false_red
  /home/symphonie/PycharmProjects/cubie/src/qb_cubie/arenas/tempfs.py:66: UserWarning: TempFS is not intended for venv or side-package isolation; use PyVenv instead.
    warnings.warn("TempFS is not intended for venv or side-package isolation; use PyVenv instead.")

tests/tests_ebt/test_ebt_imports.py::test_import_rehydration_instance[PyVenv]
  /home/symphonie/PycharmProjects/cubie/src/qb_cubie/arenas/codecs.py:102: UserWarning: It is strongly recommended to use stateless static methods or classmethods. Instance rehydration via IPC is experimental and may fail for complex objects.
    return cls._extract_instance(target)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1433 passed, 11 skipped, 6 warnings in 406.64s (0:06:46)