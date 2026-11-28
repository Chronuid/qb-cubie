# RUN-1: Universelle & domänenneutrale TGD-Knoten-Handbücher — `NODE_LIVING_DOCS`

- **Knoten-Handbuch:** [NODE_LIVING_DOCS.md](../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil:** [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
- **Run / Zyklus:** `tgd-universal-nodes` *(Ablage: `docs/misc/runs/RUN-1.md`)*
- **Ausgangs-Commit (`HEAD -> main`):** `3329843b` (Prepared the distribution of the cleaned TGD-Guides towards all 'NODE*.md' docs.)
- **Ziel-Artefakte:** Alle sechs Knoten-Handbücher in `docs/tgd/NODE_*.md` (inkl. idempotentem Router-Sync in `docs/tgd/README.md`)
- **Herkunft:** `Mensch (Huch? Das bin ja ich!) + Gemini-App (Huch? Das war Neon, Reasoning-Effort: High)`

## 1. Ziel (Scope dieses Schritts)
Überarbeite alle sechs TGD-Knoten-Handbücher (`NODE_ANALYSIS.md`, `NODE_HYPOTHESIS.md`, `NODE_PHASE_RED.md`, `NODE_PHASE_GREEN.md`, `NODE_GREEN_AUDIT.md` und `NODE_LIVING_DOCS.md`) auf Basis der aktualisierten Leitdokumente `docs/GUIDE_TGD.md`, `docs/tgd/README.md` und `docs/dev/DEV-GUIDE_TGD-Workflow.md`, sodass sie universell, domänenneutral, plattformunabhängig sowie gleichermaßen für Einsteiger und Experten verständlich formuliert sind. Quellcode (`src/`) und Test-Suite (`tests/`) bleiben vollständig unberührt (`0` Diff).

## 2. Kontext-Delta (seit letztem Knoten)
`docs/GUIDE_TGD.md`, `docs/tgd/README.md` und `docs/dev/DEV-GUIDE_TGD-Workflow.md` wurden bereits auf das neue, symmetrische und modulare TGD-Verständnis (flexibler Rollen-Baukasten, überall zuschaltbare Stützräder, durchgehende Berichts-/Doku-Schiene, plattformunabhängige `RUN`-Dokumente und *Consent-by-Exception*) aktualisiert. Die sechs einzelnen `NODE_*.md`-Handbücher spiegeln diese Anpassungen noch nicht wider und wirken im Vergleich zu `GUIDE_TGD.md` derzeit noch zu technisch und zu stark auf Software-Entwicklung bzw. `qb-cubie`-Spezifika zugeschnitten.

## 3. Verbindliche Leitlinien & Beschlüsse
- **Basis:** Alle Vorgaben aus `docs/GUIDE_TGD.md`, `docs/tgd/README.md` und `docs/dev/DEV-GUIDE_TGD-Workflow.md` gelten verbindlich.
- **Konkrete Anforderungen an alle sechs `NODE_*.md`-Dokumente:**
  1. **Universell & domänenneutral (über Software hinaus):** Formuliere Rollen, Heuristiken, Kantenfälle und Abnahmekriterien so allgemein, dass sie projektübergreifend auch außerhalb der Software-Entwicklung funktionieren (z. B. *Prüfkriterien/Checkliste* statt nur *Test-Suite*, *Umsetzung/Arbeitsergebnis* statt nur *Quellcode*, *Qualitäts-Prüfungen/Gates* statt nur *Linter/Typprüfer*). Wo konkrete Software-Begriffe zur Veranschaulichung helfen, kennzeichne sie klar als Beispiel — sämtliche `qb-cubie`-spezifischen Pfade, Befehle und Tool-Namen bleiben sauber im verlinkten `DEV-GUIDE_TGD-Workflow.md` gekapselt.
  2. **Modularer Baukasten statt starrer Zustandsautomat:** Stelle klar, dass kein starr verdrahteter Ablauf erzwungen wird. `ANALYSIS` und `HYPOTHESIS` sind optionale Bausteine, die situativ **in jedem Knoten** zugeschaltet werden können (nicht nur als feste Vorstufe vor `PHASE_RED`). `GREEN_AUDIT` ist eine optionale Rückwärtstür, die im Idealfall nicht gebraucht wird. Bilde zudem die symmetrische Rolle der Dokumentations-Ebene ab: Begleitende Berichte/Protokolle entstehen bei Bedarf in jedem Knoten, während produktive Handbücher bis `NODE_LIVING_DOCS` geschützt bleiben.
  3. **Für Einsteiger und Experten geeignet:** Orientiere dich stilistisch an `docs/GUIDE_TGD.md` und `docs/GUIDE_Quality-Assurance.md`. Nutze klare, greifbare Erklärungen und Alltags-/Baustellen-Analogien für Einsteiger — gepaart mit präziser Methodik für Experten und KI-Agenten (Poppers Fallibilismus, Hoare-Verträge $\{P\}\ S\ \{Q\}$, klare Schreibgrenzen, Vier-Säulen-Meta-QA und objektiv prüfbare Abnahmekriterien).
  4. **Plattform- & Werkzeugunabhängigkeit („mad independent“):** Verwende durchgängig anbieter- und werkzeugneutrale Begriffe (`RUN`-Dokument statt `Ticket`/`GEMINI-*.md`, neutraler *Kontext-Reset* statt `/clear`, Standard-Markdown-Links statt `@`-Referenzen).
  5. **Consent-by-Exception statt Bürokratie:** Aktualisiere die Entscheidungs- und Freigaberegeln (insbesondere in `NODE_HYPOTHESIS.md` und `NODE_PHASE_RED.md`): Jede offene Gestaltungsfrage (`E1..En`) trägt eine eindeutig markierte Standard-Empfehlung; im Folge-Schritt genügt `EMPFEHLUNGEN: ALLE` plus explizite Abweichungen. Nur mehrdeutige, ungebundene Freigaben ohne Bezug (z. B. ein isoliertes „Ok.“) führen zur Rückfrage.
  6. **Rahmen-, Anker- & Gate-Abnahme:** Behalte bestehende `CUBIE_DOC_FRAME_1`-Header (inkl. `order`-Attribut und epistemischem Hinweis) sowie gültige Querverweise auf die Anker in `docs/tgd/README.md` bei. Abnahme über:
     - `qb-cubie docframe update docs/tgd` (2× ausführen; 2. Lauf: `Updated 0 file(s)`),
     - `qb-cubie docframe check docs/tgd --format text`,
     - `qb-cubie docensurance check docs/tgd --format text`,
     - `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py`,
     - Schreibgrenzen-Nachweis: `git status -s` (`src/` = 0, `tests/` = 0).

## 4. Relevante Referenzen
- **Verbindliches Knoten-Handbuch:** [NODE_LIVING_DOCS.md](../../../tgd/NODE_LIVING_DOCS.md)
- **Projekt-Profil:** [DEV-GUIDE_TGD-Workflow.md](../../dev/DEV-GUIDE_TGD-Workflow.md)
- **Inhaltliche Leitdokumente:**
  - [GUIDE_TGD.md](../../GUIDE_TGD.md)
  - [TGD-Knoten-Übersicht (docs/tgd/README.md)](../../../tgd/README.md)
- **Stil-Referenz (Einsteiger & Experten):** [GUIDE_Quality-Assurance.md](../../GUIDE_Quality-Assurance.md)
- **Zu überarbeitende Ziel-Handbücher:**
  - [NODE_ANALYSIS.md](../../tgd/NODE_ANALYSIS.md)
  - [NODE_HYPOTHESIS.md](../../tgd/NODE_HYPOTHESIS.md)
  - [NODE_PHASE_RED.md](../../tgd/NODE_PHASE_RED.md)
  - [NODE_PHASE_GREEN.md](../../tgd/NODE_PHASE_GREEN.md)
  - [NODE_GREEN_AUDIT.md](../../tgd/NODE_GREEN_AUDIT.md)
  - [NODE_LIVING_DOCS.md](../../tgd/NODE_LIVING_DOCS.md)