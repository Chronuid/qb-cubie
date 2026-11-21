<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Erweitertes Property-Based Testing: konzeptionelle Einordnung

![Cubie](../.assets/cubie-logo-written.png)

**Status: konzeptioneller Vorschlag, keine implementierte Cubie-API.** Die frühere Bezeichnung „ePBT“ fasste unterschiedliche Qualitätssicherungsverfahren zusammen. Sie bezeichnet hier keinen etablierten Beweiskalkül und keine automatisch nachgewiesenen universellen Eigenschaften. Die vorhandene Cubie-Semantik steht in der [Vertragsreferenz](../core/GUIDE_Contract-Semantics.md).

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Verfahren sinnvoll verbinden

Property-Based Testing beschreibt Eigenschaften und prüft erzeugte Eingaben dagegen. Endliche generierte Ausführungen können Gegenbeispiele finden, belegen aber nicht automatisch die Eigenschaft für alle zulässigen Werte. Fuzzing und PBT können sich überschneiden; ihre Verwendung macht eine Prüfung weder zu Logik höherer Stufe noch zu einer vollständigen Exploration.

Typprüfer untersuchen Verträge innerhalb ihres Typmodells und ihrer Konfiguration. Linter beziehungsweise Syntaxbaumregeln untersuchen bestimmte strukturelle Merkmale. Laufzeitverträge prüfen die tatsächlich erreichten Aufrufe. Diese Verfahren ergänzen sich, liefern aber jeweils nur die durch Methode und Annahmen gedeckten Aussagen. Sie sind nicht allein durch ihre Kombination ein allgemeiner Korrektheitsbeweis.

| Verfahren | Beobachtung oder Analyse | Grenze |
| --- | --- | --- |
| EBT | Konkrete Eingaben gegen deklarierte Zielmuster | Ungeprüfte Eingaben und unzutreffende Sollwerte bleiben möglich |
| PBT / generative Tests | Erzeugte Fälle gegen eine Eigenschaft | Generator und Eigenschaft können lückenhaft oder falsch sein |
| Statische Analyse | Eigenschaften im Modell des jeweiligen Werkzeugs | Aussage hängt von Regeln, Konfiguration und Annahmen ab |
| Laufzeitverträge | Bedingungen bei tatsächlich erreichten Aufrufen | Nicht erreichte Zustände bleiben ungeprüft |
| RBT | Entscheidung eines Reviewers anhand eines Prüfauftrags | Kontext, Material und Beurteilung begrenzen die Aussage |

## Umgang mit Funden

Ein generativ gefundenes Gegenbeispiel kann nach fachlicher Prüfung als reproduzierbarer Regressionstest übernommen werden. Ein kuratiertes Beispiel besitzt aber nicht automatisch höhere Autorität als eine Property. Bei einem Widerspruch müssen Eingabe, Sollwert, Eigenschaft, Generator und Implementierung geprüft werden.

Cubie implementiert keinen eigenen allgemeinen PBT-Generator und keine Rangordnung zwischen „absoluten Fakten“ und „Hypothesen“. Eine Verbindung mit externen Generatoren ist eine mögliche Integration. Für jedes Ergebnis müssen Prüfumfang, Bedingungen und offene Einschränkungen sichtbar bleiben.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Clean-Code Pragmatismus | ↤](./Clean-Code-Pragmatism.md)  
[↦ | Die Suchmaschine von Babel: eine Metapher | ↤](./Die-Suchmaschine-von-Babel.md)  
[↦ | Erweitertes Property-Based Testing: konzeptionelle Einordnung | ↤](./Erweitertes-PBT.md)  
[↦ | FP-OOP-Isomorphismus | ↤](./FP-OOP-Isomorphismus.md)  

</div>
<!-- /qb:frame -->
