<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Orchestrator (Neon)" effort="High" -->
# TGD-Protokoll 3: CI-Matrix-Stärkung — Stufe 2 (`CI / Repository / windows-2022`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Orchestrator (Neon)
- **Reasoning-Effort:** High
- **Durchführungsdatum:** 20. November 2026, ~ 12:40 (CET)
- **Synthesebasis:** `tests/GEMINI.md`, `tests/ANALYSIS_CI_MATRIX.md`, `tests/TGD_CI_STAGE1.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/CI_PLATFORM_STATUS.md`, `docs/core/GUIDE_Arena-Management.md`, `docs/dev/DEV-GUIDE_2-3_Arenas.md`, `docs/dev/Style-Guide.md`, `src/qb_cubie/arenas/_relocation_win32.py`, `src/qb_cubie/arenas/_relocation.py`, `src/qb_cubie/arenas/_hydration.py`, `src/qb_cubie/arenas/_requirements.py`, `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/ebt.py`, `src/qb_cubie/reporter.py`, `src/qb_cubie/linters/mypy.py`, `src/qb_cubie/linters/pylint.py`, `scripts/provision_test_arenas.py`, `.github/workflows/ci.yml`, `KNOWN_ISSUES.md`, `CHANGELOG.md`
- **Stand:** qb-cubie (`v0.0.9`, gemäß `pyproject.toml:7`, Ausgangs-Commit `574282fe`)
- **Git-Log:** `git log -n 1`
```text
commit 574282fe6a34192d54aa8ca7483723af72201b86 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Fri Nov 20 12:19:05 2026 +0100

    TGD_CI_STAGE1
```

---

---

<!-- /qb:frame -->

## Kurzfassung

Dieser TGD-Durchlauf schließt **Stufe 2** der in [`ANALYSIS_CI_MATRIX.md`](./ANALYSIS_CI_MATRIX.md) entworfenen CI-Stärkung ab (`E2-A`, `E3-A`, `W9`, `W10`) und schaltet `windows-2022` im `tests`-Job von [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) neben `ubuntu-24.04` und `macos-15` für die vollständige Repository-Suite frei:

1. **Sichere Windows-`.exe`-Console-Script-Relokation (`E2-A`):**
   - Neues Hilfsmodul [`src/qb_cubie/arenas/_relocation_win32.py`](../src/qb_cubie/arenas/_relocation_win32.py) (`191` LOC, max. `12` Body-Zeilen) übernimmt die doppelte Formatprüfung für [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py):
     - **`uv 0.11.3` PE-Ressourcen-Trampolines (`_relocate_uv_trampoline`):** Liest `RT_RCDATA=10`-Ressourcen (`UV_TRAMPOLINE_KIND == b"\x01"`, `UV_PYTHON_PATH`), schließt das Daten-Handle via `FreeLibrary` strikt **vor** `BeginUpdateResourceW`, toleriert sichere relative Python-Ziele ohne `..`-Ausbruch und schreibt absolute `<base>\...\python*.exe`-Ziele sauber auf den Klon um.
     - **`distlib`/`pip`-ZIP-Wrapper (`_relocate_distlib_launcher`):** Prüft `MZ`-Header, `#!`-Shebang und trailing ZIP (`PK\x05\x06`-EOCD + `PK\x03\x04`) und schreibt den Klon-Interpreter inkl. Leerzeichen-Quoting um.
     - Beliebige übrige native `.exe`-Binaries (`native.exe`), falsche `LauncherKind`-Tags oder externe Interpreterziele werden unverändert mit `RuntimeError("Unsupported console entry point...")` abgelehnt.
2. **Plattformübergreifende POSIX-Diff-Normalisierung (`E3-A`):**
   - [`EBT._generate_diff()` / `_modified_paths()`](../src/qb_cubie/ebt.py#L701-L719) verwenden `.as_posix()`; [`PytestReporter._posix_path()` / `_summarize_fs_diffs()`](../src/qb_cubie/reporter.py#L205-L218) normieren alle FS-/Arena-Diff-Schlüssel über Vorwärtsschrägstriche (`/`).
3. **Subprocess-Encoding-, Hydrierungs-, Provisionierungs- & Test-Hygiene (`W9`, `W10`):**
   - [`mypy.py`](../src/qb_cubie/linters/mypy.py#L79-L84), [`pylint.py`](../src/qb_cubie/linters/pylint.py#L88-L94) und [`_requirements.py`](../src/qb_cubie/arenas/_requirements.py#L93-L100) setzen explizit `encoding="utf-8", errors="replace"`; [`pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py#L439-L453) decodiert `uv`-Fehlermeldungen mit `errors="replace"`; [`_hydration.py`](../src/qb_cubie/arenas/_hydration.py#L28) trimmt trailing `/\\`; [`scripts/provision_test_arenas.py`](../scripts/provision_test_arenas.py#L36-L48) nutzt `onexc=_remove_readonly`.
   - Bestehende POSIX-Altlasten in Repository-Tests (`/tmp`/`touch` in `test_security_arena_codec.py`, `python3`/`echo` in `test_basic_mp.py`/`test_multiprocess.py`, `shlex.split`/`bin/python` in `test_offline_core.py`, `symlinks=True`, `site.getsitepackages()[0]`, Backslash-Helfer in `test_ebt_fs_collisions.py`/`test_fs_reporting.py`, fehlendes `encoding="utf-8"` sowie 3 Linter-Test-Doubles) wurden portabel auf $Q_{\text{Soll}}$ migriert.

---

## Ablauf nach dem 5-Schritte-TGD-Prozess

### Phase A: Red-Phase & Test-Freeze (`tests/`)

Vor jeder Produktionsänderung wurden die neuen Kontrakte in [`tests/tests_arena/test_ci_platform_stage2.py`](./tests_arena/test_ci_platform_stage2.py) erstellt und die portablen/Linter-Test-Migrationen vorgenommen (`test_mypy_analysis_integrity.py`, `test_mypy_process_status.py`, `test_pylint_analysis_integrity.py`, `test_security_arena_codec.py`, `test_basic_mp.py`, `test_multiprocess.py`, `test_offline_core.py`, `test_ebt_hydration_boundaries.py`, `test_arena_requirements.py`, `test_exception_observations.py`, `test_ebt_arena_mutation.py`, `test_ebt_fs_collisions.py`, `test_fs_reporting.py`, `test_quality_gate.py`, `test_ebt_arena.py`, `test_ebt_imports.py`, `test_ebt_persistent_reports.py`, `test_ebt_typing.py`).

**Ergebnisse in Phase A (vor Produktions-Edits):**
- Meta-Gates 1–3 (`.venv/bin/python -m pytest tests/tests_meta/ -q`): **`84 passed in 16.66s`**.
- Ziel-Tests (`test_ci_platform_stage2.py`, `test_mypy_analysis_integrity.py`, `test_mypy_process_status.py`, `test_pylint_analysis_integrity.py`): **`100 failed, 5 passed, 1 skipped in 0.49s`** (scharfes Red-Signal auf allen neuen Verträgen sowie auf den UTF-8-Assertions der 3 Linter-Integritätssuiten; `1 skipped` = nativer Windows-`cowsay.exe`-Test auf Linux).
- Bereits auf Linux grüne migrierte Bestands-Tests (220 Fälle über die 8 geänderten Alttest-Module): **`220 passed in 33.39s`**.

### Phase B: Green-Phase unter striktem Test-Freeze

Ohne weitere Änderung unter `tests/**/*.py` wurden [`_relocation_win32.py`](../src/qb_cubie/arenas/_relocation_win32.py), [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py), [`ebt.py`](../src/qb_cubie/ebt.py), [`reporter.py`](../src/qb_cubie/reporter.py), [`_hydration.py`](../src/qb_cubie/arenas/_hydration.py), [`_requirements.py`](../src/qb_cubie/arenas/_requirements.py), [`pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py), [`mypy.py`](../src/qb_cubie/linters/mypy.py), [`pylint.py`](../src/qb_cubie/linters/pylint.py), [`scripts/provision_test_arenas.py`](../scripts/provision_test_arenas.py) und [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) umgesetzt. Im ersten Styleguide-Lauf fiel lediglich `_relocate_distlib_launcher` mit 15 Body-Zeilen auf und wurde sauber über `_rewrite_distlib_bytes` in zwei kompakte Funktionen aufgeteilt (**≤ 12 Body-Zeilen**, `test_function_size` anschließend 100 % grün).

---

## Verifikation, Styleguide & Gesamtabnahme (Phase C3)

### Styleguide-Kennzahlen der geänderten/neuen Core-Module

| Modul | Gesamtzeilen (Limit `777`) | Längste Funktion (Limit `12`) |
| :--- | :---: | :---: |
| [`src/qb_cubie/arenas/_relocation_win32.py`](../src/qb_cubie/arenas/_relocation_win32.py) *(neu)* | `191` | `12` (`_relocate_uv_trampoline` L55) |
| [`src/qb_cubie/arenas/_relocation.py`](../src/qb_cubie/arenas/_relocation.py) | `116` | `11` (`_shell_header` L99) |
| [`src/qb_cubie/arenas/_hydration.py`](../src/qb_cubie/arenas/_hydration.py) | `151` | `12` (`_checked` L95) |
| [`src/qb_cubie/arenas/_requirements.py`](../src/qb_cubie/arenas/_requirements.py) | `184` | `11` (`_inspect_environment` L93) |
| [`src/qb_cubie/arenas/pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py) | `455` | `12` (`get_state` L137) |
| [`src/qb_cubie/ebt.py`](../src/qb_cubie/ebt.py) | `751` | `12` (`_validate_wrapper_keys` L600) |
| [`src/qb_cubie/reporter.py`](../src/qb_cubie/reporter.py) | `406` | `12` (`report` L39) |
| [`src/qb_cubie/linters/mypy.py`](../src/qb_cubie/linters/mypy.py) | `97` | `10` (`check` L31) |
| [`src/qb_cubie/linters/pylint.py`](../src/qb_cubie/linters/pylint.py) | `107` | `8` (`_build_command` L39) |

### Ausgeführte Abnahme-Prüfungen (nach letztem Code- & Doku-Edit)

| Prüfung / Kommando | Ergebnis | Scope / Anmerkung |
| :--- | :---: | :--- |
| `.venv/bin/python -m pytest tests/tests_arena/test_ci_platform_stage2.py -q` | **`16 passed, 1 skipped`** `(0.15s)` | Gezielte Stufe-2-Suite (`test_windows_native_cowsay_launcher_runs_from_clone` auf Linux übersprungen) |
| `.venv/bin/python -m pytest tests/test_styleguide.py tests/tests_meta/ -q` | **`98 passed`** `(35.20s)` | Styleguide (`FUNCTION_LIMIT=12`, `MODULE_LIMIT=777`), `DocEnsurance`, `DocFrame`, Meta-Gates 1–3 |
| `.venv/bin/python -m pytest tests/test_lint.py -m "" -q` | **`9 passed`** `(7.45s)` | `ruff`, `pylint --enable=unreachable`, `mypy --warn-unreachable --check-untyped-defs` |
| `.venv/bin/python -m pytest tests/tests_arena/ -m "" -q` | **`375 passed, 1 skipped`** `(67.23s)` | Gesamte Arena-Suite inkl. `/proc`-Watchdog, Stufe 1 & Stufe 2 |
| `.venv/bin/python -m pytest tests/tests_linter/ tests/tests_user_workflows/test_quality_gate.py tests/tests_user_workflows/test_fs_reporting.py -m "" -q` | **`182 passed`** `(29.26s)` | Linter-Integrität (`MyPy`/`Pylint` UTF-8) & Reporting-/Quality-Gate-Workflows |
| `.venv/bin/python -m pytest -m "not slow" -q` | **`1686 passed, 12 skipped, 162 deselected`** `(182.98s)` | Gesamte Fast-Repository-Suite (6 erwartete Bestands-UserWarnings; 12 plattform-/tk-bedingte Skips) |

*Hinweis zur Plattformabdeckung:* Alle obigen Läufe wurden lokal unter Linux verifiziert; die native Ausführung von `Wheel` und `Repository` auf den GitHub-Actions-Runnern `macos-15` und `windows-2022` erfolgt im Workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

---

## Synchronisierte Dokumentation

- [`docs/CI_PLATFORM_STATUS.md`](../docs/CI_PLATFORM_STATUS.md) (Plattform-Matrix auf **Tier 1 Aktiv — Stufe 2** für `ubuntu-24.04`, `macos-15` und `windows-2022` gehoben)
- [`docs/core/GUIDE_Arena-Management.md`](../docs/core/GUIDE_Arena-Management.md) (unterstützte `uv`-PE-Ressourcen-Trampolines & `distlib`-ZIP-Wrapper dokumentiert)
- [`docs/dev/DEV-GUIDE_2-3_Arenas.md`](../docs/dev/DEV-GUIDE_2-3_Arenas.md) (`_relocation_win32.relocate_windows_launcher()` integriert)
- [`KNOWN_ISSUES.md`](../KNOWN_ISSUES.md) & [`CHANGELOG.md`](../CHANGELOG.md)
