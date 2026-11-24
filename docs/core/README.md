<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Core-Dokumentation

![Cubie](../.assets/cubie-logo-written.png)

Zentraler Einstiegspunkt für die verbindlichen Core-Referenzen und Nutzungsmuster von `qb-cubie`: Vertragssemantik, Example-Based Testing (`EBT`), Review-Based Testing (`RBT`), Ausführungs-Arenen (`TempFS`, `PyVenv`) und statische Analyse (`Linter`).

---

> [!NOTE]
> **Einordnung im Dokumentationsbaum:**  
> Die Dokumente unter `docs/core/` bilden die verbindliche Grundlage der öffentlichen `qb-cubie`-Core-Schnittstellen. Übergreifende Entwurfs-, Quantor-, Erwartungs-, QA- und Benchmark-Leitfäden liegen direkt unter [`docs/`](../README.md); interne Architektur- und Klassenreferenzen für Entwickler unter [`docs/dev/`](../dev/README.md).

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

## Einstieg nach Aufgabe

| Ziel / Aufgabe | Empfohlener Einstieg |
| :--- | :--- |
| **Vertragsfelder, Match-Regeln & bekannte Grenzen nachschlagen** | [Verbindliche Vertragssemantik](./GUIDE_Contract-Semantics.md) |
| **Example-Based Tests (`EBT`) mit `WorldState` schreiben** | [EBT-Nutzungsmuster](./GUIDE_EBT-Usage-Pattern.md) |
| **Review-Based Tests (`RBT`) mit eigenen Reviewern nutzen** | [RBT-Nutzungsmuster](./GUIDE_RBT-Usage-Pattern.md) |
| **Isolierte Workspaces (`TempFS`) & virtuelle Umgebungen (`PyVenv`) steuern** | [Arena-Management](./GUIDE_Arena-Management.md) |
| **Statische Code-Analyse (CST, MyPy, Pylint) einbinden** | [Linter](./GUIDE_Linter.md) |

---

## Core-Handbücher & Referenzen (`docs/core/`)

Die folgende Übersicht umfasst sämtliche direkt in `docs/core/` abgelegten Handbücher und wird automatisch durch `DocFrame` (`CUBIE_DOC_FRAME_3`) synchronisiert:

<!-- qb:frame id="CUBIE_DOC_FRAME_3" zone="router" mode="table" dir="." recursive="false" -->
| Dokument | Inhalt und Geltung |
| :--- | :--- |
| [Arena-Management](./GUIDE_Arena-Management.md) | Arenen trennen die EBT-Orchestrierung von Aufbau und Ausführung einer Testumgebung. `TempFS` und `PyVenv` verwenden temporäre Arbeitsverzeichnisse und Kindprozesse. **Beide besitzen die Rechte des aufrufenden Benutzers und bilden keine OS-Sicherheitsgrenze.** Sie sind für vertrauenswürdigen Code vorgesehen. Die [Semantikreferenz](GUIDE_Contract-Semantics.md) definiert den Vertrag und seine Grenzen. |
| [Verbindliche Vertragssemantik](./GUIDE_Contract-Semantics.md) | Diese Referenz beschreibt die vorhandene Implementierung von Cubie 0.1.1, abgeglichen mit `src/qb_cubie/core/ebt.py`, `protocols.py`, `rbt.py` und den Arenen. Sie unterscheidet die Auswertungsregel von bekannten Fehlern und berücksichtigt die Produktivkorrekturen zu Abschnitt 9.1 des [Gutachtens vom 10. November 2026](../../GUTACHTEN.md). |
| [EBT-Nutzungsmuster](./GUIDE_EBT-Usage-Pattern.md) | Die Beispiele zeigen die vorhandene API. Die [zentrale Semantikreferenz](GUIDE_Contract-Semantics.md) definiert alle Felder, Vergleichsregeln und bekannten Fehler. Verwende explizite, nichtleere Verträge. Eine EBT-Instanz kann nacheinander mehrfach ausgeführt werden; jeder Lauf erzeugt eine eigene Ergebnis-Momentaufnahme. Die folgenden Python-Blöcke sind vollständige pytest-Beispiele. |
| [Linter](./GUIDE_Linter.md) | Das Linter-Modul orchestriert die statische Code-Analyse innerhalb des Cubie-Ökosystems. Es abstrahiert die Komplexität externer CLI-Tools (wie Pylint) und nativer Python-Syntaxbäume (CST) hinter einer einheitlichen, protokollbasierten Schnittstelle, um Diagnosen verschiedener Werkzeuge einheitlich auszuwerten. Die Analyse bietet keine OS-Sicherheitsgrenze und keinen allgemeinen Korrektheitsnachweis. Bekannte Einschränkungen beschreibt die [Vertragssemantik](GUIDE_Contract-Semantics.md). |
| [RBT-Nutzungsmuster](./GUIDE_RBT-Usage-Pattern.md) | RBT delegiert eine sprachlich formulierte Prüfregel an einen Reviewer und übergibt dessen `ReviewData` an einen Reporter. Eine Entscheidung bleibt eine Beurteilung unter den jeweiligen Bedingungen. Die [Semantikreferenz](GUIDE_Contract-Semantics.md) grenzt sie von Ausführung und Beweis ab. |
<!-- /qb:frame -->

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
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

[↦ | Arena-Management | ↤](./GUIDE_Arena-Management.md)  
[↦ | Verbindliche Vertragssemantik | ↤](./GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](./GUIDE_EBT-Usage-Pattern.md)  
[↦ | Linter | ↤](./GUIDE_Linter.md)  
[↦ | RBT-Nutzungsmuster | ↤](./GUIDE_RBT-Usage-Pattern.md)  

</div>
<!-- /qb:frame -->
