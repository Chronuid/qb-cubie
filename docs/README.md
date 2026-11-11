# Dokumentation

| Ablage | Inhalt und Geltung |
| --- | --- |
| `docs/GUIDE_*.md` | Nutzungsleitfäden und Beschreibung der vorhandenen Schnittstellen. Für den Einstieg in Cubie hier beginnen. |
| [docs/dev](dev/DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md) | Technische Entwicklerübersichten und [Styleguide](dev/Style-Guide.md) für die Arbeit am Cubie-Code. |
| [docs/misc](misc/README.md) | Hintergrundtexte und optionale historische Entwicklungsunterlagen. Die Bereichsdokumentation ist ohne diese Unterlagen verständlich. |
| [tests/docs_tmp](../tests/docs_tmp/README.md) | Phasenbezogene Abnahmematrizen und historische Test-/Messnachweise. Die ausführbaren Tests liegen weiterhin in ihren ursprünglichen Testverzeichnissen. |
| [docs/feature-drafts](feature-drafts/virtualization/README.md) | Funktionsentwürfe und Prototypen; keine Zusage einer verfügbaren Produktfunktion. |

Für die Bedeutung von Qualität und bestandenen Prüfungen gelten die
[Qualitätsbegriffe](GUIDE_Quality-Assurance.md) und die
[Vertragssemantik](GUIDE_Contract-Semantics.md).

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
