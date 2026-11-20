<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Orchestrator (Neon)" effort="High" -->
# TGD-Protokoll 1: Reparatur von BUG-001 (`PyVenv`-Workspace-Isolation)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Orchestrator (Neon)
- **Reasoning-Effort:** High
- **Durchführungsdatum:** 20. November 2026, ~ 11:20 (CET)
- **Synthesebasis:** `tests/tests_arena/GEMINI.md`, `tests/tests_arena/ANALYSIS.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/CI_PLATFORM_STATUS.md`, `docs/dev/Style-Guide.md`, `docs/dev/DEV-GUIDE_Write-down-the-bugs.md`, `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/arenas/codecs.py`, `tests/tests_arena/test_ebt_arena.py`, `tests/tests_arena/test_ebt_hydration_boundaries.py`, `tests/tests_arena/test_pyvenv_workspace_isolation.py`, `tests/tests_linter/test_linter.py`, `KNOWN_ISSUES.md`, `CHANGELOG.md`
- **Stand:** qb-cubie (`v0.0.9`, gemäß `pyproject.toml:7`, Ausgangs-Commit `6a6f9ac6`)
- **Git-Log:** `git log -n 1`
```text
commit 6a6f9ac6213f374e24cc0f6796b8338326111e39 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Fri Nov 20 10:37:03 2026 +0100

    Analyzed BUG-001
```

---

---

<!-- /qb:frame -->

## Kurzfassung

Dieser Durchlauf setzt den fünfstufigen TGD-Prozess aus [`docs/GUIDE_Quality-Assurance.md` (§ 3)](../../docs/GUIDE_Quality-Assurance.md#3-test-guided-development-tgd-in-f%C3%BCnf-schritten) erstmals Ende-zu-Ende für die Reparatur von `[BUG-001]` (`PyVenv`-Workspace-Isolation, Defektklassen **K1–K6** aus [`ANALYSIS.md`](./ANALYSIS.md)) um.

- **Phase A (Red-Phase & Test-Freeze):** Ausschließlich unter `tests/` wurden 3 Bestands-Testmodule auf $Q_{\text{Soll}}$ migriert bzw. gegen einen drohenden *Vacuous Pass* gesichert und 54 neue Regressionsverträge in [`test_pyvenv_workspace_isolation.py`](./test_pyvenv_workspace_isolation.py) ergänzt. Meta-Gates (`84 passed`) und `test_linter.py` (`4 passed`) bestanden sofort; die migrierten Alt-Tests (`7 failed, 82 passed`) sowie die neue Isolations-Suite (`43 failed, 11 passed`) lieferten das erwartete scharfe Red-Signal.
- **Phase B (Green-Phase unter Test-Freeze):** Ohne eine einzige Zeile unter `tests/**/*.py` nach dem Freeze anzufassen, wurden [`src/qb_cubie/arenas/pyvenv.py`](../../src/qb_cubie/arenas/pyvenv.py) und [`src/qb_cubie/arenas/codecs.py`](../../src/qb_cubie/arenas/codecs.py) unter Einhaltung des 12-Zeilen-Limits (`pyvenv.py`: 451 LOC, max. 12 Body-Zeilen; `codecs.py`: 352 LOC, max. 10 Body-Zeilen) repariert. Alle 143 gezielten Tests (`143 passed`), alle 339 Arena-Tests (`339 passed`), Linter-/EBT-Suites (`140 passed`) sowie Styleguide/Lint/Meta (`107 passed`) sprangen auf 100 % Grün.
- **Phase C & D (Living-Documentation-Sync & Gesamtabnahme):** Drei Handbücher, `KNOWN_ISSUES.md` und `CHANGELOG.md` wurden synchronisiert. `tests/test_styleguide.py` bestand (`14 passed`), und der vollständige Repository-Lauf `.venv/bin/python -m pytest -m "" -q` schloss mit **`1812 passed, 11 skipped, 6 warnings in 405.12s (0:06:45)`** ohne Fehler ab.

---

## Schritt 1: Ausgangslage (`ANALYSIS.md`) & Architekturentscheidungen

Ausgangspunkt war der bestätigte Befund `[BUG-001]` (Defektklassen **K1–K6** am Stand `6a6f9ac6`) sowie die drei in [`ANALYSIS.md`](./ANALYSIS.md#teil-5-vorschlag-f%C3%BCr-die-n%C3%A4chsten-tgd-schritte-entscheidungspunkte--red-phase-matrix) benannten offenen Design-Entscheidungen. Im Hinblick auf langfristige Wartbarkeit und eine spätere Reaktivierung der Windows-CI-Matrix ([`docs/CI_PLATFORM_STATUS.md`](../../docs/CI_PLATFORM_STATUS.md)) wurden folgende Architekturentscheidungen getroffen:

### Entscheidung 1: Gemeinsamer temporärer Arena-Root (`_root_path`) mit getrennter Topologie

```text
<tempfile.tempdir>/cubie_arena_<custom_id>_<hex>_<rand>/   # self._root_path
├── workspace/                                             # self.workspace_path (CWD, pre.fs, post.fs)
├── .venv/                                                 # self.virtual_path (Klon von base_env, VIRTUAL_ENV)
└── ipc_<rand>/  (TemporaryDirectory pro execute())        # je Lauf erzeugt und vor Verlassen abgeräumt
    ├── ipc_in<suffix>                                     # self._in_path
    ├── ipc_out<suffix>                                    # self._out_path
    └── _cubie_phantom.py                                  # Kopie von phantom_hook.py via shutil.copyfile
```

- **Wartbarkeit & `TempFS`-Symmetrie:** `self.workspace_path` enthält vom Moment des `setup()` bis nach `teardown()` ausschließlich `pre.fs`-Dateien und Target-Effekte. Ein einzelnes `shutil.rmtree(self._root_path, ...)` entfernt `.venv/`, `workspace/` und etwaige Reste atomar auch bei Teilfehlern in `setup()`.
- **Windows-CI-Vorbereitung:**
  - `.venv/` bleibt auf derselben Verzeichnistiefe direkt unter `_root_path` wie vor dem Fix, sodass `Lib/site-packages/...`-Pfade unter Windows keinen zusätzlichen `MAX_PATH`-Druck erhalten.
  - `_cubie_phantom.py` wird über `shutil.copyfile` statt `shutil.copy2` kopiert, damit keine schreibgeschützten Dateiberechtigungen aus installierten Wheels oder Read-Only-`site-packages` übernommen werden.
  - `PyVenv.teardown()` delegiert an `shutil.rmtree(self._root_path, onexc=_remove_readonly)`, das bei `PermissionError` gezielt `stat.S_IWRITE` setzt und den Löschaufruf wiederholt – eine direkte Schutzmaßnahme gegen Windows-typische Read-Only-Dateien in Venv-Klonen.
  - `ipc_<rand>/` wird über `tempfile.TemporaryDirectory(prefix="ipc_", dir=self._root_path)` erst nach Abschluss von `run_process(...)` abgeräumt, wenn alle Subprozess-Handles geschlossen sind.

### Entscheidung 2: Option 2 (`python -P` + Transport-First + gemeinsames `_DETACH_BOOTSTRAP`) gegen K6

- **Kindprozess-Start ohne implizites CWD (`-P`):** `PyVenv._execute_runner_script()` startet `[str(self._python_exe), "-P", "-c", script]` (`-P` existiert seit Python 3.11 plattformübergreifend auf Linux, macOS und Windows; `pyproject.toml:13` verlangt `requires-python >= 3.13`).
- **Härtung von `_inject_project_code()`:** Die Hilfsmethode `_safe_host_paths()` filtert leere Einträge (`""`), `"."` sowie case-insensitiv `site-packages` und `dist-packages` (`entry.lower()`, wichtig für Windows-Groß-/Kleinschreibung) aus `sys.path` und normalisiert übrige Einträge mit `Path(entry).absolute()`. Ist die Liste leer, wird `PYTHONPATH` sauber entfernt (`pop`), damit kein leerer Pfadanteil implizit wieder `cwd` einfügt.
- **Abwärtskompatibilität für `IPCC`:** `_setup_ipc_files(ipc_dir)` stellt `str(ipc_dir.absolute())` pro `execute()`-Lauf an den Anfang von `self._env_vars["PYTHONPATH"]` (da `_prepare_env()` bei jedem `execute()` eine frische `os.environ.copy()` erstellt, akkumulieren sich keine Pfade). Externe `IPCC`-Implementierungen bleiben in Signatur (`src/qb_cubie/protocols.py`) und Transport unverändert.
- **Transport-First & Pfad-Detaching in `codecs.py`:** Alle drei Runner (`_PICKLE_RUNNER`, `_MSGSPEC_RUNNER`, `_CLOUDPICKLE_RUNNER`) importieren zuerst die Transportmodule (`importlib`, `os`, `sys`, `pickle` bzw. `msgspec` + `msgspec.msgpack` bzw. `cloudpickle`, `_cubie_phantom as _phantom`) und führen unmittelbar danach die gemeinsame Konstante `_DETACH_BOOTSTRAP` aus:
  - ermittelt `_ipc` über `os.path.normcase(os.path.realpath(os.path.dirname(_phantom.__file__)))` (plattform- und symlink-normalisiert für Windows/macOS/Linux),
  - entfernt `_cubie_phantom` aus `sys.modules` (damit selbst User-Code mit `import _cubie_phantom` eine gleichnamige Datei aus dem Workspace laden kann, während `_phantom.activate_hook(decontams)` weiterhin über die lokale Variable aktiv ist),
  - entfernt `_ipc` und leere Einträge aus `sys.path` sowie `os.environ["PYTHONPATH"]`,
  - setzt `sys.path.insert(0, os.getcwd())` vor dem Laden/Importieren von Target und Workspace-Modulen.

### Entscheidung 3: Vollständige Bestands-Test-Migration ($Q_{\text{Ist}} \to Q_{\text{Soll}}$) statt Workarounds

Die vier historischen Tests in `test_ebt_arena.py` und die drei Fälle in `test_ebt_hydration_boundaries.py` prüften direkt das alte $Q_{\text{Ist}}$-Layout (`Path(".venv")` im Workspace). Sie wurden konsequent auf $Q_{\text{Soll}}$ umgestellt und in `test_linter.py` um die fehlende `.venv/bad_code.py`-Fixture ergänzt. Alle neuen und migrierten Tests nutzen `Path`, `resolve()`, `os.pathsep`, `venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt")`, prüfen `bin`/`Scripts` sowie `lib`/`Lib` und meiden POSIX-exklusive `timeout`/`max_output_bytes`-Optionen.

---

## Schritt 2 & 3: Test-Design, Äquivalenzklassen & Meta-QA-Prüfung

### Bestands-Test-Migrationen & Vacuous-Pass-Schließung

| Datei | Änderung | Zweck ($Q_{\text{Soll}}$) |
| :--- | :--- | :--- |
| [`tests/tests_linter/test_linter.py`](../tests_linter/test_linter.py#L17-L25) | `pre=WorldState(fs={".venv/bad_code.py": "tests/fixtures/bad_code.py"})` | Verhindert *Vacuous Pass* von `test_linter_discovery_and_ignores` auf leerem Workspace |
| [`tests/tests_arena/test_ebt_arena.py`](../tests_arena/test_ebt_arena.py#L255-L338) | Block `PROOF of WORKSPACE / '.venv' SEPARATION` mit `check_workspace_is_empty`, getrenntem `VIRTUAL_ENV`-Check (`bin`/`Scripts` & `lib`/`Lib`), `venv.name == ".venv"` und `venv.parent == cwd.parent` | Sichert sauberen Workspace (`list(Path.cwd().iterdir()) == []`) und getrennte Geschwister-`.venv` (4 Tests migriert, `test_workspace_root_is_clean` beibehalten) |
| [`tests/tests_arena/test_ebt_hydration_boundaries.py`](../tests_arena/test_ebt_hydration_boundaries.py#L214-L266) | `_minimal_symlink_base`, `test_pyvenv_hydration_cannot_write_through_base_symlinks` (3 Fälle: `file`, `tree`, `directory-basename`) + neu `test_pyvenv_hydration_rejects_sibling_venv_traversal` (`../.venv/payload.txt`, `../.venv`) | Belegt Konfliktfreiheit für `".venv"` / `".venv/..."` im Workspace bei unberührter `arena=str(base)` und Host-Datei sowie explizite Ablehnung von `../.venv`-Ausbrüchen |

### Neue Regressionstest-Suite (`tests/tests_arena/test_pyvenv_workspace_isolation.py`, 54 Testfälle)

Die Suite wurde mit schlanken Top-Level-Helfern (`_write_workspace_file`, `_inspect_runtime`, `_raise_zero_division`) und `@pytest.mark.parametrize` ohne `N×M`-EBT-Kreuzprodukte und ohne einsame Negationen (Meta-Gates 1–3) aufgebaut:

1. **Namenskollisionen K1–K3 über alle 3 Codecs (`PickleCodec`, `MSGspecCodec`, `CloudpickleCodec`):**
   - `test_pre_fs_ipc_in_is_not_overwritten` (3 Bytes `ipc_in<suffix>` gegen `os.path:getsize` + Voll-Workspace-Ref),
   - `test_pre_fs_ipc_out_is_preserved_after_execute` (5 Bytes `ipc_out<suffix>` bleibt über `execute()` erhalten),
   - `test_pre_fs_cubie_phantom_is_preserved_and_importable_with_decontams` + Gegenprobe `test_decontams_still_enforces_phantom_error_with_user_phantom_file` (User-`_cubie_phantom.py` bleibt erhalten und importierbar, während `decontams=["blocked_dep"]` weiterhin `PhantomObject` durchsetzt).
2. **Vollständige Workspace-Vergleiche (K4):**
   - `test_full_workspace_comparison_matches_empty_reference` (`fs={".": empty_ref}`),
   - `test_full_workspace_comparison_detects_unexpected_target_file` (Positivvertrag gegen Referenz + Negativ-Gegenprobe mit `EBT(..., expect=False)` gegen leeren Referenzordner),
   - `test_workspace_directory_listing_contains_only_hydrated_files` (`os:listdir(".")` sieht exakt `["alpha.txt", "sub"]`).
3. **`.venv`-Kollisionen im Workspace (K5):**
   - `test_pre_fs_dotvenv_file_and_directory_stay_isolated_from_arena_venv` (`mode="file"` und `"dir"`, prüft `os.path:isfile`, `post.fs` und unverändertes `post.arena`).
4. **Transport-Shadowing & Bootstrap-Detaching (K6):**
   - `test_workspace_modules_cannot_shadow_codec_transport` (15 Fälle: 3 Codecs × `pickle.py`, `msgspec.py`, `cloudpickle.py`, `importlib.py`, `_cubie_phantom.py`),
   - `test_empty_sys_path_entry_cannot_reintroduce_workspace_shadowing` (`sys.path` mit vorangestelltem `""` und `"."`),
   - `test_ipc_dir_is_removed_from_child_sys_path_and_pythonpath` (prüft `has_phantom_mod is False`, `sys_path[0] == cwd` sowie vollständiges Entfernen des IPC-Ordners aus `sys.path` und `PYTHONPATH`).
5. **Lebenszyklus & Leckfreiheit:**
   - `test_repeated_execute_calls_leave_workspace_and_root_clean` (zwei `execute()`-Aufrufe zwischen einem `setup()`/`teardown()`, prüft `_root_path`-Einträge `['.venv', 'workspace']` und 0 Reste in `tempfile.tempdir`),
   - `test_failed_setup_and_target_error_leave_zero_tempdir_leaks` (`hydration-escape`, `target-exception`, `relocation-error` mit Dummy-`native.exe`).

---

## Schritt 4: TGD Red-Phase & strikter Test-Freeze

Vor jeglicher Änderung in `src/` oder `docs/` (`git status --short` zeigte ausschließlich die Änderungen unter `tests/`) wurden am **20. November 2026** folgende Red-Phase-Läufe ausgeführt:

| Befehl | Ergebnis | Einordnung |
| :--- | :--- | :--- |
| `.venv/bin/python -m pytest -q tests/tests_meta/` | **`84 passed in 15.78s`** | Alle drei Meta-Gates (kanonische Imports, kein `N×M`-Kreuzprodukt, keine einsame Negation) bestehen auf den neuen/migrierten Tests. |
| `.venv/bin/python -m pytest -q -m "" tests/tests_linter/test_linter.py` | **`4 passed in 1.90s`** | `test_linter_discovery_and_ignores` prüft nun explizit die `.venv/bad_code.py`-Exclusion (zuvor ohne `-m ""` durch das `slow`-Default-Filter `4 deselected in 0.13s`). |
| `.venv/bin/python -m pytest -q tests/tests_arena/test_ebt_arena.py tests/tests_arena/test_ebt_hydration_boundaries.py --tb=line` | **`7 failed, 82 passed in 5.42s`** | Exakt die 4 migrierten Tests in `test_ebt_arena.py` und die 3 Fälle in `test_pyvenv_hydration_cannot_write_through_base_symlinks` schlagen gegen das alte Layout fehl; `test_pyvenv_hydration_rejects_sibling_venv_traversal` besteht bereits. |
| `.venv/bin/python -m pytest -q tests/tests_arena/test_pyvenv_workspace_isolation.py --tb=line` | **`43 failed, 11 passed in 4.60s`** | Alle 43 K1–K6- und `repeated_execute`-Verträge scheitern deterministisch am alten `PyVenv`-Verhalten (`11 passed`: 3× `decontams`-Gegenprobe, 5× nicht-kollidierende Codec/Shadow-Paare in `test_workspace_modules_cannot_shadow_codec_transport`, 3× Fehler-Cleanup). |

Anschließend wurden alle Testdateien unter `tests/**/*.py` für den gesamten Rest der Green-Phase **eingefroren** (keine nachträgliche Änderung und kein `GREEN_AUDIT` erforderlich).

---

## Schritt 5: TGD Green-Phase, Style-Metriken & Living-Documentation-Sync

### Core-Implementierung & Stil-Metriken (`src/`)

- **[`src/qb_cubie/arenas/pyvenv.py`](../../src/qb_cubie/arenas/pyvenv.py) (451 LOC, max. 12/12 Body-Zeilen in `get_state`, `_ensure_venv_exists`, `_ensure_codec_requirements`, `_base_environment`):**
  - `_remove_readonly(func, path, exc)` (`stat.S_IWRITE` bei `PermissionError`), `_ArenaState._root_path`, `PyVenv._prepare_directories()` (`root / "workspace"` und `root / ".venv"`), `PyVenv.teardown()` / `PyVenv.run()` über `_root_path`.
  - `PyVenv._run_in_subprocess()` (`11` Body-Zeilen) nutzt `tempfile.TemporaryDirectory(prefix="ipc_", dir=self._root_path)` und ruft `_setup_ipc_files(Path(ipc_dir))` (`10` Body-Zeilen, `shutil.copyfile` + `_prepend_ipc_pythonpath`) sowie `_teardown_ipc_files()` (`3` Body-Zeilen) auf.
  - `PyVenv._safe_host_paths()` filtert `""`, `"."` und case-insensitiv `site-packages`/`dist-packages`; `PyVenv._execute_runner_script()` startet `[str(self._python_exe), "-P", "-c", script]`.
- **[`src/qb_cubie/arenas/codecs.py`](../../src/qb_cubie/arenas/codecs.py) (352 LOC, max. 10/12 Body-Zeilen in `_serialization_error`):**
  - Gemeinsamer Block `_DETACH_BOOTSTRAP` und Helfer `_render_runner(template, in_path, out_path)` für alle drei `get_runner_snippet()`-Implementierungen.
  - Dedentierte Runner `_PICKLE_RUNNER`, `_MSGSPEC_RUNNER` und `_CLOUDPICKLE_RUNNER` importieren Transportmodule und `_cubie_phantom as _phantom` vor `{bootstrap}` und erhalten `in_path`/`out_path` als String-Literale in `co_consts`.

### Green-Phase-Verifikation (bei eingefrorener Testsuite)

| Lauf | Ergebnis | Abgedeckte Schichten |
| :--- | :--- | :--- |
| `.venv/bin/python -m pytest -q tests/tests_arena/test_pyvenv_workspace_isolation.py tests/tests_arena/test_ebt_arena.py tests/tests_arena/test_ebt_hydration_boundaries.py` | **`143 passed in 10.86s`** | Alle 43 vormals roten Isolations-Tests + alle 7 vormals roten Alt-Migrationen auf 100 % Grün |
| `.venv/bin/python -m pytest -q tests/tests_arena/ -m ""` | **`339 passed in 64.38s (0:01:04)`** | Gesamte Arena-Suite inkl. `slow`-Tests (`test_ebt_resource_limits.py`, `test_ebt_console_environment.py`, `test_security_arena_codec.py`, `TempFS`) |
| `.venv/bin/python -m pytest -q -m "" tests/tests_linter/ tests/tests_ebt/test_ebt_imports.py tests/tests_ebt/test_ebt_ignores.py` | **`140 passed, 6 warnings in 15.28s`** | Linter-Arenen (`Pylint`, `MyPy`, `AstLinter`), EBT-Imports (`decontams`, relative/absolute Imports) & Ignores |
| `.venv/bin/python -m pytest -q -m "" tests/test_styleguide.py tests/test_lint.py tests/tests_meta/` | **`107 passed in 41.51s`** | `ruff`, `pylint --enable=unreachable`, `mypy --warn-unreachable --check-untyped-defs`, `FUNCTION_LIMIT=12`, `MODULE_LIMIT=777`, `DocEnsurance`, Meta-Gates 1–3 |

### Living-Documentation-Sync (`docs/`, `KNOWN_ISSUES.md`, `CHANGELOG.md`)

1. [`docs/core/GUIDE_Arena-Management.md`](../../docs/core/GUIDE_Arena-Management.md): Getrennte `.venv`-/`workspace/`-/IPC-Ablage ergänzt sowie veraltete Aussage zur fehlenden Hydrierungsgrenze (Z. 178) korrigiert.
2. [`docs/dev/DEV-GUIDE_2-3_Arenas.md`](../../docs/dev/DEV-GUIDE_2-3_Arenas.md): `_root_path`-Topologie, `python -P -c` + `PYTHONPATH`-Filterung und Transport-First-Detaching für `IPCC`-Codecs dokumentiert; Hydrierungsgrenzen-Widerspruch bereinigt.
3. [`docs/core/GUIDE_Contract-Semantics.md`](../../docs/core/GUIDE_Contract-Semantics.md): Konsistentes `fs={".": ...}`-Verhalten für `TempFS` und `PyVenv` sowie Unereichbarkeit der geklonten `.venv` für `pre.fs`-Hydrierung ergänzt.
4. [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md): `[BUG-001]` nach [`DEV-GUIDE_Write-down-the-bugs.md`](../../docs/dev/DEV-GUIDE_Write-down-the-bugs.md) in `## Behoben (Archiv)` verschoben.
5. [`CHANGELOG.md`](../../CHANGELOG.md): Abschnitt `## [Unreleased]` mit `### Behoben` für `[BUG-001]` angelegt.
6. Abschließender Dokument-Check `.venv/bin/python -m pytest -q tests/test_styleguide.py`: **`14 passed in 18.93s`** (`DocEnsurance` + `CUBIE_DOC_RULES` + `CUBIE_DOCFRAME_RULES` ohne Befund).

### Gesamtabnahme über das gesamte Repository

```bash
.venv/bin/python -m pytest -m "" -q
```

- **Ergebnis:** **`1812 passed, 11 skipped, 6 warnings in 405.12s (0:06:45)`** (`Exit Code 0`).

---

## Reflexion zum TGD-Muster & Ausblick (Windows-CI-Reaktivierung)

### Erfahrungen aus dem ersten Komplett-Durchlauf

1. **Trennung von $Q_{\text{Ist}}$-Migration und Regressionstest-Freeze trägt:** Durch die gezielte Bestandsaufnahme in `ANALYSIS.md` ließen sich alle sieben $Q_{\text{Ist}}$-gekoppelten Bestands-Tests vorab isolieren, auf $Q_{\text{Soll}}$ umstellen und gemeinsam mit den 54 neuen Verträgen einfrieren. Die Green-Phase traf dadurch auf Anhieb alle 143 Verträge ohne nachträgliche Test-Anpassungen.
2. **`slow`-Marker bei gezielten Reproduktionsläufen beachten:** Da `pyproject.toml` standardmäßig `-m 'not slow'` setzt, hätte ein Aufruf von `test_linter.py` ohne `-m ""` die Tests still übersprungen (`4 deselected`). Für TGD-Protokolle empfiehlt sich bei `slow`-markierten Modulen stets das explizite `-m ""`.
3. **Gemeinsamer `_DETACH_BOOTSTRAP`-Baustein:** Die Auslagerung der Pfad-Bereinigung in eine einzige Konstante in `codecs.py` vermeidet Duplikate über drei Codecs hinweg und bleibt gleichzeitig unterhalb des 12-Zeilen-Styleguide-Limits.

### Nächste Schritte zur Reaktivierung von `windows-2022` in `.github/workflows/ci.yml`

Diese Reparatur hält alle neuen Pfade und Cleanup-Schritte (`_remove_readonly`, `shutil.copyfile`, `os.path.normcase(os.path.realpath(...))`, `python -P`, plattformneutrale Tests) Windows-kompatibel. Für das tatsächliche Wiederaktivieren des `windows-2022`-Runners verbleiben gemäß [`docs/CI_PLATFORM_STATUS.md`](../../docs/CI_PLATFORM_STATUS.md#4-roadmap-zur-reaktivierung-von-windows) noch folgende davon unabhängige Schritte:
1. `PATH`-Bereinigung in `PyVenv._activate_arena_env()` / Subprozess-Umgebung (sofern für Windows-System-DLLs in `System32` / `%SystemRoot%` unter restriktivem `PATH` erforderlich),
2. Unterstützung bzw. sauber dokumentierte `sys.executable -m ...`-Nutzung anstelle nativer Windows-`.exe`-Launcher-Relokation in `_relocation.py` und
3. POSIX-Prozessgruppen-/Job-Object-Behandlung für optionale `timeout`/`max_output_bytes`-Limits (`_process.py`).
