<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Neon" effort="High" -->
# Auftrag: Stärkung der CI-Matrix für Windows und macOS

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** High
- **Erstellungsdatum:** 20. November 2026, ~ 11:35 (CET)
- **Synthesebasis:** `.github/workflows/ci.yml`, `docs/CI_PLATFORM_STATUS.md`, `docs/GUIDE_Quality-Assurance.md`, `docs/dev/README.md`, `docs/dev/Style-Guide.md`, `scripts/check_wheel.py`, `scripts/provision_test_arenas.py`, `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/arenas/_relocation.py`, `src/qb_cubie/arenas/_process.py`, `src/qb_cubie/arenas/codecs.py`, `tests/tests_arena/TGD_1.md`, `KNOWN_ISSUES.md`
- **Stand:** qb-cubie (`v0.0.9`, Ausgangs-Commit `6a6f9ac6` + lokale TGD-1-Reparatur von `BUG-001`)
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

## Ausgangslage

Die GitHub-Actions-CI ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) sichert `qb-cubie` derzeit asymmetrisch über die drei Zielplattformen ab (siehe [`docs/CI_PLATFORM_STATUS.md`](../docs/CI_PLATFORM_STATUS.md)):

| Plattform | Aktueller CI-Umfang (`ci.yml`) | Bestehende Lücken / Risiken |
| :--- | :--- | :--- |
| **Linux** (`ubuntu-24.04`) | `wheel` + vollständige Repository-Testsuite (`pytest -m "" -q`, Python `3.13` & `3.14`) | Referenzplattform (Tier 1). |
| **macOS** (`macos-15`) | Nur `wheel` (`scripts/check_wheel.py dist`, Python `3.13` & `3.14`) | Keine Repository-Testsuite in der CI; macOS-Spezifika (`/var` $\to$ `/private/var`-Symlinks, POSIX-Prozessgruppen ohne `/proc`, lokale Arena-Provisionierung, Linter-/Service-Suite) sind nicht über `tests/` abgesichert. |
| **Windows** (`windows-2022`) | **Eingefroren** (aus `wheel` und `tests` ausgeklammert) | Weder Wheel- noch Repository-Checks laufen in der CI. Ursachen laut `CI_PLATFORM_STATUS.md`: native `.exe`-Launcher in `_relocation.py`, `PATH`/Subprozess-Isolation, POSIX-Prozessgruppen in `_process.py` sowie POSIX-Annahmen in einzelnen Tests. |

Im Rahmen von [`tests/tests_arena/TGD_1.md`](./tests_arena/TGD_1.md) (`BUG-001`) wurden erste Windows-freundliche Grundlagen in `PyVenv` und `codecs.py` bereits gelegt (getrennter `_root_path` bei unveränderter `.venv`-Tiefe, `shutil.copyfile`, `shutil.rmtree(..., onexc=_remove_readonly)`, `python -P`, `os.path.normcase(os.path.realpath(...))`, plattformneutrale `bin`/`Scripts`- und `lib`/`Lib`-Prüfungen).

---

## Ziele

1. **macOS in der CI-Matrix substanziell stärken:**
   - Prüfen und vorbereiten, wie `macos-15` über den reinen `wheel`-Smoke-Test hinaus in die Repository-Testsuite (`.github/workflows/ci.yml`) aufgenommen werden kann (inkl. Bewertung von Laufzeit, Arena-Provisionierung und Plattform-Markern/Skips wie `test_ebt_resource_limits.py`).
2. **Windows-CI (`windows-2022`) schrittweise reaktivierbar machen:**
   - Root-Cause-Analyse aller konkreten Blocker für `CI / Wheel / windows-2022` (`scripts/check_wheel.py`, `tests/wheel/*`, `src/qb_cubie/arenas/`) sowie für eine spätere Windows-Repository-Suite (`scripts/provision_test_arenas.py`, `tests/`).
   - Belastbare, wartbare Architekturentscheidungen für:
     - **Launcher & Relokation** (`src/qb_cubie/arenas/_relocation.py`, `tests/tests_arena/test_ebt_console_environment.py`),
     - **Subprozess-Umgebung, `PATH` & Encoding** (`scripts/check_wheel.py`, `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/arenas/_requirements.py`, `src/qb_cubie/linter.py`),
     - **Ressourcenlimits (`timeout` / `max_output_bytes`)** (`src/qb_cubie/arenas/_process.py`, `tests/tests_arena/test_process_limits.py`, `tests/tests_arena/test_ebt_resource_limits.py` — klare Abwägung zwischen sauberer Plattform-Abgrenzung vs. Win32-Unterstützung),
     - **POSIX-spezifische Altlasten in Tests & Skripten** (z. B. hartkodiertes `/tmp/host_compromised.txt` und `touch` in `tests/tests_arena/test_security_arena_codec.py`, `shutil.rmtree` ohne Read-Only-Handler in `scripts/provision_test_arenas.py`, Symlink-Annahmen, `\r\n`-Zeilenenden).
3. **Ehrliche, wartbare Plattform-Garantien & lebende Dokumentation:**
   - Keine fragilen Workarounds, kein stilles Stummschalten von Fehlern (`xfail`/Vacuous Passes) und strikte Einhaltung des Styleguides (`FUNCTION_LIMIT = 12`, `ruff`, `pylint`, `mypy`, `DocEnsurance`, `DocFrame`, Meta-Gates 1–3).
   - Synchronisation von `docs/CI_PLATFORM_STATUS.md`, `docs/core/GUIDE_Arena-Management.md`, `KNOWN_ISSUES.md` und `CHANGELOG.md`.

---

## Relevante Dokumente & Einstiegspunkte

@.github/workflows/ci.yml
@docs/CI_PLATFORM_STATUS.md
@docs/GUIDE_Quality-Assurance.md
@docs/dev/README.md
@docs/dev/Style-Guide.md
@scripts/check_wheel.py
@scripts/provision_test_arenas.py
@tests/tests_arena/TGD_1.md

---

## Auftrag

Arbeite das Thema streng nach dem **5-stufigen TGD-Muster** ([`docs/GUIDE_Quality-Assurance.md` § 3](../docs/GUIDE_Quality-Assurance.md#3-test-guided-development-tgd-in-f%C3%BCnf-schritten)) strukturiert ab:

1. **Schritt 1 — Systematische Bestandsaufnahme & Analyse (zunächst rein lesend, keine Änderungen an `src/`, `tests/**/*.py`, `docs/` oder `.github/`):**
   - Prüfe `src/qb_cubie/`, `scripts/`, `tests/` (inkl. `tests/wheel/`) und `.github/workflows/ci.yml` systematisch auf konkrete Windows- und macOS-Inkompatibilitäten, `skipif`-Lücken, Pfad-/Symlink-/Encoding-Fallen sowie mögliche Laufzeit- oder Stabilitätsrisiken in GitHub Actions.
   - Dokumentiere sämtliche Befunde, Prioritäten (z. B. *Stufe 1: macOS-Repository-CI & Windows-Wheel-Reaktivierung*, *Stufe 2: Windows-Repository-Suite*), konkrete Architekturentscheidungen und eine scharfe Red-Phase-Testmatrix unter `tests/ANALYSIS_CI_MATRIX.md` mit gültigem `CUBIE_DOC_FRAME_2`-Provenance-Header.
2. **Schritte 2–5 — Orchestrierte Umsetzung nach dem TGD-Muster (nach Abstimmung der in der Analyse offenen Entscheidungspunkte):**
   - **Red-Phase & Test-Freeze:** Plattform- und Regressionsverträge gezielt unter `tests/` schärfen (inkl. Meta-Gates 1–3), kontrolliert rot nachweisen und einfrieren.
   - **Green-Phase:** Notwendige Anpassungen in `src/`, `scripts/` und `.github/workflows/ci.yml` sauber innerhalb der Styleguide-Grenzen umsetzen und vollständig verifizieren (`pytest -m "" -q`, `test_styleguide.py`, `test_lint.py`, `tests_meta/`).
   - **Living-Documentation-Sync & Protokoll:** Betroffene Handbücher (`docs/CI_PLATFORM_STATUS.md`, Arena-/Dev-Guides, `KNOWN_ISSUES.md`, `CHANGELOG.md`) synchronisieren und den gesamten Durchlauf als TGD-Protokoll mit `CUBIE_DOC_FRAME_2`-Header dokumentieren.
