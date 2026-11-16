(qb-cubie) symphonie@symphonie:~/PycharmProjects/cubie$ make test-all
.venv/bin/python -m pytest -m "" --hypothesis-profile=ci -q
......................................................F.F................................s........................................................................................................................................... [ 15%]
..................................................................................................................................................................................................................................... [ 31%]
..................................................................................................................................................................................................................................... [ 47%]
..................................................................................................................................................................................................................................... [ 63%]
.........................................................................................................................................................s..s..s..s..s..s............................................................ [ 79%]
............................................s..s..s..s............................................................................................................................................................................... [ 95%]
...................................................................                                                                                                                                                                   [100%]
================================================================================================================= FAILURES ==================================================================================================================
____________________________________________________________________________________________________________ test_src_lint[ruff] ____________________________________________________________________________________________________________

tool = 'ruff'
src_files = (PosixPath('/home/symphonie/PycharmProjects/cubie/src/qb_cubie/__init__.py'), PosixPath('/home/symphonie/PycharmProjec..._cubie/arenas/_hydration.py'), PosixPath('/home/symphonie/PycharmProjects/cubie/src/qb_cubie/arenas/_process.py'), ...)
tmp_path = PosixPath('/tmp/pytest-of-symphonie/pytest-6/test_src_lint_ruff_0')

    @pytest.mark.parametrize("tool", COMMANDS)
    def test_src_lint(tool, src_files, tmp_path):
        result = run_linter(tool, src_files, tmp_path)
>       assert result.returncode == 0, (
            f"{tool} failed (exit {result.returncode}).\n"
            f"{result.stdout}\n{result.stderr}"
        )
E       AssertionError: ruff failed (exit 1).
E         src/qb_cubie/services/doc_ensurance/doc_ensurance.py:14:52: F401 [*] `...linter.Linter` imported but unused
E         Found 1 error.
E         [*] 1 fixable with `--fix`.
E         
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/home/symphonie/PycharmProjects/cubie/.venv/bin/python', '-m', 'ruff', 'check', '--isolated', ...e.py:14:52: F401 [*] `...linter.Linter` imported but unused\nFound 1 error.\n[*] 1 fixable with `--fix`.\n', stderr='').returncode

tests/test_lint.py:29: AssertionError
____________________________________________________________________________________________________________ test_src_lint[mypy] ____________________________________________________________________________________________________________

tool = 'mypy'
src_files = (PosixPath('/home/symphonie/PycharmProjects/cubie/src/qb_cubie/__init__.py'), PosixPath('/home/symphonie/PycharmProjec..._cubie/arenas/_hydration.py'), PosixPath('/home/symphonie/PycharmProjects/cubie/src/qb_cubie/arenas/_process.py'), ...)
tmp_path = PosixPath('/tmp/pytest-of-symphonie/pytest-6/test_src_lint_mypy_0')

    @pytest.mark.parametrize("tool", COMMANDS)
    def test_src_lint(tool, src_files, tmp_path):
        result = run_linter(tool, src_files, tmp_path)
>       assert result.returncode == 0, (
            f"{tool} failed (exit {result.returncode}).\n"
            f"{result.stdout}\n{result.stderr}"
        )
E       AssertionError: mypy failed (exit 1).
E         src/qb_cubie/services/doc_frame/doc_frame.py:270:23: error: Subclass of "Sequence[FramePattern]" and "str" cannot exist: would have inconsistent method resolution order  [unreachable]
E         src/qb_cubie/services/doc_frame/doc_frame.py:270:23: error: Subclass of "Sequence[FramePattern]" and "bytes" cannot exist: would have inconsistent method resolution order  [unreachable]
E         src/qb_cubie/services/doc_ensurance/doc_ensurance.py:182:16: error: Incompatible return value type (got "tuple[DocPatternProtocol | Any | Sequence[Any], tuple[Any, ...] | None]", expected "tuple[DocPatternProtocol, tuple[Any, ...] | None]")  [return-value]
E         
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/home/symphonie/PycharmProjects/cubie/.venv/bin/python', '-m', 'mypy', '--config-file=/tmp/pyt... tuple[Any, ...] | None]", expected "tuple[DocPatternProtocol, tuple[Any, ...] | None]")  [return-value]\n', stderr='').returncode

tests/test_lint.py:29: AssertionError
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
========================================================================================================== short test summary info ==========================================================================================================
FAILED tests/test_lint.py::test_src_lint[ruff] - AssertionError: ruff failed (exit 1).
FAILED tests/test_lint.py::test_src_lint[mypy] - AssertionError: mypy failed (exit 1).
2 failed, 1428 passed, 11 skipped, 6 warnings in 395.56s (0:06:35)
make: *** [Makefile:21: test-all] Fehler 1