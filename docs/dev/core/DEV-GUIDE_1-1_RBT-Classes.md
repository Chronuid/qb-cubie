<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# RBT-Klassen

![Cubie](../../.assets/cubie-logo-written.png)

Die [RBT-Übersicht](DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md) beschreibt Ablauf und Aussagegrenzen. Die folgenden Klassen gehören zu `qb_cubie.core.rbt`, die Daten- und Schnittstellenverträge zu `qb_cubie.core.protocols`.

---

> [!Note]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
>
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ...heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../../README.md) • [QA-Handbuch](../../GUIDE_Quality-Assurance.md) • [DocEnsurance](../../services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

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

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../../.assets/cubie-small.png)

[↦ | Benchmarks: Einstieg, eigene Agenten und Messbetrieb (`GUIDE_Benchmarks.md`) | ↤](../../GUIDE_Benchmarks.md)  
[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](../../services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](../../services/GUIDE_DocFrame.md)  

[↦ | Core-Dokumentation | ↤](../../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../README.md)  
[↦ | Hintergrund & Essays | ↤](../../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../../feature-drafts/virtualization/README.md)  
[↦ | Review-Based Testing | ↤](./DEV-GUIDE_1-0_REVIEW-BASED-TESTING.md)  
[↦ | RBT-Klassen | ↤](./DEV-GUIDE_1-1_RBT-Classes.md)  
[↦ | EBT: Entwicklerübersicht | ↤](./DEV-GUIDE_2-0_EXAMPLE-BASED-TESTING.md)  
[↦ | Die EBT-Klasse | ↤](./DEV-GUIDE_2-1_EBT-Class.md)  
[↦ | WorldState | ↤](./DEV-GUIDE_2-2_WorldState-Class.md)  
[↦ | Arenen und IPC-Codecs | ↤](./DEV-GUIDE_2-3_Arenas.md)  
[↦ | `Multiprocessors` | ↤](./DEV-GUIDE_2-4_Multiprocessors.md)  
[↦ | `Linter` | ↤](./DEV-GUIDE_2-5_Linter.md)  

</div>
<!-- /qb:frame -->
