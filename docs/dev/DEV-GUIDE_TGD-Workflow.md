<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# DEV-GUIDE: TGD-Workflow-Profil für `qb-cubie`

![Cubie](../.assets/cubie-logo-written.png)

Technisches Projekt-Profil zur Anwendung der universellen TGD-Knoten-Handbücher (`docs/tgd/`) im `qb-cubie`-Repository: Knoten-Kommando-Matrix, Advisory-Check für pausierte Stil-Gates, 5-Block-Minimal-Ticket, 3-Zustands-Artefakt-Lebenszyklus und Prozess-Mutanten-Mapping (`PM1`–`PM8`).

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

Dieses Dokument ist die zentrale Single Source of Truth (SSOT) für sämtliche `qb-cubie`-spezifischen Pfade, CLI-Befehle, Gates und Ablagekonventionen im TGD-Prozess. Die universellen, projektunabhängigen Knoten-Verträge liegen in den [TGD-Knoten-Handbüchern (`docs/tgd/`)](../tgd/README.md); die epistemologische Einführung steht im [TGD-Handbuch](../GUIDE_TGD.md).

---

## 1. Knoten-Kommando-Matrix (`docs/tgd/` $\leftrightarrow$ `qb-cubie`)

**Pflicht-Pre-Flight vor jedem Knoten** (3-Klassen-Triage gemäß [`docs/tgd/README.md`](../tgd/README.md#41-pre-flight-triage-des-arbeitsverzeichnisses-3-klassen-modell)):

```bash
git status --short && git log -n 1 --oneline
```

| Knoten & Handbuch | Allowlist (`qb-cubie`) | Denylist (`0` Diff) | Verbindliche Abnahmekommandos ($Q$) |
| :--- | :--- | :--- | :--- |
| **`ANALYSIS`**<br/>[`NODE_ANALYSIS.md`](../tgd/NODE_ANALYSIS.md) | Designierter Bericht `ANALYSIS*.md` (`CUBIE_DOC_FRAME_2`) | `src/`, `tests/`, bestehende `docs/GUIDE_*.md` & `docs/dev/` | `qb-cubie docframe update <bericht>` (2×, 2. Lauf: `Updated 0 file(s)`), `qb-cubie docframe check <bericht> --format text`, `qb-cubie docensurance check <bericht> --format text`, `git status -s` |
| **`HYPOTHESIS`**<br/>[`NODE_HYPOTHESIS.md`](../tgd/NODE_HYPOTHESIS.md) | Designierter Bericht `HYPOTHESIS*.md` (`CUBIE_DOC_FRAME_2`) | `src/`, `tests/`, bestehende Produkt-Handbücher | Wie `ANALYSIS` auf `<bericht>` + vollständige `E1..En`-Entscheidungsmatrix bzw. Post-Red-Härtungsliste |
| **`PHASE_RED`**<br/>[`NODE_PHASE_RED.md`](../tgd/NODE_PHASE_RED.md) | Ausschließlich `tests/**/*.py` | `src/`, `docs/` | 1. Bestand grün: `.venv/bin/python -m pytest -q <bestand>`<br/>2. Neue Verträge deterministisch rot: `.venv/bin/python -m pytest -q <neue_tests>`<br/>3. Statische Test-Hygiene (F3): `.venv/bin/ruff check <geänderte_tests>` und `MYPYPATH=src .venv/bin/mypy <geänderte_tests>`<br/>4. Schreibgrenze: `git diff --name-only` (`src=0`, `docs=0`) |
| **`PHASE_GREEN`**<br/>[`NODE_PHASE_GREEN.md`](../tgd/NODE_PHASE_GREEN.md) | `src/**/*.py` (+ im Eskalationsfall exklusiv `tests/GREEN_AUDIT.md`) | `tests/**/*.py`, `docs/**/*.md` *(Diagnose-statt-Edit-Regel!)* | 1. Funktionale Tests & Meta-Gates: `.venv/bin/python -m pytest -q --ignore=tests/test_doc_frame.py --ignore=tests/test_doc_ensurance.py`<br/>2. Statische Prüfer: `.venv/bin/ruff check src/`, `.venv/bin/pylint src/qb_cubie`, `MYPYPATH=src .venv/bin/mypy --warn-unreachable src/qb_cubie`<br/>3. Aktive Stil-Gates + Advisory (§2): `.venv/bin/python -m pytest -q tests/test_styleguide.py` + `body_lines()`-Check<br/>4. **Beobachtender Doku-Check** (*Diagnose-statt-Edit-Regel*): `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` *(Doku-Diagnosen nur als Handoff-Backlog protokollieren, `docs/` nicht anfassen!)*<br/>5. Schreibgrenze: `git diff --name-only` (`tests/**/*.py=0`, `docs=0`) |
| **`GREEN_AUDIT`**<br/>[`NODE_GREEN_AUDIT.md`](../tgd/NODE_GREEN_AUDIT.md) | Betroffene `tests/**/*.py` *(nur bei `CONFIRMED`)* + Abschluss-Sektion in `tests/GREEN_AUDIT.md` | `src/`, `docs/` *(bei `REFUTED`: auch `tests/**/*.py` = 0!)* | 1. `AUDIT-REPRO`: Betroffene Tests (+ ggf. Subprozess-Isolations-Probe mit `sys.meta_path`-Blocker) ohne Edits reproduzieren<br/>2. `AUDIT-FIX` *(nur bei `CONFIRMED`, 0 Assertion-Edits bevorzugen)*: `.venv/bin/python -m pytest -q <betroffene_tests>` (Zielsignal: `PASSED`) + `.venv/bin/ruff check <tests>` + `MYPYPATH=src .venv/bin/mypy <tests>`<br/>3. `AUDIT-CLOSE`: `Status: RESOLVED` ($\to$ `LIVING_DOCS`) oder `Status: REFUTED` ($\to$ `PHASE_GREEN`) in `tests/GREEN_AUDIT.md` + `git diff --name-only` (`src=0`, `docs=0`) |
| **`LIVING_DOCS`**<br/>[`NODE_LIVING_DOCS.md`](../tgd/NODE_LIVING_DOCS.md) | Ausschließlich `docs/**/*.md`, `README.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md` | **Ausnahmefrei** `src/` und `tests/` *(inkl. `tests/GREEN_AUDIT.md`, Beschluss E5a)* | 1. Sync je Zielpfad/Ordner (2×, 2. Lauf idempotent `Updated 0 file(s)`): `qb-cubie docframe update <pfad>`<br/>2. Gezielte Service-CLI-Checks: `qb-cubie docframe check <pfad> --format text` & `qb-cubie docensurance check <pfad> --format text`<br/>3. Vollständige Doku-Gates: `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py`<br/>4. Schreibgrenze: `git status -s` (`src=0`, `tests=0`) |

> [!NOTE]
> **CLI-Aufruf im lokalen `.venv`:** Falls `qb-cubie` nicht direkt im `PATH` liegt, entspricht `.venv/bin/python -m qb_cubie <subcommand>` exakt dem installierten `qb-cubie <subcommand>` (Exit-Codes: `0` = OK, `1` = Prüffehlschlag, `2` = `STATE-GUARD`/I/O-Fehler).

### `qb-cubie`-spezifische Fixture-Hygiene in `PHASE_RED` (Konkretisierung von F1–F3)

* **F1 (`DocFrame`-Preset-Parität):** Vor dem Bau neuer Workspace-Fixtures die Referenz-Fixture `_seed_synced_docframe_workspace` in `tests/tests_core/tests_service_core/test_rules_and_docframe.py` prüfen. Nutzt eine Fixture `CUBIE_DOC_FRAME_1`, rendert `HEADER_QUICK_NAV` statische Links auf `GUIDE_Quality-Assurance.md` und `GUIDE_DocEnsurance.md` — diese Zieldateien müssen im Test-Workspace existieren, oder es wird bewusst das selbstgenügsame Preset `CUBIE_DOC_FRAME_2` genutzt. Gegen Bestandscode (`DocFrame.update()` / `DocFrame.check()`) vor dem Freeze einmal trockenlaufen lassen.
* **F2 (SSOT-Konstanten-Import gegen `BUG-007`):** Normtexte, Exclude-Listen und Preset-IDs direkt importieren — z. B. `EPISTEMIC_NOTICE_TEXT` aus `qb_cubie.core.services.doc_frame.presets` oder `DOC_EXCLUDES` aus `tests.test_doc_ensurance` — statt mehrzeilige Prosa in Tests zu duplizieren.
* **F3 (Statische Test-Hygiene):** `.venv/bin/ruff check` und `MYPYPATH=src .venv/bin/mypy` zwingend vor dem Freeze-Commit auf allen neuen/geänderten Testdateien ausführen.

---

## 2. Advisory-Check für pausierte Stil-Gates (`E6`, aktuell `BUG-006`)

Das universelle Zwei-Stufen-Gate-Modell ist in [`docs/tgd/NODE_PHASE_GREEN.md`](../tgd/NODE_PHASE_GREEN.md#4-arbeits---meta-qa-heuristiken) verankert. Im `qb-cubie`-Repository ist aktuell **`tests/test_styleguide.py::test_function_size`** (`FUNCTION_LIMIT = 12` physische Body-Zeilen exkl. Docstring, Kommentare und Leerzeilen) wegen **`BUG-006`** (`KNOWN_ISSUES.md`) per `@pytest.mark.skip` pausiert, während `test_module_size` (`MODULE_LIMIT = 777`) und `test_docstrings` (einzeilige Docstrings) aktiv bleiben.

**Verbindlicher Advisory-Einzeiler in `PHASE_GREEN`** für alle in diesem Zyklus neu angelegten oder geänderten `src/`-Dateien (nutzt direkt `tests.test_styleguide.body_lines`):

```bash
.venv/bin/python -c '
import ast, pathlib, sys
from tests.test_styleguide import FUNCTION_LIMIT, FUNCTIONS, body_lines
bad = []
for raw in sys.argv[1:]:
    p = pathlib.Path(raw)
    src = p.read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(src, filename=str(p))):
        if isinstance(node, FUNCTIONS):
            n = len(body_lines(src, node))
            if n > FUNCTION_LIMIT:
                bad.append(f"{p}:{node.lineno} {node.name}: {n} > {FUNCTION_LIMIT}")
print("\n".join(bad) if bad else "OK: 0 violations")
' src/qb_cubie/<geänderte_datei_1.py> src/qb_cubie/<geänderte_datei_2.py>
```

* **Abnahme-Regel:** Ziel sind **`0` Überschreitungen** auf allen neuen/geänderten `src/`-Dateien. Jede bewusst in Kauf genommene Funktion mit $> 12$ Body-Zeilen muss im Abschlussbericht knapp fachlich begründet werden.
* **Automatische Ablösung:** Sobald `BUG-006` behoben und `test_function_size` wieder ohne `@pytest.mark.skip` aktiv ist, übernimmt das reguläre `pytest tests/test_styleguide.py`-Gate vollständig und dieser manuelle Advisory-Aufruf entfällt.

---

## 3. Kanonisches 5-Block-Minimal-Ticket (`GEMINI*.md`)

Da alle stabilen Prozessregeln in [`docs/tgd/NODE_*.md`](../tgd/README.md) und diesem Projekt-Profil liegen, enthält ein Arbeits-Ticket (`GEMINI-*.md`) ausschließlich das laufzeitspezifische Delta (~20–30 Netto-Zeilen) **ohne** wiederholten `## Auftrag`-Fußblock und im entkoppelten Lauf-Ordner `docs/misc/runs/` **ohne** 55-Zeilen-`DocFrame`-Boilerplate:

````markdown
# TGD-Ticket: <Thema> — <Zyklus> / <Knoten-ID>

- **Knoten-Handbuch:** @docs/tgd/NODE_<KNOTEN>.md
- **Projekt-Profil:** @docs/dev/DEV-GUIDE_TGD-Workflow.md
- **Run / Zyklus:** `<run-id>` (z. B. `service-core-z2`)
- **Ausgangs-Commit (`HEAD`):** `<kurzer-hash>` ("<Commit-Message>")
- **Ziel-Artefakt:** `<pfad/zum/ziel.md>` *(oder `tests/` / `src/` / `docs/` gemäß Knoten-Handbuch)*
- **Ticket-Herkunft:** *(optional, 1 Zeile, z. B. `Gemini-App (Gemini 4 Neon, High) + Nutzer-Anpassung`)*

## 1. Ziel (Scope dieses Schritts)
<1–2 präzise Sätze, die fachlich eindeutig zum gewählten Knoten passen.>

## 2. Kontext-Delta (seit letztem Knoten)
<Nur neue Fakten seit dem Vorgänger-Commit — keine wiederholte Projekt-Vorgeschichte.>

## 3. Verbindliche Beschlüsse (`E1..En`) & Ausnahmen
| ID | Entscheidung / Vorgabe | Status |
| :-: | :--- | :---: |
| **E1** | <Konkrete Wahl> | `BESTÄTIGT` |
| **E2** | <Konkrete Abweichung / Anpassung> | `GEÄNDERT` |

- **Bewusste Ausnahmen / Pausierte Gates:** *(optional, sonst `Keine`)*

## 4. Eingabe-Artefakte
@docs/tgd/NODE_<KNOTEN>.md
@docs/dev/DEV-GUIDE_TGD-Workflow.md
@<reale Vorgänger-Artefakte, z. B. ANALYSIS, HYPOTHESIS, GUIDE_*, tests/GREEN_AUDIT.md>
````

### Anti-Copy-Paste-Drift-Regeln
1. **Kein doppelter `## Auftrag`-Fußblock:** Die maßgebliche Knoten-ID samt `@docs/tgd/NODE_*.md` steht einmalig im Kopfbereich.
2. **Explizite Beschluss-Quittierung:** Offene Fragen (`E1..En`) aus `HYPOTHESIS` werden immer tabellarisch mit Status (`BESTÄTIGT` / `GEÄNDERT` / `ZURÜCKGESTELLT`) entschieden — niemals mit einem unkommentierten `Ok.`.
3. **Pre-Flight-Stopp bei Widerspruch:** Widerspricht `## 1. Ziel` dem angegebenen `Knoten-Handbuch` oder fehlt eine fällige `E1..En`-Entscheidung, stoppt der Agent vor der ersten Dateiänderung.

---

## 4. Ablage- & 3-Zustands-Artefakt-Lebenszyklus (`E2`, `E4`, `E5a`)

Die folgende Matrix bildet den universellen 3-Zustands-Lebenszyklus aus [`docs/tgd/README.md`](../tgd/README.md#43-allgemeiner-3-zustands-lebenszyklus-temporärer-artefakte) auf die konkreten Pfade und Gates von `qb-cubie` ab:

| Artefakt-Typ | Zustand 1: **Aktiv** (während des Laufs) | `DocFrame` / `DocEnsurance` | Zustand 2: **Nach Zyklus-Abschluss** | Konkrete `qb-cubie`-Hygiene-Regel |
| :--- | :--- | :--- | :--- | :--- |
| **`GEMINI-*.md`** *(Minimal-Tickets)* | **`docs/misc/runs/<run-id>/`** | Über `docs/misc/runs` in `tests/test_doc_ensurance.py::DOC_EXCLUDES` vollständig entkoppelt (gilt per SSOT-Import auch für `test_doc_frame.py`; kein 55-Zeilen-Frame nötig) | **Bereinigen** (löschen — Git bewahrt Historie) oder bei Studien nach `docs/misc/lake/<run-id>/` verschieben | Folge-Ticket `GEMINI-(n+1).md` niemals im Commit von Schritt `n` mitcommitten. |
| **`ANALYSIS*.md` & `HYPOTHESIS*.md`** | Im Lauf-Ordner `docs/misc/runs/<run-id>/` *(oder temporär im Zielordner `docs/<bereich>/`)* im **`CUBIE_DOC_FRAME_2`**-Format ([Leitfaden](./DEV-GUIDE_Agent-Reports.md)) | Immer explizite Einzelprüfung via `qb-cubie docframe check <pfad>` und `qb-cubie docensurance check <pfad>` (auch bei Ablage in `DOC_EXCLUDES`!) | **Archivwürdig** (Grundsatz-/Architekturwert) $\to$ verschieben nach **`docs/misc/lake/`** mit sprechendem Namen (z. B. `ANALYSIS_SERVICE-CORE.md`, `HYPOTHESIS_TGD-NODES.md`). **Reiner Bug-Sprint** $\to$ entfernen. | Keine dauerhafte Konkurrenz zu langlebigen `GUIDE_*.md`-Handbüchern in Produktordnern. |
| **`AGENT_REPORT*.md` & `TGD_*.md`** | Im Lauf-Ordner `docs/misc/runs/<run-id>/` (z. B. bei Single-Shot-TGD) | Entkoppelt (optional `CUBIE_DOC_FRAME_2`-Check) | Nach Verifikation und Übernahme relevanter Punkte in `KNOWN_ISSUES.md` / `GUIDE_*.md` **löschen** (oder bei Studien nach `docs/misc/lake/`) | Keine dauerhaften Einzelberichte im Repository-Root liegen lassen. |
| **`tests/GREEN_AUDIT.md`** | Exakt **`tests/GREEN_AUDIT.md`** (`tests` ist in `tests/test_doc_ensurance.py::DOC_EXCLUDES`) | Bewusst nicht von `DocFrame` geprüft (leichtgewichtiges Eskalationsprotokoll) | **Bei `Status: REFUTED`:** Muss als Pflicht-Eingabe für `NODE_PHASE_GREEN` bestehen bleiben (bei erneutem Audit datierten Abschnitt anhängen).<br/>**Bei `Status: RESOLVED` + grünem `NODE_LIVING_DOCS`:** Nach `docs/misc/lake/GREEN_AUDIT_<run-id>.md` archivieren (z. B. `GREEN_AUDIT_SERVICE-CORE-Z2.md`) oder entfernen. | **Single-Active-Signal-Invariante (`E5a`):** `tests/GREEN_AUDIT.md` existiert nur bei aktivem bzw. `REFUTED`-Audit; `NODE_LIVING_DOCS` behält die ausnahmefreie Schreibgrenze (`src=0`, `tests=0`) und meldet eine abgeschlossene Datei als nachgelagerte Abschluss-Hygiene. |

> [!NOTE]
> **Aktiver Betriebsstand der Beschlüsse (`E2`, `E4`, `E5a`):**
> * **`DOC_EXCLUDES` (`E4` — aktiv):** `docs/misc/runs` ist in `tests/test_doc_ensurance.py::DOC_EXCLUDES` eingetragen und wird über direkten SSOT-Import automatisch auch von `tests/test_doc_frame.py` übernommen. Rahmenfreie Minimal-Tickets liegen regulär unter [`docs/misc/runs/`](../misc/runs/README.md).
> * **`DocFrame`-Footer (`E2` — unverändert):** `src/qb_cubie/core/services/doc_frame/presets.py` (`CONTEXT_ROUTER`) bleibt unverändert; `docs/tgd/README.md` ist direkt über [`docs/GUIDE_TGD.md`](../GUIDE_TGD.md), [`docs/README.md`](../README.md) und [`docs/dev/README.md`](./README.md) verlinkt.
> * **`Single-Active-Signal`-Hygiene (`E5a` — aktiv):** Abgeschlossene `tests/GREEN_AUDIT.md`-Protokolle werden nach grünem `NODE_LIVING_DOCS` nach `docs/misc/lake/GREEN_AUDIT_<run-id>.md` archiviert (historischer Erstbeleg: [`GREEN_AUDIT_SERVICE-CORE-Z2.md`](../misc/lake/GREEN_AUDIT_SERVICE-CORE-Z2.md)).

---

## 5. Prozess-Mutanten-Referenz (`PM1`–`PM8`)

Alle acht in der TGD-Analyse identifizierten Prozess-Mutanten sind in `qb-cubie` exakt einem Knoten-Handbuch und einem deterministischen Prüf-Gate zugeordnet:

| ID | Prozess-Mutant (Fehlverhalten) | Abfangendes Handbuch | Konkretes `qb-cubie`-Prüf-Gate |
| :-: | :--- | :--- | :--- |
| **PM1** | **Stilles Test-Hacking in `PHASE_GREEN`** (Assertion schwächen oder `@pytest.mark.skip`) | [`NODE_PHASE_GREEN.md`](../tgd/NODE_PHASE_GREEN.md) | `git diff --name-only` weist **`0` Dateien** unter `tests/**/*.py` aus (einzige erlaubte Datei unter `tests/`: `tests/GREEN_AUDIT.md`). |
| **PM2** | **Blindes Abnicken eines `GREEN_AUDIT`** (*Confirmation Bias*, unnötige Assertion-Edits) | [`NODE_GREEN_AUDIT.md`](../tgd/NODE_GREEN_AUDIT.md) | Frischer `/clear`-Kontext + eigenständige `AUDIT-REPRO`-Reproduktion (inkl. Subprozess-`sys.meta_path`-Probe bei Isolationstests) + Minimal-Invasivität (`0` Assertion-Edits bevorzugen) + explizites Urteil `RESOLVED`/`REFUTED` in `tests/GREEN_AUDIT.md`. |
| **PM3** | **`docs/`-Schreibbruch in `PHASE_GREEN`** (Repo-weiter `docframe update`-Massendiff in Green) | [`NODE_PHASE_GREEN.md`](../tgd/NODE_PHASE_GREEN.md) | Verbindliche Diagnose-statt-Edit-Regel: `tests/test_doc_frame.py` & `tests/test_doc_ensurance.py` nur diagnostisch ausführen; `git diff --name-only` zeigt **`0` Dateien** unter `docs/`; Doku-Diagnosen nur als Handoff-Liste. |
| **PM4** | **Übernahme veralteter `HYPOTHESIS`-Signaturen in `LIVING_DOCS`** (Plan-vs.-Code-Drift) | [`NODE_LIVING_DOCS.md`](../tgd/NODE_LIVING_DOCS.md) | `Code-as-Source-of-Truth`-Abgleich gegen `src/` + reales Ausführen aller Doku-Beispiele über `qb-cubie docensurance check` / `pytest tests/test_doc_ensurance.py`. |
| **PM5** | **Unbemerkte Working-Tree-Altlast & Pre-Draft-Vermischung** (fremde Edits oder `GEMINI-(n+1)` im Commit) | [`docs/tgd/README.md`](../tgd/README.md) & alle `NODE_*.md` | Pflicht-Pre-Flight `git status --short` mit 3-Klassen-Triage (Hard-Stop bei Klasse 3; Klasse-2-Folge-Tickets strikt unstaged) + Abschluss-Check `git status -s`. |
| **PM6** | **Unterdeckte synthetische Fixture & Prosa-Duplikat in `PHASE_RED`** (`CUBIE_DOC_FRAME_1`-Falle, `BUG-007`) | [`NODE_PHASE_RED.md`](../tgd/NODE_PHASE_RED.md) | Fixture-Hygiene **F1** (Referenz-Fixture + Preset-Dry-Run vor Freeze), **F2** (SSOT-Import `EPISTEMIC_NOTICE_TEXT`/`DOC_EXCLUDES`) und **F3** (`ruff` + `MYPYPATH=src mypy` vor Freeze). |
| **PM7** | **Copy-Paste-Ziel-Drift & informelle Freigabe (`Ok.`) im Ticket** | [`docs/tgd/README.md`](../tgd/README.md) & alle `NODE_*.md` | 5-Block-Minimal-Ticket ohne doppelten `Auftrag`-Fußblock, explizite `E1..En`-Bestätigungstabelle und Pre-Flight-Konsistenzcheck `Knoten-Handbuch` $\leftrightarrow$ `## 1. Ziel`. |
| **PM8** | **Stille Stil-Drift bei pausierten Gates** (`test_function_size` / `BUG-006`) | [`NODE_PHASE_GREEN.md`](../tgd/NODE_PHASE_GREEN.md) | Zwei-Stufen-Gate-Modell: verbindlicher `body_lines()`-Advisory-Einzeiler (§2) auf allen neuen/geänderten `src/`-Dateien mit Refactoring- oder Begründungspflicht. |

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | Service-Core | ↤](../services/GUIDE_Service-Core.md)  
[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Core-Internals | ↤](./core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

[↦ | DEV-GUIDE: Berichte, Analysen & Audits (`CUBIE_DOC_FRAME_2`) | ↤](./DEV-GUIDE_Agent-Reports.md)  
[↦ | DEV-GUIDE: `CUBIE_DOC_FRAME_*`-Konventionen für Agenten | ↤](./DEV-GUIDE_DocFrame-Conventions.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | DEV-GUIDE: Service-Architektur & strikte Service-Isolation | ↤](./DEV-GUIDE_Services.md)  
[↦ | DEV-GUIDE: TGD-Workflow-Profil für `qb-cubie` | ↤](./DEV-GUIDE_TGD-Workflow.md)  
[↦ | DEV-GUIDE: Bugs dokumentieren (`KNOWN_ISSUES.md`) | ↤](./DEV-GUIDE_Write-down-the-bugs.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
