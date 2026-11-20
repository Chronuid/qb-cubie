<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Bekannte Fehler und Einschränkungen (`KNOWN_ISSUES.md`)

![Cubie](./docs/.assets/cubie-logo-written.png)

Zentrale Übersicht über offene Bugs und bekannte Einschränkungen in `qb-cubie`.  
Hinweise zum Eintragen und Pflegen neuer Bugs stehen im [DEV-GUIDE: Bugs dokumentieren](./docs/dev/DEV-GUIDE_Write-down-the-bugs.md).

---

---

[README](./README.md) • [QA-Handbuch](./docs/GUIDE_Quality-Assurance.md) • [DocEnsurance](./docs/services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Offene Bugs

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

## Bekannte Einschränkungen / Plattform-Spezifika

Die folgenden Rahmenbedingungen sind dokumentiertes Verhalten (keine unerwarteten Bugs), aber für den produktiven Einsatz zu beachten:

- **Keine OS-Sicherheitsgrenze in Core-Arenen:** `TempFS` und `PyVenv` laufen mit Benutzerrechten des Hosts und eignen sich nur für vertrauenswürdigen Code (siehe [Arena-Management](./docs/core/GUIDE_Arena-Management.md)).
- **Windows-CI vorübergehend eingefroren:** Übliche POSIX-Python-Einstiegsskripte werden in `PyVenv` auf den Klon angepasst; zusätzliche native Windows-`.exe`-Launcher werden vor Target-Ausführung abgelehnt. Die vollständige Testsuite läuft in der CI unter Linux, macOS erhält die Wheel-Prüfung, und Windows-Checks sind vorübergehend eingefroren (siehe [CI_PLATFORM_STATUS.md](./docs/CI_PLATFORM_STATUS.md)).
- **Prädikate und externe Daten:** Erwartungsobjekte müssen tief kopierbar sein. Funktionen behalten Referenzen auf Closures, globale Variablen und externe Ressourcen; deren Zustand wird nicht eingefroren. Historische Traces archivieren keine Dateiinhalte.
- **PyVenv-Importhilfen (`decontams`):** `decontams` ersetzt nur ausdrücklich gewählte Module. Ohne installiertes `pytest` unterstützt eine begrenzte Importhilfe dessen Testdeklarationen; Laufzeitaufrufe benötigen die echte Bibliothek.
- **Grafischer Reviewer (`tkinter`):** Nur der Start der GUI benötigt `tkinter` und eine grafische Umgebung. Paketimport, EBT und Headless-RBT funktionieren ohne Tk.
- **Dateivergleich:** Inhalte werden bei jedem Vergleich blockweise neu gelesen (kein persistenter Vergleichscache); gleichzeitig laufende Schreibzugriffe ergeben jedoch keine atomare Momentaufnahme.
- **Vertragssemantik & Reporter:** Mehrere Eingänge teilen dieselbe Zielmenge (korrelierte Ein-/Ausgabepaare benötigen getrennte Verträge). `JsonReporter` persistiert Ergebnisse, wirft aber selbst keine fachliche Assertion. Details stehen in der [Semantikreferenz](./docs/core/GUIDE_Contract-Semantics.md).

---

## Behoben (Archiv)

### [BUG-001] `PyVenv` verändert Testdaten durch eigene IPC-Dateien im Workspace

- **Status:** Behoben *(nach v0.0.9 / TGD-Zyklus 1)*
- **Schweregrad:** Hoch
- **Bereich:** `src/qb_cubie/arenas/pyvenv.py`, `src/qb_cubie/arenas/codecs.py`
- **Umgebung / Version:** reproduziert ab `v0.0.3` bis `v0.0.9`; behoben ab Entwicklungsstand nach `v0.0.9`

**Lösung:**  
`PyVenv` trennt den fachlichen Workspace (`_root_path/workspace/`), die geklonte Umgebung (`_root_path/.venv/`) sowie die temporäre IPC- und Phantom-Ablage (`TemporaryDirectory(prefix="ipc_", dir=self._root_path)`) strikt voneinander, startet Kindprozesse mit `python -P -c` unter Herausfiltern von `""`/`"."` aus `PYTHONPATH`, und die Codecs lösen `_cubie_phantom` sowie das IPC-Verzeichnis nach dem Transport-Import ab, bevor `os.getcwd()` an `sys.path[0]` eingehängt wird. Vollständige Dokumentation und Verifikationsverlauf unter [`tests/tests_arena/TGD_1.md`](./tests/tests_arena/TGD_1.md) sowie [`GUTACHTEN.md` (§ 6.1, B1)](./GUTACHTEN.md#61-b1-pyvenv-verändert-testdaten-durch-eigene-ipc-dateien).

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./docs/GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerübersicht & Internals | ↤](./docs/dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
