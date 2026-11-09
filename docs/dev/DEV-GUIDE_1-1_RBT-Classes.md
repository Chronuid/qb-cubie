<center>

# RBT-Klassen

![Cubie](../.assets/cubie-logo-written.png)

Die [RBT-Übersicht](DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) beschreibt Ablauf und Aussagegrenzen. Die folgenden Klassen gehören zu `qb_cubie.rbt`, die Daten- und Schnittstellenverträge zu `qb_cubie.protocols`.

---

</center>

## RBT

`RBT(check, target=None, reviewer=None, tags=None, reporter=...)` speichert den Prüfauftrag. `reviewer=None` wählt `HeadlessReviewer()`. Der Standardreporter ist `PytestReporter`; ein explizites `reporter=None` deaktiviert ihn.

`run()` ruft `_arrange()`, `_review()` und `_report()` auf. `_evaluate()` bildet nur die Zielbezeichnung und ruft das Objekt nicht auf. Es gibt keine automatische Datei- oder Quellenbeschaffung. `_target_string` und `_result` halten den internen Zustand. `run()` hat keinen Ergebnisrückgabewert; eigene Reporter können `ReviewData` empfangen.

`tags` ist eine Liste von Metadaten. Die Klasse setzt damit keine pytest-Marken. Die Bewertung wird über den Reporter an pytest vermittelt; eine feste Assertion oder JSON-Formatierung ist nicht Teil der RBT-Engine selbst.

## ReviewData und Reviewer

`ReviewData(passed, report={...})` enthält eine boolesche Entscheidung und ein offenes Dictionary. Es ist eine veränderliche Dataclass, kein Beweisobjekt. `Reviewer.review(target: str | None, check: str) -> ReviewData` ist der gemeinsame Vertrag.

Eigene Reviewer können Quellen laden, APIs aufrufen und Metadaten erfassen. Diese Aufgaben werden nicht durch das Protokoll implementiert. Insbesondere existiert kein integrierter `AgentReviewer` mit LLM-Aufruf und Modellversionierung.

## HeadlessReviewer

`HeadlessReviewer(answer=None)` fragt am Terminal nach `y/n` und einem optionalen Bericht. pytest muss interaktiv mit `-s` gestartet werden. Eingabefehler propagieren.

Mit `answer=True` oder `False` liefert jeder Aufruf eine neue `ReviewData` mit der vorgegebenen Entscheidung. Das eignet sich zur technischen Anbindung, ist aber keine fachliche Prüfung.

## HumanReviewer

`HumanReviewer` öffnet eine Tkinter-GUI mit Target, Prüfregel, Entscheidungsschaltflächen und Textfeld. `review()` wartet synchron auf die Interaktion und konstruiert danach `ReviewData`. Die GUI benötigt eine verfügbare grafische Umgebung und ist kein Standard für unbeaufsichtigte CI-Läufe.

`_run_gui()`, `_build_widgets()`, `_build_buttons()` und `_finalize()` kapseln Darstellung und Übernahme der Eingaben. Der Reviewer ist von pytest entkoppelt; die Assertion und Berichtsformatierung übernimmt der gewählte Reporter.

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
