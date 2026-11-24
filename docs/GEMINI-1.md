<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="head" banner="cubie-logo-written.png" -->
<div align="center">

# GEMINI

![Cubie](./docs/.assets/cubie-logo-written.png)

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

[README](../README.md) • [QA-Handbuch](./GUIDE_Quality-Assurance.md) • [DocEnsurance](./services/GUIDE_DocEnsurance.md)  

</div>
<!-- /qb:frame -->

# Ziel

Verbesserung der Docs. Fokus auf Code-Beispiele und Terminal-Commands.

## Kontext

Viele Code-Beispiele können noch eleganter gestaltet werden. Beispielsweise steht im @docs/services/GUIDE_DocEnsurance.md noch eine etwas redundate Form der Programmierung. Hier könnte man einfach eine Instanz definieren, ohne direkt .run auszuführen, um dann mit der Instanz .run auszuführen und die Infos zu printen.

Zudem könnten wir bestimmt an vielen Stellen die session-id besser nutzen und veranschaulichen. 

Außerdem sind einige beispielhafte Terminal-Commands ( wie in @docs/services/GUIDE_DocFrame.md ) noch in einem einzigen Block zusammengefasst, obwohl es mehrere Blöcke sein sollten. Vorallem in einer IDE wie PyCharm hat es enorme Vorteile, wenn man mehrere Terminal-Commands in mehreren MD-Blöcken führt, da man dadurch diese direkt mit einem Klick ausführen kann.

## Auftrag

Gehe alle Docs iterativ durch, begutachte sie und (insofern sinnvoll) verbessere jeweils die genannten Details. 
Dokumentiere die Änderungen abschließend als unreleased im @CHANGELOG.md

<!-- qb:frame id="CUBIE_DOC_FRAME_1" zone="foot" -->

---

---

<div align="center">

![Cubie](./docs/.assets/cubie-small.png)

[↦ | Vertragsaufbau: Eindeutigkeit & Kopplung | ↤](./docs/GUIDE_Contract-Design.md)  
[↦ | Erwartungssteuerung & Safety (`expect`-Flags) | ↤](./docs/GUIDE_Expect-Flags.md)  
[↦ | Qualitätssicherung mit Cubie | ↤](./docs/GUIDE_Quality-Assurance.md)  
[↦ | Fortgeschrittene Quantoren (`all` vs. `exists`) | ↤](./docs/GUIDE_Quantifiers.md)  
[↦ | Test-Guided Development (TGD) | ↤](./docs/GUIDE_TGD.md)  

[↦ | GUIDE: `DocEnsurance` – Lebende und verifizierte Dokumentation | ↤](./docs/services/GUIDE_DocEnsurance.md)  
[↦ | DocFrame (Prototyp) | ↤](./docs/services/GUIDE_DocFrame.md)  

[↦ | Dokumentations-Übersicht | ↤](./docs/README.md)  
[↦ | Core-Dokumentation | ↤](./docs/core/README.md)  
[↦ | Entwicklerdokumentation | ↤](./docs/dev/README.md)  
[↦ | Core-Internals | ↤](./docs/dev/core/README.md)  
[↦ | Hintergrund & Essays | ↤](./docs/misc/README.md)  
[↦ | Feature-Drafts: Virtualisierung | ↤](./docs/feature-drafts/virtualization/README.md)  

</div>
<!-- /qb:frame -->
