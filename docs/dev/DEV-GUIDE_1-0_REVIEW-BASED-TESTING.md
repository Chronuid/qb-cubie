<center>

# Review-Based Testing

![Cubie](../.assets/cubie-logo-written.png)

RBT orchestriert Beurteilungen anhand einer Prüfregel. Es ist für manuelle Abnahmen oder eigene automatisierte Reviewer nutzbar. Es führt das Target nicht aus und liefert keinen formalen Korrektheits- oder Sicherheitsnachweis. Die [Semantikreferenz](../GUIDE_Contract-Semantics.md) definiert die Grenzen; vollständige Beispiele stehen im [RBT-Nutzungshandbuch](../GUIDE_RBT-Usage-Pattern.md).

---

</center>

`from cubie.rbt import RBT` ist der vorhandene Import. Die Klasse wird nicht als `cubie.RBT` exportiert.

## Ablauf

1. `_arrange()` wandelt `target` in eine Bezeichnung um. Strings und `None` bleiben erhalten; andere Objekte werden über `__name__` oder `str()` bezeichnet.
2. `_review()` ruft `reviewer.review(target=..., check=...)` synchron auf. Der Reviewer beschafft selbst Quellen und Kontext und liefert `ReviewData`.
3. `_report()` übergibt das Ergebnis an den Reporter, sofern dieser nicht `None` ist. `PytestReporter` übernimmt Formatierung und Assertion.

Ohne Target wird `None` übergeben. Der Reviewer kann dies nach einer eigenen Konvention als Projektauftrag interpretieren; RBT untersucht nicht automatisch das Repository. Auch ein Pfad als Target wird nicht automatisch gelesen.

## Verträge

`ReviewData` ist eine veränderliche Dataclass mit `passed: bool` und `report: dict`, standardmäßig leer. Das offene Dictionary kann Kriterien, Begründungen und Metadaten enthalten. Seine Struktur und dauerhafte Speicherung müssen Integrationen selbst festlegen.

Das `Reviewer`-Protokoll aus `cubie.protocols` verlangt `review(target: str | None, check: str) -> ReviewData`. Es beschreibt eine Schnittstelle, keinen fertigen LLM-Adapter und keine Validierung der fachlichen Qualität einer Entscheidung.

Standard ist `HeadlessReviewer()`: Ohne vorgegebene Antwort fragt er am Terminal interaktiv nach Entscheidung und Bericht. pytest benötigt dafür `-s`. `HumanReviewer` ist die ausdrücklich wählbare Tkinter-GUI. Automatisierte Läufe benötigen einen nichtinteraktiven Reviewer; eine vorgegebene Antwort in `HeadlessReviewer` prüft selbst keine Anforderung.

Reviewer- und Reporter-Exceptions propagieren. `RBT.run()` gibt nach regulärem Abschluss `None` zurück. Mit `reporter=None` findet der Review weiterhin statt, aber keine Reporter-Assertion.

---

---

<center>

![Error while trying to load the image](../.assets/cubie-small.png)

## Dokumentation

[↦ | Qualitätssicherung: Begriffe und Aussagegrenzen | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Vertragssemantik: zentrale Referenz | ↤](../GUIDE_Contract-Semantics.md)  
[↦ | EBT: Auswahl von Beispielen | ↤](../GUIDE_Example-Based-Testing.md)  
[↦ | EBT: ausführbare Nutzungsmuster | ↤](../GUIDE_EBT-Usage-Pattern.md)  
[↦ | RBT: Reviewer und Nutzung | ↤](../GUIDE_RBT-Usage-Pattern.md)  
[↦ | Arena-Management | ↤](../GUIDE_Arena-Management.md)  
[↦ | Linter | ↤](../GUIDE_Linter.md)  

[↦ | Entwicklerübersicht EBT | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)

</center>
