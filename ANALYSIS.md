<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="head" env="Antigravity-CLI" model="Gemini 4 Neon" effort="Medium" -->
# Analyse: Gegenwärtige Lage & Ursachen von BUG-007 (`DocFrame.update()` überschreibt Hinweis zur erkenntnistheoretischen Grenze)

**Dokument-Informationen & Herkunft:**
- **Plattform / Umgebung:** Antigravity-CLI
- **Modell:** Gemini 4 Neon
- **Reasoning-Effort:** Medium
- **Analysedatum:** 24. November 2026, ~19:08 (CET)
- **Synthesebasis:** `KNOWN_ISSUES.md`, `src/qb_cubie/core/services/doc_frame/{doc_frame.py,frame_blocks.py,doc_frame_rules.py,_catalog_scanner.py,protocols.py}`, `tests/test_styleguide.py`, `tests/tests_core/tests_services/tests_doc_frame/{test_docframe_presets_and_update.py,test_docframe_rules_and_guards.py}`, `docs/GUIDE_Quality-Assurance.md`, `docs/GUIDE_TGD.md`, `docs/services/GUIDE_DocFrame.md`, `docs/dev/DEV-GUIDE_Agent-Reports.md`, `docs/dev/services/DEV-GUIDE_DocFrame.md`, Git-Historie (`fd36cca9..c12d6186`) & lokaler Dry-Run/Pytest-Lauf
- **Stand:** qb-cubie (`v0.1.0`, Branch `main`, Commit `c12d6186`)
- **Git-Log:** `c12d6186` ("Tried to improve the docs.")

---

```text
commit c12d61864adfde37f5ea8f0a7a35b031690524ad (HEAD -> main)
Author: Chronuid <Dominickwirzba@gmail.com>
Date:   Tue Nov 24 18:57:49 2026 +0100

    Tried to improve the docs.

Auftrag (GEMINI.md):
- Erfassung der gegenwärtigen Lage und Analyse der Gründe von BUG-007 in KNOWN_ISSUES.md.
- Scope: Rein lesende Analyse (TGD-Stützrad ANALYSIS); kein Produktions- oder Testcode unter src/ oder tests/ geändert.
```
<!-- /qb:frame -->

## Kurzfassung (Executive Summary)

1. **`[BLOCKER]` Unmittelbare Lösch-Ursache (`frame_blocks.py:325-338`):** `DisclaimerSlot.render()` zerlegt den `head`-Span an jeder `---`-Linie und gibt hartkodiert **nur `segments[1]`** zurück. Sobald ein Dokument im Kopfbereich sowohl einen dokument-spezifischen Hinweis (z. B. `> [!WARNING]` / `> [!NOTE]`) **als auch** den Hinweis zur erkenntnistheoretischen Grenze besitzt ($\ge 4$ Segmente), wird `segments[2]` durch `DocFrame.update()` ersatzlos gelöscht. Dies zerstörte bereits den Hinweis in `docs/dev/services/DEV-GUIDE_DocFrame.md` (Commit `e3e3abea`) und würde im aktuellen Stand sofort `docs/services/GUIDE_DocFrame.md` und `docs/services/GUIDE_DocEnsurance.md` beschädigen.
2. **`[BLOCKER]` Fehlender Pflicht-Anker & $Q_{\text{Ist}}$/$Q_{\text{Soll}}$-Umkehrung (`doc_frame.py:125-130`, `doc_frame_rules.py:254-288`):** `STD_HEAD_BLOCKS` enthält keinen verpflichtenden Baustein für den erkenntnistheoretischen Hinweis. In 36 Dokumenten mit genau 3 Segmenten überlebt er nur *zufällig* als passiver Rohtext im optionalen `DisclaimerSlot`. Umgekehrt meldet `DocFrameOutdated` aktuell **genau die korrekten 4-Segment-Dokumente als fehlerhaft**, während Dokumente *ohne* Hinweis (`DEV-GUIDE_DocFrame.md`, 4× `CUBIE_DOC_FRAME_3`-Indizes) still als konform gelten.
3. **`[ABWEICHUNG]` Präzisierung der Reproduktion in `KNOWN_ISSUES.md`:** Ein Dry-Run gegen `KNOWN_ISSUES.md` (3 Segmente) löscht den Hinweis derzeit *nicht* sofort, sondern nur bei Dokumenten mit $\ge 4$ Segmenten; bei Dokumenten mit 2 Segmenten (`docs/misc/lake/SOLVED_ISSUES.md`) wird er umgekehrt nicht injiziert, sondern es entsteht eine doppelte Trennlinie (`---\n\n---`).
4. **`[RISIKO]` Idempotenz-Falle beim künftigen Fix:** Wird ein fester Anker-Block in `STD_HEAD_BLOCKS` ergänzt, ohne den bestehenden Hinweis aus `DisclaimerSlot` herauszufiltern, verdoppelt `DocFrame.update()` den Hinweis in allen 36 Bestands-Dokumenten, in denen er heute in `segments[1]` steht.
5. **`[HINWEIS]` Pausiertes Gate & Modul-Struktur:** `tests/test_styleguide.py::test_docs_frames` ist derzeit per `@pytest.mark.skip` pausiert; ein Dry-Run von `CUBIE_DOCFRAME_RULES` liefert aktuell **13 Diagnosen** über das Repository. Der Refactoring-Wunsch aus `BUG-007` (getrennte Test-Module für `DocEnsurance` & `DocFrame` sowie ein zentrales Template-/Preset-Modul für `head`/`foot`) ist architektonisch sauber umsetzbar.

---

## 1. Gegenwärtige Lage (Ist-Zustand am `HEAD` `c12d6186`)

### 1.1 Zeitlicher Verlauf (`git log`)

| Commit | Datum | Beobachtete Änderung |
| :--- | :--- | :--- |
| `fd36cca9` | 23.11.2026 | Hinweis zur erkenntnistheoretischen Grenze (Karl Popper / Fallibilismus) manuell in **44 Markdown-Dateien** eingepflegt (`+388 / -10`). |
| `e3e3abea` | 23.11.2026 | `BUG-007` in `KNOWN_ISSUES.md` eingetragen; `tests/test_styleguide.py` in `test_docs_code_examples` und `test_docs_frames` (mit `@pytest.mark.skip`) getrennt. Im selben Commit fehlen in `docs/dev/services/DEV-GUIDE_DocFrame.md` bereits die 11 Zeilen des Hinweises (`-11`), nachdem `DocFrame.update()` darüberlief. |
| `011e1ee6` | 24.11.2026 | Projektstruktur angepasst (`CONTEXT_ROUTER`-Hubs in `doc_frame.py`, Abschnittstrennung in `SiblingRouter.render()` in `frame_blocks.py`, Umzug `CI_PLATFORM_STATUS.md` etc.). |
| `c12d6186` | 24.11.2026 | Dokumentations-Überarbeitungen; im aktuellen Arbeitsbaum liegen lokal `A ANALYSIS.md` und `RM docs/GEMINI-1.md -> GEMINI.md`. |

### 1.2 Bestandsaufnahme der Markdown-Dokumente (`Ist`)

Ein rein lesender In-Memory-Dry-Run von `DocFrame` und `DocEnsurance(..., rules=CUBIE_DOCFRAME_RULES)` mit den produktiven `DOC_EXCLUDES` aus `tests/test_styleguide.py:113-121` ergibt über **48 nicht-exkludierte `.md`-Dateien** folgendes Lagebild:

* **Rahmen-Verteilung:** `46` Dateien besitzen `qb:frame`-Blöcke (`40`× `CUBIE_DOC_FRAME_1`, `4`× `CUBIE_DOC_FRAME_3`, `2`× `CUBIE_DOC_FRAME_2`); `2` Dateien besitzen keinen Rahmen (`ANALYSIS.md` vor diesem Bericht, `docs/misc/lake/CI-Data.md`).
* **Verteilung der `head`-Segmente (getrennt durch `---`):**
  * `42` Dateien mit **3 Segmenten** (2× `---`)
  * `2` Dateien mit **2 Segmenten** (1× `---`): `docs/misc/lake/ANALYSIS_COVERAGE_OPTIONS.md`, `docs/misc/lake/SOLVED_ISSUES.md`
  * `2` Dateien mit **4 Segmenten** (3× `---`): `docs/services/GUIDE_DocEnsurance.md`, `docs/services/GUIDE_DocFrame.md`
* **Status des erkenntnistheoretischen Hinweises:**
  * **Vor Dry-Run vorhanden:** `38 / 48` Dateien.
  * **Nach simuliertem `DocFrame.update()` vorhanden:** `36 / 48` Dateien (**2 weitere unmittelbare Verluste**).
  * **Bereits fehlend (10 Dateien):**
    * `docs/dev/services/DEV-GUIDE_DocFrame.md` (`CUBIE_DOC_FRAME_1`, bereits in `e3e3abea` gelöscht; `DocFrame.update()` restauriert ihn nicht)
    * `docs/misc/lake/SOLVED_ISSUES.md` (`CUBIE_DOC_FRAME_1`, 2 Segmente)
    * `docs/core/README.md`, `docs/dev/README.md`, `docs/dev/core/README.md`, `docs/misc/README.md` (`CUBIE_DOC_FRAME_3`, je 3 Segmente ohne Hinweis)
    * `docs/misc/lake/ANALYSIS_CI_MATRIX.md`, `docs/misc/lake/ANALYSIS_COVERAGE_OPTIONS.md` (`CUBIE_DOC_FRAME_2`)
    * `docs/misc/lake/CI-Data.md`, `ANALYSIS.md` (zum Prüfzeitpunkt noch leer/ungerahmt)

### 1.3 Aktuelle `CUBIE_DOCFRAME_RULES`-Diagnosen (pausiertes Gate)

Würde `tests/test_styleguide.py::test_docs_frames` im gegenwärtigen Zustand aktiviert, schlüge es mit **13 Diagnosen** fehl:

| Regel-ID | Anzahl | Betroffene Dateien & Ursache |
| :--- | :---: | :--- |
| `DOCFRAME-MISSING` | 3 | `ANALYSIS.md` (noch leer), `docs/misc/lake/CI-Data.md` (kein Rahmen), `docs/misc/lake/ANALYSIS_CI_MATRIX.md` (fehlende `foot`-Zone) |
| `DOCFRAME-BROKEN-ROUTE` | 1 | `GEMINI.md:1` (`../README.md` ungültig nach Verschiebung `docs/GEMINI-1.md -> GEMINI.md`) |
| `DOCFRAME-OUTDATED` (`head`) | 4 | `docs/services/GUIDE_DocFrame.md`, `docs/services/GUIDE_DocEnsurance.md` (**direkte BUG-007-Folge**), `CI_PLATFORM_STATUS.md` (fehlende `./`-Präfixe), `docs/misc/lake/SOLVED_ISSUES.md` (fehlender 2. `---`) |
| `DOCFRAME-OUTDATED` (`foot`/`router`) | 5 | `docs/misc/{Clean-Code-Pragmatism,Die-Suchmaschine-von-Babel,Erweitertes-PBT,FP-OOP-Isomorphismus}.md` (`foot`), `docs/misc/README.md` (`router`) |

---

## 2. Ursachenanalyse zu BUG-007 (Fakten & Code-Belege)

Die Symptome von `BUG-007` entstehen nicht durch einen einzelnen Tippfehler, sondern durch das Zusammenspiel von **fünf strukturellen Ursachen** in Renderer, Preset-Definition, Prüfregeln und Test-Suite:

### Ursache 1 `[BLOCKER]`: 1-Slot-Truncation in `DisclaimerSlot.render()`

In `src/qb_cubie/core/services/doc_frame/frame_blocks.py:325-338` ist `DisclaimerSlot` wie folgt implementiert:

```python
@dataclass(frozen=True)
class DisclaimerSlot:
    """Preserves an optional document-specific disclaimer block between header dividers."""

    optional: bool = True

    def render(self, ctx: FrameRenderContext) -> str:
        """Extracts and returns the trimmed disclaimer text between the first and second divider."""
        inner_lines = _strip_outer_html_wrappers(ctx.span.inner_content.splitlines())
        segments = _split_by_dividers(inner_lines)
        if len(segments) < 3:
            return ""
        return "\n".join(segments[1]).strip()
```

* **Mechanismus:** `_split_by_dividers()` teilt `inner_lines` an jeder `---`-Zeile in `segments[0], segments[1], ..., segments[k]`.
* **`HeaderContentSlot`** (`frame_blocks.py:287`) konsumiert ausschließlich `segments[0]`.
* **`DisclaimerSlot`** (`frame_blocks.py:337`) konsumiert ausschließlich `segments[1]`.
* **`HEADER_QUICK_NAV`** (`frame_blocks.py:129-141`) rendert die Navigationszeile neu und ignoriert das letzte Segment.
* **Folge bei $\ge 4$ Segmenten:** Jedes Dokument mit einem dokument-spezifischen Hinweis (`segments[1]`, z. B. `> [!WARNING] Status: Prototyp`) **und** dem erkenntnistheoretischen Hinweis (`segments[2]`, `> [!Note]`) verliert `segments[2]` beim ersten Aufruf von `DocFrame.update()` vollständig. Genau dieser Datenverlust trat in `docs/dev/services/DEV-GUIDE_DocFrame.md` (`e3e3abea`) auf und ist im Dry-Run für `docs/services/GUIDE_DocFrame.md` und `docs/services/GUIDE_DocEnsurance.md` reproduzierbar.

### Ursache 2 `[BLOCKER]`: Kein verpflichtender Anker-Block in `STD_HEAD_BLOCKS`

In `src/qb_cubie/core/services/doc_frame/doc_frame.py:125-130` lautet die Kopf-Komposition für `CUBIE_DOC_FRAME_1` und `CUBIE_DOC_FRAME_3`:

```python
STD_HEAD_BLOCKS: Final[tuple[FrameBlockProtocol, ...]] = (
    CenterWrap(
        tag="div",
        blocks=(HeaderContentSlot(), Divider(), DisclaimerSlot(), Divider(), HEADER_QUICK_NAV),
    ),
)
```

* **Konzept-Vermischung:** Es existiert kein eigener Block für den verbindlichen erkenntnistheoretischen Hinweis. Stattdessen wurde der Hinweis in Commit `fd36cca9` manuell in den optionalen `DisclaimerSlot` (oder dahinter als zweiter Block) kopiert.
* **Drei direkte Defekte daraus:**
  1. **Keine Selbstheilung / keine Injektion:** Fehlt der Hinweis in einem Dokument (`docs/dev/services/DEV-GUIDE_DocFrame.md`, `docs/misc/lake/SOLVED_ISSUES.md`, `docs/core/README.md` etc.), ergänzt `DocFrame.update()` ihn nicht. Bei 2-Segment-Dokumenten rendert `DisclaimerSlot` sogar `""`, sodass `CenterWrap` die beiden umliegenden `Divider()` direkt hintereinander (`---\n\n---`) ausgibt.
  2. **Keine zentrale Wartbarkeit:** Jede sprachliche Weiterentwicklung des Hinweises (wie in `fd36cca9`) erfordert manuelle Änderungen in >40 Dateien statt eines einzelnen `DocFrame.update()`-Laufs.
  3. **Ungeklärter Geltungsbereich für `CUBIE_DOC_FRAME_2`:** `CUBIE_DOC_FRAME_2` (`doc_frame.py:138-147`) verwendet weder `STD_HEAD_BLOCKS` noch einen Anker-Block.

### Ursache 3 `[BLOCKER]`: $Q_{\text{Ist}}$/$Q_{\text{Soll}}$-Umkehrung in `CUBIE_DOCFRAME_RULES`

In `src/qb_cubie/core/services/doc_frame/doc_frame_rules.py:254-288` prüft `DocFrameOutdated`:

```python
expected = pat.render_zone(span.zone, ctx)
if span.inner_content.strip() != expected.strip():
    msg = f"Frame zone '{span.zone}' ({span.frame_id}) is out of sync; run DocFrame.update()."
    return [Diagnostic(str(path_obj), self.rule_id, span.start_line, msg, severity=self.severity)]
```

* Keine der vier Regeln in `CUBIE_DOCFRAME_RULES` (`DocFrameMissing`, `DocFrameOutdated`, `DocFrameBrokenRoute`, `DocFrameProvenanceIncomplete`) prüft die Anwesenheit oder Korrektheit des erkenntnistheoretischen Hinweises.
* Weil `pat.render_zone("head", ctx)` den Hinweis in `segments[2]` verwirft, entsteht eine klassische **$Q_{\text{Ist}}$-vs.-$Q_{\text{Soll}}$-Inversion** (vgl. `GUIDE_Quality-Assurance.md` §2):
  * Dokumente **mit** dokument-spezifischem Hinweis **und** erkenntnistheoretischem Hinweis (`GUIDE_DocFrame.md`, `GUIDE_DocEnsurance.md`) werden als **`DOCFRAME-OUTDATED`** gemeldet – die Fehlermeldung fordert den Entwickler sogar aktiv auf, `DocFrame.update()` auszuführen und den Hinweis damit zu löschen.
  * Dokumente **ohne** erkenntnistheoretischen Hinweis (`DEV-GUIDE_DocFrame.md`, `docs/core/README.md`) bestehen `CUBIE_DOCFRAME_RULES` ohne Diagnose.

### Ursache 4 `[RISIKO]`: Fehlende zentrale Pflege-Schicht für Presets & Templates

In `src/qb_cubie/core/services/doc_frame/doc_frame.py:83-160` sind alle projektweiten Dokument-Templates (`HEADER_QUICK_NAV`, `GUIDE_ROUTER`, `SERVICE_ROUTER`, `CONTEXT_ROUTER`, `STD_HEAD_BLOCKS`, `STD_FOOTER_BLOCKS`, `CUBIE_DOC_FRAME_1..3`) direkt im Orchestrator-Modul `doc_frame.py` hartkodiert. Es gibt keine dedizierte, leicht auffindbare Single Source of Truth für Kopf-/Fuß-Bausteine und projektweite Pflicht-Texte (wie den erkenntnistheoretischen Hinweis).

### Ursache 5 `[ABWEICHUNG]`: Blinde Flecken in der Test-Suite & gebündeltes Styleguide-Modul

1. **Fehlende Äquivalenzklasse in `tests_doc_frame`:** `tests/tests_core/tests_services/tests_doc_frame/test_docframe_presets_and_update.py:14-25` prüft `_FRAME_1_DOC` ausschließlich mit **3 Segmenten** (genau einem Disclaimer). Weder ein 4-Segment-Header noch die Pflicht-Invariante des erkenntnistheoretischen Ankers sind abgedeckt – alle 46 ausgeführten Tests bleiben daher fälschlich grün.
2. **Gebündelte Verantwortlichkeiten in `tests/test_styleguide.py`:** Obwohl Commit `e3e3abea` `test_docs_code_examples` und `test_docs_frames` auf Funktionsebene getrennt hat (`tests/test_styleguide.py:124-144`), liegen statische Code-Stilprüfungen (`MODULE_LIMIT`, `FUNCTION_LIMIT`, `test_docstrings`), `DocEnsurance`-Beispielprüfung und `DocFrame`-Rahmenprüfung weiterhin in derselben Datei. Das Pausieren von `test_docs_frames` entzieht den Dokumentrahmen zudem aktuell jegliche CI-Absicherung.

---

## 3. Hypothesen, Risiken & Handlungsvorschlag (`Soll`)

### 3.1 Kritische Risiken für die Umsetzung (Hypothesen vor `Phase Red`)

* **`[RISIKO]` Hypothese H1 (Verdopplung bei Migration bestehender 3-Segment-Dokumente):**  
  Wenn ein neuer verpflichtender Block (z. B. `EpistemicNoticeBlock` / `StaticBlock`) in `STD_HEAD_BLOCKS` nach `DisclaimerSlot()` ergänzt wird, liegt der alte manuell eingefügte erkenntnistheoretische Hinweis in 36 Bestands-Dokumenten weiterhin in `segments[1]`. Ohne explizite Deduplizierung würde `DisclaimerSlot` ihn ein erstes Mal ausgeben und der neue Anker-Block ein zweites Mal.  
  *Gegenmaßnahme:* `DisclaimerSlot` muss alle Zwischensegmente `segments[1:-1]` berücksichtigen **und** den kanonischen (sowie per Marker erkannten) erkenntnistheoretischen Hinweisblock vor der Rückgabe herausfiltern, sodass er ausschließlich über den dedizierten Anker-Block gerendert wird (garantierte Idempotenz).
* **`[RISIKO]` Hypothese H2 (Leere Doppel-Trennlinien `---` / `---`):**  
  Wenn `DisclaimerSlot` leer ist, stehen in `(HeaderContentSlot(), Divider(), DisclaimerSlot(), Divider(), EPISTEMIC_NOTICE, ...)` zwei `Divider()`-Blöcke unmittelbar nebeneinander.  
  *Gegenmaßnahme:* `CenterWrap` dedupliziert konsekutive `Divider()`-Ausgaben (oder `DisclaimerSlot` rendert nur bei nicht-leerem Inhalt inkl. eigenem Trenner), sodass zwischen Header, optionalem Disclaimer, Pflicht-Anker und Quick-Nav immer genau ein `---` steht.
* **`[RISIKO]` Hypothese H3 (Rückwärtskompatibilität von `DocFrame`-Tests und -Doku-Beispielen):**  
  Die bestehenden Code-Beispiele in `docs/services/GUIDE_DocFrame.md:588-593`, `docs/dev/services/DEV-GUIDE_DocFrame.md:333-338` sowie Tests in `test_docframe_presets_and_update.py` und `test_docframe_rules_and_guards.py` konstruieren oder prüfen `STD_HEAD_BLOCKS` bzw. `CUBIE_DOC_FRAME_1`. Änderungen an `STD_HEAD_BLOCKS` müssen in der TGD-Phase *Living Documentation* synchronisiert werden.

### 3.2 Empfohlener Soll-Entwurf (Architektur & Refactoring)

| Bereich | Konkrete Soll-Maßnahme |
| :--- | :--- |
| **1. Zentrale Template-/Preset-Stelle** | Neues Modul `src/qb_cubie/core/services/doc_frame/presets.py` (o. ä.) als zentrale Pflege-Stelle für `EPISTEMIC_NOTICE_TEXT`, `STD_HEAD_BLOCKS`, `STD_FOOTER_BLOCKS`, Router und `CUBIE_DOC_FRAME_1..3` (vollständig re-exportiert über `doc_frame.py` und `__init__.py`). |
| **2. Geschützter Anker-Baustein (`frame_blocks.py`)** | Neuer `FrameBlockProtocol`-Baustein (z. B. `StaticNoticeBlock` / `FixedBlock`) für den unveränderlichen erkenntnistheoretischen Hinweis; Erweiterung von `DisclaimerSlot`, um alle optionalen Zwischensegmente `segments[1:-1]` ohne den Anker-Text verlustfrei zu bewahren und doppelte `---` zu vermeiden. |
| **3. Regel-Härtung (`doc_frame_rules.py`)** | Aktive Prüfung des Pflicht-Ankers: `DocFrameOutdated` erkennt Abweichungen automatisch über `pat.render_zone()`, sobald der Anker in `STD_HEAD_BLOCKS` verankert ist. Optional zusätzlich eine dedizierte Regel (z. B. `DocFrameAnchorMissing` / `DOCFRAME-ANCHOR-MISSING`), falls ein fehlender Anker unabhängig von allgemeiner Drift gemeldet werden soll. |
| **4. SRP-Aufteilung der Repo-Tests** | `tests/test_styleguide.py` behält reine Python-Stilmetriken; Auslagerung der Repo-Dokumentations-Gates in zwei eigene Module (`tests/test_docs_ensurance.py` und `tests/test_docs_frames.py`) sowie neue EBT-Regressionstests für 2-, 3- und 4-Segment-Header, Anker-Injektion und Idempotenz in `tests/tests_core/tests_services/tests_doc_frame/`. |
| **5. Doku-Bereinigung vor Gate-Reaktivierung** | Behebung der 13 aktuellen `CUBIE_DOCFRAME_RULES`-Befunde (insbesondere `GEMINI.md`, `CI_PLATFORM_STATUS.md`, `docs/misc/`, `docs/misc/lake/CI-Data.md` & `ANALYSIS_CI_MATRIX.md`), danach Entfernen von `@pytest.mark.skip` auf dem `DocFrame`-Repo-Test. |

### 3.3 Offene Entscheidungsfragen vor `Phase Red`

1. **Geltungsbereich `CUBIE_DOC_FRAME_2`:** Soll der erkenntnistheoretische Hinweis nur in `CUBIE_DOC_FRAME_1` & `CUBIE_DOC_FRAME_3` verankert werden, oder auch verbindlich im Kopfbereich von `CUBIE_DOC_FRAME_2` (Agenten-Berichten wie diesem Dokument)?
2. **Regel-Granularität:** Reicht `DOCFRAME-OUTDATED` als hartes Gate für fehlende/veränderte Anker-Texte aus, oder soll eine eigenständige Regel-ID (`DOCFRAME-ANCHOR-MISSING`) in `CUBIE_DOCFRAME_RULES` ergänzt werden?
3. **Umgang mit `docs/misc/lake/CI-Data.md` & `GEMINI.md`:** Sollen beide Dateien regulär gerahmt/synchronisiert oder über `DOC_EXCLUDES` ausgenommen werden?

---

## 4. Verifikationsprotokoll

Alle Prüfungen wurden rein lesend gegen den unveränderten Codebestand (`c12d6186`) ausgeführt:

| Prüfschritt | Kommando | Ergebnis |
| :--- | :--- | :--- |
| Git-Status & Historie | `git status -s && git log -n 5 --oneline` | `main` @ `c12d6186`; lokale Änderungen nur `ANALYSIS.md` & `docs/GEMINI-1.md -> GEMINI.md` |
| Commit-Forensik | `git show e3e3abea` | Bestätigt Löschung des Hinweises (`-11` Zeilen) in `docs/dev/services/DEV-GUIDE_DocFrame.md` |
| In-Memory-Dry-Run `DocFrame` | `.venv/bin/python -c "... df._render_file_frames(...) ..."` | `48` Dateien geprüft; `38 -> 36` mit Hinweis; unmittelbarer Verlust in `GUIDE_DocFrame.md` & `GUIDE_DocEnsurance.md` (beide 4 Segmente) |
| Dry-Run `CUBIE_DOCFRAME_RULES` | `.venv/bin/python -c "... DocEnsurance(..., rules=CUBIE_DOCFRAME_RULES, reporter=None).run()"` | `passed=False`, `13` Diagnosen (`3`× `MISSING`, `1`× `BROKEN-ROUTE`, `9`× `OUTDATED`) |
| Bestehende Test-Suite | `.venv/bin/python -m pytest -q tests/test_styleguide.py tests/tests_core/tests_services/tests_doc_frame/ tests/tests_cli/test_docframe_cli.py` | **`46 passed, 2 skipped`** (`25.54s`; `test_function_size` & `test_docs_frames` übersprungen) |

<!-- qb:frame id="CUBIE_DOC_FRAME_2" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./docs/GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./docs/README.md)  
[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./docs/dev/README.md)  
[↦ | Core-Internals | ↤](./docs/dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
