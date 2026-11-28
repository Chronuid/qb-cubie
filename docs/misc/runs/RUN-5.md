# RUN-5: Release-Vorbereitung `v0.1.3` (Hygiene, Version-Bump, Vollprüfung & Wheel-Check) — Voll-autonomer Durchlauf

- **Modus:** Voll-autonomer Release-Vorbereitungs-Durchlauf gemäß [DEV-GUIDE_Release-Preparation.md](../../dev/DEV-GUIDE_Release-Preparation.md) & [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
- **Knoten-Handbücher:** [TGD-Baukasten (docs/tgd/README.md)](../../tgd/README.md) · [NODE_LIVING_DOCS.md](../../tgd/NODE_LIVING_DOCS.md)
- **Projekt- & Release-Guides:** [DEV-GUIDE_Release-Preparation.md](../../dev/DEV-GUIDE_Release-Preparation.md) · [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
- **Run / Zyklus:** `release-0-1-3-prep` *(Ablage: `docs/misc/runs/release-0-1-3-docs/RUN-5.md`)*
- **Ausgangs-Commit (`HEAD`):** `<kurzer-hash>` *("<Commit-Message aus RUN-4>")*
- **Ziel-Artefakte:** `pyproject.toml`, `uv.lock`, aktive Versions-/Wheel-Referenzen (`README.md`, `docs/core/GUIDE_Contract-Semantics.md`, `experiments/`), `CHANGELOG.md`, Abschluss-Hygiene (`docs/misc/lake/`, `docs/misc/runs/`) sowie lokaler Build-Nachweis in `dist/`
- **Herkunft:** `Mensch + Gemini-App`

## 1. Ziel (Scope dieses Durchlaufs)
Bereite das Repository vollständig und reproduzierbar für den Release **`v0.1.3`** vor:
1. Führe die nachgelagerte TGD-Abschluss-Hygiene (`tests/GREEN_AUDIT.md` und abgeschlossene Lauf-Artefakte unter `docs/misc/runs/`) durch.
2. Hebe die Paketversion in `pyproject.toml` sowie `uv.lock` und alle aktiven Versions-/Wheel-Referenzen im Repository auf **`0.1.3`** an.
3. Verifiziere die vollständige Testsuite (`make test-all` inkl. `slow`-Tests, Styleguide, Lintern und Doku-Gates) sowie das gebaute Wheel (`uv build` + `scripts/check_wheel.py dist`) lokal und halte den Stand bereit für den finalen Release-Commit, Tag (`v0.1.3`) und Push durch den Nutzer.

## 2. Kontext-Delta (seit letztem Knoten)
- In `RUN-4` wurden alle Dokumentations-Drift-Stellen synchronisiert, `BUG-008` und `BUG-009` in `KNOWN_ISSUES.md` dokumentiert, `BUG-005` und `BUG-006` nach `docs/misc/lake/SOLVED_ISSUES.md` archiviert und der Abschnitt `## [0.1.3] - 2026-11-28` in `CHANGELOG.md` ergänzt.
- `pyproject.toml` steht aktuell noch auf `version = "0.1.2"`, im Test-Verzeichnis liegt noch das abgeschlossene Audit-Protokoll `tests/GREEN_AUDIT.md` (`Status: RESOLVED` aus `RUN-3`), und im Lauf-Bereich `docs/misc/runs/` liegen die abgeschlossenen Arbeitsartefakte aus `RUN-1` bis `RUN-4`.

## 3. Freigabe, Leitlinien & Phasen-Fahrplan (`Consent-by-Exception`)
- **Basis:** `EMPFEHLUNGEN: ALLE` (alle Regeln aus [DEV-GUIDE_Release-Preparation.md](../../../dev/DEV-GUIDE_Release-Preparation.md) und [DEV-GUIDE_TGD-Workflow.md](../../../dev/DEV-GUIDE_TGD-Workflow.md) gelten verbindlich).
- **Verbindlicher Ablauf (5 Schritte):**
  1. **Schritt 1 — Pre-Flight & Branch-Abgleich (Release-Phase 1):**
     - Prüfe `git status --short`, `git branch -vv`, `git log -n 5 --oneline` und `git ls-remote --tags origin`.
     - Stelle sicher, dass `main` der aktive Branch ist, keine unklaren Merge-Konflikte bestehen und keine lokalen Alt-Tags dem Remote widersprechen.
  2. **Schritt 2 — Nachgelagerte TGD-Abschluss-Hygiene (`E5a`):**
     - Verschiebe das abgeschlossene Audit-Protokoll `tests/GREEN_AUDIT.md` (`Status: RESOLVED` aus `RUN-3`) nach `docs/misc/lake/GREEN_AUDIT_DOCFRAME-RULES-SRP.md`, sodass `tests/` vor dem Release-Commit sauber ist.
     - Bereinige bzw. archiviere abgeschlossene Lauf-Artefakte unter `docs/misc/runs/` (`RUN-1.md` bis `RUN-4.md`, `docframe-rules-srp/`, `release-0-1-3-docs/`) gemäß dem 3-Zustands-Lebenszyklus (`DEV-GUIDE_TGD-Workflow.md`, §3): erhaltenswerte Analyse-/Hypothesenberichte nach `docs/misc/lake/` überführen, temporäre `RUN-*.md`-Steuerdateien entfernen (Git bewahrt die Historie).
  3. **Schritt 3 — Versions-Sprung auf `0.1.3` & aktive Referenzen aktualisieren (Release-Phase 2):**
     - Setze in `pyproject.toml` unter `[project]` den Wert `version = "0.1.3"`.
     - Synchronisiere Lockfile und `.venv`-Metadaten mit `uv lock` und `uv sync --locked --group dev`.
     - Suche alle Vorkommen von `0.1.2` per `git grep -n "0\.1\.2"` und aktualisiere **ausschließlich die aktiven Referenzen** auf `0.1.3`:
       - `README.md` (Wheel-Installationsbeispiel `dist/qb_cubie-0.1.3-py3-none-any.whl[...]`),
       - `docs/core/GUIDE_Contract-Semantics.md` (aktuelle Implementierungsversion `Cubie 0.1.3`),
       - `experiments/benchmarks/cubie_benchmarks/data/GUIDE_Ollama-Agents.md` (Wheel-Pfad),
       - `experiments/ollama-agents/README.md` (Wheel-Pfad),
       - `experiments/ollama-agents/swebench/Dockerfile` (`ARG CUBIE_WHEEL=dist/qb_cubie-0.1.3-py3-none-any.whl`).
     - **Unangetastet lassen:** Historische Abschnitte in `CHANGELOG.md`, `DEV-GUIDE_Next-Steps.md`, `GUTACHTEN.md`, `KNOWN_ISSUES.md` (Fundstellen-Metadaten) sowie eingefrorene Studienartefakte.
     - Prüfe `CHANGELOG.md` (`## [0.1.3] - 2026-11-28` passend zum Regex `^## \[0\.1\.3\](?:\s|\$)` in `.github/workflows/release.yml`) und führe `qb-cubie docframe update` (idempotent, 2×) sowie `docframe check` und `docensurance check` aus.
  4. **Schritt 4 — Lokale Vollprüfung & isolierter Wheel-Check (Release-Phase 3):**
     - Provisioniere die Test-Arenen (`.venv/bin/python scripts/provision_test_arenas.py`) und führe die komplette Testsuite über `make test-all` (`.venv/bin/python -m pytest -m "" --hypothesis-profile=ci -q`) aus — inkl. `slow`-Tests, `tests/test_styleguide.py`, `tests/test_doc_frame.py`, `tests/test_doc_ensurance.py` und `tests/test_lint.py`.
     - Entferne alte Build-Artefakte gezielt (`rm -f dist/qb_cubie-*.whl dist/qb_cubie-*.tar.gz`), baue sdist und Wheel (`uv build --python .venv/bin/python`) und prüfe das Wheel isoliert über `.venv/bin/python scripts/check_wheel.py dist`.
  5. **Schritt 5 — Kontrollierter Stopp vor Commit, Tag & Push (Human Sign-Off):**
     - Führe **kein** eigenmächtiges `git commit`, `git tag` oder `git push` aus, damit der finale Release-Commit und der atomare Push (`git push --atomic origin main v0.1.3`) bewusst vom Nutzer freigegeben bzw. ausgelöst werden können.
     - Erstelle eine kompakte Abschlussübersicht mit `git status -s`, `git diff --stat`, den Prüfergebnissen aus `make test-all` und `check_wheel.py dist` sowie den fertigen Befehlen für Release-Commit, Tag (`v0.1.3`) und Push.

## 4. Relevante Referenzen
- **Release- & Workflow-Leitfäden:**
  - [DEV-GUIDE_Release-Preparation.md](../../../dev/DEV-GUIDE_Release-Preparation.md)
  - [DEV-GUIDE_TGD-Workflow.md](../../../dev/DEV-GUIDE_TGD-Workflow.md)
  - [TGD-Knoten-Übersicht (docs/tgd/README.md)](../../../tgd/README.md)
  - [NODE_LIVING_DOCS.md](../../../tgd/NODE_LIVING_DOCS.md)
- **Betroffene Konfigurations-, Doku- & Prüfdateien:**
  - [pyproject.toml](../../../../pyproject.toml)
  - [CHANGELOG.md](../../../../CHANGELOG.md)
  - [KNOWN_ISSUES.md](../../../../KNOWN_ISSUES.md)
  - [README.md](../../../../README.md)
  - [docs/core/GUIDE_Contract-Semantics.md](../../../core/GUIDE_Contract-Semantics.md)
  - [scripts/provision_test_arenas.py](../../../../scripts/provision_test_arenas.py)
  - [scripts/check_wheel.py](../../../../scripts/check_wheel.py)
  - [.github/workflows/release.yml](../../../../.github/workflows/release.yml)