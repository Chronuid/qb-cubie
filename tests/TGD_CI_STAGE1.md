<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Orchestrator (Neon)" effort="High" -->
# TGD-Protokoll 2: CI-Matrix-Stärkung — Stufe 1 (`macos-15` Repository-Suite & Reaktivierung `CI / Wheel / windows-2022`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Orchestrator (Neon)
- **Reasoning-Effort:** High
- **Durchführungsdatum:** 20. November 2026, ~ 12:15 (CET)
- **Synthesebasis:** `tests/GEMINI.md`, `tests/ANALYSIS_CI_MATRIX.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/CI_PLATFORM_STATUS.md`, `docs/core/GUIDE_Arena-Management.md`, `docs/dev/DEV-GUIDE_2-3_Arenas.md`, `docs/dev/Style-Guide.md`, `src/qb_cubie/arenas/_process_win32.py`, `src/qb_cubie/arenas/_process.py`, `src/qb_cubie/arenas/tempfs.py`, `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/arenas/_relocation.py`, `src/qb_cubie/services/doc_frame/doc_frame.py`, `scripts/check_wheel.py`, `experiments/benchmarks/cubie_benchmarks/execution/_process.py`, `experiments/ollama-agents/ollama_agents/reviewer/tools.py`, `.github/workflows/ci.yml`, `KNOWN_ISSUES.md`, `CHANGELOG.md`
- **Stand:** qb-cubie (`v0.0.9`, gemäß `pyproject.toml:7`, Ausgangs-Commit `518cf28f`)
- **Git-Log:** `git log -n 1`

---

---
<!-- /qb:frame -->

## Kurzfassung

Dieser TGD-Durchlauf setzt **Stufe 1** der in [`ANALYSIS_CI_MATRIX.md`](./ANALYSIS_CI_MATRIX.md) entworfenen Roadmap um (freigegebene Entscheidungen **`E1-A`**, **`E2-B`**, **`E4-Split` + `M2`**, **`E5-A`**):

1. **macOS (`macos-15`) für `CI / Repository` vorbereitet und aktiviert:**
   - Symlink-Wurzeln aus `tempfile.mkdtemp()` (`/var` $\to$ `/private/var`) werden in [`TempFS.setup()`](../src/qb_cubie/arenas/tempfs.py#L94) und [`PyVenv._prepare_directories()`](../src/qb_cubie/arenas/pyvenv.py#L167) kanonisch über `.resolve()` aufgelöst; [`_relocation._relative_to_base()`](../src/qb_cubie/arenas/_relocation.py#L36-L43) löst Symlink-Basispfaddifferenzen in `_relocate_link()` auf.
   - [`TempFS.teardown()`](../src/qb_cubie/arenas/tempfs.py#L118-L119) und [`pyvenv._remove_readonly()`](../src/qb_cubie/arenas/pyvenv.py#L49-L56) bereinigen schreibgeschützte Dateien und Verzeichnisse robust über `onexc=_remove_readonly`.
   - In [`.github/workflows/ci.yml`](../.github/workflows/ci.yml#L36-L59) läuft der `tests`-Job nun für `ubuntu-24.04` und `macos-15` (`Python 3.13` & `3.14`) getrennt als `-m "not slow" -q` gefolgt von `-m slow -q` bei `timeout-minutes: 35`; [`test_ci_platform_stage1.py`](./tests_arena/test_ci_platform_stage1.py#L196-L234) ergänzt einen portablen POSIX-Prozessgruppen-Timeout-EBT ohne `/proc`-Abhängigkeit.
2. **`CI / Wheel / windows-2022` in `.github/workflows/ci.yml` reaktiviert:**
   - **Win32-Limits (`E1-A`):** Neues Hilfsmodul [`src/qb_cubie/arenas/_process_win32.py`](../src/qb_cubie/arenas/_process_win32.py) erzwingt `timeout` und `max_output_bytes` unter `os.name == "nt"` über Win32 Job Objects (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` / `TerminateJobObject` + `taskkill`-Fallback) und zwei unbuffered Daemon-Reader-Threads mit gemeinsamem Byte-Budget; [`_process.py`](../src/qb_cubie/arenas/_process.py#L16-L36) schaltet sauber auf das Win32-Backend um und lehnt nur noch sonstige unbekannte OS ab.
   - **Wheel-, Benchmarks-, Agent-, Launcher- & DocFrame-Härtung:** [`scripts/check_wheel.py`](../scripts/check_wheel.py#L22-L54) isoliert Windows-`PATH` über `build_wheel_environment()` ohne `orig_path`-Leak; [`cubie_benchmarks/execution/_process.py`](../experiments/benchmarks/cubie_benchmarks/execution/_process.py#L37-L85) ergänzt Windows-Systempfade, `PYTHONUTF8="1"` und UTF-8-Decoding; [`ollama_agents/reviewer/tools.py`](../experiments/ollama-agents/ollama_agents/reviewer/tools.py#L60-L97) ersetzt `os.killpg` auf Windows durch `CREATE_NEW_PROCESS_GROUP` + `taskkill`; [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py#L25-L67) akzeptiert Windows-Interpretervarianten (`pythonw3.13.exe`, `python3.13t.exe`, `python_d.exe`) und erkennt Backslash-Basispfade in Einstiegsskripten; [`doc_frame.py`](../src/qb_cubie/services/doc_frame/doc_frame.py#L211) schreibt explizit `newline="\n"`.

---

## Ablauf nach dem 5-Schritte-TGD-Prozess

### Phase A: Red-Phase & Test-Freeze (`tests/`)

Ausschließlich unter `tests/` wurden vor jeder Änderung an `src/`, `scripts/`, `experiments/` oder `.github/` folgende Prüfungen angepasst bzw. neu geschaffen:
- [`tests/tests_arena/test_ci_platform_stage1.py`](./tests_arena/test_ci_platform_stage1.py): neue Regressions- und Plattformvertragssuite für `M1`, `M2`, `W1` (`E1-A`), `W2`, `W3`, `W4` und `W6`.
- [`tests/tests_arena/test_process_limits.py`](./tests_arena/test_process_limits.py#L34-L87): Migration von `test_unsupported_platform_rejects_limits_explicitly` auf `os.name == "java"`, neuer Vertrag `test_windows_platform_accepts_limits_validation` und Ausweitung der Limit-Proben auf `posix` und `nt`.
- [`tests/wheel/smoke_installed.py`](./wheel/smoke_installed.py#L135-L136) und [`tests/wheel/ollama_agents_installed.py`](./wheel/ollama_agents_installed.py#L125): kanonischer `realpath`/`normcase`-Pfadvergleich für MyPy bzw. explizites `encoding="utf-8"`.

**Ergebnisse in Phase A (`HEAD = 518cf28f` unverändert):**
- Meta-Gates 1–3 (`.venv/bin/python -m pytest tests/tests_meta/ -q`): **`84 passed in 16.06s`** (0 Verstöße).
- Ziel-Tests (`.venv/bin/python -m pytest tests/tests_arena/test_ci_platform_stage1.py tests/tests_arena/test_process_limits.py -q`): **`19 failed, 28 passed in 1.35s`** (scharfes Red-Signal auf allen neuen/migrierten Verträgen für `M1`, `W1`, `W2`, `W3`, `W4`, `W6` und `_process.validate_limits`).

### Phase B: Green-Phase unter Test-Freeze

Alle Änderungen an [`_process_win32.py`](../src/qb_cubie/arenas/_process_win32.py), [`_process.py`](../src/qb_cubie/arenas/_process.py), [`tempfs.py`](../src/qb_cubie/arenas/tempfs.py), [`pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py), [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py), [`doc_frame.py`](../src/qb_cubie/services/doc_frame/doc_frame.py), [`scripts/check_wheel.py`](../scripts/check_wheel.py), [`cubie_benchmarks/execution/_process.py`](../experiments/benchmarks/cubie_benchmarks/execution/_process.py), [`ollama_agents/reviewer/tools.py`](../experiments/ollama-agents/ollama_agents/reviewer/tools.py) und [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) wurden implementiert.

> [!NOTE]
> **Transparenter Re-Plan-Eintrag zum Test-Freeze:** Im ersten Green-Lauf (`88 passed, 2 failed`) stellte sich heraus, dass `test_check_wheel_windows_env_isolates_path_without_host_leak` durch `ntpath.dirname(str(python))` in [`scripts/check_wheel.py`](../scripts/check_wheel.py#L44) ohne Test-Änderung grün wurde, während [`test_ci_platform_stage1.py#L500`](./tests_arena/test_ci_platform_stage1.py#L500) im eigenen Test-Assert `caught.value.code == "agent_timeout"` statt des realen Attributs `AdapterError.status` ([`errors.py#L9`](../experiments/ollama-agents/ollama_agents/errors.py#L9)) geprüft hatte. Gemäß Re-Plan-Protokoll wurde dieser Test-Spec-Tippfehler per Plan-Review explizit korrigiert (`caught.value.status == "agent_timeout"`), danach sofort wieder eingefroren und ohne weitere Produktionsänderungen vollständig grün verifiziert (`90 passed in 7.53s`).

---

## Verifikation, Styleguide & Qualitäts-Gates (Phase C3)

### Styleguide-Kennzahlen der geänderten/neuen Core-Module

| Modul | Gesamtzeilen (Limit `777`) | Längste Funktion (Limit `12`) |
| :--- | :---: | :---: |
| [`src/qb_cubie/arenas/_process_win32.py`](../src/qb_cubie/arenas/_process_win32.py) *(neu)* | `281` | `11` (`run_win32_process` L239) |
| [`src/qb_cubie/arenas/_process.py`](../src/qb_cubie/arenas/_process.py) | `185` | `12` (`run_process` L22) |
| [`src/qb_cubie/arenas/tempfs.py`](../src/qb_cubie/arenas/tempfs.py) | `172` | `12` (`get_state` L98) |
| [`src/qb_cubie/arenas/pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py) | `453` | `12` (`get_state` L137) |
| [`src/qb_cubie/arenas/_relocation.py`](../src/qb_cubie/arenas/_relocation.py) | `113` | `11` (`_shell_header` L96) |
| [`src/qb_cubie/services/doc_frame/doc_frame.py`](../src/qb_cubie/services/doc_frame/doc_frame.py) | `341` | `10` (`run` L202) |

### Ausgeführte Test- und Prüfläufe (alle nach letzter Produkt- und Doku-Änderung)

| Prüfung / Kommando | Ergebnis | Scope / Anmerkung |
| :--- | :---: | :--- |
| `.venv/bin/python -m pytest tests/tests_arena/test_ci_platform_stage1.py tests/tests_arena/test_process_limits.py tests/tests_arena/test_ebt_tempfs.py tests/tests_arena/test_ebt_console_environment.py tests/tests_services/tests_doc_frame/test_docframe_cli.py -q` | **`90 passed`** `(7.53s)` | Gezielte Stufe-1- & Bestands-Arena/DocFrame-Regressionen |
| `.venv/bin/python -m pytest experiments/tests/ollama_agents/reviewer/test_role_boundaries.py experiments/tests/benchmarks/phase3/test_process_adapter.py -q` | **`37 passed`** `(8.91s)` | Experiments-Adapter- & Timeout-Regressionen |
| `.venv/bin/python -m pytest tests/test_styleguide.py tests/tests_meta/ -q` | **`98 passed`** `(35.31s)` | Styleguide, `DocEnsurance`, `DocFrame`, Meta-Gates 1–3 |
| `.venv/bin/python -m pytest tests/test_lint.py -m "" -q` | **`9 passed`** `(7.27s)` | `ruff`, `pylint --enable=unreachable`, `mypy --warn-unreachable --check-untyped-defs` |
| `.venv/bin/python -m pytest tests/tests_arena/ -m "" -q` | **`359 passed`** `(66.48s)` | Vollständige Arena-Suite inkl. `/proc`-Watchdog & Stufe-1-Suiten |
| `.venv/bin/python -m pytest -m "not slow" -q` | **`1670 passed, 11 skipped, 162 deselected`** `(189.78s)` | Gesamte Fast-Repository-Suite (6 erwartete UserWarnings in bestands-IPC/TempFS-Tests; 11 plattform-/tk-bedingte Skips im Bestand) |

*Hinweis zur Plattformabdeckung:* Alle obigen Läufe wurden lokal unter Linux verifiziert; die native Laufzeitabnahme auf den GitHub-Actions-Runnern `macos-15` (`CI / Repository`) und `windows-2022` (`CI / Wheel`) erfolgt über den aktualisierten Workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

---

## Synchronisierte Dokumentation & nächste Stufe

- **Synchronisierte Dokumente:** [`docs/CI_PLATFORM_STATUS.md`](../docs/CI_PLATFORM_STATUS.md), [`docs/core/GUIDE_Arena-Management.md`](../docs/core/GUIDE_Arena-Management.md), [`docs/dev/DEV-GUIDE_2-3_Arenas.md`](../docs/dev/DEV-GUIDE_2-3_Arenas.md), [`KNOWN_ISSUES.md`](../KNOWN_ISSUES.md), [`CHANGELOG.md`](../CHANGELOG.md).
- **Ausblick Stufe 2 (`CI / Repository / windows-2022`):** Im anschließenden Zyklus folgen gemäß [`ANALYSIS_CI_MATRIX.md`](./ANALYSIS_CI_MATRIX.md) noch `E2-A` (sichere `.exe`-Console-Script-Relokation für `distlib`/`pip` + `uv-trampoline` in `_relocation_win32.py`), `E3-A` (POSIX-Slashes `/` in FS-/Arena-Diffs von `ebt.py` und `reporter.py`), `W9` (Bereinigung verbliebener POSIX-Shell-/Symlink-Altlasten in Repository-Tests) sowie `W10` (explizite UTF-8-Subprocess-Parameter in `mypy.py`/`pylint.py`/`_requirements.py` inkl. 3 Monkeypatch-Test-Doubles) vor der Freischaltung von `windows-2022` im `tests`-Job.
