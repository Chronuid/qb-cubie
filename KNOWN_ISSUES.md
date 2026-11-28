<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Bekannte Fehler und Einschränkungen (`KNOWN_ISSUES.md`)

![Cubie](./docs/.assets/cubie-logo-written.png)

Zentrale Übersicht über offene Bugs und bekannte Einschränkungen in `qb-cubie`.  
Hinweise zum Eintragen und Pflegen neuer Bugs stehen im [DEV-GUIDE: Bugs dokumentieren](./docs/dev/DEV-GUIDE_Write-down-the-bugs.md); behobene Bugs werden im [Archiv behobener Bugs](./docs/misc/lake/SOLVED_ISSUES.md) bzw. im [CHANGELOG](./CHANGELOG.md) geführt.

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](./README.md) • [QA-Handbuch](./docs/GUIDE_Quality-Assurance.md) • [DocEnsurance](./docs/services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Offene Bugs

### [BUG-008] `DocFrame`: `foot`-Zone-Kopplung, `update()`-Überschreibung kuratierter Footer & 1-Tupel-Regelübergabe

- **Status:** Offen
- **Schweregrad:** Mittel
- **Bereich:** `src/qb_cubie/core/services/doc_frame/doc_frame_rules.py` (`DocFrameOutdated`, `_should_skip_span`, `_has_missing_zones`), `src/qb_cubie/core/services/doc_frame/doc_frame.py` (`DocFrame.check`) & `src/qb_cubie/core/services/doc_ensurance/doc_ensurance.py` (`DocEnsurance`)
- **Umgebung / Version:** `v0.1.2` / Commit `8ff3d79e`, Python `3.13`, Linux (plattformunabhängig)

**Ist-Verhalten:**  
1. `DocFrameOutdated` (`doc_frame_rules.py`) erfordert aktuell zwingend `allow_empty_foot=True`, sobald `DocFrameFootLinks(severity="warning")` genutzt wird. Zudem unterdrückt `_should_skip_span()` `DOCFRAME-OUTDATED` nur bei komplett linkfreien `foot`-Zonen (`not _has_markdown_links(span.inner_content)`), sodass eigene kuratierte Markdown-Links in `zone="foot"` (oder ein `DocFrame.update()`-Lauf gegen `STD_FOOTER_BLOCKS`) bei `CUBIE_DOC_FRAME_2` und `CUBIE_DOC_FRAME_3` weiterhin einen `DOCFRAME-OUTDATED`-Error auslösen; `DocFrameMissing` (`_has_missing_zones()`) verlangt die `foot`-Tags zudem weiterhin hart als `error`.
2. `DocFrame.check()` und `DocEnsurance` akzeptieren `DocFrameRuleSet` bzw. `DocRuleSet` derzeit nur verpackt als 1-Tupel (`rules=(REPO_DOCFRAME_RULES,)` bzw. `rules=(REPO_DOC_RULES,)`), statt eine einzelne Regelset-Instanz direkt entgegenzunehmen.

**Soll-Verhalten:**  
1. Bei Presets mit optionaler/abgeschwächter `foot`-Zone (`CUBIE_DOC_FRAME_2`, `CUBIE_DOC_FRAME_3`) bleiben kuratierte eigene Markdown-Links in `zone="foot"` (oder das bewusste Weglassen der `foot`-Zone bei `CUBIE_DOC_FRAME_3`, vgl. archivierten [`BUG-005`](./docs/misc/lake/SOLVED_ISSUES.md)) ohne `DOCFRAME-OUTDATED`-Error zulässig und werden von `DocFrame.update()` nicht still mit `STD_FOOTER_BLOCKS` überschrieben.
2. `DocFrame.check(..., rules=...)` und `DocEnsurance(..., rules=...)` akzeptieren `DocFrameRuleSet` bzw. `DocRuleSet` sowohl direkt als Einzelinstanz als auch innerhalb einer Sequenz.

**Reproduktion:**  
1. In einem `CUBIE_DOC_FRAME_2`-Dokument (z. B. einem Bericht) eigene kuratierte Links in `zone="foot"` ablegen und `DocFrame.check(rules=(REPO_DOCFRAME_RULES,))` ausführen $\to$ `DOCFRAME-OUTDATED` (`error`).
2. `DocFrame.check(rules=REPO_DOCFRAME_RULES)` oder `DocEnsurance(rules=REPO_DOC_RULES)` ohne 1-Tupel-Wrapper aufrufen.

**Workaround:**  
Bei `CUBIE_DOC_FRAME_2` die `foot`-Zone leer lassen (`allow_empty_foot=True`) bzw. `DocFrame.update()` die Standard-Footer rendern lassen; `DocFrameRuleSet` und `DocRuleSet` als 1-Tupel `(REPO_DOCFRAME_RULES,)` / `(REPO_DOC_RULES,)` übergeben.

**Hinweise / Ursache:**  
`_should_skip_span()` in `doc_frame_rules.py` prüft `self.allow_empty_foot and span.zone == "foot" and not _has_markdown_links(span.inner_content)` statt eines expliziten Opt-outs für kuratierte oder optionale Footer; die `rules`-Normalisierung in `DocFrame.check()` / `DocEnsurance` prüft bislang auf `Sequence` statt auch `DocFrameRuleSet` / `DocRuleSet` direkt zu akzeptieren.

---

### [BUG-009] GitHub Actions CI-Matrix läuft bei reinen Dokumentations-Änderungen vollständig durch

- **Status:** Offen
- **Schweregrad:** Niedrig
- **Bereich:** `.github/workflows/ci.yml`
- **Umgebung / Version:** `v0.1.2`, GitHub Actions (`ubuntu-24.04`, `macos-15`, Python `3.13` & `3.14`)

**Ist-Verhalten:**  
Bei Pushes und Pull Requests, die ausschließlich Dokumentationsdateien (`docs/**`, `*.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md`) betreffen, startet `.github/workflows/ci.yml` die komplette CI-Test-Matrix (`Wheel` und `Repository` über alle aktiven Plattform- und Python-Kombinationen inklusive `slow`-Tests).

**Soll-Verhalten:**  
Reine Dokumentations-Änderungen ohne Code- oder Test-Diffs außerhalb der Doku-Gates triggern einen schlanken Doku-Gate-Lauf (`docframe`, `docensurance`, `tests/test_doc_frame.py`, `tests/test_doc_ensurance.py`), statt die vollständige Multi-OS-Testmatrix zu blockieren.

**Reproduktion:**  
Einen Commit oder Pull Request erstellen, der ausschließlich Dateien unter `docs/` oder Root-Markdown-Dateien (`README.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md`) ändert, und die ausgelösten Jobs in `.github/workflows/ci.yml` prüfen.

**Workaround:**  
Vor dem Push lokal `.venv/bin/python -m pytest -q tests/test_doc_frame.py tests/test_doc_ensurance.py` ausführen; auf GitHub den vollständigen Matrix-Durchlauf abwarten.

**Hinweise / Ursache:**  
In `.github/workflows/ci.yml` fehlen `paths`/`paths-ignore`-Filter bzw. eine vorgeschaltete Change-Detection (`dorny/paths-filter` oder `git diff`), die reine Doku-Commits auf ein dediziertes `docs`-Gate routet.

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

[↦ | Service-Core | ↤](./docs/services/GUIDE_Service-Core.md)  
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
