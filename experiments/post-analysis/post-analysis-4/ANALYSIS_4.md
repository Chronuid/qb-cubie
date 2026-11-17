<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini-4-Hydrogen" effort="High" -->
# Post-Hoc Audit 4

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini-4-Hydrogen
- **Reasoning-Effort:** High
- **Analysedatum:** 17. November 2026, ~ 09:05 (CET)
- **Synthesebasis:**
  - [ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md) (Auditiertes Dokument)
  - `src/qb_cubie/` (39 getrackte Python-Module, 7.575 LOC am `HEAD = 7e08e2ac`)
  - `tests/` (98 getrackte Python-Dateien inkl. `tests/wheel/`, 16.350 LOC)
  - `docs/`, [GUTACHTEN.md](file:///home/symphonie/PycharmProjects/cubie/GUTACHTEN.md), [META_QUESTION.md](file:///home/symphonie/PycharmProjects/cubie/META_QUESTION.md), [README.md](file:///home/symphonie/PycharmProjects/cubie/README.md)
  - Git-Commit-Historie von `qb-cubie` (`3ae8b33e` vom 13.11.2026 bis `7e08e2ac` vom 16.11.2026; 51 Commits)
- **Stand:** qb-cubie (v0.0.7)
- **Git-Log:** `git log -n 1`
```text
commit 7e08e2ac7a39586fe4ce9dfff209ee11810ea0ca (HEAD -> main, origin/main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Mon Nov 16 08:50:29 2026 +0100

    Double-Check
```

---

---

<!-- /qb:frame -->

## 1. Untersuchungsgegenstand und Audit-Methodik

Dieses Post-Studien-Audit prüft wertungsfrei die empirischen Behauptungen, Kennzahlen, Git-Metriken, Zeitangaben und Code-Befunde in [ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md) gegen den realen Repository-Zustand bei Commit `7e08e2ac` (`v0.0.7`) sowie gegen die vollständige Git-Historie ab `3ae8b33e`.

Methodisch wurden sämtliche Aussagen in `ANALYSIS_3.md` mittels AST- und Zeilenauswertung über `git ls-files`, Differenz- und Zeitstempel-Abfragen über `git show` / `git log` sowie direkter Quellcode-Inspektion in `src/qb_cubie/`, `tests/` und `docs/` verifiziert.

**Gesamtbild der Prüfung:**
- Die in **Abschnitt 6** von `ANALYSIS_3.md` aufgeführten neun technischen Code- und Test-Befunde (`DF-1` bis `DF-4`, `DE-1` bis `DE-3`, `TC-1`, `TC-2`) sind am Stand `7e08e2ac` **präzise belegt**.
- In den **Abschnitten 1 bis 5** finden sich hingegen mehrere nachweisbare **Rechen-, Zähl-, Zeitspannen- und Zuordnungsfehler** sowie **interne Selbstwidersprüche**, die überwiegend aus drei gemeinsamen Mustern entstehen:
  1. **Ungeprüfte Übernahme und Fortpflanzung von Zahlen** aus Sekundär-Artefakten (`HYPOTHESIS.md`) oder aus fehlerhaften Zwischensummen,
  2. **Vermischung von Git-Diff-Zählkonventionen** (`insertions + deletions` aus `--stat` als `+`-Additionen ausgegeben; commitweite Löschungen einzelnen Dateien zugeschrieben),
  3. **Rückprojektion späterer Dateizustände** auf frühere Commits.

---

## 2. Befunde: Quantitative Bestandsaufnahme & interne Rechenfehler (Abschnitte 1.1, 1.2 & 5)

### Befund A-1: Fehlende 200 LOC bei `DocFrame` und interner Selbstwiderspruch in `ANALYSIS_3.md`
* **Behauptung in `ANALYSIS_3.md`:**
  * Tabelle 1.1 ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L44)) beziffert `Service DocFrame (Prototyp)` (`src/qb_cubie/services/doc_frame/`) auf 7 Module mit **1.285 LOC**.
  * Abschnitt 5, Muster 3 ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L269)) nennt für `DocFrame` (inkl. `docframe.py`) **1.296 LOC**.
* **Empirischer Befund (`HEAD = 7e08e2ac`):**
  Die 7 Dateien in `src/qb_cubie/services/doc_frame/` umfassen tatsächlich **1.485 LOC** (`__init__.py`: 125, `__main__.py`: 8, `_catalog_scanner.py`: 178, `doc_frame.py`: 340, `doc_frame_rules.py`: 256, `frame_blocks.py`: 410, `protocols.py`: 168). Zusammen mit `src/qb_cubie/services/docframe.py` (11 LOC) sind es **1.496 LOC** (Differenz: **+200 LOC**).
* **Interner Selbstwiderspruch in `ANALYSIS_3.md`:**
  * In [ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L226) (zu `03d7a0dd`) gibt derselbe Bericht für `doc_frame/` bereits **1.477 LOC** an (was exakt `1.485 - 8` vor Anlage von `__main__.py` in `7e08e2ac` entspricht).
  * In [ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L255-L259) (Muster 2) summieren sich allein 5 der 7 dort aufgelisteten `doc_frame/`-Dateien auf **1.352 LOC** (`178 + 410 + 256 + 168 + 340`) – mehr als die in Tabelle 1.1 für alle 7 Module ausgewiesenen 1.285 LOC.

### Befund A-2: Interne Additionsfehler und inkorrekte Bestandszahlen in `src/qb_cubie/` und `tests/`
* **Behauptung in `ANALYSIS_3.md`:**
  * `src/qb_cubie/` umfasse **39 Module, 7.196 LOC, 112 Klassen, 536 Funktionen (`def`)** ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L10), [L40-L45](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L40-L45)).
  * `src/qb_cubie/services/` stelle **42,0 % (3.024 von 7.196 LOC)** ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L56)).
  * `tests/` umfasse **75 Module, 14.996 LOC, 51 Klassen, 665 `def`, 494 `test_*`, 470 `EBT`** ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L11), [L46-L49](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L46-L49)).
* **Empirischer Befund (`git ls-files` bei `7e08e2ac`):**
  1. **Interne Rechenfehler innerhalb von Tabelle 1.1 und Abschnitt 1.2:**
     Die eigenen Tabellenzeilen von `ANALYSIS_3.md` summieren sich auf `4.084 + 88 + 205 + 1.532 + 1.285 =` **7.194 LOC** (nicht 7.196 LOC) und für `services/` auf `205 + 1.532 + 1.285 =` **3.022 LOC** (nicht 3.024 LOC).
  2. **Abweichung gegenüber dem realen Codebestand in `src/qb_cubie/`:**

| Bereich | Behauptung (`ANALYSIS_3.md`) | Tatsächlicher Bestand (`7e08e2ac`) | Abweichung |
| :--- | :--- | :--- | :--- |
| **Core-Framework** (`src/qb_cubie/` ohne `services`, `cli`) | 22 Mod. / 4.084 LOC / 58 Kl. / 309 `def` | 22 Mod. / **4.265 LOC** / **63 Kl.** / **363 `def`** | +181 LOC / +5 Kl. / +54 `def` |
| **Service `DocFrame`** (`src/qb_cubie/services/doc_frame/`) | 7 Mod. / 1.285 LOC / 26 Kl. / 95 `def` | 7 Mod. / **1.485 LOC** / 26 Kl. / 95 `def` | +200 LOC |
| **Summe `src/qb_cubie/`** | 39 Mod. / 7.196 LOC / 112 Kl. / 536 `def` | 39 Mod. / **7.575 LOC** / **117 Kl.** / **590 `def`** | +379 LOC / +5 Kl. / +54 `def` |
| **Anteil `src/qb_cubie/services/`** | 3.024 / 7.196 LOC (42,0 %) | **3.222 / 7.575 LOC (42,5 %)** | +198 LOC / +0,5 PP |

  3. **Abweichung gegenüber dem realen Testbestand in `tests/`:**
     * `tests_doc_ensurance/`: Enthält **10** `.py`-Dateien (9 nicht-leere ohne die 0-Byte-`__init__.py`), **9** Klassen (behauptet: **10**) und **126** `def` (112 Top-Level-`^def`; behauptet: **109**). LOC (`4.264`), `test_*` (`68`) und `EBT` (`131`) treffen zu.
     * `tests_doc_frame/`: Enthält **5** `.py`-Dateien (4 nicht-leere ohne `__init__.py`), **0** Klassen und **60** `def` (59 Top-Level-`^def`; behauptet: **44**). LOC (`920`), `test_*` (`28`) und `EBT` (`25`) treffen zu.
     * `Tests: Core & Meta` (`tests/` ohne `tests_services`, `wheel`): Umfasst tatsächlich **76** `.py`-Dateien (69 nicht-leere), **10.281 LOC**, **54 Klassen**, **770 `def`**, **403 `test_*`** und **318 `EBT`** (behauptet: 62 / 9.812 / 41 / 512 / 398 / 314).
     * `Summe tests/`: Die Summenzeile schließt `tests/wheel/` (7 Dateien, 885 LOC, 3 Klassen, 58 `def`, 32 `test_*`, 11 `EBT`) stillschweigend aus; selbst ohne `wheel/` beträgt die reale Summe **91 Dateien (82 nicht-leere), 15.465 LOC, 63 Klassen, 956 `def`, 499 `test_*`, 474 `EBT`** (mit `tests/wheel/`: **98 Dateien / 89 nicht-leere, 16.350 LOC, 66 Klassen, 1.014 `def`, 531 `test_*`, 485 `EBT`**).

---

## 3. Befunde: Zeitspannen- und Datierungsfehler (Abschnitte 1.2 & 5)

### Befund B-1: Überhöhte Gesamt-Zeitspanne `3ae8b33e` $\to$ `7e08e2ac` (62,5 vs. 60,4 Stunden)
* **Behauptung (`ANALYSIS_3.md`, Z. 56):** Das Entwicklungsfenster zwischen Commit `3ae8b33e` (13.11.2026, 20:25 Uhr) und Commit `7e08e2ac` (16.11.2026, 08:50 Uhr) betrage **62,5 Stunden**.
* **Empirischer Befund:** Von `2026-11-13 20:25:51 +0100` bis `2026-11-16 08:50:29 +0100` vergehen exakt **2 Tage, 12 Stunden, 24 Minuten und 38 Sekunden**, also **~60,4 Stunden** (Fehler: +2,1 Stunden).

### Befund B-2: Stark überhöhte Entwicklungsdauer für `DocEnsurance` (`v0.0.4` $\to$ `v0.0.6`)
* **Behauptung (`ANALYSIS_3.md`, Z. 268):** In der Vergleichstabelle von Muster 3 wird für `DocEnsurance (v0.0.4 -> v0.0.6)` eine Dauer von „~15 Commits über **~40 Stunden**“ angegeben.
* **Empirischer Befund:** Vom Initial-Commit `32434293` (13.11., 23:15:21 Uhr) bis zum Release `v0.0.6` (`8309b966`, 14.11., 15:38:27 Uhr) liegen **16,4 Stunden**; selbst ab dem Planungs-Commit `3ae8b33e` (13.11., 20:25:51 Uhr) sind es **19,2 Stunden**. Die in Abschnitt 2 ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L68)) selbst genannten Eckdaten (`13.11. 20:25` bis `14.11. 15:38`) widerlegen die „~40 Stunden“ in Muster 3 direkt.

---

## 4. Befunde: Git-Diff-Metriken (`Δ LOC`) & vermischte Zählkonventionen (Abschnitte 2.1, 2.3 & 3.2)

### Befund C-1: Vermischung von `insertions + deletions` mit `+`-Additionen und Rechenfehler in Tabelle 2.3
* **Behauptung (`ANALYSIS_3.md`, Z. 104–112):** Tabelle 2.3 weist eine Spalte `Δ LOC (src / tests / docs)` mit durchgängigem `+`-Präfix aus (im Gegensatz zu Tabelle 4.1, die sauber `+insertions / -deletions` trennt).
* **Empirischer Befund (`git show --stat` / `--numstat`):**
  * Bei vier Commits (`4f05f30d`, `d59f82d5`, `bc6afb29`, `503e0f14`) wurden Insertions und Deletions aus der Summenspalte von `git show --stat` addiert und mit `+` versehen – was gelöschte Zeilen fälschlich als Neuzugänge erscheinen lässt:
    * `4f05f30d` (`src`): behauptet `+403`, real `+361 / -42` (Summe 403).
    * `d59f82d5`: behauptet `+22 / +12 / 0`, real `src:+11/-11` (Summe 22) und `tests:+7/-5` (Summe 12).
    * `bc6afb29` (`tests`): behauptet `+583`, real `+581 / -2` (Summe 583).
    * `503e0f14` (`tests`): behauptet `+528`, real `+463 / -65` (Summe 528).
  * Bei drei weiteren Commits stimmen die Angaben **weder** als Insertions **noch** als `insertions + deletions`-Summe:
    * `f33ee68a`: behauptet `+467 / +339 / +430`; real `src:+376/-158` (Summe **534**; Differenz 67 entspricht exakt `src/qb_cubie/services/__init__.py | 67`), `tests:+337/-2` (Summe 339), `docs:+352/-79` (Summe **431**).
    * `7bc102dd`: behauptet `+1.181 / +693 / +334`; real `src:+730/-473` (Summe **1.203**), `tests:+541/-137` (Summe **678**), `docs:+310/-24` (Summe 334).
    * `82893aba`: behauptet `+30 / +219 / 0`; real `src:+15/-7` (Summe **22**), `tests:+214/-13` (Summe **227**).

### Befund C-2: Fehlinterpretation von Lösch-Statistiken in `3ae8b33e`, `6cb7487e` und `30eda081`
* **`3ae8b33e` ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L82)):** Behauptet „aus `src/qb_cubie/benchmarks` heraus (-13.237 Zeilen in 458 Dateien)“. Tatsächlich betraf der Auszug aus `src/qb_cubie/benchmarks/` **417 Dateien** mit **13.142 Zeilen** (`--no-renames`), und die Dateien wurden per `git mv` nach `experiments/` verschoben (+423 Dateien / +13.165 Zeilen), nicht gelöscht. Die Zahl `458` entspricht dagegen den übrigen nicht-`experiments/`-Pfaden des Commits.
* **`6cb7487e` ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L181)):** Behauptet „Kürzung von `docs/GUIDE_Benchmarks.md` um 1.554 Zeilen (von **1.578 auf 24 Zeilen**)“. Tatsächlich fiel die Datei von **1.577 auf 47 Zeilen** (Netto-Kürzung **1.530 Zeilen**). `ANALYSIS_3.md` las die im Diff ausgewiesenen `24 insertions` fälschlich als resultierende Dateilänge und rekonstruierte daraus `1.554 + 24 = 1.578`.
* **`30eda081` ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L183)):** Behauptet „Kürzung von `README.md` um **127 Zeilen**“. Tatsächlich waren `-127` die Löschungen über **alle 5 Dateien** des Commits (`+280 / -127`); `README.md` selbst wies `+12 / -120` Zeilen auf (von **324 auf 216 Zeilen**, Netto-Kürzung **108 Zeilen**).

---

## 5. Befunde: Ungeprüfte Übernahme von Sekundärzahlen, Rückprojektionen & Zuordnungsfehler (Abschnitte 2–5)

### Befund D-1: Übernahme eines Zählfehlers aus `HYPOTHESIS.md` („22“ vs. „24“ `DocFrame`-Tests)
* **Behauptung (`ANALYSIS_3.md`, Z. 209, 226, 227):** In `03d7a0dd` (`step_1`) seien **22 EBT-Tests** entstanden; in `df3714be` (`step_2`) seien „Alle **22** neuen `DocFrame`-Tests“ grün gewesen.
* **Empirischer Befund:** Die drei in `03d7a0dd` angelegten Testmodule in `tests/tests_services/tests_doc_frame/` enthalten zusammen **24** `test_*`-Funktionen und **24** `EBT`-Aufrufe (`test_docframe_catalog_and_routing.py`: 10, `test_docframe_presets_and_update.py`: 4, `test_docframe_rules_and_guards.py`: 10; durch `@pytest.mark.parametrize` 27 `pytest`-Testfälle). Die Zahl `22` stammt nachweislich als Zählfehler aus dem Prosa-Text der damaligen `HYPOTHESIS.md` („Alle 22 EBT-Verträge“) und wurde ohne Prüfung gegen die Testdateien übernommen.

### Befund D-2: Rückprojektion späterer Dateilängen auf `ce02737d` und `05e9945b`
* **`ce02737d` (`step_4`, [ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L229)):** Behauptet „Ausbau von `DEV-GUIDE_DocFrame.md` auf **549 Zeilen**“. Zum Zeitpunkt `ce02737d` hatte die Datei **542 Zeilen**; die Länge von 549 Zeilen erreichte sie erst nach `23b083af` (+5/+0) und `7e08e2ac` (+2).
* **`05e9945b` (`step_5`, [ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L230)):** Behauptet „Ausbau von `docs/services/GUIDE_DocFrame.md` auf **702 Zeilen**“. Zum Zeitpunkt `05e9945b` hatte die Datei **695 Zeilen**; die Länge von 702 Zeilen erreichte sie erst im nachfolgenden Release-Commit `23b083af` (am `HEAD = 7e08e2ac` sind es 712 Zeilen).

### Befund D-3: Ungenaue Mengenangaben, Kausal- und Commit-Zuordnungen
1. **Multi-`pre`/Multi-`post`-Verbreitung (`920f26cf`, [ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L166)):** Behauptet, das Kreuzprodukt-Muster sei in „**über 25 Tests** innerhalb von `tests_doc_ensurance/`“ verwendet worden. Zum Zeitpunkt `920f26cf` existierte das Unterpaket `tests_doc_ensurance/` noch nicht (erst ab `174b048f`), und über alle Module in `tests/tests_services/` hinweg gab es exakt **22** `EBT`-Aufrufe mit gleichzeitig mehreren `pre`- und mehreren `post`-Einträgen.
2. **Aufzählung der in `32434293` geänderten Markdown-Guides ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L86), [L245](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L245)):** Muster 1 spricht korrekt von 10 Dateien, die Klammeraufzählung in Z. 86 nennt jedoch nur 9 Namen (`docs/feature-drafts/virtualization/vm-requirements.md` fehlt) und spricht pauschal von „sämtlichen bestehenden Markdown-Guides“, obwohl u. a. `GUIDE_Contract-Semantics.md`, `GUIDE_Example-Based-Testing.md` und `DEV-GUIDE_2-0` unverändert blieben.
3. **Dateizahl in `174b048f` vs. `0eec79d9` vs. `db8eb74d` ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L224), [L228](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L228), [L247](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L247)):**
   * `174b048f:docs/dev/services/DEV-GUIDE_DocFrame.md` analysiert laut eigenem Einleitungssatz **26 Markdown-Dateien** (25 befüllte), nicht „35 reale Dateien“ (35 war die Anzahl der in `0eec79d9` geänderten Dateien).
   * In `db8eb74d` wurden **38** Markdown-Dateien geändert (37 Repository-Dokumente plus `HYPOTHESIS.md`) und darin **39** Vorkommen des fehlerhaften Bild-Alt-Texts `![Error while trying to load the image]` in **37** Dateien (36 aktiven Dokumenten + `HYPOTHESIS.md`) ersetzt – nicht **35** (Z. 247).
   * Die Behauptung in Z. 247, erst `DocFrame` und `CUBIE_DOCFRAME_RULES` hätten „die methodischen Altlasten in `tests_doc_ensurance/`“ aufgedeckt, verwechselt die Kausalität: Diese Altlasten wurden bereits zwei Tage zuvor in [META_QUESTION.md](file:///home/symphonie/PycharmProjects/cubie/META_QUESTION.md) (`920f26cf`) diagnostiziert und in `HYPOTHESIS.md` (`df3714be`) übernommen.
4. **Vermischung von H3 und H4 in `db8eb74d` ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L228)):** Die 18 in `db8eb74d` geänderten Core-Testdateien (tatsächlich **19** Dateien inklusive `test_styleguide.py`) wurden dort **nicht** wegen Kreuzprodukt-Tests oder `expect=False` (H3) umgebaut, sondern erhielten ausschließlich Import-Bereinigungen (`from src.qb_cubie` $\to$ `from qb_cubie`, H4) sowie in `test_rbt_demo.py` eine kleine Fixtur-/Skip-Ergänzung (`+1` bis `+6` Zeilen).
5. **Modul-Docstrings in `503e0f14` vs. `82893aba` ([ANALYSIS_3.md](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L110), [L112](file:///home/symphonie/PycharmProjects/cubie/experiments/post-analysis/post-analysis-3/ANALYSIS_3.md#L112)):** `503e0f14` änderte den Modul-Docstring auf `"""Tries to verify ..."""` nur in **2** Testdateien (`test_doc_ensurance_rules.py`, `test_doc_rule_edge_cases.py`), während erst `82893aba` dies (in Fettdruck `"""**Tries to** verify ..."""`) auf alle 7 genannten Testdateien ausweitete.

---

## 6. Empirische Gegenprobe: Bestätigte Teile von `ANALYSIS_3.md`

Zur vollständigen Einordnung dokumentiert das Audit explizit, welche Teile von `ANALYSIS_3.md` der Überprüfung vollständig standgehalten haben:

1. **Abschnitt 6 (Alle neun technischen Befunde am `HEAD = 7e08e2ac`):**
   * **`DF-1` bis `DF-4` (`DocFrame`):** Pass-1/Pass-2-Divergenz in `ProvenanceBlock` (belegt durch [GUIDE_DocFrame.md](file:///home/symphonie/PycharmProjects/cubie/docs/services/GUIDE_DocFrame.md#L345-L357)) und fehlendes `attrs["title"]` in `extract_doc_meta`, Datenverlust bei Unterlisten/Codeblöcken in `_parse_existing_bullets` sowie ungeschütztes `_split_by_dividers`, `.strip()`-Divergenz in `DocFrameOutdated` (real belegt am 3-Leerzeichen-Diff in `README.md` zwischen `3448ddea` und `7e08e2ac`), vorzeitiges `return [...]` und ignorierte Waisen-/unclosed Tags.
   * **`DE-1` bis `DE-3` (`DocEnsurance`):** Stilles Überspringen von `check_document` bei `IN_MEMORY`-Strings ([doc_ensurance.py](file:///home/symphonie/PycharmProjects/cubie/src/qb_cubie/services/doc_ensurance/doc_ensurance.py#L317)), stilles Abschalten der Code-Extraktion bei reiner `FramePattern`-Übergabe ([doc_ensurance.py](file:///home/symphonie/PycharmProjects/cubie/src/qb_cubie/services/doc_ensurance/doc_ensurance.py#L181)), sowie der exakte String-Vergleich `!= "SyntaxError"` in `_run_session_linters` ([doc_ensurance.py](file:///home/symphonie/PycharmProjects/cubie/src/qb_cubie/services/doc_ensurance/doc_ensurance.py#L491)).
   * **`TC-1` & `TC-2` (`tests/` & `reporter.py`):** Vierfache `@pytest.mark.slow`-Oszillation in [tests/test_styleguide.py](file:///home/symphonie/PycharmProjects/cubie/tests/test_styleguide.py#L107) und das unter `python -O` wirkungslose `assert trace.passed` in [src/qb_cubie/reporter.py](file:///home/symphonie/PycharmProjects/cubie/src/qb_cubie/reporter.py#L46).
2. **Qualitative Kern-Episoden & Strukturmetriken:** Die `bc6afb29` $\to$ `503e0f14` $\to$ `7bc102dd`-Sequenz (`Q_Ist`-Falle), das 153-Zeilen-`HighComplexity`-Experiment (`8279fb3c`), die `divmod` $\to$ `double`-Umwidmung, die 81-minütige `klarstellung-commit-historie.md`-Episode (`43ab3efb`..`a8b22b57`), die `red-is-sometimes-good.md`-CI-Probe (`09ef9783`), die `FUNCTION_LIMIT = 12`-Konformität über alle 220 Funktionen in `src/qb_cubie/services/` sowie die `EBT`-pro-Testfunktion-Quoten (`1,93`, `3,50`, `1,00`) sind faktisch exakt.

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](../../../docs/.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../../../docs/GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../../../docs/GUIDE_Benchmarks.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../../../docs/GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../../../docs/GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../../../docs/GUIDE_Example-Based-Testing.md)  
[↦ | Linter | ↤](../../../docs/GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../../docs/GUIDE_Quality-Assurance.md)  
[↦ | RBT-Nutzungsmuster | ↤](../../../docs/GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../../docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../../docs/services/GUIDE_DocFrame.md)  

[↦ | Entwicklerübersicht & Internals | ↤](../../../docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](../../../docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../../docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
