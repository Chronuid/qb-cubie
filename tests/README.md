# Testsuite-Leitfaden

Die Testsuite von `qb-cubie` nutzt **Option A (schneller Dev-Default)** kombiniert mit **benannten Profilen** über `pytest`-Marker und das [Makefile](../Makefile).

Ein einfacher `pytest`-Aufruf führt standardmäßig nur schnelle Tests (`not slow`) aus. Schwere Skalierungs-, Subprozess-, Watchdog-Timeout-, Linter-Voll- und Doku-Tests werden über explizite Profile oder in der CI zugeschaltet.

---

## Schnellstart

```bash
# 1. Entwicklungsabhängigkeiten & Arena-Basen einmalig vorbereiten
uv sync --locked --group dev
.venv/bin/python scripts/provision_test_arenas.py

# 2. Schneller Dev-Standard (ohne slow, nutzt addopts aus pyproject.toml)
.venv/bin/python -m pytest -q
# oder via Makefile:
make test          # sequentiell
make test-fast-p   # parallel via pytest-xdist (-n auto --dist loadscope)
```

---

## Profile über `make`

Alle verfügbaren Ziele lassen sich jederzeit mit `make help` anzeigen:

| Ziel | Inhalt | Typischer Einsatz |
| :--- | :--- | :--- |
| `make test` / `make test-fast` | Schnelle Tests (`not slow`) sequentiell | Standard beim Entwickeln / Debuggen |
| `make test-fast-p` | Schnelle Tests parallel (`-n auto --dist loadscope`) | Schneller Check vor Commits |
| `make test-all` | Komplette Suite inkl. `slow` & `--hypothesis-profile=ci` | Vollständiger lokaler Abnahmelauf |
| `make test-all-p` | Komplette Suite parallel (`-n auto --dist loadscope`) | Schneller Volllauf vor dem Push |
| `make test-slow` | Nur als `slow` markierte Tests | Gezieltes Nachtesten schwerer Fälle |
| `make test-lint` | Statische Analyse (`ruff`, `pylint`, `mypy`), Styleguide & Doku-Beispiele | Code-Qualität & Doku prüfen |
| `make test-lf` | Zuletzt fehlgeschlagene Tests zuerst, Abbruch beim 1. Fehler (`--lf -x`) | Schnelle Fehler-Iteration |
| `make test-ebt` | Alle Core-EBT-Tests | Arbeit an `ebt` / `WorldState` |
| `make test-arena` | Alle Arena-Tests (inkl. Resource-Limits) | Arbeit an `TempFS` / `PyVenv` / IPC |
| `make test-mp` | Alle Multiprocessing-Tests (inkl. Scaling & Hypothesis) | Arbeit an Worker-Pools / `loky` |
| `make test-linter` | Alle Linter-Integrationstests | Arbeit an `AstLinter` / `CstLinter` |
| `make test-services` | Alle Service-Tests (z. B. `DocEnsurance`) | Arbeit an Services |
| `make test-workflows` | Alle User-Workflow-Tests | Akzeptanz-/End-to-End-Verhalten |
| `make test-reviewer` | Alle RBT- & Reviewer-Tests | Arbeit an `RBT` / Reviewern |
| `make test-meta` | Repo-Meta-Verträge, Styleguide & Offline-/Tk-Checks | Struktur- & Vertragsprüfungen |

---

## Direkte `pytest`-Nutzung & Marker

Die Konfiguration liegt in [`pyproject.toml`](../pyproject.toml) (`--strict-markers -m 'not slow'`). Sobald du auf der Kommandozeile selbst `-m` angibst, ersetzt das den Default-Filter aus `addopts`:

```bash
# Volllauf (überschreibt -m 'not slow')
.venv/bin/python -m pytest -m "" -q

# Nur ein Subsystem, aber ohne slow-Tests
.venv/bin/python -m pytest -m "arena and not slow" -q

# Ein einzelnes Verzeichnis inkl. slow-Tests
.venv/bin/python -m pytest -m "" tests/tests_linter -q

# Interaktive Tests (z. B. Reviewer) ohne Output-Capture
.venv/bin/python -m pytest -s tests/test_headless_reviewer.py
```

### Verfügbare Marker

**Laufzeit-Dimension:**
- `fast` – schnelle Unit- und Vertragstests (Standard lokal)
- `slow` – schwere Skalierungs-, Timeout-/Watchdog-, Netzwerk-, Tool-Subprozess- oder Doku-Ausführungstests

**Subsystem- & Kategorie-Dimension:**
- `ebt` (`tests/tests_ebt/`)
- `arena` (`tests/tests_arena/`)
- `multiprocess` (`tests/tests_multiprocessors/`)
- `linter` (`tests/tests_linter/`, `tests/test_lint.py`)
- `services` (`tests/tests_services/`)
- `workflows` (`tests/tests_user_workflows/`)
- `reviewer` (`test_headless_reviewer.py`, `test_human_reviewer_fresh_decision.py`, `test_rbt_reporter.py`, `test_rbt_demo.py`)
- `meta` (`test_lint.py`, `test_styleguide.py`, `test_default_collection_contract.py`, `test_offline_core.py`, `test_core_without_tk.py`)
- `lint` (`test_lint.py`, `test_styleguide.py`)
- `hypothesis` (`tests/tests_multiprocessors/test_mp_hypothesis.py`)

---

## Automatisches Tagging & neue Tests einordnen

In [`tests/conftest.py`](./conftest.py) weist `pytest_collection_modifyitems` neuen Tests automatisch ihre Subsystem- und Standard-Geschwindigkeitsmarker anhand des Dateipfads zu:

- Neue Tests in `tests/tests_ebt/`, `tests/tests_arena/` usw. erhalten ihren Subsystem-Marker automatisch.
- Wenn kein `slow`-Marker gesetzt ist, wird der Test automatisch mit `fast` markiert.
- Einzelne schwere Tests in einem schnellen Modul einfach direkt mit `@pytest.mark.slow` dekorieren.
- Einzelne schnelle Tests in einem als `slow` eingestuften Modul lassen sich umgekehrt mit `@pytest.mark.fast` explizit in den Dev-Default zurückholen.

> **Hinweis zum Collection-Vertrag:** [`test_default_collection_contract.py`](./test_default_collection_contract.py) prüft mit `-o addopts=`, dass alle historischen Testdateien weiterhin Teil der regulären `pytest`-Collection bleiben. Deshalb erfolgt die Filterung ausschließlich über Marker und **nicht** über `norecursedirs`.

---

## Hypothesis-Profile & CI

- **Lokal (`dev`, Standard):** `max_examples=15, deadline=None`
- **CI (`ci`, automatisch bei gesetztem `CI`):** `max_examples=100, deadline=None`

Manuell umschaltbar per CLI-Flag oder Umgebungsvariable:

```bash
.venv/bin/python -m pytest -m hypothesis --hypothesis-profile=ci -q
```

In [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) läuft `pytest -m "" -q`, sodass die komplette Suite inklusive aller `slow`- und `ci`-Hypothesis-Tests ausgeführt wird.
