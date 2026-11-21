<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# CI Plattform- und Kompatibilitätsstatus

![Cubie](.assets/cubie-logo-written.png)

Dieses Dokument erfasst den aktuellen Plattformsupport in der Continuous Integration (GitHub Actions) von `qb-cubie` sowie den Status vorübergehend eingefrorener Plattform-Checks (`windows-2022`).

---

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## 1. Übersicht der CI-Matrix

| Plattform / Runner | Python 3.13 | Python 3.14 | Status | Scope |
| :--- | :---: | :---: | :--- | :--- |
| **Linux** (`ubuntu-24.04`) | ✅ Besteht | ✅ Besteht | **Tier 1 (Aktiv)** | `Wheel` + vollständige `Repository`-Testsuite (`not slow` + `slow` inkl. `/proc`-Watchdog & `SIGKILL`-Crash-Check) + provisionierte Test-Arenen |
| **macOS** (`macos-15`) | ✅ Besteht | ✅ Besteht | **Tier 1 (Aktiv)** | `Wheel` + vollständige `Repository`-Testsuite (`not slow` + `slow`; `/proc`-Watchdog Linux-only, POSIX-Prozessgruppen über `test_process_limits.py` & `test_ci_platform_stage1.py` geprüft) |
| **Windows** (`windows-2022`) | ⏸️ Eingefroren | ⏸️ Eingefroren | **Vorübergehend eingefroren** | CI-Checks in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (`Wheel` & `Repository`) deaktiviert — CI derzeit rot (aktuelle Befunde in [`tests/CI-Data.md`](../tests/CI-Data.md) hinterlegt) |

---

## 2. Temporäre Einfrierung (`windows-2022`)

Nach dem Abschluss von Stufe 3 (`bf955ea8`) sind **Linux (`ubuntu-24.04`)** und **macOS (`macos-15`)** über Python 3.13 und Python 3.14 in beiden CI-Jobs (`Wheel` und `Repository`) grün und bleiben als **Tier 1** aktiv.

Die GitHub-Actions-Checks für **Windows (`windows-2022`)** schlagen weiterhin fehl (Rohdaten in [`tests/CI-Data.md`](../tests/CI-Data.md)) und werden für Release `v0.0.10` bewusst eingefroren:

- In [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) ist `windows-2022` aus der aktiven Matrix beider Jobs (`wheel` und `tests`) entfernt (`os: [ubuntu-24.04, macos-15]`).
- **Offene Befunde `Wheel / windows-2022` (Python 3.13 & 3.14 — 1 Fehler, 3 bestanden):**
  - `tests/ollama_agents_installed.py::test_installed_two_plus_five_study_preserves_all_attempts_and_external_evidence`: mindestens ein archivierter Study-Run endet nicht mit `status == "completed"`.
- **Offene Befunde `Repository / windows-2022` (Python 3.13 — 55 Fehler, 1632 bestanden, 23 übersprungen):**
  - Backslash-Escaping in Fehlertext-Assertions (`str(path)` gegen `repr`-escapte Windows-Pfade in `test_ebt_fs_collisions.py`, `test_ebt_hydration_boundaries.py`, `test_settings_bundle.py`).
  - OS-/Case-abhängige Datei- und Diagnose-Sortierung (`test_docframe_cli.py`, `test_docframe_rules_and_guards.py`, `test_doc_ensurance.py`).
  - Windows-spezifische Einzelbefunde in `test_arena_requirements.py` (`failed to locate pyvenv.cfg` statt `missing pyvenv.cfg`), `test_ci_platform_stage1.py` (extensionloses `#!`-Skript `tool` abgelehnt) und `test_ci_platform_stage2.py` (lokales Callable `invoke_cowsay` unter `spawn` nicht pickelbar).
- Die bisherigen Arbeiten aus den Stufen 1–3 bleiben im Repository und in den folgenden Abschnitten als Ausgangsbasis für eine spätere Wiederaufnahme dokumentiert.

---

## 3. Behobene Ursachen in Stufe 1 (`macos-15` & `CI / Wheel / windows-2022`)

1. **macOS Symlink-Roots (`/var` $\to$ `/private/var`):**
   - [`TempFS.setup()`](../src/qb_cubie/arenas/tempfs.py) und [`PyVenv._prepare_directories()`](../src/qb_cubie/arenas/pyvenv.py) lösen temporäre Arbeitswurzeln nun per `.resolve()` kanonisch auf; `_relocate_link()` in [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py) gleicht Symlink-Präfixe aufgelöst ab.
   - Da macOS kein `/proc`-Dateisystem besitzt, bleiben die 38 tiefen `/proc`-Watchdog-Checks in `tests/tests_arena/test_ebt_resource_limits.py` ehrlich auf Linux beschränkt; POSIX-Prozessgruppen-Abbrüche werden auf macOS über `tests/tests_arena/test_process_limits.py` und `tests/tests_arena/test_ci_platform_stage1.py` verifiziert.
   - Um unter `spawn`-Multiprocessing eine sichere CI-Laufzeit einzuhalten, führt der `tests`-Job in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) zunächst `-m "not slow" -q` und anschließend sequentiell `-m slow -q` bei `timeout-minutes: 35` aus.
2. **Win32-Prozesslimits via Job Objects & Reader-Threads (`_process.py` + `_process_win32.py`):**
   - [`_process.py`](../src/qb_cubie/arenas/_process.py) delegiert `timeout` und `max_output_bytes` unter `os.name == "nt"` an [`_process_win32.py`](../src/qb_cubie/arenas/_process_win32.py) (Win32 Job Objects mit `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` / `TerminateJobObject`, `taskkill`-Fallback und zwei unbuffered Daemon-Reader-Threads mit gemeinsamem Byte-Budget). Damit funktionieren auch `DocEnsurance(..., timeout=...)`, `qb-cubie.exe docframe update` (nun mit explizitem `newline="\n"` in [`doc_frame.py`](../src/qb_cubie/services/doc_frame/doc_frame.py)) und `TempFS`/`PyVenv` mit gesetzten Limits unter Windows.
3. **Subprozess-`PATH`-, Timeout- & Encoding-Härtung für `CI / Wheel`:**
   - [`scripts/check_wheel.py`](../scripts/check_wheel.py) kapselt `build_wheel_environment()` ohne Rückfall auf den Host-`PATH` (`orig_path`), sodass Host-Linter das isolierte `core`-Profil nicht verunreinigen.
   - [`cubie_benchmarks/execution/_process.py`](../experiments/benchmarks/cubie_benchmarks/execution/_process.py) ergänzt Windows-Systempfade, `PYTHONUTF8="1"` und `encoding="utf-8", errors="replace"`; [`ollama_agents/reviewer/tools.py`](../experiments/ollama-agents/ollama_agents/reviewer/tools.py) ersetzt `os.killpg` unter Windows durch `CREATE_NEW_PROCESS_GROUP` + `taskkill`.
   - [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py) akzeptiert Windows-Interpretervarianten wie `pythonw3.13.exe`, `python3.13t.exe` und `python_d.exe` und erkennt auch `\`-Basispfade in Einstiegsskripten.

---

## 4. Behobene Ursachen in Stufe 2 (`CI / Repository / windows-2022`)

Mit Stufe 2 ist auch die vollständige Repository-Suite unter `windows-2022` in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (`timeout-minutes: 45`) freigeschaltet (Details in [`tests/ANALYSIS_CI_MATRIX.md`](../tests/ANALYSIS_CI_MATRIX.md)):
1. **Sichere Windows-`.exe`-Console-Script-Relokation ([`_relocation_win32.py`](../src/qb_cubie/arenas/_relocation_win32.py) & [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py)):**
   - Verifizierte `uv 0.11.3` PE-Ressourcen-Trampolines (`RT_RCDATA`: `UV_TRAMPOLINE_KIND == b"\x01"`, `UV_PYTHON_PATH` via `FreeLibrary` $\to$ `BeginUpdateResourceW`/`UpdateResourceW`/`EndUpdateResourceW`) und `distlib`/`pip`-ZIP-Wrapper (`MZ... + #!<base>\...\python*.exe + PK\x03\x04...`) werden kontrolliert auf den Klon angepasst; sichere relative Python-Ziele ohne `..`-Ausbruch bleiben unverändert gültig.
   - Beliebige übrige native `.exe`-Binaries oder externe Interpreterziele werden unverändert streng mit `RuntimeError("Unsupported console entry point...")` vor Target-Ausführung abgewiesen.
2. **Plattformübergreifende Diff-Pfade ([`ebt.py`](../src/qb_cubie/ebt.py) & [`reporter.py`](../src/qb_cubie/reporter.py)):**
   - `EBT._generate_diff()` / `_modified_paths()` geben relative Schlüssel über `.as_posix()` aus, `PytestReporter._summarize_fs_diffs()` normalisiert über `_posix_path()` auf kanonische Vorwärtsschrägstriche (`/`).
3. **UTF-8-Subprocess-Hygiene & Test-Portabilität:**
   - [`mypy.py`](../src/qb_cubie/linters/mypy.py), [`pylint.py`](../src/qb_cubie/linters/pylint.py) und [`_requirements.py`](../src/qb_cubie/arenas/_requirements.py) lesen Subprocess-Ausgaben explizit mit `encoding="utf-8", errors="replace"`; [`pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py) decodiert `uv`-`stderr` mit `errors="replace"`; [`_hydration.py`](../src/qb_cubie/arenas/hydration.py) trimmt auch `\`; [`scripts/provision_test_arenas.py`](../scripts/provision_test_arenas.py) nutzt `onexc=_remove_readonly`.
   - Verbliebene POSIX-Annahmen in Repository-Tests (`/tmp`/`touch`, `python3`/`echo`, `bin/python`, `site.getsitepackages()[0]`, `shlex.split`, `symlinks=True` und implizites Plattform-Encoding) wurden plattformneutral bereinigt; ausschließlich intrinsische OS-Spezifika (`test_ebt_resource_limits.py` `/proc`-Watchdog Linux-only, `test_quality_gate.py` `SIGKILL` POSIX-only, nativer `cowsay.exe`-Test Windows-only) behalten ehrliche Plattform-Marker.

---

## 5. Behobene Ursachen in Stufe 3 (CI-Run `44735125009` — `macos-15` & `windows-2022`)

Stufe 3 schließt die echten Matrix-Befunde aus CI-Run `44735125009` (Commit `98bf4247`, protokolliert in [`tests/TGD_CI_STAGE3.md`](../tests/TGD_CI_STAGE3.md)) und friert sie als Plattformverträge in [`tests/tests_arena/test_ci_platform_stage3.py`](../tests/tests_arena/test_ci_platform_stage3.py) ein:
1. **Multi-Platform-Mypy (`--warn-unreachable` für `linux`, `darwin`, `win32`):**
   - [`pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py) nutzt einen expliziten `else:`-Zweig in `_cache_root()` gegen `mypy --platform darwin` (`[unreachable]`).
   - [`_process.py`](../src/qb_cubie/arenas/_process.py) greift über `getattr(signal, "SIGKILL", signal.SIGTERM)` und `getattr(os, "killpg", None)` auf POSIX-Symbole zu (`mypy --platform win32` `[attr-defined]`).
2. **Windows-Text-Shebangs & CRLF-Trampoline-Relokation ([`_relocation.py`](../src/qb_cubie/arenas/_relocation.py)):**
   - `_python_header()` und `_shell_header()` normalisieren Backslashes, erkennen `python.exe`/`pythonw.exe` (case-insensitive) und verarbeiten CRLF-Shell-Trampolines (`\r?\n`); extensionlose unbekannte `#!`-Skripte ohne POSIX-`+x`-Bit werden deterministisch per `_unsupported(script)` abgewiesen.
3. **Benchmark-LF-Invarianz & Windows-`file://`-URLs (`experiments/benchmarks/`):**
   - Alle 70 betroffenen `smoke`- und `base`-Szenario-Templates unter [`experiments/benchmarks/cubie_benchmarks/data/`](../experiments/benchmarks/cubie_benchmarks/data/) übergeben explizites `newline="\n"` an `write_text(...)`.
   - [`cubie_benchmarks/reporting/_files.py`](../experiments/benchmarks/cubie_benchmarks/reporting/_files.py) löst `file://`-Wheel-URLs über `Path(url2pathname(url.path))` statt `Path(unquote(url.path))` auf.
4. **Verbliebene Windows-Test-Altlasten (`tests/`):**
   - [`test_fs_reporting.py`](../tests/tests_user_workflows/test_fs_reporting.py) normiert relative Pfade via `.as_posix()`, [`test_settings_bundle.py`](../tests/tests_user_workflows/test_settings_bundle.py) vergleicht Text via `.read_text(encoding="utf-8")`, und [`test_offline_core.py`](../tests/test_offline_core.py) verwendet einen Windows-`list2cmdline`-kompatiblen Tokenizer inkl. `taskkill`-Freigabe im Audit-Guard.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](./core/README.md)  
[↦ | Entwicklerübersicht & Internals | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](./misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
