<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Argon" effort="High" -->
# Arbeitspaket: TGD Docs-Sync & Didaktische Härtung — Reparatur der QA-Handbücher und Referenzdokumentation

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Argon
- **Reasoning-Effort:** High
- **Analysedatum:** 19. November 2026, ~ 22:30 (CET)
- **Synthesebasis:** `tests/ANALYSIS.md`, `tests/HYPOTHESIS.md`, `tests/GEMINI-1.md`, `tests/GEMINI-2.md`, `tests/GEMINI-3.md`, `tests/GEMINI-4.md`, `META_QUESTION.md`, `src/qb_cubie/ebt.py`, `src/qb_cubie/protocols.py`, `src/qb_cubie/reporter.py`, `src/qb_cubie/services/doc_ensurance/doc_rules.py`, `src/qb_cubie/services/doc_ensurance/doc_patterns.py`, `src/qb_cubie/services/doc_ensurance/_markdown_scanner.py`, `src/qb_cubie/services/doc_frame/doc_frame.py`, `src/qb_cubie/services/doc_frame/doc_frame_rules.py`, `tests/test_styleguide.py`, `tests/test_lint.py`, `tests/tests_ebt/test_ebt_quantor_declaration.py`, `tests/tests_meta/test_gate_2.py`, `tests/tests_meta/test_gate_3.py`, `docs/GUIDE_Quality-Assurance.md`, `docs/GUIDE_Contract-Design.md`, `docs/GUIDE_Expect-Flags.md`, `docs/GUIDE_Quantifiers.md`, `docs/GUIDE_Contract-Semantics.md`, `docs/GUIDE_EBT-Usage-Pattern.md`, `docs/GUIDE_Example-Based-Testing.md`, `docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`, `docs/dev/DEV-GUIDE_2-1_EBT-Class.md`, `docs/dev/DEV-GUIDE_2-2_WorldState-Class.md`, `docs/services/GUIDE_DocEnsurance.md`, `README.md`, `docs/README.md`, `tests/README.md`, Git-Historie (`db96ea4b` bis `25730b6d`)
- **Stand**: qb-cubie (v0.0.8)
- **Git-Log**:

```text
commit 25730b6d9d7c4af436465c141ca933cd2332a290 (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Thu Nov 19 22:18:40 2026 +0100

    Tried to repair the cubie-core.
```

---

---

<!-- /qb:frame -->

# Operationsfähiges Arbeitspaket: Reparatur, Synchronisation & Didaktische Erweiterung der Cubie-Dokumentation (TGD Phase 4: Living-Documentation-Sync)

---

## 1. Ausgangslage, Audit des aktuellen Core-/Test-Zustands & Zielsetzung

### 1.1 Empirischer Befund auf `HEAD` (`25730b6d`)

Ein vollständiger Verifikationslauf über den reparierten Core (`25730b6d`) und die reparierte Test-Suite (`905e0a06`) liefert folgendes exaktes Bild:

1. **Core & EBT-Test-Suite (`tests/tests_ebt/`, `tests/tests_meta/`, `tests/test_lint.py`, Styleguide-Metriken):**
   - `tests/tests_ebt/` $\rightarrow$ **`649 passed in 20.60s`** (inklusive aller **32** in der Red-Phase ergänzten Guard-, Invarianten- und Sticky-Quantor-Lebenszyklus-Tests in `test_ebt_quantor_declaration.py`).
   - `tests/tests_meta/` (`test_gate_1.py`, `test_gate_2.py`, `test_gate_3.py`) $\rightarrow$ **`100 % passed`** (`0` Diagnosen im Repository-Scan).
   - `tests/test_lint.py` (`ruff`, `pylint`, `mypy --warn-unreachable`) & `tests/test_styleguide.py` (`test_module_size`, `test_function_size`, `test_docstrings`) $\rightarrow$ **`100 % passed`**.
2. **Einziger verbleibender roter Test im gesamten Repository — `tests/test_styleguide.py::test_docs_code_examples` (`DocEnsurance`):**
   Der lebende Dokumentations-Wächter `DocEnsurance` schlägt exakt an den **4 ausführbaren Alt-Codebeispielen in `docs/`** rot an, die noch `WorldState(..., expect=False)` unter dem impliziten Standard-Existenzquantor (`post="exists"`) ohne `"quantor": "all"` ausführen:
   ```text
   - [DOC-EXEC] docs/GUIDE_EBT-Usage-Pattern.md:147: Unhandled ValueError: STATE-GUARD: post[2].expect=False is forbidden under post_quantor='exists'; use WorldState(expect=True) or post={'quantor': 'all', 'states': [...]}.
   - [DOC-EXEC] docs/GUIDE_Expect-Flags.md:39:       Unhandled ValueError: STATE-GUARD: post[1].expect=False is forbidden under post_quantor='exists'; use WorldState(expect=True) or post={'quantor': 'all', 'states': [...]}.
   - [DOC-EXEC] docs/GUIDE_Expect-Flags.md:80:       Unhandled ValueError: STATE-GUARD: post[1].expect=False is forbidden under post_quantor='exists'; use WorldState(expect=True) or post={'quantor': 'all', 'states': [...]}.
   - [DOC-EXEC] docs/GUIDE_Expect-Flags.md:154:      Unhandled ValueError: STATE-GUARD: post[0].expect=False is forbidden under post_quantor='exists'; use WorldState(expect=True) or post={'quantor': 'all', 'states': [...]}.
   ```
   **Bewertung:** Dass `test_docs_code_examples` exakt an diesen 4 Stellen mit dem neuen `STATE-GUARD` anschlägt, ist der **praktische Beweis für die vierte orthogonale Prüfschicht von TGD**: Sobald der Core gehärtet ist, zwingt `DocEnsurance` die Dokumentation automatisch zur Synchronisation.

---

### 1.2 Die vier Leitziele dieses Arbeitspakets

1. **Vollständige Abbildung aller Core-Reparaturen (`25730b6d`):**
   - **Reine Standard-Quantoren ohne verdeckte Überschreibung:** `EBT.pre` arbeitet standardmäßig als **reiner Allquantor (`"all"`, UND)**, `EBT.post` als **reiner Existenzquantor (`"exists"`, ODER)**. Kein `expect`-Flag schreibt jemals heimlich einen Quantor um.
   - **Explizite Konjunktion für `WorldState(..., expect=False)`:** Lokale Verbote in `post` sind prädikatenlogisch einschränkende Bedingungen und **nur** unter `post={"quantor": "all", "states": [...]}` erlaubt. Unter `post="exists"` (implizit oder explizit) blockiert der **`STATE-GUARD`** (`ValueError`) sofort vor der Ausführung.
   - **Verbot von `pre.expect=False`:** `WorldState(..., expect=False)` in `pre` wird nicht mehr stillschweigend ignoriert, sondern vorab mit `ValueError("STATE-GUARD: ...")` abgewiesen.
   - **Strikte `bool`-Typprüfung (`validate_bool_expect`):** `WorldState.expect` und `EBT.expect` akzeptieren ausschließlich echte `bool`-Werte (`True` oder `False`, geprüft per `type(value) is not bool`). Werte wie `None`, `0`, `1`, `"true"` oder `[]` lösen sofort `TypeError("STATE-GUARD: ...")` aus.
   - **Reine Schritt-Auswertung (`evaluate_step_logic`):** Keine historische $Q^+$/$Q^-$-Partitionierung und kein *Vacuous-True*-Zweig unter `"exists"` (`evaluate_step_logic([], "exists") == False`).
   - **Sticky-Quantor-Invariante bei Wiederverwendung einer `EBT`-Instanz:** Wiederholte `.run()`-Aufrufe ohne Neuzuweisung sowie In-Place-Listenmutationen (`case.post.append(...)`) bewahren den explizit deklarierten Quantor (`pre_quantor` / `post_quantor`); eine Attribut-Neuzuweisung ohne Dict-Wrapper (`case.pre = ...` / `case.post = ...` mit `WorldState`, Liste oder `None`) setzt den Quantor beim nächsten Lauf deterministisch auf den Standardwert (`pre="all"`, `post="exists"`) zurück.
2. **Zweistufige Verständlichkeit („Für Einsteiger UND Experten“ — Ergänzen statt Ersetzen):**
   - Die präzise Fach- und Formelsprache für Experten (*Allquantor $\forall$ / Konjunktion*, *Existenzquantor $\exists$ / Disjunktion*, *Hoare-Tripel $\{P\}\ S\ \{Q\}$*, *kartesisches Kreuzprodukt $N \times M$*, *Tautologie*, *Subsumtion $Q_{\text{pos}} \implies \neg Q_{\text{neg}}$*, *Vacuous Pass*, *Mutations-Überleben*) bleibt vollständig erhalten.
   - Jede komplexe Erklärung und jedes Python-Konstrukt (`def`, `args`, `returns`, `None`, `Exception` / `raises`, `lambda`, `dict` `{"quantor": ..., "states": ...}`, `bool` vs. `int`, `@pytest.mark.parametrize`) wird durch eine **einfache, anschauliche Alltagserklärung („Einfach erklärt“)** ergänzt, sodass auch absolute Programmier- und Python-Einsteiger jedes Beispiel mühelos verstehen.
3. **Verankerung der gelebten TGD-Phasen aus den letzten Commits (`db96ea4b` $\to$ `25730b6d`):**
   - Der TGD-Abschnitt in `docs/GUIDE_Quality-Assurance.md` (und die Querverweise in `GUIDE_Expect-Flags.md`) spiegelt den in den jüngsten Commits praktisch vorexerzierten Phasenablauf wider:
     1. *Baseline, Exploratives Audit & Meta-QA-Hypothesenbildung* (`ANALYSIS.md` & `HYPOTHESIS.md`: $Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$, Subsumtion, Tautologie-Gefahr, Mutation Testing, Äquivalenzklassen),
     2. *TGD Red-Phase* (`905e0a06`: strikte Schicht-Isolation nur auf `tests/`, Migration von $Q_{\text{Ist}}$-Tests auf $Q_{\text{Soll}}$, Kalibrierung der Meta-Gates 2 & 3, gezielter Red-Nachweis neuer Verträge gegen den alten Core, anschließender **Test-Freeze**),
     3. *TGD Green-Phase* (`25730b6d`: Reparatur ausschließlich in `src/qb_cubie/` unter striktem Dateischutz auf `tests/**/*.py` mit Eskalationsprotokoll `GREEN_AUDIT.md` statt Silent-Edits),
     4. *TGD Living-Documentation-Sync* (`DocEnsurance` als 4. orthogonale Schicht, die veraltete Handbuch-Beispiele automatisch aufdeckt).
4. **Strikte Wahrung des bestehenden Handbuch-Stils & der `DocEnsurance`-/ `DocFrame`-Konventionen:**
   - Alle Rahmen-Blöcke (`CUBIE_DOC_FRAME_1`), H1-Titel (wichtig für `GUIDE_ROUTER` in `DocFrame`!), Navigationsleisten, Mutation-Disclaimer, Tonfall und Typografie bleiben erhalten.
   - Nach Umsetzung dieses Arbeitspakets muss `.venv/bin/python -m pytest -q tests/test_styleguide.py` mit **`0 failed` und `0 warnings`** durchlaufen.

---

### 1.3 Gesamtinventar aller zu bearbeitenden Dokumente (4 Kern-Handbücher + 6 identifizierte Folge-Dokumente)

| Arbeitspaket | Zieldatei | Kategorie | Warum betroffen? | Aktueller `DocEnsurance`-Status |
| :---: | :--- | :--- | :--- | :---: |
| **AP 1** | [`docs/GUIDE_Expect-Flags.md`](../docs/GUIDE_Expect-Flags.md) | **Kern-Handbuch (1/4)** | Enthält **3 der 4 aktuell crashenden Live-Code-Snippets** (Z. 39, 80, 154) sowie die veraltete $Q^+$/$Q^-$-Auswertungsregel (Z. 26–32) und Vacuous-Pass-Erklärung (Z. 150–188). | **3x `DOC-EXEC` (ROT)** |
| **AP 2** | [`docs/GUIDE_Quantifiers.md`](../docs/GUIDE_Quantifiers.md) | **Kern-Handbuch (2/4)** | Muss die reine Quantor-Semantik ohne `expect`-Überschreibung, die neuen `STATE-GUARD`s (`expect=False` nur unter `post="all"`, `expect` strikt `bool`, kein `pre.expect=False`), den Sticky-Quantor-Lebenszyklus und Einsteiger-Erklärungen abbilden. | Grün (Text veraltet) |
| **AP 3** | [`docs/GUIDE_Contract-Design.md`](../docs/GUIDE_Contract-Design.md) | **Kern-Handbuch (3/4)** | Z. 143 schränkt den Existenzquantor noch auf *„die positiven Zustände in `post`“* ein; Z. 182 verweist ohne `"quantor": "all"`-Hinweis auf `expect`-Flags; Einsteiger-Erklärungen für Kreuzprodukt ($2 \times 2$) und `@pytest.mark.parametrize` ergänzen. | Grün (Text veraltet) |
| **AP 4** | [`docs/GUIDE_Quality-Assurance.md`](../docs/GUIDE_Quality-Assurance.md) | **Kern-Handbuch (4/4)** | Haupt-Einstieg: Baustein B (Z. 81–91), Baustein C (Z. 93–105), Spickzettel (Z. 112), $Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$ (Z. 120–131), **TGD-Phasen aus den letzten Commits** (Z. 133–154), Hoare-Analogie (Z. 162), Empfehlung 1 (Z. 173) sowie Einsteiger-Grundlagen (`def`, `args`, `returns`, `WorldState`). | Grün (Text veraltet) |
| **AP 5** | [`docs/GUIDE_EBT-Usage-Pattern.md`](../docs/GUIDE_EBT-Usage-Pattern.md) | **Weiteres Doc (1/6) — PFLICHT!** | Enthält das **4. aktuell crashende Live-Code-Snippet** (`Z. 147–169`: `post=[WS("OK"), WS("WARN"), WS("ERROR", expect=False)]`) sowie veraltete Formulierungen in Z. 179–192 und Z. 254. | **1x `DOC-EXEC` (ROT)** |
| **AP 6** | [`docs/GUIDE_Contract-Semantics.md`](../docs/GUIDE_Contract-Semantics.md) | **Weiteres Doc (2/6) — PFLICHT!** | **Zentrale technische Referenz (Single Source of Truth):** Dokumentiert in Z. 25–32 und Z. 49–66 noch die alte $Q^+$/$Q^-$-Sonderformel und verschweigt dort sogar noch den `{"quantor": ..., "states": ...}`-Wrapper, die neuen `STATE-GUARD`s, den Sticky-Quantor-Reset (Z. 203–206) und `pre_quantor`/`post_quantor` im `JsonReporter` (Z. 227). | Grün (Spezifikation veraltet!) |
| **AP 7.1** | [`docs/dev/DEV-GUIDE_2-1_EBT-Class.md`](../docs/dev/DEV-GUIDE_2-1_EBT-Class.md) | **Weiteres Doc (3/6)** | Nimmt in Z. 23 noch auf die gelöschte Methode `_ensure_list` statt `_parse_state_config` Bezug, verschweigt Dict-Wrapper, `@pre.setter`/`@post.setter` (`_arrange_states`), `validate_bool_expect` und beschreibt in Z. 27 & Z. 46 noch die alte $Q^+$/$Q^-$-Aggregation. | Grün (Internals veraltet) |
| **AP 7.2** | [`docs/dev/DEV-GUIDE_2-2_WorldState-Class.md`](../docs/dev/DEV-GUIDE_2-2_WorldState-Class.md) | **Weiteres Doc (4/6)** | Behauptet in Z. 39 fälschlich, ein Feld für erwartete Exceptions existiere nicht (`raises` existiert!) und beschreibt `expect` in Z. 45 noch ohne `validate_expect()` (`bool`-Guard) und ohne `STATE-GUARD` bei `pre` / `post="exists"`. | Grün (Internals veraltet) |
| **AP 7.3** | [`docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`](../docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) | **Weiteres Doc (5/6)** | Erwähnt in Z. 20 & Z. 29 bei `pre` und `post` nur `WorldState` oder Listen davon, noch nicht das Quantor-Wrapper-Dictionary `{"quantor": "all" \| "exists", "states": ...}`. | Grün (Internals unvollständig) |
| **AP 7.4** | [`README.md`](../README.md) & [`docs/GUIDE_Example-Based-Testing.md`](../docs/GUIDE_Example-Based-Testing.md) | **Weiteres Doc (6/6)** | `README.md:122` spricht pauschal von *„dieselbe Liste erlaubter und verbotener Zielmuster“* ohne Hinweis auf die reinen Standard-Quantoren (`pre="all"`, `post="exists"`) und `post={"quantor": "all", ...}` für Verbote. `GUIDE_Example-Based-Testing.md:43` sagt noch *„Verwende pro Ausführung eine neue EBT-Instanz“* (obwohl `.run()`-Wiederverwendung mit Reset unterstützt und dokumentiert ist). | Grün (Text unpräzise) |

*(Hinweis zu ausgeschlossenen historischen Entwürfen: `docs/feature-drafts/meta-qa/1/META_GATE_2.md`, `docs/feature-drafts/meta-qa/1/META_GATE_3.md`, `META_QUESTION.md` und `GUTACHTEN.md` dokumentieren historische Sprint- und Audit-Stände und sind in `tests/test_styleguide.py:112-119` explizit von `DocEnsurance` ausgenommen; sie müssen und sollen nicht rückwirkend verfälscht werden.)*

---

## 2. Verbindliche Stil-, Didaktik- & `DocEnsurance`-Leitplanken

Jede Änderung an einer Datei unter `docs/` oder `README.md` wird automatisch von `tests/test_styleguide.py::test_docs_code_examples` gegen **`CUBIE_DOC_STYLE`**, **`CUBIE_DOC_RULES`**, **`CUBIE_DOCFRAME_RULES`** und **`CUBIE_DOC_FRAME_1..3`** geprüft. Deshalb gelten für die Umsetzung ausnahmslos diese **6 technischen und didaktischen Konstruktionsregeln**:

1. **Anker-Regel vor jedem `python`-Codeblock (`DOC-PRE`, `Explanation(min_chars=20)`):**
   - Unmittelbar **vor** jedem ```` ```python ````-Block **muss** ein normaler Fließtext-Absatz (`MdBlock(kind="paragraph")` mit mindestens 20 Zeichen) stehen!
   - **Achtung Scanner-Falle (`_markdown_scanner.py:11, 79-86`):** Aufzählungspunkte (`* `, `- `, `1. `), Tabellenzeilen (`| ... |`), Überschriften (`# ...`) und einfache Zitate (`> ...` ohne GitHub-Alert-Header) erzeugen **keinen** `paragraph`-Block, sondern `list`- bzw. `heading`-Blöcke! Steht direkt über einem ```` ```python ````-Block eine Aufzählungsliste oder Überschrift ohne abschließenden Überleitungs-Satz als eigener Absatz, bricht `DocEnsurance` sofort mit `DOC-PRE: Missing or invalid pre-block 'explanation'` ab!
   - **Goldene Regel:** Vor jedem ```` ```python ````-Block steht immer ein eigenständiger Überleitungs-Absatz (keine Liste, keine Tabelle, keine Überschrift).
2. **Ergebnis-Block nach jedem `python`-Codeblock (`DOC-POST`, `DOC-OUT`, `DOC-NO-OUTPUT`, `DOC-LARGE-OUTPUT`):**
   - Unmittelbar **nach** jedem ```` ```python ````-Block muss ein `<details>\n<summary>Ergebnis</summary>\n\n```text\n...\n```\n</details>`-Block stehen, dessen Text exakt mit dem `stdout` des Snippets (bzw. bei `raises=<Exception>` mit `"<Typ>: <Nachricht>"`) übereinstimmt (maximal 25 Zeilen Output).
3. **Maximale Codeblock-Länge (`DOC-HIGH-COMPLEXITY`, `max_lines=30`, `severity="error"`):**
   - Kein ```` ```python ````-Codeblock darf mehr als **30 Zeilen** umfassen! Alle in diesem Arbeitspaket geplanten Code-Snippets sind exakt auf **15 bis 27 Zeilen** ausgelegt.
4. **Schutz der `CUBIE_DOC_FRAME_1`-Zonen und H1-Dokumenttitel (`DOCFRAME-OUTDATED`, `DOCFRAME-MISSING`, `DOCFRAME-BROKEN-ROUTE`):**
   - Die `<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" ... -->`- und `zone="foot"`-Blöcke sowie die H1-Überschriften (`# ...`) der Dokumente dürfen **nicht** verändert werden (da `GUIDE_ROUTER` die H1-Titel aller `docs/GUIDE_*.md`-Dateien in jedem Footer des gesamten Repositories referenziert!).
5. **Zweistufige Didaktik („Für Einsteiger & Experten“):**
   - **Für Programmier- und Python-Einsteiger:** Fachbegriffe (`Funktion`, `args`, `returns`, `None`, `Exception`/`raises`, `lambda`, `Dictionary` `{...}`, `bool` `True`/`False`, `@pytest.mark.parametrize`, `Allquantor`/`Existenzquantor`, `Kreuzprodukt`, `Vacuous Pass`, `Tautologie`, `Subsumtion`) werden direkt beim Auftreten durch greifbare Alltagsbilder (*Küchenmaschine/Rezept*, *UND-Checkliste vs. ODER-Auswahlliste*, *Speisekarten-Verwechslung*, *Türsteher-ODER-Falle*, *Foto vom Tatort vs. Bauplan*) und kurze Python-Lesehilfen erklärt.
   - **Für Experten:** Die formale Prädikatenlogik ($\forall$, $\exists$, $Q^+$, $Q^-$, $\text{sat}(p, q)$, $\{P\}\ S\ \{Q\}$, $Q_{\text{pos}} \implies \neg Q_{\text{neg}}$), Laufzeit-/Typ-Guards (`type(value) is not bool`, `STATE-GUARD`) und Meta-Gate-Verweise (`META-EBT-CROSS-PRODUCT`, `META-EBT-LONELY-NEGATION`) stehen präzise daneben.
6. **Stil-Kontinuität:**
   - Die 4 QA-Handbücher (`GUIDE_Quality-Assurance.md`, `GUIDE_Contract-Design.md`, `GUIDE_Expect-Flags.md`, `GUIDE_Quantifiers.md`) nutzen weiterhin die direkte, einladende `"du"`-Ansprache mit übersichtlichen Tabellen, GitHub-Alerts (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!CAUTION]`) und `👉`-Wegweisern.
   - Die Referenz- und Entwicklerdokumente (`GUIDE_Contract-Semantics.md`, `GUIDE_EBT-Usage-Pattern.md`, `DEV-GUIDE_*`, `README.md`) behalten ihren kompakten, präzisen Referenzstil.

---

## 3. Detaillierte Arbeitspakete für die 4 Kern-Handbücher (AP 1 – AP 4)

---

### Arbeitspaket 1 (AP 1): [`docs/GUIDE_Expect-Flags.md`](../docs/GUIDE_Expect-Flags.md)

> [!IMPORTANT]
> **Warum AP 1 zuerst umgesetzt wird:**
> `docs/GUIDE_Expect-Flags.md` enthält **3 der 4 aktuell fehlschlagenden Live-Code-Snippets** (Zeilen 39, 80 und 154) und bildet die zentrale Anlaufstelle für `expect=True` und `expect=False`.

#### AP 1.1: Einleitung im Header-Slot (Zeile 8)
- **Hinweis zu `DocFrame`:** Da `HeaderContentSlot()` den Text vor dem ersten `---` innerhalb von `zone="head"` unverändert übernimmt (`frame_blocks.py`), darf Zeile 8 sprachlich präzisiert werden, ohne dass `DOCFRAME-OUTDATED` auslöst:
  ```markdown
  Dieses Handbuch beschreibt den gezielten Einsatz von `expect=True` und `expect=False` auf `WorldState`- und `EBT`-Ebene: Wie man Soll-Ziele und Negativ-Filter in einem konjunktiven `post={"quantor": "all", ...}`-Vertrag kombiniert, kaputte grüne Tests ehrlich rot macht, Red-Phase-Gegenproben schreibt und die gefährliche „einsame Negation“ (*Vacuous Pass*) vermeidet. Die formalen Auswertungsregeln definiert die [Vertragssemantik](GUIDE_Contract-Semantics.md).
  ```

#### AP 1.2: Abschnitt 1 — „Zwei Ebenen für `expect` (Standardwert: `True`)“ (Zeilen 22–32)
Ersetze Zeilen 22–32 durch eine sowohl für Python-Einsteiger als auch für Experten glasklare Darstellung der zwei Ebenen, der strikten Quantor-Trennung und der neuen `STATE-GUARD`s:

```markdown
## 1. Zwei Ebenen für `expect` (Standardwert: `True`)

**Einfach erklärt (für Einsteiger):** Beim Testen möchtest du manchmal sagen: *„Genau dieses Ergebnis wünsche ich mir“* (`expect=True`, der Standard). Manchmal möchtest du aber auch das Gegenteil ausdrücken: *„Dieser gefährliche Wert darf auf keinen Fall herauskommen!“* oder *„Dieser ganze Testlauf muss bei einem Fehler rot anschlagen!“* Dafür nutzt du den Schalter `expect=False`. In Python sind `True` (*Wahr / Ja*) und `False` (*Falsch / Nein*) die beiden einzigen echten Wahrheitswerte (`bool`).

In Cubie existiert das Flag `expect` (Standardwert jeweils `True`) auf **zwei klar getrennten Ebenen**, die niemals die Quantoren (`"all"` oder `"exists"`) heimlich umschreiben:

| Ebene | Bedeutung von `expect=True` (Standard) | Bedeutung von `expect=False` | Typischer Einsatz & Quantor-Regel |
| :--- | :--- | :--- | :--- |
| **`WorldState(..., expect=...)`** (in `post`) | **Gefordertes / erlaubtes Zielmuster:** Alle in diesem `WorldState` angegebenen Prüfungen müssen zutreffen (`sat(q) = match(q)`). | **Verbotenes Muster (Negativ-Filter):** Dieses Muster darf **nicht** zutreffen (`sat(q) = not match(q)`). | Ein positives Soll-Ergebnis fordern und gleichzeitig gefährliche Rückgaben ausschließen. **Zwingend mit `post={"quantor": "all", "states": [...]}` nutzen!** |
| **`EBT(..., expect=...)`** (auf dem Vertrag) | Der gesamte `EBT`-Lauf muss bestehen (`evaluation == lauf_ok`). | Kehrt das fertige Gesamtergebnis am Ende um (`evaluation == not lauf_ok`). | Red-Phase-Nachweise und Gegenproben: beweisen, dass ein Soll-Vertrag bei einem bekannten Fehler tatsächlich rot anschlägt. |

### Warum `WorldState(..., expect=False)` immer `post={"quantor": "all", ...}` erfordert

Standardmäßig prüft `post` nach der **ODER-Regel** (`post_quantor="exists"`): Es reicht, wenn *mindestens ein* Zustand aus `post` erfüllt ist. Ein Verbot (`expect=False`) in einer solchen ODER-Liste wäre jedoch eine logische Falle:

* **Einfach erklärt (Die Türsteher-ODER-Falle):** Stell dir vor, du gibst einem Türsteher eine **ODER-Liste** (`"exists"`): *„Einlass, wenn das Ergebnis eine ganze Zahl ist **ODER** wenn es nicht `99` ist.“*
  * Kommt jetzt die verbotene Zahl `99` heraus, stimmt zwar die zweite Bedingung nicht – aber die erste Bedingung (*„ist eine ganze Zahl“*) stimmt! Weil bei **ODER** ein einziger Treffer genügt, winkt der Türsteher die verbotene `99` einfach grün durch.
  * Kommt stattdessen ein völlig kaputter Wert wie `"absturz"` oder `None` heraus, stimmt die zweite Bedingung (*„ist nicht `99`“*) – und der Türsteher winkt auch diesen Fehler grün durch!
  * Damit ein Soll-Ziel **und** ein Verbot gemeinsam wirken (*„Muss eine ganze Zahl sein **UND** darf nicht `99` sein“*), brauchst du zwingend eine **UND-Checkliste**: `post={"quantor": "all", "states": [...]}`.
* **Für Experten (Prädikatenlogik & Tautologie-Schutz):** Unter dem Existenzquantor ($\exists q \in Q : \text{sat}(q, y)$) erzeugt jedes Verbot $q^-$ innerhalb des positiven Zielbereichs ($\{y \mid m(q^-, y)\} \subseteq \{y \mid m(q^+, y)\}$) die unbedingte Tautologie $m(q^+, y) \lor \neg m(q^-, y) \equiv \top$ für alle $y \in \text{Any}$ (bzw. bei disjunktem Sollwert dessen logische Subsumtion). Unter dem Allquantor ($\forall q \in Q : \text{sat}(q, y)$) hingegen wirkt dieselbe Formel als reine Konjunktion $(\forall q \in Q^+ : m(q, y)) \land (\forall q \in Q^- : \neg m(q, y))$, ohne dass `expect=False` jemals das Quantor-Verhalten überschreibt.

> [!IMPORTANT]
> **Drei harte `STATE-GUARD`-Schutzregeln im Cubie-Core:**
> 1. **Kein `WorldState(expect=False)` unter `post="exists"`:** Übergibst du `WorldState(..., expect=False)` im Standard-`post` (oder unter explizitem `"quantor": "exists"`), bricht Cubie sofort vor der Target-Ausführung mit `ValueError("STATE-GUARD: ...")` ab.
> 2. **Kein `WorldState(expect=False)` in `pre`:** Vorbedingungen beschreiben Eingaben, die ausgeführt werden sollen – kein Verbot. `pre` mit `expect=False` wird ebenfalls sofort mit `ValueError("STATE-GUARD: ...")` abgewiesen.
> 3. **Strikt nur echte `bool`-Werte (`True` oder `False`):** Sowohl `WorldState.expect` als auch `EBT.expect` lehnen `None` (*„Nichts“*), Zahlen wie `0` oder `1` (in Python ist `bool` technisch eine Unterklasse von `int`!) oder Strings sofort mit `TypeError("STATE-GUARD: ...")` ab. Außerdem fängt `EBT(..., expect=False)` keine unbehandelten Target-Exceptions (Programm-Abstürze) ab – dafür dient `post=WorldState(raises=...)`.
```

#### AP 1.3: Abschnitt 2 — „Best Practice 1: Soll-Ziel und Negativ-Filter im selben `post`“ (Zeilen 35–66) — **LIVE-FIX #1**
Ersetze Zeilen 35–66 (behebt den `DOC-EXEC`-Fehler in Zeile 39, bleibt mit 21 Codezeilen weit unter `max_lines=30` und erklärt `lambda` und das `{"quantor": "all", ...}`-Dictionary für Einsteiger):

````markdown
## 2. Best Practice 1: Soll-Ziel und Negativ-Filter im selben `post`

Wenn du in einem Fachtest sowohl festlegen möchtest, **was** herauskommen muss (`expect=True`), als auch, **was** unter keinen Umständen passieren darf (`expect=False`), packst du beide `WorldState`-Einträge in eine explizite **UND-Checkliste** (`post={"quantor": "all", "states": [...]}`).

* **Python-Lesehilfe für Einsteiger:**
  * Das geschweifte Klammerpaar `{"quantor": "all", "states": [...]}` ist ein Python-**Dictionary** (wie ein kleines Formular mit zwei beschrifteten Feldern: `"quantor": "all"` schaltet auf den UND-Modus um, und `"states"` enthält die Liste der Prüfregeln).
  * `lambda value: value < 0` ist eine einzeilige Mini-Prüffunktion in Python: Sie nimmt das beobachtete Ergebnis (`value`) entgegen und prüft, ob es kleiner als `0` (also ein negativer Preis) ist. Zusammen mit `expect=False` bedeutet das: *„Ein Ergebnis `< 0` ist verboten!“*

Im folgenden Beispiel zieht `apply_discount` mit dem Gutschein `"SAVE15"` genau `15` vom Preis `100` ab (`85`), während negative Preise ausdrücklich verboten sind:

```python
from qb_cubie import EBT, WorldState


def apply_discount(price: int, coupon: str) -> int:
    return price - 15 if coupon == "SAVE15" else price


trace = EBT(
    target=apply_discount,
    pre=WorldState(args=(100, "SAVE15")),
    post={
        "quantor": "all",
        "states": [
            WorldState(returns=85),
            WorldState(returns=lambda value: value < 0, expect=False),
        ],
    },
).run()

print(f"Rabatt-Vertrag erfüllt: {trace.evaluation} | Beobachtet: {trace.traces[0].outcome.returns}")
```

<details>
<summary>Ergebnis</summary>

```text
Rabatt-Vertrag erfüllt: True | Beobachtet: 85
```
</details>
````

#### AP 1.4: Abschnitt 3 — „Best Practice 2: Ehrlich-roter Bug-Nachweis (kaputte Tests reparieren)“ (Zeilen 69–112) — **LIVE-FIX #2**
Ersetze Zeilen 69–112 (behebt den `DOC-EXEC`-Fehler in Zeile 80, bleibt mit 24 Codezeilen unter `max_lines=30` und erklärt den Übergang von $Q_{\text{Ist}}$ zu $Q_{\text{Soll}}$ für Einsteiger und Experten):

````markdown
## 3. Best Practice 2: Ehrlich-roter Bug-Nachweis (kaputte Tests reparieren)

Stell dir vor, beim Ausprobieren einer Funktion hat sich ein Fehler in deine Test-Suite eingeschlichen: Eine kaputte Rabatt-Funktion gibt fälschlicherweise `-10` zurück, und jemand hat diesen kaputten Wert `-10` versehentlich mit dem Standard `expect=True` als „gewünschtes Ergebnis“ in den Test geschrieben. In der Qualitätssicherung nennt man das eine ungeprüfte **Beobachtung des Ist-Zustands ($Q_{\text{Ist}}$)** statt einer echten **Soll-Vorgabe ($Q_{\text{Soll}}$)** (mehr dazu im [QA-Handbuch](GUIDE_Quality-Assurance.md#2-die-gefährlichste-falle-der-qualitätssicherung-charakterisierung-q_ist-vs-spezifikation-q_soll)). Die Folge: Dein Test leuchtet trügerisch **grün**, obwohl der Code kaputt ist!

Statt den Testfall wegzuwerfen, reparierst du ihn in drei klaren Schritten:

1. **Bug-Symptom verbieten:** Du setzt an dem aufgezeichneten Fehlzustand `WorldState(returns=-10, expect=False)`.
2. **Positives Soll-Gesetz ergänzen:** Du fügst das echte fachliche Ziel hinzu, etwa `WorldState(returns=lambda value: value >= 0)` (*„Der Preis muss mindestens 0 sein“*).
3. **Unter `"quantor": "all"` bündeln:** Da beide Regeln gleichzeitig gelten müssen, verpackst du sie in `post={"quantor": "all", "states": [...]}`.

* **Was dadurch passiert (TGD Red-to-Green):**
  * **Sofort ehrlich rot (Red-Phase):** Solange der Bug (`-10`) noch im Code steckt, schlägt der Test jetzt zuverlässig fehl (`trace.evaluation == False`).
  * **Automatisch grün nach der Reparatur (Green-Phase):** Sobald du `buggy_discount` im Quellcode reparierst (z. B. `return price - 15`), erfüllt das Ergebnis `85` sowohl `value >= 0` als auch `!= -10` – und derselbe Test wird ohne weitere Änderung **grün (`True`)**!

Im folgenden Beispiel nutzen wir `reporter=None` (dadurch gibt Cubie das Prüfergebnis `trace.evaluation` direkt als `False` zurück, statt den Lauf sofort mit einem `pytest`-Fehler abzubrechen):

```python
from qb_cubie import EBT, WorldState


def buggy_discount(price: int) -> int:
    return -10  # Bug: negativer Preis statt Rabatt


# Mit "quantor": "all" und expect=False verbieten wir das Bug-Symptom (-10)
# und fordern gleichzeitig das Soll-Gesetz (value >= 0) – der Test wird ehrlich rot:
trace = EBT(
    target=buggy_discount,
    pre=WorldState(args=100),
    post={
        "quantor": "all",
        "states": [
            WorldState(returns=lambda value: value >= 0),  # Eigentliches Soll-Gesetz
            WorldState(returns=-10, expect=False),          # Verbotenes Bug-Symptom
        ],
    },
    reporter=None,
).run()

print(f"Test schlägt gegen den Bug an (ehrlich rot): {trace.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Test schlägt gegen den Bug an (ehrlich rot): False
```
</details>

* **Der Nutzen:** Du bewahrst das konkrete Fehlerszenario (`returns=-10`) als dauerhaftes Schutzschild (Regressions-Wächter) in deinem Vertrag, während das positive Soll-Ziel (`value >= 0`) sicherstellt, dass die Funktion nach dem Fix auch wirklich einen gültigen Preis liefert.
````

#### AP 1.5: Abschnitt 4 — „Best Practice 3: Red-Phase-Gegenproben mit `EBT(..., expect=False)`“ (Zeilen 115–147)
Behalte das funktionierende Code-Snippet (Zeilen 119–135) unverändert bei und ergänze direkt davor eine kurze Einsteiger-Erklärung zu `ExceptionExpectation` und dem Unterschied zu `WorldState(expect=False)`:

```markdown
## 4. Best Practice 3: Red-Phase-Gegenproben mit `EBT(..., expect=False)`

Manchmal möchtest du nicht bloß einen einzelnen Rückgabewert verbieten, sondern beweisen, dass ein **kompletter Soll-Vertrag** bei einem noch fehlenden Schutzmechanismus tatsächlich Alarm schlägt (eine sogenannte **Red-Phase-Gegenprobe** im Test-Guided Development):

* **Einfach erklärt (für Einsteiger):** Wenn jemand eine Funktion `configure_timeout(-5)` mit einer unsinnigen negativen Sekundenzahl aufruft, soll die Funktion in Python kontrolliert mit einem Fehler-Alarm (`ValueError`) stoppen, dessen Fehlermeldung das Wort `"positive"` enthält. Diesen gewünschten Fehler-Alarm beschreibt man in Cubie mit `ExceptionExpectation(ValueError, match=r"positive")`.
* Solange dieser Schutz (`STATE-GUARD`) in der Funktion aber noch **fehlt** (Red-Phase), läuft `-5` einfach durch und der Soll-Vertrag scheitert. Setzt du nun `expect=False` außen auf **`EBT(..., expect=False)`**, sagst du zu Cubie: *„Ich erwarte, dass dieser Soll-Vertrag gegen den unfertigen Code noch scheitert!“* Da `post` hier nur ein einziges positives Ziel (`expect=True`) enthält, ist kein `"quantor": "all"` nötig:
```
*(Direkt danach folgt unverändert der Codeblock `from qb_cubie import EBT, ExceptionExpectation, WorldState ...` aus Z. 119–147.)*

#### AP 1.6: Abschnitt 5 — „Anti-Pattern: Die ‚einsame Negation‘ (*Vacuous Pass*)“ (Zeilen 150–191) — **LIVE-FIX #3**
Ersetze Zeilen 150–191 (behebt den `DOC-EXEC`-Fehler in Zeile 154, bleibt mit 25 Codezeilen unter `max_lines=30` und erklärt die zweistufige Absicherung aus Laufzeit-`STATE-GUARD` und *Vacuous Pass* für Einsteiger und Experten):

````markdown
## 5. Anti-Pattern: Die „einsame Negation“ (*Vacuous Pass*)

Was passiert, wenn man in einem Test **nur** hinschreibt, was *nicht* herauskommen darf (`expect=False`), aber komplett vergisst anzugeben, was *eigentlich* herauskommen soll (`expect=True`)?

In der Qualitätssicherung nennt man das eine **„einsame Negation“** (*Lonely Negation*), und sie führt zu einem sogenannten **Vacuous Pass** (auf Deutsch: *„leerer Durchmarsch“*):

* **Einfach erklärt (für Einsteiger):** Stell dir vor, du bestellst im Restaurant eine warme Suppe, schreibst auf deinen Prüfzettel für die Küche aber nur die einzige Regel: *„Es darf kein Stein auf dem Teller liegen (`returns=-1, expect=False`).“* Wenn der Kellner dir jetzt einen komplett **leeren Teller** (`None` – in Python das Wort für *„Nichts / leer“*) hinstellt, liegt darauf tatsächlich kein Stein. Dein Test prüft: *„Ist `None` ungleich `-1`?“* – sagt *„Ja, stimmt!“* und leuchtet **grün (`True`)**, obwohl du überhaupt keine Suppe bekommen hast!
* **Zweistufiger Schutz in Cubie (für Einsteiger & Experten):**
  1. **Stufe 1 — Laufzeit-`STATE-GUARD` bei `post="exists"`:** Wenn du `post=WorldState(returns=-1, expect=False)` ohne `"quantor": "all"` schreibst, stoppt Cubie dich sofort vor dem Start mit einem `ValueError("STATE-GUARD: ...")`.
  2. **Stufe 2 — Positives Anker-Ziel in `post={"quantor": "all", ...}` (+ statisches Meta-Gate 3):** Selbst wenn du `post={"quantor": "all", "states": WorldState(returns=-1, expect=False)}` schreibst, bleibt ein einzelnes Verbot ohne positives Ziel (`lonely`) blind gegenüber völlig falschen Rückgaben wie `None` ($\forall q \in \{q^-\} : \neg m(q, \text{None}) \equiv \top$). Erst wenn du mindestens ein positives Soll-Ziel wie `WorldState(returns=int)` (*„Muss eine ganze Zahl sein“*) in dieselbe `"all"`-Liste aufnimmst (`guarded`), fliegt das kaputte `None` sofort auf (`False`). In Cubies eigener Test-Suite spürt zusätzlich der statische Code-Wächter **Meta-Gate 3 (`META-EBT-LONELY-NEGATION`)** solche einsamen Negationen automatisch auf.

Das folgende Beispiel stellt die „einsame Negation“ (`lonely`, trügerisch `True`) und den sauber verankerten Vertrag mit positivem Typ-Ziel (`guarded`, erkennt den `None`-Bug als `False`) unter `post={"quantor": "all", ...}` direkt gegenüber:

```python
from qb_cubie import EBT, WorldState


def broken_total(price: int) -> int | None:
    return None  # Bug: liefert None ("Nichts") statt eines gültigen Preises


lonely = EBT(
    target=broken_total,
    pre=WorldState(args=100),
    post={"quantor": "all", "states": WorldState(returns=-1, expect=False)},
    reporter=None,
).run()

guarded = EBT(
    target=broken_total,
    pre=WorldState(args=100),
    post={
        "quantor": "all",
        "states": [WorldState(returns=int), WorldState(returns=-1, expect=False)],
    },
    reporter=None,
).run()

print(f"Nur Verbot (Vacuous Pass): {lonely.evaluation} | Mit Positiv-Ziel: {guarded.evaluation}")
```

<details>
<summary>Ergebnis</summary>

```text
Nur Verbot (Vacuous Pass): True | Mit Positiv-Ziel: False
```
</details>

* **Merksatz für `expect=False`:** Nutze `WorldState(..., expect=False)` immer innerhalb von `post={"quantor": "all", "states": [...]}` und kombiniere es dort mit mindestens einem positiven Soll-Ziel (`expect=True`, z. B. Typ, Wertebereich oder Struktur), damit dein Vertrag nicht durch einen *Vacuous Pass* blind für andere Fehler wird.

> [!TIP]
> **Weiterführende Handbücher:** Wie du Verträge eindeutig auf einzelne Wertepaare schneidest, zeigt [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md). Wie du die Quantoren `"all"` und `"exists"` sowie ihren Lebenszyklus bei wiederholten Läufen steuerst, erklärt [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).
````

---

### Arbeitspaket 2 (AP 2): [`docs/GUIDE_Quantifiers.md`](../docs/GUIDE_Quantifiers.md)

#### AP 2.1: Abschnitt 1 — „Standardregeln vs. explizite Quantor-Steuerung“ (Zeilen 22–30)
Ersetze Zeilen 22–30, um den Begriff „Quantor“ für Einsteiger zu entmystifizieren und die **reine, durch kein `expect`-Flag überschreibbare Quantor-Semantik** für Experten kristallklar festzuschreiben:

```markdown
## 1. Standardregeln vs. explizite Quantor-Steuerung

**Einfach erklärt (Was ist überhaupt ein „Quantor“?):** Das Wort *Quantor* stammt aus der Logik und beantwortet beim Testen eine ganz einfache Alltagsfrage: **„Wie viele Punkte auf meiner Prüfliste müssen klappen, damit der Test gewonnen hat?“** Es gibt genau zwei Möglichkeiten:

* **`"all"` (der Allquantor $\forall$ — die UND-Checkliste):** Wie beim Sicherheitscheck vor einem Flugzeugstart muss **jeder einzelne Punkt** (`alle`) erfüllt sein (`Bedingung 1 UND Bedingung 2 UND ...`). Scheitert auch nur ein Punkt, ist der Check nicht bestanden.
* **`"exists"` (der Existenzquantor $\exists$ — die ODER-Auswahlliste):** Wie an einer Supermarktkasse, die *„Bargeld ODER EC-Karte ODER Kreditkarte“* akzeptiert, reicht es völlig aus, wenn **mindestens eine** Option (`existiert mindestens eine`) passt (`Option 1 ODER Option 2 ODER ...`).

Ohne besondere Angabe wendet Cubie zwei feste, **100 % reine Standardregeln** an:

* Für **`pre` (Eingaben)** gilt standardmäßig **`"all"` (Allquantor / UND)**: Jede angegebene Eingabe wird ausgeführt und muss den Test bestehen.
* Für **`post` (Erwartungen)** gilt standardmäßig **`"exists"` (Existenzquantor / ODER)**: Die Rückgabe muss zu mindestens einem der angegebenen Zielmuster passen.

> [!IMPORTANT]
> **Grundgesetz der Quantoren-Reinheit:** Die Standard-Quantoren (`pre="all"`, `post="exists"`) werden **niemals** heimlich durch ein `expect`-Flag überschrieben! Wenn du die Quantoren ändern möchtest (oder in `post` ein Verbot mit `WorldState(..., expect=False)` einsetzen willst), legst du den Quantor immer **explizit** über ein kleines Python-Dictionary mit den beiden Schlüsseln `"quantor"` (`"all"` oder `"exists"`) und `"states"` (ein einzelner `WorldState` oder eine Liste von `WorldState`-Objekten) fest.
```

#### AP 2.2: Abschnitt 2 — „Muster 1: Alle Bedingungen gleichzeitig erzwingen (`post` mit `"all"`)“ (Zeilen 33–68)
Ersetze den erklärenden Text vor dem Codeblock (Zeilen 33–36) und ergänze unter dem `<details>`-Block eine kurze Erklärung für Einsteiger und Experten (der Codeblock selbst in Z. 37–59 ist 23 Zeilen lang, bereits 100 % grün und bleibt exakt erhalten!):

```markdown
## 2. Muster 1: Alle Bedingungen gleichzeitig erzwingen (`post` mit `"all"`)

Mit `post={"quantor": "all", "states": [...]}` schaltest du `post` von der Standard-ODER-Auswahl auf eine **strikte UND-Checkliste** um. Das brauchst du in zwei typischen Situationen:

1. **Mehrere Eigenschaften gleichzeitig prüfen:** Ein Ergebnis soll mehrere Teilregeln auf einmal einhalten – zum Beispiel *„muss eine ganze Zahl (`int`) sein **UND** größer als `0` (`value > 0`) **UND** durch `2` teilbar (`value % 2 == 0`, also eine gerade Zahl)“*.
2. **Soll-Ziele mit Verboten (`expect=False`) kombinieren:** Weil `post` auf `"all"` steht, werden erlaubte Ziele (`expect=True`) und Verbote (`expect=False`) völlig einheitlich mit **UND** (`all(...)`) verknüpft: Jedes positive Muster muss zutreffen, und kein verbotenes Muster darf eintreten (siehe [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md)).

Im folgenden Beispiel verdoppelt `double(4)` die Zahl zu `8` und wird gegen alle drei UND-Bedingungen in `post` geprüft:
```
*(Direkt danach folgen unverändert der Codeblock `from qb_cubie import EBT, WorldState ...` und der `<details>`-Block aus Zeilen 37–67.)*

#### AP 2.3: Abschnitt 3 — „Muster 2: Alternative Eingabe-Routen erlauben (`pre` mit `"exists"`)“ (Zeilen 71–99)
Ergänze vor dem bestehenden Codeblock (Zeilen 75–90, 16 Zeilen, bereits 100 % grün) die anschauliche Einsteiger-Analogie:

```markdown
## 3. Muster 2: Alternative Eingabe-Routen erlauben (`pre` mit `"exists"`)

Mit `pre={"quantor": "exists", "states": [...]}` schaltest du die Eingabeseite von der Standard-UND-Pflicht auf eine **ODER-Auswahl** um.

* **Einfach erklärt (Notstrom-Prinzip):** Stell dir einen Server-Dienst mit einer Hauptleitung (`"/main"`) und einer Ersatzleitung (`"/backup"`) vor. Für die Verfügbarkeit des Systems reicht es, wenn **mindestens eine** der beiden Leitungen mit `"ok"` antwortet. Selbst wenn `"/main"` gerade `"offline"` liefert, besteht der Gesamtlauf, sobald `"/backup"` erfolgreich `"ok"` meldet:
```
*(Direkt danach folgen unverändert der Codeblock `from qb_cubie import EBT, WorldState ...` und der `<details>`-Block aus Zeilen 75–98.)*

#### AP 2.4: Abschnitt 4 — „Leitplanken, `STATE-GUARD`s, Lebenszyklus und Abgrenzung“ (Zeilen 102–111)
Ersetze Zeilen 102–111, sodass alle **neuen Core-`STATE-GUARD`s** sowie die **Sticky-Quantor-Lebenszyklus-Invariante** vollständig und leicht verständlich dokumentiert sind:

```markdown
## 4. Leitplanken, `STATE-GUARD`s, Lebenszyklus und Abgrenzung

Damit sich niemals fehlerhafte oder mehrdeutige Quantor-Konfigurationen in deine Tests einschleichen, prüft Cubie vor jedem Testlauf vier harte **`STATE-GUARD`-Leitplanken**:

| Leitplanke / `STATE-GUARD` | Was wird geprüft? | Fehlertyp bei Verstoß |
| :--- | :--- | :--- |
| **1. Wrapper-Struktur** | Das Dictionary darf ausschließlich die Schlüssel `"quantor"` (`"all"` oder `"exists"`, strikt `str`) und `"states"` (ein einzelner `WorldState` oder eine nichtleere `list[WorldState]`) enthalten. | `TypeError` / `ValueError` (`STATE-GUARD`) |
| **2. Verbot unter `post="exists"` & in `pre`** | Ein `WorldState(..., expect=False)` ist **nur** unter `post={"quantor": "all", ...}` zulässig. Unter `post="exists"` (Standard oder explizit) sowie in `pre` ist `expect=False` verboten. | `ValueError` (`STATE-GUARD`) |
| **3. Strikte `bool`-Prüfung auf `expect`** | `WorldState.expect` und `EBT.expect` akzeptieren ausschließlich `True` oder `False` (`type(val) is bool`). Werte wie `None`, `0`, `1` oder `"true"` werden abgewiesen. | `TypeError` (`STATE-GUARD`) |
| **4. Wiederverwendung & Sticky-Quantor-Reset** | Führst du dasselbe `EBT`-Objekt mehrfach mit `.run()` aus (oder änderst `case.post.append(...)` in-place), bleibt der deklarierte Quantor erhalten. Weist du `case.pre = ...` oder `case.post = ...` jedoch ohne Dict-Wrapper neu zu (z. B. `case.post = [ws1, ws2]`), setzt Cubie den Quantor automatisch auf den Standard (`pre="all"`, `post="exists"`) zurück. | Automatischer Reset in `_arrange()` |

> [!TIP]
> **Kontrolle im `RunTrace` und JSON-Bericht:** Welche Quantoren in einem Lauf tatsächlich wirksam waren, kannst du jederzeit nach `.run()` über `trace.pre_quantor` und `trace.post_quantor` (sowie in den JSON-Berichten des `JsonReporter`) ablesen.

Wichtig für die Abgrenzung zu den anderen Handbüchern:

* **`post` mit `"all"` ersetzt keine Paar-Zuordnung:** Alle Zustände in `post` gelten gemeinsam für *jeden* ausgeführten Eingang aus `pre`. Wenn zwei unterschiedliche Eingaben (`3` und `5`) unterschiedliche Rückgaben (`6` und `10`) verlangen, gehören sie weiterhin in getrennte Verträge oder in `@pytest.mark.parametrize` (siehe [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md)).
* **Erwartungssteuerung gezielt kombinieren:** Wie du in `post={"quantor": "all", ...}` positive Soll-Ziele und Verbote (`WorldState(..., expect=False)`) sicher kombinierst und die „einsame Negation“ (*Vacuous Pass*) vermeidest, beschreibt [Erwartungssteuerung & Safety (`expect`-Flags)](GUIDE_Expect-Flags.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).
```

---

### Arbeitspaket 3 (AP 3): [`docs/GUIDE_Contract-Design.md`](../docs/GUIDE_Contract-Design.md)

#### AP 3.1: Abschnitt 1 — Einsteiger-Erklärung zu Einzelverträgen & `@pytest.mark.parametrize` (Zeilen 22–104)
- Ergänze in Abschnitt 1 vor dem ersten Codeblock (Z. 24) eine kurze Einsteiger-Orientierung (*Was passiert bei `test_double_three()` und `test_double_five()`? Warum gibt `len(trace.traces)` genau `1` aus?*) und vor dem zweiten Codeblock (`### Saubere Skalierung mit @pytest.mark.parametrize`, Z. 65–68) eine einfache Erklärung für Python-Neulinge:
  ```markdown
  ### Saubere Skalierung mit `@pytest.mark.parametrize`

  **Einfach erklärt (für Einsteiger):** Wenn du nicht bloß zwei, sondern zehn Wertepaare testen willst, wäre es mühsam, zehnmal fast dieselbe `def test_double_...()`-Funktion untereinander zu kopieren. In `pytest` gibt es dafür den sogenannten **Decorator** `@pytest.mark.parametrize` (erkennbar am `@`-Zeichen über der Funktion). Er funktioniert wie eine automatische Stempelmaschine: Du gibst ihm die Namen der beiden Variablen (`"value, expected"`) und eine Liste von Paaren (`[(3, 6), (5, 10)]`). Pytest führt die Funktion `test_double` dann für jedes Paar **einzeln und komplett getrennt** aus – so erhältst du weiterhin genau `1` eindeutiges Prüfpaar pro Lauf:
  ```
  *(Direkt danach folgt unverändert der Codeblock aus Zeilen 69–103.)*

#### AP 3.2: Abschnitt 2 — „Anti-Pattern: Gedankenlose Quantoren-Kombination (Unterspezifikation)“ (Zeilen 107–145)
- Behalte den Codeblock (Zeilen 111–139) unverändert bei.
- **Korrigiere in Zeilen 141–145 die veraltete Formulierung (*„und die positiven Zustände in `post` wirken als Existenzquantor“*)** auf die reine Quantor-Semantik und ergänze das anschauliche Speisekarten-Bild für Einsteiger sowie den Hinweis auf Meta-Gate 2 für Experten:
  ```markdown
  Warum hier **4 statt 2 Paare** geprüft werden und warum dies ein **Anti-Pattern** ist, folgt direkt aus den reinen Standard-Quantoren von `EBT` (siehe [Vertragssemantik](GUIDE_Contract-Semantics.md#endliche-auswertungsregel)):

  * **Einfach erklärt (Die Speisekarten-Verwechslung):** Stell dir vor, zwei Gäste bestellen im Restaurant: Gast 1 bestellt für Eingabe `3` (erwartet Gericht `6`), Gast 2 bestellt für Eingabe `5` (erwartet Gericht `10`). Wenn du beide Bestellungen `[3, 5]` in `pre` und beide Gerichte `[6, 10]` gemeinsam in `post` wirfst, weiß Cubie **nicht**, welches Gericht zu welchem Gast gehört! Stattdessen legt Cubie beiden Gästen einfach die gemeinsame Speisekarte `{6, 10}` hin und prüft für jeden Gast nur: *„Stand das servierte Gericht irgendwo auf der Karte?“* Selbst wenn die Küche die Teller komplett vertauscht (`3 -> 10` und `5 -> 6`) oder jedem Gast stur `6` hinstellt (`return 6`), steht `6` auf der Karte – und der Test wird trotz kaputter Küche **grün**!
  * **Technisch & formal (Kartesisches Kreuzprodukt $N \times M$):** Standardmäßig wirkt `pre` als **reiner Allquantor (`"all"`, *für jede Eingabe*)** und `post` als **reiner Existenzquantor (`"exists"`, *muss mindestens eines der Zielmuster aus `post` passen*)**. `EBT` bildet daher das Kreuzprodukt aus allen `pre`- und `post`-Einträgen und prüft sowohl `3` als auch `5` jeweils gegen `6` **und** gegen `10` ($2 \times 2 = 4$ Vergleiche in `trace.traces`, Formel: $\forall p \in \text{pre} : \exists q \in \text{post} : \text{match}(p, q)$).
  * **Automatischer Schutz in der Cubie-Suite (Meta-Gate 2):** In Cubies eigener Test-Suite erkennt der statische Syntaxbaum-Wächter **`META-EBT-CROSS-PRODUCT`** (`tests/tests_meta/test_gate_2.py`) solche unbegründeten $N \times M$-Kreuzprodukte (`len(pre) > 1` und `len(post) > 1` unter `post="exists"`) automatisch.
  ```

#### AP 3.3: Abschnitt 3 — „Wann mehrere Eingänge in einen Vertrag gehören“ & Weiterführender Tipp (Zeilen 148–183)
- Ergänze vor dem `normalize`-Codeblock (Z. 150) eine kurze Einsteiger-Erklärung zum Begriff **Äquivalenzklasse** und zu `text.strip().lower()` (*„Alle drei Eingaben `' TEXT '`, `'text'` und `'TeXt'` gehören in dieselbe Gruppe (Äquivalenzklasse), weil bei allen dreien am Ende exakt dasselbe Wort `'text'` herauskommen muss. In Python schneidet `.strip()` die Leerzeichen am Rand ab und `.lower()` macht alle Buchstaben klein.“*).
- Aktualisiere den `[!TIP]`-Kasten in Zeilen 181–182 auf die explizite `"quantor": "all"`-Pflicht bei `expect=False`:
  ```markdown
  > [!TIP]
  > **Weiterführende Handbücher:** Wie du erwartete Soll-Ziele und verbotene Ergebnisse (`expect=False`) innerhalb eines konjunktiven `post={"quantor": "all", ...}`-Vertrags kombinierst, erklärt [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md). Wie du die Standard-Quantoren `"all"` und `"exists"` gezielt umdrehst, zeigt [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md). Zurück zur Gesamtübersicht geht es im [QA-Handbuch](GUIDE_Quality-Assurance.md).
  ```

---

### Arbeitspaket 4 (AP 4): [`docs/GUIDE_Quality-Assurance.md`](../docs/GUIDE_Quality-Assurance.md)

#### AP 4.1: Abschnitt 1 — Grundkurs & die drei Grundbausteine A, B, C + Spickzettel (Zeilen 41–116)
1. **Grundkurs (nach dem `<details>`-Block von `double(3) -> 6` in Zeile 69):**
   Ergänze eine kompakte, einsteigerfreundliche Aufschlüsselung des ersten Codebeispiels, damit absolute Programmier-Neulinge sofort abgeholt werden:
   ```markdown
   **Kurz erklärt für Programmier- und Python-Einsteiger:**
   * **`def double(x: int) -> int:`** definiert in Python eine **Funktion** (wie eine kleine Küchenmaschine): Oben wirfst du eine ganze Zahl `x` (`int`) hinein, drinnen rechnet sie `x * 2`, und mit **`return`** gibt sie das fertige Ergebnis zurück.
   * **`WorldState(...)`** ist dein **Wunschzettel (Zustandsbeschreibung)**: In **`pre=WorldState(args=3)`** steht, welches Argument (`args=3`) wir oben in die Funktion hineinstecken. In **`post=WorldState(returns=6)`** steht, welchen Rückgabewert (`returns=6`) wir unten erwarten.
   * **`EBT(...).run()`** führt den Vertrag aus und gibt das Prüfprotokoll **`trace`** zurück. Darin zeigt **`trace.evaluation`** als Wahrheitswert (`True` = bestanden, `False` = durchgefallen), ob der Vertrag eingehalten wurde.
   ```
2. **Baustein B (`expect`-Flags, Zeilen 81–91):**
   Präzisiere Punkt 1 und die `[!CAUTION]`-Box auf die reparierte Core-Semantik:
   ```markdown
   ### Baustein B: Erlaubtes und Verbotenes steuern (`expect`-Flags)

   Standardmäßig bedeutet `expect=True`: *„Genau das soll passieren.“* Mit `expect=False` (strikt `bool`: `True` oder `False`) kannst du gezielt sagen, was **nicht** passieren darf – und zwar auf zwei klar getrennten Ebenen, ohne dass jemals ein Quantor heimlich überschrieben wird:

   1. **Auf einem `WorldState` in `post` (Verbot unter `"quantor": "all"`):** Du legst fest, was herauskommen muss (`expect=True`), und verbietest gleichzeitig gefährliche Werte (`expect=False`, z. B. negative Preise). Weil Soll-Ziel **und** Verbot gleichzeitig gelten müssen (UND-Checkliste), stehen solche Zustände immer in **`post={"quantor": "all", "states": [...]}`**. Im Standard-ODER-Modus (`post="exists"`) sowie in `pre` blockiert Cubies `STATE-GUARD` jedes `WorldState(..., expect=False)` sofort mit einem `ValueError`.
   2. **Auf `EBT(..., expect=False)` (Gegenprobe auf Vertragsebene):** Du kehrst das fertige Gesamtergebnis des gesamten Vertrags am Ende um. So beweist du in der Red-Phase, dass dein Soll-Vertrag bei einem bekannten Fehler tatsächlich anschlägt.

   > [!CAUTION]
   > **Vorsicht vor der „einsamen Negation“ (*Vacuous Pass*):** Selbst wenn du `post={"quantor": "all", "states": [...]}` nutzt, darfst du darin nicht *nur* Verbote (`expect=False`) ohne mindestens ein positives Soll-Ziel (`expect=True`) angeben. Sonst schlüpfen völlig falsche Rückgaben (wie `None`, also „Nichts“) unbemerkt grün durch, bloß weil sie technisch gesehen nicht der eine verbotene Wert sind.

   👉 **Alle Muster, Reparatur-Beispiele und `STATE-GUARD`-Regeln:** [Erwartungssteuerung & Safety (`expect`-Flags)](GUIDE_Expect-Flags.md)
   ```
3. **Baustein C (`all` vs. `exists`, Zeilen 93–105):**
   Schärfe die Standardregeln auf reine Quantoren (ohne das Wort *„erlaubtes“*, das die alte $Q^+$/$Q^-$-Spaltung implizierte) und ergänze die Einsteiger-Intuition (UND-Checkliste vs. ODER-Auswahlliste):
   ```markdown
   ### Baustein C: „Alle“ oder „mindestens eines“ gezielt wählen (`all` vs. `exists`)

   Ohne besondere Angabe arbeitet Cubie nach zwei **reinen Standardregeln**, die durch kein `expect`-Flag heimlich verändert werden:

   * In **`pre`** gilt der **reine Allquantor (`"all"` — die UND-Checkliste)**: **Alle** angegebenen Eingänge müssen bestehen.
   * In **`post`** gilt der **reine Existenzquantor (`"exists"` — die ODER-Auswahlliste)**: Es reicht, wenn **mindestens ein** angegebenes Zielmuster passt.

   Wenn du es andersherum brauchst (oder in `post` ein Verbot mit `expect=False` kombinierst), verpackst du die Zustände explizit in das Dictionary `{"quantor": ..., "states": ...}`:

   * **`post` mit `"all"` (UND-Checkliste):** Das Ergebnis muss **alle** Regeln gleichzeitig erfüllen (z. B. *eine ganze Zahl **und** positiv **und** nicht `-10`*).
   * **`pre` mit `"exists"` (ODER-Auswahlliste):** Es genügt, wenn **mindestens eine** von mehreren Eingabe-Routen zum Erfolg führt (z. B. Hauptleitung `/main` **oder** Ersatzleitung `/backup` antwortet mit `"ok"`).

   👉 **Alle Code-Beispiele, `STATE-GUARD`-Regeln und Lebenszyklus-Details:** [Fortgeschrittene Quantoren (`all` vs. `exists`)](GUIDE_Quantifiers.md)
   ```
4. **Spickzettel für den Einstieg (Zeile 112):**
   Aktualisiere Zeile 112 in der Tabelle auf:
   ```markdown
   | Soll-Wert fordern und gefährliche Werte verbieten | `post={"quantor": "all", "states": [WorldState(..., expect=True), WorldState(..., expect=False)]}` | [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md) |
   ```

#### AP 4.2: Abschnitt 2 — Charakterisierung ($Q_{\text{Ist}}$) vs. Spezifikation ($Q_{\text{Soll}}$) (Zeilen 120–131)
Ergänze für Einsteiger ein greifbares Bild der Symbole $Q_{\text{Ist}}$ und $Q_{\text{Soll}}$ sowie den Bezug zur realen Reparatur des Cubie-Cores:

```markdown
## 2. Die gefährlichste Falle der Qualitätssicherung: Charakterisierung ( $Q_{\text{Ist}}$ ) vs. Spezifikation ( $Q_{\text{Soll}}$ )

Eine der wichtigsten Erfahrungen aus der praktischen Arbeit mit Test-Suiten – gerade nach explorativen Analysen – betrifft den Unterschied zwischen **Beobachtung ( $Q_{\text{Ist}}$ )** und **Gesetz ( $Q_{\text{Soll}}$ )** sowie den Grundsatz: **Ein einmal richtig auf $Q_{\text{Soll}}$ eingestellter Prüffall wird in der Green-Phase nicht mehr manipuliert.**

* **Einfach erklärt ($Q_{\text{Ist}}$ vs. $Q_{\text{Soll}}$):**
  * **$Q_{\text{Ist}}$ (Das Foto vom Tatort / Charakterisierung):** Beschreibt, was der Code im Moment *tatsächlich tut* – inklusive seiner Fehler und Eigenheiten.
  * **$Q_{\text{Soll}}$ (Der Bauplan / Spezifikation):** Beschreibt, was der Code *eigentlich tun muss*, damit er fachlich und logisch korrekt arbeitet.
  * **Die Falle:** Wenn man bestehenden Code ausprobiert und das beobachtete Ergebnis ($Q_{\text{Ist}}$) blind mit dem Standard `expect=True` in einen Test kopiert, obwohl darin ein Bug steckt, verteidigt der Test ab sofort den Bug!

Die Folgen eines solchen Fehlers in der Test-Suite sind gravierend:

* **Falscher Erfolg (False Positive):** Die Test-Suite leuchtet komplett grün (`PASSED`), obwohl der Defekt mitten im System steckt.
* **Blockierte Reparatur:** Sobald jemand den Bug im Produktionscode beheben will, schlägt der fehlerhaft auf $Q_{\text{Ist}}$ eingestellte Test rot fehl, weil er das alte Fehlverhalten erzwingt. (Genau das zeigte sich auch bei der Härtung des Cubie-Cores: Mehrere ältere Tests hatten sich darauf verlassen, dass `WorldState(expect=False)` im Standard-`post` heimlich den Existenzquantor überschreibt – erst die Umstellung dieser Tests von der fehlerhaften $Q_{\text{Ist}}$-Gewohnheit auf die explizite $Q_{\text{Soll}}$-Deklaration `post={"quantor": "all", ...}` machte den Weg für die Core-Reparatur frei.)
```

#### AP 4.3: Abschnitt 3 — „Test-Guided Development (TGD) in fünf Schritten“ (Zeilen 133–154) — **Spiegelung der realen TGD-Phasen aus den letzten Commits**
Überarbeite Abschnitt 3 so, dass die 5 TGD-Schritte erhalten bleiben, aber die **in den jüngsten Commits (`db96ea4b` $\to$ `740f3134` $\to$ `905e0a06` $\to$ `d4ea5c1b` $\to$ `25730b6d`) praktisch veranschaulichten TGD-Phasen** (Analyse & Meta-QA-Hypothesen $\to$ Adapter & Äquivalenzklassen $\to$ isolierte Red-Phase mit Test-Freeze $\to$ Green-Phase mit Eskalationsprotokoll statt Test-Manipulation $\to$ Living-Documentation-Sync über `DocEnsurance`) sowohl für Einsteiger als auch für Experten lebendig und praxisnah dargestellt werden:

```markdown
## 3. Test-Guided Development (TGD) in fünf Schritten

Test-Guided Development (TGD) erweitert klassisches Test-Driven Development (TDD) um explorative System-Audits, formale Meta-QA-Prüffragen an die Test-Suite selbst und die strikte Trennung orthogonaler Prüf-Schichten (`tests/` $\to$ `src/` $\to$ `docs/`). Die jüngste Reparatur der Quantoren-Semantik im Cubie-Core veranschaulicht diesen fünfstufigen Ablauf in der Praxis:

### Schritt 1: Baseline, Exploratives Audit & Meta-QA-Hypothesenbildung (`ANALYSIS` & `HYPOTHESIS`)
Bevor eine einzige Zeile Code oder Test geändert wird, wird der Ist-Zustand ($Q_{\text{Ist}}$) gegen das gewünschte Architektur-Gesetz ($Q_{\text{Soll}}$) vermessen und in überprüfbare Hypothesen überführt:
* **Einfach erklärt:** Erst Detektivarbeit leisten und einen klaren Reparaturplan aufstellen, statt blind im Code herumzuprobieren.
* **Für Experten (Meta-QA-Fragen an die Test-Suite):** Prüfe bestehende und geplante Tests vorab auf **logische Subsumtion** ($Q_{\text{pos}} \implies \neg Q_{\text{neg}}$, bei der ein positives Ziel das Verbot bereits impliziert und das Verbot dadurch ungetestet bleibt), **prädikatenlogische Tautologien** (wie $(y \in \mathbb{Z}) \lor (y \neq 99) \equiv \top$ unter `post="exists"`), **Vacuous Passes** (`0pos/Kneg`) und **überlebende Core-Mutanten** (schlägt wirklich ein Test fehl, wenn eine Kernfunktion wie `evaluate_step_logic()` ungefixt bleibt?).

### Schritt 2: Schlanke, zustandsfreie Test-Adapter (`Stateless Adapters`)
Wenn das zu prüfende Subsystem komplexe Report-Objekte mit vielen internen Feldern zurückgibt, sollte der Test nicht an irrelevanten Implementierungsdetails kleben.
* **Einfach erklärt:** Schreibe eine winzige Hilfsfunktion (5–12 Zeilen), die das komplexe Ergebnis auf ein kleines, übersichtliches Python-Dictionary mit den wirklich wichtigen Eckdaten zusammenfasst (z. B. `{"passed": report.passed, "rules": [d.rule_id for d in report.diagnostics]}`). Dadurch bleiben die `WorldState`-Definitionen im `EBT`-Aufruf kurz und auf einen Blick lesbar.

### Schritt 3: Äquivalenzklassen, Kantenfälle & Lebenszyklus-Invarianten statt Daten-Flut
Zwanzig fast identische Gutwetter-Tests erhöhen nur die Laufzeit, aber nicht die Sicherheit. Entscheidend ist die gezielte Abdeckung der fachlichen Äquivalenzklassen und Zustandsübergänge:
* **Positiv-Invarianz & Schwellenwerte (Off-by-One):** Repräsentative Normalfälle sowie exakte Grenzwerte (z. B. $19$ vs. $20$ Zeichen oder $30$ vs. $31$ Codezeilen).
* **Explizite `STATE-GUARD`s & Python-Typfallen:** Ungültige Konfigurationen müssen vor der Target-Ausführung mit `ValueError` oder `TypeError` (`match="STATE-GUARD"`) abgewiesen werden. Beachte dabei Python-Besonderheiten wie `issubclass(bool, int) is True`: Ein echter `bool`-Guard prüft `type(val) is bool`, damit Zahlen wie `1` oder `0` sowie `None` nicht durchrutschen.
* **Lebenszyklus- & Mutations-Übergänge:** Wenn Objekte wiederverwendet werden (wie ein `EBT`-Fall über mehrere `.run()`-Aufrufe), prüfe den gesamten Zyklus: (1) zweiter Lauf *ohne* Neuzuweisung (Quantor bleibt erhalten), (2) In-Place-Listenmutation `case.post.append(...)` bzw. Attribut-Mutation `ws.expect = False`, und (3) Attribut-Neuzuweisung `case.post = [...]` ohne Wrapper (Quantor springt sauber auf den Standard `"exists"` bzw. `"all"` zurück).

### Schritt 4: TGD Red-Phase — Test-Suite isoliert schärfen, Red-Nachweis führen & Tests einfrieren
In der Red-Phase wird **ausschließlich `tests/`** bearbeitet (`src/` und `docs/` bleiben unangetastet):
1. **Altlasten ($Q_{\text{Ist}}$) und Meta-Gates bereinigen:** Bestehende Tests, die versehentlich altes Fehlverhalten voraussetzen, werden auf die saubere $Q_{\text{Soll}}$-Deklaration (z. B. `post={"quantor": "all", "states": [...]}`) migriert; statische Wächter (`test_gate_2.py`, `test_gate_3.py`) werden nach der Wächter-Kalibrierungs-Triade (Clean-Probes, Fault-Probes, Repo-Scan) aktualisiert. Alle migrierten Bestands-Tests müssen bereits gegen den aktuellen Core **100 % grün (`PASSED`)** laufen.
2. **Gezielter Red-Nachweis für neue Verträge:** Die neuen Guard-, Invarianten- und Lebenszyklus-Tests werden hinzugefügt und müssen gegen den noch unreparierten Core deterministisch **rot fehlschlagen (`FAILED`)** – das beweist, dass die neuen Tests scharf geschaltet sind und keinen überlebenden Mutanten dulden.
3. **Strikter Test-Freeze:** Sobald dieses exakte Differenzsignal (Bestand grün, neue Verträge kontrolliert rot) steht, wird die Test-Suite **eingefroren**.

### Schritt 5: TGD Green-Phase & Living-Documentation-Sync — Core reparieren & alle Schichten synchronisieren
In der Green-Phase wird zunächst **ausschließlich der Produktionscode in `src/`** repariert:
* **Unantastbarkeit der Tests & Eskalations-Protokoll (`GREEN_AUDIT`):** Während der Core-Reparatur gilt ein striktes Änderungsverbot auf `tests/**/*.py` (keine Edits, kein `skip`, kein Abschwächen von Assertions). Taucht unterwegs der begründete Verdacht auf, dass sich in der Red-Phase ein Denkfehler oder Widerspruch in einen Test eingeschlichen hat, wird der Test **nicht** heimlich umgeschrieben, sondern ein strukturierter Befundbericht (z. B. `tests/GREEN_AUDIT.md`) mit Zeilennummer, Reproduktionsbeleg und Klärungsvorschlag angelegt.
* **Code-Härtung unter Stil-Gates:** Der Core wird innerhalb der harten Architektur-Grenzen (`MODULE_LIMIT = 777` Zeilen, `FUNCTION_LIMIT = 12` physische Body-Zeilen, einzeilige Docstrings, `0` Fehler in `ruff`, `pylint` und `mypy --warn-unreachable`) repariert, bis alle zuvor roten Tests auf **`PASSED`** springen.
* **Living-Documentation-Sync (`DocEnsurance`):** Sobald ein neuer `STATE-GUARD` im Core scharf geschaltet ist, meldet sich automatisch die vierte orthogonale Schicht (`tests/test_styleguide.py::test_docs_code_examples`) und zeigt auf jedes Code-Beispiel in `docs/`, das noch veraltete Muster nutzt. Erst wenn auch die Handbücher aktualisiert sind und `pytest` über alle Schichten (`EBT`, `Meta-Gates`, `Linter`, `DocEnsurance` / `DocFrame`) komplett grün läuft, ist der TGD-Zyklus abgeschlossen.
```

#### AP 4.4: Abschnitt 4 (Hoare-Analogie, Zeile 162) & Abschnitt 5 (Empfehlung 1, Zeile 173)
1. **Zeile 162 (Hoare-Analogie $\{P\}\ S\ \{Q\}$):**
   Ersetze den zweiten und dritten Satz durch die reine Quantor-Definition inklusive Einsteiger-Erklärung:
   ```markdown
   * **Die Hoare-Analogie $\{P\}\ S\ \{Q\}$ als Strukturmodell:** Die Anordnung `pre` ( $\{P\}$: *Was stecken wir vorher hinein?* ), `target` ( $S$: *Welche Funktion führen wir aus?* ) und `post` ( $\{Q\}$: *Was muss nachher herauskommen?* ) in `EBT` ist eine bewusste architektonische und didaktische Analogie zum Hoare-Tripel der Informatik. Ein `WorldState` ist dabei ein konkreter Datensatz oder ein Prädikat-Muster, und die Auswertung prüft endliche, explizite Zustandslisten nach reinen Quantoren: Standardmäßig muss jeder ausgeführte Eingang aus `pre` (`pre_quantor="all"`, UND) mindestens einen Zielzustand aus `post` (`post_quantor="exists"`, ODER) erfüllen. Über `{"quantor": "all" | "exists", "states": ...}` lassen sich beide Quantoren explizit umschalten, wobei Verbote (`WorldState(..., expect=False)`) ausschließlich unter `post={"quantor": "all", ...}` zulässig sind. Alle Details regelt die [Vertragssemantik](GUIDE_Contract-Semantics.md).
   ```
2. **Zeile 173 (Herzliche Empfehlungen, Punkt 1):**
   Präzisiere Punkt 1 auf `post={"quantor": "all", ...}` und das Green-Phase-Eskalationsprinzip:
   ```markdown
   1. **Einmal richtig eingestellte Prüffälle sind in der Green-Phase unantastbar:** Ein in der Red-Phase auf $Q_{\text{Soll}}$ fixierter Prüffall wird während der Code-Reparatur niemals manipuliert (bei einem vermuteten Test-Widerspruch wird stattdessen ein transparenter Audit-Befund dokumentiert). Und falls vorab ein alter explorativer Test auffällt, der ein Fehlersymptom versehentlich als gültig (`expect=True`) aufgezeichnet hat, dreht man dieses Symptom mit `WorldState(..., expect=False)` um und kombiniert es mit dem positiven Soll-Ziel in `post={"quantor": "all", "states": [...]}` (oder negiert den gesamten Lauf über `EBT(..., expect=False)`).
   ```

---

## 4. Detaillierte Arbeitspakete für die 6 identifizierten weiteren Dokumente (AP 5 – AP 7)

---

### Arbeitspaket 5 (AP 5): [`docs/GUIDE_EBT-Usage-Pattern.md`](../docs/GUIDE_EBT-Usage-Pattern.md) — **LIVE-FIX #4**

> [!IMPORTANT]
> **Warum AP 5 zwingend erforderlich ist:**
> In `docs/GUIDE_EBT-Usage-Pattern.md:147-169` steht das **4. aktuell crashende Live-Code-Snippet**, das `test_docs_code_examples` mit `ValueError: STATE-GUARD: post[2].expect=False is forbidden under post_quantor='exists'` zum Scheitern bringt!

#### AP 5.1: Abschnitt „Erlaubte und verbotene Ergebnisse“ (Zeilen 143–186) — **LIVE-FIX #4**
- **Analyse des bisherigen Snippets (Z. 147–169):**
  Bisher stand dort `post=[WorldState(returns="OK"), WorldState(returns="WARN"), WorldState(returns="ERROR", expect=False)]`.
  - Unter `post="exists"` (ODER) ist `expect=False` durch den `STATE-GUARD` verboten.
  - Unter `post="all"` (UND) könnten `returns="OK"` und `returns="WARN"` niemals gleichzeitig wahr sein (`"OK" != "WARN"`).
  - Die saubere Lösung: Das Beispiel zeigt im selben `test_status()`-Snippet (25 Zeilen $\le 30$) **beide** Muster klar getrennt:
    1. **Erlaubte Alternativen unter Standard-`post` (`"exists"`, ODER):** `post=[WorldState(returns="OK"), WorldState(returns="WARN")]`.
    2. **Positives Typ-/Bereichsziel plus explizites Verbot unter `post={"quantor": "all", ...}` (UND):** `post={"quantor": "all", "states": [WorldState(returns=str), WorldState(returns="ERROR", expect=False)]}`.
- **Drop-in-Ersatz für Zeilen 143–186 in `docs/GUIDE_EBT-Usage-Pattern.md`:**

````markdown
## Erlaubte Alternativen und verbotene Ergebnisse

Für mehrere erlaubte Ergebnis-Alternativen (wie `"OK"` **oder** `"WARN"`) nutzt `post` standardmäßig den reinen Existenzquantor (`"exists"`, ODER-Verknüpfung). Soll dagegen ein positives Zielmuster mit einem expliziten Verbot (`WorldState(..., expect=False)`) kombiniert werden, müssen beide Bedingungen gleichzeitig gelten und werden deshalb in `post={"quantor": "all", "states": [...]}` (Allquantor, UND-Verknüpfung) gebündelt:

```python
from qb_cubie import EBT, WorldState


def choose_status():
    return "OK"


def test_status():
    # 1. Standard post="exists" (ODER): Mindestens eine erlaubte Alternative passt
    EBT(
        target=choose_status,
        post=[WorldState(returns="OK"), WorldState(returns="WARN")],
    ).run()

    # 2. Explizites post="all" (UND): Muss ein String sein UND darf nicht "ERROR" sein
    EBT(
        target=choose_status,
        post={
            "quantor": "all",
            "states": [
                WorldState(returns=str),
                WorldState(returns="ERROR", expect=False),
            ],
        },
    ).run()


if __name__ == "__main__":
    test_status()
    print("OK")
```

<details>
<summary>Ergebnis</summary>

```text
OK
```
</details>

Im Standard-Modus (`post_quantor="exists"`) sind ausschließlich positive Zielmuster (`expect=True`) zulässig; ein `WorldState(..., expect=False)` unter `post="exists"` oder in `pre` wird vor der Target-Ausführung durch einen `STATE-GUARD` (`ValueError`) abgewiesen. Unter `post={"quantor": "all", ...}` sollte jedes Verbot (`expect=False`) mit mindestens einem positiven Soll-Muster (`expect=True`) verankert werden, damit nicht beliebige falsche Typen (wie `None`) durch einen *Vacuous Pass* bestehen.

Bei mehreren `pre`- und `post`-Einträgen gilt dieselbe gesamte Zielmenge für jeden Eingang. Ein gemeinsames `post` für die Werte `2` und `4` erlaubt auch eine Vertauschung. Es entsteht keine Zuordnung nach Listenposition.

Das gleiche Prinzip kann einen beobachteten Würfelwert über `post={"quantor": "all", "states": [WorldState(returns=int), WorldState(returns=lambda v: 1 <= v <= 6)]}` (oder sechs positive Alternativen `1` bis `6` unter `post="exists"`) auf den Bereich `1` bis `6` beschränken. Eine konstante Rückgabe innerhalb dieses Bereichs besteht ebenfalls. Alle möglichen Ergebnisse, Zufälligkeit und Verteilung sind damit nicht geprüft.

`EBT(expect=False)` negiert dagegen das fertige Gesamtergebnis auf Vertragsebene (`expect` akzeptiert auf `WorldState` und `EBT` strikt nur `bool`). Es prüft keine erwartete Exception; Target-Ausnahmen propagieren weiterhin.
````

#### AP 5.2: Abschnitt „Explizite Quantor-Deklaration (`all` und `exists`)“ (Zeilen 187–255)
1. **Zeilen 189–191:** Entferne die veraltete Einschränkung *„für positive Zustände“* und präzisiere die Homogenität unter `"all"`:
   ```markdown
   Standardmäßig verwendet `pre` den reinen Allquantor (`"all"`, alle Eingänge müssen bestehen) und `post` den reinen Existenzquantor (`"exists"`, mindestens ein Zielmuster muss zutreffen). Über ein Wrapper-Dictionary `{"quantor": "all" | "exists", "states": ...}` lässt sich diese Quantor-Semantik explizit festlegen – sowohl für eine Liste von `WorldState`-Objekten als auch für einen einzelnen `WorldState`.

   Mit `post={"quantor": "all", ...}` müssen **alle** deklarierten Ziel-Bedingungen gleichzeitig erfüllt sein (UND-Verknüpfung); positive Zustände (`expect=True`) müssen zutreffen und eingestreute Verbote (`expect=False`) dürfen nicht zutreffen:
   ```
2. **Zeile 254:** Ergänze die neuen `STATE-GUARD`s und den Sticky-Quantor-Reset:
   ```markdown
   Das Wrapper-Dictionary akzeptiert ausschließlich die Schlüssel `"quantor"` (`"all"` oder `"exists"`) und `"states"` (ein einzelner `WorldState` oder eine nichtleere Liste von `WorldState`-Objekten). Ungültige Schlüssel, unbekannte Quantoren, leere `"states"`-Listen, nicht-boolesche `expect`-Werte (`TypeError`) sowie `WorldState(..., expect=False)` in `pre` oder unter `post="exists"` (`ValueError`) lehnt der `STATE-GUARD` vor jeder Target-Ausführung ab. Bei wiederholten `.run()`-Aufrufen auf derselben `EBT`-Instanz bleiben explizit deklarierte Quantoren erhalten, bis `case.pre` oder `case.post` ohne Dict-Wrapper neu zugewiesen wird (Reset auf `pre="all"` bzw. `post="exists"`). Die wirksamen Quantoren werden als `pre_quantor` und `post_quantor` im `RunTrace` sowie im JSON-Bericht des `JsonReporter` gespeichert.
   ```

---

### Arbeitspaket 6 (AP 6): [`docs/GUIDE_Contract-Semantics.md`](../docs/GUIDE_Contract-Semantics.md) — **Single Source of Truth synchronisieren**

> [!IMPORTANT]
> **Warum AP 6 kritisch ist:**
> Alle anderen Handbücher verweisen für die verbindlichen Auswertungsregeln auf `docs/GUIDE_Contract-Semantics.md`. Aktuell fehlt dort in der Begriffs-Tabelle und in der *Endlichen Auswertungsregel* noch das `{"quantor": ..., "states": ...}`-Interface, und Zeilen 51–62 schreiben noch die abgeschaffte $Q^+$/$Q^-$-Sonderformel vor!

#### AP 6.1: Tabelle „Begriffe und Felder“ (Zeilen 23–32)
Aktualisiere die 6 Zeilen `EBT-Vertrag`, `pre`, `post`, `post.expect=True`, `post.expect=False` und `EBT(expect=False)` in der Tabelle:

```markdown
| EBT-Vertrag | Endliche Menge konkreter Ausführungen mit quantifizierten Eingängen (`pre_quantor`, Standard `"all"`) und gemeinsamen Zielmustern (`post_quantor`, Standard `"exists"`). Kein Korrektheitsbeweis. |
| `WorldState` | Veränderliche Dataclass mit `args`, `kwargs`, `arena`, `fs`, `returns`, `expect` (strikt `bool`), `raises`, `exception`. Kein allgemein bewiesenes Zustandsprädikat und keine eingefrorene Momentaufnahme. |
| `pre` | Ein `WorldState`, eine nichtleere Liste davon, `None` (wird zu `[WorldState()]`) oder ein Quantor-Dictionary `{"quantor": "all" \| "exists", "states": ...}` (Standard-Quantor: `"all"`). Für jeden Eintrag wird das Target einmal aufgerufen. `[]`, unbekannte Wrapper-Schlüssel/-Quantoren oder `pre[i].expect=False` führen zu `ValueError("STATE-GUARD: ...")`; ungültige Typen und Listeneinträge zu `TypeError("STATE-GUARD: ...")`. |
| `post` | Ein `WorldState`, eine nichtleere Liste gemeinsamer Zielmuster, `None` (wird zu `[WorldState()]`) oder `{"quantor": "all" \| "exists", "states": ...}` (Standard-Quantor: `"exists"`). Es gibt keine Inferenz von `post=42` zu `WorldState(returns=42)`. |
| `args` | `None` ergibt keine Positionsargumente. Listen und Tupel werden in Positionsargumente entpackt; andere Objekte werden als ein Argument übergeben. `args=[1, 2]` ruft `f(1, 2)` auf; `args=([1, 2],)` ruft `f([1, 2])` auf; `args=(None,)` ruft `f(None)` auf. |
| `kwargs` | Ein Dictionary mit Schlüsselwortargumenten; `None` wird zu `{}`. Andere Werte führen zu `TypeError`. |
| `post.returns` | Erwarteter Rückgabewert oder Muster. Ausgelassen oder `qb_cubie.UNSPECIFIED` bedeutet „nicht prüfen“; explizites `None` erwartet den Wert `None`. |
| `post.expect=True` | Gefordertes/erlaubtes Zielmuster (`sat(p, q) = match(p, q)`). Alle in diesem Zustand aktivierten Prüfungen müssen passen. `expect` muss strikt `bool` (`True`/`False`) sein (`TypeError("STATE-GUARD: ...")` bei `None`, `int`, etc.). |
| `post.expect=False` | Verbotenes Zielmuster (`sat(p, q) = not match(p, q)`). **Ausschließlich unter `post={"quantor": "all", ...}` zulässig**; unter `post_quantor="exists"` (implizit oder explizit) sowie in `pre` wird `expect=False` vor der Target-Ausführung mit `ValueError("STATE-GUARD: ...")` abgewiesen. |
| `EBT(expect=False)` | Negiert das nach `pre_quantor` und `post_quantor` fertig aggregierte Gesamtergebnis aller Eingangsschritte (`expect` strikt `bool`, sonst `TypeError("STATE-GUARD: ...")`). Erwartet weder eine Exception noch das Scheitern jedes einzelnen Schritts. |
```

#### AP 6.2: Abschnitt „Endliche Auswertungsregel“ (Zeilen 49–66)
Ersetze Zeilen 49–66 durch die reparierte, einheitliche Quantor-Formel inklusive einer klaren Einsteiger-Zusammenfassung und der `STATE-GUARD`-Invarianten:

```markdown
## Endliche Auswertungsregel

Seien `P` die nichtleere Liste der deklarierten Eingänge (`pre` mit `pre_quantor` $\in \{\text{"all"}, \text{"exists"}\}$, Standard `"all"`) und `Q` die nichtleere Liste der Zielmuster (`post` mit `post_quantor` $\in \{\text{"all"}, \text{"exists"}\}$, Standard `"exists"`). `match(p, q)` (`EvaluationTrace.evaluation`) bedeutet: Das bei der Ausführung von `p` beobachtete Ergebnis erfüllt alle in `q` aktivierten Vergleiche (`diffs is None`).

Vor der Ausführung stellt der `STATE-GUARD` sicher, dass alle `expect`-Flags strikt vom Typ `bool` sind (`TypeError`), für alle $p \in P$ stets `p.expect is True` gilt (`ValueError`) und unter `post_quantor == "exists"` für alle $q \in Q$ ebenfalls `q.expect is True` gilt (`ValueError`).

Für jeden Eingang $p \in P$ und jedes Zielmuster $q \in Q$ gilt:

```text
sat(p, q)     = match(p, q),       falls q.expect is True
                NICHT match(p, q), falls q.expect is False  (nur unter post_quantor="all" zulässig)

schritt_ok(p) = mindestens ein q aus Q erfüllt sat(p, q), falls post_quantor == "exists"
                alle q aus Q erfüllen sat(p, q),          falls post_quantor == "all"

lauf_ok       = alle schritt_ok(p) für p aus P,           falls pre_quantor == "all"
                mindestens ein schritt_ok(p) für p aus P, falls pre_quantor == "exists"

evaluation    = lauf_ok, falls EBT.expect is True, sonst NICHT lauf_ok
```

**Einfach zusammengefasst (für Einsteiger & Alltag):**
* **Im Standardfall (`pre="all"`, `post="exists"`):** Für **jede** Eingabe in `pre` (UND) muss **mindestens ein** Zielmuster in `post` (ODER) passen.
* **Bei `post={"quantor": "all", "states": [...]}`:** Für die Eingabe müssen **alle** Einträge in `post` gleichzeitig erfüllt sein (UND) – alle positiven Muster (`expect=True`) müssen zutreffen und kein verbotenes Muster (`expect=False`) darf zutreffen.
* **Warnung vor einsamer Negation (*Vacuous Pass*):** Besteht `post` unter `post_quantor == "all"` ausschließlich aus negativen Zielmustern (`expect=False`), schließt der Vertrag nur diese benannten Muster aus; jede andere Rückgabe (wie `None`) erfüllt dann `all(not match(p, q))` trivial. Verbote sollten daher stets mit mindestens einem positiven Zielmuster (`expect=True`) im selben `"quantor": "all"`-Vertrag kombiniert werden.

Jeder Eingang wird gegen dieselbe gesamte Zielmenge verglichen. `pre=[1, 2]` und `post=[2, 4]` sind hier nur Kurznotation für die Mengenidee, **keine gültige API-Schreibweise**: Tatsächlich werden `WorldState`-Objekte benötigt. Auch mit diesen Objekten würde eine gemeinsame Zielmenge `{2, 4}` unter `post_quantor="exists"` eine vertauschte Zuordnung akzeptieren. Für `f(1)=2` und `f(2)=4` sind getrennte Verträge nötig.

Die Quantoren beziehen sich nur auf die endlichen Listen und die jeweils beobachteten Ausführungen (für eine direkt an `evaluate_step_logic([], post_quantor)` übergebene leere Trace-Liste liefert `"exists"` gemäß `any([])` den Wert `False` und `"all"` gemäß `all([])` den Wert `True`; `EBT` selbst lehnt leere Zustandslisten vorab per `ValueError` ab). Bei nichtdeterministischen Targets belegt ein Match weder alle möglichen Ausgaben noch deren Häufigkeit. Die Auswertungsregel ist kein Beweiskalkül und misst keine Testabdeckung.
```

#### AP 6.3: Abschnitte „Wiederholte Läufe und historische Ergebnisse“ (Z. 205) & „Persistente EBT-Berichte“ (Z. 227)
1. **Zeile 205 ergänzen (Sticky-Quantor-Reset & Mutations-Revalidierung):**
   ```markdown
   Zustandslisten, Quantor-Wrapper und `expect`-Flags (`bool`-Typ sowie das Verbot von `expect=False` in `pre` und unter `post_quantor="exists"`) werden beim Aufbau der EBT-Instanz und vor jedem Lauf in `_arrange()` geprüft. FS-Kurzformen werden vor jedem Lauf auf Namenskollisionen geprüft. Damit werden auch nachträgliche In-Place-Mutationen (etwa `case.post[0].expect = False` oder `case.post.append(...)`) vor der Ausführung validiert. Bei wiederholten `.run()`-Aufrufen ohne Neuzuweisung von `case.pre` bzw. `case.post` (sowie bei In-Place-Listenmutationen) bleiben explizit deklarierte Quantoren (`pre_quantor`, `post_quantor`) erhalten; wird `case.pre` oder `case.post` hingegen ohne Quantor-Dictionary neu zugewiesen (Einzel-`WorldState`, Liste oder `None`), setzt `_arrange()` den jeweiligen Quantor auf seinen Standardwert (`pre_quantor="all"`, `post_quantor="exists"`) zurück. Konfigurationsfehler propagieren unabhängig von `expect=False` und `reporter=None`.
   ```
2. **Zeile 227 ergänzen (`pre_quantor` und `post_quantor` im JSON-Bericht):**
   ```markdown
   `JsonReporter(path)` speichert einen abgeschlossenen `RunTrace` als UTF-8-JSON mit
   `schema_version: 1`, Lauf-ID, Target, Laufzeit, `expect`, `pre_quantor`, `post_quantor`, Gesamtbewertung und allen
   Vergleichsspuren einschließlich positiver und negativer Post-Zustände.
   ```

---

### Arbeitspaket 7 (AP 7): Entwickler-Dokumentation (`docs/dev/`) & `README.md` / `GUIDE_Example-Based-Testing.md`

#### AP 7.1: [`docs/dev/DEV-GUIDE_2-1_EBT-Class.md`](../docs/dev/DEV-GUIDE_2-1_EBT-Class.md)
1. **Zeile 23 (`Konstruktor und Konfiguration`):**
   Ersetze die veraltete `_ensure_list(None)`-Beschreibung durch `_parse_state_config`:
   ```markdown
   `target` muss ohne Arena oder mit `TempFS` ein Callable sein; zusätzliche String-Referenzen werden durch den `PyVenv`-Codec aufgelöst. `pre` und `post` akzeptieren einen `WorldState`, nichtleere Listen davon, `None` oder ein Quantor-Wrapper-Dictionary `{"quantor": "all" | "exists", "states": ...}`. `_parse_state_config()` normalisiert `None` zu `[WorldState()]` unter dem jeweiligen Standard-Quantor (`pre_quantor="all"`, `post_quantor="exists"`), entpackt Dict-Wrapper über `_parse_quantor_wrapper()` und prüft über `_validate_states()` sowie `_validate_state_expects()` alle Invarianten: Leere Listen, unbekannte/fehlende Wrapper-Schlüssel, ungültige Quantor-Strings sowie `expect=False` in `pre` oder unter `post_quantor="exists"` führen zu `ValueError("STATE-GUARD: ...")`; falsche Container-/Elementtypen oder nicht-boolesche `expect`-Werte zu `TypeError("STATE-GUARD: ...")`. Eine `ConventionMap` oder Inferenz primitiver Werte in `args`, `kwargs` oder `returns` existiert nicht.
   ```
2. **Zeile 27 (`expect` & `@pre.setter` / `@post.setter`):**
   ```markdown
   `expect` wird über `validate_bool_expect()` strikt auf `type(value) is bool` geprüft und negiert bei `False` das fertige Gesamtergebnis aller Schritte. Es behandelt keine erwarteten Exceptions. `post.expect` kennzeichnet in `post={"quantor": "all", ...}` erlaubte (`True`) oder verbotene (`False`) Muster; unter `post_quantor="exists"` sowie in `pre` wird `expect=False` per `STATE-GUARD` (`ValueError`) abgewiesen. `pre` und `post` sind als Properties implementiert: Eine Attribut-Neuzuweisung (`case.pre = ...`, `case.post = ...`) markiert `_pre_reassigned` bzw. `_post_reassigned`, sodass `_arrange_states()` beim nächsten Lauf den Quantor auf `"all"` bzw. `"exists"` zurücksetzt, sofern kein neuer Dict-Wrapper übergeben wurde.
   ```
3. **Zeile 37 (`Pipeline`, Schritt 1) & Zeile 46 (`Aggregation`):**
   - In Zeile 37 ergänzen: `1. _arrange() validiert max_workers und EBT.expect, aktualisiert und prüft über _arrange_states() die Zustandslisten samt Quantor-Reset und expect-Guards, prüft validate_exception_contract() und normalisiert anschließend fs.`
   - Zeile 46 ersetzen durch:
     ```markdown
     Die Traces werden nach Eingangsschritt gruppiert. Pro Schritt wertet `evaluate_step_logic(traces, self.post_quantor)` die Einzelerfüllungen `sat(t) = t.evaluation if t.post.expect else not t.evaluation` strikt nach `self.post_quantor` aus (`all(results)` bei `"all"`, `any(results)` bei `"exists"` – ohne historische $Q^+$/$Q^-$-Partitionierung und ohne Vacuous-True bei leerer Trace-Liste unter `"exists"`). Danach werden die Schritt-Ergebnisse gemäß `self.pre_quantor` (`all(successes)` bei `"all"`, `any(successes)` bei `"exists"`) verknüpft. `EBT.expect=False` negiert dieses Endergebnis. Alle Eingänge teilen dieselbe Zielmenge; eine Zuordnung von `pre[i]` zu `post[i]` entsteht nicht.
     ```

#### AP 7.2: [`docs/dev/DEV-GUIDE_2-2_WorldState-Class.md`](../docs/dev/DEV-GUIDE_2-2_WorldState-Class.md)
1. **Zeile 39 (`returns` & `raises`):**
   Ersetze den fehlerhaften letzten Satz (*„`stdout`, `stderr` und ein Feld für erwartete Exceptions existieren nicht.“*) durch:
   ```markdown
   `stdout` und `stderr` sind keine `WorldState`-Felder. Für erwartete Target-Exceptions existiert `raises: ExceptionExpectation | None = None` (und `exception: Exception | None = None` für beobachtete Ausnahmen im Outcome); `validate_exception_contract()` stellt sicher, dass `returns` und `raises` niemals im selben Zustand kombiniert werden.
   ```
2. **Zeile 45 (`expect`):**
   ```markdown
   `expect: bool = True` wird bereits in `__post_init__` (sowie vor jedem Lauf in `EBT._arrange()`) über `validate_expect()` / `validate_bool_expect()` strikt auf `type(self.expect) is bool` geprüft (`TypeError("STATE-GUARD: ...")` bei `None`, `0`, `1` usw.). In `post` unterscheidet `expect` unter `post={"quantor": "all", ...}` geforderte (`True`) und verbotene (`False`) Muster. Es negiert nicht selbst den gesamten Lauf; dafür gibt es `EBT.expect`. In `pre` sowie unter `post_quantor="exists"` ist `expect=False` unzulässig und wird von `EBT` vor der Ausführung mit `ValueError("STATE-GUARD: ...")` abgewiesen.
   ```

#### AP 7.3: [`docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`](../docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)
- Ergänze in Zeile 20 und Zeile 29, dass `pre` und `post` neben `WorldState`, nichtleeren Listen davon und `None` auch das explizite Quantor-Wrapper-Dictionary `{"quantor": "all" | "exists", "states": ...}` akzeptieren (Standard: `pre_quantor="all"`, `post_quantor="exists"`).

#### AP 7.4: [`README.md`](../README.md) (Zeile 122) & [`docs/GUIDE_Example-Based-Testing.md`](../docs/GUIDE_Example-Based-Testing.md) (Zeile 43)
1. **`README.md` (Zeile 122):**
   Präzisiere den ersten Satz des Absatzes auf:
   ```markdown
   Standardmäßig wirkt `pre` als reiner Allquantor (`"all"`, jeder Eingang muss bestehen) und `post` als reiner Existenzquantor (`"exists"`, mindestens ein Zielmuster muss passen); über `{"quantor": "all" | "exists", "states": ...}` lassen sich beide Quantoren explizit steuern, wobei Verbote (`WorldState(..., expect=False)`) ausschließlich unter `post={"quantor": "all", ...}` zulässig sind. Bei mehreren Eingängen gilt dieselbe Zielmenge für jeden Eingang; es gibt keine automatische paarweise Zuordnung zwischen `pre[i]` und `post[i]`. Zusammengehörige Ein-/Ausgabepaare benötigen getrennte EBT-Verträge. Eine Liste erlaubter Würfelergebnisse prüft nur die beobachtete Ausgabe; auch ein konstanter Generator kann bestehen. Zufälligkeit und Verteilung werden damit nicht geprüft.
   ```
2. **`docs/GUIDE_Example-Based-Testing.md` (Zeile 43):**
   Harmonisiere den ersten Satz mit `GUIDE_Contract-Semantics.md:203`:
   ```markdown
   Verwende nichtleere Zustandslisten und explizite Erwartungen; bei aufeinanderfolgenden `.run()`-Aufrufen auf derselben EBT-Instanz setzt Cubie die Laufdaten (und bei Neuzuweisung von `pre`/`post` ohne Dict-Wrapper auch den jeweiligen Quantor) automatisch zurück, nicht jedoch externe Target-Seiteneffekte. `returns=None` erwartet explizit `None`; ausgelassenes `returns` oder `returns=qb_cubie.UNSPECIFIED` lässt den Rückgabewert offen. Die genauen Quantor- und `expect`-Regeln stehen in der [Semantikreferenz](GUIDE_Contract-Semantics.md), in [Erwartungssteuerung & Safety](GUIDE_Expect-Flags.md) und in [Fortgeschrittene Quantoren](GUIDE_Quantifiers.md); historische Befunde sind im [Gutachten](../GUTACHTEN.md) dokumentiert. Erfolgreiche Beispiele sind begrenzte Beobachtungen, keine allgemeine Korrektheitsgarantie.
   ```

---

## 5. Empfohlene Ausführungsreihenfolge & Abnahmeprotokoll

Damit die Umsetzung schnell, deterministisch und ohne Zwischenkonflikte mit `DocEnsurance` und `DocFrame` abläuft, wird folgende Reihenfolge empfohlen:

### Schritt 1: Die 4 crashenden Live-Code-Snippets samt Handbüchern aktualisieren (AP 1 & AP 5)
1. `docs/GUIDE_Expect-Flags.md` gemäß **AP 1** aktualisieren (behebt die 3 `DOC-EXEC`-Fehler in Zeilen 39, 80 und 154).
2. `docs/GUIDE_EBT-Usage-Pattern.md` gemäß **AP 5** aktualisieren (behebt den 4. `DOC-EXEC`-Fehler in Zeile 147).
3. **Sofortige Zwischenprobe mit `DocEnsurance`:**
   ```bash
   .venv/bin/python -m pytest -q tests/test_styleguide.py -k "test_docs_code_examples"
   ```
   $\rightarrow$ Bereits nach Schritt 1 muss `test_docs_code_examples` von `FAILED` auf **`PASSED`** springen!

### Schritt 2: Die übrigen 3 Kern-Handbücher aktualisieren (AP 2, AP 3 & AP 4)
1. `docs/GUIDE_Quantifiers.md` gemäß **AP 2** aktualisieren.
2. `docs/GUIDE_Contract-Design.md` gemäß **AP 3** aktualisieren.
3. `docs/GUIDE_Quality-Assurance.md` gemäß **AP 4** aktualisieren (inklusive Einsteiger-Grundkurs, aktualisiertem Spickzettel und den 5 TGD-Phasen aus den letzten Commits).

### Schritt 3: Referenz-, Entwickler- und Einstiegs-Dokumentation nachziehen (AP 6 & AP 7)
1. `docs/GUIDE_Contract-Semantics.md` gemäß **AP 6** als technische Single Source of Truth synchronisieren.
2. `docs/dev/DEV-GUIDE_2-1_EBT-Class.md`, `docs/dev/DEV-GUIDE_2-2_WorldState-Class.md`, `docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md`, `README.md` und `docs/GUIDE_Example-Based-Testing.md` gemäß **AP 7.1 – AP 7.4** aktualisieren.

### Schritt 4: Vollständige Endabnahme über alle orthogonalen Prüf-Schichten
Führe nach Abschluss aller Dokumentations-Edits die folgenden Prüfungen aus:

```bash
# 1. Lebende Dokumentation (CUBIE_DOC_STYLE, CUBIE_DOC_RULES, CUBIE_DOCFRAME_RULES) + Code-Styleguide
.venv/bin/python -m pytest -q tests/test_styleguide.py

# 2. Statische Code-Analyse (ruff, pylint, mypy --warn-unreachable)
.venv/bin/python -m pytest -q tests/test_lint.py

# 3. Meta-Gates (Gate 1: Canonical Imports, Gate 2: Cross-Product, Gate 3: Lonely Negation)
.venv/bin/python -m pytest -q tests/tests_meta/

# 4. EBT-Core-Testsuite inkl. Quantor-Deklarationen & STATE-GUARDs
.venv/bin/python -m pytest -q tests/tests_ebt/
```

**Verbindliche Abnahmekriterien (Definition of Done):**
- [ ] `tests/test_styleguide.py` (inklusive `test_docs_code_examples` über alle Markdown-Dokumente) läuft mit **`0 failed` und `0 warnings`** durch.
- [ ] Kein Code-Snippet in `docs/` überschreitet 30 Zeilen (`DOC-HIGH-COMPLEXITY`), vor jedem Python-Block steht ein erklärender Textabsatz $\ge 20$ Zeichen (`DOC-PRE`), und alle `<details>`-Ergebnisblöcke stimmen exakt mit dem Laufzeit-Output überein (`DOC-OUT`).
- [ ] Alle H1-Titel und `qb:frame`-Blöcke (`CUBIE_DOC_FRAME_1..3`) sind synchron (`0` `DOCFRAME-*`-Diagnosen).
- [ ] Weder `src/qb_cubie/` noch `tests/**/*.py` wurden während des Docs-Sync verändert (`git diff src/ tests/` zeigt außer `tests/GEMINI-5.md` keine Änderungen).

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../docs/.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../docs/GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../docs/GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../docs/GUIDE_Contract-Design.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../docs/GUIDE_Example-Based-Testing.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../docs/GUIDE_Expect-Flags.md)  
[↦ | Linter | ↤](../docs/GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../docs/GUIDE_Quantifiers.md)  
[↦ | RBT-Nutzungsmuster | ↤](../docs/GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../docs/services/GUIDE_DocFrame.md)  

[↦ | Entwicklerübersicht & Internals | ↤](../docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](../docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../docs/feature-drafts/virtualization/README.md)  
[↦ | Analysis: Reperatur vom Cubie-Core | ↤](./ANALYSIS.md)  
[↦ | Reperatur vom Cubie-Core | ↤](./GEMINI-1.md)  
[↦ | Analysis: Reperatur vom Cubie-Core | ↤](./GEMINI-2.md)  
[↦ | Analysis: Reperatur vom Cubie-Core | ↤](./GEMINI-3.md)  
[↦ | Arbeitspaket: TGD Green-Phase — Reparatur & Härtung des Cubie-Core | ↤](./GEMINI-4.md)  
[↦ | Arbeitspaket: TGD Docs-Sync & Didaktische Härtung — Reparatur der QA-Handbücher und Referenzdokumentation | ↤](./GEMINI-5.md)  
[↦ | Analysis: Reperatur vom Cubie-Core | ↤](./HYPOTHESIS.md)  

</div>
<!-- /qb:frame -->
