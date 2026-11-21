<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Neon" effort="High" -->
# Analysis: Reparatur von BUG-001 (`PyVenv`-Workspace-Isolation)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Neon
- **Reasoning-Effort:** High
- **Analysedatum:** 20. November 2026, ~ 10:15 (CET)
- **Synthesebasis:** `tests/tests_arena/GEMINI.md`, `KNOWN_ISSUES.md`, `GUTACHTEN.md` (§ 6.1, B1), `pyproject.toml`, `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/arenas/codecs.py`, `src/qb_cubie/arenas/phantom_hook.py`, `src/qb_cubie/arenas/tempfs.py`, `src/qb_cubie/arenas/_tempfs_runner.py`, `../../src/qb_cubie/arenas/hydration.py`, `src/qb_cubie/arenas/_relocation.py`, `src/qb_cubie/ebt.py`, `src/qb_cubie/protocols.py`, `src/qb_cubie/linter.py`, `tests/tests_arena/test_ebt_arena.py`, `tests/tests_arena/test_ebt_hydration_boundaries.py`, `tests/tests_arena/test_ebt_tempfs.py`, `tests/tests_arena/test_ebt_console_environment.py`, `tests/tests_arena/test_arena_requirements.py`, `tests/tests_arena/test_ebt_phantom_calls.py`, `tests/tests_arena/test_phantom_import_policy.py`, `tests/tests_arena/test_ebt_arena_mutation.py`, `tests/tests_arena/test_ebt_resource_limits.py`, `tests/tests_arena/resource_cases/runner.py`, `tests/tests_arena/test_security_arena_codec.py`, `tests/tests_arena/test_ipc_codecs.py`, `tests/tests_arena/test_random_findings.py`, `tests/tests_ebt/test_ebt_imports.py`, `tests/tests_ebt/test_ebt_ignores.py`, `tests/tests_ebt/test_ebt_directory_topology.py`, `tests/tests_ebt/test_ebt_fs_collisions.py`, `tests/tests_linter/test_linter.py`, `tests/tests_linter/test_mypy.py`, `tests/test_offline_core.py`, `tests/test_styleguide.py`, `tests/wheel/smoke_installed.py`, `docs/dev/README.md`, `docs/dev/Style-Guide.md`, `docs/dev/DEV-GUIDE_2-3_Arenas.md`, `docs/dev/DEV-GUIDE_Write-down-the-bugs.md`, `docs/core/GUIDE_Arena-Management.md`, `docs/core/GUIDE_Contract-Semantics.md`, `docs/GUIDE_Quality-Assurance.md`, Git-Historie (`bc11bff1` bis `c8beda64`)
- **Stand:** qb-cubie (`v0.0.9`, gemäß `pyproject.toml:7`)
- **Git-Log:** `git log -n 1`
```text
commit c8beda64ea7104aa6f9e8165fb41552da170e4c9 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Fri Nov 20 10:04:31 2026 +0100

    Added the QA-GUIDES as routing table to the docs/README.md
```

---

---

<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **Vollständige Bestätigung von `BUG-001` — plus drei weitere direkt verwandte Symptome derselben Ursache:**
   In [`src/qb_cubie/arenas/pyvenv.py`](../../src/qb_cubie/arenas/pyvenv.py) teilen sich fachliche Testdaten (`pre.fs` / `post.fs`) und Arena-Infrastruktur (`.venv/`, `_cubie_phantom.py`, `ipc_in<suffix>`, `ipc_out<suffix>` sowie implizit erzeugtes `__pycache__/`) exakt dasselbe Verzeichnis (`self.workspace_path`). Empirische Gegenproben gegen `HEAD = c8beda64` bestätigen über alle drei Codecs (`PickleCodec`, `MSGspecCodec`, `CloudpickleCodec`) insgesamt **sechs konkrete Defekt-Klassen**:
   - **K1:** Stilles Überschreiben bereitgestellter `ipc_in<suffix>`-Testdaten vor Target-Aufruf.
   - **K2:** Stilles Überschreiben und anschließendes Löschen bereitgestellter `ipc_out<suffix>`-Testdaten durch `_teardown_ipc_files()`.
   - **K3:** Stilles Überschreiben bereitgestellter `_cubie_phantom.py`-Testdaten — **und** dauerhafter Verbleib von `_cubie_phantom.py` sowie `__pycache__/` im Workspace (beide werden in `_teardown_ipc_files()` nicht entfernt).
   - **K4:** Systematisches Scheitern vollständiger Workspace-Vergleiche (`post=WorldState(fs={".": empty_ref})`) an **81 unerwarteten Infrastruktur-Pfaden** unter `['.venv', '__pycache__', '_cubie_phantom.py']`.
   - **K5:** Stille Umlenkung bei `pre.fs={".venv": <host_file>}` — `_hydration.py` leitet die Datei über `if target.is_dir(): target = target / source.name` still in `workspace/.venv/<source.name>` um statt eine Datei `.venv` anzulegen; umgekehrt schreiben Mappings wie `".venv/..."` physisch in die geklonte Venv hinein.
   - **K6 (Shadowing-Risiko analog `TempFS`):** Da `PyVenv` den Kindprozess mit `python -c <script>` startet (`sys.path[0] == "" == workspace_path`), schattet eine über `pre.fs` bereitgestellte Datei wie `msgspec.py`, `cloudpickle.py`, `pickle.py` oder `_cubie_phantom.py` die Transport-Infrastruktur des Runners ab und führt vor der Target-Ausführung zum `Arena System-Error (Exit Code 1)`. Eine bloße Auslagerung von `_cubie_phantom.py` über `PYTHONPATH` ohne Entkopplung der `sys.path`-Reihenfolge würde K6 für `_cubie_phantom.py` **nicht** beheben!

2. **Kritische Bestands-Test-Konflikte ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$) in der Testsuite:**
   Der Baseline-Lauf `tests/tests_arena/` ist aktuell grün (**243 passed, 40 deselected in 23.39s**). Eine Trennung von `.venv/` und `workspace_path` kollidiert jedoch mit **zwei historischen Test-Gruppen** und legt **einen drohenden Vacuous Pass** frei:
   - **4 brechende Alt-Tests in [`tests/tests_arena/test_ebt_arena.py:255-328`](../../tests/tests_arena/test_ebt_arena.py#L255-L328):** Der historische Block `PROOF of '.venv'-ENCAPSULATION` (Commit `bc11bff1`) erzwingt ausdrücklich `Path(".venv").is_dir() == True` und `VIRTUAL_ENV == str(Path.cwd() / ".venv")` im `workspace_path` ($Q_{\text{Ist}}$-Altlast).
   - **3 brechende parametrisierte Fälle in [`tests/tests_arena/test_ebt_hydration_boundaries.py:214-241`](../../tests/tests_arena/test_ebt_hydration_boundaries.py#L214-L241):** `test_pyvenv_hydration_cannot_write_through_base_symlinks` erwartet `ValueError` bei `pre.fs={".venv...": ...}`, weil er voraussetzt, dass `base` nach `workspace/.venv` geklont wurde. Nach der physischen Trennung von `workspace/` und `.venv/` ist diese Schutzinvariante strukturell stärker erfüllt (Hydrierung kann `.venv`-Symlinks gar nicht mehr erreichen), sodass der Test auf das neue $Q_{\text{Soll}}$ umgestellt werden muss.
   - **1 drohender *Vacuous Pass* in [`tests/tests_linter/test_linter.py:17-25`](../../tests/tests_linter/test_linter.py#L17-L25):** `test_linter_discovery_and_ignores` prüft die `.venv`-Exclusion von `Pylint` ohne eigenes `pre.fs` — er verließ sich implizit auf `PyVenv`s eigenes `.venv/` im Workspace und würde nach dem Fix auf einem leeren Verzeichnis vakuös grün durchlaufen.

3. **Betroffene Dokumentation & Architektur-Grenzen:**
   - **3 Handbücher** ([`docs/core/GUIDE_Arena-Management.md`](../../docs/core/GUIDE_Arena-Management.md), [`docs/dev/DEV-GUIDE_2-3_Arenas.md`](../../docs/dev/DEV-GUIDE_2-3_Arenas.md), [`docs/core/GUIDE_Contract-Semantics.md`](../../docs/core/GUIDE_Contract-Semantics.md)) sowie [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) müssen synchronisiert werden.
   - `src/qb_cubie/arenas/pyvenv.py` steht aktuell bei **408 LOC** (max. Funktionslänge **12/12** in `get_state`, `setup` bei **10/12**); die Reparatur erfordert saubere Kompositions-Helfer, um `tests/test_styleguide.py` (`FUNCTION_LIMIT = 12`) und `tests/test_lint.py` (`ruff`, `pylint`, `mypy`) ohne Verstöße einzuhalten.

---

## Teil 1: Technische Root-Cause-Analyse & Empirische Baseline (`HEAD = c8beda64`)

### 1.1 Code-Anatomie des Namensraum-Konflikts in `src/qb_cubie/arenas/pyvenv.py`

Die fehlende Trennung zwischen fachlichem Arbeitsbereich (`workspace_path`) und Laufzeit-Infrastruktur entsteht an vier Stellen in [`src/qb_cubie/arenas/pyvenv.py`](../../src/qb_cubie/arenas/pyvenv.py):

1. **Klonen der Venv in `workspace_path` ([`pyvenv.py:103-114`](../../src/qb_cubie/arenas/pyvenv.py#L103-L114)):**
   ```python
   workspace = Path(tempfile.mkdtemp(prefix=f"{self.arena_id}_"))
   self.workspace_path = workspace
   self.virtual_path = workspace / ".venv"
   shutil.copytree(base_env, str(self.virtual_path), symlinks=True)
   relocate_scripts(base_env, self.virtual_path)
   self._hydrate()
   ```
   `workspace_path` dient gleichzeitig als Wurzel für die geklonte Venv (`workspace/.venv`), als Hydrierungsziel für `pre.fs`, als `cwd` des Kindprozesses und als Basisverzeichnis für `get_state().fs` (welches `EBT._evaluate_fs()` gegen `post.fs` vergleicht).

2. **Platzierung von IPC-Dateien und Phantom-Hook im Workspace ([`pyvenv.py:250-260`](../../src/qb_cubie/arenas/pyvenv.py#L250-L260)):**
   ```python
   self._in_path = str(self.workspace_path / f"ipc_in{self.codec.file_suffix}")
   self._out_path = str(self.workspace_path / f"ipc_out{self.codec.file_suffix}")
   phantom_src = CURRENT_DIR / "phantom_hook.py"
   ...
   shutil.copy2(phantom_src, self.workspace_path / "_cubie_phantom.py")
   ```
   Weder Existenz noch Eigentümerschaft der drei Zielpfade werden geprüft; eine über `pre.fs` hydrierte Datei wird kommentarlos überschrieben.

3. **Unvollständiges Aufräumen nach `execute()` ([`pyvenv.py:297-305`](../../src/qb_cubie/arenas/pyvenv.py#L297-L305)):**
   ```python
   if self._in_path and os.path.exists(self._in_path):
       os.remove(self._in_path)
   if self._out_path and os.path.exists(self._out_path):
       os.remove(self._out_path)
   ```
   - `ipc_in<suffix>` und `ipc_out<suffix>` werden bedingungslos gelöscht — einschließlich gleichnamiger Testdaten aus `pre.fs`.
   - `_cubie_phantom.py` und das beim Kindprozess-Import entstandene `__pycache__/_cubie_phantom.*.pyc` werden **gar nicht** entfernt und bleiben für `EBT._evaluate_fs()` sichtbar.

4. **Start des Kindprozesses mit `cwd` auf `sys.path[0]` ([`pyvenv.py:321-325`](../../src/qb_cubie/arenas/pyvenv.py#L321-L325) & [`codecs.py:223-336`](../../src/qb_cubie/arenas/codecs.py#L223-L336)):**
   ```python
   self._process = run_process(
       [str(self._python_exe), "-c", script], env=self._env_vars,
       cwd=self.workspace_path, capture_output=True, ...
   )
   ```
   Bei `python -c` setzt CPython automatisch `sys.path[0] = ""` (entspricht `cwd == workspace_path`) **vor** `PYTHONPATH`, Standardbibliothek und `site-packages`. Die drei Runner-Snippets in [`codecs.py`](../../src/qb_cubie/arenas/codecs.py#L223-L336) importieren als allererstes `pickle` / `msgspec` / `cloudpickle`, `importlib` und `_cubie_phantom`. Dadurch schattet jede gleichnamige Datei in `pre.fs` die Transport-Schicht ab.

### 1.2 Empirische Verifikation aller sechs Defekt-Klassen gegen `v0.0.9`

Alle folgenden Beobachtungen wurden am `20.11.2026` direkt gegen `HEAD = c8beda64` mit `.venv/bin/python` und `tests/.arenas/empty_venv` reproduziert:

| ID | Gegenprobe (`pre.fs` / Vertrag) | Beobachtetes Ist-Verhalten ($Q_{\text{Ist}}$) | Erwartetes Soll-Verhalten ($Q_{\text{Soll}}$) |
| :--- | :--- | :--- | :--- |
| **K1** | `pre.fs={"ipc_in<suffix>": 3 Bytes}` $\to$ `os.path:getsize` | `Pickle`: **56 B**, `MSGspec`: **93 B**, `Cloudpickle`: **112 B** (`eval=False`) | Exakt **3 Bytes** bei allen 3 Codecs |
| **K2** | `pre.fs={"ipc_out<suffix>": 3 Bytes}` $\to$ `builtins:int("1")` + `post.fs` | Alle 3 Codecs: `Path not found. Arena: False, Host: True` (`eval=False`) | Datei bleibt unverändert erhalten (`diffs=None`, `eval=True`) |
| **K3** | `pre.fs={"_cubie_phantom.py": 15 Bytes}` $\to$ `getsize` + `post.fs` | `actual_size=4095` (`phantom_hook.py`), `diffs.fs`: `{'_cubie_phantom.py': {'modified': ['.']}}` | Exakt **15 Bytes**, unverändert im Workspace |
| **K4** | Leeres `pre.fs`, `builtins:int("1")`, `post.fs={".": empty_ref}` | `eval=False`, **81** `unexpected`-Einträge unter `['.venv', '__pycache__', '_cubie_phantom.py']` | `eval=True`, `diffs=None` (Workspace ist vollständig leer) |
| **K5** | `pre.fs={".venv": <host_file>}` $\to$ `os.path:isfile(".venv")` | `returns=False`; Datei landet still in `.venv/dotvenv_file` (`has_dotvenv_dir=True`) | `os.path.isfile(".venv") == True`; geklonte Arena-Venv unberührt |
| **K6** | `pre.fs={"msgspec.py": "raise RuntimeError('SHADOWED_MSGSPEC')"}` | `RuntimeError: Arena System-Error (Exit Code 1)` beim `import msgspec` vor Target-Aufruf | Target läuft erfolgreich (`eval=True`); `msgspec.py` bleibt unveränderte Workspace-Datei |

Zusätzliche Lebenszyklus-Beobachtung bei leerem `WorldState()`:
- Direkt nach `arena.setup(WorldState())`: `workspace_path` enthält `['.venv']`.
- Direkt nach `arena.execute(...)` (also zum Zeitpunkt von `EBT._evaluate_fs()`): `workspace_path` enthält `['.venv', '__pycache__', '_cubie_phantom.py']`.

### 1.3 Referenz-Vergleich mit `TempFS`

[`src/qb_cubie/arenas/tempfs.py`](../../src/qb_cubie/arenas/tempfs.py) und [`src/qb_cubie/arenas/_tempfs_runner.py`](../../src/qb_cubie/arenas/_tempfs_runner.py) lösen genau diese Problemklasse bereits sauber als Architektur-Vorbild:
1. **Externe IPC-Ablage (`tempfs.py:78-79`):** `with tempfile.TemporaryDirectory(prefix=f"{self.arena_id}_ipc_") as ipc_dir:` hält `input.pkl` und `output.pkl` strikt außerhalb von `self.workspace_path` und räumt sie nach jedem `execute()` deterministisch ab.
2. **Transport-First-Import (`_tempfs_runner.py:18-26`):** Der Runner lädt zuerst `cloudpickle` über die Caller-Pfade und hängt **erst danach** `sys.path.insert(0, str(Path.cwd()))` ein.
3. **Vertragliche Absicherung (`test_ebt_tempfs.py:313-321`):** `test_workspace_contains_no_ipc_files_and_cannot_shadow_transport` beweist für `TempFS`, dass `pre.fs={"cloudpickle.py": ...}` weder den Transport abschattet noch IPC-Artefakte im `Path.cwd().iterdir()` erscheinen.

---

## Teil 2: Vollständige Inventur der Testsuite ($Q_{\text{Ist}}$-Altlasten, Vacuous Passes & Invarianten)

### 2.1 Baseline-Messung

- `.venv/bin/python -m pytest -q tests/tests_arena/` am Stand `c8beda64`: **`243 passed, 40 deselected in 23.39s`**.
- Statische Architektur-Metriken der betroffenen Produktionsmodule (geprüft mit `tests/test_styleguide.py::body_lines`):
  - [`src/qb_cubie/arenas/pyvenv.py`](../../src/qb_cubie/arenas/pyvenv.py): **408 LOC**, 33 Funktionen, Maximum: `get_state` (`12/12` Body-Zeilen), `setup` (`10/12`), `_run_in_subprocess` (`10/12`), `teardown` (`7/12`).
  - [`src/qb_cubie/arenas/codecs.py`](../../src/qb_cubie/arenas/codecs.py): **336 LOC**, 20 Funktionen, Maximum: `_serialization_error` (`10/12` Body-Zeilen).
  - [`src/qb_cubie/arenas/phantom_hook.py`](../../src/qb_cubie/arenas/phantom_hook.py): **117 LOC**, 18 Funktionen, Maximum: `activate_hook` (`8/12` Body-Zeilen).

### 2.2 Kategorie A — Bestands-Tests, die durch die Reparatur **gebrochen werden** ($Q_{\text{Ist}}$-Kopplung)

| Datei & Zeilen | Test(s) | Aktuelle Annahme ($Q_{\text{Ist}}$) | Warum betroffen & empfohlene $Q_{\text{Soll}}$-Migration |
| :--- | :--- | :--- | :--- |
| [`tests/tests_arena/test_ebt_arena.py:255-328`](../../tests/tests_arena/test_ebt_arena.py#L255-L328) | `test_clean_workspace_contains_venv_folder`, `test_bugreport_workspace_contains_venv_folder`, `test_venv_contains_system_folders`, `test_virtual_env_var_is_correct` *(4 Tests; `test_workspace_root_is_clean` bleibt grün)* | Historischer Block `PROOF of '.venv'-ENCAPSULATION` (Commit `bc11bff1`): verlangt `Path(".venv").is_dir() == True` und `VIRTUAL_ENV == str(Path.cwd() / ".venv")` direkt im `workspace_path`. | Verteidigt genau die in `BUG-001` bemängelte Mischung von `.venv/` und Workspace. **Migration:** Prüfen, dass `Path.cwd()` frei von `.venv`, `bin`/`lib`, `_cubie_phantom.py` und `ipc_*` ist (`list(Path.cwd().iterdir()) == []`) und `VIRTUAL_ENV` auf ein getrenntes, geklontes `cubie_arena_*`-Verzeichnis außerhalb von `Path.cwd()` zeigt, das `bin`/`Scripts` und `lib`/`Lib` enthält. |
| [`tests/tests_arena/test_ebt_hydration_boundaries.py:214-241`](../../tests/tests_arena/test_ebt_hydration_boundaries.py#L214-L241) | `test_pyvenv_hydration_cannot_write_through_base_symlinks` *(3 parametrisierte Fälle: `file`, `tree`, `directory-basename`)* | Hydriert `pre.fs={".venv": ...}` bzw. `".venv/payload.txt"` gegen eine Minimal-Basis mit Symlink `base/payload.txt -> host-file.txt` und erwartet `ValueError` aus `_hydrate()`. | Setzt voraus, dass `base` nach `workspace/.venv` geklont wurde. Nach Trennung liegt `.venv` außerhalb von `workspace/`; `_hydrate()` legt legal `workspace/.venv/payload.txt` an, ohne den Basis-Symlink überhaupt zu berühren (und die Minimal-Basis ohne Python-Binary würde danach erst in `_get_python_exe()` scheitern). **Migration:** Mit einer echten/minimalen ausführbaren Basis (wie `hydration_base` + externem Symlink im Klon) prüfen, dass `pre.fs={".venv/payload.txt": source}` und `pre.fs={".venv": source}` ausschließlich in `workspace/` landen, `protected` (Host-Ziel des Basis-Symlinks) **und** `virtual_path` unverändert bleiben — und parallel beweisen, dass `../.venv/payload.txt` weiterhin vor Target-Ausführung mit `ValueError` abgelehnt wird! |

### 2.3 Kategorie B — Bestands-Test mit drohendem **Vacuous Pass** (Meta-QA-Befund)

| Datei & Zeilen | Test | Versteckte Kopplung | Risiko & Empfehlung |
| :--- | :--- | :--- | :--- |
| [`tests/tests_linter/test_linter.py:17-25`](../../tests/tests_linter/test_linter.py#L17-L25) | `test_linter_discovery_and_ignores` | Startet `AstLinter(Pylint()).check` mit leerem `pre=WorldState()` in `PyVenv("tests/.arenas/linter_env")` und erwartet `returns=[]`. Docstring: *„The .venv directory was successfully excluded.“* | Bisher scannte `Pylint` den Workspace inkl. `PyVenv`s eigenem `.venv/` (und `_cubie_phantom.py`). Sobald `.venv/` den Workspace verlässt, ist `Path.cwd()` komplett leer — der Test bleibt grün, testet aber gar keine `.venv`-Exclusion mehr! **Empfehlung:** Explizit `pre=WorldState(fs={".venv/bad_code.py": "tests/fixtures/bad_code.py"})` bereitstellen (analog `tests/tests_linter/test_mypy.py:99`). |

### 2.4 Kategorie C — Kritische Invarianten bestehender Tests, die der Fix **zwingend erhalten** muss

Eine Prüfung aller 28 Testdateien mit `PyVenv`-Bezug ergibt folgende harte Kompatibilitäts-Invarianten:

1. **Kein Verzeichnis-Leak in `tempfile.tempdir` (`scratch`):**
   - [`test_ebt_hydration_boundaries.py:71,273`](../../tests/tests_arena/test_ebt_hydration_boundaries.py#L71) und [`resource_cases/runner.py:114`](../../tests/tests_arena/resource_cases/runner.py#L114) setzen `tempfile.tempdir = str(scratch)` und fordern nach Erfolg, Hydrierungsfehler, Timeout und Output-Limit exakt `scratch_entries == []`.
2. **`VIRTUAL_ENV`-Namenskonvention & Teardown-Zerstörung:**
   - [`test_ebt_arena.py:97,166,244,250-252`](../../tests/tests_arena/test_ebt_arena.py#L235-L252) fordern `"cubie_arena_" in VIRTUAL_ENV`, `arena.workspace_path is None`, `arena.virtual_path is None` und `not Path(VIRTUAL_ENV).exists()` nach `teardown()`.
3. **Frühzeitiger Abbruch ohne Disk-Artefakte vor `mkdtemp`:**
   - [`test_arena_requirements.py:144,171,202`](../../tests/tests_arena/test_arena_requirements.py#L123-L202) fordern, dass bei fehlender Basis, unerfüllten Codec-Anforderungen oder fehlendem `pyvenv.cfg` `arena.workspace_path is None` bleibt und die Basis nicht mutiert wird.
4. **Aufräumen bei fehlgeschlagenem `relocate_scripts()`:**
   - [`test_ebt_console_environment.py:108-126,146-153`](../../tests/tests_arena/test_ebt_console_environment.py#L107-L153) fordern bei ungültigem Launcher in `setup()` Abbruch vor Target-Ausführung sowie `arena.workspace_path is None and arena.virtual_path is None` (und vollständiges Löschen des bereits angelegten Klons).
5. **Importierbarkeit hydrierter Module aus `workspace_path` (`cwd`):**
   - [`test_ebt_imports.py:193-251`](../../tests/tests_ebt/test_ebt_imports.py#L193-L251) (`test_import_dynamic_fs`, `test_import_absolute_shadowing` mit `utils.py`, `test_import_relative_package`), [`test_ebt_console_environment.py:91`](../../tests/tests_arena/test_ebt_console_environment.py#L91), [`test_ebt_phantom_calls.py:77`](../../tests/tests_arena/test_ebt_phantom_calls.py#L77) und [`test_phantom_import_policy.py:42,69`](../../tests/tests_arena/test_phantom_import_policy.py#L42) importieren Module, die per `pre.fs` in `workspace_path` liegen. `workspace_path` **muss** beim Target-Import und zur Target-Laufzeit auf `sys.path[0]` stehen.
6. **Arena-Diff-Semantik (`post.arena`) unverändert:**
   - [`test_ebt_arena_mutation.py`](../../tests/tests_arena/test_ebt_arena_mutation.py) und [`test_ebt_ignores.py:91-104`](../../tests/tests_ebt/test_ebt_ignores.py#L91-L104) vergleichen `get_state().arena` (`str(self.virtual_path.absolute())`) gegen `post.arena`. Da `virtual_path` weiterhin der saubere Venv-Klon ist, bleibt das 100 % kompatibel — und wird sogar robuster, da `pre.fs` die Venv nicht mehr versehentlich verschmutzen kann (z. B. in `tests/tests_linter/test_mypy.py:99`).
7. **Wheel-Tauglichkeit (`phantom_hook.py`):**
   - [`tests/wheel/smoke_installed.py:96-106`](../../tests/wheel/smoke_installed.py#L96-L106) testet `PyVenv` gegen ein installiertes, potenziell schreibgeschütztes Wheel (`site-packages/qb_cubie/arenas/phantom_hook.py`). Der Kindprozess darf deshalb kein `__pycache__` im Installationsverzeichnis von `qb_cubie` voraussetzen.
8. **Security-Matrix (`test_security_arena_codec.py`):**
   - [`tests/tests_arena/test_security_arena_codec.py:12-54`](../../tests/tests_arena/test_security_arena_codec.py#L12-L54) sucht im Runner-Stack nach `co_consts`-Strings mit `.pkl` bzw. `.msgpack`. Da `out_path` weiterhin ein absoluter Pfad mit `self.codec.file_suffix` im generierten Runner-Snippet bleibt, bleiben beide Tests kompatibel.

---

## Teil 3: Architekturentwurf & Design-Optionen für die Reparatur

### 3.1 Ziel-Verzeichnislayout (empfohlen: ein gemeinsamer Laufzeit-Root)

Analog zu `TempFS` — aber erweitert um die geklonte virtuelle Umgebung und die Phantom-Middleware — sollte `PyVenv.setup()` einen **einzelnen temporären Elternordner** (`self._root_path`) anlegen und darin fachlichen Arbeitsbereich und Infrastruktur strikt trennen:

```text
<tempfile.tempdir>/cubie_arena_<custom_id>_<hex>_<rand>/   # self._root_path
├── workspace/                                             # self.workspace_path (CWD, pre.fs, post.fs)
├── .venv/                                                 # self.virtual_path (Klon von base_env, VIRTUAL_ENV)
└── _ipc_<rand>/  (TemporaryDirectory pro execute())       # temporär je Lauf, automatisch abgeräumt
    ├── ipc_in<suffix>                                     # self._in_path
    ├── ipc_out<suffix>                                    # self._out_path
    └── _cubie_phantom.py                                  # Kopie von phantom_hook.py (außerhalb workspace!)
```

**Vorteile dieser Topologie:**
1. **100 % sauberer `workspace_path`:** Vor, während und nach `execute()` enthält `self.workspace_path` ausschließlich Dateien aus `pre.fs` und Effekte des Targets. Vollständige Verzeichnisvergleiche (`post.fs={".": ref_dir}`) funktionieren identisch zu `TempFS`.
2. **Atomares, leckfreies `teardown()`:** `shutil.rmtree(self._root_path)` entfernt `workspace/`, `.venv/` und etwaige Reste in einem Schritt — auch wenn `setup()` nach `mkdtemp` (z. B. in `copytree`, `relocate_scripts` oder `_hydrate`) fehlschlägt. Dabei bleiben `self._root_path`, `self.workspace_path` und `self.virtual_path` nach `teardown()` konsistent `None`.
3. **Unveränderte `VIRTUAL_ENV`- und `arena_id`-Invariante:** `self.virtual_path` liegt unter `<tempdir>/cubie_arena_<id>_<rand>/.venv`, enthält also weiterhin `"cubie_arena_"` und steht nicht mehr innerhalb von `self.workspace_path`.
4. **Struktureller Hydrierungsschutz:** `_hydration.py` verankert `self.root = workspace_path.resolve()`. Jeder Versuch `../.venv/...` oder `../_ipc_...` aus `workspace/` auszubrechen, wird weiterhin deterministisch mit `ValueError` abgewiesen, während fachliche Mappings wie `".venv"` oder `".venv/bad_types.py"` konfliktfrei im Workspace landen.
5. **Mehrfache `execute()`-Aufrufe je `setup()`:** Da `_ipc_<rand>/` per `tempfile.TemporaryDirectory(prefix="ipc_", dir=self._root_path)` im `try/finally` von `_run_in_subprocess()` verwaltet wird, bleiben wiederholte `execute()`-Aufrufe auf derselben vorbereiteten Arena ohne gegenseitige Rückstände sauber.
6. **Kein Schreibzugriff ins `qb_cubie`-Installationspaket:** Die Kopie `_cubie_phantom.py` liegt im temporären `_ipc_<rand>/`-Ordner; etwaige Bytecode-Dateien (`__pycache__`) entstehen niemals in `workspace/` und niemals im installierten `site-packages/qb_cubie/`.

### 3.2 Entkopplung von `_cubie_phantom.py` & Schutz vor Transport-Shadowing (K6)

Hier besteht eine wichtige Architekturentscheidung zwischen zwei Optionen:

#### Option 1 (Minimale Auslagerung via `PYTHONPATH` — **unzureichend für K6!**)
- Kopiert `phantom_hook.py` nach `<ipc_dir>/_cubie_phantom.py` und hängt `<ipc_dir>` an `PYTHONPATH` an; `python -c <script>` bleibt unverändert.
- **Problem:** Bei `python -c` steht `""` (`cwd == workspace_path`) als `sys.path[0]` **vor** `PYTHONPATH` und **vor** `site-packages`.
  - Enthält `pre.fs` eine Datei `_cubie_phantom.py`, importiert der Runner die **Benutzerdatei** statt Cubies Phantom-Hook!
  - Enthält `pre.fs` `msgspec.py`, `cloudpickle.py` oder `pickle.py`, stürzt der Runner beim Codec-Import ab (wie in Probe K6 empirisch bewiesen).

#### Option 2 (Empfohlen: `python -P` + Transport-First-Reihenfolge, konsistent mit `TempFS`)
- `PyVenv` ruft den Kindprozess mit `[str(self._python_exe), "-P", "-c", script]` auf (`-P` existiert seit Python 3.11; `qb-cubie` verlangt `requires-python >= 3.13` laut `pyproject.toml:13`).
- `<ipc_dir>` (mit `_cubie_phantom.py`) wird im `PYTHONPATH` eingetragen (oder per `spec_from_file_location` geladen).
- Durch `-P` ist `workspace_path` beim Start des Runners **nicht** auf `sys.path`:
  1. Alle Transport-Imports (`pickle` / `msgspec` / `cloudpickle`, `importlib`, `_cubie_phantom`) werden garantiert aus der Arena-Venv bzw. `<ipc_dir>` geladen — immun gegen `msgspec.py`, `cloudpickle.py`, `pickle.py` und `_cubie_phantom.py` im Workspace!
  2. Unmittelbar nach den Transport-Imports (und vor dem Laden des Targets / der Payload-Deserialisierung) führen die drei Runner in [`src/qb_cubie/arenas/codecs.py`](../../src/qb_cubie/arenas/codecs.py#L223-L336) exakt dasselbe Muster wie [`_tempfs_runner.py:25`](../../src/qb_cubie/arenas/_tempfs_runner.py#L25) aus:
     ```python
     sys.path.insert(0, os.getcwd())
     ```
  3. Optional wird `_cubie_phantom` nach Bindung an eine lokale Variable (oder nach `import _cubie_phantom as _phantom`) aus `sys.modules` entfernt (`sys.modules.pop("_cubie_phantom", None)`), sodass selbst ein Target, das absichtlich `import _cubie_phantom` aufruft, seine eigene Workspace-Datei `_cubie_phantom.py` laden kann (ohne Kollision mit Cubies interner Middleware)!
  4. **Feinheit bei `PickleCodec` und `CloudpickleCodec`:**
     - `PickleCodec`: `decontams = pickle.load(f)` lädt nur Strings; danach `sys.path.insert(0, os.getcwd())` vor `with _cubie_phantom.activate_hook(decontams)` und dem zweiten `pickle.load(f)` (welches Klassen aus Workspace-Modulen referenzieren kann).
     - `CloudpickleCodec`: `sys.path.insert(0, os.getcwd())` nach `import cloudpickle, importlib, _cubie_phantom` und vor `cloudpickle.load(f)` (da Cloudpickle-Payloads Workspace-Module importieren können).
     - `MSGspecCodec`: `sys.path.insert(0, os.getcwd())` nach `msgspec.msgpack.decode(...)` und vor `with _cubie_phantom.activate_hook(decontams)` / `importlib.import_module(...)`.

#### Abwägung für benutzerdefinierte `IPCC`-Codecs
Das öffentliche Protokoll `IPCC` ([`src/qb_cubie/protocols.py:189-205`](../../src/qb_cubie/protocols.py#L189-L205)) bleibt in seiner Signatur (`file_suffix`, `requirements`, `dump`, `load`, `get_runner_snippet(in_path, out_path)`) **100 % unverändert**.
- Einziger Hinweis bei Option 2 (`-P`): Sollte ein externer Custom-`IPCC`-Codec ein eigenes Runner-Snippet schreiben, das Workspace-Module importiert, ohne selbst `sys.path.insert(0, os.getcwd())` auszuführen, würde `-P` diesen Import unterbinden.
- **Bewertung:** Da es im Repository keine fremden `IPCC`-Implementierungen gibt und die drei mitgelieferten Codecs das gesamte `IPCC`-Ökosystem bilden, überwiegt der Sicherheits- und Symmetriegewinn zu `TempFS` (Schutz gegen K6) deutlich. Alternativ ließe sich für noch strengere Custom-Codec-Abwärtskompatibilität prüfen, ob `-P` generell für `PyVenv` als Vertrag in `DEV-GUIDE_2-3_Arenas.md` dokumentiert wird (empfohlen, da simpel, explizit und ohne Magie).

### 3.3 Betrachtung von `PyVenv._inject_project_code()` (`PYTHONPATH`)

In [`pyvenv.py:230-237`](../../src/qb_cubie/arenas/pyvenv.py#L230-L237) baut `_inject_project_code()` heute `PYTHONPATH` aus `[p for p in sys.path if "site-packages" not in p and "dist-packages" not in p]`.
- **Wichtige Prüfung:** Enthält `sys.path` des Host-Prozesses `""` (leerer String) oder `"."`?
  - Wenn `""` in `safe_paths` landet, interpretiert CPython einen leeren Eintrag in `PYTHONPATH` (z. B. `":/src"` oder `"/src:"`) ebenfalls als `cwd` (`workspace_path`) — was `-P` unterlaufen würde!
  - **Konkreter Fix-Hinweis:** Beim Zusammenbau von `PYTHONPATH` sollten leere Einträge (`p == ""` bzw. `not p`) herausgefiltert und `<ipc_dir>` (für `_cubie_phantom.py`) sauber angehängt/eingefügt werden, sodass `PYTHONPATH` beim Kindprozess-Start **kein** implizites `cwd` einschleust! (Hinweis: `safe_paths` muss weiterhin das Projekt-`src/`-Verzeichnis enthalten, damit Host-Testmodule wie `tests.tests_arena.test_ebt_arena` in `PyVenv` importierbar bleiben.)

### 3.4 Styleguide-Check für die spätere Implementierung (`FUNCTION_LIMIT = 12`)

Da `pyvenv.py` bereits nahe an der 12-Zeilen-Grenze liegt:
- `setup(self, state)` sollte das Anlegen der Verzeichnisstruktur in eine kleine Hilfsmethode (z. B. `_prepare_directories(self) -> None`) auslagern, um deutlich unter 12 Body-Zeilen zu bleiben.
- `teardown(self)` prüft `self._root_path is None` (oder `self.workspace_path is None`), löscht `self._root_path` (sofern existent) und setzt `_root_path`, `workspace_path`, `virtual_path` auf `None`.
- `_run_in_subprocess(self, target, args, kwargs)` kann `with tempfile.TemporaryDirectory(prefix="ipc_", dir=self._root_path) as ipc_dir:` nutzen und `_setup_ipc_files(Path(ipc_dir))` / `_teardown_ipc_files()` sauber auf dem temporären `ipc_dir` betreiben (bzw. das Verzeichnis durch den Kontextmanager automatisch abräumen lassen).
- `PYTHONPATH`-Konstruktion mit `<ipc_dir>` muss `self._env_vars` pro `execute()`-Aufruf sauber halten (keine Akkumulation alter `ipc_dir`-Einträge über mehrere `execute()`-Aufrufe hinweg — da `_prepare_env()` bei jedem `execute()` eine frische `os.environ.copy()` anlegt, ist das sauber, solange `<ipc_dir>` nicht in `self._env_vars` vor `_prepare_env()` mutiert wird!).

---

## Teil 4: Betroffene Dokumentation (`docs/` & Repository-Root)

| Dokument | Betroffene Stelle(n) | Anpassungsbedarf |
| :--- | :--- | :--- |
| [`docs/core/GUIDE_Arena-Management.md`](../../docs/core/GUIDE_Arena-Management.md) | **Z. 42–44** (Hydrierung & Basis-Links), **Z. 56** (*„kopiert eine vorhandene virtuelle Umgebung in den Workspace“*), *(Zusatzfund **Z. 177**: veralteter Satz „Hydrierungsziele werden nicht auf den Workspace begrenzt“ widerspricht Z. 29–45)* | Z. 56 korrigieren: `.venv`, IPC-Dateien und Phantom-Middleware liegen außerhalb des fachlichen `workspace_path` (analog `TempFS`); vollständige Workspace-Vergleiche `fs={".": ...}` funktionieren ohne Infrastruktur-Artefakte. Z. 42–44 entsprechend präzisieren. |
| [`docs/dev/DEV-GUIDE_2-3_Arenas.md`](../../docs/dev/DEV-GUIDE_2-3_Arenas.md) | **Z. 41** (*„`workspace_path` bezeichnet den temporären Arbeitsordner und `virtual_path` dessen kopierte `.venv`“*) | Klarstellen, dass `workspace_path` (fachlicher Arbeitsbereich), `virtual_path` (geklonte Venv) und die temporäre IPC-/Phantom-Ablage getrennte Verzeichnisse unterhalb eines gemeinsamen temporären Laufzeit-Roots sind; Verhalten von `-P` / `sys.path`-Reihenfolge für `IPCC`-Runner dokumentieren. |
| [`docs/core/GUIDE_Contract-Semantics.md`](../../docs/core/GUIDE_Contract-Semantics.md) | **Z. 156** (`fs={".": "fixtures/post"}`), **Z. 180–182** (geklonte PyVenv-Basis) | Klarstellen, dass die geklonte `PyVenv`-Umgebung und ihre IPC-Dateien außerhalb des geprüften Workspace liegen, sodass `fs={".": ...}` für `TempFS` und `PyVenv` konsistent arbeitet. |
| [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) | **Z. 22–47** (`[BUG-001]`) | Nach Abschluss der Green-Phase gemäß [`DEV-GUIDE_Write-down-the-bugs.md`](../../docs/dev/DEV-GUIDE_Write-down-the-bugs.md#L100) auf `Behoben` setzen / archivieren und Fix in `CHANGELOG.md` dokumentieren. |

---

## Teil 5: Vorschlag für die nächsten TGD-Schritte (Entscheidungspunkte & Red-Phase-Matrix)

Gemäß dem 5-stufigen TGD-Prozess ([`docs/GUIDE_Quality-Assurance.md` § 3](../../docs/GUIDE_Quality-Assurance.md#3-test-guided-development-tgd-in-fünf-schritten)) wurden in diesem Analyse-Schritt **keine** Dateien in `src/`, `tests/**/*.py` oder `docs/` verändert.

### Offene Design-Entscheidungen vor der Red-Phase

1. **Bestätigung der Topologie:** Gemeinsamer temporärer Root (`self._root_path`) mit getrennten `workspace/`, `.venv/` und temporärem `_ipc_<rand>/` je `execute()`-Aufruf? *(Empfohlen)*
2. **Bestätigung von Option 2 (`python -P` + Transport-First + leere `PYTHONPATH`-Einträge filtern):** Soll neben K1–K5 direkt auch K6 (Transport-Shadowing durch `msgspec.py`, `cloudpickle.py`, `pickle.py`, `_cubie_phantom.py` analog `TempFS`) mitbehoben werden? *(Empfohlen — sonst bleibt `pre.fs={"_cubie_phantom.py": ...}` trotz Auslagerung anfällig für Import-Shadowing!)*
3. **Bestätigung der Test-Migration ($Q_{\text{Ist}} \to Q_{\text{Soll}}$):** Einverständnis zur Anpassung der 3 identifizierten Alt-Teststellen in der Red-Phase:
   - [`tests/tests_arena/test_ebt_arena.py:255-328`](../../tests/tests_arena/test_ebt_arena.py#L255-L328) (4 `.venv`-im-Workspace-Tests auf getrennte Venv + reinen Workspace umstellen),
   - [`tests/tests_arena/test_ebt_hydration_boundaries.py:214-241`](../../tests/tests_arena/test_ebt_hydration_boundaries.py#L214-L241) (`test_pyvenv_hydration_cannot_write_through_base_symlinks` auf Isolation statt Kollision + `../.venv`-Ausbruchs-Guard umstellen),
   - [`tests/tests_linter/test_linter.py:17-25`](../../tests/tests_linter/test_linter.py#L17-L25) (explizite `.venv/bad_code.py`-Fixture ergänzen gegen Vacuous Pass).

### Geplante Regressionstest-Matrix für die Red-Phase (z. B. `tests/tests_arena/test_pyvenv_workspace_isolation.py`)

Alle folgenden Verträge schlagen gegen den aktuellen Core (`c8beda64`) kontrolliert **ROT (`FAILED`)** fehl und müssen in der Green-Phase deterministisch auf **GRÜN (`PASSED`)** springen:

1. **Namenskollisionen über alle 3 Codecs (`PickleCodec`, `MSGspecCodec`, `CloudpickleCodec`):**
   - `pre.fs` mit `ipc_in<suffix>` (exakter Inhalt & Bytegröße im Target **und** im `post.fs`-Vergleich unverändert).
   - `pre.fs` mit `ipc_out<suffix>` (Inhalt im Target **und** nach `execute()` im `post.fs`-Vergleich unverändert vorhanden).
   - `pre.fs` mit `_cubie_phantom.py` (Inhalt unverändert, kein Überschreiben durch `phantom_hook.py`, kein Shadowing der Phantom-Middleware inkl. funktionierendem `decontams`-Check!).
   - `pre.fs` mit `.venv` als Datei **und** `.venv/data.txt` als Verzeichnisbaum (beides landet im fachlichen Workspace, ohne `virtual_path` zu verändern).
2. **Transport-Shadowing-Schutz (Option 2):**
   - `pre.fs` mit `msgspec.py` (`MSGspecCodec`), `cloudpickle.py` (`CloudpickleCodec`) und `pickle.py` (`PickleCodec`), die beim Import `RuntimeError("shadowed")` werfen — Runner startet trotzdem fehlerfrei und Datei bleibt unverändert.
3. **Vollständige Workspace-Vergleiche (`post.fs={".": ref_dir}`) über alle 3 Codecs:**
   - No-Op-Target gegen leeres Referenzverzeichnis (`diffs is None`, `eval is True`).
   - Mutierendes Target (erzeugt/ändert fachliche Datei) gegen exakte Referenz-Topologie (inkl. Gegenprobe mit `expect=False` bei zusätzlicher unerwarteter Datei).
   - `sorted(p.name for p in Path.cwd().iterdir())` enthält während der Ausführung ausschließlich hydrierte Dateien (kein `.venv`, kein `_cubie_phantom.py`, kein `__pycache__`, kein `ipc_*`).
4. **Lebenszyklus- & Cleanup-Invarianten:**
   - Mehrfache `execute()`-Aufrufe zwischen einem `setup()` und `teardown()` hinterlassen keine IPC-Reste im Workspace oder in `tempfile.tempdir`.
   - Fehlerhafte `setup()`-Läufe (`relocate_scripts`-Fehler, Hydrierungs-Escape `../.venv/escape.txt`), Target-Exceptions und normale `teardown()`-Läufe hinterlassen exakt **0** Einträge in `tempfile.tempdir` (`scratch`) und setzen `workspace_path` sowie `virtual_path` auf `None`.
   - `post.arena`-Vergleich (z. B. gegen `empty_venv`) bleibt trotz `pre.fs={".venv/user.txt": ...}` unverändert grün (Beweis der physischen Trennung zwischen fachlichem `.venv` und Arena-`virtual_path`).
