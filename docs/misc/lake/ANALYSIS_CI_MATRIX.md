<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Orchestrator (Neon)" effort="High" -->
# Analysis: Stärkung der CI-Matrix für Windows und macOS

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Orchestrator (Neon)
- **Reasoning-Effort:** High
- **Analysedatum:** 20. November 2026, ~ 11:55 (CET)
- **Synthesebasis:** `tests/GEMINI.md`, `../../../.github/workflows/ci.yml`, `pyproject.toml`, `KNOWN_ISSUES.md`, `CHANGELOG.md`, `../../../CI_PLATFORM_STATUS.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/core/GUIDE_Arena-Management.md`, `docs/dev/DEV-GUIDE_2-3_Arenas.md`, `docs/services/GUIDE_DocEnsurance.md`, `tests/tests_arena/ANALYSIS.md`, `tests/tests_arena/TGD_1.md`, `src/qb_cubie/` (`arenas/*`, `ebt.py`, `reporter.py`, `linters/mypy.py`, `linters/pylint.py`, `services/doc_ensurance/*`, `services/doc_frame/*`), `scripts/check_wheel.py`, `scripts/provision_test_arenas.py`, `experiments/benchmarks/cubie_benchmarks/`, `experiments/ollama-agents/ollama_agents/`, `tests/` inkl. `tests/wheel/` und `tests/tests_meta/`, Git-Historie (`a4af5dad`, `085e7a00`, `518cf28f`)
- **Stand:** qb-cubie (`v0.0.9`, gemäß `pyproject.toml:7`, Ausgangs-Commit `518cf28f`)
- **Git-Log:** `git log -n 1`

---

---
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

Das vorliegende Audit vermisst den aktuellen Code- und Testbestand von `qb-cubie` (`HEAD = 518cf28f`, Python `3.13`/`3.14`; **1823** gesammelte Tests insgesamt: **1661** `fast` + **162** `slow`) rein lesend gegen die Plattformziele aus [`tests/GEMINI.md`](./GEMINI.md) und [`../../../.github/workflows/ci.yml`](../../../.github/workflows/ci.yml):

1. **macOS (`macos-15`) hat genau einen bestätigten Blocker im Produktionscode plus ein klares Laufzeit-/Skalierungsrisiko:**
   - **Blocker `M1` (`/var` → `/private/var`-Symlink-Drift):** [`TempFS.setup()`](../src/qb_cubie/arenas/tempfs.py#L67-L68) und [`PyVenv._prepare_directories()`](../src/qb_cubie/arenas/pyvenv.py#L165) übernehmen `tempfile.mkdtemp(...)` unaufgelöst (auf macOS `/var/folders/...`), während Kindprozesse über `Path.cwd()` bzw. `sys.prefix` `/private/var/folders/...` sehen. In [`test_ebt_tempfs.py`](./tests_arena/test_ebt_tempfs.py#L34) schlagen dadurch **9 Testfälle** sicher fehl; [`_relocate_link()`](../src/qb_cubie/arenas/_relocation.py#L36-L47) und [`test_ebt_console_environment.py`](./tests_arena/test_ebt_console_environment.py#L144) sind analog gefährdet.
   - **Watchdog & Laufzeit (`M2`, `M3`):** [`test_ebt_resource_limits.py`](./tests_arena/test_ebt_resource_limits.py#L22-L24) wird unter macOS wegen fehlendem `/proc` übersprungen (`skipif(sys.platform != "linux")`), während [`test_process_limits.py`](./tests_arena/test_process_limits.py#L42-L94) und die DocEnsurance-Limit-Tests unter macOS aktiv bleiben. Kritischer ist die Laufzeit der `162` langsamen Tests: Bereits auf Linux mit `fork` dauert `pytest -m "" -q` **405.12s (6m45s)** (gemäß [`TGD_1.md`](./tests_arena/TGD_1.md#L32)); mit macOS-`spawn` stößt der aktuelle `timeout-minutes: 20` im `tests`-Job ohne Parallelisierung oder Timeout-Anpassung an die Grenze (`pytest-xdist 3.8.0` ist in `[dependency-groups] dev` bereits vorhanden).

2. **Schlüsselbefund für Windows (`windows-2022`) — `DocEnsurance`-Default-Timeout als Dreh- und Angelpunkt:**
   - [`DocEnsurance.__init__`](../src/qb_cubie/services/doc_ensurance/doc_ensurance.py#L120) erzwingt standardmäßig `timeout=10.0` und konfiguriert damit eine [`TempFS(timeout=10.0)`](../src/qb_cubie/services/doc_ensurance/doc_ensurance.py#L267-L273), was auf Windows über [`_process.validate_limits()`](../src/qb_cubie/arenas/_process.py#L13-L17) sofort mit `NotImplementedError("Arena execution limits currently require POSIX process groups")` abbricht.
   - Damit blockiert dieser Punkt nicht erst Stufe 2 (`tests`-Suite, `test_docs_code_examples`, `tests_doc_ensurance/`), sondern **bereits Stufe 1 (`CI / Wheel / windows-2022`)** durch [`smoke_installed.py`](../../../tests/wheel/smoke_installed.py#L167) (`DocEnsurance(..., timeout=2.0).run()`).

3. **Zweistufige Machbarkeit (`Stufe 1` vs. `Stufe 2`):**
   - **Stufe 1 (`CI / Repository / macos-15` + Reaktivierung `CI / Wheel / windows-2022`):** Erfordert `M1`, `M3` (CI-Laufzeitstrategie), `W1` (Entscheidung E1 zu `_process.py`), `W2` (`check_wheel.py`-`PATH`-Leak), `W3` (`cubie_benchmarks/execution/_process.py`), `W4` (`ollama_agents/reviewer/tools.py`), `W5` (`smoke_installed.py:135`) und `W6` (`_relocation.py` Python-Exe-Regex + `doc_frame.py` LF-Hygiene).
   - **Stufe 2 (Vollständige Suite `CI / Repository / windows-2022`):** Erfordert zusätzlich `W7` (sichere `.exe`-Console-Script-Relokation für `distlib`/`pip` + `uv-trampoline` bei unveränderter Ablehnung beliebiger `.exe`-Binaries), `W8` (POSIX-Diff-Pfadnormalisierung in `ebt.py`/`reporter.py`), `W9` (Bereinigung von POSIX-Annahmen in Tests/Scripts) und `W10` (UTF-8-Subprocess-/Datei-Encoding inkl. Anpassung von 3 Monkeypatch-Doubles in `tests_linter/`).

---

## Teil 1: Befund-Inventar für macOS (`macos-15`)

### `M1` — Unaufgelöster `mkdtemp`-Pfad (`/var` → `/private/var`-Symlink-Drift) `[BLOCKER]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Bestätigter Blocker für Stufe 1** (`CI / Repository / macos-15`) |
| **Produktionscode** | [`src/qb_cubie/arenas/tempfs.py#L67-L68`](../src/qb_cubie/arenas/tempfs.py#L67-L68), [`src/qb_cubie/arenas/pyvenv.py#L165`](../src/qb_cubie/arenas/pyvenv.py#L165), [`src/qb_cubie/arenas/_relocation.py#L11-L15`](../src/qb_cubie/arenas/_relocation.py#L11-L15), [`src/qb_cubie/arenas/_relocation.py#L36-L47`](../src/qb_cubie/arenas/_relocation.py#L36-L47) |
| **Betroffene Tests** | [`tests/tests_arena/test_ebt_tempfs.py#L34`](../tests/tests_arena/test_ebt_tempfs.py#L34) (`L89`, `L116` — zusammen 9 Testfälle inkl. Parametrisierung), [`tests/tests_arena/test_ebt_console_environment.py#L144`](../tests/tests_arena/test_ebt_console_environment.py#L144) |

- **Root Cause:** Unter macOS zeigt `$TMPDIR` auf `/var/folders/...`; `/var` ist ein Symlink auf `/private/var`.
  1. `TempFS.setup()` erzeugt `self.workspace_path = Path(tempfile.mkdtemp(prefix=f"{self.arena_id}_"))` **ohne `.resolve()`**. Im Subprozess liefert `Path.cwd()` jedoch den physisch aufgelösten Pfad `/private/var/folders/...`. Deshalb schlägt `assert Path.cwd() == arena.workspace_path` in `test_ebt_tempfs.py` auf `macos-15` deterministisch fehl.
  2. `PyVenv._prepare_directories()` erzeugt `root = Path(tempfile.mkdtemp(prefix=f"{self.arena_id}_"))` ebenfalls **ohne `.resolve()`**. Dadurch erhält `VIRTUAL_ENV` (via `self.virtual_path.absolute()`) ggf. `/var/folders/...`, während `sys.prefix` im Subprozess auf `/private/var/folders/...` auflösen kann und `test_ebt_console_environment.py:144` (`json.loads(text)["prefix"] == json.loads(text)["virtual_env"]`) gefährdet.
  3. `_relocation.relocate_scripts()` übergibt `base.absolute()` und `clone.absolute()` an `_relocate_link()`. Wenn `target` im `os.readlink(script)` kanonisch `/private/var/...` enthält, `base` aber als `/var/...` übergeben wird, schlägt `target.is_relative_to(base)` fehl und löst fälschlich `_unsupported(script)` aus.
- **Lösungsansatz & Kritische Grenze:**
  - `Path(tempfile.mkdtemp(...)).resolve()` in `TempFS.setup()` und `PyVenv._prepare_directories()` (sowie aufgelöster Vergleich in `_relocate_link()`, falls `target.resolve().is_relative_to(base.resolve())`).
  - **Wichtige Invariante:** In `_requirements._environment_python()` (`_requirements.py:52-57`) darf der Interpreter-Symlink `bin/python` **nicht** per `.resolve()` auf den Host-Interpreter aufgelöst werden, da Python `pyvenv.cfg` über den unaufgelösten Symlink-Pfad findet! Die Auflösung betrifft ausschließlich Verzeichniswurzeln (`mkdtemp()` bzw. `base`/`clone`-Basispfad-Vergleich).
  - *Nebengewinn für Windows:* `.resolve()` beseitigt zugleich 8.3-Kurznamen-Drift (`RUNNER~1` vs. `runneradmin`) in temporären Verzeichnissen.

---

### `M2` — Ressourcenlimit-Abdeckung unter macOS (`test_ebt_resource_limits.py`) `[ABWEICHUNG]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Transparente Plattformgrenze (Stufe 1 / Entscheidung E4)** |
| **Produktionscode** | [`src/qb_cubie/arenas/_process.py`](../src/qb_cubie/arenas/_process.py) (POSIX-Prozessgruppen, `selectors`, `os.killpg`) |
| **Tests** | [`tests/tests_arena/test_ebt_resource_limits.py#L22-L37`](../tests/tests_arena/test_ebt_resource_limits.py#L22-L37) (`skipif(sys.platform != "linux")`), [`tests/tests_arena/test_process_limits.py#L42-L94`](../tests/tests_arena/test_process_limits.py#L42-L94), [`tests/tests_services/tests_doc_ensurance/test_doc_ensurance_arenas.py#L180-L200`](../tests/tests_services/tests_doc_ensurance/test_doc_ensurance_arenas.py#L180-L200), [`tests/tests_services/tests_doc_ensurance/test_doc_ensurance_configs.py#L194-L210`](../tests/tests_services/tests_doc_ensurance/test_doc_ensurance_configs.py#L194-L210) |

- **Root Cause:** `test_ebt_resource_limits.py` verifiziert Zombie-Reaping und Startzeit-Identität von Enkelprozessen über `Path(f"/proc/{pid}/stat")` (`lines 29-36`). macOS stellt kein `/proc`-Dateisystem bereit; deshalb greift `pytestmark = pytest.mark.skipif(sys.platform != "linux", ...)` für alle Tests in diesem Modul.
- **Tatsächliche macOS-Restabdeckung:** Das zugrunde liegende Bounded-Execution-Modul `_process.py` läuft auf macOS regulär mit POSIX-Prozessgruppen und wird dort bereits durch `test_process_limits.py` (`os.name == "posix"`) sowie die Timeout-/Budget-Tests von `DocEnsurance` geprüft. In [`resource_cases/runner.py`](./tests_arena/resource_cases/runner.py) bzw. `test_ebt_resource_limits.py` bleibt der `/proc`-Skip technisch ehrlich, sollte aber in [`../../../CI_PLATFORM_STATUS.md`](../../../CI_PLATFORM_STATUS.md) explizit dokumentiert (und optional um einen kompakten POSIX-portablen Prozessbaum-/Timeout-EBT-Test ohne `/proc` ergänzt) werden.

---

### `M3` — Laufzeit- und `spawn`-Skalierungsrisiko unter `macos-15` `[HOHES RISIKO]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Laufzeitrisiko für Stufe 1** (`CI / Repository / macos-15`) |
| **Betroffene Tests** | [`tests/tests_multiprocessors/test_multiprocess.py#L200-L289`](../tests/tests_multiprocessors/test_multiprocess.py#L200-L289) (`@pytest.mark.slow`), [`tests/tests_multiprocessors/test_mp_hypothesis.py#L215-L235`](../tests/tests_multiprocessors/test_mp_hypothesis.py#L215-L235) (`@pytest.mark.slow`) |
| **CI-Konfiguration** | [`.github/workflows/ci.yml#L36-L56`](../../../.github/workflows/ci.yml#L36-L56) (`timeout-minutes: 20`, sequentielles `pytest -m "" -q`) |

- **Root Cause & Zahlenbasis:**
  - Auf `ubuntu-24.04` (mit `fork`-Startmethode) benötigt die Gesamtsuite `pytest -m "" -q` (`1812 passed, 11 skipped`) bereits **405.12s (6m45s)** ([`TGD_1.md`](./tests_arena/TGD_1.md#L32)).
  - Unter macOS verwendet `multiprocessing` standardmäßig **`spawn`**: Jeder Pool-Worker importiert Python und `qb_cubie` neu.
  - Insbesondere `test_multiprocess.py` (`scale=[10, 50, 150]` über `TempFS` und `PyVenv` über 3 Skalierungsfunktionen × 3 Prozessoren, ca. **1.800 Arena-Klone + Subprozesse**) sowie `test_mp_hypothesis.py` (`3 × 100` Hypothesis-Beispiele mit `EBT(multiprocessing=True)`) skalieren unter `spawn` und APFS-`copytree` deutlich langsamer als unter Linux/`fork`.
  - Bei unverändertem sequentiellen `pytest -m "" -q` und `timeout-minutes: 20` drohen Timeout-Abbrüche auf `macos-15` (insbesondere bei zwei Matrix-Läufen `3.13` und `3.14` und auf `windows-2022` in Stufe 2 noch stärker wegen NTFS).
  - Positiver Befund: `pytest-xdist` (`3.8.0`) ist bereits in [`pyproject.toml#L46`](../../../pyproject.toml#L46) (`[dependency-groups] dev`) enthalten und installiert. Allerdings müssen xdist-Wechselwirkungen mit `test_mp_xdist.py` und die gleichzeitige CPU-Last bei geschachtelten Multiprozessor-Tests beachtet werden (z. B. `-m "not slow"` vs. `-m slow` aufteilen oder `-n 2 --dist loadscope` mit erhöhtem `timeout-minutes`).

---

### `M4` — Symlink-Eltern-Guard in `ollama_agents/paths.py` `[BEOBACHTUNG]`

- [`experiments/ollama-agents/ollama_agents/paths.py#L21-L35`](../../../experiments/ollama-agents/ollama_agents/paths.py#L21-L35) lehnt in `guard(absolute(path))` jedes Elternverzeichnis ab, das ein Symlink ist (`parent.is_symlink()`).
- Im aktuellen Wheel-Check auf `macos-15` passiert das nur, weil `pytest`'s `tmp_path` unter `/private/var/...` bereits aufgelöst ist. Übergibt ein Aufrufer jedoch direkt einen unaufgelösten `/var/folders/...`-Pfad (z. B. aus `tempfile.mkdtemp()` ohne `.resolve()`), bricht `ollama_agents` unter macOS mit `InvalidRequest("Symlink parent path is forbidden: /var")`. Kein unmittelbarer CI-Blocker, aber als bekanntes macOS-Verhalten festzuhalten.

---

## Teil 2: Befund-Inventar für Windows (`windows-2022`)

### 2.1 Blocker für Stufe 1 (`CI / Wheel / windows-2022`)

#### `W1` — `DocEnsurance`-Default-Timeout (`10.0s`) & POSIX-only `_process.py` `[KRITISCHER BLOCKER]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Kritischer Blocker bereits für Stufe 1 (`Wheel`) und Stufe 2 (`Repository`)** |
| **Produktionscode** | [`src/qb_cubie/arenas/_process.py#L13-L33`](../src/qb_cubie/arenas/_process.py#L13-L33), [`src/qb_cubie/services/doc_ensurance/doc_ensurance.py#L120`](../src/qb_cubie/services/doc_ensurance/doc_ensurance.py#L120) (`L267-L273`) |
| **Betroffene Tests & Docs** | [`tests/wheel/smoke_installed.py#L167`](../../../tests/wheel/smoke_installed.py#L167), [`tests/test_styleguide.py#L109`](../../../tests/test_styleguide.py#L109), [`tests/tests_arena/test_process_limits.py#L34-L94`](../tests/tests_arena/test_process_limits.py#L34-L94), [`tests/tests_arena/test_ebt_phantom_calls.py#L76`](../tests/tests_arena/test_ebt_phantom_calls.py#L76) (`L93`), alle 9 Module in [`tests/tests_services/tests_doc_ensurance/`](./tests_services/tests_doc_ensurance/), [`tests/tests_services/tests_doc_frame/test_docframe_rules_and_guards.py`](./tests_services/tests_doc_frame/test_docframe_rules_and_guards.py), [`docs/core/GUIDE_Arena-Management.md#L128-L137`](../../core/GUIDE_Arena-Management.md#L128-L137), [`docs/services/GUIDE_DocEnsurance.md#L110-L124`](../../services/GUIDE_DocEnsurance.md#L110-L124) |

- **Root Cause:**
  - `DocEnsurance.__init__(..., timeout: float | None = 10.0)` ruft `_configure_arena(arena, self.timeout)` auf und erstellt `TempFS(timeout=10.0)` bzw. setzt `arena.timeout = 10.0`.
  - `TempFS.__init__()` und `PyVenv.__init__()` delegieren an `_process.validate_limits(timeout, max_output_bytes)`, welches bei `os.name != "posix" and (timeout is not None or max_output_bytes is not None)` sofort **`NotImplementedError("Arena execution limits currently require POSIX process groups")`** wirft.
  - Zusätzlich prüft [`test_unsupported_platform_rejects_limits_explicitly()`](./tests_arena/test_process_limits.py#L34-L39) per Monkeypatch ausdrücklich die alte $Q_{\text{Ist}}$-Annahme, dass `os.name="nt"` einen `NotImplementedError` auslöst (`match="POSIX"`).
- **Warum das der zentrale Architekturpunkt ist:**
  - `tests/wheel/smoke_installed.py:167` ruft ausdrücklich `DocEnsurance(target=doc, pattern=CUBIE_DOC_STYLE, reporter=None, timeout=2.0).run()` auf — bereits `CI / Wheel / windows-2022` scheitert ohne Lösung an dieser Stelle.
  - In Stufe 2 wäre ohne Win32-Limits die komplette Dokumentations-Verifikation (`test_styleguide.py:test_docs_code_examples`, `tests_doc_ensurance/`, `GUIDE_Arena-Management.md:128`) auf Windows kaputt.
  - Eine echte Win32-Umsetzung (`timeout` per Deadline + Win32 Job Object mit `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` / `TerminateJobObject` + `taskkill /F /T /PID`-Fallback; `max_output_bytes` per zwei Daemon-Reader-Threads auf `stdout`/`stderr` mit gemeinsamer Atom-/Lock-Budgetprüfung) löst alle genannten Blockaden auf einmal — ohne das Sicherheitsversprechen von `DocEnsurance` unter Windows auszuhöhlen (siehe **Entscheidung E1**).

---

#### `W2` — Host-`PATH`-Leak in `../../../scripts/check_wheel.py` auf Windows `[BLOCKER STUFE 1]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Bestätigter Blocker für Stufe 1** (`CI / Wheel / windows-2022`) |
| **Datei** | [`scripts/check_wheel.py#L44-L60`](../../../scripts/check_wheel.py#L44-L60) |

- **Root Cause:** Seit Commit `a4af5dad` hängt `../../../scripts/check_wheel.py` unter `os.name == "nt"` in den Zeilen 53–55 `orig_path = os.environ.get("PATH", "")` wieder an `environment["PATH"]` an. Das widerspricht direkt dem Isolationskommentar in Zeile 44 (`# Only the test venv may supply optional linter executables.`).
- **Fehlerfolge:** Wenn auf dem Windows-Runner (`windows-2022`) `mypy` oder `pylint` im Host-`PATH` installiert sind (z. B. über vorherige Setup-Tools oder globale Python-Installationen), findet [`MyPy`](../src/qb_cubie/linters/mypy.py#L76)/[`Pylint`](../src/qb_cubie/linters/pylint.py) diese Executables im `core`-Profil und bricht [`smoke_installed.py` (`test_linter_runtime_dependencies`)](../../../tests/wheel/smoke_installed.py#L105-L143) und `test_mypy_with_native_absolute_file_path` (erwartet `qb-cubie[linters]`-Fehler im `core`-Profil).
- **Lösung:** `orig_path` vollständig entfernen; nur `[str(python.parent), sys.base_prefix, os.path.join(system_root, "System32"), system_root, os.path.join(system_root, "System32", "Wbem")]` in `environment["PATH"]` aufnehmen, `WINDIR` neben `SystemRoot`/`COMSPEC`/`PATHEXT`/`TEMP`/`TMP` weiterreichen und `root = Path(temporary).resolve()` auflösen. (`cubie_benchmarks/measurement/provenance.py:28-49` fängt fehlendes `git` bereits sauber über `except (OSError, subprocess.SubprocessError)` ab — `git` im `PATH` ist für den Wheel-Check nicht nötig.)

---

#### `W3` — Fehlender System-`PATH` und fehlendes UTF-8 in `cubie_benchmarks/execution/_process.py` `[BLOCKER STUFE 1]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Bestätigter Blocker für Stufe 1** (`check_wheel.py`-Profil `"benchmarks"`) |
| **Datei** | [`experiments/benchmarks/cubie_benchmarks/execution/_process.py#L37-L75`](../../../experiments/benchmarks/cubie_benchmarks/execution/_process.py#L37-L75) |

- **Root Cause:**
  1. `_environment()` (Zeilen 70–75) setzt `"PATH": str(Path(sys.executable).parent)` ohne `System32`/`SystemRoot` sowie ohne `COMSPEC`, `PATHEXT` und `PYTHONUTF8`. Im Profil `"benchmarks"` starten `benchmark_installed.py` und `benchmark_base_installed.py` Subprozesse darüber (`_execute`), die unter Windows System-DLLs oder `PATHEXT` benötigen können.
  2. `_execute()` (Zeilen 40–42) startet `subprocess.Popen(..., text=True)` ohne `encoding="utf-8", errors="replace"`, was unter deutscher/Windows-`cp1252`-Locale zu `UnicodeDecodeError` beim Lesen von Subprozess-Ausgaben führt (sofern `PYTHONUTF8` nicht gesetzt ist).

---

#### `W4` — POSIX-only `os.killpg` / `signal.SIGKILL` in `ollama_agents/reviewer/tools.py` `[BLOCKER STUFE 1]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Bestätigter Blocker für Stufe 1** (`ollama_agents_installed.py` im Wheel-Check) |
| **Dateien** | [`experiments/ollama-agents/ollama_agents/reviewer/tools.py#L60-L81`](../../../experiments/ollama-agents/ollama_agents/reviewer/tools.py#L60-L81), [`tests/wheel/ollama_agents_installed.py#L125`](../../../tests/wheel/ollama_agents_installed.py#L125) (`L175`) |

- **Root Cause:** `reviewer/tools.py` (wird sowohl vom `reviewer` als auch vom `developer` importiert) ruft bei Timeout `os.killpg(process.pid, signal.SIGKILL)` auf (Zeile 78). Beide Symbole existieren auf Windows (`os.name == "nt"`) nicht → `AttributeError` beim ersten Subprozess-Timeout in `ollama_agents_installed.py`! Zudem öffnen Zeilen 125 und 175 in `ollama_agents_installed.py` Dateien über `.read_text()` ohne `encoding="utf-8"`.
- **Lösung:** Analog [`cubie_benchmarks/execution/_process.py#L59-L67`](../../../experiments/benchmarks/cubie_benchmarks/execution/_process.py#L59-L67) unter `os.name == "nt"` `subprocess.CREATE_NEW_PROCESS_GROUP` / `taskkill /F /T /PID` (+ `process.kill()` Fallback) statt `start_new_session=True` / `os.killpg` verwenden und `encoding="utf-8"` ergänzen.

---

#### `W5` — 8.3-Kurznamen / Drive-Case-Sensitivität in `../../../tests/wheel/smoke_installed.py` `[RISIKO STUFE 1]`

- [`tests/wheel/smoke_installed.py#L128-L143`](../../../tests/wheel/smoke_installed.py#L128-L143) prüft `Path(diagnostics[0].file_path) == source`. Unter `windows-2022` kann Mypy Groß-/Kleinschreibung des Laufwerksbuchstabens oder einen nicht aufgelösten Pfad zurückgeben. Vergleich über `Path(os.path.normcase(os.path.realpath(diagnostics[0].file_path))) == Path(os.path.normcase(os.path.realpath(source)))` härtet den Check plattformneutral (und funktioniert mit echtem Mypy).

---

#### `W6` — Windows-Python-Varianten in `_relocation.py` & LF-Zeilenenden in `doc_frame.py` `[BLOCKER STUFE 1/2]`

| Attribut | Detail |
| :--- | :--- |
| **Dateien** | [`src/qb_cubie/arenas/_relocation.py#L26`](../src/qb_cubie/arenas/_relocation.py#L26) (`L52`), [`src/qb_cubie/services/doc_frame/doc_frame.py#L211`](../src/qb_cubie/services/doc_frame/doc_frame.py#L211) |

- **`_relocation.py:26`:** Die Regex `r"(?:python|[π𝜋]thon)(?:w|\d+(?:\.\d+)*)?(?:\.exe)?"` passt auf `python.exe`, `pythonw.exe`, `python3.exe`, `python3.13.exe`, **aber nicht** auf `pythonw3.13.exe`, `python3.13t.exe` oder `python_d.exe`, die Pythons stdlib `venv` bzw. `uv` unter Windows `Scripts/` anlegen können → sofortiges `_unsupported(script)` schon bei einer frischen Standard-Venv!
- **`_relocation.py:52`:** `_relocate_text` sucht nur nach `os.fsencode(base) + b"/"`, nicht nach `b"\\"` (relevant für `.py`/`.bat`/`.ps1` mit Windows-Pfadtrennern).
- **`doc_frame.py:211`:** `file_path.write_text(new_content, encoding="utf-8")` ohne `newline="\n"` konvertiert auf Windows alle `\n` in `\r\n` und verändert damit Zeilenenden bestehender LF-Markdown-Dateien (`qb-cubie.exe docframe update`, bereits in `smoke_installed.py:187` ausgeführt).

---

### 2.2 Blocker für Stufe 2 (`CI / Repository / windows-2022`)

#### `W7` — Native Windows `.exe`-Console-Script-Launcher in `_relocation.py` (`cowsay_env` / `linter_env`) `[KRITISCHER BLOCKER STUFE 2]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Kritischer Blocker für Stufe 2 (`CI / Repository / windows-2022`)** |
| **Produktionscode** | [`src/qb_cubie/arenas/_relocation.py#L25-L33`](../src/qb_cubie/arenas/_relocation.py#L25-L33), [`src/qb_cubie/arenas/pyvenv.py#L425-L440`](../src/qb_cubie/arenas/pyvenv.py#L425-L440) (`ArenaBuilder`) |
| **Provisionierte Basen** | [`scripts/provision_test_arenas.py#L20-L25`](../../../scripts/provision_test_arenas.py#L20-L25) (`cowsay_env` mit `cowsay.exe`, `linter_env` mit `pylint.exe`, `isort.exe`, `pyreverse.exe`, `symilar.exe`, `pylint-config.exe`) |
| **Betroffene Tests** | ~20+ Repository-Tests in [`test_ebt_arena.py`](./tests_arena/test_ebt_arena.py), [`test_ebt_arena_mutation.py`](./tests_arena/test_ebt_arena_mutation.py), [`test_ebt_console_environment.py`](./tests_arena/test_ebt_console_environment.py), [`test_pyvenv_workspace_isolation.py#L341-L350`](./tests_arena/test_pyvenv_workspace_isolation.py#L341-L350), [`test_ebt_ignores.py`](./tests_ebt/test_ebt_ignores.py), [`test_ebt_imports.py`](./tests_ebt/test_ebt_imports.py), [`test_linter.py`](./tests_linter/test_linter.py), [`test_linter_ast.py`](./tests_linter/test_linter_ast.py) |

- **Root Cause:**
  - Auf Linux und macOS erzeugen `pip` und `uv` reine Text-Einstiegsskripte mit `#!...`-Shebang, die `_relocate_text()` bereits umschreibt.
  - Auf Windows erzeugen `uv pip install` (`uv 0.11.3`) und `pip` in `Scripts/` für jedes Konsolenskript (z. B. `cowsay.exe`, `pylint.exe`) ein PE-Wrapper-Executable.
  - `_relocation.py:30-31` verwirft derzeit **ausnahmslos jede** Nicht-Python-`.exe` mit `RuntimeError("Unsupported console entry point...")`. Dadurch ist weder `cowsay_env` noch `linter_env` unter Windows in `PyVenv` ausführbar.
- **Konkrete Format-Analyse auf Windows:**
  1. **`distlib`/`pip`-Wrapper:** Aufbau `[PE-Launcher-Stub] + b"#!" + <absoluter_python_pfad> + b"\r\n" + [ZIP-Archiv PK\x03\x04...]`. Der Launcher liest die Shebang-Zeile zwischen Stub und ZIP. Wichtig: Da das ZIP-Archiv Offsets ab Dateianfang (oder relativ) referenzieren kann, muss der Central Directory End-of-Central-Directory (EOCD) / Zip-Offset sauber berücksichtigt oder per `zipfile`/Offset-Anpassung beibehalten werden! (Genauer: `distlib` liest den ZIP-Trailer vom Dateiende; `zipfile` in Python bzw. `pip`/`distlib` erwartet ggf. unverschobene interne Zip-Offsets relativ zur PE-Größe, sofern sich die Shebang-Länge ändert — eine Anpassung des ZIP-Start-Offsets bzw. der Offsets im Central Directory / Zip-Stub oder Beibehalt der `distlib`-Shebang-Struktur inklusive Offset-Korrektur verhindert korrupte ZIP-Einträge bei unterschiedlich langen Klon-Pfaden!).
  2. **`uv-trampoline` (`uv 0.11.3`):** `uv` nutzt eigene Rust-Trampolines mit deterministischem Trailer am Dateiende: `[PE-Stub] + [optional ZIP] + [UTF-8-Python-Pfad] + [u32 Little-Endian Pfadlänge] + [4-Byte-Magic: UVSC | UVPY | UVUV]`. Zusätzlich unterstützt `uv venv --relocatable` relative Interpreterpfade in Trampolines.
  3. **Sichere Validierungsgrenze (`GUTACHTEN` / B7):** Alle übrigen `.exe`-Dateien **ohne** gültige `distlib`-Shebang-Struktur oder gültigen `uv`-Trampoline-Trailer — z. B. `native.exe` in [`test_ebt_console_environment.py#L107`](./tests_arena/test_ebt_console_environment.py#L107) und [`test_pyvenv_workspace_isolation.py#L343`](./tests_arena/test_pyvenv_workspace_isolation.py#L343) — **müssen** weiterhin zwingend vor dem Target-Aufruf mit `RuntimeError("Unsupported console entry point...")` abgelehnt werden! (Siehe **Entscheidung E2**.)

---

#### `W8` — Backslash- vs. POSIX-Slash-Separatoren in Diff-Pfaden (`ebt.py` & `reporter.py`) `[KRITISCHER BLOCKER STUFE 2]`

| Attribut | Detail |
| :--- | :--- |
| **Status / Priorität** | **Bestätigter Blocker für Stufe 2** (`CI / Repository / windows-2022`) |
| **Produktionscode** | [`src/qb_cubie/ebt.py#L701-L719`](../src/qb_cubie/ebt.py#L701-L719) (`_generate_diff`, `_modified_paths`), [`src/qb_cubie/reporter.py#L204-L213`](../src/qb_cubie/reporter.py#L204-L213) (`_summarize_fs_diffs`) |
| **Betroffene Tests** | [`tests/tests_ebt/test_ebt_directory_topology.py#L24-L60`](../tests/tests_ebt/test_ebt_directory_topology.py#L24-L60), [`tests/tests_ebt/test_ebt_fresh_file_comparison.py#L77-L78`](../tests/tests_ebt/test_ebt_fresh_file_comparison.py#L77-L78), [`tests/tests_ebt/test_ebt_fs_collisions.py#L22`](../tests/tests_ebt/test_ebt_fs_collisions.py#L22) (`L100`, `L108`, `L136`), [`tests/tests_user_workflows/test_fs_reporting.py#L65-L95`](../../../tests/tests_user_workflows/test_fs_reporting.py#L65-L95) (`L152` u. a. — 10+ Assertions) |

- **Root Cause:**
  - `EBT._generate_diff()` (Zeilen 706–707) und `_modified_paths()` (Zeile 718) formatieren relative `Path`-Keys mit `str(path)` statt `path.as_posix()`. Auf Windows entstehen Keys wie `"a\\b"` oder `"nested\\report.bin"`.
  - `PytestReporter._summarize_fs_diffs()` (Zeilen 210, 212) verwendet `os.path.normpath(os.path.join(str(scope), str(name)))`, was auf Windows `"out\\report.csv"` statt `"out/report.csv"` liefert.
  - Hinweis auch auf die Testhelfer selbst: `test_ebt_fs_collisions.py:22` (`str(path)`) und `test_fs_reporting.py:152` (`str(Path(scope) / name)`) erzeugen auf Windows Backslashes, obwohl die Soll-Erwartungen in den Parametern Literale wie `"out/2026/report.csv"` und `"left/shared"` sind! (Siehe **Entscheidung E3**.)

---

#### `W9` — Konkrete POSIX-Altlasten in Tests und Arena-Helfern `[BLOCKER STUFE 2]`

| Stelle | Aktueller Code ($Q_{\text{Ist}}$) | Problem unter `windows-2022` | Konkrete Behebung |
| :--- | :--- | :--- | :--- |
| [`test_security_arena_codec.py#L15`](../tests/tests_arena/test_security_arena_codec.py#L15) (`L34`, `L51`, `L65`) | `"touch /tmp/host_compromised.txt"` & `Path("/tmp/host_compromised.txt")` | Weder `/tmp` noch `touch` existieren unter Windows | Dynamischer Pfad in pytest `tmp_path` + portabler Python-Schreibbefehl |
| [`test_basic_mp.py#L31`](../tests/tests_multiprocessors/test_basic_mp.py#L31), [`test_multiprocess.py#L35`](../tests/tests_multiprocessors/test_multiprocess.py#L35) (`L45`) | `os.system('python3 -c ...')` & `os.system("echo '...' > venv_mutation_marker.txt")` | `python3` existiert in Windows-Venvs nicht; `echo 'x'` schreibt unter `cmd.exe` literale Single-Quotes `'...'` mit CRLF | `sys.executable` via `subprocess.run` bzw. portables Python-`Path(...).write_text(...)` |
| [`test_offline_core.py#L33`](../tests/test_offline_core.py#L33) (`L43`, `L80`, `L156`, `L272`) | `shlex.split(command)`, `name not in {"mypy", "pylint"}`, `symlinks=True`, `Path(base) / "bin" / "python"` | `shlex.split` in POSIX-Modus frisst Windows-Backslashes; `mypy.exe`/`pylint.exe` werden vom Audit-Hook abgelehnt; `symlinks=True` scheitert ohne Developer-Mode mit `WinError 1314`; `bin/python` fehlt unter `Scripts/python.exe` | `shlex.split(command, posix=os.name != "nt")`; Basisnamen ohne `.exe` (oder `{"mypy", "mypy.exe", "pylint", "pylint.exe"}`) zulassen; `symlinks=os.name != "nt"`; `_environment_python(Path(base))` |
| [`test_ebt_hydration_boundaries.py#L26`](../tests/tests_arena/test_ebt_hydration_boundaries.py#L26), [`test_arena_requirements.py#L21`](../tests/tests_arena/test_arena_requirements.py#L21), [`test_exception_observations.py#L25`](../tests/tests_arena/test_exception_observations.py#L25) | `venv.EnvBuilder(with_pip=False, symlinks=True)` | Wirft ohne Admin-Rechte / Developer Mode `OSError: [WinError 1314]` | `symlinks=os.name != "nt"` (analog `test_pyvenv_workspace_isolation.py:342`) |
| [`test_ebt_arena_mutation.py#L39`](../tests/tests_arena/test_ebt_arena_mutation.py#L39) | `Path(site.getsitepackages()[0])` | Liefert unter Windows oft das Venv-Root statt `Lib/site-packages` (Index 0 ist `prefix`, Index 1 `Lib\site-packages`) | `Path(sysconfig.get_path("purelib"))` |
| [`tempfs.py#L107`](../src/qb_cubie/arenas/tempfs.py#L107), [`provision_test_arenas.py#L36`](../../../scripts/provision_test_arenas.py#L36) | `shutil.rmtree(path)` ohne `onexc` | Schreibgeschützte Dateien in Workspaces/Venvs lösen auf Windows `PermissionError` aus | Gemeinsames/sauberes `onexc=_remove_readonly`-Aufräumen |
| [`_hydration.py#L28`](../src/qb_cubie/arenas/hydration.py#L28) | `Path(str(value).rstrip("/"))` | Trailing Backslashes aus Windows-Pfadstrings werden nicht getrimmt | `.rstrip("/\\")` |
| [`cubie_benchmarks/execution/_inputs.py#L196`](../../../experiments/benchmarks/cubie_benchmarks/execution/_inputs.py#L196) | `Path("/tmp/cubie-preflight-unused")` | Linux-Pfad-Literal im `check_runtime`-Preflight für Docker-SWEbench | Dokumentierte Docker-Grenze (läuft im Wheel-Check ohne `check_runtime`) |

---

#### `W10` — Encoding-, CRLF- & Test-Double-Hygiene `[HOHES RISIKO STUFE 2]`

1. **Produktionscode ohne explizites UTF-8:**
   - [`src/qb_cubie/linters/mypy.py#L82-L84`](../src/qb_cubie/linters/mypy.py#L82-L84) und [`src/qb_cubie/linters/pylint.py#L92-L94`](../src/qb_cubie/linters/pylint.py#L92-L94) rufen `subprocess.run(..., text=True, capture_output=True)` ohne `encoding="utf-8", errors="replace"` auf (Mypy/Pylint analysieren UTF-8-Quellcode und liefern Unicode-Diagnosen, z. B. Umlaute oder typografische Zeichen).
   - [`src/qb_cubie/arenas/_requirements.py#L95-L99`](../src/qb_cubie/arenas/_requirements.py#L95-L99) ruft `subprocess.run(..., check=True, capture_output=True, text=True)` ebenfalls ohne `encoding="utf-8", errors="replace"` auf.
   - [`src/qb_cubie/arenas/pyvenv.py#L438`](../src/qb_cubie/arenas/pyvenv.py#L438) (`L451`) decodiert `e.stderr.decode()` ohne `errors="replace"`.
2. **Kritischer Test-Double-Fallstrick beim Ergänzen von `encoding=` in `mypy.py` / `pylint.py`:**
   - [`tests/tests_linter/test_mypy_analysis_integrity.py#L22`](../tests/tests_linter/test_mypy_analysis_integrity.py#L22), [`tests/tests_linter/test_mypy_process_status.py#L26`](../tests/tests_linter/test_mypy_process_status.py#L26) und [`tests/tests_linter/test_pylint_analysis_integrity.py#L28`](../tests/tests_linter/test_pylint_analysis_integrity.py#L28) monkeypatchen `subprocess.run` mit **strikten Keyword-Signaturen ohne `encoding`/`errors` oder `**kwargs`** (`def run(cmd, *, text, capture_output)`).
   - **Konsequenz:** Sobald `mypy.py`/`pylint.py` `encoding="utf-8", errors="replace"` übergeben, brechen diese 3 Testmodule mit `TypeError: unexpected keyword argument 'encoding'` — ihre Test-Doubles müssen daher in der **Red-Phase** zuerst explizit auf `encoding="utf-8", errors="replace"` (inkl. Assertions darauf) erweitert werden!
3. **Tests mit implizitem Plattform-Encoding (`.read_text()` / `.write_text()` ohne `encoding="utf-8"`):**
   - [`tests/tests_arena/test_ebt_arena.py#L195`](../tests/tests_arena/test_ebt_arena.py#L195) (`böse_mutation.txt`), [`tests/tests_arena/test_exception_observations.py#L81`](../tests/tests_arena/test_exception_observations.py#L81), [`tests/tests_ebt/test_ebt_imports.py#L130-L245`](../tests/tests_ebt/test_ebt_imports.py#L130-L245), [`tests/tests_ebt/test_ebt_typing.py#L18-L109`](../tests/tests_ebt/test_ebt_typing.py#L18-L109), [`tests/test_offline_core.py#L200`](../tests/test_offline_core.py#L200), [`tests/wheel/ollama_agents_installed.py#L125`](../../../tests/wheel/ollama_agents_installed.py#L125) (`L175`).

---

#### `W11` — Styleguide-Budget (`FUNCTION_LIMIT = 12`, `MODULE_LIMIT = 777`) `[ARCHITEKTURGRENZE]`

Vermessung der betroffenen Produktionsmodule gemäß exakt [`tests/test_styleguide.py#L9-L68`](../../../tests/test_styleguide.py#L9-L68):

| Modul | Aktuelle LOC (Limit 777) | Längste Funktion (Limit 12 Body-Zeilen) | Headroom & Architektur-Konsequenz |
| :--- | :---: | :---: | :--- |
| [`ebt.py`](../src/qb_cubie/ebt.py) | `751` | `12` (`_validate_wrapper_keys` L600) | Nur 26 LOC frei; Änderung in `_generate_diff`/`_modified_paths` über Einzeiler (`.as_posix()`) ohne neue Zeilen. |
| [`doc_ensurance.py`](../src/qb_cubie/services/doc_ensurance/doc_ensurance.py) | `526` | `12` (`_report` L348) | Bei Option E1-A **0 Zeilen Änderung** nötig; bei E1-B sauberer 1-Zeilen-Helper. |
| [`pyvenv.py`](../src/qb_cubie/arenas/pyvenv.py) | `451` | `12` (`get_state` L135) | `_prepare_directories` liegt klar unter Limit; `errors="replace"` in `_ensure_venv_exists`/`_install_packages` ist zeilenneutral. |
| [`reporter.py`](../src/qb_cubie/reporter.py) | `400` | `12` (`report` L38) | `_summarize_fs_diffs` nutzt kompakte POSIX-Pfadnormalisierung (`PurePosixPath`/Helfer). |
| [`doc_frame.py`](../src/qb_cubie/services/doc_frame/doc_frame.py) | `341` | `10` (`run` L202) | `write_text(..., newline="\n")` ist zeilenneutral. |
| [`_process.py`](../src/qb_cubie/arenas/_process.py) | `179` | `11` (`_monitor_process` L70) | Win32 Job-Object + Reader-Thread-Logik **zwingend** in neues Hilfsmodul `arenas/_process_win32.py` auslagern. |
| [`tempfs.py`](../src/qb_cubie/arenas/tempfs.py) | `160` | `12` (`get_state` L86) | `.resolve()` auf `mkdtemp()` + `_remove_readonly` leicht einbaubar. |
| [`_hydration.py`](../src/qb_cubie/arenas/hydration.py) | `151` | `12` (`_checked` L95) | `.rstrip("/\\")` in `_filesystem_mapping` (L28) zeilenneutral. |
| [`pylint.py`](../src/qb_cubie/linters/pylint.py) | `107` | `8` (`_build_command` L39) | Genug Headroom für UTF-8-Option. |
| [`_relocation.py`](../src/qb_cubie/arenas/_relocation.py) | `99` | `11` (`_shell_header` L82) | `.exe`-Relokation (`distlib` + `uv-trampoline`) in eigenes Hilfsmodul `arenas/_relocation_win32.py` auslagern. |
| [`mypy.py`](../src/qb_cubie/linters/mypy.py) | `97` | `10` (`check` L31) | Genug Headroom für UTF-8-Option. |

---

## Teil 3: Zweistufiger Umsetzungs- und Priorisierungsplan

| Stufe | Ziel-CI-Jobs (`../../../.github/workflows/ci.yml`) | Enthaltene Befunde & Arbeiten | Abhängige Entscheidung |
| :--- | :--- | :--- | :--- |
| **Stufe 1** | **1.** `CI / Repository / macos-15` (`3.13`, `3.14`)<br>**2.** `CI / Wheel / windows-2022` (`3.13`, `3.14`) | `M1` (`.resolve()` für `TempFS`/`PyVenv` + `_relocate_link`), `M2` (Doku + optional kompakter macOS-Limit-EBT), `M3` (CI-Laufzeitstrategie), `W1` (`_process.py` Win32 vs. `DocEnsurance`-Timeout), `W2` (`check_wheel.py` ohne `orig_path`), `W3` (`cubie_benchmarks/execution/_process.py`), `W4` (`ollama_agents/reviewer/tools.py` + `ollama_agents_installed.py`), `W5` (`smoke_installed.py` 8.3/Case), `W6` (`_PYTHON_EXE_RE`, Backslash-Erkennung, `doc_frame.py` `newline="\n"`) | **E1**, **E4**, **E5** (und optional E2-B vs. E2-A Vorzug) |
| **Stufe 2** | **3.** `CI / Repository / windows-2022` (`3.13`, `3.14` inkl. `provision_test_arenas.py`) | `W7` (`distlib`- & `uv`-`.exe`-Launcher-Relokation in `_relocation_win32.py`), `W8` (POSIX-Slashes in `ebt.py`/`reporter.py` Diffs), `W9` (POSIX-Altlasten in Tests & `provision_test_arenas.py`), `W10` (UTF-8-Subprocess/IO in `mypy.py`, `pylint.py`, `_requirements.py`, Tests + 3 Linter-Test-Doubles) | **E2**, **E3**, **E5** |

---

## Teil 4: Architekturentscheidungen & offene Abstimmungspunkte (`E1–E5`)

Vor Eintritt in Schritt 2 (Red-Phase & Test-Freeze) bedürfen folgende fünf Design-Entscheidungen der Freigabe:

### `E1` — Ressourcenlimits (`_process.py`) & `DocEnsurance`-Default-Timeout unter Windows

- **Option `E1-A` (Empfohlen): Echte Win32-Unterstützung für `timeout` und `max_output_bytes` in `_process.py` + `_process_win32.py`**
  - *Technik:* Statt `os.name != "posix"` mit `NotImplementedError` abzuweisen, werden `timeout` und `max_output_bytes` auf Windows (`os.name == "nt"`) über zwei Daemon-Reader-Threads (vermeidet den fehlenden `selectors`-Pipe-Support auf Windows sowie Pipe-Deadlocks) mit gemeinsamem Lock/Byte-Budget und Win32 Job Objects via `ctypes.windll.kernel32` (`CreateJobObjectW`, `SetInformationJobObject` mit `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, `AssignProcessToJobObject`, `TerminateJobObject` + `taskkill /F /T /PID`-Fallback) durchgesetzt. Unbekannte OS-Namen wie `"java"` werfen weiterhin `NotImplementedError`.
  - *Vorteil:* `DocEnsurance(..., timeout=10.0)` / `timeout=2.0` (`smoke_installed.py:167`, `GUIDE_DocEnsurance.md:110`), `GUIDE_Arena-Management.md:128`, `test_docs_code_examples`, alle `tests_doc_ensurance/`, `test_ebt_phantom_calls.py:76,93` und `test_process_limits.py` laufen nativ und ehrlich auf Windows — ohne abgeschwächte Garantien.
  - *Test-Migration:* [`test_process_limits.py#L34-L39`](./tests_arena/test_process_limits.py#L34-L39) muss von `"nt"` auf eine generische nicht unterstützte Plattform umgestellt werden, und die `@pytest.mark.skipif(os.name != "posix")` in Zeilen 42/60/70/80 entfallen für `"nt"`.
- **Option `E1-B` (Minimal-Alternative): `_process.py` bleibt POSIX-only; `DocEnsurance` umgeht `timeout` unter Windows**
  - *Nachteil:* `tests/wheel/smoke_installed.py:167` (`timeout=2.0`), `docs/core/GUIDE_Arena-Management.md:128` und `docs/services/GUIDE_DocEnsurance.md:110` bräuchten explizite Plattform-Ausnahmen; `DocEnsurance` verlöre unter Windows seinen Hänger-Schutz.

### `E2` — Windows `.exe`-Console-Script-Launcher (`_relocation.py`)

- **Option `E2-A` (Empfohlen für Stufe 2): Sichere Dual-Format-Relokation (`distlib` + `uv-trampoline`)**
  - *Technik:* Neues Hilfsmodul `_relocation_win32.py` prüft `.exe`-Dateien in `Scripts/` auf exakt zwei bekannte Wrapper-Formate und passt ausschließlich den eingebetteten Python-Interpreterpfad auf den Arena-Klon an (bei `distlib` inkl. ZIP-Offset-/Trailer-Korrektur, bei `uv` durch Erneuerung des `UTF-8-Pfad + u32-Länge + UVSC/UVPY/UVUV`-Trailers; zusätzlich optional `uv venv --relocatable` in `ArenaBuilder`). Jede andere `.exe`-Datei (`native.exe`, unbekannte PE-Binaries) löst unverändert `RuntimeError("Unsupported console entry point...")` aus (`test_ebt_console_environment.py:107`, `test_pyvenv_workspace_isolation.py:343`).
- **Option `E2-B` (Stufe-1-Reduktion):** In Stufe 1 nur `_PYTHON_EXE_RE` (`pythonw3.x.exe`, `python3.xt.exe`, `python_d.exe`) und `b"\\"` in `_relocate_text` beheben; `.exe`-Console-Script-Relokation auf Stufe 2 verschieben. (Bei Wahl von `E5-A` wird `E2-B` in Stufe 1 umgesetzt und `E2-A` direkt anschließend in Stufe 2.)

### `E3` — Cross-Platform-Normalisierung von Diff-Pfaden (`ebt.py` & `reporter.py`)

- **Option `E3-A` (Empfohlen): Kanonische POSIX-Slashes (`/`) in allen Diff-Ausgaben**
  - *Technik:* `EBT._generate_diff()` / `_modified_paths()` in `ebt.py:706-718` verwenden `path.as_posix()`, `PytestReporter._summarize_fs_diffs()` in `reporter.py:210-212` normalisiert auf POSIX-Slashes (wie bereits in `doc_frame` über `.as_posix()`).
  - *Vorteil:* `JsonReporter`-Artefakte und `trace.diffs` sind betriebssystemübergreifend stabil; alle bestehenden Diff-Assertions in `test_ebt_directory_topology.py`, `test_ebt_fresh_file_comparison.py`, `test_ebt_fs_collisions.py` und `test_fs_reporting.py` bleiben fachlich unverändert gültig (lediglich die Testhelfer `test_ebt_fs_collisions.py:22` und `test_fs_reporting.py:152` nutzen ebenfalls `.as_posix()`).
- **Option `E3-B`:** OS-native Separatoren behalten und alle 15+ Diff-Test-Assertions plattformabhängig umschreiben (verschlechtert Snapshot-/JSON-Vergleichbarkeit).

### `E4` — Umfang & Laufzeitstrategie der CI-Matrix (`../../../.github/workflows/ci.yml`)

1. **`macos-15` im `tests`-Job (`Python 3.13` & `3.14`):**
   - *Variante `E4-Fast`:* CI führt `-n 2 --dist loadscope` (nutzt bereits im Repo vorhandenes `pytest-xdist 3.8.0`) mit `timeout-minutes: 30` aus — erfordert vorab Abgleich mit [`test_mp_xdist.py`](./tests_multiprocessors/test_mp_xdist.py) wegen Worker-in-Worker-Multiprocessing.
   - *Variante `E4-Split` (Empfohlen):* Zwei getrennte Pytest-Aufrufe im `tests`-Job — `-m "not slow" -q` (schnelles Feedback, ggf. mit xdist) gefolgt von `-m slow -q` ohne äußeres xdist (vermeidet Übersubskription in `test_multiprocess.py` / `test_mp_hypothesis.py`), mit `timeout-minutes: 35` für `macos-15` (und später `windows-2022`).
   - *Variante `E4-Seq`:* Unverändertes `pytest -m "" -q` mit `timeout-minutes: 35–45`.
2. **macOS-Ressourcenlimit-Ergänzung (`M2`):** Soll neben dem ehrlichen Linux-`/proc`-Skip in `test_ebt_resource_limits.py` ein kompakter POSIX-portabler EBT-Prozessgruppen-Timeout-Test (ohne `/proc`, aktiv auf Linux **und** macOS) ergänzt werden? *(Empfohlen: Ja — prüft `os.killpg` im EBT-Kontext auch nativ auf `macos-15`.)*
3. **Windows-Matrix in `ci.yml`:** Stufe 1 nimmt `windows-2022` in `wheel` (`os: [ubuntu-24.04, macos-15, windows-2022]`) und `macos-15` in `tests` auf; Stufe 2 erweitert `tests` auf `[ubuntu-24.04, macos-15, windows-2022]` inkl. `uv run --no-sync python scripts/provision_test_arenas.py`.

### `E5` — Ausführungsreihenfolge der TGD-Zyklen

- **Option `E5-A` (Empfohlen): Zwei saubere, eigenständige TGD-Zyklen (`Stufe 1` → `Stufe 2`)**
  - Zuerst **Stufe 1** (`macos-15` Repo-CI + `windows-2022` Wheel-CI inkl. `E1-A` und `E2-B`) komplett durch Schritte 2–5 führen und verifizieren; anschließend in einem fokussierten zweiten Zyklus **Stufe 2** (`E2-A`, `E3-A`, `W8–W10`, `CI / Repository / windows-2022`) abschließen.
- **Option `E5-B`:** Stufe 1 und Stufe 2 in einem gemeinsamen TGD-Durchlauf kombinieren.

---

## Teil 5: Geplante Red-Phase-Testmatrix (Vorbereitung Schritt 2)

Alle neuen und migrierten Tests müssen **Meta-Gate 1** (kanonische `qb_cubie`-Imports, [`test_gate_1.py`](../../../tests/tests_meta/test_gate_1.py)), **Meta-Gate 2** (keine unbegründeten EBT-Kreuzprodukte, [`test_gate_2.py`](../../../tests/tests_meta/test_gate_2.py)) und **Meta-Gate 3** (keine einsamen Negationen, [`test_gate_3.py`](../../../tests/tests_meta/test_gate_3.py)) einhalten, ohne stille `xfail`s oder *Vacuous Passes*.

### 5.1 Host-agnostisch auf Linux verifizierbare Red-Phase-Proben

| Befund | Ziel-Testmodul | Scharfes Red-Signal gegen `HEAD = 518cf28f` |
| :--- | :--- | :--- |
| `M1` | Neues/erweitertes Arena-Testmodul (z. B. [`test_ebt_tempfs.py`](./tests_arena/test_ebt_tempfs.py) / neues Plattform-Modul) | Monkeypatch `tempfile.mkdtemp` liefert einen Pfad über einen temporären Verzeichnis-Symlink (`alias -> real_dir`): `TempFS` und `PyVenv` (`VIRTUAL_ENV` vs. `sys.prefix`) scheitern an unaufgelöstem `workspace_path`/`_root_path`, sowie `_relocate_link` bei Symlink-Differenz zwischen `base` und `target.resolve()`. |
| `W1` (`E1-A`) | [`tests/tests_arena/test_process_limits.py`](./tests_arena/test_process_limits.py) | Simulation des Win32-Dispatcher-Pfads (bounded output budget + timeout + Baumabbruch); Migration von `test_unsupported_platform_rejects_limits_explicitly` auf `"java"`. |
| `W2` | Neues Unit-Testmodul für `../../../scripts/check_wheel.py` | Aufruf der `PATH`-Konstruktionsfunktion mit simuliertem `os.name == "nt"` und `PATH=C:\FakeLinter\bin` weist nach, dass `FakeLinter` aktuell fälschlich in den isolierten Wheel-`PATH` durchsickert. |
| `W3`, `W4` | Gezielte Unit-Tests für `cubie_benchmarks.execution._process` & `ollama_agents.reviewer.tools` | Prüfung auf UTF-8/System-`PATH` sowie Windows-kompatibles Timeout-Killing (ohne direktes ungeschütztes `os.killpg` bei `os.name == "nt"`). |
| `W6` | [`tests/tests_arena/test_ebt_console_environment.py`](./tests_arena/test_ebt_console_environment.py) / [`tests/tests_services/tests_doc_frame/`](./tests_services/tests_doc_frame/) | `_relocate()` mit `pythonw3.13.exe`, `python3.13t.exe`, `python_d.exe` + Backslash-Skripten schlägt fehl; `DocFrame.update()` unter `newline` erhält `\r\n` vs. `\n` Vertrag. |
| `W7` (`E2-A`) | Neues Arena-Launcher-Testmodul (`test_win32_launcher_relocation.py`) | Synthetische `distlib`-(`PE + #!<base>\Scripts\python.exe\r\n + ZIP` mit `PK`-Integritätsprüfung) und `uv-trampoline`-Launcher (`UTF-8 + u32 len + UVSC/UVPY`) scheitern aktuell an `Unsupported console entry point`; `native.exe` ohne Launcher-Signatur bleibt weiterhin abgelehnt! |
| `W8` (`E3-A`) | [`tests/tests_ebt/test_ebt_directory_topology.py`](./tests_ebt/test_ebt_directory_topology.py) / [`../../../tests/tests_user_workflows/test_fs_reporting.py`](../../../tests/tests_user_workflows/test_fs_reporting.py) | Direkte Probe für `PureWindowsPath`-/`os.sep`-Normalisierung in `_generate_diff` & `_summarize_fs_diffs` + `.as_posix()` in Testhelfern. |
| `W10` | [`tests/tests_linter/test_mypy_analysis_integrity.py`](./tests_linter/test_mypy_analysis_integrity.py), [`test_mypy_process_status.py`](./tests_linter/test_mypy_process_status.py), [`test_pylint_analysis_integrity.py`](./tests_linter/test_pylint_analysis_integrity.py) | Erweiterung der 3 Monkeypatch-Doubles auf `encoding="utf-8", errors="replace"` schlägt gegen `mypy.py`/`pylint.py` vor Green-Phase rot fehl (`assert encoding == "utf-8"`). |

### 5.2 Nativ auf `macos-15` und `windows-2022` wirksame Verträge

- **`macos-15` (`Stufe 1`):** `test_ebt_tempfs.py` (9 Fälle), `test_ebt_console_environment.py`, neuer kompakter POSIX-EBT-Timeout-Test (ohne `/proc`), vollständige Suite `pytest -m ""` nach CI-Strategie `E4`.
- **`windows-2022` (`Stufe 1`):** `python scripts/check_wheel.py dist` komplett über alle 3 Profile (`core`, `linters`, `benchmarks` inkl. `smoke_installed.py:167` `DocEnsurance`, `smoke_installed.py:187` `qb-cubie.exe docframe update`, `benchmark_installed.py` und `ollama_agents_installed.py`).
- **`windows-2022` (`Stufe 2`):** `provision_test_arenas.py` + `pytest -m ""` über bereinigte `test_security_arena_codec.py`, `test_basic_mp.py`, `test_multiprocess.py`, `test_offline_core.py`, `test_ebt_arena_mutation.py`, `test_process_limits.py`, `test_ebt_phantom_calls.py`, `test_ebt_directory_topology.py`, `test_fs_reporting.py` und `test_styleguide.py:test_docs_code_examples`.

---

## Teil 6: Living-Documentation-Sync-Checkliste (Vorbereitung Schritt 5)

Nach der Green-Phase müssen folgende Dokumente synchronisiert und über `DocEnsurance` (`tests/test_styleguide.py:test_docs_code_examples`) verifiziert werden:

1. **[`../../../CI_PLATFORM_STATUS.md`](../../../CI_PLATFORM_STATUS.md):** Plattform-Tabelle auf den realen Stand nach Stufe 1 / Stufe 2 heben; historische Analyse (`a4af5dad`/`085e7a00`) aktualisieren (inkl. Korrektur von Abschnitt 4 Punkt 3, falls echte `distlib`/`uv`-Relokation umgesetzt wird, sowie macOS-`/proc`-Skip-Dokumentation).
2. **[`../../core/GUIDE_Arena-Management.md`](../../core/GUIDE_Arena-Management.md):** Aussagen in Zeilen 61–63 (*„Native Windows-Konsolenlauncher sind derzeit nicht unterstützt“*) und Zeilen 120–145 (*POSIX-Limits* vs. Win32-Unterstützung gemäß E1/E2) an das neue $Q_{\text{Soll}}$ angleichen.
3. **[`docs/dev/DEV-GUIDE_2-3_Arenas.md`](../docs/dev/DEV-GUIDE_2-3_Arenas.md):** Beschreibung der unterstützten Einstiegsskripte (Zeile 43) und optionalen Betriebsgrenzen (`_process.py`, Zeilen 65–70) aktualisieren.
4. **[`../../../KNOWN_ISSUES.md`](../../../KNOWN_ISSUES.md) & [`../../../CHANGELOG.md`](../../../CHANGELOG.md):** Behobene Plattform-Einschränkungen im `[Unreleased]`-Abschnitt von `../../../CHANGELOG.md` dokumentieren, offene verbleibende Grenzen (z. B. Docker-Pfad in `cubie_benchmarks` `swebench` oder macOS-`/proc`-Watchdog) ehrlich in `KNOWN_ISSUES.md` / `CI_PLATFORM_STATUS.md` führen.
5. **TGD-Abschlussprotokoll:** Strukturierte Dokumentation analog [`tests/tests_arena/TGD_1.md`](./tests_arena/TGD_1.md) nach erfolgreichem Gesamtabnahmelauf.

---

> [!NOTE]
> **Schritt-1-Grenze eingehalten:** Gemäß [`tests/GEMINI.md`](./GEMINI.md) und [`../../GUIDE_Quality-Assurance.md` (§ 3)](../../GUIDE_Quality-Assurance.md#3-test-guided-development-tgd-in-f%C3%BCnf-schritten) wurden in diesem Analyseschritt **keine** Dateien in `../../../src`, `tests/**/*.py`, `docs/`, `scripts/`, `experiments/` oder `.github/` verändert. Erst nach Abstimmung der Entscheidungspunkte **`E1–E5`** startet Schritt 2 (Red-Phase & Test-Freeze).

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../../README.md)  
[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../../dev/README.md)  
[↦ | Core-Internals | ↤](../../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  

[↦ | Analysis: Stärkung der CI-Matrix für Windows und macOS | ↤](./ANALYSIS_CI_MATRIX.md)  
[↦ | Analyse: Möglichkeiten zum Bau eines Analyse-Werkzeugs für EBT-Case-Coverage auf Quellcode-Objekten | ↤](./ANALYSIS_COVERAGE_OPTIONS.md)  
[↦ | Archiv behobener Bugs (`SOLVED_ISSUES.md`) | ↤](./SOLVED_ISSUES.md)  

</div>
<!-- /qb:frame -->

