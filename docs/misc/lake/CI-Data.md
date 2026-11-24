# Wheel / windows-2022 / Python 3.13 sagt: 

================================== FAILURES ===================================
_ test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence _

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-6/test_installed_two_plus_five_s0')
provider = ('http://127.0.0.1:61944', [('/api/version', None), ('/api/tags', None), ('/api/ps', None), ('/api/show', {'model': 'gemma4:12b'}), ('/api/version', None), ('/api/tags', None), ...])

    def test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence(tmp_path, provider):
        from ollama_agents.pilot.live import measure_smoke
    
        from cubie_benchmarks.reporting.archives import read_archive
    
        endpoint, calls = provider
        root = tmp_path / 'calibrated study'
        study = measure_smoke(root, endpoint=endpoint, exploratory=True)
        assert study['study_kind'] == 'exploratory' and study['human_admission'] is False
        assert [stage['stage'] for stage in study['stages']] == ['calibration', 'calibration', 'pilot', 'pilot']
        counts = []
        model_calls = 0
        for stage in study['stages']:
            archive = root / stage['archive']
            runs = read_archive(archive)['runs']
            counts.append(len(runs))
>           assert stage['evidence_complete'] and all(run['status'] == 'completed' for run in runs)
E           assert (True and False)
E            +  where False = all(<generator object test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence.<locals>.<genexpr> at 0x0000026D3B78FD30>)

tests\ollama_agents_installed.py:207: AssertionError
---------------------------- Captured stderr call -----------------------------
Starting reviewer-calibration
Archived reviewer-calibration: 4 attempts
Starting developer-calibration
Archived developer-calibration: 2 attempts
Starting reviewer-pilot
Archived reviewer-pilot: 10 attempts
Starting developer-pilot
Archived developer-pilot: 5 attempts
=========================== short test summary info ===========================
FAILED tests/ollama_agents_installed.py::test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence - assert (True and False)
 +  where False = all(<generator object test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence.<locals>.<genexpr> at 0x0000026D3B78FD30>)
1 failed, 3 passed in 32.87s
Traceback (most recent call last):
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 119, in <module>
    main()
    ~~~~^^
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 114, in main
    run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config),
    ~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        str(tests / "ollama_agents_installed.py"))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
subprocess.CalledProcessError: Command '['C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-s45jkiw5\\venv\\Scripts\\python.exe', '-I', '-m', 'pytest', '-q', '--import-mode=importlib', '-c', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-s45jkiw5\\pytest.ini', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-s45jkiw5\\tests\\ollama_agents_installed.py']' returned non-zero exit status 1.
Error: Process completed with exit code 1.


# Wheel / windows-2022 / Python 3.14 sagt:

================================== FAILURES ===================================
_ test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence _

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-6/test_installed_two_plus_five_s0')
provider = ('http://127.0.0.1:61219', [('/api/version', None), ('/api/tags', None), ('/api/ps', None), ('/api/show', {'model': 'gemma4:12b'}), ('/api/version', None), ('/api/tags', None), ...])

    def test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence(tmp_path, provider):
        from ollama_agents.pilot.live import measure_smoke
    
        from cubie_benchmarks.reporting.archives import read_archive
    
        endpoint, calls = provider
        root = tmp_path / 'calibrated study'
        study = measure_smoke(root, endpoint=endpoint, exploratory=True)
        assert study['study_kind'] == 'exploratory' and study['human_admission'] is False
        assert [stage['stage'] for stage in study['stages']] == ['calibration', 'calibration', 'pilot', 'pilot']
        counts = []
        model_calls = 0
        for stage in study['stages']:
            archive = root / stage['archive']
            runs = read_archive(archive)['runs']
            counts.append(len(runs))
>           assert stage['evidence_complete'] and all(run['status'] == 'completed' for run in runs)
E           assert (True and False)
E            +  where False = all(<generator object test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence.<locals>.<genexpr> at 0x0000016B7F9C3C60>)

tests\ollama_agents_installed.py:207: AssertionError
---------------------------- Captured stderr call -----------------------------
Starting reviewer-calibration
Archived reviewer-calibration: 4 attempts
Starting developer-calibration
Archived developer-calibration: 2 attempts
Starting reviewer-pilot
Archived reviewer-pilot: 10 attempts
Starting developer-pilot
Archived developer-pilot: 5 attempts
=========================== short test summary info ===========================
FAILED tests/ollama_agents_installed.py::test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence - assert (True and False)
 +  where False = all(<generator object test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence.<locals>.<genexpr> at 0x0000016B7F9C3C60>)
1 failed, 3 passed in 32.39s
Traceback (most recent call last):
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 119, in <module>
    main()
    ~~~~^^
  File "D:\a\qb-cubie\qb-cubie\scripts\check_wheel.py", line 114, in main
    run("-m", "pytest", "-q", "--import-mode=importlib", "-c", str(config),
    ~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        str(tests / "ollama_agents_installed.py"))
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
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
subprocess.CalledProcessError: Command '['C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-qp5y8f7y\\venv\\Scripts\\python.exe', '-I', '-m', 'pytest', '-q', '--import-mode=importlib', '-c', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-qp5y8f7y\\pytest.ini', 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\qb-cubie-wheel-qp5y8f7y\\tests\\ollama_agents_installed.py']' returned non-zero exit status 1.
Error: Process completed with exit code 1.


---

---

Repository / windows-2022 / Python 3.13 sagt;

Wieder viel zu viel. Hier ist eine zufällige Hand voll: 

"""

tests\tests_ebt\test_ebt_fs_collisions.py:56: AssertionError
_ test_collisions_fail_before_arena_setup[file-and-directory-reverse-set-pre] _

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_collisions_fail_before_ar34')
colliding_sources = [WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_collisions_fail_before_ar34/...:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_collisions_fail_before_ar34/second/shared')]
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000027A79396270>
field = 'pre', collection = <class 'set'>, reverse = True

    @pytest.mark.parametrize("field", ["pre", "post"])
    @pytest.mark.parametrize("collection", [list, tuple, set], ids=["list", "tuple", "set"])
    @pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
    def test_collisions_fail_before_arena_setup(
        tmp_path, colliding_sources, monkeypatch, field, collection, reverse,
    ):
        sources = list(reversed(colliding_sources)) if reverse else colliding_sources
        # Include trailing slashes to exercise directory basename normalization.
        fs = collection(str(source) + ("/" if source.is_dir() else "") for source in sources)
        arena, marker = TempFS(), tmp_path / "called"
        setup = Mock(wraps=arena.setup)
        monkeypatch.setattr(arena, "setup", setup)
        with pytest.raises(ValueError) as error:
            EBT(target=partial(mark_execution, marker), arena=arena,
                **{field: WorldState(fs=fs)}, reporter=None).run()
        message = str(error.value)
        assert field in message and "fs" in message and "shared" in message
>       assert all(str(source) in message for source in sources)
E       assert False
E        +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25FCA0>)

tests\tests_ebt\test_ebt_fs_collisions.py:56: AssertionError
_ test_collisions_fail_before_arena_setup[file-and-directory-reverse-set-post] _

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_collisions_fail_before_ar35')
colliding_sources = [WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_collisions_fail_before_ar35/...:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_collisions_fail_before_ar35/second/shared')]
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000027A79395C50>
field = 'post', collection = <class 'set'>, reverse = True

    @pytest.mark.parametrize("field", ["pre", "post"])
    @pytest.mark.parametrize("collection", [list, tuple, set], ids=["list", "tuple", "set"])
    @pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
    def test_collisions_fail_before_arena_setup(
        tmp_path, colliding_sources, monkeypatch, field, collection, reverse,
    ):
        sources = list(reversed(colliding_sources)) if reverse else colliding_sources
        # Include trailing slashes to exercise directory basename normalization.
        fs = collection(str(source) + ("/" if source.is_dir() else "") for source in sources)
        arena, marker = TempFS(), tmp_path / "called"
        setup = Mock(wraps=arena.setup)
        monkeypatch.setattr(arena, "setup", setup)
        with pytest.raises(ValueError) as error:
            EBT(target=partial(mark_execution, marker), arena=arena,
                **{field: WorldState(fs=fs)}, reporter=None).run()
        message = str(error.value)
        assert field in message and "fs" in message and "shared" in message
>       assert all(str(source) in message for source in sources)
E       assert False
E        +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A775783C0>)

tests\tests_ebt\test_ebt_fs_collisions.py:56: AssertionError
_____________ test_ebt_default_project_and_string_path_resolution _____________

    def test_ebt_default_project_and_string_path_resolution():
        """
        Gesetz: DocEnsurance l�st target=None standardm��ig auf das gesamte Projekt-Root
        (alle Ordner inkl. Root-Dateien) auf, w�hrend einzeilige Pfad-Strings ('docs',
        'docs/guide.md') gezielt nur das angegebene Dateisystemziel pr�fen.
        """
        EBT(
            target=run_string_path_ensurance,
            arena=TempFS(),
            pre=[
                WorldState(args=("docs",)),
                WorldState(args=("docs/guide.md",)),
            ],
            post=WorldState(
                returns={
                    "passed": True,
                    "outputs": [["42"]],
                }
            ),
            custom_id="doc_string_path_resolution",
        ).run()
    
        EBT(
            target=run_default_project_ensurance,
            arena=TempFS(),
            pre=[
                WorldState(args=(False, False)),
                WorldState(args=(True, False)),
                WorldState(args=(True, True)),
            ],
            post=WorldState(
                returns={
                    "passed": True,
                    "target_is_root": True,
                    "outputs": [["root"], ["docs"], ["guides"]],
                }
            ),
            custom_id="doc_default_project_all_folders",
>       ).run()
          ^^^^^
E       AssertionError: EBT-Assert failed for step 'cubie_run_doc_default_project_all_folders_78a0b78e484247ad8652b5d694ca9ee6_0':
E       Target: run_default_project_ensurance
E         [Q-State 0] Validation: Mismatch
E           - Returns: Expected {'passed': True, 'target_is_root': True, 'outputs': [['root'], ['docs'], ['guides']]} | Actual {'passed': True, 'target_is_root': True, 'outputs': [['docs'], ['guides'], ['root']]} (Mismatch)

tests\tests_services\tests_doc_ensurance\test_doc_ensurance.py:599: AssertionError
_________________ test_cli_docframe_update_json_and_excludes __________________

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_cli_docframe_update_json_0')
capsys = <_pytest.capture.CaptureFixture object at 0x0000027A7B400290>

    def test_cli_docframe_update_json_and_excludes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Verifies JSON output and repeatable --exclude filtering for docframe update."""
        root = _seed_doc_project(tmp_path / "proj_json")
        (root / "drafts").mkdir()
        (root / "drafts" / "notes.md").write_text(
            '<!-- qb:frame id="UNKNOWN_FRAME" zone="head" -->\n# Bad\n<!-- /qb:frame -->\n',
            encoding="utf-8",
        )
        code = cli_main(["docframe", "update", str(root), "--exclude", "drafts", "--format", "json"])
        payload = json.loads(capsys.readouterr().out)
        assert code == 0
        assert payload["passed"] is True
>       assert payload["updated_files"] == ["README.md", "docs/GUIDE_Sample.md"]
E       AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
E         
E         At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
E         
E         Full diff: (-: missing in left side, +: extra in left side)
E           [
E         +     'docs/GUIDE_Sample.md',
E               'README.md',
E         -     'docs/GUIDE_Sample.md',
E           ]

tests\tests_services\tests_doc_frame\test_docframe_cli.py:61: AssertionError
____________ test_module_entrypoints_execute_cleanly[module_args0] ____________

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_module_entrypoints_execut0')
module_args = ['-m', 'qb_cubie', 'docframe', 'update']

    @pytest.mark.parametrize(
        "module_args",
        [
            ["-m", "qb_cubie", "docframe", "update"],
            ["-m", "qb_cubie.services.docframe", "update"],
            ["-m", "qb_cubie.services.doc_frame", "update"],
        ],
    )
    def test_module_entrypoints_execute_cleanly(tmp_path: Path, module_args: list[str]) -> None:
        """Executes all python -m CLI entrypoints in a subprocess without warnings."""
        root = _seed_doc_project(tmp_path / "proj_mod")
        proc = subprocess.run(
            [sys.executable, *module_args, str(root), "--format", "json"],
            capture_output=True, text=True, timeout=20, check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "RuntimeWarning" not in proc.stderr
        payload = json.loads(proc.stdout)
>       assert payload["updated_files"] == ["README.md", "docs/GUIDE_Sample.md"]
E       AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
E         
E         At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
E         
E         Full diff: (-: missing in left side, +: extra in left side)
E           [
E         +     'docs/GUIDE_Sample.md',
E               'README.md',
E         -     'docs/GUIDE_Sample.md',
E           ]

tests\tests_services\tests_doc_frame\test_docframe_cli.py:95: AssertionError
____________ test_module_entrypoints_execute_cleanly[module_args1] ____________

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_module_entrypoints_execut1')
module_args = ['-m', 'qb_cubie.services.docframe', 'update']

    @pytest.mark.parametrize(
        "module_args",
        [
            ["-m", "qb_cubie", "docframe", "update"],
            ["-m", "qb_cubie.services.docframe", "update"],
            ["-m", "qb_cubie.services.doc_frame", "update"],
        ],
    )
    def test_module_entrypoints_execute_cleanly(tmp_path: Path, module_args: list[str]) -> None:
        """Executes all python -m CLI entrypoints in a subprocess without warnings."""
        root = _seed_doc_project(tmp_path / "proj_mod")
        proc = subprocess.run(
            [sys.executable, *module_args, str(root), "--format", "json"],
            capture_output=True, text=True, timeout=20, check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "RuntimeWarning" not in proc.stderr
        payload = json.loads(proc.stdout)
>       assert payload["updated_files"] == ["README.md", "docs/GUIDE_Sample.md"]
E       AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
E         
E         At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
E         
E         Full diff: (-: missing in left side, +: extra in left side)
E           [
E         +     'docs/GUIDE_Sample.md',
E               'README.md',
E         -     'docs/GUIDE_Sample.md',
E           ]

tests\tests_services\tests_doc_frame\test_docframe_cli.py:95: AssertionError
____________ test_module_entrypoints_execute_cleanly[module_args2] ____________

tmp_path = WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_module_entrypoints_execut2')
module_args = ['-m', 'qb_cubie.services.doc_frame', 'update']

    @pytest.mark.parametrize(
        "module_args",
        [
            ["-m", "qb_cubie", "docframe", "update"],
            ["-m", "qb_cubie.services.docframe", "update"],
            ["-m", "qb_cubie.services.doc_frame", "update"],
        ],
    )
    def test_module_entrypoints_execute_cleanly(tmp_path: Path, module_args: list[str]) -> None:
        """Executes all python -m CLI entrypoints in a subprocess without warnings."""
        root = _seed_doc_project(tmp_path / "proj_mod")
        proc = subprocess.run(
            [sys.executable, *module_args, str(root), "--format", "json"],
            capture_output=True, text=True, timeout=20, check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "RuntimeWarning" not in proc.stderr
        payload = json.loads(proc.stdout)
>       assert payload["updated_files"] == ["README.md", "docs/GUIDE_Sample.md"]
E       AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
E         
E         At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
E         
E         Full diff: (-: missing in left side, +: extra in left side)
E           [
E         +     'docs/GUIDE_Sample.md',
E               'README.md',
E         -     'docs/GUIDE_Sample.md',
E           ]

tests\tests_services\tests_doc_frame\test_docframe_cli.py:95: AssertionError
____________ test_ebt_docframe_broken_route_rule_on_missing_asset _____________

    def test_ebt_docframe_broken_route_rule_on_missing_asset() -> None:
        """Verifies that DOCFRAME-BROKEN-ROUTE flags missing banner or route target files in the workspace."""
        expected_diags = [
            ("DOCFRAME-BROKEN-ROUTE", "error", "README.md"),
            ("DOCFRAME-BROKEN-ROUTE", "error", "GUIDE_Quality-Assurance.md"),
            ("DOCFRAME-BROKEN-ROUTE", "error", "GUIDE_DocEnsurance.md"),
        ]
        EBT(
            target=_run_docframe_check,
            arena=TempFS(),
            pre=WorldState(args=("broken_banner",)),
            post=WorldState(returns={"passed": False, "diagnostics": expected_diags}),
            custom_id="docframe_rule_broken_route",
>       ).run()
          ^^^^^
E       AssertionError: EBT-Assert failed for step 'cubie_run_docframe_rule_broken_route_cb4b10eeb5e242cb91bb31c9e6e84657_0':
E       Target: _run_docframe_check
E         [Q-State 0] Validation: Mismatch
E           - Returns: Expected {'passed': False, 'diagnostics': [('DOCFRAME-BROKEN-ROUTE', 'error', 'README.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_Quality-Assurance.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_DocEnsurance.md')]} | Actual {'passed': False, 'diagnostics': [('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_Quality-Assurance.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_DocEnsurance.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'README.md')]} (Mismatch)

tests\tests_services\tests_doc_frame\test_docframe_rules_and_guards.py:216: AssertionError
______ test_ambiguous_settings_are_rejected_before_target_execution[pre] ______

settings_files = [WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_ambiguous_settings_are_re0/s...runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_ambiguous_settings_are_re0/shipping/settings.json')]
field = 'pre'

    @pytest.mark.parametrize("field", ["pre", "post"])
    def test_ambiguous_settings_are_rejected_before_target_execution(settings_files, field):
        calls = []
        with pytest.raises(ValueError, match="settings.json") as error:
            EBT(target=lambda: calls.append("executed"), arena=TempFS(),
                **{field: WorldState(fs=settings_files)}).run()
        assert calls == []
>       assert all(str(path) in str(error.value) for path in settings_files)
E       assert False
E        +  where False = all(<generator object test_ambiguous_settings_are_rejected_before_target_execution.<locals>.<genexpr> at 0x0000027A00962260>)

tests\tests_user_workflows\test_settings_bundle.py:61: AssertionError
_____ test_ambiguous_settings_are_rejected_before_target_execution[post] ______

settings_files = [WindowsPath('C:/Users/runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_ambiguous_settings_are_re1/s...runneradmin/AppData/Local/Temp/pytest-of-runneradmin/pytest-0/test_ambiguous_settings_are_re1/shipping/settings.json')]
field = 'post'

    @pytest.mark.parametrize("field", ["pre", "post"])
    def test_ambiguous_settings_are_rejected_before_target_execution(settings_files, field):
        calls = []
        with pytest.raises(ValueError, match="settings.json") as error:
            EBT(target=lambda: calls.append("executed"), arena=TempFS(),
                **{field: WorldState(fs=settings_files)}).run()
        assert calls == []
>       assert all(str(path) in str(error.value) for path in settings_files)
E       assert False
E        +  where False = all(<generator object test_ambiguous_settings_are_rejected_before_target_execution.<locals>.<genexpr> at 0x0000027A00962B20>)

tests\tests_user_workflows\test_settings_bundle.py:61: AssertionError
============================== warnings summary ===============================
tests/tests_ebt/test_ebt_ignores.py::test_standard_fs_critical_red
tests/tests_ebt/test_ebt_ignores.py::test_custom_fs_ignores_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignore_deep_directory_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignores_with_forall_green
tests/tests_ebt/test_ebt_ignores.py::test_fs_ignores_with_expect_false_red
  D:\a\qb-cubie\qb-cubie\src\qb_cubie\arenas\tempfs.py:79: UserWarning: TempFS is not intended for venv or side-package isolation; use PyVenv instead.
    warnings.warn("TempFS is not intended for venv or side-package isolation; use PyVenv instead.")

tests/tests_ebt/test_ebt_imports.py::test_import_rehydration_instance[PyVenv]
  D:\a\qb-cubie\qb-cubie\src\qb_cubie\arenas\codecs.py:100: UserWarning: It is strongly recommended to use stateless static methods or classmethods. Instance rehydration via IPC is experimental and may fail for complex objects.
    return cls._extract_instance(target)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/tests_arena/test_arena_requirements.py::test_probe_rejects_incomplete_venv_without_installing - AssertionError: Regex pattern did not match.
  Expected regex: 'Could not inspect arena requirements.*missing pyvenv\\.cfg'
  Actual message: 'Could not inspect arena requirements using C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_probe_rejects_incomplete_0\\base\\Scripts\\python.exe: failed to locate pyvenv.cfg: The system cannot find the file specified.\n\n\n'
FAILED tests/tests_arena/test_ci_platform_stage1.py::test_relocate_link_handles_symlinked_base_prefix - RuntimeError: Unsupported console entry point cannot be relocated safely: tool. Use a base without this launcher and invoke its module with the clone's Python.
FAILED tests/tests_arena/test_ci_platform_stage2.py::test_windows_native_cowsay_launcher_runs_from_clone - AttributeError: Can't get local object 'test_windows_native_cowsay_launcher_runs_from_clone.<locals>.invoke_cowsay'
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[tempfs-absolute-file-ebt] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina0\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina0\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina0\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina0\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina0\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina0\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina0\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina0\\\\outside': expected a relative filesystem path") tblen=14>.value
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[tempfs-absolute-file-standalone] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina1\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina1\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina1\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina1\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina1\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina1\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina1\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina1\\\\outside': expected a relative filesystem path") tblen=8>.value
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[tempfs-absolute-directory-ebt] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina2\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina2\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina2\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina2\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina2\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina2\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina2\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina2\\\\outside': expected a relative filesystem path") tblen=14>.value
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[tempfs-absolute-directory-standalone] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina3\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina3\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina3\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina3\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina3\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina3\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina3\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina3\\\\outside': expected a relative filesystem path") tblen=8>.value
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[pyvenv-absolute-file-ebt] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina12\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina12\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina12\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina12\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina12\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina12\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina12\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...unneradmin\\\\pytest-0\\\\test_hydration_rejects_destina12\\\\outside': expected a relative filesystem path") tblen=14>.value
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[pyvenv-absolute-file-standalone] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina13\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina13\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina13\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina13\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina13\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina13\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina13\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina13\\\\outside': expected a relative filesystem path") tblen=8>.value
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[pyvenv-absolute-directory-ebt] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina14\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina14\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina14\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina14\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina14\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina14\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina14\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...unneradmin\\\\pytest-0\\\\test_hydration_rejects_destina14\\\\outside': expected a relative filesystem path") tblen=14>.value
FAILED tests/tests_arena/test_ebt_hydration_boundaries.py::test_hydration_rejects_destinations_outside_workspace[pyvenv-absolute-directory-standalone] - assert 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina15\\outside' in "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina15\\\\outside': expected a relative filesystem path"
 +  where 'C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina15\\outside' = str('C:\\Users\\runneradmin\\AppData\\Local\\Temp\\pytest-of-runneradmin\\pytest-0\\test_hydration_rejects_destina15\\outside')
 +  and   "Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina15\\\\outside': expected a relative filesystem path" = str(ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina15\\\\outside': expected a relative filesystem path"))
 +    where ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina15\\\\outside': expected a relative filesystem path") = <ExceptionInfo ValueError("Invalid pre.fs destination 'C:\\\\Users\\\\runneradmin\\\\AppData\\\\Local\\\\Temp\\\\pytes...runneradmin\\\\pytest-0\\\\test_hydration_rejects_destina15\\\\outside': expected a relative filesystem path") tblen=8>.value
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-forward-list-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D5380>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-forward-list-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D5C40>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-forward-tuple-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D5FC0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-forward-tuple-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D7D80>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-forward-set-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7ADC8AC0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-forward-set-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B174BA0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-reverse-list-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1742E0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-reverse-list-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B176B20>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-reverse-tuple-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7ADC97E0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-reverse-tuple-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A787C35A0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-reverse-set-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D42E0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[files-reverse-set-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D52A0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-forward-list-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D5380>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-forward-list-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B175700>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-forward-tuple-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B174BA0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-forward-tuple-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7AE65EE0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-forward-set-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25E5E0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-forward-set-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25EF80>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-reverse-list-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25CD60>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-reverse-list-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25C2E0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-reverse-tuple-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7AE65EE0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-reverse-tuple-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B177AE0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-reverse-set-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B177BC0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[directories-reverse-set-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D5EE0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-forward-list-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D7920>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-forward-list-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B1D73E0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-forward-tuple-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A787C3D80>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-forward-tuple-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7ADC9D20>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-forward-set-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25D000>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-forward-set-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25FAE0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-reverse-list-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25DFC0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-reverse-list-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7ADF42E0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-reverse-tuple-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25E340>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-reverse-tuple-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25F140>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-reverse-set-pre] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A7B25FCA0>)
FAILED tests/tests_ebt/test_ebt_fs_collisions.py::test_collisions_fail_before_arena_setup[file-and-directory-reverse-set-post] - assert False
 +  where False = all(<generator object test_collisions_fail_before_arena_setup.<locals>.<genexpr> at 0x0000027A775783C0>)
FAILED tests/tests_services/tests_doc_ensurance/test_doc_ensurance.py::test_ebt_default_project_and_string_path_resolution - AssertionError: EBT-Assert failed for step 'cubie_run_doc_default_project_all_folders_78a0b78e484247ad8652b5d694ca9ee6_0':
Target: run_default_project_ensurance
  [Q-State 0] Validation: Mismatch
    - Returns: Expected {'passed': True, 'target_is_root': True, 'outputs': [['root'], ['docs'], ['guides']]} | Actual {'passed': True, 'target_is_root': True, 'outputs': [['docs'], ['guides'], ['root']]} (Mismatch)
FAILED tests/tests_services/tests_doc_frame/test_docframe_cli.py::test_cli_docframe_update_json_and_excludes - AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
  
  At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
  
  Full diff: (-: missing in left side, +: extra in left side)
    [
  +     'docs/GUIDE_Sample.md',
        'README.md',
  -     'docs/GUIDE_Sample.md',
    ]
FAILED tests/tests_services/tests_doc_frame/test_docframe_cli.py::test_module_entrypoints_execute_cleanly[module_args0] - AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
  
  At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
  
  Full diff: (-: missing in left side, +: extra in left side)
    [
  +     'docs/GUIDE_Sample.md',
        'README.md',
  -     'docs/GUIDE_Sample.md',
    ]
FAILED tests/tests_services/tests_doc_frame/test_docframe_cli.py::test_module_entrypoints_execute_cleanly[module_args1] - AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
  
  At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
  
  Full diff: (-: missing in left side, +: extra in left side)
    [
  +     'docs/GUIDE_Sample.md',
        'README.md',
  -     'docs/GUIDE_Sample.md',
    ]
FAILED tests/tests_services/tests_doc_frame/test_docframe_cli.py::test_module_entrypoints_execute_cleanly[module_args2] - AssertionError: assert ['docs/GUIDE_..., 'README.md'] == ['README.md',...DE_Sample.md']
  
  At index 0 diff: 'docs/GUIDE_Sample.md' != 'README.md'
  
  Full diff: (-: missing in left side, +: extra in left side)
    [
  +     'docs/GUIDE_Sample.md',
        'README.md',
  -     'docs/GUIDE_Sample.md',
    ]
FAILED tests/tests_services/tests_doc_frame/test_docframe_rules_and_guards.py::test_ebt_docframe_broken_route_rule_on_missing_asset - AssertionError: EBT-Assert failed for step 'cubie_run_docframe_rule_broken_route_cb4b10eeb5e242cb91bb31c9e6e84657_0':
Target: _run_docframe_check
  [Q-State 0] Validation: Mismatch
    - Returns: Expected {'passed': False, 'diagnostics': [('DOCFRAME-BROKEN-ROUTE', 'error', 'README.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_Quality-Assurance.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_DocEnsurance.md')]} | Actual {'passed': False, 'diagnostics': [('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_Quality-Assurance.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'GUIDE_DocEnsurance.md'), ('DOCFRAME-BROKEN-ROUTE', 'error', 'README.md')]} (Mismatch)
FAILED tests/tests_user_workflows/test_settings_bundle.py::test_ambiguous_settings_are_rejected_before_target_execution[pre] - assert False
 +  where False = all(<generator object test_ambiguous_settings_are_rejected_before_target_execution.<locals>.<genexpr> at 0x0000027A00962260>)
FAILED tests/tests_user_workflows/test_settings_bundle.py::test_ambiguous_settings_are_rejected_before_target_execution[post] - assert False
 +  where False = all(<generator object test_ambiguous_settings_are_rejected_before_target_execution.<locals>.<genexpr> at 0x0000027A00962B20>)
55 failed, 1632 passed, 23 skipped, 162 deselected, 6 warnings in 319.27s (0:05:19)
Error: Process completed with exit code 1.


"""