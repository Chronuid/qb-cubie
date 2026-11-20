<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# CI Plattform- und Kompatibilitätsstatus

![Cubie](.assets/cubie-logo-written.png)

Dieses Dokument erfasst den aktuellen Plattformsupport in der Continuous Integration (GitHub Actions) von `qb-cubie` sowie den schrittweisen Ausbau für macOS und Windows.

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
| **Windows** (`windows-2022`) | ✅ Aktiv (Stufe 2) | ✅ Aktiv (Stufe 2) | **Tier 1 (Aktiv — Stufe 2)** | `Wheel` + vollständige `Repository`-Testsuite (`not slow` + `slow` inkl. `provision_test_arenas.py`, Win32-Job-Objects, `uv`/`distlib`-Launcher-Relokation & nativem `cowsay.exe`-Test; POSIX-Signal-/Symlink-Watchdogs POSIX-only) |

---

## 2. Behobene Ursachen in Stufe 1 (`macos-15` & `CI / Wheel / windows-2022`)

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

## 3. Behobene Ursachen in Stufe 2 (`CI / Repository / windows-2022`)

Mit Stufe 2 ist auch die vollständige Repository-Suite unter `windows-2022` in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (`timeout-minutes: 45`) freigeschaltet (Details in [`tests/ANALYSIS_CI_MATRIX.md`](../tests/ANALYSIS_CI_MATRIX.md)):
1. **Sichere Windows-`.exe`-Console-Script-Relokation ([`_relocation_win32.py`](../src/qb_cubie/arenas/_relocation_win32.py) & [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py)):**
   - Verifizierte `uv 0.11.3` PE-Ressourcen-Trampolines (`RT_RCDATA`: `UV_TRAMPOLINE_KIND == b"\x01"`, `UV_PYTHON_PATH` via `FreeLibrary` $\to$ `BeginUpdateResourceW`/`UpdateResourceW`/`EndUpdateResourceW`) und `distlib`/`pip`-ZIP-Wrapper (`MZ... + #!<base>\...\python*.exe + PK\x03\x04...`) werden kontrolliert auf den Klon angepasst; sichere relative Python-Ziele ohne `..`-Ausbruch bleiben unverändert gültig.
   - Beliebige übrige native `.exe`-Binaries oder externe Interpreterziele werden unverändert streng mit `RuntimeError("Unsupported console entry point...")` vor Target-Ausführung abgewiesen.
2. **Plattformübergreifende Diff-Pfade ([`ebt.py`](../src/qb_cubie/ebt.py) & [`reporter.py`](../src/qb_cubie/reporter.py)):**
   - `EBT._generate_diff()` / `_modified_paths()` geben relative Schlüssel über `.as_posix()` aus, `PytestReporter._summarize_fs_diffs()` normalisiert über `_posix_path()` auf kanonische Vorwärtsschrägstriche (`/`).
3. **UTF-8-Subprocess-Hygiene & Test-Portabilität:**
   - [`mypy.py`](../src/qb_cubie/linters/mypy.py), [`pylint.py`](../src/qb_cubie/linters/pylint.py) und [`_requirements.py`](../src/qb_cubie/arenas/_requirements.py) lesen Subprocess-Ausgaben explizit mit `encoding="utf-8", errors="replace"`; [`pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py) decodiert `uv`-`stderr` mit `errors="replace"`; [`_hydration.py`](../src/qb_cubie/arenas/_hydration.py) trimmt auch `\`; [`scripts/provision_test_arenas.py`](../scripts/provision_test_arenas.py) nutzt `onexc=_remove_readonly`.
   - Verbliebene POSIX-Annahmen in Repository-Tests (`/tmp`/`touch`, `python3`/`echo`, `bin/python`, `site.getsitepackages()[0]`, `shlex.split`, `symlinks=True` und implizites Plattform-Encoding) wurden plattformneutral bereinigt; ausschließlich intrinsische OS-Spezifika (`test_ebt_resource_limits.py` `/proc`-Watchdog Linux-only, `test_quality_gate.py` `SIGKILL` POSIX-only, nativer `cowsay.exe`-Test Windows-only) behalten ehrliche Plattform-Marker.

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
