<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Dokumentation

![Cubie](.assets/cubie-logo-written.png)

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

| Ablage | Inhalt und Geltung |
| --- | --- |
| [docs/core](core/README.md) | Verbindliche Core-Referenzen und Nutzungsmuster (`Contract-Semantics`, `EBT`, `RBT`, `Arena-Management`, `Linter`). |
| `docs/GUIDE_*.md` | Übergreifende Leitfäden zu Qualitätssicherung, Test-Guided Development (TGD), Vertragsaufbau, Quantoren, `expect`-Flags und Benchmarks. |
| [docs/services](services/GUIDE_DocEnsurance.md) | Leitfäden zu den Services in `qb_cubie.core.services` (`DocEnsurance` sowie [DocFrame (Prototyp)](services/GUIDE_DocFrame.md) – noch zu evaluieren und zu härten). |
| [docs/dev](dev/README.md) | Entwicklerdokumentation: [Core-Internals](dev/core/README.md), [Services](dev/services/DEV-GUIDE_DocEnsurance.md), [Styleguide](dev/Style-Guide.md) und [Release-Leitfaden](dev/DEV-GUIDE_Release-Preparation.md). |
| [docs/misc](misc/README.md) | Hintergrundtexte, optionale historische Entwicklungsunterlagen sowie das Sammelbecken [`docs/misc/lake/`](misc/lake/SOLVED_ISSUES.md) (Analysen, CI-Daten, Archiv behobener Bugs). |
| [tests/README.md](../tests/README.md) | Leitfaden zur Testsuite, Marker-Profilen, `Makefile`-Zielen und Hypothesis-Profilen. |
| `docs/feature-drafts` | Funktionsentwürfe und Prototypen ([Benchmarks](feature-drafts/GUIDE_Benchmarks.md), [Virtualisierung](feature-drafts/virtualization/README.md), `meta-qa/`); keine Zusage einer verfügbaren Produktfunktion. |

Für die Bedeutung von Qualität und bestandenen Prüfungen gelten die
[Qualitätsbegriffe](GUIDE_Quality-Assurance.md) und die
[Vertragssemantik](core/GUIDE_Contract-Semantics.md).

Der gesamte Benchmark-Bereich ist **experimentell und gehört nicht zum
qb-cubie Core**. Der gemeinsame [Benchmark-Guide](feature-drafts/GUIDE_Benchmarks.md) erklärt
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

## Quality-Assurance-Handbücher

| Handbuch | Schwerpunkt und Inhalt |
| --- | --- |
| [Qualitätssicherung mit Cubie](GUIDE_Quality-Assurance.md) | Einstieg und Gesamtüberblick zu deklarativen Verträgen, den orthogonalen Prüfschichten (`EBT`, Arenen, Linter, `DocEnsurance`, `RBT`), Test-Guided Development (TGD) sowie den Grundlagen von `EBT`. |
| [Vertragsaufbau: Eindeutigkeit & Kopplung](GUIDE_Contract-Design.md) | Eindeutiger und wartbarer Aufbau von `EBT`-Verträgen: ein Vertrag pro Ein-/Ausgabepaar, saubere Skalierung mit `@pytest.mark.parametrize` und Vermeidung von Unterspezifikation durch gemischte `pre`-/`post`-Listen. |
| [Erwartungssteuerung & Safety (`expect`-Flags)](GUIDE_Expect-Flags.md) | Einsatz von `expect=True` und `expect=False` auf `WorldState`- und `EBT`-Ebene, Kombination von Soll-Zielen und Negativ-Filtern unter `post={"quantor": "all", ...}`, `STATE-GUARD`-Regeln, Red-Phase-Gegenproben und Vermeidung von *Vacuous Pass*. |
| [Fortgeschrittene Quantoren (`all` vs. `exists`)](GUIDE_Quantifiers.md) | Standard-Quantoren (`pre="all"`, `post="exists"`) und deren explizite Umkehrung: mehrere Bedingungen gleichzeitig mit `post` auf `"all"` erzwingen (UND) oder alternative Eingabe-Routen mit `pre` auf `"exists"` zulassen (ODER). |
| [Test-Guided Development (TGD)](GUIDE_TGD.md) | TGD für Einsteiger und Experten: TDD mit kontrollierter Rückwärtstür (`GREEN_AUDIT`) im Sinne von Karl Poppers Fallibilismus, optionale Stützräder (`ANALYSIS` & `HYPOTHESIS`), der Fünf-Schritte-Ablauf und Living Documentation. |

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./README.md)  
[↦ | Core-Dokumentation | ↤](./core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./dev/README.md)  
[↦ | Core-Internals | ↤](./dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
