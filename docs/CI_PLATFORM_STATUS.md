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
| **Linux** (`ubuntu-24.04`) | ✅ Besteht | ✅ Besteht | **Tier 1 (Aktiv)** | `Wheel` + vollständige `Repository`-Testsuite (`not slow` + `slow` inkl. `/proc`-Watchdog) + provisionierte Test-Arenen |
| **macOS** (`macos-15`) | ✅ Besteht | ✅ Besteht | **Tier 1 (Aktiv — Stufe 1)** | `Wheel` + vollständige `Repository`-Testsuite (`not slow` + `slow`; `/proc`-Watchdog in `test_ebt_resource_limits.py` übersprungen, POSIX-Prozessgruppen über `test_process_limits.py` & `test_ci_platform_stage1.py` geprüft) |
| **Windows** (`windows-2022`) | 🔄 Stufe 1 (Wheel aktiv) | 🔄 Stufe 1 (Wheel aktiv) | **Stufe 1 reaktiviert** | `CI / Wheel` mit Win32-Prozesslimits & isoliertem `PATH` aktiv; vollständige `Repository`-Suite folgt in Stufe 2 |

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

## 3. Verbleibende Lücken für Stufe 2 (`CI / Repository / windows-2022`)

Die vollständige Repository-Testsuite unter Windows (`tests`-Job) benötigt noch folgende Bausteine aus Stufe 2 (detailliert in [`tests/ANALYSIS_CI_MATRIX.md`](../tests/ANALYSIS_CI_MATRIX.md)):
1. **Sichere `.exe`-Console-Script-Relokation:** Kontrollierte Dual-Format-Anpassung für verifizierte `distlib`/`pip`-Wrapper (`PE + #! + ZIP`) und `uv-trampoline`-Launcher (`UVSC`/`UVPY`/`UVUV`) für `cowsay_env` und `linter_env` bei unveränderter Ablehnung beliebiger nativer `.exe`-Binaries.
2. **Plattformübergreifende Diff-Pfade:** Normierung relativer Pfade in [`ebt.py`](../src/qb_cubie/ebt.py) (`_generate_diff`, `_modified_paths`) und [`reporter.py`](../src/qb_cubie/reporter.py) (`_summarize_fs_diffs`) auf kanonische POSIX-Slashes (`/`).
3. **Test- & Linter-Hygiene unter Windows:** Beseitigung verbliebener POSIX-Shell-Kommandos (`/tmp`, `touch`, `python3`, `echo ... > ...`), `symlinks=os.name != "nt"` in Test-Venv-Fixtures sowie explizites UTF-8-Subprozess-Decoding in `mypy.py`/`pylint.py`/`_requirements.py` und Freischaltung von `windows-2022` im `tests`-Job von `.github/workflows/ci.yml`.

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
