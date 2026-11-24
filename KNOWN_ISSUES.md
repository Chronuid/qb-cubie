<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Bekannte Fehler und Einschränkungen (`KNOWN_ISSUES.md`)

![Cubie](./docs/.assets/cubie-logo-written.png)

Zentrale Übersicht über offene Bugs und bekannte Einschränkungen in `qb-cubie`.  
Hinweise zum Eintragen und Pflegen neuer Bugs stehen im [DEV-GUIDE: Bugs dokumentieren](./docs/dev/DEV-GUIDE_Write-down-the-bugs.md); behobene Bugs werden im [Archiv behobener Bugs](./docs/misc/lake/SOLVED_ISSUES.md) bzw. im [CHANGELOG](./CHANGELOG.md) geführt.

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
>
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ...heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](./README.md) • [QA-Handbuch](./docs/GUIDE_Quality-Assurance.md) • [DocEnsurance](./docs/services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Offene Bugs

### [BUG-007] `DocFrame.update()` überschreibt den Hinweis zur erkenntnistheoretischen Grenze

- **Status:** Offen
- **Schweregrad:** Hoch
- **Bereich:** `src/qb_cubie/core/services/doc_frame/doc_frame.py` (`DocFrame.update`), `src/qb_cubie/core/services/doc_frame/doc_frame_rules.py`, `tests/test_styleguide.py`
- **Umgebung / Version:** `v0.1.0` / Commit `fd36cca9`, Python `3.13`, Linux (plattformunabhängig)

**Ist-Verhalten:**  
Beim Ausführen von `DocFrame.update()` wird der Hinweis zur erkenntnistheoretischen Grenze (`> [!Note]` – Karl Poppers kritischer Rationalismus / Fallibilismus) im Kopfbereich (`zone="head"`) der Dokumente überschrieben bzw. entfernt.

**Soll-Verhalten:**  
Der Hinweis zur erkenntnistheoretischen Grenze darf durch `DocFrame.update()` niemals entfernt oder überschrieben werden. Er soll im Gegenteil als fester, verpflichtender Anker immer Bestandteil der Dokumentköpfe sein und durch die `DocFrame`-Regeln aktiv geprüft werden.

**Reproduktion:**  
1. Dokument mit vorhandenem `> [!Note]`-Hinweis zur erkenntnistheoretischen Grenze in `zone="head"` (z. B. `KNOWN_ISSUES.md` oder `docs/dev/DEV-GUIDE_Write-down-the-bugs.md`) prüfen.
2. `DocFrame.update()` ausführen:
```bash
.venv/bin/python -c "from qb_cubie.core.services.doc_frame import DocFrame; DocFrame.update()"
```
3. `git diff` zeigt, dass der Hinweis zur erkenntnistheoretischen Grenze im Kopfbereich überschrieben wurde.

**Hinweise / Ursache:**  
- Der Hinweis zur erkenntnistheoretischen Grenze ist aktuell nicht als geschützter/verpflichtender Anker-Block in den `DocFrame`-Head-Templates verankert.
- **Architektur-/Refactoring-Wunsch für den Fix:** Idealerweise sollte die Behebung mit einer saubereren Aufteilung der Test-Module einhergehen – je ein eigenes Test-Modul für `DocEnsurance` und ein eigenes Test-Modul für `DocFrame` (statt gemeinsamer Bündelung in `tests/test_styleguide.py`) – sowie einer zentralen Stelle zum Pflegen und Bearbeiten der Dokumentköpfe und -füße (`head`/`foot`).

---

### [BUG-002] `PytestReporter` verliert Assertions unter optimiertem Python (`python -O`)

- **Status:** Offen *(Gutachten-Befund B2, P1)*
- **Schweregrad:** Hoch
- **Bereich:** `src/qb_cubie/reporter.py` (`PytestReporter.report`)
- **Umgebung / Version:** reproduziert ab `v0.0.3`, unverändert in `v0.0.9` (alle Plattformen)

**Ist-Verhalten:**  
`PytestReporter.report()` verwendet normale `assert`-Anweisungen, um Fehlschläge von EBT, RBT und Services (z. B. `DocEnsurance`) durchzusetzen. Wird Python mit `-O` gestartet, entfallen diese `assert`-Anweisungen vollständig: `result.evaluation` ist zwar `False`, aber `.run()` wirft keine Exception und `python -O -m pytest` meldet einen fehlgeschlagenen Vertrag als `1 passed` (Exitcode `0`).

**Soll-Verhalten:**  
Negative EBT-, RBT- und Service-Ergebnisse lösen im `PytestReporter` unabhängig vom Python-Optimierungsmodus deterministisch eine `AssertionError`-Exception aus, sodass pytest mit einem Exitcode ≠ 0 abbricht.

**Reproduktion:**  
```bash
.venv/bin/python -O -c "from qb_cubie import EBT, WorldState; r = EBT(target=lambda: 1, post=WorldState(returns=2)).run(); print(r.evaluation)"
```
Ausgabe: `False` ohne `AssertionError` (gleiches Verhalten bei abgelehntem `RBT` mit `HeadlessReviewer(answer=False)` und fehlgeschlagenem `DocEnsurance`).

**Workaround:**  
Tests nicht mit `python -O` / `PYTHONOPTIMIZE=1` ausführen oder zusätzlich `result.evaluation` explizit prüfen.

**Hinweise / Ursache:**  
Quelle: [`GUTACHTEN.md` (§ 6.2, B2)](./GUTACHTEN.md#62-b2-fehlerweitergabe-verschwindet-unter-optimiertem-python).  
Empfohlene Korrektur: `assert ...` in `PytestReporter.report()` durch explizites `if not ...: raise AssertionError(...)` ersetzen und Regressionstests für EBT, RBT und Services in einem `python -O`-Kindprozess ergänzen.

---

### [BUG-003] `CstLinter.check()` gibt für nicht existierende Pfade stumm `[]` zurück

- **Status:** Offen *(Gutachten-Befund B3, P2)*
- **Schweregrad:** Mittel
- **Bereich:** `src/qb_cubie/linter.py` (`CstLinter.check`)
- **Umgebung / Version:** reproduziert ab `v0.0.3`, unverändert in `v0.0.9` (alle Plattformen)

**Ist-Verhalten:**  
Wird `CstLinter.check()` ein nicht existierendes `Path`-Objekt übergeben, greift weder `target.is_file()` noch `target.is_dir()`. Die Methode läuft ohne Fehler durch und liefert eine leere Diagnoseliste `[]`. Ein Tippfehler oder falsch konfigurierter Pfad ist damit nicht von einer erfolgreichen Prüfung ohne Befunde zu unterscheiden.

**Soll-Verhalten:**  
Nicht existierende oder ungeeignete `Path`-Ziele werden ausdrücklich mit einer Exception (z. B. `FileNotFoundError`) abgelehnt.

**Reproduktion:**  
```bash
.venv/bin/python -c "from pathlib import Path; from qb_cubie import CstLinter; print(CstLinter([]).check(Path('/nicht/vorhanden.py')))"
```
Ausgabe: `[]`.

**Workaround:**  
Vor dem Aufruf von `CstLinter.check(path)` manuell `path.exists()` prüfen.

**Hinweise / Ursache:**  
Quelle: [`GUTACHTEN.md` (§ 6.3, B3)](./GUTACHTEN.md#63-b3-fehlende-linterziele-werden-als-leeres-ergebnis-zurückgegeben).  
Empfohlene Korrektur: Ungültige Pfade in `CstLinter.check()` explizit ablehnen und optional bei Verzeichnisprüfungen zwischen „keine `.py`-Dateien gefunden“ und „Dateien ohne Befund geprüft“ unterscheiden.

---

### [BUG-004] `DocFrame.update()` aktualisiert keine verstreuten relativen Links außerhalb generierter Router-/Footer-Blöcke bei Doku-Umbauten

- **Status:** Offen
- **Schweregrad:** Mittel
- **Bereich:** `src/qb_cubie/services/doc_frame/doc_frame.py` (`DocFrame.update`, `_render_file_frames`) & `src/qb_cubie/services/doc_frame/doc_frame_rules.py` (`DocFrameBrokenRoute`)
- **Umgebung / Version:** `v0.0.9` / Commit `561338af`, Python `3.13`, Linux (plattformunabhängig)

**Ist-Verhalten:**  
Wenn Markdown-Dokumente in einen neuen Unterordner verschoben werden (z. B. `docs/GUIDE_*.md` $\to$ `docs/core/GUIDE_*.md`), synchronisiert `DocFrame.update()` ausschließlich die automatisch generierten Navigations- und Router-Blöcke (`HEADER_QUICK_NAV`, `GUIDE_ROUTER`, `CONTEXT_ROUTER`, `AUTO_INDEX_ROUTER`). Alle übrigen relativen Markdown-Links bleiben unberührt:
1. Relative Links im Fließtext (Body) anderer Dokumente zeigen weiterhin auf den alten Pfad und brechen still (z. B. `[Vertragssemantik](GUIDE_Contract-Semantics.md)` statt `core/GUIDE_Contract-Semantics.md`).
2. Relative Links innerhalb geschützter `HeaderContentSlot`-Intros (z. B. `[Gutachten](../GUTACHTEN.md)` in einer verschobenen Datei oder `[Semantikreferenz](../GUIDE_Contract-Semantics.md)` in `docs/dev/*.md`) werden ebenfalls nicht angepasst – bei verschobenen Dokumenten schlägt `DocFrameBrokenRoute` fehl, während kaputte Body-Links gar nicht erst gemeldet werden.
3. Beim Umzug der fünf Core-Guides nach `docs/core/` mussten verstreute Links über 19 Dateien hinweg manuell nachgezogen werden.

**Soll-Verhalten:**  
`DocFrame.update()` löst bei Doku-Umbauten anhand des `DocumentCatalog` (eindeutige Dateinamen bzw. verschobene Ziele) veraltete relative Markdown-Links – sowohl in geschützten Head-Slots als auch im Dokumentkörper (außerhalb von Code-Fences) – automatisch auf die neuen relativen Pfade auf (inkl. Erhalt von `#anchor`-Fragmenten) oder meldet mehrdeutige/tote Links konsistent über `DocFrameBrokenRoute`.

**Reproduktion:**  
1. Beliebiges Dokument mit eingehenden Fließtext-Links in ein Unterverzeichnis verschieben (z. B. `git mv docs/GUIDE_Linter.md docs/core/GUIDE_Linter.md`).
2. `DocFrame.update()` ausführen:
```bash
.venv/bin/python -c "from qb_cubie.services import DocFrame; DocFrame.update()"
```
3. Ergebnis: Footer-Routen werden aktualisiert, alle relativen Fließtext- und Intro-Links auf `GUIDE_Linter.md` in anderen Dokumenten sowie ausgehende relative Links in der verschobenen Datei zeigen weiterhin auf den alten, nun ungültigen Pfad.

**Workaround:**  
Nach dem Verschieben von Dokumenten alle verstreuten Links im Repository per Suche/Skript manuell umschreiben und anschließend `DocFrame.update()` sowie einen eigenen Broken-Link-Check über den Dokumentkörper ausführen.

**Hinweise / Ursache:**  
`DocFrame._render_file_frames()` fasst per Design ausschließlich `<!-- qb:frame ... -->`-Spans an und lässt `HeaderContentSlot`-Fließtext sowie den Dokumentkörper unangetastet; `DocFrameBrokenRoute` prüft zudem nur Links innerhalb von `FrameSpan.inner_content`. Da `DocumentCatalog` in Pass 1 bereits alle Markdown-Dateien im Repository kennt, ließe sich ein optionaler Link-Healer (z. B. auf Basis eindeutiger Basenames oder eines expliziten Rename-Mappings) sauber in Pass 2 integrieren.

---

### [BUG-005] `CUBIE_DOC_FRAME_3`-Routing-Dokumente (`README.md`) erzwingen eine redundante `foot`-Zone

- **Status:** Offen
- **Schweregrad:** Niedrig
- **Bereich:** `src/qb_cubie/services/doc_frame/doc_frame.py` (`CUBIE_DOC_FRAME_3`) & `src/qb_cubie/services/doc_frame/doc_frame_rules.py` (`_has_missing_zones`, `DocFrameMissing`)
- **Umgebung / Version:** `v0.0.9` / Commit `561338af`, Python `3.13`, Linux (plattformunabhängig)

**Ist-Verhalten:**  
`_has_missing_zones()` erzwingt für jedes Dokument pauschal sowohl eine `head`- als auch eine `foot`-Zone (`if "head" not in zones or "foot" not in zones`), und das Preset `CUBIE_DOC_FRAME_3` konfiguriert `foot=STD_FOOTER_BLOCKS`. Dadurch müssen reine Routing-Dokumente (z. B. `docs/core/README.md`, `docs/dev/README.md`, `docs/misc/README.md`) zusätzlich zu ihrer `zone="router"`-Übersichtstabelle noch eine vollständige `zone="foot"`-Navigation mitführen, die das lokale Routing erneut dupliziert. Fehlt `zone="foot"`, bricht `DocFrameMissing` mit `DOCFRAME-MISSING` ab.

**Soll-Verhalten:**  
Routing-Dokumente mit `CUBIE_DOC_FRAME_3` benötigen keine `foot`-Zone (bzw. `foot` ist für `FramePattern`-Presets ohne konfigurierte `foot`-Blöcke optional), da diese Dokumente das Routing bereits selbst über `zone="router"` abbilden. `_has_missing_zones()` sollte eine Zone nur dann als Pflicht prüfen, wenn das zugehörige `FramePattern` für diese Zone auch Blöcke definiert (`pat.head`, `pat.router`, `pat.foot`).

**Reproduktion:**  
1. In einem `CUBIE_DOC_FRAME_3`-Dokument (z. B. `docs/core/README.md`) den `<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->`-Block entfernen.
2. `DocEnsurance` mit `CUBIE_DOCFRAME_RULES` ausführen:
```bash
.venv/bin/python -m pytest tests/test_styleguide.py -k "test_docs_code_examples"
```
3. Ergebnis: `[DOCFRAME-MISSING] ... Document is missing required 'head' or 'foot' qb:frame block.`

**Workaround:**  
In `CUBIE_DOC_FRAME_3`-Routing-Dokumenten vorerst weiterhin eine `zone="foot"`-Sektion mitführen.

**Hinweise / Ursache:**  
In `src/qb_cubie/services/doc_frame/doc_frame_rules.py` prüft `_has_missing_zones()` die Existenz von `"head"` und `"foot"` hartkodiert statt dynamisch anhand von `bool(pat.head)` / `bool(pat.foot)` (wie es für `pat.router` bereits geschieht). Zudem weist `CUBIE_DOC_FRAME_3` in `doc_frame.py` derzeit `foot=STD_FOOTER_BLOCKS` statt `foot=()` zu.

---

### [BUG-006] `tests/test_styleguide.py::test_function_size` unterstützt keine `# noqa`-Ausnahmekommentare mit Begründung

- **Status:** Offen *(Workaround aktiv via `@pytest.mark.skip`)*
- **Schweregrad:** Niedrig
- **Bereich:** `tests/test_styleguide.py` (`test_function_size`)
- **Umgebung / Version:** `v0.0.10`, Python `3.13`, plattformunabhängig

**Ist-Verhalten:**  
`test_function_size` prüft starr `len(body_lines(source, node)) > FUNCTION_LIMIT` (`12`) ohne Möglichkeit, einzelne Funktionen temporär und begründet per `# noqa`-Kommentar (z. B. `# noqa: function-size -- ...`) auszusetzen. Dadurch lässt sich etwa `src/qb_cubie/ebt.py:618` (`_validate_wrapper_keys`, 14 Zeilen) nicht gezielt pausieren, während die nächste Mutation des `ebt.py`-Moduls noch genauer durchdacht wird.

**Soll-Verhalten:**  
`test_function_size` (und perspektivisch auch weitere Styleguide-Checks in `tests/test_styleguide.py`) erkennt explizite `# noqa`-Kommentare an der Funktionsdefinition (idealerweise mit verpflichtender Begründung), sodass begründete, zeitlich begrenzte Ausnahmen feingranular möglich sind, ohne den gesamten Test global zu überspringen.

**Reproduktion:**  
```bash
.venv/bin/python -m pytest -q tests/test_styleguide.py -k "test_function_size"
```
Ohne `@pytest.mark.skip` schlägt der Test an `src/qb_cubie/ebt.py:618` (`_validate_wrapper_keys`: 14 body lines, maximum 12) fehl, auch wenn ein `# noqa`-Kommentar gesetzt ist.

**Workaround:**  
`tests/test_styleguide.py::test_function_size` ist bis auf Weiteres mit `@pytest.mark.skip` pausiert (Begründung: die nächste Mutation vom `ebt.py`-Modul wird noch genauer durchdacht).

**Hinweise / Ursache:**  
`body_lines()` filtert `tokenize.COMMENT` heraus und `test_function_size()` wertet die Kommentar-Tokens auf der `def`-Zeile derzeit nicht aus.

---

## Bekannte Einschränkungen / Plattform-Spezifika

Die folgenden Rahmenbedingungen sind dokumentiertes Verhalten (keine unerwarteten Bugs), aber für den produktiven Einsatz zu beachten:

- **Keine OS-Sicherheitsgrenze in Core-Arenen:** `TempFS` und `PyVenv` laufen mit Benutzerrechten des Hosts und eignen sich nur für vertrauenswürdigen Code (siehe [Arena-Management](./docs/core/GUIDE_Arena-Management.md)).
- **Plattformabdeckung & unterstützte Venv-Launcher (Linux & macOS Tier 1 aktiv, Windows-CI vorübergehend eingefroren):** Die vollständige Testsuite (`Wheel` + `Repository`) ist in [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) für Linux (`ubuntu-24.04`) und macOS (`macos-15`) aktiviert und grün (`Python 3.13` & `3.14`), inkl. Multi-Platform-Mypy (`linux`/`darwin`/`win32`) und LF-invarianter Benchmark-Templates. Die Windows-CI (`windows-2022`) ist nach verbleibenden Windows-Befunden (dokumentiert in [`docs/misc/lake/CI-Data.md`](docs/misc/lake/CI-Data.md) und [CI_PLATFORM_STATUS.md](CI_PLATFORM_STATUS.md)) vorübergehend aus der aktiven Matrix eingefroren. In `PyVenv` werden neben POSIX-Shebangs/-Trampolinen (inkl. CRLF) auch Windows-`python.exe`/`pythonw.exe`-Text-Shebangs, verifizierte `uv`-PE-Ressourcen-Trampolines und `distlib`/`pip`-Wrapper kontrolliert auf den Klon angepasst; beliebige sonstige native `.exe`-Binaries sowie unbekannte `#!`-Skripte bleiben bewusst mit `RuntimeError` ausgeschlossen. Intrinsische OS-Checks (`/proc`-Watchdog auf Linux, `SIGKILL`-Crash-Check auf POSIX, nativer `cowsay.exe`-Test auf Windows) laufen plattformbezogen (siehe [CI_PLATFORM_STATUS.md](CI_PLATFORM_STATUS.md)).
- **Prädikate und externe Daten:** Erwartungsobjekte müssen tief kopierbar sein. Funktionen behalten Referenzen auf Closures, globale Variablen und externe Ressourcen; deren Zustand wird nicht eingefroren. Historische Traces archivieren keine Dateiinhalte.
- **PyVenv-Importhilfen (`decontams`):** `decontams` ersetzt nur ausdrücklich gewählte Module. Ohne installiertes `pytest` unterstützt eine begrenzte Importhilfe dessen Testdeklarationen; Laufzeitaufrufe benötigen die echte Bibliothek.
- **Grafischer Reviewer (`tkinter`):** Nur der Start der GUI benötigt `tkinter` und eine grafische Umgebung. Paketimport, EBT und Headless-RBT funktionieren ohne Tk.
- **Dateivergleich:** Inhalte werden bei jedem Vergleich blockweise neu gelesen (kein persistenter Vergleichscache); gleichzeitig laufende Schreibzugriffe ergeben jedoch keine atomare Momentaufnahme.
- **Vertragssemantik & Reporter:** Mehrere Eingänge teilen dieselbe Zielmenge (korrelierte Ein-/Ausgabepaare benötigen getrennte Verträge). `JsonReporter` persistiert Ergebnisse, wirft aber selbst keine fachliche Assertion. Details stehen in der [Semantikreferenz](./docs/core/GUIDE_Contract-Semantics.md).

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

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
