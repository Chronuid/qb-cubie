<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Hintergrund und optionale Entwicklungsunterlagen

![Cubie](../.assets/cubie-logo-written.png)

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

Die Texte zu *Clean-Code-Pragmatism*, *Die Suchmaschine von Babel*,
*Erweitertes PBT* und *FP-OOP-Isomorphismus* enthalten Hintergrundüberlegungen.
Sie sind keine verbindlichen API-Verträge oder Nachweise implementierter Funktionen.

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Clean-Code Pragmatismus](./Clean-Code-Pragmatism.md) | Dieser Essay diskutiert kontextabhängige Entwurfsentscheidungen und pragmatische Clean-Code-Prinzipien. |
| [Die Suchmaschine von Babel: eine Metapher](./Die-Suchmaschine-von-Babel.md) | **Status: konzeptioneller Essay.** Cubie enthält weder eine Suchmaschine für Programme noch einen Codegenerator. Den implementierten Vertrag beschreibt die [Semantikreferenz](../core/GUIDE_Contract-Semantics.md). |
| [Erweitertes Property-Based Testing: konzeptionelle Einordnung](./Erweitertes-PBT.md) | **Status: konzeptioneller Vorschlag, keine implementierte Cubie-API.** Die frühere Bezeichnung „ePBT“ fasste unterschiedliche Qualitätssicherungsverfahren zusammen. Sie bezeichnet hier keinen etablierten Beweiskalkül und keine automatisch nachgewiesenen universellen Eigenschaften. Die vorhandene Cubie-Semantik steht in der [Vertragsreferenz](../core/GUIDE_Contract-Semantics.md). |
| [FP-OOP-Isomorphismus](./FP-OOP-Isomorphismus.md) | Dieser Essay untersucht Beziehungen zwischen funktionaler und objektorientierter Programmierung. |
| [Technische Bestandsaufnahme von **qb-cubie** 0.1.0](./deep-research-report.md) |  |
<!-- /qb:frame -->

Die hier verbliebenen Agenten-/Benchmark-Konzepte, Anforderungsentwürfe und
Entwicklungsprotokolle sind optionale historische Arbeitsunterlagen. Die übrige
Dokumentation setzt ihre Verfügbarkeit nicht voraus; sie können aus dem Kontext
oder Checkout entfernt werden. Relevante Informationen werden eigenständig in
den jeweiligen Bereichen geführt:

| Bereich | Eigenständige Dokumentation |
| --- | --- |
| Benchmark-Nutzung, Loadervertrag, Bewertungsgrenzen und ausstehende Nachweise | [Benchmark-Leitfaden](../feature-drafts/GUIDE_Benchmarks.md) |
| Ollama-Rollen, Kalibrierung und explorative Messung | [Ollama-Agenten](../../experiments/ollama-agents/README.md) |
| Historischer Nutzungstest eigener Developer-Aufgaben und Folgerungen | [Ollama-Nutzungsexperiment](../../experiments/ollama-user-benchmark/README.md) |
| Separate Testguided-Vergleichsstudie | [Studienprotokoll](../../experiments/testguided-study/PROTOKOLL.md) |

## Sammelbecken (`docs/misc/lake/`)

Dokumente ohne feste Bereichszuordnung (CI-Analysen, Konzeptstudien und das Archiv behobener Bugs) werden regelmäßig in [`docs/misc/lake/`](./lake/SOLVED_ISSUES.md) gesammelt, um die übrigen Ordner übersichtlich zu halten:

| Dokument | Inhalt |
| :--- | :--- |
| [Archiv behobener Bugs (`SOLVED_ISSUES.md`)](./lake/SOLVED_ISSUES.md) | Separates Archiv für behobene Bugs aus [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md). |
| [Analyse: CI-Matrix](./lake/ANALYSIS_CI_MATRIX.md) | Plattform-Matrix-Analyse (`linux`, `macos`, `windows`) und Härtungsschritte. |
| [Analyse: Coverage-Optionen](./lake/ANALYSIS_COVERAGE_OPTIONS.md) | Konzeptstudie zu Testabdeckung und statischen/dynamischen Analyse-Optionen. |
| [CI-Rohdaten (`CI-Data.md`)](./lake/CI-Data.md) | Protokollierte CI-Läufe und Plattform-Befunde. |

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

[↦ | Clean-Code Pragmatismus | ↤](./Clean-Code-Pragmatism.md)  
[↦ | Die Suchmaschine von Babel: eine Metapher | ↤](./Die-Suchmaschine-von-Babel.md)  
[↦ | Erweitertes Property-Based Testing: konzeptionelle Einordnung | ↤](./Erweitertes-PBT.md)  
[↦ | FP-OOP-Isomorphismus | ↤](./FP-OOP-Isomorphismus.md)  
[↦ | Technische Bestandsaufnahme von **qb-cubie** 0.1.0 | ↤](./deep-research-report.md)  

</div>
<!-- /qb:frame -->
