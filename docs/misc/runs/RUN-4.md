# RUN-4: Living-Docs-Review, `KNOWN_ISSUES` & `CHANGELOG` für Release `v0.1.3` — Voll-autonomer TGD-Durchlauf

- **Modus:** Voll-autonomer TGD-Durchlauf (`ANALYSIS` $\to$ `LIVING_DOCS`)
- **Knoten-Handbücher:** [TGD-Baukasten (docs/tgd/README.md)](../../tgd/README.md) · [ANALYSIS](../../tgd/NODE_ANALYSIS.md) · [LIVING_DOCS](../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil:** [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
- **Run / Zyklus:** `release-0-1-3-docs` *(Ablage: `docs/misc/runs/release-0-1-3-docs/RUN-4.md`)*
- **Ausgangs-Commit:** `8ff3d79e` (HEAD -> main) Tried docframe-rules-srp with a fully autonomous TGD-run
- **Ziel-Artefakte:** `docs/**/*.md`, `README.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md` *(ausnahmefrei `0` Änderungen an `src/` und `tests/`)*
- **Herkunft:** `Mensch (<3) + Gemini-App (Hydrogen, High)`

## 1. Ziel (Scope dieses Durchlaufs)
Führe einen ganzheitlichen `LIVING_DOCS`-Durchlauf zur Vorbereitung des Versionssprungs auf **`v0.1.3`** durch:
1. Prüfe und optimiere alle bestehenden Dokumentationsdateien (`README.md` und `docs/**/*.md`) im Hinblick auf Klarheit, Konsistenz, Einsteiger-/Experten-Zugänglichkeit und Übereinstimmung mit dem realen Quellcode (*Code as Source of Truth*).
2. Dokumentiere zwei neu identifizierte Bugs sauber in `KNOWN_ISSUES.md` (ohne sie in diesem Run im Quellcode oder in Workflows umzusetzen).
3. Aktualisiere `CHANGELOG.md` vollständig und strukturiert für die anstehende Version **`0.1.3`**, sodass der Repository-Stand sauber für den Release-Versionssprung vorbereitet ist.

## 2. Kontext-Delta (seit letztem Knoten)
- In `RUN-2` (`348b8ed0`) wurde das 12-Zeilen-Funktionslimit (`tests/test_styleguide.py::test_function_size`, `BUG-006`) reaktiviert und der Quellcode in `src/qb_cubie/` nach SRP neu geschnitten.
- In `RUN-3` wurden atomare SRP-Regel-Interfaces (`DocFrameFootLinks`, `FrameRuleProfile`, `DocFrameRuleSet`, `CUBIE_DOCFRAME_RULE_SET` sowie `DocRuleSet` in `DocEnsurance`) implementiert, die `foot`-Link-Prüfung für `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` auf `warning` abgeschwächt und die TGD-Handbuchreihe (`GUIDE_TGD.md`, `docs/tgd/*`, `DEV-GUIDE_TGD-Workflow.md`) auf den modularen Baukasten und plattformunabhängige `RUN-*.md`-Dokumente umgestellt.
- Im Test-Verzeichnis liegt noch das abgeschlossene Audit-Protokoll `tests/GREEN_AUDIT.md` (`Status: RESOLVED` aus `RUN-3`). Gemäß der *Single-Active-Signal-Invariante* (`E5a`) darf `NODE_LIVING_DOCS` `tests/` **nicht** berühren, muss die fällige Archivierung nach `docs/misc/lake/` aber im Abschlussbericht als nachgelagerte 1-Schritt-Hygiene für die Orchestrierung ausweisen.

## 3. Freigabe, Leitlinien & Phasen-Fahrplan (`Consent-by-Exception`)
- **Basis:** `EMPFEHLUNGEN: ALLE` (sämtliche Invarianten, Schreibgrenzen und Gate-Regeln aus `docs/tgd/README.md`, `docs/tgd/NODE_ANALYSIS.md`, `docs/tgd/NODE_LIVING_DOCS.md`, `docs/dev/DEV-GUIDE_TGD-Workflow.md`, `docs/dev/DEV-GUIDE_Write-down-the-bugs.md` und `docs/dev/DEV-GUIDE_Release-Preparation.md` gelten verbindlich).
- **Verbindliche Leitplanken & Arbeitsschritte:**
  1. **Strikte Schreibgrenze (`src/` = 0, `tests/` = 0):**
     - Dieser Durchlauf ist ein reiner Dokumentations-, Bug-Tracking- und Release-Vorbereitungs-Run. Es werden **keine** Dateien unter `src/` oder `tests/` (inkl. `pyproject.toml` oder `.github/workflows/`) geändert.
  2. **Schritt 1 — `ANALYSIS` (kurze Drift- & Bestandsinventur, nur Analysebericht im Run-Ordner):**
     - Prüfe `git log` seit dem letzten Release (`v0.1.2`), `CHANGELOG.md`, `KNOWN_ISSUES.md`, `README.md` sowie die Guides unter `docs/` (Einstiegs-Guides, `core/`, `services/`, `dev/`, `tgd/`, `misc/`) auf veraltete Signaturen, unvollständige Querverweise, sprachliche Holprigkeiten oder fehlende Dokumentation der Änderungen aus `RUN-1` bis `RUN-3`.
  3. **Schritt 2 — `LIVING_DOCS`: Zwei neue Bugs in `KNOWN_ISSUES.md` festhalten:**
     - Dokumentiere beide Bugs im etablierten Format von `KNOWN_ISSUES.md` (siehe [DEV-GUIDE_Write-down-the-bugs.md](../../../dev/DEV-GUIDE_Write-down-the-bugs.md)) mit fortlaufenden Bug-IDs:
       - **Bug A — `DocFrame` `foot`-Zone-Kopplung, `update()`-Überschreibung & 1-Tupel-Regelübergabe:**
         1. `DocFrameOutdated` (`src/qb_cubie/core/services/doc_frame/doc_frame_rules.py`) erfordert aktuell zwingend `allow_empty_foot=True`, sobald `DocFrameFootLinks(severity="warning")` genutzt wird; zudem unterdrückt `_should_skip_span` `DOCFRAME-OUTDATED` nur bei komplett linkfreien `foot`-Zonen (`not _has_markdown_links(...)`), sodass eigene kuratierte Markdown-Links in `zone="foot"` (oder ein `DocFrame.update()`-Lauf gegen `STD_FOOTER_BLOCKS`) bei `CUBIE_DOC_FRAME_2` / `CUBIE_DOC_FRAME_3` weiterhin einen `DOCFRAME-OUTDATED`-Error auslösen und `DocFrameMissing` das Vorhandensein der `foot`-Tags weiterhin hart als `error` verlangt.
         2. `DocFrame.check()` und `DocEnsurance` akzeptieren `DocFrameRuleSet` bzw. `DocRuleSet` derzeit nur verpackt als 1-Tupel (`rules=(REPO_DOCFRAME_RULES,)` / `rules=(REPO_DOC_RULES,)`) statt direkt als Einzelinstanz.
       - **Bug B — GitHub Actions CI-Matrix läuft bei reinen Dokumentations-Änderungen vollständig durch:**
         - Bei Pushes/PRs, die ausschließlich Dokumentationsdateien (`docs/**`, `*.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md`) betreffen, wird aktuell die komplette CI-Test-Matrix über alle 6 Umgebungen ausgelöst, statt reine Doku-Updates auf einen schlanken Doku-Gate-Lauf (`docframe`, `docensurance`, `test_doc_frame.py`, `test_doc_ensurance.py`) zu begrenzen.
  4. **Schritt 3 — `LIVING_DOCS`: Alle Docs durchgehen & optimieren (`Code as Source of Truth`):**
     - Verifiziere alle Guides unter `docs/` und `README.md` gegen den realen Stand in `src/qb_cubie/` und `tests/` (insbesondere `README.md`, `docs/README.md`, `docs/GUIDE_*.md`, `docs/core/*`, `docs/services/*`, `docs/dev/*`, `docs/tgd/*`).
     - Schärfe unklare Formulierungen, stelle sicher, dass zentrale Guides sowohl für Einsteiger als auch für Experten klar aufgebaut sind, und halte die Sprache durchgängig werkzeug- und plattformneutral (Standard-Markdown-Links).
  5. **Schritt 4 — `LIVING_DOCS`: `CHANGELOG.md` für `v0.1.3` vorbereiten:**
     - Ergänze in `CHANGELOG.md` (orientiert an [DEV-GUIDE_Release-Preparation.md](../../../dev/DEV-GUIDE_Release-Preparation.md)) einen vollständigen, übersichtlichen Abschnitt für **`[0.1.3]`** (mit `Added`, `Changed`, `Fixed`, `Documentation`), der sämtliche Neuerungen seit `0.1.2` abdeckt (u. a. SRP-Regel-Interfaces `FrameRuleProfile` / `DocFrameRuleSet` / `DocRuleSet`, konfigurierbare `DocFrameFootLinks`-Warnstufe für `CUBIE_DOC_FRAME_2`/`3`, Reaktivierung des 12-Zeilen-Limits `BUG-006` inkl. SRP-Code-Aufbereitung, TGD-Knoten-Handbücher `docs/tgd/` & plattformunabhängige `RUN-*.md`-Workflows).
  6. **Schritt 5 — Abnahme & Abschluss-Hygiene-Hinweis:**
     - Führe `qb-cubie docframe update` über alle relevanten `docs/`-Ordner idempotent aus (2×; 2. Lauf: `Updated 0 file(s)`).
     - Verifiziere `qb-cubie docframe check` und `qb-cubie docensurance check` (`--format text`) sowie `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` (`0` Fehler).
     - Belege per `git status -s` die strikte Schreibgrenze (`src/` = 0, `tests/` = 0) und weise im Abschlussbericht explizit auf die nachgelagerte Abschluss-Hygiene hin (Archivierung von `tests/GREEN_AUDIT.md` nach `docs/misc/lake/` sowie Bereinigung/Archivierung der abgeschlossenen Lauf-Ordner unter `docs/misc/runs/`).

## 4. Relevante Referenzen
- **TGD-Regelwerk & Knoten-Handbücher:**
  - [TGD-Knoten-Übersicht (docs/tgd/README.md)](../../../tgd/README.md)
  - [NODE_ANALYSIS.md](../../../tgd/NODE_ANALYSIS.md)
  - [NODE_LIVING_DOCS.md](../../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil, Bug- & Release-Guides:**
  - [DEV-GUIDE_TGD-Workflow.md](../../../dev/DEV-GUIDE_TGD-Workflow.md)
  - [DEV-GUIDE_Write-down-the-bugs.md](../../../dev/DEV-GUIDE_Write-down-the-bugs.md)
  - [DEV-GUIDE_Release-Preparation.md](../../../dev/DEV-GUIDE_Release-Preparation.md)
  - [DEV-GUIDE_DocFrame-Conventions.md](../../../dev/DEV-GUIDE_DocFrame-Conventions.md)
  - [DEV-GUIDE_Agent-Reports.md](../../../dev/DEV-GUIDE_Agent-Reports.md)
- **Release- & Dokumentations-Ziele:**
  - [README.md](../../../../README.md)
  - [CHANGELOG.md](../../../../CHANGELOG.md)
  - [KNOWN_ISSUES.md](../../../../KNOWN_ISSUES.md)
  - [docs/README.md](../../../README.md)