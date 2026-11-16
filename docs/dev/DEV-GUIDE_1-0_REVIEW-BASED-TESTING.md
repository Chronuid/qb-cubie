<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# Review-Based Testing

![Cubie](../.assets/cubie-logo-written.png)

RBT orchestriert Beurteilungen anhand einer Prüfregel. Es ist für manuelle Abnahmen oder eigene automatisierte Reviewer nutzbar. Es führt das Target nicht aus und liefert keinen formalen Korrektheits- oder Sicherheitsnachweis. Die [Semantikreferenz](../GUIDE_Contract-Semantics.md) definiert die Grenzen; vollständige Beispiele stehen im [RBT-Nutzungshandbuch](../GUIDE_RBT-Usage-Pattern.md).

---

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

`from qb_cubie.rbt import RBT` ist der vorhandene Import. Die Klasse wird nicht als `qb_cubie.RBT` exportiert.

## Ablauf

1. `_arrange()` wandelt `target` in eine Bezeichnung um. Strings und `None` bleiben erhalten; andere Objekte werden über `__name__` oder `str()` bezeichnet.
2. `_review()` ruft `reviewer.review(target=..., check=...)` synchron auf. Der Reviewer beschafft selbst Quellen und Kontext und liefert `ReviewData`.
3. `_report()` übergibt das Ergebnis an den Reporter, sofern dieser nicht `None` ist. `PytestReporter` übernimmt Formatierung und Assertion.

Ohne Target wird `None` übergeben. Der Reviewer kann dies nach einer eigenen Konvention als Projektauftrag interpretieren; RBT untersucht nicht automatisch das Repository. Auch ein Pfad als Target wird nicht automatisch gelesen.

## Verträge

`ReviewData` ist eine veränderliche Dataclass mit `passed: bool` und `report: dict`, standardmäßig leer. Das offene Dictionary kann Kriterien, Begründungen und Metadaten enthalten. Seine Struktur und dauerhafte Speicherung müssen Integrationen selbst festlegen.

Das `Reviewer`-Protokoll aus `qb_cubie.protocols` verlangt `review(target: str | None, check: str) -> ReviewData`. Es beschreibt eine Schnittstelle, keinen fertigen LLM-Adapter und keine Validierung der fachlichen Qualität einer Entscheidung.

Standard ist `HeadlessReviewer()`: Ohne vorgegebene Antwort fragt er am Terminal interaktiv nach Entscheidung und Bericht. pytest benötigt dafür `-s`. `HumanReviewer` ist die ausdrücklich wählbare Tkinter-GUI. Automatisierte Läufe benötigen einen nichtinteraktiven Reviewer; eine vorgegebene Antwort in `HeadlessReviewer` prüft selbst keine Anforderung.

Reviewer- und Reporter-Exceptions propagieren. `RBT.run()` gibt nach regulärem Abschluss `None` zurück. Mit `reporter=None` findet der Review weiterhin statt, aber keine Reporter-Assertion.

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../GUIDE_Benchmarks.md)  
[↦ | Verbindliche Vertragssemantik | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT-Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | Example-Based Testing | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | RBT-Nutzungsmuster | ↤](../GUIDE_RBT-Usage-Pattern.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../services/GUIDE_DocFrame.md)  

[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  
[↦ | DEV-GUIDE: Next Steps – `services`-Zweig, Sprint-Aufarbeitung und Audit-Fixes | ↤](./DEV-GUIDE_Next-Steps.md)  
[↦ | DEV-GUIDE: Release-Vorbereitung und sauberer Release | ↤](./DEV-GUIDE_Release-Preparation.md)  
[↦ | Styleguide | ↤](./Style-Guide.md)  

</div>
<!-- /qb:frame -->
