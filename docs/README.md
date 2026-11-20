<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Dokumentation

![Cubie](.assets/cubie-logo-written.png)

---

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

| Ablage | Inhalt und Geltung |
| --- | --- |
| [docs/core](core/README.md) | Verbindliche Core-Referenzen und Nutzungsmuster (`Contract-Semantics`, `EBT`, `RBT`, `Arena-Management`, `Linter`). |
| `docs/GUIDE_*.md` | Übergreifende Leitfäden zu Qualitätssicherung, Vertragsaufbau, Quantoren, `expect`-Flags und Benchmarks. |
| [docs/services](services/GUIDE_DocEnsurance.md) | Leitfäden zu den Services in `qb_cubie.services` (`DocEnsurance` sowie [DocFrame (Prototyp)](services/GUIDE_DocFrame.md) – noch zu evaluieren und zu härten). |
| [docs/dev](dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) | Technische Entwicklerübersichten, [Styleguide](dev/Style-Guide.md) und [Release-Leitfaden](dev/DEV-GUIDE_Release-Preparation.md) für die Arbeit am Cubie-Code. |
| [docs/misc](misc/README.md) | Hintergrundtexte und optionale historische Entwicklungsunterlagen. Die Bereichsdokumentation ist ohne diese Unterlagen verständlich. |
| [tests/README.md](../tests/README.md) | Leitfaden zur Testsuite, Marker-Profilen, `Makefile`-Zielen und Hypothesis-Profilen. |
| [docs/feature-drafts](feature-drafts/virtualization/README.md) | Funktionsentwürfe und Prototypen; keine Zusage einer verfügbaren Produktfunktion. |

Für die Bedeutung von Qualität und bestandenen Prüfungen gelten die
[Qualitätsbegriffe](GUIDE_Quality-Assurance.md) und die
[Vertragssemantik](core/GUIDE_Contract-Semantics.md).

Der gesamte Benchmark-Bereich ist **experimentell und gehört nicht zum
qb-cubie Core**. Der gemeinsame [Benchmark-Guide](GUIDE_Benchmarks.md) erklärt
Installation, eigene Agenten und Szenarien, Cubie-/Pytest-Vergleiche, SWE-bench,
Datenverträge und Messbetrieb einschließlich Nachbewertung und CI. Ergebnisse und
Grenzen der bisherigen lokalen Messungen stehen bei den
[Ollama-Agenten](../experiments/ollama-agents/README.md#explorative-messung-vom-10-november-2026)
und beim [historischen Nutzungstest](../experiments/ollama-user-benchmark/README.md#nutzungsexperiment-vom-10-november-2026).

Die davon getrennte [Testguided-Vergleichsstudie](../experiments/testguided-study/README.md)
vergleicht zwei lokale Ollama-Agenten mit swegemma, frei überarbeitbaren Tests
und unabhängiger Lösungsbewertung. Ihr
[Studienprotokoll](../experiments/testguided-study/PROTOKOLL.md) ist der Einstieg
für den experimentellen Nutzennachweis; der experimentelle Benchmark-Guide beschreibt
einen anderen Ablauf.

Relative Markdown-Links beziehen sich auf das jeweilige Dokument. Unverlinkte
Repositorypfade und Shellbefehle beziehen sich, sofern nicht anders angegeben,
auf die Repositorywurzel. Dateinamen eines beschriebenen Beispielprojekts
beziehen sich dagegen auf dieses Beispielprojekt.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](./GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](./core/README.md)  
[↦ | Entwicklerübersicht & Internals | ↤](./dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Hintergrund & Essays | ↤](./misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
