<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Archiv behobener Bugs (`SOLVED_ISSUES.md`)

![Cubie](../../.assets/cubie-logo-written.png)

Separates Archiv für behobene Bugs aus [`KNOWN_ISSUES.md`](../../../KNOWN_ISSUES.md), bevor bzw. neben ihrer Übernahme in das [`CHANGELOG.md`](../../../CHANGELOG.md).  
Details zum Ablauf stehen im [DEV-GUIDE: Bugs dokumentieren](../../dev/DEV-GUIDE_Write-down-the-bugs.md).

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Zweck

Dieses Dokument entlastet [`KNOWN_ISSUES.md`](../../../KNOWN_ISSUES.md), indem behobene Bugs mit ihrer Lösung, dem Fix-Commit bzw. der Zielversion getrennt von den offenen Fehlern dokumentiert werden.

Sobald ein Bug-Fix vollständig in einem veröffentlichten Release im [`CHANGELOG.md`](../../../CHANGELOG.md) aufgegangen ist, kann der zugehörige Archiveintrag hier bereinigt werden.

---

## Archivierte Bug-Fixes

### [BUG-007] `DocFrame.update()` überschreibt den Hinweis zur erkenntnistheoretischen Grenze

- **Status:** Behoben *(Unreleased / nach `v0.1.0`)*
- **Schweregrad:** Hoch
- **Bereich:** `src/qb_cubie/core/services/doc_frame/{presets.py,frame_blocks.py,doc_frame.py}`, `tests/test_doc_ensurance.py`, `tests/test_doc_frame.py`, `tests/tests_core/tests_services/tests_doc_frame/`

**Ursache & Lösung:**  
- **Zentrale Preset- & Anker-Definition (`presets.py`):** Neues Modul `src/qb_cubie/core/services/doc_frame/presets.py` als zentrale Single Source of Truth für `EPISTEMIC_NOTICE_TEXT`, `EPISTEMIC_NOTICE` (`StaticBlock`), `STD_HEAD_BLOCKS`, `STD_FOOTER_BLOCKS` und `CUBIE_DOC_FRAME_1..3` eingeführt (vollständig re-exportiert über `doc_frame.py` und `qb_cubie.core.services`).
- **Verlustfreier `DisclaimerSlot` & Divider-Deduplizierung (`frame_blocks.py`):** `DisclaimerSlot.render()` bewahrt nun alle dokument-spezifischen Zwischensegmente `segments[1:-1]` (statt nur `segments[1]`), filtert den erkenntnistheoretischen Ankertext heraus (um Duplikate bei 3-Segment-Bestandsdokumenten zu verhindern), und `CenterWrap.render()` dedupliziert aufeinanderfolgende `---`-Trenner.
- **Aktive Prüfung & SRP-Aufteilung der Test-Module:** Da `EPISTEMIC_NOTICE` fester Bestandteil von `STD_HEAD_BLOCKS` ist, wird ein fehlender oder veränderter Hinweis durch `CUBIE_DOCFRAME_RULES` (`DOCFRAME-OUTDATED`) aktiv abgefangen. Die Repository-weiten Dokumentations-Tests wurden aus `tests/test_styleguide.py` in zwei eigenständige Module `tests/test_doc_ensurance.py` und `tests/test_doc_frame.py` (ohne `@pytest.mark.skip`) ausgelagert.

---

*(Weitere historische Bug-Fixes – z. B. `[BUG-001]` – sind bereits in veröffentlichten Releases im [`CHANGELOG.md`](../../../CHANGELOG.md) aufgegangen.)*

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../../README.md)  
[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../../dev/README.md)  
[↦ | Core-Internals | ↤](../../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  

[↦ | Analysis: Stärkung der CI-Matrix für Windows und macOS | ↤](./ANALYSIS_CI_MATRIX.md)  
[↦ | Analyse: Möglichkeiten zum Bau eines Analyse-Werkzeugs für EBT-Case-Coverage auf Quellcode-Objekten | ↤](./ANALYSIS_COVERAGE_OPTIONS.md)  
[↦ | Wheel / windows-2022 / Python 3.13 sagt: | ↤](./CI-Data.md)  
[↦ | Archiv behobener Bugs (`SOLVED_ISSUES.md`) | ↤](./SOLVED_ISSUES.md)  

</div>
<!-- /qb:frame -->
