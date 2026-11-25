<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GEMINI

![Cubie](../.assets/cubie-logo-written.png)

---

> [!NOTE]  
> qb-cubie anerkennt explizit unsere **erkenntnistheoretischen Grenzen** im Sinne von Karl Poppers kritischem Rationalismus. Jede Aussage über ein System (und damit auch jeder Testfall als formalisierte Soll-Spezifikation) ist grundsätzlich **fehlbar** (*Fallibilismus*).  
>
> **Ein Test ist kein unfehlbares Dogma, sondern eine vorläufig bewährte Falsifikationshypothese.**  
> *Wenn du dein ganzes Leben lang nur weiße Schwäne gesehen hast …  
> ... heißt das dann, dass es keine schwarzen Schwäne gibt?*  
> **Code, Tests und Dokumentation von Cubie befinden sich in aktiver Weiterentwicklung.**

---

[README](../../README.md) • [QA-Handbuch](../GUIDE_Quality-Assurance.md) • [DocEnsurance](./GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

# Ziel

Hypothetisierung von möglichen Konzepten und Designs für den Aufbau eines Service-Cores.

## Kontext

Die beiden Services DocEnsurance und DocFrame sind historisch gewachsen. Die Topologie von DocFrame ist gegenwärtig noch eine reine Projektion von DocEnsurance. Es besteht aktuell noch kein gemeinsamer Kern. Ich möchte gerne weitere Services ausarbeiten. Hierfür wäre es gut, einen Service-Core zu haben, welcher Services vereinheitlicht, stabilisiert und verbessert, sowie den Aufbau neuer Services vereinfacht.


## Weiteres

Für einfache, klar umrissene Änderungen genügt der reine TGD-Kern (**Phase Red $\to$ Phase Green (+ Rückwärtstür) $\to$ Phase Living-Documentation**). Bei komplizierten Umbauten – und ganz besonders bei der Arbeit mit KI-Agenten – zeigt die Praxis jedoch, dass zwei vorgeschaltete **Stützräder** die Qualität massiv verbessern:

### Stützrad 1: Analyse (`ANALYSIS`) – erst verstehen, was gerade Sache ist
* **Einfach erklärt:** Bevor eine einzige Zeile Test oder Produktionscode geändert wird, untersucht man in Ruhe das bestehende System und schreibt auf, wie es sich aktuell tatsächlich verhält ($Q_{\text{Ist}}$) und was eigentlich gelten müsste ($Q_{\text{Soll}}$).
* **Warum das besonders Agenten hilft:** Bei komplexen Zusammenhängen neigen KI-Agenten dazu, vorschnell Code zu ändern, ohne alle Abhängigkeiten zu überblicken. Eine dokumentierte Analyse-Phase zwingt dazu, erst Fakten zu sammeln und ein gemeinsames Lagebild herzustellen.

### Stützrad 2: Hypothese (`HYPOTHESIS`) – wissenschaftliche Sprache statt voreiliger Gewissheit
* **Einfach erklärt:** Eine Hypothese ist eine klar formulierte Idee, *was* die eigentliche Ursache sein könnte – zusammen mit weiteren überprüfbaren Ideen, die man ausprobieren kann. Sich bewusst an diese wissenschaftliche Sprache zu halten (*„Hypothese: ...“* statt *„Beweis: ...“*), ist sauberer und robuster: Man könnte ja falsch liegen! So bleibt die Dokumentation stabil, ehrlich und ordentlich, selbst wenn eine Vermutung später widerlegt wird.
* **Wann sie sich lohnt:** Die Hypothesen-Phase ist **rein optional**, aber beim Aufbau eines neuen Testmoduls oft sehr nützlich, weil sie Denkfehler aus der Analyse noch vor der Phase Red abfängt und zu deutlich schärferen Tests führt.
* **Für Experten (Meta-QA-Fragen an die Test-Suite):** Prüfe bestehende und geplante Tests bereits in der Hypothesen-Phase auf **logische Subsumtion** ($Q_{\text{pos}} \implies \neg Q_{\text{neg}}$, bei der ein positives Ziel das Verbot bereits impliziert und das Verbot dadurch ungetestet bleibt), **prädikatenlogische Tautologien** (wie $(y \in \mathbb{Z}) \lor (y \neq 99) \equiv \top$ unter `post="exists"`), **Vacuous Passes** (`0pos/Kneg`) und **überlebende Core-Mutanten** (schlägt wirklich ein Test fehl, wenn eine Kernfunktion wie `evaluate_step_logic()` ungefixt bleibt?).

---

* @docs/services/ANALYSIS.md

---

## Auftrag

* Entwickel Hypothesen für die Konzepte und ein mögliches Design für einen neuen Service-Core.

* Formuliere deinen Hypothesen-Bericht in @HYPOTHESIS.md nach dem @docs/dev/DEV-GUIDE_Agent-Reports.md

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](../.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](../GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](../GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](../GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](../GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](../GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](../README.md)  
[↦ | Core-Dokumentation | ↤](../core/README.md)  
[↦ | Entwicklerdokumentation | ↤](../dev/README.md)  
[↦ | Core-Internals | ↤](../dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](../misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](../feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
