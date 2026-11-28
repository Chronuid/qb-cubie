# RUN-2: Reaktivierung des 12-Zeilen-Limits (`BUG-006`) & SRP-Refactoring — Voll-autonomer TGD-Durchlauf

- **Modus:** Voll-autonomer TGD-Durchlauf (`PHASE_RED` $\to$ `PHASE_GREEN` $\to$ `LIVING_DOCS`, mit situativen Stützrädern `ANALYSIS` / `HYPOTHESIS` und optionaler Rückwärtstür `GREEN_AUDIT`)
- **Knoten-Handbücher:** [TGD-Baukasten (docs/tgd/README.md)](../../tgd/README.md) · [PHASE_RED](../../tgd/NODE_PHASE_RED.md) · [PHASE_GREEN](../../tgd/NODE_PHASE_GREEN.md) · [LIVING_DOCS](../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil:** [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
- **Ausgangs-Commit:** `42c37ded` (HEAD -> main, origin/main) Tried to repair the docs.
- **Ziel-Artefakte:** `tests/test_styleguide.py`, betroffene Module in `src/qb_cubie/`, `docs/dev/DEV-GUIDE_TGD-Workflow.md` (sowie `KNOWN_ISSUES.md` / angrenzende Doku bei Bedarf)
- **Herkunft:** `Mensch (Meow :3) + Gemini-App (Modell: Hydrogen, Reasoning-Effort: High)`

## 1. Ziel (Scope dieses Durchlaufs)
Reaktiviere das pausierte 12-Zeilen-Funktionslimit (`tests/test_styleguide.py::test_function_size`, `FUNCTION_LIMIT = 12` / `BUG-006`), bereite den betroffenen Quellcode in `src/qb_cubie/` nach einem durchdachten **Single Responsibility Principle (SRP)** auf und kürze anschließend in `LIVING_DOCS` die nun hinfällige Erklärung bzw. Sonderregelung zum pausierten 12-Zeilen-Gate aus [`DEV-GUIDE_TGD-Workflow.md`](../../dev/DEV-GUIDE_TGD-Workflow.md) heraus.

## 2. Kontext-Delta (seit letztem Knoten)
- Die TGD-Handbuchreihe (`docs/GUIDE_TGD.md`, `docs/tgd/README.md`, alle sechs `docs/tgd/NODE_*.md` sowie `docs/dev/DEV-GUIDE_TGD-Workflow.md`) wurde auf den modularen Rollen-Baukasten und das plattformunabhängige `RUN-*.md`-Format umgestellt.
- Bisher war `tests/test_styleguide.py::test_function_size` (`FUNCTION_LIMIT = 12` physische Body-Zeilen exkl. Docstring, Kommentare und Leerzeilen) wegen `BUG-006` per `@pytest.mark.skip` pausiert und wurde in `PHASE_GREEN` über einen manuellen `body_lines()`-Advisory-Einzeiler kompensiert (`DEV-GUIDE_TGD-Workflow.md`, §2 & `PM8`). Mit diesem Durchlauf wird das Gate wieder regulär scharfgeschaltet.

## 3. Freigabe, Leitlinien & Phasen-Fahrplan (`Consent-by-Exception`)
- **Basis:** `EMPFEHLUNGEN: ALLE` (sämtliche Invarianten, Schreibgrenzen und Gate-Regeln aus `docs/tgd/README.md`, `docs/tgd/NODE_*.md` und `docs/dev/DEV-GUIDE_TGD-Workflow.md` gelten verbindlich).
- **Verbindliche Qualitäts- und Phasen-Vorgaben:**
  1. **Pre-Flight & Bestandsvermessung (optionales Stützrad `ANALYSIS`):**
     - Pre-Flight-Triage (`git status --short && git log -n 1 --oneline`) gemäß 3-Klassen-Modell durchführen.
     - Alle Funktionen in `src/qb_cubie/` mit `len(body_lines(src, node)) > 12` exakt vermessen, nach Modulen gruppieren und auf fachliche Verantwortlichkeiten hin analysieren.
  2. **Phase 1 — `PHASE_RED` (nur `tests/`):**
     - In `tests/test_styleguide.py` den `@pytest.mark.skip` von `test_function_size` (`BUG-006`) entfernen (inkl. eventuell ungenutzter Imports bereinigen).
     - Zweistufiges Differenzsignal belegen: übrige Tests grün, `test_function_size` schlägt deterministisch auf den verbliebenen `> 12`-Zeilen-Funktionen rot (`FAILED`) an.
     - Statische Test-Hygiene (`ruff check` und `MYPYPATH=src mypy` auf `tests/test_styleguide.py`) prüfen und Test-Freeze setzen (`src/` = 0, `docs/` = 0).
  3. **Phase 2 — `PHASE_GREEN` (nur `src/`):**
     - Betroffene Module in `src/qb_cubie/` nach einem **durchdachten SRP-Design** neu schneiden (siehe [Style-Guide.md](../../dev/Style-Guide.md)):
       - **Kein mechanisches Zeilen-Zerhacken:** Keine künstlichen `helper_1`/`helper_2`-Splitter ohne eigene fachliche Aussage. Stattdessen klare Verantwortlichkeiten trennen (z. B. Validierung/Guards, Datenaufbereitung/Transformation, Kernlogik, Formatierung/I/O), sprechende Funktions- oder Hilfsobjekt-Namen wählen und Top-Down-Lesbarkeit bewahren.
       - Alle Styleguide- und Architektur-Gates einhalten: `FUNCTION_LIMIT = 12` physische Body-Zeilen, `MODULE_LIMIT = 777` Zeilen, einzeilige Docstrings, `STATE-GUARD`-Konventionen und azyklische Modulabhängigkeiten.
     - Vollständige Abnahme in `PHASE_GREEN`: funktionale Tests, `tests/test_styleguide.py` (inkl. aktivem `test_function_size`), `ruff`, `pylint`, `mypy --warn-unreachable` grün; beobachtender Doku-Check ohne Edits an `docs/` (`tests/**/*.py` = 0, `docs/` = 0).
     - Sollte wider Erwarten ein Widerspruch in einem eingefrorenen Test auftreten, greift die reguläre Rückwärtstür über `tests/GREEN_AUDIT.md` und [`NODE_GREEN_AUDIT.md`](../../tgd/NODE_GREEN_AUDIT.md).
  4. **Phase 3 — `LIVING_DOCS` (nur `docs/` & `KNOWN_ISSUES.md`):**
     - In [`DEV-GUIDE_TGD-Workflow.md`](../../dev/DEV-GUIDE_TGD-Workflow.md) die nun obsolete Erklärung und Workaround-Regelung zum pausierten 12-Zeilen-Gate herauskürzen (insbesondere Abschnitt 2 zum manuellen `body_lines()`-Advisory-Check für `BUG-006` sowie die Sonderhinweise auf das pausierte Gate in der Kommando-Matrix und in `PM8` auf das regulär aktive `tests/test_styleguide.py`-Gate umstellen).
     - Prüfen, ob weitere Dokumente (`KNOWN_ISSUES.md` für `BUG-006` oder `NODE_PHASE_GREEN.md`) auf die nun erledigte Pausierung verweisen, und konsistent nachziehen.
     - Doku-Gates verifizieren: `qb-cubie docframe update` (2× idempotent, 2. Lauf `Updated 0 file(s)`), `qb-cubie docframe check`, `qb-cubie docensurance check` und `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` grün (`src/` = 0, `tests/` = 0).

## 4. Relevante Referenzen
- **TGD-Regelwerk & Knoten-Handbücher:**
  - [TGD-Knoten-Übersicht (docs/tgd/README.md)](../../tgd/README.md)
  - [NODE_ANALYSIS.md](../../tgd/NODE_ANALYSIS.md)
  - [NODE_PHASE_RED.md](../../tgd/NODE_PHASE_RED.md)
  - [NODE_PHASE_GREEN.md](../../tgd/NODE_PHASE_GREEN.md)
  - [NODE_GREEN_AUDIT.md](../../tgd/NODE_GREEN_AUDIT.md)
  - [NODE_LIVING_DOCS.md](../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil & Styleguide:**
  - [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
  - [Style-Guide.md](../../dev/Style-Guide.md)
- **Betroffene Arbeits- & Referenzdateien:**
  - [tests/test_styleguide.py](../../../tests/test_styleguide.py)
  - [KNOWN_ISSUES.md](../../../KNOWN_ISSUES.md)