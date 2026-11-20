# Wheel / windows-2022 / Python 3.13 sagt:

================================== FAILURES ===================================
_______ test_installed_smoke_runs_both_benchmarks_and_persists_evidence _______

installed_suite = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-2/test_installed_smoke_runs_both0/own project with spaces/sets/smoke.toml')
tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-2/test_installed_smoke_runs_both0')

    def test_installed_smoke_runs_both_benchmarks_and_persists_evidence(installed_suite, tmp_path):
        initialize_cli(installed_suite)
        from cubie_benchmarks import plan_suite
    
        plan = plan_suite(installed_suite)
        contract(lambda: cli("run", "--suite", installed_suite, cwd=tmp_path),
                 expected=lambda p: p.returncode == 0)
        results = list(Path(plan["output"]).glob("*/results.json"))
        assert len(results) == 1
        root = results[0].parent
        result = json.loads(results[0].read_text(encoding="utf-8"))
        assert {r["benchmark"] for r in result["runs"]} == {"review_agent", "developer_agent"}
>       assert all(r["status"] == "completed" and r["quality_passed"] for r in result["runs"])
E       assert False
E        +  where False = all(<generator object test_installed_smoke_runs_both_benchmarks_and_persists_evidence.<locals>.<genexpr> at 0x000001F899573440>)

tests\benchmark_installed.py:98: AssertionError
=========================== short test summary info ===========================
FAILED tests/benchmark_installed.py::test_installed_smoke_runs_both_benchmarks_and_persists_evidence - assert False
 +  where False = all(<generator object test_installed_smoke_runs_both_benchmarks_and_persists_evidence.<locals>.<genexpr> at 0x000001F899573440>)
1 failed, 7 passed in 8.52s
Traceback (most recent call last):
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 119, in <module>
    main()
    ~~~~^^
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 106, in main
    run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config), str(tests / filename))
    ~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 84, in run
    subprocess.run(
    ~~~~~~~~~~~~~~^
        [str(python), "-I", *arguments], cwd=root, env=environment,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        check=True, timeout=timeout,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\hostedtoolcache\windows\Python\3.13.17\x64\Lib\subprocess.py", line 578, in run
    raise CalledProcessError(retcode, process.args,
                             output=stdout, stderr=stderr)
subprocess.CalledProcessError: Command '['C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-br4u_23j\\venv\\Scripts\\python.exe', '-I', '-m', 'pytest', '-q', '--import-mode=importlib', '-c', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-br4u_23j\\pytest.ini', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-br4u_23j\\tests\\benchmark_installed.py']' returned non-zero exit status 1.
Error: Process completed with exit code 1.

---

# Wheel / windows-2022 / Python 3.14 sagt:


================================== FAILURES ===================================
_______ test_installed_smoke_runs_both_benchmarks_and_persists_evidence _______

installed_suite = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-2/test_installed_smoke_runs_both0/own project with spaces/sets/smoke.toml')
tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-2/test_installed_smoke_runs_both0')

    def test_installed_smoke_runs_both_benchmarks_and_persists_evidence(installed_suite, tmp_path):
        initialize_cli(installed_suite)
        from cubie_benchmarks import plan_suite
    
        plan = plan_suite(installed_suite)
        contract(lambda: cli("run", "--suite", installed_suite, cwd=tmp_path),
                 expected=lambda p: p.returncode == 0)
        results = list(Path(plan["output"]).glob("*/results.json"))
        assert len(results) == 1
        root = results[0].parent
        result = json.loads(results[0].read_text(encoding="utf-8"))
        assert {r["benchmark"] for r in result["runs"]} == {"review_agent", "developer_agent"}
>       assert all(r["status"] == "completed" and r["quality_passed"] for r in result["runs"])
E       assert False
E        +  where False = all(<generator object test_installed_smoke_runs_both_benchmarks_and_persists_evidence.<locals>.<genexpr> at 0x0000020585AD18A0>)

tests\benchmark_installed.py:98: AssertionError
=========================== short test summary info ===========================
FAILED tests/benchmark_installed.py::test_installed_smoke_runs_both_benchmarks_and_persists_evidence - assert False
 +  where False = all(<generator object test_installed_smoke_runs_both_benchmarks_and_persists_evidence.<locals>.<genexpr> at 0x0000020585AD18A0>)
1 failed, 7 passed in 13.80s
Traceback (most recent call last):
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 119, in <module>
    main()
    ~~~~^^
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 106, in main
    run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config), str(tests / filename))
    ~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 84, in run
    subprocess.run(
    ~~~~~~~~~~~~~~^
        [str(python), "-I", *arguments], cwd=root, env=environment,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        check=True, timeout=timeout,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\hostedtoolcache\windows\Python\3.14.10\x64\Lib\subprocess.py", line 578, in run
    raise CalledProcessError(retcode, process.args,
                             output=stdout, stderr=stderr)
subprocess.CalledProcessError: Command '['C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-tsptkqwf\\venv\\Scripts\\python.exe', '-I', '-m', 'pytest', '-q', '--import-mode=importlib', '-c', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-tsptkqwf\\pytest.ini', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-tsptkqwf\\tests\\benchmark_installed.py']' returned non-zero exit status 1.
Error: Process completed with exit code 1.

---

# Repository / macos-15 / Python 3.13 sagt:


Run uv run --no-sync python -m pytest -m slow -q
..F......ssssssssssssssssssssssssssssssssssssssss....................... [ 44%]
........................................................................ [ 88%]
..................                                                       [100%]
=================================== FAILURES ===================================
_____________________________ test_src_lint[mypy] ______________________________

tool = 'mypy'
src_files = (PosixPath('/Users/runner/work/qb-cubie/qb-cubie/src/qb_cubie/__init__.py'), PosixPath('/Users/runner/work/qb-cubie/qb...b_cubie/arenas/__init__.py'), PosixPath('/Users/runner/work/qb-cubie/qb-cubie/src/qb_cubie/arenas/_hydration.py'), ...)
tmp_path = PosixPath('/private/var/folders/9d/l02zfgrs7c16twd3wbpdmhkc0000gn/T/pytest-of-runner/pytest-1/test_src_lint_mypy_0')

    @pytest.mark.parametrize("tool", COMMANDS)
    def test_src_lint(tool, src_files, tmp_path):
        result = run_linter(tool, src_files, tmp_path)
>       assert result.returncode == 0, (
            f"{tool} failed (exit {result.returncode}).\n"
            f"{result.stdout}\n{result.stderr}"
        )
E       AssertionError: mypy failed (exit 1).
E         src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]
E         
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/Users/runner/work/qb-cubie/qb-cubie/.venv/bin/python3', '-m', 'mypy', '--config-file=/private...returncode=1, stdout='src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]\n', stderr='').returncode

tests/test_lint.py:29: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lint.py::test_src_lint[mypy] - AssertionError: mypy failed (exit 1).
  src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]
  
  
assert 1 == 0
 +  where 1 = CompletedProcess(args=['/Users/runner/work/qb-cubie/qb-cubie/.venv/bin/python3', '-m', 'mypy', '--config-file=/private...returncode=1, stdout='src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]\n', stderr='').returncode
1 failed, 121 passed, 40 skipped, 1698 deselected in 500.17s (0:08:20)
Error: Process completed with exit code 1.

---

# Repository / macos-15 / Python 3.14 sagt:

Run uv run --no-sync python -m pytest -m slow -q
..F......ssssssssssssssssssssssssssssssssssssssss....................... [ 44%]
........................................................................ [ 88%]
..................                                                       [100%]
=================================== FAILURES ===================================
_____________________________ test_src_lint[mypy] ______________________________

tool = 'mypy'
src_files = (PosixPath('/Users/runner/work/qb-cubie/qb-cubie/src/qb_cubie/__init__.py'), PosixPath('/Users/runner/work/qb-cubie/qb...b_cubie/arenas/__init__.py'), PosixPath('/Users/runner/work/qb-cubie/qb-cubie/src/qb_cubie/arenas/_hydration.py'), ...)
tmp_path = PosixPath('/private/var/folders/9d/l02zfgrs7c16twd3wbpdmhkc0000gn/T/pytest-of-runner/pytest-1/test_src_lint_mypy_0')

    @pytest.mark.parametrize("tool", COMMANDS)
    def test_src_lint(tool, src_files, tmp_path):
        result = run_linter(tool, src_files, tmp_path)
>       assert result.returncode == 0, (
            f"{tool} failed (exit {result.returncode}).\n"
            f"{result.stdout}\n{result.stderr}"
        )
E       AssertionError: mypy failed (exit 1).
E         src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]
E         
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/Users/runner/work/qb-cubie/qb-cubie/.venv/bin/python3', '-m', 'mypy', '--config-file=/private...returncode=1, stdout='src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]\n', stderr='').returncode

tests/test_lint.py:29: AssertionError
=========================== short test summary info ============================
FAILED tests/test_lint.py::test_src_lint[mypy] - AssertionError: mypy failed (exit 1).
  src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]
  
  
assert 1 == 0
 +  where 1 = CompletedProcess(args=['/Users/runner/work/qb-cubie/qb-cubie/.venv/bin/python3', '-m', 'mypy', '--config-file=/private...returncode=1, stdout='src/qb_cubie/arenas/pyvenv.py:46:5: error: Statement is unreachable  [unreachable]\n', stderr='').returncode
1 failed, 121 passed, 40 skipped, 1698 deselected in 729.03s (0:12:09)
Error: Process completed with exit code 1.

# Repository / windows-2022 / Python 3.13 sagt:

Viel zu viel, omg. 67 Fehler. Das knall ich dir hier nicht alles rein. Hier ist eine zufällige Hand voll:

"""

 ERROR tests/tests_user_workflows/test_fs_reporting.py::test_report_counts_agree_with_reference[outside-mapping-is-not-an-unexpected-file] - AssertionError: assert {'debug.txt':....csv': b'250'} == {'out/report....': b'outside'}
  
  Omitting 1 identical items, use -vv to show
  Left contains 1 more item:
  {'out\\report.csv': b'250'}
  Right contains 1 more item:
  {'out/report.csv': b'250'}
  
  Full diff: (-: missing in left side, +: extra in left side)
    {
  -     'out/report.csv': b'250',
        'debug.txt': b'outside',
  +     'out\\report.csv': b'250',
    }
ERROR tests/tests_user_workflows/test_fs_reporting.py::test_report_counts_agree_with_reference[overlapping-scopes-count-file-once] - AssertionError: assert {'out\\report.csv': b'999'} == {'out/report.csv': b'999'}
  
  Left contains 1 more item:
  {'out\\report.csv': b'999'}
  Right contains 1 more item:
  {'out/report.csv': b'999'}
  
  Full diff: (-: missing in left side, +: extra in left side)
    {
  -     'out/report.csv': b'999',
  ?         ^
  +     'out\\report.csv': b'999',
  ?         ^^
    }
ERROR tests/tests_user_workflows/test_fs_reporting.py::test_report_paths_and_truncation_agree_with_reference[mapped-directory-with-nested-change] - AssertionError: assert {'out\\2026\\....csv': b'999'} == {'out/2026/re....csv': b'999'}
  
  Left contains 1 more item:
  {'out\\2026\\report.csv': b'999'}
  Right contains 1 more item:
  {'out/2026/report.csv': b'999'}
  
  Full diff: (-: missing in left side, +: extra in left side)
    {
  -     'out/2026/report.csv': b'999',
  ?         ^    ^
  +     'out\\2026\\report.csv': b'999',
  ?         ^^    ^^
    }

[...]

 ERROR tests/tests_user_workflows/test_fs_reporting.py::test_report_paths_and_truncation_agree_with_reference[mapped-single-file] - AssertionError: assert {'out\\report.csv': b'999'} == {'out/report.csv': b'999'}
  
  Left contains 1 more item:
  {'out\\report.csv': b'999'}
  Right contains 1 more item:
  {'out/report.csv': b'999'}
  
  Full diff: (-: missing in left side, +: extra in left side)
    {
  -     'out/report.csv': b'999',
  ?         ^
  +     'out\\report.csv': b'999',
  ?         ^^
    }
ERROR tests/tests_user_workflows/test_fs_reporting.py::test_report_paths_and_truncation_agree_with_reference[outside-mapping-is-not-an-unexpected-file] - AssertionError: assert {'debug.txt':....csv': b'250'} == {'out/report....': b'outside'}
  
  Omitting 1 identical items, use -vv to show
  Left contains 1 more item:
  {'out\\report.csv': b'250'}
  Right contains 1 more item:
  {'out/report.csv': b'250'}
  
  Full diff: (-: missing in left side, +: extra in left side)
    {
  -     'out/report.csv': b'250',
        'debug.txt': b'outside',
  +     'out\\report.csv': b'250',
    }
ERROR tests/tests_user_workflows/test_fs_reporting.py::test_report_paths_and_truncation_agree_with_reference[overlapping-scopes-count-file-once] - AssertionError: assert {'out\\report.csv': b'999'} == {'out/report.csv': b'999'}
  
  Left contains 1 more item:
  {'out\\report.csv': b'999'}
  Right contains 1 more item:
  {'out/report.csv': b'999'}
  
  Full diff: (-: missing in left side, +: extra in left side)
    {
  -     'out/report.csv': b'999',
  ?         ^
  +     'out\\report.csv': b'999',
  ?         ^^
    }
67 failed, 1593 passed, 23 skipped, 162 deselected, 6 warnings, 15 errors in 364.67s (0:06:04)
Error: Process completed with exit code 1.

"""

Repository / windows-2022 / Python 3.14 sagt: 

Wieder zu viel.