<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Orchestrator (Argon) -> Gemini 4 Neon" effort="High -> Medium" -->
# TGD-Protokoll 4: CI-Matrix-Stärkung — Stufe 3 (Red-Phase & Test-Freeze nach CI-Run `44735125009`)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Orchestrator (Argon) → *Run-Interrupt (Quota)* → Gemini 4 Neon
- **Reasoning-Effort:** High (Audit/Analyse) → Medium (Red-Phase & Test-Freeze)
- **Durchführungsdatum:** 20. November 2026, ~ 17:33 (CET)
- **Synthesebasis:** `tests/GEMINI.md`, `tests/CI-Data.md`, `tests/TGD_CI_STAGE2.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/CI_PLATFORM_STATUS.md`, `docs/dev/README.md`, `docs/dev/Style-Guide.md`, `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/arenas/_process.py`, `src/qb_cubie/arenas/_relocation.py`, `experiments/benchmarks/cubie_benchmarks/reporting/_files.py`, `experiments/benchmarks/cubie_benchmarks/data/{smoke,base}/scenarios/**/*.py.txt`, `tests/tests_user_workflows/test_fs_reporting.py`, `tests/tests_user_workflows/test_settings_bundle.py`, `tests/test_offline_core.py`
- **Stand:** qb-cubie (`v0.0.10`, gemäß `pyproject.toml:7`, Ausgangs-Commit `93830b69` auf Branch `experimental`)
- **Git-Log:** `git log -n 1`
```text
commit 93830b69df045ecb74862e5cdf297a11ea94ffb2 (HEAD -> experimental)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Fri Nov 20 13:53:25 2026 +0100

    Tried CI. Got Test-Data.
```

---

---

<!-- /qb:frame -->

## Kurzfassung

Dieser TGD-Durchlauf verarbeitet die echten GitHub-Actions-Ergebnisse aus **CI-Run `44735125009`** (Commit `98bf4247`, `v0.0.10`, dokumentiert in [`tests/CI-Data.md`](./CI-Data.md)) über alle 12 Matrix-Jobs (`Wheel` & `Repository` × `ubuntu-24.04`, `macos-15`, `windows-2022` × Python `3.13`, `3.14`).

Gemäß bewusster Entscheidung nach einem **Run-Interrupt (Quota-Limit)** während der Read-Only-Audit-Phase wurde dieser Durchlauf gezielt nach **Phase A (Red-Phase & Test-Freeze)** abgeschlossen:
- **Keine Produktionsdateien (`src/`, `experiments/`) wurden verändert.**
- Alle drei portablen Test-Altlasten auf Windows (`test_fs_reporting.py`, `test_settings_bundle.py`, `test_offline_core.py`) wurden auf $Q_{\text{Soll}}$ migriert.
- Alle bestätigten fehlschlagenden CI-Matrix-Checks (`macos-15` Mypy, `win32` Mypy, Windows-Text-Shebang-/CRLF-Relokation, `cubie_benchmarks`-LF-Byte-Invarianz und Windows-`file://`-URL-Auflösung) wurden als **eingefrorene Red-Phase-Verträge** in [`tests/tests_arena/test_ci_platform_stage3.py`](./tests_arena/test_ci_platform_stage3.py) (ohne `xfail`) festgeschrieben.

---

## Run-Interrupt-Protokoll

- **Ereignis:** Während der abschließenden Read-Only-Prüfung (Plan-Mode) auf **Orchestrator (Argon)** (`High`) wurde der Lauf durch `Run interrupted: ⚠ Individual quota reached.` abgebrochen.
- **Repository-Zustand beim Abbruch:** 100 % sauber (`git status` unverändert auf `experimental` bei `93830b69`); es waren noch keine Dateien editiert worden.
- **Fortsetzung & Entscheidung:** Nach Modellwechsel auf **Gemini 4 Neon** (`Medium`) wurde in Abstimmung mit dem Nutzer auf einen `git reset --hard` verzichtet. Stattdessen wurden die aus dem Audit gewonnenen Erkenntnisse unmittelbar genutzt, um:
  1. die fehlschlagenden CI-Matrix-Checks als ausführbare Red-Phase-Verträge einzufrieren, und
  2. den Lauf inkl. Interrupt-Verlauf sauber im vorliegenden TGD-Bericht zu dokumentieren.

---

## Ablauf nach dem 5-Schritte-TGD-Prozess

### Schritt 1: Baseline & CI-Matrix-Audit (Run `44735125009` / `98bf4247`)

| Matrix-Job | Python 3.13 / 3.14 | Status | Identifizierte Ursache(n) |
| :--- | :--- | :--- | :--- |
| `Wheel / ubuntu-24.04` | 3.13, 3.14 | **PASS** | — |
| `Wheel / macos-15` | 3.13, 3.14 | **PASS** | — |
| `Repository / ubuntu-24.04` | 3.13, 3.14 | **PASS** | — |
| `Repository / macos-15` | 3.13, 3.14 | **FAIL** (Step 8 `slow`) | `test_src_lint[mypy]`: `src/qb_cubie/arenas/pyvenv.py:46` (`Statement is unreachable [unreachable]` bei `--platform darwin`). |
| `Wheel / windows-2022` | 3.13, 3.14 | **FAIL** (Step 6 `check_wheel.py`) | `benchmarks`-Profil (`benchmark_installed.py`): `write_text(..., encoding="utf-8")` ohne `newline="\n"` erzeugt CRLF gegen `.read_bytes()` mit LF in `data/smoke` & `data/base`; zusätzlich `Path(unquote(url.path))` statt `url2pathname` in `reporting/_files.py:55`. |
| `Repository / windows-2022` | 3.13, 3.14 | **FAIL** (Step 7 `not slow`) | `67 failed, 1593 passed, 23 skipped, 162 deselected, 6 warnings, 15 errors`: (1) alle **15 Errors** durch Backslashes in `test_fs_reporting.py:126`; (2) CRLF-Bytevergleich in `test_settings_bundle.py:40-42`; (3) `shlex.split(command, posix=False)` in `test_offline_core.py:32` scheitert an Windows-`list2cmdline`-Escapes (`\"`) + fehlendes `taskkill` in `GUARD`; (4) `_relocation.py` lehnt Windows-Text-Shebangs (`python.exe`/`pythonw.exe`, z. B. `dill`-Skripte `get_gprof`/`get_objgraph`/`undill` in `linter_env`), CRLF-Shell-Trampolines und extensionlose nicht-ausführbare Shebang-Skripte falsch ab; (5) `mypy --platform win32` schlägt auf `arenas/_process.py:154,160` (`SIGKILL`/`killpg`) fehl. |

### Schritt 2 & 3: Äquivalenzklassen & Test-Migrationen

1. **Test-Migrationen auf $Q_{\text{Soll}}$ (Windows-Portabilität in bestehenden Tests):**
   - [`tests/tests_user_workflows/test_fs_reporting.py`](../tests/tests_user_workflows/test_fs_reporting.py#L126): `path.relative_to(direct).as_posix()` statt `str(path.relative_to(direct))` (eliminiert alle 15 Fixture-Errors).
   - [`tests/tests_user_workflows/test_settings_bundle.py`](../tests/tests_user_workflows/test_settings_bundle.py#L40-L42): Textvergleich via `.read_text(encoding="utf-8")` statt `.read_bytes()` gegen LF-Literal.
   - [`tests/test_offline_core.py`](../tests/test_offline_core.py#L21-L55): Quote-bewusster Windows-`list2cmdline`-Tokenizer (`split_command`) im Audit-Hook `GUARD` sowie Freigabe von `taskkill` neben `mypy`/`pylint`.
2. **Eingefrorene Red-Phase-Verträge in [`tests/tests_arena/test_ci_platform_stage3.py`](./tests_arena/test_ci_platform_stage3.py):**
   - **`C1` (Multi-Platform Mypy):** `test_src_mypy_passes_for_all_ci_platforms[linux|darwin|win32]` prüft `mypy --warn-unreachable --check-untyped-defs --platform <plat> src/`.
   - **`C2` (Windows Text-Shebang & CRLF-Relokation):**
     - `test_relocation_rewrites_windows_python_exe_text_shebangs[lf|crlf × python.exe|pythonw.exe]`
     - `test_relocation_rewrites_crlf_shell_trampoline`
     - `test_relocation_rejects_non_executable_unsupported_shebang_script`
   - **`C3` (`cubie_benchmarks` LF-Invarianz & Windows `file://`-URL):**
     - `test_smoke_benchmark_solution_matches_acceptance_under_crlf_default_write_text`
     - `test_benchmark_templates_use_explicit_lf_newline_when_writing_text` (deckt alle 70 betroffenen `smoke`- und `base`-Templates ab)
     - `test_benchmark_wheel_hash_uses_url2pathname_for_windows_file_urls`

### Schritt 4: Red-Phase-Verifikation & Test-Freeze

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Meta-Gates 1–3 | `.venv/bin/python -m pytest tests/tests_meta/ -q` | **`84 passed in 16.53s`** |
| Migrierte Bestands-Tests | `.venv/bin/python -m pytest tests/tests_user_workflows/test_fs_reporting.py tests/tests_user_workflows/test_settings_bundle.py tests/test_offline_core.py -q` | **`101 passed in 23.89s`** |
| Eingefrorene Stage-3-Verträge | `.venv/bin/python -m pytest tests/tests_arena/test_ci_platform_stage3.py -q --tb=short` | **`11 failed, 1 passed in 5.32s`** (`linux` grün; alle 11 Ziel-Defekte deterministisch rot) |

---

## Übergabe für Phase B (Green-Phase unter striktem Test-Freeze)

Die Dateien unter `tests/` sind ab sofort **eingefroren**. Im nächsten Durchlauf müssen ausschließlich folgende Produktions- und Benchmark-Dateien angepasst werden (unter Einhaltung von `FUNCTION_LIMIT <= 12`, `MODULE_LIMIT <= 777` und Einzeiler-Docstrings):

1. [`src/qb_cubie/arenas/pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py#L44-L46): `else:`-Zweig in `_cache_root()` gegen `mypy --platform darwin` `[unreachable]`.
2. [`src/qb_cubie/arenas/_process.py`](../src/qb_cubie/arenas/_process.py#L154-L160): `getattr(signal, "SIGKILL", signal.SIGTERM)` und `getattr(os, "killpg", None)` gegen `mypy --platform win32` `[attr-defined]`.
3. [`src/qb_cubie/arenas/_relocation.py`](../src/qb_cubie/arenas/_relocation.py#L77-L110): CRLF-Trampoline-Erkennung (`\r?\n`), `(?:\.exe)?`-Match in `_python_header`/`_shell_header` (case-insensitive) sowie Ablehnung nicht-ausführbarer unbekannter `#!`-Skripte via `_unsupported(script)`.
4. [`experiments/benchmarks/cubie_benchmarks/data/`](../experiments/benchmarks/cubie_benchmarks/data/): Explizites `newline="\n"` in allen 70 `write_text(...)`-Aufrufen der `smoke`- und `base`-Szenario-Templates.
5. [`experiments/benchmarks/cubie_benchmarks/reporting/_files.py`](../experiments/benchmarks/cubie_benchmarks/reporting/_files.py#L55): `Path(url2pathname(url.path))` statt `Path(unquote(url.path))`.
6. Abschließend: `tests/test_styleguide.py`, `tests/test_lint.py`, vollständige Testsuite, `python scripts/check_wheel.py dist`, Living-Documentation-Sync (`docs/CI_PLATFORM_STATUS.md`, `CHANGELOG.md`, `KNOWN_ISSUES.md`) sowie `python -m qb_cubie docframe update`.

---

## Schritt 5: Phase B — Green-Phase & Abschlussverifikation (abgeschlossen)

Unter striktem **Test-Freeze** (keine Änderungen an Testdateien unter `tests/*.py`) wurden alle 5 Zielkomponenten umgesetzt:

1. [`src/qb_cubie/arenas/pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py#L44-L47): Expliziter `else:`-Zweig in `_cache_root()` gegen `mypy --platform darwin` (`[unreachable]`).
2. [`src/qb_cubie/arenas/_process.py`](../src/qb_cubie/arenas/_process.py#L150-L167): `getattr(signal, "SIGKILL", signal.SIGTERM)` und `getattr(os, "killpg", None)` gegen `mypy --platform win32` (`[attr-defined]`).
3. [`src/qb_cubie/arenas/_relocation.py`](../src/qb_cubie/arenas/_relocation.py#L77-L120): CRLF-Trampoline-Erkennung (`\r?\n`), `_is_python_interpreter()` mit Backslash-Normalisierung und case-insensitivem `(?:\.exe)?`-Match sowie Ablehnung unbekannter `#!`-Skripte ohne `+x`-Bit via `_unsupported(script)`.
4. [`experiments/benchmarks/cubie_benchmarks/data/`](../experiments/benchmarks/cubie_benchmarks/data/): Alle 70 betroffenen `smoke`- und `base`-Szenario-Templates auf explizites `newline="\n"` bei `write_text(...)` umgestellt (AST-verifiziert).
5. [`experiments/benchmarks/cubie_benchmarks/reporting/_files.py`](../experiments/benchmarks/cubie_benchmarks/reporting/_files.py#L9-L56): `Path(url2pathname(url.path))` statt `Path(unquote(url.path))`.
6. **Living-Documentation-Sync:** [`docs/CI_PLATFORM_STATUS.md`](../docs/CI_PLATFORM_STATUS.md), [`CHANGELOG.md`](../CHANGELOG.md) und [`KNOWN_ISSUES.md`](../KNOWN_ISSUES.md) aktualisiert und per `python -m qb_cubie docframe update --exclude docs/feature-drafts --exclude experiments --exclude tests` geprüft (`Updated 0 file(s); all frames up to date.`).

### Abschluss-Verifikationsmatrix

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Eingefrorene Stage-3-Verträge | `.venv/bin/python -m pytest tests/tests_arena/test_ci_platform_stage3.py -q --tb=short` | **`12 passed in 5.16s`** |
| Styleguide & Linter (inkl. `slow`) | `.venv/bin/python -m pytest tests/test_styleguide.py tests/test_lint.py -m "" -v --tb=short` | **`23 passed in 26.10s`** (`ruff`, `pylint`, `mypy`, Modul-/Funktionsgrößen, Docstrings, Doc-Beispiele) |
| Vollständige Suite (`not slow`) | `.venv/bin/python -m pytest -m "not slow" -q` | **`1698 passed, 12 skipped, 162 deselected, 6 warnings in 198.76s`** |
| Vollständige Suite (`slow`) | `.venv/bin/python -m pytest -m slow -q` | **`162 passed, 1710 deselected in 230.82s`** |
| Wheel-Build & -Prüfung | `uv build --python .venv/bin/python && .venv/bin/python scripts/check_wheel.py dist` | **`PASS` (Exit-Code `0`, alle Wheel-Profile inkl. `benchmarks`)** |
| DocFrame-Sync | `.venv/bin/python -m qb_cubie docframe update --exclude docs/feature-drafts --exclude experiments --exclude tests` | **`Updated 0 file(s); all frames up to date.`** |
