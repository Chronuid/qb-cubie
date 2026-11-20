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

### [BUG-001] `PyVenv` verändert Testdaten durch eigene IPC-Dateien im Workspace

- **Status:** Offen *(Gutachten-Befund B1, P1)*
- **Schweregrad:** Hoch
- **Bereich:** `src/qb_cubie/arenas/pyvenv.py` (`setup`, `_setup_ipc_files`, `_teardown_ipc_files`)
- **Umgebung / Version:** reproduziert ab `v0.0.3`, unverändert in `v0.0.9` (Linux, Python 3.13)

**Ist-Verhalten:**  
`PyVenv` legt seine Austauschdateien (`ipc_in<suffix>`, `ipc_out<suffix>`), das Hilfsmodul `_cubie_phantom.py` sowie `.venv/` direkt im geprüften `workspace_path` ab. Dadurch teilen sich Infrastruktur und Testdaten denselben Namensraum:
1. Eine über `pre.fs` bereitgestellte `ipc_in.<suffix>` wird vor dem Target-Aufruf still durch die IPC-Nutzlast überschrieben.
2. Eine über `pre.fs` bereitgestellte `ipc_out.<suffix>` wird nach der Ausführung durch `_teardown_ipc_files()` gelöscht.
3. Vollständige Workspace-Vergleiche (z. B. gegen ein leeres Referenzverzeichnis) schlagen durch `.venv/` und `_cubie_phantom.py` fehl.

**Soll-Verhalten:**  
Infrastrukturdateien (`ipc_in`, `ipc_out`, `_cubie_phantom.py`, `.venv`) liegen getrennt vom fachlichen Arbeitsbereich (analog zu den IPC-Dateien in `TempFS`). Bereitgestellte Testdaten werden weder überschrieben noch gelöscht.

**Reproduktion:**  
EBT-Vertrag mit `PyVenv` und `PickleCodec` ausführen, bei dem `pre.fs` eine Datei `ipc_in.pkl` (z. B. 3 Bytes) oder `ipc_out.pkl` bereitstellt: `os.path.getsize("ipc_in.pkl")` beobachtet die serialisierte IPC-Nutzlast statt 3 Bytes; `ipc_out.pkl` fehlt beim anschließenden Dateivergleich (`Path not found. Arena: False, Host: True`).

**Workaround:**  
In `PyVenv`-Tests keine Dateien namens `ipc_in.*`, `ipc_out.*` oder `_cubie_phantom.py` im Workspace-Root ablegen und Dateivergleiche auf fachliche Unterverzeichnisse eingrenzen.

**Hinweise / Ursache:**  
Quelle: [`GUTACHTEN.md` (§ 6.1, B1)](./GUTACHTEN.md#61-b1-pyvenv-verändert-testdaten-durch-eigene-ipc-dateien).  
Empfohlene Korrektur: IPC-Dateien, Hilfsmodule und `.venv` außerhalb des geprüften Workspace führen und Namenskollisionen sowie vollständige Verzeichnisvergleiche durch Regressionstests absichern.

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

## Bekannte Einschränkungen / Plattform-Spezifika

Die folgenden Rahmenbedingungen sind dokumentiertes Verhalten (keine unerwarteten Bugs), aber für den produktiven Einsatz zu beachten:

- **Keine OS-Sicherheitsgrenze in Core-Arenen:** `TempFS` und `PyVenv` laufen mit Benutzerrechten des Hosts und eignen sich nur für vertrauenswürdigen Code (siehe [Arena-Management](./docs/core/GUIDE_Arena-Management.md)).
- **Windows-CI vorübergehend eingefroren:** Übliche POSIX-Python-Einstiegsskripte werden in `PyVenv` auf den Klon angepasst; zusätzliche native Windows-`.exe`-Launcher werden vor Target-Ausführung abgelehnt. Die vollständige Testsuite läuft in der CI unter Linux, macOS erhält die Wheel-Prüfung, und Windows-Checks sind vorübergehend eingefroren (siehe [CI_PLATFORM_STATUS.md](./docs/CI_PLATFORM_STATUS.md)).
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
